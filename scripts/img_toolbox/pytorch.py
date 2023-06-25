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

def upscale_pytorch(shot, images:list, image_list:list,
    model_name:str, directories:str, input_hash, step_no, output_folder:str,
    get_hash:bool=False, do_force:bool=False):

    module_path = os.path.join(directories['3rd_party'], directories['esrgan'])
    model_filepath = os.path.join(directories['3rd_party'],
        "models", 'pytorch',
        f"{model_name}{'.pth' if not model_name.endswith('.pth') else ''}")
    if not os.path.isfile(model_filepath):
        sys.exit(print_red("Error: model file %s does not exist" % (model_filepath)))

    sys.path.append(module_path)
    from upscale import (
        AlphaOptions,
        SeamlessOptions
    )
    from img_toolbox.esrgan import Esrgan_upscale

    # Default values for upscaler
    suffix = f"{model_name}_{input_hash}"
    seamless = None
    if model_name == 'realesr-animevideov3':
        suffix = model_name
        scale = 4
    elif model_name == 'RealESRGAN_x4plus_anime_6B':
        suffix = model_name
        scale = 4
    elif model_name == '2x_LD-Anime_Skr_v1.0':
        suffix = "skr"
    elif model_name == '4x-AnimeSharp':
        suffix = "AnimeSharp"
        seamless = SeamlessOptions.TILE
    else:
        suffix = model_name

    match = re.match("^([\d]{1})[x]{1}.*", model_name.lower())
    if match is not None:
        scale = int(match.group(1))
    else:
        match = re.match(".*x([\d]{1}).*", model_name.lower())
        if match is not None:
            scale = int(match.group(1))
        else:
            scale = 2
    # Hash
    filter_str = f"{input_hash},{suffix}"
    if get_hash:
        hash = calculate_hash(filter_str=filter_str)
        hash += "_" + suffix
        return hash, scale, None
    hash = log_filter(filter_str, shot['hash_log_file'])
    hash += "_" + suffix



    print_cyan(f"(PyTorch)\tstep no. {step_no}, ({scale}x) upscaling, model {model_name}, input hash={input_hash}, output hash={hash}, suffix={suffix}")


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


    # Load model
    esrgan_upscale = Esrgan_upscale(
        seamless=seamless,
        cpu=cpu,
        device_id=device_id,
        fp16=fp16)
    esrgan_upscale.load_model(model_filepath)


    # Walk through images
    count = shot['count']
    i = 0
    for f_no, f_output in zip(range(count), output_image_list):
        start_time = time.time()
        i += 1

        # print("\t%s -> %s" % (image_list[f_no], f_output))

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
            output_img = esrgan_upscale.run(
                img=img,
                scale=scale)

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




