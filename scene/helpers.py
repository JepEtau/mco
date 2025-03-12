from __future__ import annotations
from copy import deepcopy
import os
from pprint import pprint
import re
import sys
from warnings import warn
from utils.mco_types import Scene
from utils.media import vcodec_to_extension
from parsers import (
    db,
    VideoSettings,
    TaskName,
    TASK_NAMES,
    ProcessingTask,
    scene_no_str,
)
from utils.p_print import *
from utils.path_utils import absolute_path

# Task order:
#   initial -> hr -> cg -> final


_doc_previous_task: dict[str, str] = {
    'initial': '',
    'sim_lr': 'initial',
    'lr': 'initial',
    'hr': 'initial',
    'tf': 'hr',
    'cg': 'hr',
    'final': 'cg',
}

_g_asuivre_previous_task: dict[str, str] = {
    'sim_lr': 'initial',
    'lr': 'initial',
    'hr': 'initial',
    'cg': 'hr',
    'final': 'cg',
}


def set_doc_filepath_(scene: Scene) -> None:
    k_ep, k_ch = scene['dst']['k_ep'], scene['dst']['k_ch']
    primary_src_scene = scene['src'].primary_scene()
    task: ProcessingTask = scene['task']
    task_name: str = task.name
    # _task_name: str = 'lr' if task_name in ('initial', 'sim') else task_name
    scene_filters = scene['filters']
    vsettings: VideoSettings = task.video_settings
    s_no_str = scene_no_str(scene)

    # Append the model name to evaluate models: only for upscale task
    if task_name == 'upscale':
        sequence: str = scene_filters[task_name].sequence
        for t in (
            ':cuda', ':trt', ':fp16', ':fp32', ':bf16'
        ):
            sequence = sequence.replace(t, '')
        suffix: str = ""
        for s in sequence.split(','):
            if result := re.search(re.compile(r"^([^=]*)="), s):
                suffix += f"+{result.group(1)}" if suffix else f"{result.group(1)}"
            else:
                suffix += f"+{s}" if suffix else s
        suffix = f"__{suffix}"


    # Cache path, in/out files
    in_cache_doc: str = os.path.abspath(
        os.path.join(
            db['common']['directories']['cache_doc'],
            os.pardir,
            k_ch,
            k_ep
        )
    )
    out_cache_doc = in_cache_doc
    in_basename: str = f"{k_ep}_{k_ch}_{s_no_str}__{primary_src_scene['k_ed_ep_ch_no'][0]}"
    out_basename = in_basename


    # Specific to g_doc (asuivre should follow the same way)
    if scene['dst']['k_ch'] == 'g_doc':
        _k_ed, _k_ep, _k_ch, _no = primary_src_scene['k_ed_ep_ch_no']
        in_basename: str = f"{_k_ch}_{_no:02}__{_k_ed}_{_k_ep}"
        out_basename = in_basename

        # Cache path
        in_cache_doc = os.path.abspath(os.path.join(in_cache_doc, os.pardir))
        out_cache_doc = in_cache_doc
        if task_name in ('sim_lr', 'final'):
            out_cache_doc: str = os.path.abspath(
                os.path.join(
                    db['common']['directories']['cache_doc'],
                    os.pardir,
                    k_ch
                )
            )
            _k_ed, _k_ep, _k_ch, _no = primary_src_scene['k_ed_ep_ch_no']
            out_basename: str = f"{k_ep}_{k_ch}_{s_no_str}__{_k_ed}"



    # Input file for this task
    prev_task_name: TaskName = _doc_previous_task[task_name]
    suffix = "_hr_" if task_name in ('final') else ""
    in_vsettings: VideoSettings = db['vsettings']['hr']
    in_ext: str = vcodec_to_extension[in_vsettings.codec]
    suffix = (
        f"{suffix}{prev_task_name}"
        if task_name not in ('upscale', 'hr')
        else ""
    )
    task.in_video_file = os.path.join(
        in_cache_doc,
        f"{prev_task_name}",
        f"{in_basename}{suffix}{in_ext}"
    )


    # Output file
    suffix = "hr_" if task_name == 'cg' else ""
    ext: str = vcodec_to_extension[vsettings.codec]

    # For doc in hr, add a suffix to mix different sources
    suffix2: str = ''
    if k_ch == 'doc' and task_name == 'hr':
        if 'mco_doc' in scene_filters['hr'].sequence:
            suffix2 += f"_tpz"

    task.video_file = absolute_path(
        os.path.join(
            out_cache_doc,
            task_name,
            f"{out_basename}_{suffix}{task_name}{suffix2}{ext}"
        )
    )

    if scene['dst']['k_ch'] == 'g_doc' and task_name == 'final':
        task.video_file = absolute_path(
            os.path.join(
                db['common']['directories']['cache_doc'],
                os.pardir,
                k_ch,
                task_name,
                f"{out_basename}_{suffix}{task_name}{ext}"
            )
        )

        # Fallback to tf if not mco_doc
        if not 'mco_doc' in scene_filters['hr'].sequence:
            task.fallback_in_video_files['tf'] = task.in_video_file.replace("_hr_", "_tf_")
            if not os.path.exists(task.in_video_file):
                task.in_video_file = task.fallback_in_video_files['tf']



