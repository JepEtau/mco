import os
from typing import Literal
from parsers import (
    IMG_FILENAME_TEMPLATE,
    task_to_dirname,
    TaskName
)
from utils.mco_types import (
    Scene
)
from utils.p_print import *


def get_frame_list(scene: Scene, replace: bool = False) -> list[str]:
    dirname: str = task_to_dirname[scene['task'].name]

    h: str = scene['task'].hashcode
    filename_template = IMG_FILENAME_TEMPLATE % (
        scene['k_ep'],
        scene['k_ed'],
        int(dirname[:2]),
        f"_{h}" if h != '' else ""
    )
    directory: str = os.path.join(scene['cache'], dirname)

    frame_replace = scene['replace']
    if replace:
        return list([
            os.path.join(
                directory,
                filename_template % (frame_replace[no] if no in frame_replace else no)
            )
            for no in range(scene['start'], scene['start'] + scene['count'])
            if no not in frame_replace
        ])

    else:
        return list([
            os.path.join(directory, filename_template % (no))
            for no in range(scene['start'], scene['start'] + scene['count'])
            if no not in frame_replace
        ])
