from collections import deque
import math
import os
from pprint import pprint
import subprocess
import sys
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
    DsrRegion,
    get_frame_rate,
    Effect,
    get_loop_nframes,
)
from parsers._helpers import get_chapter_video
from processing.dsr import generate_dsr_mask
from processing.effects import apply_final_effects, apply_upscale_effects
from processing.frame_cache import FrameCache
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
from utils.time_conversions import FrameRate, frame_to_s, frame_to_sexagesimal, ms_to_frame
from utils.tools import ffmpeg_exe
from utils.media import (
    VideoInfo, extract_media_info_mco, frame_rate_dec, str_to_video_codec
)


def generate_lr_scene(
    scene: Scene,
    force: bool = False,
    verbose: bool = False
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
    )


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

    if verbose:
        print(lightcyan("Decoder:"))
        print(f"  nb of src scenes: {remaining_src_scenes}")
        print(f"  to produce: {to_produce}")

        print("  pipe:")
        print(f"    pixfmt: {in_pipe_pixfmt}")
        print(f"    shape: {img_shape}")
        print(f"    dtype: {img_dtype}")
        print(f"    nbytes: {pipe_img_nbytes}")


    # Decode / Encode
    #-------------------------------------------------------------------------------------
    remaining: int = to_produce
    produced: int = 0

    # Extract src scenes
    for src_index, src_scene in enumerate(scene['src'].scenes()):
        in_scene: Scene = src_scene.in_scene
        src_scene_inputs: Inputs = in_scene['inputs']
        in_video_fp: str = src_scene_inputs.progressive().filepath

        src_start, src_count = src_scene.start, src_scene.count
        if to_produce < src_count:
            src_count = to_produce

        to_decode: int = src_scene.to_decode
        _to_decode: int = to_decode

        # TODO ensure to_decode is consistent for all scenes
        if to_decode != src_count:
            if (
                'effects' not in in_scene
                or (
                    not in_scene['effects'].has_effect('decimate')
                    and not in_scene['effects'].has_effect('decimate')
                )
            ):
                pprint(src_scene)
                raise ValueError(red(f"to decode ({to_decode}) != src.count ({src_count})"))


        # Decimate
        factor_mod1: int = 0
        factor_mod2: int = 0
        if 'effects' in in_scene:
            if e := in_scene['effects'].get_effect('decimate'):
                factor_mod1, _ = e.extra_param
                # factor_mod1 += 1
                print(yellow(f"  decimate:"), f"{in_scene['no']}: {to_decode} -> {src_count} (mod={factor_mod1})")
                # print(int(to_decode * / (factor_mod1 - 1)))
                # pprint(src_scene)
                # # pprint(in_scene)
                # print(to_decode)
                # raise

            elif e := in_scene['effects'].get_effect('decimate_2'):
                factor_mod1, factor_mod2 = e.extra_param
                # to_decode = int(factor_2_mod * src_count * factor / (factor - 1))
                print(yellow(f"  decimate_2:"), f"{in_scene['no']}: {factor_mod2}")
                # pprint(in_scene)
                # raise


        # FFmpeg command
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
        print(lightcyan(f"  scene no. {scene['no']}"))
        print(f"    to extract: {to_decode}")
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

        # Frame replacement
        src_f_replace = in_scene['replace']
        frame_cache: FrameCache = FrameCache(verbose=False)
        frame_cache.set_replaced_frames(src_f_replace)
        # print(f"    replacements:")
        # pprint(frame_cache.replacements)

        # Replace a segment by a loop
        if (
            'effects' in in_scene
            and in_scene['effects'].has_effect(name='replace_by_loop')
        ):
            for loop in in_scene['effects'].get_effects(name='replace_by_loop'):
                frame_cache.add_loop_segment(
                    (loop.start, loop.loop, loop.f_ref)
                )
            # print(f"    loops:")
            # pprint(frame_cache.segments)

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

        # Decode


        # decoder frame no.
        d_f_no: int = src_start
        f_index: int = 0

        # f_no is the frame no. to send to the encoder
        f_no: int = src_start

        # Number of src scenes to use
        remaining_src_scenes -= 1

        # decimate
        decimate_index: int = 0
        decimate_index2: int = 0

        while (
            _to_decode
            and remaining > 0
        ):
            _in_f_no = src_start + f_index
            if _in_f_no >= src_start + to_decode:
                break


            # decimate
            if factor_mod1:
                # print(f"decimate index: {decimate_index} % {factor_mod1} -> {decimate_index // factor_mod1}")
                decimate_index += 1
                if decimate_index // factor_mod1 == 1:
                    decimate_index = 0
                    # print(f"  discard {_in_f_no}")
                    f_index += 1
                    _in_f_no = src_start + f_index
                    if _in_f_no >= src_start + to_decode:
                        break

            # Get frame_no to send to the consumer
            f_no = frame_cache.get_out_f_no(_in_f_no)
            # if f_no != d_f_no:
            # print(lightcyan(f"  ({f_index}) decoded: {d_f_no}, _in_f_no: {_in_f_no}, waiting for {f_no}"))


            # if not cached, decode a new frame
            img_buffer: np.ndarray = None
            while f_no not in frame_cache:
                img_buffer: np.ndarray = np.frombuffer(
                    d_subprocess.stdout.read(pipe_img_nbytes),
                    dtype=np.uint8,
                )

                # if factor_mod2:
                #     decimate_index2 = (decimate_index2 + 1) % factor_mod2
                #     if decimate_index2:
                #         d_f_no += 1
                #         src_remaining_to_decode -= 1
                #         continue

                # Throw this frame away if replaced
                if frame_cache.to_replace(d_f_no):
                    # print(f"      discard: {d_f_no}")
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

            # Create a frame object
            frame: NnFrame = NnFrame(
                f_no=f_no,
                tensor=img,
                last=False,

                scene=scene,
                src_scene_index=src_index,
            )

            # Tag it as last frame if no other src scene to decode
            # and this is the last frame of this src scene
            if remaining_src_scenes == 0 and remaining == 1:
                # print(yellow(f"  Tag last frame: {frame.f_no}"))
                frame.last = True


            # Send to encoder...
            #-----------------------------------------------

            encoder.encode_frame(frame)

            #-----------------------------------------------

            # back to decoder
            # increment _in_f_no, because 'loop' frames have been sent to the encoder
            loop = get_loop_nframes(src_scene, f_no=f_no)
            if loop:
                remaining -= loop
                f_index += loop
            else:
                remaining -= 1
                f_index += 1

            # All frames of the scene have been decoded and sent to consumer
            if to_produce == 0:
                print("all frames to be decoded have been decoded")
                # break

        # remaining source no
        if verbose:
            print(yellow(f"  remaining src scenes: {remaining_src_scenes}"))
        if remaining_src_scenes == 0:
            break





    main_logger.info(f"produced: {produced}")
    if is_last_scene(scene):
        if 'silence' in ch_video and ch_video['silence']:
            silence: int = ch_video['silence']
            img_black = np.zeros(img_shape, dtype=e_pipe_dtype)
            [e_subprocess.stdin.write(img_black) for _ in range(silence)]
            produced += silence
            print(f"produced w/ silence: {produced}")


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
            print(f"{scene_key} stderr:")
            pprint(stderr)
            return False
    return True



class Encoder:
    def __init__(
        self,
        scene: Scene,
        e_subprocess: subprocess.Popen,
    ):
        self.e_index: int = 0
        self.scene: Scene = scene
        self.e_subprocess: subprocess.Popen = e_subprocess
        self.watermark: bool = do_watermark(scene=scene)


    def encode_frame(self, frame: NnFrame) -> None:
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

            self.e_subprocess.stdin.write(np_to_uint8(out_frame.img))

            self.e_index += 1
            # print(f"sent {len(out_frames)} -> total = {self.e_index}")

