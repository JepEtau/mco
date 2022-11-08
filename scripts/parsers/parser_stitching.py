#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import collections
import configparser
from copy import deepcopy
import numpy as np
import os
import os.path
from pathlib import Path
from pathlib import PosixPath
from pprint import pprint
import re
import sys
from images.curve import Curve

from utils.common import K_GENERIQUES, get_k_part_from_frame_no
from utils.common import get_shot_from_frame_no_new

STITCHING_EXTRACTORS = [
    'sift',
    'surf',
    'brisk',
    'orb'
]

STITCHING_MATCHING = [
    'bf',
    'knn'
]

STITCHING_METHOD = [
    'RHO',
    'RANSAC',
    'LMEDS'
]

# 'crop': [50,50,60,36],
# roi = [y0,y1,x0,x1]
STITCHING_SHOT_PARAMETERS_DEFAULT = {
    'roi': [0, 0, 0, 0],
    'extractor': 'sift',
    'matching': 'bf',
    'method': 'RHO',
    'reproj_threshold': 5,
    'knn_ratio': 0.2,
    'sharpen': [3, 0.5],    # radius, amount
    'is_enabled': False,    # Enable homography
    'is_default': True,     # Use thes default parameters
    'is_shot': True,        # This struct is common to a shot (a frame otherwise)
}


# top, bottom, left, right
# !!!! These values shall never be modified
# because crop values for sticthich (stabilized?) depends on theses values.
STICTHING_FGD_PAD = [60, 60, 80, 60]



STITCHING_CURVES_DEFAULT = {
    'k_curves': '',
    'points': dict(),
    'lut': None,
}



def parse_stitching_configurations(db, k_ep_or_g:str, parse_parameters=False):
    # Open configuration file
    filepath = os.path.join(db['common']['directories']['config'], k_ep_or_g, "%s_stitching.ini" % (k_ep_or_g))
    if filepath.startswith("~/"):
        filepath = os.path.join(PosixPath(Path.home()), filepath[2:])
    if not os.path.exists(filepath):
        # print("warning: %s does not exists" % (filepath))
        return

    # Parse the file
    config = configparser.ConfigParser()
    config.read(filepath)
    print("%s.parse_stitching_configurations: %s" % (__name__, k_ep_or_g))
    for k_section in config.sections():
        if '.' not in k_section:
            sys.exit("parse_stitching_configurations: error, no edition,ep,part specified")
        k_ed, k_ep, k_part = k_section.split('.')

        for frame_no_str in config.options(k_section):

            # get frame_no and type
            frame_no_type = re.search(re.compile("(\d+)([_a-z]*)"), frame_no_str)
            if frame_no_type is None:
                continue
            type = frame_no_type.group(2)
            if type == '_parameters' and not parse_parameters:
                continue
            frame_no = int(frame_no_type.group(1))

            # get shot from frame_no
            k_part = get_k_part_from_frame_no(db, k_ed, k_ep, frame_no)
            shot = get_shot_from_frame_no_new(db, frame_no=frame_no, k_ed=k_ed, k_ep=k_ep, k_part=k_part)
            if shot is None:
                sys.exit("parse_stabilize_configurations: error, shot not found for frame no. %d in %s:%s:%s" % (
                    frame_no, k_ed, k_ep, k_part))

            if type == '_parameters' and parse_parameters:
                # Parameters to calculate the homography matrix for each frame
                # AND the crop area after the stitching
                if 'stitching' not in shot.keys():
                    shot['stitching'] = dict()
                if 'parameters' not in shot['stitching'].keys():
                    shot['stitching'].update({
                        'parameters': deepcopy(STITCHING_SHOT_PARAMETERS_DEFAULT)
                    })

                # Get all parameters
                properties = config.get(k_section, frame_no_str).replace(' ', '').split(',')
                for property in properties:
                    property_array_str = property.split('=')
                    p = _parameter_to_property(property_array_str)
                    shot['stitching']['parameters'][p[0]] = p[1]

                shot['stitching']['parameters']['is_default'] = False


            elif type == '_fgd_crop':
                if 'stitching' not in shot.keys():
                    shot['stitching'] = dict()
                property_array_str = config.get(k_section, frame_no_str).replace(' ', '')
                shot['stitching']['fgd_crop'] = list(map(int, property_array_str.split(':')))


            elif type == '_curves':
                k_curves = config.get(k_section, frame_no_str).replace(' ', '')
                if k_curves != '':
                    if 'stitching' not in shot.keys():
                        shot['stitching'] = dict()
                    shot['stitching']['curves'] = {
                        'k_curves': k_curves,
                        'points': None,
                        'lut': None,
                    }

            else:
                if 'stitching' not in shot.keys():
                    shot['stitching'] = dict()
                if 'frames' not in shot['stitching'].keys():
                    shot['stitching']['frames'] = dict()

                shot['stitching']['frames'][frame_no] = dict()
                properties = config.get(k_section, frame_no_str).replace(' ', '').split(';')
                for property in properties:
                    property_array_str = property.split('=')
                    if property_array_str[0] == 'm':
                        m = np.fromstring(property_array_str[1], dtype=np.float64, count=9, sep=',')
                        shot['stitching']['frames'][frame_no]['m'] = m.reshape(3,3)
                        continue

                    p = _parameter_to_property(property_array_str)
                    if p[0] == 'roi':
                        shot['stitching']['frames'][frame_no][p[0]] = p[1]
                        continue

                    if parse_parameters:
                        # Customized parameters for this frame
                        if 'parameters' not in shot['stitching']['frames'][frame_no].keys():
                            shot['stitching']['frames'][frame_no]['parameters'] = deepcopy(STITCHING_SHOT_PARAMETERS_DEFAULT)
                        # Overwrite default parameters by the one specified here
                        shot['stitching']['frames'][frame_no]['parameters'][p[0]] = p[1]
                        shot['stitching']['frames'][frame_no]['parameters']['is_default'] = False


