from __future__ import annotations
from dataclasses import dataclass, field
from pprint import pprint
import sys
from typing import Any, Literal, TypedDict, TYPE_CHECKING

import numpy as np

from utils.hash import calc_hash


if TYPE_CHECKING:
    from .images import Images
    from parsers import (
        Chapter,
        ProcessingTask,
        Filter,
        TaskName,
        SceneGeometry,
        ChapterGeometry,
    )
    from nn_inference.threads.t_decoder import VideoStreamInfo
    from scene.src_scene import SrcScenes



class Singleton(type):
    _instances: dict[Any] = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]



@dataclass(slots=True)
class McoFrame:
    no: int
    img: np.ndarray
    scene: Scene = None



class Inputs(TypedDict):
    class Interlaced(TypedDict):
        filepath: str

    class Progressive(TypedDict):
        filepath: str
        cache: str
        enable: bool
        start: int
        count: int
        info: VideoStreamInfo

    interlaced: Interlaced
    progressive: Progressive


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


class ChapterAudio(TypedDict):
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









@dataclass
class AudioTrack:
    chapters: dict[Chapter, ChapterAudio] = field(default_factory=dict)
    lang: Literal['fr', 'en'] = 'en'
    src_ed: str | None = None
    src_ep: str | None = None

    def set_source(self, edition: str, episode: str | None) -> None:
        self.src_ed = edition
        self.src_ep = episode

    def edition(self) -> str | None:
        """Return the edition used to generate the audio track"""
        return self.src_ed

    def episode(self) -> str | None:
        """Return the episode used to generate the audio track"""
        return self.src_ed



class GenericSrc(TypedDict):
    k_ed: str
    k_ep: str





EffectName = Literal[
    'fadein',
    'fadeout',
    'loop',
    'loop_and_fadein',
    'loop_and_fadeout',
    'overlay'
    'watermark',
    'zoom_in',
    'zoom_out',
]


@dataclass
class Effect:
    name: EffectName
    frame_ref: int = 0
    loop: int = 0
    fade: int = 0
    zoom_factor: float = 0
    extra_param: Any | None = None

    def hash(self) -> str:
        params: str = ",".join([
            str(v) for k, v in self.__dict__.items() if k != 'extra_param'
        ])
        _params: str = ""
        if isinstance(self.extra_param, list | tuple):
            _params = ",".join(map(str, self.extra_param))
        elif isinstance(self.extra_param, dict):
            _params = ",".join(f"{k}:{v}" for k, v in self.extra_param.items())
        elif self.extra_param is not None:
            _params = str(self.extra_param)
        params += f",{_params}" if params else ""
        return calc_hash(params)


@dataclass
class Effects(list):
    effects: list[Effect] = field(default_factory=list)

    def do_watermark(self) -> bool:
        for e in self.effects:
            if e.name == 'watermark':
                return True
        return False

    def primary_effect(self) -> Effect | None:
        for e in self.effects:
            if e.name != 'watermark':
                return e
        return None

    # def add(self, effect: Effect) -> None:
    #     self.effects.append(effect)

    def has_effects(self) -> bool:
        if len(self.effects) == 0:
            return False
        for effect in self.effects:
            if effect.fade != 0 or effect.loop != 0:
                return True
        return False

    def has_effect(self, name: EffectName) -> bool:
        for e in self.effects:
            if e.name == name:
                return True
        return False

    def append(self, object: Any) -> None:
        return self.effects.append(object)

    def get_effect(self, name: EffectName) -> Effect | None:
        """Returns the first effect found
        """
        for e in self.effects:
            if e.name == name:
                return e
        return None

    def get_effects(self, name: EffectName):
        """yield avery effect
        """
        for e in self.effects:
            if e.name == name:
                yield e

    def hash(self) -> str:
        if len(self.effects) == 0:
            return ''
        return calc_hash(';'.join(e.hash() for e in self.effects))


class RefScene(TypedDict):
    no: int
    start: int
    count: int


class Scene(TypedDict):
    # This type decsribes a scene
    # Some variables are not defined in the list of src scenes but are set
    # when a scene is copied from src list to the target list.

    k_ed: str
    k_ep: str
    k_chapter: str

    # Scene no. start frame no. and frame count of this scene
    no: int
    start: int
    count: int

    # Filters: this is the processing chain for this scene. Once consolidated,
    # this variable specifies a list of filters for each frame
    filters: dict[TaskName, Filter]
    # If specified (i.e. not 'default'), this scene uses another chain defined in the
    # ini file of the edition/episode/chapter
    filters_id: str

    task: ProcessingTask

    # This structure defines the destination of this scene. It is automatically set
    # when consolidating the scene.
    # This also permits to use a scene from an episode/chapter to another one
    #   e.g. from 'to_follow' to 'episode' and vice-versa.
    # It is defined only in the 'target' list of scenes
    # 2023-06-14: replacement is currently not validated
    dst: dict

    # This struct defines the src scene uses to generate this one.
    # When processing this scene, it uses the k_ed:k_episode:k_chapter:scene specified by this variable
    # e.g. we can use a scene from another edition if not available in this one
    # if a list of segments has to be specified, they shall use the same episode/chapter/scene no.
    src: SrcScenes

    ref: RefScene

    # list of frames to replace
    replace: dict[int, int]

    # contains parameters to deshake.
    #   warning: stabilize = deshake. TODO correct this
    deshake: dict

    # geometry applied to this. After consolidation, it contains
    # the width of the dst chapter.
    geometry: SceneGeometry

    # Video effect: fade in / fade out / loop and fade out
    # historic: only the first effect is used. Do not rembebr why defined as a list...
    effects: Effects


    # The following variables are set by the script when 'consolidating' the target scene
    # i.e. specifies all variables to generate images

    # struct which define the the input file
    inputs: Inputs
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

    # Path of the cache directory for this scene
    cache: str

    # List of unique frames to generate this scene
    # This is usefull to optimize some tasks
    # the generated files have to use this list and replace directory, filenames
    in_frames: Images

    # This list contains the frames used to generate a clip after processing
    out_frames: list[str | int]



class DstScene(TypedDict):
    k_ep: str
    k_chapter: str


class ChapterVideo(TypedDict):
    start: int
    end: int # Attention, this is the end+1 frame no.
    count: int

    scenes: list[Scene]
    effects: Effects

    # default geometry for scenes that have not geometry defined
    geometry: ChapterGeometry

    # used to sync audio and video: nb of frames to add before this chapter
    avsync: int

    # Add black frames after this chapter
    silence: int

    task: ProcessingTask

    k_ed_src: str

    # Episode, chapter: used to avoid too many arguments
    k_ep: str
    k_ch: str



@dataclass
class VideoTrack:
    target: dict[Chapter, ChapterVideo] = field(default_factory=dict)



@dataclass
class Episode:
    audio: AudioTrack
    video: VideoTrack




