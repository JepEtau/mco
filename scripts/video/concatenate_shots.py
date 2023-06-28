# -*- coding: utf-8 -*-
import os
from pprint import pprint

from img_toolbox.ffmpeg_utils import execute_ffmpeg_command

from video.utils import create_folder_for_concatenation
from utils.time_conversions import current_datetime_str

from utils.pretty_print import *



def concatenate_shots(db, k_ep:str, k_part:str, video_files:dict,
                      force:bool=False, simulation:bool=False):
    verbose = False
    print_lightcyan(f"\nConcatenate shots: {k_ep}:{k_part}")
    if verbose:
        pprint(video_files)

    if k_part in ['g_debut', 'g_fin']:
        suffix = f"{k_part}_video"
        k_ep_or_g = k_part
    else:
        suffix = f"{k_ep}_{k_part}"
        k_ep_or_g = k_ep

    language = db[k_ep_or_g]['audio']['lang']
    lang_str = '' if language == 'fr' else f"_{language}"

    # Folder used to store concatenation file
    create_folder_for_concatenation(db, k_ep, k_part)

    # Last task is the suffix
    last_task = video_files['shotlist'][0]['last_task']
    last_task_str = '' if last_task == '' else f"_{last_task}"

    concatenation_filepath = ''

    if len(video_files['shotlist']) > 1:
        # Create concatenation file
        cache_directory = db[k_ep_or_g]['cache_path']
        concatenation_filepath = os.path.join(cache_directory,
            "concatenation",
            f"{suffix}_{video_files['hash']}{last_task_str}.txt")

        concatenation_file = open(concatenation_filepath, "w")
        for shot in video_files['shotlist']:
            filepath = shot['path']
            hash = shot['hash']
            p = filepath.replace('.txt', f"_{hash}{last_task_str}.mkv")
            p = p.replace('concatenation', 'video')
            concatenation_file.write(f"file \'{p}\' \n")
        concatenation_file.close()

        # Output video file
        output_filepath = os.path.join(cache_directory,
            "video",
            f"{suffix}_{video_files['hash']}{last_task_str}{lang_str}.mkv")

        if verbose:
            print("%s %s: concatenate shots into a single clip: %s" % (current_datetime_str(), k_part, output_filepath))
        print(f"\t{output_filepath}")
        # Concatenate shots into a single video
        ffmpeg_command = [db['common']['tools']['ffmpeg']]
        ffmpeg_command.extend(db['common']['settings']['verbose'].split(' '))
        ffmpeg_command.extend([
            "-f", "concat",
            "-safe", "0",
            "-i", concatenation_filepath,
            "-c", "copy",
            "-y", output_filepath
        ])
        if os.path.exists(output_filepath) and not force:
            print_lightgrey(' '.join(ffmpeg_command))
        else:
            if verbose:
                print_lightgrey(' '.join(ffmpeg_command))
            std = execute_ffmpeg_command(db,
                command=ffmpeg_command,
                filename=output_filepath,
                simulation=simulation)
            print(std)
    else:
        concatenation_filepath = video_files['shotlist'][0]['path']
        output_filepath = concatenation_filepath.replace('concatenation', 'video')
        output_filepath = output_filepath.replace('.txt', f"_{video_files['shotlist'][0]['hash']}{last_task_str}.mkv")

    return concatenation_filepath, output_filepath

