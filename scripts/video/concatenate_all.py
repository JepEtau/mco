# -*- coding: utf-8 -*-
import os
from pprint import pprint

from img_toolbox.ffmpeg_utils import execute_ffmpeg_command
from video.utils import create_folder_for_concatenation
from utils.pretty_print import *



def concatenate_all(db, k_ep:str, force=False, simulation:bool=False) -> None:
    print(p_lightgreen(f"Concatenate all A/V files:"), p_lightcyan(f"{k_ep}"))

    language = db[k_ep]['audio']['lang']
    lang_str = '' if language == 'fr' else f"_{language}"

    cache_directory = db[k_ep]['cache_path']
    output_filename = f"{k_ep}_no_chapters{lang_str}.mkv"
    output_filepath = os.path.join(cache_directory, output_filename)
    print(f"\tA/V file (without chapters): {output_filepath}")

    # if os.path.exists(output_filepath) and not force:
    #     return

    # Create concatenation file
    create_folder_for_concatenation(db, k_ep=k_ep, k_part='')
    concatenation_filepath = os.path.join(cache_directory, "concatenation", f"{k_ep}.txt")
    concatenation_filepath = os.path.normpath(os.path.join(os.getcwd(), concatenation_filepath))
    concatenation_file = open(concatenation_filepath, "w")

    p = os.path.join(db['g_debut']['cache_path'], f"g_debut{lang_str}.mkv")
    concatenation_file.write(f"file \'{p}\' \n")

    p = os.path.join(cache_directory, f"{k_ep}_av{lang_str}.mkv")
    concatenation_file.write(f"file \'{p}\' \n")

    p = os.path.join(db['g_fin']['cache_path'], f"g_fin{lang_str}.mkv")
    concatenation_file.write(f"file \'{p}\' \n")

    concatenation_file.close()

    # Concatenate files
    ffmpeg_command = [db['common']['tools']['ffmpeg']]
    ffmpeg_command.extend(db['common']['settings']['verbose'].split(' '))
    ffmpeg_command.extend([
        "-f", "concat",
        "-safe", "0",
        "-i", concatenation_filepath,
        "-c", "copy",
        "-y", output_filepath
    ])

    std = execute_ffmpeg_command(db,
        command=ffmpeg_command,
        filename=output_filename,
        simulation=simulation)
    if len(std) > 0:
        print(std)

