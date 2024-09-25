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
        return f"{':'.join(key[:3])}:{key[-1]:03}"


    def get(self, src_scene: SrcScene, f_no: int, initial: bool=False) -> int:
        scene: Scene = src_scene['scene']
        try:
            if initial:
                return scene['replace'][f_no]
        except:
            pass

        _key = self._key(src_scene)
        try:
            replace_dict = self._db[_key]
        except:
            try:
                self._db[_key] = deepcopy(scene['replace'])
            except:
                self._db[_key] = {}
        replace_dict = self._db[_key]

        return (
            replace_dict[f_no]
            if f_no in replace_dict
            else f_no
        )


    def get_replacements(
        self,
        scene: Scene,
    ) -> dict[int, dict[int, int]]:
        scene_replace: dict[int, int] = {}
        scene_no: int = scene['no']
        for src_scene in scene['src'].scenes():
            _key = self._key(src_scene)
            if _key in self._db:
                scene_replace.update(self._db[_key])
        return {scene_no: dict(sorted(scene_replace.items()))}


    def add(
            self,
            scene_key: str,
            current: int,
            by: int
    ) -> None:
        replace_dict = self._db[scene_key]
        replace_dict[current] = by


    def remove_multiple(self, scene: Scene, frame_nos: list[int]) -> None:
        print(f"remove multiple: {frame_nos}")
        # replace_dict = self._db[scene_key]
        # del replace_dict[current]
        # pprint(self._db)
        for src_scene in scene['src'].scenes():
            _key = self._key(src_scene)
            if _key in self._db:
                for f_no in frame_nos:
                    if f_no in self._db[_key]:
                        del self._db[_key][f_no]
        # print("->")
        # pprint(self._db)
