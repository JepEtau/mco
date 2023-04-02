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
    cv2_rgb_filter,
)




def apply_python_rgb_filter(shot, images:list, image_list:list,
        step_no, filters_str:str, input_hash:str,
        do_save:bool, output_folder:str,
        get_hash:bool=False):

        try:
            filters_str += "=%s" % (shot['curves']['k_curves'])
        except:
            print_yellow("\t\t\tNo RGB curves")
            return '', None

        hash = log_filter("%s,%s" % (input_hash, filters_str), shot['hash_log_file'])
        if get_hash:
            return hash, None

        # Output images in memory
        use_memory = True if shot['count'] <= MAX_FRAMES_COUNT else False

        # Output image list
        if do_save:
            output_image_list = get_image_list(
                shot=shot,
                folder=output_folder,
                step_no=step_no,
                hash=hash)

        # RGB correction frame by frame: create a list of works for multiprocessing
        count = shot['count']
        worklist = list()
        output_images = [None] * shot['count']
        if do_save:
            for frame_no, f_output in zip(range(count), output_image_list):
                if not os.path.exists(f_output):
                    worklist.append([frame_no, images[frame_no]])
                elif use_memory:
                    output_images[frame_no] = cv2.imread(f_output, cv2.IMREAD_COLOR)
        else:
            for frame_no in range(count):
                worklist.append([frame_no, images[frame_no]])

        # Execute the pool of works
        no = 0
        with ThreadPoolExecutor(max_workers=min(cpu_count, len(worklist))) as executor:
            work_result = {executor.submit(work_cv2_rgb_filter, work[0], work[1], shot['curves']['lut']): list
                            for work in worklist}
            for future in concurrent.futures.as_completed(work_result):
                frame_no, img = future.result()
                if use_memory:
                    output_images[frame_no] = img
                if do_save:
                    cv2.imwrite(output_image_list[frame_no], img)
                no += 1
                print_yellow("\t\t\tapplying RGB curves: %d%%" % (int((100.0 * no)/len(worklist))), flush=True, end='\r')
        print("\t\t\t                           ", end='\r')

        return hash, output_images





def work_cv2_rgb_filter(frame_no, img, lut) -> list:
    output_img = cv2_rgb_filter(img, lut)
    return (frame_no, output_img)

