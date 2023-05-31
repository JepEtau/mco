# -*- coding: utf-8 -*-
import sys
import cv2
import gc
import os
import numpy as np
import platform
from pprint import pprint
import signal

from filters.ffmpeg_utils import clean_ffmpeg_filter
from filters.utils import MAX_FRAMES_COUNT
from utils.common import FPS
from utils.pretty_print import *
from utils.get_image_list import (
    FILENAME_TEMPLATE,
    get_image_list,
)
from utils.hash import (
    calculate_hash,
    log_filter
)
from utils.process import (
    create_process,
)




def ffmpeg_filter(shot, images:list, image_list:list,
    step_no, input_hash, filter_str, do_save:bool, output_folder, db_common,
    get_hash:bool=False, do_force:bool=False):

    """Apply FFmpeg filter to images
    """

    filter_str_hash = "%s,%s" % (input_hash, clean_ffmpeg_filter(filter_str))
    if get_hash:
        hash = calculate_hash(filter_str=filter_str_hash)
        return hash, None
    hash = log_filter(filter_str_hash, shot['hash_log_file'])
    print_cyan("(FFmpeg)\tstep no. %d, filter=[%s], input_hash= %s, output hash= %s" % (step_no, filter_str, input_hash, hash))

    # Output images in memory
    use_memory = True if shot['count'] <= MAX_FRAMES_COUNT else False


    # Generate a list of output images
    output_image_list = get_image_list(shot=shot,
        folder=output_folder,
        step_no=step_no,
        hash=hash)
    if do_save and not os.path.exists(output_folder):
        os.makedirs(output_folder)

    output_images = list()
    frame_count = shot['count']

    # Image size
    if use_memory:
        height, width, channels = images[0].shape
    else:
        height, width, channels = cv2.imread(image_list[0], cv2.IMREAD_COLOR).shape
    img_size = width * height * 3

    # Create the FFmpeg command
    ffmpeg_command = [
        db_common['tools']['ffmpeg'],
        "-hide_banner",
        "-loglevel", "error"]

    # Force to use concatenate file because process bufsize is limited
    if frame_count > (2000000000 / img_size):
        use_memory = False

    do_use_ffv1 = False
    if not platform.system() == "Windows":
        # Linux, creation of FFv1 fails: process does not return.
        use_memory = False
        do_use_ffv1 = False

    if use_memory:
        print("\t\t\tUse memory")
        # All images are in memory
        ffmpeg_command.extend([
            '-f', 'rawvideo',
            '-pixel_format', 'bgr24',
            '-video_size', "%dx%d" % (width, height),
            "-r", str(FPS),
            '-i', 'pipe:0',

            "-filter_complex", "[0:v]%s[outv]" % (filter_str),
            "-map", "[outv]",

            "-f", "image2pipe",
            "-pix_fmt", "bgr24",
            "-vcodec", "rawvideo",
            "-"
        ])
        bufsize = int(frame_count * img_size * 1.10)

        bytes_arr = bytearray()
        for img in images:
            bytes_arr.extend(img.tobytes())
        # print_yellow("bufsize=\t%d" % (bufsize))
        # print_yellow("stdin size=\t%d" % (len(bytes_arr)))
        # print_yellow(ffmpeg_command)

        process = create_process(ffmpeg_command, db_common['process'], bufsize=bufsize)
        stdout, stderr = process.communicate(input=bytes(bytes_arr))
        for i, index in zip(range(frame_count), range(0, frame_count*img_size, img_size)):
            img = np.frombuffer(stdout[index:index + img_size], np.uint8).reshape([height, width, channels])
            output_images.append(img)
            if do_save:
                cv2.imwrite(img=img, filename=output_image_list[i])

    else:

        # Images already saved?
        if os.path.exists(image_list[-1]):
            are_already_been_saved = True
            print_lightgrey("\t\t\tImages have already been saved")
        else:
            are_already_been_saved = False
            print_lightgrey("\t\t\tImages have not been saved")


        if not do_use_ffv1:
            print_lightgrey("\t\t\tUse FFmpeg concatenate filter")

            input_folder = os.path.dirname(image_list[0])
            if not are_already_been_saved:
                if not os.path.exists(input_folder):
                    os.makedirs(input_folder)
                for img, filepath in zip(images, image_list):
                    cv2.imwrite(img=img, filename=filepath)

            # Images are not needed anymore
            images.clear()
            gc.collect()

            # Create a concatenation file
            duration_str = "duration %.02f\n" % (1/float(FPS))
            concatenation_filepath = os.path.join(input_folder, "concatenation_tmp.txt")
            concatenation_file = open(concatenation_filepath, "w")
            for f in image_list:
                concatenation_file.write("file \'%s\' \n" % (os.path.abspath(f)))
                concatenation_file.write(duration_str)
            concatenation_file.close()

            # Concatenate, Filtering
            ffmpeg_command.extend([
                "-r", str(FPS),
                "-f", "concat",
                "-safe", "0",
                "-i", concatenation_filepath,

                "-filter_complex", "[0:v]%s[outv]" % (filter_str),
                "-map", "[outv]",

                "-f", "image2pipe",
                "-pix_fmt", "bgr24",
                "-vcodec", "rawvideo",
                "-"
            ])
            process = create_process(ffmpeg_command, db_common['process'])

            # Save images
            for frame_no, img_filepath in zip(range(frame_count), output_image_list):
                print("\t\t\tFFmpeg filter: %d%%" % (int((100.0 * frame_no)/frame_count)), end='\r')
                raw_frame = process.stdout.read(img_size)
                img = np.frombuffer(raw_frame, dtype=np.uint8).reshape((height, width, channels))
                if do_save:
                    cv2.imwrite(filename=img_filepath, img=img)
                output_images.append(img)
            stdout, stderr = process.communicate()
            print("                                       ", end='\r')

        else:
            print_lightgrey("\t\t\tGenerate and use a FFV1 file")

            # Remove temporary file
            try: os.remove(ffv1_filepath)
            except:pass

            if not os.path.exists(output_folder):
                os.makedirs(output_folder)

            # Create a FFV1 file
            ffv1_filepath = os.path.join(output_folder, 'tmp.mkv')
            height, width, c = images[0].shape
            ffmpeg_command = [db_common['tools']['ffmpeg']]
            ffmpeg_command.extend(["-loglevel", "debug"])
            frame_count = len(images)
            ffmpeg_command.extend([
                '-f', 'rawvideo',
                '-pixel_format', 'bgr24',
                '-video_size', "%dx%d" % (width, height),
                "-r", str(FPS),
                '-i', 'pipe:0',

                "-vcodec", "ffv1",
                "-y", ffv1_filepath
            ])
            process = create_process(ffmpeg_command, db_common['process'])
            for img in images:
                process.stdin.write(img.tobytes())
            print_lightgrey("\t\t\tWaiting for end", flush=True)
            stdout, stderr = process.communicate()


            # Images are not needed anymore
            images.clear()
            gc.collect()

            # Filtering
            print_lightgrey("\t\t\tStart filtering", flush=True)
            ffmpeg_command.extend([
                "-i", ffv1_filepath,

                "-filter_complex", "[0:v]%s[outv]" % (filter_str),
                "-map", "[outv]",

                "-f", "image2pipe",
                "-pix_fmt", "bgr24",
                "-vcodec", "rawvideo",
                "-"
            ])
            process = create_process(ffmpeg_command, db_common['process'])

            # Save images
            for frame_no, img_filepath in zip(range(frame_count), output_image_list):
                print("\t\t\tFFmpeg filter: %d%%" % (int((100.0 * frame_no)/frame_count)), end='\r')
                raw_frame = process.stdout.read(img_size)
                img = np.frombuffer(raw_frame, dtype=np.uint8).reshape((height, width, channels))
                if do_save:
                    cv2.imwrite(filename=img_filepath, img=img)
                output_images.append(img)
            stdout, stderr = process.communicate()
            print("                                       ", end='\r')

            # Remove temporary file
            try: os.remove(ffv1_filepath)
            except:pass

    return hash, output_images





