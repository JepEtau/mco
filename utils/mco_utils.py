from __future__ import annotations
import os
import subprocess
import sys
import time
from scene.filters import do_watermark
from utils.mco_types import ChapterVideo, Scene
from utils.p_print import *
from parsers import (
    db, task_to_dirname, TaskName, TASK_NAMES
)
from .logger import main_logger



def get_target_video(scene: Scene) -> ChapterVideo:
    k_ep = scene['dst']['k_ep']
    k_ch = scene['dst']['k_ch']
    if k_ch in ('g_debut', 'g_fin'):
        return db[k_ch]['video']
    else:
        return db[k_ep]['video']['target'][k_ch]


def is_first_scene(scene: Scene) -> bool:
    return bool(scene is get_target_video(scene)['scenes'][0])


def is_last_scene(scene: Scene) -> bool:
    return bool(scene is get_target_video(scene)['scenes'][-1])


def nested_dict_set(d: dict, o: object, *keys) -> None:
    nested_d = d
    for k in keys:
        if k == keys[-1]:
            break
        if k not in nested_d.keys():
            nested_d[k] = dict()
        nested_d = nested_d[k]
    nested_d[k] = o



def get_cache_path(scene: Scene, out: bool=False) -> str:
    task_name: TaskName = scene['task'].name
    cache_dir: str = db['common']['directories']['cache']
    k_ch_dst: str = scene['dst']['k_ch'] if 'dst' in scene else scene['k_ch']

    # Put all images in a single folder for start/end credits
    if k_ch_dst in ('g_debut', 'g_fin'):
        return os.path.join(
            cache_dir,
            k_ch_dst,
            f"{scene['no']:03}"
        )

    if scene['k_ch'] in ('g_asuivre', 'g_documentaire'):
        if out:
            return os.path.join(
                cache_dir,
                scene['dst']['k_ep'],
                k_ch_dst,
                f"{scene['src']['no']:03}"
            )
        return os.path.join(
            cache_dir,
            scene['src']['k_ep'],
            k_ch_dst,
            f"{scene['src']['no']:03}"
        )


    # If last task is geometry, use the dst structure
    if task_name == 'final':
        output_path: str = os.path.join(
            cache_dir,
            scene['dst']['k_ep'],
            k_ch_dst,
            f"{scene['no']:03}"
        )

    elif task_name == 'initial':
        # Work in the src directory
        output_path = os.path.join(
            cache_dir,
            scene['k_ep'],
            k_ch_dst,
            f"{scene['no']:03}"
        )

    else:
        # Otherwise, use the src directory
        #  because these frames are used by multiple episodes
        output_path: str = os.path.join(
            cache_dir,
            scene['k_ep'],
            k_ch_dst,
            f"{scene['src']['no']:03}"
        )

    return output_path


def get_dirname(scene: Scene, out: bool = False) -> tuple[str, str]:
    task_name: TaskName = scene['task'].name
    print(red(f"get_dirname: out:{out}, {task_name}"))
    if (
        out
        and task_name == 'lr'
        and not do_watermark(scene)
    ):
        return task_to_dirname['initial'], scene['filters']['initial'].hash

    # Use initial folder as the source
    if (
        task_name == 'lr'
        and not do_watermark(scene)
        or task_name == 'hr'
    ):
        return task_to_dirname['initial'], scene['filters']['initial'].hash


    index: str = 0
    try:
        index = TASK_NAMES.index(task_name)
    except:
        index = 0

    if index < 1:
        dirname = task_to_dirname[TASK_NAMES[0]]
    elif out:
        dirname: str = task_to_dirname[TASK_NAMES[index]]
    else:
        dirname: str = task_to_dirname[TASK_NAMES[index - 1]]

    return dirname, scene['filters'][task_name].hash


def get_out_directory(scene: Scene):
    task_name: TaskName = scene['task'].name
    dirname: str = task_to_dirname[task_name]
    cache_dir: str = db['common']['directories']['cache']

    if (
        scene['task'].name in 'lr'
        and not do_watermark(scene)
    ):
        return os.path.join(
            get_cache_path(scene),
            task_to_dirname['initial']
        )

    # Put all images in a single folder for 'génériques'
    if scene['k_ch'] in ('g_debut', 'g_fin'):
        return os.path.join(
            cache_dir,
            scene['k_ch'],
            f"{scene['no']:03}",
            dirname,
        )

    if scene['k_ch'] in ('g_reportage', 'g_asuivre'):
        output_path = os.path.join(
            cache_dir,
            scene['k_ep'],
            scene['k_ch'],
            f"{scene['no']:03}",
            dirname,
        )

    if task_name == 'final' or do_watermark(scene):
        output_path = os.path.join(
            cache_dir,
            scene['dst']['k_ep'],
            scene['dst']['k_ch'],
            f"{scene['no']:03}",
            dirname,
        )

    elif task_name == 'initial':
        # Work in the src directory
        output_path = os.path.join(
            cache_dir,
            scene['k_ep'],
            scene['k_ch'],
            f"{scene['no']:03}",
            dirname
        )

    else:
        # Work in the src directory
        output_path = os.path.join(
            cache_dir,
            scene['k_ep'],
            scene['k_ch'],
            f"{scene['src']['no']:03}",
            dirname
        )
    return output_path



def run_simple_command(command: list[str] | tuple[str]) -> bool:
    start_time: float = time.time()
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    stdout: str = ''
    stderr: str = ''
    try:
        stdout = result.stdout.decode('utf-8')
    except:
        pass
    try:
        stderr = result.stderr.decode('utf-8')
    except:
        pass

    main_logger.debug(f"[V] {command[0]} executed in {time.time() - start_time:.02f}s")
    if stdout:
        print(stdout)
    if stderr:
        print(stderr)
        return False
    return True
