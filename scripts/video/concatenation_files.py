# -*- coding: utf-8 -*-
import sys
import os
from pprint import pprint

from utils.common import (
    FPS,
    K_GENERIQUES,
    K_PARTS,
)
from processing_chain.get_frame_list import (
    get_frame_list,
    get_frame_list_single,
)
from video.utils import create_folder_for_concatenation
from utils.pretty_print import *




def create_concatenation_file(db, k_ep, k_part, shot, previous_concatenation_filepath=''):
    print_lightgrey(f"\tcreate concatenation file: ", end='')
    print_lightcyan(f"{k_ep}, {k_part}, shot no. {shot['no']}")
    # Use a single concatenation file for
    #   - g_asuivre, g_reportage
    if k_part in ['g_asuivre', 'g_reportage']:
        return create_single_concatenation_file(db,
            k_ep=k_ep, k_part=k_part, shot=shot,
            previous_concatenation_filepath=previous_concatenation_filepath)

    # This function is used for the following parts:
    #   - episode
    #   - reportage

    # Get the list of images
    images_filepath = get_frame_list(db=db,
        k_ep=k_ep, k_part=k_part, shot=shot)

    # Folder for concatenation file
    create_folder_for_concatenation(db, k_ep, k_part)

    # Open concatenation file
    k_ed = shot['k_ed']
    if (previous_concatenation_filepath == ''
        or len(images_filepath) >= 5):
        # Use previous concatenation files because FFmpeg
        # cannot create a video file from less than 5 frames
        if k_part in ['g_debut', 'g_fin']:
            concatenation_filepath = os.path.join(
                db[k_part]['cache_path'],
                "concatenation",
                f"{k_part}_{shot['no']:03}__{k_ed}_{shot['k_ep']}_.txt")
        else:
            concatenation_filepath = os.path.join(
                db[k_ep]['cache_path'],
                "concatenation",
                f"{k_ep}_{k_part}_{shot['no']:03}__{k_ed}_.txt")

        # Save this filepath because it may be used for next shot
        previous_concatenation_filepath = concatenation_filepath
        concatenation_file = open(concatenation_filepath, "w")

    else:
        sys.exit(print_red("(TODO: deprecate) Use previous concatenation file: %s" % (previous_concatenation_filepath)))
        concatenation_file = open(previous_concatenation_filepath, 'a')

    # print(f"{concatenation_filepath}")

    # Frame duration
    duration_str = "duration %.02f\n" % (1/FPS)

    # Write into the concatenation file
    for p in images_filepath:
        concatenation_file.write(f"file \'{p}\' \n")
        concatenation_file.write(duration_str)
    concatenation_file.close()

    return previous_concatenation_filepath


def create_single_concatenation_file(db, k_ep, k_part, shot, previous_concatenation_filepath=''):
    """This function is used for the following parts:
        - precedemment
        - g_asuivre
        - asuivre
        - g_reportage
    """
    # print("%s._create_concatenation_file" % (__name__))
    # pprint(shot)
    k_ep_or_g = k_ep if k_part not in ['g_debut', 'g_fin'] else k_part

    # Get the list of images
    images_filepath = get_frame_list_single(db,
        k_ep=k_ep, k_part=k_part, shot=shot)

    # Folder for concatenation file
    create_folder_for_concatenation(db, k_ep, k_part)

    # Open concatenation file
    # hash = shot['last_step']['hash']
    k_ed = shot['k_ed']
    if previous_concatenation_filepath == '':
        # Create a concatenation file

        if k_part in ['g_debut', 'g_fin']:
            # Use the edition/episode defined as reference
            concatenation_filepath = os.path.join(
                db[k_ep_or_g]['cache_path'], "concatenation",
                "%s_video.txt" % (k_ep_or_g))
        else:
            concatenation_filepath = os.path.join(db[k_ep_or_g]['cache_path'],
                "concatenation", "%s_%s_%03d__%s_%s_.txt" % (k_ep, k_part, 0, k_ed, shot['src']['k_ep']))
        previous_concatenation_filepath = concatenation_filepath
        concatenation_file = open(concatenation_filepath, "w")

    else:
        # Use the previous concatenation file
        concatenation_file = open(previous_concatenation_filepath, "a")

    # Frame duration
    duration_str = "duration %.02f\n" % (1/FPS)

    # Write into the concatenation file
    for p in images_filepath:
        concatenation_file.write(f"file \'{p}\' \n")
        concatenation_file.write(duration_str)
    concatenation_file.close()

    return previous_concatenation_filepath


