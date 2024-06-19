import os
from parsers import (
    IMG_FILENAME_TEMPLATE,
    task_to_dirname,
    TASK_NAMES
)
from utils.mco_types import (
    Scene
)
from utils.p_print import *


def get_out_dirname(scene: Scene, out: bool =False) -> str:
    if scene['task'].name in ('lr'):
        dirname: str = task_to_dirname['initial']

    else:
        index: str = 0
        task_name: str = scene['task'].name
        try:
            index = TASK_NAMES.index(task_name)
        except:
            index = 0
        if index < 1:
            return task_to_dirname[TASK_NAMES[0]]
        if out:
            dirname: str = task_to_dirname[TASK_NAMES[index]]
        else:
            dirname: str = task_to_dirname[TASK_NAMES[index - 1]]
    return dirname



def get_frame_list(scene: Scene, replace: bool = False, out: bool = True) -> list[str]:
    dirname: str = get_out_dirname(
        scene,
        False if scene['task'].name in ('lr') else out
    )
    directory: str = os.path.join(scene['cache'], dirname)
    print(red(f"get_frame_list: {dirname}"))

    h: str = scene['task'].hashcode
    filename_template = IMG_FILENAME_TEMPLATE % (
        scene['k_ep'],
        scene['k_ed'],
        int(dirname[:2]),
        f"_{h}" if h != '' else ""
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
