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
    pprint_scene_mapping,
)
from utils.arg_parser import common_argument_parser
from utils.mco_types import (
    Scene,
    ChapterVideo,
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
        chapter_video: ChapterVideo
        if chapter in ('g_debut', 'g_fin'):
            chapter_video = db[chapter]['video']
        elif k_ep == 'ep00':
            sys.exit(red("Missing episode no."))
        elif chapter in db[k_ep]['video']['target']:
            chapter_video = db[k_ep]['video']['target'][chapter]
        else:
            continue

        if 'count' not in chapter_video:
            pprint(chapter_video)
        if chapter_video['count'] <= 0:
            continue
        chapter_video['task'] = ProcessingTask(name=task)

        # Walk through target scenes
        scenes: list[Scene] = chapter_video['scenes']
        target_count = 0
        ref_count: int = 0
        for scene in scenes:
            pprint_scene_mapping(scene)

            if 'ref' in scene:
                ref_count += scene['ref']['count']
            target_count += scene['dst']['count']

        if 'ref' not in scene:
            ref_count = 0
            k_ep_or_g = chapter if chapter in ('g_debut', 'g_fin') else k_ep
            _k_ed = 'k' if db[k_ep_or_g]['audio']['lang'] == 'fr' else 'f'
            print(f"  reference: {_k_ed}:{k_ep}:{chapter}")
            if _k_ed in db[k_ep_or_g]['video']:
                for s in db[k_ep_or_g]['video'][_k_ed][chapter]['scenes']:
                    ref_count += s['count']
            else:
                print("Ignore reference as it has not been parsed")
        print(f"  Reference: {ref_count}")
        print(f"  Target: {target_count}")

        # for scene in scenes:
        #     print(lightcyan(f"Scene no. {scene['no']}"))
        #     pprint(scene)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
