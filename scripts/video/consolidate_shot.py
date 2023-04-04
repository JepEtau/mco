# -*- coding: utf-8 -*-
import sys
import os
from copy import deepcopy
from pprint import pprint

from filters.apply_filters import apply_filters
from filters.consolidate import consolidate_filters
from filters.utils import (
    get_filters_from_shot,
    get_step_no_from_last_task,
)
from utils.hash import (
    calculate_hash,
    create_hash_file,
    get_hash_from_last_task,
)
from utils.common import (
    K_GENERIQUES,
    nested_dict_set,
)
from utils.get_curves import get_lut_from_curves
from utils.path import get_cache_path
from utils.pretty_print import *




def consolidate_shot(db, shot) -> None:
    """This procedure is used to simplify a single shot and add
    properties to process it: removes unecessary property, add
    paths to input/output files, update frames no. depending on edition, etc.

    Args:
        db: the global database
        shot: a single shot to consolidate

    Returns:
        None

    """
    # k_ed, k_ep and k_part are the source keys for this shot
    # [dst][k_ep] and [dst][k_part] are the destination (i.e. target)
    k_ep = shot['k_ep']
    k_ed = shot['k_ed']
    k_part = shot['k_part']

    print_yellow("consolidate_shot: target: %s:%s" % (shot['dst']['k_ep'], shot['dst']['k_part']))
    # pprint(shot)
    # print("--------------------------------------------------------------------")

    # Input
    shot['input'] = db['editions'][k_ed]['inputs']['video'][k_ep]

    # Cache directory

    shot['cache'] = get_cache_path(db, shot)
    # os.path.join(db['common']['directories']['cache'], k_ep, k_part, "%03d" % (shot['no']))


    if False:
        # Frame ref is used for deinterlace, calculate it: use the offset array
        shot['ref'] = shot['start']
        if k_part in K_GENERIQUES:
            k_ep_target = db[k_part]['video']['src']['k_ep']
            # k_ed_ref = db[k_ep]['target']['video']['k_ed_ref']
            k_ed_ref = k_ed
        else:
            # pprint(db[k_ep]['target']['video'])
            # pprint(shot)
            # k_ed_target = db[k_ep]['target']['video']['src']['k_ed']
            try:
                k_ed_ref = db[k_ep]['video']['target']['k_ed_ref']
                # if shot['k_ep'] != shot['dst']['k_ep']:
                k_ep_target = shot['dst']['k_ep']
            except:
                # study mode
                k_ed_ref = k_ed
                k_ep_target = k_ep


        if ((k_ed != k_ed_ref or k_ep != k_ep_target)
            and k_part == shot['dst']['k_part']):
            # Apply offset only if part is different:
            # when replacing episode<->asuivre or episode<->precedemment or asuivre <-> precedemment
            print("\t\t\tapply offset for %s: target:%s:%s:%s ref:%s:%s:%s" % (
                k_part,
                k_ed, k_ep_target, shot['dst']['k_part'],
                k_ed_ref, k_ep, k_part))
            try:
                offsets = db[k_ep]['video'][k_ed][k_part]['offsets']
                # print("%s:%s:%s, offsets=" % (k_ed_src, k_ep, k_part), offsets)
                for offset in offsets:
                    if offset['start'] <= shot['start'] <= offset['end']:
                        # shot['ref'] = shot['start'] + offset['offset']
                        shot['start'] = shot['start'] - offset['offset']
                        break
            except:
                print("offsets are not defined in %s:%s for part %s" % (k_ed, k_ep, k_part))
        # else:
        #     print("\t\t\tdisable offset for %s" % (k_part))



    # Geometry
    #---------------------------------------------------------------------------
    print("consolidate_shot: get geometry for %s:%s:%s" % (k_ed, k_ep, k_part))
    if k_part in ['g_asuivre', 'g_reportage']:
            # pprint(shot)
            # print("-------------------------")
            # pprint(db[k_ep]['video'][k_ed][k_part])
            # print("-------------------------")
            # pprint(db[k_part]['video'])
            k_ep_dst = shot['dst']['k_ep']
            k_ep_src = shot['k_ep']
            k_ed_src = shot['k_ed']

            # if 'video' in db[k_part]['video']['common'].keys():
            #     k_ed_dst = db[k_part]['video']['common']['reference']['k_ed']
                # print("get geometry from part %s:%s:%s for %s:%s:%s" % (
                #     k_ed, k_ep, k_part[2:], k_ed_src, k_ep_dst, k_part))
                # pprint(db[k_ep_dst])
            try:
                shot['geometry'] = {
                    'part': db[k_ep_dst]['video'][k_ed][k_part[2:]]['geometry'],
                    'shot': db[k_ep]['video'][k_ed][k_part]['geometry'],
                }
            except:
                print_yellow("undefined geometry: %s" % (k_part))
            # else:
            #     print("warning: no geometry/video defined in %s for %s:%s:%s" % (k_part, k_ed_src, k_ep_dst, k_part))

    else:
        k_ed_src = shot['src']['k_ed']
        k_ep_src = shot['src']['k_ep']
        k_part_src = shot['src']['k_part']
        shot_no_src = shot['src']['no']

        try:
            if k_part in ['g_debut', 'g_fin']:
                target_geometry = db[k_part]['target']['video']['geometry']
            else:
                target_geometry = db[k_ep]['video']['target']['geometry']
        except:
            target_geometry = None
        nested_dict_set(shot, target_geometry, 'geometry', 'part')

        try:
            default_shot_src_geometry = db[k_ep_src]['video'][k_ed_src][k_part_src]['geometry']
        except:
            default_shot_src_geometry = {
                'keep_ratio': True,
                'fit_to_part': False,
                'crop': [0] * 4,
                'is_default': True,
            }

        try:
            shot_src_geometry = db[k_ep_src]['video'][k_ed_src][k_part_src]['shots'][shot_no_src]['geometry']['shot']
        except:
            shot_src_geometry = None

        if shot_src_geometry is not None:
            nested_dict_set(shot, shot_src_geometry, 'geometry', 'shot')
            shot['geometry']['shot']['is_default'] = False
        else:
            nested_dict_set(shot, default_shot_src_geometry, 'geometry', 'shot')
            try: shot['geometry']['shot']['is_default'] = True
            except: pass

    nested_dict_set(shot,
        db['common']['dimensions']['final'],
        'geometry', 'dimensions', 'final')



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
        if filter['task'] in ['replace', 'pre_replace']:
            shot['last_step']['step_no_replace'] = step_no
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
