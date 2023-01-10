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
from utils.path import (
    get_deinterlaced_filepath_list,
    get_deinterlaced_path_and_filename,
)
from utils.time_conversions import timestamp2sexagesimal



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

    w = frame['dimensions']['deinterlace']['w']
    h = frame['dimensions']['deinterlace']['h']
    ffmpeg_filter_str = ffmpeg_filter_str.replace("width_deinterlace", "%d" % (w))
    ffmpeg_filter_str = ffmpeg_filter_str.replace("height_deinterlace", "%d" % (h))

    if step in ['deinterlace', 'pre_upscale']:
        width = frame['dimensions']['deinterlace']['w']
        height = frame['dimensions']['deinterlace']['h']
        ffmpeg_filter_str = ffmpeg_filter_str.replace("width_deinterlace", "%d" % (width))
        ffmpeg_filter_str = ffmpeg_filter_str.replace("height_deinterlace", "%d" % (height))
    else:
        # Upscale is done by FFmpeg
        width = frame['dimensions']['upscale']['w']
        height = frame['dimensions']['upscale']['h']
        ffmpeg_filter_str = ffmpeg_filter_str.replace("width_upscale", "%d" % (width))
        ffmpeg_filter_str = ffmpeg_filter_str.replace("height_upscale", "%d" % (height))

    return [ffmpeg_filter_str, width, height]



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



def ffmpeg_extract_shot(database, shot, filter_str, width, height, task='upscale'):
    command_ffmpeg = [database['common']['settings']['ffmpeg_exe']]
    command_ffmpeg.extend(database['common']['settings']['verbose'].split(' '))

    frames_count = shot['count']
    frame_start = shot['ref']

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
        raw_frame = pipe_in.stdout.read(3 * height * width)
        pipe_in.stdout.flush()
        if raw_frame is None or len(raw_frame) == 0:
            sys.exit("error: frame %d (%s) has not been extracted\n\t%s" % (frame_start + no, shot['k_ed'], command_ffmpeg))

        raw_frame = np.frombuffer(raw_frame, dtype=np.uint8)
        img = raw_frame.reshape((height, width, 3))
        cv2.imwrite(img_filepaths[no], img)
        # print("extracted frame no. %d (%s) " % (frame_start + no, shot['k_ed']), flush = True)
        no += 1

    return no



def ffmpeg_extract_shot_tests(db, shot, filter_str, width, height, task='upscale'):

    command_ffmpeg = [db['common']['settings']['ffmpeg_exe']]
    command_ffmpeg.extend(db['common']['settings']['verbose'].split(' '))

    frames_count = shot['count']
    frame_start = shot['ref']

    output_path, filename = get_deinterlaced_path_and_filename(db, shot, task=task)
    output_filepath = os.path.join(output_path, filename)
    latest_filepath =  output_filepath % (frame_start + frames_count - 1)
    # print("%s: %s -> %s" % (output_path, filename, output_filepath))

    command_ffmpeg.extend([
        "-ss", frame_no_to_sexagesimal(frame_start),
        "-i", shot['input'],
        "-t", str(frames_count/db['common']['fps']),
        "-filter_complex", ffmeg_clean_filter_complex(filter_str),
        "-start_number", str(frame_start),
        "-map", "[outv]",
        "-y", output_filepath
    ])

    process_cfg = db['common']['process']
    pipe_in = create_pipe_in(command_ffmpeg, process_cfg)
    while not os.path.exists(latest_filepath):
        time.sleep(1)

    # print(command_ffmpeg)
    # subprocess.call(command_ffmpeg)
    # print("ended")


    # if hasattr(subprocess, 'STARTUPINFO'):
    #     startupInfo = subprocess.STARTUPINFO()
    #     startupInfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    #     startupInfo.dwFlags |= subprocess.STARTF_USESTDHANDLES
    #     osEnvironment = os.environ
    # else:
    #     startupInfo = None
    #     osEnvironment = None
    # _proc = subprocess.Popen(command_ffmpeg,
    #                         stdin=subprocess.PIPE,
    #                         stdout=subprocess.PIPE,
    #                         stderr=subprocess.PIPE,
    #                         shell=False,
    #                         env=osEnvironment,
    #                         startupinfo=startupInfo,
    #                         )
    # try:
    #     std_out, std_err = _proc.communicate(timeout=300)
    # except:
    #     _proc.kill()
    #     std_out, std_err = _proc.communicate()

    # if len(std_out) > 0:
    #     print("STDERR")
    #     print(std_out)
    #     print("")

    # if len(std_err) > 0:
    #     print("STDERR")
    #     print(std_err)

    return shot['count']



