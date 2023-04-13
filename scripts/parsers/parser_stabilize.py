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
from filters.deshake import verify_stabilize_segments
from parsers.parser_generiques import get_dependencies_for_generique
from utils.pretty_print import *

from utils.common import (
    K_GENERIQUES,
    get_k_part_from_frame_no,
)
from shot.utils import get_shot_from_frame_no
from utils.nested_dict import nested_dict_set

SEGMENTS_MAX_COUNT = 5

# mode, options=
#   - vertical
#   - horizontal
#   - rotation
STABILIZE_MODES = ['vertical', 'horizontal', 'rotation']


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
            shot = get_shot_from_frame_no(db, frame_no=frame_no, k_ed=k_ed, k_ep=k_ep, k_part=k_part)
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
                segment_dict = {
                    'alg': parameters[0],
                    'mode': {
                        'vertical': False,
                        'horizontal': False,
                        'rotation': False
                    }
                }
                for parameter in parameters[1:]:
                    # print_orange("\t%s" % (parameter))
                    k, v = parameter.split('=')
                    if k in ['start', 'end']:
                        nested_dict_set(segment_dict, int(v), k)
                    elif k == 'mode':
                        options = v.split('+')
                        for option in options:
                            if option in STABILIZE_MODES:
                                segment_dict['mode'][option] = True
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
                sys.exit(print_red(f"Error: parse_stabilize_configurations: erroneous parameters:\n\t{filepath}\n\t{k_ed}:{k_ep}:{k_part} shot no. {shot['no']}, frame no. {shot['start']}"))

            if verbose:
                pprint(shot['deshake'])
                # sys.exit()


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