def upscale_real_esrgan(shot, images:list, image_list:list,
    model_name:str, directories:str, input_hash:str, step_no, output_folder:str,
    get_hash:bool=False, do_force:bool=False):

    module_path = os.path.join(directories['3rd_party'], directories['real_esrgan'])
    sys.path.append(module_path)
    from realesrgan.archs.srvgg_arch import SRVGGNetCompact
    from realesrgan import RealESRGANer
    from basicsr.archs.rrdbnet_arch import RRDBNet

    model_filepath = os.path.join(directories['3rd_party'], "models", 'real_esrgan', "%s.pth" % (model_name))
    if not os.path.isfile(model_filepath):
        sys.exit(print_red("Error: model file %s does not exist" % (model_filepath)))

    # log hash
    netscale = -1
    if model_name == 'realesr-animevideov3':
        suffix = "animevideov3"
        netscale = 4
    elif model_name == 'RealESRGAN_x4plus_anime_6B':
        suffix = "x4plus_anime_6B"
        netscale = 4
    elif model_name == '1x_AnimeUndeint_Compact_130k_net_g':
        suffix = "AnimeUndeint"
        netscale = 1
    elif model_name == '2x_LD-Anime_Compact_330k_net_g':
        suffix = "2x_LD-Anime_Compact_330k_net_g"
    elif model_name == 'RealESRGAN_x2plus':
        suffix = "RealESRGAN_x2plus"
        netscale = 2
    elif model_name == '2x_Futsuu_Anime_Compact_130k_net_g':
        suffix = model_name
    elif model_name == 'sudo_RealESRGAN2x_Dropout_3.799.042_G':
        suffix = 'sudo_3.799.042_G'
        netscale = 2
    elif model_name == '2xHFA2kCompact_net_g_74000':
        suffix = 'HFA2kCompact_net_g_74000'
    else:
        suffix = model_name

    match = re.match("^([\d]{1})[xX]{1}.*", model_name)
    if match is not None:
        netscale = int(match.group(1))

    if netscale == -1:
        sys.exit(print_red(f"Error, cannot find netscale for model {model_name}"))

    # Hash
    filter_str = f"{input_hash},{suffix}"
    if get_hash:
        hash = calculate_hash(filter_str=filter_str)
        hash += "_" + suffix
        return hash, netscale, None
    hash = log_filter(filter_str, shot['hash_log_file'])
    hash += "_" + suffix


    print_cyan(f"(REAL_ESRGAN)\tstep no. {step_no}, ({netscale}x) upscaling, model {model_name}, input hash={input_hash}, output hash={hash}, suffix={suffix}")

    # Default values for upscaler
    dni_weight = None
    tile = 0
    tile_pad = 10
    pre_pad = 0

    # Verify that a compatible GPU is available (CUDA)
    if torch.cuda.is_available():
        gpu_id = 0
        fp16 = True
    else:
        print_orange("Warning: using CPU")
        gpu_id = None
        fp16 = False

    # Generate a list of output images
    output_image_list = get_image_list(
        shot=shot,
        folder=output_folder,
        step_no=step_no,
        hash=hash)
    output_images = list()

    # Output images in memory
    use_memory = True if shot['count'] <= MAX_FRAMES_COUNT else False


    # Initialize module
    scale = netscale
    if model_name == 'realesr-animevideov3':
        # x4 VGG-style model (XS size)
        model = SRVGGNetCompact(
            num_in_ch=3,
            num_out_ch=3,
            num_feat=64,
            num_conv=16,
            upscale=4,
            act_type='prelu')
    elif model_name == 'RealESRGAN_x4plus_anime_6B':
        # x4 RRDBNet model with 6 blocks
        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=6, num_grow_ch=32, scale=4)
    elif model_name == '2x_LD-Anime_Compact_330k_net_g':
        model = SRVGGNetCompact(num_in_ch=3, num_out_ch=3, num_feat=64, num_conv=16, upscale=2, act_type='prelu')
    elif model_name == '2x_Futsuu_Anime_Compact_130k_net_g':
        model = SRVGGNetCompact(num_in_ch=3, num_out_ch=3, num_feat=64, num_conv=16, upscale=2, act_type='prelu')
    elif model_name == '2xHFA2kCompact_net_g_74000':
        model = SRVGGNetCompact(num_in_ch=3, num_out_ch=3, num_feat=64, num_conv=16, upscale=2, act_type='prelu')
    elif model_name == '1x_HurrDeblur_SuperUltraCompact_nf24-nc8_244k_net_g':
        model = SRVGGNetCompact(num_in_ch=3, num_out_ch=3, num_feat=24, num_conv=8, upscale=1, act_type='prelu')
    elif model_name == 'RealESRGAN_x2plus':
        # x2 RRDBNet model
        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=2)
    elif 'compact' in model_name.lower():
        model = SRVGGNetCompact(num_in_ch=3, num_out_ch=3, num_feat=64, num_conv=16, upscale=netscale, act_type='prelu')
    else:
        sys.exit(print_red("error: model %s is not initialized" % (model_name)))

    # Load model
    upscaler = RealESRGANer(
        scale=netscale,
        model_path=model_filepath,
        dni_weight=dni_weight,
        model=model,
        tile=tile,
        tile_pad=tile_pad,
        pre_pad=pre_pad,
        half=fp16,
        gpu_id=gpu_id)


    # Walk through images
    count = shot['count']
    i = 0
    print(f"upscale factor: {netscale}")
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

            # Upscale
            output_img, _ = upscaler.enhance(
                img=img, alpha_upsampler='realesrgan')

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
    return hash, netscale, output_images


