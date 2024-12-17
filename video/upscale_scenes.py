import math
import numpy as np
import sys
import os
from pprint import pprint
import time

from nn_inference.model_mgr import ModelManager
from nn_inference.threads.t_decoder import VideoStreamInfo
from nn_inference.toolbox.upscale_doc import (
    upscale_doc_scenes,
    upscale_doc_chapter,
)

from parsers._types import VideoSettings
from parsers.p_print import pprint_scene_mapping
from processing.upscale import UpscalePipeline
from processing import supported_filters
from scene.consolidate import consolidate_scene
from scene.src_scene import SrcScene
from utils.hash import calc_hash
from utils.mco_types import Scene, ChapterVideo
from utils.mco_utils import is_up_to_date, extract_media_info_mco
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
    model_manager = ModelManager()
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

        if k_ch == 'doc':
            upscale_doc_chapter(
                ch_video=ch_video,
                debug=debug,
                force=force
            )
            continue


        # Walk through target scenes
        scenes: list[Scene] = ch_video['scenes']
        for scene in scenes:

            if scene_no is not None and scene_no != -1 and scene['no'] != scene_no:
                print(f"skip scene no. {scene['no']}")
                continue

            if scene_min != -1 and scene_max != -1:
                if scene['no'] < scene_min or scene['no'] > scene_max:
                    continue

            if k_ed is not None and k_ed:
                if scene['src'].get_edition() != k_ed:
                    continue

            pprint_scene_mapping(scene)

            # Set the last task
            scene['task'] = ProcessingTask(name=task_name)

            # Generate frames for this scene
            consolidate_scene(scene=scene, watermark=watermark, evaluation=evaluation)

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

                # Separate doc from other
                # because it uses different upscalers
                pprint(scene_filters)
                # if scene_filters.sequence == 'doc':
                #     # For documentary, there is no frame replace... yet
                #     scenes_to_upscale_doc.append(scene)
                #     total_frames += scene['src'].frame_count(exclude_loop=True)
                # else:
                for filter_str in scene_filters.sequence.split(','):
                    if filter_str.startswith(supported_filters):
                        print(lightgreen("supported:"), filter_str)
                        params: list[str] = filter_str.split("=", maxsplit=1)
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

                    # Doc model must not be followed by any model
                    elif filter_str.startswith('mco_doc'):
                        # Save the output as intermediary file -> patch this file
                        scene['task'].fallback_in_video_files['hr'] = scene['task'].video_file
                        scene['task'].video_file = (
                            scene['task'].video_file.replace("_hr", "_hr_tmp")
                        )
                        scene['task'].in_video_file = scene['task'].video_file
                        scenes_to_upscale_doc.append(scene)
                        break

                    model: str = filter_str
                    model_key = model_manager.register(model)
                    if model_key is None:
                        raise ValueError(red(f"[E] {model} is not a valid model"))
                    scene_filters.steps.append(model_key)
                print(lightcyan(f"Scene {scene['no']} filters:"))
                pprint(scene_filters)

                # if scene['dst']['k_ch'] not in ('g_doc', 'doc'):
                scenes_to_upscale.append(scene)
                total_frames += (
                    scene['src'].frame_count(exclude_loop=True)
                    - len(scene['src'].get_frame_replace().keys())
                )


        hashcode: str = calc_hash(hashes_str[:-1])
        basename: str = f"{k_ed}_{k_ep}_{k_ch}_{task_name}_{hashcode}"
        cache_path = (
            db[k_ch]['cache_path']
            if k_ch in ('g_debut', 'g_fin')
            else db[k_ep]['cache_path']
        )

        ch_vsettings: VideoSettings = db['common']['video_format'][task_name]
        ext: str = vcodec_to_extension[ch_vsettings.codec]
        ch_video['task'] = ProcessingTask(
            name=task_name,
            hash=hashcode,
            concat_file=os.path.join(cache_path, "concat", f"{basename}.txt"),
            video_file=os.path.join(cache_path, f"video_lr", f"{basename}{ext}"),
            video_settings=ch_vsettings,
        )

    print(f"Consolidated scenes: {time.time() - start_time_full:.03f}s")
    print(f"Total number of scenes to upscale: {len(scenes_to_upscale)}")
    print(f"Total number of scenes to upscale (doc): {len(scenes_to_upscale_doc)}")
    print(f"Total number of frames to upscale: {total_frames}")

    if model_manager.count():
        print(model_manager)

    if scenes_to_upscale and model_manager.count() == 0:
        raise ValueError(red("No models"))

    if not scenes_to_upscale and not scenes_to_upscale_doc:
        print(f"No scenes to upscale")
        return


    # Extract video info before to optimize processing
    # avoid extracting multiple time info from the same input
    vinfos: dict[str, VideoStreamInfo] = {}
    for scene in scenes_to_upscale + scenes_to_upscale_doc:
        if sys.platform != 'win32':
            break

        for src_scene in scene['src'].scenes():
            progressive_input = src_scene['scene']['inputs'].progressive()

            in_media_path = progressive_input.filepath
            if in_media_path not in vinfos:
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

                vinfos[in_media_path] = VideoStreamInfo(
                    img_dtype=d_dtype,
                    img_c_order=d_c_order,
                    img_shape=in_video_info['shape'],
                    img_nbytes=stdin_img_nbytes,
                    pix_fmt=pix_fmt,
                    frame_rate=in_video_info['frame_rate_r'],
                    metadata=in_video_info['metadata'],
                )
                scene['task'].video_settings.metadata.update(vinfos[in_media_path].metadata)
            progressive_input.info = vinfos[in_media_path]

        if debug:
            print(lightcyan(f"========================= Scene {scene['no']} ================================="))
            pprint(scene)
            print(lightcyan("==============================================================================="))


    device: str = 'cuda'
    # pprint(scenes_to_upscale)
    if scenes_to_upscale:
        pipeline = UpscalePipeline(
            device,
            scenes=scenes_to_upscale,
            total_frames=total_frames,
            debug=debug,
            simulation=simulation,
        )
        pipeline.run()

    if scenes_to_upscale_doc:
        upscale_doc_scenes(
            scenes=scenes_to_upscale_doc,
            debug=debug,
            force=force
        )

    print("done")
