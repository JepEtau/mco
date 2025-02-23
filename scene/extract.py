import math
import os
from pprint import pprint
import subprocess
import sys

import numpy as np
from parsers import (
    db,
    get_fps,
    VideoSettings,
)
from processing.watermark import add_watermark
from scene.filters import do_watermark
from utils.mco_types import McoFrame, Scene
from utils.mco_utils import run_simple_command
from utils.p_print import *
from utils.path_utils import path_split
from utils.time_conversions import FrameRate, frame_to_s, frame_to_sexagesimal
from utils.tools import ffmpeg_exe
from utils.media import VideoInfo, extract_media_info_mco, str_to_video_codec



def extract_scene(
    scene: Scene,
    force: bool = False,
    debug: bool = False
) -> bool:
    scene_key: str = f"{scene['k_ed']}:{scene['k_ep']}:{scene['k_ch']}:{scene['k_ch']}:{scene['no']}"

    in_video_fp: str = scene['inputs'].progressive().filepath
    if not os.path.exists(in_video_fp):
        raise FileExistsError(red(f"Missing input file: {in_video_fp}"))
    out_video_fp: str = scene['task'].video_file
    in_video_info: VideoInfo = extract_media_info_mco(in_video_fp)['video']

    if not force:
        if os.path.exists(out_video_fp):
            out_video_info: VideoInfo = extract_media_info_mco(out_video_fp)['video']
            if out_video_info['frame_count'] == scene['count']:
                return True

    start: int = scene['start'] - scene['inputs'].progressive().start
    count: int = scene['count']

    # Decimate
    factor: int = 0
    factor_2_mod: int = 0
    if 'effects' in scene:
        if e := scene['effects'].get_effect('decimate'):
            factor, _ = e.extra_param
            print(yellow(f"decimate:"), f"{scene['no']}: {count}")
        elif e := scene['effects'].get_effect('decimate_2'):
            factor, factor_2_mod = e.extra_param
            print(yellow(f"decimate_2:"), f"{scene['no']}: {factor_2_mod}")
            pprint(scene)

    frame_no: int = scene['start']
    vsettings: VideoSettings = scene['task'].video_settings
    if start < 0:
        raise ValueError(f"Error, start < 0 for scene {scene['no']}")

    # k_ed_ref = db['ep01']['audio']['src']['k_ed']
    # if scene['k_ed'] == k_ed_ref:
    #     in_video_fp: str = scene['inputs']['interlaced']['filepath']
    #     in_video_info: VideoInfo = extract_media_info_mco(in_video_fp)['video']
    #     start: int = scene['start']

    # Output directory
    xtract_directory: str = path_split(scene['task'].video_file)[0]
    os.makedirs(xtract_directory, exist_ok=True)

    # Create FFmpeg command
    frame_rate: FrameRate = get_fps(db)
    d_command: list[str] = [
        ffmpeg_exe,
        "-hide_banner",
        "-loglevel", "warning",
        "-nostats",
        "-ss", str(frame_to_sexagesimal(no=start, frame_rate=frame_rate)),
        "-i", in_video_fp,
        "-t", str(frame_to_s(no=count, frame_rate=frame_rate))
    ]
    h, w = in_video_info['shape'][:2]

    # Force to 576p to facilitate comparisons
    filter_complex: list[str] = []
    if h != 640 or w != 480:
        filter_complex = [
            "-filter_complex",
            f"[0:v]scale=640:480:sws_flags=bilinear+accurate_rnd+bitexact+full_chroma_int,setsar=1[outv]",
            "-map", "[outv]"
        ]

    if do_watermark(scene=scene):
        video_info: VideoInfo = extract_media_info_mco(in_video_fp)['video']
        h, w, c = video_info['shape']
        pipe_pixfmt = 'bgr24'
        nbytes = math.prod(video_info['shape'])
        d_command.extend([
            "-f", "image2pipe",
            "-pix_fmt", pipe_pixfmt,
            "-vcodec", "rawvideo",
            "-"
        ])

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

            *filter_complex,

            "-pix_fmt", vsettings.pix_fmt,
            "-vcodec", str_to_video_codec[vsettings.codec].value,
            *vsettings.codec_options,
            out_video_fp, "-y"
        ]

        if debug:
            print(lightgreen(" ".join(d_command)))
            print(f"shape: {w}x{h}x{c}, nbytes: {nbytes}")
            print(blue(" ".join(writer_command)))

        d_subproces: subprocess.Popen = None
        try:
            d_subproces = subprocess.Popen(
                d_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except Exception as e:
            print(red(f"[E][W] {scene_key} Unexpected error: {type(e)}"))
            return False

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

        # Get image from pipe, add watermak and output to pipe
        index: int = 0
        out_i: int = 0
        factor_2_i: int = 0
        for i in range(count):
            buffer = d_subproces.stdout.read(nbytes)
            in_img = np.frombuffer(
                buffer,
                dtype=np.uint8,
                count=nbytes
            ).reshape((h, w, c))
            out_img: np.ndarray = add_watermark(
                McoFrame(no=frame_no, img=in_img, scene=scene),
                no=frame_no
            )
            frame_no += 1

            index += 1
            if factor != 0 and (index % factor) == 0:
                index = 0
                continue
            if factor_2_mod:
                factor_2_i = (factor_2_i + 1) % factor_2_mod
                if factor_2_i:
                    continue

            writer_subproces.stdin.write(np.ascontiguousarray(out_img))

            out_i += 1
            if out_i >= scene['count']:
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

    else:
        d_command.extend([
            *filter_complex,
            "-pix_fmt", vsettings.pix_fmt,
            "-vcodec", str_to_video_codec[vsettings.codec].value,
            *vsettings.codec_options,
            out_video_fp, "-y"
        ])
        if debug:
            print(lightgrey(" ".join(d_command)))
        return run_simple_command(d_command)

    return True

