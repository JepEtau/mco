import subprocess
import sys
import os
import time
from pprint import pprint

from scene.consolidate import consolidate_scene
from utils.hash import calc_hash
from utils.mco_types import Scene, VideoChapter
from utils.p_print import *
from utils.time_conversions import s_to_sexagesimal
from utils.tools import ffmpeg_exe
from .concat_scenes import concat_scenes
from .combine_frames import combine_frames

from utils.mco_utils import makedirs, nested_dict_set
from parsers import (
    db,
    Chapter,
    all_chapter_keys,
    key,
    TaskName,
    ProcessingTask
)
from video.concat_files import (
    generate_concat_file,
    generate_silence_concat_file,
)



def generate_video_track(
    episode: str,
    chapter: Chapter = '',
    task: TaskName = '',
    force: bool = False,
    simulation: bool = False,
    scene_no: int | None = None,
    watermark: bool = False,
    edition: str | None = None,
):
    k_ep = key(episode)

    # Create the video directory for this episode or chapter
    makedirs(k_ep, chapter, 'video')

    # List video files for each chapter
    # video_clips = dict()
    # for k in all_chapter_keys():
    #     video_clips[k] = {
    #         'hash': '',
    #         'scenes': [],
    #     }

    # print("Generate video: %s, %s, tasks=%s" % (edition, k_ep, ', '.join(tasks)))

    # Create the scen vclip chapter by chapter
    chapters: Chapter = all_chapter_keys() if chapter == '' else [chapter]
    hashes: dict[Chapter, str] = {}
    for chapter in chapters:
        hashes_str = ''

        # k_ep_src is the default episode source used to generate a chapter
        k_ep_src: str = ''
        video: VideoChapter
        if chapter in ['g_debut', 'g_fin']:
            video = db[chapter]['video']
            k_ep_src = video['src']['k_ep']

        elif k_ep == 'ep00':
            sys.exit(red("Missing episode no."))

        else:
            # Use the source video clip if edition is specified
            # Used for study
            video = (
                db[k_ep]['video']['target'][chapter]
                if edition == ''
                else db[k_ep]['video'][edition][chapter]
            )
            k_ep_src = k_ep

        # Do not generate clip for unused chapters
        if video['count'] == 0:
            continue

        print(f"\n<<<<<<<<<<<<<<<<<<<<< {chapter} >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

        video['task'] = ProcessingTask(name=task)
        previous_concat_fp = ''

        # Walk through target scenes
        scenes: list[Scene] = video['scenes']
        for scene in scenes:
            start_time = time.time()
            if not scene['no'] != scene_no:
                continue

            # Patch the for study mode
            if edition != '':
                scene.update({
                    'dst': {
                        'count': scene['count'],
                        'k_ed': edition,
                        'k_ep': episode,
                        'k_ch': chapter,
                    },
                    'src': {
                        'k_ed': edition,
                        'k_ep': episode,
                        'k_ch': chapter,
                    },
                    'k_ed': edition,
                    'k_ep': episode,
                    'k_ch': chapter,
                })


            print(lightgreen(
                f"\t{scene['no']}: {scene['start']}",
                f"\t({scene['dst']['count']})\t<- {scene['k_ed']}:{scene['k_ep']}:{scene['k_ch']}",
                f"   {scene['start']} ({scene['count']})"
            ))

            # Set the last task
            scene['task'] = ProcessingTask(name=task)

            # Generate frames for this scene
            if not simulation:
                process_scene(scene=scene, force=force)
            else:
                consolidate_scene(scene=scene)

            # Calculate hash for the video
            hashes_str += f",{scene['task'].hashcode}"


            # Create concatenation file
            do_generate_video = False
            concat_fp = generate_concat_file(
                episode=k_ep_src,
                chapter=chapter,
                scene=scene,
                previous_concat_fp=previous_concat_fp
            )
            if concat_fp != previous_concat_fp and concat_fp != '':
                # Add the filepath to the the concatenation video file
                scene['task'].concat_file = concat_fp
                # clips.append({
                #     'path': concat_fp,
                #     'hash': scene_hash,
                #     'task': scene['task'] if scene['task'] != 'final' else ''
                # })
                do_generate_video = True
            else:
                # This scene has not enough frames to generate a video scene,
                # append images to the previous scene and regenerate it
                combine_frames(
                    chapter=chapter,
                    # scene=clips[-1],
                    scene=scene,
                    force=True,
                    simulation=simulation,
                    watermark=f"{scene['no'] - 1}" if watermark else None
                )
            previous_concat_fp = concat_fp

            # Combine images into a video file
            if do_generate_video:
                # print(purple("\tcombine images to video (scene): k_p=%s, scene no. %d" % (k_p, scene['no'])))
                combine_frames(
                    chapter=chapter,
                    # scene=clips[-1],
                    scene=scene,
                    force=force,
                    simulation=simulation,
                    watermark=f"{scene['no']}" if watermark else None
                )

            elapsed = time.time() - start_time
            print(purple(
                f"\t\tscene no. {scene['no']} generated in "
                f"{s_to_sexagesimal(elapsed)} ({elapsed/scene['count']:02f}s/f)\n"
            ))

            if True:
                print(lightcyan("================================== Scene ======================================="))
                pprint(scene)
                print(lightcyan("==============================================================================="))
                # sys.exit()

            print(purple(scene['task']))

        video['hash'] = calc_hash(hashes_str[:-1])
        # video_clips[chapter]['hash'] = video_fp['hash']

    # For each part, concatenate scenes in a single clip
    for chapter in chapters:
        video: VideoChapter
        if chapter in ['g_debut', 'g_fin']:
            video: VideoChapter = db[chapter]['video']
        else:
            video: VideoChapter = (
                db[k_ep]['video']['target'][chapter]
                if edition == ''
                else db[k_ep]['video'][edition][chapter]
            )

        if len(video) > 0:
            concat_scenes(
                episode=episode,
                chapter=chapter,
                video=video,
                force=force,
                simulation=simulation
            )

    verbose = True

    # Create concatenation files and video files for silences
    if chapter == '':
        print(lightgreen(f"\nCreate silences after:"))
        silences = generate_silence_concat_file(episode=episode)
        if verbose:
            print(lightgreen(f"silences:"))
            pprint(silences)

        for chapter, filepaths in silences.items():
            if verbose:
                print(lightgreen(f"combine images to video: {chapter}"))
                pprint(filepaths)

            for f in filepaths:
                if verbose:
                    print(f"{chapter}: {f}")
                virtual_video_scene: Scene = Scene(
                    task=ProcessingTask(
                        name=task,
                        concat_file=f,
                    )
                )
                scene_fp = combine_frames(
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
    if chapter == '':

        # Generate concatenation files which contains all video files
        concat_fp = create_concatenation_file_video(
            k_ep=k_ep,
            chapter=chapter,
            video_files=video_clips
        )

        # Get language
        language = db[episode]['audio']['lang']
        lang_str = '' if language == 'fr' else f"_{language}"

        # Concatenate video clips
        episode_video_filepath = os.path.join(
            db[episode]['cache_path'],
            "video",
            f"{episode}_video{lang_str}.mkv"
        )

        # Force concatenation
        print(
            lightgreen(
                f"\nConcatenate video clips:\n"
            ),
            f"\t{episode_video_filepath}\n"
        )
        ffmpeg_command = [
            ffmpeg_exe,
            db['common']['settings']['verbose'].split(' '),
            "-f", "concat",
            "-safe", "0",
            "-i", concat_fp,
            "-c", "copy",
            "-y", episode_video_filepath
        ]

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






