# -*- coding: utf-8 -*-
import os
from pprint import pprint
import sys
from filters.ffmpeg_utils import get_video_duration
from filters.utils import get_step_no_from_task
from utils.common import FPS
from utils.pretty_print import *
from utils.time_conversions import frames_to_ms

PATH_DATABASE = "./database"


def create_folder_for_video(db, k_ep):
    """ Create the directory that shall contains all video stream
        that will be concatenated

        Returns
            Path of the created folder
    """
    if k_ep in ['ep00', 'ep40']:
        return

    if k_ep in['g_debut', 'g_fin']:
        video_directory = os.path.join(db[k_ep]['cache_path'], 'video')
    else:
        video_directory = os.path.join(db[k_ep]['cache_path'], 'video')

    if not os.path.exists(video_directory):
        os.makedirs(video_directory)
    return video_directory


def create_folder_for_concatenation(db, k_ep, k_part):
    k_ep_or_g = k_part if k_part in ['g_debut', 'g_fin'] else k_ep

    concatenation_directory = os.path.join(db[k_ep_or_g]['cache_path'], "concatenation")
    if not os.path.exists(concatenation_directory):
        os.makedirs(concatenation_directory)



def get_input_path_from_shot(db, shot, task):
    step_no = get_step_no_from_task(shot, task)

    if shot['k_part'] in ['g_debut', 'g_fin']:
        # Put all images in a single folder for 'génériques'
        return os.path.normpath(os.path.join(db['common']['directories']['cache'],
                shot['k_part'],
                '%03d' % (shot['no']),
                '%02d' % (step_no)))

    if task in ['geometry', 'upscale_rgb_geometry', 'final']:
        # If last task is geometry, use the dst structure
        output_path = os.path.normpath(os.path.join(db['common']['directories']['cache'],
            shot['src']['k_ep'],
            shot['src']['k_part'],
            '%03d' % (shot['no']),
            '%02d' % (step_no)))
    else:
        # Otherwise, use the src directory as these images are shared among
        # episodes
        output_path = os.path.normpath(os.path.join(db['common']['directories']['cache'],
            shot['k_ep'],
            shot['k_part'],
            '%03d' % (shot['no']),
            '%02d' % (step_no)))
    return output_path


def get_output_path_from_shot(db, shot, task):
    step_no = get_step_no_from_task(shot, task)

    if shot['k_part'] in ['g_debut', 'g_fin']:
        # Put all images in a single folder for 'génériques'
        return os.path.normpath(os.path.join(db['common']['directories']['cache'],
                shot['k_part'],
                '%03d' % (shot['no']),
                '%02d' % (step_no)))

    if task in ['geometry', 'upscale_rgb_geometry', 'final']:
        # If last task is geometry, use the dst structure
        output_path = os.path.normpath(os.path.join(db['common']['directories']['cache'],
            shot['dst']['k_ep'],
            shot['dst']['k_part'],
            '%03d' % (shot['no']),
            '%02d' % (step_no)))
    else:
        # Otherwise, use the src directory as these images are shared among
        # episodes
        output_path = os.path.normpath(os.path.join(db['common']['directories']['cache'],
            shot['k_ep'],
            shot['k_part'],
            '%03d' % (shot['no']),
            '%02d' % (step_no)))
    return output_path



def get_cache_path(db, shot):
    if shot['k_part'] in ['g_debut', 'g_fin']:
        # Put all images in a single folder for 'génériques'
        return os.path.normpath(os.path.join(
            db['common']['directories']['cache'],
            shot['k_part'],
            '%03d' % (shot['no'])))

    if shot['last_task'] in ['geometry', 'upscale_rgb_geometry']:
        # If last task is geometry, use the dst structure
        output_path = os.path.normpath(os.path.join(
            db['common']['directories']['cache'],
            shot['dst']['k_ep'],
            shot['dst']['k_part'],
            '%03d' % (shot['no'])))
    else:
        # Otherwise, use the src directory as these images are shared among
        # episodes
        output_path = os.path.normpath(os.path.join(
            db['common']['directories']['cache'],
            shot['k_ep'],
            shot['k_part'],
            '%03d' % (shot['no'])))

    return output_path



def get_input_filepath(database, frame):
    k_ed = frame['k_ed']
    if frame['k_ep'] != 0:
        return database['editions'][k_ed]['inputs']['video'][frame['k_ep']]
    else:
        return database['editions'][k_ed]['inputs']['video'][frame['k_ep']]




def is_progressive_file_valid(shot, db_common, verbose:bool=False):
    verbose = True

    if verbose:
        print_lightgreen("is_progressive_file_valid")
    progressive_filepath = shot['inputs']['progressive']['filepath']
    if not os.path.exists(progressive_filepath):
        if verbose:
            print(f"progressive filepath: {progressive_filepath}")
        return False

    progressive_duration = get_video_duration(db_common,
        progressive_filepath,
        integrity=False)
    interlaced_duration = get_video_duration(
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
        interlaced_duration -= (frames_to_ms(start) / 1000)
        if progressive_duration != interlaced_duration:
            if verbose:
                print("\tnot valid: %.02fs, should be %.02fs" % (progressive_duration, interlaced_duration))
            return False
    else:
        # Partial video
        if progressive_duration != count / FPS:
            if verbose:
                print("\tnot valid: %.02fs, sould be %.02fs" % (progressive_duration, count * FPS))
                sys.exit(print_yellow(f"verify this!"))
            return False

    if verbose:
        print("\tvalid")
    return True