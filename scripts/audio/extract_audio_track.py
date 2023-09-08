# -*- coding: utf-8 -*-
import sys

import numpy as np
import os

from pprint import pprint
from utils.pretty_print import *
from utils.common import (
    K_AUDIO_PARTS,
    K_GENERIQUES,
)
from img_toolbox.ffmpeg_utils import execute_simple_ffmpeg_command
from utils.time_conversions import (
    current_datetime_str,
)


def extract_audio_track(db, k_ep:str, k_ed, force=False) -> str:
    # Returns the extracted filepath
    verbose = False

    # print("%s.extract_audio_track: %s:%s" % (__name__, k_ed, k_ep_or_g))

    if k_ed == '':
        k_ed = db[k_ep]['audio']['src']['k_ed']

    if k_ep in ['g_debut', 'g_fin']:
        k_ep_src = db[k_ep]['audio']['src']['k_ep']
    else:
        k_ep_src = k_ep

    print(f"{current_datetime_str()} extract_audio_track from {k_ed}:{k_ep_src}")

    # Input audio file
    try:
        input_filepath = db['editions'][k_ed]['inputs']['audio'][k_ep_src]
    except:
        sys.exit(red(f"Missing input file: edition {k_ed}, epiosde {k_ep_src[2:]}"))
    if force or verbose:
        print(f"%s extract audio stream: %s:%s from %s" % (current_datetime_str(), k_ed, k_ep_src, input_filepath))

    if not os.path.exists(input_filepath):
        sys.exit(f"Error: audio: input file is missing, edition: {k_ed}")


    # Output audio file
    output_directory = os.path.join(db[k_ep_src]['cache_path'], "audio")
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)


    output_filename = f"{k_ep_src}_{k_ed}_audio_extract.{db['common']['settings']['audio_format']}"
    output_filepath = os.path.join(output_directory, output_filename)

    if os.path.exists(output_filepath):
        # Already exists
        print("\talready extracted")
        return output_filepath

    filename, extension = os.path.splitext(input_filepath)
    if extension == '.wav' and os.path.exists(input_filepath):
        # Already extracted
        print("\tuse file: %s" % (input_filepath))
        return input_filepath
    else:
        print(f"\t{input_filepath} -> {output_filepath}")

        # FFmpeg command
        ffmpeg_command = [db['common']['tools']['ffmpeg']]
        ffmpeg_command.extend(db['common']['settings']['verbose'].split(' '))
        ffmpeg_command.extend([
            "-i", input_filepath,
            "-sn",
            "-vn"
        ])

        # AWFULL but necessary to keep 24bit audio for the edition 'b'
        # TODO: do a ffprobe before
        if "b_ep" in input_filepath:
            ffmpeg_command.extend(["-c:a", "copy"])

        ffmpeg_command.extend(["-y", output_filepath])

        execute_simple_ffmpeg_command(ffmpeg_command)

        return output_filepath

