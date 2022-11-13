# -*- coding: utf-8 -*-
import sys
from collections import OrderedDict
from pprint import pprint

from utils.common import (
    K_GENERIQUES,
    get_k_part_from_frame_no,
    get_shot_from_frame,
)

FILTER_BASE_NO = {
    'deinterlace': 0,
    'pre_upscale': 100,
    'upscale': 200,
    'denoise': 300,
    'bgd': 400,
    'stitching': 500,
    'sharpen': 600,
    'rgb': 700,
    'geometry': 900,
}

# The following are used for debug purpose
FILTER_BASE_NO_DEBUG = {
    'deinterlace_rgb': 990,
    'upscale_rgb_geometry': 995,
}


def filter_id_to_step(filter_id:int):
    tmp = dict()
    for k, v in FILTER_BASE_NO.items():
        tmp[v] = k
    tmp_sorted = OrderedDict(sorted(tmp.items()))
    tmp_sorted_keys = list(tmp_sorted.keys())
    tmp_sorted_keys.append(999)
    for i in range(len(tmp_sorted_keys) - 1):
        if tmp_sorted_keys[i] <= filter_id < tmp_sorted_keys[i+1]:
            break
    # print("%d -> %s" % (filter_id, tmp[tmp_sorted_keys[i]]))
    return tmp[tmp_sorted_keys[i]]



def get_filters_generiques(db, frame, k_part):
    # print("%s.get_filters_generiques: %s: frame=" % (__name__, k_part), frame)
    k_ep = frame['k_ep']
    k_part_g = frame['k_part']
    k_ed = frame['k_ed']

    # Common for others
    if frame['filters'] == 'default':
        # print("\t-> defined in this frame, use default")
        filters = db[k_ep][k_ed]['filters'][k_part_g]
    elif not isinstance(frame['filters'], dict):
        filters = db[k_ep][k_ed]['filters']["%s.%s" % (k_part_g, frame['filters'])]
        # print("\t-> customized filter")
        # pprint(filters)
        # sys.exit("Error: %s: cannot consolidate frame due to the customized filter (%s) %s:%s:%s" % (__name__, frame['filters'], k_ed, k_ep, k_part_g))
    elif isinstance(frame['filters'], dict):
        # print("\t-> customized filter already defined in this frame")
        return frame['filters']
    else:
        # print("\t-> cannot find the filters, use default")
        filters = db[k_ep][k_ed]['filters'][k_part_g]

    return filters

    return None



def get_filters(database, frame, k_part=''):
    filters = None

    if k_part in K_GENERIQUES:
        return get_filters_generiques(database, frame, k_part)


    # Get shot from frame no.
    k_episode = frame['k_ep']
    k_ed = frame['k_ed']

    # For generique, do not used
    if k_part not in K_GENERIQUES and k_part == '':
        k_part = get_k_part_from_frame_no(database, k_ed, k_episode, frame['no'])

    if k_part in K_GENERIQUES:
        part = database[k_part][k_ed]
    else:
        # print("%s: part=%s" % (__name__, k_part))
        part = database[k_episode][k_ed][k_part]

    if 'shots' in part['video'].keys():
        print("Get associated filter for %s:%s" % (k_ed, k_part))
        # Get associated filter
        shot = get_shot_from_frame(database, k_ed, frame, k_part=k_part)
        # Now get filter name
        if shot['filters'] != 'default':
            # This shot does not use a default filter
            if k_part.startswith("g_"):
                # TODO: why? Replace 'filters' by 'k_filters'!
                k_filter = "default_%s" % (shot['filters'])
            else:
                k_filter = "%s_%s" % (k_part, shot['filters'])
        else:
            # This part uses a a default filter
            k_filter = 'default'
            if not k_part.startswith("g_"):
                k_filter = k_part

        # pprint(part)
        # if 'filters' in part.keys():
        #     # This part has a custom filter. TODO: redundant with part['filters'][part] ?
        #     filters = part['filters'][k_filter]
        # if k_part in part['filters'].keys():
        #         filters = part['filters'][k_part]
        # else:
        #     filters = part['filters']['default']
    else:
        # print("Use default filter:")
        # Shot is not defined, use the default filters
        # print("warning: shot is not found for frame no. %d" % (frame['no']))
        k_filter = 'default'

    if k_part in K_GENERIQUES:
        # Generique
        print("part=%s, edition=%s" % (k_part, k_ed))
        filters = database[k_part][k_ed]['filters'][k_part]
    else:
        # episode
        db_filters = database[k_episode][k_ed]['filters']
        if k_part in db_filters:
            filters = db_filters[k_part]
            # print("use default for part %s" % (k_part))
        else:
            filters = db_filters['default']
            # print("use default for episode no. %d" % (episode_no))

    # else:
    #     sys.exit("ERROR: no default filter defined for edition ['%s']/episode no. %d" % (k_ed, episode_no))
    return filters



