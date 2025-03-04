import gc
import math
import numpy as np
import sys
import os
from pprint import pprint
import time

import torch
from nn_inference.threads.t_progress import ProgressThread
from nn_inference.model_mgr import ModelManager
from nn_inference.resource_mgr import ResourceManager
from nn_inference.threads.t_decoder import VideoStreamInfo
from nn_inference.toolbox.upscale_doc import (
    consolidate_initial_doc,
    consolidate_initial_doc_scenes,
    upscale_doc_scenes,
    upscale_doc_chapter,
)

from parsers.p_print import pprint_scene_mapping
from scene.upscale_scene import UpscalePipeline
from processing import supported_filters
from scene.consolidate import consolidate_scene
from scene.src_scene import SrcScene
from utils.mco_types import Scene, ChapterVideo
from utils.mco_utils import (
    is_up_to_date,
    extract_media_info_mco,
    calculate_scene_frame_count,
)
from utils.media import vcodec_to_extension
from utils.p_print import *
from parsers import (
    db,
    Chapter,
    all_chapter_keys,
    ep_key,
    TaskName,
    ProcessingTask,
    Filter,
    calc_hash,
    VideoSettings,
)



def upscale_scenes(
    episode: str,
    single_chapter: Chapter = '',
    task_name: TaskName = '',
    force: bool = False,
    simulation: bool = False,
    scene_no: int | None = None,
    scene_min: int = -1,
    scene_max: int = -1,
    scene_list: list[int] = [],
    watermark: bool = False,
    edition: str | None = None,
    debug: bool = False,
    compare: bool = False,
):
    k_ep = ep_key(episode)
    k_ed = edition
    chapters: Chapter = all_chapter_keys() if single_chapter == '' else [single_chapter]

    do_concatenate_video: bool = (
        True
        if single_chapter == '' # or single_chapter in ('g_debut', 'g_fin')
        else False
    )

    if (
        (k_ep is None or k_ep in ('', 0))
        and single_chapter not in ('g_debut', 'g_fin', 'g_doc')
    ):
        raise ValueError(red("[E] episode must be set"))

    print(f"upscale_scenes: {edition}:{episode}:{single_chapter}")
    if single_chapter in ('g_doc'):
        pprint(db['ep01']['video']['target'].keys())
    # print(k_ep)
    # raise

    # List models and scenes to upscale
    scenes_to_upscale: list[Scene] = []
    scenes_to_upscale_doc: list[Scene] = []
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

        ch_video['task'] = ProcessingTask(name=task_name)
        if debug:
            print(f"\n<<<<<<<<<<<<<<<<<<<<< {k_ch} >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            # pprint(ch_video)
            print(f"scene_no: {scene_no}, scenes range: {scene_min} -> {scene_max}")

        # if k_ch == 'doc':
        #     upscale_doc_chapter(
        #         ch_video=ch_video,
        #         debug=debug,
        #         force=force
        #     )
        #     continue

        # For optimization, cache input video info to avoid doing this at every scene
        cached_video_info: dict[str, VideoStreamInfo] = {}

        # Walk through target scenes
        scenes: list[Scene] = ch_video['scenes']
        for scene in scenes:

            if scene_no is not None and scene_no != -1 and scene['no'] != scene_no:
                # print(f"skip scene no. {scene['no']}")
                continue

            if scene_min != -1:
                if scene['no'] < scene_min:
                    continue

            if scene_max != -1:
                if scene['no'] > scene_max:
                    continue

            if scene_list:
                if scene['no'] not in scene_list:
                    continue

            if k_ed is not None and k_ed:
                if scene['src'].get_edition() != k_ed:
                    continue

            pprint_scene_mapping(scene)

            # Set the last task
            scene['task'] = ProcessingTask(name=task_name)

            # Generate frames for this scene
            consolidate_scene(scene=scene, watermark=watermark, compare=compare)

            if debug:
                print(lightcyan("======================= consolidate scene for upscale ============================="))
                pprint(scene)
                print(lightcyan("==============================================================================="))

            # Calculate hash for the video
            hashes_str += f",{scene['task'].hash}"

            # Windows only
            # if sys.platform != 'win32':
            #     continue

            # Add models to the model manager
            # and add the scene to the list to upscale
            if not is_up_to_date(scene, display_msg=True) or force:
                scenes_to_upscale.append(scene)
                total_frames += calculate_scene_frame_count(scene)

                # Parse input video, but do this only if needed
                for src_scene in scene['src'].scenes():
                    progressive_input = src_scene.in_scene['inputs'].progressive()

                    in_media_path = progressive_input.filepath
                    if in_media_path not in cached_video_info:
                        in_video_info = extract_media_info_mco(in_media_path)['video']
                        # Force output to rgb
                        d_c_order = 'rgb'
                        if in_video_info['bpp'] > 8:
                            d_dtype = np.uint16
                            pix_fmt = f"{d_c_order}48"
                        else:
                            d_dtype = np.uint8
                            pix_fmt = f"{d_c_order}24"
                        stdin_img_nbytes = math.prod(in_video_info['shape']) * np.dtype(d_dtype).itemsize

                        cached_video_info[in_media_path] = VideoStreamInfo(
                            img_dtype=d_dtype,
                            img_c_order=d_c_order,
                            img_shape=in_video_info['shape'],
                            img_nbytes=stdin_img_nbytes,
                            pix_fmt=pix_fmt,
                            frame_rate=in_video_info['frame_rate_r'],
                            metadata=in_video_info['metadata'],
                        )
                        scene['task'].video_settings.metadata.update(cached_video_info[in_media_path].metadata)
                    progressive_input.info = cached_video_info[in_media_path]


        hashcode: str = calc_hash(hashes_str[:-1])
        basename: str = f"{k_ed}_{k_ep}_{k_ch}_{task_name}_{hashcode}"
        cache_path = (
            db[k_ch]['cache_path']
            if k_ch in ('g_debut', 'g_fin')
            else db[k_ep]['cache_path']
        )

        ch_vsettings: VideoSettings = db['vsettings'][task_name]
        ext: str = vcodec_to_extension[ch_vsettings.codec]
        ch_video['task'] = ProcessingTask(
            name=task_name,
            hash=hashcode,
            concat_file=os.path.join(cache_path, "concat", f"{basename}.txt"),
            video_file=os.path.join(cache_path, f"video_lr", f"{basename}{ext}"),
            video_settings=ch_vsettings,
        )

    print(lightcyan(f"Consolidated scenes:"), f"{time.time() - start_time_full:.03f}s")
    print(lightcyan(f"Total number of scenes to upscale:"), f"{len(scenes_to_upscale)}")
    print(lightcyan(f"Total number of frames to upscale:"), f"{total_frames}")

    # Create a progress bar
    f_progress_thread: ProgressThread | None = None
    if total_frames:
        f_progress_thread = ProgressThread(total=total_frames)
        ResourceManager().register_thread(f_progress_thread)

    # Now upscale scenes
    for scene in scenes_to_upscale:
        print(lightgreen("Scene no. "), scene['no'])
        # Get all models
        model_manager = ModelManager()
        scene_filters: Filter = scene['filters'][scene['task'].name]
        src_scene: SrcScene = scene['src'].primary_scene()
        if scene_filters.sequence == '':
            raise ValueError(red(
                f"No filter defined for scene {src_scene['k_ed_ep_ch_no']}"
            ))

        if len(scene_filters.steps) != 0:
            print(yellow(f"sequence already parsed: scene {src_scene['k_ed_ep_ch_no']}"))

        # Separate doc from other
        # because it uses different upscalers
        # pprint(scene_filters)
        # if scene_filters.sequence == 'doc':
        #     # For documentary, there is no frame replace... yet
        #     scenes_to_upscale_doc.append(scene)
        #     total_frames += scene['src'].frame_count(exclude_loop=True)
        # else:
        for filter_str in scene_filters.sequence.split(','):
            if filter_str.startswith(supported_filters):
                print(darkgrey("supported:"), filter_str)
                params: list[str] = filter_str.split("=", maxsplit=1)
                filter_name = params[0]
                filter_params: str | float | None = None
                if len(params) is not None:
                    filter_params = None

                if filter_name == 'resize':
                    filter_params = float(params[1])

                elif filter_name == 'rotate90':
                    filter_params = (
                        int(params[1])
                        if len(params) > 1
                        else 1
                    )

                elif len(params) == 1:
                    filter_params = None

                else:
                    filter_params = params[1]

                scene_filters.steps.append((params[0], filter_params))
                continue

            # Doc model must not be followed by any model
            elif filter_str.startswith('mco_doc'):
                # Save the output as intermediary file -> patch this file
                scene['task'].fallback_in_video_files['hr'] = scene['task'].video_file
                scene['task'].video_file = (
                    scene['task'].video_file.replace("_hr", "_hr_tpz")
                )
                scene['task'].in_video_file = scene['task'].video_file
                scenes_to_upscale_doc.append(scene)
                break

            elif filter_str.startswith('dvr'):
                scenes_to_upscale_doc.append(scene)
                break

            model: str = filter_str
            model_key = model_manager.register(model)
            if model_key is None:
                raise ValueError(red(f"[E] {model} is not a valid model"))
            scene_filters.steps.append(model_key)
        # print(lightcyan(f"Scene {scene['no']} filters:"))
        # pprint(scene_filters)


        if model_manager.count():
            print(model_manager)

        pipeline = UpscalePipeline(
            device="cuda:0",
            scene=scene,
            model_manager=model_manager,
            progress_thread=f_progress_thread,
            debug=debug,
            simulation=simulation,
        )
        err, encoded = pipeline.run()

        # Delete modele manager, memory allocation, empty cache
        model_manager.clean()
        del model_manager
        gc.collect()
        torch.cuda.empty_cache()

    if f_progress_thread is not None:
        f_progress_thread.put(0, force=True)
        total_elapsed: float = f_progress_thread.elapsed()
        while True:
            if f_progress_thread is not None and f_progress_thread.is_alive():
                f_progress_thread.stop(force=True)
                time.sleep(0.1)
            else:
                break

    if scenes_to_upscale_doc:
        print(f"Total number of scenes to upscale (doc): {len(scenes_to_upscale_doc)}")
        for scene in scenes_to_upscale_doc:

            # consolidate_initial_doc_scenes(ch_video=ch_video)
            filters: Filter = (
                ch_video['scenes'][0]['filters'][task_name]
                if scene_no is None
                else ch_video['scenes'][scene_no]['filters'][task_name]
            )

            if 'mco_doc' in filters.sequence:
                # consolidate_initial_doc(ch_video, debug=debug)
                upscale_doc_scenes(
                    scenes=scenes_to_upscale_doc,
                    debug=debug,
                    force=force
                )

    if not scenes_to_upscale and not scenes_to_upscale_doc:
        print(f"No scenes to upscale")
        return


    print("done")
