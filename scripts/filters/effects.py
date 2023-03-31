# -*- coding: utf-8 -*-
import sys
import os
import os.path
import numpy as np
import cv2
from pprint import pprint

from filters.utils import STEP_INC
from utils.get_image_list import (
    FILENAME_TEMPLATE,
    get_first_image_filepath,
    get_image_list,
    get_new_image_list
)
from utils.path import (
    get_input_path_from_shot,
    get_output_path_from_shot,
)
from utils.pretty_print import *


def create_black_frame(db, shot):
    black_image_filepath = os.path.join(
        db['common']['directories']['cache'], 'black.png')

    if 'shape' not in shot['last_step'].keys():
        # The shot was already been generated
        output_folder = get_output_path_from_shot(db, shot, task=shot['last_task'])
        img_filepath = get_first_image_filepath(shot,
            folder=output_folder,
            step_no=shot['last_step']['step_no'],
            hash=shot['last_step']['hash'])
        img = cv2.imread(img_filepath, cv2.IMREAD_COLOR)
        shot['last_step']['shape'] = img.shape

    (height, width, c) = shot['last_step']['shape']
    black_image = np.zeros([height, width, c], dtype=np.uint8)
    cv2.imwrite(black_image_filepath, black_image)



def effect_loop_and_fadeout(db, shot):
    # Validate with:
    #   - ep01: episode
    #   - ep01: asuivre
    #   - g_debut


    # Start and count of frames for the loop
    loop_start = shot['effects'][1]
    loop_count = shot['effects'][2]
    fadeout_count = shot['effects'][3]
    print_green("effect_loop_and_fadeout: loop: start=%d, count=%d / fadeout: count=%d" % (loop_start, loop_count, fadeout_count))


    # Get hash to set the suffix
    hash = shot['last_step']['hash']
    step_no = shot['last_step']['step_no']
    if hash == '':
        # Last filter is null, use previous hash
        previous_filter = shot['filters'][step_no - STEP_INC]
        hash = previous_filter['hash']
        input_filepath = get_input_path_from_shot(db=db,
            shot=shot, task=previous_filter['task'])
    else:
        input_filepath = get_input_path_from_shot(db=db,
            shot=shot, task=shot['last_task'])
    suffix = "_%s" % (hash)

    # Input directory
    print_lightgreen("\tinput_filepath: %s" % (input_filepath))


    # Output directory
    k_ep_dst = shot['dst']['k_ep']
    k_part_dst = shot['dst']['k_part']
    if k_part_dst in ['g_debut', 'g_fin']:
        output_filepath = os.path.join(db[k_part_dst]['cache_path'])
    else:
        output_filepath = os.path.join(db[k_ep_dst]['cache_path'], k_part_dst)
    output_filepath = os.path.join(output_filepath,
        '%03d' % (shot['no']),
        '%02d' % (step_no))
    if not os.path.exists(output_filepath):
        os.makedirs(output_filepath)
    print_lightgreen("\toutput_filepath: %s" % (output_filepath))


    # Input image list before the loop
    if shot['last_step']['step_no'] == shot['last_step']['step_no_replace']:
        image_list = get_new_image_list(shot=shot,
            step_no=step_no,
            hash=shot['filters'][step_no - STEP_INC]['hash'])
    else:
        image_list = get_image_list(shot=shot,
            folder=input_filepath,
            step_no=step_no,
            hash=hash)
    # Duplicate the last one
    loop_start -= shot['start']
    last_image_filepath = image_list[loop_start]
    print_lightgreen("\tfile used for the loop effect: %s" % (last_image_filepath))
    image_list += [last_image_filepath] * loop_count
    print_lightgreen("\tnb of frames after the loop: %s" % (len(image_list)))
    input_image_list = image_list[-1*fadeout_count:]
    # pprint(input_image_list)
    print_lightgreen("\tfade out: frames count: %d" % (len(input_image_list)))


    # Output image list
    filename_template = FILENAME_TEMPLATE % (
        shot['k_ep'], shot['k_ed'], step_no, suffix)
    if shot['last_task'] == 'deinterlace':
        start = shot['start'] + shot['count']
        end = start + fadeout_count
    else:
        start = shot['count']
        end = start + fadeout_count
    output_image_list = list([os.path.join(output_filepath, filename_template % (f_no))
        for f_no in range(start, end)])

    print_lightgreen("\toutput image count: %d" % (len(output_image_list)))
    pprint(output_image_list)


    (height, width, channel_count) = shot['last_step']['shape']

    # Create a  black image for fadeout
    img_black = np.zeros([height, width, channel_count], dtype=np.uint8)

    for count, img_input, img_output in zip(range(fadeout_count), input_image_list, output_image_list):
        # Calculate coefficient: last frame is not completely black because there is always
        # a silence after this (i.e. black frames)
        coef = float(count) / fadeout_count
        # keep print for debug until end of validation
        print("\t% 2d: %s -> %s, coef=%f" % (count, img_input, img_output, coef))

        # Mix images
        img_src = cv2.imread(img_input, cv2.IMREAD_COLOR)
        img_dst = cv2.addWeighted(img_src, 1 - coef, img_black, coef, 0)

        cv2.imwrite(img_output, img_dst)