def _parameter_to_property(p):
    if p[0] == 'roi':
        return [p[0], list(map(int, p[1].split(':')))]

    if p[0] == 'sharpen':
        return [int(p[0]), np.float32(p[1])]

    if p[0] == 'reproj_threshold':
        return [p[0], int(p[1])]

    if p[0] == 'knn_ratio':
        return [p[0], np.float32(p[1])]

    if p[0] == 'en':
        return ['is_enabled', True if p[1].lower()=='true' else False]

    return list(p)



def get_shots_stitching_parameters(db, k_ep, k_part) -> dict:
    """ Returns a dict of stitching parameters for each shot of this k_ep:k_part
    """
    shots_stitching_parameters = dict()

    # Get the list of editions and episode that are used by this ep/part
    if k_part in ['g_debut', 'g_fin']:
        db_video = db[k_part]['common']['video']
    else:
        print("%s.get_shots_stitching_parameters: %s:%s" % (__name__, k_ep, k_part))
        k_ed_src = db[k_ep]['common']['video']['reference']['k_ed']
        k_ep_src = k_ep
        db_video = db[k_ep_src][k_ed_src][k_part]['video']
        print("%s.get_shots_stitching_parameters: src=%s:%s:%s" % (__name__, k_ed_src, k_ep_src, k_part))

    for shot in db_video['shots']:
        # print(shot)
        if ('src' not in shot.keys()
            or ('use' in shot['src'].keys()
            and not shot['src']['use'])):
            shot_src = shot
        else:
            if 'k_ed' in shot['src'].keys():
                k_ed_src = shot['src']['k_ed']
            k_ep_src = shot['src']['k_ep']
            k_part_src = get_k_part_from_frame_no(db, k_ed_src, k_ep_src, shot['src']['start'])
            shot_src = get_shot_from_frame_no_new(db, frame_no=shot['src']['start'], k_ed=k_ed_src, k_ep=k_ep_src, k_part=k_part_src)

        # Append to the dict if parameters are defined
        if ('stitching' not in shot_src.keys()
            or 'parameters' not in shot_src['stitching'].keys()):
            continue

        if shot_src['stitching']['parameters'] is not None:
            shots_stitching_parameters[shot['no']] = shot_src['stitching']['parameters']

    return shots_stitching_parameters



