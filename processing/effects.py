import sys
import os
import os.path
import numpy as np
import cv2
from parsers import (
    db,
    IMG_FILENAME_TEMPLATE,
    get_fps,
    task_to_dirname,
)
from pprint import pprint
from utils.mco_utils import get_cache_path, get_out_directory
from utils.p_print import *
from utils.logger import main_logger
from utils.mco_types import Scene
from video.frame_list import get_out_dirname




def effect_loop_and_fadein(scene: Scene):
    # Validate with:
    #   - ep02: episode

    sys.exit("effect_loop_and_fadein")

    # Start and count of frames for the loop
    fadein_count = scene['effects'][2]
    print(green(f"\tloop and fadein: loop: start={fadein_count}, fadein: count={fadein_count}"))


    # Get hash to set the suffix
    hash = scene['last_step']['hash']
    step_no = scene['last_step']['step_no']
    if hash == '':
        # Last filter is null, use previous hash
        previous_filter = scene['filters'][step_no - STEP_INC]
        hash = previous_filter['hash']
        input_filepath = get_input_path_from_shot(
            scene=scene, task=previous_filter['task'])
    else:
        input_filepath = get_input_path_from_shot(
            scene=scene)
    suffix = "_%s" % (hash)

    # Input directory
    print(lightgrey("\tinput_filepath: %s" % (input_filepath)))

    # Output directory
    k_ep_dst = scene['dst']['k_ep']
    k_ch_dst = scene['dst']['k_part']
    if k_ch_dst in ['g_debut', 'g_fin']:
        output_filepath = os.path.join(db[k_ch_dst]['cache_path'])
    else:
        output_filepath = os.path.join(db[k_ep_dst]['cache_path'], k_ch_dst)
    output_filepath = os.path.join(output_filepath,
        f"{scene['no']:03}", f"{step_no:02}")
    if not os.path.exists(output_filepath):
        os.makedirs(output_filepath)
    print(lightgrey(f"\toutput_filepath: {output_filepath}"))


    # Input image list
    if scene['last_task'] == 'edition':
        image_list = get_image_list_pre_replace(scene=scene,
            folder=input_filepath,
            step_no=step_no,
            hash=hash)
    elif scene['last_step']['step_no'] == scene['last_step']['step_edition']:
        image_list = get_new_image_list(scene=scene,
            step_no=step_no,
            hash=scene['filters'][step_no - STEP_INC]['hash'])
    else:
        image_list = get_image_list(scene=scene,
            folder=input_filepath,
            step_no=step_no,
            hash=hash)
    img_input = image_list[0]

    # Output image list
    filename_template = FILENAME_TEMPLATE % (
        scene['k_ep'], scene['k_ed'], step_no, suffix)
    if scene['last_task'] == 'deinterlace':
        start = scene['start'] + scene['count']
        end = start + fadein_count
    else:
        start = scene['count']
        end = start + fadein_count
    output_image_list = list([os.path.join(output_filepath, filename_template % (f_no))
        for f_no in range(end-1, start-1, -1)])

    print(lightgrey("\toutput image count: %d" % (len(output_image_list))))
    # pprint(output_image_list)

    (height, width, channel_count) = scene['last_step']['shape']

    # Create a  black image for fadeout
    img_black = np.zeros([height, width, channel_count], dtype=np.uint8)

    cache_strlen = len(db['common']['directories']['cache']) + 1
    img_src = cv2.imread(img_input, cv2.IMREAD_COLOR)
    print(lightgrey("\tinput image filepath: %s" % (img_input)))
    for count, img_output in zip(range(fadein_count), output_image_list):
        coef = 1 - np.power(0.5, (float(count) / fadein_count))
        # keep print for debug until end of validation
        print(f"\t{count:02d}: {img_input[cache_strlen:]} -> {img_output[cache_strlen:]}, coef={coef:.02f}")

        # Mix images
        img_dst = cv2.addWeighted(img_src, 1 - coef, img_black, coef, 0)
        img_src = img_dst

        cv2.imwrite(img_output, img_dst)



