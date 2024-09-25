from dataclasses import dataclass, field
from typing import Literal

import numpy as np
from utils.mco_types import Scene
from PySide6.QtGui import (
    QPixmap,
)



@dataclass(slots=True)
class Frame:
    key: str
    i: int
    no: int
    by: int
    img: np.ndarray | None = None
    pixmap: QPixmap | None = None



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
    by: Frame | None


