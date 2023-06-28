# -*- coding: utf-8 -*-
import os
import sys
from pprint import pprint
from copy import deepcopy
import platform
import cv2

from utils.types import Shot
from utils.pretty_print import *

from img_toolbox.ffmpeg_utils import get_video_duration



INITIAL_FRAME_WIDTH = 720
INITIAL_FRAME_HEIGHT = 576

FINAL_FRAME_WIDTH = 1440
FINAL_FRAME_HEIGHT = 1080
STEP_INC = 1

# Maximum nb of frames which can be loaded in memory
if platform.system() == "Windows":
    MAX_FRAMES_COUNT = 800
else:
    MAX_FRAMES_COUNT = 250

FILTER_TAGS = [
    'deinterlace',
    'replace',
    'pre_upscale',
    'upscale',
    'sharpen',
    'edition',
    'rgb',
    'geometry',
    'final'
]


def is_lowres_img(img):
    # dirty function to indicate if an image is low res
    return True if img.shape[0] < (INITIAL_FRAME_WIDTH*3/2) else False

def is_lowres_height(height):
    # dirty function to indicate if an image is low res
    return True if height < (INITIAL_FRAME_WIDTH*3/2) else False

def is_highres_height(height):
    # dirty function to indicate if an image is low res
    return True if height > (INITIAL_FRAME_WIDTH*3/2) else False

def get_step_no_from_task(shot:Shot, task):
    __task = 'geometry' if task == 'final' else task
    for f, i in zip(shot['filters'], range(len(shot['filters']))):
        if __task == f['task']:
            return i

    print_red("Error: get_step_no_from_task: [%s] not found" % (task))
    return None


def get_step_no_from_last_task(shot):
    return get_step_no_from_task(shot, shot['last_task'])



def get_processing_chain(db, shot:Shot):
    verbose = False
    k_ed = shot['k_ed']
    k_ep = shot['k_ep']
    k_part = shot['k_part']
    if verbose:
        print_lightgreen(f"get filters from shot: {k_ed}:{k_ep}:{k_part}, no. {shot['no']:03}, start: {shot['start']}")

    if shot['filters_id'] == 'default':
        if verbose:
            print_lightgrey(f"\tdefault filter")
            pprint(db[k_ep]['video'][k_ed][k_part]['filters'])

        # This shot uses default filters. Use the one defined in the part
        if 'filters' not in db[k_ep]['video'][k_ed][k_part].keys():
            sys.exit(print_red(f"Error: {k_ed}:{k_ep}:{k_part}: no available filters"))

        try:
            filters = db[k_ep]['video'][k_ed][k_part]['filters']['default']
        except:
            print_red(f"Error: default filter is not defined but required by {k_ed}:{k_ep}:{k_part}, no. {shot['no']:03}")
            pprint(shot)
            sys.exit()

    elif isinstance(shot['filters_id'], str):
        if verbose:
            print_lightgrey(f"\tcustom filter: {shot['filters']}")

        # This shot uses a custom filter defined in the 'filters' struct in this part
        try:
            filters = db[k_ep]['video'][k_ed][k_part]['filters'][shot['filters_id']]
        except:
            print_red(f"Error: {k_ed}:{k_ep}:{k_part}, no. {shot['no']:03}, filter {shot['filters']} not found")
            print_red(f"\tdefined filters: {list(db[k_ep]['video'][k_ed][k_part]['filters'].keys())}")
            print_orange(f"\tfallback: using default")
            filters = db[k_ep]['video'][k_ed][k_part]['filters']['default']
    else:
        # This shot may default filters, but to be validated
        print_red(f"Error: no filters defined for {k_ed}:{k_ep}:{k_part}, no. {shot['no']:03}")
        sys.exit()

    return deepcopy(filters)



def get_dimensions_from_crop_values(width, height, crop) -> list:
    c_t, c_b, c_l, c_r = crop
    c_w = width - (c_l + c_r)
    c_h = height - (c_t + c_b)
    return [c_t, c_b, c_l, c_r, c_w, c_h]



def has_add_border_task(shot:Shot):
    # Returns true if borders have been added
    for f in shot['filters'][STEP_INC:]:
        if f['str'] == 'add_borders':
            return True
    return False



def is_stabilize_task_enabled(shot:Shot):
    # Returns true if deshake/stabilize task is enabled, False otherwise

    # No deshake parameters or disabled
    if ('deshake' not in shot.keys()
        or shot['deshake'] is None
        or not shot['deshake']['enable']):
        return False

    # Is deshake/stablize task is in list of filters
    for f in shot['filters']:
        if f['task'] in ['deshake', 'stabilize']:
            return True

    return False





def is_progressive_file_valid(shot, db_common, verbose:bool=False):
    verbose = False

    if verbose:
        print_lightgreen("is_progressive_file_valid")
    progressive_filepath = shot['inputs']['progressive']['filepath']
    if not os.path.exists(progressive_filepath):
        if verbose:
            print(f"progressive filepath: {progressive_filepath}")
        return False

    progressive_duration, progressive_frame_count = get_video_duration(db_common,
        progressive_filepath,
        integrity=False)
    interlaced_duration, interlaced_frame_count = get_video_duration(
        db_common,
        shot['inputs']['interlaced']['filepath'],
        integrity=False)

    start = shot['inputs']['progressive']['start']
    count = shot['inputs']['progressive']['count']

    if verbose:
        print("\tfile: %s" % (progressive_filepath))
        print_lightgrey("\tinterlaced: %.02fs" % (interlaced_duration))
        print_lightgrey("\tprogressive: %.02fs" % (progressive_duration))
        print_lightgrey("\tstart: %d, count: %d" % (start, count))

    if start == 0 and count == -1:
        # Full video
        if interlaced_duration != progressive_duration:
            if verbose:
                print("\tnot valid: interlaced != progressive")
            return False

    elif count == -1:
        # Partial video from start to end of video file
        interlace_count = interlaced_frame_count - start
        progressive_count = progressive_frame_count

        if progressive_count < interlace_count:
            if verbose:
                print(f"\tnot valid: {progressive_count}, should be {interlace_count}")
            sys.exit()
            return False
    else:
        # Partial video
        progressive_count = progressive_frame_count
        if progressive_count < count:
            if verbose:
                print(f"\tnot valid: {progressive_count}, should be {interlace_count}")
                sys.exit(print_yellow(f"verify this!"))
            sys.exit()
            return False

    if verbose:
        print("\tvalid")
    return True


def show_image(img, img_name:str='', ratio:float=1.0):
    window_name = 'image' if img_name == '' else img_name
    cv2.namedWindow(window_name)
    if ratio != 1:
        _img = cv2.resize(img.copy(), (0, 0), fx=ratio,fy=ratio) if img.shape[0] > 800 else img.copy()
    else:
        _img = img.copy()
    cv2.moveWindow(window_name, 100, 100)
    cv2.imshow(window_name, _img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
