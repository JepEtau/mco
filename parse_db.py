import gc
import logging
from pprint import pprint
import signal
import sys
from parsers import (
    parse_database,
    logger,
    db,
    Chapter,
    all_chapter_keys,
    key,
    ProcessingTask,
    TaskName,
)
from utils.arg_parser import common_argument_parser
from utils.mco_types import (
    Scene,
    VideoChapter,
)
from utils.p_print import *


def main():
    # Arguments
    parser = common_argument_parser(description="Parse the database")

    parser.add_argument(
        "--en",
        action="store_true",
        required=False,
        help="English version"
    )

    parser.add_argument(
        "--stats",
        choices=['scene'],
        default='',
        required=False,
        help="debug"
    )

    parser.add_argument(
        "--edition",
        "-ed",
        choices=['f', 'k', 's', 'j'],
        default='',
        required=False,
        help="Use this edition as source rather than the one selected in database"
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

    # print(db.keys())
    # pprint(db['common'])
    k_ep = key(episode)
    task: TaskName = 'initial'

    single_chapter: Chapter = arguments.chapter
    chapters: Chapter = all_chapter_keys() if single_chapter == '' else [single_chapter]
    for chapter in chapters:
        k_ep_src: str = ''
        video: VideoChapter
        if chapter in ('g_debut', 'g_fin'):
            video = db[chapter]['video']
            k_ep_src: str = k_ep if task == 'initial' else video['src']['k_ep']
        elif k_ep == 'ep00':
            sys.exit(red("Missing episode no."))

        if video['count'] <= 0:
            continue
        video['task'] = ProcessingTask(name='initial')

        # Walk through target scenes
        scenes: list[Scene] = video['scenes']
        for scene in scenes:
            print(lightgreen(f"    {scene['no']}".rjust(8)), end=':')
            print(lightgreen(f"{scene['start']}".rjust(6)), end='')
            print(f"{scene['dst']['count']}".rjust(8), end='')

            print(f"    {scene['k_ed']}:{scene['k_ep']}:{scene['k_ch']}".rjust(8), end='')
            print(f"   {scene['src']['start']}".rjust(8), end='')
            print(f"({scene['src']['count']})".rjust(8), end='')
            print()
            # print(scene['src'])


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
