# -*- coding: utf-8 -*-
from pprint import pprint
import cv2

from utils.pretty_print import *
from utils.hash import (
    calculate_hash_for_replace,
    log_filter,
)
from utils.get_image_list import (
    get_new_image_list,
    get_image_list
)


def python_replace(shot:dict,
        images:list, image_list:list,
        step_no:int,
        filters_str:str,
        input_hash:str,
        get_hash:bool=False):

    output_images = list()
    output_image_list = list()
    if not get_hash:
        print_cyan("(python)\tstep no. %d, filter=%s, input_hash= %s" % (step_no, filters_str, input_hash))

    # Calculate hash
    hash = calculate_hash_for_replace(shot)
    if hash != '':
        hash = log_filter("%s,replace=%s" % (input_hash, hash), shot['hash_log_file'])
        if not get_hash:
            # print_yellow("BEFORE replace")
            # pprint(image_list)
            output_image_list = get_new_image_list(shot=shot, step_no=step_no, hash=input_hash)
            # print_yellow("AFTER replace")
            # pprint(image_list)
    else:
        # No images were replaced
        print_yellow("\t\t\tNo images were replaced")
        return input_hash, image_list, images

    return hash, output_image_list, output_images


def python_pre_replace(shot:dict,
        images:list, image_list:list,
        step_no:int,
        filters_str:str,
        input_hash:str,
        output_folder:str,
        get_hash:bool=False):

    # If this task is called, this means that it is the last task, save images
    hash = input_hash
    if not get_hash:
        print_cyan("(python)\tstep no. %d, task=%s, input_hash= %s" % (step_no, filters_str, input_hash))

        output_image_list = get_image_list(shot=shot,
            folder=output_folder,
            step_no=step_no,
            hash=input_hash)

        for img, img_filepath in zip(images, output_image_list):
            cv2.imwrite(img_filepath, img)

    return hash, image_list, list()