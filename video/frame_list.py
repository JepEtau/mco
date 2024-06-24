import os
from parsers import (
    IMG_FILENAME_TEMPLATE,
    task_to_dirname,
    TASK_NAMES,
    TaskName
)
from utils.mco_types import (
    Scene
)
from utils.mco_utils import do_watermark
from utils.p_print import *


def get_dirname(scene: Scene, out: bool = False) -> tuple[str, str]:
    task_name: TaskName = scene['task'].name
    print(red(f"get_dirname: out:{out}, {task_name}"))
    if not out:
        if (
            task_name == 'lr' and not do_watermark(scene)
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



def get_frame_list(scene: Scene, replace: bool = False, out: bool = True) -> list[str]:
    dirname, hashcode = get_dirname(scene, out)
    directory: str = os.path.join(scene['cache'], dirname)
    print(red(f"get_frame_list: out:{out} -> {dirname}"))

    filename_template = IMG_FILENAME_TEMPLATE % (
        scene['k_ep'],
        scene['k_ed'],
        int(dirname[:2]),
        f"_{hashcode}" if hashcode != '' else ""
    )

    frame_replace = scene['replace']
    if replace:
        imgs: list[str] = []
        for no in range(scene['start'], scene['start'] + scene['count']):
            out_no: int = frame_replace[no] if no in frame_replace else no
            imgs.append(os.path.join(directory, filename_template % (out_no)))
        return imgs

    else:
        return list([
            os.path.join(directory, filename_template % (no))
            for no in range(scene['start'], scene['start'] + scene['count'])
            if no not in frame_replace
        ])
