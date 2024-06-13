import sys
import os
from pprint import pprint

from parsers.helpers import get_fps

from utils.mco_types import Scene
# Audio, VideoPart
from utils.mco_utils import makedirs
from utils.p_print import *
# from utils.types import
from parsers import (
    db,
    main_chapter_keys,
    credit_chapter_keys,
)
from utils.time_conversions import ms_to_frame
from video.frame_list import get_frame_list



def generate_concat_file(
    k_ep: str,
    k_ch: str,
    scene: Scene,
    previous_concat_fp: str = ''
):
    print(lightgrey(f"\tcreate concatenation file: "), end='')
    print(lightcyan(f"{k_ep}, {k_ch}, scene no. {scene['no']}"))
    # Use a single concatenation file for
    #   - g_asuivre, g_documentaire
    if k_ch in ['g_asuivre', 'g_documentaire']:
        return generate_single_concat_file(
            k_ep=k_ep,
            k_ch=k_ch,
            scene=scene,
            previous_concat_fp=previous_concat_fp
        )

    # This function is used for the following chapters:
    #   - episode
    #   - documentaire

    # Get the list of frames for this scene
    images_filepath = get_frame_list(k_ep=k_ep, k_ch=k_ch, scene=scene)

    # Folder for concatenation file
    makedirs(k_ep, k_ch, 'concatenation')

    # Open concatenation file
    k_ed = scene['k_ed']
    if previous_concat_fp == '' or len(images_filepath) >= 5:
        # Use previous concatenation files because FFmpeg
        # cannot create a video file from less than 5 frames
        if k_ch in ('g_debut', 'g_fin'):
            concatenation_filepath = os.path.join(
                db[k_ch]['cache_path'],
                "concatenation",
                f"{k_ch}_{scene['no']:03}__{k_ed}_{scene['k_ep']}_.txt"
            )
        else:
            concatenation_filepath = os.path.join(
                db[k_ep]['cache_path'],
                "concatenation",
                f"{k_ep}_{k_ch}_{scene['no']:03}__{k_ed}_.txt"
            )

        # Save this filepath because it may be used for next scene
        previous_concat_fp = concatenation_filepath
        concatenation_file = open(concatenation_filepath, "w")

    else:
        print(orange(f"Use previous concatenation file: {previous_concat_fp}"))
        print(orange(f"{len(images_filepath)}"))
        # print("-------------------------------------")
        # for k, v in db[k_ep]['video']['target'][k_ch].items():
        #     if k == 'scenes':
        #         continue
        #     print(f"{k}:")
        #     pprint(v)
        # sys.exit(print_red("Error or (TODO: deprecate) Use previous concatenation file: %s ?" % (previous_concatenation_filepath)))
        concatenation_file = open(previous_concat_fp, 'a')

    # print(f"{concatenation_filepath}")

    # Frame duration
    duration_str = "duration %.02f\n" % (1/get_fps(db))

    # Write into the concatenation file
    for p in images_filepath:
        concatenation_file.write(f"file \'{p}\' \n")
        concatenation_file.write(duration_str)
    concatenation_file.close()

    return previous_concat_fp


def generate_single_concat_file(db, k_ep, k_ch, scene, previous_concatenation_filepath=''):
    """This function is used for the following chs:
        - precedemment
        - g_asuivre
        - asuivre
        - g_documentaire
    """
    # print("%s._create_concatenation_file" % (__name__))
    # pprint(scene)
    k_ep_or_g = k_ep if k_ch not in ['g_debut', 'g_fin'] else k_ch

    # Get the list of images
    images_filepath = get_frame_list_single(
        k_ep=k_ep, k_ch=k_ch, scene=scene
    )

    # Folder for concatenation file
    makedirs(k_ep, k_ch, 'concatenation')

    # Open concatenation file
    # hash = scene['last_step']['hash']
    k_ed = scene['k_ed']
    if previous_concatenation_filepath == '':
        # Create a concatenation file

        if k_ch in ['g_debut', 'g_fin']:
            # Use the edition/episode defined as reference
            concatenation_filepath = os.path.join(
                db[k_ep_or_g]['cache_path'], "concatenation",
                "%s_video.txt" % (k_ep_or_g))
        else:
            concatenation_filepath = os.path.join(
                db[k_ep_or_g]['cache_path'],
                "concatenation",
                "%s_%s_%03d__%s_%s_.txt" % (k_ep, k_ch, 0, k_ed, scene['src']['k_ep'])
            )
        previous_concatenation_filepath = concatenation_filepath
        concatenation_file = open(concatenation_filepath, "w")

    else:
        # Use the previous concatenation file
        concatenation_file = open(previous_concatenation_filepath, "a")

    # Frame duration
    duration_str = "duration %.02f\n" % (1/get_fps(db))

    # Write into the concatenation file
    for p in images_filepath:
        concatenation_file.write(f"file \'{p}\' \n")
        concatenation_file.write(duration_str)
    concatenation_file.close()

    return previous_concatenation_filepath



