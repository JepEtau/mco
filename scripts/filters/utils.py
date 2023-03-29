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



def consolidate_filters(shot):

    # Append RGB curves
    if (shot['last_task'] == 'final'
        or shot['last_task'] == 'rgb'):
        shot['filters'].append({
            'type': 'python',
            'save': True,
            'str': 'rgb'
        })

    # Append geometry if exists (i.e.crop)
    if (shot['last_task'] == 'final'
        or shot['last_task'] == 'geometry'):
        if 'geometry' in shot.keys():
            shot['filters'].append({
                'type': 'python',
                'save': True,
                'str': 'geometry',
            })

    # Force saving: deinterlace and last step
    shot['filters'][0]['save'] = True
    shot['filters'][-1]['save'] = True

    # Associate task to filter
    for i in range(len(shot['filters'])):
        filter = shot['filters'][i]

        # Deinterlace
        if i == 0:
            filter['task'] = 'deinterlace'

        # Upscale
        elif 'scale' in filter['str']:
            filter['task'] = 'upscale'
            if shot['filters'][i-1]['task'] == '':
                shot['filters'][i-1]['task'] = 'pre_upscale'

        elif filter['type'] in ['real_cugan', 'real_esrgan', 'esrgan']:
            if '1x' in filter['str']:
                # denoise/sharpen/other
                filter['task'] = ''
            else:
                filter['task'] = 'upscale'
                if shot['filters'][i-1]['task'] == '':
                    shot['filters'][i-1]['task'] = 'pre_upscale'

        # RGB curves
        elif 'rgb' in filter['str']:
            if shot['filters'][i-1]['task'] == '':
                shot['filters'][i-1]['task'] = 'sharpen'
            filter['task'] = 'rgb'

        # Geometry
        elif 'geometry' in filter['str']:
            filter['task'] = 'geometry'

        # Default: no task
        else:
            filter['task'] = ''

        # Force saving if too many frames
        if shot['count'] >= MAX_FRAMES_COUNT:
            filter['save'] = True


    # Force saving last task
    for filter in shot['filters']:
        if filter['task'] == shot['last_task']:
           filter['save'] = True
           break


    # If last task does not have a tag, this means that it is
    # the end of sharpening
    if shot['filters'][-1]['task'] == '':
        shot['filters'][-1]['task'] = 'sharpen'


    # Deshake & stabilization: do not add pad if more than 1 time
    deshake_stab_count = 0
    for filter in shot['filters']:
        if (filter['str'].startswith('deshake')
            or filter['str'].startswith('stabilize')
            or filter['str'].startswith('homography')):

            deshake_stab_count += 1
            if deshake_stab_count > 1:
                filter['str'] += "=no_border"




