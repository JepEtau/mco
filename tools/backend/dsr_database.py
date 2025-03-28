from __future__ import annotations
from collections import OrderedDict
from configparser import ConfigParser
from copy import deepcopy
import re
import sys
from logger import log
import os
from pprint import pprint

from utils.p_print import lightgreen
from ._types import (
    DsrAction,
    Selection,
)
from utils.mco_types import (
    Scene,
)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from scene.src_scene import SrcScene

from parsers import (
    db,
    SceneDsr,
    DsrRegion,
    credit_chapter_keys,
)



class DsrDatabase:

    def __init__(self) -> None:
        self._db: dict[str, SceneDsr] = {}
        self.modified_scenes: set[str] = set()
        self.modified_src_scenes: set[str] = set()
        self.history: list = []
        self.history_depth: int = 10


    @staticmethod
    def _key(src_scene: Scene) -> str:
        # This scene must be a scene which is a src
        key = src_scene['k_ed_ep_ch_no']
        return f"{':'.join(key[:3])}:{key[-1]:03}"


    # def initialize(self, selection: Selection) -> None:
    #     scenes: list[Scene] = selection.scenes
    #     for scene in scenes:
    #         self._db[self._key(scene)] = deepcopy(scene['dsr'])


    def clear(self) -> None:
        self._db.clear()
        self.modified_scenes.clear()
        self.modified_src_scenes: set[str] = set()
        self.history.clear()


    def get(
        self,
        src_scene: SrcScene,
        f_no: int,
        initial: bool = False
    ) -> list[DsrRegion]:
        scene: Scene = src_scene.in_scene
        try:
            if initial:
                return scene['dsr'].get(f_no)
        except:
            pass

        _key = self._key(src_scene)
        try:
            scene_dsr = self._db[_key]
        except:
            if (
                'dsr' not in scene
                or scene['dsr'] is None
            ):
                return []
            self._db[_key] = deepcopy(scene['dsr'])

        scene_dsr = self._db[_key]
        return scene_dsr.get(f_no)


    def get_scene_dsr(
        self,
        scene: Scene,
    ) -> dict[int, SceneDsr]:
        """Returns all dsr for this scene
        """
        scene_dsr: dict[int, SceneDsr] = {}
        scene_no: int = scene['no']
        for src_scene in scene['src'].scenes():
            _key = self._key(src_scene)
            if _key in self._db:
                scene_dsr.update(self._db[_key].get_all())

        return {scene_no: dict(sorted(scene_dsr.items()))}


    def _push_to_history(self):
        self.history.append({
            '_db': deepcopy(self._db),
            'modified_scenes': deepcopy(self.modified_scenes),
        })
        if len(self.history) > self.history_depth:
            self.history = self.history[1:]


    def update_scene_dsr(
        self,
        scene: Scene,
        modification: DsrAction
    ) -> None:
        self._push_to_history()

        src_scene_key = modification.frame.src_scene_key
        print(lightgreen("modification src scene:"), src_scene_key)
        if src_scene_key not in self._db:
            self._db[src_scene_key] = SceneDsr()

        self._db[src_scene_key].set_regions(
            modification.frame.no,
            modification.regions
        )
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
            dsr_fp = os.path.join(
                db['common']['directories']['config'], k_ep, f"{k_ep}_dsr.ini"
            )

            # Parse the file
            if os.path.exists(dsr_fp):
                config_dsr = ConfigParser(dict_type=OrderedDict)
                config_dsr.read(dsr_fp)
            else:
                config_dsr = ConfigParser({}, OrderedDict)

            # Update the config file, select section
            k_section = '.'.join((k_ed, k_ep, k_ch))
            _src_scene = db[k_ep]['video'][k_ed][k_ch]['scenes'][int(src_scene_no)]
            initial_scene_dsr: SceneDsr = _src_scene['dsr']

             # Remove dsr that are not used anymore
            print("initial frames")
            if initial_scene_dsr is not None:
                for f_no in initial_scene_dsr.get_all().keys():
                    if (
                        config_dsr.has_option(k_section, f"{f_no}")
                        and not self._db[src_scene_key].get(f_no)
                    ):
                        print(f"remove: {k_section}: {f_no}")
                        config_dsr.remove_option(k_section, f"{f_no}")

            # Set new values
            for f_no, regions in self._db[src_scene_key].get_all().items():
                if not regions:
                    continue

                if not config_dsr.has_section(k_section):
                    config_dsr.add_section(k_section)

                scene_regions_str: str = ""
                for region in regions:
                    region_str = f"\n{region.shape} = "
                    region_str += f"{','.join(map(str, (region.center)))}"
                    region_str += f":{','.join(map(str, (region.axes)))}"
                    region_str += f":{region.angle}"

                    scene_regions_str += region_str

                config_dsr.set(k_section, f"{f_no}", scene_regions_str)

            # Write to the database
            with open(dsr_fp, 'w') as config_file:
                config_dsr.write(config_file)


            # Remove modified
            _src_scene['dsr'] = deepcopy(self._db[src_scene_key])
            self.modified_src_scenes.remove(src_scene_key)

        self.modified_scenes.remove(scene['no'])
        self.history.clear()
        print("done")


    def discard(self, scene: Scene):
        if not self.is_modified(scene):
            return

        for src_scene in scene['src'].scenes():
            src_scene_key = self._key(src_scene)
            self._db[src_scene_key] = deepcopy(
                src_scene['scene']['dsr']
            )
            self.modified_src_scenes.remove(src_scene_key)

        self.modified_scenes.remove(scene['no'])
        self.history.clear()