def create_concatenation_file_video(db, k_ep, k_part, video_files:dict):
    """ This function creates a concatenation file which lists
        all video files to merge:
        - precedemment
        - episode
        - g_asuivre
        - asuivre
        - g_reportage
        - reportage

        Returns:
          Concatenation file path
    """
    verbose = False
    if verbose:
        print_lightcyan("create_concatenation_file_video %s:%s" % (k_ep, k_part))
        pprint(video_files)

    # Assume language is same for k_ep and start/end/to_follow/documentary credits
    language = db[k_ep]['audio']['lang']
    lang_str = '' if language == 'fr' else f"_{language}"

    for k_ep_or_g in [k_ep, 'g_debut', 'g_fin']:

        if k_ep_or_g in ['g_debut', 'g_fin']:
            k_part = k_ep_or_g
            suffix = f"{k_part}"
        else:
            suffix = f"_{k_part}" if k_part != '' else ''
            suffix = f"{k_ep}{suffix}_video"
            k_part = ''

        # Folder used to store concatenation file
        create_folder_for_concatenation(db, k_ep, k_part)

        # Open concatenation file
        concatenation_filepath = os.path.join(
            db[k_ep_or_g]['cache_path'],
            "concatenation",
            f"{suffix}{lang_str}.txt")
        concatenation_file = open(concatenation_filepath, "w")
        if verbose:
            print_green(f"create_concatenation_file_video: {concatenation_filepath}")

        if k_part in ['g_debut', 'g_fin']:
            for k_p in K_PARTS:
                for shot in video_files[k_p]:
                    p = shot['path'].replace('.txt', f"_{shot['hash']}_{shot['last_task']}{lang_str}.mkv")
                    p = p.replace('concatenation', 'video')
                    concatenation_file.write(f"file \'{p}\' \n")
        else:
            for k_p in K_PARTS:
                try:
                    for filepath in video_files[k_p]['files']:
                        p = filepath.replace('concatenation', 'video')
                        concatenation_file.write(f"file \'{p}\' \n")
                except:
                    if k_p in K_GENERIQUES:
                        for shot in video_files[k_p]['shotlist']:
                            p = shot['path'].replace('.txt', f"_{shot['hash']}_{shot['last_task']}{lang_str}.mkv")
                            p = p.replace('concatenation', 'video')
                            concatenation_file.write(f"file \'{p}\' \n")
        concatenation_file.close()
        return concatenation_filepath


def create_concatenation_file_silence(db, k_ep):
    # Create a concatenation file for silence
    files = dict()
    for k_p in K_PARTS:
        files[k_p] = list()
        # print("%s:%s" % (k_ep, k_p))
        if k_p not in db[k_ep]['audio'].keys():
            continue

        if ('silence' in db[k_ep]['audio'][k_p].keys()
                and db[k_ep]['audio'][k_p]['silence'] > 0):

            print_lightgrey(f"\t- {k_p}")

            # Convert silence duration in nb of frames
            # print(db[k_ep]['audio'][k_p]['silence'])
            silence_count = int(db[k_ep]['audio'][k_p]['silence'] * FPS / 1000)
            # print("silence = %d frames" % (silence_count))

            # Frame duration
            black_image_filepath = os.path.join(db['common']['directories']['cache'], 'black.png')
            duration_str = "duration %.02f\n" % (1/FPS)

            # Create the concatenation file for the silence
            create_folder_for_concatenation(db, k_ep, k_part=k_p)
            concatenation_filepath = os.path.join(db[k_ep]['cache_path'],
                "concatenation",
                "%s_%s__999_silence.txt" % (k_ep, k_p))
            concatenation_file = open(concatenation_filepath, "w")

            # Add frames to the files
            for i in range(silence_count):
                concatenation_file.write("file \'%s\' \n" % (black_image_filepath))
                concatenation_file.write(duration_str)

            files[k_p].append(concatenation_filepath)

            concatenation_file.close()

    return files

