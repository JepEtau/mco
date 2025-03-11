import configparser
from enum import IntEnum
import os
from pprint import pprint
import re
import sys
from typing import Literal
from dataclasses import dataclass, field

import cv2
import numpy as np

from ._helpers import get_chapter_video
from ._keys import all_chapter_keys, credit_chapter_keys
from .helpers import nested_dict_set
from utils.mco_types import Scene, ChapterVideo

from .scenes import get_scene_from_frame_no
from ._db import db
from utils.p_print import *
from utils.path_utils import absolute_path


# This node is used to deshake a scene.
# Each scene can be splitted into segments with different params
# This params permits to deshake only for some dimension
# to avoid deshaking traveling
# It has been experimentad that the deshake was sometimes better
# when using the frame in the middle of a scene rather than using the first
# or the last one.
# When the scene is splitted into multiple segments, the transformation
# applied to the last frame is used to wrap the next frame.
#
# BUG: the first frame a segment should be used to align the first frame
#       of the following segment. However, some additionnal params
#       are needed to not apply dx/dy/theta transformation when the
#       modes are different from a segment to the other
#
# TODO: optimize by not looking the keypoints in the duplicated frame
#       but still apply the transformation


StabilizeModeStr = Literal['vertical', 'horizontal', 'translation', 'rotation', 'all']
StabilizeEnhance = Literal['contrast', 'auto', 'none']
StabilizeFrom = Literal['middle', 'start', 'end', 'frame']
StabilizeFeaturesExtractors = Literal['gftt', 'sift']
StabilizeMethod = Literal['cv2_gftt', 'cv2_sift']



class StabilizeMode(IntEnum):
    VERTICAL = 0x1
    HORIZONTAL = 0x2
    TRANSLATION = 0x3
    ROTATION = 0x4
    ALL = 0x7


StabilizeModeStrToMode: dict[StabilizeModeStr, StabilizeMode] = {
    'vertical': StabilizeMode.VERTICAL,
    'horizontal': StabilizeMode.HORIZONTAL,
    'translation': StabilizeMode.TRANSLATION,
    'rotation': StabilizeMode.ROTATION,
    'all': StabilizeMode.ALL,
}



@dataclass(slots=True)
class MotionTracker:
    # Define regions used to track keypoints
    enable: bool = False
    inside: bool = True
    regions: list[np.ndarray] = field(default_factory=list)



@dataclass
class StabilizeSegment:
    start: int = 0
    end: int = 0
    count: int = 0
    start_from: Literal['first', 'last', 'middle', 'frame'] = 'middle'
    ref: int = 0
    mode: StabilizeMode = StabilizeMode.ALL
    extractor: Literal['sift', 'brisk'] = 'sift'
    tracker: MotionTracker = field(default_factory=MotionTracker)
    contrast_threshold: float = 0.04
    edge_threshold: float = 10.
    absolute: bool = False

    enhance: StabilizeEnhance = 'none'

    # To be moved to the variables of the node
    scene_f_no: int = 0



@dataclass(slots=True)
class StabilizeParams:
    enable: bool = False
    segments: list[StabilizeSegment] = field(default_factory=list)
    scene_framecount: int = 0
    # size of borders added before
    borders: int = 24






def verify_stabilize_segments(scene: Scene, segments: list[StabilizeSegment]):
    if len(segments) == 0:
        return True

    # 1st segment
    scene_start: int = scene['src'].first_frame_no()
    scene_end: int = scene_start + scene['dst']['count']
    segment = segments[0]
    if segment.start < scene_start or segment.end >= scene_end:
        # Segment shall fit in scene
        print(red(f"Error: segment [{segment.start}..{segment.end}]is not a part of the scene [{scene_start}..{scene_end}]"))
        return False

    if (
        segment.start_from == 'frame'
        and not (segment.start <= segment.ref <= segment.end)
    ):
        # ref shall be inside segment
        return False

    if len(segments) == 1:
        # Single segment
        return True

    previous_segment = segments[0]
    for segment in segments [1:]:
        if segment.end >= scene_end:
            # Segment shall fit in scene
            return False

        if (
            segment.start_from == 'frame'
            and not (segment.start <= segment.ref <= segment.end)
        ):
            # ref shall be inside segment
            return False

        if previous_segment.start <= segment.start <= previous_segment.end:
            # Segment shall not overlap the previous one
            return False

        previous_segment = segment

    return True


def extract_parameters(parameters_str: str) -> tuple[list, dict]:
    verbose = True
    if verbose:
        print(lightcyan("extract_parameters:"), parameters_str)

    stab_parameters_list = parameters_str.split('=')
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
    tracker = MotionTracker()
    for v in tracker_str.split(','):
        if len(v) == 0:
            continue

        if v == 'enable':
            tracker.enable = True

        elif v == 'inside':
            tracker.inside = True

        elif v == 'outside':
            tracker.inside = False

        elif v.startswith('('):
            point_list = re.findall(re.compile(r"\((\d+)\.(\d+)\)"), v)
            tracker.regions.append(
                list(
                    [int(point[0]), int(point[1])] for point in point_list
                )
            )

    if verbose:
        pprint(tracker)
    return tracker




