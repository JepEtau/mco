# -*- coding: utf-8 -*-
import os
from pprint import pprint
from filters.utils import get_step_no_from_last_task, get_step_no_from_task

from utils.common import (
    K_GENERIQUES,
)
# from filters.utils import (
#     FILTER_BASE_NO,
#     FILTER_BASE_NO_DEBUG,
#     get_filter_id,
#     get_filter_id_generique,
# )


PATH_DATABASE = "../database"


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



def get_deinterlaced_filepath_list(db, shot:dict, task, do_50p=False):
    # Returns a list of filepath for the specified task

    if task not in ['deinterlace', 'pre_upscale', 'upscale']:
        # reworked, thius, this function can be used only for deinterlace task
        raise Exception("get_deinterlaced_filepath_list: this function cannot be used for task [%s]" % (task))

    # print("%s.task: k_step=%s, shot=" % (__name__, k_step))
    # pprint(shot)
    filepath_list = list()
    prefix = "%s_" % (shot['k_ep'])

    if shot['k_part'] in K_GENERIQUES:
        filter_id = get_filter_id_generique(db, shot, task)
    else:
        filter_id = get_filter_id(db, shot, task)

    suffix = "__%s__%03d" % (shot['k_ed'], filter_id)

    deinterlace_output_path = get_output_path_from_shot(db=db, shot=shot, task=task)
    if do_50p:
        shot_end = shot['start'] + 2 * shot['count']
    else:
        shot_end = shot['start'] + shot['count']
    for no in range(shot['start'], shot_end):
        filename = "%s%06d%s.png" % (prefix, no, suffix)
        filepath_list.append(os.path.join(deinterlace_output_path, filename))

    return filepath_list



def get_deinterlaced_path_and_filename(db, shot:dict, task):
    if task not in ['deinterlace', 'pre_upscale', 'upscale']:
        # reworked, thius, this function can be used only for deinterlace task
        raise Exception("get_deinterlaced_path_and_filename: this function cannot be used for task [%s]" % (task))
    prefix = "%s_" % (shot['k_ep'])

    if shot['k_part'] in K_GENERIQUES:
        filter_id = get_filter_id_generique(db, shot, task)
    else:
        filter_id = get_filter_id(db, shot, task)

    suffix = "__%s__%03d" % (shot['k_ed'], filter_id)
    deinterlace_output_path = get_output_path_from_shot(db=db, shot=shot, task=task)
    filename = prefix + '%' + "05d%s.png" % (suffix)

    return deinterlace_output_path, filename



def get_frames_output_filepaths(db, shot:dict, frame_no:int):
    k_ep = shot['k_ep']
    k_ed = shot['k_ed']

    filepaths = dict()
    for task in FILTER_BASE_NO:
        if task == 'upscale_rgb_geometry':
            suffix = "__%s__%03d" % (k_ed, FILTER_BASE_NO_DEBUG['upscale_rgb_geometry'])
        else:
            suffix = "__%s__%03d" % (k_ed, get_filter_id(db, shot, task))

        outputFilename = "%s_%06d%s.png" % (k_ep, frame_no, suffix)
        output_directory = get_output_path_from_shot(db=db, shot=shot, task=task)
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        filepaths[task] = os.path.join(output_directory, outputFilename).strip('\n')

    # For debug and verification of video edition
    for task in FILTER_BASE_NO_DEBUG:
        if task in shot['tasks']:
            suffix = "__%s__%03d" % (k_ed, FILTER_BASE_NO_DEBUG[task])
            outputFilename = "%s_%06d%s.png" % (k_ep, frame_no, suffix)
            output_directory = get_output_path_from_shot(db=db, shot=shot, task=task)
            if not os.path.exists(output_directory):
                os.makedirs(output_directory)
            filepaths[task] = os.path.join(output_directory, outputFilename).strip('\n')
            break

    return filepaths



def get_frames_output_paths_for_study(db, frame:dict):
    k_ep = frame['k_ep']
    k_ed = frame['k_ed']
    k_part = frame['k_part']
    frame_no = frame['no']

    # Output directory for frames
    if k_part in K_GENERIQUES:
        output_directory = db[k_part]['common']['frames']['path_output']
    else:
        output_directory = os.path.join(db[k_ep]['common']['frames']['path_output'], k_part)
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Structure used to store the filepath for each task
    filepaths = dict()
    for task in FILTER_BASE_NO:
        if task == 'upscale_rgb_geometry':
            suffix = "__%s__%03d" % (k_ed, FILTER_BASE_NO_DEBUG['upscale_rgb_geometry'])
        else:
            suffix = "__%s__%03d" % (k_ed, get_filter_id(db, frame, task))

        if frame['k_part'] in K_GENERIQUES:
            outputFilename = "ep00_%06d_%s%s.png" % (frame_no, k_ep, suffix)
        else:
            outputFilename = "%s_%06d%s.png" % (k_ep, frame_no, suffix)

        filepaths[task] = os.path.join(output_directory, outputFilename).strip('\n')

    return filepaths
