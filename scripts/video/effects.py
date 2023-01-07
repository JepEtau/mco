# -*- coding: utf-8 -*-
import sys
import os
import os.path
import shutil

import numpy as np
import cv2
from pprint import pprint

from utils.get_filters import get_filter_id
from utils.path import (
    get_output_path_from_shot,
)



def create_black_frame(db, last_task):
    extension = db['common']['settings']['frame_format']
    black_image_filepath = os.path.join(db['common']['directories']['cache'], 'black.%s' % (extension))

    if 'deinterlace' in last_task:
        dimensions = db['common']['dimensions']['deinterlace']
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



def effect_loop_and_fadeout(db, shot, frames, last_task):
    # verified:
    #   - ep01: episode
    #   - ep01: asuivre


    # loop on frame_no
    loop_start = shot['effects'][1]
    loop_count = shot['effects'][2]

    fadeout_count = shot['effects'][3]

    # print("%s.effect_loop_and_fadeout" % (__name__))
    # pprint(shot)
    # fadeout_start = shot['start'] + shot['count'] - fadeout_count
    # print("\n\tloop (%d), fadeout %d->%d, added frames=%d" % (loop_count, fadeout_start, fadeout_start + fadeout_count, loop_count))

    # Input directory: use the latest task even if it is not
    input_filepath = get_output_path_from_shot(db=db, shot=shot, task='rgb')
    # print("\tinput filepath=%s" % (input_filepath))

    # Output directory
    k_part = shot['k_part']
    if k_part in ['g_debut', 'g_fin']:
        output_filepath = os.path.join(
            db[k_part]['target']['path_cache'],
            '%06d' % (shot['start']))
    else:
        # Because it is the latest task was geometry to use the dst k_ep:k_part:shot_no
        output_filepath = get_output_path_from_shot(db=db, shot=shot, task='geometry')
    # print("\toutput filepath=%s" % (output_filepath))
    if not os.path.exists(output_filepath):
        os.makedirs(output_filepath)

    # Suffix for each image
    suffix = "__%s__%03d.%s" % (
        shot['k_ed'],
        get_filter_id(db, shot, last_task),
        db['common']['settings']['frame_format'])

    # Get dimensions from last task
    if 'deinterlace' in last_task:
        # deinterlace (or deinterlace_rgb for debug)
        dimensions = db['common']['dimensions']['initial']
    elif 'geometry' in last_task:
        # geometry (or upscale_rgb_geometry for debug)
        dimensions = db['common']['dimensions']['final']
    else:
        dimensions = db['common']['dimensions']['upscale']

    # Create a  black image for fadeout and open the src image
    img_black = np.zeros([dimensions['h'], dimensions['w'], 3], dtype=np.uint8)

    # Default filename if loop == fadeout
    filename = "%s_%06d%s" % (shot['k_ep'], loop_start, suffix)

    # Copy to dst because it is only done if last task is geometry
    if 'geometry' not in last_task:
        input_img_filepath = os.path.join(input_filepath, filename)
        output_img_filepath = os.path.join(output_filepath, filename)
        if output_img_filepath != input_img_filepath:
            # keep print for debug until end of validation
            print("\tno geometry: effect: effect_loop_and_fadeout: copy %s -> %s" % (input_img_filepath, output_img_filepath))
            shutil.copy(input_img_filepath, output_img_filepath)

    if loop_count > fadeout_count:
        # keep print for debug until end of validation
        print("\tinfo: loop (%d) is > fadeout (%d)" % (loop_count, fadeout_count))
        input_img_filepath = os.path.join(output_filepath, filename)

    # 2022-02-03:
    print("2022-12-03: validate this!")
    input_img_filepath = os.path.join(output_filepath, filename)
    for count in range(0, fadeout_count):
        # Input file
        if count < fadeout_count - loop_count:
            offset = shot['src']['start'] - shot['start'] + shot['src']['count'] - (fadeout_count - loop_count) + count
            input_img_filepath = frames[offset]['filepath'][last_task]

        # Output file
        filename = "%s_%06d%s" % (shot['k_ep'], shot['start'] + shot['count'] + count, suffix)
        output_img_filepath = os.path.join(output_filepath, filename)

        # Calculate coefficient: last frame is not completely black because there is always
        # a silence after this (i.e. black frames)
        coef = float(count) / fadeout_count
        # keep print for debug until end of validation
        print("\t% 2d: %s -> %s, coef=%f" % (count, input_img_filepath, output_img_filepath, coef))

        # Mix images
        img_src = cv2.imread(input_img_filepath, cv2.IMREAD_COLOR)
        img_dst = cv2.addWeighted(img_src, 1 - coef, img_black, coef, 0)

        # Create the destination image
        cv2.imwrite(output_img_filepath, img_dst)



