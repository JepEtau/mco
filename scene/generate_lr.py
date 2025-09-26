from collections import deque
import math
import os
from pprint import pprint
from queue import Queue
import subprocess
import sys
from threading import Event, Thread
from warnings import warn
import cv2
import numpy as np
import time
from nn_inference.resource_mgr import NnFrame
from nn_inference.threads.t_decoder import VideoStreamInfo
from parsers import (
    db,
    VideoSettings,
    SceneDsr,
    DsrPatch,
    get_frame_rate,
    Effect,
    get_loop_nframes,
    Warp,
)
from processing.dsr import generate_dsr_mask
from processing.effects import apply_final_effects, apply_upscale_effects
from processing.frame_cache import FrameCache
from processing.warp import warp_image
from processing.watermark import add_watermark
from scene.filters import do_watermark
from scene.src_scene import SrcScene, SrcScenes
from utils.images_io import write_image
from utils.logger import main_logger
from utils.mco_types import ChapterVideo, Inputs, McoFrame, Scene
from utils.mco_utils import (
    calculate_scene_frame_count,
    ffmpeg_metadata,
    get_target_audio,
    get_target_video,
    is_first_scene,
    is_last_scene,
    is_up_to_date
)
from utils.np_dtypes import np_to_float32, np_to_uint8
from utils.p_print import *
from utils.path_utils import path_split
from utils.pxl_fmt import PIXEL_FORMAT
from utils.time_conversions import FrameRate, frame_to_s, frame_to_sexagesimal
from utils.tools import ffmpeg_exe
from utils.media import (
    VideoInfo, extract_media_info_mco, frame_rate_dec, str_to_video_codec
)
from processing.frame_warp_cache import FrameWarpCache

