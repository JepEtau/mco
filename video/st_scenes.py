from datetime import datetime
import math
import numpy as np
import subprocess
import sys
import os
import time
from pprint import pprint

from parsers._types import VideoSettings
from parsers.p_print import pprint_scene_mapping
from scene.consolidate import consolidate_scene
from scene.src_scene import SrcScene
from utils.hash import calc_hash
from utils.mco_types import Scene, ChapterVideo
from utils.mco_utils import is_up_to_date, scene_id_str
from utils.media import extract_media_info, vcodec_to_extension
from utils.p_print import *
from utils.tools import ffmpeg_exe
from parsers import (
    db,
    Chapter,
    all_chapter_keys,
    key,
    TaskName,
    ProcessingTask,
    Filter,
)



def st_scenes(
    episode: str,
    single_chapter: Chapter = '',
    task: TaskName = '',
    force: bool = False,
    simulation: bool = False,
    scene_no: int | None = None,
    edition: str | None = None,
    debug: bool = False,
):
    k_ep = key(episode)
    k_ed = edition
    chapters: Chapter = all_chapter_keys() if single_chapter == '' else [single_chapter]

    do_concatenate_video: bool = (
        True
        if single_chapter == '' # or single_chapter in ('g_debut', 'g_fin')
        else False
    )

    if k_ep == '' and single_chapter not in ('g_debut', 'g_fin'):
        raise ValueError(red("[E] episode must be set"))

    start_time_full = time.time()
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
            # pprint(ch_video)
            print(f"scene_no: {scene_no}")

        # Walk through target scenes
        scenes: list[Scene] = ch_video['scenes']
        for scene in scenes:
            scene_id: str = scene_id_str(scene)
            start_time = time.time()
            if scene_no is not None and scene_no != -1 and scene['no'] != scene_no:
                continue
            pprint_scene_mapping(scene)

            # Consolidate this scene
            consolidate_scene(scene, task_name=task)


            if debug:
                print(lightcyan(f"======================= generate_{task}_scenes: Scene ============================="))
                # pprint(scene)
                print(lightcyan("==============================================================================="))

            in_fp: str = scene['task'].in_video_file
            in_mtime: float = 0
            # in_mtime_str: str = "-"
            if os.path.exists(in_fp):
                in_mtime = os.path.getmtime(in_fp)
                # in_mtime_str = datetime.fromtimestamp(in_mtime).strftime("%Y-%m-%d %H:%M:%S")
            else:
                print(red(f"{scene_id}: missing input file:"), in_fp)
                continue
            # print(f"input: {in_fp}\n  {in_mtime_str}")

            out_fp: str = scene['task'].video_file
            out_mtime: float = 0
            out_mtime_str: str = "-"
            if os.path.exists(out_fp):
                out_mtime = os.path.getmtime(out_fp)
                out_mtime_str = datetime.fromtimestamp(out_mtime).strftime("%Y-%m-%d %H:%M:%S")
            # print(f"output: {out_fp}\n  {out_mtime_str}")


            if out_mtime_str == "-":
                print(yellow(f"{scene_id}: stabilized scene is not generated"))

            elif out_mtime < in_mtime:
                print(yellow(f"{scene_id} has to be updated"))

