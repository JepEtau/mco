# -*- coding: utf-8 -*-
import sys

import configparser
import os
import os.path
from pathlib import (
    Path,
    PosixPath,
)
import re
from pprint import pprint

from utils.common import (
    K_GENERIQUES,
    get_k_part_from_frame_no,
    get_shot_from_frame_no_new,
)

# cv2.goodFeaturesToTrack
STABILIZATION_SHOT_PARAMETERS_DEFAULT = {
    'start': -1,
    'end': -1,
    'ref': -1,
    'max_corners': 0,
    'quality_level': 0.01,
    'min_distance': 7,
    'block_size': 7,
    'delta_interval': [0, 0, 0, 0],
    'is_enabled': False,
    'is_default': True,
}

STABILIZATION_SHOT_PARAMETERS_KEYS = [
    'start',
    'end',
    'ref',
    'max_corners',
    'quality_level',
    'min_distance',
    'block_size',
    'is_enabled',
]

def parse_stabilize_configurations(db, k_ep_or_g:str, parse_parameters=False):
    # Open configuration file
    filepath = os.path.join(db['common']['directories']['config'], k_ep_or_g, "%s_stabilize.ini" % (k_ep_or_g))
    if filepath.startswith("~/"):
        filepath = os.path.join(PosixPath(Path.home()), filepath[2:])
    if not os.path.exists(filepath):
        # print("warning: %s does not exists" % (filepath))
        return

    # Parse the file
    config = configparser.ConfigParser()
    config.read(filepath)
    # print("%s.parse_stabilize_configurations: %s" % (__name__, k_ep_or_g))
    for k_section in config.sections():
        if '.' not in k_section:
            sys.exit("parse_stabilize_configurations: error, no edition,ep,part specified")
        k_ed, k_ep, k_part = k_section.split('.')

        for frame_no_str in config.options(k_section):

            # get frame_no and type
            frame_no_type = re.search(re.compile("(\d+)([_a-z]*)"), frame_no_str)
            if frame_no_type is None:
                continue
            type_str = frame_no_type.group(2)
            if type_str == '_parameters' and not parse_parameters:
                continue
            frame_no = int(frame_no_type.group(1))


            k_part = get_k_part_from_frame_no(db, k_ed, k_ep, frame_no)
            shot = get_shot_from_frame_no_new(db, frame_no=frame_no, k_ed=k_ed, k_ep=k_ep, k_part=k_part)
            if shot is None:
                sys.exit("parse_stabilize_configurations: error, shot not found for frame no. %d in %s:%s:%s" % (
                    frame_no, k_ed, k_ep, k_part))

            if type_str == '_parameters' and parse_parameters:
                # Parameters to generate the translation for each frame:
                #  These parameters correspond to the arguments of the cv2.goodFeaturesToTrack function

                # 1 line = 1 segment , used when multiple stabilizations in this shot
                if 'stabilization' not in shot.keys():
                    shot['stabilization'] = dict()
                if 'parameters' not in shot['stabilization'].keys():
                    shot['stabilization']['parameters'] = []

                settings_array_str = config.get(k_section, frame_no_str).split('\n')
                for settings_str in settings_array_str:
                    settings_str_array = settings_str.replace (' ', '').split(',')
                    if settings_str_array[0] == '':
                        continue

                    # Append a new segment
                    shot['stabilization']['parameters'].append(dict())
                    current_segment = shot['stabilization']['parameters'][-1]

                    for settings_str in settings_str_array:
                        properties = settings_str.split('=')

                        if properties[0] == 'segment':
                            # start, end, ref
                            segment_array_str = properties[1].split(':')
                            segment_array = list(map(int, segment_array_str))
                            current_segment.update({
                                'start': segment_array[0],
                                'end': segment_array[1],
                                'ref': segment_array[2],
                            })
                            if segment_array[0] == -1:
                                current_segment['start'] = shot['start']
                            if segment_array[1] == -1:
                                current_segment['end'] = shot['end']
                            if segment_array[2] == -1:
                                current_segment['ref'] = shot['start'] + int(shot['count'] / 2)

                        elif properties[0] == 'ref_points':
                            max_corners_str, quality_level_str, min_distance_str, block_size_str = properties[1].split(':')
                            current_segment.update({
                                'max_corners': int(max_corners_str),
                                'quality_level': float(quality_level_str),
                                'min_distance': int(min_distance_str),
                                'block_size': int(block_size_str),
                            })

                        elif properties[0] == 'delta_interval':
                            # dx_min_str, dx_max_str, dy_min_str, dy_max_str
                            delta_interval_str = properties[1].split(':')
                            current_segment['delta_interval'] = list(map(int, delta_interval_str))

                    current_segment['is_enabled']  = True

            elif type_str in ['_roi', '_crop']:
                array_str = config.get(k_section, frame_no_str).split(':')
                shot['stabilization'][type_str[1:]] = list(map(int, array_str))

            else:
                if 'stabilization' not in shot.keys():
                    shot['stabilization'] = dict()
                if 'frames' not in shot['stabilization'].keys():
                    shot['stabilization']['frames'] = dict()
                # dx, dy
                dx_dy_str = config.get(k_section, frame_no_str).split(':')
                shot['stabilization']['frames'][frame_no] = list(map(float, dx_dy_str))

    # pprint(shot)
    # sys.exit()



