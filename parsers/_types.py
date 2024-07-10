from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, get_args
from ._keys import key

TaskName = Literal[
    # Deinterlace the input video:
    #   input: interlaced video
    #   output: progressive video. single file: FFv1 8-bit
    #   out_hash:
    # folder: 00_initial
    # NOT YET SUPPORTED
    'initial',

    # Create a low resolution video for edition only
    # Uses the final video mounting
    # Uses the frames to replace/duplicates to remove, etc.
    # Test purpose only, prefix = lr
    # 00_lr
    'lr',

    # Denoise & upscale:
    # - Identify images to upscale only
    # - Remove outer black borders
    # - upscale
    # - resize to
    #
    #   input: progressive video
    #   output: in 2 steps.
    #       upscaled frames
    'upscale',

    #       create a clip/scene
    #   ??? out_hash: upscale mode
    # 01_hr
    'hr',

    # Upscaled and color grading, external tool
    # Input: clips from upscale: hash?
    # output: FFv1 8 or 16bit
    # 03_restored
    'restored',
    'color',

    # Finalize: temporal filter, geometry, fading
    #   output: all params
    # 04_final
    'final'
]

TASK_NAMES: list[str] = get_args(TaskName)

task_to_dirname: dict[TaskName, str] = {
    'initial': '00_initial',
    'lr': '00_lr',
    'upscale': '01_upscaled',
    'hr': '02_hr',
    'restored': '03_restored',
    'final': '04_final',
}

filter_name_to_dirname: dict[str, TaskName] = {
    'initial': 'initial',
    'lr': 'lr',
    'upscale': 'upscaled',
    'hr': 'hr',
    'restored': 'restored',
    'final': 'final',
}


@dataclass
class VideoSettings:
    codec: str
    codec_options: list[str]
    pix_fmt: str
    frame_rate: int



@dataclass
class ProcessingTask:
    name: TaskName
    hashcode: str = ''
    concat_file: str = ''
    video_file: str = ''
    do_generate: bool = True
    video_settings: VideoSettings | None = None


@dataclass
class Filter:
    sequence: str | list[str] = ''
    hash: str = ''
    # TODO remove
    # id: str | None = None
    task_name: str = ''
    size: tuple[int, int] = ()
    steps: list = field(default_factory=list)


@dataclass
class OutputSettings:
    audio_format: str = 'wav'
    lang: Literal['fr', 'en'] = 'en'
    verbose: str ='-hide_banner -loglevel warning'
    color_range: str = 'tv'
    color_space: str ='bt709'
    film_tune: str ='-tune grain'
    pixel_format: str ='yuv420p'
    quality: str ='-c:v libx264 -preset slow -crf 17'
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
        return self.a_files[key(ep)]

    def get_video_file(self, ep: int | str) -> str:
        return self.a_files[key(ep)]

    def set_audio_file(self, ep: int | str) -> str:
        return self.a_files[key(ep)]

    def set_video_file(self, ep: int | str) -> str:
        return self.a_files[key(ep)]




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


