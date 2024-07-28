from copy import deepcopy
import os
from pprint import pprint
import sys
from typing import OrderedDict
from processing.deint import calc_deint_hash, get_qtgmc_args, get_template_script
from utils.hash import calc_hash
from utils.mco_types import ChapterVideo, Effect, Scene
from utils.images import Images
from parsers import (
    db,
    Filter,
    TASK_NAMES,
    ProcessingTask,
    VideoSettings,
    TaskName,
)
from utils.mco_utils import get_cache_path, get_target_video, is_last_scene, nested_dict_set
from utils.p_print import *
from utils.path_utils import absolute_path, path_split
from video.concat_frames import get_video_filename, set_video_filename
from video.out_frames import get_out_frame_paths
from .filters import get_filters


def consolidate_scene(scene: Scene, watermark: bool = False) -> None:
    """This procedure is used to simplify a single scene and add
    properties to process it: removes unecessary property, add
    paths to input/output files, update frames no. depending on edition, etc.

    edition_mode: used to not consolidate geometry/curves and remove replace/stabilize/deshake
    """
    verbose: bool = False

    task_name: TaskName = scene['task'].name

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
    k_ep = scene['dst']['k_ep']
    k_ed = scene['dst']['k_ed']
    k_ch = scene['dst']['k_ch']
    if k_ch in ['g_asuivre', 'g_documentaire']:
        # print("\t\t\tconsolidate_scene: get geometry from %s:%s:%s" % (k_ed, k_ep, k_ch[2:]))
        k_ep_dst = scene['dst']['k_ep']
        try:
            target_geometry = db[k_ep_dst]['video']['target'][k_ch[2:]]['geometry']['target']
        except:
            target_geometry = None
        nested_dict_set(scene, target_geometry, 'geometry', 'target')

        try:
            scene_geometry = db[k_ep]['video'][k_ed][k_ch]['geometry']
            scene_geometry['is_default'] = False
        except:
            scene_geometry = {
                'keep_ratio': True,
                'fit_to_width': False,
                'crop': [0] * 4,
                'is_default': False,
            }
        nested_dict_set(scene, scene_geometry, 'geometry', 'scene')

    else:
        k_ed_src, k_ep_src, k_ch_src, scene_no_src = primary_src_scene['k_ed_ep_ch_no']
        if verbose:
            print(f"\t\t\tconsolidate_scene: get geometry for {k_ed}:{k_ep}:{k_ch}")

        # Target geometry: width defined
        try:
            if k_ch in ('g_debut', 'g_fin'):
                target_geometry = db[k_ch]['video']['geometry']['target']
            else:
                target_geometry = db[k_ep]['video']['target'][k_ch]['geometry']['target']
        except:
            target_geometry = None
        nested_dict_set(scene, target_geometry, 'geometry', 'target')

        # Get default geometry for a scene
        try:
            default_scene_src_geometry = db[k_ep_src]['video'][k_ed_src][k_ch_src]['geometry']
            default_scene_src_geometry['is_default'] = True
        except:
            default_scene_src_geometry = {
                'keep_ratio': True,
                'fit_to_width': False,
                'crop': [0] * 4,
                'is_default': True
            }

        # Get the customized geometry for a scene
        try:
            scene_src_geometry = db[k_ep_src]['video'][k_ed_src][k_ch_src]['scenes'][scene_no_src]['geometry']['scene']
            scene_src_geometry['is_default'] = False
        except:
            scene_src_geometry = None

        if scene_src_geometry is not None:
            # Use the customized
            nested_dict_set(scene, scene_src_geometry, 'geometry', 'scene')
            scene['geometry']['scene']['is_default'] = False
        else:
            # Use the default because no customized defined
            nested_dict_set(scene, default_scene_src_geometry, 'geometry', 'scene')
            try: scene['geometry']['scene']['is_default'] = True
            except: pass

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
    scene_filters['hr'].hash = calc_hash(';'.join([deint_hashcode, replace_hash, upscale_hashcode]))
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

    # List frames
    if task_name == 'hr':
        if k_ch in ('g_asuivre', 'g_documentaire'):
            raise NotImplementedError(red("TODO: HR for g_asuivre and g_documentaire"))
            if 'start' in scene['dst']:
                # print("use the dst start and count for the concatenation file")
                start = scene['dst']['start']
                end = start + scene['dst']['count']
            else:
                start = scene['start']
                end = start + scene['count']
            scene['out_frames'] = list([no for no in range(start, end)])

        else:
            out_frames: list[int] = []

            # Append images
            if 'segments' in scene['src'] and len(scene['src']['segments']) > 0:
                index_start = max(0, scene['src']['start'] - scene['start'])
                index_end = index_start + scene['dst']['count']
            else:
                index_start = max(0, scene['src']['start'] - scene['start'])
                index_end = index_start + scene['dst']['count']

            frame_replace = scene['replace']
            for no in range(scene['start'], scene['start'] + scene['count']):
                out_frames.append(frame_replace[no] if no in frame_replace else no)
            scene['out_frames'] = out_frames[index_start:index_end]

        scene['task'].in_video_file = get_video_filename(scene=scene, task_name='upscale')

    # Output
    #---------------------------------------------------------------------------

    # Output video settings
    _task_name: str = task_name
    if task_name == 'hr':
        _task_name = 'upscale'
    elif task_name == 'initial':
        _task_name = 'hr'

    vsettings: VideoSettings = db['common']['video_format'].get(_task_name, None)
    if vsettings is not None:
        scene['task'].video_settings = deepcopy(vsettings)
        vsettings = scene['task'].video_settings
        if task_name == 'hr':
            vsettings.pad = db['common']['video_format'][task_name].pad
            vsettings.metadata['HR'] = scene['task'].hashcode
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

    suffix = f"_{scene['task'].hashcode}"
    suffix += f"_{task_name}"
    scene['task'].video_file = absolute_path(
        os.path.join(
            cache_path,
            f"scenes_{task_name}",
            f"{basename}{suffix}.mkv"
        )
    )


    # Effects
    #---------------------------------------------------------------------------
    # pprint(scene)
    # sys.exit()
    if is_last_scene(scene) and 'effects' in scene:
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
    if verbose:
        print(lightcyan("TO"))
        pprint(scene)
        print(lightcyan("==============================================================================="))
        sys.exit()
