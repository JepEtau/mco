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
from utils.ffmpeg import (
    ffmpeg_deinterlace_single_frame,
    ffmpeg_deinterlace_and_pre_upscale_single_frame,
    ffmpeg_deinterlace_and_upscale_single_frame,
)
from images.frames import consolidate_frame_list_for_study
from images.filtering import (
    filter_upscale,
    filter_denoise,
    filter_bgd,
    filter_sharpen,
    filter_geometry,
    filter_rgb,
)
from images.combine import combine_images

study_mode = True


def process_single_frame(db_common:dict, work_no:int, frame:dict) -> None:
    tasks = frame['tasks'].copy()
    force = frame['force']
    print("%d - %d: %s" % (work_no, frame['no'], ', '.join(tasks)), flush=True)
    # pprint(frame)

    # print("processing frame: k_ed=%s, no=%d" % (frame['k_ed'], frame['no']))
    # Define default values and images


    img_ffmpeg = None
    if 'deinterlace' in tasks:
        # FFMPEG: Deinterlace only
        if 'upscale' not in tasks:
            print("\t\t\tFFMPEG: Deinterlace only")
            img_ffmpeg = ffmpeg_deinterlace_single_frame(db_common, frame)
            cv2.imwrite(frame['filepath']['deinterlace'], img_ffmpeg)
            tasks.remove('deinterlace')

        # Deinterlace and pre-upscale:
        elif ('pre_upscale' in tasks and frame['filters']['ffmpeg']['upscale'] is None):
            print("\t\t\tFFMPEG: Deinterlace and pre-upscale, upscale done by opencv")
            img_ffmpeg = ffmpeg_deinterlace_and_pre_upscale_single_frame(db_common, frame)
            tasks.remove('deinterlace')
            tasks.remove('pre_upscale')
            cv2.imwrite(frame['filepath']['pre_upscale'], img_ffmpeg)
            if frame['filters']['opencv']['upscale'] is None:
                sys.exit("Missing upscale filter for %s:%s:%s" % (frame['k_ed'], frame['k_ep'], frame['k_part']))

        # Deinterlace and upscale
        elif 'upscale' in tasks and frame['filters']['ffmpeg']['upscale'] is not None:
            print("\t\t\tFFMPEG: Deinterlace, pre_upscale and upscale")
            img_ffmpeg = ffmpeg_deinterlace_and_upscale_single_frame(db_common, shot)
            cv2.imwrite(frame['filepath']['upscale'], img_ffmpeg)
            tasks.remove('deinterlace')
            try: tasks.remove('pre_upscale')
            except: pass
            tasks.remove('upscale')

        # Other cases: deinterlace only
        else:
            # print("\t\t\tFFMPEG: Deinterlace only")
            img_ffmpeg = ffmpeg_deinterlace_single_frame(db_common, frame)
            cv2.imwrite(frame['filepath']['deinterlace'], img_ffmpeg)
            tasks.remove('deinterlace')


    # Upscale image
    img_upscaled = None
    if 'upscale' in tasks:
        # print("upscale image: %d" % (frame['no']))
        if not os.path.exists(frame['filepath']['upscale']) or force:

            # Get the input image: deinterlaced or pre_upscaled
            if img_ffmpeg is None:
                if os.path.exists(frame['filepath']['pre_upscale']):
                    # Upscale the pre-upscaled image
                    img_ffmpeg = cv2.imread(frame['filepath']['pre_upscale'], cv2.IMREAD_COLOR)
                elif os.path.exists(frame['filepath']['deinterlace']):
                    # Upscale the deinterlaced image
                    img_ffmpeg = cv2.imread(frame['filepath']['deinterlace'], cv2.IMREAD_COLOR)
                else:
                    sys.exit("Error: cannot find the image to upscale frame no." % (frame['no']))


            img_upscaled = filter_upscale(frame, img_ffmpeg)
            if img_upscaled is None:
                # There is no defined filter, or an error occured
                sys.exit("Error: upscaling frame no. %d has failed" % (frame['no']))
            else:
                cv2.imwrite(frame['filepath']['upscale'], img_upscaled)
        tasks.remove('upscale')


    # Denoise image
    img_denoised = None
    if 'denoise' in tasks:
        if not os.path.exists(frame['filepath']['denoise']) or force:
            if img_upscaled is None:
                print("upscaled image: %s " % (frame['filepath']['upscale']))
                img_upscaled = cv2.imread(frame['filepath']['upscale'], cv2.IMREAD_COLOR)

            # print("denoise image: %d" % (frame['no']))
            img_denoised = filter_denoise(frame, img_upscaled)
            if img_denoised is None:
                # There is no defined filter, use the input image
                print("no denoise filters")
                img_denoised = img_upscaled
            else:
                cv2.imwrite(frame['filepath']['denoise'], img_denoised)
            tasks.remove('denoise')

    # Stitching tasks: ...

    # Sharpen image
    img_sharpened = None
    if 'sharpen' in tasks:
        if not os.path.exists(frame['filepath']['sharpen']) or force:
            if img_denoised is None:
                img_denoised = cv2.imread(frame['filepath']['denoise'], cv2.IMREAD_COLOR)

            img_sharpened = filter_sharpen(frame, img_denoised)
            cv2.imwrite(frame['filepath']['sharpen'], img_sharpened)
        tasks.remove('sharpen')


    is_rgb_valid = False
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
        tasks.remove('geometry')
    else:
        if is_rgb_valid:
            cv2.imwrite(frame['filepath']['rgb'], img_rgb)


    return (work_no, tasks)




