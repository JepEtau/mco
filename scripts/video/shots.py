# -*- coding: utf-8 -*-
import sys

import gc
import os
import os.path
from copy import deepcopy
import cv2

import multiprocessing
from multiprocessing import *
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

from pprint import pprint

from images.filtering import (
    filter_denoise,
    filter_rgb,
    filter_upscale,
    filter_sharpen,
    filter_geometry,
)
from images.frames import (
    create_framelist_from_shot,
)
from utils.consolidate_shots import consolidate_shot
from utils.ffmpeg import (
    ffmpeg_deinterlace_and_pre_upscale_shot,
    ffmpeg_deinterlace_shot,
    ffmpeg_deinterlace_and_upscale_shot,
)
from utils.tasks import simplify_tasks
from video.effects import (
    effect_loop_and_fadeout,
    effect_fadeout,
)


def extract_frames_from_shot(db_common:dict, shot:dict) -> None:
    tasks = shot['tasks'].copy()
    extracted_images_count = None

    if 'deinterlace' not in tasks:
        return

    # Deinterlace only
    if 'upscale' not in tasks:
        print("\t\t\tFFMPEG: deinterlace only")
        extracted_images_count = ffmpeg_deinterlace_shot(db_common, shot)
        tasks.remove('deinterlace')

    # Deinterlace and pre-upscale:
    elif ('pre_upscale' in tasks and shot['filters']['ffmpeg']['upscale'] is None):
        print("\t\t\tFFMPEG: deinterlace and pre-upscale, upscale done by opencv")
        extracted_images_count = ffmpeg_deinterlace_and_pre_upscale_shot(db_common, shot)
        tasks.remove('deinterlace')
        tasks.remove('pre_upscale')
        if shot['filters']['opencv']['upscale'] is None:
            sys.exit("Missing upscale filter for %s:%s:%s" % (shot['k_ed'], shot['k_ep'], shot['k_part']))

    # Deinterlace and upscale
    elif 'upscale' in tasks and shot['filters']['ffmpeg']['upscale'] is not None:
        print("\t\t\tFFMPEG: deinterlace, pre_upscale and upscale")
        extracted_images_count = ffmpeg_deinterlace_and_upscale_shot(db_common, shot)
        tasks.remove('deinterlace')
        try: tasks.remove('pre_upscale')
        except: pass
        tasks.remove('upscale')

    # Other cases: deinterlace only
    else:
        print("\t\t\tFFMPEG: else, deinterlace")
        extracted_images_count = ffmpeg_deinterlace_shot(db_common, shot)
        tasks.remove('deinterlace')


    return (tasks, extracted_images_count)




def process_single_frame(work_no:int, frame:dict) -> None:
    tasks = frame['tasks'].copy()
    img_input = None
    img_denoised = None
    img_sharpened = None
    img_upscaled = None
    if False:
        print("---------------------------------------------------------------------------",flush=True)
        print("%d: " % (frame['no']), tasks,flush=True)
        pprint(frame)
        print("---------------------------------------------------------------------------",flush=True)

    # print("%d: " % (frame['no']), tasks,flush=True)

    # For debug and verificattions: deinterlace->RGB
    if 'deinterlace_rgb' in tasks:
        img_input = cv2.imread(frame['filepath']['deinterlace'], cv2.IMREAD_COLOR)
        try:
            # print("apply RGB curves: %d" % (frame['no']))
            img_rgb = filter_rgb(frame, img_input)
        except:
            # print("Warning: no RGB curves are defined")
            img_rgb = img_input
        cv2.imwrite(frame['filepath']['deinterlace_rgb'], img_rgb)
        return (work_no, list())


    # Upscale image
    if 'upscale' in tasks:
        # print("\t\tupscale image: %d" % (frame['no']))
        if not os.path.exists(frame['filepath']['upscale']):
            # Get the input image: deinterlaced or pre_upscaled
            if img_input is None:
                if os.path.exists(frame['filepath']['pre_upscale']):
                    # Upscale the pre-upscaled image
                    img_input = cv2.imread(frame['filepath']['pre_upscale'], cv2.IMREAD_COLOR)
                elif os.path.exists(frame['filepath']['deinterlace']):
                    # Upscale the deinterlaced image
                    img_input = cv2.imread(frame['filepath']['deinterlace'], cv2.IMREAD_COLOR)
                else:
                    sys.exit("Error: cannot find the image to upscale frame no." % (frame['no']))

            img_upscaled = filter_upscale(frame, img_input)
            if img_upscaled is None:
                # There is no defined filter, or an error occured
                sys.exit("Error: upscaling frame no. %d has failed" % (frame['no']))

            elif tasks[-1] == 'upscale':
                # Last task, save the file
                cv2.imwrite(frame['filepath']['upscale'], img_upscaled)
        tasks.remove('upscale')

    if img_upscaled is None and 'denoise' in tasks:
        # This image is already upscaled, and required for the following task
        try:
            img_upscaled = cv2.imread(frame['filepath']['upscale'], cv2.IMREAD_COLOR)
        except:
            sys.exit("Error: cannot find the upscaled image for frame no. %d" % (frame['no']))


    # For debug and verificattions: deinterlace->upscale->RGB->geometry
    if 'upscale_rgb_geometry' in tasks:
        try:
            # print("apply RGB curves: %d" % (frame['no']))
            img_upscaled_rgb = filter_rgb(frame, img_upscaled)
            cv2.imwrite(frame['filepath']['deinterlace_rgb'], img_upscaled_rgb)
        except:
            # print("Warning: no RGB curves are defined")
            img_upscaled_rgb = img_upscaled
        # print("apply geometry: %d" % (frame['no']))
        img_upscaled_rgb_geometry = filter_geometry(frame, img_upscaled_rgb)
        if img_upscaled_rgb_geometry is None:
            img_upscaled_rgb_geometry = img_upscaled_rgb
        cv2.imwrite(frame['filepath']['upscale_rgb_geometry'], img_upscaled_rgb_geometry)
        return (work_no, list())



    # Denoise image
    if 'denoise' in tasks:
        # print("denoise image: %d" % (frame['no']))
        img_denoised = filter_denoise(frame, img_upscaled)
        if img_denoised is None:
            # There is no defined filter, use the input image
            img_denoised = img_upscaled
        elif tasks[-1] == 'denoise':
            cv2.imwrite(frame['filepath']['denoise'], img_denoised)
        tasks.remove('denoise')


    # Sharpen image
    if 'sharpen' in tasks:
        # print("sharpen image: %d" % (frame['no']))
        # # pprint(frame)
        # sys.exit()
        if img_denoised is None:
            # Denoise dimage has been saved in a file
            img_denoised = cv2.imread(frame['filepath']['denoised'], cv2.IMREAD_COLOR)
        img_sharpened = filter_sharpen(frame, img_denoised)
        cv2.imwrite(frame['filepath']['sharpen'], img_sharpened)
        tasks.remove('sharpen')


    if 'rgb' in tasks:
        # print("apply RGB curves: %d" % (frame['no']))
        is_rgb_valid = False
        if img_sharpened is None:
            # Open the saved sharpened image
            img_sharpened = cv2.imread(frame['filepath']['sharpen'], cv2.IMREAD_COLOR)
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


    if 'geometry' in tasks:
        # print("geometry: %d" % (frame['no']))
        # pprint(frame['geometry'])
        if img_rgb is None:
            img_rgb = cv2.imread(frame['filepath']['rgb'], cv2.IMREAD_COLOR)
        img_finalized = filter_geometry(frame, img_rgb)
        if img_finalized is not None:
            cv2.imwrite(frame['filepath']['geometry'], img_finalized)
        # elif is_rgb_valid:
        #     # Save the corrected image because the finalized image cannot be saved
        #     cv2.imwrite(frame['filepath']['rgb'], img_rgb)

        tasks.remove('geometry')

    return (work_no, tasks)