def generate_video_concat_file(k_ep, k_ch, video_files:dict):
    """ This function creates a concatenation file which lists
        all video files to merge:
        - precedemment
        - episode
        - g_asuivre
        - asuivre
        - g_documentaire
        - documentaire

        Returns:
          Concatenation file path
    """
    verbose = False
    if verbose:
        print(lightcyan("create_video_concat_file %s:%s" % (k_ep, k_ch)))
        pprint(video_files)

    # Assume language is same for k_ep and start/end/to_follow/documentary credits
    language = db[k_ep]['audio']['lang']
    lang_str = '' if language == 'fr' else f"_{language}"

    for k_ep_or_g in [k_ep, 'g_debut', 'g_fin']:

        if k_ep_or_g in ['g_debut', 'g_fin']:
            k_ch = k_ep_or_g
            suffix = f"{k_ch}"
        else:
            suffix = f"_{k_ch}" if k_ch != '' else ''
            suffix = f"{k_ep}{suffix}_video"
            k_ch = ''

        # Folder used to store concatenation file
        makedirs(k_ep, k_ch, 'concatenation')

        # Open concatenation file
        concatenation_filepath = os.path.join(
            db[k_ep_or_g]['cache_path'],
            "concatenation",
            f"{suffix}{lang_str}.txt")
        concatenation_file = open(concatenation_filepath, "w")
        if verbose:
            print(green(f"create_video_concat_file: {concatenation_filepath}"))

        if k_ch in ['g_debut', 'g_fin']:
            print(red("Not allowed"))
            for k in main_chapter_keys():
                for scene in video_files[k]:
                    p = scene['path'].replace('.txt', f"_{scene['hash']}_{scene['last_task']}{lang_str}.mkv")
                    p = p.replace('concatenation', 'video')
                    concatenation_file.write(f"file \'{p}\' \n")
        else:
            for k in main_chapter_keys():
                try:
                    for filepath in video_files[k]['files']:
                        p = filepath.replace('concatenation', 'video')
                        concatenation_file.write(f"file \'{p}\' \n")
                except:
                    if k in credit_chapter_keys():
                        for scene in video_files[k]['scenelist']:
                            p = scene['path'].replace('.txt', f"_{scene['hash']}_{scene['last_task']}{lang_str}.mkv")
                            p = p.replace('concatenation', 'video')
                            concatenation_file.write(f"file \'{p}\' \n")
        concatenation_file.close()
        return concatenation_filepath



def create_slience_concat_files(db, k_ep) -> dict:
    # Create a concatenation file for silence
    files: dict[str, list] = {}
    for k_ch in main_chapter_keys():
        files[k_ch] = []
        if k_ch not in db[k_ep]['audio'].keys():
            continue

        db_audio = db[k_ep]['audio'][k_ch]

        if 'silence' in db_audio.keys() and db_audio['silence'] > 0:
            print(lightgrey(f"\t- {k_ch}"))

            # Convert silence duration in nb of frames
            silence_count = ms_to_frame(db_audio['silence'])
            # print("silence = %d frames" % (silence_count))

            # Duration
            black_image_filepath = os.path.join(db['common']['directories']['cache'], 'black.png')
            duration_str = f"duration {1/get_fps(db):.02f}\n"

            # Create the concatenation file for the silence
            makedirs(k_ep, k_ch, 'concatenation')
            concatenation_filepath = os.path.join(
                db[k_ep]['cache_path'],
                "concatenation",
                f"{k_ep}_{k_ch}__999_silence.txt"
            )
            concatenation_file = open(concatenation_filepath, "w")

            # Add frames to the files
            for _ in range(silence_count):
                concatenation_file.write(f"file \'{black_image_filepath}\' \n")
                concatenation_file.write(duration_str)

            files[k_ch].append(concatenation_filepath)
            concatenation_file.close()

    return files

