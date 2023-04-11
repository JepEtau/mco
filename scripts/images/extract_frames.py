# -*- coding: utf-8 -*-
import sys

import cv2
import gc
import os
import time
from pprint import pprint

import multiprocessing
from multiprocessing import *
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

from utils.common import K_GENERIQUES
from filters.ffmpeg_deinterlace import (
    ffmpeg_deinterlace_single_frame,
    ffmpeg_deinterlace_and_pre_upscale_single_frame,
)
from images.frames import consolidate_frame_list_for_study
from filters.filters import (
    filter_pre_upscale,
    filter_denoise,
    filter_sharpen,
    filter_rgb,
)
study_mode = True


def process_single_frame(db_common:dict, work_no:int, frame:dict) -> None:
    tasks = frame['tasks'].copy()
    force = frame['force']
    print("%d - %d: %s" % (work_no, frame['no'], ', '.join(tasks)), flush=True)
    # pprint(frame)

    # print("processing frame: k_ed=%s, no=%d" % (frame['k_ed'], frame['no']))
    # Define default values and images

    # print(frame['tasks'])
    # pprint(frame['filters'])
    # sys.exit()
    img_ffmpeg = None
    if 'deinterlace' in tasks:
        # FFMPEG: Deinterlace only
        if (frame['filters']['ffmpeg']['pre_upscale'] is None
            and frame['filters']['ffmpeg']['upscale'] is None):
            print("\t\tFFMPEG: Deinterlace only")
            img_ffmpeg = ffmpeg_deinterlace_single_frame(db_common, frame)
            # patch: force the image to be saved, needed for AI super resolution, ncnn implementation
            # if tasks[-1] == 'deinterlace':
            if True:
                # print("\t\tsave as %s" % (frame['filepath']['deinterlace']))
                cv2.imwrite(frame['filepath']['deinterlace'], img_ffmpeg)
            tasks.remove('deinterlace')

        # Deinterlace and pre-upscale:
        elif ('pre_upscale' in tasks
            and frame['filters']['ffmpeg']['upscale'] is None
            and frame['filters']['ffmpeg']['pre_upscale'] is not None):
            print("\t\tFFMPEG: Deinterlace and pre-upscale")
            img_ffmpeg = ffmpeg_deinterlace_and_pre_upscale_single_frame(db_common, frame)
            tasks.remove('deinterlace')
            tasks.remove('pre_upscale')
            # patch: force the image to be saved, needed for AI super resolution, ncnn implementation
            # if tasks[-1] == 'pre_upscale':
            if True:
                cv2.imwrite(frame['filepath']['pre_upscale'], img_ffmpeg)
            if frame['filters']['opencv']['upscale'] is None:
                pprint(frame)
                sys.exit("process_single_frame: missing upscale filter for %s:%s:%s" % (frame['k_ed'], frame['k_ep'], frame['k_part']))

        # Deinterlace and upscale
        elif 'upscale' in tasks and frame['filters']['ffmpeg']['upscale'] is not None:
            print("\t\tFFMPEG: Deinterlace, pre_upscale and upscale")
            img_ffmpeg = ffmpeg_deinterlace_and_pre_upscale_single_frame(db_common, frame)
            # patch: force the image to be saved, needed for AI super resolution, ncnn implementation
            # if tasks[-1] == 'upscale':
            if True:
                cv2.imwrite(frame['filepath']['upscale'], img_ffmpeg)
            tasks.remove('deinterlace')
            try:
                tasks.remove('pre_upscale')
            except:
                pass
            tasks.remove('upscale')

        # Other cases: deinterlace only
        else:
            # print("\t\t\tFFMPEG: Deinterlace only")
            img_ffmpeg = ffmpeg_deinterlace_single_frame(db_common, frame)
            # patch: force the image to be saved, needed for AI super resolution, ncnn implementation
            # if tasks[-1] == 'deinterlace':
            if True:
                cv2.imwrite(frame['filepath']['deinterlace'], img_ffmpeg)
            tasks.remove('deinterlace')


    # Pre_upscale image
    img_pre_upscaled = None
    do_pre_upscale = False
    if 'pre_upscale' in tasks:
        print("\t\tpre_upscale filter:", frame['filters']['opencv']['pre_upscale'])
        if 'upscale' in tasks and (not os.path.exists(frame['filepath']['upscale']) or force):
            # pre_upscae is required
            do_pre_upscale = True

        if frame['filters']['opencv']['pre_upscale'] is not None or force:
            do_pre_upscale = True

        # print("\t\t\tpre_upscale image: %d" % (frame['no']))
        if (not os.path.exists(frame['filepath']['pre_upscale']) and do_pre_upscale) or force:
            img_pre_upscaled = filter_pre_upscale(frame, img_ffmpeg)

        if img_pre_upscaled is None:
            # There is no defined filter, use the input image
            print("\t\twarning: no pre_upscale filters or already exists")
            img_pre_upscaled = img_ffmpeg
        elif tasks[-1] == 'pre_upscale':
            cv2.imwrite(frame['filepath']['pre_upscale'], img_pre_upscaled)
        tasks.remove('pre_upscale')
    else:
        img_pre_upscaled = img_ffmpeg
    if frame['filters']['opencv']['upscale'] is not None:
        # Save because the upscale filter requires a file (xxxGAN)
        cv2.imwrite(frame['filepath']['pre_upscale'], img_pre_upscaled)

    # Upscale image
    img_upscaled = None
    if 'upscale' in tasks:
        print("\t\tupscale image: %d" % (frame['no']))
        print("\t\tuse %s" % (frame['filepath']['upscale']))
        if not os.path.exists(frame['filepath']['upscale']) or force:
            # return (work_no, tasks)
            returned_value = filter_upscale_sr(frame, img_pre_upscaled)
            if returned_value is None:
                # There is no defined filter, or an error occured, or used sr
                # sys.exit("Error: upscaling frame no. %d has failed" % (frame['no']))
                # Used super resolution
                img_upscaled = cv2.imread(frame['filepath']['upscale'], cv2.IMREAD_COLOR)
            elif tasks[-1] == 'upscale':
                cv2.imwrite(frame['filepath']['upscale'], returned_value)
                img_upscaled = returned_value
            else:
                img_upscaled = returned_value
        tasks.remove('upscale')
    else:
        img_upscaled = img_pre_upscaled

    # Denoise image
    img_denoised = None
    if 'denoise' in tasks:
        if img_upscaled is None:
            print("\t\t!warning: using upscaled image: %s " % (frame['filepath']['upscale']))
            img_upscaled = cv2.imread(frame['filepath']['upscale'], cv2.IMREAD_COLOR)

        # print("denoise image: %d" % (frame['no']))
        if True:
            img_denoised = filter_denoise(frame, img_upscaled)

        if img_denoised is None:
            # There is no defined filter, use the input image
            print("no denoise filters")
            img_denoised = img_upscaled
        elif tasks[-1] == 'denoise':
            cv2.imwrite(frame['filepath']['denoise'], img_denoised)
        tasks.remove('denoise')
    else:
        img_denoised = img_upscaled

    # Sharpen image
    img_sharpened = None
    if 'sharpen' in tasks:
        img_sharpened = filter_sharpen(frame, img_denoised)
        cv2.imwrite(frame['filepath']['sharpen'], img_sharpened)
        tasks.remove('sharpen')
    else:
        img_sharpened = img_denoised



    is_rgb_valid = False
    if 'rgb' in tasks:
        # print("apply RGB curves: %d" % (frame['no']))
        is_rgb_valid = False
        try:
            img_rgb = filter_rgb(frame, img_sharpened)
            if tasks[-1] == 'rgb':
                cv2.imwrite(frame['filepath']['rgb'], img_rgb)
            is_rgb_valid = True
        except:
            # no RGB curves
            # print("no RGB curves for shot %d" % (frame['shot_no']))
            img_rgb = img_sharpened
        tasks.remove('rgb')


    # if 'geometry' in tasks:
    #     # print("geometry: %d" % (frame['no']))
    #     # pprint(frame['geometry'])
    #     if img_rgb is None:
    #         img_rgb = cv2.imread(frame['filepath']['rgb'], cv2.IMREAD_COLOR)
    #     img_finalized = filter_geometry(frame, img_rgb)
    #     if img_finalized is not None:
    #         cv2.imwrite(frame['filepath']['geometry'], img_finalized)
    #     tasks.remove('geometry')
    # else:
    #     if is_rgb_valid:
    #         cv2.imwrite(frame['filepath']['rgb'], img_rgb)


    return (work_no, tasks)




