import os
from pprint import pprint
import sys
from parsers import (
    db,
    IMG_FILENAME_TEMPLATE,
    get_fps,
    task_to_dirname
)
from processing.effects import effect_fadeout, effect_loop_and_fadeout
from utils.logger import main_logger
from utils.mco_types import Effect, Scene
from utils.mco_utils import get_cache_path, get_out_directory, run_simple_command
from utils.p_print import *
from utils.time_conversions import frame_to_s, frame_to_sexagesimal
from utils.tools import ffmpeg_exe
from video.frame_list import get_frame_list, get_dirname


def process_scene(scene: Scene, force: bool = False) -> bool:

    # Extract frames from video
    task_name: str = scene['task'].name
    if task_name in ('initial', 'lr'):
        # Assume:
        #   input: 8bpp

        in_video_fp: str = scene['inputs']['progressive']['filepath']
        if task_name == 'lr' and not os.path.exists(in_video_fp):
            raise FileExistsError(red(f"Missing input file: {in_video_fp}"))
        out_frames = get_frame_list(scene=scene, replace=False, out=True)

        # Create filename template
        # directory: str = get_out_directory(scene)
        directory: str = os.path.join(get_cache_path(scene), task_to_dirname['initial'])
        dirname: str = get_dirname(scene=scene, out=True)[0]
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

        if do_process:
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

            if 'segments' not in scene['src']:
                start: int = (
                    scene['src']['start'] - scene['inputs']['progressive']['start']
                )
                count: int = scene['src']['count']
                scene_start: int = scene['src']['start']
            else:
                _scene: Scene = (
                    db[scene['src']['k_ep']]
                    ['video']
                    [scene['src']['k_ed']]
                    [scene['src']['k_ch']]
                    ['scenes']
                    [scene['src']['no']]
                )
                start: int = _scene['start']
                count: int = _scene['count']
                scene_start: int = start
                # pprint(scene)
                # sys.exit()

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
                "-start_number", str(scene_start),
                filepath_template
            ]

            main_logger.debug(' '.join(ffmpeg_command))
            success: bool = run_simple_command(ffmpeg_command)
        else:
            success: bool = True

        if success and 'effects' in scene and not 'segments' in scene['src']:
            # pprint(scene)
            fp = filepath_template % scene['src']['start']

            effect: Effect = scene['effects'].primary_effect()
            main_logger.debug(lightcyan("Effects:"))

            if effect.name == 'loop_and_fadeout':
                effect_loop_and_fadeout(scene, effect)

            elif effect.name == 'fadeout':
                effect_fadeout(scene, effect)

            elif effect.name == 'loop_and_fadein':
                raise NotImplementedError("effect_loop_and_fadein")
                effect_loop_and_fadein(scene, effect)

            else:
                main_logger.debug(f"\t{effect}")

        return success


    else:
        raise NotImplementedError(red(f"task={task_name}"))

    return False