def set_g_asuivre_filepath_(scene: Scene) -> None:
    k_ep_dst, k_ch_dst = scene['dst']['k_ep'], scene['dst']['k_ch']

    primary_src_scene = scene['src'].primary_scene()
    task: ProcessingTask = scene['task']
    task_name: str = task.name
    # _task_name: str = 'lr' if task_name in ('initial', 'sim') else task_name
    scene_filters = scene['filters']
    vsettings: VideoSettings = task.video_settings
    s_no_str = scene_no_str(scene)

    # Append the model name to evaluate models: only for upscale task
    if task_name == 'upscale':
        sequence: str = scene_filters[task_name].sequence
        for t in (
            ':cuda', ':trt', ':fp16', ':fp32', ':bf16'
        ):
            sequence = sequence.replace(t, '')
        suffix: str = ""
        for s in sequence.split(','):
            if result := re.search(re.compile(r"^([^=]*)="), s):
                suffix += f"+{result.group(1)}" if suffix else f"{result.group(1)}"
            else:
                suffix += f"+{s}" if suffix else s
        suffix = f"__{suffix}"


    # Cache path, in/out files
    in_cache_doc: str = os.path.abspath(
        os.path.join(
            db['common']['directories']['cache_doc'], os.pardir, k_ch_dst, k_ep_dst
        )
    )
    out_cache_doc = in_cache_doc
    in_basename: str = f"{k_ep_dst}_{k_ch_dst}_{s_no_str}__{primary_src_scene['k_ed_ep_ch_no'][0]}"
    out_basename = in_basename


    # Specific to g_doc (asuivre should follow the same way)
    if k_ch_dst == 'g_asuivre':
        _k_ed, _k_ep, _k_ch, _no = primary_src_scene['k_ed_ep_ch_no']
        in_basename: str = f"{_k_ch}_{_no:02}__{_k_ed}_{_k_ep}"
        out_basename = in_basename

        # Cache path
        in_cache_doc = os.path.abspath(os.path.join(in_cache_doc, os.pardir))
        out_cache_doc = in_cache_doc
        if task_name in ('final', 'sim_lr'):
            out_cache_doc: str = os.path.abspath(
                os.path.join(
                    db['common']['directories']['cache_doc'], os.pardir, k_ch_dst, k_ep_dst
                )
            )
            _k_ed, _k_ep, _k_ch, _no = primary_src_scene['k_ed_ep_ch_no']
            out_basename: str = f"{k_ep_dst}_{k_ch_dst}_{s_no_str}__{_k_ed}"


    # Input file for this task
    prev_task_name: TaskName = _g_asuivre_previous_task[task_name]
    suffix = "hr_" if task_name in ('final', ) else ""
    in_vsettings: VideoSettings = db['vsettings']['hr']
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

    # Store the g_asuivre of all episodes in the same directory
    if (
        k_ch_dst == 'g_asuivre'
        and task_name in ('sim_lr', 'final',)
    ):
        task.video_file = absolute_path(
            os.path.join(
                db['common']['directories']['cache_doc'],
                os.pardir,
                k_ch_dst,
                task_name,
                f"{out_basename}_{suffix}{task_name}{ext}"
            )
        )
    # No fallback


