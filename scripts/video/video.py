# -*- coding: utf-8 -*-
import sys
import os
import time

import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import multiprocessing

from pprint import pprint

from utils.common import (
    K_ALL_PARTS,
    K_ALL_PARTS_ORDERED,
)
from utils.consolidate_shots import consolidate_shot
from utils.ffmpeg import ffmpeg_execute_command
from utils.path import create_video_directory
from utils.time_conversions import current_datetime_str
from video.concatenation import (
    combine_images_into_video,
    concatenate_shots,
    create_concatenation_file,
    create_concatenation_file_silence,
    create_concatenation_file_video,
)
from video.effects import create_black_frame
from video.shots import process_shot


def generate_video(db, k_ep:str,
                    tasks:list, cpu_count=0, k_part:str='',
                    force:bool=False, simulation:bool=False,
                    shot_min:int=0, shot_max:int=999999,
                    do_regenerate=False):
    start_time = time.time()

    # Create the video directory
    create_video_directory(db, k_ep)

    # Generate a black frame for silences
    if not simulation:
        create_black_frame(db, tasks[-1])

    # List video files for each
    video_files = dict()
    for k in K_ALL_PARTS:
        video_files[k] = list()

    # print("Generate video: %s, %s, tasks=%s" % (edition, k_ep, ', '.join(tasks)))

    # Process part(s)
    k_parts = K_ALL_PARTS_ORDERED if k_part == '' else [k_part]
    for k_p in k_parts:

        if k_p in ['g_debut', 'g_fin']:
            db_video = db[k_p]['target']['video']
            k_ep_src_main = db[k_p]['target']['video']['src']['k_ep']
            create_video_directory(db, k_p)
        elif k_ep == 'ep00':
            sys.exit("Erreur: le numéro de l'épisode est manquant")
        else:
            db_video = db[k_ep]['target']['video'][k_p]
            k_ep_src_main = k_ep

        if db_video['count'] == 0:
            # Part is empty: precedemment in ep01, asuivre in ep39
            continue

        print("%s %s: extract and process images" % (current_datetime_str(), k_p))

        previous_concatenation_filepath = ''

        # Walk through target shots
        shots = db_video['shots']
        for shot in shots:
            start_shot_time = time.time()
            if not (shot_min <= shot['no'] < shot_max):
                continue

            print("\t\t%s: %s\t(%d)\t<- %s:%s:%s   %d (%d)" % (
                "{:3d}".format(shot['no']),
                "{:5d}".format(shot['start']),
                shot['dst']['count'],
                shot['k_ed'],
                shot['k_ep'],
                shot['k_part'],
                shot['start'],
                shot['count']),
                flush=True)

            # Add list of task for this shot
            shot['tasks'] = tasks.copy()

            # Generate frames for this shot
            if not simulation:
                process_shot(db,
                    shot=shot,
                    cpu_count=cpu_count)
            else:
                consolidate_shot(db, shot=shot)
                pprint(shot)

            # print("+++++++++++++++++++++ shot for concatenation +++++++++++++++++++++")
            # pprint(shot)
            # print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            # print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n")
            # Create concatenation file
            tmp = create_concatenation_file(db,
                k_ep=k_ep_src_main, k_part=k_p, shot=shot,
                previous_concatenation_filepath=previous_concatenation_filepath)
            if tmp != previous_concatenation_filepath and tmp != '':
                # Add the filepath to the the concatenation video file
                video_files[k_p].append(tmp)
            previous_concatenation_filepath = tmp

            if k_p == 'episode':
                minutes, seconds = divmod(time.time() - start_shot_time, 60)
                print("\t\t\t=> processed shot in %d:%02d" % (minutes, seconds), flush=True)


    minutes, seconds = divmod(time.time() - start_shot_time,60)
    print("=> processed shots in %d:%02d" % (minutes, seconds), flush=True)

    # Combine images to mkv
    for k_p, files in video_files.items():
        if k_part != '' and k_p != k_part or simulation:
            # Do not combine when a single part has to be processed
            continue

        cpu_count = int(multiprocessing.cpu_count() / 2)
        with ThreadPoolExecutor(max_workers=cpu_count) as executor:
            work_result = {executor.submit(combine_images_into_video,
                            db['common']['settings'], k_p, work, force=force, simulation=simulation): None
                            for work in files}
            for future in concurrent.futures.as_completed(work_result):
                pass

    # Do not continue if generique is the only ask part to generate
    #  and which are not related to an episode
    if k_part in ['g_debut', 'g_fin']:
        return


    # Concatenate shots in a single clip
    for k_p, filepaths in video_files.items():
        if len(filepaths) > 1 and not simulation:
            concatenate_shots(db, k_ep=k_ep, k_part=k_p, video_files=video_files, force=force)


    # Create concatenation files and video files for silences
    if k_part == '' and not simulation:
        # Only if a full generation is asked
        video_files_tmp = create_concatenation_file_silence(db, k_ep=k_ep)
        for k_p, filepaths in video_files_tmp.items():
            video_files[k_p] += filepaths
            for f in filepaths:
                # print("%s: %s" % (k_p, f))
                combine_images_into_video(db['common']['settings'], k_part=k_p, input_filename=f, force=force, simulation=simulation)


    # Concatenate video clips from all parts
    if k_part == '' and not simulation:
        # Generate a concatenation file that contains all video files except g_debut and g_fin
        concatenation_filepath = create_concatenation_file_video(db, k_ep=k_ep, video_files=video_files)

        # Concatenate video clips
        episode_video_filepath = os.path.join(db[k_ep]['target']['path_cache'],
            "video", "%s_video.mkv" % (k_ep))
        if not os.path.exists(episode_video_filepath) or force or do_regenerate:
            print("%s concatenate video clips to %s" % (current_datetime_str(), episode_video_filepath))
            command_ffmpeg = [db['common']['settings']['ffmpeg_exe']]
            command_ffmpeg.extend(db['common']['settings']['verbose'].split(' '))
            command_ffmpeg.extend([
                "-f", "concat",
                "-safe", "0",
                "-i", concatenation_filepath,
                "-c", "copy",
                "-y", episode_video_filepath
            ])
            std = ffmpeg_execute_command(command_ffmpeg, filename=episode_video_filepath)
            if len(std) > 0:
                print(std)





