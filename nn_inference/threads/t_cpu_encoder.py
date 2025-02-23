from collections import deque
import os
import numpy as np
from pprint import pprint
from queue import Queue
import subprocess
import sys
from threading import Event
import torch
from typing import Callable

from parsers import VideoSettings
from nn_inference.resource_mgr import NnFrame, BaseThread
from nn_inference.toolbox.filtering import get_encoder_ffmpeg_filters
from processing.effects import apply_upscale_effects
from processing.frame_replace import (
    ItemCache,
    get_frames_to_remove,
)
from pynnlib.import_libs import is_cuda_available
from scene.filters import do_watermark, get_ffmpeg_pad_filter, clean_fcomplex
from scene.src_scene import SrcScene
from utils.mco_types import McoFrame, Scene
from utils.mco_utils import ffmpeg_metadata
from utils.media import str_to_video_codec
from utils.p_print import *
from utils.path_utils import path_split
from utils.pxl_fmt import PIXEL_FORMAT
from utils.tools import ffmpeg_exe



class CpuEncoderThread(BaseThread):
    def __init__(self) -> None:
        super().__init__()
        self._stop_event: Event = Event()
        self.in_queue: Queue = Queue(1)
        self._encoded: int = 0


    @property
    def encoded(self) -> int:
        return self._encoded


    def run(self) -> None:
        verbose: bool = False

        in_queue: Queue = self.in_queue
        writer_subproces: subprocess.Popen | None = None

        # Default settings
        stdin_pixfmt: str = 'rgb24'
        stdin_dtype: np.dtype = np.uint8
        if verbose:
            print(purple("[V][E] Encoder, config:"))

        self._encoded: int = 0
        scene: Scene | None = None
        src_scene: SrcScene = None
        frame: NnFrame = None
        # backward_imgs: deque = deque()
        # try:
        if True:
            while not self._stop_event.is_set():
                # Wait for a frame or a poison pill
                input = in_queue.get(block=True)
                if input is None or self._stop_event.is_set():
                    if verbose:
                        print(purple("[V][E] Received Null tensor"))

                    # if src_scene is not None and src_scene['backward']:
                    #     count = len(backward_imgs)
                    #     for _ in range(count):
                    #         writer_subproces.stdin.write(backward_imgs.pop())

                    self.end_encoding(writer_subproces)
                    writer_subproces = None
                    break

                frame: NnFrame = input

                if scene is None:
                    # This is a different scene:
                    # - end the current encoder subprocess
                    # - start a new one
                    if src_scene is not None and src_scene['backward']:
                        count = len(backward_imgs)
                        for _ in range(count):
                            writer_subproces.stdin.write(backward_imgs.pop())

                    self.end_encoding(writer_subproces)

                    # New scene
                    scene = frame.scene
                    fp: str = scene['task'].video_file

                    print(purple(f"[V][E] New target scene: {scene['no']}"))

                    # Use the destination frame count because we integrate all loops here
                    to_produce: int = scene['dst']['count']
                    remaining = to_produce
                    out_i: int = 0
                    print(purple(f"[V][E] output video file: {fp}"))
                    print(purple(f"[V][E] Frames to produce: {to_produce}"))
                    if verbose:
                        print(purple(f"[V][E] output video file: {fp}"))
                        print(purple(f"[V][E] Frames to produce: {to_produce}"))

                    src_scene: SrcScene = None
                    vsettings: VideoSettings = scene['task'].video_settings
                    if vsettings.codec not in str_to_video_codec:
                        sys.exit(red(f"{vsettings.codec} is not supported"))

                    # stdin pixel format
                    if PIXEL_FORMAT[vsettings.pix_fmt]['bpp'] > 8:
                        stdin_pixfmt = 'rgb48'
                        stdin_dtype = np.uint16
                        stdin_torch_dtype: torch.dtype = torch.uint16
                    else:
                        stdin_pixfmt = 'rgb24'
                        stdin_dtype = np.uint8
                        stdin_torch_dtype: torch.dtype = torch.uint8

                    # FFmpeg complex filter
                    filter_complex: list[str] = []
                    # upscale_height = 1080 + 2 * vsettings.pad
                    # if h > upscale_height:
                    #     # used for 'upscale' task only
                    #     fcomplex_str += f"""
                    #         scale=-1:{upscale_height}
                    #             :lanczos+accurate_rnd+bitexact+full_chroma_int
                    #     """
                    filter_complex_list: list[str] = []

                    filter_complex_list.append("""
                        setparams=colorspace=bt709
                            :color_primaries=bt709
                            :color_trc=bt709
                    """)

                    pad_filter: str = get_ffmpeg_pad_filter(scene)
                    if pad_filter:
                        filter_complex_list.append(pad_filter)

                    additional_filters: list[str] = get_encoder_ffmpeg_filters(
                        frame.sequence, start_step_no=frame.step_no
                    )
                    if additional_filters:
                        filter_complex_list.extend(additional_filters)

                    # Generate the FFmpeg filter command
                    fcomplex_str: str = ','.join(filter_complex_list)
                    fcomplex_str = clean_fcomplex(fcomplex_str)
                    if fcomplex_str:
                        filter_complex = [
                            "-filter_complex", f"[0:v]{fcomplex_str}[outv]",
                            "-map", "[outv]"
                        ]

                    if verbose:
                        print(purple(f"[V][E] fcomplex_str:"), fcomplex_str)

                    codec: str = str_to_video_codec[vsettings.codec].value
                    codec_settings = vsettings.codec_options
                    if not is_cuda_available():
                        codec_settings = []
                        codec = 'libx264'

                    metadata: list[str] = ffmpeg_metadata(scene)
                    h, w = frame.tensor.shape[:2]
                    encoder_command: list[str] = [
                        ffmpeg_exe,
                        "-hide_banner",
                        "-loglevel", "error",
                        "-nostats",

                        "-f", "rawvideo",
                        '-pixel_format', stdin_pixfmt,
                        '-video_size', f"{w}x{h}",
                        "-r", str(vsettings.frame_rate),

                        "-i", "pipe:0",
                        *filter_complex,

                        "-vcodec", codec,
                        *codec_settings,
                        "-pix_fmt", vsettings.pix_fmt,
                        "-color_range", "limited",

                        *metadata,
                        "-y",
                        fp
                    ]

                    print(purple(f"[V][E] command: "), " ".join(encoder_command))

                    os.makedirs(path_split(fp)[0], exist_ok=True)
                    try:
                        writer_subproces = subprocess.Popen(
                            encoder_command,
                            stdin=subprocess.PIPE,
                            stdout=sys.stdout,
                            stderr=subprocess.STDOUT,
                            # bufsize=10**8
                        )
                    except Exception as e:
                        print(f"[E] Unexpected error: {type(e)}", flush=True)

                # Get tensor from frame
                if verbose:
                    print(
                        purple(f"[V][E] Received:"),
                        f"{frame.tensor.shape}, {frame.tensor.dtype}, {frame.tensor.shape}"
                    )

                # Simulate tensor_to_img and dtoh_transfer
                multiplier: float = 1.
                tensor: np.ndarray = frame.tensor
                tensor_dtype: np.dtype = tensor.dtype
                if tensor_dtype != stdin_dtype:
                    num = (
                        float(np.iinfo(stdin_dtype).max)
                        if tensor_dtype in (np.float32, np.float16)
                        else 1.
                    )
                    denum = (
                        float(np.iinfo(tensor_dtype).max)
                        if stdin_dtype == np.float32
                        else 1.
                    )
                    multiplier: float = num / denum

                out_img: np.ndarray = tensor
                if multiplier != 1.:
                    out_img = out_img.astype(np.float32, copy=False)
                    out_img = out_img * multiplier
                out_img = out_img.astype(stdin_dtype, copy=False)

                # Frame replace
                # Src scene is not the same, create a new cache for frame replacement
                if src_scene is None or frame.src_scene is not src_scene:
                    src_scene = frame.src_scene
                    if verbose:
                        print(purple(f"[V][E] New src scene:"), src_scene['no'])

                    # Do not replace frames as this video
                    # will be used to remove dust, scratches
                    # and set the frames to be replaced
                    frame_cache: ItemCache = ItemCache()
                    frame_replace: list | dict[int, int] = []
                    if frame.scene['task'].name != 'dsr':
                        frame_replace = src_scene['replace']
                        frames_to_replace: list[int] = get_frames_to_remove(frame_replace)
                        frame_cache.set_occurences(frame_replace)
                        frame_cache.set_exceptions(frames_to_replace)

                    start: int = src_scene['start']

                    if verbose:
                        print(purple(f"[V][E] frame replace: "), src_scene['replace'])

                    # if src_scene['backward']:
                    #     backward_imgs: deque = deque()

                in_f_no: int = frame.f_no
                in_frame: McoFrame = McoFrame(
                    no=frame.f_no,
                    scene=frame.scene,
                    img=out_img
                )


                # if verbose:
                #     print(yellow(f"[V][E] ({self._encoded}) write image: {out_img.shape}, {out_img.dtype}, in_f_no: {in_f_no}"))
                # print(purple(f"\nreceived frame no. {in_frame.no}"))
                # frame_cache.add(in_f_no, in_frame)

                # Send to FFmpeg
                # sent = 0
                # while remaining > 0:
                #     f_no = (
                #         frame_replace[in_f_no]
                #         if in_f_no in frame_replace
                #         else in_f_no
                #     )
                #     out_frame: McoFrame = frame_cache[f_no]
                #     if out_frame is not None:

                #         if src_scene['backward']:
                #             backward_imgs.append(out_frame.img)
                #             out_i += 1
                #             remaining -= 1

                #         else:
                #             out_frames: list[McoFrame] = apply_upscale_effects(
                #                 in_f_no, out_frame, out_i
                #             )
                #             if verbose:
                #                 for i, f in enumerate(out_frames):
                #                    print(yellow(f"[V][E] {out_i + i}: send {f.no}"), flush=True)

                #             [writer_subproces.stdin.write(f.img) for f in out_frames]
                #             out_i += len(out_frames)
                #             remaining -= len(out_frames)
                #             sent += len(out_frames)

                #         # in_f_no += 1

                #     else:
                #         break

                out_frames: list[McoFrame] = apply_upscale_effects(
                    in_f_no, in_frame, out_i
                )
                if verbose:
                    for i, f in enumerate(out_frames):
                        print(yellow(f"[V][E] {out_i + i}: send {f.no}"), flush=True)

                [writer_subproces.stdin.write(f.img) for f in out_frames]
                out_i += len(out_frames)
                remaining -= len(out_frames)
                sent += len(out_frames)


                del frame.tensor
                if self.progress_thread is not None:
                    self.progress_thread.put(sent)
                self._encoded += sent
                sent = 0

            print(
                yellow(f"[V][E] Encoded all frames"),
                f"{self._encoded}",
                flush=True
            )

        # except:
        #     print(red(f"[V][E] Error while executing: "), " ".join(encoder_command))
        self.end_encoding(writer_subproces)


    def end_encoding(self, sub_process: subprocess.Popen| None) -> bool:
        # Close output video
        print(yellow(f"[V][E] end encoding"), flush=True)
        if sub_process is not None:
            stderr_bytes: bytes | None = None
            if sub_process is not None:
                try:
                    # Arbitrary timeout value
                    print(yellow(f"[V][E] sent null"), flush=True)
                    _, stderr_bytes = sub_process.communicate()
                except:
                    sub_process.kill()
                    pass
            if stderr_bytes is not None:
                std_str = stderr_bytes.decode('utf-8)')
                # TODO: parse the output file
                for l in std_str:
                    if not l.startswith("x265 [info]"):
                        print(l.strip())
        return True


    def stop(self, force: bool=False) -> None:
        self._stop_event.set()
        if force:
            while not self.in_queue.empty():
                self.in_queue.get_nowait()
        self.put_frame(None)


    def put_frame(self, frame: NnFrame) -> bool:
        self.in_queue.put(frame)
        return True


    @property
    def encoded(self) -> int:
        return self._encoded

    def set_progress_callback(self, function: Callable) -> None:
        self.callback = function


