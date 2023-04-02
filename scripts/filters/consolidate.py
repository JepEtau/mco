# -*- coding: utf-8 -*-
import sys
from pprint import pprint
from utils.pretty_print import *
from filters.utils import (
    MAX_FRAMES_COUNT,
    STEP_INC
)



def consolidate_filters(shot):

    # Insert replace at the right place
    # for step_no in range(len(shot['filters']), -1, -1):
    is_inserted = False
    replace_filter = {
        'type': 'python',
        'save': False,
        'str': 'replace',
        'task': 'replace',
    }
    for step_no in range(len(shot['filters'])):
        filter_str = shot['filters'][step_no]['str']
        if ('hqdn3d' in filter_str
        or 'deshake' in filter_str
        or 'stabilize' in filter_str):
            # Insert before temporal filter
            shot['filters'].insert(step_no, replace_filter)
            # print_green("replace filter: inserted at position %d" % (step_no))
            is_inserted = True
            break
    if not is_inserted:
        shot['filters'][-1]['task'] = 'sharpen'
        shot['filters'].append(replace_filter)
        # print_green("replace filter: append")


    # Force saving: deinterlace
    shot['filters'][0]['save'] = True
    shot['filters'][-1]['save'] = True


    # Associate task to filter
    for i in range(len(shot['filters'])):
        filter = shot['filters'][i]
        # Previous filter
        previous_filter = shot['filters'][i-1] if i>=1 else None

        if 'task' not in filter.keys():
            filter['task'] = ''

        # Deinterlace
        if i == 0:
            filter['task'] = 'deinterlace'

        # Upscale
        elif 'scale' in filter['str']:
            filter['task'] = 'upscale'
            if previous_filter['task'] == '':
                previous_filter['task'] = 'pre_upscale'

        elif filter['type'] in ['real_cugan', 'real_esrgan', 'esrgan']:
            if '1x' in filter['str']:
                # denoise/sharpen/other
                filter['task'] = ''
            else:
                filter['task'] = 'upscale'
                if previous_filter['task'] == '':
                    previous_filter['task'] = 'pre_upscale'


        elif filter['task'] == 'replace':
            if previous_filter['task'] == '' and i > STEP_INC:
                # Previous is undefined and is not 'deinterlace'
                previous_filter['task'] = 'sharpen'


        # Force saving if too many frames
        if shot['count'] >= MAX_FRAMES_COUNT:
            filter['save'] = True

    # Set task for last filter if not set
    previous_filter = shot['filters'][-1]
    if previous_filter['task'] == '':
        # Remove all sharpen tasks
        for filter in shot['filters']:
            if filter['task'] == 'sharpen':
                filter['task'] = ''
        previous_filter['task'] = 'sharpen'

    # Append RGB curves
    shot['filters'].append({
        'type': 'python',
        'save': False,
        'str': 'rgb',
        'task': 'rgb'
    })

    # Append geometry
    shot['filters'].append({
        'type': 'python',
        'save': True,
        'str': 'geometry',
        'task': 'geometry'
    })

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



    # Force saving last task
    if 'last_task' in shot.keys():
        # when not in video edition
        for filter in shot['filters']:
            if filter['task'] == shot['last_task']:
                filter['save'] = True
                break

