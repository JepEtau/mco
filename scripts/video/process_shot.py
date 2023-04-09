# -*- coding: utf-8 -*-
import sys
import gc
import os.path
import time
from pprint import pprint

from filters.apply_filters import apply_filters
from filters.utils import STEP_INC
from filters.effects import (
    create_black_frame,
    effect_loop_and_fadeout,
    effect_fadeout,
)
from utils.get_image_list import (
    get_image_list_pre_replace,
    get_image_list,
)
from utils.pretty_print import *

from video.consolidate_shot import consolidate_shot



def process_shot(db, shot, cpu_count=0):
    start_time = time.time()

    # Consolidate shot
    consolidate_shot(db, shot)

    if True:
        print_lightcyan("================================== SHOT =======================================")
        pprint(shot)
        print_lightcyan("===============================================================================")
        # sys.exit()

    # Simplify anf get starting step no.
    step_no = simplify_shot_process(db=db, shot=shot)

    if step_no != -1:

        # Apply filters to all frames of this shot
        apply_filters(db=db, shot=shot, step_no_start=step_no)
        spent_time = time.time() - start_time
        print_green("(%.01fs -> %0.2fs/f)" % (spent_time, spent_time/shot['count']))


    # Create a black frame used for silences
    create_black_frame(db, shot)

    # Clean
    gc.collect()


    # No effects if last task is pre_replace
    if shot['last_task'] == 'pre_replace':
        return

    # Effects
    if 'effects' in shot.keys():
        effect = shot['effects'][0]
        print("<<<<<<<<<<<<<<<<<<<<< EFFECTS >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        # print("APPLY effect", shot['effects'])
        # pprint(shot)
        if effect == 'loop_and_fadeout':
            effect_loop_and_fadeout(db, shot)

        elif effect == 'fadeout':
            effect_fadeout(db, shot)


    # sys.exit(print_red("\n終わり\n"))







def simplify_shot_process(db, shot) -> int:

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
