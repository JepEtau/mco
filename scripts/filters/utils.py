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
    verbose = False
    k_ed = shot['k_ed']
    k_ep = shot['k_ep']
    k_part = shot['k_part']
    if verbose:
        print_lightgreen(f"get filters from shot: {k_ed}:{k_ep}:{k_part}, no. {shot['no']:03}, start: {shot['start']}")

    if shot['filters_id'] == 'default':
        if verbose:
            print_lightgrey(f"\tdefault filter")
            pprint(db[k_ep]['video'][k_ed][k_part]['filters'])

        # This shot uses default filters. Use the one defined in the part
        if 'filters' not in db[k_ep]['video'][k_ed][k_part].keys():
            sys.exit(print_red(f"Error: {k_ed}:{k_ep}:{k_part}: no available filters"))

        try:
            filters = db[k_ep]['video'][k_ed][k_part]['filters']['default']
        except:
            print_red(f"Error: default filter is not defined but required by {k_ed}:{k_ep}:{k_part}, no. {shot['no']:03}")
            pprint(shot)
            sys.exit()

    elif isinstance(shot['filters_id'], str):
        if verbose:
            print_lightgrey(f"\tcustom filter: {shot['filters']}")

        # This shot uses a custom filter defined in the 'filters' struct in this part
        try:
            filters = db[k_ep]['video'][k_ed][k_part]['filters'][shot['filters_id']]
        except:
            print_red(f"Error: {k_ed}:{k_ep}:{k_part}, no. {shot['no']:03}, filter {shot['filters']} not found")
            print_red(f"\tdefined filters: {list(db[k_ep]['video'][k_ed][k_part]['filters'].keys())}")
            print_orange(f"\tfallback: using default")
            filters = db[k_ep]['video'][k_ed][k_part]['filters']['default']
    else:
        # This shot may default filters, but to be validated
        print_red(f"Error: no filters defined for {k_ed}:{k_ep}:{k_part}, no. {shot['no']:03}")
        sys.exit()

    return deepcopy(filters)



def get_dimensions_from_crop_values(width, height, crop) -> list:
    c_t, c_b, c_l, c_r = crop
    c_w = width - (c_l + c_r)
    c_h = height - (c_t + c_b)
    return [c_t, c_b, c_l, c_r, c_w, c_h]



def has_add_border_task(shot):
    # Returns true if borders have been added
    for f in shot['filters'][STEP_INC:]:
        if f['str'] == 'add_borders':
            return True
    return False



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