# -*- coding: utf-8 -*-
import cv2
import os
import sys
import multiprocessing
from multiprocessing import *
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import platform

from pprint import pprint
from filters.dnn_superres import upscale_cv2_dnn_superres
from filters.ffmpeg_utils import clean_ffmpeg_filter

from filters.homography import Homography
from filters.deshake import deshake
from filters.python_geometry import (
    add_borders,
    apply_python_geometry_filter,
)
from filters.utils import MAX_FRAMES_COUNT
from utils.pretty_print import *
from utils.hash import (
    calculate_hash,
    log_filter,
)
from utils.get_image_list import (
    get_image_list,
)

from filters.filters import (
    calculate_geometry_parameters,
    cv2_bilateral_filter,
    cv2_fastNlMeansDenoisingColored,
    cv2_gaussianBlur,
    cv2_geometry_filter,
    cv2_resize,
    cv2_scale,
    sk_unsharp_mask,
    cv2_edge_sharpen_sobel,
    cv2_morphology_ex
)
from filters.python_rgb import apply_python_rgb_filter


def apply_python_filters(shot:dict, images:list, image_list:list,
    step_no, filters_str:str, input_hash:str,
    do_save:bool, output_folder:str,
    get_hash:bool=False, do_force:bool=False):

    filters_str = clean_ffmpeg_filter(filters_str)

    if not get_hash:
        print_cyan("(cv2, skimage)\tstep no. %d, filter=[%s], input_hash= %s" % (step_no, filters_str, input_hash))

    # Get filter names and arguments
    filter_list = list()
    for filter_str in filters_str.split(','):
        if filter_str == '':
            continue
        args = filter_str.split('=')
        filter_name = args[0]
        if len(args) > 1:
            args = args[1].split(':')
            filter_list.append([filter_name, args])
        else:
            filter_list.append([filter_name, []])


    # multiprocessing
    if platform.system() == "Windows":
        cpu_count = int(multiprocessing.cpu_count() * (3/4))
    else:
        cpu_count = int(multiprocessing.cpu_count() * (1/2))

    # Output images in memory
    use_memory = True if shot['count'] <= MAX_FRAMES_COUNT else False

    # Process all images
    filter_name = filter_list[0][0]

    if filter_name == 'add_borders':
        # Add borders
        return add_borders(
            shot=shot,
            images=images,
            image_list=image_list,
            step_no=step_no,
            filters_str=filters_str,
            input_hash=input_hash,
            get_hash=get_hash,
            do_save=do_save,
            output_folder=output_folder)


    elif filter_name == 'deshake':
        # Deshake
        hash, output_images = deshake(
            shot=shot,
            images=images,
            image_list=image_list,
            step_no=step_no,
            input_hash=input_hash,
            get_hash=get_hash,
            do_force=do_force)

        if get_hash:
            return hash, None

        if do_save and hash != '':
            # Output image list
            output_image_list = get_image_list(
                shot=shot,
                folder=output_folder,
                step_no=step_no,
                hash=hash)

            # Discard if output files already exist
            if not do_force:
                do_extract = False
                for f in output_image_list:
                    if not os.path.exists(f):
                        do_extract = True
                        break
                if not do_extract:
                    print("\t\t\timages already exist")
                    return hash, output_images

            # Write images
            print("\t\t\tinfo: saving images")
            for img, f_output in zip(output_images, output_image_list):
                cv2.imwrite(filename=f_output, img=img)

        return hash, output_images


    elif filter_name == 'stabilize':
        sys.exit(print_red("Smooth stabilize not yet supported"))


    elif filter_name == 'homography':
        # Deshake
        homography = Homography()
        hash, output_images = homography.stabilize(
            images=images,
            ref='start',
            step_no=step_no,
            input_hash=input_hash,
            do_force=True,
            do_log=False,
            get_hash=get_hash)

        if get_hash:
            return hash

        if do_save:
            # Output image list
            output_image_list = get_image_list(
                shot=shot,
                folder=output_folder,
                step_no=step_no,
                hash=hash)

            # Discard if output files already exist
            do_extract = False
            for f in output_image_list:
                if not os.path.exists(f):
                    do_extract = True
                    break
            if not do_extract:
                print("\t\t\timages already filtered")
                return hash

            # Write images
            for img, f_output in zip(output_images, output_image_list):
                cv2.imwrite(filename=f_output, img=img)

        return hash, output_images


    elif filter_name == 'rgb':
        return apply_python_rgb_filter(
            shot=shot,
            images=images,
            image_list=image_list,
            step_no=step_no,
            filters_str=filters_str,
            input_hash=input_hash,
            get_hash=get_hash,
            do_save=do_save,
            output_folder=output_folder)


    elif filter_name == 'geometry':
        if 'geometry' not in shot.keys():
            # Geometry not defined
            sys.exit(print_red("\t\t\twarning: no geometry defined for shot no. %d" % (shot['no'])))
            hash = ''
            return hash, None

        return apply_python_geometry_filter(
            shot=shot,
            images=images,
            image_list=image_list,
            step_no=step_no,
            filters_str=filters_str,
            input_hash=input_hash,
            get_hash=get_hash,
            do_save=do_save,
            output_folder=output_folder)




    elif filter_name.startswith('dnn_superres'):
        return upscale_cv2_dnn_superres(
            shot=shot,
            images=images,
            image_list=image_list,
            step_no=step_no,
            filters_str=filters_str,
            input_hash=input_hash,
            get_hash=get_hash,
            do_save=do_save,
            output_folder=output_folder)


    # Other filters
    filters = "%s,%s" % (input_hash, filters_str)
    if get_hash:
        hash = calculate_hash(filter_str=filters)
        return hash, None
    hash = log_filter(filters, shot['hash_log_file'])

    # Output image list
    if do_save:
        output_image_list = get_image_list(
            shot=shot,
            folder=output_folder,
            step_no=step_no,
            hash=hash)



    # Filter frame by frame: create a list of works for multiprocessing
    count = shot['count']
    worklist = list()
    output_images = list()
    if use_memory:
        output_images = [None] * shot['count']
        if do_save and not do_force:
            for frame_no, f_output in zip(range(count), output_image_list):
                if not os.path.exists(f_output):
                    worklist.append([frame_no, images[frame_no]])
                else:
                    output_images[frame_no] = cv2.imread(f_output, cv2.IMREAD_COLOR)
        else:
            for frame_no in range(count):
                worklist.append([frame_no, images[frame_no]])
    else:
        # Do not load images in memeory
        if not do_force:
            for frame_no, f_output in zip(range(count), output_image_list):
                if not os.path.exists(f_output):
                    worklist.append([frame_no, image_list[frame_no]])
        else:
            for frame_no in range(count):
                worklist.append([frame_no, image_list[frame_no]])


    if len(worklist) == 0:
        sys.exit(print_red("error: apply_python_filters: worklist is empty"))

    # Execute the pool of works
    if cpu_count > 1:
        no = 0
        with ThreadPoolExecutor(max_workers=min(cpu_count, len(worklist))) as executor:
            work_result = {executor.submit(work_python_filters, work[0], work[1], filter_list): list
                            for work in worklist}
            for future in concurrent.futures.as_completed(work_result):
                frame_no, img = future.result()
                if use_memory:
                    output_images[frame_no] = img
                if do_save:
                    cv2.imwrite(output_image_list[frame_no], img)
                no += 1
                print_yellow("\t\tfiltering (multi-processing): %d%%" % (int((100.0 * no)/len(worklist))), flush=True, end='\r')
    else:
        no = 0
        for work in worklist:
            frame_no, img = work_python_filters(work[0], work[1], filter_list)
            if use_memory:
                output_images[frame_no] = img
            if do_save:
                cv2.imwrite(output_image_list[frame_no], img)
            no += 1
            print_yellow("\t\tfiltering (single process): %d%%" % (int((100.0 * no)/len(worklist))), flush=True, end='\r')
    print("\t\t                                                  ", end='\r')

    return hash, output_images






