# -*- coding: utf-8 -*-
import sys
import datetime
import os
import re
import signal
import subprocess
import time

from pprint import pprint
from utils.common import FPS
from utils.pretty_print import *
from utils.process import create_process
from utils.time_conversions import timestamp2sexagesimal

def clean_ffmpeg_filter(a_string):
    for c in ['\"', '\r', '\n', ' ']:
        a_string = a_string.replace(c, '')
    return a_string


def get_ffmpeg_filter(db, frame, step):
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

    ffmpeg_filter_str = ffmpeg_filter_str.replace('nnedi3_weights', db['common']['directories']['nnedi3_weights'])

    return [ffmpeg_filter_str, width, height]



def get_video_resolution(video_filepath, db_common):
    ffprobe_command = ([
        db_common['tools']['ffprobe'],
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=s=x:p=0",
        video_filepath])
    result = subprocess.run(ffprobe_command, stdout=subprocess.PIPE)
    dimensions_str = result.stdout.decode('utf-8').split('x')
    return int(dimensions_str[0]), int(dimensions_str[1])



def get_video_duration(db_common, filename='', integrity=True):
    ffprobe_command = [db_common['tools']['ffprobe'], "-hide_banner"]
    if integrity:
        ffprobe_command.extend(["-count_frames"])
    ffprobe_command.extend(["-i", filename])

    process = create_process(ffprobe_command, db_common['process'])
    stdout, stderr = process.communicate()

    duration = 0
    frame_count = 0
    if stderr is not None:
        line = stderr.decode(encoding='UTF-8')
        line += stdout.decode(encoding='UTF-8')
        if integrity:
            result= re.search(r"(File ended prematurely)", line)
            if result is not None:
                return 0.0

        result = re.search(r"Duration: ([0-9]{2}):([0-9]{2}):([0-9]{2}).([0-9]{2}),", line)
        if result:
            duration = int(result[1]) * 60
            duration = (duration + int(result[2])) * 60
            duration = (duration + int(result[3])) * 100
            duration += int(result[4])
            frame_count = int(duration * FPS / 100)
        else:
            return 0.0
    else:
        return 0.0

    return (float(duration)/100.0, frame_count)



def execute_ffmpeg_command(db, command=None, filename='', print_msg=False, simulation:bool=False):
    if command is None:
        sys.exit(print_red("Error: FFmpeg command is empty"))

    if simulation:
        print_lightgrey(' '.join(command))
        return ''

    if print_msg:
        now = datetime.datetime.now()
        _msg = "(%s) %s" % (now.strftime("%Y-%m-%d %H:%M:%S"), filename)
        print(_msg, end="", flush=True)
        startTime = time.time()

    process = create_process(command, db['common']['process'])
    stdout, stderr = process.communicate()

    result = stderr.decode(encoding='UTF-8')
    result += stdout.decode(encoding='UTF-8')

    if print_msg:
        elapsedTime = time.time() - startTime
        print("\t(%s)" % (timestamp2sexagesimal(elapsedTime)))

    return result



def execute_simple_ffmpeg_command(ffmpeg_command):
    start_time = time.time()

    result = subprocess.run(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout = result.stdout.decode('utf-8')
    stderr = result.stderr.decode('utf-8')
    elapsed_time = time.time() - start_time
    print("\t\t\tsimple FFmpeg command executed in %.02fs" % (elapsed_time))
    if len(stdout) > 0:
        print(stdout)
    if len(stderr) > 0:
        print(stderr)
        return False
    return True
