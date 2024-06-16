import os
import subprocess
import time
from typing import Literal
from utils.mco_types import Scene
from utils.p_print import *
from parsers import (
    Chapter, key, db, task_to_dirname, TaskName
)
from .logger import main_logger



def makedirs(
    episode,
    chapter: Chapter = '',
    type: Literal['video', 'concat'] = 'video'
):
    """ Create a directory that contains all video clips or the concatenation files
    """
    episode = key(episode)
    if episode in ['ep00', 'ep40']:
        return

    k = chapter if chapter in ('g_debut', 'g_fin') else episode

    if type == 'video':
        directory = os.path.join(db[k]['cache_path'], 'video')

    elif type == 'concat':
        directory = os.path.join(db[k]['cache_path'], "concat")

    else:
        raise ValueError(f"Wrong type: {type}")

    os.makedirs(directory, exist_ok=True)
    return directory



def nested_dict_set(d: dict, o: object, *keys) -> None:
    nested_d = d
    for k in keys:
        if k == keys[-1]:
            break
        if k not in nested_d.keys():
            nested_d[k] = dict()
        nested_d = nested_d[k]
    nested_d[k] = o



def get_cache_path(scene: Scene) -> str:
    task_name: TaskName = scene['task'].name
    cache_dir: str = db['common']['directories']['cache']

    # Put all images in a single folder for start/end credits
    if scene['k_ch'] in ('g_debut', 'g_fin'):
        return os.path.join(
            db['common']['directories']['cache'],
            scene['k_ch'],
            f"{scene['no']:03}"
        )

    # If last task is geometry, use the dst structure
    if task_name == 'final':
        output_path: str = os.path.join(
            db['common']['directories']['cache'],
            scene['dst']['k_ep'],
            scene['dst']['k_ch'],
            f"{scene['no']:03}"
        )

    elif task_name == 'initial':
        # Work in the src directory
        output_path = os.path.join(
            cache_dir,
            scene['k_ep'],
            scene['k_ch'],
            f"{scene['no']:03}"
        )

    else:
        # Otherwise, use the src directory
        #  because these frames are used by multiple episodes
        output_path: str = os.path.join(
            db['common']['directories']['cache'],
            scene['k_ep'],
            scene['k_ch'],
            f"{scene['src']['no']:03}"
        )

    return output_path



def get_out_directory(scene: Scene):
    task_name: TaskName = scene['task'].name
    dirname: str = task_to_dirname[task_name]
    cache_dir: str = db['common']['directories']['cache']

    # Put all images in a single folder for 'génériques'
    if scene['k_ch'] in ('g_debut', 'g_fin'):
        return os.path.join(
            cache_dir,
            scene['k_ch'],
            f"{scene['no']:03}",
            dirname,
        )

    if task_name == 'final':
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
