from pprint import pprint
import time
from import_parsers import *
from parsers import (
    db,
    TaskName,
    key,
    Chapter,
    all_chapter_keys,
    ProcessingTask,
    pprint_scene_mapping,
)
from utils.mco_types import Scene, ChapterVideo
from utils.p_print import *
from scene.consolidate import consolidate_scene
from utils.time_conversions import s_to_sexagesimal
from utils.hash import calc_hash


def consolidate_target(
    k_ep: str,
    k_p: str = '',
    task: TaskName = 'initial',
    debug: bool = False
):
    chapters: Chapter = all_chapter_keys()
    start_time = time.time()

    for k_ch in chapters:
        hashes_str = ''

        ch_video: ChapterVideo
        if k_ch in ('g_debut', 'g_fin'):
            ch_video = db[k_ch]['video']

        elif k_ep == 'ep00':
            sys.exit(red("Missing episode no."))

        else:
            ch_video = db[k_ep]['video']['target'][k_ch]

        # Do not generate clip for unused chapters
        if ch_video['count'] <= 0:
            continue

        ch_video['task'] = ProcessingTask(name=task)
        if debug:
            print(f"\n<<<<<<<<<<<<<<<<<<<<< {k_ch} >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

        # Walk through target scenes
        scenes: list[Scene] = ch_video['scenes']
        for scene in scenes:
            # pprint_scene_mapping(scene)

            # Set the last task
            scene['task'] = ProcessingTask(name=task)

            # Generate frames for this scene
            consolidate_scene(scene=scene)

            if debug:
                print(lightcyan("======================= consolidate_target: Scene ============================="))
                pprint(scene)
                print(lightcyan("==============================================================================="))

            # Calculate hash for the video
            hashes_str += f",{scene['task'].hashcode}"

            if debug:
                elapsed = time.time() - start_time
                print(purple(
                    f"\t\tscene no. {scene['no']} generated in "
                    f"{s_to_sexagesimal(elapsed)} ({elapsed/scene['dst']['count']:02f}s/f)\n"
                ))

            # if debug:
            #     print(lightcyan("================================== Scene ======================================="))
            #     pprint(scene)
            #     print(lightcyan("==============================================================================="))
                # sys.exit()

        hashcode: str = calc_hash(hashes_str[:-1])
        ch_video['task'] = ProcessingTask(
            name=task,
            hashcode=hashcode,
            concat_file="not_applicable",
            video_file="not_applicable",
        )
    print(f"Consolidated in {time.time() - start_time:.02f}s")
