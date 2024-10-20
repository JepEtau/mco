from __future__ import annotations
from copy import deepcopy
import os
from pprint import pprint
import re
import sys
from utils.hash import calc_hash
from utils.mco_types import (
    ChapterVideo, Effect, Effects, Scene,
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
)
from utils.mco_utils import (
    get_cache_path,
    get_target_video,
    is_first_scene,
    is_last_scene,
)
from utils.p_print import *
from utils.path_utils import absolute_path


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
    evaluation: bool = False
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

    scene['src'].consolidate(task_name=task_name, watermark=False)
    primary_src_scene = scene['src'].primary_scene()

    if verbose:
        print(lightgreen("Consolidate scene:"))
        print(lightcyan("================================== Scene ======================================="))
        pprint(scene)
        print(lightcyan("-------------------------------------------------------------------------------"))


    # Cache directory
    scene['cache'] = get_cache_path(scene)
    # os.path.join(db['common']['directories']['cache'], k_ep, k_ch, "%03d" % (scene['no']))


    # Geometry
    #---------------------------------------------------------------------------
    k_ep: str = scene['dst']['k_ep']
    k_ed: str = scene['dst']['k_ed']
    k_ch: str = scene['dst']['k_ch']
    if k_ch in ['g_asuivre', 'g_documentaire']:
        ch_geometry: ChapterGeometry = deepcopy(
            db[scene['dst']['k_ep']]['video']['target'][k_ch[2:]]['geometry']
        )
        if ch_geometry is None:
            raise ValueError(yellow(f"no geometry for chapter: {k_ch}"))
        scene['geometry'] = SceneGeometry(chapter=ch_geometry)

    else:
        if verbose:
            print(f"\t\t\tconsolidate_scene: get geometry for {k_ed}:{k_ep}:{k_ch}")
        chapter: ChapterVideo | None = None
        if k_ch in ('g_debut', 'g_fin'):
            chapter = db[k_ch]['video']
        else:
            chapter = db[k_ep]['video']['target'][k_ch]
        scene['geometry'].chapter = deepcopy(chapter['geometry'])


    # Processing chain
    #---------------------------------------------------------------------------

    # Get filters used by this scene: use the filters from the first src scene
    # all src scenes MUST have the same filters. Assume that's the case
    scene['filters'] = deepcopy(primary_src_scene['scene']['filters'])

    # consolidate_scene_filters: add missing filters
    scene_filters = scene['filters']
    for t in TASK_NAMES:
        if t not in scene_filters:
            scene_filters[t] = Filter(task_name=t)

    deint_hashcode = scene_filters['initial'].hash

    # Replace
    replace_hash: str = ''
    frame_replace = scene['src'].get_frame_replace()
    if len(frame_replace.keys()) != 0:
        replace_hash = ','.join([f"{k}:{v}" for k, v in frame_replace.items()])

    # Upscale
    upscale_hashcode = calc_hash(';'.join([
        deint_hashcode,
        scene_filters['upscale'].sequence.replace('.pth', '')
    ]))

    # Store hashes
    scene_filters['lr'].hash = calc_hash(';'.join([deint_hashcode, replace_hash]))
    scene_filters['sim'].hash = scene_filters['lr'].hash
    scene_filters['hr'].hash = upscale_hashcode
    scene_filters['upscale'].hash = upscale_hashcode

    # Update the scene task
    scene['task'].hashcode = scene_filters[task_name].hash

    if task_name == 'lr' and watermark:
        # if 'effects' in scene:
        #     scene['effects'] = Effects()
        # scene['effects'].append(Effect(name='watermark'))
        sequence: str = scene['filters'][task_name].sequence
        scene['filters'][task_name].sequence = (
            f"{sequence};watermark"
            if sequence
            else "watermark"
        )


    # Output
    #---------------------------------------------------------------------------

    # Output video settings
    _task_name: str = task_name
    if task_name == 'initial':
        _task_name = 'lr'
    elif task_name == 'sim':
        _task_name = 'lr'

    vsettings: VideoSettings = db['common']['video_format'].get(_task_name, None)
    if vsettings is not None:
        task.video_settings = deepcopy(vsettings)
        vsettings = task.video_settings
        if task_name == 'hr':
            vsettings.pad = db['common']['video_format'][task_name].pad
            vsettings.metadata['HR'] = task.hashcode
    elif task_name in ('st', 'tf', 'cg'):
        vsettings: VideoSettings = db['common']['video_format'].get('hr', None)
        vsettings.pad = 0
    else:
        raise ValueError(f"VideoSettings not defined for task: {task_name}")

    # Output video filename
    _k_ed, _k_ep = primary_src_scene['k_ed_ep_ch_no'][:2]
    if k_ch in ('g_debut', 'g_fin'):
        cache_path: str = db[k_ch]['cache_path']
        basename = f"{k_ch}_{scene['no']:03}__{_k_ed}_{_k_ep}"
    else:
        cache_path: str = db[k_ep]['cache_path']
        basename = f"{k_ep}_{k_ch}_{scene['no']:03}__{_k_ed}"

    suffix: str = ""
    if task_name != "hr":
        if task.hashcode != '':
            suffix = f"_{task.hashcode}"
    suffix += f"_{task_name}"

    # Append the model name to evaluate models: only for upscale task
    if evaluation and task_name == 'upscale':
        sequence: str = scene_filters[task_name].sequence
        for t in (
            ':cuda', ':trt', ':fp16', ':fp32'
        ):
            sequence = sequence.replace(t, '')
        suffix: str = ""
        for s in sequence.split(','):
            print(s)
            if (result := re.search(re.compile(r"(.*)="), s)):
                suffix += f"+{result.group(1)}"
            else:
                suffix += f"+{s}"

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
    task.video_file = absolute_path(
        os.path.join(cache_path, f"scenes_{task_name}", f"{basename}{suffix}{ext}")
    )

    # Input file for this task
    if task_name in ('st', 'tf', 'cg', 'final'):
        suffix: str = ""
        if task_name == 'tf':
            suffix: str = "hr_"
        elif task_name == 'final':
            suffix: str = "tf_"

        in_vsettings: VideoSettings = db['common']['video_format']['hr']
        in_ext: str = vcodec_to_extension[in_vsettings.codec]

        task.in_video_file = os.path.join(
            scene['cache'], f"scenes_{prev_task_name}", f"{basename}_{suffix}{prev_task_name}{in_ext}"
        )

        # Add fallback input video filename bc some tasks may be not processed
        if task_name in ('st', 'tf', 'final'):
            task.fallback_in_video_files = {
                'hr': os.path.join(scene['cache'], f"scenes_hr", f"{basename}_hr{in_ext}"),
                'st': os.path.join(scene['cache'], f"scenes_st", f"{basename}_hr_st{in_ext}"),
                'tf': os.path.join(scene['cache'], f"scenes_tf", f"{basename}_tf{in_ext}"),
            }


    # Effects
    #---------------------------------------------------------------------------
    # pprint(scene)
    # sys.exit()
    if is_last_scene(scene) and 'effects' in scene:
        # TODO: clean this bc effects has been refactored
        print(yellow("last scene"))
        ch_video: ChapterVideo = get_target_video(scene)
        ch_effect: Effect = (
            ch_video['effects'].primary_effect()
            if 'effects' in ch_video
            else None
        )
        scene_effect: Effect = scene['effects'].primary_effect()
        pprint(ch_effect)
        pprint(scene_effect)
        if ch_effect is not None and 'fadeout' in ch_effect.name:
            if scene_effect is not None and 'fadeout' in scene_effect.name:
                # Patch fadeout
                scene_effect.fade = min(
                    max(scene_effect.fade, ch_effect.fade),
                    scene['dst']['count'] + scene_effect.loop
                )
                # scene_effect.frame_ref = (
                #     scene['src'].first_frame_no() + scene['dst']['count']
                #     + scene_effect.loop - scene_effect.fade
                # )
            elif scene_effect is None:
                scene['effects'] = Effects([
                    Effect(
                        name='fadeout',
                        frame_ref=scene['dst']['count'] - ch_effect.fade,
                        fade= ch_effect.fade
                    )
                ])
            # verbose = True

    if is_first_scene(scene):
        ch_video: ChapterVideo = get_target_video(scene)
        if (
            'effects' in ch_video
            and (ch_effect := ch_video['effects'].get_effect('fadein'))
        ):
            if 'effects' not in scene:
                scene['effects'] = Effects()
            scene_effect: Effect = deepcopy(ch_effect)
            scene_effect.frame_ref = scene['src'].first_frame_no()
            scene['effects'].append(scene_effect)

    if verbose:
        print(lightcyan("TO"))
        pprint(scene)
        print("End of scene consolidation")
        print(lightcyan("==============================================================================="))
        sys.exit()
