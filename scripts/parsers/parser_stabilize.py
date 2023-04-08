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
from utils.pretty_print import *

from utils.common import (
    K_GENERIQUES,
    get_k_part_from_frame_no,
    get_src_shot_from_frame_no,
    nested_dict_set,
)

# cv2.goodFeaturesToTrack
STABILIZE_SHOT_PARAMETERS_DEFAULT = {
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

STABILIZE_SHOT_PARAMETERS_KEYS = [
    'start',
    'end',
    'ref',
    'max_corners',
    'quality_level',
    'min_distance',
    'block_size',
    'is_enabled',
]

def parse_stabilize_configurations(db, k_ep_or_g:str):
    verbose = False

    # Open configuration file
    filepath = os.path.join(db['common']['directories']['config'], k_ep_or_g, "%s_stabilize.ini" % (k_ep_or_g))
    if filepath.startswith("~/"):
        filepath = os.path.join(PosixPath(Path.home()), filepath[2:])
    if not os.path.exists(filepath):
        # print("warning: %s does not exist" % (filepath))
        return

    # Parse the file
    config = configparser.ConfigParser()
    config.read(filepath)
    if verbose:
        print_lightgreen("%s.parse_stabilize_configurations: %s" % (__name__, k_ep_or_g))
    for k_section in config.sections():
        if '.' not in k_section:
            sys.exit("parse_stabilize_configurations: error, no edition,ep,part specified")
        k_ed, k_ep, k_part = k_section.split('.')

        for frame_no_str in config.options(k_section):
            if verbose:
                print_lightblue("\t%s:%s:%s: %s" % (k_ed, k_ep, k_part, frame_no_str))

            # get frame_no and type(deshake or smooth stabilize)
            frame_no_type = re.search(re.compile("(\d+)_(deshake|stabilize)"), frame_no_str)
            if frame_no_type is None:
                sys.exit(print_red("error: frame no. not recognized in file %s, section: %s" % (filepath, k_section)))
            frame_no = int(frame_no_type.group(1))
            type_str = frame_no_type.group(2)

            # Get shot from frame no.
            k_part = get_k_part_from_frame_no(db, k_ed, k_ep, frame_no)
            if k_part == '':
                continue
            shot = get_src_shot_from_frame_no(db, frame_no=frame_no, k_ed=k_ed, k_ep=k_ep, k_part=k_part)
            if verbose:
                if shot is None:
                    print_orange("\twarning, shot not found for frame no. %d in %s:%s:%s" % (
                        frame_no, k_ed, k_ep, k_part))

            # Read and split parameters for this shot
            segments_str = config.get(k_section, frame_no_str)
            for c in ['\r', '\n', ' ', '\t', "\"", "\'"]:
                segments_str = segments_str.replace(c, '')
            if segments_str.endswith(';'):
                segments_str = segments_str[:-1]
            segments = segments_str.split(';')

            shot[type_str] = dict()

            if verbose:
                print_lightblue(segments)

            # first arg is enable
            enabled_args = segments[0].split('=')
            if verbose:
                print_lightblue(enabled_args)
            if enabled_args[0] == 'enable':
                if enabled_args[1] == 'true':
                    shot[type_str]['enable'] = True
                elif enabled_args[1] == 'false':
                    shot[type_str]['enable'] = False
                else:
                    print_red("Error: parse_stabilize_configurations: erroneus enable value: %s" % (enabled_args[1]))
                    shot[type_str]['enable'] = False
            else:
                print_red("Error: parse_stabilize_configurations: enable value is missing")

            if verbose:
                pprint(shot['deshake'])
            # if len(segments) > 2:
            #     sys.exit(print_red("stabilizer: more than 2 segments is not not yet supported"))

            # For each segment, get parameters
            nested_dict_set(shot[type_str], list(), 'segments')
            shot_segments = shot[type_str]['segments']

            for segment in segments[1:]:
                parameters = segment.split(':')
                segment_dict = {'alg': parameters[0]}
                for parameter in parameters[1:]:
                    # print_orange("\t%s" % (parameter))
                    k, v = parameter.split('=')
                    if k in ['start', 'end']:
                        nested_dict_set(segment_dict, int(v), k)
                    else:
                        nested_dict_set(segment_dict, v, k)

                if len(shot_segments) > 0:
                    # max 2 segments
                    if segment_dict['start'] < shot_segments[0]['start']:
                        shot_segments.insert(0, segment_dict)
                    else:
                        shot_segments.append(segment_dict)
                else:
                    # default: append
                    shot_segments.append(segment_dict)

            if verbose:
                pprint(shot['deshake'])
                # sys.exit()


def get_shots_stabilize_parameters(db, k_ep, k_part) -> dict:
    """ Returns a dict of stabilize parameters for each shot of this k_ep:k_part
    """
    shots_stabilize_parameters = dict()
    print_red("TODO: rework this")
    return shots_stabilize_parameters

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
        # if 'stabilize' not in shot_src.keys():
        #     shot_src['stabilize'] = {'frames': dict()}
        # if 'parameters' not in shot_src['stabilize'].keys():
        #     shot_src['stabilize']['parameters'] = [deepcopy(STABILIZE_SHOT_PARAMETERS_DEFAULT)]
        #     if len(shot_src['stabilize']['frames'].keys()) > 0:
        #         sys.exit("Error: %s:%s: At least one frame has stabilize but no parameters are defined" % (k_ep, k_part))
        #         shot_src['stabilize']['parameters'][0]['is_enabled'] = True

        if 'stabilize' in shot_src.keys():
            if 'frames' in shot['stabilize'].keys():
                for p in shot['stabilize']['parameters']:
                    p['is_processed'] = True
            else:
                for p in shot['stabilize']['parameters']:
                    p['is_processed'] = False

            shots_stabilize_parameters[shot['no']] = shot_src['stabilize']['parameters']

    return shots_stabilize_parameters



def get_frames_stabilize(db, k_ep, k_part) -> dict:
    """ Returns a dict of transformation parameters for each frame of this k_ep:k_part
    """
    frames_stabilize = dict()
    print_red("TODO: rework this")
    return frames_stabilize

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

        if ('stabilize' in shot_src.keys() and 'frames' in shot_src['stabilize'].keys()):
            frames_stabilize.update({shot['no']: shot_src['stabilize']['frames']})

    return frames_stabilize

