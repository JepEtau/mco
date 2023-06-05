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
    execute_simple_ffmpeg_command
)

FPS = 25


def concatenate_images_to_video(image_list, output_path, suffix='', fps=FPS, interlace=False):
    start_time = time.time()

    suffix = f"output_{suffix}" if suffix != '' else "output"

    # Create output folder
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # Create the concatenation file
    duration_str = "duration %.02f\n" % (1/float(FPS))
    input_path = os.path.dirname(image_list[0])
    concatenation_filepath = os.path.join(input_path, f"concatenation_{suffix}.txt")
    concatenation_file = open(concatenation_filepath, "w")
    for f in image_list:
        concatenation_file.write(f"file \'{os.path.abspath(f)}\'\n")
        concatenation_file.write(duration_str)
    concatenation_file.close()

    # Create command
    ffmpeg_verbose="-hide_banner -loglevel warning"
    ffmpeg_verbose = ''
    if sys.platform == 'win32':
        ffmpeg_command = [os.path.abspath("ffmpeg.exe")]
    else:
        ffmpeg_command = [os.path.abspath("../mco_3rd_party/ffmpeg-5.1/ffmpeg")]
    # ffmpeg_command.extend(ffmpeg_verbose.split(' '))
    # suffix_2 = '_%sfps' % (fps) if fps != FPS else ''
    # suffix_2 = '_%sfps' % (fps)
    # interlace_str = "-vf tinterlace=interleave_top,fieldorder=tff"
    # ffmpeg_command.extend([
    #     "-r", f"{fps}",
    #     "-f", "concat",
    #     "-safe", "0",
    #     "-i", concatenation_filepath,

    #     "-vcodec", "ffv1",
    #     "-level", "1",
    #     "-coder", "1 ",
    #     "-context", "1",
    #     "-g", "1",
    #     "-y", os.path.join(output_path, f"{suffix}.mkv")
    # ])

    ffmpeg_command.extend([
        "-r", f"{fps}",
        "-f", "concat",
        "-safe", "0",
        "-i", concatenation_filepath,

        "-filter_complex", f"[0:v]scale=iw*0.5:-1:sws_flags=bicubic[outv]",
        "-map", "[outv]"
    ])

    if sys.platform == 'win32':
        ffmpeg_command.extend([
            "-vcodec", "ffv1",
        ])
    else:
        ffmpeg_command.extend([
            "-tune", "animation",
            "-pix_fmt", "yuv420p",
            "-preset", "medium",
            "-crf",  "15",
        ])

    ffmpeg_command.extend(["-y", os.path.join(output_path, f"{suffix}.mkv")])

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






def concatenate_images_to_video_cv2(image_list, output_path, suffix='', fps=FPS, interlace=False):
    process_cfg = get_process_cfg()

    start_time = time.time()

    #  TODO: rework output filename
    if suffix != '':
        suffix = "_%s" % (suffix)

    # Create output folder
    if not os.path.exists(output_path):
        os.makedirs(output_path)


    # Open images
    images = [cv2.imread(f_input, cv2.IMREAD_COLOR) for f_input in image_list]

    start_time2 = time.time()

    height, width, c = images[0].shape
    frame_count = len(images)

    # Create command
    if sys.platform == 'win32':
        ffmpeg_command = [os.path.abspath("../3rd_party/ffmpeg-5.1/bin/ffmpeg.exe")]
    else:
        ffmpeg_command = [os.path.abspath("../3rd_party/ffmpeg-5.1/ffmpeg")]
    ffmpeg_command.extend([
        "-hide_banner",
        "-loglevel", "error",

        '-f', 'rawvideo',
        '-pixel_format', 'bgr24',
        '-video_size', "%dx%d" % (width, height),
        "-r", str(FPS),
        '-i', 'pipe:0',

        "-tune", "animation",
        "-c:v", "libx264",
        "-preset", "medium"
    ])
    ffmpeg_command.extend([
        "-crf",  "17",
        "-y", os.path.join(output_path, "f_ep01_%s_cv2.mkv" % (suffix))
    ])
    img_size = width * height * 3
    bufsize = int(10 * img_size * 1.10)

    if False:
        bytes_arr = bytearray()
        for img in images:
            bytes_arr.extend(img.tobytes())
        process = create_process(ffmpeg_command, process_cfg, bufsize=bufsize)
        stdout, stderr = process.communicate(input=bytes(bytes_arr))
    elif False:
        bytes_arr = bytearray()
        for img in images:
            bytes_arr += img.tobytes()
        process = create_process(ffmpeg_command, process_cfg, bufsize=bufsize)
        stdout, stderr = process.communicate(input=bytes(bytes_arr))
    elif True:
        process = create_process(ffmpeg_command, process_cfg, bufsize=bufsize)
        for img in images:
            process.stdin.write(img.tobytes())
        stdout, stderr = process.communicate()

    print("spent_time= %.02f" % (time.time() - start_time2))
    print_cyan("spent_time= %.02f" % (time.time() - start_time))








def main():
    parser = argparse.ArgumentParser(description="concat to mkv file")
    parser.add_argument("--input", "-i", type=str, required=True)
    parser.add_argument("--suffix", "-s", type=str, required=True)
    parser.add_argument("--output", "-o", type=str, default='outputs', required=False)
    parser.add_argument("--fps", type=int, choices=[FPS, 2*FPS], default=FPS, required=False)
    arguments = parser.parse_args()

    input_path = os.path.normpath(arguments.input)
    output_path = os.path.basename(arguments.output)
    suffix = arguments.suffix

    # List images
    image_list = list()
    for f in os.listdir(input_path):
        if f.endswith(".png") and suffix in f:
            image_list.append(os.path.join(input_path, f))
    image_list = sorted(image_list)

    if len(image_list) == 0:
        sys.exit("No images found")

    # Concatenate images into a video (ffv1)
    if True:
        concatenate_images_to_video(image_list=image_list,
            output_path=output_path,
            suffix=suffix,
            fps=arguments.fps)
    else:
        concatenate_images_to_video_cv2(image_list=image_list,
            output_path=output_path,
            suffix=suffix)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()


