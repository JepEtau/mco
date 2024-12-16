from __future__ import annotations
from copy import deepcopy
import os
from pprint import pprint
import re
import sys
from warnings import warn
from utils.hash import calc_hash
from utils.mco_types import Scene
from utils.media import vcodec_to_extension
from parsers import (
    credit_chapter_keys,
    db,
    VideoSettings,
    TaskName,
    TASK_NAMES,
    ProcessingTask,
)
from utils.p_print import *
from utils.path_utils import absolute_path

# Task order:
#   initial -> lr (with pad) - > lr_st -> hr -> cg -> final

def set_doc_out_filepath_(scene: Scene) -> None:
    k_ep, k_ch = scene['dst']['k_ep'], scene['dst']['k_ch']
    primary_src_scene = scene['src'].primary_scene()
    task: ProcessingTask = scene['task']
    task_name: str = task.name
    # _task_name: str = 'lr' if task_name in ('initial', 'sim') else task_name
    scene_filters = scene['filters']
    vsettings: VideoSettings = task.video_settings

    # suffix: str = f"_{task_name}"

    # Append the model name to evaluate models: only for upscale task
    if task_name == 'upscale':
        sequence: str = scene_filters[task_name].sequence
        for t in (
            ':cuda', ':trt', ':fp16', ':fp32'
        ):
            sequence = sequence.replace(t, '')
        suffix: str = ""
        for s in sequence.split(','):
            if result := re.search(re.compile(r"^([^=]*)="), s):
                suffix += f"+{result.group(1)}" if suffix else f"{result.group(1)}"
            else:
                suffix += f"+{s}" if suffix else s
        suffix = f"__{suffix}"

    doc_previous_task: dict[str, str] = {
        'hr': 'initial',
        'cg': 'hr',
        'final': 'cg',
    }
    prev_task_name: TaskName = doc_previous_task[task_name]

    # In/out files
    basename: str = f"{k_ep}_{k_ch}_{scene['no']:03}__{primary_src_scene['k_ed_ep_ch_no'][0]}"

    # Input file for this task
    suffix = "hr_" if task_name in ('final') else ""
    in_vsettings: VideoSettings = db['common']['video_format']['hr']
    in_ext: str = vcodec_to_extension[in_vsettings.codec]
    task.in_video_file = os.path.join(
        db['common']['directories']['cache_doc'],
        k_ep,
        f"{prev_task_name}",
        f"{basename}_{suffix}{prev_task_name}{in_ext}"
    )

    # Output file
    suffix = "hr_" if task_name in ('cg', 'final') else ""
    ext: str = vcodec_to_extension[vsettings.codec]
    task.video_file = absolute_path(
        os.path.join(
            db['common']['directories']['cache_doc'],
            k_ep,
            task_name,
            f"{basename}_{suffix}{task_name}{ext}"
        )
    )

    # No fallback