def process_shot(db, shot, cpu_count=0):

    # Extract only a part of the common database
    db_common = {
        'common': {
            'settings': {
                'ffmpeg_exe': db['common']['settings']['ffmpeg_exe'],
                'verbose': db['common']['settings']['verbose'],
                'frame_format': db['common']['settings']['frame_format'],
            },
            'process': db['common']['process'],
            'fps': db['common']['fps'],
            'directories': {
                'cache': db['common']['directories']['cache']
            }
        }
    }

    # Save last task for further processing (effects)
    last_task = shot['tasks'][-1]

    # Internal variables for work
    shot_pathfiles = list()
    shot_work = None

    # Consolidate shot
    consolidate_shot(db, shot)

    if False:
        # For debug
        # print("---------------- db_common ---------------")
        # pprint(db_common)
        print("------------------ SHOT ------------------")
        pprint(shot)
        print("------------------------------------------")
        # sys.exit()
    else:
        if shot['curves'] is None:
            print("\t\t\tcurves: none")
        else:
            print("\t\t\tcurves: %s" % (shot['curves']['k_curves']))


    # 2) Create list(s) of frames
    # ==========================================================================
    frames = create_framelist_from_shot(db, shot=shot)

    # 4) Determine what to do for each frame
    # ==========================================================================
    simplify_tasks(db, frames)


    if False:
        # For debug
        print("framelist from shot after simplification")
        pprint(frames)
        sys.exit()


    # 5) Extract: ffmpeg deinterlace/upscale
    # ==========================================================================
    # For each layer, determine if 'upscale' is in tasks. If at least
    # one frame has to be extracted, then extract all shot
    worklist = list()
    for f in frames:
        do_extract = False
        if 'deinterlace' in f['tasks'] or 'pre_upscale' in f['tasks']:
            do_extract = True
        elif 'upscale' in f['tasks']:
            if f['filters']['ffmpeg']['upscale'] is not None:
                # upscale is done by FFMPEG
                do_extract = True
            # else:
                # upscale is done by opencv
        if do_extract:
            break

    if do_extract:
        tasks, extracted_images_count = extract_frames_from_shot(db_common, shot)
        for f in frames:
            f['tasks'] = tasks.copy()

    # Clean
    gc.collect()


    # 6) All other tasks
    # ==========================================================================
    worklist = list()
    for no, frame in zip(range(len(frames)), frames):
        if frame['tasks']:
            worklist.append([no, frame])

    # print("Number of cpu : %d" % (multiprocessing.cpu_count()))
    cpu_count = int((multiprocessing.cpu_count() * 3)/4)
    min_workers = 12
    # if cpu_count >= 12:
    #     min_workers = 70
    # else:
    #     min_workers = 10
    with ThreadPoolExecutor(max_workers=min(min_workers,len(frames))) as executor:
        work_result = {executor.submit(process_single_frame, work[0], work[1]): None
                        for work in worklist}
        for future in concurrent.futures.as_completed(work_result):
            work_no, tasks = future.result()
            f = worklist[work_no][1]
            f['tasks'] = tasks.copy()

    # Clean useless variables
    del worklist
    gc.collect()


    # 7) Effects
    # ==========================================================================
    if 'effects' in shot.keys():
        # print("<<<<<<<<<<<<<<<<<<<<< EFFECTS >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        # print("APPLY effect", shot['effects'])
        # pprint(shot)
        if shot['effects'][0] == 'loop_and_fadeout':
            effect_loop_and_fadeout(db, shot, frames, last_task)

        elif shot['effects'][0] == 'fadeout':
            effect_fadeout(db, shot, frames, last_task)



