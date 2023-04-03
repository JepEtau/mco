# -*- coding: utf-8 -*-
import cv2
import os
import sys
import multiprocessing
from multiprocessing import *
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

from pprint import pprint


from filters.utils import MAX_FRAMES_COUNT
from utils.pretty_print import *
from utils.hash import (
    log_filter,
)
from utils.get_image_list import (
    get_image_list,
)

from filters.filters import (
    calculate_geometry_parameters,
    cv2_geometry_filter,
)




def apply_python_geometry_filter(shot, images:list, image_list:list,
    step_no, filters_str:str, input_hash:str,
    do_save:bool, output_folder:str,
    get_hash:bool=False, do_force:bool=False):

    # Set filters_str to calculate hash
    filters_str = "geometry=w=%d,crop=%s,keep_ratio=%s,fit_to_part=%s" % (
        shot['geometry']['part']['w'],
        ':'.join(list(["%d" % (x) for x in shot['geometry']['shot']['crop']])),
        'y' if shot['geometry']['shot']['keep_ratio'] else 'n',
        'y' if shot['geometry']['shot']['fit_to_part'] else 'n')

    hash = log_filter("%s,%s" % (input_hash, filters_str), shot['hash_log_file'])
    if get_hash:
        return hash, None

    # multiprocessing
    if sys.platform == 'win32':
        cpu_count = int(multiprocessing.cpu_count() * (3/4))
    else:
        cpu_count = int(multiprocessing.cpu_count() * (1/2))

    # Output images in memory
    use_memory = True if shot['count'] <= MAX_FRAMES_COUNT else False

    # Output image list
    if do_save:
        output_image_list = get_image_list(
            shot=shot,
            folder=output_folder,
            step_no=step_no,
            hash=hash)

    # Calculate values to crop/resize/add padding
    if len(images) == 0:
        img = cv2.imread(image_list[0], cv2.IMREAD_COLOR)
    else:
        img = images[0]
    geometry = calculate_geometry_parameters(shot=shot, img=img)


    # Create a list of works for multiprocessing
    count = shot['count']
    worklist = list()
    output_images = list()
    if use_memory:
        if do_save and not do_force:
            for frame_no, f_output in zip(range(count), output_image_list):
                if not os.path.exists(f_output):
                    worklist.append([frame_no, images[frame_no]])
                else:
                    output_images[frame_no] = cv2.imread(f_output, cv2.IMREAD_COLOR)
        else:
            for frame_no in range(count):
                worklist.append([frame_no, images[frame_no]])
        output_images = [None] * shot['count']
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
            work_result = {executor.submit(work_cv2_geometry_filter, work[0], work[1], geometry): list
                            for work in worklist}
            for future in concurrent.futures.as_completed(work_result):
                frame_no, img = future.result()
                if use_memory:
                    output_images[frame_no] = img
                if do_save:
                    cv2.imwrite(output_image_list[frame_no], img)
                no += 1
                print_yellow("\t\tgeometry (multi-processing): %d%%" % (int((100.0 * no)/len(worklist))), flush=True, end='\r')
    else:
        no = 0
        for work in worklist:
            frame_no, img = work_cv2_geometry_filter(work[0], work[1], geometry)
            if use_memory:
                output_images[frame_no] = img
            if do_save:
                cv2.imwrite(output_image_list[frame_no], img)
            no += 1
            print_yellow("\t\tgeometry (single process): %d%%" % (int((100.0 * no)/len(worklist))), flush=True, end='\r')
    print("\t\t                           ", end='\r')

    return hash, output_images







def work_cv2_geometry_filter(frame_no, input_img, geometry) -> list:
    # For large shot, img is provided as the filepath
    if type(input_img) is str:
        img = cv2.imread(input_img, cv2.IMREAD_COLOR)
    else:
        img = input_img

    output_img = cv2_geometry_filter(img, geometry)
    return (frame_no, output_img)

