#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
import os.path
import signal
from pprint import pprint
import argparse
import subprocess
import time
import cv2
import numpy as np

sys.path.append('scripts')
from utils.pretty_print import print_cyan
from utils.process import (
    create_process,
    get_process_cfg,
)
from filters.ffmpeg_utils import (
    clean_ffmpeg_filter,
    execute_simple_ffmpeg_command
)

FPS = 25

shakiness = 10
accuracy = 15
smoothing = 0
stepsize = 3
mincontrast = 0.1
tripod = 0


def ffmpeg_stabilize(input_filepath):
    start_time = time.time()

    folder = os.path.dirname(input_filepath)
    cache_directory = 'cache'

    filters_str="vidstabdetect=shakiness=%d:accuracy=%d:result=%s/transforms.trf" % (
        shakiness, accuracy, folder)
    filters_str = clean_ffmpeg_filter(filters_str)


    # Create command
    ffmpeg_verbose="-hide_banner -loglevel warning"
    ffmpeg_verbose = ''
    if sys.platform == 'win32':
        command_ffmpeg_common = [os.path.abspath("../mco_3rd_party/ffmpeg-5.1/bin/ffmpeg.exe")]
    else:
        command_ffmpeg_common = [os.path.abspath("../mco_3rd_party/ffmpeg-5.1/ffmpeg")]


    transforms_filepath = os.path.join(cache_directory, "ffmpeg_transforms.trf")
    if os.path.exists(transforms_filepath):
        os.remove(transforms_filepath)
    transforms_filepath = transforms_filepath.replace('\\', '/')

    dummy_file = os.path.join("cache", "ffmpeg_dummy.mkv")

    # ffmpeg_command.extend([
    #     "-i", f"{input_filepath}",
    #     "-vf", f"vidstabdetect=shakiness={shakiness}:accuracy={accuracy}:result=ffmpeg_transforms.trf",
    #     # "-f", "avi", "pipe:1"
    #     # "-vcodec", "rawvideo", "-"
    #     # "-f", "null", "-"
    #     "-f", "nut", "-"
    # ])
    ffmpeg_command = command_ffmpeg_common + [
        "-i", f"{input_filepath}",
        "-vf", f"vidstabdetect=shakiness={shakiness}:accuracy={accuracy}:result={transforms_filepath}:stepsize={stepsize}:mincontrast={mincontrast}:tripod={tripod}:show=2",
        "-y", f"{dummy_file}"
    ]

    # ffmpeg_command.extend(["-y", os.path.join(folder, f"patati.mkv")])
    print(' '.join(ffmpeg_command))

    result = subprocess.run(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout = result.stdout.decode('utf-8')
    stderr = result.stderr.decode('utf-8')
    if len(stdout) > 0:
        print(stdout)
    if len(stderr) > 0:
        print(stderr)

    print("detection done\n\n\n")

    ffmpeg_command = command_ffmpeg_common + [
        "-i", f"{input_filepath}",
        # "-vf", f"vidstabtransform=input={transforms_filepath}:smoothing={smoothing}:interpol=bicubic:crop=keep:optzoom=0:zoomspeed=0",
        "-vf", f"vidstabtransform=input={transforms_filepath}:optalgo=avg:maxangle=0:relative=1:smoothing={smoothing}:interpol=bicubic:tripod={1 if tripod!=0 else 0}:crop=keep:optzoom=0:zoomspeed=0",
    ]
    ffmpeg_command.extend(["-y", os.path.join(folder, f"patati.mkv")])

    print(' '.join(ffmpeg_command))
    # process_cfg = get_process_cfg()
    # execute_simple_ffmpeg_command(ffmpeg_command)

    result = subprocess.run(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout = result.stdout.decode('utf-8')
    stderr = result.stderr.decode('utf-8')
    if len(stdout) > 0:
        print(stdout)
    if len(stderr) > 0:
        print(stderr)


    print_cyan("generated in %.02f" % (time.time() - start_time))







def main():
    parser = argparse.ArgumentParser(description="stabilize")
    parser.add_argument("--input", "-i", type=str, required=True)
    arguments = parser.parse_args()

    input_path = os.path.normpath(arguments.input)
    # output_path = os.path.basename(arguments.output)
    # suffix = arguments.suffix

    ffmpeg_stabilize(input_path)



if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()


