from argparse import ArgumentParser
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
)
from processing.frame_cache import FrameCache
from scene.consolidate import consolidate_scene
from scene.generate_lr import generate_lr_scene
from utils.arg_parser import common_argument_parser
from utils.logger import main_logger as main_logger
from utils.mco_types import ChapterVideo, Scene, Inputs
from utils.mco_utils import calculate_scene_frame_count, run_simple_command
from utils.p_print import *
from utils.path_utils import absolute_path, path_split
from utils.time_conversions import FrameRate, frame_to_s, frame_to_sexagesimal
from video.extract_scenes import extract_scenes
from utils.media import (
    VideoInfo, extract_media_info_mco, frame_rate_dec, str_to_video_codec
)
from utils.tools import ffmpeg_exe



def main():
    # Arguments
    parser: ArgumentParser = common_argument_parser(
        description="Extract frames from a video scene"
    )

    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default="",
        required=False,
        help="Chapter"
    )

    arguments = parser.parse_args()
    verbose: bool = arguments.verbose

    if verbose:
        main_logger.addHandler(logging.StreamHandler(sys.stdout))
        main_logger.setLevel("DEBUG")

    if arguments.input:
        video_to_images(arguments)
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



def video_to_images(arguments) -> None:
    in_video_fp: str = absolute_path(arguments.input)
    directory, basename = path_split(in_video_fp)[:2]
    k_ep, task_name, k_ch = directory.split(os.sep)[-3:]
    _, _, scene_no, k_ed = basename.replace("__", "_").split("_", maxsplit=4)[:4]

    img_directory = os.path.join(
        os.sep.join(directory.split(os.sep)[:-3]).replace("cache", "imgs"),
        f"{k_ep}_{scene_no}_{task_name}_{k_ed}"
    )
    os.makedirs(img_directory, exist_ok=True)

    ffmpeg_command: list[str] = [
        ffmpeg_exe,
        "-hide_banner",
        "-loglevel", "error",
        "-stats",
        "-i", in_video_fp,
        os.sep.join([img_directory, "%03d.png"])
    ]
    print(lightgreen(' '.join(ffmpeg_command)))

    d_subprocess: subprocess.Popen | None = None
    try:
        d_subprocess = subprocess.Popen(
            ffmpeg_command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
    except Exception as e:
        print(f"[E] Unexpected error: {type(e)}", flush=True)

    os.set_blocking(d_subprocess.stdout.fileno(), False)
    while True:
        if d_subprocess.poll() is not None:
            print()
            break

        line: str = d_subprocess.stdout.readline().decode('utf-8')
        if line:
            print(line.strip(), end='\r')



if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
