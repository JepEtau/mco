import os
from pprint import pprint
import sys

import numpy as np
from parsers import (
    db,
    Chapter,
    get_fps,
    ep_key,
    main_chapter_keys,
    ProcessingTask,
)
from parsers import TaskName
from processing.black_frame import generate_black_frame
from utils.images import Images
from utils.mco_types import Scene, ChapterVideo
from utils.mco_path import makedirs
from utils.mco_utils import run_simple_command
from utils.media import VideoInfo, extract_media_info
from utils.p_print import *
from utils.logger import main_logger
from utils.path_utils import absolute_path, path_split
from utils.time_conversions import ms_to_frame
from utils.tools import ffmpeg_exe


def get_silence_filepath(k_ep: str, chapter: str, task: TaskName) -> str:
    return os.path.join(
        db[k_ep]['cache_path'],
        "video",
        f"{k_ep}_{chapter}_silence_{task}.mkv"
    )


def set_video_filename(scene: Scene) -> None:
    scene['task'].video_file = absolute_path(
        get_video_filename(scene, task_name='')
    )


def get_video_filename(scene: Scene, task_name: TaskName = '') -> str:
    suffix: str = ''
    if task_name == '':
        task: ProcessingTask = scene['task']
        hashcode: str = task.hashcode
        task_name = task.name
    else:
        hashcode: str = scene['filters'][task_name].hash

    if hashcode != '' and task_name not in ('hr'):
        suffix += f"_{hashcode}"

    if task_name != '':
        suffix += f"_{task_name}"

    try:
        k_ed, k_ep, k_ch = scene['src']['k_ed'], scene['src']['k_ep'], scene['src']['k_ch']
    except:
        pprint(scene)
        raise
    cache_dir: str = db[k_ep]['cache_path']
    if k_ch in ('g_debut', 'g_fin'):
        cache_dir = db[k_ch]['cache_path']
        basename = f"{k_ch}_{scene['no']:03}__{k_ed}_{scene['k_ep']}"

    elif k_ch in ('g_asuivre', 'g_documentaire'):
        cache_dir = db[scene['dst']['k_ep']]['cache_path']
        basename = f"{scene['dst']['k_ep']}_{k_ch}_{0:03}__{k_ed}_{scene['src']['k_ep']}"

    else:
        basename = f"{k_ep}_{k_ch}_{scene['no']:03}__{k_ed}"

    folder_name: str = "video"
    if task_name == 'initial':
        folder_name = f"scenes_{scene['k_ed']}"
    elif task_name == 'hr':
        folder_name = 'scenes_hr'
    elif task_name == 'lr':
        folder_name = 'scenes_lr'
    elif task_name == 'restored':
        folder_name = 'restored'

    pprint(db['common'])
    sys.exit("get_video_filename")

    return absolute_path(
        os.path.join(cache_dir, folder_name, f"{basename}{suffix}.mkv")
    )







def generate_video_concat_file(
    episode: int | str,
    chapter: str,
):
    """ This function creates a concatenation file which lists
        all video files to merge:
        - precedemment
        - episode
        - g_asuivre
        - asuivre
        - g_documentaire
        - documentaire

        Returns:
          Concatenation file path
    """
    k_ep, k_ch = ep_key(episode), chapter
    verbose: bool = False
    main_logger.debug(f"create_video_concat_file {k_ep}:{k_ch}")

    # Assume language is same for k_ep and start/end/to_follow/documentary credits
    if k_ch in ('g_debut', 'g_fin'):
        language = db[k_ch]['audio']['lang']
    else:
        language = db[k_ep]['audio']['lang']
    lang_str = '' if language == 'fr' else f"_{language}"

    for k_ep_or_g in [k_ep, 'g_debut', 'g_fin']:
        if k_ep_or_g is None:
            continue

        if chapter != '' and k_ep_or_g != chapter:
            continue

        if k_ep_or_g in ('g_debut', 'g_fin'):
            k_ch = k_ep_or_g
            suffix = f"{k_ch}"
        else:
            suffix = f"_{k_ch}" if k_ch != '' else ''
            suffix = f"{k_ep}{suffix}_video"
            k_ep_or_g = k_ep
            # k_ch = ''

        # Folder used to store concatenation file
        makedirs(k_ep, k_ch, 'concat')

        # Open concatenation file
        concat_fp = os.path.join(
            db[k_ep_or_g]['cache_path'],
            "concat",
            f"{suffix}{lang_str}.txt")
        concat_file = open(concat_fp, "w")
        if True:
            print(green(f"create_video_concat_file: {concat_fp}"))

        if k_ep_or_g in ('g_debut', 'g_fin'):
            video: ChapterVideo = db[k_ep_or_g]['video']
            concat_file.write(f"file \'{video['task'].video_file}\' \n")
            audio = db[k_ep_or_g]['audio']
            # if 'silence' in audio and audio['silence'] > 0:
            #     silence_fp: str = os.path.join(
            #         db[k_ep_or_g]['cache_path'],
            #         "video",
            #         f"{k_ep_or_g}_silence.mkv"
            #     )
            #     concat_file.write(f"file \'{silence_fp}\' \n")

            # import sys
            # sys.exit()
            # for k in main_chapter_keys():
            #     for scene in video_files[k]:
            #         p = scene['path'].replace('.txt', f"_{scene['hash']}_{scene['last_task']}{lang_str}.mkv")
            #         p = p.replace('concat', 'video')
            #         concat_file.write(f"file \'{p}\' \n")
        else:
            for _chapter in main_chapter_keys():
                if chapter != '' and _chapter != chapter:
                    continue

                video = db[k_ep]['video']['target'][_chapter]
                if video['count'] == 0:
                    continue

                if len(video['scenes']) > 1:
                    concat_file.write(f"file \'{video['task'].video_file}\' \n")
                else:
                    pprint(video['scenes'][0])
                    concat_file.write(f"file \'{video['scenes'][0]['task'].video_file}\' \n")

                if chapter != '':
                    continue

                # audio = db[k_ep]['audio'][_chapter]
                # if 'silence' in audio and audio['silence'] > 0:
                #     silence_fp: str = get_silence_filepath(
                #         k_ep, _chapter, video['task'].name
                #     )
                #     concat_file.write(f"file \'{silence_fp}\' \n")

        concat_file.close()
        return concat_fp
