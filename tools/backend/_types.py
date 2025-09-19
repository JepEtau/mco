from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Literal, TYPE_CHECKING

import numpy as np
from utils.mco_types import (
    Scene,
)
from PySide6.QtGui import (
    QPixmap,
)

if TYPE_CHECKING:
    from parsers import (
        ChapterGeometry,
        DetectInnerRectParams,
        SceneGeometry,
        DsrPatch,
    )

AppType = Literal['replace', 'geometry', 'deshake']


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
    dsr: list[DsrPatch] = field(default_factory=list)
    warp: Warp = field(default_factory=list)
    img: np.ndarray | None = None
    qimage: QPixmap | None = None
    _k_ep_ch_no: tuple[str, str, int] = ("", "", 0)

    def __post_init__(self):
        _k_ep_ch_no: list[str] = self.scene_key.split(':')
        self._k_ep_ch_no = tuple(_k_ep_ch_no[:2] + [int(_k_ep_ch_no[2])])

    @property
    def k_ep_ch_no(self) -> tuple[str, str, str, int]:
        return self._k_ep_ch_no


@dataclass(slots=True)
class CurrentFrame:
    no: int
    frame: Frame
    original: Frame | None = None


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
    'use_ac',
    'copy_ac_to_crop',
    'multiple'
]


@dataclass(slots=True)
class GeometryAction:
    type: GeometryActionType
    parameter: GeometryActionParameter
    value: int | bool | DetectInnerRectParams | dict



@dataclass(slots=True)
class GeometryPreviewOptions:
    allowed: bool
    final_preview: bool
    width_edition: bool
    crop_edition: bool
    crop_preview: bool
    resize_preview: bool




@dataclass(slots=True)
class DsrProcessParams:
    auto: bool


DsrActionType = Literal['update', 'undo']
@dataclass(slots=True)
class DsrAction:
    type: DsrActionType
    frame: Frame
    regions: list[DsrPatch]


@dataclass(slots=True)
class DsrPreviewOptions:
    final_preview: bool
    edition: bool
    mask: bool


@dataclass(slots=True)
class WarpAction:
    frame: Frame
    enabled: bool
    matcher: Literal['knn', 'bf']
    knn_ratio: int
    max_distance_ratio: float
    ref_frame: Literal['previous', 'next']

