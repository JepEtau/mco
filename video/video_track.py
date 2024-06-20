import subprocess
import sys
import os
import time
from pprint import pprint

from scene.consolidate import consolidate_scene
from scene.process import process_scene
from utils.hash import calc_hash
from utils.logger import main_logger
from utils.mco_types import Scene, VideoChapter
from utils.p_print import *
from utils.time_conversions import s_to_sexagesimal
from utils.tools import ffmpeg_exe
from utils.mco_utils import makedirs
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



def generate_video_track(
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
    do_concatenate_video: bool = (
        True
        if single_chapter == '' # or single_chapter in ('g_debut', 'g_fin')
        else False
    )

    # Create the video directory for this episode or chapter
    makedirs(k_ep, single_chapter, 'video')

    # List video files for each chapter
    # video_clips = dict()
    # for k in all_chapter_keys():
    #     video_clips[k] = {
    #         'hash': '',
    #         'scenes': [],
    #     }

    # print("Generate video: %s, %s, tasks=%s" % (edition, k_ep, ', '.join(tasks)))

    # Create the scen vclip chapter by chapter
    chapters: Chapter = all_chapter_keys() if single_chapter == '' else [single_chapter]
    unique_input_frame_count: int = 0

    start_time_full = time.time()

    for chapter in chapters:
        hashes_str = ''

        # k_ep_src is the default episode source used to generate a chapter
        k_ep_src: str = ''
        video: VideoChapter
        if chapter in ('g_debut', 'g_fin'):
            video = db[chapter]['video']
            k_ep_src: str = k_ep if task == 'initial' else video['src']['k_ep']

        elif k_ep == 'ep00':
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
            print(f"\n<<<<<<<<<<<<<<<<<<<<< {chapter} >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        print(lightcyan(chapter))

        video['task'] = ProcessingTask(name=task)
        previous_concat_fp = ''

        # Walk through target scenes
        scenes: list[Scene] = video['scenes']
        for scene in scenes:
            start_time = time.time()
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

            print(
                lightgreen(f"\t{scene['no']}: {scene['start']}"),
                f"\t({scene['dst']['count']})\t<- {scene['k_ed']}:{scene['k_ep']}:{scene['k_ch']}",
                f"   {scene['start']} ({scene['count']})"
            )

            # Set the last task
            scene['task'] = ProcessingTask(name=task)

            # Generate frames for this scene
            consolidate_scene(scene=scene)


            if not simulation:
                result = process_scene(scene=scene, force=force)
                if not result:
                    pprint(db[scene['k_ep']]['video'][scene['k_ed']])
                    raise RuntimeError(
                        red(f"Failed processing scene: source: {scene['k_ed']}:{scene['k_ep']}:{scene['k_ch']}")
                    )
            else:
                # For stats
                if chapter not in ('g_debut', 'g_fin'):
                    unique_input_frame_count += len(scene['in_frames'])

            if task == 'initial':
                continue

            # Calculate hash for the video
            hashes_str += f",{scene['task'].hashcode}"

            # if len(scene['out_frames']) < 5:
            #     print(lightcyan("================================== Scene ======================================="))
            #     pprint(scene)
            #     print(lightcyan("==============================================================================="))
            #     raise ValueError("Scene has less than 5 frames")


            # Create concatenation file
            set_concat_filename(episode=k_ep_src, chapter=chapter, scene=scene)
            set_video_filename(scene)
            generate_concat_file(
                episode=episode,
                chapter=chapter,
                video=video,
                scene=scene
            )
            combine_frames(
                chapter=chapter,
                scene=scene,
                force=force,
                simulation=simulation,
                watermark=f"{scene['no']}" if watermark else None
            )

            if debug:
                elapsed = time.time() - start_time
                print(purple(
                    f"\t\tscene no. {scene['no']} generated in "
                    f"{s_to_sexagesimal(elapsed)} ({elapsed/scene['count']:02f}s/f)\n"
                ))

            if debug:
                print(lightcyan("================================== Scene ======================================="))
                pprint(scene)
                print(lightcyan("==============================================================================="))
                # sys.exit()

        video['hash'] = calc_hash(hashes_str[:-1])

    if task == 'initial':
        print(f"Total time: {time.time() - start_time_full:.03f}s")
        return

    if scene_no is not None:
        return

    # For each part, concatenate scenes in a single clip
    for chapter in chapters:
        video: VideoChapter
        if chapter in ('g_debut', 'g_fin'):
            video: VideoChapter = db[chapter]['video']
        else:
            video: VideoChapter = (
                db[k_ep]['video']['target'][chapter]
                if edition == ''
                else db[k_ep]['video'][edition][chapter]
            )

        if video['count'] > 0:
            concat_scenes(
                episode=episode,
                chapter=chapter,
                video=video,
                force=force,
                simulation=simulation
            )

    verbose = False

    # Create concatenation files and video files for silences
    if single_chapter == '':
        main_logger.debug(lightgreen(f"\nCreate silences after:"))
        silences = generate_silence_concat_file(episode=episode)
        for chapter, filepaths in silences.items():
            if verbose:
                main_logger.debug(lightgreen(f"combine images to video: {chapter}"))
                pprint(filepaths)

            for f in filepaths:
                if verbose:
                    main_logger.debug(f"{chapter}: {f}")
                virtual_video_scene: Scene = Scene(
                    task=ProcessingTask(
                        name=task,
                        concat_file=f,
                    )
                )
                combine_frames(
                    chapter=chapter,
                    scene=virtual_video_scene,
                    force=force,
                    simulation=simulation
                )
                # try:
                #     video_clips[chapter]['files'].append(scene_fp)
                # except:
                #     nested_dict_set(video_clips[chapter], [scene_fp], 'files')

    if verbose:
        print(lightgreen(f"video files used to concatenate all clips"))


    # Concatenate video clips from all chapters
    if do_concatenate_video:

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
        main_logger.debug(
            lightgreen(f"\nConcatenate video clips:\n")
            + f"\t{episode_video_filepath}\n"
        )
        ffmpeg_command: list[str] = [
            ffmpeg_exe,
            *db['common']['settings']['verbose'],
            "-f", "concat",
            "-safe", "0",
            "-i", concat_fp,
            "-c", "copy",
            "-y", episode_video_filepath
        ]

        main_logger.debug(' '.join(ffmpeg_command))
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

    print(f"Total number of frames to upscale: {unique_input_frame_count}")
    print(f"Total time: {time.time() - start_time_full:.03f}s")



