from argparse import ArgumentParser
import os
from pprint import pprint
import signal
import subprocess
import sys
import time
from processing.deint import _clean_str
from utils.logger import main_logger as main_logger
from utils.media import (
    VideoInfo,
    extract_media_info_mco,
    str_to_video_codec,
)
from utils.p_print import *
from utils.path_utils import absolute_path, path_split
from utils.time_conversions import s_to_sexagesimal
from utils.tools import ffmpeg_exe



def main():
    # Arguments
    parser = ArgumentParser(description="overlay 2 videos")

    parser.add_argument(
        "-i",
        '--input',
        type=str,
        action="append",
        required=True,
        help="input video"
    )

    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="",
        required=False,
        help="out filepath"
    )

    parser.add_argument(
        "--opacity",
        "-op",
        type=float,
        default=0.5,
        required=False,
        help="from 0.01 to 0.99"
    )
    arguments = parser.parse_args()

    in0_fp: str = absolute_path(arguments.input[0])
    in1_fp: str = absolute_path(arguments.input[1])
    opacity: float = max(0.01, min(0.99, arguments.opacity))

    if not os.path.isfile(in0_fp):
        raise FileExistsError(red(f"Missing file: {in0_fp}"))
    if not os.path.isfile(in1_fp):
        raise FileExistsError(red(f"Missing file: {in1_fp}"))

    print(lightcyan("video 0:"), in0_fp)
    print(lightcyan("video 1:"), in1_fp)
    print(lightcyan("opacity:"), f"{opacity:.02f}")

    in0_vi: VideoInfo = extract_media_info_mco(in0_fp)['video']
    in1_vi: VideoInfo = extract_media_info_mco(in1_fp)['video']

    out_fp: str = absolute_path(arguments.output)
    if not arguments.output:
        in_dir, in_basename, ext = path_split(in0_fp)
        out_fp: str = os.path.join(
            in_dir, f"{in_basename}_{opacity:.02f}{ext}"
        )
    print(lightcyan("output video:"), out_fp)

    if in0_vi['shape'] != in1_vi['shape']:
        raise ValueError(red(f"Different shapes: {in0_vi['shape']} != {in1_vi['shape']}"))

    # Complex filter
    in_codec = in0_vi['codec']
    in_pixfmt = in0_vi['pix_fmt']
    ovl_pixfmt = in0_vi['pix_fmt'].replace("yuv", "yuva")
    complex_filter: list[str] = f"""
        [0:v]format={ovl_pixfmt},colorchannelmixer=aa={opacity:.02f}[outv0];
        [1:v]format={ovl_pixfmt},colorchannelmixer=aa={1. - opacity:.02f}[outv1];
        [outv0][outv1]overlay=0:0[outv]
    """

    # Create the command
    ffmpeg_command: list[str] = [
        ffmpeg_exe,
        "-hide_banner",
        "-loglevel", "error",
        "-stats",

        "-i", in0_fp,
        "-i", in1_fp,

        "-filter_complex", _clean_str(complex_filter),
        "-map", "[outv]",

        "-pix_fmt", in_pixfmt,
        "-vcodec", str_to_video_codec[in_codec].value,

        "-y", out_fp
    ]
    print()
    print(' '.join(ffmpeg_command))
    print()

    os.makedirs(path_split(in0_fp)[0], exist_ok=True)

    start_time: float = time.time()
    sub_process = subprocess.Popen(
        ffmpeg_command,
        stdin=subprocess.PIPE,
        stdout=sys.stdout,
        stderr=subprocess.STDOUT,
    )

    stdout, _ = sub_process.communicate()
    if stdout is not None:
        for line in stdout.decode('utf-8').split('\n'):
            print(line)

    print(cyan("Elapsed time"), f"{s_to_sexagesimal(time.time() - start_time)}")


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()

