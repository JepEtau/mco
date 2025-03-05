from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Literal
from .hash import calc_hash


EffectName = Literal[
    'fadein',
    'fadeout',
    'loop',
    'loop_and_fadein',
    'loop_and_fadeout',
    'overlay'
    'watermark',
    'zoom_in',
    'zoom_out',
    # Extend by looping on 1st/last frame: used by doc
    'se_loop',
    'title',
    'decimate',
    'decimate_2',
    'replace_by_loop',
]



@dataclass
class Effect:
    name: EffectName
    f_ref: int = 0
    start: int = 0
    loop: int = 0
    fade: int = 0
    zoom_factor: float = 0
    extra_param: Any | None = None

    def hash(self) -> str:
        params: str = ",".join([
            str(v) for k, v in self.__dict__.items() if k != 'extra_param'
        ])
        _params: str = ""
        if isinstance(self.extra_param, list | tuple):
            _params = ",".join(map(str, self.extra_param))
        elif isinstance(self.extra_param, dict):
            _params = ",".join(f"{k}:{v}" for k, v in self.extra_param.items())
        elif self.extra_param is not None:
            _params = str(self.extra_param)
        params += f",{_params}" if params else ""
        return calc_hash(params)



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


    def has_effects(self) -> bool:
        for effect in self.effects:
            if effect.fade != 0 or effect.loop != 0:
                return True
        return False


    def has_effect(self, name: EffectName) -> bool:
        if self.effects is None or len(self.effects) == 0:
            return False

        for e in self.effects:
            if e.name == name:
                return True
        return False


    def append(self, object: Any) -> None:
        return self.effects.append(object)


    def get_effect(self, name: EffectName) -> Effect | None:
        """Returns the first effect found
        """
        for e in self.effects:
            if e.name == name:
                return e
        return None


    def get_effects(self, name: EffectName):
        """yield every effect
        """
        for e in self.effects:
            if e.name == name:
                yield e


    def hash(self) -> str:
        if len(self.effects) == 0:
            return ''
        return calc_hash(';'.join(e.hash() for e in self.effects))


    def remove_effect(self, name: EffectName) -> None:
        """Returns the first effect found
        """
        for i, e in enumerate(self.effects):
            if e.name == name:
                del self.effects[i]
                break
