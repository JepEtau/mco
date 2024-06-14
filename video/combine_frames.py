import os
from pprint import pprint

# from img_toolbox.python_deshaker import DEBUG_DESHAKE
# from img_toolbox.ffmpeg_utils import run_simple_command

from utils.mco_types import Scene
from utils.mco_utils import run_simple_command
from utils.p_print import *
from parsers import (
    db,
    get_fps,
    ProcessingTask,
)
from utils.path_utils import absolute_path, path_split
from utils.tools import ffmpeg_exe


def combine_frames(
    chapter,
    scene: Scene,
    force: bool = False,
    simulation: bool = False,
    watermark: str| None = None,
) -> None:
    verbose = False
    db_common: dict = db['common']
    task: ProcessingTask = scene['task']

    suffix: str = ''
    if task.hashcode != '':
        suffix += f"_{task.hashcode}"

    if task != '':
        suffix += f"_{task.name}"

    dir, basename, _ = path_split(task.concat_file)
    task.video_file= absolute_path(
        os.path.join(dir, os.pardir, "video", f"{basename}{suffix}.mkv")
    )
    video_filepath: str = task.video_file

    print(
        lightgrey(f"\tcombine images into video:"),
        lightcyan(f"{chapter}:"),
        f"{video_filepath}"
    )

    if not os.path.exists(video_filepath) or force:
        db_settings: dict[str, str] = db_common['settings']

        ffmpeg_command = [ffmpeg_exe]
        ffmpeg_command.extend(db_settings['verbose'].split(' '))
        ffmpeg_command.extend([
            "-r", str(get_fps(db)),
            "-f", "concat",
            "-safe", "0",
            "-i", task.concat_file,
            "-pix_fmt", db_settings['video_pixel_format'],
            "-colorspace:v", "bt709",
            "-color_primaries:v", "bt709",
            "-color_trc:v", "bt709",
            "-color_range:v", "tv"
        ])

        if watermark is not None:
            watermark_argument = f"drawtext=text=\'{watermark}\':fontcolor=green:fontsize=24:x=10:y=h-th-10"
            ffmpeg_command.extend(["-vf", watermark_argument])

        ffmpeg_command.extend(db_settings['video_quality'].split(' '))

        if 'documentaire' in chapter:
            ffmpeg_command.extend(db_settings['video_film_tune'].split(' '))
        else:
            ffmpeg_command.extend(db_settings['video_tune'].split(' '))

        ffmpeg_command.extend(["-y", video_filepath])

        if verbose:
            print(green(ffmpeg_command))
        if simulation:
            return

        success = run_simple_command(ffmpeg_command=ffmpeg_command)
        if not success:
            print(red(f"Error: failed to generate {video_filepath}"))
            try:
                os.remove(video_filepath)
            except:
                pass



