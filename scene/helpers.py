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
#   initial -> hr -> cg -> final

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
        'lr': 'initial',
        'hr': 'initial',
        'cg': 'hr',
        'final': 'cg',
    }
    prev_task_name: TaskName = doc_previous_task[task_name]

    # Cache path, in/out files
    in_cache_doc: str = os.path.abspath(
        os.path.join(db['common']['directories']['cache_doc'], os.pardir, k_ch, k_ep)
    )
    out_cache_doc = in_cache_doc
    in_basename: str = f"{k_ep}_{k_ch}_{scene['no']:03}__{primary_src_scene['k_ed_ep_ch_no'][0]}"
    out_basename = in_basename


    # Specific to g_doc (asuivre should follow the same way)
    if scene['dst']['k_ch'] == 'g_doc':
        _k_ed, _k_ep, _k_ch, _no = primary_src_scene['k_ed_ep_ch_no']
        in_basename: str = f"{_k_ch}_{_no:03}__{_k_ed}_{_k_ep}"
        out_basename = in_basename

        # Cache path
        in_cache_doc = os.path.abspath(os.path.join(in_cache_doc, os.pardir))
        out_cache_doc = in_cache_doc
        if task_name == 'final':
            out_cache_doc: str = os.path.abspath(
                os.path.join(
                    db['common']['directories']['cache_doc'], os.pardir, k_ch, k_ep
                )
            )
            _k_ed, _k_ep, _k_ch, _no = primary_src_scene['k_ed_ep_ch_no']
            out_basename: str = f"{k_ep}_{k_ch}_{scene['no']:03}__{_k_ed}"


    # Input file for this task
    suffix = "hr_" if task_name in ('final') else ""
    in_vsettings: VideoSettings = db['common']['video_format']['hr']
    in_ext: str = vcodec_to_extension[in_vsettings.codec]
    task.in_video_file = os.path.join(
        in_cache_doc,
        f"{prev_task_name}",
        f"{in_basename}_{suffix}{prev_task_name}{in_ext}"
    )


    # Output file
    suffix = "hr_" if task_name == 'cg' else ""
    ext: str = vcodec_to_extension[vsettings.codec]

    task.video_file = absolute_path(
        os.path.join(
            out_cache_doc,
            task_name,
            f"{out_basename}_{suffix}{task_name}{ext}"
        )
    )

    if scene['dst']['k_ch'] == 'g_doc' and task_name == 'final':
        task.video_file = absolute_path(
            os.path.join(out_cache_doc, f"{out_basename}_{suffix}{task_name}{ext}")
        )


    # No fallback

