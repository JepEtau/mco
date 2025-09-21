from __future__ import annotations
from collections import OrderedDict
from configparser import ConfigParser
from copy import deepcopy
from logger import log
import os
from pprint import pprint
from utils.mco_types import Scene
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from scene.src_scene import SrcScene
from parsers import (
    db,
    Warp,
)
from utils.p_print import *



class WarpDatabase:

    def __init__(self) -> None:
        self._db: dict[str, dict[int, int]] = {}
        self.modified_scenes: set[str] = set()
        self.modified_src_scenes: set[str] = set()
        self.history: list = []
        self.history_depth: int = 10


    @staticmethod
    def _key(src_scene: Scene) -> str:
        # This scene must be a scene which is a src
        key = src_scene['k_ed_ep_ch_no']
        return f"{':'.join(key[:3])}:{key[-1]:03}"


    def get(self, src_scene: SrcScene, f_no: int) -> Warp:
        """Returns the frame no. used to warp this frame
        """
        scene: Scene = src_scene.in_scene
        _key = self._key(src_scene)
        try:
            warp_dict = self._db[_key]
        except:
            try:
                self._db[_key] = deepcopy(scene['warp'])
            except:
                self._db[_key] = {}
        warp_dict = self._db[_key]

        return (
            warp_dict[f_no]
            if f_no in warp_dict
            else f_no
        )


    def warps(
        self,
        scene: Scene,
    ) -> dict[int, dict[int, Warp]]:
        """Returns all warpments for this scene
        """
        scene_warp: dict[int, int] = {}
        scene_no: int = scene['no']
        for src_scene in scene['src'].scenes():
            _key = self._key(src_scene)
            if _key in self._db:
                scene_warp.update(self._db[_key])
        return {scene_no: dict(sorted(scene_warp.items()))}


    def get_nb_of_warps(self, scene: Scene) -> int:
        """Returns nb of warps for this scene
        """
        count: int = 0
        for src_scene in scene['src'].scenes():
            _key = self._key(src_scene)
            if _key in self._db:
                count += len(self._db[_key].keys())
            else:
                count += len(src_scene.in_scene['warp'].keys())
        return count


    def _push_to_history(self):
        self.history.append({
            '_db': deepcopy(self._db),
            'modified_src_scenes': deepcopy(self.modified_src_scenes),
            'modified_scenes': deepcopy(self.modified_scenes),
        })
        if len(self.history) > self.history_depth:
            self.history = self.history[1:]


    def modify(
        self,
        scene: Scene,
        src_scene_key: str,
        frame_no: int,
        warp: Warp
    ) -> None:
        self._push_to_history()
        if src_scene_key not in self._db:
            self._db[src_scene_key] = {}
        self._db[src_scene_key][frame_no] = warp
        self.modified_src_scenes.add(src_scene_key)
        self.modified_scenes.add(scene['no'])


    def remove_multiple(self, scene: Scene, frame_nos: list[int]) -> None:
        self._push_to_history()
        for src_scene in scene['src'].scenes():
            src_scene_key = self._key(src_scene)
            if src_scene_key in self._db:
                for f_no in frame_nos:
                    if f_no in self._db[src_scene_key]:
                        del self._db[src_scene_key][f_no]
            self.modified_src_scenes.add(src_scene_key)
        self.modified_scenes.add(scene['no'])


    def is_modified(self, scene: Scene) -> bool:
        if scene['no'] in self.modified_scenes:
            return True
        for src_scene in scene['src'].scenes():
            src_scene_key = self._key(src_scene)
            if src_scene_key in self.modified_src_scenes:
                return True
        return False


    def modified_scene_nos(self) -> list[int]:
        return list(self.modified_scenes)


    def undo(self) -> None:
        if len(self.history) > 0:
            log.info('get previous database')
            previous = self.history[-1]
            self._db = previous['_db']
            self.modified_src_scenes = previous['modified_src_scenes']
            self.modified_scenes = previous['modified_scenes']
            self.history = self.history[:-1]
        else:
            log.info('history is empty')


    def save(self, scene: Scene):
        if not self.is_modified(scene):
            return

        for src_scene in scene['src'].scenes():
            src_scene_key = self._key(src_scene)
            print(f"SRC scene_key: {src_scene_key}", end=' ')
            if src_scene_key not in self.modified_src_scenes:
                print("not modified")
                continue
            print ("to save")

            k_ed, k_ep, k_ch, src_scene_no = src_scene_key.split(':')
            # k = k_ch if k_ch in credit_chapter_keys() else k_ep
            k = k_ep
            warp_fp = os.path.join(
                db['common']['directories']['config'], k, f"{k}_warp.ini"
            )

            # Parse the file
            if os.path.exists(warp_fp):
                config_warp = ConfigParser(dict_type=OrderedDict)
                config_warp.read(warp_fp)
            else:
                config_warp = ConfigParser({}, OrderedDict)

            # Update the config file, select section
            k_section = '.'.join((k_ed, k_ep, k_ch))
            in_scene: Scene = db[k_ep]['video'][k_ed][k_ch]['scenes'][int(src_scene_no)]
            initial_scene_warp = in_scene['warp']

            # Remove warps that are not used anymore
            if initial_scene_warp is not None:
                for f_no in initial_scene_warp.keys():
                    if (
                        config_warp.has_option(k_section, f"{f_no}")
                        and not self._db[src_scene_key].get(f_no)
                    ):
                        print(f"remove: {k_section}: {f_no}")
                        config_warp.remove_option(k_section, f"{f_no}")

            if not config_warp.has_section(k_section):
                config_warp.add_section(k_section)

            # Set new values
            warp: Warp
            for f_no, warp in self._db[src_scene_key].items():
                if warp.enabled:
                    config_warp.set(k_section, f"{f_no}", f"{warp}")

                else:
                    # Remove if disabled
                    if (
                        config_warp.has_option(k_section, f"{f_no}")
                        and not self._db[src_scene_key].get(f_no)
                    ):
                        print(f"remove warp: {k_section}: {f_no}")
                        config_warp.remove_option(k_section, f"{f_no}")

            # Write to the database
            with open(warp_fp, 'w') as config_file:
                config_warp.write(config_file)

            # Remove modified
            in_scene['warp'] = deepcopy(self._db[src_scene_key])
            self.modified_src_scenes.remove(src_scene_key)

        self.modified_scenes.remove(scene['no'])
        self.history.clear()


    def discard(self, scene: Scene):
        if not self.is_modified(scene):
            return

        for src_scene in scene['src'].scenes():
            src_scene_key = self._key(src_scene)
            self._db[src_scene_key] = deepcopy(src_scene.in_scene['warp'])
            self.modified_src_scenes.remove(src_scene_key)

        self.modified_scenes.remove(scene['no'])
        self.history.clear()
