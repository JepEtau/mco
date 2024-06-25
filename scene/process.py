from concurrent.futures import ThreadPoolExecutor
import multiprocessing
import os
from pprint import pprint
import sys

import numpy as np
from parsers import (
    db,
    get_fps,
    task_to_dirname
)
from processing.effects import effect_fadeout, effect_loop_and_fadeout
from processing.watermark import add_watermark
from scene.filters import do_watermark
from utils.images import IMG_FILENAME_TEMPLATE, Image, Images
from utils.images_io import load_image
from utils.logger import main_logger
from utils.mco_types import Effect, Scene
from utils.mco_utils import get_cache_path, get_dirname, run_simple_command
from utils.p_print import *
from utils.time_conversions import frame_to_s, frame_to_sexagesimal
from utils.tools import ffmpeg_exe
from video.out_frames import get_out_frame_paths



def process_scene(scene: Scene, force: bool = False) -> bool:
    task_name: str = scene['task'].name
    if task_name in ('initial', 'lr'):
        # Assume:
        #   input: 8bpp

        in_video_fp: str = scene['inputs']['progressive']['filepath']
        if task_name == 'lr' and not os.path.exists(in_video_fp):
            raise FileExistsError(red(f"Missing input file: {in_video_fp}"))

        do_process: bool = True
        if not force:
            do_process = False
            for fp in scene['in_frames'].out_images():
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

            if start < 0:
                raise ValueError(f"Error, start < 0 for scene {scene['no']}")

            # Create filename template
            directory: str = os.path.join(get_cache_path(scene), task_to_dirname['initial'])
            dirname: str = get_dirname(scene=scene, out=True)[0]
            h: str = scene['task'].hashcode
            filename_template = IMG_FILENAME_TEMPLATE % (
                scene['k_ep'], scene['k_ed'], int(dirname[:2]), f"_{h}" if h != '' else ""
            )
            filepath_template: str = os.path.join(directory, filename_template)
            os.makedirs(directory, exist_ok=True)

            # Create FFmpeg command
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

        if do_watermark(scene):
            max_workers: int = multiprocessing.cpu_count()
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                for _ in executor.map(
                    lambda args: add_watermark(*args),
                    [(img, scene) for img in scene['in_frames'].images()]
                ):
                    pass




        if success and 'effects' in scene and not 'segments' in scene['src']:
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

