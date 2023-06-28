# -*- coding: utf-8 -*-
import sys
import os
from pprint import pprint

from audio.utils import read_audio_file
from img_toolbox.ffmpeg_utils import (
    execute_ffmpeg_command,
    get_video_duration,
)
from utils.common import FPS
from utils.pretty_print import *



def combine_av_tracks(db, k_ep_or_g, last_task, force:bool=False, simulation:bool=False):
    # Output filepath
    print(p_lightgreen(f"Merge audio and video tracks:"), p_lightcyan(f"{k_ep_or_g}"))
    cache_path = db[k_ep_or_g]['cache_path']

    language = db[k_ep_or_g]['audio']['lang']
    lang_str = '' if language == 'fr' else f"_{language}"

    suffix = '' if last_task == '' or last_task == 'final' else f"_{last_task}"

    if k_ep_or_g in ['g_debut', 'g_fin']:
        audio_video_filepath = os.path.join(cache_path, f"{k_ep_or_g}{suffix}{lang_str}.mkv")
    else:
        audio_video_filepath = os.path.join(cache_path, f"{k_ep_or_g}_av{suffix}{lang_str}.mkv")

    if os.path.exists(audio_video_filepath) and not force and not simulation:
        return

    # Get nb of frames from video stream
    if k_ep_or_g in ['g_debut', 'g_fin']:
        video_filepath = os.path.join(cache_path, "video",
            f"{k_ep_or_g}_video_{db[k_ep_or_g]['video']['hash']}{suffix}{lang_str}.mkv")

    else:
        video_filepath = os.path.join(cache_path, "video", f"{k_ep_or_g}_video{lang_str}.mkv")

    try:
        video_frames_count = get_video_duration(db['common'], video_filepath, integrity=False)[1]
    except:
        video_frames_count = 0

    # Get equivalent nb of frames from audio stream
    audio_filepath = os.path.join(cache_path, "audio", f"{k_ep_or_g}_audio{lang_str}.{db['common']['settings']['audio_format']}")
    try:
        channels_count, sample_rate, in_track, duration = read_audio_file(audio_filepath)
    except:
        duration = 0
    audio_frames_count = int(duration*FPS)

    print(f"\tvideo: {video_filepath}: {video_frames_count}")
    print(f"\taudio: {audio_filepath}: {audio_frames_count}")
    print(f"\tAV file: {audio_video_filepath}")

    # Cannot continue if nb of frames differ
    if audio_frames_count != video_frames_count and not simulation:
        sys.exit(print_red(f"Error: cannot merge audio and video tracks: nb of frames differs"))

    # Merge Audio and Video tracks
    ffmpeg_command = [db['common']['tools']['ffmpeg']]
    ffmpeg_command.extend(db['common']['settings']['verbose'].split(' '))
    ffmpeg_command.extend([
        "-i", video_filepath,
        "-i", audio_filepath,
        "-c:v", "copy",
        "-c:a", "copy",
        "-shortest",
        "-y", audio_video_filepath
    ])

    std = execute_ffmpeg_command(db,
        command=ffmpeg_command,
        filename=audio_video_filepath,
        simulation=simulation)
    if len(std) > 0:
        print(std)





