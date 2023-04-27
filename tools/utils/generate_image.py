# -*- coding: utf-8 -*-
from copy import deepcopy
import sys

import time

from filters.python_geometry import IMG_BORDER_HIGH_RES
from utils.nested_dict import nested_dict_set
import cv2
import numpy as np

from pprint import pprint
from logger import log
from utils.pretty_print import *

from filters.filters import (
    calculate_geometry_parameters,
    cv2_geometry_filter,
    filter_rgb)
from filters.utils import get_dimensions_from_crop_values


def generate_image(frame:dict, preview_options:dict):
    verbose = False

    if verbose:
        log.info("generate single image")
        print_purple(f"Generate image: {frame['k_ed']}:{frame['k_ep']}:{frame['k_part']}:{frame['shot_no']:03}:{frame['frame_no']}")
        pprint(frame)

    # geometry_values are the calculated dimensions, crop, pad etc.
    geometry_values = deepcopy(frame['geometry_values'])

    if verbose:
        print_lightcyan("\t- preview options:")
        pprint(preview_options)
        print_lightcyan("\t- calculated geometry values")
        pprint(geometry_values)

    # Initial image
    if frame['cache_deshake'] is not None and preview_options['stabilize']['enabled']:
        if verbose:
            print_lightcyan("\t- use deshake img")
        img_initial = frame['cache_deshake']
    else:
        if verbose:
            print_lightcyan("\t- use initial img")
        img_initial = frame['cache_initial']
    img_height, img_width, c = img_initial.shape


    # Final width and height
    w_final = geometry_values['final']['w']
    h_final = geometry_values['final']['h']

    # Shot geometry
    shot_geometry = frame['geometry']['shot']
    if shot_geometry is None and 'default' in frame['geometry'].keys():
        # Shot geometry may contains the default geometry when using video editor
        shot_geometry = frame['geometry']['default']

    if verbose:
        print_lightcyan("\t- geometry used for this shot:", end=' ')
        print(shot_geometry)

    preview_geometry = preview_options['geometry']
    preview_shot_geometry = preview_options['geometry']['shot']

    # Cropped dimensions
    if preview_options['geometry']['add_borders']:
        # No border were added
        crop_values = shot_geometry['crop']
    else:
        crop_values = list(map(lambda x: x + IMG_BORDER_HIGH_RES, shot_geometry['crop']))

    crop_top, crop_bottom, crop_left, crop_right, cropped_width, cropped_height = get_dimensions_from_crop_values(
        width=img_width, height=img_height, crop=crop_values)

    if verbose:
        print_lightcyan("\t- modified geometry:", end=' ')
        print(f"crop: ({crop_top}, {crop_bottom}, {crop_left}, {crop_right}), cropped img: {cropped_width}x{cropped_height}")


    # Apply RGB curves
    #------------------------------------
    if preview_options['curves']['enabled'] and frame['curves'] is not None:
        try:
            img_rgb = filter_rgb(frame, img_initial)
        except:
            print("Cannot apply RGB curves")
            img_rgb = img_initial

        if preview_options['curves']['split']:
            # Merge 2 images to split the screen
            x = preview_options['curves']['split_x']
            if preview_geometry['shot']['resize_preview']:
                w_tmp = int((cropped_width * h_final) / float(cropped_height))
                pad_left = int((w_final - w_tmp) / 2)
                x = max(0, int((x-pad_left) / (h_final / float(cropped_height))) + crop_left)
            img_rgb[0:img_height, x:img_width,] = img_initial[0:img_height,x:img_width,]
    else:
        img_rgb = img_initial



    # Final image: function
    #------------------------------------
    if preview_geometry['final_preview']:
        # Use the functions that will be called by the script
        nested_dict_set(frame['geometry'], {'w': w_final, 'h': h_final}, 'dimensions', 'final')
        virtual_shot = {
            'geometry': frame['geometry'],
            'last_task': frame['task']
        }
        geometry_values = calculate_geometry_parameters(shot=virtual_shot, img=img_initial)
        img_finalized = cv2_geometry_filter(img=img_rgb, geometry=geometry_values)
        return (frame['index'], img_finalized)



    # Crop the image
    #------------------------------------
    if not preview_shot_geometry['crop_preview'] and preview_shot_geometry['crop_edition']:
        # Add a rectangle to the original image
        if verbose:
            print("\t-> image not cropped")
        img_cropped = img_rgb

    elif preview_shot_geometry['crop_preview']:
        # Crop and NO rectangle
        if verbose:
            print("\t-> image cropped, ", end=' ')
        # (1) Crop the image
        img_cropped = np.ascontiguousarray(img_rgb[
            crop_top : img_height - crop_bottom,
            crop_left : img_width - crop_right], dtype=np.uint8)
        if verbose:
            print(img_cropped.shape)

    else:
        # Not options['crop_preview'] and not preview_shot_geometry['crop_edition']
        # i.e. Original image
        img_cropped = img_rgb

        if preview_shot_geometry['resize_preview']:
            pprint(frame['geometry'])
            print("Error: generate_image: resize not possible because no crop preview selected")

    # Resize the image
    #------------------------------------
    target_width = frame['geometry']['target']['w']
    fit_to_width = shot_geometry['fit_to_width']
    keep_ratio = shot_geometry['keep_ratio']
    crop_2 = None
    pad_error = None
    if preview_shot_geometry['resize_preview']:

        if preview_shot_geometry['crop_preview']:
            # Resize the cropped image
            if verbose:
                print("\t-> Resize the cropped image")

            img_resized = cv2.resize(src=img_cropped,
                dsize=(geometry_values['resize']['w'], geometry_values['resize']['h']),
                interpolation=cv2.INTER_LANCZOS4)
        else:
            # Calculate the new dimensions of the image to add a rect on it
            if verbose:
                print("\t-> Resize the original image")

            resized_width = int(0.5 + (img_width * geometry_values['resize']['w']) / float(cropped_width))
            resized_height = int(0.5 + (img_height * geometry_values['resize']['h']) / float(cropped_height))
            img_resized = cv2.resize(src=img_rgb,
                dsize=(resized_width, resized_height),
                interpolation=cv2.INTER_LANCZOS4)

            if verbose:
                print("\t-> resized original image: %dx%d, calculated:%dx%d" % (
                    img_resized.shape[1], img_resized.shape[0], resized_width, resized_height))

        img_resized_cropped = img_resized

    else:
        img_resized_cropped = img_cropped



    # Final image
    if preview_geometry['final_preview']:

        # Error case
        pad_error = geometry_values['pad_error']
        if pad_error is not None:
            # print_red("Error: add padding but should not")
            img_resized_consolidated = cv2.copyMakeBorder(src=img_resized_cropped,
            top=pad_error[0], bottom=pad_error[1],
            left=pad_error[2], right=pad_error[3],
            borderType=cv2.BORDER_CONSTANT, value=[255, 255, 255])
        else:
            img_resized_consolidated = img_resized_cropped

        if verbose:
            print("\t-> Finalize the image (add padding)")

        # Add padding
        img_finalized = cv2.copyMakeBorder(src=img_resized_consolidated,
            top=0, bottom=0, left=geometry_values['pad']['left'], right=geometry_values['pad']['right'],
            borderType=cv2.BORDER_CONSTANT, value=[0, 0, 0])
    else:
        img_finalized = img_resized_cropped

    return (frame['index'], img_finalized)

    if img_resized_cropped is not None:
        # print("generate_image: %dms" % (int(1000 * (time.time() - now))))
        return (frame['index'], img_resized_cropped)
    else:
        # print("generate_image: %dms" % (int(1000 * (time.time() - now))))
        if img_finalized.shape[0] == 576:
            img_resized_final_2 = cv2.resize(img_cropped, (img_finalized.shape[1] * 2, img_finalized.shape[0]*2), interpolation=cv2.INTER_LANCZOS4)
        else:
            img_resized_final_2 = img_finalized
        return (frame['index'], img_resized_final_2)


