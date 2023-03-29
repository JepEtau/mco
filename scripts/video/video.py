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
from utils.hash import calculate_hash
from video.consolidate_shot import consolidate_shot
from filters.ffmpeg_utils import execute_ffmpeg_command
from utils.path import create_folder_for_video
from utils.time_conversions import current_datetime_str
from utils.pretty_print import *
from video.concatenation import (
    combine_images_into_video,
    concatenate_shots,
    create_concatenation_file,
    create_concatenation_file_silence,
    create_concatenation_file_video,
)
from video.process_shot import process_shot


def generate_video(db, k_ed:str, k_ep:str,
                    last_task:str, cpu_count=0, k_part:str='',
                    force:bool=False, simulation:bool=False,
                    shot_min:int=0, shot_max:int=999999,
                    do_regenerate=False):
    start_time = time.time()

    # Create the video directory
    create_folder_for_video(db, k_ep)


    # List video files for each
    video_files = dict()
    for k in K_ALL_PARTS:
        video_files[k] = {
            'hash': '',
            'shotlist': list(),
        }

    # print("Generate video: %s, %s, tasks=%s" % (edition, k_ep, ', '.join(tasks)))

    # Process part(s)
    k_parts = K_ALL_PARTS_ORDERED if k_part == '' else [k_part]
    for k_p in k_parts:
        hashes_str = ''

        if k_p in ['g_debut', 'g_fin']:
            db_video = db[k_p]['video']
            k_ep_src_main = db_video['src']['k_ep']
            create_folder_for_video(db, k_p)
        elif k_ep == 'ep00':
            sys.exit("Erreur: le numéro de l'épisode est manquant")
        else:
            if k_ed == '':
                # Final
                db_video = db[k_ep]['video']['target'][k_p]
            else:
                # Study
                db_video = db[k_ep]['video'][k_ed][k_p]
            k_ep_src_main = k_ep

        if db_video['count'] == 0:
            # Part is empty: precedemment in ep01, asuivre in ep39
            continue

        print_green("%s %s: extract and process images" % (current_datetime_str(), k_p))

        previous_concatenation_filepath = ''

        # Walk through target shots
        shots = db_video['shots']
        for shot in shots:
            start_shot_time = time.time()
            if not (shot_min <= shot['no'] < shot_max):
                continue

            # If in study mode, patch the shot
            if k_ed != '':
                shot.update({
                    'dst': {
                        'count': shot['count'],
                        'k_ed': k_ed,
                        'k_ep': k_ep,
                        'k_part': k_p,
                    },
                    'src': {
                        'k_ed': k_ed,
                        'k_ep': k_ep,
                        'k_part': k_p,
                    },
                    'k_ed': k_ed,
                    'k_ep': k_ep,
                    'k_part': k_p,
                })


            print_lightcyan("\t\t%s: %s\t(%d)\t<- %s:%s:%s   %d (%d)" % (
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
            shot['last_task'] = last_task

            # Generate frames for this shot
            if not simulation:
                process_shot(db,
                    shot=shot,
                    cpu_count=cpu_count)
            else:
                consolidate_shot(db, shot=shot)
                pprint(shot)

            # Calculate hash for the video
            shot_hash = shot['last_step']['hash']
            shot_hash = shot['last_task'] if shot_hash == '' else shot_hash
            hashes_str += '%s:' % (shot_hash)

            if False:
                print_lightcyan("================================== SHOT =======================================")
                pprint(shot)
                print_lightcyan("===============================================================================")
                # sys.exit()

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
                video_files[k_p]['shotlist'].append({
                    'path': tmp,
                    'hash': shot_hash
                })
            previous_concatenation_filepath = tmp

            if k_p == 'episode':
                minutes, seconds = divmod(time.time() - start_shot_time, 60)
                if minutes != 0 and seconds != 0:
                    print("\t\t\t%d:%02d" % (minutes, seconds), flush=True)

        hashes_str = hashes_str[:-1]
        db_video['hash'] = calculate_hash(hashes_str)
        video_files[k_p]['hash'] = db_video['hash']

    # minutes, seconds = divmod(time.time() - start_shot_time,60)
    # print("=> processed shots in %d:%02d" % (minutes, seconds), flush=True)

    pprint(video_files)
    # Combine images to mkv
    for k_p, video_shots in video_files.items():
        if k_part != '' and k_p != k_part or simulation:
            # Do not combine when a single part has to be processed
            # print_yellow("Do not combine when a single part has to be processed: k_p=%s" % (k_p))
            continue

        print_purple("\tcombine images to video (shot): k_p=%s" % (k_p))

        if False:
            # Multi processing
            cpu_count = int(multiprocessing.cpu_count() / 2)
            with ThreadPoolExecutor(max_workers=cpu_count) as executor:
                work_result = {executor.submit(combine_images_into_video,
                                db['common'], k_p, work, force=force, simulation=simulation): None
                                for work in video_shots['shotlist']}
                for future in concurrent.futures.as_completed(work_result):
                    pass
        else:
            for video_shot in video_shots['shotlist']:
                combine_images_into_video(db['common'], k_p, video_shot, force=force, simulation=simulation)


    # For each part, concatenate shots in a single clip
    for k_p, v in video_files.items():
        if len(v['shotlist']) > 1 and not simulation:
            print_lightgreen("concatenate_shots, k_part=%s" % (k_p))
            concatenate_shots(db, k_ep=k_ep, k_part=k_p, video_files=v, force=force)

    # Create concatenation files and video files for silences
    if k_part == '' and not simulation:
        # Only if a full generation is asked
        video_files_tmp = create_concatenation_file_silence(db, k_ep=k_ep)
        for k_p, filepaths in video_files_tmp.items():
            video_files[k_p] += filepaths
            for f in filepaths:
                # print("%s: %s" % (k_p, f))
                print_purple("TODO: clean this! combine images to mkv")
                combine_images_into_video(db['common'],
                    k_part=k_p,
                    input_filename=f,
                    force=force,
                    simulation=simulation)


    # Concatenate video clips from all parts
    if k_part == '' and not simulation:
        # Generate concatenation files which contains all video files
        concatenation_filepath = create_concatenation_file_video(db,
            k_ep=k_ep, k_part=k_part, video_files=video_files)

        # Concatenate video clips
        episode_video_filepath = os.path.join(db[k_ep]['cache_path'],
            "video", "%s_video_%s.mkv" % (k_ep, db_video['hash']))
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
            std = execute_ffmpeg_command(db, command=command_ffmpeg, filename=episode_video_filepath)
            if len(std) > 0:
                print(std)





