# -*- coding: utf-8 -*-
import os
import sys
import re
import signal
from utils.process import create_process
from utils.get_image_list import (
    FILENAME_TEMPLATE,
    get_image_list,
)
from utils.hash import (
    calculate_hash,
    log_filter,
)
from utils.pretty_print import *
import numpy as np
import cv2


def apply_avisynth_filters(shot, image_list,
    step_no, filters_str, input_hash, output_folder, db_common, get_hash:bool=False, do_force:bool=False):

    # Deinterlace only
    if not get_hash:
        print_cyan("(AviSynth)", end='')
        print_lightcyan("\tfilters=%s" % (filters_str))

    if 'deinterlace' not in filters_str:
        sys.exit(print_red("\terror: filter not yet supported, ignoring"))

    # Create folder to store the script
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Use a script name: easier for debug.
    # Later, generate it from a template
    script_filepath =os.path.abspath(os.path.join(
        db_common['directories']['config'],
        shot['k_ep'],
        "%s_%s.avs" % (shot['k_ep'], filters_str)))
    cache_path = output_folder

    # Open original script
    with open(script_filepath, mode='r+') as script_file:
        lines = script_file.readlines()

    # Modify it for this shot
    filter_str = ""
    for i, line in zip(range(len(lines)), lines):

        # Replace input file
        input_search = re.search(re.compile(r"^FFMPEGSource2\(\"(.+)\""), line)
        if input_search is not None:
            # print("succeded, line=[%s]" % (line.strip()))
            line = line.replace(input_search.group(1), shot['input'])
            # print("-> line=[%s]" % (line.strip()))

        # Replace first and last frame for trim
        # !!! Add frames because avisynth/FFmpge2 source is not frame accurate
        if shot['start'] > 0:
            avisynth_start = shot['start']
            avisynth_count = shot['count'] + 2
        else:
            avisynth_start = shot['start']
            avisynth_count = shot['count'] + 2

        input_file_search = re.search(re.compile("trim\(([^\)]+)"), line)
        if input_file_search is not None:
            line = line.replace(input_file_search.group(1),
                "%d,-%d" % (avisynth_start, avisynth_count))

        # Line has been patched
        lines[i] = line

        # Do not log input file/trim values
        stripped_line = line
        for c in ['\r', '\n', '\t', ' ', '\"', '\'']:
            stripped_line = stripped_line.replace(c, '')
        if line.startswith('#') or len(stripped_line) == 0:
            continue
        input_file_search = re.search(re.compile("FFMPEGSource2\(([^,]+)"), stripped_line)
        if input_file_search is not None:
            stripped_line = stripped_line.replace(input_file_search.group(1), 'source')
        else:
            # trim shall never be written on the same line
            input_file_search = re.search(re.compile("trim\(([^\)]+)"), stripped_line)
            if input_file_search is not None:
                stripped_line = stripped_line.replace(input_file_search.group(1), "first_frame,last_frame")
        filter_str += stripped_line + ';'

    # Calculate hash from this script
    if get_hash:
        hash = calculate_hash(filter_str=filter_str)
        return hash, None
    hash = log_filter(filter_str, shot['hash_log_file'])

    # Write it in the cache directory
    consolidated_filepath = os.path.join(cache_path,
        "%s_%s_%s.avs" % (shot['k_ep'], filters_str, hash))
    with open(consolidated_filepath, mode='w') as script_file:
        for line in lines:
            script_file.write(line)

    # Execute the FFmpeg command
    ffmpeg_command_common = [db_common['tools']['ffmpeg']]
    ffmpeg_verbose="-hide_banner -loglevel error"
    ffmpeg_command_common.extend(ffmpeg_verbose.split(' '))


    filename_template = os.path.abspath(os.path.join(output_folder,
        FILENAME_TEMPLATE % (shot['k_ep'], shot['k_ed'], step_no, '_' + hash)))
    output_image_list = get_image_list(
        shot=shot,
        folder=output_folder,
        step_no=step_no,
        hash=hash)

    # Discard if output files already exist
    do_extract = False
    for f in output_image_list:
        if not os.path.exists(f):
            do_extract = True
            break
    output_images = list()


    if do_extract:
        ffmpeg_command = ffmpeg_command_common + [
            "-i", os.path.abspath(consolidated_filepath),
            "-start_number", str(avisynth_start),
            filename_template
        ]
        process = create_process(command=ffmpeg_command, process_cfg=db_common['process'])
        try:
            stdout, stderr = process.communicate()
        except KeyboardInterrupt:
            process.send_signal(signal.SIGINT)
            sys.exit()
        except:
            process.kill()
            print("Error: timeout")
            stdout, stderr = process.communicate()
    else:
        print("\t\t\timages already deinterlaced")


    return hash, output_images



# # slower
# if do_extract:
#     # TODO: get initial dimension
#     height = 576
#     width = 720
#     ffmpeg_command = ffmpeg_command_common + [
#         "-i", os.path.abspath(consolidated_filepath),
#         "-f", "image2pipe",
#         "-pix_fmt", "bgr24",
#         "-vcodec", "rawvideo",
#         "-"
#     ]
#     process = create_process(ffmpeg_command, process_cfg=db_common['process'])
#     for frame_no, img_filepath in zip(range(shot['start'], shot['start'] + shot['count']), output_image_list):
#         # print("Extract frames: %d%%" % (int((100.0 * no)/frames_count)), end='\r')
#         raw_frame = process.stdout.read(3 * height * width)
#         # if raw_frame is None or len(raw_frame) == 0:
#         #     sys.exit("error: frame %d (%s) has not been extracted\n\t%s" % (frame_start + no, shot['k_ed'], ffmpeg_command))
#         img = np.frombuffer(raw_frame, dtype=np.uint8).reshape((height, width, 3))
#         output_images.append(img)
#         cv2.imwrite(filename=img_filepath, img=img)
#         # print("extracted frame no. %d (%s) " % (frame_start + no, shot['k_ed']), flush = True)

#     # print("                                       ", end='\r')


#     # print_lightgreen(ffmpeg_command)
#     process = create_process(command=ffmpeg_command, process_cfg=db_common['process'])
#     try:
#         stdout, stderr = process.communicate()
#     except KeyboardInterrupt:
#         process.send_signal(signal.SIGINT)
#         sys.exit()
#     except:
#         process.kill()
#         print("Error: timeout")
#         stdout, stderr = process.communicate()


# else:
#     print("\t\t\timages already deinterlaced")
