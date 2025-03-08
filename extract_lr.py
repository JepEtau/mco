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
    ep_key,
)
from parsers.episode import parse_episode
from utils.arg_parser import common_argument_parser
from utils.logger import main_logger as main_logger
from utils.p_print import *
from video.extract_scenes import extract_scenes



def main():
    # Arguments
    parser: ArgumentParser = common_argument_parser(
        description="Generate LQ scenes for experiments"
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

    if not (episode > 0 or episode <= 39 or episode == 99):
        sys.exit(red("Episode must be between 1 and 39"))

    elif episode != 0 and chapter == '':
        chapter = 'episode'

    if chapter in ('g_debut', 'g_fin'):
        episode = 0

    if episode != 0:
        print(f"Episode: {episode}")

    if chapter != '':
        print("Chapter: %s" % (chapter))

    k_ep: str = ep_key(episode)

    # Parse database
    parse_database(episode=k_ep, edition=arguments.edition)
    gc.collect()

    parse_episode(k_ed=arguments.edition, k_ep=k_ep)
    extract_scenes(
        episode=k_ep,
        single_chapter=chapter,
        task_name='lr',
        force=arguments.force,
        simulation=arguments.simulate,
        scene_no=arguments.scene,
        scene_min=arguments.scene_min,
        scene_max=arguments.scene_max,
        watermark=False,
        edition=arguments.edition,
        debug=arguments.debug
    )


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
