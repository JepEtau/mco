# -*- coding: utf-8 -*-
import sys
from pprint import pprint
from utils.pretty_print import *
from img_toolbox.utils import (
    MAX_FRAMES_COUNT,
    STEP_INC
)



def consolidate_tasks(shot):
    # Deshake & stabilization: do not add pad if more than 1 time

    # Add borders even if no deshake/stabilize to simplify
    # !!! Except for documentaire
    if shot['k_part'] != 'documentaire':
        add_borders_filter = {
            'type': 'python',
            'save': False,
            'str': 'add_borders',
            'task': 'add_borders',
        }
        shot['filters'].insert(STEP_INC, add_borders_filter)
    # deshake_stab_count = 0
    # for filter in shot['filters']:
    #     if (filter['str'].startswith('deshake')
    #         or filter['str'].startswith('stabilize')
    #         or filter['str'].startswith('homography')):

    #         deshake_stab_count += 1
    #         if deshake_stab_count > 1:
    #             filter['str'] += "=no_border"


    # Insert 'replace' at the best place
    # just after add borders if deshake/temporal filtering or animeSR upscaling
    # in general, always after add_borders except for documentaire
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
        or 'stabilize' in filter_str
        or shot['filters'][step_no]['type'] == 'animesr'):
            # Insert before temporal filter
            shot['filters'].insert(step_no, replace_filter)
            # print_green("replace filter: inserted at position %d" % (step_no))
            is_inserted = True
            break
    if not is_inserted:
        shot['filters'][-1]['task'] = 'sharpen'
        shot['filters'].append(replace_filter)
        # print_green("replace filter: append")


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
        # elif ('scale' in filter['str']
        #     or 'dnn_superres' in filter['str']):
        #     filter['task'] = 'upscale'
        #     if previous_filter['task'] == '':
        #         previous_filter['task'] = 'pre_upscale'

        elif filter['type'] in ['real_cugan', 'pytorch', 'animesr']:
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


    # Append color fix
    shot['filters'].append({
        'type': 'python',
        'save': True,
        'str': 'color_fix',
        'task': 'color_fix'
    })


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


    # Patch the list for 'edition' task
    if shot['last_task'] == 'edition':
        # Change the task 'replace' into 'null'
        for filter in shot['filters']:
            if filter['task'] == 'replace':
                filter.update({'type': 'null', 'task': '', 'str': ''})
            elif 'deshake' in filter['str']:
                filter.update({'type': 'null', 'task': '', 'str': ''})

        # Now insert an 'edition' task just before 'rgb' filter
        edition_filter = {
            'type': 'python',
            'save': True,
            'str': 'pre_replace',
            'task': 'edition',
        }
        for step_no in range(len(shot['filters'])):
            filter = shot['filters'][step_no]

            if filter['task'] == 'rgb':
                # Do not save the previous filter because the 'edition' filter will do it
                shot['filters'][step_no-1]['save'] = False
                # Insert the pre_upsacle filter
                shot['filters'].insert(step_no, edition_filter)
                edition_step_no = step_no
                break

        # Simplify
        for step_no in range(edition_step_no-1, 1 , -1):
            f = shot['filters'][step_no]
            if not (f['task'] == '' and f['type'] == 'null'):
                f.update({'task': 'edition', 'save': True})
                break



    # Force saving last task
    if 'last_task' in shot.keys():
        # when not in video edition
        for filter in shot['filters']:
            if filter['task'] == shot['last_task']:
                filter['save'] = True
                break


    # pprint(shot['filters'])
    # sys.exit()
