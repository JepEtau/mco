# -*- coding: utf-8 -*-
import re
import cv2
import os
import sys
import time
import torch
import numpy as np
from pprint import pprint
from utils.pretty_print import *
from img_toolbox.utils import MAX_FRAMES_COUNT

from utils.hash import (
    calculate_hash,
    log_filter,
)
from utils.get_image_list import (
    get_image_list,
)


def real_cugan_executor(
        shot,
        images:list, image_list:list,
        scale:int, denoise:int,
        directories:str,
        input_hash, step_no,
        output_folder:str,
        get_hash:bool=False,
        do_force:bool=False):

    module_path = os.path.join(directories['3rd_party'], directories['real_cugan'])
    sys.path.append(module_path)
    from upcunet_v3 import RealWaifuUpScaler

    if denoise < 4:
        denoise_to_model = {
            -1: 'conservative',
            0: 'no-denoise',
            1: 'denoise1x',
            2: 'denoise2x',
            3: 'denoise3x',
        }
        model_name = f"up{scale}x-latest-{denoise_to_model[denoise]}.pth"

    # else:
    #     if denoise == 5:
    #         model_name = ""

    model_filepath = os.path.join(directories['3rd_party'], "models", 'real_cugan', model_name)
    if not os.path.isfile(model_filepath):
        raise Exception("Error: model file %s does not exist" % (model_filepath))

    # ModelName="up2x-latest-no-denoise.pth"
    # ModelName="up2x-latest-denoise1x.pth"
    #{0,1,2,3,4,auto}; the larger the number, the smaller the memory consumption
    # Tile=4
    suffix = f"s{scale}_n{denoise}"

    # Hash
    filter_str = f"{input_hash},{suffix}"
    if get_hash:
        hash = calculate_hash(filter_str=filter_str)
        hash += "_" + suffix
        return hash, scale, None
    hash = log_filter(filter_str, shot['hash_log_file'])
    hash += "_" + suffix


    print_cyan("(REAL_CUGAN)\tstep no. %d, model= %s, input hash= %s, output hash= %s, suffix= %s" % (
        step_no, model_name, input_hash, hash, suffix))


    # Generate a list of output images
    output_image_list = get_image_list(
        shot=shot,
        folder=output_folder,
        step_no=step_no,
        hash=hash)
    output_images = list()

    # Output images in memory
    use_memory = True if shot['count'] <= MAX_FRAMES_COUNT else False


    # Verify that a compatible GPU is available (CUDA)
    if torch.cuda.is_available():
        half=True
        device="cuda:0"
    else:
        sys.exit(print_red("Error: CUDA is mandatory"))

    # Load model
    upscaler = RealWaifuUpScaler(
        scale=scale,
        weight_path=model_filepath,
        half=half,
        device=device)

    # Walk through images
    count = shot['count']
    i = 0
    for f_no, f_output in zip(range(count), output_image_list):
        i += 1
        start_time = time.time()
        torch.cuda.empty_cache()

        # print("\t%s -> %s" % (image_list[f_no], f_output))

        # Continue if the output file already exists
        if not do_force and os.path.exists(f_output):
            if use_memory:
                output_images.append(cv2.imread(f_output, cv2.IMREAD_COLOR))
            continue

        try:
            # Load image
            if use_memory:
                img = images[f_no][:, :, [2, 1, 0]]
            else:
                img = cv2.imread(image_list[f_no], cv2.IMREAD_COLOR)[:, :, [2, 1, 0]]

            # Upscale
            upscaled_img = upscaler(
                frame=img,
                tile_mode=0,
                cache_mode=3,
                alpha=1)
            output_img = upscaled_img[:, :, ::-1]

            if use_memory:
                output_images.append(output_img)

            # Always save on SSD because this process is time consuming
            cv2.imwrite(f_output, output_img)

        except RuntimeError as e:
            print("Error: failed to upscale %s" % (image_list[f_no]))
            print(e)
        else:
            print(f"\t\t({i}/{count}) upscaled in %.02fs" % (time.time() - start_time), end='\r')

    # print(f"{''.join([' ']*20)}")
    print("")

    return hash, scale, output_images