def process_frames(database, frames, cpu_count):
    db_common = {
        'common': {
            'settings': {
                'ffmpeg_exe': database['common']['settings']['ffmpeg_exe'],
                'verbose': database['common']['settings']['verbose']
            },
            'process': database['common']['process'],
            'fps': database['common']['fps']
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
            img_combine_count = 0

        frames_2 = list()
        for f in frames:
            if f['tasks']:
                frames_2.append(f)

        for f in frames_2:
            print("%s, %d -> %d: " % (f['k_ed'], f['ref'], f['no']), end='')
            print(f['tasks'])

        for f in frames_2:
            if f['tasks'][0] == 'stitching':
                img_combine_count +=1


    # Clean useless variables
    del worklist
    gc.collect()


    if len(frames_2)>0 and img_combine_count==len(frames_2):
        print("remaining images to combine %d/%d" % (img_combine_count, len(frames_2)))
        # Only combine images, retry one time again
        worklist = list([i, frames_2[i]] for i in range(len(frames_2)))

        with ThreadPoolExecutor(max_workers=cpu_count) as executor:
            work_result = {executor.submit(process_single_frame, db_common, work[0], work[1]): None
                            for work in worklist}

            for future in concurrent.futures.as_completed(work_result):
                work_no, tasklist = future.result()
                f = worklist[work_no][1]
                f['tasks'] = tasklist.copy()
                img_combine_count = 0

        img_combine_count = 0
        for f in frames:
            if not f['tasks']:
                frames_2.remove(f)
        for f in frames_2:
            if f['tasks'][0] == 'stitching':
                img_combine_count +=1
        print("remaining images to combine %d/%d" % (img_combine_count, len(frames_2)))
        if img_combine_count == len(frames_2):
            # Do not continue if it is not possible to combine images
            print("Warning: cannot combine images, end of processing")
        else:
            print("Error: todo, correct this: img_combine_count [%d]!= len(frames_2) [%d]!" %
                (img_combine_count, len(frames_2)))







def extract_frames_for_study(db, k_ed, k_ep, k_part, tasks, force:bool=False, shot_min:int=0, shot_max:int=999999):
    print("%s.extract_frames_for_study: %s:%s:%s, tasks=%s" % (__name__, k_ed, k_ep, k_part, ', '.join(tasks)))

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
            # Use the target ed
            k_ed_src = db['editions']['fgd']

    # Get the list of frames for studies
    frames = consolidate_frame_list_for_study(db,
        k_ed_src, k_ep_src, k_part,
        tasks,
        force=force)
    # pprint(frames)
    if frames is None:
        sys.exit("Error: no frame to extract")

    # Extract only a few settings for the process
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
                'frames': db['common']['directories']['frames']
            }
        }
    }

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
    cpu_count = int(multiprocessing.cpu_count() / 2)

    startTime = time.time()
    with ThreadPoolExecutor(max_workers=cpu_count) as executor:
        work_result = {executor.submit(process_single_frame, db_common, work[0], work[1]): None
                        for work in worklist}

        for future in concurrent.futures.as_completed(work_result):
            work_no, tasklist = future.result()
            f = worklist[work_no][1]
            f['tasks'] = tasklist.copy()
    print("=> done in %.04fs" % (time.time() - startTime), flush=True)

