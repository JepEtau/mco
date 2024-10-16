import sys
import os
from pprint import pprint

import numpy as np

from nn_inference.toolbox.resize_to_4_3 import ConvertTo43Params, calculate_transformation_values, dimensions_from_crop
from scene.consolidate import consolidate_scene
from utils.mco_types import Scene, ChapterVideo, SceneGeometry
from utils.mco_utils import scene_id_str
from utils.media import VideoInfo, extract_media_info
from utils.p_print import *
from parsers import (
    FINAL_WIDTH,
    db,
    Chapter,
    all_chapter_keys,
    key,
    TaskName,
    ProcessingTask,
    pprint_scene_mapping,
    FINAL_HEIGHT,
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

        if geometry_stats:
            geometry_crops: list[list[int, int, int, int]] = []
            ch_width: int = ch_video['geometry'].width

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
                        os.symlink(src_fp, fp)


            if geometry_stats:
                geometry: SceneGeometry = scene['geometry']
                crop_values: list[int, int, int, int] = (
                    geometry.autocrop
                    if geometry.use_autocrop
                    else geometry.crop
                )

                if any(crop_values) == 0:
                    # Not valid:
                    print(red("crop is missing"))
                else:
                    geometry_crops.append(crop_values)

                    in_vi: VideoInfo = extract_media_info(scene['task'].in_video_file)['video']
                    in_h, in_w = in_vi['shape'][:2]

                    c_t, c_b, c_l, c_r, c_w, c_h = dimensions_from_crop(in_w, in_h, crop_values)
                    print(lightgrey(f"-> cropped size ({c_w}, {c_h}). Crop values: [{c_t}, {c_b}, {c_l}, {c_r}]"))

                    to_43_params: ConvertTo43Params = ConvertTo43Params(
                        crop=crop_values,
                        keep_ratio=geometry.keep_ratio,
                        fit_to_width=geometry.fit_to_width,
                        final_height=FINAL_HEIGHT,
                        scene_width=ch_width,
                    )
                    transformation = calculate_transformation_values(
                        in_w=in_w,
                        in_h=in_h,
                        out_w=FINAL_WIDTH,
                        params=to_43_params,
                        verbose=True
                    )


        scene_crops: np.ndarray = np.array(geometry_crops)
        pprint(scene_crops)

