# -*- coding: utf-8 -*-
import sys
import os
import time
# from datetime import (
#     date,
#     datetime,
#     time,
#     timedelta
# )

import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import multiprocessing

from pprint import pprint

from utils.common import (
    K_ALL_PARTS,
    K_ALL_PARTS_ORDERED,
)
from shot.consolidate_shot import consolidate_shot
from img_toolbox.ffmpeg_utils import execute_ffmpeg_command
from processing_chain.hash import calculate_hash
from utils.nested_dict import nested_dict_set
from utils.time_conversions import convert_s_to_m_s_ms, current_datetime_str
from utils.pretty_print import *

from video.concatenation_files import (
    create_concatenation_file,
    create_concatenation_file_silence,
    create_concatenation_file_video,
)
from video.utils import create_folder_for_video
from video.concatenate_shots import concatenate_shots
from video.combine_images_into_video import combine_images_into_video
from shot.process_shot import process_shot


def generate_video_track(db, k_ed:str, k_ep:str,
                    last_task:str, cpu_count=0, k_part:str='',
                    force:bool=False, simulation:bool=False,
                    shot_min:int=0, shot_max:int=999999,
                    do_regenerate=False,
                    watermark:bool=False):

    # Create the video directory
    create_folder_for_video(db, k_ep)


    # List video files for each part
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

        print(f"\n<<<<<<<<<<<<<<<<<<<<< {k_p} >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        print(f"{current_datetime_str()}")

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


            print_lightgreen("\t%s: %s\t(%d)\t<- %s:%s:%s   %d (%d)" % (
                "{:3d}".format(shot['no']),
                "{:5d}".format(shot['start']),
                shot['dst']['count'],
                shot['k_ed'],
                shot['k_ep'],
                shot['k_part'],
                shot['start'],
                shot['count']),
                flush=True)

            # Set the last task
            shot['last_task'] = last_task

            # Generate frames for this shot
            if not simulation:
                process_shot(db,
                    shot=shot,
                    force=force)
            else:
                consolidate_shot(db, shot=shot)

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
            do_generate_shot_video = False
            tmp = create_concatenation_file(db,
                k_ep=k_ep_src_main, k_part=k_p, shot=shot,
                previous_concatenation_filepath=previous_concatenation_filepath)
            if tmp != previous_concatenation_filepath and tmp != '':
                # Add the filepath to the the concatenation video file
                video_files[k_p]['shotlist'].append({
                    'path': tmp,
                    'hash': shot_hash,
                    'last_task': shot['last_task'] if shot['last_task'] != 'final' else ''
                })
                do_generate_shot_video = True
            else:
                # This shot has not enough frames to generate a video shot,
                # append images to the previous shot and regenerate it
                watermark_str = f"{shot['no'] - 1}" if watermark else None
                combine_images_into_video(db['common'],
                    k_p,
                    video_shot=video_files[k_p]['shotlist'][-1],
                    force=True,
                    simulation=simulation,
                    watermark=watermark_str)

            previous_concatenation_filepath = tmp


            # if do_generate_shot_video and shot['last_task'] not in ['edition']:
            if do_generate_shot_video:
                # print_purple("\tcombine images to video (shot): k_p=%s, shot no. %d" % (k_p, shot['no']))
                watermark_str = f"{shot['no']}" if watermark else None
                combine_images_into_video(db['common'],
                    k_p,
                    video_shot=video_files[k_p]['shotlist'][-1],
                    force=force,
                    simulation=simulation,
                    watermark=watermark_str)


            elapsed_time = time.time() - start_shot_time
            minutes, seconds, milliseconds = convert_s_to_m_s_ms(elapsed_time)
            print_purple(f"\t\tshot no. {shot['no']} generated in %02d:%02d.%d (%.02fs/f)\n" % (
                minutes, seconds, int(1 + milliseconds/100),
                elapsed_time/shot['count']))


        hashes_str = hashes_str[:-1]
        db_video['hash'] = calculate_hash(hashes_str)
        video_files[k_p]['hash'] = db_video['hash']

    # minutes, seconds = divmod(time.time() - start_shot_time,60)
    # print("=> processed shots in %d:%02d" % (minutes, seconds), flush=True)

    # Remove g_debut, g_fin
    # for k_p in ['g_debut', 'g_fin']:
    #     try:
    #         del video_files[k_p]
    #     except:
    #         pass

    # For each part, concatenate shots in a single clip
    for k_p, v in video_files.items():
        if len(v['shotlist']) > 0:
            concatenation_filepath, output_filepath = concatenate_shots(db,
                k_ep=k_ep, k_part=k_p, video_files=v, force=force, simulation=simulation)
            video_files[k_p]['files'] = [output_filepath]

    verbose = False
    if verbose:
        print_lightgreen(f"video_files")
        pprint(video_files)

    # Create concatenation files and video files for silences
    if k_part == '':
        print_lightgreen(f"\nCreate silences after:")
        video_files_tmp = create_concatenation_file_silence(db, k_ep=k_ep)
        if verbose:
            print_lightgreen(f"video_files_tmp")
            pprint(video_files_tmp)

        for k_p, filepaths in video_files_tmp.items():
            if verbose:
                print_lightgreen(f"combine images to video: {k_p}")
                pprint(filepaths)
            if len(filepaths) == 0:
                continue

            for f in filepaths:
                # print("%s: %s" % (k_p, f))
                virtual_video_shot = {'path': f, 'last_task': '', 'hash': ''}
                output_filepath = combine_images_into_video(
                    db_common=db['common'],
                    k_part=k_p,
                    video_shot=virtual_video_shot,
                    force=force,
                    simulation=simulation)
                try:
                    video_files[k_p]['files'].append(output_filepath)
                except:
                    nested_dict_set(video_files[k_p], [output_filepath], 'files')

    if verbose:
        print_lightgreen(f"video files used to concatenate all clips")
        pprint(video_files)


    # Concatenate video clips from all parts
    if k_part == '':
        # Generate concatenation files which contains all video files
        concatenation_filepath = create_concatenation_file_video(db,
            k_ep=k_ep, k_part=k_part, video_files=video_files)

        # Get language
        language = db[k_ep]['audio']['lang']
        lang_str = '' if language == 'fr' else f"_{language}"

        # Concatenate video clips
        episode_video_filepath = os.path.join(db[k_ep]['cache_path'], "video",
            f"{k_ep}_video{lang_str}.mkv")

        # Force concatenation
        # if not os.path.exists(episode_video_filepath) or force or do_regenerate:
        print(p_lightgreen(f"\nConcatenate video clips:\n"), f"\t{episode_video_filepath}\n")
        ffmpeg_command = [db['common']['tools']['ffmpeg']]
        ffmpeg_command.extend(db['common']['settings']['verbose'].split(' '))
        ffmpeg_command.extend([
            "-f", "concat",
            "-safe", "0",
            "-i", concatenation_filepath,
            "-c", "copy",
            "-y", episode_video_filepath
        ])

        std = execute_ffmpeg_command(db,
            command=ffmpeg_command,
            filename=episode_video_filepath,
            simulation=simulation)
        if len(std) > 0:
            print(std)