def effect_loop_and_fadeout(scene: Scene):
    # Validate with:
    #   - ep01: episode
    #   - ep01: asuivre
    #   - g_debut
    verbose: bool = False

    # Start and count of frames for the loop
    loop_start = scene['effects'][1]
    loop_count = scene['effects'][2]
    fadeout_count = scene['effects'][3]
    if verbose:
        print(green(f"\tloop and fadeout: loop: start={loop_start}, count={loop_count} / fadeout: count={fadeout_count}"))

    hash: str = scene['task'].hashcode
    dirname: str = task_to_dirname[scene['task'].name]
    task_no: int = int(dirname[:2])
    suffix: str = f"_{hash}"
    k_ed = scene['k_ed']
    k_ep_src = scene['k_ep']

    # Input directory
    in_dir: str = os.path.join(
        get_cache_path(scene), get_out_dirname(scene)
    )
    if verbose:
        print(lightgrey(f"\tinput_filepath: {in_dir}"))

    # Output directory
    k_ep_dst: str = scene['dst']['k_ep']
    k_ch_dst: str = scene['dst']['k_ch']
    if k_ch_dst in ('g_debut', 'g_fin'):
        out_dir: str = os.path.join(db[k_ch_dst]['cache_path'])
    else:
        out_dir: str = os.path.join(db[k_ep_dst]['cache_path'], k_ch_dst)
    out_dir = os.path.join(out_dir, f"{scene['no']:03}", dirname)
    if verbose:
        print(lightgrey("\toutput_directory: %s" % (out_dir)))
    os.makedirs(out_dir, exist_ok=True)


    # Input image list before the loop
    # if scene['last_task'] == 'edition':
    #     image_list = get_image_list_pre_replace(scene=scene,
    #         folder=input_filepath,
    #         step_no=step_no,
    #         hash=hash)
    # elif scene['last_step']['step_no'] == scene['last_step']['step_edition']:
    #     image_list = get_new_image_list(scene=scene,
    #         step_no=step_no,
    #         hash=scene['filters'][step_no - STEP_INC]['hash'])
    # else:
    #     image_list = get_image_list(scene=scene,
    #         folder=input_filepath,
    #         step_no=step_no,
    #         hash=hash)

    # Duplicate the last one
    filename_template = IMG_FILENAME_TEMPLATE % (k_ep_src, k_ed, task_no, suffix)
    loop_img: str = os.path.join(in_dir, filename_template % (loop_start))
    if verbose:
        print(lightgrey(f"\tfile used for the loop effect: {loop_img}"))


    in_imgs: list[str] = [
        os.path.join(in_dir, filename_template % (
            scene['start'] + scene['count'] - (fadeout_count - loop_count) + i
        ))
        for i in range(fadeout_count - loop_count)
    ]
    in_imgs.extend([loop_img] * loop_count)
    if verbose:
        pprint(in_imgs)
        print(lightgrey(f"\toutput image count: {len(in_imgs)}"))

    out_imgs: list[str] = [
        os.path.join(out_dir, filename_template % (
            scene['start'] + scene['count'] + i
        ))
        for i in range(fadeout_count - loop_count)
    ]
    out_imgs.extend([
        os.path.join(
            out_dir, filename_template % (
                scene['start'] + scene['count'] + fadeout_count - loop_count + i
            )
        )
        for i in range(loop_count)
    ])
    if verbose:
        pprint(out_imgs)
        print(lightgrey(f"\toutput image count: {len(out_imgs)}"))

    # sys.exit()

    img_src: np.ndarray = cv2.imread(in_imgs[0], cv2.IMREAD_COLOR)
    img_black = np.zeros(img_src.shape, dtype=img_src.dtype)

    cache_strlen = len(db['common']['directories']['cache']) + 1
    for count, img_input, img_output in zip(
        range(fadeout_count),
        in_imgs,
        out_imgs
    ):
        # Calculate coefficient: last frame is not completely black because there is always
        # a silence after this (i.e. black frames)
        coef = float(count) / fadeout_count
        # keep print for debug until end of validation
        if verbose:
            print(f"\t{count:02d}: {img_input[cache_strlen:]} -> {img_output[cache_strlen:]}, coef={coef:.02f}")

        # Mix images
        img_src = cv2.imread(img_input, cv2.IMREAD_COLOR)
        img_dst = cv2.addWeighted(img_src, 1 - coef, img_black, coef, 0)

        cv2.imwrite(img_output, img_dst)




def effect_fadeout(scene: Scene):
    # verified:
    #   - ep01: documentaire
    # warning: ep02, 'en' version
    verbose: bool = True

    fadeout_start = scene['effects'][1]
    fadeout_count = scene['effects'][2]
    if verbose:
        pprint(scene)
        print(green(f"\tfadeout: start={fadeout_start}, count={fadeout_count}"))

    hash: str = scene['task'].hashcode
    dirname: str = task_to_dirname[scene['task'].name]
    task_no: int = int(dirname[:2])
    suffix: str = f"_{hash}"
    k_ed = scene['k_ed']
    k_ep_src = scene['k_ep']

    # Input directory
    in_dir: str = os.path.join(
        get_cache_path(scene), get_out_dirname(scene)
    )
    if verbose:
        print(lightgrey(f"\tinput_filepath: {in_dir}"))

    # Output directory
    k_ep_dst: str = scene['dst']['k_ep']
    k_ch_dst: str = scene['dst']['k_ch']
    if k_ch_dst in ('g_debut', 'g_fin'):
        out_dir: str = os.path.join(db[k_ch_dst]['cache_path'])
    else:
        out_dir: str = os.path.join(db[k_ep_dst]['cache_path'], k_ch_dst)
    out_dir = os.path.join(out_dir, f"{scene['no']:03}", dirname)
    if verbose:
        print(lightgrey("\toutput_directory: %s" % (out_dir)))
    os.makedirs(out_dir, exist_ok=True)

    filename_template = IMG_FILENAME_TEMPLATE % (k_ep_src, k_ed, task_no, suffix)
    in_imgs: list[str] = [
        os.path.join(in_dir, filename_template % (f_no))
        for f_no in range(fadeout_start, fadeout_start + fadeout_count)
    ]
    out_imgs: list[str] = [
        os.path.join(out_dir, filename_template % (scene['src']['start'] + scene['src']['count'] + i))
        for i in range(fadeout_count)
    ]

    img_src: np.ndarray = cv2.imread(in_imgs[0], cv2.IMREAD_COLOR)
    img_black = np.zeros(img_src.shape, dtype=img_src.dtype)

    cache_strlen = len(db['common']['directories']['cache']) + 1
    for i, img_input, img_output in zip(
        range(fadeout_count),
        in_imgs,
        out_imgs
    ):
        # Calculate coefficient: last frame is not completely black because there is always
        # a silence after this (i.e. black frames)
        coef = float(i) / fadeout_count
        # keep print for debug until end of validation
        if verbose:
            print(f"\t{i:02d}: {img_input[cache_strlen:]} -> {img_output[cache_strlen:]}, coef={coef:.02f}")

        # Mix images
        img_src = cv2.imread(img_input, cv2.IMREAD_COLOR)
        img_dst = cv2.addWeighted(img_src, 1 - coef, img_black, coef, 0)

        cv2.imwrite(img_output, img_dst)
