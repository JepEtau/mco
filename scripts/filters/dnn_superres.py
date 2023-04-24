# -*- coding: utf-8 -*-
import cv2
# from cv2 import dnn_superres
import gc
import os
import sys
import time

from filters.utils import MAX_FRAMES_COUNT

from utils.hash import (
    calculate_hash,
    log_filter,
)
from utils.get_image_list import (
    get_image_list,
)
from utils.pretty_print import *

# pip uninstall opencv-python
# pip uninstall opencv-contrib-python
# pip install opencv-python-rolling==4.7.0.20230211


def upscale_cv2_dnn_superres(shot, images:list, image_list:list,
        step_no, filters_str:str, input_hash:str,
        do_save:bool, output_folder:str,
        get_hash:bool=False, do_force:bool=False):

    # Get method
    filter_name, method = filters_str.split('=')
    scale = 2

    suffix = "%s_%s" % (method, input_hash)

    # Hash
    filter_str = "%s,%s" % (input_hash, method)
    if get_hash:
        hash = calculate_hash(filter_str=filter_str)
        hash += "_" + suffix
        return hash, None
    hash = log_filter(filter_str, shot['hash_log_file'])
    hash += "_" + suffix

    print_cyan("(DNN_SUPERRES)\tstep no. %d, method= %s, input hash= %s, output hash= %s, suffix= %s" % (
        step_no, method, input_hash, hash, suffix))

    # Generate a list of output images
    output_image_list = get_image_list(
        shot=shot,
        folder=output_folder,
        step_no=step_no,
        hash=hash)
    output_images = list()


    # Output images in memory
    use_memory = True if shot['count'] <= MAX_FRAMES_COUNT else False
    use_memory = False

    if method == 'edsr' and scale == 2:
        model_filepath = "EDSR_x2.pb"

    elif method == 'edsr' and scale == 4:
        model_filepath = "EDSR_x4.pb"

    elif method == 'espcn' and scale == 2:
        model_filepath = "ESPCN_x2.pb"

    elif method == 'fsrcnn' and scale == 2:
        model_filepath = "FSRCNN_x2.pb"

    elif method == 'lapsrn' and scale == 2:
        model_filepath = "LapSRN_x2.pb"
    else:
        sys.exit(print_red("error: dnn_superres: method=%s, scale=%d" % (method, scale)))

    model_filepath = os.path.abspath(os.path.join("../..",
        "mco_3rd_party",
        "models",
        "dnn_superres",
        model_filepath))
    print_yellow("dnn_superres: model=%s" % (model_filepath))

    images.clear()
    gc.collect()

    # Create and set model
    sr = cv2.dnn_superres.DnnSuperResImpl_create()
    sr.readModel(model_filepath)
    sr.setModel(method, scale)
    model_scale = sr.getScale()
    print_yellow("dnn_superres: model scale=%d" % (model_scale))
    print_yellow("dnn_superres: use_memory=%s" % ('yes' if use_memory else 'no'))



    # Walk through images
    count = shot['count']
    for f_no, f_output in zip(range(count), output_image_list):
        start_time = time.time()

        print("\t%s -> %s" % (image_list[f_no], f_output))

        # Continue if the output file already exists
        if not do_force and os.path.exists(f_output):
            if use_memory:
                output_images.append(cv2.imread(f_output, cv2.IMREAD_COLOR))
            continue

        try:
            # Load image
            if use_memory:
                img = images[f_no]
            else:
                img = cv2.imread(image_list[f_no], cv2.IMREAD_COLOR)

            # Upscale
            output_img = sr.upsample(img=img)
            if scale == 4:
                output_img = cv2.resize(output_img,
                    (int(output_img.shape[1]/2), int(output_img.shape[0]/2)),
                    interpolation=cv2.INTER_LANCZOS4)

            if use_memory:
                output_images.append(output_img)

            # Always save on SSD because this process is time consuming
            cv2.imwrite(f_output, output_img)

        except RuntimeError as e:
            print("Error: failed to upscale %s" % (image_list[f_no]))
            print(e)
        else:
            print("\tinfo: upscaled in %.02fs" % (time.time() - start_time))

    return hash, output_images