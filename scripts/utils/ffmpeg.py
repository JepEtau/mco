# -*- coding: utf-8 -*-
import sys
import datetime
import os
import re
import numpy as np
import cv2
import signal
import subprocess
import time

from pprint import pprint

from images.frames import frame_no_to_sexagesimal
from utils.common import create_pipe_in
from utils.path import get_deinterlaced_filepath_list
from utils.time_conversions import timestamp2sexagesimal


def ffmeg_clean_filter_complex(a_string):
    for c in ['\"', '\r', '\n']:
        a_string = a_string.replace(c, '')
    return a_string

def ffmpeg_execute_command(command=None, filename='', mode='', print_msg=False):
    # if mode == 'debug' or True:
    if mode == 'debug':
        print("\n*** FFMPEG command ***")
        for elem in command:
            if elem.startswith("-"):
                print("\n\t", end="")
            else:
                print("\t", end="")
            print(elem, end="")
        print("\n")

    if print_msg:
        now = datetime.datetime.now()
        _msg = "(%s) %s" % (now.strftime("%Y-%m-%d %H:%M:%S"), filename)
        print(_msg, end="", flush=True)
        startTime = time.time()

    line = ''
    if mode != 'debug':
        if hasattr(subprocess, 'STARTUPINFO'):
            startupInfo = subprocess.STARTUPINFO()
            startupInfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupInfo.dwFlags |= subprocess.STARTF_USESTDHANDLES
            osEnvironment = os.environ
        else:
            startupInfo = None
            osEnvironment = None

        if sys.platform == 'win32':
            _process = subprocess.Popen(command,
                                    stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    shell=False,
                                    env=osEnvironment,
                                    startupinfo=startupInfo,
                                    )
                                    # creationflags=subprocess.CREATE_NEW_CONSOLE

        else:
            _process = subprocess.Popen(command,
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        shell=False,
                                        env=osEnvironment,
                                        startupinfo=startupInfo,
                                        )

        try:
            _stdout, _stderr = _process.communicate()
        except KeyboardInterrupt:
            _process.send_signal(signal.SIGINT)
            sys.exit()
        except:
            _process.kill()
            print("Error: timeout")
            _stdout, _stderr = _process.communicate()

        line = _stderr.decode(encoding='UTF-8')
        line += _stdout.decode(encoding='UTF-8')

    if print_msg:
        elapsedTime = time.time() - startTime
        print("\t(%s)" % (timestamp2sexagesimal(elapsedTime)))
    return line




def get_duration(db, filename='', integrity=True):
    ffprobe_exe = db['common']['settings']['ffprobe_exe']
    command = [ffprobe_exe, "-hide_banner"]
    if integrity:
        command.extend(["-count_frames"])
    command.extend(["-i", filename])

    # Execute command
    if hasattr(subprocess, 'STARTUPINFO'):
        startupInfo = subprocess.STARTUPINFO()
        startupInfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupInfo.dwFlags |= subprocess.STARTF_USESTDHANDLES
        osEnvironment = os.environ
    else:
        startupInfo = None
        osEnvironment = None

    _stderr = None
    if False:
        for elem in command:
            if elem.startswith("-"):
                print("\n\t", end="")
            else:
                print("\t", end="")
            print(elem, end="")
        print("\n")
    if sys.platform == 'win32':
        _process = subprocess.Popen(command,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                shell=False,
                                env=osEnvironment,
                                startupinfo=startupInfo,
                                )
                                # creationflags=subprocess.CREATE_NEW_CONSOLE

    else:
        _process = subprocess.Popen(command,
                                    stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    shell=False,
                                    env=osEnvironment,
                                    startupinfo=startupInfo,
                                    )
    try:
        _stdout, _stderr = _process.communicate()
    except KeyboardInterrupt:
        _process.send_signal(signal.SIGINT)
    except:
        _process.kill()
        _stdout, _stderr = _process.communicate()

    duration = 0
    if _stderr is not None:
        line = _stderr.decode(encoding='UTF-8')
        line += _stdout.decode(encoding='UTF-8')
        # print(line)
        if integrity:
            # print(line)
            result= re.search(r"(File ended prematurely)", line)
            if result is not None:
                return 0.0

        result = re.search(r"Duration: ([0-9]{2}):([0-9]{2}):([0-9]{2}).([0-9]{2}),", line)
        if result:
            duration = int(result[1]) * 60
            duration = (duration + int(result[2])) * 60
            duration = (duration + int(result[3])) * 100
            duration += int(result[4])
        else:
            return 0.0
    else:
        return 0.0

    return float(duration)/100.0



