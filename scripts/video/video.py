# -*- coding: utf-8 -*-
import sys
from copy import deepcopy
import os

import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import multiprocessing

from pprint import pprint

from utils.common import (
    K_ALL_PARTS,
    K_ALL_PARTS_ORDERED,
    get_k_part_from_frame_no,
    get_shot_from_frame_no_new,
)
from utils.consolidate import consolidate_shot
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


def generate_video(db, k_ed, k_ep:str, tasks:list, cpu_count=0, k_part:str='', force:bool=False, simulation:bool=False, shot_min:int=0, shot_max:int=999999):

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
            db_video = db[k_ep]['common']['video'][k_p]
            k_ep_src_main = k_ep
            # pprint(db_video)

        if db_video['count'] == 0:
            continue

        print("%s %s: extract and process images" % (current_datetime_str(), k_p))

        previous_concatenation_filepath = ''

        # Walk through shots
        shots = db_video['shots']
        for shot in shots:
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

            shot['']
            try:
                shot_src.update({
                    'layers': db[k_ep_src]['common']['video'][k_part_src]['layers']
                })
            except:
                # no layers specified
                pass


            shot_src.update({
                'k_ed': k_ed_src,
                'k_ep': k_ep_src,
                'k_part': k_part_src,
                'tasks': tasks.copy(),
                'dst': shot['dst'],
            })
            if 'effects' in shot.keys():
                shot_src.update({'effects': shot['effects']})

            # if 'dst' in shot.keys():
            #     print("--> detected dst to generate the video: target: %s:%s -->" % (k_ep, k_part))
            #     pprint(shot)
            #     print("")
            #     shot_src['dst'] = shot['dst']
            if shot == shots[-1]:
                shot_src['last'] = True

            # Generate frames for this shot
            if not simulation:
                process_shot(db,
                    shot=shot_src,
                    db_combine={},
                    cpu_count=cpu_count)
            else:
                consolidate_shot(db, shot=shot_src)

            # Patch the shot to create the concatenation file
            if 'src' in shot.keys() and shot['src']['use']:
                # shot_properties_saved = ({'start': shot_src['start'], 'count': shot_src['count']})
                shot_src['dst'].update({
                    'start': shot['src']['start'],
                    'count': shot['src']['count']
                })
            # shot_src['count'] = shot['count']

            print("+++++++++++++++++++ shot SRC for concatenation +++++++++++++++++++")
            pprint(shot_src)
            print("+++++++++++++++++++++++++++ shot  ++++++++++++++++++++++++++++++++")
            pprint(shot)
            print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n")
            # Create concatenation file
            tmp = create_concatenation_file(db,
                k_ep=k_ep_src_main, k_part=k_p, shot=shot_src,
                previous_concatenation_filepath=previous_concatenation_filepath)
            if tmp != previous_concatenation_filepath and tmp != '':
                # Add the filepath to the the concatenation video file
                video_files[k_p].append(tmp)
            previous_concatenation_filepath = tmp


    # Combine images to mkv
    for k_p, files in video_files.items():
        if k_part != '' and k_p != k_part or simulation:
            # Do not combine when a single part has to be processed
            continue

        # for f in files:
        #     combine_images_into_video(
        #         db_settings= db['common']['settings'],
        #         k_part=k_p,
        #         input_filename=f,
        #         force=force,
        #         simulation=simulation)

        cpu_count = int(multiprocessing.cpu_count() / 2)
        with ThreadPoolExecutor(max_workers=cpu_count) as executor:
            work_result = {executor.submit(combine_images_into_video,
                            db['common']['settings'], k_p, work, force=force, simulation=simulation): None
                            for work in files}
            for future in concurrent.futures.as_completed(work_result):
                pass

    if k_part in ['g_debut', 'g_fin']:
        return

    # Concatenate shots in a single clip
    for k_p, filepaths in video_files.items():
        if len(filepaths) > 1 and not simulation:
            concatenate_shots(db, k_ed=k_ed, k_ep=k_ep, k_part=k_p, video_files=video_files, force=force)


    # Create concatenation files and video files for silences
    if k_part == '' and not simulation:
        # Only if a full generation is asked
        video_files_tmp = create_concatenation_file_silence(db, k_ed=k_ed, k_ep=k_ep)
        for k_p, filepaths in video_files_tmp.items():
            video_files[k_p] += filepaths
            for f in filepaths:
                # print("%s: %s" % (k_p, f))
                combine_images_into_video(db['common']['settings'], k_part=k_p, input_filename=f, force=force, simulation=simulation)


    # Concatenate video clips from all parts
    if k_part == '' and not simulation:
        # Generate a concatenation file that contains all video files except g_debut and g_fin
        concatenation_filepath = create_concatenation_file_video(db, k_ed=k_ed, k_ep=k_ep, video_files=video_files)

        # Concatenate video clips
        episode_video_filepath = os.path.join(db[k_ep]['common']['path']['cache'],
            "video", "%s_video.mkv" % (k_ep))
        if not os.path.exists(episode_video_filepath) or force:
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




