from copy import deepcopy
import os
from pprint import pprint
from typing import OrderedDict
from processing.deint import calc_deint_hash, get_qtgmc_args, get_template_script
from utils.hash import calc_hash
from utils.mco_types import Effect, Effects, Scene
from parsers import (
    db,
    Filter,
    TASK_NAMES,
    ProcessingTask,
)
from utils.mco_utils import get_cache_path, nested_dict_set
from utils.p_print import *
from utils.path_utils import absolute_path, path_split
from video.frame_list import get_frame_list
from video.out_frame_list import get_out_frame_list, get_out_frame_list_single
from .filters import get_filters


def _consolidate_for_initial(scene: Scene) -> None:
    k_ep = scene['k_ep']
    k_ed = scene['k_ed']
    k_ch = scene['k_ch']

    scene['filters'] = deepcopy(get_filters(scene))

    # consolidate_scene_filters
    scene_filters = scene['filters']

    # Add missing filters
    for t in TASK_NAMES:
        if t not in scene_filters:
            scene_filters[t] = Filter(task_name=t)

    # Deinterlace
    template_script: str = get_template_script(
        episode=scene['src']['k_ep'],
        edition=scene['src']['k_ed']
    )
    qtgmc_args: OrderedDict[str, str] = get_qtgmc_args(template_script)
    deint_hashcode, _ = calc_deint_hash(qtgmc_args)
    scene_filters['initial'].hash = deint_hashcode

    # Update the scene task
    scene['task'].hashcode = scene_filters[scene['task'].name].hash

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






def consolidate_scene(scene: Scene, watermark: bool = False) -> None:
    """This procedure is used to simplify a single scene and add
    properties to process it: removes unecessary property, add
    paths to input/output files, update frames no. depending on edition, etc.

    edition_mode: used to not consolidate geometry/curves and remove replace/stabilize/deshake
    """
    verbose = False
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

    # Get filters used by this scene
    scene['filters'] = deepcopy(get_filters(scene))

    # consolidate_scene_filters
    scene_filters = scene['filters']

    # Add missing filters
    for t in TASK_NAMES:
        if t not in scene_filters:
            scene_filters[t] = Filter(task_name=t)

    # Deinterlace
    template_script: str = get_template_script(
        episode=scene['src']['k_ep'],
        edition=scene['src']['k_ed']
    )
    qtgmc_args: OrderedDict[str, str] = get_qtgmc_args(template_script)
    deint_hashcode, _ = calc_deint_hash(qtgmc_args)
    scene_filters['initial'].hash = deint_hashcode

    scene_filters['lr'].hash = deint_hashcode

    upscale_hashcode = calc_hash(';'.join([deint_hashcode, scene_filters['hr'].sequence]))
    scene_filters['hr'].hash = upscale_hashcode

    # Update the scene task
    scene['task'].hashcode = scene_filters[scene['task'].name].hash

    if False:
        # Consolidate filters: add rgb/geometry, identify tasks
        consolidate_tasks(scene)

        # Update filters: add hash for each filter
        hash_log_file = create_hash_file(db, scene['k_ep'])
        scene['hash_log_file'] = hash_log_file

        hashes = process_chain_list(db=db, scene=scene, get_hashes=True)
        for hash, filter in zip(hashes, scene['filters']):
            filter['hash'] = hash[1]

        scene['last_step'] = {
            'hash': get_hash_from_last_task(scene),
            'step_no': get_step_no_from_last_task(scene),
        }

    # Find replace filter
    # pprint(scene['filters'])
    # if scene['filters'] is not None:
    #     for step_no, filter in enumerate(scene['filters']):
    #         if filter['task'] in ['replace', 'edition']:
    #             scene['last_step']['step_edition'] = step_no
    #             break

    # print(cyan("Filters: %s:%s:%s, scene no. %d" % (scene['k_ed'], scene['k_ep'], scene['k_ch'], scene['no']))
    # for f in scene['filters']:
    #     print("\t", end='')
    #     print(green(f['task'], end='\t\t')
    #     if f['task'] == '':
    #         print('\t', end='')
    #     print(green(f['str'])
    # print(green(scene['last_step'])
    # sys.exit()

    # Set the progressive filepath
    basename: str = path_split(scene['inputs']['interlaced']['filepath'])[1]
    filename: str = f"{basename}_{deint_hashcode}.mkv"
    progressive_fp: str = os.path.join(
        db['common']['directories']['cache_progressive'],
        filename
    )
    scene['inputs']['progressive']['filepath'] = progressive_fp

    if scene['task'].name == 'lr' and watermark:
        # if 'effects' in scene:
        #     scene['effects'] = Effects()
        # scene['effects'].append(Effect(name='watermark'))
        sequence: str = scene['filters']['lr'].sequence
        scene['filters']['lr'].sequence = (
            f"{sequence};watermark"
            if sequence
            else "watermark"
        )

    # List frames
    if scene['task'].name == 'lr':
        scene['in_frames'] = get_frame_list(scene, out=False)
        if k_ch in ('g_asuivre', 'g_documentaire'):
            scene['out_frames'] = get_out_frame_list_single(
                episode=k_ep,
                chapter=k_ch,
                scene=scene
            )

        else:
            scene['out_frames'] = get_out_frame_list(
                episode=k_ep,
                chapter=k_ch,
                scene=scene
            )

    elif scene['task'].name == 'hr':

        frames = get_frame_list(scene, replace=True, out=False)
        scene['in_frames'] = list(OrderedDict.fromkeys(frames))

        if k_ch in ('g_asuivre', 'g_documentaire'):
            scene['out_frames'] = get_out_frame_list_single(
                episode=k_ep,
                chapter=k_ch,
                scene=scene
            )

        else:
            scene['out_frames'] = get_out_frame_list(
                episode=k_ep,
                chapter=k_ch,
                scene=scene
            )



        # print(lightcyan("==============================================================================="))
        # pprint(scene)
        # print(lightcyan("==============================================================================="))


    if verbose:
        print(lightcyan("TO"))
        pprint(scene)
        print(lightcyan("==============================================================================="))
        # sys.exit()