def get_ffmpeg_filter(frame, step):
    filter_str = frame['filters']['ffmpeg']['deinterlace']
    if step in ['pre_upscale', 'upscale', 'denoise']:
        f = frame['filters']['ffmpeg']['pre_upscale']
        if f is not None:
            filter_str += ',' + f

    if step in ['upscale', 'denoise']:
        f = frame['filters']['ffmpeg']['upscale']
        if f is not None and f != 'default':
            filter_str += ',' + f

    if step == 'denoise':
        f = frame['filters']['ffmpeg']['denoise']
        if f is not None and f != 'default':
            filter_str += ',' + f

    ffmpeg_filter_str = "[0:v]%s[outv]" % (filter_str)

    if step in ['deinterlace', 'pre_upscale']:
        width = frame['dimensions']['initial']['w']
        height = frame['dimensions']['initial']['h']
        ffmpeg_filter_str = ffmpeg_filter_str.replace("width_initial", "%d" % (width))
    else:
        # Upscale is done by FFmpeg
        width = frame['dimensions']['upscale']['w']
        height = frame['dimensions']['upscale']['h']
        ffmpeg_filter_str = ffmpeg_filter_str.replace("height_upscale", "%d" % (height))
        ffmpeg_filter_str = ffmpeg_filter_str.replace("width_upscale", "%d" % (width))

    return [ffmpeg_filter_str, width, height]



def ffmpeg_extract_single_frame(database, frame, filter_str, width, height):
    # print("ffmpeg_extract_frame", flush=True)
    command_ffmpeg = [database['common']['settings']['ffmpeg_exe']]
    command_ffmpeg.extend(database['common']['settings']['verbose'].split(' '))
    # print(command_ffmpeg, flush=True)
    # TODO: get nb of frames depending if this is the first frame of a shot
    # 1 if 1st frame
    # 2 otherwise, keep the second one
    frames_count = 2
    frame_no = frame['no'] - 1

    command_ffmpeg.extend([
        "-ss", frame_no_to_sexagesimal(frame_no),
        "-i", frame['input'],
        "-t", str(frames_count/database['common']['fps']),
        "-f", "image2pipe",
        "-filter_complex", ffmeg_clean_filter_complex(filter_str),
        "-map", "[outv]",
        "-pix_fmt", "bgr24",
        "-vcodec", "rawvideo",
        "-"
    ])
    # print(command_ffmpeg)
    process_cfg = database['common']['process']
    pipe_in = create_pipe_in(command_ffmpeg, process_cfg)
    # , mode='debug')

    # Get frame(s) extracted by FFMPEG
    rawFrame = None
    no = 0
    while no < frames_count:
        # print("extract image (%d;%d)" % (width, height))
        rawFrame = pipe_in.stdout.read(3 * height * width)
        pipe_in.stdout.flush()
        if rawFrame is None or len(rawFrame) == 0:
            print("Error: frame has not been extracted\n\t%s" % (command_ffmpeg))
            print(pipe_in.stderr)
            sys.exit()

        if no == 1:
            rawFrame = np.frombuffer(rawFrame, dtype=np.uint8)
            rgbFrame = rawFrame.reshape((height, width, 3))
        no += 1
    return rgbFrame



def ffmpeg_deinterlace_single_frame(database, frame):
    # print("deinterlace: (-) -> %s" % (frame['filepath']['deinterlace']))
    # Extract image with ffmpeg
    filter_str, width, height = get_ffmpeg_filter(frame, 'deinterlace')
    return ffmpeg_extract_single_frame(database, frame, filter_str, width, height)




