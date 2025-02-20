from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass
import numpy as np
from pprint import pprint
import subprocess
from threading import Event, Lock
import time
from typing import TYPE_CHECKING

from nn_inference.threads.t_helpers import get_encoder_step_no, get_first_nnmodel_step_no
from nn_inference.toolbox.filtering import get_decoder_ffmpeg_filters

from .t_cpu_encoder import CpuEncoderThread
from .t_decoder import VideoStreamInfo
from processing.frame_replace import ItemCache, get_frames_to_cache, get_frames_to_remove
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


    def set_inference_threads(self, i_threads: dict[str, InferenceThread]):
        self.i_threads = i_threads


    @property
    def decoded(self) -> int:
        return self._decoded


    def run(self) -> None:
        verbose: bool = True
        scene: Scene = self.scene

        e_thread: CpuEncoderThread = self.config.e_thread

        # Calculate number of frames to generate, this might differ
        # from the destination: do not process frames with effects
        to_produce: int = calculate_scene_frame_count(scene)

        # A scene may use multiple segments from different scenes
        rem_src_scene = len(scene['src'].scenes())
        print(f"remaining scenes: {rem_src_scene}")

        remaining: int = to_produce
        out_i: int = 0
        produced: int = 0

        # A scene may use multiple segments from different scenes
        for src in scene['src'].scenes():
            src_scene: SrcScene = src['scene']
            # Input scene is low resolution, this won't work for doc
            #  but we don't care because we use another pipeline for this
            #  consolidate_src should be modified for this
            src_scene_inputs: Inputs = src_scene['inputs']
            in_video_fp: str = src_scene_inputs.progressive().filepath

            if verbose or True:
                print(lightgreen(f"[V][D] scene {scene['no']}"))
            in_video_info: VideoStreamInfo = src_scene_inputs.progressive().info

            frame_rate: FrameRate = in_video_info.frame_rate
            src_start: int = src['start']
            src_count: int = src['count']

            # Path the src scene so that the encoder receive the correct frame no.
            # TODO: verify that this will not impact the other scene when using the
            # same src
            src['scene']['start'] = src_start
            src['scene']['count'] = src_count

            if to_produce < src_count:
                src_count = to_produce
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
            in_dtype: np.dtype = in_video_info.img_dtype
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

            # Frame replacement
            src_f_replace = src_scene['replace']
            if task_name != 'dsr':
                frames_to_replace: list[int] = get_frames_to_remove(src_f_replace)
                frames_to_cache: list[int] = get_frames_to_cache(src_f_replace)
                frame_cache: ItemCache = ItemCache(verbose=True)
                frame_cache.set_occurences(src_f_replace)
                frame_cache.set_exceptions(frames_to_replace)
                if verbose:
                    print(lightgreen(f"[V][D] Frames to replace"), frames_to_replace)
                    print(lightgreen(f"[V][D] Frames to cache"), frames_to_cache)

            # Backward scene....
            src_scene['backward'] = src['backward']
            if src_scene['backward']:
                raise NotImplementedError("not implemented anymore")

            # remaining source no
            rem_src_scene -= 1

            # in_f_no is incremented before reading in pipe
            f_index: int = 0
            in_f_no: int = src_start - 1
            out_f_no: int = src_start

            print(f"decoder: scene: {remaining} from {src_start}, remaining src scenes: {rem_src_scene}")
            while (
                not self._stop_event.is_set()
                and remaining > 0
            ):
                # print(lightgreen("[V][D] Read input stream"))
                # We discard all frames that will be replaced
                img_buffer: np.ndarray = None
                while img_buffer is None and remaining > 0:
                    # There is a bug here when end of file is reached
                    # We don't care because it won't happen
                    img_buffer: np.ndarray = np.frombuffer(
                        self.sub_process.stdout.read(pipe_img_nbytes),
                        dtype=in_dtype,
                    )
                    in_f_no += 1
                    remaining -= 1

                    # Throw this frame away if is replaced
                    if (
                        in_f_no in frames_to_replace
                        and task_name != 'dsr'
                    ):
                        print(lightgreen(f"[V][D] Discard {in_f_no}"))
                        img_buffer = None
                    # We have an img_buffer or nothing if no more frame to extract

                frame_cache.add(in_f_no, img_buffer)

                # Get the frame no to be used
                in_img = None
                f_no = (
                    src_f_replace[out_f_no]
                    if out_f_no in src_f_replace
                    else out_f_no
                )
                print(f"  in: {in_f_no}, waiting for {f_no}")
                in_img = None
                if f_no == in_f_no:
                    in_img = img_buffer

                elif f_no in frame_cache:
                    in_img = frame_cache[f_no]

                if in_img is not None:
                    produced += 1
                    out_i += 1

                    out_f_no += 1
                    src_count -= 1

                else:
                    # Continue if not found because it will be decoded later
                    print(f"{f_no} is not found, decode a new one")
                    continue

                # Wait for release
                # print(lightgreen(f"[V][D] Wait"))
                self._lock.acquire(blocking=True)
                if self._stop_event.is_set():
                    return

                if remaining < 0 or img_buffer is None:
                    remaining = 0
                    print(red("release"))
                    self.release()
                    break

                # Simulate HtoD transfer and "image to tensor"
                d_img = img_buffer.reshape(img_shape)
                img_dtype: np.dtype = in_dtype
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
                    f_no=in_f_no,
                    tensor=d_tensor,
                    scene=scene,
                    src_scene=src_scene,
                    # TODO remove deepcopy
                    sequence=deepcopy(filter_steps),
                    step_no=start_step_no,
                    encoder_step_no=encoder_step_no,
                )

                # Wait -> run other threads
                time.sleep(0.00001)

                if verbose:
                    print(
                        f"[V][D] ({lightgreen(f_index, remaining)}) ({in_f_no}) Put tensor in queue:",
                        f"{d_tensor.shape}, {d_tensor.dtype}"
                    )
                    print(f"[V][D]     Step no.:{frame.step_no}, {frame.sequence[frame.step_no]}")

                # Send the frame to the consumer
                if frame.step_no >= frame.encoder_step_no:
                    consumer = e_thread
                else:
                    consumer = self.i_threads['cpu']
                    consumer.put_frame(frame)

                self._decoded += 1
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

