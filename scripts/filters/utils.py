# -*- coding: utf-8 -*-
import sys
from pprint import pprint
from utils.pretty_print import *

# Maximum nb of frames which can be loaded in memory
if sys.platform == 'win32':
    MAX_FRAMES_COUNT = 800
else:
    MAX_FRAMES_COUNT = 250

FILTER_TAGS = [
    'deinterlace',
    'pre_upscale',
    'upscale',
    'sharpen',
    'rgb',
    'geometry',
    'final'
]


def get_hash_from_task(shot, task):
    __task = 'geometry' if task == 'final' else task
    for f in shot['filters']:
        if __task == f['task']:
            return f['hash']

    pprint(shot['filters'])
    sys.exit(print_red("Error: get_hash_from_step: [%s] not found" % (task)))
    return None


def get_hash_from_last_task(shot):
    return get_hash_from_task(shot, shot['last_task'])


def get_step_no_from_task(shot, task):
    __task = 'geometry' if task == 'final' else task
    for f, i in zip(shot['filters'], range(len(shot['filters']))):
        if __task == f['task']:
            return i

    sys.exit(print_red("Error: get_step_no_from_task: [%s] not found" % (task)))
    return None


def get_step_no_from_last_task(shot):
    return get_step_no_from_task(shot, shot['last_task'])



def get_filters_from_shot(db, shot):
    k_ep = shot['k_ep']
    k_part = shot['k_part']
    k_ed = shot['k_ed']

    if shot['filters'] == 'default':
        # This shot uses default filters. Use the one defined in the part
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

    return filters


