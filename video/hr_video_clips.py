from collections import deque
import re
import sys
import os
import time
from pprint import pprint


from processing.upscale import UpscalePipeline
from nn_inference.threads.common import Frame
from scene.consolidate import consolidate_scene

from utils.logger import main_logger
from utils.mco_types import Scene, VideoChapter
from utils.p_print import *
from utils.path_utils import path_split, absolute_path
from utils.time_conversions import s_to_sexagesimal
from utils.tools import ffmpeg_exe
from utils.mco_utils import makedirs
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
from video.frame_list import get_frame_list
from .concat_frames import (
    generate_concat_file,
    generate_silence_concat_file,
    generate_video_concat_file,
    set_concat_filename,
    set_video_filename,
)
from .concat_scenes import concat_scenes
from .combine_frames import combine_frames



def generate_hr_video_clip(
    episode: str,
    single_chapter: Chapter = '',
    task: TaskName = '',
    force: bool = False,
    simulation: bool = False,
    scene_no: int | None = None,
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
    in_frame_count: int = 0

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
            in_frame_count += len(scene['in_frames'])
            set_concat_filename(episode=k_ep_src, chapter=chapter, scene=scene)
            set_video_filename(scene)

            if debug:
                print(lightcyan("================================== Scene ======================================="))
                pprint(scene)
                print(lightcyan("==============================================================================="))

    print(f"Total number of frames to upscale: {in_frame_count}")
    print(f"Total time: {time.time() - start_time_full:.03f}s")


    frames: list = list()
    in_frame_count: int = 0
    out_frame_count: int = 0
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
        for scene in scenes:
            if scene_no is not None and scene['no'] != scene_no:
                continue

            # print(lightcyan("================================== Scene ======================================="))
            # pprint(scene)
            # print(lightcyan("==============================================================================="))
            dirname: str = task_to_dirname[scene['task'].name]
            task_no: str = dirname[:2]
            hashcode: str = scene['task'].hashcode
            out_video_fp: str = scene['task'].video_file
            for i, in_img in enumerate(scene['in_frames']):
                dir, basename, extension = path_split(in_img)
                # IMG_FILENAME_TEMPLATE
                if (result := re.search(re.compile(r"(.*__)\d{2}_[a-z0-9]{7}"), basename)):
                    basename = result.group(1)
                else:
                    raise ValueError(f"{basename} is not a valid basename")
                out_img: str = os.path.join(
                    absolute_path(os.path.join(dir, os.pardir, dirname)),
                    f"{basename}{task_no}_{hashcode}{extension}"
                )
                # print(f"{i:02d}: {in_img} -> {out_img}")

                if not os.path.exists(in_img):
                    raise ValueError(f"missing input file: {in_img}")

                if (
                    not os.path.exists(out_img)
                    or os.stat(in_img).st_mtime > os.stat(out_img).st_mtime
                ):
                    # print(f"regenerate {out_img}")
                    frames.append(
                        Frame(
                            in_img_fp=in_img,
                            out_img_fp=out_img,
                            scene_no=scene['no'],
                            scene=scene_no,
                            out_video_fp=out_video_fp
                        )
                    )
                    out_video_fp = ''


            in_frame_count += len(scene['in_frames'])
            out_frame_count += len(scene['out_frames'])
        break

    print(f"Total number of frames to upscale: {in_frame_count}")
    print(f"Total number of frames to generate clips: {out_frame_count}")
    print(f"Total number of frames to process: {len(frames)}")

    device: str = 'cuda'
    fp16: bool = True

    pipeline = UpscalePipeline(
        frames,
        device,
        fp16,
        debug
    )


    # 1. Upscale


    # 2. Add borders

    # 3. Generate video