def generate_lr_scene(
    scene: Scene,
    force: bool = False,
    verbose: bool = True,
    save_as_png: bool = False,
) -> bool:
    scene_key: str = f"{scene['dst']['k_ep']}:{scene['dst']['k_ch']}:{scene['no']}"
    out_video_fp: str = scene['task'].video_file

    if is_up_to_date(scene) and not force:
        return True

    # Specific to lr/sim: get input shape to set encoder vi
    in_video_fp: str = (
        scene['src']
        .primary_scene()
        .in_scene['inputs']
        .progressive()
        .filepath
    )
    in_vi: VideoInfo = extract_media_info_mco(in_video_fp)['video']
    in_h, in_w, c = in_vi['shape']


    # Encoder
    #-------------------------------------------------------------------------------------
    # Output video settings
    vsettings: VideoSettings = scene['task'].video_settings

    # Pipe and other values for subprocess
    out_w, out_h = in_w, in_h
    if vsettings.size is not None:
        out_w, out_h = vsettings.size
    e_pipe_dtype: np.dtype = np.uint8
    # (
    #     np.uint8
    #     if PIXEL_FORMAT[in_pipe_pixfmt]['bpp'] <= 8
    #     else np.uint16
    # )
    e_pixel_format: str = "bgr24" if e_pipe_dtype == np.uint8 else "bgr48"
    frame_rate: float = frame_rate_dec(vsettings.frame_rate)
    metadata: list[str] = ffmpeg_metadata(scene)

    to_produce: int = calculate_scene_frame_count(scene)

    # Output directory
    lr_directory: str = path_split(scene['task'].video_file)[0]
    os.makedirs(lr_directory, exist_ok=True)

    if verbose:
        print(lightcyan("Encoder:"))
        print(f"   to produce: {to_produce}")
        print("  pipe:")
        print(f"    dtype: {e_pipe_dtype}")
        print(f"    pixfmt: {e_pixel_format}")
        print(f"    size: {out_w}x{out_h}")


    if save_as_png:
        encoder: ImageWriter = ImageWriter(scene=scene, verbose=verbose)

    else:
        e_command: list[str] = [
            ffmpeg_exe,
            "-hide_banner",
            "-loglevel", "warning",
            "-nostats",

            "-f", "rawvideo",
            '-pixel_format', e_pixel_format,
            '-video_size', f"{out_w}x{out_h}",
            "-r", str(frame_rate),
            "-i", "pipe:0",

            "-pix_fmt", vsettings.pix_fmt,
            "-vcodec", str_to_video_codec[vsettings.codec].value,
            *vsettings.codec_options,
            *metadata,
            out_video_fp, "-y"
        ]
        if verbose:
            print(lightcyan(f"  e_command:"), " ".join(e_command))
        e_subprocess: subprocess.Popen = None
        try:
            e_subprocess = subprocess.Popen(
                e_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except Exception as e:
            print(red(f"[E][W] {scene_key} Unexpected error: {type(e)}"))
            return False

        encoder: Encoder = Encoder(
            scene=scene,
            e_subprocess=e_subprocess,
            verbose=verbose
        )
    encoder.start()


    # Decoder (common)
    #-------------------------------------------------------------------------------------

    # Resize to have the same resolution whatever the source
    dec_filter_complex: list[str] = []
    if out_w != in_w or out_h != in_h:
        in_w, in_h = out_w, out_h
        dec_filter_complex = [
            "-filter_complex",
            f"[0:v]scale={out_w}:{out_h}:sws_flags=bicubic+accurate_rnd+bitexact+full_chroma_int[outv]",
            "-map", "[outv]"
        ]

    # TODO change to rgb48 if sim_hr
    in_pipe_pixfmt = 'bgr24'
    img_shape = (in_h, in_w, c)
    img_dtype: np.dtype = np.uint8
    pipe_img_nbytes = math.prod(img_shape)
    frame_rate: float = frame_rate_dec(in_vi['frame_rate_r'])

    # A scene may use multiple segments from different scenes
    remaining_src_scenes = len(scene['src'].scenes())


    # Decode / Encode
    #-------------------------------------------------------------------------------------

    # Extract src scenes
    for src_index, src_scene in enumerate(scene['src'].scenes()):
        in_scene: Scene = src_scene.in_scene
        src_scene_inputs: Inputs = in_scene['inputs']
        in_video_fp: str = src_scene_inputs.progressive().filepath

        src_start, src_count = src_scene.start, src_scene.count
        if to_produce < src_count:
            src_count = to_produce

        # to_decode is used to count nb of frames to be decoded, passed to FFmpeg
        to_decode: int = src_scene.to_decode
        _to_decode: int = to_decode
        remaining = src_count
        src_end = src_start + to_decode

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
            if verbose:
                print("remove last frame")
            to_decode -= 1
            for i in range(src_scene.start + to_decode - 1, 1, -1):
                if not frame_cache.to_replace(i):
                    break
                to_decode -= 1
            _to_decode = to_decode


        if verbose:
            print(lightcyan("Decoder:"))
            print(f"  nb of src scenes: {remaining_src_scenes}")
            print(f"  to decode: {to_decode}")
            print(f"  to send to the encoder: {remaining}")

            print("  pipe:")
            print(f"    pixfmt: {in_pipe_pixfmt}")
            print(f"    shape: {img_shape}")
            print(f"    dtype: {img_dtype}")
            print(f"    nbytes: {pipe_img_nbytes}")


        # FFmpeg decoder command
        frame_rate: FrameRate = in_vi['frame_rate_r']
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
            *dec_filter_complex,
            "-f", "image2pipe",
            "-pix_fmt", in_pipe_pixfmt,
            "-vcodec", "rawvideo",
            "-"
        ]
        if verbose:
            print(lightcyan(f"  scene no. {scene['no']}"))
            print(f"    to decode: {to_decode}")
            print(f"    to process: {remaining}")

        if verbose:
            print(lightcyan(f"  d_command:"), " ".join(d_command))

        d_subprocess: subprocess.Popen = None
        try:
            d_subprocess = subprocess.Popen(
                d_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except Exception as e:
            print(red(f"[E][W] {scene_key} Unexpected error: {type(e)}"))
            return False

        # Dust and scratch removal
        scene_dsr: SceneDsr = in_scene['dsr']
        if scene_dsr is not None:
            scene_dsr.set_frame_size((in_w, in_h))

        # Verify not supported feature
        ch_video: ChapterVideo = get_target_video(scene)
        if is_first_scene(scene):
            print(lightcyan("first scene, avsync:"), ch_video['avsync'])
            if ch_video['avsync'] != 0:
                raise NotImplementedError("avsync not yet supported")

        # Wrap
        wrap_f_ref_no: int = -1
        frame_warp_cache: FrameWarpCache = FrameWarpCache()

        # Decode

        # decoder frame no.
        d_f_no: int = src_start
        f_index: int = 0
        f_in_index: int = 0

        # f_no is the frame no. to send to the encoder
        f_no: int = src_start

        # Number of src scenes to use
        remaining_src_scenes -= 1

        # decimate
        decimate_index: int = 0

        sent = 0

        # Loop until all frames have been sent to the encoder
        while remaining:

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
            # if f_no != d_f_no:
            print(lightcyan(f"  ({f_index}) waiting for {f_no}, _in_f_no: {_in_f_no}"))

            # if not cached, decode a new frame
            img_buffer: np.ndarray = None
            while f_no not in frame_cache:
                img_buffer: np.ndarray = np.frombuffer(
                    d_subprocess.stdout.read(pipe_img_nbytes),
                    dtype=np.uint8,
                )

                # Throw this frame away if replaced
                if frame_cache.to_replace(d_f_no):
                    print(f"      discard: {d_f_no}")
                    pass
                else:
                    # print(f"      add: {d_f_no}")
                    frame_cache.add(d_f_no, img_buffer)

                d_f_no += 1
                _to_decode -= 1

            # f_no is in cache
            if f_no in frame_cache:
                img_buffer = frame_cache[f_no]
            else:
                raise RuntimeError(f"missing frame: {f_no}")

            if remaining < 0 or img_buffer is None:
                raise ValueError(red("remaining < 0 or img_buffer is None"))

            img: np.ndarray = img_buffer.astype(img_dtype).reshape(img_shape)
            # print(f"{img.shape}, {img.dtype}")

            # Create a frame object
            frame: NnFrame = NnFrame(
                f_no=f_no,
                tensor=img,
                last=False,

                scene=scene,
                src_scene_index=src_index,
            )


            # Wrap frame
            print(f"\n{purple(f"f_no: ")} {f_no}")
            frames: list[NnFrame] = []
            if (
                'warp' in in_scene
                and f_no in in_scene['warp']
            ):
                warp: Warp = in_scene['warp'][f_no]
                if warp.enabled:
                    wrap_f_ref_no = f_no + 1
                    while wrap_f_ref_no in frame_cache.replacements.keys():
                        wrap_f_ref_no += 1
                    print(f"warp: {f_no}, ref frame: {wrap_f_ref_no}")
                    if wrap_f_ref_no in frame_warp_cache.cached:
                        print("already in cache, do wrap")
                        raise
                        wrap_f_ref_no = -1
                    else:
                        print(f".... request new frame, wait for {wrap_f_ref_no}")
                        frame_warp_cache.append(f_no, frame)
                        f_index += 1
                        continue
                    print(frame_warp_cache.cached)
                else:
                    wrap_f_ref_no = -1
                    print("warp is disabled")

            elif wrap_f_ref_no != -1:
                if wrap_f_ref_no in frame_warp_cache.cached:
                    raise ValueError("not supported)")
                    wrap_f_ref_no = -1

                if f_no == wrap_f_ref_no:
                    print(f"This frame is the reference, wrap every frame in cache until")
                    ref_frame = frame
                    while frame_warp_cache.cached:
                        pop_frame: NnFrame = frame_warp_cache.popleft()
                        if pop_frame.f_no in in_scene['warp']:
                            print(lightgreen(f"wrap {pop_frame.f_no} with ref {ref_frame.f_no}"))

                            pop_frame.tensor = warp_image(
                                img=pop_frame.tensor,
                                ref_img=ref_frame.tensor,
                                warp=in_scene['warp'][pop_frame.f_no]
                            )

                            frames.append(pop_frame)
                    frames.append(ref_frame)
                    f_index = f_index - len(frames) + 1
                    wrap_f_ref_no = -1
                    print(f"send {', '.join([f"{f.f_no}" for f in frames])}")
            else:
                frames = [frame]
            # print(frame_warp_cache.cached)


            for f in frames:
                # Tag it as last frame if no other src scene to decode
                # and this is the last frame of this src scene
                if remaining_src_scenes == 0 and remaining == 1:
                    # print(yellow(f"  Tag last frame: {frame.f_no}"))
                    f.last = True

                # Send to encoder...
                #-----------------------------------------------
                f_no = f.f_no
                print(lightcyan(f"{sent}:"), f"{f_no}", end="\n")
                encoder.put_frame(f)
                if verbose:
                    sent += 1

                # increment _in_f_no, because 'loop' frames have been sent to the encoder
                loop = get_loop_nframes(src_scene, f_no=f_no)
                if loop:
                    remaining -= loop
                    f_index += loop
                else:
                    remaining -= 1
                    f_index += 1

            # All frames of the scene have been decoded and sent to consumer
            # if _to_decode == 0:
            #     print(f"all frames to be decoded have been decoded ({to_decode})")

            # if remaining == 0:
            #     print(f"all frames have been sent to the encoder")
            # print(f"remaining: {remaining}")

        # remaining source no
        if verbose:
            print(yellow(f"  sent frames: {sent}"))
            print(yellow(f"  remaining src scenes: {remaining_src_scenes}"))
        if remaining_src_scenes == 0:
            break

    del frame_cache

    # Poison pill
    encoder.put_frame(None)

    if d_subprocess.poll() is None:
        print(yellow(f"to decode was higher than what has to be decoded {_to_decode}"))
        timeout: int = 10
        while d_subprocess.poll() is None and timeout:
            time.sleep(0.1)
            timeout -= 1
        if not timeout:
            print(f"    kill decoder")
            d_subprocess.kill()

    while encoder.is_alive():
        time.sleep(0.1)

    return True



class Encoder(Thread):
    def __init__(
        self,
        scene: Scene,
        e_subprocess: subprocess.Popen,
        verbose: bool,
    ):
        super().__init__(name="encoder")
        self.verbose: bool = verbose
        self.e_index: int = 0
        self.scene: Scene = scene
        self.e_subprocess: subprocess.Popen = e_subprocess
        self.watermark: bool = do_watermark(scene=scene)

        self._stop_event: Event = Event()
        self.in_queue: Queue = Queue(1)

    def put_frame(self, frame: NnFrame) -> bool:
        self.in_queue.put(frame)
        return True


    def run(self) -> None:
        in_queue: Queue = self.in_queue
        e_subprocess = self.e_subprocess
        verbose: bool = self.verbose

        while not self._stop_event.is_set():
            # Wait for a frame or a poison pill
            input = in_queue.get(block=True)
            if input is None or self._stop_event.is_set():
                if verbose:
                    print(purple("[V][E] Received Null tensor"))
                break

            frame: NnFrame = input

            # print(lightgreen(f"    ({self.e_index}) encode: {frame.f_no}, {frame.tensor.shape}, {frame.tensor.dtype}"))

            # effect are made on np.ndarray
            in_f_no: int = frame.f_no
            mco_frame = McoFrame(
                no=in_f_no,
                img=frame.tensor,
                scene=self.scene,
                src_scene_index=frame.src_scene_index,
            )

            # Watermark
            if self.watermark:
                out_img: np.ndarray = add_watermark(
                    frame=mco_frame,
                    no=in_f_no
                )
                mco_frame.img = out_img

            mco_frame.img = np_to_float32(mco_frame.img)


            # Apply upscale effects (loops)
            src_scene: SrcScene = frame.scene['src'].scenes()[frame.src_scene_index]
            out_f_no: int = src_scene.start + self.e_index
            out_frames = apply_upscale_effects(
                out_f_no=out_f_no,
                frame=mco_frame,
                out_i=self.e_index,
            )
            # print(f"upscale effects: {len(out_frames)}")

            # Convert to np.float
            for f in out_frames:
                f.img = np_to_float32(f.img)

            # Final effects: fades and specific to generic (overlay, title, blend)
            # print(f"encode: f_no. {out_f_no}, nb of frames: {len(out_frames)}")
            for out_frame in  out_frames:
                out_f_no: int = src_scene.start + self.e_index

                out_frame: McoFrame = apply_final_effects(
                    out_f_no=out_f_no,
                    frame=out_frame,
                    out_i=self.e_index
                )
                # for debug
                # if out_frames is None:
                #     self.e_subprocess.communicate(timeout=60)
                #     raise
                out_img = np_to_uint8(out_frame.img)
                e_subprocess.stdin.write(out_img)

                self.e_index += 1
                # print(f"sent {len(out_frames)} -> total = {self.e_index}")

                scene_shape = out_frame.img.shape
                # scene_dtype = out_frame.img.dtype

        # Final: Add silence
        scene = frame.scene
        if is_last_scene(frame.scene):
            ch_video: ChapterVideo = get_target_video(scene)
            if 'silence' in ch_video and ch_video['silence']:
                silence: int = ch_video['silence']
                img_black = np.zeros(scene_shape, dtype=np.uint8)
                [e_subprocess.stdin.write(img_black) for _ in range(silence)]
                self.e_index +=  silence
                if verbose:
                    print(purple(f"added silence: {silence}"))
        if verbose:
            print(purple(f"produced w/ silence: {self.e_index}"))


        stderr_bytes: bytes | None = None
        try:
            # Arbitrary timeout value
            _, stderr_bytes = e_subprocess.communicate(timeout=60)
        except:
            e_subprocess.kill()
            return False

        if stderr_bytes is not None:
            stderr = stderr_bytes.decode('utf-8)')
            # TODO: parse the output file
            if stderr != '':
                pprint(stderr)
                return False

        if verbose:
            print(purple(f"encoder: ended"))



class ImageWriter(Thread):
    def __init__(
        self,
        scene: Scene,
        verbose: bool,
    ):
        super().__init__(name="image_writer")
        self.verbose: bool = verbose
        self.scene: Scene = scene
        self._stop_event: Event = Event()
        self.in_queue: Queue = Queue(1)

        # Output folder
        k_ed, k_ep = scene['src'].primary_scene().k_ed_ep_ch_no[:2]
        self.img_directory = os.path.join(
            os.sep.join(scene['cache'].split(os.sep)[:-3]),
            "imgs",
            f"{k_ep}_{scene['no']:03}_{scene['task'].name}_{k_ed}"
        )
        os.makedirs(self.img_directory, exist_ok=True)

    def put_frame(self, frame: NnFrame) -> bool:
        self.in_queue.put(frame)
        return True


    def run(self) -> None:
        in_queue: Queue = self.in_queue
        verbose: bool = self.verbose

        e_index: int = 0
        while not self._stop_event.is_set():
            # Wait for a frame or a poison pill
            input = in_queue.get(block=True)
            if input is None or self._stop_event.is_set():
                if verbose:
                    print(purple("[V][E] Received Null tensor"))
                break

            frame: NnFrame = input

            print(lightgreen(f"    ({e_index}) write: {frame.f_no}, {frame.tensor.shape}, {frame.tensor.dtype}"))

            # effect are made on np.ndarray
            in_f_no: int = frame.f_no
            mco_frame = McoFrame(
                no=in_f_no,
                img=np_to_float32(frame.tensor),
                scene=self.scene,
                src_scene_index=frame.src_scene_index,
            )

            # Apply upscale effects (loops)
            src_scene: SrcScene = frame.scene['src'].scenes()[frame.src_scene_index]
            out_f_no: int = src_scene.start + e_index
            out_frames = apply_upscale_effects(
                out_f_no=out_f_no,
                frame=mco_frame,
                out_i=e_index,
            )
            # print(f"upscale effects: {len(out_frames)}")

            # Convert to np.float
            for f in out_frames:
                f.img = np_to_float32(f.img)

            # Final effects: fades and specific to generic (overlay, title, blend)
            # print(f"encode: f_no. {out_f_no}, nb of frames: {len(out_frames)}")
            for out_frame in out_frames:
                img_fp: str = os.path.join(self.img_directory, f"{e_index:03}.png")
                print(f"   write: {e_index}: {out_frame.img.shape} as {img_fp}")
                write_image(img_fp, out_frame.img)
                e_index += 1