def ffmpeg_deinterlace_shot(database, shot):
    filter_str, width, height = get_ffmpeg_filter(shot, 'deinterlace')
    print(filter_str)
    return ffmpeg_extract_shot(database, shot, filter_str, width, height, task='deinterlace')



def ffmpeg_deinterlace_and_pre_upscale_shot(database, shot):
    filter_str, width, height = get_ffmpeg_filter(shot, 'pre_upscale')
    return ffmpeg_extract_shot(database, shot, filter_str, width, height, task='pre_upscale')



def ffmpeg_deinterlace_and_upscale_shot(database, shot):
    filter_str, width, height = get_ffmpeg_filter(shot, 'upscale')
    return ffmpeg_extract_shot(database, shot, filter_str, width, height, task='upscale')



def ffmpeg_extract_single_frame(db, frame, filter_str, width, height, task='upscale'):
    command_ffmpeg = [db['common']['settings']['ffmpeg_exe']]
    command_ffmpeg.extend(db['common']['settings']['verbose'].split(' '))

    # TODO: get nb of frames depending if this is the first frame of a shot
    # 1 if 1st frame
    # 2 otherwise, keep the second one
    frames_count = 2
    frame_no = frame['ref'] - 1

    command_ffmpeg.extend([
        "-ss", frame_no_to_sexagesimal(frame_no),
        "-i", frame['input'],
        "-t", str(frames_count/db['common']['fps']),
        "-f", "image2pipe",
        "-filter_complex", ffmeg_clean_filter_complex(filter_str),
        "-map", "[outv]",
        "-pix_fmt", "bgr24",
        "-vcodec", "rawvideo",
        "-"
    ])
    # print(command_ffmpeg)
    process_cfg = db['common']['process']
    pipe_in = create_pipe_in(command_ffmpeg, process_cfg)

    # Get frame(s) extracted by FFMPEG
    raw_frame = None
    no = 0
    while no < frames_count:
        # print("extract image (%d;%d)" % (width, height))
        raw_frame = pipe_in.stdout.read(3 * height * width)
        pipe_in.stdout.flush()
        if raw_frame is None or len(raw_frame) == 0:
            print("Error: frame has not been extracted\n\t%s" % (command_ffmpeg))
            print(pipe_in.stderr)
            sys.exit()

        if no == 1:
            raw_frame = np.frombuffer(raw_frame, dtype=np.uint8)
            deinterleaced_frame = raw_frame.reshape((height, width, 3))
        no += 1

    return deinterleaced_frame



def ffmpeg_deinterlace_single_frame(database, frame):
    filter_str, width, height = get_ffmpeg_filter(frame, 'deinterlace')
    return ffmpeg_extract_single_frame(database, frame, filter_str, width, height, task='deinterlace')



def ffmpeg_deinterlace_and_pre_upscale_single_frame(database, frame):
    filter_str, width, height = get_ffmpeg_filter(frame, 'pre_upscale')
    return ffmpeg_extract_single_frame(database, frame, filter_str, width, height, task='pre_upscale')



def ffmpeg_deinterlace_and_upscale_single_frame(database, frame):
        filter_str, width, height = get_ffmpeg_filter(frame, 'upscale')
        return ffmpeg_extract_single_frame(database, frame, filter_str, width, height, task='upscale')
