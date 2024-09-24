from __future__ import annotations
from copy import deepcopy
from pprint import pprint
from import_parsers import *
from utils.mco_types import Scene, Singleton
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from scene.src_scene import SrcScene



class ReplaceDatabase:

    def __init__(self) -> None:
        self._db: dict[str, dict[int, int]] = {}


    @staticmethod
    def _key(src_scene: Scene) -> str:
        # This scene must be a scene which is a src
        key = src_scene['k_ed_ep_ch_no']
        return f"{'.'.join(key[:3])}.{key[-1]:03}"


    def get(self, src_scene: SrcScene, f_no: int, initial: bool=False) -> int:
        scene: Scene = src_scene['scene']
        try:
            if initial:
                return scene['replace'][f_no]
        except:
            pass

        _key = self._key(src_scene)
        try:
            replace_list = self._db[_key]
        except:
            try:
                self._db[_key] = deepcopy(scene['replace'])
            except:
                self._db[_key] = {}
        replace_list = self._db[_key]

        return (
            replace_list[f_no]
            if f_no in replace_list
            else f_no
        )


    def get_replacements(
        self,
        scene: Scene
    ) -> dict[int, dict[int, int]]:
        scene_replace: dict[int, int] = {}
        scene_no: int = scene['no']
        for src_scene in scene['src'].scenes():
            _key = self._key(src_scene)
            if _key in self._db:
                scene_replace.update(self._db[_key])
        return {scene_no: scene_replace}