# FFV1/cv2.imwrite tests
    # if filter_str == 'ffv1':

    #     ffv1_filepath = "N:\\cache\\ep01\\episode\\023\\test.mkv"


    #     # pprint(image_list)
    #     print("reading frames")
    #     start_time = time.time()
    #     images = [cv2.imread(f_input, cv2.IMREAD_COLOR) for f_input in image_list]
    #     print("reading PNG files: %.03f" % (time.time() - start_time))
    #     # 0.774s


    #     if False:
    #         # Process
    #         print("start processing")
    #         start_time = time.time()
    #         height, width, c = images[0].shape
    #         frame_count = len(images)
    #         ffmpeg_command = [db_common['tools']['ffmpeg']]
    #         ffmpeg_command.extend(["-loglevel", "debug"])
    #         ffmpeg_command.extend([
    #             '-f', 'rawvideo',
    #             '-pixel_format', 'bgr24',
    #             '-video_size', "%dx%d" % (width, height),
    #             "-r", str(FPS),
    #             '-i', 'pipe:0',

    #             "-filter_complex", "[0:v]hqdn3d=2[outv]",
    #             "-map", "[outv]",

    #             "-f", "image2pipe",
    #             "-pix_fmt", "bgr24",
    #             "-vcodec", "rawvideo",
    #             "-"
    #         ])
    #         process_cfg = db_common['process']
    #         bufsize = int(len(image_list) * height * width * 3 * 1.10)
    #         output_images = create_process_tests(ffmpeg_command, images, bufsize=bufsize)
    #         print("processing: %.03f" % (time.time() - start_time))
    #         # 2.621s
    #         # win11: 1.206s

    #         print("ENDED***********************")
    #         # process.stdin.close()
    #         # print("closed")
    #         # out_data = process.stdout.read()
    #         # # _stdout, _stderr = process.communicate()
    #         # # _stdout, _stderr = process.communicate()
    #         # # print(">> STDOUT:", flush=True)
    #         # # print(_stdout.decode(encoding='UTF-8'), flush=True)
    #         # # print(">> STDERR:", flush=True)
    #         # # print(_stderr.decode(encoding='UTF-8'), flush=True)
    #         # print(len(out_data), flush=True)

    #         # for no in range(frame_count):
    #         #     print("read frame no. %d" % (no))
    #         #     raw_frame = np.frombuffer(process.stdout.read(3 * height * width), dtype=np.uint8)
    #         #     output_images.append(raw_frame.reshape((height, width, 3)))
    #         #     # process.stdout.flush()

    #         # print("process time: %.03f" % (time.time() - start_time))

    #         # Write png files
    #         output_image_list = get_image_list(shot=shot,
    #             folder=output,
    #             step_no=step_no,
    #             hash="toto")
    #         start_time = time.time()
    #         for img, f_output in zip(output_images, output_image_list):
    #             cv2.imwrite(filename=f_output, img=img)
    #         print("write png files: %.03f" % (time.time() - start_time))
    #         # 1.673s

    #         sys.exit()
    #     else:
    #         # FFV1 with processing
    #         start_time = time.time()
    #         height, width, c = images[0].shape
    #         ffmpeg_command = [db_common['tools']['ffmpeg']]
    #         ffmpeg_command.extend(["-loglevel", "debug"])
    #         frame_count = len(images)
    #         ffmpeg_command.extend([
    #             '-f', 'rawvideo',
    #             '-pixel_format', 'bgr24',
    #             '-video_size', "%dx%d" % (width, height),
    #             "-r", str(FPS),
    #             '-i', 'pipe:0',
    #             # "-pix_fmt", "yuv444p",
    #             "-filter_complex", "[0:v]hqdn3d=2[outv]",
    #             "-map", "[outv]",
    #             "-vcodec", "ffv1",
    #             "-y", ffv1_filepath
    #         ])
    #         process_cfg = db_common['process']
    #         bufsize = int(frame_count * height * width * 3 * 1.10)
    #         process = create_process(ffmpeg_command, db_common['process'], bufsize=bufsize)
    #         for img in images:
    #             process.stdin.write(img.tobytes())
    #         # print("write flv file: %.03f" % (time.time() - start_time))
    #         _stdout, _stderr = process.communicate(input='')

    #         # Reading flv file
    #         # start_time = time.time()
    #         ffmpeg_command = [db_common['tools']['ffmpeg']]
    #         ffmpeg_command.extend([
    #             "-i", ffv1_filepath,
    #             "-f", "image2pipe",
    #             "-pix_fmt", "bgr24",
    #             "-vcodec", "rawvideo",
    #             "-"
    #         ])
    #         process_cfg = db_common['process']
    #         bufsize = int(len(image_list) * height * width * 3 * 1.10)
    #         process = create_process(ffmpeg_command, db_common['process'], bufsize=bufsize)
    #         output_images = list()
    #         for no in range(frame_count):
    #             raw_frame = np.frombuffer(process.stdout.read(3 * height * width), dtype=np.uint8)
    #             output_images.append(raw_frame.reshape((height, width, 3)))
    #             # process.stdout.flush()
    #         print("processing through ffv1: %.03f" % (time.time() - start_time))
    #         # win 11: 1.977s

    #         # Write png files
    #         output_image_list = get_image_list(shot=shot,
    #             folder=output,
    #             step_no=step_no,
    #             hash="tutu")
    #         start_time = time.time()
    #         for img, f_output in zip(output_images, output_image_list):
    #             cv2.imwrite(filename=f_output, img=img)
    #         print("write png files: %.03f" % (time.time() - start_time))
    #         # 1.673s


    #         sys.exit()

    #     # FFV1
    #     start_time = time.time()
    #     height, width, c = images[0].shape
    #     ffmpeg_command = [db_common['tools']['ffmpeg']]
    #     ffmpeg_command.extend(["-loglevel", "debug"])
    #     frame_count = len(images)
    #     ffmpeg_command.extend([
    #         '-f', 'rawvideo',
    #         '-pixel_format', 'bgr24',
    #         '-video_size', "%dx%d" % (width, height),
    #         "-r", str(FPS),
    #         '-i', 'pipe:0',
    #         # "-pix_fmt", "yuv444p",
    #         "-filter_complex", "[0:v]hqdn3d=2[outv]",
    #         "-map", "[outv]",
    #         "-vcodec", "ffv1",
    #         "-y", ffv1_filepath
    #     ])
    #     process_cfg = db_common['process']
    #     bufsize = int(frame_count * height * width * 3 * 1.10)
    #     process = create_process(ffmpeg_command, db_common['process'], bufsize=bufsize)
    #     for img in images:
    #         process.stdin.write(img.tobytes())
    #     print("write flv file: %.03f" % (time.time() - start_time))
    #     # 61ms
    #     # _stdout, _stderr = process.communicate()
    #     # print(">> STDOUT:", flush=True)
    #     # print(_stdout.decode(encoding='UTF-8'), flush=True)
    #     # print(">> STDERR:", flush=True)
    #     # print(_stderr.decode(encoding='UTF-8'), flush=True)

    #     # Reading flv file
    #     start_time = time.time()
    #     ffmpeg_command = [db_common['tools']['ffmpeg']]
    #     ffmpeg_command.extend([
    #         "-i", ffv1_filepath,
    #         "-f", "image2pipe",
    #         "-pix_fmt", "bgr24",
    #         "-vcodec", "rawvideo",
    #         "-"
    #     ])
    #     process_cfg = db_common['process']
    #     bufsize = int(len(image_list) * height * width * 3 * 1.10)
    #     process = create_process(ffmpeg_command, db_common['process'], bufsize=bufsize)
    #     output_images = list()
    #     for no in range(frame_count):
    #         raw_frame = np.frombuffer(process.stdout.read(3 * height * width), dtype=np.uint8)
    #         output_images.append(raw_frame.reshape((height, width, 3)))
    #         # process.stdout.flush()
    #     print("read ffv1 file: %.03f" % (time.time() - start_time))


    #     return hash, None

