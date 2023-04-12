import os
import os.path
from filters.utils import STEP_INC

from utils.pretty_print import *
from utils.get_image_list import (
    get_image_list_pre_replace,
    get_image_list,
)

def optimize_tasks(db, shot) -> int:

    # Get the step_no for this task
    for step_no_max, filter in zip(range(len(shot['filters'])), shot['filters']):
        if filter['task'] == shot['last_task']:
            break

    # Simplify tasks
    for step_no in range(step_no_max, -1, -1):
        filter = shot['filters'][step_no]

        hash = filter['hash']
        if hash == '':
            # no hash, not saved or null filter continue
            print_yellow("\t* step no. %d is empty or not saved" % (step_no))
            continue

        output_folder = os.path.join(shot['cache'], "%02d" %  (step_no))
        if filter['task'] == 'pre_replace':
            image_list = get_image_list_pre_replace(shot,
                folder=output_folder,
                step_no=step_no,
                hash=hash)
        else:
            if shot['dst']['k_part'] in ['g_debut', 'g_fin']:
                print_yellow("\treplace output folder from %s to " % (output_folder), end='')
                output_folder_dst = output_folder.replace(shot['k_ep'],shot['dst']['k_ep'])
                print_yellow("%s" % (output_folder_dst))
            else:
                output_folder_dst = output_folder
            image_list = get_image_list(shot,
                folder=output_folder_dst,
                step_no=step_no,
                hash=hash)

        do_process = False
        for f in image_list:
            if not os.path.exists(f):
                do_process = True
                break
        if not do_process:
            print_green("\t* step no. %d already done" % (step_no))
            step_no += STEP_INC
            break
        else:
            print_red("\t* process step no. %d" % (step_no))

    if step_no > step_no_max:
        # Files already exist
        step_no = -1

    print_orange("\trestart from step no. %d" % (step_no))

    return step_no
