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
    parse_target_chapter,
    Chapter,
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
    'upscale': 'initial',
    'tf': 'hr',
    'cg': 'hr',
    'final': 'cg',
}

_g_asuivre_previous_task: dict[str, str] = {
    'initial': '',
    'sim_lr': 'initial',
    'lr': 'initial',
    'upscale': 'initial',
    'hr': 'initial',
    'cg': 'hr',
    'final': 'cg',
}



def get_upscale_suffix(
    scene: Scene,
    compare: bool = False
) -> str:
    task_name: TaskName = scene['task'].name

    # Append the model name to evaluate models: only for upscale task
    if task_name != 'upscale':
        return ""

    scene_filters = scene['filters']
    sequence: str = scene_filters[task_name].sequence
    for t in (
        ':cuda', ':trt', ':fp16', ':fp32', ':bf16', ':static'
    ):
        sequence = sequence.replace(t, '')
    suffix: str = ""
    for s in sequence.split(','):
        if result := re.search(re.compile(r"^([^=]*)=(.*)"), s):
            _s = result.group(1)
            if ("darker" in s or "unsharp" in s):
                _s += f"_{result.group(2).replace(':', '_')}"
            suffix += f"+{_s}" if suffix else f"{_s}"
        else:
            suffix += f"+{s}" if suffix else s
    if compare:
        # use the first scene no
        suffix = f"_{scene['src'].primary_scene()['k_ed_ep_ch_no'][-1]:03}_{suffix}"
    else:
        suffix = f"__{suffix}"

    return suffix



def set_doc_filepath_(scene: Scene, compare: bool = False) -> None:
    k_ep, k_ch = scene['dst']['k_ep'], scene['dst']['k_ch']
    primary_src_scene = scene['src'].primary_scene()
    task: ProcessingTask = scene['task']
    task_name: str = task.name
    # _task_name: str = 'lr' if task_name in ('initial', 'sim') else task_name
    scene_filters = scene['filters']
    vsettings: VideoSettings = task.video_settings
    s_no_str = scene_no_str(scene)

    # Append the model name to evaluate models: only for upscale task
    suffix = get_upscale_suffix(scene=scene, compare=compare)

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
    suffix = ""
    if task_name in ('final', ):
        suffix = "_hr_"
    elif task_name in ('tf', ):
        suffix = "_"

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



def set_g_asuivre_filepath_(scene: Scene,compare: bool = False) -> None:
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




def set_prec_asuivre_filepath_(scene: Scene, compare: bool = False) -> None:
    task = scene['task']
    task_name = task.name
    primary_src_scene = scene['src'].primary_scene()
    k_ep: str = scene['dst']['k_ep']
    k_ch: Chapter = scene['dst']['k_ch']
    vsettings = task.video_settings
    lang = db[k_ep]['audio']['lang']

    in_k_ed, in_k_ep, in_k_ch, in_scene_no = primary_src_scene['k_ed_ep_ch_no']
    s_no_str: str = scene_no_str(scene)

    # Input/output cache directory
    in_cache_path: str = db[in_k_ep]['cache_path']
    out_cache_path: str = in_cache_path
    if task_name == 'final':
        out_cache_path: str = db[k_ep]['cache_path']

    # Get the
    in_s_no_str = s_no_str
    if task_name in ('tf', 'cg', 'final'):
        # The input scene no has to be the target's one
        #   and not the original one for these chapters/scenes
        print(lightcyan(f"consolidate scene: prec/asuivre, parse {in_k_ep}:{in_k_ch}"))
        target_chapter_scenes: list[Scene] = parse_target_chapter(
            k_ep=in_k_ep, k_ch=in_k_ch
        )
        src_ed_ep_ch_no = scene['src'].primary_scene().k_ed_ep_ch_no
        for _scene in target_chapter_scenes:
            if _scene['src'].scenes()[0].k_ed_ep_ch_no == src_ed_ep_ch_no:
                in_scene_no = _scene['no']
                break
        # The source is the episode -> 3 digits
        in_s_no_str = f"{in_scene_no:03}"


    # Output video filename
    # Use the original basename if not final
    in_basename: str = f"{in_k_ep}_{in_k_ch}_{in_s_no_str}__{in_k_ed}"
    out_basename: str = f"{in_k_ep}_{in_k_ch}_{in_s_no_str}__{in_k_ed}"
    if task_name == 'final':
        out_basename = f"{k_ep}_{k_ch}_{s_no_str}__{in_k_ed}"

    suffix: str = ""
    # Append the hash for comparisons except for some tasks
    if task_name not in ('hr', 'tf', 'final') and task.hash != '':
        suffix = f"_{task.hash}"
    suffix += f"_{task_name}"

    upscale_suffix = get_upscale_suffix(scene=scene, compare=compare)
    if upscale_suffix:
        suffix = upscale_suffix

    # Some tasks are optionals, use the previous task
    previous = {
        'st': 'hr',
        'tf': 'st',
        'cg': 'tf',
        'final': 'cg',
    }
    if task_name in list(previous.keys()):
        prev_task_name: TaskName = previous[task_name]
        if task_name == 'st':
            suffix: str = f"_hr_{task_name}"
        elif task_name == 'cg':
            suffix: str = f"_tf_{task_name}"
        # TODO: when using python deshaker suffix shall not be changed

    # Output file
    ext: str = vcodec_to_extension[vsettings.codec]
    if task_name == 'final' and lang != 'fr':
        suffix += f"_{lang}"

    task.video_file = absolute_path(
        os.path.join(out_cache_path, f"{task_name}", f"{out_basename}{suffix}{ext}")
    )
    if task_name == 'upscale':
        cache_path: str = absolute_path(os.path.join(out_cache_path, f"{task_name}"))
        cache_path = os.path.join(cache_path, f"{scene['dst']['k_ch']}")
        task.video_file = os.path.join(cache_path, f"{out_basename}{suffix}{ext}")


    # Input video file

    # Input file for this task might not use the previous one
    #  but the input of the previous task, update input file
    if task_name in ('st', 'tf', 'cg', 'final'):
        suffix: str = ""
        if task_name == 'tf':
            suffix = "hr_"
        elif task_name == 'final':
            suffix = "tf_"

        # These taks use the same video settings as hr
        in_vsettings: VideoSettings = db['vsettings']['hr']
        in_ext: str = vcodec_to_extension[in_vsettings.codec]

        # Input basename/cache
        task.in_video_file = os.path.join(
            in_cache_path,
            f"{prev_task_name}",
            f"{in_basename}_{suffix}{prev_task_name}{in_ext}"
        )

        # Add fallback input video filename bc some tasks may be not processed
        task.fallback_in_video_files = {
            'hr': os.path.join(in_cache_path, f"hr", f"{in_basename}_hr{in_ext}"),
            'st': os.path.join(in_cache_path, f"st", f"{in_basename}_hr_st{in_ext}"),
            'tf': os.path.join(in_cache_path, f"tf", f"{in_basename}_tf{in_ext}"),
        }

        in_video_fp: str = task.in_video_file
        if not os.path.exists(in_video_fp) and task_name not in ('cg', ):
            for i in range(
                TASK_NAMES.index(task.name),
                TASK_NAMES.index('hr') - 1,
                -1
            ):
                _task_name: TaskName = TASK_NAMES[i]
                if _task_name == task_name:
                    continue

                if _task_name not in task.fallback_in_video_files:
                    continue
                in_video_fp = task.fallback_in_video_files[_task_name]
                if _task_name == 'hr' or os.path.exists(in_video_fp):
                    break
            task.in_video_file = in_video_fp
