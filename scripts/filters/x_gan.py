# -*- coding: utf-8 -*-
import cv2
import os
import sys
import time
import torch
import numpy as np
from pprint import pprint
from filters.utils import MAX_FRAMES_COUNT

from utils.hash import (
    calculate_hash,
    log_filter,
)
from utils.get_image_list import (
    get_image_list,
)
from utils.pretty_print import *



def upscale_real_cugan(shot, images:list, image_list:list, scale:int, denoise:int,
    module_path:str, input_hash, step_no, output_folder:str, get_hash:bool=False, do_force:bool=False):

    print_green(module_path)
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
        model_name = "up%dx-latest-%s.pth" % (scale, denoise_to_model[denoise])
    # else:
    #     if denoise == 5:
    #         model_name = ""

    model_path = os.path.join(module_path, "weights_v3", model_name)
    if not os.path.isfile(model_path):
        raise Exception("Error: model file %s does not exist" % (model_path))

    # ModelName="up2x-latest-no-denoise.pth"
    # ModelName="up2x-latest-denoise1x.pth"
    #{0,1,2,3,4,auto}; the larger the number, the smaller the memory consumption
    # Tile=4
    suffix = "s%d_n%d" % (scale, denoise)

    # Hash
    filter_str = "%s,%s" % (input_hash, model_name)
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
        weight_path=model_path,
        half=half,
        device=device)

    # Walk through images
    count = shot['count']
    for f_no, f_output in zip(range(count), output_image_list):
        start_time = time.time()
        torch.cuda.empty_cache()

        print("\t%s -> %s" % (image_list[f_no], f_output))

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
            img_upscaled = upscaler(
                frame=img,
                tile_mode=0,
                cache_mode=3,
                alpha=1)
            output_img = img_upscaled[:, :, ::-1]

            if use_memory:
                output_images.append(output_img)

            # Always save on SSD because this process is time consuming
            cv2.imwrite(f_output, output_img)

        except RuntimeError as e:
            print("Error: failed to upscale %s" % (image_list[f_no]))
            print(e)
        else:
            print("\tinfo: upscaled in %.02fs" % (time.time() - start_time))

    return hash, scale, output_images



def upscale_real_esrgan(shot, images:list, image_list:list,
    scale:int, model_name:str, module_path:str, input_hash:str, step_no, output_folder:str,
    get_hash:bool=False, do_force:bool=False):

    sys.path.append(module_path)
    from realesrgan.archs.srvgg_arch import SRVGGNetCompact
    from realesrgan import RealESRGANer
    from basicsr.archs.rrdbnet_arch import RRDBNet

    model_filepath = os.path.join(module_path, "weights", "%s.pth" % (model_name))
    if not os.path.isfile(model_filepath):
        sys.exit(print_red("Error: model file %s does not exist" % (model_filepath)))

    # log hash
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
        netscale = 4
    elif model_name == 'RealESRGAN_x2plus':
        suffix = "RealESRGAN_x2plus"
        netscale = 2
    elif model_name == '2x_Futsuu_Anime_Compact_130k_net_g':
        suffix = model_name
        netscale = 2
    elif model_name == 'sudo_RealESRGAN2x_Dropout_3.799.042_G':
        suffix = 'sudo_3.799.042_G'
        netscale = 2
    elif model_name.startswith('4x_'):
        suffix = model_name
        netscale = 4
    else:
        suffix = model_name
        netscale = 2

    # Hash
    filter_str = "%s,%s" % (input_hash, suffix)
    if get_hash:
        hash = calculate_hash(filter_str=filter_str)
        hash += "_" + suffix
        return hash, netscale, None
    hash = log_filter(filter_str, shot['hash_log_file'])
    hash += "_" + suffix


    print_cyan("(REAL_ESRGAN)\tstep no. %d, upscaling with model %s, input hash= %s, output hash= %s, suffix= %s" % (
        step_no, model_name, input_hash, hash, suffix))

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
        tile = 320
    elif model_name == '2x_LD-Anime_Compact_330k_net_g':
        model = SRVGGNetCompact(num_in_ch=3, num_out_ch=3, num_feat=64, num_conv=16, upscale=2, act_type='prelu')
    elif model_name == '2x_Futsuu_Anime_Compact_130k_net_g':
        model = SRVGGNetCompact(num_in_ch=3, num_out_ch=3, num_feat=64, num_conv=16, upscale=2, act_type='prelu')
    elif model_name == '1x_HurrDeblur_SuperUltraCompact_nf24-nc8_244k_net_g':
        model = SRVGGNetCompact(num_in_ch=3, num_out_ch=3, num_feat=24, num_conv=8, upscale=1, act_type='prelu')
    elif model_name == 'RealESRGAN_x2plus':
        # x2 RRDBNet model
        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=2)
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
    for f_no, f_output in zip(range(count), output_image_list):
        start_time = time.time()

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
                img=img,
                outscale=scale,
                alpha_upsampler='realesrgan')

            if use_memory:
                output_images.append(output_img)

            # Always save on SSD because this process is time consuming
            cv2.imwrite(f_output, output_img)

        except RuntimeError as e:
            print("Error: failed to upscale %s" % (image_list[f_no]))
            print(e)
        else:
            print("\tinfo: upscaled in %.02fs" % (time.time() - start_time))

    return hash, netscale, output_images



