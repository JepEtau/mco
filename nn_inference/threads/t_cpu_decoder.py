from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass
import numpy as np
from pprint import pprint
import subprocess
from torch import Tensor
from threading import Event, Lock
import time
from typing import TYPE_CHECKING

from nn_inference.threads.t_helpers import get_encoder_step_no, get_first_nnmodel_step_no
from nn_inference.toolbox.filtering import get_decoder_ffmpeg_filters

from .t_cpu_encoder import CpuEncoderThread
from .t_decoder import VideoStreamInfo
from processing.frame_cache import FrameCache
from scene.filters import clean_fcomplex
from utils.mco_utils import calculate_scene_frame_count
if TYPE_CHECKING:
    from .t_inference import InferenceThread
    from scene.src_scene import SrcScene
    from parsers import Filter

from nn_inference.resource_mgr import NnFrame, BaseThread
from nn_inference.model_mgr import ModelManager

from utils.mco_types import Scene, Inputs
from utils.media import FShape
from utils.p_print import *
from utils.time_conversions import (
    FrameRate,
    frame_to_s,
    frame_to_sexagesimal,
)
from utils.tools import ffmpeg_exe



@dataclass
class CpuDecoderThreadConfig:
    e_thread: CpuEncoderThread
    model_manager: ModelManager
    channels_last: bool = False



