# -*- coding: utf-8 -*-
import sys
import multiprocessing
from multiprocessing import *
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import as_completed
import platform
import time
import cv2
from pprint import pprint

from utils.pretty_print import *


def load_images(count, image_filepaths):
    start_time = time.time()

    # images = [cv2.imread(f_input, cv2.IMREAD_COLOR) for f_input in image_list]
    loaded_images = [None] * count

    if count > len(image_filepaths):
        print_red(f"Error: load_images: {count} > {len(image_filepaths)}")

    cpu_count = multiprocessing.cpu_count()
    cpu_count = min(int(cpu_count * (3/4)), cpu_count-2)

    if True:
        with ThreadPoolExecutor(max_workers=min(cpu_count, count)) as executor:
            works = [[no, image_filepaths[no]] for no in range(count)]
            futures = [executor.submit(__load_image, w) for w in works]
            for future in concurrent.futures.as_completed(futures):
                (i, img) = future.result()
                loaded_images[i] = img

    else:
        worker_count = int(count / cpu_count)
        img_count = cpu_count * worker_count
        remaining_img_count = count - img_count

        with ProcessPoolExecutor(worker_count) as executor:
            futures = list()

            for i in range(0, img_count, worker_count):
                futures.append(executor.submit(__load_images, [[no, image_filepaths[no]] for no in range(i, i+worker_count)]))

            # Put the img in the list
            for future in as_completed(futures):
                i_imgs = future.result()
                for (no, img) in i_imgs:
                    loaded_images[no] = img
                    # print(f"loaded image no. {no}")

        if remaining_img_count > 0:
            i_imgs = __load_images([[no, image_filepaths[no]] for no in range(img_count, count)])
            for (no, img) in i_imgs:
                loaded_images[no] = img

    elapsed_time = time.time() - start_time
    print(f"loaded {count} images in {elapsed_time:.02f}s (cpu count={cpu_count})")
    sys.exit()

    return loaded_images



def __load_images(i_fps):
    # List of [i, image_filepath]
    with ThreadPoolExecutor(len(i_fps)) as executor:
        futures = [executor.submit(__load_image, i_fp) for i_fp in i_fps]
        i_img =  [future.result() for future in futures]
        return i_img



def __load_image(i_fp):
    i, filepath = i_fp
    # print(f"load no. {i}: {filepath}")
    return i, cv2.imread(filepath, cv2.IMREAD_COLOR)