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
from scene.generate_hr import _get_complex_filter
from utils.logger import main_logger
from utils.mco_types import Scene
from utils.mco_utils import run_simple_command
from utils.p_print import *
from utils.path_utils import path_split
from utils.time_conversions import FrameRate, frame_to_s, frame_to_sexagesimal
from utils.tools import ffmpeg_exe
from utils.media import VideoInfo, extract_media_info, str_to_video_codec



def extract_scene(scene: Scene, force: bool = False, debug: bool = False) -> bool:
    scene_key: str = f"{scene['k_ed']}:{scene['k_ep']}:{scene['k_ch']}:{scene['k_ch']}:{scene['no']}"

    in_video_fp: str = scene['inputs']['progressive']['filepath']
    if not os.path.exists(in_video_fp):
        raise FileExistsError(red(f"Missing input file: {in_video_fp}"))
    out_video_fp: str = scene['task'].video_file
    in_video_info: VideoInfo = extract_media_info(in_video_fp)['video']

    if not force:
        if os.path.exists(out_video_fp):
            out_video_info: VideoInfo = extract_media_info(out_video_fp)['video']
            if out_video_info['frame_count'] == scene['count']:
                return True

    start: int = scene['start'] - scene['inputs']['progressive']['start']
    count: int = scene['count']
    frame_no: int = scene['start']
    vsettings: VideoSettings = scene['task'].video_settings
    if start < 0:
        raise ValueError(f"Error, start < 0 for scene {scene['no']}")

    # Output directory
    xtract_directory: str = path_split(scene['task'].video_file)[0]
    os.makedirs(xtract_directory, exist_ok=True)

    # Create FFmpeg command
    frame_rate: FrameRate = get_fps(db)
    xtract_command: list[str] = [
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
    if h != 576 or w != 576:
        filter_complex = [
            "-filter_complex",
            f"[0:v]scale=768:576:sws_flags=lanczos+accurate_rnd+bitexact+full_chroma_int[outv]",
            "-map", "[outv]"
        ]

    if do_watermark(scene=scene):
        video_info: VideoInfo = extract_media_info(in_video_fp)['video']
        h, w, c = video_info['shape']
        pipe_pixfmt = 'bgr24'
        nbytes = math.prod(video_info['shape'])
        xtract_command.extend([
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
            print(lightgreen(" ".join(xtract_command)))
            print(f"shape: {w}x{h}x{c}, nbytes: {nbytes}")
            print(blue(" ".join(writer_command)))

        xtract_subproces: subprocess.Popen = None
        try:
            xtract_subproces = subprocess.Popen(
                xtract_command,
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
        for _ in range(count):
            in_img = np.frombuffer(
                xtract_subproces.stdout.read(nbytes),
                dtype=np.uint8,
                count=nbytes
            ).reshape((h, w, 3))
            out_img: np.ndarray = add_watermark(in_img, scene, frame_no)
            frame_no += 1
            writer_subproces.stdin.write(np.ascontiguousarray(out_img))

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
        xtract_command.extend([
            *filter_complex,
            "-pix_fmt", vsettings.pix_fmt,
            "-vcodec", str_to_video_codec[vsettings.codec].value,
            *vsettings.codec_options,
            out_video_fp, "-y"
        ])
        if debug:
            print(lightgrey(" ".join(xtract_command)))
        return run_simple_command(xtract_command)

    return True

