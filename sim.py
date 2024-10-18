from argparse import ArgumentParser
import gc
import logging
from pprint import pprint
import signal
import sys
from parsers import (
    parse_database,
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

    parser.add_argument(
        "--scene",
        "-s",
        type=int,
        default=-1,
        required=False,
        help="scene no. to process. Integer or frame value (e.g. 2450f)"
    )

    parser.add_argument(
        "--force",
        action="store_true",
        required=False,
        help="Overwrite"
    )

    parser.add_argument(
        "--simulate",
        action="store_true",
        required=False,
        help="Simulate the process"
    )

    parser.add_argument(
        "--watermark",
        action="store_true",
        required=False,
        help="Watermark each scene with scene no."
    )

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
    parse_database(episode=episode, lang=arguments.lang)
    gc.collect()

    scene_no: int = arguments.scene
    task = 'sim'

    generate_lr_scenes(
        episode=arguments.episode,
        single_chapter=arguments.chapter,
        task_name=task,
        force=arguments.force,
        simulation=arguments.simulate,
        scene_no=scene_no,
        watermark=arguments.watermark,
        debug=arguments.debug
    )


    print(lightcyan("Combine audio and video tracks"))
    if arguments.chapter in ('g_debut', 'g_fin') and scene_no == -1:
        print(lightcyan("Combine audio and video tracks:"), arguments.chapter)
        combine_av_tracks(
            episode=arguments.episode,
            chapter=arguments.chapter,
            task=task,
            force=True,
            simulation=arguments.simulate
        )

    if arguments.chapter == '':
        for k in ('g_debut', 'g_fin'):
            combine_av_tracks(
                episode='',
                chapter=k,
                task=task,
                force=True,
                simulation=arguments.simulate
            )

        combine_av_tracks(
            episode=arguments.episode,
            chapter='',
            task=task,
            force=True,
            simulation=arguments.simulate
        )

        # Merge video and audio stream from all parts (except g_debut and g_fin)
        concatenate_all(
            episode=arguments.episode,
            task=task,
            simulation=arguments.simulate
        )

        add_chapters(
            episode=arguments.episode,
            task=task,
            simulation=arguments.simulate
        )



if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
