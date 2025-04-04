from argparse import ArgumentParser, Namespace
import gc
import logging
import math
import os
from pprint import pprint
import signal
import subprocess
import sys
import time

import numpy as np
from parsers import (
    parse_database,
    Chapter,
    ep_key,
    get_chapter_video,
    db,
    ProcessingTask,
    TaskName,
    VideoSettings,
    parse_episode,
    pprint_scene_mapping,
    TASK_NAMES,
)
from scene.consolidate import consolidate_scene
from scene.generate_lr import generate_lr_scene
from utils.arg_parser import common_argument_parser
from utils.logger import main_logger as main_logger
from utils.mco_types import ChapterVideo, Scene
from utils.media import VideoCodec, extract_media_info
from utils.p_print import *
from utils.path_utils import absolute_path, path_split
from utils.tools import ffmpeg_exe



# Keep here to fasten modifications
DEFAULT_H265_PARAMS: str = """
    -preset slow
    -crf 16
    -profile:v main422-10
    -x265-params sao=0
"""

DEFAULT_HVEC_NVENC_PARAMS: str = """
    -profile:v main
    -b_ref_mode disabled
    -tag:v hvc1
    -g 30
    -preset p7
    -tune hq
    -rc constqp
    -qp 17
    -rc-lookahead 20
    -spatial_aq 1
    -aq-strength 15
    -b:v 0
"""


def execute_ffmpeg_command(command: list[str], verbose: bool = False) -> None:
    command = list(filter(None, command))
    if verbose:
        print(lightgreen("FFmpeg command:"), darkgrey(' '.join(command)))

    d_subprocess: subprocess.Popen | None = None
    try:
        d_subprocess = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
    except Exception as e:
        print(f"[E] Unexpected error: {type(e)}", flush=True)

    os.set_blocking(d_subprocess.stdout.fileno(), False)
    while True:
        if d_subprocess.poll() is not None:
            if verbose:
                print()
            break

        line: str = d_subprocess.stdout.readline().decode('utf-8')
        if line and verbose:
            print(line.strip(), end='\r')



def video_to_images(arguments: Namespace) -> None:
    in_video_fp: str = absolute_path(arguments.input)
    directory, basename = path_split(in_video_fp)[:2]

    dir_list: list[str] = directory.split(os.sep)
    if dir_list[-1] not in TASK_NAMES:
        k_ep, task_name, _ = dir_list[-3:]
        imgs_dir = os.sep.join(dir_list[:-3]).replace("cache", "imgs")
    else:
        k_ep, task_name = dir_list[-2:]
        imgs_dir = os.sep.join(dir_list[:-2]).replace("cache", "imgs")

    _, _k_ch, scene_no, k_ed = basename.replace("__", "_").split("_", maxsplit=4)[:4]

    scene_img_directory: str = os.path.join(
        imgs_dir, f"{k_ep}_{scene_no}_{task_name}_{k_ed}"
    )
    os.makedirs(scene_img_directory, exist_ok=True)

    # Crop for comparison
    ffmpeg_filter: list[str] = []
    if arguments.compare:
        task_name: TaskName
        if task_name in ('hr', 'tf', 'cg'):
            h, w, _ = extract_media_info(in_video_fp)['video']['shape']
            pad = 24
            ffmpeg_filter = [
                "-vf", f"crop={w - 2 * pad}:{h - 2 * pad}:{pad}:{pad}"
            ]

    ffmpeg_command: list[str] = [
        ffmpeg_exe,
        "-hide_banner",
        "-loglevel", "error",
        "-stats",
        "-i", in_video_fp,
        *ffmpeg_filter,
        os.sep.join([scene_img_directory, "%03d.png"])
    ]

    execute_ffmpeg_command(command=ffmpeg_command, verbose=True)



