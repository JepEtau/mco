from collections import deque
import math
import os
from pprint import pprint
import subprocess
import sys
import cv2
import numpy as np
import time
from parsers import (
    db,
    VideoSettings,
    SceneDsr,
    DsrRegion,
)
from processing.dsr import generate_dsr_mask
from processing.effects import apply_effect
from processing.frame_replace import (
    ItemCache, frame_occurences, get_frames_to_remove
)
from processing.watermark import add_watermark
from scene.filters import do_watermark
from utils.images_io import write_image
from utils.logger import main_logger
from utils.mco_types import ChapterVideo, McoFrame, Scene
from utils.mco_utils import (
    ffmpeg_metadata,
    get_target_video,
    is_first_scene,
    is_last_scene,
    is_up_to_date
)
from utils.np_dtypes import np_to_float32
from utils.p_print import *
from utils.path_utils import path_split
from utils.pxl_fmt import PIXEL_FORMAT
from utils.time_conversions import frame_to_s, frame_to_sexagesimal
from utils.tools import ffmpeg_exe
from utils.media import (
    VideoInfo, extract_media_info_mco, frame_rate_dec, str_to_video_codec
)



def generate_lr_scene(scene: Scene, force: bool = False) -> bool:
    scene_key: str = f"{scene['dst']['k_ep']}:{scene['dst']['k_ch']}:{scene['no']}"
    out_video_fp: str = scene['task'].video_file

    if is_up_to_date(scene) and not force:
        return True

    # Output directory
    lr_directory: str = path_split(scene['task'].video_file)[0]
    os.makedirs(lr_directory, exist_ok=True)

    # Pipe out video file
    in_video_fp: str = (
        scene['src']
        .primary_scene()['scene']['inputs']
        .progressive()
        .filepath
    )
    in_vi: VideoInfo = extract_media_info_mco(in_video_fp)['video']
    in_pipe_pixfmt = 'bgr24'
    out_pipe_dtype = (
        np.uint8
        if PIXEL_FORMAT[in_pipe_pixfmt]['bpp'] <= 8
        else np.uint16
    )

    # Force to the same height to be able to mix different editions when in sim
    # otherwise upscale 2x when in lr
    # consider that all src scenes have the same dimension
    enc_filter_complex: list[str] = []
    dec_filter_complex: list[str] = []
    in_video_shape = in_vi['shape']
    in_h, in_w, in_c = in_video_shape
    if scene['task'].name in ('lr', 'sim'):
        print(lightcyan("low resolution / sim, use same size"))
        if scene['task'].name == 'lr':
            in_h, in_w = 540, 720
        else:
            in_h, in_w = 1080, 1440
        dec_filter_complex = [
            "-filter_complex",
            f"[0:v]scale={in_w}:{in_h}:sws_flags=bicubic+accurate_rnd+bitexact+full_chroma_int[outv]",
            "-map", "[outv]"
        ]
        in_video_shape = (in_h, in_w, in_c)

    # else:
    #     if h != 576 or w != 576:
    #         filter_complex = [
    #             "-filter_complex",
    #             f"[0:v]scale=768:576:sws_flags=bicubic+accurate_rnd+bitexact+full_chroma_int[outv]",
    #             "-map", "[outv]"
    #         ]
    out_video_shape = in_video_shape
    out_h, out_w = out_video_shape[:2]

    # Consider that all src scene have the same dimension
    in_pipe_pixfmt = 'bgr24'
    in_pipe_dtype = np.uint8
    in_pipe_img_nbytes = math.prod(in_video_shape)
    in_pipe_img_shape: tuple[int, int, int] = in_video_shape
    frame_rate: float = frame_rate_dec(in_vi['frame_rate_r'])

    # Encoder subprocess
    vsettings: VideoSettings = scene['task'].video_settings
    metadata: list[str] = ffmpeg_metadata(scene)
    encoder_command: list[str] = [
        ffmpeg_exe,
        "-hide_banner",
        "-loglevel", "warning",
        "-nostats",

        "-f", "rawvideo",
        '-pixel_format', in_pipe_pixfmt,
        '-video_size', f"{out_w}x{out_h}",
        "-r", str(frame_rate),
        "-i", "pipe:0",

        *enc_filter_complex,

        "-pix_fmt", vsettings.pix_fmt,
        "-vcodec", str_to_video_codec[vsettings.codec].value,
        *vsettings.codec_options,
        *metadata,
        out_video_fp, "-y"
    ]
    print(lightcyan(f"Encoder:"), " ".join(encoder_command))
    encoder_subprocess: subprocess.Popen = None
    try:
        encoder_subprocess = subprocess.Popen(
            encoder_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except Exception as e:
        print(red(f"[E][W] {scene_key} Unexpected error: {type(e)}"))
        return False

    produced: int = 0
    to_produce: int = scene['dst']['count']
    watermark: bool = do_watermark(scene=scene)

    print(lightcyan("chapter effects:"))
    # pprint(db[scene['dst']['k_ep']]['video']['target'][scene['dst']['k_ch']]['effects'])

    # Extract src scenes
    for src in scene['src'].scenes():
        src_scene: Scene = src['scene']
        in_video_fp: str = src_scene['inputs'].progressive().filepath
        start: int = src['start']
        count: int = src['count']
        if to_produce < count:
            count = to_produce
        # print(f"extract {count} frames")
        to_produce -= count

        decoder_command: list[str] = [
            ffmpeg_exe,
            "-hide_banner",
            "-loglevel", "warning",
            "-nostats",
            "-ss",
            str(
                frame_to_sexagesimal(
                    no=start - src_scene['inputs'].progressive().start,
                    frame_rate=frame_rate
                )
            ),
            "-i", in_video_fp,
            "-t", str(frame_to_s(no=count, frame_rate=frame_rate)),
            *dec_filter_complex,
            "-f", "image2pipe",
            "-pix_fmt", in_pipe_pixfmt,
            "-vcodec", "rawvideo",
            "-"
        ]
        print(lightcyan(f"Decoder:"), " ".join(decoder_command))
        decoder_subprocess: subprocess.Popen = None
        try:
            decoder_subprocess = subprocess.Popen(
                decoder_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except Exception as e:
            print(red(f"[E][W] {scene_key} Unexpected error: {type(e)}"))
            return False

        # print(" ".join(decoder_command))

        # Replacements
        frame_replace = src_scene['replace']
        frames_to_replace: list[int] = get_frames_to_remove(frame_replace)
        frame_cache: ItemCache = ItemCache()
        frame_cache.set_occurences(frame_occurences(frame_replace))
        frame_cache.set_exceptions(frames_to_replace)

        # Dust and scratch removal
        scene_dsr: SceneDsr = src_scene['dsr']
        if scene_dsr is not None:
            scene_dsr.set_frame_size((in_w, in_h))
        # scene_dsr.set_frame_size((1440, 1080))

        ch_video: ChapterVideo = get_target_video(scene)
        if is_first_scene(scene):
            print(lightcyan("first scene, avsync:"), ch_video['avsync'])
            if ch_video['avsync'] != 0:
                raise NotImplementedError("avsync not yet supported")

        in_f_no: int = start - 1
        out_f_no: int = start

        in_frame: McoFrame = None
        out_frame: McoFrame = None
        out_i: int = 0
        backward_imgs: deque = deque()
        while count:

            in_frame: McoFrame = None
            while in_frame is None:
                in_f_no += 1
                img: np.ndarray = np.frombuffer(
                    decoder_subprocess.stdout.read(in_pipe_img_nbytes),
                    dtype=in_pipe_dtype,
                ).reshape(in_pipe_img_shape)
                if in_f_no not in frames_to_replace:
                    # print(purple(f"Read frame no.{in_f_no}"))
                    mask_img: np.ndarray = generate_dsr_mask(
                        scene=src_scene,
                        frame_no=in_f_no,
                        shape=img.shape,
                    )
                    if mask_img is not None:
                        # start_time = time.time()
                        radius: int = 5
                        img = cv2.inpaint(
                            img,
                            inpaintMask=mask_img,
                            inpaintRadius=radius,
                            flags=cv2.INPAINT_TELEA
                        )
                        # print(f"elapsed: {(time.time() - start_time) * 1000:.01f}ms")
                        # write_image(f"mask_{in_f_no:04}_in.png", img)
                        # write_image(f"mask_{in_f_no:04}_out.png", out_img)
                    in_frame: McoFrame = McoFrame(
                        no=in_f_no, img=img, scene=scene
                    )

            out_frame = None
            while True:
                f_no = frame_replace[out_f_no] if out_f_no in frame_replace else out_f_no
                out_frame = None

                from_cache = False

                if f_no == in_f_no:
                    out_frame = in_frame

                elif f_no in frame_cache:
                    out_frame = frame_cache[f_no]
                    from_cache = True

                elif in_f_no not in frame_cache:
                    frame_cache.add(in_f_no, in_frame)

                if out_frame is not None:

                    if watermark:
                        out_frame.img = add_watermark(
                            frame=out_frame,
                            no=out_frame.no
                        )

                    out_frames = apply_effect(out_f_no, out_frame, out_i)
                    if isinstance(out_frames, list):
                        print(yellow(f"\t{out_i}: send {len(out_frames)}"))
                        if src['backward']:
                            for f in out_frames:
                                backward_imgs.append(f.img)
                        else:
                            for f in out_frames:
                                # print(lightcyan(f.img.shape))
                                encoder_subprocess.stdin.write(f.img)

                        produced += len(out_frames)
                        out_i += len(out_frames)

                    else:
                        out_frame = out_frames
                        # print(yellow(f"\t{out_i}: send {out_frame.no} (from {'cache' if from_cache else 'producer'})"))
                        if src['backward']:
                            backward_imgs.append(out_frame.img)
                        else:
                            # print(lightcyan(out_frame.img.shape))
                            encoder_subprocess.stdin.write(out_frame.img)
                        produced += 1
                        out_i += 1

                    out_f_no += 1
                    count -= 1
                else:
                    break

        del frame_cache
        if backward_imgs:
            count = len(backward_imgs)
            for _ in range(count):
                encoder_subprocess.stdin.write(backward_imgs.pop())

    main_logger.info(f"produced: {produced}")
    if is_last_scene(scene):
        if 'silence' in ch_video and ch_video['silence']:
            print(f"silence!!! {ch_video['silence']}")
            img_black = np.zeros(in_video_shape, dtype=out_pipe_dtype)
            [encoder_subprocess.stdin.write(img_black) for _ in range(ch_video['silence'])]

            produced += ch_video['silence']
            print(f"produced w/ silence: {produced}")


    stderr_bytes: bytes | None = None
    try:
        # Arbitrary timeout value
        _, stderr_bytes = encoder_subprocess.communicate(timeout=10)
    except:
        encoder_subprocess.kill()
        return False

    if stderr_bytes is not None:
        stderr = stderr_bytes.decode('utf-8)')
        # TODO: parse the output file
        if stderr != '':
            print(f"{scene_key} stderr:")
            pprint(stderr)
            return False
    return True

