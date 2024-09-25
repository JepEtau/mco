from dataclasses import dataclass, field
from utils.mco_types import Scene



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

