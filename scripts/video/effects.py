#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import os.path
import numpy as np
import cv2
from shutil import copy
from pprint import pprint
import sys

from utils.common import get_shot_no_from_frame_no
from utils.get_filters import get_filter_id
from utils.path import get_output_frame_filepaths



def create_black_frame(db, last_task):
    extension = db['common']['settings']['frame_format']
    black_image_filepath = os.path.join(db['common']['directories']['cache'], 'black.%s' % (extension))

    if last_task == 'deinterlace':
        dimensions = db['common']['dimensions']['initial']
    elif last_task == 'geometry':
        dimensions = db['common']['dimensions']['final']
    else:
        dimensions = db['common']['dimensions']['upscale']

    if os.path.exists(black_image_filepath):
        img_tmp = cv2.imread(black_image_filepath, cv2.IMREAD_COLOR)
        if dimensions['h'] == img_tmp.shape[0] and dimensions['w'] == img_tmp.shape[1]:
            # The black image already exists and dimensions are correct
            return

    black_image = np.zeros([dimensions['h'], dimensions['w'], 3], dtype=np.uint8)
    cv2.imwrite(black_image_filepath, black_image)



def effect_comb(db, shot, frame, last_task):
    # Apply 'comb' effect on the frame passed as argument
    # use 'last_task' to get the frame filepath

    k_ep_dst = shot['effects'][2]
    frames_count = shot['effects'][1]
    frame_start_no = shot['start'] - frames_count - 1

    # Divide the nb of frames per 3
    frames_per_band = int(frames_count / 3)

    # 3 static frames between frames
    frames_per_band = frames_per_band - 3

    # Get dimensions from last task
    if last_task == 'deinterlace':
        dimensions = db['common']['dimensions']['initial']
    elif last_task == 'geometry':
        dimensions = db['common']['dimensions']['final']
    else:
        dimensions = db['common']['dimensions']['upscale']

    # Calculate delta
    delta_y = int(dimensions['h'] / (frames_per_band+2))
    delta_x = int(dimensions['w'] / 3)

    # Read image:
    # print(frame['filepath'][last_task])
    img_src = cv2.imread(frame['filepath'][last_task], cv2.IMREAD_COLOR)

    # Create the destination image
    img_dst = np.zeros([dimensions['h'], dimensions['w'], 3], dtype=np.uint8)

    # Patch output folder
    output_folder = os.path.join(db[k_ep_dst]['common']['path']['cache'], shot['k_part'])
    shot['output_path'] = output_folder

    # Create the images and save them
    count = 0
    x = 0
    for i in range(0, 3):
        # nb of bands: 3

        y = 0
        for ii in range(frames_per_band+1):
            count += 1
            if i == 0 or i ==2:
                # bottom to top
                y += delta_y
                img_dst[0:y, x:x+delta_x] = img_src[0:y, x:x+delta_x]
            else:
                # top to bottom
                y += delta_y
                img_dst[dimensions['h']-y:dimensions['h'], x:x+delta_x] = img_src[dimensions['h']-y:dimensions['h'], x:x+delta_x]

            output_folder
            output_filepath = get_output_frame_filepaths(db, shot, frame_start_no + count)[last_task]
            # print("\t(x, y) = (%d, %d) -> %s" % (x, y, output_filepath))
            cv2.imwrite(output_filepath, img_dst)

        if i == 0:
            # bottom to top
            y -= delta_y
        else:
            # top to bottom
            y += delta_y

        y = dimensions['h']
        for ii in range(3):
            # loop on 3 frames
            count += 1
            img_dst[dimensions['h']-y:dimensions['h'], x:x+delta_x] = img_src[dimensions['h']-y:dimensions['h'], x:x+delta_x]
            output_filepath = get_output_frame_filepaths(db, shot, frame_start_no + count)[last_task]
            # print("\t(x, y) = (%d, %d) -> %s" % (x, y, output_filepath))
            cv2.imwrite(output_filepath, img_dst)
            if count >= frames_count:
                break

        x += delta_x


