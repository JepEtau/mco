import argparse
import gc
import logging
from pprint import pprint
import signal
import sys
from parsers import (
    key,
    parse_database,
    logger,
    all_chapter_keys,
    get_dependencies,
)
from parsers.helpers import get_chapter_video_src
from utils.p_print import *

g_database = dict()

def main():
    # Arguments
    parser = argparse.ArgumentParser(description="Deinterlace")
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
        g_database,
        episode=episode,
        lang='en' if arguments.en else 'fr'
    )
    gc.collect()

    db = g_database
    ep: str = key(episode)
    # Dependencies
    dependencies = get_dependencies(
        db=db,
        episode=ep,
        chapter=chapter,
        track='video'
    )
    # editions: list[str] = list([ed for ed, eps in dependencies.items() if ep in eps])
    editions: list[str] = list(dependencies.keys())

    # Get all range to deinterlace for each dependency
    interlaced: dict[str, set] = {}
    for ed in editions:
        for k_c in all_chapter_keys():
            inputs = get_chapter_video_src(db, ep, ed, k_c)['inputs']
            fp: str = inputs['interlaced']['filepath']
            segment: tuple[int, int] = (inputs['progressive']['start'], inputs['progressive']['count'])
            if fp not in interlaced:
                interlaced[fp] = set()
            interlaced[fp].add(segment)

    pprint(interlaced)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
