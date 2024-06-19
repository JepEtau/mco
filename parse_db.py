import argparse
import gc
import logging
from pprint import pprint
import signal
import sys
from parsers import (
    parse_database,
    logger,
    all_chapter_keys,
)
from utils.p_print import *


def main():
    # Arguments
    parser = argparse.ArgumentParser(description="Parse the database")
    parser.add_argument(
        "--episode",
        "-ep",
        type=int,
        default=0,
        required=False,
        help="from 1 to 39"
    )

    parser.add_argument(
        "--chapter",
        choices=all_chapter_keys(),
        default='',
        required=False,
        help="Chapter"
    )

    parser.add_argument(
        "--en",
        action="store_true",
        required=False,
        help="English version"
    )

    parser.add_argument(
        "--stats",
        action="store_true",
        required=False,
        help="debug"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        required=False,
        help="debug"
    )

    arguments = parser.parse_args()

    if arguments.debug:
        logger.addHandler(logging.StreamHandler(sys.stdout))
        logger.setLevel("DEBUG")

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
    parse_database(
        episode=episode,
        lang='en' if arguments.en else 'fr'
    )
    gc.collect()


    # For inspection
    # db_ep: dict = g_database['ep01']
    # print(db_ep.keys())
    # print(db_ep['cache_path'])
    # pprint(db_ep['audio'])

    # print(g_database.keys())
    # pprint(g_database['common'])



if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
