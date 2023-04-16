# -*- coding: utf-8 -*-
import os
import shutil

from pprint import pprint
from utils.pretty_print import *

from shot.consolidate_shot import consolidate_shot
from shot.utils import get_shot_from_frame_no
from utils.get_image_list import FILENAME_TEMPLATE
from utils.common import K_GENERIQUES



def copy_frames_for_study(db, k_ed, k_ep, k_part, last_task):
    verbose = False
    if k_part in K_GENERIQUES:
        db_frames = db[k_part]['video']['frames']
    else:
        db_frames = db[k_ep]['video']['frames']

    if verbose:
        print_lightcyan(f"{k_ed}:{k_ep}:{k_part}, last_task={last_task}")
        pprint(db_frames)

    # Create a list of shots xhich are consolidated to avoid redo this task
    consolidated_shot_list = list()


    # shots = db[k_ep]['video'][k_ed][k_part]['shots']
    frame_no = db_frames[k_part]['list'][0]
    for frame_no in db_frames[k_part]['list']:
    # if True:

        # Get shot from frame no.
        shot = get_shot_from_frame_no(db,
            frame_no=frame_no,
            k_ed=k_ed,
            k_ep=k_ep,
            k_part=k_part)
        if shot is None:
            print_yellow(f"Warning: no shot found, skip frame no. {frame_no}")

        # Consolidate shot (if not already done)
        if shot['no'] not in consolidated_shot_list:

            # Consolidate shot, as if it was the src and the dst shot
            shot.update({
                'dst': {
                    'count': shot['count'],
                    'k_ed': k_ed,
                    'k_ep': k_ep,
                    'k_part': k_part,
                },
                'src': {
                    'k_ed': k_ed,
                    'k_ep': k_ep,
                    'k_part': k_part,
                    'no' : shot['no'],
                },
                'k_ed': k_ed,
                'k_ep': k_ep,
                'k_part': k_part,
            })

            # Set the last task
            shot['last_task'] = last_task

            # Remove 'replace' dict
            shot['replace'].clear()

            # Call a function which consolidate this shot and calculate all hashes
            consolidate_shot(db, shot)

            consolidated_shot_list.append(shot['no'])

            if verbose:
                print_lightcyan("================================== SHOT =======================================")
                pprint(shot)
                print_lightcyan("===============================================================================")


        # Get the 'real' frame no: apply offsets
        # TODO


        # Finally get image filename and filepath
        step_no = shot['last_step']['step_no']
        hash = shot['last_step']['hash']
        suffix = "_%s" % (hash) if hash != '' else ''
        filename_template = FILENAME_TEMPLATE % (k_ep, k_ed, step_no, suffix)

        if step_no == 0 or shot['last_task'] == 'edition':
            new_frame_no = frame_no
        else:
            new_frame_no = frame_no - shot['start']
        image_src_filename = filename_template % (new_frame_no)
        image_src_filepath = os.path.join(
            shot['cache'], "%02d" % (step_no),
            image_src_filename)

        if k_part in K_GENERIQUES:
            image_dst_folder = os.path.join(db_frames['path_output'])
        else:
            image_dst_folder = os.path.join(db_frames['path_output'], k_part)
        image_dst_filename = filename_template % (frame_no)
        image_dst_filepath = os.path.join(image_dst_folder, image_dst_filename)

        # Copy image
        if os.path.exists(image_src_filepath):

            # Create dst folder if not already exist
            if not os.path.exists(image_dst_folder):
                os.makedirs(image_dst_folder)

            print_lightgreen(f"{image_src_filename}: {shot['cache']}/{step_no:02} -> {image_dst_filepath}")
            shutil.copy2(image_src_filepath, image_dst_filepath)

        else:
            print_orange(f"{image_src_filepath}: missing file")

