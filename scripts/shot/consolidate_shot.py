# -*- coding: utf-8 -*-
import sys
import os
from copy import deepcopy
from pprint import pprint

from filters.apply_filters import apply_filters
from filters.consolidate import consolidate_filters
from filters import IMG_BORDER_HIGH_RES
from filters.utils import (
    get_filters_from_shot,
    get_step_no_from_last_task,
    has_add_border_task,
)
from utils.hash import (
    calculate_hash,
    create_hash_file,
    get_hash_from_last_task,
)
from utils.common import (
    K_GENERIQUES,
)
from utils.nested_dict import nested_dict_set
from utils.get_curves import get_lut_from_curves
from utils.path import get_cache_path
from utils.pretty_print import *




def consolidate_shot(db, shot, edition_mode:bool=False) -> None:
    """This procedure is used to simplify a single shot and add
    properties to process it: removes unecessary property, add
    paths to input/output files, update frames no. depending on edition, etc.

    edition_mode: used to not consolidate geometry/curves and remove replace/stabilize/deshake

    Args:
        db: the global database
        shot: a single shot to consolidate

    Returns:
        None

    """
    verbose = False
    if verbose:
        print_lightgreen("Consolidate shot:")
        print_lightcyan("================================== SHOT =======================================")
        pprint(shot)
        print_lightcyan("-------------------------------------------------------------------------------")


    # k_ed, k_ep and k_part are the source keys for this shot
    # [dst][k_ep] and [dst][k_part] are the destination (i.e. target)
    k_ep = shot['k_ep']
    k_ed = shot['k_ed']
    k_part = shot['k_part']

    # print_yellow("consolidate_shot: target: %s:%s" % (shot['dst']['k_ep'], shot['dst']['k_part']))
    # pprint(shot)
    # print("--------------------------------------------------------------------")

    # Inputs
    shot['inputs'] = deepcopy(db[k_ep]['video'][k_ed][k_part]['inputs'])
    shot['inputs']['progressive']['cache'] = db['common']['directories']['cache_progressive']

    # Cache directory

    shot['cache'] = get_cache_path(db, shot)
    # os.path.join(db['common']['directories']['cache'], k_ep, k_part, "%03d" % (shot['no']))


    # Geometry
    #---------------------------------------------------------------------------
    if k_part in ['g_asuivre', 'g_reportage']:
        # print("\t\t\tconsolidate_shot: get geometry from %s:%s:%s" % (k_ed, k_ep, k_part[2:]))
        k_ep_dst = shot['dst']['k_ep']
        try:
            target_geometry = db[k_ep_dst]['video']['target'][k_part[2:]]['geometry']['target']
        except:
            target_geometry = None
        nested_dict_set(shot, target_geometry, 'geometry', 'target')

        try:
            shot_geometry = db[k_ep]['video'][k_ed][k_part]['geometry']
            shot_geometry['is_default'] = False
        except:
            shot_geometry = {
                'keep_ratio': True,
                'fit_to_width': False,
                'crop': [0] * 4,
                'is_default': False,
            }
        nested_dict_set(shot, shot_geometry, 'geometry', 'shot')

    else:
        # print("\t\t\tconsolidate_shot: get geometry for %s:%s:%s" % (k_ed, k_ep, k_part))
        k_ed_src = shot['src']['k_ed']
        k_ep_src = shot['src']['k_ep']
        k_part_src = shot['src']['k_part']
        shot_no_src = shot['src']['no']

        # Target geometry: width defined
        try:
            if k_part in ['g_debut', 'g_fin']:
                target_geometry = db[k_part]['video']['geometry']['target']
            else:
                target_geometry = db[k_ep]['video']['target'][k_part]['geometry']['target']
        except:
            target_geometry = None
        nested_dict_set(shot, target_geometry, 'geometry', 'target')

        # Get default geometry for a shot
        try:
            default_shot_src_geometry = db[k_ep_src]['video'][k_ed_src][k_part_src]['geometry']
            default_shot_src_geometry['is_default'] = True
        except:
            default_shot_src_geometry = {
                'keep_ratio': True,
                'fit_to_width': False,
                'crop': [0] * 4,
                'is_default': True
            }

        # Get the customized geometry for a shot
        try:
            shot_src_geometry = db[k_ep_src]['video'][k_ed_src][k_part_src]['shots'][shot_no_src]['geometry']['shot']
            shot_src_geometry['is_default'] = False
        except:
            shot_src_geometry = None

        if shot_src_geometry is not None:
            # Use the customized
            nested_dict_set(shot, shot_src_geometry, 'geometry', 'shot')
            shot['geometry']['shot']['is_default'] = False
        else:
            # Use the default because no customized defined
            nested_dict_set(shot, default_shot_src_geometry, 'geometry', 'shot')
            try: shot['geometry']['shot']['is_default'] = True
            except: pass


    # RGB correction: calculate the lut from the curves
    #---------------------------------------------------------------------------
    if shot['curves'] is not None:
        shot['curves']['lut'], curves_points_str = get_lut_from_curves(db,
            k_ed,
            k_ep,
            k_part,
            shot['curves']['k_curves'])
        shot['curves']['hash'] = calculate_hash(curves_points_str)

    # Filters
    #---------------------------------------------------------------------------

    # Get filters used by this shot
    shot['filters'] = get_filters_from_shot(db, shot)

    # Consolidate filters: add rgb/geometry, identify tasks
    consolidate_filters(shot)

    # Update filters: add hash for each filter
    hash_log_file = create_hash_file(db, shot['k_ep'])
    shot['hash_log_file'] = hash_log_file

    hashes = apply_filters(db=db, shot=shot, get_hashes=True)
    for hash, filter in zip(hashes, shot['filters']):
        filter['hash'] = hash[1]

    shot['last_step'] = {
        'hash': get_hash_from_last_task(shot),
        'step_no': get_step_no_from_last_task(shot),
    }

    # Find replace filter
    for step_no, filter in zip(range(len(shot['filters'])), shot['filters']):
        if filter['task'] in ['replace', 'edition']:
            shot['last_step']['step_edition'] = step_no
            break

    # print_cyan("Filters: %s:%s:%s, shot no. %d" % (shot['k_ed'], shot['k_ep'], shot['k_part'], shot['no']))
    # for f in shot['filters']:
    #     print("\t", end='')
    #     print_green(f['task'], end='\t\t')
    #     if f['task'] == '':
    #         print('\t', end='')
    #     print_green(f['str'])
    # print_green(shot['last_step'])
    # sys.exit()



    # consolidate the FFv1 filepath
    filename = os.path.split(shot['inputs']['interlaced']['filepath'])[1]
    filename = filename.replace('.mkv', "_%s.mkv" % (shot['filters'][0]['hash']))
    shot['inputs']['progressive']['filepath'] = os.path.join(
        db['common']['directories']['cache_progressive'], filename)


    # Remove keys which shall not be used by video editor
    if edition_mode:
        # for k in ['replace', 'deshake', 'geometry', 'curves']:
        for k in ['replace', 'deshake']:
            try:
                shot[k].clear()
            except:
                pass
        try: shot['curves']['lut'].clear()
        except: pass



    if verbose:
        print_lightcyan("TO")
        pprint(shot)
        print_lightcyan("===============================================================================")
        # sys.exit()
