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

    parser.add_argument(
        "--scene",
        "-s",
        type=str,
        default='',
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
        "--stats",
        action="store_true",
        required=False,
        help="Statistics to find the dimension of the scene for each chapter"
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


    scene_no: int | None = None
    scene_arg: str = arguments.scene
    if scene_arg.endswith('f'):
        raise NotImplementedError("scene_arg not yet implemented")
        scene_no = frame_to_scene_no(int(scene_arg[:-1]))
    elif scene_arg != '':
        scene_no: int = int(scene_arg)

    task = 'final'
    final_scenes(
        episode=arguments.episode,
        single_chapter=arguments.chapter,
        scene_no=scene_no,
        task=task,
        force=arguments.force,
        simulation=arguments.simulate,
        debug=arguments.debug,
        stats=arguments.stats
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