def effect_fadeout(db, shot):
    # verified:
    #   - ep01: reportage
    fadeout_start = shot['effects'][1]
    fadeout_count = shot['effects'][2]
    print_green("effect_fadeout: start=%d, count=%d" % (fadeout_start, fadeout_count))
    # pprint(shot)

    # Input directory
    input_filepath = get_input_path_from_shot(db=db,
        shot=shot, task=shot['last_task'])
    print_lightgreen("\tinput_filepath: %s" % (input_filepath))

    # Get hash to set the suffix
    hash = shot['last_step']['hash']
    step_no = shot['last_step']['step_no']
    if hash == '':
        # Last filter is null, use previous hash
        hash = shot['filters'][step_no - STEP_INC]['hash']
    suffix = "_%s" % (hash)

    # Output directory
    k_ep_dst = shot['dst']['k_ep']
    k_part_dst = shot['dst']['k_part']
    if k_part_dst in ['g_debut', 'g_fin']:
        output_filepath = os.path.join(db[k_part_dst]['cache_path'])
    else:
        output_filepath = os.path.join(db[k_ep_dst]['cache_path'], k_part_dst)
    output_filepath = os.path.join(output_filepath,
        '%03d' % (shot['no']),
        '%02d' % (step_no))
    if not os.path.exists(output_filepath):
        os.makedirs(output_filepath)
    print_lightgreen("\toutput_filepath: %s" % (output_filepath))

    # Input image list
    if shot['last_step']['step_no'] == shot['last_step']['step_no_replace']:
        image_list = get_new_image_list(shot=shot,
            step_no=step_no,
            hash=shot['filters'][step_no - STEP_INC]['hash'])
    else:
        image_list = get_image_list(shot=shot,
            folder=input_filepath,
            step_no=step_no,
            hash=hash)
    # pprint(image_list)
    index_start = fadeout_start - shot['start']
    index_end = index_start + fadeout_count
    input_image_list = image_list[index_start:index_end]
    print_lightgreen("\tinput image count: %d" % (len(input_image_list)))
    # pprint(input_image_list)

    # Output image list
    filename_template = FILENAME_TEMPLATE % (
        shot['k_ep'], shot['k_ed'], step_no, suffix)
    if shot['last_task'] == 'deinterlace':
        start = shot['start'] + shot['count']
        end = start + fadeout_count
    else:
        start = shot['count']
        end = start + fadeout_count
    output_image_list = list([os.path.join(output_filepath, filename_template % (f_no))
        for f_no in range(start, end)])
    print_lightgreen("\toutput image count: %d" % (len(output_image_list)))
    # pprint(output_image_list)

    (height, width, channel_count) = shot['last_step']['shape']

    # Create a  black image for fadeout
    img_black = np.zeros([height, width, channel_count], dtype=np.uint8)

    for count, img_input, img_output in zip(range(fadeout_count), input_image_list, output_image_list):
        # Calculate coefficient: last frame is not completely black because there is always
        # a silence after this (i.e. black frames)
        coef = float(count) / fadeout_count
        # keep print for debug until end of validation
        print("\t% 2d: %s -> %s, coef=%f" % (count, img_input, img_output, coef))

        # Mix images
        img_src = cv2.imread(img_input, cv2.IMREAD_COLOR)
        img_dst = cv2.addWeighted(img_src, 1 - coef, img_black, coef, 0)

        cv2.imwrite(img_output, img_dst)
