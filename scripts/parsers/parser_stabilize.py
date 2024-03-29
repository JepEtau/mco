# -*- coding: utf-8 -*-
from copy import deepcopy
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
from img_toolbox.deshake import verify_stabilize_segments
from parsers.parser_generiques import get_dependencies_for_generique
from utils.pretty_print import *

from utils.common import (
    K_GENERIQUES,
    get_k_part_from_frame_no,
)
from shot.utils import get_shot_from_frame_no
from utils.nested_dict import nested_dict_set


# mode, options=
#   - vertical
#   - horizontal
#   - rotation
STABILIZE_MODES = ['vertical', 'horizontal', 'rotation']
STABILIZE_ENHANCEMENTS = ['contrast', 'auto', 'none']
STABILIZE_FROM = ['middle', 'start', 'end', 'frame']
STABILIZE_CV2_FEATURES_EXTRACTORS = ['gftt', 'sift']
STABILIZERS = [
    'cv2_gftt',
    'cv2_sift',
    # 'sk',      not yet implemented, use the same class as cv2
    'ffmpeg',       # not yet implemented
    # 'topaz',      not yet implemented
]

DEFAULT_SEGMENT_VALUES = {
    'start': -1,
    'end': -1,
    'stab': STABILIZERS[0].split('_')[0],
    'from': STABILIZE_FROM[0],  # Start the deshake from the specified frame
    'ref': -1,                  # The initial frame no when starting to deshake
    'static': False,            # If set to True, use the same image to get the initial keypoints for each frame
    'enhance': STABILIZE_ENHANCEMENTS[0],   # Enhance the gray image to identify and compute keypoints
    'mode': {                   # Translation/rotation applied to the image
        'vertical': True,
        'horizontal': True,
        'rotation': True,
    },
    'tracker': {                # Define the regions to identify and compute keypoints
        'enable': False,
        'inside': True,
        'is_hr': True,          # Indicates if coordinates were defined with a highres or lowres image
        'regions': list(),
    },
    'cv2': {'feature_extractor': 'gftt'},
}


EMPTY_SEGMENT_VALUES = {
    # 'start': -1,
    # 'end': -1,
    'stab': STABILIZERS[0].split('_')[0],
    'from': STABILIZE_FROM[0],  # Start the deshake from the specified frame
    'ref': -1,                  # The initial frame no when starting to deshake
    'static': False,            # If set to True, use the same image to get the initial keypoints for each frame
    'enhance': STABILIZE_ENHANCEMENTS[0],   # Enhance the gray image to identify and compute keypoints
    'mode': {                   # Translation/rotation applied to the image
        'vertical': False,
        'horizontal': False,
        'rotation': False,
    },
    'tracker': {                # Define the regions to identify and compute keypoints
        'enable': False,
        'inside': True,
        'is_hr': True,          # Indicates if coordinates were defined with a highres or lowres image
        'regions': list(),
    },
}


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
        print_lightgreen(f"parse_stabilize_configurations: {k_ep_or_g}")
    for k_section in config.sections():
        if '.' not in k_section:
            sys.exit("parse_stabilize_configurations: error, no edition,ep,part specified")
        k_ed, k_ep, k_part = k_section.split('.')

        for frame_no_str in config.options(k_section):
            if verbose:
                print_lightblue(f"\t{k_ed}:{k_ep}:{k_part}:{frame_no_str}")

            # get frame_no and type(deshake or smooth stabilize)
            frame_no_type = re.search(re.compile("(\d+)_(deshake|stabilize)"), frame_no_str)
            if frame_no_type is None:
                sys.exit(red(f"error: frame no. not recognized in file {filepath}, section: {k_section}"))
            frame_no = int(frame_no_type.group(1))
            type_str = frame_no_type.group(2)

            # Get shot from frame no.
            k_part = get_k_part_from_frame_no(db, k_ed, k_ep, frame_no)
            if k_part == '':
                continue
            shot = get_shot_from_frame_no(db, frame_no=frame_no, k_ed=k_ed, k_ep=k_ep, k_part=k_part)
            if verbose:
                if shot is None:
                    print_orange("\twarning, shot not found for frame no. %d in %s:%s:%s" % (
                        frame_no, k_ed, k_ep, k_part))

            if frame_no != shot['start']:
                print_orange(f"warning: parse stabilize configuration:", end=' ')
                print(f"{frame_no} is not the start of {k_ed}:{k_ep}:{k_part}, no. {shot['no']:03}, {shot['start']}")



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
                segment_dict = deepcopy(EMPTY_SEGMENT_VALUES)

                stab, stab_parameters = parse_stab_parameters(parameters[0])
                segment_dict.update({
                    'stab': stab,
                    stab: stab_parameters,
                })

                for parameter in parameters[1:]:
                    # print_orange("\t%s" % (parameter))
                    k, v = parameter.split('=')
                    if k in ['start', 'end', 'ref']:
                        nested_dict_set(segment_dict, int(v), k)
                    elif k == 'mode':
                        options = v.split('+')
                        for option in options:
                            if option in STABILIZE_MODES:
                                segment_dict['mode'][option] = True
                    elif k == 'tracker':
                        nested_dict_set(segment_dict, parse_tracker(v), 'tracker')
                    elif k == 'static':
                        nested_dict_set(segment_dict, True if v.lower() == 'true' else False, k)
                    elif k == 'enhance':
                        if v in STABILIZE_ENHANCEMENTS:
                            nested_dict_set(segment_dict, v, k)
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

            are_segments_valid = verify_stabilize_segments(shot=shot, segments=shot_segments)
            if not are_segments_valid:
                print_red(f"Error: parse_stabilize_configurations: erroneous parameters:\n\t{filepath}\n\t{k_ed}:{k_ep}:{k_part} shot no. {shot['no']}, {shot['start']}->{shot['start']+shot['count']}")
                pprint(shot_segments)
                sys.exit()
            if verbose:
                pprint(shot['deshake'])
                # if k_ed == 'f' and shot['no'] == 23:
                #     sys.exit()


