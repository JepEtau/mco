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
    task: TaskName = 'lr'

    single_chapter: Chapter = arguments.chapter
    chapters: Chapter = all_chapter_keys() if single_chapter == '' else [single_chapter]
    for chapter in chapters:
        print(lightcyan(f"{chapter}"))
        k_ep_src: str = ''
        chapter_video: VideoChapter
        if chapter in ('g_debut', 'g_fin'):
            chapter_video = db[chapter]['video']
            k_ep_src: str = k_ep if task == 'initial' else chapter_video['src']['k_ep']
        elif k_ep == 'ep00':
            sys.exit(red("Missing episode no."))
        elif chapter in db[k_ep]['video']['target']:
            chapter_video = db[k_ep]['video']['target'][chapter]
        else:
            continue

        if chapter_video['count'] <= 0:
            continue
        chapter_video['task'] = ProcessingTask(name=task)

        # Walk through target scenes
        scenes: list[Scene] = chapter_video['scenes']
        ref_count: int = 0
        target_count = 0
        src_count = 0
        for scene in scenes:
            print(lightgreen(f"    {scene['no']}".rjust(8)), end=':')
            print(lightgreen(f"{scene['start']}".rjust(6)), end='')
            if 'segments' in scene['src']:
                print(lightgreen(f"  (src: {scene['src']['segments'][0]['count']})".rjust(8)), end='')
                print(lightgreen(f"{scene['count']}".rjust(6)), end='')
            else:
                print(lightgreen(f"  (src: {scene['src']['count']})".rjust(8)), end='')
                print(lightgreen(f"{scene['count']}".rjust(6)), end='')
            if 'ref' in scene:
                ref_count += scene['ref']['count']
            print(f"{scene['dst']['count']}".rjust(8), end='')
            target_count += scene['dst']['count']

            print(f"  <-  {scene['k_ed']}:{scene['k_ep']}:{scene['k_ch']}:{scene['src']['no']: 3}".ljust(18), end='')

            src_scene = db[scene['k_ep']]['video'][scene['k_ed']][scene['k_ch']]['scenes'][scene['src']['no']]
            print(f"   {src_scene['start']}".rjust(10), end='')
            print(f"{src_scene['count']}".rjust(8), end='')
            try:
                src_count += src_scene['count']
            except:
                pprint(scene['src'])
            print()

        print(f"Reference: {ref_count}")
        print(f"Source: {src_count}")
        print(f"Destination: {target_count}")

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
