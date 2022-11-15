# -*- coding: utf-8 -*-
import os
from pprint import pprint

from utils.common import (
    K_GENERIQUES,
    get_k_part_from_frame_no,
)
from utils.get_filters import (
    FILTER_BASE_NO,
    FILTER_BASE_NO_DEBUG,
    get_filter_id,
    get_filter_id_generique,
)


PATH_DATABASE = "../database"


def create_video_directory(db, k_ep):
    """ Create the directory that shall contains all video stream
        that will be concatenated

        Returns
            Path of the created folder
    """
    if k_ep in ['ep00', 'ep40']:
        return

    video_directory = os.path.join(db[k_ep]['target']['path']['cache'], "video")
    if not os.path.exists(video_directory):
        os.makedirs(video_directory)
    return video_directory



def create_audio_directory(db, k_ep):
    """ Create the directory that shall contains all audio stream

        Returns
            Path of the created folder
    """
    if k_ep in ['ep00', 'ep40']:
        return

    audio_directory = os.path.join(db[k_ep]['target']['path']['cache'], "audio")
    if not os.path.exists(audio_directory):
        os.makedirs(audio_directory)
    return audio_directory



def create_folder_for_concatenation(db, k_ep):
    """ Create the directory that shall contains all video stream
        that will be concatenated

        Returns
            Path of the created folder
    """
    concatenation_directory = os.path.join(db[k_ep]['target']['path']['cache'], "concatenation")
    if not os.path.exists(concatenation_directory):
        os.makedirs(concatenation_directory)



def get_output_path_from_shot(db, shot, task):
    if shot['k_part'] in ['g_debut', 'g_fin']:
        # Put all images in a single folder for 'génériques'
        return os.path.join(db['common']['directories']['cache'],
                shot['k_part'],
                '%05d' % (shot['start']))

    if task in ['geometry', 'deinterlace_rgb', 'upscale_rgb_geometry']:
        # If last task is geometry, use the dst structure
        output_path = os.path.join(db['common']['directories']['cache'],
            shot['dst']['k_ep'],
            shot['dst']['k_part'],
            '%05d' % (shot['start']))
    else:
        # Otherwise, use the src directory as these images are shared by
        # multiple episode
        output_path = os.path.join(db['common']['directories']['cache'],
            shot['k_ep'],
            shot['k_part'],
            '%05d' % (shot['start']))
    return output_path


def get_input_filepath(database, frame):
    k_ed = frame['k_ed']
    if frame['k_ep'] != 0:
        return database['editions'][k_ed]['inputs'][frame['k_ep']]
    else:
        return database['editions'][k_ed]['inputs'][frame['k_ep']]



def get_output_frame_filepaths_for_study(database, frame:dict, k_part=''):
    # print("%s.get_output_frame_filepaths_for_study: %s" % (__name__, k_part))
    # pprint(frame)
    k_ep = frame['k_ep']
    k_ed = frame['k_ed']
    k_part_dst = frame['k_part']
    if k_part_dst == '':
        k_part = get_k_part_from_frame_no(database, k_ed, k_ep, frame['no'])

    path_frames = database[k_ep][k_ed]['path']['frames']
    if k_part_dst in K_GENERIQUES:
        output_directory = os.path.join(path_frames, k_part_dst)
    elif k_part_dst in ['precedemment', 'asuivre']:
        # TODO: clean this
        output_directory = os.path.join(path_frames, k_ep, k_part_dst)
    else:
        output_directory = os.path.join(path_frames, k_ep, k_part_dst)

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    extension = database['common']['settings']['frame_format']

    filepaths = dict()
    for k_step in FILTER_BASE_NO.keys():
        if k_step in frame['filters']['id'].keys():
            # use the id for this frame
            suffix = "__%s__%03d" % (k_ed, FILTER_BASE_NO[k_step] + frame['filters']['id'][k_step])
        else:
            # TODO: correct this ?
            suffix = "__%s__%03d" % (k_ed, FILTER_BASE_NO[k_step])
        if k_part_dst in K_GENERIQUES:
            outputFilename = "ep00_%05d_%s%s.%s" % (int(frame['ref']), k_ep, suffix, extension)
        else:
            outputFilename = "%s_%05d%s.%s" % (k_ep, int(frame['ref']), suffix, extension)
        filepaths[k_step] = os.path.join(output_directory, outputFilename).strip('\n')

    return filepaths



