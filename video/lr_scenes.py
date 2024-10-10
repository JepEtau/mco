import subprocess
import sys
import os
import time
from pprint import pprint

from scene.consolidate import consolidate_scene
from scene.generate_lr import generate_lr_scene
from utils.hash import calc_hash
from utils.logger import main_logger
from utils.mco_types import Scene, ChapterVideo
from utils.mco_utils import is_up_to_date
from utils.p_print import *
from utils.time_conversions import s_to_sexagesimal
from utils.tools import ffmpeg_exe
from parsers import (
    db,
    Chapter,
    all_chapter_keys,
    key,
    TaskName,
    ProcessingTask,
    pprint_scene_mapping,
)
from .concat_frames import generate_video_concat_file
from .concat_scenes import concat_scenes



def generate_lr_scenes(
    episode: str,
    single_chapter: Chapter,
    task: TaskName = '',
    force: bool = False,
    simulation: bool = False,
    scene_no: int = -1,
    scene_min: int = -1,
    scene_max: int = -1,
    watermark: bool = False,
    edition: str | None = None,
    debug: bool = False
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

        # Walk through target scenes
        scenes: list[Scene] = ch_video['scenes']
        for scene in scenes:
            start_time = time.time()
            if scene_no != -1 and scene['no'] != scene_no:
                continue
            if scene_min != -1 and scene_max != -1:
                if scene['no'] < scene_min or scene['no'] > scene_max:
                    continue

            pprint_scene_mapping(scene)

            # Set the last task
            scene['task'] = ProcessingTask(name=task)

            # Generate frames for this scene
            consolidate_scene(scene=scene, watermark=watermark)

            if debug:
                print(lightcyan(f"======================= generate_{task}_scenes: Scene ============================="))
                pprint(scene)
                print(lightcyan("==============================================================================="))

            if not simulation and not is_up_to_date(scene) or force:
                result = generate_lr_scene(scene=scene, force=force)
                if not result:
                    # pprint(db[scene['k_ep']]['video'][scene['k_ed']])
                    raise RuntimeError(
                        red(f"Failed processing scene: source: {scene['k_ed']}:{scene['k_ep']}:{scene['k_ch']}")
                    )

            # Calculate hash for the video
            hashes_str += f",{scene['task'].hashcode}"

            if debug:
                elapsed = time.time() - start_time
                print(purple(
                    f"\t\tscene no. {scene['no']} generated in "
                    f"{s_to_sexagesimal(elapsed)} ({elapsed/scene['dst']['count']:02f}s/f)\n"
                ))

            # if debug:
            #     print(lightcyan("================================== Scene ======================================="))
            #     pprint(scene)
            #     print(lightcyan("==============================================================================="))
                # sys.exit()

        hashcode: str = calc_hash(hashes_str[:-1])
        basename: str = f"{k_ed}_{k_ep}_{k_ch}_{task}_{hashcode}"
        cache_path = (
            db[k_ch]['cache_path']
            if k_ch in ('g_debut', 'g_fin')
            else db[k_ep]['cache_path']
        )
        ch_video['task'] = ProcessingTask(
            name=task,
            hashcode=hashcode,
            concat_file=os.path.join(cache_path, "concat", f"{basename}.txt"),
            video_file=os.path.join(cache_path, f"video_lr", f"{basename}.mkv"),
        )
    print(f"Generated scenes in {time.time() - start_time_full:.03f}s")

    if scene_no != -1:
        return


    # For each part, concatenate scenes in a single clip
    for k_ch in chapters:
        ch_video: ChapterVideo
        if k_ch in ('g_debut', 'g_fin'):
            ch_video: ChapterVideo = db[k_ch]['video']
        else:
            ch_video: ChapterVideo = db[k_ep]['video']['target'][k_ch]

        if ch_video['count'] > 0:
            concat_scenes(
                episode=k_ep,
                chapter=k_ch,
                video=ch_video,
                force=force,
                simulation=simulation
            )

            # if single_chapter == '':
            #     main_logger.debug(lightgreen(f"\nCreate silences after:"))
            #     for chapter in chapters:
            #         generate_silence(k_ep, chapter)

    # print(f"\n<<<<<<<<<<<<<<<<<<<<< {chapter} >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    # pprint(ch_video['task'])
    # sys.exit()

    verbose = True

    # Create concatenation files and video files for silences



    if verbose:
        print(lightgreen(f"video files used to concatenate all clips"))
    # do_concatenate_video = True

    # Concatenate video clips
    if do_concatenate_video:
        if verbose:
            print(lightgreen(f"Concatenate all clips into a single one"))

        # Generate concatenation files which contains all video files
        concat_fp = generate_video_concat_file(
            episode=k_ep,
            chapter=single_chapter,
        )

        # Get language
        language = db[k_ep]['audio']['lang']
        lang_str = '' if language == 'fr' else f"_{language}"

        # Concatenate video clips
        episode_video_filepath = os.path.join(
            db[k_ep]['cache_path'],
            "video",
            f"{k_ep}_video{lang_str}.mkv"
        )

        # Force concatenation
        print(
            lightgreen(f"\nConcatenate video clips:\n")
            + f"\t{episode_video_filepath}\n"
        )
        ffmpeg_command: list[str] = [
            ffmpeg_exe,
            "-hide_banner",
            "-loglevel", "warning",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_fp,
            "-c", "copy",
            "-y", episode_video_filepath
        ]

        print(' '.join(ffmpeg_command))
        if not simulation:
            sub_process = subprocess.Popen(
                ffmpeg_command,
                stdin=subprocess.PIPE,
                stdout=sys.stdout,
                stderr=subprocess.STDOUT,
            )

            stdout, stderr = sub_process.communicate()
            if stderr is not None:
                for line in stderr.decode('utf-8').split('\n'):
                    print(line)
            if stdout is not None:
                for line in stdout.decode('utf-8').split('\n'):
                    print(line)

    print(f"Total time: {time.time() - start_time_full:.03f}s")



