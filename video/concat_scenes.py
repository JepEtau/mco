import os
from pprint import pprint

from utils.mco_utils import makedirs, run_simple_command
from utils.mco_types import Scene, VideoChapter
from utils.logger import main_logger
from utils.p_print import *
from parsers import (
    db,
    key,
    ProcessingTask,
)


def concat_scenes(
    episode: str,
    chapter: str,
    video: VideoChapter,
    force: bool=False,
    simulation: bool=False
) -> None:
    verbose = False
    if 'scenes' not in video:
        return
    scenes: list[Scene] = video['scenes']
    if not scenes:
        return
    k_ep, k_ch = key(episode), chapter
    hashcode: str = video['hash']

    main_logger.debug(lightcyan(f"\nConcatenate scenes: {k_ep}:{k_ch}"))

    # if verbose:
    #     pprint(video_files)

    if k_ch in ('g_debut', 'g_fin'):
        prefix = f"{k_ch}_video"
        k_ep_or_g = k_ch
    else:
        prefix = f"{k_ep}_{k_ch}"
        k_ep_or_g = k_ep

    language = db[k_ep_or_g]['audio']['lang']
    lang_str = '' if language == 'fr' else f"_{language}"

    # Folder used to store concat file
    makedirs(episode, chapter, 'concat')

    # Last task is the suffix
    task: ProcessingTask = video['task']
    cache_directory: str = db[k_ep_or_g]['cache_path']
    suffix = '' if task == '' else f"_{task.name}"
    concat_fp: str = ''

    if len(scenes) > 1:
        # Create concat file
        concat_fp = os.path.join(
            cache_directory,
            "concat",
            f"{prefix}_{hashcode}{suffix}.txt"
        )

        concat_file = open(concat_fp, "w")
        for scene in scenes:
            # filepath = scene['path']
            # hash = scene['task'].hash
            # p = filepath.replace('.txt', f"_{hash}{suffix}.mkv")
            # p = p.replace('concat', 'video')
            concat_file.write(f"file \'{scene['task'].video_file}\' \n")
        concat_file.close()

        # Output video file
        out_video: str = os.path.join(
            cache_directory,
            "video",
            f"{prefix}_{hashcode}{suffix}{lang_str}.mkv"
        )

        if verbose:
            print(f"{k_ch}: concatenate scenes into a single clip: {out_video}")
        main_logger.debug(f"\t{out_video}")
        # Concatenate scenes into a single video
        ffmpeg_command = [db['common']['tools']['ffmpeg']]
        ffmpeg_command.extend(db['common']['settings']['verbose'].split(' '))
        ffmpeg_command.extend([
            "-f", "concat",
            "-safe", "0",
            "-i", concat_fp,
            "-c", "copy",
            "-y", out_video
        ])
        if verbose:
            print(lightgrey(' '.join(ffmpeg_command)))

        if os.path.exists(out_video) and not force:
            print(lightgrey(' '.join(ffmpeg_command)))
        elif not simulation:
            success = run_simple_command(command=ffmpeg_command)
            if not success:
                raise RuntimeError(red("Failed to conactenate scenes"))
    else:
        concat_fp = os.path.join(
            cache_directory,
            "concat",
            f"{prefix}_{hashcode}{suffix}.txt"
        )
        out_video: str = os.path.join(
            cache_directory,
            "video",
            f"{prefix}_{hashcode}{suffix}{lang_str}.mkv"
        )


    task.video_file = out_video
    task.concat_file = concat_fp