def get_deinterlaced_filepath_list(db, shot:dict, task):
    # Returns a list of filepath for the specified task

    if task not in ['deinterlace', 'pre_upscale', 'upscale']:
        # reworked, thius, this function can be used only for deinterlace task
        raise Exception("get_deinterlaced_filepath_list: this function cannot be used for task [%s]" % (task))

    # print("%s.task: k_step=%s, shot=" % (__name__, k_step))
    # pprint(shot)
    filepath_list = list()
    extension = db['common']['settings']['frame_format']
    prefix = "%s_" % (shot['k_ep'])

    if shot['k_part'] in K_GENERIQUES:
        filter_id = get_filter_id_generique(db, shot, task)
    else:
        filter_id = get_filter_id(db, shot, task)

    suffix = "__%s__%03d" % (shot['k_ed'], filter_id)

    deinterlace_output_path = get_output_path_from_shot(db=db, shot=shot, task=task)
    for no in range(shot['ref'], shot['ref'] + shot['count']):
        filename = "%s%05d%s.%s" % (prefix, no, suffix, extension)
        filepath_list.append(os.path.join(deinterlace_output_path, filename))

    return filepath_list




def get_deinterlaced_path_and_filename(db, shot:dict, task):
    if task not in ['deinterlace', 'pre_upscale', 'upscale']:
        # reworked, thius, this function can be used only for deinterlace task
        raise Exception("get_deinterlaced_path_and_filename: this function cannot be used for task [%s]" % (task))

    extension = db['common']['settings']['frame_format']
    prefix = "%s_" % (shot['k_ep'])

    if shot['k_part'] in K_GENERIQUES:
        filter_id = get_filter_id_generique(db, shot, task)
    else:
        filter_id = get_filter_id(db, shot, task)

    suffix = "__%s__%03d" % (shot['k_ed'], filter_id)
    deinterlace_output_path = get_output_path_from_shot(db=db, shot=shot, task=task)
    filename = prefix + '%' + "05d%s.%s" % (suffix, extension)

    return deinterlace_output_path, filename



def get_output_frame_filepaths(db, shot:dict, frame_no:int):
    k_ep = shot['k_ep']
    k_ed = shot['k_ed']

    extension = db['common']['settings']['frame_format']

    filepaths = dict()
    for task in FILTER_BASE_NO:
        if task == 'stitching':
            suffix = "__%s__%03d" % (k_ed, get_filter_id(db, shot, 'sharpen'))
        elif task == 'upscale_rgb_geometry':
            suffix = "__%s__%03d" % (k_ed, FILTER_BASE_NO_DEBUG['upscale_rgb_geometry'])
        else:
            suffix = "__%s__%03d" % (k_ed, get_filter_id(db, shot, task))

        outputFilename = "%s_%05d%s.%s" % (k_ep, frame_no, suffix, extension)
        output_directory = get_output_path_from_shot(db=db, shot=shot, task=task)
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        filepaths[task] = os.path.join(output_directory, outputFilename).strip('\n')

    # For debug and verification of video edition
    for task in FILTER_BASE_NO_DEBUG:
        if task in shot['tasks']:
            suffix = "__%s__%03d" % (k_ed, FILTER_BASE_NO_DEBUG[task])
            outputFilename = "%s_%05d%s.%s" % (k_ep, frame_no, suffix, extension)
            output_directory = get_output_path_from_shot(db=db, shot=shot, task=task)
            if not os.path.exists(output_directory):
                os.makedirs(output_directory)
            filepaths[task] = os.path.join(output_directory, outputFilename).strip('\n')
            break

    return filepaths


