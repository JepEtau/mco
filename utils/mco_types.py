from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal, TypedDict, TYPE_CHECKING

if TYPE_CHECKING:
    from .images import Images
    from parsers import (
        Chapter,
        ProcessingTask,
        Filter,
        TaskName,
        db
    )
    from nn_inference.threads.t_decoder import VideoStreamInfo

from parsers import (
    db
)
# Common to all types:
# k_ed: key: editon. 1 letter format in [k, s, f, ..]
# k_ep: key: episode no. format: ep##
# k_chapter: key: refer to K_ALL_chapterS

# no: scene no.
# start: start frame form 0 to ..
# count: frame count of a chapter/scene/segment


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


class SceneGeometry(TypedDict):
    is_default: bool


class Geometry(TypedDict):
    keep_ratio: bool
    fit_to_width: bool
    crop: list[int]
    is_default: bool
    scene: SceneGeometry


class SrcScene(TypedDict):
    scene: Scene
    start: int
    count: int
    k_ed_ep_ch_no: tuple[str]


@dataclass
class SrcScenes:
    _scenes: list[SrcScene] = field(default_factory=list)

    def add_scene(
        self,
        k_ed: str,
        k_ep: str,
        k_ch: str,
        no: int,
        start: int,
        count: int
    ) -> None:
        try:
            _scene: Scene = db[k_ep]['video'][k_ed][k_ch]['scenes'][no]
            start = _scene['start'] if start == -1 else start
            count = _scene['count'] if count == -1 else count
        except:
            _scene = None
        self._scenes.append(
            SrcScene(
                scene=_scene,
                start=start,
                count=count,
                k_ed_ep_ch_no=(k_ed, k_ep, k_ch, no)
            )
        )


    def scenes(self) -> list[SrcScene]:
        return self._scenes


    def get_dependencies(self) -> dict[str, set[str]]:
        """returns a dict of ed, ep
        """
        dependencies: dict[str, set[str]] = {}
        for scene in self._scenes:
            k_ed, k_ep = scene['k_ed_ep_ch_no'][:2]
            if k_ed not in dependencies:
                dependencies[k_ed] = set()
            dependencies[k_ed].add(k_ep)
        return dependencies


    def _consolidate_scene(self, src_scene: SrcScene) -> None:
        k_ed, k_ep, k_ch, no = src_scene['k_ed_ep_ch_no']
        _src_scene = db[k_ep]['video'][k_ed][k_ch]['scenes'][no]
        src_scene.update({
            'scene': _src_scene,
            'start': _src_scene['start'] if src_scene['start'] == -1 else src_scene['start'],
            'count': _src_scene['count'] if src_scene['count'] == -1 else src_scene['count'],
        })


    def frame_count(self) -> int:
        count: int = 0
        for src_scene in self._scenes:
            if src_scene['scene'] is None:
                self._consolidate_scene(src_scene)
            count += src_scene['count']
        return count


    def last_frame_no(self) -> int:
        last_scene = self._scenes[-1]
        return last_scene['start'] + last_scene['count'] - 1


    def first_frame_no(self) -> int:
        return self._scenes[0]['start']

    def primary_scene(self) -> SrcScene:
        primary_scene = self._scenes[0]
        if primary_scene['scene'] is None:
            self._consolidate_scene(primary_scene)
        return primary_scene

    def __len__(self) -> int:
        return len(self._scenes)



class RefScene(TypedDict):
    no: int
    start: int
    count: int


@dataclass
class Effect:
    name: Literal['loop', 'fadeout', 'loop_and_fadeout', 'loop_and_fadein', 'watermark']
    frame_ref: int = 0
    loop: int = 0
    fade: int = 0


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
    geometry: Geometry

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
    geometry: Geometry

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




