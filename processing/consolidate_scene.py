import sys
import os
from copy import deepcopy
from pprint import pprint

# from processing_chain.process_chain import process_chain_list
# from processing_chain.consolidate import consolidate_tasks

# from img_toolbox.utils import (
#     get_processing_chain,
#     get_step_no_from_last_task,
# )
# from processing_chain.hash import (
#     calculate_hash,
#     create_hash_file,
#     get_hash_from_last_task,
# )

from parsers import nested_dict_set
from utils.mco_types import Scene
from utils.path import get_cache_path
from utils.p_print import *


def consolidate_scene(db, scene: Scene, edition_mode: bool = False) -> None:
    """This procedure is used to simplify a single scene and add
    properties to process it: removes unecessary property, add
    paths to input/output files, update frames no. depending on edition, etc.

    edition_mode: used to not consolidate geometry/curves and remove replace/stabilize/deshake

    Args:
        db: the global database
        scene: a single scene to consolidate

    Returns:
        None

    """
    verbose = False
    if verbose:
        print(lightgreen("Consolidate scene:"))
        print(lightcyan("================================== scene ======================================="))
        pprint(scene)
        print(lightcyan("-------------------------------------------------------------------------------"))


    # k_ed, k_ep and k_part are the source keys for this scene
    # [dst][k_ep] and [dst][k_part] are the destination (i.e. target)
    k_ep = scene['k_ep']
    k_ed = scene['k_ed']
    k_part = scene['k_part']

    # print(yellow("consolidate_scene: target: %s:%s" % (scene['dst']['k_ep'], scene['dst']['k_part'])))
    # pprint(scene)
    # print("--------------------------------------------------------------------")

    # Inputs
    scene['inputs'] = deepcopy(db[k_ep]['video'][k_ed][k_part]['inputs'])
    scene['inputs']['progressive']['cache'] = db['common']['directories']['cache_progressive']

    # Cache directory

    scene['cache'] = get_cache_path(db, scene)
    # os.path.join(db['common']['directories']['cache'], k_ep, k_part, "%03d" % (scene['no']))


    # Geometry
    #---------------------------------------------------------------------------
    if k_part in ['g_asuivre', 'g_documentaire']:
        # print("\t\t\tconsolidate_scene: get geometry from %s:%s:%s" % (k_ed, k_ep, k_part[2:]))
        k_ep_dst = scene['dst']['k_ep']
        try:
            target_geometry = db[k_ep_dst]['video']['target'][k_part[2:]]['geometry']['target']
        except:
            target_geometry = None
        nested_dict_set(scene, target_geometry, 'geometry', 'target')

        try:
            scene_geometry = db[k_ep]['video'][k_ed][k_part]['geometry']
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
        # print("\t\t\tconsolidate_scene: get geometry for %s:%s:%s" % (k_ed, k_ep, k_part))
        k_ed_src = scene['src']['k_ed']
        k_ep_src = scene['src']['k_ep']
        k_part_src = scene['src']['k_part']
        scene_no_src = scene['src']['no']

        # Target geometry: width defined
        try:
            if k_part in ['g_debut', 'g_fin']:
                target_geometry = db[k_part]['video']['geometry']['target']
            else:
                target_geometry = db[k_ep]['video']['target'][k_part]['geometry']['target']
        except:
            target_geometry = None
        nested_dict_set(scene, target_geometry, 'geometry', 'target')

        # Get default geometry for a scene
        try:
            default_scene_src_geometry = db[k_ep_src]['video'][k_ed_src][k_part_src]['geometry']
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
            scene_src_geometry = db[k_ep_src]['video'][k_ed_src][k_part_src]['scenes'][scene_no_src]['geometry']['scene']
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



    # Filters
    #---------------------------------------------------------------------------

    # Get filters used by this scene
    # scene['filters'] = get_processing_chain(db, scene)

    # Consolidate filters: add rgb/geometry, identify tasks
    # consolidate_tasks(scene)

    # Update filters: add hash for each filter
    # hash_log_file = create_hash_file(db, scene['k_ep'])
    # scene['hash_log_file'] = hash_log_file

    # hashes = process_chain_list(db=db, scene=scene, get_hashes=True)
    # for hash, filter in zip(hashes, scene['filters']):
    #     filter['hash'] = hash[1]

    # scene['last_step'] = {
    #     'hash': get_hash_from_last_task(scene),
    #     'step_no': get_step_no_from_last_task(scene),
    # }

    # Find replace filter
    for step_no, filter in zip(range(len(scene['filters'])), scene['filters']):
        if filter['task'] in ['replace', 'edition']:
            scene['last_step']['step_edition'] = step_no
            break

    # print(cyan("Filters: %s:%s:%s, scene no. %d" % (scene['k_ed'], scene['k_ep'], scene['k_part'], scene['no'])))
    # for f in scene['filters']:
    #     print("\t", end='')
    #     print(green(f['task'], end='\t\t'))
    #     if f['task'] == '':
    #         print('\t', end='')
    #     print(green(f['str']))
    # print(green(scene['last_step']))
    # sys.exit()



    # consolidate the FFv1 filepath
    filename: str = os.path.split(scene['inputs']['interlaced']['filepath'])[1]
    filename = filename.replace('.mkv', "_%s.mkv" % (scene['filters'][0]['hash']))
    scene['inputs']['progressive']['filepath'] = os.path.join(
        db['common']['directories']['cache_progressive'], filename
    )


    # Remove keys which shall not be used by video editor
    if edition_mode:
        # for k in ['replace', 'deshake', 'geometry', 'curves']:
        for k in ['replace', 'deshake']:
            try:
                scene[k].clear()
            except:
                pass
        try: scene['curves']['lut'].clear()
        except: pass



    if verbose:
        print(lightcyan("TO"))
        pprint(scene)
        print(lightcyan("==============================================================================="))
        # sys.exit()
