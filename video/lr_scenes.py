import subprocess
import sys
import os
import time
from pprint import pprint
from scene.consolidate import consolidate_scene
from scene.generate_lr import generate_lr_scene
from utils.hash import calc_hash
from utils.media import vcodec_to_extension
from utils.mco_types import Scene, ChapterVideo
from utils.mco_utils import is_final_up_to_date
from utils.p_print import *
from utils.time_conversions import s_to_sexagesimal
from utils.tools import ffmpeg_exe
from parsers import (
    db,
    Chapter,
    all_chapter_keys,
    ep_key,
    TaskName,
    ProcessingTask,
    pprint_scene_mapping,
    VideoSettings,
)
from video.consolidate_scenes import get_chapter_video
from .concat_frames import generate_video_concat_file
from .concat_scenes import concat_scenes



def generate_lr_scenes(
    episode: str,
    single_chapter: Chapter,
    task_name: TaskName = '',
    force: bool = False,
    simulation: bool = False,
    scene_no: int = -1,
    scene_min: int = -1,
    scene_max: int = -1,
    watermark: bool = False,
    edition: str | None = None,
    debug: bool = False
):
    k_ep = ep_key(episode)
    chapters: Chapter = all_chapter_keys() if single_chapter == '' else [single_chapter]

    if k_ep == '' and single_chapter not in ('g_debut', 'g_fin'):
        raise ValueError(red("[E] episode must be set"))

    start_time_full = time.time()
    for k_ch in chapters:
        hashes_str = ''

        ch_video: ChapterVideo | None = get_chapter_video(k_ep, k_ch)
        if ch_video is None:
            continue

        ch_video['task'] = ProcessingTask(name=task_name)
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

            # Consolidate this scene
            scene['task'] = ProcessingTask(name=task_name)
            consolidate_scene(scene=scene, watermark=watermark)

            # Calculate hash for the video
            hashes_str += f",{scene['task'].hash}"

            if debug:
                print(lightcyan(f"======================= generate_{task_name}_scenes: Scene ============================="))
                pprint(scene)
                print(lightcyan("==============================================================================="))

            if not force and is_final_up_to_date(scene):
                continue

            result = generate_lr_scene(scene=scene, force=force)
            if not result:
                # pprint(db[scene['k_ep']]['video'][scene['k_ed']])
                raise RuntimeError(
                    red(f"Failed processing scene: source: {scene['k_ed']}:{scene['k_ep']}:{scene['k_ch']}")
                )

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
        if k_ch in ('g_debut', 'g_fin'):
            basename: str = f"{k_ch}_{task_name}_{hashcode}"
            cache_path: str = db[k_ch]['cache_path']
        else:
            basename: str = f"{k_ep}_{k_ch}_{task_name}_{hashcode}"
            cache_path: str = db[k_ep]['cache_path']

        vsettings: VideoSettings = db['common']['video_format']['lr']
        ext: str = vcodec_to_extension[vsettings.codec]
        ch_video['task'] = ProcessingTask(
            name=task_name,
            hash=hashcode,
            concat_file=os.path.join(cache_path, "concat", f"{basename}.txt"),
            video_file=os.path.join(cache_path, f"video", f"{basename}{ext}"),
        )
    print(f"Generated scenes in {time.time() - start_time_full:.03f}s")

    if scene_no != -1:
        return


    # For each part, concatenate scenes in a single clip
    for k_ch in chapters:
        ch_video: ChapterVideo | None = get_chapter_video(k_ep, k_ch)
        if ch_video is None:
            continue
        concat_scenes(
            episode=k_ep,
            chapter=k_ch,
            video=ch_video,
            force=force,
            simulation=simulation
        )


    # Create concatenation files and video files for silences
    do_concatenate_video: bool = bool(single_chapter == '')
    if do_concatenate_video:
        print(lightgreen(f"Concatenate all scenes"))

        # Generate concatenation files which contains all video files
        concat_fp = generate_video_concat_file(
            episode=k_ep,
            chapter=single_chapter,
        )

        # Get language
        language = db[k_ep]['audio']['lang']
        lang_str = '' if language == 'fr' else f"_{language}"

        # Concatenate video clips
        raise ValueError("vcodec_to_extension")
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



