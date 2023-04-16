# -*- coding: utf-8 -*-
import sys
from pprint import pprint
from utils.pretty_print import *
from copy import deepcopy
import platform


FINAL_FRAME_WIDTH = 1440
FINAL_FRAME_HEIGHT = 1080
STEP_INC = 1

# Maximum nb of frames which can be loaded in memory
if platform.system() == "Windows":
    MAX_FRAMES_COUNT = 800
else:
    MAX_FRAMES_COUNT = 250

FILTER_TAGS = [
    'deinterlace',
    'replace',
    'pre_upscale',
    'upscale',
    'sharpen',
    'edition',
    'rgb',
    'geometry',
    'final'
]




def get_step_no_from_task(shot, task):
    __task = 'geometry' if task == 'final' else task
    for f, i in zip(shot['filters'], range(len(shot['filters']))):
        if __task == f['task']:
            return i

    print_red("Error: get_step_no_from_task: [%s] not found" % (task))
    return None


def get_step_no_from_last_task(shot):
    return get_step_no_from_task(shot, shot['last_task'])



def get_filters_from_shot(db, shot):
    k_ed = shot['k_ed']
    k_ep = shot['k_ep']
    k_part = shot['k_part']

    if shot['filters'] == 'default':
        # This shot uses default filters. Use the one defined in the part
        if 'filters' not in db[k_ep]['video'][k_ed][k_part].keys():
            sys.exit(print_red("Error: no default filter defined: %s:%s:%s" %
                (k_ed, k_ep, k_part)))
        filters = db[k_ep]['video'][k_ed][k_part]['filters']['default']

    elif not isinstance(shot['filters'], dict):
        # This shot uses a custom filter defined in the 'filters' struct in this part
        filters = db[k_ep]['video'][k_ed][k_part]['filters']["%s.%s" % (k_part, shot['filters'])]

    elif isinstance(shot['filters'], dict):
        # The filters are defined in the shot structure
        return shot['filters']

    else:
        # This shot may default filters, but to be validated
        print("no filters defined for %s:%s:%s no.%d" % (k_ed, k_ep, k_part, shot['no']))
        filters = db[k_ep]['video'][k_ed][k_part]['filters']['default']
        sys.exit()

    return deepcopy(filters)



def get_dimensions_from_crop_values(width, height, crop) -> list:
    c_t, c_b, c_l, c_r = crop
    c_w = width - (c_l + c_r)
    c_h = height - (c_t + c_b)
    return [c_t, c_b, c_l, c_r, c_w, c_h]




def is_stabilize_task_enabled(shot):
    # Returns true if deshake/stabilize task is enabled, False otherwise

    # No deshake parameters or disabled
    if ('deshake' not in shot.keys()
        or shot['deshake'] is None
        or not shot['deshake']['enable']):
        return False

    # Is deshake/stablize task is in list of filters
    for f in shot['filters']:
        if f['task'] in ['deshake', 'stabilize']:
            return True

    return False