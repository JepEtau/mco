# -*- coding: utf-8 -*-
import cv2
import numpy as np
import os
import re
import sys
import time
import torch
from pprint import pprint

from img_toolbox.scunet_model_arch import WMSA
from img_toolbox.scunet_model_arch import SCUNet as net
from img_toolbox.utils import MAX_FRAMES_COUNT
from utils.pretty_print import *
from processing_chain.hash import (
    calculate_hash,
    log_filter,
)
from processing_chain.get_image_list import (
    get_image_list,
)


def scunet_executor(shot, images:list, image_list:list,
    model_name:str, directories:str, input_hash, step_no, output_folder:str,
    get_hash:bool=False, do_force:bool=False):

    model_filepath = os.path.join(directories['3rd_party'],
        "models", 'scunet',
        f"scunet_color_real_{model_name}.pth" if model_name in ['psnr', 'gan'] else f"{model_name}.pth")


    # Default values
    suffix = f"{model_name}_{input_hash}"
    scale = 1

    # Hash
    filter_str = f"{input_hash},{suffix}"
    if get_hash:
        hash = calculate_hash(filter_str=filter_str)
        hash += "_" + suffix
        return hash, scale, None
    hash = log_filter(filter_str, shot['hash_log_file'])
    hash += "_" + suffix

    if not os.path.isfile(model_filepath):
        sys.exit(print_red("Error: model file %s does not exist" % (model_filepath)))

    print_cyan(f"(SCUnet)\tstep no. {step_no}, ({scale}x), model {model_name}, input hash={input_hash}, output hash={hash}, suffix={suffix}")


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
        device_id = 0
        cpu = False
        fp16 = True
    else:
        print_orange("Warning: using CPU")
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # nb of channels in the image
    channel_count = 3

    # Load model
    torch.cuda.empty_cache()
    state_dict = torch.load(model_filepath)

    model = net(in_nc=channel_count, config=[4, 4, 4, 4, 4, 4, 4], dim=64)
    model.load_state_dict(state_dict, strict=True)
    model.eval()
    for _, v in model.named_parameters():
        v.requires_grad = False
    model = model.to(device)

    # number_parameters = sum(map(lambda x: x.numel(), model.parameters()))

    # Walk through images
    count = shot['count']
    i = 0
    for f_no, f_output in zip(range(count), output_image_list):
        start_time = time.time()
        i += 1

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

            input_img = torch.from_numpy(np.transpose(img, (2, 0, 1))).float().div(255.).unsqueeze(0).to(device)

            upscaled_img = model(input_img)
            torch.cuda.empty_cache()

            output_img = upscaled_img.data.squeeze().float().clamp_(0, 1).cpu().numpy()
            output_img = np.transpose(output_img, (1, 2, 0))
            output_img = np.uint8((output_img*255.0).round())

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




