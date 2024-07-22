from copy import deepcopy
import os
from pprint import pprint
import sys
from typing import OrderedDict
from processing.deint import calc_deint_hash, get_qtgmc_args, get_template_script
from utils.hash import calc_hash
from utils.mco_types import Scene
from utils.images import Images
from parsers import (
    db,
    Filter,
    TASK_NAMES,
    ProcessingTask,
    VideoSettings,
    TaskName,
)
from utils.mco_utils import get_cache_path, nested_dict_set
from utils.p_print import *
from utils.path_utils import absolute_path, path_split
from video.concat_frames import get_video_filename, set_video_filename
from video.out_frames import get_out_frame_paths
from .filters import get_filters


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

    scene['filters'] = get_filters(scene)

    # Consolidate_scene_filters: add missing filters
    scene_filters = scene['filters']
    for t in TASK_NAMES:
        if t not in scene_filters:
            scene_filters[t] = Filter(task_name=t)

    # Deinterlace
    template_script: str = get_template_script(
        episode=k_ep,
        edition=k_ed
    )
    qtgmc_args: OrderedDict[str, str] = get_qtgmc_args(template_script)
    deint_hashcode, _ = calc_deint_hash(qtgmc_args)
    scene_filters[task_name].hash = deint_hashcode

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
    filename: str = f"{basename}_{deint_hashcode}.mkv"
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
    basename = f"{k_ed}_{k_ep}_{k_ch}_{scene['no']:03}"
    suffix = f"_{scene['task'].hashcode}"
    suffix += f"_{task_name}"
    scene['task'].video_file = absolute_path(
        os.path.join(
            db[k_ep]['cache_path'],
            f"scenes_{scene['k_ed']}",
            f"{basename}{suffix}.mkv"
        )
    )

    # print(lightgreen("Consolidate scene:"))
    # print(lightcyan("================================== Scene ======================================="))
    # pprint(scene)
    # print(lightcyan("-------------------------------------------------------------------------------"))
    # sys.exit()


def consolidate_scene(scene: Scene, watermark: bool = False) -> None:
    """This procedure is used to simplify a single scene and add
    properties to process it: removes unecessary property, add
    paths to input/output files, update frames no. depending on edition, etc.

    edition_mode: used to not consolidate geometry/curves and remove replace/stabilize/deshake
    """
    verbose: bool = True
    if verbose:
        print(lightgreen("Consolidate scene:"))
        print(lightcyan("================================== Scene ======================================="))
        pprint(scene)
        print(lightcyan("-------------------------------------------------------------------------------"))

    # if scene['task'].name == 'initial':
    #     return _consolidate_for_initial(scene)

    # k_ed, k_ep and k_ch are the source keys for this scene
    # [dst][k_ep] and [dst][k_ch] are the destination (i.e. target)
    k_ep = scene['k_ep']
    k_ed = scene['k_ed']
    k_ch = scene['k_ch']

    # print(yellow("consolidate_scene: target: %s:%s" % (scene['dst']['k_ep'], scene['dst']['k_ch']))
    # pprint(scene)
    # print("--------------------------------------------------------------------")

    # Inputs
    scene['inputs'] = deepcopy(db[k_ep]['video'][k_ed][k_ch]['inputs'])
    scene['inputs']['progressive']['cache'] = db['common']['directories']['cache_progressive']

    # Cache directory

    scene['cache'] = get_cache_path(scene)
    # os.path.join(db['common']['directories']['cache'], k_ep, k_ch, "%03d" % (scene['no']))


    # Geometry
    #---------------------------------------------------------------------------
    if scene['task'].name != 'initial':
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
            if verbose:
                print("\t\t\tconsolidate_scene: get geometry for %s:%s:%s" % (k_ed, k_ep, k_ch))
            k_ed_src = scene['src']['k_ed']
            k_ep_src = scene['src']['k_ep']
            k_ch_src = scene['src']['k_ch']
            scene_no_src = scene['src']['no']

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
    primary_src_scene = scene['src'].primary_scene()

    # Get filters used by this scene: use the filters from the first src scene
    # all src scenes MUST have the same filters. Assume that's the case
    scene['filters'] = deepcopy(get_filters(primary_src_scene))

    # consolidate_scene_filters: add missing filters
    scene_filters = scene['filters']
    for t in TASK_NAMES:
        if t not in scene_filters:
            scene_filters[t] = Filter(task_name=t)

    # Deinterlace
    template_script: str = get_template_script(
        episode=primary_src_scene['scene']['k_ep'],
        edition=primary_src_scene['scene']['k_ed']
    )['scene']
    qtgmc_args: OrderedDict[str, str] = get_qtgmc_args(template_script)
    deint_hashcode, _ = calc_deint_hash(qtgmc_args)
    scene_filters['initial'].hash = deint_hashcode

    scene_filters['lr'].hash = deint_hashcode

    # Upscale
    upscale_hashcode = calc_hash(';'.join([deint_hashcode, scene_filters['upscale'].sequence]))
    scene_filters['upscale'].hash = upscale_hashcode

    # HR
    frame_replace = scene['src'].get_frame_replace()
    if len(frame_replace.keys()) != 0:
        hash = calc_hash(
            f"{upscale_hashcode};"
            + ','.join([f"{k}:{v}" for k, v in frame_replace.items()])
        )
    else:
        hash = upscale_hashcode
    scene_filters['hr'].hash = hash

    # Update the scene task
    scene['task'].hashcode = scene_filters[scene['task'].name].hash


    # Set the progressive filepath
    basename: str = path_split(scene['inputs']['interlaced']['filepath'])[1]
    filename: str = f"{basename}_{deint_hashcode}.mkv"
    progressive_fp: str = os.path.join(
        db['common']['directories']['cache_progressive'],
        filename
    )
    scene['inputs']['progressive']['filepath'] = progressive_fp

    task_name: str = scene['task'].name
    if task_name in ('initial', 'lr') and watermark:
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
    if task_name in ('initial', 'lr'):
        scene['in_frames'] = Images(scene)
        scene['out_frames'] = get_out_frame_paths(
            episode=k_ep,
            chapter=k_ch,
            scene=scene
        )

    elif task_name == 'hr':
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
    # print(lightcyan("==============================================================================="))
    # pprint(scene)
    # print(lightcyan("==============================================================================="))


    if verbose:
        print(lightcyan("TO"))
        pprint(scene)
        print(lightcyan("==============================================================================="))
        sys.exit()