def upscale_esrgan(shot, images:list, image_list:list,
    scale:int, model_name:str, module_path:str, input_hash, step_no, output_folder:str,
    get_hash:bool=False, do_force:bool=False):

    model_filepath = os.path.join(module_path, "models", "%s.pth" % (model_name))
    if not os.path.isfile(model_filepath):
        sys.exit(print_red("Error: model file %s does not exist" % (model_filepath)))

    sys.path.append(module_path)
    from upscale import (
        AlphaOptions,
        SeamlessOptions
    )
    from filters.esrgan import Esrgan_upscale

    # Default values for upscaler
    suffix = "%s_%s" % (model_name, input_hash)
    seamless = None
    if model_name == '2x_LD-Anime_Skr_v1.0':
        suffix = "skr"
        scale = 2
    elif model_name == '1x_SSAntiAlias9x':
        suffix = "ssaa"
        scale = 1
    elif model_name == '4x-AnimeSharp':
        suffix = "AnimeSharp"
        scale = 4
        seamless = SeamlessOptions.TILE
    elif model_name == '2x_AnimeClassics_UltraLite_510K':
        suffix = "AnimeClassics"
        scale = 2
    elif model_name == '4x-UniScaleNR-Balanced':
        suffix = "4x-UniScaleNR-Balanced"
        scale = 4
    elif model_name == '4x-UniScaleNR-Strong':
        suffix = "4x-UniScaleNR-Strong"
        scale = 4
    elif model_name == '4x_DigitalFrames_2.1_Final':
        suffix = "4x_DigitalFrames"
        scale = 4
    elif model_name == '4x-AnimeSharp':
        suffix = "4x-AnimeSharp"
        scale = 4
    elif model_name == '4x_OLDIES_290000_G_FINAL_interp_03':
        suffix = "4x_OLDIES_290000"
        scale = 4
    elif model_name == '2x-UniScale_CartoonRestore-lite':
        suffix = "2x-UniScale_CartoonRestore-lite"
        scale = 2
    elif model_name == '2X_KcjpunkAnime_2.0_Lite_196496_G':
        suffix = "2X_KcjpunkAnime"
        scale = 2
    elif model_name == '4xFSDedither_Manga':
        suffix = '4xFSDedither_Manga'
        scale = 4
    elif model_name == '1x_ReFocus_V3_140000_G':
        suffix = '1x_ReFocus_V3_140000_G'
        scale = 1
    else:
        suffix = model_name

    # Hash
    filter_str = "%s,%s" % (input_hash, model_name)
    if get_hash:
        hash = calculate_hash(filter_str=filter_str)
        hash += "_" + suffix
        return hash, scale, None
    hash = log_filter(filter_str, shot['hash_log_file'])
    hash += "_" + suffix



    print_cyan("(ESRGAN)\tstep no. %d, model= %s, input hash= %s, output hash= %s, suffix= %s" % (
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
            output_img = esrgan_upscale.upscale(
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
            print("\tinfo: upscaled in %.02fs" % (time.time() - start_time))


    return hash, scale, output_images
