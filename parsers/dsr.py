from dataclasses import dataclass, field
from typing import Literal


@dataclass(slots=True)
class PatchDsr:
    shape: Literal['round', 'ellipse', 'rect']
    # x, y
    coordinates: tuple[int, int]
    size: tuple[int, int]



@dataclass(slots=True)
class FrameDsr:
    use_auto: bool = True
    # patches




@dataclass(slots=True)
class SceneDsr:
    auto: bool = True

    _frames: dict[int, FrameDsr] = field(default_factory=dict)

    def get_frame(self, no: int) -> FrameDsr | None:
        if no in self._frames:
            return self._frames[no]
