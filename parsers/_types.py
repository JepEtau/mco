from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal
from ._keys import key


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


