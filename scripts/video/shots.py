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

from images.combine import combine_images
from images.filtering import (
    filter_denoise,
    filter_rgb,
    filter_upscale,
    filter_bgd,
    filter_sharpen,
    filter_geometry,
)
from images.frames import (
    create_framelist_from_shot,
    patch_frames_for_stitching,
)
from utils.consolidate_shots import consolidate_shot
from utils.ffmpeg import (
    ffmpeg_deinterlace_and_pre_upscale_shot,
    ffmpeg_deinterlace_shot,
    ffmpeg_deinterlace_and_upscale_shot,
)
from utils.tasks import simplify_tasks
from video.effects import (
    effect_comb,
    effect_loop_and_fadeout,
    effect_fadeout,
)


def extract_frames_from_shot(db_common:dict, k_layer:str, shot:dict) -> None:
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


    return (k_layer, tasks, extracted_images_count)




def process_single_frame(work_no:int, frame:dict) -> None:
    tasks = frame['tasks'].copy()
    img_input = None
    img_denoised = None
    img_stitching = None
    img_sharpened = None
    img_upscaled = None
    if False:
        print("---------------------------------------------------------------------------",flush=True)
        print("%d: " % (frame['no']), tasks,flush=True)
        pprint(frame)
        print("---------------------------------------------------------------------------",flush=True)

    print("%d: " % (frame['no']), tasks,flush=True)

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
        # print("upscale image: %d" % (frame['no']))
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
    if (img_denoised is None
    and ('bgd' in tasks
        or 'stitching' in tasks
        or 'sharpen' in tasks)):
        # This image is already denoised,
        # required if this frame is bgd or stitching
        img_upscaled = cv2.imread(frame['filepath']['upscale'], cv2.IMREAD_COLOR)


    # Apply curves to the background image
    if 'bgd' in tasks:
        if frame['layer'] == 'bgd':
            if img_denoised is None:
                img_denoised = cv2.imread(frame['filepath']['denoise'], cv2.IMREAD_COLOR)
            img_bgd = filter_bgd(frame, img_denoised)
            cv2.imwrite(frame['filepath']['bgd'], img_bgd)
            # This is a background image, do not continue
            print("\t%d is BGD image, stop here" % (frame['no']))
            tasks.clear()
            return (work_no, tasks)
        tasks.remove('bgd')


    # Combine bgd and fgd image
    if 'stitching' in tasks:
        if frame['layer'] == 'fgd':
            if not os.path.exists(frame['filepath']['bgd']):
                # Cannnot merge because the bgd file does not exist
                print("\tfailed: waiting for bgd frame %s" % (frame['filepath']['bgd']))
                return (work_no, tasks)

            # Open fgd image if exists and is not already loaded
            if img_denoised is None:
                img_denoised = cv2.imread(frame['filepath']['denoise'], cv2.IMREAD_COLOR)

            # Open bgd image
            img_bgd = cv2.imread(frame['filepath']['bgd'], cv2.IMREAD_COLOR)

            # Combine images
            img_stitching = combine_images(frame['stitching']['geometry'], img_denoised, img_bgd)
            cv2.imwrite(frame['filepath']['stitching'], img_stitching)
            # if (img_stitching is None:
            #  and 'sharpen' in tasks):
            #     # This image is already denoised,
            #     # required if this frame is bgd or stitching
            #     img_upscaled = cv2.imread(frame['filepath']['upscale'], cv2.IMREAD_COLOR)


        tasks.remove('stitching')
    # else:
    #     # no stitching

    # Sharpen image
    if 'sharpen' in tasks:
        # print("sharpen image: %d" % (frame['no']))
        # print(frame['filepath']['stitching'])
        # # pprint(frame)
        # sys.exit()
        if img_stitching is None:
            if not os.path.exists(frame['filepath']['stitching']):
                # use the denoised image
                if img_denoised is None:
                    # Denoise dimage has been saved in a file
                    img_stitching = cv2.imread(frame['filepath']['denoised'], cv2.IMREAD_COLOR)
                else:
                    # Use the denoise image which is in memory
                    img_stitching = img_denoised
            else:
                img_stitching = cv2.imread(frame['filepath']['stitching'], cv2.IMREAD_COLOR)
        img_sharpened = filter_sharpen(frame, img_stitching)
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




