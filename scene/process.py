import os
from pprint import pprint
import sys
from parsers import (
    db,
    IMG_FILENAME_TEMPLATE,
    get_fps
)
from utils.logger import main_logger
from utils.mco_types import Scene
from utils.mco_utils import get_out_directory, run_simple_command
from utils.p_print import *
from utils.time_conversions import frame_to_s, frame_to_sexagesimal
from utils.tools import ffmpeg_exe
from video.frame_list import get_frame_list, get_out_dirname


def process_scene(scene: Scene, force: bool = False) -> bool:

    # Create a black frame used for silences/effects
    # create_black_frame(scene)


    # Effects
    # if 'effects' in scene:
    #     effect = scene['effects'][0]

    #     if effect == 'loop_and_fadeout':
    #         effect_loop_and_fadeout(db, scene)

    #     elif effect == 'fadeout':
    #         effect_fadeout(db, scene)

    #     elif effect == 'loop_and_fadein':
    #         effect_loop_and_fadein(db, scene)

    #     else:
    #         print_green("\tuse concatenation files")

    # Extract frames from video
    task_name: str = scene['task'].name
    if task_name in ('initial', 'lr'):
        # Assume:
        #   input: 8bpp

        in_video_fp: str = scene['inputs']['progressive']['filepath']
        out_frames = get_frame_list(scene=scene, replace=False, out=True)

        # Create filename template
        directory: str = get_out_directory(scene)
        dirname: str = get_out_dirname(scene=scene, out=True)
        h: str = scene['task'].hashcode
        filename_template = IMG_FILENAME_TEMPLATE % (
            scene['k_ep'],
            scene['k_ed'],
            int(dirname[:2]),
            f"_{h}" if h != '' else ""
        )
        os.makedirs(directory, exist_ok=True)
        filepath_template: str = os.path.join(directory, filename_template)

        do_process: bool = True
        if not force:
            do_process = False
            for fp in out_frames:
                if not os.path.exists(fp):
                    do_process = True
                    break
            if not do_process:
                return True

        if scene['task'].name == 'initial':
            src_video = (
                db
                [scene['src']['k_ep']]
                ['video']
                [scene['src']['k_ed']]
                [scene['src']['k_ch']]
            )
            scene['src']['start'] = src_video['start']
            scene['src']['count'] = src_video['count']

        start: int = (
            scene['src']['start'] - scene['inputs']['progressive']['start']
        )
        count: int = scene['src']['count']

        if start < 0:
            raise ValueError(f"Error, start < 0 for scene {scene['no']}")
        ffmpeg_command: list[str] = [
            ffmpeg_exe,
            "-hide_banner",
            "-loglevel", "warning",
            "-ss", str(frame_to_sexagesimal(no=start, frame_rate=get_fps(db))),
            "-i", in_video_fp,
            "-t", str(frame_to_s(no=count, frame_rate=get_fps(db))),
            '-pixel_format', 'bgr24',
            "-start_number", str(scene['src']['start']),
            filepath_template
        ]

        main_logger.debug(' '.join(ffmpeg_command))
        success: bool = run_simple_command(ffmpeg_command)
        return success


    else:
        raise NotImplementedError(red(f"task={task_name}"))

    return False
