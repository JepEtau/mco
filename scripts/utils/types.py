# -*- coding: utf-8 -*-
from typing import Literal, TypedDict, Union

# Common to all types:
# k_ed: key: editon. 1 letter format in [k, s, f, ..]
# k_ep: key: episode no. format: ep##
# k_part: key: refer to K_ALL_PARTS

# no: shot no.
# start: start frame form 0 to ..
# count: frame count of a part/shot/segment

class GenericSrc(TypedDict):
    k_ed: str
    k_ep: str


class ShotGeometry(TypedDict):
    is_default: bool

class Geometry(TypedDict):
    keep_ratio: bool
    fit_to_width: bool
    crop: list[int]
    is_default: bool
    shot: ShotGeometry


class SrcShot(TypedDict):
    k_ed: str
    k_ep: str
    k_part: str
    no: int
    start: int
    count: int
    segment: list


class Shot(TypedDict):
    # This type decsribes a shot
    # Some variables are not defined in the list of src shots but are set
    # when a shot is copied from src list to the target list.

    k_ed: str
    k_ep: str
    k_part: str

    # Shot no. start frame no. and frame count of this shot
    no: int
    start: int
    count: int

    # Filters: this is the processing chain for this shot. Once consolidated,
    # this variable specifies a list of filters for each frame
    filters: list
    # If specified (i.e. not 'default'), this shot uses another chain defined in the
    # ini file of the edition/episode/part
    filters_id: str
    # This key is used to stop the processing once this task is reached
    last_task: str

    # This structure defines the destination of this shot. It is automatically set
    # when consolidating the shot.
    # This also permits to use a shot from an episode/part to another one
    #   e.g. from 'to_follow' to 'episode' and vice-versa.
    # It is defined only in the 'target' list of shots
    # 2023-06-14: replacement is currently not validated
    dst: dict

    # This struct defines the src shot uses to generate this one.
    # When processing this shot, it uses the k_ed:k_episode:k_part:shot specified by this variable
    # e.g. we can use a shot from another edition if not available in this one
    # if a list of segments has to be specified, they shall use the same episode/part/shot no.
    src: SrcShot

    # RGB curves: name, points and LUT table
    curves: dict

    # list of frames to replace
    replace: dict

    # contains parameters to deshake.
    #   warning: stabilize = deshake. TODO correct this
    deshake: dict

    # geometry applied to this. After consolidation, it contains
    # the width of the dst part.
    geometry: Geometry

    # Video effect: fade in / fade out / loop and fade out
    # historic: only the first effect is used. Do not rembebr why defined as a list...
    effects: list


    # The following variables are set by the script when 'consolidating' the target shot
    # i.e. specifies all variables to generate images

    # struct which define the the input file
    inputs: dict
        # 'progressive' : dict
        #       'filepath' : str
        #       'filepath' : str


    last_step: dict
        # 'hash'
        # 'step_no'
        # 'step_edition' : indicates which is the latest step to generate frames
        #                   used by the video editor

    # path to the file which contains all hashes for this episode
    hash_log_file: str

    # Path the the cache directory for this shot
    cache: str


class Curves(TypedDict):
    # name of the curves to be used
    k_curves: str

    lut: dict
    #   'r': list
    #   'g': list
    #   'b': list
    #   'a': list

class DstShot(TypedDict):
    k_ep: str
    k_part: str


class VideoPart(TypedDict):
    start: int
    end: int # Attention, this is the end+1 frame no.
    count: int

    shots: list[Shot]
    effects: dict

    # default geometry for shots that have not geometry defined
    geometry: Geometry

    # used to sync audio and video: nb of frames to add before this part
    avsync: int

    # Add black frames after this part
    silence: int





# unless specified, timestamps and duration are in ms
class AudioSrc(TypedDict):
    k_ed: str
    k_ep: str


class AudioSegment(TypedDict):
    start: int
    end: int
    duration: int

    avsync: int
    gain: int
    silence: int


class Audio(TypedDict):
    start: int
    end: int
    duration: int

    avsync: int
    silence: int

    fadein: int
    fadeout: int
    fade_alg: Literal['sin', 'cos']

    segments: list[AudioSegment]

    src: AudioSrc
    lang: Literal['fr', 'en']
