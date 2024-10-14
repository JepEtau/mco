from copy import deepcopy
import os
from pprint import pprint
import sys
from typing import OrderedDict
from processing.deint import calc_deint_hash, get_qtgmc_args, get_template_script

from utils.mco_utils import get_cache_path
from utils.p_print import *
from utils.path_utils import absolute_path, path_split
from utils.media import vcodec_to_extension
from .filters import get_filters

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from utils.mco_types import Scene
from parsers import (
    db,
    Filter,
    TASK_NAMES,
    ProcessingTask,
    VideoSettings,
    TaskName,
)
from utils.mco_types import Scene, Inputs


def consolidate_src_scene(
    scene: Scene,
    task_name: TaskName = 'initial',
    watermark: bool = False
) -> None:
    verbose: bool = False
    if verbose:
        print(lightgreen("Consolidate scene:"))
        print(lightcyan("================================== Scene ======================================="))
        pprint(scene)
        print(lightcyan("-------------------------------------------------------------------------------"))

    scene['task'] = ProcessingTask(name=task_name)

    k_ep = scene['k_ep']
    k_ed = scene['k_ed']
    k_ch = scene['k_ch']

    scene['filters'] = deepcopy(get_filters(scene))

    # Consolidate_scene_filters: add missing filters
    scene_filters = scene['filters']
    for t in TASK_NAMES:
        if t not in scene_filters:
            scene_filters[t] = Filter(task_name=t)
    scene_filters['hr'] = scene_filters['upscale']

    # Deinterlace
    template_script: str = get_template_script(
        k_ep=k_ep,
        k_ed=k_ed
    )
    qtgmc_args: OrderedDict[str, str] = get_qtgmc_args(template_script)
    deint_hashcode, _ = calc_deint_hash(qtgmc_args)
    scene_filters['initial'].hash = deint_hashcode

    # Update the scene task
    scene['task'].hashcode = scene_filters[scene['task'].name].hash

    task_name: str = scene['task'].name
    if watermark:
        sequence: str = scene['filters'][task_name].sequence
        scene['filters'][task_name].sequence = (
            f"{sequence};watermark"
            if sequence
            else "watermark"
        )

    # Inputs
    scene['cache'] = get_cache_path(scene)
    scene['inputs'] = deepcopy(db[k_ep]['video'][k_ed][k_ch]['inputs'])
    scene['inputs']['progressive']['cache'] = db['common']['directories']['cache_progressive']

    # Set the progressive filepath
    basename: str = path_split(scene['inputs']['interlaced']['filepath'])[1]
    ext: str = vcodec_to_extension['h264']
    filename: str = f"{basename}_{deint_hashcode}{ext}"
    progressive_fp: str = os.path.join(
        db['common']['directories']['cache_progressive'],
        filename
    )
    scene['inputs']['progressive']['filepath'] = progressive_fp

    # Output video settings
    _task_name: TaskName = 'lr'
    vsettings: VideoSettings = db['common']['video_format'].get(_task_name, None)
    if vsettings is not None:
        scene['task'].video_settings = deepcopy(vsettings)
        vsettings = scene['task'].video_settings
    else:
        raise ValueError(f"VideoSettings not defined for task: {task_name}")

    # Output video filename
    if k_ch in ('g_debut', 'g_fin'):
        cache_path: str = db[k_ch]['cache_path']
    else:
        cache_path: str = db[k_ep]['cache_path']

    basename = f"{k_ed}_{k_ep}_{k_ch}_{scene['no']:03}"
    suffix: str = ""
    if task_name != "restored":
        if scene['task'].hashcode != '':
            suffix = f"_{scene['task'].hashcode}"
        suffix += f"_{task_name}"

    ext: str = vcodec_to_extension[vsettings.codec]
    scene['task'].video_file = absolute_path(
        os.path.join(
            cache_path,
            f"scenes_{scene['k_ed']}",
            f"{basename}{suffix}{ext}"
        )
    )

    if verbose:
        print(lightgreen("Consolidate scene:"))
        print(lightcyan("================================== Scene ======================================="))
        pprint(scene)
        print(lightcyan("-------------------------------------------------------------------------------"))
        sys.exit()
