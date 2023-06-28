# -*- coding: utf-8 -*-
import sys
import cv2
import os
import psutil
import time
import torch
import numpy as np
import gc
from basicsr.data.transforms import mod_crop
from basicsr.utils.img_util import (
    img2tensor,
    tensor2img,
)

from img_toolbox.utils import MAX_FRAMES_COUNT
from utils.pretty_print import *

from processing_chain.hash import (
    calculate_hash,
    log_filter,
)
from processing_chain.get_image_list import (
    get_image_list,
)


@torch.no_grad()
def animesr_executor(shot, images:list, image_list:list,
    model_name:str, directories:str, input_hash, step_no,
    do_save:bool, output_folder:str,
    get_hash:bool=False, do_force:bool=False):

    module_path = os.path.join(directories['3rd_party'], directories['animesr'])
    model_filepath = os.path.join(directories['3rd_party'], "models", 'animesr', "%s.pth" % (model_name))
    if not os.path.isfile(model_filepath):
        sys.exit(print_red("Error: model file %s does not exist" % (model_filepath)))

    from animesr.archs.vsr_arch import MSRSWVSR

    # released models are all x4 models
    netscale = 4

    suffix = f"{model_name}_{input_hash}"

    # Hash
    filter_str = "%s,%s" % (input_hash, model_name)
    if get_hash:
        hash = calculate_hash(filter_str=filter_str)
        hash += "_" + suffix
        return hash, netscale, None
    hash = log_filter(filter_str, shot['hash_log_file'])
    hash += "_" + suffix


    print_cyan(f"(ANimeSR)\tstep no. {step_no}, {model_name}, input hash:{input_hash}, output hash:{hash}, suffix={suffix}")

    # Verify that a compatible GPU is available (CUDA)
    if torch.cuda.is_available():
        gpu_id = 0
        fp16 = True
    else:
        print_orange("Warning: using CPU")
        gpu_id = None
        fp16 = False
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


    # Generate a list of output images
    output_image_list = get_image_list(
        shot=shot,
        folder=output_folder,
        step_no=step_no,
        hash=hash)
    output_images = list()

    # Output images in memory
    use_memory = True if shot['count'] <= MAX_FRAMES_COUNT else False

    count = shot['count']
    if len(images) != count:
        sys.exit(print_red("Error: upscale_animesr: missing frames in buffer"))


    # Prepare and load model
    model = MSRSWVSR(num_feat=64, num_block=[5, 3, 2], netscale=netscale)
    loadnet = torch.load(model_filepath)
    model.load_state_dict(loadnet, strict=True)
    model.eval()
    model = model.to(device)
    model = model.half() if fp16 else model

    # Load 1st images
    height, width = images[0].shape[:2]
    # out_height, out_width = int(height * netscale), int(width * netscale)

    previous_image = get_frame(images[0], device, fp16)
    current_image = previous_image
    next_image = get_frame(images[min(1, count - 1)], device, fp16)

    state = previous_image.new_zeros(1, 64, height, width)
    output = previous_image.new_zeros(1, 3, height * netscale, width * netscale)

    count = shot['count']
    i = 0
    for f_no, f_output in zip(range(count), output_image_list):
        start_time = time.time()
        i += 1

        if not do_force and os.path.exists(f_output):
            if use_memory:
                output_images.append(cv2.imread(f_output, cv2.IMREAD_COLOR))
            continue

        # print("\t%s -> %s" % (image_list[f_no], output_image_list[f_no]))
        try:
            torch.cuda.synchronize(device=device)
            output, state = model.cell(torch.cat((previous_image, current_image, next_image), dim=1),
                output, state)

            torch.cuda.synchronize(device=device)
            output_img = tensor2img(output, rgb2bgr=False)
            # if outscale != netscale:
            #     output_img_scaled = cv2.resize(output_img,
            #         (out_width, out_height), interpolation=cv2.INTER_LANCZOS4)
            # else:
            #     output_img_scaled = output_img
            if use_memory:
                output_images.append(output_img)
            if do_save:
                cv2.imwrite(f_output, output_img)

            previous_image = current_image
            current_image = next_image

            torch.cuda.synchronize(device=device)
            next_image = get_frame(images[min(f_no + 2, count - 1)], device, fp16)

        except RuntimeError as e:
            print("Error: failed to upscale %s" % (image_list[f_no]))
            print(e)
        else:
            print(f"\t\t({i}/{count}) upscaled in %.02fs" % (time.time() - start_time), end='\r')

    # print(f"{''.join([' ']*20)}")
    print("")

    return hash, netscale, output_images



def get_frame(img, device, fp16):
    img = img.astype(np.float32) / 255.
    img = mod_crop(img, scale=4)
    img = img2tensor(img, bgr2rgb=False, float32=True).unsqueeze(0).to(device)
    return img.half() if fp16 else img