def process_shot(db, shot, db_combine:dict={}, cpu_count=0):
    # db: global database
    # db_combine: contains coordinates and curves to combine foreground and background
    # shot: this dictionary contains info of the "foreground" shot
    # cpu_count: maximum nb of processes to use for extracting/filtering images

    # TODO: specify mode:
    # study: save all
    # combine: save denoise images
    # rgb: save sharpen
    # final: save bgd, combine, final

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


    # 1) Create layer(s) and consolidate
    # ==========================================================================

    # Create the foreground layer
    # warning: shot is not copied for fgd
    layers = {
        'fgd': {
            'shot': shot,
            'pathfiles': list(),
            'work': None
        }
    }

    # If the edition is specified, it means that combine is disabled,
    # else, create the background layer
    # print("process_shot:")
    if ('stitching' in shot.keys()
    and 'stitching' not in db['common']['options']['discard_tasks']):

        do_stitching = True
        layers.update({
            'bgd': {
                'shot': deepcopy(shot),
                'pathfiles': list(),
                'work': None
            },
        })

        for l in ['fgd', 'bgd']:
            layers[l]['shot']['layer'] = l

    else:
        # Only foreground layer
        # print("Only foreground layer")
        do_stitching = False
        layers['fgd']['shot']['layer'] = 'fgd'

    # Consolidate layer(s)
    for l in layers.keys():
        consolidate_shot(db, layers[l]['shot'])

    if False:
        # For debug
        print("--------------- Foreground ---------------")
        pprint(layers['fgd']['shot'])
        if do_stitching:
            print("--------------- Background ---------------")
            pprint(layers['bgd']['shot'])
        print("------------------------------------------")
        sys.exit()
    else:
        if layers['fgd']['shot']['curves'] is None:
            print("\t\t\tcurves: none")
        else:
            print("\t\t\tcurves: %s" % (layers['fgd']['shot']['curves']['k_curves']))


    # 2) Create list(s) of frames
    # ==========================================================================
    frames = dict()
    for l in layers.keys():
        frames[l] = create_framelist_from_shot(db, layers[l]['shot'])


    # 3) Patch frames to combine images (image stitching)
    # ==========================================================================
    patch_frames_for_stitching(frames, db_combine, do_stitching)


    # 4) Determine what to do for each frame
    # ==========================================================================
    simplify_tasks(db, frames)


    if False:
        # For debug
        print("framelist from shot after simplification")
        pprint(frames)

        # for k, layer in frames.items():
        #     for f in layer:
        #         print(f['tasks'])
        #         print("\t%s:\t%s" % (f['no'], f['filepath'][f['tasks'][-1]]))
        sys.exit()



    # 5) Extract: deinterlace/upscale
    # ==========================================================================
    # For each layer, determine if 'upscale' is in tasks. If at least
    # one frame has to be extracted, then extract all shot
    worklist = list()
    for layer in layers.keys():
        for f in frames[layer]:
            do_append = False
            if 'deinterlace' in f['tasks'] or 'pre_upscale' in f['tasks']:
                do_append = True
            elif 'upscale' in f['tasks']:
                if f['filters']['ffmpeg']['upscale'] is not None:
                    # upscale is done by FFMPEG
                    do_append = True
                # else:
                    # upscale is done by opencv
            if do_append:
                worklist.append([db_common, layer, layers[layer]['shot']])
                break


    # Create a pool of processes to extract all frames from shot
    if cpu_count == 0:
        # print("Number of cpu : %d" % (multiprocessing.cpu_count()))
        cpu_count = int(multiprocessing.cpu_count() / 2)


    with ThreadPoolExecutor(max_workers=cpu_count) as executor:
        work_result = {executor.submit(extract_frames_from_shot, db_common, work[1], work[2]): None
                        for work in worklist}

        for future in concurrent.futures.as_completed(work_result):
            k_layer, tasks, extracted_images_count = future.result()
            if extracted_images_count != shot['count']:
                sys.exit("error: nb. of extracted images differs from specified (%d vs %d" % (extracted_images_count, shot['count']))
            for f in frames[k_layer]:
                f['tasks'] = tasks.copy()


    # Clean
    gc.collect()


    # 6) Denoise, bgd
    # ==========================================================================
    for i in range(2):
        # It is needed to run 2 times because processinf bgd takes long time, thus
        # the fgd cannot continue until the bgd frame is ready
        worklist = list()
        k_layers = layers.keys()
        no = 0
        for i in range(len(frames['fgd'])):
            for layer in k_layers:
                if frames[layer][i]['tasks']:
                    worklist.append([no, frames[layer][i]])
                    no += 1

    # print("Number of cpu : %d" % (multiprocessing.cpu_count()))
    cpu_count = int((multiprocessing.cpu_count() * 3)/4)
    with ThreadPoolExecutor(max_workers=min(100,len(frames['fgd']))) as executor:
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

        if shot['effects'][0] == 'comb':
            # first foreground frame of the shot, i.e. first frame in the list of frames
            effect_comb(db, shot, frames['fgd'][0], last_task)

        elif shot['effects'][0] == 'loop_and_fadeout':
            # latest foreground frame of the shot, i.e. last frame in the list of frames
            effect_loop_and_fadeout(db, shot, frames['fgd'], last_task)

        elif shot['effects'][0] == 'fadeout':
            effect_fadeout(db, shot, frames['fgd'], last_task)