def effect_fadeout(db, shot, frames, last_task):
    # verified:
    #   - ep01: reportage
    fadeout_count = shot['effects'][2]

    # fadeout_start = shot['effects'][1]
    # print("\n%s.effect_fadeout: start=%d, count=%d" % (__name__, fadeout_start, fadeout_count))
    # pprint(shot)

    # Input directory: use the latest task even if it is not
    input_filepath = get_output_path_from_shot(db=db, shot=shot, task='rgb')

    # Output directory
    k_part = shot['k_part']
    if k_part in ['g_debut', 'g_fin']:
        output_filepath = os.path.join(
            db['common']['directories']['cache'],
            k_part,
            "99999")
    else:
        # As if the latest task was geometry to use the dst k_ep:k_part:shot_no
        output_filepath = get_output_path_from_shot(db=db, shot=shot, task='geometry')
    # print("\toutput filepath=%s" % (output_filepath))
    if not os.path.exists(output_filepath):
        os.makedirs(output_filepath)

    # Suffix for each image
    suffix = "__%s__%03d.%s" % (
        shot['k_ed'],
        get_filter_id(db, shot, last_task),
        db['common']['settings']['frame_format'])

    # Get dimensions from last task
    if 'deinterlace' in last_task:
        # deinterlace (or deinterlace_rgb for debug)
        dimensions = db['common']['dimensions']['initial']
    elif 'geometry' in last_task:
        # geometry (or upscale_rgb_geometry for debug)
        dimensions = db['common']['dimensions']['final']
    else:
        dimensions = db['common']['dimensions']['upscale']

    # Create a  black image for fadeout
    img_black = np.zeros([dimensions['h'], dimensions['w'], 3], dtype=np.uint8)

    # # Copy to dst because it is only done if last task is geometry
    if 'geometry' not in last_task:
        for count in range(0, fadeout_count):
            index = shot['src']['start'] + shot['src']['count'] + count
            filename = "%s_%06d%s" % (shot['k_ep'], index, suffix)
            input_img_filepath = os.path.join(input_filepath, filename)
            output_img_filepath = os.path.join(output_filepath, filename)
            if output_img_filepath != input_img_filepath:
                # keep print for debug until end of validation
                print("\tno geometry: effect: fadeout: copy %s -> %s" % (input_img_filepath, output_img_filepath))
                shutil.copy(input_img_filepath, output_img_filepath)

    for count in range(0, fadeout_count):

        if shot['src']['start'] + shot['src']['count'] < shot['start'] + shot['count']:
            # Input file
            offset = shot['src']['start'] - shot['start'] + shot['src']['count'] + count
            input_img_filepath = frames[offset]['filepath'][last_task]

            # Output file
            filename = "%s_%06d%s" % (shot['k_ep'], shot['start'] + shot['count'] + count, suffix)
            output_img_filepath = os.path.join(output_filepath, filename)
        else:
            # Input file
            offset = -1 * (fadeout_count - count)
            input_img_filepath = frames[offset]['filepath'][last_task]

            # Output file
            filename = "%s_%06d%s" % (shot['k_ep'], shot['start'] + shot['count'] + count, suffix)
            output_img_filepath = os.path.join(input_filepath, filename)


        # Calculate coefficient: last frame is not completely black because there is always
        # a silence after this (i.e. black frames)
        coef = float(count) / fadeout_count
        # keep print for debug until end of validation
        print("\t% 2d: %s -> %s, coef=%f" % (count, input_img_filepath, output_img_filepath, coef))

        # Mix images
        img_src = cv2.imread(input_img_filepath, cv2.IMREAD_COLOR)
        img_dst = cv2.addWeighted(img_src, 1 - coef, img_black, coef, 0)

        cv2.imwrite(output_img_filepath, img_dst)
