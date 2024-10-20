import math
import re
import numpy as np
import subprocess
import sys
import os
import time
from pprint import pprint

from nn_inference.model_mgr import ModelManager
from nn_inference.threads.t_decoder import VideoStreamInfo
from parsers._types import VideoSettings
from parsers.p_print import pprint_scene_mapping
from processing.upscale import UpscalePipeline
from processing import supported_filters
from scene.consolidate import consolidate_scene
from scene.src_scene import SrcScene
from utils.hash import calc_hash
from utils.mco_types import Scene, ChapterVideo
from utils.mco_utils import is_up_to_date
from utils.media import extract_media_info, vcodec_to_extension
from utils.p_print import *
from utils.tools import ffmpeg_exe
from parsers import (
    db,
    Chapter,
    all_chapter_keys,
    ep_key,
    TaskName,
    ProcessingTask,
    Filter,
)



def upscale_scenes(
    episode: str,
    single_chapter: Chapter = '',
    task: TaskName = '',
    force: bool = False,
    simulation: bool = False,
    scene_no: int | None = None,
    scene_min: int = -1,
    scene_max: int = -1,
    watermark: bool = False,
    edition: str | None = None,
    debug: bool = False,
    evaluation: bool = False,
):
    k_ep = ep_key(episode)
    k_ed = edition
    chapters: Chapter = all_chapter_keys() if single_chapter == '' else [single_chapter]

    do_concatenate_video: bool = (
        True
        if single_chapter == '' # or single_chapter in ('g_debut', 'g_fin')
        else False
    )

    if k_ep == '' and single_chapter not in ('g_debut', 'g_fin'):
        raise ValueError(red("[E] episode must be set"))

    # List models and scenes to upscale
    model_manager = ModelManager()
    scenes_to_upscale: list[Scene] = []
    total_frames: int = 0

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
            print(f"scene_no: {scene_no}, scenes range: {scene_min} -> {scene_max}")

        # Walk through target scenes
        scenes: list[Scene] = ch_video['scenes']
        for scene in scenes:
            start_time = time.time()
            if scene_no is not None and scene_no != -1 and scene['no'] != scene_no:
                print(f"skip scene no. {scene['no']}")
                continue
            if scene_min != -1 and scene_max != -1:
                if scene['no'] < scene_min or scene['no'] > scene_max:
                    continue

            pprint_scene_mapping(scene)

            # Set the last task
            scene['task'] = ProcessingTask(name=task)

            # Generate frames for this scene
            consolidate_scene(scene=scene, watermark=watermark, evaluation=evaluation)

            if debug:
                print(lightcyan("======================= consolidate scene for upscale ============================="))
                pprint(scene)
                print(lightcyan("==============================================================================="))


            # Calculate hash for the video
            hashes_str += f",{scene['task'].hashcode}"

            # Add models to the model manager
            # and add the scene to the list to upscale
            if not is_up_to_date(scene) or force:

                # Get all models
                scene_filters: Filter = scene['filters'][scene['task'].name]
                src_scene: SrcScene = scene['src'].primary_scene()
                if scene_filters.sequence == '':
                    raise ValueError(red(
                        f"No filter defined for scene {src_scene['k_ed_ep_ch_no']}"
                    ))

                if len(scene_filters.steps) != 0:
                    print(yellow(f"sequence already parsed: scene {src_scene['k_ed_ep_ch_no']}"))
                pprint(scene_filters)

                # regex = rf"^({'|'.join(supported_filters)})"
                for filter_str in scene_filters.sequence.split(','):
                    # if (result := re.search(re.compile(regex), filter_str)):
                    if filter_str.startswith(supported_filters):
                        print(lightgreen("supported:"), filter_str)
                        # filter_params = ()
                        params: list[str] = filter_str.split("=")
                        # scene_filters.steps.append((result.group(1),))
                        filter_name = params[0]
                        filter_params: str | float | None = None
                        if len(params) is not None:
                            filter_params = None

                        if filter_name == 'resize':
                            filter_params = float(params[1])
                        elif len(params) == 1:
                            filter_params = None
                        else:
                            filter_params = params[1]

                        scene_filters.steps.append(
                            (params[0], filter_params)
                        )
                        continue

                    model: str = filter_str
                    model_key = model_manager.register(model)
                    if model_key is None:
                        raise ValueError(red(f"[E] {model} is not a valid model"))
                    scene_filters.steps.append(model_key)

                pprint(scene_filters)

                scenes_to_upscale.append(scene)
                total_frames += (
                    scene['src'].frame_count(exclude_loop=True)
                    - len(scene['src'].get_frame_replace().keys())
                )

        hashcode: str = calc_hash(hashes_str[:-1])
        basename: str = f"{k_ed}_{k_ep}_{k_ch}_{task}_{hashcode}"
        cache_path = (
            db[k_ch]['cache_path']
            if k_ch in ('g_debut', 'g_fin')
            else db[k_ep]['cache_path']
        )

        ch_vsettings: VideoSettings = db['common']['video_format'][task]
        ext: str = vcodec_to_extension[ch_vsettings.codec]
        ch_video['task'] = ProcessingTask(
            name=task,
            hashcode=hashcode,
            concat_file=os.path.join(cache_path, "concat", f"{basename}.txt"),
            video_file=os.path.join(cache_path, f"video_lr", f"{basename}{ext}"),
            video_settings=ch_vsettings,
        )

    print(f"Consolidated scenes: {time.time() - start_time_full:.03f}s")
    print(f"Total number of scenes to upscale: {len(scenes_to_upscale)}")
    print(f"Total number of frames to upscale: {total_frames}")

    print(model_manager)
    if scenes_to_upscale and model_manager.count() == 0:
        raise ValueError(red("No models"))

    if not len(scenes_to_upscale):
        print(f"No scenes to upscale")
        return

    # Extract video before to optimize processing
    # avoid extracting multiple time info from the same input
    vinfos: dict[str, VideoStreamInfo] = {}
    for scene in scenes_to_upscale:
        for src_scene in scene['src'].scenes():
            progressive_input = src_scene['scene']['inputs']['progressive']

            in_media_path = progressive_input['filepath']
            if in_media_path not in vinfos:

                in_video_info = extract_media_info(in_media_path)['video']
                # force output to rgb
                d_c_order = 'rgb'
                if in_video_info['bpp'] > 8:
                    d_dtype = np.uint16
                    pix_fmt = f"{d_c_order}48"
                else:
                    d_dtype = np.uint8
                    pix_fmt = f"{d_c_order}24"
                stdin_img_nbytes = math.prod(in_video_info['shape']) * np.dtype(d_dtype).itemsize

                vinfos[in_media_path] = VideoStreamInfo(
                    img_dtype=d_dtype,
                    img_c_order=d_c_order,
                    img_shape=in_video_info['shape'],
                    img_nbytes=stdin_img_nbytes,
                    pix_fmt=pix_fmt,
                    frame_rate=in_video_info['frame_rate_r'],
                    metadata=in_video_info['metadata'],
                )
                scene['task'].video_settings.metadata = vinfos[in_media_path].metadata
            progressive_input['info'] = vinfos[in_media_path]

        if debug:
            print(lightcyan("================================== Scene ======================================="))
            pprint(scene)
            print(lightcyan("==============================================================================="))


    device: str = 'cuda'

    pipeline = UpscalePipeline(
        device,
        scenes=scenes_to_upscale,
        total_frames=total_frames,
        debug=debug,
        simulation=simulation,
    )

    pipeline.run()

    print("done")