def parse_stab_parameters(stab_parameters_str:str):
    verbose = False
    if verbose:
        print(lightcyan("parse_stab_parameters:"), stab_parameters_str)

    stab_parameters_list = stab_parameters_str.split('=')
    stab = stab_parameters_list[0]

    parameters_dict = dict()
    if stab == 'cv2':
        try:
            parameters = stab_parameters_list[1].split(',')
            feature_extractor = parameters[0]
        except:
            feature_extractor = 'gftt'

        parameters_dict['feature_extractor'] = feature_extractor
        # if parameters[0] == 'gftt':
        #     # todo: add custom settings:
        #     #   max_corners
        #     #   quality_level
        #     #   min_distance
        #     #   block_size
        # elif parameters[0] == 'sirf':
        #     # todo: add custom settings:
        #     #   contrast_threshold
        #     #   edge_threshold

    if verbose:
        pprint(parameters_dict)

    return stab, parameters_dict




def parse_tracker(tracker_str:str):
    verbose = False
    if verbose:
        print(lightcyan("parse_tracker:"), tracker_str)
    tracker = {
        'is_hr': True,
        'enable': False,
        'inside': True,
        'regions': list(),
    }
    for v in tracker_str.split(','):
        if len(v) == 0:
            continue

        if v == 'enable':
            tracker['enable'] = True
        elif v == 'lr':
            tracker['is_hr'] = False
        elif v == 'hr':
            tracker['is_hr'] = True
        elif v == 'inside':
            tracker['inside'] = True
        elif v == 'outside':
            tracker['inside'] = False
        elif v.startswith('('):
            point_list = re.findall(re.compile("\((\d+)\.(\d+)\)"), v)
            tracker['regions'].append(list([int(point[0]), int(point[1])] for point in point_list))

    if verbose:
        pprint(tracker)
    return tracker




def get_initial_shot_stabilize_settings(db, k_ep, k_part) -> dict:
    verbose = False
    if verbose:
        print_lightgreen(f"get_shot_stabilization: {k_ep}:{k_part}")
    stabilization_dict = dict()


    if k_part in K_GENERIQUES:
        dependencies = get_dependencies_for_generique(db, k_part_g=k_part)
        if verbose:
            print_lightgrey(f"\tdependencies: {dependencies}")

        for k_ed_src in dependencies.keys():
            for k_ep_src in dependencies[k_ed_src]:
                try: db_video = db[k_ep_src]['video'][k_ed_src][k_part]
                except: continue

                if 'shots' not in db_video.keys():
                    continue
                for shot in db_video['shots']:
                    shot_start = shot['start']
                    try:
                        if shot['deshake'] is not None:
                            nested_dict_set(stabilization_dict, shot['deshake'],
                                k_ed_src, k_ep_src, k_part, shot_start)
                    except:
                        continue
    else:
        dependencies = db['editions']['available']
        if verbose:
            print_lightgrey(f"\tdependencies: {dependencies}")

        for k_ed_src in dependencies:
            try: db_video = db[k_ep]['video'][k_ed_src][k_part]
            except: continue

            if 'shots' not in db_video.keys():
                continue
            for shot in db_video['shots']:
                shot_start = shot['start']
                try:
                    if shot['deshake'] is not None:
                        nested_dict_set(stabilization_dict, shot['deshake'],
                            k_ed_src, k_ep, k_part, shot_start)
                except:
                    continue
    return stabilization_dict
