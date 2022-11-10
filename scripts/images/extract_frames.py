#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import gc
import os
import sys
import time
from pprint import pprint

import multiprocessing
from multiprocessing import *
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor


from utils.common import K_GENERIQUES
from utils.get_filters import get_filters
from utils.get_curves import get_curves
from utils.path import get_input_filepath
from utils.path import get_output_frame_filepaths_for_study
from utils.ffmpeg import (
    ffmpeg_deinterlace_single_frame,
    ffmpeg_deinterlace_and_pre_upscale_single_frame,
    ffmpeg_deinterlace_and_upscale_single_frame,
)
from images.frames import get_frames_for_study
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



def process_single_frame(database:dict, work_no, frame):
    print("%d - %d" % (work_no, frame['no']))
    pprint(frame)

    # print("processing frame: k_ed=%s, no=%d" % (frame['k_ed'], frame['ref']))
    # Define default values and images
    img_denoised = None
    img_ffmpeg = None

    list_of_tasks = frame['tasks'].copy()
    # print("\nprocess_single_frame\n\tForce", frame['force'])
    print("\tTasks:", list_of_tasks, flush=True)

    # FFMPEG: Deinterlace only
    if ('deinterlace' in list_of_tasks
      and 'pre_upscale' not in list_of_tasks
      and 'upscale' not in list_of_tasks):
        print("1.1. FFMPEG: deinterlace only", flush=True)
        if os.path.exists(frame['filepath']['deinterlace']) and not frame['force']:
            # print("\tdeinterlace: skip frame %d, file already exist" % (frame['no']))
            img_ffmpeg = cv2.imread(frame['filepath']['deinterlace'], cv2.IMREAD_COLOR)
        else:
            print("\tframe: %s:%s:%s, ref=%d, no=%d\tdeinterlace" % (frame['k_ed'], frame['k_ep'], frame['k_part'], frame['ref'], frame['no']), flush=True)
            img_ffmpeg = ffmpeg_deinterlace_single_frame(database, frame)
            # if list_of_tasks[-1] == 'deinterlace':
            # deinterlace only
            cv2.imwrite(frame['filepath']['deinterlace'], img_ffmpeg)
        list_of_tasks.remove('deinterlace')


    # FFMPEG: Deinterlace and pre-upscale only
    elif ('deinterlace' in list_of_tasks
      and 'pre_upscale' in list_of_tasks
      and frame['filters']['opencv']['upscale'] is not None
      or list_of_tasks[-1] == 'pre_upscale'):

        print("1.2. FFMPEG: deinterlace, pre-upscale", flush=True)
        if os.path.exists(frame['filepath']['pre_upscale']) and not frame['force']:
            print("\tdeinterlace, pre_upscale: skip frame %d, file already exist" % (frame['no']))
            img_ffmpeg = cv2.imread(frame['filepath']['pre_upscale'], cv2.IMREAD_COLOR)
        else:
            print("\tframe: k_ed=%s, %s, no=%d\tpre_upscale" % (frame['k_ed'], frame['k_ep'], frame['ref']), flush=True)
            img_ffmpeg = ffmpeg_deinterlace_and_pre_upscale_single_frame(database, frame)
            # if list_of_tasks[-1] == 'pre_upscale':
            # deinterlace/upscale only
            cv2.imwrite(frame['filepath']['pre_upscale'], img_ffmpeg)
        list_of_tasks.remove('deinterlace')
        list_of_tasks.remove('pre_upscale')


    # FFMPEG: From deinterlace to upscale
    elif ('deinterlace' in list_of_tasks
      and 'upscale' in list_of_tasks
      and frame['filters']['ffmpeg']['upscale'] is not None):
        print("1.3. FFMPEG: deinterlace, pre-upscale, upscale", flush=True)

        if os.path.exists(frame['filepath']['upscale']) and not frame['force']:
            print("\tdeinterlace, upscale: skip frame %d, file already exist" % (frame['no']))
            img_ffmpeg = cv2.imread(frame['filepath']['upscale'], cv2.IMREAD_COLOR)
        else:
            print("\tframe: k_ed=%s, %s, no=%d\tupscale" % (frame['k_ed'], frame['k_ep'], frame['ref']))
            img_ffmpeg = ffmpeg_deinterlace_and_upscale_single_frame(database, frame)
            # if list_of_tasks[-1] == 'upscale':
            # deinterlace/upscale only
            cv2.imwrite(frame['filepath']['upscale'], img_ffmpeg)
        list_of_tasks.remove('deinterlace')
        list_of_tasks.remove('upscale')
        if 'pre_upscale' in list_of_tasks:
            list_of_tasks.remove('pre_upscale')
        img_upscaled = img_ffmpeg


    # OpenCV: upscale
    if 'upscale' in list_of_tasks:
        if os.path.exists(frame['filepath']['upscale']) and not frame['force']:
            # Use the already processed image
            print("\tupscale: skip frame %d, file already exist" % (frame['no']))
            img_ffmpeg = cv2.imread(frame['filepath']['upscale'], cv2.IMREAD_COLOR)
        else:
            print("\tframe: k_ed=%s, %s, no=%d\tupscale" % (frame['k_ed'], frame['k_ep'], frame['ref']))
            img_upscaled = filter_upscale(frame, img_ffmpeg)
            if list_of_tasks[-1] == 'upscale':
                cv2.imwrite(frame['filepath']['upscale'], img_upscaled)
        list_of_tasks.remove('upscale')


    # OpenCV: denoise
    if 'denoise' in list_of_tasks:
        if os.path.exists(frame['filepath']['denoise']) and not frame['force']:
            print("\tdenoise: skip frame %d, file already exist" % (frame['no']))
            img_denoised = cv2.imread(frame['filepath']['denoise'], cv2.IMREAD_COLOR)
        else:
            # try:
            print("\tframe: k_ed=%s, %s, no=%d\tdenoise" % (frame['k_ed'], frame['k_ep'], frame['ref']))
            img_denoised = filter_denoise(frame, img_upscaled)
            # except:
            #     print("failed: frame no. %d" % (frame['no']))
            #     print("\tfilter=%s" % (frame['filters']['opencv']['denoise']))
            if study_mode and img_denoised is not None:
                cv2.imwrite(frame['filepath']['denoise'], img_denoised)
            elif img_denoised is None:
                # There is no defined filter, use the input image
                img_denoised = img_upscaled
        list_of_tasks.remove('denoise')


    # OpenCV: Apply curves to the background image
    if 'bgd' in list_of_tasks:
        if frame['layer'] == 'bgd':
            if os.path.exists(frame['filepath']['bgd']) and not frame['force']:
                print("\tbgd: skip frame %d, file already exist" % (frame['no']))
                img_bgd = cv2.imread(frame['filepath']['bgd'], cv2.IMREAD_COLOR)
            else:
                img_bgd = filter_bgd(frame, img_denoised)
                if img_bgd is not None:
                    cv2.imwrite(frame['filepath']['bgd'], img_bgd)
                # This is a background image, do not continue
                print("%d is BGD image, stop here" % (frame['ref']))
            list_of_tasks.clear()
            return (work_no, list_of_tasks)
        list_of_tasks.remove('bgd')


    # OpenCV: Combine bgd and fgd image
    if 'stitching' in list_of_tasks:
        if frame['layer'] == 'fgd':
            # overwrite = True
            if os.path.exists(frame['filepath']['stitching']) and not frame['force']:
                print("\tcombine: skip frame %d, file already exist" % (frame['no']))
                img_combine = cv2.imread(frame['filepath']['stitching'], cv2.IMREAD_COLOR)
                list_of_tasks.remove('stitching')
            elif frame['filepath']['bgd'] == '':
                # No background, do not combine and continue processing
                print("!!!!!! %s does not exists in bgd filepath" % (frame['filepath']['bgd']))
                list_of_tasks.remove('stitching')
            elif not os.path.exists(frame['filepath']['bgd']):
                # Cannnot merge because the file does not exist yet
                print("\tfailed: merge with %s" % (frame['filepath']['bgd']))
                return (work_no, list_of_tasks)
            else:
                if img_denoised is None and os.path.exists(frame['filepath']['denoise']):
                    img_denoised = cv2.imread(frame['filepath']['denoise'], cv2.IMREAD_COLOR)
                # else:
                #     print("!!!Error: %s does not exist, cannot combine" % (frame['filepath']['denoise']))
                img_bgd = cv2.imread(frame['filepath']['bgd'], cv2.IMREAD_COLOR)

                print("img_denoised: %dx%d" % (img_denoised.shape[1], img_denoised.shape[0]))
                print("img_bgd: %dx%d" % (img_bgd.shape[1], img_bgd.shape[0]))

                img_combine = combine_images(frame, img_denoised, img_bgd)

                print("img_combine: %dx%d" % (img_combine.shape[1], img_combine.shape[0]))
                if study_mode and img_combine is not None:
                    cv2.imwrite(frame['filepath']['stitching'], img_combine)
                    list_of_tasks.remove('stitching')

    elif frame['layer'] != 'bgd':
        # foreground images or no combination
        if os.path.exists(frame['filepath']['stitching']):
            img_combine = cv2.imread(frame['filepath']['stitching'], cv2.IMREAD_COLOR)
        elif img_denoised is not None:
            img_combine = img_denoised
            # print("!!!Error: %s does not exist, cannot open combine sharpen" % (frame['filepath']['stitching']))


    if 'sharpen' in list_of_tasks:
        if os.path.exists(frame['filepath']['sharpen']) and not frame['force']:
            print("\tsharpen: skip frame %d, file already exist" % (frame['no']))
            img_sharpened = cv2.imread(frame['filepath']['sharpen'], cv2.IMREAD_COLOR)
        else:
            try:
                img_sharpened = filter_sharpen(frame, img_combine)
            except:
                print("failed: frame no. %d" % (frame['no']))
                print("\tfilter=%s" % (frame['filters']['opencv']['sharpen']))
            if study_mode and img_sharpened is not None:
                cv2.imwrite(frame['filepath']['sharpen'], img_sharpened)
            elif img_sharpened is None:
                print("sharpen filters returned empty image")
        list_of_tasks.remove('sharpen')


    if 'rgb' in list_of_tasks:
        if os.path.exists(frame['filepath']['rgb']) and not frame['force']:
            print("\trgb: skip frame %d, file already exist" % (frame['no']))
            img_rgb = cv2.imread(frame['filepath']['sharpen'], cv2.IMREAD_COLOR)
        else:
            try:
                img_rgb = filter_rgb(frame, img_sharpened)
            except:
                print("failed: frame no. %d" % (frame['no']))
                print("\tfilter=%s" % (frame['filters']['opencv']['rgb']))
            if study_mode and img_rgb is not None:
                cv2.imwrite(frame['filepath']['rgb'], img_rgb)
            elif img_rgb is None:
                print("rgb filter returned empty image")
        list_of_tasks.remove('rgb')

    if 'geometry' in list_of_tasks:
        # if os.path.exists(frame['filepath']['geometry']) and not frame['force']:
        #     print("\tfinal: skip frame %d, file already exist" % (frame['no']))
        # else:
        img_final = filter_geometry(frame, img_rgb)
        if img_final is not None:
            cv2.imwrite(frame['filepath']['geometry'], img_final)
        else:
            print("crop and resize filter returned empty image")

        # filter_crop(frame)
        list_of_tasks.remove('geometry')


    # print("process_single_frame: -> ", list_of_tasks)
    return (work_no, list_of_tasks)




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
            print("%s,%d: " % (f['k_ed'], f['ref']), end='')
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
            print("error: todo, correct this: img_combine_count [%d]!= len(frames_2) [%d]!" %
                (img_combine_count, len(frames_2)))