def process_frames(db, frames, cpu_count):
    db_common = {
        'common': {
            'settings': {
                'ffmpeg_exe': db['common']['settings']['ffmpeg_exe'],
                'verbose': db['common']['settings']['verbose']
            },
            'process': db['common']['process'],
            'directories': {
                'nnedi3_weights': db['common']['directories']['nnedi3_weights'],
                'realcugan_ncnn_vulkan': db['common']['directories']['realcugan_ncnn_vulkan'],
                'realcugan_ncnn_vulkan_win32': db['common']['directories']['realcugan_ncnn_vulkan_win32'],
                'realesrgan_ncnn_vulkan': db['common']['directories']['realesrgan_ncnn_vulkan'],
                'realesrgan_ncnn_vulkan_win32': db['common']['directories']['realesrgan_ncnn_vulkan_win32'],
            }
        }
    }

    worklist = list([i, frames[i]] for i in range(len(frames)))

    with ThreadPoolExecutor(max_workers=cpu_count) as executor:
        work_result = {executor.submit(process_single_frame, db_common, work[0], work[1]): None
                        for work in worklist}

        for future in concurrent.futures.as_completed(work_result):
            work_no, tasklist = future.result()
            f = worklist[work_no][1]
            f['tasks'] = tasklist.copy()

    # Clean useless variables
    del worklist
    gc.collect()



