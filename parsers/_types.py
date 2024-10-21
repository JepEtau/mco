from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, get_args
from ._keys import ep_key


class Db:
    common: dict





TaskName = Literal[
    # Deinterlace the input video:
    'initial',

    # Create a low resolution video for edition only
    # Uses the final video mounting
    # Uses the frames to replace/duplicates to remove, etc.
    # Test purpose only, prefix = lr
    # 00_lr
    'lr',

    # sim:
    # - Use the deinterlaced video
    # - resize to 1080p (1440x1080)
    # - add the effects (overlay)
    #   What is not done:
    #   - NN upscale
    #   - stabilization
    #   - temporal filtering
    #   - color grade
    #   - final crop/resize
    'sim',

    # Upscale and generate a 1080p image for comparison
    'upscale',

    # Create video clips to be stabilized
    'hr',

    # Stabilize video, external tool
    'st',

    # Temporal fix
    #   get the video from stabilized or hr if not stabilized
    #   and apply some temporal filtering
    #     - open tf and compare metadata to st modified date
    #     - apply filter if st changed
    #     - test modified date: hr < st < tf
    'tf',

    # Color grading, external tool
    'cg',

    # Finalize: geometry, fading
    'final'
]

TASK_NAMES: list[str] = get_args(TaskName)

task_to_dirname: dict[TaskName, str] = {
    'initial': '00_initial',
    'lr': '01_lr',
    'upscale': '02_upscaled',
    'hr': '03_hr',
    'final': '05_final',
}

filter_name_to_dirname: dict[str, TaskName] = {
    'initial': 'initial',
    'lr': 'lr',
    'upscale': 'upscaled',
    'hr': 'hr',
    'final': 'final',
}


@dataclass
class ColorSettings:
    colorspace: str = 'bt709'
    color_primaries: str = 'bt709'
    color_trc: str = 'bt709'
    color_range: str = 'limited'



@dataclass
class VideoSettings:
    codec: str
    codec_options: list[str]
    pix_fmt: str
    frame_rate: int
    pad: int = 0
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass
class ProcessingTask:
    name: TaskName
    hash: str = ''
    concat_file: str = ''
    video_file: str = ''
    do_generate: bool = True
    video_settings: VideoSettings | None = None
    in_video_file: str = ''
    fallback_in_video_files: dict[TaskName, str] = field(default_factory=dict)


@dataclass
class Filter:
    sequence: str | list[str] = ''
    hash: str = ''
    # TODO remove
    # id: str | None = None
    task_name: str = ''
    size: tuple[int, int] = ()
    steps: list[Any] = field(default_factory=list)


@dataclass
class OutputSettings:
    audio_format: str = 'wav'
    lang: Literal['fr', 'en'] = 'en'
    verbose: str ='-hide_banner -loglevel warning'
    color_range: str = 'tv'
    color_space: str ='bt709'
    film_tune: str ='-tune grain'
    pixel_format: str ='yuv420p'
    quality: str ='-c:v libx264 -preset slow -crf 15'
    tune: str ='-tune stillimage'


class Singleton(type):
    _instances: dict[Any] = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


@dataclass
class Edition:
    a_files: dict[str, str]
    v_files: dict[str, str]

    def get_audio_file(self, ep: int | str) -> str:
        return self.a_files[ep_key(ep)]

    def get_video_file(self, ep: int | str) -> str:
        return self.a_files[ep_key(ep)]

    def set_audio_file(self, ep: int | str) -> str:
        return self.a_files[ep_key(ep)]

    def set_video_file(self, ep: int | str) -> str:
        return self.a_files[ep_key(ep)]




@dataclass
class Editions:
    editions: dict[str, Edition] = field(default_factory=dict)

    def available(self) -> list[str]:
        return self.editions.keys()

    def register_audio_file(self, edition: str, filepath: str) -> None:
        """Set the input audio file"""
        self.editions[edition].set_audio_file



class Database(
    metaclass=Singleton,

):
    def __init__(self) -> None:
        self._final_size: tuple[int, int]
        self.directories : dict[str, str | Path]
        self.editions: Editions = Editions()
        self.out_settings: OutputSettings = OutputSettings()

    @property
    def final_size(self) -> tuple[int, int]:
        return self._final_size

    @final_size.setter
    def final_size(self, size: tuple[int, int]) -> None:
        self._final_size = size


