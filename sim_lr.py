from argparse import ArgumentParser
import gc
import logging
from pprint import pprint
import signal
import sys
from parsers import (
    ep_key,
    parse_database,
    TaskName,
)
from utils.arg_parser import common_argument_parser
from utils.logger import main_logger as main_logger
from utils.p_print import *
from av_merge.combine_av import combine_av_tracks, concatenate_all
from av_merge.chapters import add_chapters
from video.lr_scenes import generate_lr_scenes



def main():
    # Arguments
    parser: ArgumentParser = common_argument_parser(
        description="Generate Low Resolution video",
        add_language=True,
    )

    arguments = parser.parse_args()

    if arguments.debug:
        main_logger.addHandler(logging.StreamHandler(sys.stdout))
        main_logger.setLevel("DEBUG")

    ep_no: int = arguments.episode
    chapter: str = arguments.chapter
    if ep_no == 0 and chapter == '':
        sys.exit("Error: at least an episode or a chapter shall be specified")

    if ep_no < 0 or ep_no > 39:
        sys.exit(red("Episode must be between 1 and 39"))

    if chapter in ('g_debut', 'g_fin'):
        ep_no = 0
    if ep_no != 0:
        print(f"Episode: {ep_no}")
    if chapter != '':
        print(f"Chapter: {chapter}")
    print(f"Language: {arguments.lang}")
    print("Tasks:")
    print("\t- parse database")

    # Parse database
    parse_database(episode=ep_no, lang=arguments.lang, verbose=arguments.verbose)
    gc.collect()

    k_ep = ep_key(ep_no)
    task: TaskName = 'sim_lr'

    generate_lr_scenes(
        episode=k_ep,
        single_chapter=arguments.chapter,
        task_name=task,
        force=arguments.force,
        simulation=arguments.simulate,
        scene_no=arguments.scene,
        scene_min=arguments.scene_min,
        scene_max=arguments.scene_max,
        watermark=arguments.watermark,
        debug=arguments.debug,
    )

    # Merge audio and video files of 'g_debut' and 'g_fin' and no scene
    if arguments.chapter in ('g_debut', 'g_fin') and arguments.scene == -1:
        combine_av_tracks(
            episode=k_ep,
            chapter=arguments.chapter,
            task=task,
            force=True,
            simulation=arguments.simulate
        )

    # Don't merge if chapter is specified
    if arguments.chapter == '':
        # for k in ('g_debut', 'g_fin'):
        #     combine_av_tracks(
        #         episode='',
        #         chapter=k,
        #         task=task,
        #         force=True,
        #         simulation=arguments.simulate
        #     )

        combine_av_tracks(
            episode=k_ep,
            chapter='',
            task=task,
            force=True,
            simulation=arguments.simulate
        )

        # Merge video and audio stream from all parts (except g_debut and g_fin)
        concatenate_all(
            episode=k_ep,
            task=task,
            simulation=arguments.simulate
        )

        add_chapters(
            episode=k_ep,
            task=task,
            simulation=arguments.simulate
        )



if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
