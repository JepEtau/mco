#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pprint import pprint

from utils.get_filters import FILTER_BASE_NO
from utils.get_filters import get_filter_id
from utils.get_filters import get_filter_id_generique
from utils.common import K_GENERIQUES, get_k_part_from_frame_no

import os

PATH_DATABASE = "../database"
PATH_DATABASE_COMBINE = "../db"
PATH_CURVES = "../curves"


def create_video_directory(db, k_ep):
    """ Create the directory that shall contains all video stream
        that will be concatenated

        Returns
            Path of the created folder
    """
    if k_ep in ['ep00', 'ep40']:
        return

    video_directory = os.path.join(db[k_ep]['common']['path']['cache'], "video")
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

    audio_directory = os.path.join(db[k_ep]['common']['path']['cache'], "audio")
    if not os.path.exists(audio_directory):
        os.makedirs(audio_directory)
    return audio_directory



def create_folder_for_concatenation(db, k_ep):
    """ Create the directory that shall contains all video stream
        that will be concatenated

        Returns
            Path of the created folder
    """
    concatenation_directory = os.path.join(db[k_ep]['common']['path']['cache'], "concatenation")
    if not os.path.exists(concatenation_directory):
        os.makedirs(concatenation_directory)



def get_output_folder_from_shot(db, shot):
    if shot['k_part'] in ['g_debut', 'g_fin']:
        # Put all images in a single folder for 'génériques'
        return os.path.join(db['common']['directories']['cache'],
                shot['k_part'],
                '%05d' % (shot['start']))

    return os.path.join(db['common']['directories']['cache'],
                shot['k_ep'],
                shot['k_part'],
                '%05d' % (shot['start']))



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



def get_output_filepath_list(db, shot:dict, k_step):
    # Returns a list of filepaths for the filter specified by 'k_step'

    # print("%s.get_output_filepath_list: k_step=%s, shot=" % (__name__, k_step))
    # pprint(shot)
    filepaths = list()
    extension = db['common']['settings']['frame_format']
    prefix = "%s_" % (shot['k_ep'])

    if shot['k_part'] in K_GENERIQUES:
        filter_id = get_filter_id_generique(db, shot, k_step)
    else:
        filter_id = get_filter_id(db, shot, k_step)

    suffix = "__%s__%03d" % (shot['k_ed'], filter_id)

    for no in range(shot['ref'], shot['ref'] + shot['count']):
        filename = "%s%05d%s.%s" % (prefix, no, suffix, extension)
        filepaths.append(os.path.join(shot['output_path'], filename))

    return filepaths



def get_output_frame_filepaths(db, shot:dict, frame_no:int):
    k_ep = shot['k_ep']
    k_ed = shot['k_ed']

    output_directory = shot['output_path']
    extension = db['common']['settings']['frame_format']

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    filepaths = dict()
    for k_step in FILTER_BASE_NO.keys():
        if k_step == 'stitching':
            suffix = "__%s__%03d" % (k_ed, get_filter_id(db, shot, 'sharpen'))
        else:
            suffix = "__%s__%03d" % (k_ed, get_filter_id(db, shot, k_step))

        outputFilename = "%s_%05d%s.%s" % (k_ep, frame_no, suffix, extension)
        filepaths[k_step] = os.path.join(output_directory, outputFilename).strip('\n')

    return filepaths



def create_output_folder_for_shot(layers):
    for layer in layers.keys():
        output_path = os.path.normpath(layers[layer]['shot']['output_path'])
        if not os.path.exists(output_path):
            os.makedirs(output_path)