class CpuDecoderThread(BaseThread):
    def __init__(
        self,
        config: CpuDecoderThreadConfig,
        scene: Scene,
        device: str = "cpu",
    ) -> None:
        super().__init__()
        self._stop_event: Event = Event()
        self._lock: Lock = Lock()
        self._lock.acquire(blocking=False)

        self.scene: Scene = scene
        self.sub_process: subprocess.Popen | None = None
        self.i_threads: dict[str, InferenceThread] = None
        self._decoded: int = 0
        self.config: CpuDecoderThreadConfig = config
        self.device: str = device


    def set_inference_threads(self, i_threads: dict[str, InferenceThread]):
        self.i_threads = i_threads


    @property
    def decoded(self) -> int:
        return self._decoded


    def run(self) -> None:
        verbose: bool = True
        scene: Scene = self.scene

        e_thread: CpuEncoderThread = self.config.e_thread

        # with torch.cuda.stream(cuda_stream):
        if True:
            # Calculate number of frames to generate, this might differ
            # from the destination: do not process frames with effects
            to_produce: int = calculate_scene_frame_count(scene)
            remaining: int = to_produce

            # A scene may use multiple segments from different scenes
            remaining_src_scenes = len(scene['src'].scenes())

            # A scene may use multiple segments from different scenes
            for src in scene['src'].scenes():
                src_scene: SrcScene = src.scene
                # Input scene is low resolution, this won't work for doc
                #  but we don't care because we use another pipeline for this
                #  consolidate_src should be modified for this
                src_scene_inputs: Inputs = src_scene['inputs']
                in_video_fp: str = src_scene_inputs.progressive().filepath

                if verbose or True:
                    print(lightgreen(f"[V][D] scene {scene['no']}"))
                in_video_info: VideoStreamInfo = src_scene_inputs.progressive().info

                frame_rate: FrameRate = in_video_info.frame_rate
                src_start, src_count = src.start, src.count
                if to_produce < src_count:
                    raise ValueError("why is to_produce < count?")
                    src_count = to_produce

                to_decode: int = src_count

                # Path the src scene so that the encoder receive the correct frame no.
                # TODO: verify that this will not impact the other scene when using the
                # same src
                src.scene['start'] = src_start
                src.scene['count'] = src_count
                if verbose:
                    print(lightgreen(f"[V][D] {src_count} frames to extract"))

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
                img_dtype: np.dtype = in_video_info.img_dtype
                pipe_img_nbytes = in_video_info.img_nbytes

                # Generate the decoder command line
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
                    "-t", str(frame_to_s(no=src_count, frame_rate=frame_rate)),

                    *filter_complex,

                    "-f", "image2pipe",
                    "-pix_fmt", in_video_info.pix_fmt,
                    "-vcodec", "rawvideo",
                    "-"
                ]
                # if verbose:
                print(lightgreen(f"[V][D] FFmpeg command:"), ' '.join(d_command))

                # Open subprocess
                self.sub_process = None
                try:
                    self.sub_process = subprocess.Popen(
                        d_command,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                except Exception as e:
                    print(f"[E] Unexpected error: {type(e)}", flush=True)

                if self.sub_process is None:
                    self._has_error = True
                    self._error_msg = "[E] Decoder failed to start"

                # Search the first nn model
                step_no: int = get_first_nnmodel_step_no(filter_steps)

                # Search the encoder step no.
                encoder_step_no: int = get_encoder_step_no(filter_steps)
                print(lightgreen(f"[V][D] encoder step no. -> {encoder_step_no}"))
                print(lightgreen(f"[V][D] first NN model step no -> {step_no}"))

                # Flow control
                flip_r_b: bool = in_video_info.img_c_order != 'rgb'

                # Frame replacement
                src_f_replace = src_scene['replace']
                frame_cache: FrameCache = FrameCache(verbose=False)
                if task_name != 'dsr':
                    frame_cache.set_replaced_frames(src_f_replace)

                # Backward scene....
                if src['backward']:
                    raise NotImplementedError("not implemented anymore")

                # decoder frame no.
                decoded: int = 0
                d_f_no: int = src_start
                f_index: int = 0

                # f_no is the frame no. to send to the encoder
                f_no: int = src_start

                # Number of src scenes to use
                remaining_src_scenes -= 1

                while (
                    not self._stop_event.is_set()
                    and to_decode
                    and remaining > 0
                ):
                    _in_f_no = src_start + f_index
                    if _in_f_no >= src_start + src_count:
                        print("BREAAAAAAK")
                        break

                    # Get frame_no to send to the consumer
                    f_no = frame_cache.get_out_f_no(_in_f_no)
                    # print(lightcyan(f"  ({f_index}) decoded: {d_f_no}, waiting for {f_no}"))

                    # if not cached, decode a new frame
                    img_buffer: np.ndarray = None
                    while f_no not in frame_cache:
                        img_buffer: np.ndarray = np.frombuffer(
                            self.sub_process.stdout.read(pipe_img_nbytes),
                            dtype=img_dtype,
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
                        decoded += 1

                    # f_no is in cache
                    if f_no in frame_cache:
                        img_buffer = frame_cache[f_no]
                    else:
                        raise RuntimeError(f"missing frame: {f_no}")


                    # Wait for release
                    # print(lightgreen(f"[V][D] Wait"))
                    self._lock.acquire(blocking=True)
                    if self._stop_event.is_set():
                        return

                    if remaining < 0 or img_buffer is None:
                        print(yellow("remaining < 0 or img_buffer is None"))
                        remaining = 0
                        self.release()
                        break

                    # Simulate HtoD transfer and "image to tensor"
                    d_img = img_buffer.reshape(img_shape)
                    tensor_dtype: np.dtype = np.float32
                    divisor: float = (
                        float(np.iinfo(img_dtype).max)
                        if tensor_dtype != img_dtype
                        else 1.
                    )
                    d_tensor: np.ndarray = d_img
                    if divisor != 1.:
                        d_tensor = d_tensor.astype(np.float32)
                        d_tensor /= divisor
                    d_tensor = np.ascontiguousarray(d_tensor.astype(tensor_dtype))

                    # Create a frame object
                    frame: NnFrame = NnFrame(
                        f_no=f_no,
                        tensor=d_tensor,
                        last=False,

                        scene=scene,
                        src_scene=src_scene,
                        sequence=filter_steps,
                        step_no=start_step_no,
                        encoder_step_no=encoder_step_no,
                    )

                    if remaining_src_scenes == 0 and remaining == 1:
                        print(yellow(f"  Tag last frame: {frame.f_no}"))
                        frame.last = True

                    # Wait -> run other threads
                    time.sleep(0.00001)

                    if verbose:
                        print(
                            f"[V][D] ({lightgreen(f_index)}) ({_in_f_no}), {remaining}. Tensor:",
                            f"{d_tensor.shape}, {d_tensor.dtype}"
                        )
                        print(f"[V][D]     Step no.:{frame.step_no}, {frame.sequence[frame.step_no]}")

                    # Send the frame to the consumer
                    if frame.step_no >= frame.encoder_step_no:
                        consumer = e_thread
                    else:
                        consumer = self.i_threads['cpu']
                        consumer.put_frame(frame)

                    remaining -= 1
                    f_index += 1

                # except:
                #     if verbose:
                #         print(lightgreen(f"[V][D] Encountered end of file or error. Decoded {f_no} frames"))
                print(lightgreen(f"[V][D] End of src scene {src_scene['no']}"))
            print(lightgreen(f"[V][D] End of scene {scene['no']}"))
        print(lightgreen(f"[V][D] End of decoding"))


    def stop(self, force: bool=False) -> None:
        self._stop_event.set()

        if force:
            self.release()
            try:
                self.sub_process.kill()
            except:
                pass


    def release(self) -> None:
        try:
            self._lock.release()
        except:
            pass


    def set_produce_flag(self) -> None:
        self.release()

