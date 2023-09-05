# -*- coding: utf-8 -*-
import os
from pprint import pprint

from img_toolbox.python_deshaker import DEBUG_DESHAKE
from img_toolbox.ffmpeg_utils import execute_simple_ffmpeg_command

from utils.common import FPS
from utils.pretty_print import *


def combine_images_into_video(db_common, k_part, video_shot,
    force=False, simulation:bool=False, watermark:str=None):

    verbose = False

    input_filename = video_shot['path']
    shot_filepath = input_filename.replace("concatenation", "video")
    suffix = ''
    if video_shot['hash'] != '':
        suffix += "_%s" % (video_shot['hash'])
    if video_shot['last_task'] != '':
        suffix += "_%s" % (video_shot['last_task'])
    shot_filepath = shot_filepath.replace('.txt', f'{suffix}.mkv')

    print(lightgrey(f"\tcombine images into video:"), p_lightcyan(f"{k_part}:"), f"{shot_filepath}")

    if not os.path.exists(shot_filepath) or force or DEBUG_DESHAKE:
        db_settings = db_common['settings']

        ffmpeg_command = [db_common['tools']['ffmpeg']]
        ffmpeg_command.extend(db_settings['verbose'].split(' '))
        ffmpeg_command.extend([
            "-r", str(FPS),
            "-f", "concat",
            "-safe", "0",
            "-i", input_filename,
            "-pix_fmt", db_settings['video_pixel_format'],
            "-colorspace:v", "bt709",
            "-color_primaries:v", "bt709",
            "-color_trc:v", "bt709",
            "-color_range:v", "tv"
        ])

        if watermark is not None:
            watermark_argument = f"drawtext=text=\'{watermark}\':fontcolor=green:fontsize=24:x=10:y=h-th-10"

            ffmpeg_command.extend([
                "-vf", watermark_argument
            ])

        ffmpeg_command.extend(db_settings['video_quality'].split(' '))

        if 'documentaire' in k_part:
            ffmpeg_command.extend(db_settings['video_film_tune'].split(' '))
        else:
            ffmpeg_command.extend(db_settings['video_tune'].split(' '))
        ffmpeg_command.extend(["-y", shot_filepath])

        if verbose:
            print_green(ffmpeg_command)
        if simulation:
            return

        success = execute_simple_ffmpeg_command(ffmpeg_command=ffmpeg_command)
        if not success:
            print_red("error: failed to generate %s" % (shot_filepath))
            try:
                os.remove(shot_filepath)
            except:
                pass

    return shot_filepath