def ffmpeg_deinterlace_and_pre_upscale_single_frame(database, frame):
    filter_str = ""
    # if frame['filters']['ffmpeg']['pre_upscale'] is not None:
    print("pre_upscale: (-) -> %s" % (frame['filepath']['upscale']))
    # get FFMPEG filter
    filter_str, width, height = get_ffmpeg_filter(frame, 'pre_upscale')
    print(filter_str)
    # print("(%dx%d)" % (width, height))
    return ffmpeg_extract_single_frame(database, frame, filter_str, width, height)

    # return None



def ffmpeg_deinterlace_and_upscale_single_frame(database, frame):
    filter_str = ""
    if frame['filters']['ffmpeg']['upscale'] is not None:
        # print("upscale: (-) -> %s" % (frame['filepath']['upscale']))
        # get FFMPEG filter
        filter_str, width, height = get_ffmpeg_filter(frame, 'upscale')
        # print(filter_str)
        # print("(%dx%d" % (width, height))
        return ffmpeg_extract_single_frame(database, frame, filter_str, width, height)

    return None




def ffmpeg_extract_shot(database, shot, filter_str, width, height, task='upscale'):

    command_ffmpeg = [database['common']['settings']['ffmpeg_exe']]
    command_ffmpeg.extend(database['common']['settings']['verbose'].split(' '))

    frames_count = shot['count']
    frame_start = shot['start']

    command_ffmpeg.extend([
        "-ss", frame_no_to_sexagesimal(frame_start),
        "-i", shot['input'],
        "-t", str(frames_count/database['common']['fps']),
        "-f", "image2pipe",
        "-filter_complex", ffmeg_clean_filter_complex(filter_str),
        "-map", "[outv]",
        "-pix_fmt", "bgr24",
        "-vcodec", "rawvideo",
        "-"
    ])
    # print(command_ffmpeg)
    process_cfg = database['common']['process']
    pipe_in = create_pipe_in(command_ffmpeg, process_cfg)

    # list of filepaths
    img_filepaths = get_deinterlaced_filepath_list(database, shot, task=task)

    # Get frame(s) extracted by FFMPEG
    no = 0
    while no < frames_count:
        # print("Extract frames: %d%%" % (int((100.0 * no)/frames_count)), flush=True, end='\r')
        rawFrame = pipe_in.stdout.read(3 * height * width)
        pipe_in.stdout.flush()
        if rawFrame is None or len(rawFrame) == 0:
            sys.exit("error: frame %d (%s) has not been extracted\n\t%s" % (frame_start + no, shot['k_ed'], command_ffmpeg))

        rawFrame = np.frombuffer(rawFrame, dtype=np.uint8)
        img = rawFrame.reshape((height, width, 3))
        cv2.imwrite(img_filepaths[no], img)
        # print("extracted frame no. %d (%s) " % (frame_start + no, shot['k_ed']), flush = True)
        no += 1
    return no

    # print("", flush=True, end='\r')




def ffmpeg_deinterlace_shot(database, shot):
    filter_str, width, height = get_ffmpeg_filter(shot, 'deinterlace')
    return ffmpeg_extract_shot(database, shot, filter_str, width, height, task='deinterlace')



def ffmpeg_deinterlace_and_pre_upscale_shot(database, shot):
    filter_str = ""
    # if shot['filters']['ffmpeg']['pre_upscale'] is None:
    #     print("warning: pre-upscale filter is not defined")
    # get FFMPEG filter
    filter_str, width, height = get_ffmpeg_filter(shot, 'pre_upscale')

    return ffmpeg_extract_shot(database, shot, filter_str, width, height, task='pre_upscale')



def ffmpeg_deinterlace_and_upscale_shot(database, shot):
    # filter_str = ""
    # if shot['filters']['ffmpeg']['upscale'] is not None:
    # get FFMPEG filter
    filter_str, width, height = get_ffmpeg_filter(shot, 'upscale')
    return ffmpeg_extract_shot(database, shot, filter_str, width, height, task='upscale')