def get_filters_from_shot(db, shot):
    k_ep = shot['k_ep']
    k_part = shot['k_part']
    edition = shot['k_ed']

    if shot['filters'] == 'default':
        filters = db[k_ep][edition]['filters'][k_part]
    elif not isinstance(shot['filters'], dict):
        filters = db[k_ep][edition]['filters']["%s.%s" % (k_part, shot['filters'])]
    elif isinstance(shot['filters'], dict):
        return shot['filters']
    else:
        filters = db[k_ep][edition]['filters'][k_part]

    return filters



def get_filter_id_generique(db, shot, k_step):
    k_ep = shot['k_ep']
    k_part = shot['k_part']
    edition = shot['k_ed']

    # print("%s.get_filter_id_generique: %s:%s:%s" % (__name__, edition, k_ep, k_part))

    # print("filter %s, %s, %s, %03d =" % (edition, k_ep, k_part, shot['no']))
    # print(type(filters))
    filters = shot['filters']
    if type(filters) is dict:
        # print(">> filter %s, %s, %s, %03d, %s =" % (edition, k_ep, k_part, shot['no'], k_step))
        # pprint(filters)
        filter_ids = filters['id']
    else:
        if 'shots' in db[k_part][edition]['video'].keys():
            filters = db[k_part][edition]['video']['shots'][shot['no']]['filters']
        elif k_part in K_GENERIQUES:
            filters = db[k_part][edition]['filters']
        else:
            filters = db[k_ep][edition][k_part]['video']['filters']

        if filters == 'default':
            filter_ids = db[k_part][edition]['filters'][filters]['id']
        elif type(filters) is dict:
            filter_ids = filters['id']
        else:
            print("filter %s, %s, %03d = %s" % (edition, k_part, shot['no'], filters))
            filter_ids = db[k_part][edition]['filters'][filters]['id']
            sys.exit("Error: TODO: %s: correct this" % (__name__))

    if k_step in filter_ids.keys():
        filter_id = filter_ids[k_step] + FILTER_BASE_NO[k_step]
    else:
        filter_id = FILTER_BASE_NO[k_step]

    return filter_id



def get_filter_id(db, shot, k_step):
    # print("%s.get_filter_id: " % (__name__), shot)

    # If this shot is already consolidated, it has the filter element
    filters = shot['filters']
    if type(filters) is dict:
        filter_ids = filters['id']

        if k_step in filter_ids.keys():
            filter_id = filter_ids[k_step] + FILTER_BASE_NO[k_step]
        elif k_step in FILTER_BASE_NO_DEBUG.keys():
            # For debug and verifications
            return FILTER_BASE_NO_DEBUG[k_step]
        else:
            filter_id = FILTER_BASE_NO[k_step]
        return filter_id

    k_ep = shot['k_ep']
    k_part = shot['k_part']
    edition = shot['k_ed']

    if 'filters' not in shot.keys():
        sys.exit("filters have not been consolidated for %s" % (shot['k_ep']))

    # print(type(filters))
    filters = shot['filters']
    if type(filters) is dict:
        # print(">> filter %s, %s, %s, %03d, %s =" % (edition, k_ep, k_part, shot['no'], k_step))
        # pprint(filters)
        filter_ids = filters['id']
    else:
        db_ep = db[k_ep][edition]
        db_video = db_ep[k_part]['video']

        if 'shots' in db_video.keys():
            filters = db_video['shots'][shot['no']]['filters']
        else:
            filters = db_video['filters']

        if filters == 'default':
            filter_ids = db_ep['filters'][k_part]['id']
        else:
            print("filter %s, %s, %s, %03d =" % (edition, k_ep, k_part, shot['no']), filters)
            filter_ids = db_ep['filters'][filters]['id']
            sys.exit("Error: TODO: %s: correct this" % (__name__))

    # For debug and verifications
    if k_step in FILTER_BASE_NO_DEBUG.keys():
        return FILTER_BASE_NO_DEBUG[k_step]

    if k_step in filter_ids.keys():
        filter_id = filter_ids[k_step] + FILTER_BASE_NO[k_step]
    elif k_step in FILTER_BASE_NO_DEBUG.keys():
        # For debug and verifications
        return FILTER_BASE_NO_DEBUG[k_step]
    else:
        filter_id = FILTER_BASE_NO[k_step]

    return filter_id