# -*- coding: utf-8 -*-
import multiprocessing
from multiprocessing import *
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import os
import platform
import cv2
import gc
import sys
import torch
from filters.avisynth import avisynth_deinterlace
from filters.ffmpeg_deinterlace import ffmpeg_deinterlace
from filters.ffmpeg_filter import ffmpeg_filter
from filters.python import apply_python_filters
from filters.python_replace import (
    python_replace,
    python_edition,
)
from filters.utils import MAX_FRAMES_COUNT
from filters.x_gan import (
    upscale_esrgan,
    upscale_real_cugan,
    upscale_real_esrgan,
)
from utils.get_image_list import (
    get_image_list,
    STEP_INC,
)

from utils.pretty_print import *



def load_image(i, filepath):
    return i, cv2.imread(filepath, cv2.IMREAD_COLOR)


def apply_filters(db, shot, step_no_start=0, get_hashes=False):

    image_list = list()
    images = list()
    hashes = list()
    do_force = False

    # Initialize variables depending on starting step no.
    step_no = step_no_start
    if get_hashes or step_no_start == 0:
        # Start from 0
        filters = shot['filters']
        hash = ''

        # Set a do_force flag because replace has been modified
        # or new full process
        do_force = True
    else:
        # Start from a step > 0
        print_green("start from step no. %d" % (step_no))
        filters = shot['filters'][step_no:]
        hash = shot['filters'][step_no-STEP_INC]['hash']
        output_folder = os.path.join(shot['cache'], "%02d" %  (step_no-STEP_INC))
        image_list = get_image_list(shot=shot,
            folder=output_folder,
            step_no=step_no-STEP_INC,
            hash=hash)
        # if filters[0]['task'] == shot['last_task']:
            # print_yellow("No need to apply filters")
            # image_filepath = get_first_image_filepath(shot=shot,
            #     folder=output_folder,
            #     step_no=step_no-STEP_INC,
            #     hash=hash)
            # img = cv2.imread(image_filepath, cv2.IMREAD_COLOR)
            # shot['last_step']['shape'] = img.shape
            # return hashes

    if platform.system() == "Windows":
        cpu_count = int(multiprocessing.cpu_count() * (3/4))
    else:
        cpu_count = 2


    # walk through filters
    for filter in filters:
        # Current output folder
        output_folder = os.path.join(shot['cache'], "%02d" %  (step_no))

        if not get_hashes:
            if filter['save'] and not os.path.exists(output_folder):
                os.makedirs(output_folder)

            # Load frames in memory if not already done and nb of frames < max
            print_yellow("\t\t\tshot count: %d, len(images): %d, len(image_list): %d" % (
                shot['count'], len(images), len(image_list)))

            if step_no > 0 and shot['count'] < MAX_FRAMES_COUNT and len(images) != shot['count']:
                print_lightgrey("\t\t\tLoading %d images in memory, from %s" % (shot['count'], image_list[0]), flush=True)

                # images = [cv2.imread(f_input, cv2.IMREAD_COLOR) for f_input in image_list]
                images = [None] * shot['count']
                nos = list(range(shot['count']))
                with ThreadPoolExecutor(max_workers=min(cpu_count, shot['count'])) as executor:
                    work_result = {executor.submit(load_image, i, fp): list for i, fp in zip(nos, image_list)}
                    for future in concurrent.futures.as_completed(work_result):
                        i, img = future.result()
                        images[i] = img

                shot['last_step']['shape'] = images[0].shape

            elif step_no > 0:
                if shot['count'] >= MAX_FRAMES_COUNT:
                    print("Error: cannot load %d images in memory, max: %d" % (shot['count'], MAX_FRAMES_COUNT), flush=True)
                print_lightgrey("\t\t\tNo need to load images in memory, from %s" % (image_list[0]), flush=True)
        else:
            # Get hash, use an empty list
            images = [None] * shot['count']




        # xGAN
        #-----------------------------------------------------------------------
        if filter['type'] in ['real_cugan', 'real_esrgan', 'esrgan']:
            if not torch.cuda.is_available():
                print_red("\t\t\terror: cannot upscale with this GPU/CPU")
                # print_orange("\t\t\tfallback: bad quality upscale (CV2: nearest)")
                # filter_str = "scale=2:nearest"
                # hash, images = apply_python_filters(
                #     shot,
                #     images=images,
                #     image_list=image_list,
                #     step_no=step_no,
                #     filters_str=filter_str,
                #     input_hash=hash,
                #     do_save=filter['save'],
                #     output_folder=output_folder,
                #     get_hash=get_hashes,
                #     do_force=do_force)
                # if not get_hashes:
                #     print_lightgrey("\t\t\tupscale: returned %d images" % (len(images)))
                if not get_hashes:
                    sys.exit("Goodbye!")


            xgan = {
                'name': filter['type'],
                'model': '',
            }

            args = filter['str'].split(',')
            for arg in args:
                arg_name, arg_value = arg.split('=')
                xgan[arg_name] = arg_value

            # Model name is required
            if xgan['name'] == 'real_cugan':
                if 'n' not in xgan.keys():
                    sys.exit(print_red("\n(Real-CUGAN): denoise value is required"))
                # print("\n\t\t\t(Real-CUGAN) scale: %d, denoise: %d" % (int(xgan['s']), int(xgan['n'])))
                hash, scale, images = upscale_real_cugan(
                    shot=shot,
                    images=images,
                    image_list=image_list,
                    scale=int(xgan['s']),
                    denoise=int(xgan['n']),
                    directories=db['common']['directories'],
                    input_hash=hash,
                    step_no=step_no,
                    output_folder=output_folder,
                    get_hash=get_hashes,
                    do_force=do_force)
                # if not get_hashes:
                #     print("\t\t\tupscale: returned %s" % (hash))

            elif xgan['name'] == 'real_esrgan':
                if xgan['model'] == '':
                    sys.exit(print_red("\n(Real-ESRGAN) model name is required"))
                hash, scale, images = upscale_real_esrgan(
                    shot=shot,
                    images=images,
                    image_list=image_list,
                    scale=2,
                    model_name=xgan['model'],
                    directories=db['common']['directories'],
                    input_hash=hash,
                    step_no=step_no,
                    output_folder=output_folder,
                    get_hash=get_hashes,
                    do_force=do_force)
                # if not get_hashes:
                #     print("\t\t\tupscale: returned %s" % (hash))

            elif xgan['name'] == 'esrgan':
                if xgan['model'] == '':
                    sys.exit(print_red("\n(ESRGAN) model name is required"))
                hash, scale, images = upscale_esrgan(
                    shot=shot,
                    images=images,
                    image_list=image_list,
                    scale=2,
                    model_name=xgan['model'],
                    directories=db['common']['directories'],
                    input_hash=hash,
                    step_no=step_no,
                    output_folder=output_folder,
                    get_hash=get_hashes,
                    do_force=do_force)




        # Python: opencv2/scikit
        #-----------------------------------------------------------------------
        elif filter['type'] == 'python':
            previous_hash = hash

            if filter['str'] == 'replace':
                hash, image_list, images = python_replace(
                    shot,
                    images=images,
                    image_list=image_list,
                    step_no=step_no,
                    filters_str=filter['str'],
                    input_hash=hash,
                    get_hash=get_hashes)

            elif filter['str'] == 'pre_replace':
                # This task is 'edition', save images that will be used by the video editor
                hash, image_list, images = python_edition(
                    shot,
                    images=images,
                    image_list=image_list,
                    step_no=step_no,
                    filters_str=filter['str'],
                    input_hash=hash,
                    output_folder=output_folder,
                    get_hash=get_hashes)
            else:
                hash, images = apply_python_filters(
                    shot,
                    images=images,
                    step_no=step_no,
                    filters_str=filter['str'],
                    input_hash=hash,
                    do_save=filter['save'],
                    output_folder=output_folder,
                    image_list=image_list,
                    get_hash=get_hashes,
                    do_force=do_force)

                if images is None:
                    images = list()

                if not get_hashes and filter['str'] != 'deshake':
                    print_lightgrey("\t\t\tpython: returned %d images" % (len(images)))

                if hash == '':
                    # There was an error: missing paramaters, filter, etc.
                    hash = previous_hash
                    hashes.append([step_no, '', ''])
                    step_no += STEP_INC
                    if filter['str'] != 'deshake' and filter['str'] != 'rgb':
                        print_yellow("\t\t\twarning: python filter: something went wrong: %s" % (filter['str']))

                    # Exit if last task
                    if not get_hashes and filter['task'] == shot['last_task']:
                        break

                    continue

        # FFmpeg
        #-----------------------------------------------------------------------
        elif filter['type'] == 'ffmpeg':
            # print("(FFmpeg) filters=%s" % (filter['str']))

            if filter['task'] == 'deinterlace':
                # Deinterlace
                hash, images = ffmpeg_deinterlace(
                    shot=shot,
                    step_no=step_no,
                    filter_str=filter['str'],
                    output_folder=output_folder,
                    db_common=db['common'],
                    get_hash=get_hashes)

            else:
                # Other filters
                hash, images = ffmpeg_filter(
                    shot=shot,
                    images=images,
                    image_list=image_list,
                    step_no=step_no,
                    input_hash=hash,
                    filter_str=filter['str'],
                    do_save=filter['save'],
                    output_folder=output_folder,
                    db_common=db['common'],
                    get_hash=get_hashes,
                    do_force=do_force)

        # Avisynth+
        #-----------------------------------------------------------------------
        elif filter['type'] == 'avisynth':
            if filter['task'] == 'deinterlace':
                hash, images = avisynth_deinterlace(
                    shot=shot,
                    image_list=image_list,
                    step_no=step_no,
                    filters_str=filter['str'],
                    output_folder=output_folder,
                    db_common=db['common'],
                    get_hash=get_hashes)

            else:
                print_red("Error: avisynth filters are not supported")
                pprint(filter)
                sys.exit()



        # Null
        #-----------------------------------------------------------------------
        elif filter['type'] == 'null':
            if not get_hashes:
                print_cyan("(null)\tstep no. %d, filter=null, input_hash= %s" % (step_no, hash))

            # No filtering, used when we want to compare images from
            # different editions
            hashes.append([step_no, '', ''])
            step_no += STEP_INC
            continue

        # Unrecognized filter
        #-----------------------------------------------------------------------
        else:
            print_red("Error: unregonized filter:")
            pprint(filter)
            sys.exit()

        # Store hash
        hashes.append([step_no, hash, filter['task']])

        if not get_hashes:
            # Get dimensions from last image
            if images is not None and len(images) > 0:
                shot['last_step']['shape'] = images[0].shape
            elif len(image_list) > 0:
                img = cv2.imread(image_list[0], cv2.IMREAD_COLOR)
                shot['last_step']['shape'] = img.shape


        # Get the list of images which will be used as input for the next step
        if filter['str'] != 'replace':
            # note: pre_replace is not tested because it it the last task
            image_list = get_image_list(shot=shot,
                folder=output_folder,
                step_no=step_no,
                hash=hash)

        # Increment step
        step_no += STEP_INC


        # if not get_hashes:
        #     gc.collect()

        # Exit if last task
        if not get_hashes and filter['task'] == shot['last_task']:
            break
    try:
        print_purple(shot['last_step'])
    except:
        pass
    return hashes
