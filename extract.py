from argparse import ArgumentParser
import gc
import logging
from pprint import pprint
import signal
import sys
from parsers import (
    parse_database,
    all_chapter_keys,
    Chapter,
)
from parsers.episode import parse_episode
from utils.arg_parser import common_argument_parser
from utils.logger import main_logger as main_logger
from utils.p_print import *
from video.extract_scenes import extract_scenes



def main():
    # Arguments
    parser: ArgumentParser = common_argument_parser(
        description="Generate the HR scenes",
        add_language=True
    )

    parser.add_argument(
        "--stats",
        action="store_true",
        required=False,
        help="debug"
    )

    arguments = parser.parse_args()

    if arguments.debug:
        main_logger.addHandler(logging.StreamHandler(sys.stdout))
        main_logger.setLevel("DEBUG")

    episode: int = arguments.episode
    chapter: Chapter = arguments.chapter
    if episode == 0 and chapter == '':
        sys.exit("Error: at least an episode or a chapter shall be specified")
    elif episode != 0 and chapter == '':
        chapter = 'episode'

    if not (episode > 0 or episode <= 39 or episode == 99):
        sys.exit(red("Episode must be between 1 and 39"))

    if chapter in ('g_debut', 'g_fin'):
        episode = 0
    if episode != 0:
        print(f"Episode: {episode}")
    if chapter != '':
        print("Chapter: %s" % (chapter))
    print("Tasks:")
    print("\t- parse database")

    # Parse database
    parse_database(episode=episode, edition=arguments.edition)
    gc.collect()

    parse_episode(k_ed=arguments.edition, k_ep=arguments.episode)
    extract_scenes(
        episode=arguments.episode,
        single_chapter=arguments.chapter,
        task_name='extract',
        force=arguments.force,
        simulation=arguments.simulate,
        scene_no=arguments.scene,
        scene_min=arguments.scene_min,
        scene_max=arguments.scene_max,
        watermark=arguments.watermark,
        edition=arguments.edition,
        debug=arguments.debug
    )


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
