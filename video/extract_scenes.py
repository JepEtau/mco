import subprocess
import sys
import os
import time
from pprint import pprint

from scene.consolidate import consolidate_src_scene
from scene.extract import extract_scene
from scene.generate_lr import generate_lr_scene
from utils.hash import calc_hash
from utils.logger import main_logger
from utils.mco_types import Scene, ChapterVideo
from utils.mco_utils import get_cache_path, run_simple_command
from utils.p_print import *
from utils.time_conversions import s_to_sexagesimal
from utils.tools import ffmpeg_exe
from utils.mco_path import makedirs
from parsers import (
    db,
    Chapter,
    all_chapter_keys,
    key,
    TaskName,
    ProcessingTask
)
from .concat_frames import (
    generate_concat_file,
    generate_silence_concat_file,
    generate_video_concat_file,
    set_concat_filename,
    set_video_filename,
)
from .concat_scenes import concat_scenes
from .combine_frames import combine_frames



def extract_scenes(
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
    concatenate_clips: bool = (
        True
        if scene_no is None and scene_min == -1 and scene_max ==-1
        else False
    )

    # Create the video directory for this episode or chapter
    makedirs(k_ep, single_chapter, 'video')

    # Create the scen vclip chapter by chapter
    chapters: Chapter = all_chapter_keys() if single_chapter == '' else [single_chapter]

    start_time_full = time.time()

    for chapter in chapters:
        hashes_str = ''
        video: ChapterVideo = db[k_ep]['video'][k_ed][chapter]

        # Do not generate clip for unused chapters
        pprint(video)
        if video['count'] <= 0:
            continue

        if debug:
            print(f"\n<<<<<<<<<<<<<<<<<<<<< {chapter} >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        print(lightcyan(chapter))

        video['task'] = ProcessingTask(name=task)

        # Walk through target scenes
        scenes: list[Scene] = video['scenes']
        for scene in scenes:
            start_time = time.time()
            if scene_no is not None and scene['no'] != scene_no:
                continue
            if scene_min != -1 and scene_max != -1:
                if scene['no'] < scene_min or scene['no'] > scene_max:
                    continue

            print(
                lightgreen(f"  {scene['no']: 3}: {scene['start']: 6}".ljust(14)),
                f"{scene['count']}".rjust(4),
            )

            # COnsolidate this scene
            consolidate_src_scene(
                scene=scene,
                task_name='initial',
                watermark=watermark
            )

            if debug:
                print(lightcyan("================================== Scene ======================================="))
                pprint(scene)
                print(lightcyan("==============================================================================="))

            if not simulation:
                result = extract_scene(scene=scene, force=force)
                if not result:
                    pprint(scene)
                    raise RuntimeError(
                        red(f"Failed processing scene: source: {scene['k_ed']}:{scene['k_ep']}:{scene['k_ch']}")
                    )

            # Calculate hash for the video
            hashes_str += f",{scene['task'].hashcode}"

            if debug:
                elapsed = time.time() - start_time
                print(purple(
                    f"\t\tscene no. {scene['no']} generated in "
                    f"{s_to_sexagesimal(elapsed)} ({elapsed/scene['count']:02f}s/f)\n"
                ))

        hashcode: str = calc_hash(hashes_str[:-1])
        basename: str = f"{k_ed}_{k_ep}_{chapter}_{task}_{hashcode}"
        video['task'] = ProcessingTask(
            name=task,
            hashcode=hashcode,
            concat_file=os.path.join(db[k_ep]['cache_path'], "concat", f"{basename}.txt"),
            video_file=os.path.join(db[k_ep]['cache_path'], f"scenes_{k_ed}", f"{basename}.mkv"),
        )

    print(f"Total time: {time.time() - start_time_full:.03f}s")

    if scene_no is not None:
        return

    # Concatenate video clips from all chapters
    if concatenate_clips:
        for chapter in chapters:
            video: ChapterVideo
            # if chapter in ('g_debut', 'g_fin'):
            #     video: ChapterVideo = db[chapter]['video']
            # else:
            video: ChapterVideo = db[k_ep]['video'][k_ed][chapter]

            pprint(video['task'])
            out_video_file: str = video['task'].video_file
            modified_time: int = 0
            if os.path.exists(out_video_file):
                modified_time = os.stat(out_video_file).st_mode

            do_concatenate: bool = False
            with open(video['task'].concat_file, "w") as f:
                for scene in video['scenes']:
                    out_filepath: str = scene['task'].video_file
                    f.write(f"file '{out_filepath}'\n")

                    if (
                        not os.path.exists(out_filepath)
                        or os.stat(out_filepath).st_mode > modified_time
                    ):
                        do_concatenate = True

            print(f"dogenerate: {do_concatenate}")

            if do_concatenate:
                # Force concatenation
                main_logger.debug(
                    lightgreen(f"\nConcatenate video clips:\n")
                    + f"\t{out_video_file}\n"
                )
                ffmpeg_command: list[str] = [
                    ffmpeg_exe,
                    "-hide_banner",
                    "-loglevel", "warning",
                    "-f", "concat",
                    "-safe", "0",
                    "-i", video['task'].concat_file,
                    "-c", "copy",
                    "-y", out_video_file
                ]

                main_logger.debug(' '.join(ffmpeg_command))
                run_simple_command(ffmpeg_command)
                if not simulation:
                    sub_process = subprocess.Popen(
                        ffmpeg_command,
                        stdin=subprocess.PIPE,
                        stdout=sys.stdout,
                        stderr=subprocess.STDOUT,
                    )

    print(f"Total time: {time.time() - start_time_full:.03f}s")



