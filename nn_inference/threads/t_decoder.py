from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass, field
import time
import warnings
import numpy as np
from pprint import pprint
import subprocess
from threading import Event, Lock
import torch
from torch import Tensor
from typing import TYPE_CHECKING

from nn_inference.toolbox.cuda_filters import save_tensor_for_ccor_
from nn_inference.toolbox.dh_transfers import (
    htod_transfer,
)
from nn_inference.toolbox.filtering import (
    apply_cuda_filters_,
    get_decoder_ffmpeg_filters,
)

from .t_helpers import (
    get_encoder_step_no,
    get_first_nnmodel_step_no,
)
from processing.frame_cache import (
    FrameCache,
)
from scene.filters import clean_fcomplex
from utils.mco_utils import calculate_scene_frame_count
if TYPE_CHECKING:
    from .t_inference import InferenceThread
    from .t_encoder import EncoderThread
    from scene.src_scene import SrcScene
    from parsers import Filter
from nnarchs import (
    NnModelSession,
    np_dtype_to_torch,
    img_to_tensor,
)
from nn_inference.model_mgr import ModelManager
from nn_inference.resource_mgr import McoFrame, BaseThread
from utils.mco_types import Scene, Inputs
from utils.media import ChannelOrder, FShape
from utils.p_print import *
from utils.time_conversions import (
    FrameRate,
    frame_to_s,
    frame_to_sexagesimal,
)
from utils.tools import ffmpeg_exe
from parsers import (
    get_loop_nframes,
)

warnings.filterwarnings("ignore", category=UserWarning, message=".*non-writable tensors.*")

@dataclass
class VideoStreamInfo:
    img_dtype: np.dtype
    img_c_order: ChannelOrder
    img_shape: FShape
    img_nbytes: int
    pix_fmt: str
    frame_rate: int
    metadata: dict[str, str] = field(default_factory=dict)



@dataclass(slots=True)
class DecoderThreadConfig:
    e_thread: EncoderThread
    model_manager: ModelManager
    channels_last: bool = False



