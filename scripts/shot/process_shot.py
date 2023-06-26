# -*- coding: utf-8 -*-
import sys
import gc

import time
from pprint import pprint

from processing_chain.process_chain import process_chain_list
from img_toolbox.utils import STEP_INC
from img_toolbox.effects import (
    create_black_frame,
    effect_fadein,
    effect_loop_and_fadeout,
    effect_fadeout,
)
from processing_chain.optimize_tasks import optimize_tasks
from shot.consolidate_shot import consolidate_shot
from utils.pretty_print import *
from utils.types import Shot



def process_shot(db, shot:Shot, force:bool=False):
    start_time = time.time()

    # Consolidate shot
    consolidate_shot(db, shot)

    if True:
        print_lightcyan("================================== SHOT =======================================")
        pprint(shot)
        print_lightcyan("===============================================================================")
        # sys.exit()

    # Simplify anf get starting step no.
    if force:
        step_no = 0
    else:
        step_no = optimize_tasks(db=db, shot=shot)

    if step_no != -1:

        # Execute the list of tasks (simple chain)
        process_chain_list(db=db, shot=shot, start_task_no=step_no, force=force)

        spent_time = time.time() - start_time
        print_green("(%.01fs -> %0.2fs/f)" % (spent_time, spent_time/shot['count']))


    # Create a black frame used for silences/effects
    create_black_frame(db, shot)

    # Clean
    gc.collect()


    # No effects if last task is edition. deinterlace task ?
    if shot['last_task'] == 'edition':
        return

    # Effects
    if 'effects' in shot.keys():
        effect = shot['effects'][0]
        print_lightcyan("Effects:")

        if effect == 'loop_and_fadeout':
            effect_loop_and_fadeout(db, shot)

        elif effect == 'fadeout':
            effect_fadeout(db, shot)

        elif effect == 'fadein':
            # TODO rename fadein into loop_and_fadein?
            effect_fadein(db, shot)

        else:
            print_green("\tuse concatenation files")


    # sys.exit(print_red("\n終わり\n"))




