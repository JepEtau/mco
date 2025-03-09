from argparse import ArgumentParser
import gc
import logging
import os
from pprint import pprint
import signal
import sys
from parsers import (
    Chapter,
    db,
    ep_key,
    parse_database,
    TaskName,
    get_chapter_video,
)
from parsers.p_print import pprint_scene_mapping
from scene.consolidate import consolidate_scene
from utils.arg_parser import common_argument_parser
from utils.logger import main_logger as main_logger
from utils.mco_types import ChapterVideo, Scene
from utils.mco_utils import calculate_scene_frame_count, is_up_to_date
from utils.media import extract_media_info_mco
from utils.p_print import *
try:
    import winsound
except ImportError:
    pass


def main():
    # Arguments
    parser: ArgumentParser = common_argument_parser('Upscale scenes', add_language=True)
    arguments = parser.parse_args()

    if arguments.debug:
        main_logger.addHandler(logging.StreamHandler(sys.stdout))
        main_logger.setLevel("DEBUG")

    episode: int = arguments.episode
    chapter: str = arguments.chapter
    if episode == 0 and chapter == '':
        sys.exit("Error: at least an episode or a chapter shall be specified")

    if episode < 0 or episode > 39:
        sys.exit(red("Episode must be between 1 and 39"))

    if chapter in ('g_debut', 'g_fin'):
        episode = 0
    if episode != 0:
        print(f"Episode: {episode}")
    if chapter != '':
        print("Chapter: %s" % (chapter))
    print(f"Language: {arguments.lang}")
    print("Tasks:")
    print("\t- parse database")

    # Parse database
    k_ep: str = ep_key(arguments.episode)
    k_ch: Chapter = 'episode'

    parse_database(episode=k_ep, lang=arguments.lang)
    gc.collect()

    task_name: TaskName = arguments.task
    if not task_name:
        task_name = 'cg'


    ch_video: ChapterVideo = get_chapter_video(k_ep, k_ch)
    # Walk through target scenes
    scenes: list[Scene] = ch_video['scenes']
    for scene in scenes:
        pprint_scene_mapping(scene)
        # Consolidate this scene
        consolidate_scene(scene, task_name=task_name)

        # Out vidoe file
        out_video_fp: str = scene['task'].video_file
        if not os.path.isfile(out_video_fp):
            print(red(f"scene no. {scene['no']}: missing file: {out_video_fp}"))
            continue

        out_video_info = extract_media_info_mco(out_video_fp)['video']
        # print(f"output scene file: {out_video_info['frame_count']}")

        dst_frame_count = calculate_scene_frame_count(scene)
        # print(f"  dst scene: {dst_frame_count}")

        if out_video_info['frame_count'] != dst_frame_count:
            print(red(f"scene no. {scene['no']}: wrong duration: {out_video_info['frame_count']}, must be {dst_frame_count}"))


    if sys.platform == "win32":
        winsound.Beep(frequency=440, duration=200)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
