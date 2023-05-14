# -*- coding: utf-8 -*-
import sys
import gc

import time
from pprint import pprint

from filters.apply_filters import apply_filters
from filters.utils import STEP_INC
from filters.effects import (
    create_black_frame,
    effect_fadein,
    effect_loop_and_fadeout,
    effect_fadeout,
)
from shot.optimize_tasks import optimize_tasks
from shot.consolidate_shot import consolidate_shot
from utils.pretty_print import *



def process_shot(db, shot, force:bool=False):
    start_time = time.time()

    # Consolidate shot
    consolidate_shot(db, shot)

    if False:
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

        # Apply filters to all frames of this shot
        apply_filters(db=db, shot=shot, step_no_start=step_no, force=force)
        spent_time = time.time() - start_time
        print_green("(%.01fs -> %0.2fs/f)" % (spent_time, spent_time/shot['count']))


    # Create a black frame used for silences
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
        # print("APPLY effect", shot['effects'])
        # pprint(shot)
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




