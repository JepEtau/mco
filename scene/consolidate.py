from __future__ import annotations
from copy import deepcopy
import os
from pprint import pprint
import re
import sys
from warnings import warn
from scene.helpers import (
    set_doc_filepath_,
    set_g_asuivre_filepath_,
)
from parsers.hash import calc_hash
from utils.mco_types import (
    ChapterVideo, Scene,
)
from utils.media import vcodec_to_extension
from parsers import (
    db,
    Filter,
    TASK_NAMES,
    ProcessingTask,
    VideoSettings,
    TaskName,
    ChapterGeometry,
    SceneGeometry,
    credit_chapter_keys,
    Chapter,
    scene_no_str,
    calc_hash,
    Effects,
    Effect,
)
from utils.mco_utils import (
    get_cache_path,
    get_target_video,
    is_first_scene,
    is_last_scene,
)
from utils.p_print import *
from utils.path_utils import absolute_path
from .src_scene import SrcScene, SrcScenes


def is_scene_stabilized(scene: Scene) -> bool | None:
    try:
        st_fp: str = scene['task'].fallback_in_video_files['st']
    except:
        return None
    return os.path.isfile(st_fp) and not os.path.islink(st_fp)



def consolidate_scene(
    scene: Scene,
    task_name: TaskName = '',
    watermark: bool = False,
    compare: bool = False
) -> None:
    """This procedure is used to simplify a single scene and add
    properties to process it: removes unecessary property, add
    paths to input/output files, update frames no. depending on edition, etc.

    edition_mode: used to not consolidate geometry/curves and remove replace/stabilize/deshake
    """
    verbose: bool = False

    if task_name != '':
        scene['task'] = ProcessingTask(name=task_name)
    task: ProcessingTask = scene['task']
    task_name: TaskName = task.name
    task_name_index: int = TASK_NAMES.index(task_name)

    s_no_str = scene_no_str(scene)

    scene['src'].consolidate(task_name=task_name, watermark=False)
    primary_src_scene = scene['src'].primary_scene()

    k_ep: str = scene['dst']['k_ep']
    k_ch: Chapter = scene['dst']['k_ch']

    lang: str = 'fr'
    if k_ch in ('g_debut', 'g_fin'):
        lang = db[k_ch]['audio']['lang']
    else:
        lang = db[k_ep]['audio']['lang']

    if verbose:
        print(lightgreen("Consolidate scene:"))
        print(lightcyan("================================== Scene ======================================="))
        pprint(scene)
        print(lightcyan("-------------------------------------------------------------------------------"))


    # Cache directory
    scene['cache'] = get_cache_path(scene)
    # os.path.join(db['common']['directories']['cache'], k_ep, k_ch, "%03d" % (scene['no']))

    # Effects
    #---------------------------------------------------------------------------
    if k_ch == 'g_asuivre' and task_name in ('hr', 'upscale'):
        src_scene: SrcScene = scene['src'].primary_scene()
        loop_effect = scene['effects'].get_effect('loop')

        scene['dst']['count'] = 100
        loop_effect.loop = scene['dst']['count'] - 1
        src_scene.effects = scene['effects']

    elif k_ch == 'g_doc' and task_name in ('hr', 'upscale'):
        src_scene: SrcScene = scene['src'].primary_scene()
        in_scene: Scene = src_scene.in_scene
        src_scene.count = in_scene['count']

        loop_effect = Effect(
            name='loop',
            f_ref=in_scene['start'] + in_scene['count'] - 1,
            start=0,
            loop=0
        )

        scene['dst']['count'] = 280
        loop_effect.loop = (scene['dst']['count'] - in_scene['count'])
        src_scene.effects = Effects([loop_effect])


    # Geometry
    #---------------------------------------------------------------------------
    if k_ch in ['g_asuivre', 'g_doc']:
        # Use following chapter to set this geometry
        ch_geometry: ChapterGeometry = deepcopy(
            db[scene['dst']['k_ep']]['video']['target'][k_ch[2:]]['geometry']
        )
        if ch_geometry is None:
            raise ValueError(yellow(f"no geometry for chapter: {k_ch}"))
        if 'geometry' not in scene:
            scene['geometry'] = SceneGeometry()
        scene['geometry'].chapter = ch_geometry

    else:
        if verbose:
            print(f"\t\t\tconsolidate_scene: get geometry for {k_ep}:{k_ch}")
        chapter: ChapterVideo | None = None
        if k_ch in ('g_debut', 'g_fin'):
            chapter = db[k_ch]['video']
        else:
            chapter = db[k_ep]['video']['target'][k_ch]
        try:
            scene['geometry'].chapter = deepcopy(chapter['geometry'])
        except:
            if task_name == 'final':
                raise ValueError(f"no geometry defined for {k_ep}:{k_ch}")
            scene['geometry'] = SceneGeometry()


    # Processing chain
    #---------------------------------------------------------------------------

    # Get filters used by this scene: use the filters from the first src scene
    # all src scenes MUST have the same filters. Assume that's the case
    scene['filters'] = deepcopy(primary_src_scene.in_scene['filters'])

    # consolidate_scene_filters: add missing filters
    scene_filters = scene['filters']
    for t in TASK_NAMES:
        if t not in scene_filters:
            scene_filters[t] = Filter(task_name=t)


    # Output video Settings
    #---------------------------------------------------------------------------
    _task_name: TaskName = task_name
    if task_name == 'initial':
        _task_name = 'lr'
    elif task_name == 'cg':
        _task_name = 'tf'

    in_vsettings: VideoSettings = db['vsettings'].get(_task_name, None)
    if in_vsettings is not None:
        task.video_settings = deepcopy(in_vsettings)
        vsettings = task.video_settings
        if task_name == 'hr':
            vsettings.pad = db['vsettings'][task_name].pad

    # elif task_name_index > TASK_NAMES.index('upscale'):
    else:
        task.video_settings = deepcopy(db['vsettings'].get(task_name, None))
        vsettings = task.video_settings
        vsettings.pad = 0

    # pprint(task)
    # raise
    # else:
    #     raise ValueError(f"VideoSettings not defined for task: {task_name}")


    # Hash code, metadata
    #---------------------------------------------------------------------------

    # Deinterlace
    deint_hash = scene_filters['initial'].hash
    vsettings.metadata['00_deint'] = scene_filters['initial'].hash

    # Replace
    replace_hash: str = ''
    frame_replace = scene['src'].get_frame_replace()
    if len(frame_replace.keys()) > 0:
        replace_hash = ','.join([f"{k}:{v}" for k, v in frame_replace.items()])
    vsettings.metadata['00_replace'] = calc_hash(replace_hash)

    # lowres
    t_hash: str = calc_hash(';'.join([deint_hash, replace_hash]))
    scene_filters['lr'].hash = t_hash
    if watermark and task_name in ('extract', 'lr', 'sim_lr'):
        sequence: str = scene['filters'][task_name].sequence
        scene['filters'][task_name].sequence = (
            f"{sequence};watermark"
            if sequence
            else "watermark"
        )

    # upscale, hr
    sequence: str = scene['filters']['upscale'].sequence
    for i, f in enumerate(sequence.split(',')):
        for s in ('.pth', '.onnx', '.safetensor'):
            f = f.replace(s, '')
        if task_name_index >= TASK_NAMES.index('upscale'):
            vsettings.metadata[f"{i + 1:02}"] = f
    scene_filters['upscale'].hash = t_hash

    t_hash = calc_hash(f"{t_hash};{vsettings.pad}")
    scene_filters['hr'].hash = t_hash

    # TODO: append stabilization parameters
    scene_filters['st'].hash = t_hash

    # Temporal filters
    t_hash = calc_hash(f"{t_hash};{scene['filters']['tf'].sequence}")
    scene_filters['tf'].hash = t_hash

    # Color grade
    scene_filters['cg'].hash = t_hash

    # Final: effects + geometry
    t_hash = calc_hash(f"{t_hash};{scene['geometry'].hash()}")
    t_effect_hash: str = ""
    if ('effects' in scene and scene['effects'].has_effects()):
        t_effect_hash = scene['effects'].hash()
        t_hash = calc_hash(f"{t_hash};{t_effect_hash}")

    scene_filters['final'].hash = t_hash

    # For simulation, use lowres and effects
    scene_filters['sim'].hash = calc_hash(
        f"{scene_filters['lr'].hash};{t_effect_hash}"
    )

    task.hash = scene_filters[task_name].hash
    vsettings.metadata['hash'] = task.hash


    # Filenames
    #---------------------------------------------------------------------------
    if k_ch in ('g_doc', 'doc'):
        set_doc_filepath_(scene)

    elif k_ch == 'g_asuivre':
        set_g_asuivre_filepath_(scene)

    else:
        # Output video filename
        _k_ed, _k_ep = primary_src_scene['k_ed_ep_ch_no'][:2]
        if k_ch in ('g_debut', 'g_fin'):
            cache_path: str = db[k_ch]['cache_path']
            basename = f"{k_ch}_{s_no_str}__{_k_ed}_{_k_ep}"

        elif (
            k_ch in ('g_asuivre', 'g_doc')
            and task_name not in ('lr', 'sim', 'final')
        ):
            cache_path: str = db[k_ch]['cache_path']
            basename = f"{k_ch}_{s_no_str}__{_k_ed}_{_k_ep}"

        else:
            cache_path: str = db[k_ep]['cache_path']
            basename = f"{k_ep}_{k_ch}_{s_no_str}__{_k_ed}"

        suffix: str = ""
        # Append the hash for comparisons except for some tasks
        if (
            task_name not in ('hr', 'tf', 'final')
            and task.hash != ''
        ):
            suffix = f"_{task.hash}"
        suffix += f"_{task_name}"

        # Append the model name to evaluate models: only for upscale task
        if task_name == 'upscale':
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
            os.path.join(cache_path, f"{task_name}", f"{basename}{suffix}{ext}")
        )
        if task_name == 'upscale':
            cache_path: str = absolute_path(os.path.join(cache_path, f"{task_name}"))
            if k_ch not in credit_chapter_keys():
                cache_path = os.path.join(cache_path, f"{scene['dst']['k_ch']}")
            task.video_file = os.path.join(cache_path, f"{basename}{suffix}{ext}")

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

            task.in_video_file = os.path.join(
                scene['cache'],
                f"{prev_task_name}",
                f"{basename}_{suffix}{prev_task_name}{in_ext}"
            )

            # Add fallback input video filename bc some tasks may be not processed
            task.fallback_in_video_files = {
                'hr': os.path.join(scene['cache'], f"hr", f"{basename}_hr{in_ext}"),
                'st': os.path.join(scene['cache'], f"st", f"{basename}_hr_st{in_ext}"),
                'tf': os.path.join(scene['cache'], f"tf", f"{basename}_tf{in_ext}"),
            }

            in_video_fp: str = task.in_video_file
            if not os.path.exists(in_video_fp):
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

    if verbose:
        print(lightcyan("TO"))
        pprint(scene)
        print("End of scene consolidation")
        print(lightcyan("==============================================================================="))
        raise
