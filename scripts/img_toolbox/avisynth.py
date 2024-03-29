# -*- coding: utf-8 -*-
import sys
import os
import re
from datetime import datetime
import time
import cv2
import numpy as np
import platform

from img_toolbox.ffmpeg_deinterlace import ffmpeg_deinterlace
from img_toolbox.ffmpeg_utils import (
    execute_simple_ffmpeg_command,
    get_video_resolution
)
from utils.common import FPS
from img_toolbox.utils import is_progressive_file_valid
from utils.process import create_process
from processing_chain.get_image_list import (
    FILENAME_TEMPLATE,
    get_image_list,
    get_deinterlaced_image_filepaths,
)
from processing_chain.hash import (
    calculate_hash,
    log_filter,
)
from utils.pretty_print import *
from utils.time_conversions import convert_s_to_m_s_ms, frame_no_to_sexagesimal
from utils.types import Shot


# Extract more frames to verify frames no for each shot
AVISYNTH_ADD_FRAMES = 0


def avisynth_executor(shot:Shot, image_list,
    input_hash,
    step_no, filters_str,
    do_save:bool, output_folder:str,
    db_common, get_hash:bool=False):

    if filters_str == 'deinterlace':
        return avisynth_deinterlace(shot, image_list,
            step_no, filters_str,
            do_save, output_folder,
            db_common, get_hash)
    else:
        # raise ValueError(f"filter [{filters_str}] is not supported")

        return avisynth_script_executor(shot, image_list,
            input_hash,
            step_no, filters_str,
            do_save, output_folder,
            db_common, get_hash)



