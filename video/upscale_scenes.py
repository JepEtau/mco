from collections import deque
import re
import sys
import os
import time
from pprint import pprint


from processing.upscale import UpscalePipeline
from nn_inference.resource_mgr import Frame
from scene.consolidate import consolidate_scene
from utils.images import Image, Images
from utils.mco_types import Scene, VideoChapter
from utils.p_print import *
from utils.path_utils import path_split, absolute_path
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
            set_video_filename(scene)

            if debug:
                print(lightcyan("================================== Scene ======================================="))
                pprint(scene)
                # pprint(scene['in_frames'])
                print(lightcyan("==============================================================================="))

    print(f"Total time: {time.time() - start_time_full:.03f}s")


    scenes_to_upscale: list[Scene] = []
    # in_frame_count: int = 0
    # out_frame_count: int = 0
    # video_count: int = 0
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
        models: set[str] = set()
        for scene in scenes:
            if scene_no is not None and scene['no'] != scene_no:
                continue

            # print(lightcyan("================================== Scene ======================================="))
            # pprint(scene)
            # print(lightcyan("==============================================================================="))
            out_video_fp: str = scene['task'].video_file
            # out_video_datetime: float = 0
            if os.path.exists(out_video_fp):
                continue
            #     out_video_datetime: float = os.stat(out_video_fp).st_mtime
            # max_img_datetime: float = 0

            # Get all models
            filter: str = scene['filters'][scene['task'].name].sequence
            models.add(filter)

            scenes_to_upscale.append(scene)

            os.makedirs(path_split(out_video_fp)[0], exist_ok=True)

            # do_generate_video = False
            # if len(frames) == 0:
            #     # Regenerate video if there is a newer imgage
            #     if max_img_datetime > out_video_datetime:
            #         do_generate_video = True
            # else:
            #     video_count += 1

            # if do_generate_video:
            #     if len(frames) == 0:
            #         scenes_to_combine.append(scene)
            #     elif not os.path.exists(out_video_fp):
            #         video_count += 1

    #     in_frame_count += len(frames)
    #     out_frame_count += len(frames)
    #     # break

    print(f"Total number of scenes to upscale: {len(scenes_to_upscale)}")
    # print(f"Total number of frames to generate clips: {out_frame_count}")
    # print(f"Total number of frames to process: {len(frames)}")
    # if len(frames) == 0:
    #     print(f"No frame to upscale")
    #     return
    # print(f"Total number of video clips to: {video_count}")

    # device: str = 'cuda'
    # fp16: bool = True

    # pipeline = UpscalePipeline(
    #     models,
    #     device,
    #     fp16,
    #     scenes_to_combine=scenes_to_combine,
    #     video_count=video_count,
    #     debug=debug,
    #     simulation=simulation,
    # )
    # pipeline.run()

    # 1. Upscale


    # 2. Add borders

    # 3. Generate video

    print("done")