def parse_stabilize_file(k_ep: str, k_ch: str = '') -> None:
    """The stabilize config file contains the parameters for each dst scene.
    """
    verbose = False
    if verbose:
        print(lightcyan(f"parse_stabilize_configurations for {k_ep}:{k_ch}"))

    # Open configuration file
    k_ep_or_g: str = k_ch if k_ch in credit_chapter_keys() else k_ep
    filepath = absolute_path(
            os.path.join(
            db['common']['directories']['config'],
            k_ep_or_g,
            f"{k_ep_or_g}_stabilize.ini"
        )
    )
    if not os.path.exists(filepath):
        return

    # Parse the file
    config = configparser.ConfigParser()
    config.read(filepath)
    if verbose:
        print(lightgreen(f"parse_stabilize_configurations: {k_ep_or_g}"))

    for _k_ch in config.sections():
        if _k_ch not in all_chapter_keys():
            if verbose:
                print(red(f"stabilization: {_k_ch} is not a valid section name"))
            continue

        chapter_video: ChapterVideo | None = None
        if not (chapter_video := get_chapter_video(k_ep, _k_ch)):
            if verbose:
                print(yellow(f"ignoring: {k_ep}:{_k_ch}"))
            continue

        for scene_ed_str in config.options(_k_ch):
            if verbose:
                print(blue(f"\t{k_ep}:{_k_ch}:{scene_ed_str}"))

            # get frame_no and type(deshake or smooth stabilize)
            scene_ed = scene_ed_str.split('_')
            scene_no: int = int(scene_ed[0])
            k_ed: str = scene_ed[1]

            scene: Scene = chapter_video['scenes'][scene_no]
            if k_ed != scene['src'].primary_scene().in_scene['k_ed']:
                if verbose:
                    print(yellow(f"ignoring scene {scene_no}, k_ed={k_ed}"))
                continue

            # Read and split parameters for this scene
            segments_str = config.get(_k_ch, scene_ed_str)
            for c in ['\r', '\n', ' ', '\t', "\"", "\'"]:
                segments_str = segments_str.replace(c, '')
            if segments_str.endswith(';'):
                segments_str = segments_str[:-1]
            segments = segments_str.split(';')

            if 'stabilize' not in scene:
                scene['stabilize'] = StabilizeParams()
            stabilize: StabilizeParams = scene['stabilize']
            if verbose:
                print(lightblue(segments))

            # first arg is enable
            enabled_args = segments[0].split('=')
            if verbose:
                print(lightblue(enabled_args))
            if enabled_args[0] == 'enable':
                stabilize.enable = True if enabled_args[1] == 'true' else False
            elif verbose:
                print(red("Error: parse_stabilize_configurations: enable value is missing"))

            if verbose:
                pprint(scene['stabilize'])
            # if len(segments) > 2:
            #     sys.exit(print(red("stabilizer: more than 2 segments is not not yet supported")))


            for segment in segments[1:]:
                parameters = segment.split(':')
                segment = StabilizeSegment()
                if verbose:
                    pprint(parameters)
                # stab, stab_parameters = extract_parameters(parameters[0])
                # pprint(stab)
                # pprint(stab_parameters)
                # print("--------")
                # segment.update({
                #     'stab': stab,
                #     stab: stab_parameters,
                # })

                for parameter in parameters:
                    # print(orange("\t%s" % (parameter)))
                    k, v = parameter.split('=')
                    if k in ['start', 'end', 'ref']:
                        segment.__dict__[k] = int(v)

                    elif k == 'mode':
                        options = v.split('+')
                        mode: StabilizeMode = 0
                        for option in options:
                            mode = mode | StabilizeModeStrToMode[option]
                        segment.mode = mode

                    elif k == 'tracker':
                        segment.tracker = parse_tracker(v)

                    elif k in ('static', 'absolute'):
                        segment.absolute =  True if v.lower() == 'true' else False

                    elif k == 'enhance':
                        segment.enhance = v

                    elif k == 'from':
                        segment.start_from = v

                    else:
                        # nested_dict_set(segment, v, k)
                        raise ValueError(red(f"unrecognized: {k}: {v}"))

                if len(stabilize.segments) > 0:
                    # max 2 segments
                    if segment.start < stabilize.segments[0].start:
                        stabilize.segments.insert(0, segment)
                    else:
                        stabilize.segments.append(segment)
                else:
                    # default: append
                    stabilize.segments.append(segment)

            are_segments_valid = verify_stabilize_segments(
                scene=scene, segments=stabilize.segments
            )
            if not are_segments_valid:
                print(red(f"Error: parse_stabilize_configurations: erroneous parameters:\n\t{filepath}\n\t{k_ed}:{k_ep}:{_k_ch} scene no. {scene['no']}, {scene['start']}->{scene['start']+scene['count']}"))
                pprint(stabilize.segments)
                sys.exit()
            if verbose:
                pprint(scene['stabilize'])
                # if k_ed == 'f' and scene['no'] == 23:
                #     sys.exit()


    # if k_ep_or_g == "ep01":
    #     pprint(scene)
    #     sys.exit("parsed")
