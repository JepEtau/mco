# -*- coding: utf-8 -*-
import os
from img_toolbox.utils import STEP_INC
from utils.pretty_print import *

FILENAME_TEMPLATE = "%s_%%05d__%s__%02d%s.png"


def get_first_image_filepath(shot, folder, step_no, hash=''):
    suffix = "_%s" % (hash) if hash != '' else ''
    filename_template = FILENAME_TEMPLATE % (shot['k_ep'], shot['k_ed'], step_no, suffix)

    if step_no == 0 or shot['last_task'] == 'edition':
        # Deinterlace or edition uses the original frame no.
        # print("\t\tget_first_image_filepath: deinterlaced")
        new_frame_no = shot['start']
    else:
        new_frame_no = 0

    image_filepath = os.path.join(os.path.normpath(folder),
        filename_template % (new_frame_no))
    return image_filepath


def get_new_image_list(shot, step_no, hash=''):
    # if step_no != shot['last_step']['step_edition'])
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
        if step_no == shot['last_step']['step_edition']:
            print_red("warning: get_image_list, current step is step_edition")
            return get_image_list_pre_replace(shot, folder, step_no, hash=hash)
    except:
        pass

    # Template to name the files
    suffix = f"_{hash}" if hash != '' else ''
    filename_template = FILENAME_TEMPLATE % (shot['k_ep'], shot['k_ed'], step_no, suffix)

    # Generate the list
    image_list = list()
    if step_no == 0:
        # Start frame no.: deinterlace: use frame no to facilitate the debug
        if 'segments' in shot['src'].keys() and len(shot['src']['segments']) > 0:
            print(lightcyan(f"!!!WARNING: {shot['k_ed']}:{shot['k_ep']}:{shot['k_part']}:{shot['no']}\n"),
                yellow(f"get_image_list used with step_no=0 and segments defined\n"),
                yellow(f"must be only used to generate a concatenation file"))
            for s in shot['src']['segments']:
                start, count = s['start'], s['count']
                image_list += list([os.path.join(os.path.normpath(folder),
                    filename_template % (no)) for no in range(start, start+count)])
        else:
            start, count = shot['start'], shot['count']
    else:
        start, count = 0, shot['dst']['count']

    if len(image_list) == 0:
        image_list = list([os.path.join(os.path.normpath(folder),
            filename_template % (no)) for no in range(start, start+count)])

    return image_list



def get_deinterlaced_image_filepaths(shot, folder, hash=''):
    # List the original frames when deinterlacing
    # step = 0
    step_no = 0

    # Template to name the files
    suffix = f"_{hash}" if hash != '' else ''
    filename_template = FILENAME_TEMPLATE % (shot['k_ep'], shot['k_ed'], step_no, suffix)

    # Generate the list
    start, count = shot['start'], shot['count']
    image_list = list([os.path.join(os.path.normpath(folder),
            filename_template % (no)) for no in range(start, start+count)])

    return image_list



def get_image_list_pre_replace(shot, folder, step_no, hash=''):

    # Template to name the files
    suffix = "_%s" % (hash) if hash != '' else ''
    filename_template = FILENAME_TEMPLATE % (shot['k_ep'], shot['k_ed'], step_no, suffix)
    folder = os.path.join(shot['cache'], "%02d" %  (step_no))

    # Generate the list
    image_list = list()
    if 'segments' in shot['src'].keys() and len(shot['src']['segments']) > 0:
        for s in shot['src']['segments']:
            start, count = s['start'], s['count']
            image_list = list([os.path.join(os.path.normpath(folder),
                    filename_template % (no)) for no in range(start, start+count)])

    else:
        start, count = shot['src']['start'], shot['src']['count']
        image_list = list([os.path.join(os.path.normpath(folder),
                filename_template % (no)) for no in range(start, start+count)])

    return image_list