def images_to_video(arguments: Namespace) -> None:
    # Input folder name
    in_folder_path: str = absolute_path(arguments.input)

    # Use provided output filepath or automatically generate one
    out_video_fp: str = arguments.output
    if not out_video_fp:
        # Use parent folder and folder name to generate filepath
        dir_list: list[str] = in_folder_path.split(os.sep)
        grandparent, parent = dir_list[-2:]
        out_dir: str = ""
        if grandparent.startswith("ep"):
            out_dir = os.path.join(dir_list[:-2], grandparent)
            out_basename = f"{grandparent}_{parent}"
        else:
            grandparent = ""
            out_dir = os.sep.join(dir_list[:-1])
            out_basename: str = f"{parent}"

        # Add task name if provided
        taskname: str = arguments.task
        if taskname:
            out_basename = f"{out_basename}_{taskname}"

        out_video_fp: str = os.path.join(out_dir, f"{out_basename}.mkv")

    out_video_fp = absolute_path(out_video_fp)

    # Output video settings
    vcodec: VideoCodec = VideoCodec.H265
    pix_fmt: str = 'yuv420p'
    codec_params: list[str] = []
    if vcodec == VideoCodec.H265:
        codec_params = DEFAULT_H265_PARAMS
    elif vcodec == VideoCodec.HEVC_NVENC:
        codec_params = DEFAULT_HVEC_NVENC_PARAMS

    extra_params: list[str] = []
    if codec_params:
        def _clean_ffmpeg_params(data: str) -> str:
            for c in ['\"', '\r', '\n', '\t']:
                data = data.replace(c, '')
            # avoid too many spaces when debugging
            for _ in range(4):
                data = data.replace('  ', ' ')
            return data

        extra_params = list(
            [x for x in _clean_ffmpeg_params(codec_params).split(" ") if x]
        )

    # Create command
    ffmpeg_command: list[str] = [
        ffmpeg_exe,
        "-hide_banner",
        "-loglevel", "error",
        "-stats",
        "-i", os.sep.join([in_folder_path, "%03d.png"]),

        "-vf", "setparams=colorspace=bt709:color_primaries=bt709:color_trc=bt709",
        "-r", "25",
        "-vcodec", vcodec.value,
        "-pix_fmt", pix_fmt,
        "-color_range", "limited",
        *extra_params,
        "-y", out_video_fp
    ]
    execute_ffmpeg_command(command=ffmpeg_command, verbose=True)




def main():
    # Arguments
    parser: ArgumentParser = common_argument_parser(
        description="Extract frames from a video scene"
    )

    parser.set_defaults(task="")

    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default="",
        required=False,
        help="Input video file"
    )

    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="",
        required=False,
        help="Output video file"
    )

    arguments: Namespace = parser.parse_args()
    verbose: bool = arguments.verbose

    if verbose:
        main_logger.addHandler(logging.StreamHandler(sys.stdout))
        main_logger.setLevel("DEBUG")

    if arguments.input:
        if os.path.isfile(arguments.input):
            video_to_images(arguments)

        elif os.path.isdir(arguments.input):
            images_to_video(arguments)
        return


    episode: int = arguments.episode
    k_ep: str = ep_key(episode)
    k_ed: str = arguments.edition
    k_ch: Chapter = arguments.chapter
    scene_no: int = arguments.scene
    task_name: TaskName = arguments.task

    if episode == 0 and k_ch == '':
        sys.exit("Error: at least an episode or a chapter shall be specified")

    if not (episode > 0 or episode <= 39 or episode == 99):
        sys.exit(red("Episode must be between 1 and 39"))

    elif episode != 0 and k_ch == '':
        k_ch = 'episode'

    if k_ch in ('g_debut', 'g_fin'):
        episode = 0

    if episode != 0:
        print(f"Episode: {episode}")

    if k_ch != '':
        print(f"Chapter: {k_ch}")

    if scene_no == -1:
        raise ValueError(red("missing scene no."))


    # Parse database
    parse_database(episode=k_ep, edition=k_ed)
    gc.collect()

    parse_episode(k_ed=k_ed, k_ep=k_ep)

    ch_video: ChapterVideo | None = get_chapter_video(k_ep, k_ch)
    ch_video['task'] = ProcessingTask(name=task_name)
    scenes: list[Scene] = ch_video['scenes']
    scene: Scene = scenes[scene_no]

    # Consolidate this scene
    pprint_scene_mapping(scene)
    scene['task'] = ProcessingTask(name=task_name)
    consolidate_scene(scene=scene)
    generate_lr_scene(scene=scene, save_as_png=True)



if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
