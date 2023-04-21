# -*- coding: utf-8 -*-
import sys
import cv2
import os
import subprocess
import torch
import numpy as np
from filters.utils import MAX_FRAMES_COUNT
from utils.pretty_print import *

from utils.hash import (
    calculate_hash,
    log_filter,
)
from utils.get_image_list import (
    get_image_list,
)


def upscale_animesr(shot, images:list, image_list:list,
    scale:int, model_name:str, directories:str, input_hash, step_no, output_folder:str,
    get_hash:bool=False, do_force:bool=False):

    module_path = os.path.join(directories['3rd_party'], directories['animesr'])
    model_filepath = os.path.join(directories['3rd_party'], "models", 'animesr', "%s.pth" % (model_name))
    if not os.path.isfile(model_filepath):
        sys.exit(print_red("Error: model file %s does not exist" % (model_filepath)))


    suffix = f"{model_name}_{input_hash}"

    # Hash
    filter_str = "%s,%s" % (input_hash, model_name)
    if get_hash:
        hash = calculate_hash(filter_str=filter_str)
        hash += "_" + suffix
        return hash, scale, None
    hash = log_filter(filter_str, shot['hash_log_file'])
    hash += "_" + suffix


    print_cyan("(ANimeSR)\tstep no. %d, upscaling with model %s, input hash= %s, output hash= %s, suffix= %s" % (
        step_no, model_name, input_hash, hash, suffix))



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


