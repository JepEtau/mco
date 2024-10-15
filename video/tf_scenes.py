from datetime import datetime
import subprocess
import sys
import os
import time
from pprint import pprint

from parsers.p_print import pprint_scene_mapping
from scene.consolidate import consolidate_scene
from .st_scenes import convert_video_for_evaluation
from utils.mco_types import Scene, ChapterVideo
from utils.mco_utils import scene_id_str
from utils.p_print import *
from utils.path_utils import absolute_path
from parsers import (
    db,
    Chapter,
    all_chapter_keys,
    key,
    TaskName,
    ProcessingTask,
)



def tf_scenes(
    episode: str,
    single_chapter: Chapter = '',
    scene_no: int | None = None,
    task: TaskName = '',
    evaluate: bool = False,
    force: bool = False,
    debug: bool = False,
):
    k_ep = key(episode)
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
            # pprint(ch_video)
            print(f"scene_no: {scene_no}")

        # Walk through target scenes
        scenes: list[Scene] = ch_video['scenes']
        for scene in scenes:
            if scene_no is not None and scene_no != -1 and scene['no'] != scene_no:
                continue
            pprint_scene_mapping(scene)

            # Consolidate this scene
            consolidate_scene(scene, task_name=task)
            scene_id: str = scene_id_str(scene)

            if debug:
                print(lightcyan(f"======================= generate_{task}_scenes: Scene ============================="))
                pprint(scene)
                print(lightcyan("==============================================================================="))

            do_process: bool = False

            in_fp: str = scene['task'].in_video_file
            in_mtime: float = 0
            if os.path.exists(in_fp):
                in_mtime = os.path.getmtime(in_fp)
            else:
                print(yellow(f"{scene_id}: missing input file:"), in_fp)
                print(yellow("  use non stabilized video"))
                # Fallback to HR if not stabilized
                in_fp: str = scene['task'].fallback_in_video_files['hr']
                in_mtime: float = 0
                if os.path.exists(in_fp):
                    in_mtime = os.path.getmtime(in_fp)
                else:
                    print(red(f"{scene_id}: missing input file:"), in_fp)
                    continue

            out_fp: str = scene['task'].video_file
            out_mtime: float = 0
            out_mtime_str: str = "-"
            if os.path.exists(out_fp):
                out_mtime = os.path.getmtime(out_fp)
                out_mtime_str = datetime.fromtimestamp(out_mtime).strftime("%Y-%m-%d %H:%M:%S")

            if out_mtime_str == "-":
                print(yellow(f"{scene_id}: temporal filtered scene is not generated"))
                do_process = True

            elif out_mtime < in_mtime or force:
                print(yellow(f"{scene_id} has to be updated"))
                do_process = True


            # Run temporalfilter
            if do_process:
                print(lightcyan(f"{scene_id}: temporal filtering"))

                pytf_cmd: list[str] = [
                    sys.executable,
                    # absolute_path("~/github/py_temporalfix/py_temporalfix.py"),
                    absolute_path("A:\\py_temporalfix\\py_temporalfix.py"),
                    "--input", in_fp,
                    "--output", out_fp,
                ]
                print(lightcyan("pytf command:"))
                print(lightgreen(' '.join(pytf_cmd)))

                pytf_subprocess: subprocess.Popen | None = None
                try:
                    pytf_subprocess = subprocess.Popen(
                        pytf_cmd,
                        stdin=subprocess.DEVNULL,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                except Exception as e:
                    print(f"[E] Unexpected error: {type(e)}", flush=True)


                line: str = ''
                os.set_blocking(pytf_subprocess.stderr.fileno(), False)
                print(f"Apply temporal filters:")
                try:
                    while True:
                        line = pytf_subprocess.stderr.readline().decode('utf-8')
                        if line:
                            print(f"  {line.strip()}", end='\r')
                        if pytf_subprocess.poll() is not None:
                            break
                except:
                    pass
                # print()

                # stdout_b: bytes | None = None
                # try:
                #     # Arbitrary timeout value
                #     stdout_b, _ = pytf_subprocess.communicate(timeout=10)
                # except:
                #     pytf_subprocess.kill()
                #     return

                # if stdout_b is not None:
                #     stdout = stdout_b.decode('utf-8)')
                #     if stdout:
                #         print(f"FFmpeg stdout:\n{stdout}")
                #     print()
            print()




            if evaluate:
                convert_video_for_evaluation(
                    [in_fp, out_fp],
                    force=force,
                    debug=debug
                )


