import sys
import os
from tempfile import gettempdir
import time

from scene.consolidate import consolidate_scene
from scene.generate_hr import generate_hr_scene
from utils.mco_types import Scene, VideoChapter
from utils.media import extract_media_info
from utils.p_print import *
from utils.mco_utils import makedirs, run_simple_command
from utils.tools import ffmpeg_exe
from parsers import (
    db,
    Chapter,
    all_chapter_keys,
    key,
    TaskName,
    ProcessingTask,
)
from utils.path_utils import path_split
from .concat_frames import (
    set_video_filename,
)


def generate_hr_scenes(
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
    scenes_to_process: list[Scene] = []

    if scene_min != -1 and scene_max != -1 and len(chapters) > 1:
        raise ValueError(red(f"[E] Missing chapter when specifing scene_min and scene_max"))


    start_time = time.time()
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

            out_video_file: str = scene['task'].video_file
            if os.path.exists(out_video_file) and not force:
                try:
                    video_info = extract_media_info(out_video_file)['video']
                    if (
                        'HR' in video_info['metadata']
                        and video_info['metadata']['HR'] == scene['task'].hashcode
                        and not force
                    ):
                        print(f"Scene no. {scene['no']} is up-to-date, ignore")
                        continue
                except:
                    print(f"failed opening {out_video_file}")
                    pass
            scenes_to_process.append(scene)

    print(f"Total time: {time.time() - start_time:.03f}s")

    print(f"Total number of scenes to generate: {len(scenes_to_process)}")
    for scene in scenes_to_process:
        # if debug:
        #     print(lightcyan("================================== Scene ======================================="))
        #     pprint(scene)
        #     print(lightcyan("==============================================================================="))

        succes: bool = generate_hr_scene(scene=scene, debug=debug)
        if not succes:
            return


    if scene_min != -1 and scene_max != -1:
        concat_fp = os.path.join(gettempdir(), f"mco_concat_tmp.txt")
        with open(concat_fp, mode='w') as f:
            for scene in scenes:
                if scene_min != -1 and scene_max != -1:
                    if scene['no'] < scene_min or scene['no'] > scene_max:
                        continue
                f.write(f"file \'{scene['task'].video_file}\' \n")

        # Output video file
        out_filename: str = f"{chapter}_{scene_min}-{scene_max}.mkv"
        if chapter not in ('g_debut', 'g_fin'):
            out_filename = f"{k_ep}_{out_filename}"

        out_video: str = os.path.join(
            path_split(scene['task'].video_file)[0],
            out_filename
        )
        concat_command: list[str] = [
            ffmpeg_exe,
            "-hide_banner",
            "-loglevel", "warning",
            "-nostats",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_fp,
            "-c", "copy",
            "-y", out_video
        ]
        if debug:
            print(lightgreen(f"[V] FFmpeg concat command:"), ' '.join(concat_command))

        if not simulation:
            success = run_simple_command(command=concat_command)
            os.remove(concat_fp)
            if not success:
                raise RuntimeError(red("Failed to conactenate scenes"))


    print("Done.")

