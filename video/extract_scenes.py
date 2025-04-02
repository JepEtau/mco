from __future__ import annotations
import os
import time
from pprint import pprint

from scene.consolidate_src import consolidate_src_scene
from scene.extract import extract_scene
from utils.logger import main_logger
from utils.mco_types import Scene, ChapterVideo
from utils.mco_utils import run_simple_command
from utils.media import vcodec_to_extension
from utils.p_print import *
from utils.path_utils import path_split
from utils.time_conversions import s_to_sexagesimal
from utils.tools import ffmpeg_exe
from parsers import (
    db,
    Chapter,
    all_chapter_keys,
    ep_key,
    TaskName,
    ProcessingTask,
    VideoSettings,
    calc_hash,
    get_chapter_video,
)


def extract_scenes(
    episode: str,
    single_chapter: Chapter = '',
    task_name: TaskName = '',
    force: bool = False,
    simulation: bool = False,
    scene_no: int = -1,
    scene_min: int = -1,
    scene_max: int = -1,
    watermark: bool = False,
    edition: str | None = None,
    debug: bool = False,
    compare: bool = False,
):
    """
        compare: used for lr to set basename for source comparisons

    """
    k_ed = edition
    k_ep = ep_key(episode)
    chapters: Chapter = all_chapter_keys() if single_chapter == '' else [single_chapter]

    concatenate_clips: bool = (
        True
        if (
            (scene_no == -1 and scene_min == -1 and scene_max == -1)
            and task_name not in ('initial', 'extract')
        )
        else False
    )
    concatenate_clips = True

    start_time_full = time.time()
    for k_ch in chapters:
        hashes_str = ""
        ch_video: ChapterVideo | None = None
        try:
            ch_video: ChapterVideo | None = db[k_ep]['video'][k_ed][k_ch]
        except:
            pass
        if ch_video is None:
            continue

        ch_video['task'] = ProcessingTask(name=task_name)
        if debug:
            print(f"\n<<<<<<<<<<<<<<<<<<<<< {k_ch} >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            print(f"scene_no: {scene_no}")

        # Walk through target scenes
        scenes: list[Scene] = ch_video['scenes']
        for scene in scenes:
            start_time = time.time()
            if scene_no != -1 and scene['no'] != scene_no:
                continue
            if scene_min != -1 and scene['no'] < scene_min:
                continue
            if scene_max != -1 and scene['no'] > scene_max:
                continue

            print(
                lightgreen(f"  {scene['no']: 3}: {scene['start']: 6}".ljust(14)),
                f"{scene['count']}".rjust(4),
            )

            # Get source scene for comparisons
            ed_scene = scene
            if compare:
                target_scenes: list[Scene] = get_chapter_video(k_ep, k_ch)['scenes']
                in_scene: Scene = target_scenes[scene_no]['src'].primary_scene().in_scene
                if in_scene['k_ed'] == k_ed:
                    ed_scene_no: int = in_scene['no']
                    ed_scene = scenes[ed_scene_no]

            # Consolidate this scene
            consolidate_src_scene(
                scene=ed_scene,
                task_name=task_name,
                watermark=watermark,
                compare=compare,
                target_scene_no=scene_no,
            )

            if debug:
                print(lightcyan("================================== Scene ======================================="))
                pprint(ed_scene)
                print(lightcyan("==============================================================================="))

            if not simulation:
                result = extract_scene(
                    scene=ed_scene, compare=compare, force=force, debug=debug
                )
                if not result:
                    # pprint(ed_scene)
                    raise RuntimeError(
                        red(f"Failed processing scene: source: {ed_scene['k_ed']}:{ed_scene['k_ep']}:{scene['k_ch']}")
                    )

            # Calculate hash for the video
            hashes_str += f",{ed_scene['task'].hash}"

            if debug:
                elapsed = time.time() - start_time
                print(purple(
                    f"\t\tscene no. {ed_scene['no']} generated in "
                    f"{s_to_sexagesimal(elapsed)} ({elapsed/ed_scene['count']:02f}s/f)\n"
                ))

        hashcode: str = calc_hash(hashes_str[:-1])
        if task_name == 'lr':
           basename: str = f"{k_ep}_{k_ch}_{k_ed}_{task_name}_{hashcode}"
        else:
           basename: str = f"{k_ed}_{k_ep}_{k_ch}_{task_name}_{hashcode}"

        k_ep_or_g: str = k_ch if k_ch in ('g_debut', 'g_fin') else k_ep
        concat_fp: str =os.path.join(
            db[k_ep_or_g]['cache_path'], "concat", f"{basename}.txt"
        )
        os.makedirs(path_split(concat_fp)[0], exist_ok=True)
        with open(concat_fp, "w") as concat_file:
            for scene in scenes:
                concat_file.write(f"file \'{scene['task'].video_file}\' \n")

        vsettings: VideoSettings = db['vsettings'][task_name]
        ch_video['task'] = ProcessingTask(
            name=task_name,
            hash=hashcode,
            concat_file=concat_fp,
            video_file=os.path.join(
                db[k_ep_or_g]['cache_path'],
                f"ed_{k_ed}",
                f"{basename}{vcodec_to_extension[vsettings.codec]}"
            ),
        )
    print(f"Extracted scenes in {time.time() - start_time_full:.03f}s")

    if scene_no != -1:
        return

    # Concatenate video clips from all chapters
    if concatenate_clips:
        for k_ch in chapters:
            ch_video: ChapterVideo = db[k_ep]['video'][k_ed][k_ch]

            out_video_file: str = ch_video['task'].video_file
            modified_time: int = 0
            if os.path.exists(out_video_file):
                modified_time = os.stat(out_video_file).st_mode

            do_concatenate: bool = False
            pprint(ch_video['task'])
            with open(ch_video['task'].concat_file, "w") as f:
                for scene in ch_video['scenes']:
                    out_filepath: str = scene['task'].video_file
                    f.write(f"file '{out_filepath}'\n")

                    if (
                        not os.path.exists(out_filepath)
                        or os.stat(out_filepath).st_mode > modified_time
                    ):
                        do_concatenate = True

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
                    "-i", ch_video['task'].concat_file,
                    "-c", "copy",
                    "-y", out_video_file
                ]

                main_logger.debug(' '.join(ffmpeg_command))
                run_simple_command(ffmpeg_command)
                # if not simulation:
                #     sub_process = subprocess.Popen(
                #         ffmpeg_command,
                #         stdin=subprocess.PIPE,
                #         stdout=sys.stdout,
                #         stderr=subprocess.STDOUT,
                #     )

    print(f"Total time: {time.time() - start_time_full:.03f}s")



