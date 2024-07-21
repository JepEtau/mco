import os
import subprocess
import time
from typing import Literal, TYPE_CHECKING
# if TYPE_CHECKING:
from scene.filters import do_watermark
from utils.mco_types import Scene
from parsers import Chapter
from utils.p_print import *
from parsers import (
    key, db, task_to_dirname, TaskName, TASK_NAMES
)
from .logger import main_logger


def makedirs(
    episode,
    chapter: Chapter = '',
    type: Literal['video', 'concat'] = 'video'
):
    """ Create a directory that contains all video clips or the concatenation files
    """
    k_ep = key(episode)
    if k_ep in ['ep00', 'ep40']:
        return

    k = chapter if chapter in ('g_debut', 'g_fin') else k_ep

    if type == 'video':
        directory = os.path.join(db[k]['cache_path'], 'video')

    elif type == 'concat':
        directory = os.path.join(db[k]['cache_path'], "concat")

    else:
        raise ValueError(f"Wrong type: {type}")

    os.makedirs(directory, exist_ok=True)
    return directory