class DecoderThread(BaseThread):
    def __init__(
        self,
        config: DecoderThreadConfig,
        scene: Scene,
        device: str = "cuda:0",
    ) -> None:
        super().__init__()
        self._stop_event: Event = Event()
        self._lock: Lock = Lock()
        self._lock.acquire(blocking=False)

        self.scene: Scene = scene
        self.d_subprocess: subprocess.Popen | None = None
        self.i_threads: dict[str, InferenceThread] = None
        self._decoded: int = 0
        self.config: DecoderThreadConfig = config
        self.device: str = device


    def set_inference_threads(self, i_threads: dict[str, InferenceThread]):
        self.i_threads = i_threads


    @property
    def decoded(self) -> int:
        return self._decoded


    @torch.inference_mode()
    def run(self) -> None:
        debug = self.debug

        model_manager: ModelManager = self.config.model_manager
        # Create a cuda stream and allocate Host memory
        cuda_stream: torch.cuda.Stream = torch.cuda.Stream(model_manager.device)
        vpi_nbytes = model_manager.in_nbytes
        host_mem: Tensor = torch.empty(
            vpi_nbytes,
            dtype=torch.uint8,
            pin_memory=True
        )

        e_thread: EncoderThread = self.config.e_thread

        scene: Scene = self.scene

        with torch.cuda.stream(cuda_stream):
            # Calculate number of frames to generate, this might differ
            # from the destination: do not process frames with effects
            to_produce: int = calculate_scene_frame_count(scene)
            remaining: int = to_produce

            # A scene may use multiple segments from different scenes
            remaining_src_scenes = len(scene['src'].scenes())

            for src_index, src_scene in enumerate(scene['src'].scenes()):
                in_scene: Scene = src_scene.in_scene
                src_scene_inputs: Inputs = in_scene['inputs']
                in_video_fp: str = src_scene_inputs.progressive().filepath

                if debug or True:
                    print(lightgreen(f"[V][D] scene {scene['no']}"))
                in_video_info: VideoStreamInfo = src_scene_inputs.progressive().info

                src_start, src_count = src_scene.start, src_scene.count
                if to_produce < src_count:
                    raise ValueError("why is to_produce < count?")
                    src_count = to_produce

                # Path the src scene so that the encoder receive the correct frame no.
                # TODO: verify that this will not impact the other scene when using the
                # same src
                # src_scene.in_scene['start'] = src_start
                # src_scene.in_scene['count'] = src_count
                to_decode: int = src_scene.to_decode
                _to_decode: int = to_decode
                remaining = src_count
                src_end = src_start + to_decode

                if debug:
                    print(lightgreen(f"[V][D] {to_decode} frames to extract"))

                # TODO ensure to_decode is consistent for all scenes
                if to_decode != src_count:
                    if (
                        'effects' not in in_scene
                        or (
                            not in_scene['effects'].has_effect('decimate')
                            and not in_scene['effects'].has_effect('decimate')
                        )
                    ):
                        pprint(scene)
                        pprint(src_scene)
                        raise ValueError(red(f"to decode ({to_decode}) != src.count ({src_count})"))

                # Decimate
                factor_mod1: int = 0
                if 'effects' in in_scene:
                    if e := in_scene['effects'].get_effect('decimate'):
                        factor_mod1, _ = e.extra_param
                        print(yellow(f"  decimate:"), f"{in_scene['no']}: {to_decode} -> {remaining} (mod={factor_mod1})")
                        src_end = src_start + to_decode

                # Frame replacement
                src_f_replace = in_scene['replace']
                frame_cache: FrameCache = FrameCache(verbose=False)
                frame_cache.set_replaced_frames(src_f_replace)

                # Replace a segment by a loop
                if (
                    'effects' in in_scene
                    and in_scene['effects'].has_effect(name='replace_by_loop')
                ):
                    for loop in in_scene['effects'].get_effects(name='replace_by_loop'):
                        frame_cache.add_loop_segment(
                            (loop.start, loop.loop, loop.f_ref)
                        )

                # If last frames will be replaced, do not decode them
                if frame_cache.to_replace(src_scene.start + to_decode - 1):
                    to_decode -= 1
                    for i in range(src_scene.start + to_decode - 1, 1, -1):
                        if not frame_cache.to_replace(i):
                            break
                        to_decode -= 1
                    _to_decode = to_decode
                print(yellow(f"[V][D] new to_decode: {_to_decode}"))


                # Get filters
                task_name = scene['task'].name
                filter_steps: Filter = scene['filters'][task_name].steps

                # Add some filters executed by FFmpeg
                filter_complex_list: list[str] = []
                additional_filters, start_step_no = (
                    get_decoder_ffmpeg_filters(filter_steps)
                )
                pprint(additional_filters)
                if additional_filters:
                    filter_complex_list.extend(additional_filters)

                # Generate the FFmpeg filter command
                fcomplex_str: str = ','.join(filter_complex_list)
                fcomplex_str = clean_fcomplex(fcomplex_str)
                filter_complex: list[str] = []
                if fcomplex_str:
                    filter_complex = [
                        "-filter_complex", f"[0:v]{fcomplex_str}[outv]",
                        "-map", "[outv]"
                    ]

                # if verbose:
                print(lightgreen(f"[V][E] filter_complex:"), filter_complex)
                print(f"start step_no: {start_step_no}")

                # Input stream
                img_shape: FShape = in_video_info.img_shape
                img_dtype: np.dtype = np_dtype_to_torch[in_video_info.img_dtype]
                pipe_img_nbytes = in_video_info.img_nbytes

                # FFmpeg decoder command
                frame_rate: FrameRate = in_video_info.frame_rate
                d_command: list[str] = [
                    ffmpeg_exe,
                    "-hide_banner",
                    "-loglevel", "warning",
                    "-nostats",
                    "-ss",
                    str(
                        frame_to_sexagesimal(
                            no=src_start - src_scene_inputs.progressive().start,
                            frame_rate=frame_rate
                        )
                    ),
                    "-i", in_video_fp,
                    "-t", str(frame_to_s(no=to_decode, frame_rate=frame_rate)),

                    *filter_complex,

                    "-f", "image2pipe",
                    "-pix_fmt", in_video_info.pix_fmt,
                    "-vcodec", "rawvideo",
                    "-"
                ]
                # if verbose:
                print(lightgreen(f"[V][D] FFmpeg command:"), ' '.join(d_command))

                # Open subprocess
                self.d_subprocess = None
                try:
                    self.d_subprocess = subprocess.Popen(
                        d_command,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                except Exception as e:
                    print(f"[E] Unexpected error: {type(e)}", flush=True)

                if self.d_subprocess is None:
                    self._has_error = True
                    self._error_msg = "[E] Decoder failed to start"

                # Search the first nn model
                step_no: int = get_first_nnmodel_step_no(filter_steps)
                print(lightgreen(f"[V][D] first NN model step no -> {step_no}"))
                if step_no == -1:
                    encoder_step_no: int = len(filter_steps)
                    first_model_dtype = torch.float16
                else:
                    session: NnModelSession = model_manager.session(filter_steps[step_no])
                    first_model_dtype = session.dtype

                    # Search the encoder step no.
                    encoder_step_no: int = get_encoder_step_no(filter_steps)
                print(lightgreen(f"[V][D] decoder step no. -> {encoder_step_no}"))

                # Flow control
                flip_r_b: bool = in_video_info.img_c_order != 'rgb'

                # decoder frame no.
                d_f_no: int = src_start
                f_index: int = 0

                # f_no is the frame no. to send to the encoder
                f_no: int = src_start

                # Number of src scenes to use
                remaining_src_scenes -= 1

                # decimate
                decimate_index: int = 0

                while (
                    not self._stop_event.is_set()
                    and remaining > 0
                ):
                    _in_f_no = src_start + f_index
                    if _in_f_no >= src_end:
                        print(red(f"heeee? {_in_f_no} >= {src_end}"))
                        break

                    # decimate
                    if factor_mod1:
                        # print(f"decimate index: {decimate_index} % {factor_mod1} -> {decimate_index // factor_mod1}")
                        if decimate_index // factor_mod1 == 1:
                            decimate_index = 0
                            # print(f"  discard {_in_f_no}")
                            f_index += 1
                            _in_f_no = src_start + f_index
                            if _in_f_no >= src_end:
                                print(red(f"decimate: heeee? {_in_f_no} >= {src_end}"))
                                break
                        else:
                            decimate_index += 1

                    # Get frame_no to send to the consumer
                    f_no = frame_cache.get_out_f_no(_in_f_no)
                    # print(lightcyan(f"  ({f_index}) decoded: {d_f_no}, waiting for {f_no}"))

                    # if not cached, decode a new frame
                    img_buffer: Tensor = None
                    while f_no not in frame_cache:
                        img_buffer: Tensor = torch.frombuffer(
                            self.d_subprocess.stdout.read(pipe_img_nbytes),
                            dtype=torch.uint8,
                        )
                        # print(lightcyan(f"  ({f_index}) decoded: {d_f_no}, waiting for {f_no}"))

                        # Throw this frame away if replaced
                        if (
                            frame_cache.to_replace(d_f_no)
                            and task_name != 'dsr'
                        ):
                            # print(f"  discard: {d_f_no}")
                            pass
                        else:
                            frame_cache.add(d_f_no, img_buffer)

                        d_f_no += 1
                        _to_decode -= 1

                    # f_no is in cache
                    if f_no in frame_cache:
                        img_buffer = frame_cache[f_no]
                    else:
                        raise RuntimeError(f"missing frame: {f_no}")

                    # print(lightcyan(f"   {out_i}: send {f_no}"))

                    # Wait until resource (GPU) is available
                    self._lock.acquire(blocking=True)
                    if self._stop_event.is_set():
                        return

                    if remaining < 0 or img_buffer is None:
                        raise ValueError(red("remaining < 0 or img_buffer is None"))
                        remaining = 0
                        self.release()
                        break

                    # HtoD transfer
                    #   returns an image (h,w,c) with dtype the datatype of the pipe
                    d_img: Tensor = htod_transfer(
                        host_mem=host_mem,
                        img_buffer=img_buffer,
                        img_dtype=img_dtype,
                        img_shape=img_shape,
                        cuda_stream=cuda_stream
                    )

                    time.sleep(0.0001)
                    cuda_stream.synchronize()

                    # Use the dtype of the first session following
                    # All filters between decoder and the next session will use this dtype
                    d_tensor: Tensor = img_to_tensor(
                        d_img=d_img,
                        tensor_dtype=first_model_dtype,
                        flip_r_b=flip_r_b,
                    )

                    # Create a frame object
                    frame: McoFrame = McoFrame(
                        f_no=f_no,
                        tensor=d_tensor.clone(),
                        last=False,

                        scene=scene,
                        src_scene_index=src_index,
                        sequence=deepcopy(filter_steps),
                        step_no=start_step_no,
                        encoder_step_no=encoder_step_no,
                    )

                    # Tag it as last frame if no other src scene to decode
                    # and this is the last frame of this src scene
                    # that it's the latest one and it has to continue producing frames
                    # by itself
                    if remaining_src_scenes == 0 and remaining == 1:
                        print(yellow(f"  Tag last frame: {frame.f_no}"))
                        frame.last = True

                    # Save tensor if this frame tensor will be used as ref
                    frame = save_tensor_for_ccor_(frame)

                    # Execute synchronous filters.
                    # TODO: later, use a separate thread for this
                    # Apply cuda filters until next inference or decoder
                    apply_cuda_filters_(frame, verbose=debug)

                    time.sleep(0.0001)
                    cuda_stream.synchronize()

                    if debug:
                        print(
                            f"[V][D] ({lightgreen(f_index)}) ({_in_f_no}), {remaining}. Tensor:",
                            f"{d_tensor.shape}, {d_tensor.dtype}"
                        )
                        # print(f"[V][D]     Step no.:{frame.step_no}") #, {frame.sequence[frame.step_no]}")

                    # Skip following model if inpainting and dsr
                    # patch_next_step_no_(frame=frame, model_manager=model_manager)

                    # print(f"    ({f_index}) send {frame.f_no}")


                    # Send the frame to the consumer
                    if frame.step_no >= frame.encoder_step_no:
                        consumer = e_thread
                    else:
                        consumer = self.i_threads[
                            model_manager.xprovider(frame.sequence[step_no])
                        ]
                    consumer.put_frame(frame)

                    # increment _in_f_no, because 'loop' frames have been sent to the encoder
                    loop = get_loop_nframes(src_scene, f_no=f_no)
                    if loop:
                        remaining -= loop
                        f_index += loop
                    else:
                        remaining -= 1
                        f_index += 1

                    # All frames of the scene have been decoded and sent to consumer
                    if _to_decode == 0:
                        print(f"all frames to be decoded have been decoded: {to_decode}")

                    if debug:
                        print(f"[V][D] remaining _to_decode: {_to_decode}")

                print(yellow(f"  remaining src scenes: {remaining_src_scenes}"))
                if remaining_src_scenes == 0:
                    break
                print(lightgreen(f"[V][D] End of src scene {in_scene['no']}"))

                if self.d_subprocess.poll() is None:
                    timeout: int = 10
                    while self.d_subprocess.poll() is None and timeout:
                        time.sleep(0.1)
                        timeout -= 1
                    if not timeout:
                        self.d_subprocess.kill()
                    print(yellow(f"to decode was higher than what has to be decoded {_to_decode}"))

            print(lightgreen(f"[V][D] End of scene {scene['no']}"))

        print(lightgreen(f"[V][D] End of decoding, decoded: {src_count}"))



    def stop(self, force: bool=False) -> None:
        self._stop_event.set()

        if force:
            self.release()
            try:
                self.d_subprocess.kill()
            except:
                pass


    def release(self) -> None:
        try:
            self._lock.release()
        except:
            pass


    def set_produce_flag(self) -> None:
        self.release()

