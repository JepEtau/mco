from collections import deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import math
import multiprocessing
import os
from pprint import pprint
import subprocess
import sys

import numpy as np
from parsers import (
    db,
    get_fps,
    task_to_dirname,
    VideoSettings,
)
from processing.effects import effect_fadeout, effect_loop_and_fadeout
from processing.frame_replace import ItemCache, frame_occurences, get_frames_to_cache, get_frames_to_remove
from processing.watermark import add_watermark
from scene.filters import do_watermark
from scene.src_scene import SrcScene
from utils.images import IMG_FILENAME_TEMPLATE, Image, Images
from utils.images_io import load_image
from utils.logger import main_logger
from utils.mco_types import Effect, Scene
from utils.mco_utils import get_cache_path, get_dirname, run_simple_command
from utils.p_print import *
from utils.path_utils import path_split
from utils.time_conversions import FrameRate, frame_to_s, frame_to_sexagesimal
from utils.tools import ffmpeg_exe
from video.out_frames import get_out_frame_paths
from utils.media import VideoInfo, extract_media_info, str_to_video_codec


def generate_lr_scene(scene: Scene, force: bool = False) -> bool:
    scene_key: str = f"{scene['dst']['k_ep']}:{scene['dst']['k_ch']}:{scene['no']}"

    for s in scene['src'].scenes():
        in_video_fp: str = s['scene']['inputs']['progressive']['filepath']
        if not os.path.exists(in_video_fp):
            raise FileExistsError(red(f"Missing input file: {in_video_fp}"))

    out_video_fp: str = scene['task'].video_file
    if not force:
        if os.path.exists(out_video_fp):
            try:
                out_video_info: VideoInfo = extract_media_info(out_video_fp)['video']
                if out_video_info['frame_count'] == scene['dst']['count']:
                    return True
            except:
                pass

    task_name: str = scene['task'].name

    # Output directory
    lr_directory: str = path_split(scene['task'].video_file)[0]
    os.makedirs(lr_directory, exist_ok=True)

    # Out video clip
    in_video_fp = scene['src'].primary_scene()['scene']['inputs']['progressive']['filepath']
    video_info: VideoInfo = extract_media_info(in_video_fp)['video']
    h, w, c = video_info['shape']
    pipe_pixfmt = 'bgr24'

    frame_rate: FrameRate = get_fps(db)
    vsettings: VideoSettings = scene['task'].video_settings
    writer_command: list[str] = [
        ffmpeg_exe,
        "-hide_banner",
        "-loglevel", "warning",
        "-nostats",

        "-f", "rawvideo",
        '-pixel_format', pipe_pixfmt,
        '-video_size', f"{w}x{h}",
        "-r", str(frame_rate),
        "-i", "pipe:0",

        # *filter_complex,

        "-pix_fmt", vsettings.pix_fmt,
        "-vcodec", str_to_video_codec[vsettings.codec].value,
        *vsettings.codec_options,
        out_video_fp, "-y"
    ]
    writer_subproces: subprocess.Popen = None
    try:
        writer_subproces = subprocess.Popen(
            writer_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except Exception as e:
        print(red(f"[E][W] {scene_key} Unexpected error: {type(e)}"))
        return False


    for src in scene['src'].scenes():
        src_scene: Scene = src['scene']
        in_video_fp: str = src_scene['inputs']['progressive']['filepath']
        start: int = src['start']
        count: int = src['count']


        xtract_command: list[str] = [
            ffmpeg_exe,
            "-hide_banner",
            "-loglevel", "warning",
            "-nostats",
            "-ss", str(frame_to_sexagesimal(no=start, frame_rate=frame_rate)),
            "-i", in_video_fp,
            "-t", str(frame_to_s(no=count, frame_rate=frame_rate))
        ]
        video_info: VideoInfo = extract_media_info(in_video_fp)['video']
        h, w, c = video_info['shape']
        pipe_pixfmt = 'bgr24'
        in_frame_nbytes = math.prod(video_info['shape'])
        xtract_command.extend([
            "-f", "image2pipe",
            "-pix_fmt", pipe_pixfmt,
            "-vcodec", "rawvideo",
            "-"
        ])

        reader_subproces: subprocess.Popen = None
        try:
            reader_subproces = subprocess.Popen(
                xtract_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except Exception as e:
            print(red(f"[E][W] {scene_key} Unexpected error: {type(e)}"))
            return False


        def _read_frame() -> np.ndarray:
            frame = reader_subproces.stdout.read(in_frame_nbytes)
            if len(frame) < in_frame_nbytes:
                raise ValueError(red(f"[E][R] {scene_key} Unexpected error: frame size < {in_frame_nbytes}"))
            return frame

        # Replacements
        frame_replace = src_scene['replace']
        frames_to_replace: list[int] = get_frames_to_remove(frame_replace)
        frames_to_cache: deque[int] = get_frames_to_cache(frame_replace)
        frame_cache: ItemCache = ItemCache()
        frame_cache.set_occurences(frame_occurences(frame_replace))
        frame_cache.set_exceptions(frames_to_replace)

        if len(frames_to_cache):
            f_no_to_cache: int = frames_to_cache.popleft()
            f_no_to_replace: int = frames_to_replace[0]
            ftr_no: int = 1
        else:
            f_no_to_cache: int = -1
            f_no_to_replace: int = -1
            ftr_no: int = 0


        _out_f_nos: list[int] = []

        to_produce: int = count
        from_cache: bool = False
        print(lightcyan(f"Frames to produce: {to_produce}"))
        pprint(frames_to_replace)

        @dataclass(slots=True)
        class Frame:
            no: int
            img: np.ndarray

        in_f_no: int = start - 1
        out_f_no: int = start
        frame: Frame

        in_frame: Frame = None
        out_frame: Frame = None
        out_i: int = 0
        while to_produce:

            in_frame: Frame = None
            while in_frame is None:
                in_f_no += 1
                img: np.ndarray = _read_frame()
                if in_f_no not in frames_to_replace:
                    print(purple(f"Read frame no.{in_f_no}"))
                    in_frame: Frame = Frame(no=in_f_no, img=img)

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
                    print(yellow(f"\t{out_i}: send {out_frame.no} (from {'cache' if from_cache else 'producer'})"))
                    writer_subproces.stdin.write(out_frame.img)
                    out_f_no += 1
                    out_i += 1
                    to_produce -= 1
                else:
                    break

        stderr_bytes: bytes | None = None
        try:
            # Arbitrary timeout value
            _, stderr_bytes = writer_subproces.communicate(timeout=10)
        except:
            writer_subproces.kill()
            return False

        if stderr_bytes is not None:
            stderr = stderr_bytes.decode('utf-8)')
            # TODO: parse the output file
            if stderr != '':
                print(f"{scene_key} stderr:")
                pprint(stderr)
                return False

        # # Get image from pipe, add watermak and output to pipe
        # frame_no = start
        # for _ in range(count):
        #     in_img = np.frombuffer(
        #         reader_subproces.stdout.read(nbytes),
        #         dtype=np.uint8,
        #         count=nbytes
        #     ).reshape((h, w, 3))
        #     out_img: np.ndarray = add_watermark(in_img, scene, frame_no)
        #     frame_no += 1
        #     writer_subproces.stdin.write(np.ascontiguousarray(out_img))



        # for image in scene['in_frames'].images():
        #     print(f"{image.in_fp}\n  -> {image.out_fp}")
        # pprint(scene['in_frames'].in_images())
        # pprint(scene['in_frames'].out_images())
        # sys.exit()

        # if do_watermark(scene):
        #     # Force extract and add watermark if extract only
        #     # Used to identify scene no and compare 2 src and target editions
        #     do_generate: bool = False
        #     if task_name == 'lr':
        #         for fp in scene['in_frames'].out_images():
        #             if not os.path.exists(fp):
        #                 print(yellow(f"LR: do generate, missing {fp}"))
        #                 do_generate = True
        #                 break
        #     else:
        #         do_generate = True

        #     if do_generate:
        #         lr_directory: str = path_split(scene['in_frames'].out_images()[0])[0]
        #         os.makedirs(lr_directory, exist_ok=True)

        #         max_workers: int = multiprocessing.cpu_count()
        #         with ThreadPoolExecutor(max_workers=max_workers) as executor:
        #             for _ in executor.map(
        #                 lambda args: add_watermark(*args),
        #                 [(img, scene) for img in scene['in_frames'].images()]
        #             ):
        #                 pass

        # if success and 'effects' in scene and not 'segments' in scene['src']:
        #     effect: Effect = scene['effects'].primary_effect()
        #     main_logger.debug(lightcyan("Effects:"))

        #     if effect.name == 'loop_and_fadeout':
        #         effect_loop_and_fadeout(scene, effect)

        #     elif effect.name == 'fadeout':
        #         effect_fadeout(scene, effect)

        #     elif effect.name == 'loop_and_fadein':
        #         raise NotImplementedError("effect_loop_and_fadein")
        #         effect_loop_and_fadein(scene, effect)

        #     else:
        #         main_logger.debug(f"\t{effect}")

        # return success

    sys.exit()
    return False

