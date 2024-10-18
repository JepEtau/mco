from __future__ import annotations
from collections import OrderedDict
from configparser import ConfigParser
from copy import copy, deepcopy
import re
import sys
from logger import log
import os
from pprint import pprint

from utils.p_print import lightgreen
from ._types import (
    Selection,
)
from utils.mco_types import (
    Scene,
    ChapterVideo,
)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from scene.src_scene import SrcScene

from parsers import (
    Chapter,
    credit_chapter_keys,
    db,
)



class DeshakeDatabase:

    def __init__(self) -> None:
        self._db: dict[str, dict[int, int]] = {}
        self.modified_scenes: set[str] = set()
        self.history: list = []
        self.history_depth: int = 10


    @staticmethod
    def _key(scene: Scene) -> str:
        k_ep_dst: str = scene['dst']['k_ep']
        return f"{k_ep_dst if k_ep_dst else 'ep00'}:{scene['dst']['k_ch']}:{scene['no']:03}"


    @staticmethod
    def _chapter_key(scene: Scene) -> str:
        k_ep: str = scene['dst']['k_ep']
        k_ch: str = scene['dst']['k_ch']
        if k_ch not in ('g_debut', 'g_fin'):
            return ':'.join((k_ep, k_ch.replace('g_', '')))
        return k_ch


    def initialize(self, selection: Selection) -> None:
        scenes: list[Scene] = selection.scenes
        for scene in scenes:
            # Use the primary scene to avoid conflicts between
            # scenes which share the same scene as source
            # src_scene = scene['src'].primary_scene()
            # src_scene_key: str = self._key(src_scene)
            # if src_scene_key not in self._db:
            #     if 'deshake' in src_scene['scene']:
            #     else:
            #         self._db[src_scene_key] = SceneDeshake()
            self._db[self._key(scene)] = deepcopy(scene['deshake'])

        k_ep, k_ch = selection.k_ep, selection.k_ch

        # TODO: verify this for g_asuivre and g_documentaire
        chapter: ChapterVideo
        k_ch_key: str = self._chapter_key(scenes[0])
        if k_ch in ('g_debut', 'g_fin'):
            chapter = db[k_ch]['video']
        else:
            chapter = db[k_ep]['video']['target'][k_ch]
        pprint(chapter)
        self._db[k_ch_key] = deepcopy(chapter['deshake'])


    def clear(self) -> None:
        self._db.clear()
        self.modified_scenes.clear()
        self.history.clear()


    def get(self, src_scene: SrcScene, f_no: int, initial: bool=False) -> int:
        scene: Scene = src_scene['scene']
        try:
            if initial:
                return scene['deshake'][f_no]
        except:
            pass

        _key = self._key(src_scene)
        try:
            deshake_dict = self._db[_key]
        except:
            try:
                self._db[_key] = deepcopy(scene['deshake'])
            except:
                self._db[_key] = {}
        deshake_dict = self._db[_key]

        return (
            deshake_dict[f_no]
            if f_no in deshake_dict
            else f_no
        )


    def get_deshake(self, scene: Scene) -> dict[int, TargetSceneDeshake]:
        scene_key: str = self._key(scene)
        return {
            scene_key: TargetSceneDeshake(
                chapter=self._db[self._chapter_key(scene)],
                scene=self._db[scene_key]
            )
        }


    def get_scene_deshake(self, scene: Scene) -> SceneDeshake:
        return self._db[self._key(scene)]


    def _push_to_history(self):
        self.history.append({
            '_db': deepcopy(self._db),
            'modified_scenes': deepcopy(self.modified_scenes),
        })
        if len(self.history) > self.history_depth:
            self.history = self.history[1:]


    def update_scene_deshake(
        self,
        scene: Scene,
        modification: DeshakeAction
    ) -> None:
        parameter, value = modification.parameter, modification.value

        if parameter != 'autocrop':
            self._push_to_history()


        else:
            scene_key: str = self._key(scene)
            scene_deshake: SceneDeshake = self._db[scene_key]

            if parameter.startswith('crop_'):
                i = 0
                if parameter == 'crop_top':
                    i = 0
                    new = scene_deshake.crop[i] + value
                elif parameter == 'crop_bottom':
                    i = 1
                    new = scene_deshake.crop[i] - value
                elif parameter == 'crop_left':
                    i = 2
                    new = scene_deshake.crop[i] + value
                elif parameter == 'crop_right':
                    i = 3
                    new = scene_deshake.crop[i] - value
                if 0 <= new < 400:
                    scene_deshake.crop[i] = new
                scene_deshake.use_default = False

            elif parameter == 'keep_ratio':
                scene_deshake.keep_ratio = bool(value)

            elif parameter == 'fit_to_width':
                scene_deshake.fit_to_width = bool(value)

            elif parameter == 'detection':
                if modification.type == 'set':
                    scene_deshake.detection_params = deepcopy(value)
                    scene_deshake.custom_detection_params = True

                elif modification.type == 'discard':
                    scene_deshake.detection_params = DetectInnerRectParams()
                    scene_deshake.custom_detection_params = False

            elif parameter == 'autocrop':
                scene_deshake.autocrop = deepcopy(value)

            elif parameter == 'use_ac':
                scene_deshake.use_autocrop = value

            elif parameter == 'copy_ac_to_crop':
                scene_deshake.crop = deepcopy(scene_deshake.autocrop)

            self.modified_scenes.add(scene_key)


    def is_modified(self, scene: Scene) -> bool:
        if self._key(scene) in self.modified_scenes:
            return True

        if self._chapter_key(scene) in self.modified_scenes:
            return True

        return False


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
        scene_deshake: SceneDeshake = self._db[k_scene]
        k_ch: str = scene['dst']['k_ch']
        chapter_deshake: ChapterDeshake | None = None
        k_ch_key: str = self._chapter_key(scene)
        if k_ch_key in self.modified_scenes:
            chapter_deshake: ChapterDeshake = self._db[k_ch_key]

        k_ep: str = scene['dst']['k_ep']
        k: str = k_ch if k_ch in ('g_debut', 'g_fin') else k_ep
        deshake_fp = os.path.join(
            db['common']['directories']['config'], k, f"{k}_deshake.ini"
        )

        print(deshake_fp)
        pprint(scene_deshake)
        pprint(chapter_deshake)
        print(f"k_ch_key: {k_ch_key}")
        print(f"k_scene: {k_scene}")
        print(f"section: {k_ch}")

        # Parse the file
        if os.path.exists(deshake_fp):
            config_deshake = ConfigParser(dict_type=OrderedDict)
            config_deshake.read(deshake_fp)
        else:
            config_deshake = ConfigParser({}, OrderedDict)

        # Select section
        k_section: str = k_ch
        if not config_deshake.has_section(k_section):
            config_deshake.add_section(k_section)

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
            if config_deshake.has_option(k_section, option):
                print(f"remove: {k_section}: {option}")
                config_deshake.remove_option(k_section, option)

            values: list[str] = []
            if not all([x==0 for x in scene_deshake.crop]):
                values.append(f"crop={':'.join(map(str, scene_deshake.crop))}")

            values.append(f"keep_ratio={'true' if scene_deshake.keep_ratio else 'false'}")
            values.append(f"fit_to_width={'true' if scene_deshake.fit_to_width else 'false'}")
            if scene_deshake.use_default:
                values.append(f"default=true")

            if not all([x==0 for x in scene_deshake.autocrop]):
                values.append(f"autocrop={':'.join(map(str, scene_deshake.autocrop))}")
                if scene_deshake.use_autocrop:
                    values.append(f"use_autocrop=true")

            if not scene_deshake.custom_detection_params:
                values.append(f"default_detection_params=true")
                params: DetectInnerRectParams = scene_deshake.detection_params
                params_str: str = ":".join(map(str, (
                    params.threshold_min,
                    params.morph_kernel_radius,
                    params.erode_kernel_radius,
                )))
                params_str += f":{'true' if params.do_add_borders else 'false'}"

            values_str: str = ", ".join(values)
            print(lightgreen(values_str))
            config_deshake.set(k_section, option, values_str)

        # Chapter
        if chapter_deshake is not None:
            option = 'width'
            if config_deshake.has_option(k_section, option):
                print(f"remove: {k_section}: {option}")
                config_deshake.remove_option(k_section, option)
            config_deshake.set(k_section, option, f"{chapter_deshake.width}")


        # Write to the database
        with open(deshake_fp, 'w') as config_file:
            config_deshake.write(config_file)

        # Remove modified
        if k_scene in self.modified_scenes:
            scene['deshake'] = deepcopy(self._db[k_scene])
            self.modified_scenes.remove(k_scene)

        if chapter_deshake is not None:
            chapter: ChapterVideo
            if k_ch in ('g_debut', 'g_fin'):
                chapter = db[k_ch]['video']
            else:
                chapter = db[k_ep]['video']['target'][k_ch]
            chapter['deshake'] = deepcopy(self._db[k_ch_key])
            self.modified_scenes.remove(k_ch_key)

        self.history.clear()
        print("done")


    def discard(self, scene: Scene):
        if not self.is_modified(scene):
            return

        # Scene deshake
        k_scene = self._key(scene)
        self._db[k_scene] = deepcopy(scene['deshake'])
        self.modified_scenes.remove(k_scene)

        # Chapter deshake
        k_ch_key: str = self._chapter_key(scene)
        k_ch: str = scene['dst']['k_ch']
        if k_ch_key in self.modified_scenes:
            chapter: ChapterVideo
            if k_ch in ('g_debut', 'g_fin'):
                chapter = db[k_ch]['video']
            else:
                k_ep: str = scene['dst']['k_ep']
                chapter = db[k_ep]['video']['target'][k_ch]
            self._db[k_ch_key] = deepcopy(chapter['deshake'])
            self.modified_scenes.remove(k_ch_key)

        self.history.clear()
