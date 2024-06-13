from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal, TypedDict, TYPE_CHECKING

if TYPE_CHECKING:
    from parsers import (
        Chapter,
        ProcessingTask,
    )

# Common to all types:
# k_ed: key: editon. 1 letter format in [k, s, f, ..]
# k_ep: key: episode no. format: ep##
# k_chapter: key: refer to K_ALL_chapterS

# no: scene no.
# start: start frame form 0 to ..
# count: frame count of a chapter/scene/segment



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


class SceneGeometry(TypedDict):
    is_default: bool


class Geometry(TypedDict):
    keep_ratio: bool
    fit_to_width: bool
    crop: list[int]
    is_default: bool
    scene: SceneGeometry


class SceneSrc(TypedDict):
    k_ed: str
    k_ep: str
    k_chapter: str
    no: int
    start: int
    count: int
    segment: list


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
    filters: list
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
    src: SceneSrc

    # list of frames to replace
    replace: dict

    # contains parameters to deshake.
    #   warning: stabilize = deshake. TODO correct this
    deshake: dict

    # geometry applied to this. After consolidation, it contains
    # the width of the dst chapter.
    geometry: Geometry

    # Video effect: fade in / fade out / loop and fade out
    # historic: only the first effect is used. Do not rembebr why defined as a list...
    effects: list


    # The following variables are set by the script when 'consolidating' the target scene
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

    # Path the the cache directory for this scene
    cache: str


class DstScene(TypedDict):
    k_ep: str
    k_chapter: str


class VideoChapter(TypedDict):
    start: int
    end: int # Attention, this is the end+1 frame no.
    count: int

    scenes: list[Scene]
    effects: dict

    # default geometry for scenes that have not geometry defined
    geometry: Geometry

    # used to sync audio and video: nb of frames to add before this chapter
    avsync: int

    # Add black frames after this chapter
    silence: int


@dataclass
class VideoTrack:
    target: dict[Chapter, VideoChapter] = field(default_factory=dict)






@dataclass
class Episode:
    audio: AudioTrack
    video: VideoTrack




