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
)
from processing.dsr import generate_dsr_mask
from processing.effects import apply_effect
from processing.frame_cache import FrameCache
from processing.watermark import add_watermark
from scene.filters import do_watermark
from scene.src_scene import SrcScene
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
from utils.np_dtypes import np_to_float32
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

        to_decode: int = src_count

        # Patch the input scene so that the encoder receive the correct frame no.
        # TODO: verify that this will not impact the other scene when using the
        # same src
        if (
            src_scene.in_scene['start'] != src_start
            or src_scene.in_scene['count'] != src_count
        ):
            raise ValueError(red("input scene has been patched"))
        src_scene.in_scene['start'] = src_start
        src_scene.in_scene['count'] = src_count

        # Decimate
        factor: int = 0
        factor_2_mod: int = 0
        if 'effects' in in_scene:
            if e := in_scene['effects'].get_effect('decimate'):
                factor, _ = e.extra_param
                print(yellow(f"  decimate:"), f"{in_scene['no']}: {src_count}")
                # to_decode = int(src_count * factor / (factor - 1) )

            elif e := in_scene['effects'].get_effect('decimate_2'):
                factor, factor_2_mod = e.extra_param
                # to_decode = int(factor_2_mod * src_count * factor / (factor - 1))
                print(yellow(f"  decimate_2:"), f"{in_scene['no']}: {factor_2_mod}")
                pprint(in_scene)

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
        print(f"    replacements:")
        pprint(frame_cache.replacements)

        # Replace a segment by a loop
        replace_by_loop: bool = False
        if (
            'effects' in in_scene
            and in_scene['effects'].has_effect(name='replace_by_loop')
        ):
            replace_by_loop = True
            for loop in in_scene['effects'].get_effects(name='replace_by_loop'):
                frame_cache.add_loop_segment(
                    (loop.start, loop.loop, loop.f_ref)
                )
            print(f"    loops:")
            pprint(frame_cache.segments)

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

        while (
            to_decode
            and remaining > 0
        ):
            _in_f_no = src_start + f_index
            if _in_f_no >= src_start + src_count:
                print("BREAAAAAAK but why?")
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

                # Throw this frame away if replaced
                if frame_cache.to_replace(d_f_no):
                    print(f"      discard: {d_f_no}")
                else:
                    # print(f"      add: {d_f_no}")
                    frame_cache.add(d_f_no, img_buffer)


                d_f_no += 1
                to_decode -= 1

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
                print(yellow(f"  Tag last frame: {frame.f_no}"))
                frame.last = True


            # Send to encoder...
            #-----------------------------------------------

            encoder.encode_frame(frame)

            #-----------------------------------------------

            # back to decoder
            # increment _in_f_no, because 'loop' frames have been sent to the encoder
            loop = get_frameloop(src_scene, f_no=f_no)
            inc = 0 if not loop else loop - 1

            remaining -= 1 + inc
            f_index += 1 + inc

            # All frames of the scene have been decoded and sent to consumer
            if to_produce == 0:
                print("all frames to be decoded have been decoded")
                # break

        # remaining source no
        print(yellow(f"  remaining src scenes: {remaining_src_scenes}"))
        if remaining_src_scenes == 0:
            break


        # raise
        # # in_f_no is incremented before reading in pipe
        # d_virtual_f_no: int = src_start
        # f_index: int = 0
        # f_no: int = d_virtual_f_no
        # d_f_no: int = d_virtual_f_no
        # decoded: int = 0

        # out_f_no: int = src_start

        # in_frame: McoFrame = None
        # out_frame: McoFrame = None
        # out_i: int = 0

        # # backward
        # backward_imgs: deque = deque()

        # # decimate
        # decimate_index: int = 0
        # decimate_index2: int = 0
        # while (
        #     decoded < src_count
        #     and remaining > 0
        # ):

        #     in_frame: McoFrame = None
        #     while in_frame is None:
        #         d_virtual_f_no += 1
        #         img: np.ndarray = np.frombuffer(
        #             d_subprocess.stdout.read(in_pipe_img_nbytes),
        #             dtype=img_dtype,
        #         ).reshape(img_shape)

        #         # if replace_by_loop:
        #         #     for l in loops:



        #         if d_virtual_f_no not in frames_to_replace:
        #             # print(purple(f"Read frame no.{in_f_no}"))
        #             mask_img: np.ndarray = generate_dsr_mask(
        #                 scene=src_scene,
        #                 frame_no=d_virtual_f_no,
        #                 shape=img.shape,
        #             )
        #             if mask_img is not None:
        #                 # start_time = time.time()
        #                 radius: int = 5
        #                 img = cv2.inpaint(
        #                     img,
        #                     inpaintMask=mask_img,
        #                     inpaintRadius=radius,
        #                     flags=cv2.INPAINT_TELEA
        #                 )
        #                 # print(f"elapsed: {(time.time() - start_time) * 1000:.01f}ms")
        #                 # write_image(f"mask_{in_f_no:04}_in.png", img)
        #                 # write_image(f"mask_{in_f_no:04}_out.png", out_img)
        #             in_frame: McoFrame = McoFrame(
        #                 no=d_virtual_f_no, img=img, scene=scene
        #             )

        #     # decimate
        #     decimate_index += 1
        #     if factor != 0 and (decimate_index % factor) == 0:
        #         decimate_index = 0
        #         out_f_no += 1
        #         continue
        #     if factor_2_mod:
        #         decimate_index2 = (decimate_index2 + 1) % factor_2_mod
        #         if decimate_index2:
        #             out_f_no += 1
        #             continue

        #     out_frame = None
        #     frame_cache.add(d_virtual_f_no, in_frame)
        #     while True:
        #         f_no = frame_replace[out_f_no] if out_f_no in frame_replace else out_f_no
        #         out_frame = None

        #         from_cache = False
        #         if f_no == d_virtual_f_no:
        #             out_frame = in_frame

        #         elif f_no in frame_cache:
        #             out_frame = frame_cache[f_no]
        #             from_cache = True

        #         if out_frame is not None:

        #             if watermark:
        #                 out_frame.img = add_watermark(
        #                     frame=out_frame,
        #                     no=out_frame.no
        #                 )

        #             out_frames = apply_effect(out_f_no, out_frame, out_i)
        #             if isinstance(out_frames, list):
        #                 print(yellow(f"\t{out_i}: send {len(out_frames)}"))
        #                 if src['backward']:
        #                     for f in out_frames:
        #                         backward_imgs.append(f.img)
        #                 else:
        #                     for f in out_frames:
        #                         # print(lightcyan(f.img.shape))
        #                         e_subprocess.stdin.write(f.img)

        #                 produced += len(out_frames)
        #                 out_i += len(out_frames)

        #             else:
        #                 out_frame = out_frames
        #                 # print(yellow(f"\t{out_i}: send {out_frame.no} (from {'cache' if from_cache else 'producer'})"))
        #                 if src['backward']:
        #                     backward_imgs.append(out_frame.img)
        #                 else:
        #                     # print(lightcyan(out_frame.img.shape))
        #                     e_subprocess.stdin.write(out_frame.img)
        #                 produced += 1
        #                 out_i += 1

        #             out_f_no += 1
        #             src_count -= 1
        #         else:
        #             break

        # del frame_cache
        # if backward_imgs:
        #     src_count = len(backward_imgs)
        #     for _ in range(src_count):
        #         e_subprocess.stdin.write(backward_imgs.pop())

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

        print(lightgreen(f"    ({self.e_index}) encode: {frame.f_no}"))


        mco_frame = McoFrame(
            no=frame.f_no,
            img=frame.tensor,
            scene=self.scene
        )
        f_no: int = frame.f_no

        # Effects only on np.ndarray
        if self.watermark:
            out_img: np.ndarray = add_watermark(
                frame=mco_frame,
                no=frame.f_no
            )

        out_imgs = [out_img]

        src_scene: SrcScene = frame.scene['src'].scenes()[frame.src_scene_index]
        loop = get_frameloop(src_scene, f_no=f_no)
        if loop:
            out_imgs = [out_img] * loop

        [self.e_subprocess.stdin.write(img) for img in out_imgs]
        self.e_index += len(out_imgs)
        print(f"sent {len(out_imgs)} -> total = {self.e_index}")



def get_frameloop(src_scene: SrcScene, f_no: int) -> int:
    loop: int = 0
    in_scene: Scene = src_scene.in_scene
    e: Effect
    for e in in_scene['effects'].get_effects('replace_by_loop'):
        if f_no == e.f_ref:
            loop = e.loop + 1
            # decrease loop if start of src is higher than start of loop
            if src_scene.start > e.start:
                loop -= src_scene.start - e.start
                raise ValueError(red("validate loop start < src start"))

            # decrease loop if end of src is lower than end of loop
            elif (e.start + e.loop)  > (src_scene.start + src_scene.count):
                loop -= (
                    (e.start + e.loop)
                    - (src_scene.start + src_scene.count)
                )
                raise ValueError(red("validate loop (start+loop) is > end of source"))
    return loop
