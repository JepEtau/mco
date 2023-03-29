# -*- coding: utf-8 -*-
import os
import sys

from pprint import pprint
import subprocess

from filters.ffmpeg_utils import clean_ffmpeg_filter, ffmpeg_execute_command

from utils.pretty_print import *
from utils.hash import (
    log_filter
)
from utils.common import (
    FPS,
)


class FFmpeg_stabilizer:
    def __init__(self) -> None:
        self.__shakiness = 10
        self.__accuracy = 15


    def stabilize(self, image_list, output, input_hash, do_log=False):
        if not os.path.exists(output):
            os.makedirs(output)

        filters_str="vidstabdetect=shakiness=%d:accuracy=%d:result=%s/transforms.trf" % (
            self.__shakiness, self.__accuracy, os.path.basename(output))
        filters_str = clean_ffmpeg_filter(filters_str)

        hash = log_filter("%s,stab_%s" % (input_hash, filters_str), shot['hash_log_file'])
        print("(FFmpeg) stabilize, hash=%s" % (hash))

        # Generate a list of output images
        count = len(image_list)
        output_image_list = [os.path.join(output, "f_%05d_%s.png" % (no, hash)) for no in range(count)]

        # Discard if output files already exist
        do_process = False
        for f in output_image_list:
            if not os.path.exists(f):
                do_process = True
                break

        # Create the concatenation file
        duration_str = "duration %.02f\n" % (1/float(FPS))
        concatenation_filepath = os.path.join(output, "concatenation_%s.txt" % (hash))
        concatenation_file = open(concatenation_filepath, "w")
        for f in image_list:
            concatenation_file.write("file \'%s\' \n" % (os.path.abspath(f)))
            concatenation_file.write(duration_str)
        concatenation_file.close()


        ffmpeg_verbose="-hide_banner -loglevel warning"
        if sys.platform == 'win32':
            command_ffmpeg_common = [os.path.abspath("../3rd_party/ffmpeg-5.1/bin/ffmpeg.exe")]
        else:
            command_ffmpeg_common = [os.path.abspath("../3rd_party/ffmpeg-5.1/ffmpeg")]
        command_ffmpeg_common.extend(ffmpeg_verbose.split(' '))

        # 1st step: create a video because vidstabdetect cannot work with images as input
        f_tmp = "a_tmp.mkv"
        if not os.path.exists(f_tmp):
            command_ffmpeg = command_ffmpeg_common + [
                "-r", str(FPS),
                "-f", "concat",
                "-safe", "0",
                "-i", concatenation_filepath,
                "-vcodec", "ffv1",
                "-level", "1",
                "-coder", "1 ",
                "-context", "1",
                "-g", "1",
                "-y", f_tmp
            ]
            print(command_ffmpeg)
            std = ffmpeg_execute_command(command=command_ffmpeg, print_msg=True)
            if len(std) > 0:
                print(std)


        # 2nd step: get the ffmpeg transforms file
        transforms_filepath = "ffmpeg_transforms.trf"
        shakiness = 1
        if os.path.exists(transforms_filepath):
            os.remove(transforms_filepath)
        command_ffmpeg = command_ffmpeg_common + [
            "-i", f_tmp,
            "-vf", "vidstabdetect=shakiness=%d:accuracy=15:result=ffmpeg_transforms.trf" % (shakiness),
            # "-f", "avi", "pipe:1"
            # "-vcodec", "rawvideo", "-"
            # "-f", "null", "-"
            "-f", "nut", "-"
        ]
        command_ffmpeg = command_ffmpeg_common + ["-i", f_tmp,
            "-vf", "vidstabdetect=shakiness=%d:accuracy=15:result=ffmpeg_transforms.trf:show=1" % (shakiness),
            "-y", "a_dummy.mkv"
        ]
        print(command_ffmpeg)
        result = subprocess.run(command_ffmpeg, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout = result.stdout.decode('utf-8')
        stderr = result.stderr.decode('utf-8')
        if len(stdout) > 0:
            print(stdout)
        if len(stderr) > 0:
            print(stderr)
        # std = ffmpeg_execute_command(command=command_ffmpeg, print_msg=True)
        # if len(std) > 0:
        #     print(std)
        # print(command_ffmpeg)
        # process = create_process(command_ffmpeg)
        # process.stdout.read()
        # process.stdout.flush()
        # no = 0
        # while no < count:
        #     print("%d" % (no))
        #     raw_frame = process.stdout.read(3 * 720 * 576)
        #     if raw_frame is None or len(raw_frame) == 0:
        #         break
        #     process.stdout.flush()
        #     no += 1
        # std = ffmpeg_execute_command(command=command_ffmpeg, print_msg=True)
        # if len(std) > 0:
        #     print(std)


        # 3rd apply the transformation on the input video
        command_ffmpeg = command_ffmpeg_common + [
            "-i", "a_tmp.mkv",
            "-vf", "vidstabtransform=input=ffmpeg_transforms.trf:interpol=bicubic:crop=keep:optzoom=0:zoomspeed=0",
            "-y", "a_result.mkv"
        ]

        # command_ffmpeg = command_ffmpeg_common + [
        #     "-r", str(FPS),
        #     "-f", "concat",
        #     "-safe", "0",
        #     "-i", concatenation_filepath,
        #     "-vf", "vidstabtransform=input=ffmpeg_transforms.trf",
        #     "-y", "a_result.mkv"
        # ]

        print(command_ffmpeg)
        result = subprocess.run(command_ffmpeg, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout = result.stdout.decode('utf-8')
        stderr = result.stderr.decode('utf-8')
        if len(stdout) > 0:
            print(stdout)
        if len(stderr) > 0:
            print(stderr)


        # std = ffmpeg_execute_command(command=command_ffmpeg, print_msg=True)
        # if len(std) > 0:
        #     print(std)

        return count, hash

    def get_output_shape(self):
        return  self._height, self._width, self._channels