def get_frames_stitching_parameters(db, k_ep, k_part) -> dict:
    """ Returns a dict of stitching parameters for each frame of this k_ep:k_part
    these parameters differ from the ones that are defined in shot
    """
    frames_stitching_parameters = dict()

    # Get the list of editions and episode that are used by this ep/part
    if k_part in ['g_debut', 'g_fin']:
        db_video = db[k_part]['common']['video']
    else:
        print("%s.get_frames_stitching_parameters: %s:%s" % (__name__, k_ep, k_part))
        k_ed_src = db[k_ep]['common']['video']['reference']['k_ed']
        k_ep_src = k_ep
        db_video = db[k_ep_src][k_ed_src][k_part]['video']
        print("%s.get_frames_stitching_parameters: src=%s:%s:%s" % (__name__, k_ed_src, k_ep_src, k_part))


    for shot in db_video['shots']:
        # print(shot)
        if ('src' not in shot.keys()
            or ('use' in shot['src'].keys()
            and not shot['src']['use'])):
            shot_src = shot
        else:
            if 'k_ed' in shot['src'].keys():
                k_ed_src = shot['src']['k_ed']
            k_ep_src = shot['src']['k_ep']
            k_part_src = get_k_part_from_frame_no(db, k_ed_src, k_ep_src, shot['src']['start'])
            shot_src = get_shot_from_frame_no_new(db, frame_no=shot['src']['start'], k_ed=k_ed_src, k_ep=k_ep_src, k_part=k_part_src)

        # pprint(shot_src)
        if 'stitching' not in shot_src.keys():
            shot_src['stitching'] = {'frames': dict()}

        if 'parameters' not in shot_src['stitching'].keys():
            shot_src['stitching']['parameters'] = deepcopy(STITCHING_SHOT_PARAMETERS_DEFAULT)
            if len(shot_src['stitching']['frames'].keys()) > 0:
                # At least one frame has stitching, thus enable this, but may be buggy as the default parameters
                shot_src['stitching']['parameters']['is_enabled'] = True
                sys.exit("Error: %s:%s: At least one frame has stitching but no parameters are defined" % (k_ep, k_part))


        # TODO
        # if 'stitching' in shot_src.keys() and 'frames' in shot_src['stitching'].keys():
        #     is_enabled = shot_src['stitching']['parameters']['is_enabled']
        #     for frame_no, f in shot_src['stitching']['frames'].values():
        #         # enable/disable parameters if shot parameters are enabled/disabled
        #         if ('parameters' in shot_src['stitching']['frames'].keys()
        #             and f['parameters']['is_enabled']):

        #             frames_stitching_parameters.update({
        #             shot['no']: shot_src['stitching']['frames']
        #             })

    return frames_stitching_parameters




def get_shots_stitching_fgd_crop(db, k_ep, k_part) -> dict:
    """ Returns a dict of fgd crop for each shot of this k_ep:k_part
    """
    fgd_crop = dict()

    # Get the list of editions and episode that are used by this ep/part
    if k_part in ['g_debut', 'g_fin']:
        db_video = db[k_part]['common']['video']
    else:
        print("%s.get_shots_stitching_fgd_crop: %s:%s" % (__name__, k_ep, k_part))
        k_ed_src = db[k_ep]['common']['video']['reference']['k_ed']
        k_ep_src = k_ep
        db_video = db[k_ep_src][k_ed_src][k_part]['video']
        print("%s.get_shots_stitching_fgd_crop: src=%s:%s:%s" % (__name__, k_ed_src, k_ep_src, k_part))

    for shot in db_video['shots']:
        # print(shot)
        if ('src' not in shot.keys()
            or ('use' in shot['src'].keys()
            and not shot['src']['use'])):
            shot_src = shot
        else:
            if 'k_ed' in shot['src'].keys():
                k_ed_src = shot['src']['k_ed']
            k_ep_src = shot['src']['k_ep']
            k_part_src = get_k_part_from_frame_no(db, k_ed_src, k_ep_src, shot['src']['start'])
            shot_src = get_shot_from_frame_no_new(db, frame_no=shot['src']['start'], k_ed=k_ed_src, k_ep=k_ep_src, k_part=k_part_src)

        # Append to the dict if fgd_crop is defined
        if ('stitching' not in shot_src.keys()
            or 'fgd_crop' not in shot_src['stitching'].keys()):
            continue

        if shot_src['stitching']['fgd_crop'] is not None:
            fgd_crop[shot['no']] = shot_src['stitching']['fgd_crop']

    return fgd_crop





