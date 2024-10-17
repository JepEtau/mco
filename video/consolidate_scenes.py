import sys
import os
from pprint import pprint
from scene.consolidate import consolidate_scene
from utils.geometry_utils import ChGeometryStats
from utils.mco_types import Scene, ChapterVideo
from utils.mco_utils import scene_id_str
from utils.p_print import *
from parsers import (
    db,
    Chapter,
    all_chapter_keys,
    key,
    TaskName,
    ProcessingTask,
    pprint_scene_mapping,
)



def consolidate_scenes(
    episode: str,
    single_chapter: Chapter,
    scene_no: int | None = None,
    task: TaskName = '',
    debug: bool = False,
    symlink: bool = False,
    geometry_stats: bool = False,
):
    k_ep = key(episode)
    chapters: Chapter = all_chapter_keys() if single_chapter == '' else [single_chapter]

    if k_ep == '' and single_chapter not in ('g_debut', 'g_fin'):
        raise ValueError(red("[E] episode must be set"))

    for k_ch in chapters:

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
            print(f"scene_no: {scene_no}")


        # Walk through target scenes
        scenes: list[Scene] = ch_video['scenes']
        for scene in scenes:
            if scene_no is not None and scene_no != -1 and scene['no'] != scene_no:
                continue
            pprint_scene_mapping(scene)

            # Consolidate this scene
            consolidate_scene(scene, task_name=task)
            scene_id: str = scene_id_str(scene)

            if debug:
                print(lightcyan(f"======================= generate_{task}_scenes: {scene_id} ============================="))
                pprint(scene)
                print(lightcyan("==============================================================================="))

            # Create symbolic links
            if symlink:
                for tn in ('tf', 'st'):
                    fp: str = scene['task'].fallback_in_video_files[tn]
                    if os.path.exists(fp) and os.path.islink(fp):
                        print(lightcyan(f"remove symlink"), f"{fp}")
                        os.unlink(fp)

                previous = {
                    'st': 'hr',
                    'tf': 'st',
                }

                for tn in ('st', 'tf'):
                    fp: str = scene['task'].fallback_in_video_files[tn]
                    if not os.path.exists(fp):
                        src_fp: str = scene['task'].fallback_in_video_files[previous[tn]]
                        print(lightcyan(f"create a symlink: "), f"{os.path.split(src_fp)[-1]} <- {os.path.split(fp)[-1]}")
                        if not os.path.exists(src_fp):
                            raise FileNotFoundError(red(f"{src_fp}"))
                        os.symlink(src_fp, fp)


        if geometry_stats:
            ch_geometry_stats: ChGeometryStats = ChGeometryStats()
            for scene in scenes:
                ch_geometry_stats.append(scene)
            print(f"valid scenes: {ch_geometry_stats.valid_scenes()}")
            print(f"erroneous scenes: {ch_geometry_stats.erroneous_scenes()}")
            print(f"undefined scenes: {ch_geometry_stats.undefined_scenes()}")
            print(f"max theoretical width: {ch_geometry_stats.max_width()}")
            print(f"MIN max width: {ch_geometry_stats.min_max_width_scene()}")
            print(f"fit to width: {ch_geometry_stats.fit_to_width_scenes()}")
            print(f"anamorphic: {ch_geometry_stats.anamorphic_scenes()}")