def extract_frames_for_study(db, k_ed, k_ep, k_part, tasks, force:bool=False, shot_min:int=0, shot_max:int=999999):
    # print("%s.extract_frames_for_study: %s:%s:%s, tasks=%s" % (__name__, k_ed, k_ep, k_part, ', '.join(tasks)))

    # Use the default edition/episode if none specified
    k_ed_src = k_ed
    k_ep_src = k_ep
    if k_ed == '':
        if k_part in K_GENERIQUES:
            # Use the edition defined as src unless specified as argument
            # k_ed_src = db[k_part]['target']['video']['src']['k_ed']
            if k_ep == 'ep00':
                k_ep_src = db[k_part]['target']['video']['src']['k_ep']
        else:
            sys.exit("extract_frames_for_study: no specified edition")

    # Get the list of frames for studies
    frames = consolidate_frame_list_for_study(db,
        k_ed_src, k_ep_src, k_part,
        tasks,
        force=force)
    # pprint(frames)
    # sys.exit()
    if frames is None:
        sys.exit("Error: no frame to extract")

    # Extract only a few settings for the process
    # db_common = {
    #     'common': {
    #         'settings': {
    #             'verbose': db['common']['settings']['verbose'],
    #         },
    #         'process': db['common']['process'],
    #         'directories': {
    #             'frames': db['common']['directories']['frames'],
    #             'nnedi3_weights': db['common']['directories']['nnedi3_weights'],
    #             'realcugan_ncnn_vulkan': db['common']['directories']['realcugan_ncnn_vulkan'],
    #             'realcugan_ncnn_vulkan_win32': db['common']['directories']['realcugan_ncnn_vulkan_win32'],
    #             'realesrgan_ncnn_vulkan': db['common']['directories']['realesrgan_ncnn_vulkan'],
    #             'realesrgan_ncnn_vulkan_win32': db['common']['directories']['realesrgan_ncnn_vulkan_win32'],
    #         }
    #     }
    # }

    # Create output directory
    frames_directory = db['common']['directories']['frames']
    if not os.path.exists(frames_directory):
        os.makedirs(frames_directory)


    # Create a list of works
    worklist = list()
    no = 0
    for i in range(len(frames)):
        if frames[i]['tasks']:
            worklist.append([no, frames[i]])
            no += 1


    print("Number of cpu: %d" % (multiprocessing.cpu_count()))
    cpu_count = int(3 * multiprocessing.cpu_count() / 4)

    startTime = time.time()
    # Patch to 1 for AI SR
    # with ThreadPoolExecutor(max_workers=min(1, len(frames))) as executor:
    #     work_result = {executor.submit(process_single_frame, db_common, work[0], work[1]): None
    #                     for work in worklist}

    #     for future in concurrent.futures.as_completed(work_result):
    #         work_no, tasklist = future.result()
    #         f = worklist[work_no][1]
    #         f['tasks'] = tasklist.copy()

    for work in worklist:
        process_single_frame(db_common, work[0], work[1])

    print("=> done in %.04fs" % (time.time() - startTime), flush=True)

