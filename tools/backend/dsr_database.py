from __future__ import annotations
from collections import OrderedDict
from configparser import ConfigParser
from copy import deepcopy
import re
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
    FrameDsr,
    DsrMask,
)



class DsrDatabase:

    def __init__(self) -> None:
        self._db: dict[str, dict[int, int]] = {}
        self.modified_scenes: set[str] = set()
        self.history: list = []
        self.history_depth: int = 10


    @staticmethod
    def _key(src_scene: Scene) -> str:
        # This scene must be a scene which is a src
        key = src_scene['k_ed_ep_ch_no']
        return f"{':'.join(key[:3])}:{key[-1]:03}"


    def initialize(self, selection: Selection) -> None:
        scenes: list[Scene] = selection.scenes
        for scene in scenes:
            self._db[self._key(scene)] = deepcopy(scene['dr'])


    def clear(self) -> None:
        self._db.clear()
        self.modified_scenes.clear()
        self.history.clear()


    def get(self, src_scene: SrcScene, f_no: int, initial: bool=False) -> int:
        scene: Scene = src_scene['scene']
        try:
            if initial:
                return scene['dr'][f_no]
        except:
            pass

        _key = self._key(src_scene)
        try:
            dr_dict = self._db[_key]
        except:
            try:
                self._db[_key] = deepcopy(scene['dr'])
            except:
                self._db[_key] = {}
        dr_dict = self._db[_key]

        return dr_dict[f_no] if f_no in dr_dict else f_no


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
        parameter, value = modification.parameter, modification.value

        self._push_to_history()

        scene_key = self._key(scene)


        # elif parameter == 'keep_ratio':
        #     scene_dsr.keep_ratio = bool(value)

        # elif parameter == 'fit_to_width':
        #     scene_dsr.fit_to_width = bool(value)

        # elif parameter == 'detection':
        #     if modification.type == 'set':
        #         scene_dsr.detection_params = deepcopy(value)
        #         scene_dsr.custom_detection_params = True

        #     elif modification.type == 'discard':
        #         scene_dsr.detection_params = DetectInnerRectParams()
        #         scene_dsr.custom_detection_params = False

        # elif parameter == 'autocrop':
        #     scene_dsr.autocrop = deepcopy(value)

        # elif parameter == 'use_ac':
        #     scene_dsr.use_autocrop = value

        # elif parameter == 'copy_ac_to_crop':
        #     scene_dsr.crop = deepcopy(scene_dsr.autocrop)

        self.modified_scenes.add(scene_key)


    def is_modified(self, scene: Scene) -> bool:
        return bool(self._key(scene) in self.modified_scenes)


    def modified_scene_nos(self) -> list[int]:
        modified: list[int] = []
        for k in self.modified_scenes:
            if result := re.search(re.compile(r":(\d{3})"), k):
               modified.append(int(result.group(1)))
        return modified


    def undo(self) -> None:
        if len(self.history) > 0:
            log.info('get previous database')
            previous = self.history[-1]
            self._db = previous['_db']
            self.modified_scenes = previous['modified_scenes']
            self.history = self.history[:-1]
        else:
            log.info('history is empty')


    def save(self, scene: Scene):
        if not self.is_modified(scene):
            return

        print("modified scenes:", self.modified_scenes)
        k_scene = self._key(scene)
        scene_dsr: FrameDsr = self._db[k_scene]
        k_ch: str = scene['dst']['k_ch']
        k_ep: str = scene['dst']['k_ep']
        k: str = k_ch if k_ch in ('g_debut', 'g_fin') else k_ep
        dsr_fp = os.path.join(
            db['common']['directories']['config'], k, f"{k}_dsr.ini"
        )

        print(dsr_fp)
        pprint(scene_dsr)
        print(f"k_scene: {k_scene}")
        print(f"section: {k_ch}")

        # Parse the file
        if os.path.exists(dsr_fp):
            config_dsr = ConfigParser(dict_type=OrderedDict)
            config_dsr.read(dsr_fp)
        else:
            config_dsr = ConfigParser({}, OrderedDict)

        # Select section
        k_section: str = k_ch
        if not config_dsr.has_section(k_section):
            config_dsr.add_section(k_section)

        # Scene
        if k_scene in self.modified_scenes:
            scene_no: int = scene['no']
            src_scene: Scene = scene['src'].primary_scene()['scene']
            option: str = "_". join((
                f"{scene_no:03}",
                src_scene['k_ed'],
                src_scene['k_ep'],
                src_scene['k_ch'],
                f"{src_scene['no']:03}"
            ))

            # Scene
            if config_dsr.has_option(k_section, option):
                print(f"remove: {k_section}: {option}")
                config_dsr.remove_option(k_section, option)

            values: list[str] = []

            values_str: str = ", ".join(values)
            print(lightgreen(values_str))
            config_dsr.set(k_section, option, values_str)


        # Write to the database
        with open(dsr_fp, 'w') as config_file:
            config_dsr.write(config_file)

        # Remove modified
        if k_scene in self.modified_scenes:
            scene['dr'] = deepcopy(self._db[k_scene])
            self.modified_scenes.remove(k_scene)

        self.history.clear()
        print("done")


    def discard(self, scene: Scene):
        if not self.is_modified(scene):
            return

        k_scene = self._key(scene)
        self._db[k_scene] = deepcopy(scene['dr'])
        self.modified_scenes.remove(k_scene)

        self.history.clear()
