# -*- coding: utf-8 -*-
import os
from filters.utils import STEP_INC
from utils.pretty_print import *

FILENAME_TEMPLATE = "%s_%%05d__%s__%02d%s.png"


def get_first_image_filepath(shot, folder, step_no, hash=''):
    suffix = "_%s" % (hash) if hash != '' else ''
    filename_template = FILENAME_TEMPLATE % (shot['k_ep'], shot['k_ed'], step_no, suffix)

    if step_no == 0 or shot['last_task'] == 'pre_replace':
        # Deinterlace or pre_replace uses the original frame no.
        print("\t\t\tget_first_image_filepath: deinterlaced")
        new_frame_no = shot['start']
    else:
        new_frame_no = 0

    image_filepath = os.path.join(os.path.normpath(folder),
        filename_template % (new_frame_no))
    return image_filepath


def get_new_image_list(shot, step_no, hash=''):
    # if step_no != shot['last_step']['step_no_replace'])
    #     sys.exit()
    print_orange("\t\t\tget_new_image_list: use replace list, step=%d" % (step_no))

    # Template to name the files
    suffix = "_%s" % (hash) if hash != '' else ''
    filename_template = FILENAME_TEMPLATE % (shot['k_ep'], shot['k_ed'], step_no-STEP_INC, suffix)
    folder = os.path.join(shot['cache'], "%02d" %  (step_no - STEP_INC))

    # Start frame no.
    # Generate the list
    replace = shot['replace']
    image_list = list()
    if (step_no - STEP_INC) == 0:
        # Deinterlace: use frame no to facilitate the debug
        for no in range(shot['start'], shot['start'] + shot['count']):
            try:
                new_frame_no = replace[no]
                # print_purple("\t%d -> %d" % (no, new_frame_no))
            except:
                new_frame_no = no
                # print_green("\t%d -> %d" % (no, new_frame_no))

            image_list.append(os.path.join(os.path.normpath(folder),
                filename_template % (new_frame_no)))
    else:
        for no in range(shot['count']):
            try:
                new_frame_no = replace[shot['start'] + no] - shot['start']
                # print_purple("\t%d <- %d" % (no, new_frame_no))
            except:
                new_frame_no = no
                # print_green("\t%d <- %d" % (no, new_frame_no))

            image_list.append(os.path.join(os.path.normpath(folder),
                filename_template % (new_frame_no)))

    return image_list


def get_image_list(shot, folder, step_no, hash=''):
    try:
        if step_no == shot['last_step']['step_no_replace']:
            print_red("error: get_image_list, current step is step_no")
    # try:
    #     if step_no == shot['last_step']['step_no_replace']:
    #         return get_new_image_list(shot=shot, step_no=step_no, hash=hash)
    except:
        # print_orange("get_image_list: continue, step=%d" % (step_no))
        pass

    # Template to name the files
    suffix = "_%s" % (hash) if hash != '' else ''
    filename_template = FILENAME_TEMPLATE % (shot['k_ep'], shot['k_ed'], step_no, suffix)

    # Start frame no.: deinterlace: use frame no to facilitate the debug
    frame_start = shot['start'] if step_no == 0 else 0

    # Generate the list
    image_list = list()
    for no in range(frame_start, frame_start+shot['count']):
        image_list.append(os.path.join(os.path.normpath(folder),
            filename_template % (no)))

    return image_list


def get_image_list_pre_replace(shot, folder, step_no, hash=''):

    # Template to name the files
    suffix = "_%s" % (hash) if hash != '' else ''
    filename_template = FILENAME_TEMPLATE % (shot['k_ep'], shot['k_ed'], step_no, suffix)
    folder = os.path.join(shot['cache'], "%02d" %  (step_no))

    # Generate the list
    image_list = list()
    for frame_no in range(shot['start'], shot['start'] + shot['count']):
        image_list.append(os.path.join(os.path.normpath(folder),
            filename_template % (frame_no)))

    return image_list