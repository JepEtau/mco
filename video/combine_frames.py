import os
from pprint import pprint

# from img_toolbox.python_deshaker import DEBUG_DESHAKE
# from img_toolbox.ffmpeg_utils import run_simple_command

from utils.logger import main_logger
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
from av_merge.combine_av import get_video_duration


# def verify_integrity(
#     scene: Scene
# ) -> None:
#     task: ProcessingTask = scene['task']

#     if task.concat_file == '':



def combine_frames(
    chapter,
    scene: Scene,
    force: bool = False,
    simulation: bool = False,
) -> None:
    verbose = False
    pprint(scene)
    task: ProcessingTask = scene['task']
    video_fp: str = task.video_file

    main_logger.debug(
        lightgrey(f"\tcombine images into video:")
        + lightcyan(f"{chapter}:")
        + f"{video_fp}"
    )

    if os.path.exists(video_fp) and not 'silence' in video_fp:
        video_frames_count: int = 0
        try:
            _, video_frames_count = get_video_duration(video_fp, integrity=False)
        except:
            pass
        # Force regeneration if the scene has effects
        main_logger.debug(f"\t\tvideo: {video_frames_count}, should be {scene['dst']['count']}")
        if 'effects' in scene and chapter not in ('g_debut', 'g_fin'):
            force  = True
        elif video_frames_count != scene['dst']['count']:
            force = True

    if not os.path.exists(video_fp) or force:
        db_settings: dict[str, str] = db['common']['settings']

        ffmpeg_command: list[str] = [
            ffmpeg_exe,
            *db['common']['settings']['verbose'],
            "-r", str(get_fps(db)),
            "-f", "concat",
            "-safe", "0",
            "-i", task.concat_file,
            "-pix_fmt", db_settings['video_pixel_format'],
            "-colorspace:v", "bt709",
            "-color_primaries:v", "bt709",
            "-color_trc:v", "bt709",
            "-color_range:v", "tv"
        ]

        # Force all scenes to the same dimension
        if task.name == 'lr':
            ffmpeg_command.extend(["-vf", "scale=768:576"])

        ffmpeg_command.extend(db_settings['video_quality'].split(' '))

        if 'documentaire' in chapter:
            ffmpeg_command.extend(db_settings['video_film_tune'].split(' '))
        else:
            ffmpeg_command.extend(db_settings['video_tune'].split(' '))

        ffmpeg_command.extend(["-y", video_fp])

        if verbose:
            print(green(ffmpeg_command))
        if simulation:
            return

        os.makedirs(path_split(video_fp)[0], exist_ok=True)

        success: bool = False
        main_logger.debug(' '.join(map(str, ffmpeg_command)))
        try:
            success = run_simple_command(command=ffmpeg_command)
        except Exception as e:
            raise RuntimeError(red("Failed running FFmpeg command"))

        if not success:
            try:
                os.remove(video_fp)
            except:
                pass
            raise(red(f"Error: failed to generate {video_fp}"))




