from __future__ import annotations
from collections import OrderedDict
from configparser import ConfigParser
from copy import copy, deepcopy
from logger import log
import os
from pprint import pprint
from import_parsers import *
from parsers._keys import credit_chapter_keys
from utils.mco_types import Scene, Singleton
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from scene.src_scene import SrcScene
from parse_db import db




class ReplaceDatabase:

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


    def _push_to_history(self):
        self.history.append({
            '_db': deepcopy(self._db),
            'modified_src_scenes': deepcopy(self.modified_src_scenes),
            'modified_scenes': deepcopy(self.modified_scenes),
        })
        if len(self.history) > self.history_depth:
            self.history = self.history[1:]


    def add(
        self,
        scene: Scene,
        src_scene_key: str,
        current: int,
        by: int
    ) -> None:
        self._push_to_history()
        replace_dict = self._db[src_scene_key]
        if current != by:
            replace_dict[current] = by
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

        modified_src_scenes = copy(self.modified_src_scenes)
        for src_scene in scene['src'].scenes():
            src_scene_key = self._key(src_scene)
            print(f"SRC scene_key: {src_scene_key}", end=' ')
            if src_scene_key not in self.modified_src_scenes:
                print("not modified")
                continue
            print ("to save")

            k_ed, k_ep, k_ch, src_scene_no = src_scene_key.split(':')
            # filepath
            k = (
                k_ch if k_ch in credit_chapter_keys()
                else k_ep
            )
            replace_fp = os.path.join(
                db['common']['directories']['config'], k, f"{k}_replace.ini"
            )

            # Parse the file
            if os.path.exists(replace_fp):
                config_replace = ConfigParser(dict_type=OrderedDict)
                config_replace.read(replace_fp)
            else:
                config_replace = ConfigParser({}, OrderedDict)

            # Update the config file, select section
            k_section = '.'.join((k_ed, k_ep, k_ch, ))
            _src_scene = db[k_ep]['video'][k_ed][k_ch]['scenes'][int(src_scene_no)]
            initial_replace = _src_scene['replace']
            # config_replace[k_section] = {}

            for no in initial_replace:
                if (
                    config_replace.has_option(k_section, f"{no}")
                    and no not in self._db[src_scene_key]
                ):
                    print(f"remove: {k_section}: {no}")
                    config_replace.remove_option(k_section, f"{no}")

            # Set new values
            for no, by in self._db[src_scene_key].items():
                if no != by:
                    if not config_replace.has_section(k_section):
                        config_replace.add_section(k_section)
                    config_replace.set(k_section, f"{no}", f"{by}")

            # Write to the database
            with open(replace_fp, 'w') as config_file:
                config_replace.write(config_file)

            # Remove modified
            _src_scene['replace'] = deepcopy(self._db[src_scene_key])
            self.modified_src_scenes.remove(src_scene_key)

        self.modified_scenes.remove(scene['no'])
        self.history.clear()


    def discard(self, scene: Scene):
        if not self.is_modified(scene):
            return

        for src_scene in scene['src'].scenes():
            src_scene_key = self._key(src_scene)
            self._db[src_scene_key] = deepcopy(src_scene['scene']['replace'])
            self.modified_src_scenes.remove(src_scene_key)

        self.modified_scenes.remove(scene['no'])
        self.history.clear()
