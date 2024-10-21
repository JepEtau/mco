import gc
import logging
from pprint import pprint
import signal
import sys
from parsers import (
    TASK_NAMES,
    parse_database,
    logger,
    db,
    Chapter,
    all_chapter_keys,
    ep_key,
    ProcessingTask,
    TaskName,
    pprint_scene_mapping,
)
from scene.consolidate import consolidate_scene
from utils.arg_parser import common_argument_parser
from utils.mco_types import (
    Scene,
    ChapterVideo,
)
from utils.p_print import *
from video.consolidate_scenes import get_chapter_video


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

    parser.add_argument(
        "--task",
        "-t",
        choices=TASK_NAMES,
        default='lr',
        required=False,
        help="task name"
    )

    parser.add_argument(
        "--scene",
        "-s",
        type=int,
        default=-1,
        required=False,
        help="scene no."
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
    k_ep = ep_key(episode)
    task: TaskName = arguments.task

    k_ch: Chapter = arguments.chapter
    chapters: Chapter = all_chapter_keys() if k_ch == '' else [k_ch]
    for chapter in chapters:
        print(lightcyan(f"{chapter}"))
        chapter_video: ChapterVideo = get_chapter_video(k_ep, k_ch)
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


        # pprint(chapter_video)
        scene_no: int = arguments.scene
        if scene_no != -1:
            print(lightcyan(f"Scene no. {scene_no}"))
            ch_video: ChapterVideo | None = get_chapter_video(k_ep, k_ch)
            if ch_video is None:
                continue

            consolidate_scene(scenes[scene_no], task_name=task)

            pprint(ch_video.keys())
            pprint(scenes[scene_no])


        # for scene in scenes:
        #     print(lightcyan(f"Scene no. {scene['no']}"))
        #     pprint(scene)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