def get_frames_stitching_transformation(db, k_ep, k_part) -> dict:
    """ Returns a dict of transformation parameters for each frame of this k_ep:k_part
    """
    frames_stitching = dict()

    # Get the list of editions and episode that are used by this ep/part
    if k_part in ['g_debut', 'g_fin']:
        db_video = db[k_part]['common']['video']
    else:
        print("%s.get_frames_stitching_transformation: %s:%s" % (__name__, k_ep, k_part))
        k_ed_src = db[k_ep]['common']['video']['reference']['k_ed']
        k_ep_src = k_ep
        db_video = db[k_ep_src][k_ed_src][k_part]['video']
        print("%s.get_frames_stitching_transformation: src=%s:%s:%s" % (__name__, k_ed_src, k_ep_src, k_part))

    for shot in db_video['shots']:
        # print(shot)
        if ('src' not in shot.keys()
            or ('use' in shot['src'].keys()
            and not shot['src']['use'])):
            shot_src = shot
        else:
            if 'k_ed' in shot['src'].keys():
                k_ed_src = shot['src']['k_ed']
            k_ep_src = shot['src']['k_ep']
            k_part_src = get_k_part_from_frame_no(db, k_ed_src, k_ep_src, shot['src']['start'])
            shot_src = get_shot_from_frame_no_new(db, frame_no=shot['src']['start'], k_ed=k_ed_src, k_ep=k_ep_src, k_part=k_part_src)

        if 'stitching' in shot_src.keys() and 'frames' in shot_src['stitching'].keys():

            is_enabled = shot_src['stitching']['parameters']['is_enabled']
            for f in shot_src['stitching']['frames']:
                # enable/disable parameters if shot parameters are enabled/disabled
                if 'parameters' in shot_src['stitching']['frames'].keys():
                    f['parameters']['is_enabled'] = is_enabled

            frames_stitching.update({
                shot['no']: shot_src['stitching']['frames']
            })

    return frames_stitching



def get_shot_stitching_curves(db, k_ep, k_part) -> dict:
    shot_stitching_curves = dict()

    # Get the list of editions and episode that are used by this ep/part
    if k_part in ['g_debut', 'g_fin']:
        db_video = db[k_part]['common']['video']
    else:
        print("%s.get_shot_stitching_curves: %s:%s" % (__name__, k_ep, k_part))
        k_ed_src = db[k_ep]['common']['video']['reference']['k_ed']
        k_ep_src = k_ep
        db_video = db[k_ep_src][k_ed_src][k_part]['video']
        print("%s.get_shot_stitching_curves: src=%s:%s:%s" % (__name__, k_ed_src, k_ep_src, k_part))

    for shot in db_video['shots']:
        # print(shot)
        if ('src' not in shot.keys()
            or ('use' in shot['src'].keys()
            and not shot['src']['use'])):
            shot_src = shot
        else:
            if 'k_ed' in shot['src'].keys():
                k_ed_src = shot['src']['k_ed']
            k_ep_src = shot['src']['k_ep']
            k_part_src = get_k_part_from_frame_no(db,
                k_ed_src,
                k_ep_src,
                shot['src']['start'])
            shot_src = get_shot_from_frame_no_new(db,
                frame_no=shot['src']['start'],
                k_ed=k_ed_src,
                k_ep=k_ep_src,
                k_part=k_part_src)

        # Append to the dict if stitching curves are defined
        if ('stitching' not in shot_src.keys()
            or 'curves' not in shot_src['stitching'].keys()):
            continue

        if shot_src['stitching']['curves'] is not None:
            shot_stitching_curves[shot['no']] = shot_src['stitching']['curves']

    return shot_stitching_curves