def get_shots_stabilize_parameters(db, k_ep, k_part) -> dict:
    """ Returns a dict of stabilization parameters for each shot of this k_ep:k_part
    """
    shots_stabilize_parameters = dict()

    # Get the list of editions and episode that are used by this ep/part
    if k_part in K_GENERIQUES:
        db_video = db[k_part]['target']['video']
    else:
        # print("%s.get_shots_stabilize_parameters: %s:%s" % (__name__, k_ep, k_part))
        k_ed_src = db[k_ep]['target']['video']['src']['k_ed']
        k_ep_src = k_ep
        db_video = db[k_ep_src][k_ed_src][k_part]['video']
        # print("%s.get_shots_stabilize_parameters: src=%s:%s:%s" % (__name__, k_ed_src, k_ep_src, k_part))

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
        # if 'stabilization' not in shot_src.keys():
        #     shot_src['stabilization'] = {'frames': dict()}
        # if 'parameters' not in shot_src['stabilization'].keys():
        #     shot_src['stabilization']['parameters'] = [deepcopy(STABILIZATION_SHOT_PARAMETERS_DEFAULT)]
        #     if len(shot_src['stabilization']['frames'].keys()) > 0:
        #         sys.exit("Error: %s:%s: At least one frame has stabilization but no parameters are defined" % (k_ep, k_part))
        #         shot_src['stabilization']['parameters'][0]['is_enabled'] = True

        if 'stabilization' in shot_src.keys():
            if 'frames' in shot['stabilization'].keys():
                for p in shot['stabilization']['parameters']:
                    p['is_processed'] = True
            else:
                for p in shot['stabilization']['parameters']:
                    p['is_processed'] = False

            shots_stabilize_parameters[shot['no']] = shot_src['stabilization']['parameters']

    return shots_stabilize_parameters



def get_frames_stabilize(db, k_ep, k_part) -> dict:
    """ Returns a dict of transformation parameters for each frame of this k_ep:k_part
    """
    frames_stabilize = dict()

    # Get the list of editions and episode that are used by this ep/part
    if k_part in K_GENERIQUES:
        db_video = db[k_part]['target']['video']
    else:
        # print("%s.get_frames_stabilize: src=%s:%s:%s" % (__name__, k_ed_src, k_ep_src, k_part))
        k_ed_src = db[k_ep]['target']['video']['src']['k_ed']
        k_ep_src = k_ep
        db_video = db[k_ep_src][k_ed_src][k_part]['video']

    for shot in db_video['shots']:
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

        if ('stabilization' in shot_src.keys() and 'frames' in shot_src['stabilization'].keys()):
            frames_stabilize.update({shot['no']: shot_src['stabilization']['frames']})

    return frames_stabilize