def work_cv2_geometry_filter(frame_no, input_img, geometry) -> list:
    if type(input_img) is str:
        img = cv2.imread(input_img, cv2.IMREAD_COLOR)
    else:
        img = input_img
    output_img = cv2_geometry_filter(img, geometry)
    return (frame_no, output_img)


def work_python_filters(frame_no, input_img, filter_list) -> list:
    # For large shot, img is provided as the filepath
    if type(input_img) is str:
        img = cv2.imread(input_img, cv2.IMREAD_COLOR)
    else:
        img = input_img
    # reenable this for edge_sharpen_sobel:
    # initial_image = img.copy()

    for function, args in filter_list:

        if function == 'unsharp_mask':
            img = sk_unsharp_mask(img,
                radius=int(args[0]),
                amount=float(args[1]))

        elif function == 'bilateralFilter':
            img = cv2_bilateral_filter(img,
                diameter=int(args[0]),
                sigmaColor=float(args[1]),
                sigmaSpace=float(args[2]))

        elif function == 'fastNlMeansDenoisingColored':
            img = cv2_fastNlMeansDenoisingColored(img,
                h=int(args[0]),
                hColor=int(args[1]),
                templateWindowSize=int(args[2]),
                searchWindowSize=int(args[3]))

        elif function == 'gaussianBlur':
            img = cv2_gaussianBlur(img,
                radius=int(args[0]),
                sigma=float(args[1]))

        elif function =='edge_sharpen_sobel':
            img = cv2_edge_sharpen_sobel(img,
                denoised_image=initial_image,
                k_size=int(args[0]),
                blend_factor=float(args[1]))

        elif function == 'morphologyEx':
            img = cv2_morphology_ex(img,
                type=args[0],
                radius=int(args[1]),
                iterations=int(args[2]))

        elif function == 'scale':
            img = cv2_scale(img,
                scale=int(args[0]),
                interpolation=args[1])

        elif function == 'resize':
            img = cv2_resize(img,
                width=int(args[0]),
                height=int(args[1]),
                interpolation=args[2])
        else:
            sys.exit("warning: missing filter: %s" % (function))

    return (frame_no, img)