def save_shot_stitching_curves(db, k_ep, k_part, shots:dict, stitching_curves) -> dict:
    print("save_shot_stitching_curves: %s:%s" % (k_ep, k_part))

    for shot_no, shot in shots.items():
        print("\t- shot no. %d" % (shot_no))
        # print("***********************************************")
        # pprint(shot)

        # Select the shot used for the generation
        if 'src' in shot.keys() and shot['src']['use']:
            k_ed_src = shot['src']['k_ed']
            k_ep_src = shot['src']['k_ep']
            k_part_src = get_k_part_from_frame_no(db, k_ed=k_ed_src, k_ep=k_ep_src, frame_no=shot['src']['start'])
            shot_src = get_shot_from_frame_no_new(db,
                shot['src']['start'], k_ed=k_ed_src, k_ep=k_ep_src, k_part=k_part_src)
            if 'count' not in shot['src'].keys():
                shot['src']['count'] = shot_src['count']
            if shot_src is None:
                sys.exit()
        else:
            k_ed_src = db[k_ep]['common']['video']['reference']['k_ed']
            k_ep_src = k_ep
            k_part_src = k_part
            shot_src = shot


        # Use the config file
        if k_part in K_GENERIQUES:
            k_ed_src = db[k_part]['common']['video']['reference']['k_ed']
            k_part_src = k_part


        # Open configuration file
        if k_part in K_GENERIQUES:
            filepath = os.path.join(db['common']['directories']['config'], k_part_src, "%s_stitching.ini" % (k_part))
        else:
            filepath = os.path.join(db['common']['directories']['config'], k_ep_src, "%s_stitching.ini" % (k_ep))
        if filepath.startswith("~/"):
            filepath = os.path.join(PosixPath(Path.home()), filepath[2:])


        # Parse the file
        if os.path.exists(filepath):
            config_stitching = configparser.ConfigParser(dict_type=collections.OrderedDict)
            config_stitching.read(filepath)
        else:
            config_stitching = configparser.ConfigParser({}, collections.OrderedDict)

        # Select the section
        k_section = '%s.%s.%s' % (k_ed_src, k_ep_src, k_part_src)

        # Add section if not exists
        if not config_stitching.has_section(k_section):
            config_stitching[k_section] = dict()


        # add bgd curves used for stitching
        if shot_no in stitching_curves.keys():
            curves = stitching_curves[shot_no]
            key_str = "%d_curves" % (shot['start'])
            if curves is None or curves['k_curves'] == '':
                # Remove the curves for this shot
                if config_stitching.has_option(k_section, key_str):
                    config_stitching.remove_option(k_section, key_str)
            else:
                # Associate the curves to this shot
                config_stitching.set(k_section, key_str, curves['k_curves'])
        else:
            print("not in modified")

        # Sort the section
        config_stitching[k_section] = collections.OrderedDict(sorted(config_stitching[k_section].items(), key=lambda x: x[0]))

        # Write to the database
        with open(filepath, 'w') as config_file:
            config_stitching.write(config_file)




def parse_stitching_curves_database(db, k_ep:str):

    # Open configuration file
    filepath = os.path.join(db['common']['directories']['curves'], "stitching", "%s_stitching_curves.ini" % (k_ep))
    if filepath.startswith("~/"):
        filepath = os.path.join(PosixPath(Path.home()), filepath[2:])
    if not os.path.exists(filepath):
        print("warning: %s:parse_stitching_curves: %s, %s is missing" % (__name__, k_ep, filepath))
        return

    # Initialize local database
    db_stitching_curves = dict()

    # Parse the file
    config = configparser.ConfigParser()
    config.read(filepath)
    for k_curves in config.sections():
        db_stitching_curves[k_curves] = deepcopy(STITCHING_CURVES_DEFAULT)
        db_stitching_curves[k_curves]['k_curves'] = k_curves
        db_stitching_curves[k_curves]['channels'] = {
            'r': Curve(),
            'g': Curve(),
            'b': Curve(),
        }
        for k_channel in ['r', 'g', 'b']:
            points_str = config.get(k_curves, k_channel).replace(' ', '').strip()
            match = re.match("([r|g|b)=(.*)", points_str)
            groups = match.group(2).split(',')
            db_stitching_curves[k_curves]['channels'][k_channel].remove_all_points()
            for group in groups:
                xy = group.split(':')
                db_stitching_curves[k_curves]['channels'][k_channel].add_point(
                    np.float32(xy[0]),np.float32(xy[1]))

            # db_stitching_curves[k_curves]['points'][k_channel] = list()
            # for point_str in points_str.split(','):
            #     xy = np.fromstring(point_str, dtype=np.float32, count=2, sep=':')
            #     db_stitching_curves[k_curves]['points'][k_channel].append([xy[0], xy[1]])

            # curve = Curve()
            # curve.remove_all_points()
            # for p in curves['points'][k_c]:
            #     curve.add_point(p[0], p[1])

        # print("curve name: %s" % (k_curves))
        # for c in ['r', 'g', 'b']:
        #     print("\t%s" % (c))
        #     points = db_stitching_curves[k_curves]['points'][c]
        #     for p in points:
        #         print("\t ", p)


    return db_stitching_curves



