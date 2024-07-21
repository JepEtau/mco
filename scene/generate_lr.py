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
from utils.path_utils import path_split
from utils.time_conversions import frame_to_s, frame_to_sexagesimal
from utils.tools import ffmpeg_exe
from video.out_frames import get_out_frame_paths



def generate_lr_scene(scene: Scene, force: bool = False) -> bool:
    task_name: str = scene['task'].name
    if task_name in ('initial', 'lr'):
        # Assume:
        #   input: 8bpp

        in_video_fp: str = scene['inputs']['progressive']['filepath']
        if task_name == 'lr' and not os.path.exists(in_video_fp):
            raise FileExistsError(red(f"Missing input file: {in_video_fp}"))

        do_generate: bool = True
        if not force:
            do_generate = False
            for fp in scene['in_frames'].out_images():
                if not os.path.exists(fp):
                    do_generate = True
                    break

        if do_generate:
            if scene['task'].name == 'initial':
                src_video = (
                    db
                    [scene['src']['k_ep']]
                    ['video']
                    [scene['src']['k_ed']]
                    [scene['src']['k_ch']]
                )
                scene['src'].update({
                    'start': src_video['scenes'][scene['src']['no']]['start'],
                    'count': src_video['scenes'][scene['src']['no']]['count'],
                })

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
                pprint(_scene)
                start: int = scene['src']['segments'][0]['start']
                count: int = scene['src']['segments'][0]['count']
                scene_start: int = start

            if start < 0:
                raise ValueError(f"Error, start < 0 for scene {scene['no']}")

            # Create filename template
            xtract_directory: str = os.path.join(get_cache_path(scene), task_to_dirname['initial'])
            xtract_dirname: str = get_dirname(scene=scene, out=True)[0]
            xtract_hash: str = scene['task'].hashcode
            xtract_filename_template = IMG_FILENAME_TEMPLATE % (
                scene['k_ep'],
                scene['k_ed'],
                int(xtract_dirname[:2]),
                f"_{xtract_hash}" if xtract_hash != '' else ""
            )
            xtract_filepath_template: str = os.path.join(xtract_directory, xtract_filename_template)
            os.makedirs(xtract_directory, exist_ok=True)

            # Create FFmpeg command
            do_extract: bool = True
            if not force:
                do_extract = False
                for fp in scene['in_frames'].in_images():
                    # print(fp)
                    if not os.path.exists(fp):
                        do_extract = True
                        break

            if do_extract:
                print("do extract scene")
                ffmpeg_command: list[str] = [
                    ffmpeg_exe,
                    "-hide_banner",
                    "-loglevel", "warning",
                    "-ss", str(frame_to_sexagesimal(no=start, frame_rate=get_fps(db))),
                    "-i", in_video_fp,
                    "-t", str(frame_to_s(no=count, frame_rate=get_fps(db))),
                    '-pixel_format', 'bgr24',
                    "-start_number", str(scene_start),
                    xtract_filepath_template
                ]
                print(' '.join(ffmpeg_command))
                success: bool = run_simple_command(ffmpeg_command)
            else:
                success = True
        else:
            success: bool = True

        # for image in scene['in_frames'].images():
        #     print(f"{image.in_fp}\n  -> {image.out_fp}")
        # pprint(scene['in_frames'].in_images())
        # pprint(scene['in_frames'].out_images())
        # sys.exit()

        if do_watermark(scene):
            do_generate: bool = False
            for fp in scene['in_frames'].out_images():
                if not os.path.exists(fp):
                    print(yellow(f"LR: do generate, missing {fp}"))
                    do_generate = True
                    break
            if do_generate:
                lr_directory: str = path_split(
                    scene['in_frames'].out_images()[0]
                )[0]
                # lr_directory: str = os.path.join(
                #     get_cache_path(scene),
                #     task_to_dirname[scene['task'].name]
                # )
                os.makedirs(lr_directory, exist_ok=True)
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

