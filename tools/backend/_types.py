from dataclasses import dataclass, field
from typing import Literal

import numpy as np
from utils.mco_types import (
    ChapterGeometry,
    DetectInnerRectParams,
    Scene,
    SceneGeometry,
)
from PySide6.QtGui import (
    QPixmap,
)


AppType = Literal['replace', 'geometry', 'stabilization']


@dataclass(slots=True)
class TargetSceneGeometry:
    chapter: ChapterGeometry
    scene: SceneGeometry
    is_erroneous: bool = False


@dataclass(slots=True)
class Frame:
    src_scene_key: str
    scene_key: str
    i: int
    no: int
    by: int
    img: np.ndarray | None = None
    pixmap: QPixmap | None = None
    _k_ep_ch_no: tuple[str, str, int] = ("", "", 0)

    def __post_init__(self):
        _k_ep_ch_no: list[str] = self.scene_key.split(':')
        self._k_ep_ch_no = tuple(_k_ep_ch_no[:2] + [int(_k_ep_ch_no[2])])

    @property
    def k_ep_ch_no(self) -> tuple[str, str, str, int]:
        return self._k_ep_ch_no


@dataclass(slots=True)
class PlaylistProperties:
    frame_nos: list[int] = field(default_factory=list)
    count: int = 0
    ticks: list[int] = field(default_factory=list)
    scenes: list[int] = field(default_factory=list)



@dataclass(slots=True)
class Selection:
    k_ep: str = 'ep01'
    k_ch: str = 'g_debut'
    task: str = ''
    scenes: list[Scene] = field(default_factory=list)
    invalid: list[int] = field(default_factory=list)



ReplaceActionType = Literal['replace', 'remove']

@dataclass(slots=True)
class ReplaceAction:
    type: ReplaceActionType
    current: Frame | None
    by: Frame | int | None


GeometryActionType = Literal['select', 'remove', 'set', 'discard']
GeometryActionParameter =  Literal[
    'crop_top',
    'crop_bottom',
    'crop_left',
    'crop_right',
    'width',
    'fit_to_width',
    'keep_ratio',
    'detection',
    'autocrop',
]


@dataclass(slots=True)
class GeometryAction:
    type: GeometryActionType
    parameter: GeometryActionParameter
    value: int | bool | DetectInnerRectParams

