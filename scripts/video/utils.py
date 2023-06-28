# -*- coding: utf-8 -*-
import os
from pprint import pprint
from utils.pretty_print import *


def create_folder_for_video(db, k_ep_or_g):
    """ Create the directory that shall contains all video stream
        that will be concatenated

        Returns
            Path of the created folder
    """
    if k_ep_or_g in ['ep00', 'ep40']:
        return

    if k_ep_or_g in['g_debut', 'g_fin']:
        video_directory = os.path.join(db[k_ep_or_g]['cache_path'], 'video')
    else:
        video_directory = os.path.join(db[k_ep_or_g]['cache_path'], 'video')

    if not os.path.exists(video_directory):
        os.makedirs(video_directory)
    return video_directory


def create_folder_for_concatenation(db, k_ep, k_part):
    k_ep_or_g = k_part if k_part in ['g_debut', 'g_fin'] else k_ep

    concatenation_directory = os.path.join(db[k_ep_or_g]['cache_path'], "concatenation")
    if not os.path.exists(concatenation_directory):
        os.makedirs(concatenation_directory)