def avisynth_deinterlace(shot, image_list,
    step_no, filters_str,
    do_save:bool, output_folder:str,
    db_common, get_hash:bool=False):

    verbose = False

    # Deinterlace only
    if not get_hash:
        print_cyan("(AviSynth)", end='')
        print_lightcyan("\tfilters=%s" % (filters_str))

    # Use a script template
    script_filepath =os.path.abspath(os.path.join(
        db_common['directories']['config'],
        shot['k_ep'], f"{shot['k_ep']}_{filters_str}.avs"))

    # Parse and modify this script
    (filter_str, lines) = avisynth_patch_deinterlace_script(shot,
        script_filepath, shot['inputs']['interlaced']['filepath'])

    # Calculate hash from this script
    if get_hash:
        hash = calculate_hash(filter_str=filter_str)
        return hash, None
    hash = log_filter(filter_str, shot['hash_log_file'])


    if verbose:
        print_lightcyan("avisynth_deinterlace")

    # Get progressive filename
    progressive_filepath = shot['inputs']['progressive']['filepath']

    # Write it in the cache directory
    if shot['inputs']['progressive']['enable']:
        # and shot['inputs']['progressive']['start'] == 0
        # and shot['inputs']['progressive']['count'] == -1):
        # Store it in the cache_progressive folder
        cache_progressive = shot['inputs']['progressive']['cache']
        if not os.path.exists(cache_progressive):
            os.makedirs(cache_progressive)
        script_filepath = progressive_filepath.replace('.mkv', '.avs')

        # os.path.join(
        #     cache_progressive,
        #     "%s_%s_%s.avs" % (shot['k_ep'], filters_str, hash))
    else:
        # Store it in the output folder
        script_filepath = os.path.join(
            output_folder,
            f"{shot['k_ep']}_{filters_str}_{hash}.avs")

    # Create the output folder
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    if verbose:
        print_yellow("\t\t\t%s" % (script_filepath))
    if not os.path.exists(script_filepath):
        with open(script_filepath, mode='w') as script_file:
            for line in lines:
                script_file.write(line)


    # Output images
    filename_template = os.path.abspath(os.path.join(output_folder,
        FILENAME_TEMPLATE % (shot['k_ep'], shot['k_ed'], step_no, '_' + hash)))
    output_image_list = get_deinterlaced_image_filepaths(
        shot=shot,
        folder=output_folder,
        hash=hash)
    output_images = list()

    # Discard if output files already exist
    do_extract = False
    for f in output_image_list:
        if not os.path.exists(f):
            if verbose:
                print(f"missing file: {f}")
            do_extract = True
            break
    if not do_extract:
        print("\t\t\timages already deinterlaced")
        return hash, output_images


    # Initialize flags
    do_deinterlace = False
    do_generate_ffv1_file = False
    do_use_ffv1_file = False

    # Try using ffv1 file if enable and exists
    if shot['inputs']['progressive']['enable']:
        do_use_ffv1_file = True
        if is_progressive_file_valid(shot=shot, db_common=db_common):
            if verbose:
                print("\t\t\tffv1 is enabled and file exists: %s" % (progressive_filepath))
                do_generate_ffv1_file = False

        else:
            if verbose:
                print("\t\t\tffv1 is enabled but file does not exist: %s" % (progressive_filepath))
            do_generate_ffv1_file = True
            if platform.system() != "Windows":
                print_red("\t\t\terror: avisynth is not supported on this platform")
                # Force deinterlace because avisynth is not supported
                do_deinterlace = True
                do_generate_ffv1_file = False
                do_use_ffv1_file = False

    else:
        if verbose:
            print("\t\t\tffv1 is disabled")
        do_deinterlace = True


    # Execute the FFmpeg command
    ffmpeg_command_common = [db_common['tools']['ffmpeg']]
    ffmpeg_verbose = db_common['settings']['verbose']
    # ffmpeg_verbose = "-hide_banner -loglevel error"
    ffmpeg_command_common.extend(ffmpeg_verbose.split(' '))


    # Generate FFv1 file if not exists
    if do_generate_ffv1_file:
        ffmpeg_command = ffmpeg_command_common + [
            "-i", os.path.abspath(script_filepath),
            "-r", str(25),
            '-pixel_format', 'bgr24',
            "-threads", "4",
            "-vcodec", "ffv1",
            "-y", progressive_filepath
        ]
        start_time = time.time()
        print_lightgreen(f"%s: {shot['k_ed']}:{shot['k_ep']}:{shot['k_part']} FFv1 file has to be generated" % (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        print_lightgreen("\tIt may take about 30 minutes")

        print_lightgrey("\t\t\t%s" % (' '.join(ffmpeg_command)))
        execute_simple_ffmpeg_command(ffmpeg_command=ffmpeg_command)

        elapsed_time = time.time() - start_time
        minutes, seconds, milliseconds = convert_s_to_m_s_ms(elapsed_time)
        print_purple("\t\t\tDeinterlaced shot no. %d in %02d:%02d.%d (%.02fs/f)" % (
            shot['no'],
            minutes, seconds, int(1 + milliseconds/100),
            elapsed_time/shot['count']))
        convert_s_to_m_s_ms
        print(" %.02fs" % (time.time() - start_time))

    if do_deinterlace:
        if platform.system() == "Windows":
            avisynth_start = shot['start'] if shot['start'] < AVISYNTH_ADD_FRAMES else shot['start'] - AVISYNTH_ADD_FRAMES
            ffmpeg_command = ffmpeg_command_common + [
                "-i", os.path.abspath(script_filepath),
                '-pixel_format', 'bgr24',
                "-start_number", str(avisynth_start),
                filename_template
            ]
            print_lightgrey("\t\t\t%s" % (' '.join(ffmpeg_command)))
            execute_simple_ffmpeg_command(ffmpeg_command=ffmpeg_command)
        else:
            print_orange("\t\t\treplaced by low-quality deinterlace algorithm (yadif)")
            # Deinterlace
            # http://avisynth.nl/index.php/Nnedi3_resize16#Parameters_for_nnedi3
            filter_deinterlace="""nnedi=weights=nnedi3_weights:
                nsize=s8x6:nns=n128:qual=slow:etype=s:pscrn=new3,fps=fps=25
                """
            filter_deinterlace_fast="""yadif,fps=fps=25 """
            __hash, output_images = ffmpeg_deinterlace(
                shot=shot,
                step_no=step_no,
                filter_str=filter_deinterlace_fast,
                output_folder=output_folder,
                db_common=db_common,
                get_hash=get_hash,
                forced_hash=hash)

    if do_use_ffv1_file:
        # Frame start and count
        frame_start = shot['start']
        frame_start -= shot['inputs']['progressive']['start']
        frame_count = shot['count']
        if verbose:
            print("\textract: %d (%d)" % (frame_start, frame_count))

        if AVISYNTH_ADD_FRAMES > 0 and frame_start > AVISYNTH_ADD_FRAMES:
            frame_start -= AVISYNTH_ADD_FRAMES
            frame_count += 2 * AVISYNTH_ADD_FRAMES
            if verbose:
                print("\tpatched to : %d (%d)" % (frame_start, frame_count))

            filename_template = os.path.abspath(os.path.join(output_folder,
                FILENAME_TEMPLATE % (shot['k_ep'], shot['k_ed'], step_no, '_' + hash)))
            output_image_list = [filename_template % (i) for i in range(frame_start, frame_start+frame_count)]


        # Get video dimensions
        width, height = get_video_resolution(progressive_filepath, db_common)

        # FFmpeg command
        ffmpeg_command = ffmpeg_command_common + [
            "-ss", frame_no_to_sexagesimal(frame_start),
            "-i", progressive_filepath,
            "-t", str(frame_count/FPS),
            "-f", "image2pipe",
            "-pix_fmt", "bgr24",
            "-vcodec", "rawvideo",
            "-"
        ]

        # Create a process and start it
        print_lightgrey("\t\t\t%s" % (' '.join(ffmpeg_command)))
        process = create_process(command=ffmpeg_command,
            process_cfg=db_common['process'])

        # Get frames from pipe
        for no, img_filepath in zip(range(frame_count), output_image_list):
            raw_frame = np.frombuffer(process.stdout.read(3 * height * width), dtype=np.uint8)
            if raw_frame is None or len(raw_frame) == 0:
                sys.exit("error: frame %d has not been extracted\n\t%s" % (no, ffmpeg_command))
            img = raw_frame.reshape((height, width, 3))
            if  do_save:
                cv2.imwrite(img_filepath, img)
            output_images.append(img)
            no += 1
            print_yellow("\t\t\textracting: %d%%" % (int((100.0 * no)/frame_count)), flush=True, end='\r')
        print("\t\t                                                  ", end='\r')

    return hash, output_images




def avisynth_script_executor(shot, image_list,
    input_hash,
    step_no, script_filename,
    do_save:bool, output_folder:str,
    db_common, get_hash:bool=False):

    verbose = False

    if not get_hash:
        print_cyan("(AviSynth)", end='')
        print_lightcyan("\tfilters=%s" % (script_filename))

    # Get the script file
    script_filepath = os.path.abspath(os.path.join(
        db_common['directories']['config'],
        shot['k_ep'], f"{script_filename}.avs"))

    # Dirty, specific to this project
    if step_no == 0:
        # Assume this is the interlaced video
        raise ValueError("This script cannot be used to deinterlace. Append a deinterlace script before")


    # Get file(s) from previous node
    input_filepath = ''
    if step_no == 1:
        # previous task was deinterlace, use the deinterlace filter
        filename = os.path.split(shot['inputs']['interlaced']['filepath'])[1]
        filename = filename.replace('.mkv', f"_{input_hash}.mkv")
        input_filepath = os.path.join(db_common['directories']['cache_progressive'], filename)
        do_generate_ffv1_file = False
    else:
        # Create a FFv1 file until find a solution to pipe in/out images
        # input_filepath= ...
        print(red("TODO: create FFv1 file"))
        input_filepath = os.path.abspath(os.path.join(output_folder,
            FILENAME_TEMPLATE % (shot['k_ep'], shot['k_ed'], step_no, '_' + input_hash)))
        do_generate_ffv1_file = True

    # Parse and modify this script
    (filter_str, lines) = avisynth_patch_script(shot, script_filepath, input_filepath=input_filepath)
    hash = calculate_hash(filter_str=filter_str)

    # Calculate hash
    filter_str = f"{script_filename}_{hash}"
    if get_hash:
        hash = calculate_hash(filter_str=filter_str)
        return hash, None
    hash = log_filter(filter_str, shot['hash_log_file'])


    if verbose:
        print_lightcyan("avisynth_deinterlace")

    # Get progressive filename

    # Store it in the output folder
    script_filepath = os.path.join(
        output_folder,
        f"{shot['k_ep']}_{script_filename}_{hash}.avs")

    # Create the output folder
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    if verbose:
        print_yellow("\t\t\t%s" % (script_filepath))
    if not os.path.exists(script_filepath):
        with open(script_filepath, mode='w') as script_file:
            for line in lines:
                script_file.write(line)

    # Output images
    filename_template = os.path.abspath(os.path.join(output_folder,
        FILENAME_TEMPLATE % (shot['k_ep'], shot['k_ed'], step_no, '_' + hash)))
    output_image_list = get_image_list(
        shot=shot,
        folder=output_folder,
        step_no=step_no,
        hash=hash)
    output_images = list()

    # Discard if output files already exist
    do_extract = False
    for f in output_image_list:
        if not os.path.exists(f):
            if verbose:
                print(f"missing file: {f}")
            do_extract = True
            break
    if not do_extract:
        print("\t\t\timages already generated")
        return hash, output_images


    # FFmpeg command
    ffmpeg_command_common = [db_common['tools']['ffmpeg']]
    ffmpeg_verbose = db_common['settings']['verbose']
    # ffmpeg_verbose = "-hide_banner -loglevel error"
    ffmpeg_command_common.extend(ffmpeg_verbose.split(' '))


    # Execute script
    ffmpeg_command = ffmpeg_command_common + [
        "-i", os.path.abspath(script_filepath),
        '-pixel_format', 'bgr24',
        "-start_number", "0",
        filename_template
    ]
    print_lightgrey("\t\t\t%s" % (' '.join(ffmpeg_command)))
    execute_simple_ffmpeg_command(ffmpeg_command=ffmpeg_command)



    do_use_ffv1_file = False
    if do_use_ffv1_file:
        # Frame start and count
        frame_start = shot['start']
        frame_start -= shot['inputs']['progressive']['start']
        frame_count = shot['count']
        if verbose:
            print("\textract: %d (%d)" % (frame_start, frame_count))

        # Get video dimensions
        width, height = get_video_resolution(progressive_filepath, db_common)

        # FFmpeg command
        ffmpeg_command = ffmpeg_command_common + [
            "-ss", frame_no_to_sexagesimal(frame_start),
            "-i", progressive_filepath,
            "-t", str(frame_count/FPS),
            "-f", "image2pipe",
            "-pix_fmt", "bgr24",
            "-vcodec", "rawvideo",
            "-"
        ]

        # Create a process and start it
        print_lightgrey("\t\t\t%s" % (' '.join(ffmpeg_command)))
        process = create_process(command=ffmpeg_command,
            process_cfg=db_common['process'])

        # Get frames from pipe
        for no, img_filepath in zip(range(frame_count), output_image_list):
            raw_frame = np.frombuffer(process.stdout.read(3 * height * width), dtype=np.uint8)
            if raw_frame is None or len(raw_frame) == 0:
                sys.exit("error: frame %d has not been generated\n\t%s" % (no, ffmpeg_command))
            img = raw_frame.reshape((height, width, 3))
            if  do_save:
                cv2.imwrite(img_filepath, img)
            output_images.append(img)
            no += 1
            print_yellow("\t\t\tprocessing: %d%%" % (int((100.0 * no)/frame_count)), flush=True, end='\r')
        print("\t\t                                                  ", end='\r')

    return hash, output_images







def avisynth_patch_deinterlace_script(shot:Shot, script_filepath, input_filepath):

    # Modify this script
    with open(script_filepath, mode='r+') as script_file:
        lines = script_file.readlines()


    # Replace first and last frame for trim
    # !!! Add frames because avisynth/FFmpge2 source is not frame accurate
    if shot['start'] > 0:
        avisynth_start = shot['start'] - AVISYNTH_ADD_FRAMES
        avisynth_count = shot['count'] +  2 * AVISYNTH_ADD_FRAMES
    else:
        avisynth_start = shot['start']
        avisynth_count = shot['count'] +  AVISYNTH_ADD_FRAMES

    # Deinterlace shot
    trim_line = "trim(%d,end=%d)" % (avisynth_start, (avisynth_start + avisynth_count - 1))

    if shot['inputs']['progressive']['enable']:
        # Use progressive file
        if (shot['inputs']['progressive']['start'] == 0
            and shot['inputs']['progressive']['count'] == -1):
            # Full
            trim_line = "# " + trim_line
        elif shot['inputs']['progressive']['count'] == -1:
            # From start to the end of video file
            trim_line = "trim(%d,0)" % (shot['inputs']['progressive']['start'])
        else:
            # From start to the end of the specified end
            trim_line = "trim(%d,end=%d)" % (
                shot['inputs']['progressive']['start'],
                shot['inputs']['progressive']['start'] + shot['inputs']['progressive']['count'] - 1)

    trim_line += '\n'

    # Modify this script for this shot
    filter_str = ""
    for i, line in zip(range(len(lines)), lines):

        # Replace input file
        if (search := re.search(re.compile("FFMPEGSource2\(\"(.+)\""), line)):
            line = line.replace(search.group(1), input_filepath)

        if (search := re.search(re.compile("FFVideoSource\(\"(.+)\""), line)):
            line = line.replace(search.group(1), input_filepath)

        # Trim
        if (search := re.search(re.compile("trim\(([^\)]+)"), line)):
            line = trim_line

        # Line has been patched
        lines[i] = line

        # TODO: discard comments: http://avisynth.nl/index.php/The_full_AviSynth_grammar

        # Do not log input file/trim values
        stripped_line = line
        for c in ['\r', '\n', '\t', ' ', '\"', '\'']:
            stripped_line = stripped_line.replace(c, '')

        if line.startswith('#') or len(stripped_line) == 0:
            continue

        comment_pos = line.find('#')
        if comment_pos != -1:
            if '#' in line:
                stripped_line = line[:comment_pos]

        if line.startswith('#') or len(stripped_line) == 0:
            continue

        if (search := re.search(re.compile("FFMPEGSource2\(([^,]+)"), stripped_line)):
            stripped_line = stripped_line.replace(search.group(1), 'source')
        if (search := re.search(re.compile("FFVideoSource\(([^,]+)"), stripped_line)):
            stripped_line = stripped_line.replace(search.group(1), 'source')

        if (search := re.search(re.compile("trim\(([^\)]+)"), stripped_line)):
            stripped_line = stripped_line.replace(search.group(1), "first_frame,last_frame")

        # Do not append lines which contains multiprocessing keywords,
        # otherwise frame no. will be erroneous
        do_append = True
        if ('MT_MODE' in stripped_line
            or 'MTMode' in stripped_line
            or 'Prefetch' in stripped_line):
            do_append = False

        if do_append:
            filter_str += stripped_line + ';'

    return (filter_str, lines)




def avisynth_patch_script(shot:Shot, script_filepath, input_filepath):

    # Modify this script
    with open(script_filepath, mode='r+') as script_file:
        lines = script_file.readlines()

    # Replace first and last frame for trim
    # !!! Add frames because avisynth/FFmpge2 source is not frame accurate
    # TODO verify this!!!
    if shot['start'] > 0:
        avisynth_start = shot['start'] - AVISYNTH_ADD_FRAMES
        avisynth_count = shot['count'] +  2 * AVISYNTH_ADD_FRAMES
    else:
        avisynth_start = shot['start']
        avisynth_count = shot['count'] +  AVISYNTH_ADD_FRAMES
    trim_line = "trim(%d, end=%d)\n" % (avisynth_start, (avisynth_start + avisynth_count - 1))

    # Modify this script for this shot
    filter_str = ""
    for i, line in zip(range(len(lines)), lines):

        if input_filepath != '':
            # Replace input file
            input_search = re.search(re.compile(r"^FFMPEGSource2\(\"(.+)\""), line)
            if input_search is not None:
                line = line.replace(input_search.group(1), input_filepath)

        # Trim
        input_file_search = re.search(re.compile("trim\(([^\)]+)"), line)
        if input_file_search is not None:
            line = trim_line


        # TODO: discard comments: http://avisynth.nl/index.php/The_full_AviSynth_grammar

        # Do not log input file/trim values
        stripped_line = line
        for c in ['\r', '\n', '\t', ' ', '\"', '\'']:
            stripped_line = stripped_line.replace(c, '')

        if line.startswith('#') or len(stripped_line) == 0:
            continue

        comment_pos = line.find('#')
        if comment_pos != -1:
            if '#' in line:
                stripped_line = line[:comment_pos]


        input_file_search = re.search(re.compile("FFMPEGSource2\(([^,]+)"), stripped_line)
        if input_file_search is not None:
            stripped_line = stripped_line.replace(input_file_search.group(1), 'source')
        else:
            # trim shall never be written on the same line
            input_file_search = re.search(re.compile("trim\(([^\)]+)"), stripped_line)
            if input_file_search is not None:
                stripped_line = stripped_line.replace(input_file_search.group(1), "first_frame,last_frame")

        filter_str += stripped_line + ';'

        # Line has been patched
        lines[i] = line

    return (filter_str, lines)