def extract_frames_for_study(database, editions, episode_no, k_part, tasks, force:bool=False, compare:bool=False):
    print("%s.extract_frames_for_study: episode no. %d, k_part=%s, tasks=%s" % (__name__, episode_no, k_part, ', '.join(tasks)))

    # Use the default edition if none specified
    if editions[0] == '':
        if k_part in K_GENERIQUES:
            # use the edition defined as reference unless specified as argument
            editions = [database[k_part]['common']['video']['reference']['k_ed']]
            pprint(database[k_part]['common']['video']['reference'])
        else:
            editions = [database['editions']['default']]
    print("k_ed=%s" % (', '.join(editions)))

    # Get the list of frames for studies
    frames_count, frames = get_framelist_for_study(database,
        editions, episode_no, k_part,
        tasks,
        force=force,
        compare=False)
    # print("frames (%d):")
    # pprint(frames,indent=4)

    startTime = time.time()
    work = []
    print("Number of cores: %d" % (multiprocessing.cpu_count()))
    for i in range(frames_count):
        for edition in editions:
            f = frames[edition][i]
            work.append(f)
    process_frames(database, work, cpu_count=int(multiprocessing.cpu_count() / 2))
    print("=> done in %.04fs" % (time.time() - startTime), flush=True)



def get_framelist_for_study(database, editions, episode_no, k_part, tasks, force:bool=False, compare:bool=False):
    # print("%s.get_framelist: episode no. %d, k_part=%s, tasks=%s, editions: " % (__name__, episode_no, k_part, ', '.join(tasks)), editions)

    # Create a list of frames, each frame has all
    # properties for the full processing
    frames = dict()
    for edition in editions:
        # Get the list of frames
        frames[edition] = get_frames_for_study(
            database,
            edition=edition,
            episode_no=episode_no,
            k_part=k_part)

        # print("%s.get_framelist: frames=" % (__name__))
        # pprint(frames)

        # Consolidate each frame
        for f in frames[edition]:
            # print("||||||||||||||||||||||||||||||||||")
            # pprint(f)
            # shot = get_shot_from_frame_no_new(db=database, frame_no=f['no'], k_ed=edition, k_ep=f['k_ep'], k_part=k_part)
            # pprint(shot)
            # continue

            f['k_ed'] = edition

            if f['k_ep'] == 0:
                f['k_ep'] = 'ep%02d' % (episode_no)

            f['k_part'] = k_part
            f['filters'] = get_filters(database, frame=f, k_part=k_part)

            f['input'] = get_input_filepath(database, frame=f)
            f['filepath'] = get_output_frame_filepaths_for_study(database,
                                frame=f, k_part=k_part).copy()
            f['tasks'] = tasks.copy()
            f['dimensions'] = database['editions'][edition]['dimensions']

            # firstly, consider all frames as foreground (i.e. no stitching)
            # TODO: correct this for image stitching
            f['layer'] = 'fgd'
            # print("frame no. %d" % (f['no']))

            f['curves'] = get_curves(database, frame=f, k_part=k_part)
            f['force'] = force



            # Get shot from frame_no.
            # if k_part in K_GENERIQUES:
            #     shot = get_shot_from_frame_no(database[k_part], f['no'], edition)
            # else:
            #     shot = get_shot_from_frame_no(database[f['k_ep']][edition], f['no'], k_part)

            # TODO: add geometry

            # print("++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            # pprint(f)


            # if f['curves']['lut'] is not None:
            # pprint(f, indent=4)


    # if not compare:
    if False:
        # Patch frame for image stitching
        edition_fgd = database['editions']['fgd']
        edition_bgd = database['editions']['bgd']
        frames_count = len(frames[database['editions']['fgd']])
        for i in range(frames_count):
            f_bgd = frames[edition_bgd][i]
            f_fgd = frames[edition_fgd][i]

            if f_fgd['ref'] != f_bgd['ref']:
                sys.exit("error: frame no. differs between bgd and fgd")

            # Patch filepath/layer for foreground/background
            f_fgd['filepath']['bgd'] = f_bgd['filepath']['bgd']
            f_fgd['layer'] = 'fgd'
            f_bgd['layer'] = 'bgd'

            # Remove 'bgd' from tasks
            if 'bgd' in f_fgd['tasks']:
                f_fgd['tasks'].remove('bgd')

            # Remove tasks which should not be done for bacground image
            for t in ['stitching', 'sharpen', 'rgb', 'geometry']:
                if t in f_bgd['tasks']:
                    f_bgd['tasks'].remove(t)

            if f_bgd['layer'] == 'bgd':
                f_ref = f_bgd['ref']
                k_episode = f['k_ep']
                if f_ref in database_combine[k_episode].keys():
                    # print("+++ %d :" % (f_ref), database_combine[k_episode][f_ref])
                    f_fgd['stitching'] = {'geometry': database_combine[k_episode][f_ref]['geometry'].copy()}

                    if 'bgd' in f_bgd['tasks']:
                        # Add rgb correction ('bgd') for background image if in tasks
                        bgd_curve = database_combine[k_episode][f_ref]['curve']
                        if bgd_curve is not None:
                            f_bgd['stitching'] = {'curve': database_combine[k_episode][f_ref]['curve']}
                    else:
                        # No curve defined: remove 'bgd' task
                        f_fgd['filepath']['bgd'] = f_bgd['filepath']['denoise']

                else:
                    # No combine/curve defined: remove 'bgd' task from bgd and combine from fgd
                    if 'bgd' in f_bgd['tasks']:
                        f_bgd['tasks'].remove('bgd')
                    if 'stitching' in f_fgd['tasks']:
                        f_fgd['tasks'].remove('stitching')

            # Patch filepaths
            # print("=========================================")
            # pprint(f_bgd)
            # print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            # pprint(f_fgd)
            # print("<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>")
    else:
        # k_ep = 'ep%02d' % (episode_no + 1)
        # edition = editions[0]

        # print(k_ep)
        # shot = get_shot_from_frame_no(database[k_ep][edition], 2671)
        # shot2 = get_shot_from_frame_no(database['ep%02d' % (episode_no)][edition], shot['src']['start'])


        # pprint(shot)
        # print("-------------")
        # pprint(shot2)

        # sys.exit()



        # Extract frames for comparisons: for each frame,
        # the combination stage is discarded.
        frames_count = 9999999
        for edition in editions:
            for f in frames[edition]:
                # Consider all frames as foreground
                f['layer'] = 'fgd'
                # Remove tasks which shall not be done for foreground images
                for t in ['bgd', 'stitching']:
                    if t in f['tasks']:
                        f['tasks'].remove(t)
            frames_count = min(frames_count, len(frames[edition]))

    return frames_count, frames




result_list = []
def log_result(result):
    # This is called whenever foo_pool(i) returns a result.
    # result_list is modified only by the main process, not the pool workers.
    result_list.append(result)

