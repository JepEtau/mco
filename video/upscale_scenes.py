from collections import deque
import math
import re
import subprocess
import sys
import os
import time
from pprint import pprint

import numpy as np


from nn_inference.model_mgr import ModelManager
from nn_inference.threads.t_decoder import VideoStreamInfo
from processing.decoder import decoder_frame_prop
from processing.upscale import UpscalePipeline
from nn_inference.resource_mgr import Frame
from scene.consolidate import consolidate_scene
from utils.images import Image, Images
from utils.images_io import write_image
from utils.mco_types import Scene, VideoChapter
from utils.media import extract_media_info
from utils.p_print import *
from utils.path_utils import path_split, absolute_path
from utils.mco_utils import makedirs
from utils.tools import ffmpeg_exe
from parsers import (
    db,
    Chapter,
    all_chapter_keys,
    key,
    TaskName,
    ProcessingTask,
    task_to_dirname,
    Filter,
)
from .concat_frames import (
    set_concat_filename,
    set_video_filename,
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
    debug: bool = False
):

    k_ep = key(episode)
    k_ed = edition

    # Create the video directory for this episode or chapter
    makedirs(k_ep, single_chapter, 'video')

    # Create the scen vclip chapter by chapter
    chapters: Chapter = all_chapter_keys() if single_chapter == '' else [single_chapter]

    start_time_full = time.time()
    for chapter in chapters:

        # k_ep_src is the default episode source used to generate a chapter
        k_ep_src: str = ''
        video: VideoChapter
        if chapter in ('g_debut', 'g_fin'):
            video = db[chapter]['video']
            k_ep_src: str = k_ep if task == 'initial' else video['src']['k_ep']

        elif k_ep is None or k_ep == 'ep00':
            sys.exit(red("Missing episode no."))

        else:
            # Use the source video clip if edition is specified
            # Used for study
            video = (
                db[k_ep]['video']['target'][chapter]
                if k_ed == ''
                else db[k_ep]['video'][k_ed][chapter]
            )
            k_ep_src = k_ep

        # Do not generate clip for unused chapters
        if video['count'] <= 0:
            continue

        if debug:
            print(lightcyan(chapter))

        video['task'] = ProcessingTask(name=task)

        # Walk through target scenes
        scenes: list[Scene] = video['scenes']
        for scene in scenes:
            if scene_no is not None and scene['no'] != scene_no:
                continue
            if scene_min != -1 and scene_max != -1:
                if scene['no'] < scene_min or scene['no'] > scene_max:
                    continue

            # Patch the for study mode
            if k_ed != '':
                scene.update({
                    'dst': {
                        'count': scene['count'],
                        'k_ed': k_ed,
                        'k_ep': k_ep,
                        'k_ch': chapter,
                    },
                    'src': {
                        'k_ed': k_ed,
                        'k_ep': k_ep_src,
                        'k_ch': chapter,
                    },
                    'k_ed': k_ed,
                    'k_ep': k_ep_src,
                    'k_ch': chapter,
                })

            if debug:
                print(
                    lightgreen(f"\t{scene['no']}: {scene['start']}"),
                    f"\t({scene['dst']['count']})\t<- {scene['k_ed']}:{scene['k_ep']}:{scene['k_ch']}",
                    f"   {scene['start']} ({scene['count']})"
                )

            # Set the last task
            scene['task'] = ProcessingTask(name=task)

            # Generate frames for this scene
            consolidate_scene(scene=scene)
            set_video_filename(scene)

    print(f"Total time: {time.time() - start_time_full:.03f}s")

    model_manager = ModelManager()

    scenes_to_upscale: list[Scene] = []
    for chapter in chapters:
        k_ep_src: str = ''
        video: VideoChapter
        if chapter in ('g_debut', 'g_fin'):
            video = db[chapter]['video']
            k_ep_src: str = k_ep if task == 'initial' else video['src']['k_ep']
        else:
            video = (
                db[k_ep]['video']['target'][chapter]
                if k_ed == ''
                else db[k_ep]['video'][k_ed][chapter]
            )
            k_ep_src = k_ep

        if video['count'] <= 0:
            continue

        # Walk through target scenes
        scenes: list[Scene] = video['scenes']
        total_frames: int = 0
        for scene in scenes:
            if scene_no is not None and scene['no'] != scene_no:
                continue
            if scene_min != -1 and scene_max != -1:
                if scene['no'] < scene_min or scene['no'] > scene_max:
                    continue

            # print(lightcyan("================================== Scene ======================================="))
            # pprint(scene)
            # print(lightcyan("==============================================================================="))
            if os.path.exists(scene['task'].video_file) and not force:
                continue

            # Get all models
            filters: Filter = scene['filters'][scene['task'].name]
            if filters.sequence == '':
                raise ValueError(red(
                    f"No filter defined for scene {scene['src']['k_ed']}:{scene['src']['k_ep']}:{scene['src']['k_ch']}:{scene['src']['no']}"
                ))

            if len(filters.steps) != 0:
                print(yellow(f"sequence already parsed: scene {scene['src']['k_ed']}:{scene['src']['k_ep']}:{scene['src']['k_ch']}:{scene['src']['no']}"))

            for model in filters.sequence.split(','):
                if '.pth' not in model:
                    raise NotImplementedError(f"{scene['src']['k_ed']}:{scene['src']['k_ep']}:{scene['src']['k_ch']}:{scene['src']['no']}: {model}")
                model_key = model_manager.register(model)
                if model_key is None:
                    raise ValueError(red(f"[E] {model} is not a valid model"))
                filters.steps.append(model_key)

            scenes_to_upscale.append(scene)
            total_frames += scene['src']['count']


    print(f"Total number of scenes to upscale: {len(scenes_to_upscale)}")
    print(f"Total number of frames to upscale: {total_frames}")

    print(model_manager)
    if scenes_to_upscale and model_manager.count() == 0:
        raise ValueError(red("No models"))
    # sys.exit()

    if not len(scenes_to_upscale):
        print(f"No scenes to upscale")
        return

    vinfos: dict[str, VideoStreamInfo] = {}
    for scene in scenes_to_upscale:
        in_media_path = scene['inputs']['progressive']['filepath']
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
        scene['inputs']['progressive']['info'] = vinfos[in_media_path]

        if debug:
            print(lightcyan("================================== Scene ======================================="))
            pprint(scene)
            print(lightcyan("==============================================================================="))


    if False:
        command: str = [
            ffmpeg_exe,
            "-hide_banner",
            "-loglevel", "warning",
            "-nostats",
            "-ss", "3:48",
            "-i", scenes_to_upscale[0]['inputs']['progressive']['filepath'],
            "-t", "1",
            "-f", "image2pipe",
            "-pix_fmt", 'bgr24',
            "-vcodec", "rawvideo",
            "-"
        ]
        print(' '.join(command))

        sub_process: subprocess.Popen | None = None
        try:
            sub_process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                # stderr=sys.stdout,
            )
        except Exception as e:
            print(f"[E] Unexpected error: {type(e)}", flush=True)

        stdin_img_size = 768*576*3
        in_dtype = np.uint8
        i = 0
        # print(f"img size: {stdin_img_size}")
        while True:
            try:
                img: np.ndarray = np.frombuffer(
                    sub_process.stdout.read(stdin_img_size),
                    dtype=in_dtype
                ).reshape((576, 768, 3))
                # print(i)
                # write_image(f"test{i:05}.png", img)
                i += 1
                # if i == 25:
                #     break
            except:
                break


    device: str = 'cuda'
    fp16: bool = True

    pipeline = UpscalePipeline(
        device,
        fp16,
        scenes=scenes_to_upscale,
        total_frames=total_frames,
        debug=debug,
        simulation=simulation,
    )
    pipeline.run()

    print("done")
