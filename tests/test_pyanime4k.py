#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# pathlib.Path path objects are recommended instead of strings
import pathlib

# import pyanime4k library
import pyanime4k
import signal

if False:
    # # display single image upscaled with Anime4KCPP
    # pyanime4k.show_upscaled_image(pathlib.Path('image1.png'))

    # # upscale a single image
    # pyanime4k.upscale_images(pathlib.Path('image1.png'))

    # upscale a list of images
    images = [
        pathlib.Path('src/ep01_04730__f__00_140b7b2.png'),
        pathlib.Path('src/ep01_05655__f__00_140b7b2.png')
    ]

    pyanime4k.upscale_images(
        input_paths=images,
        output_path=pathlib.Path('./output')
    )


# upscale a single video file
signal.signal(signal.SIGINT, signal.SIG_DFL)



pyanime4k.upscale_videos(
    input_paths=pathlib.Path('ep01_023.mp4'),
    output_path=pathlib.Path('./output'),
    GPU_mode=True
    )
pyanime4k.upscale_videos(pathlib.Path('ep01_episode_e974d59_deinterlace.mp4'), output_path=pathlib.Path('./output'))


# # upscale multiple files
# videos = [
#     pathlib.Path('video1.mp4'),
#     pathlib.Path('video2.mp4')
# ]

# pyanime4k.upscale_videos(
#     input_paths=videos,
#     output_path=pathlib.Path('./output')
# )