def write_stitching_curves_to_database(db, k_ep:str, curves:dict):
    # Open configuration file
    filepath = os.path.join(db['common']['directories']['curves'], "stitching", "%s_stitching_curves.ini" % (k_ep))
    if filepath.startswith("~/"):
        filepath = os.path.join(PosixPath(Path.home()), filepath[2:])

    if os.path.exists(filepath):
        config_stitching_curves_db = configparser.ConfigParser(dict_type=collections.OrderedDict)
        config_stitching_curves_db.read(filepath)
    else:
        config_stitching_curves_db = configparser.ConfigParser({}, collections.OrderedDict)

    k_curves = curves['k_curves']

    # Update the config file
    k_section = k_curves

    # Create a section if it does not exist
    if not config_stitching_curves_db.has_section(k_section):
        config_stitching_curves_db[k_section] = dict()

    # Modify/Add the points to this section
    for c in ['r', 'g', 'b']:
        for c in ['r', 'g', 'b']:
            points = curves['points'][c]
            matrix_str = ""
            for p_xy in points:
                matrix_str += "%s:%s, " % (
                    np.format_float_positional(p_xy.x()),
                    np.format_float_positional(p_xy.y()))
            config_stitching_curves_db.set(k_curves, c, matrix_str[:-2])

    # Sort the section
    config_stitching_curves_db[k_section] = collections.OrderedDict(sorted(config_stitching_curves_db[k_section].items(), key=lambda x: x[0]))

    # Write to the database
    with open(filepath, 'w') as config_file:
        config_stitching_curves_db.write(config_file)

    return True








# def get_frames_stitching(db, k_ep, k_part) -> dict:
#     """ Returns a dict of stitching parameters for each frame of this k_ep:k_part
#     """
#     frames_stitching = dict()

#     # Get the list of editions and episode that are used by this ep/part
#     if k_part in ['g_debut', 'g_fin']:
#         db_video = db[k_part]['common']['video']
#     else:
#         print("%s.get_frames_stitching: %s:%s" % (__name__, k_ep, k_part))
#         k_ed_src = db[k_ep]['common']['video']['reference']['k_ed']
#         k_ep_src = k_ep
#         db_video = db[k_ep_src][k_ed_src][k_part]['video']
#         print("%s.get_frames_stitching: src=%s:%s:%s" % (__name__, k_ed_src, k_ep_src, k_part))

#     for shot in db_video['shots']:
#         # print(shot)
#         if ('src' not in shot.keys()
#             or ('use' in shot['src'].keys()
#             and not shot['src']['use'])):
#             shot_src = shot
#         else:
#             if 'k_ed' in shot['src'].keys():
#                 k_ed_src = shot['src']['k_ed']
#             k_ep_src = shot['src']['k_ep']
#             k_part_src = get_k_part_from_frame_no(db, k_ed_src, k_ep_src, shot['src']['start'])
#             shot_src = get_shot_from_frame_no_new(db, frame_no=shot['src']['start'], k_ed=k_ed_src, k_ep=k_ep_src, k_part=k_part_src)

#         # pprint(shot_src)
#         if shot_src['stitching'] is not None:
#             frames_stitching.update({shot['no']: shot_src['stitching']['frames']})

#     return frames_stitching

