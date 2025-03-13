from argparse import ArgumentParser
import gc
import logging
from pprint import pprint
import signal
import sys
from parsers import (
    parse_database,
    ep_key,
    Chapter,
    TaskName,
)
from utils.arg_parser import common_argument_parser
from utils.logger import main_logger
from utils.p_print import *
from av_merge.combine_av import combine_av_tracks, concatenate_all
from av_merge.chapters import add_chapters
from video.final_scenes import final_scenes



def main():
    # Arguments
    parser: ArgumentParser = common_argument_parser(
        description="Generate episode (final)",
        add_language=True,
    )

    arguments = parser.parse_args()

    if arguments.debug:
        main_logger.addHandler(logging.StreamHandler(sys.stdout))
        main_logger.setLevel("DEBUG")

    simulate: bool = arguments.simulate

    ep_no: int = arguments.episode
    k_ch: Chapter = arguments.chapter
    if ep_no == 0 and k_ch == '':
        sys.exit("Error: at least an episode or a chapter shall be specified")

    if ep_no < 0 or ep_no > 39:
        sys.exit(red("Episode must be between 1 and 39"))

    if k_ch in ('g_debut', 'g_fin'):
        ep_no = 0
    if ep_no != 0:
        print(f"Episode: {ep_no}")
    if k_ch != '':
        print("Chapter: %s" % (k_ch))
    print(f"Language: {arguments.lang}")
    print("Tasks:")
    print("\t- parse database")

    k_ep: str = ep_key(ep_no)

    # Parse database
    parse_database(episode=k_ep, lang=arguments.lang)
    gc.collect()

    scene_no: int = arguments.scene

    task_name: TaskName = 'final'
    final_scenes(
        k_ep=k_ep,
        single_chapter=k_ch,
        scene_no=scene_no,
        scene_min=arguments.scene_min,
        scene_max=arguments.scene_max,
        scene_list=[],
        task_name=task_name,
        force=arguments.force,
        simulate=simulate,
        debug=arguments.debug,
    )


    if arguments.chapter in ('g_debut', 'g_fin') and scene_no == -1:
        combine_av_tracks(
            k_ep=k_ep,
            k_ch=arguments.chapter,
            task=task_name,
            force=True,
            simulation=arguments.simulate
        )

    if arguments.chapter == '':
        for k in ('g_debut', 'g_fin'):
            combine_av_tracks(
                k_ep='',
                k_ch=k,
                task=task_name,
                force=True,
                simulation=simulate,
            )

        combine_av_tracks(
            k_ep=k_ep,
            k_ch='',
            task=task_name,
            force=True,
            simulation=simulate,
        )

        # Merge video and audio stream from all parts (except g_debut and g_fin)
        concatenate_all(
            k_ep=k_ep,
            task=task_name,
            simulation=simulate,
        )

        add_chapters(
            k_ep=k_ep,
            task=task_name,
            simulation=simulate,
        )



if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
