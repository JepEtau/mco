# -*- coding: utf-8 -*-
import sys
import os
from pprint import pprint

from img_toolbox.ffmpeg_utils import execute_ffmpeg_command

from utils.pretty_print import *
from utils.time_conversions import (
    ms_to_frames,
    frame2sexagesimal,
)


CHAPTER_NAMES = {
    'en': [
        "Opening credits",
        "Previously",
        "Episode",
        "To follow",
        "Documentary",
        "End credits",
    ],
    'fr': [
        "Générique de début",
        "Précédemment",
        "Episode",
        "A suivre",
        "Documentaire",
        "Générique de fin",
    ],
}



def add_chapters(db, k_ep:str, last_task:str, simulation:bool=False) -> None:
    # Add chapters to the video file
    language = db[k_ep]['audio']['lang']
    lang_str = '' if language == 'fr' or last_task=='final' else f"_{language}"

    suffix = '' if last_task == '' or last_task == 'final' else f"_{last_task}"

    cache_directory = db[k_ep]['cache_path']
    input_filename = f"{k_ep}_no_chapters{suffix}{lang_str}.mkv"
    input_filepath = os.path.join(cache_directory, input_filename)

    output_directory = db['common']['directories']['outputs']
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    final_filename = f"{k_ep}{suffix}{lang_str}.mkv"
    final_filepath = os.path.join(output_directory, final_filename)

    print(p_lightgreen(f"Add chapters:"), lightcyan(f"{k_ep}"))
    print(f"\tFinal file: {final_filepath}")

    # Create file for chapters
    chapters_filepath = os.path.join(cache_directory, "concatenation", f"{k_ep}_chapters{lang_str}.txt")
    chapters_filepath = os.path.normpath(os.path.join(os.getcwd(), chapters_filepath))
    chapters_file = open(chapters_filepath, "w")

    index = 0
    count = 0

    chapters_file.write(f"CHAPTER0{index}=00:00:00.000\n")
    chapters_file.write(f"CHAPTER0{index}NAME={CHAPTER_NAMES[language][0]}\n")
    count += db['g_debut']['audio']['count']

    k_part = 'precedemment'
    if db[k_ep]['audio'][k_part]['count'] > 0:
        index += 1
        chapters_file.write(f"CHAPTER0{index}={frame2sexagesimal(count)}0\n")
        chapters_file.write(f"CHAPTER0{index}NAME={CHAPTER_NAMES[language][1]}\n")

        video_count = db[k_ep]['video']['target'][k_part]['avsync']
        video_count += db[k_ep]['video']['target'][k_part]['count']
        # video_count += ms_to_frames(db['g_debut']['audio'][k_part]['silence'])
        count += video_count

    k_part = 'episode'
    # print(f"{k_part}: {count}")
    index += 1
    chapters_file.write(f"CHAPTER0{index}={frame2sexagesimal(count)}0\n")
    chapters_file.write(f"CHAPTER0{index}NAME={CHAPTER_NAMES[language][2]}\n")
    video_count = db[k_ep]['video']['target'][k_part]['avsync']
    video_count += db[k_ep]['video']['target'][k_part]['count']
    video_count += ms_to_frames(db[k_ep]['audio'][k_part]['silence'])
    count += video_count


    k_part = 'asuivre'
    # print(f"{k_part}: {count}")
    if db[k_ep]['audio'][k_part]['count'] > 0:
        index += 1
        chapters_file.write(f"CHAPTER0{index}={frame2sexagesimal(count)}0\n")
        chapters_file.write(f"CHAPTER0{index}NAME={CHAPTER_NAMES[language][3]}\n")

        audio_duration = db[k_ep]['audio']['g_'+k_part]['avsync']
        audio_duration += db[k_ep]['audio']['g_'+k_part]['duration']
        audio_duration += db[k_ep]['audio'][k_part]['duration']
        audio_duration += db[k_ep]['audio'][k_part]['silence']
        count += ms_to_frames(audio_duration)

    k_part = 'documentaire'
    # print(f"{k_part}: {count}")
    index += 1
    chapters_file.write(f"CHAPTER0{index}={frame2sexagesimal(count)}0\n")
    chapters_file.write(f"CHAPTER0{index}NAME={CHAPTER_NAMES[language][4]}\n")

    audio_duration = db[k_ep]['audio']['g_'+k_part]['avsync']
    audio_duration += db[k_ep]['audio']['g_'+k_part]['duration']
    audio_duration += db[k_ep]['audio'][k_part]['duration']
    audio_duration += db[k_ep]['audio'][k_part]['silence']
    count += ms_to_frames(audio_duration)

    index += 1
    k_part = 'g_fin'
    # print(f"{k_part}: {count}")
    chapters_file.write(f"CHAPTER0{index}={frame2sexagesimal(count)}0\n")
    chapters_file.write(f"CHAPTER0{index}NAME={CHAPTER_NAMES[language][5]}\n")

    chapters_file.close()


    mkvmerge_command = [db['common']['tools']['mkvmerge']]
    mkvmerge_command.extend([
                    '--quiet',
                    '--chapters', chapters_filepath,
                    '--output', final_filepath,
                    input_filepath])

    std = execute_ffmpeg_command(db,
        command=mkvmerge_command,
        filename=final_filepath,
        simulation=simulation)
    if len(std) > 0:
        print(std)

