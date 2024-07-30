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
from video.final_scenes import generate_final_scenes



def main():
    # Arguments
    parser: ArgumentParser = common_argument_parser(
        description="Generate episode (final)",
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
        "--scene_min",
        type=int,
        default=-1,
        required=False,
        help="starting scene no. to process"
    )

    parser.add_argument(
        "--scene_max",
        type=int,
        default=-1,
        required=False,
        help="last scene no. to process"
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
    print(f"Language: {'en' if arguments.en else 'fr'}")
    print("Tasks:")
    print("\t- parse database")

    # Parse database
    parse_database(episode=episode, lang='en' if arguments.en else 'fr')
    gc.collect()


    task = 'final'
    generate_final_scenes(
        episode=arguments.episode,
        single_chapter=arguments.chapter,
        task=task,
        force=arguments.force,
        simulation=arguments.simulate,
        scene_no=arguments.scene,
        scene_min=arguments.scene_min,
        scene_max=arguments.scene_max,
        debug=arguments.debug
    )

    if arguments.chapter in ('g_debut', 'g_fin') and arguments.scene == -1:
        # Merge audio and video files
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
