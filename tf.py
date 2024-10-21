from argparse import ArgumentParser
import gc
import logging
from pprint import pprint
import signal
import sys
from parsers import parse_database
from utils.arg_parser import common_argument_parser
from utils.logger import main_logger as main_logger
from utils.p_print import *
from video.tf_scenes import tf_scenes



def main():
    # Arguments
    parser: ArgumentParser = common_argument_parser(
        description="Temporal filters",
        add_language=True
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
        "--eval",
        "-e",
        action="store_true",
        required=False,
        help="Use to compare before/after stabilization"
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

    task = 'tf'

    tf_scenes(
        episode=arguments.episode,
        single_chapter=arguments.chapter,
        scene_no=scene_no,
        task_name=task,
        evaluate=arguments.eval,
        force=arguments.force,
        debug=arguments.debug,
    )


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
