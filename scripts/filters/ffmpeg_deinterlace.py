# -*- coding: utf-8 -*-
import sys
import cv2
import numpy as np
import os
from pprint import pprint


from filters.ffmpeg_utils import (
    clean_ffmpeg_filter,
    get_ffmpeg_filter,
    get_video_resolution
)
from filters.utils import MAX_FRAMES_COUNT
from utils.get_image_list import (
    FILENAME_TEMPLATE
)
from utils.hash import calculate_hash, log_filter
from utils.pretty_print import *
from utils.time_conversions import *
from utils.process import create_process




def ffmpeg_deinterlace(shot, step_no,
        filter_str, output_folder:str, db_common, get_hash:bool=False, forced_hash=''):

    filter_str=clean_ffmpeg_filter(filter_str)

    if forced_hash == '':
        # Generate and log hash
        if get_hash:
            hash = calculate_hash(filter_str=filter_str)
            return hash, list()
        hash = log_filter(filter_str, shot['hash_log_file'])
    else:
        # Hash is forced by the calling function
        hash = forced_hash

    print_cyan("(FFmpeg)\tstep no. %d, filters=%s, hash= %s" % (step_no, filter_str, hash))

    frame_start = shot['start']
    frame_count = shot['count']
    input_file = shot['inputs']['interlaced']['filepath']

    # list of foutput filepath
    filename_template = os.path.abspath(os.path.join(output_folder,
        FILENAME_TEMPLATE % (shot['k_ep'], shot['k_ed'], step_no, '_' + hash)))

    output_image_list = [filename_template % (i) for i in range(frame_start, frame_start+frame_count)]
    output_images = list()

    # Discard if output files already exist
    do_extract = False
    for f in output_image_list:
        if not os.path.exists(f):
            do_extract = True
            break
    if not do_extract:
        return hash, output_images

    # Get video dimensions
    width, height = get_video_resolution(input_file, db_common)

    # Output images in memory
    use_memory = True if shot['count'] <= MAX_FRAMES_COUNT else False

    ffmpeg_command = [db_common['tools']['ffmpeg']]
    ffmpeg_command.extend(["-hide_banner", "-loglevel", "warning"])

    # filter_str = filter_str.replace("nnedi3_weights",
    #     db_common['tools']['nnedi3_weights'])
    filter_str = filter_str.replace("nnedi3_weights", "nnedi3_weights.bin")

    ffmpeg_filter_str = "[0:v]%s[outv]" % (filter_str)
    ffmpeg_command.extend([
        "-ss", frame_no_to_sexagesimal(frame_start),
        "-i", input_file,
        "-t", str(frame_count/FPS),
        "-f", "image2pipe",
        "-filter_complex", clean_ffmpeg_filter(ffmpeg_filter_str),
        "-map", "[outv]",
        "-pix_fmt", "bgr24",
        "-vcodec", "rawvideo",
        "-"
    ])
    print_lightgrey("\t\t\t%s" % (' '.join(ffmpeg_command)))
    process = create_process(command=ffmpeg_command,
        process_cfg=db_common['process'])


    # Get frame(s) extracted by FFmpeg
    for no, img_filepath in zip(range(frame_count), output_image_list):
        raw_frame = np.frombuffer(process.stdout.read(3 * height * width), dtype=np.uint8)
        if raw_frame is None or len(raw_frame) == 0:
            sys.exit("error: frame %d has not been extracted\n\t%s" % (no, ffmpeg_command))
        img = raw_frame.reshape((height, width, 3))
        cv2.imwrite(img_filepath, img)
        if use_memory:
            output_images.append(img)
        no += 1
        print_yellow("\t\t\textracting: %d%%" % (int((100.0 * no)/frame_count)), flush=True, end='\r')
    print("\t\t                                                  ", end='\r')

    return hash, output_images



# TODO: remove following functions

def ffmpeg_deinterlace_single_frame(db, frame):
    filter_str, width, height = get_ffmpeg_filter(db, frame, 'deinterlace')
    return extract_single_frame(db, frame, filter_str, width, height, task='deinterlace')


def ffmpeg_deinterlace_and_pre_upscale_single_frame(db, frame):
    filter_str, width, height = get_ffmpeg_filter(db, frame, 'pre_upscale')
    return extract_single_frame(db, frame, filter_str, width, height, task='pre_upscale')


def ffmpeg_deinterlace_and_upscale_single_frame(db, frame):
        filter_str, width, height = get_ffmpeg_filter(db, frame, 'upscale')
        return extract_single_frame(db, frame, filter_str, width, height, task='upscale')





def extract_single_frame(db, frame, filter_str, width, height, task='upscale'):
    ffmpeg_command = [db['common']['settings']['ffmpeg_exe']]
    ffmpeg_command.extend(db['common']['settings']['verbose'].split(' '))

    # TODO: get nb of frames depending if this is the first frame of a shot
    # 1 if 1st frame
    # 2 otherwise, keep the second one
    frames_count = 2
    frame_no = frame['ref'] - 1

    ffmpeg_command.extend([
        "-ss", frame_no_to_sexagesimal(frame_no),
        "-i", frame['input'],
        "-t", str(frames_count/FPS),
        "-f", "image2pipe",
        "-filter_complex", clean_ffmpeg_filter(filter_str),
        "-map", "[outv]",
        "-pix_fmt", "bgr24",
        "-vcodec", "rawvideo",
        "-"
    ])
    # print(ffmpeg_command)
    process = create_process(ffmpeg_command)

    # Get frame(s) extracted by FFMPEG
    raw_frame = None
    no = 0
    while no < frames_count:
        # print("extract image (%d;%d)" % (width, height))
        raw_frame = process.stdout.read(3 * height * width)
        process.stdout.flush()
        if raw_frame is None or len(raw_frame) == 0:
            print("Error: frame has not been extracted\n\t%s" % (ffmpeg_command))
            print(process.stderr)
            sys.exit()

        if no == 1:
            raw_frame = np.frombuffer(raw_frame, dtype=np.uint8)
            deinterleaced_frame = raw_frame.reshape((height, width, 3))
        no += 1

    return deinterleaced_frame


