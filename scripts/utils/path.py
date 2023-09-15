# -*- coding: utf-8 -*-
import os
from pprint import pprint
from img_toolbox.utils import get_step_no_from_task
from utils.pretty_print import *
from utils.types import Shot

PATH_DATABASE = "./database"


def get_input_path_from_shot(db, shot:Shot, task):
    step_no = get_step_no_from_task(shot, task)

    if shot['k_part'] in ['g_debut', 'g_fin']:
        # Put all images in a single folder for 'génériques'
        return os.path.normpath(os.path.join(db['common']['directories']['cache'],
                shot['k_part'],
                f"{shot['no']:03}",
                '%02d' % (step_no)))

    if task in ['geometry', 'upscale_rgb_geometry', 'final']:
        # If last task is geometry, use the dst structure
        output_path = os.path.normpath(os.path.join(db['common']['directories']['cache'],
            shot['src']['k_ep'],
            shot['src']['k_part'],
            f"{shot['no']:03}",
            '%02d' % (step_no)))
    else:
        # Otherwise, use the src directory as these images are shared among
        # episodes
        output_path = os.path.normpath(os.path.join(db['common']['directories']['cache'],
            shot['k_ep'],
            shot['k_part'],
            f"{shot['src']['no']:03}",
            '%02d' % (step_no)))
    return output_path


def get_output_path_from_shot(db, shot:Shot, task):
    step_no = get_step_no_from_task(shot, task)

    if shot['k_part'] in ['g_debut', 'g_fin']:
        # Put all images in a single folder for 'génériques'
        return os.path.normpath(os.path.join(db['common']['directories']['cache'],
            shot['k_part'], f"{shot['no']:03}", f"{step_no:02}"))

    if task in ['geometry', 'upscale_rgb_geometry', 'final']:
        # If last task is geometry, use the dst structure
        output_path = os.path.normpath(os.path.join(db['common']['directories']['cache'],
            shot['dst']['k_ep'], shot['dst']['k_part'], f"{shot['no']:03}", f"{step_no:02}"))
    else:
        # Otherwise, use the src directory as these images are shared among
        # episodes
        output_path = os.path.normpath(os.path.join(db['common']['directories']['cache'],
            shot['k_ep'], shot['k_part'], f"{shot['src']['no']:03}", f"{step_no:02}"))
    return output_path


def get_cache_path(db, shot:Shot):

    if shot['k_part'] in ['g_debut', 'g_fin']:
        # Put all images in a single folder for 'génériques'
        return os.path.normpath(os.path.join(
            db['common']['directories']['cache'],
            shot['k_part'], f"{shot['no']:03}"))

    if shot['last_task'] in ['geometry', 'upscale_rgb_geometry']:
        # If last task is geometry, use the dst structure
        output_path = os.path.normpath(os.path.join(
            db['common']['directories']['cache'],
            shot['dst']['k_ep'],
            shot['dst']['k_part'],
            f"{shot['no']:03}"))
    else:
        # Otherwise, use the src directory as these images are shared among
        # episodes
        output_path = os.path.normpath(os.path.join(
            db['common']['directories']['cache'],
            shot['k_ep'],
            shot['k_part'],
            f"{shot['src']['no']:03}"))

    return output_path


def get_input_filepath(database, frame):
    k_ed = frame['k_ed']
    if frame['k_ep'] != 0:
        return database['editions'][k_ed]['inputs']['video'][frame['k_ep']]
    else:
        return database['editions'][k_ed]['inputs']['video'][frame['k_ep']]