def effect_loop_and_fadeout(db, shot, frames, last_task):
    # loop on frame_no
    loop_start = shot['effects'][1]
    loop_count = shot['effects'][2]

    fadeout_count = shot['effects'][3]
    fadeout_start = shot['start'] + shot['count'] - fadeout_count

    # print("%s.effect_loop_and_fadeout" % (__name__))
    # pprint(shot)

    # print("\n\tloop (%d), fadeout %d->%d, added frames=%d" % (loop_count, fadeout_start, fadeout_start + fadeout_count, loop_count))

    # Initial input filepath
    input_filepath = shot['output_path']
    # print("\tinput filepath=%s" % (input_filepath))

    # Output directory
    k_ep = shot['k_ep']
    k_part = shot['k_part']
    output_filepath = shot['output_path']
    if 'dst' in shot.keys():
        print("--> detected dst for the effect_loop_and_fadeout")
        k_ep_dst = shot['dst']['k_ep']
        k_part_dst = shot['dst']['k_part']
        if k_ep_dst != k_ep and k_part_dst != k_part:
            output_filepath = os.path.join(db['common']['directories']['cache'], k_ep_dst, k_part_dst, "%05d" % (shot['start']))
    elif shot['k_part'] in ['g_debut', 'g_fin']:
        output_filepath = os.path.join(db['common']['directories']['cache'], shot['k_part'], "%05d" % (shot['start']))

    # print("\toutput filepath=%s" % (output_filepath))
    if not os.path.exists(output_filepath):
        os.makedirs(output_filepath)
    suffix = "__%s__%03d.%s" % (
        shot['k_ed'],
        get_filter_id(db, shot, last_task),
        db['common']['settings']['frame_format'])


    # Get dimensions from last task
    if last_task == 'deinterlace':
        dimensions = db['common']['dimensions']['initial']
    elif last_task == 'geometry':
        dimensions = db['common']['dimensions']['final']
    else:
        dimensions = db['common']['dimensions']['upscale']


    # Create a  black image for fadeout and open the src image
    img_black = np.zeros([dimensions['h'], dimensions['w'], 3], dtype=np.uint8)

    # Default filename if loop == fadeout
    filename = "%s_%05d%s" % (shot['k_ep'], loop_start, suffix)

    if loop_count > fadeout_count:
        print("WARNING: loop (%d) is > fadeout (%d)" % (loop_count, fadeout_count))
        input_img_filepath = os.path.join(shot['output_path'], filename)

    for count in range(0, fadeout_count):
        # Input file
        if count < fadeout_count - loop_count:
            # print("\tfadeout before loop")
            # Use the src
            input_img_filepath = frames[-1 * (fadeout_count - loop_count - count)]['filepath'][last_task]
        #    input_img_filepath = frames[-1]['filepath'][last_task]
        elif count == fadeout_count - loop_count:
            # print("\tstart loop")
            if count == 0:
                # Use the loop
                input_img_filepath = os.path.join(shot['output_path'], filename)
            else:
                input_img_filepath = os.path.join(output_filepath, filename)

        # Output file
        filename = "%s_%05d%s" % (shot['k_ep'], shot['start'] + shot['count'] + count, suffix)
        output_img_filepath = os.path.join(output_filepath, filename)

        # print("\t% 2d: %s -> %s" % (count, input_img_filepath, output_img_filepath))

        # Calculate coefficient
        coef = count / fadeout_count

        # Mix images
        img_src = cv2.imread(input_img_filepath, cv2.IMREAD_COLOR)
        img_dst = cv2.addWeighted(img_src, 1 - coef, img_black, coef, 0)

        # Create the destination image
        cv2.imwrite(output_img_filepath, img_dst)



def effect_fadeout(db, shot, frames, last_task):
    fadeout_count = shot['effects'][2]
    fadeout_start = shot['effects'][1]

    # print("\n%s.effect_fade_out: start=%d, count=%d" % (__name__, fadeout_start, fadeout_count))
    # pprint(shot)
    # sys.exit()

    # Initial input filepath
    input_filepath = shot['output_path']
    # print("\tinput filepath=%s" % (input_filepath))

    # Destination
    k_ep = shot['k_ep']
    k_part = shot['k_part']
    output_filepath = shot['output_path']
    if 'dst' in shot.keys():
        print("--> detected dst for the effect_loop_and_fadeout")
        k_ep_dst = shot['dst']['k_ep']
        k_part_dst = shot['dst']['k_part']
        if k_ep_dst != k_ep and k_part_dst != k_part:
            # Use the same folder when src=dst
            output_filepath = os.path.join(db['common']['directories']['cache'], k_ep_dst, k_part_dst, "%05d" % (shot['start']))
    elif shot['k_part'] in ['g_debut', 'g_fin']:
        output_filepath = os.path.join(db['common']['directories']['cache'], shot['k_part'], "99999")

    # print("\toutput filepath=%s" % (output_filepath))
    if not os.path.exists(output_filepath):
        os.makedirs(output_filepath)

    suffix = "__%s__%03d.%s" % (
        shot['k_ed'],
        get_filter_id(db, shot, last_task),
        db['common']['settings']['frame_format'])

    # Get dimensions from last task
    if last_task == 'deinterlace':
        dimensions = db['common']['dimensions']['initial']
    elif last_task == 'geometry':
        dimensions = db['common']['dimensions']['final']
    else:
        dimensions = db['common']['dimensions']['upscale']

    # Create a  black image for fadeout
    img_black = np.zeros([dimensions['h'], dimensions['w'], 3], dtype=np.uint8)

    for count in range(0, fadeout_count):
        # Input file
        input_img_filepath = frames[-1 * (fadeout_count - count)]['filepath'][last_task]

        # Output file
        filename = "%s_%05d%s" % (shot['k_ep'], shot['start'] + shot['count'] + count, suffix)
        output_img_filepath = os.path.join(output_filepath, filename)

        # print("\t% 2d: %s -> %s" % (count, input_img_filepath, output_img_filepath))

        # Calculate coefficient
        coef = count / fadeout_count

        # Mix images
        img_src = cv2.imread(input_img_filepath, cv2.IMREAD_COLOR)
        img_dst = cv2.addWeighted(img_src, 1 - coef, img_black, coef, 0)

        cv2.imwrite(output_img_filepath, img_dst)
