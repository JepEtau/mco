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
        self._is_modified: bool = False
        self._modified_scenes: set[str] = set()


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
        self._is_modified = True
        self._modified_scenes.add(scene_key)


    def remove_multiple(self, scene: Scene, frame_nos: list[int]) -> None:
        for src_scene in scene['src'].scenes():
            scene_key = self._key(src_scene)
            if scene_key in self._db:
                for f_no in frame_nos:
                    if f_no in self._db[scene_key]:
                        del self._db[scene_key][f_no]
        self._modified_scenes.add(scene_key)
        self._is_modified = True


    @property
    def is_modified(self) -> bool:
        return self._is_modified


    def save(self):
        pprint(self._db)
        if not self._is_modified:
            return True

        for key in self._modified_scenes:
            k_ed, k_ep, k_ch, scene_no = key.split()
            if k_ch in

        # for k_ed, ed_values in self.db_replaced_frames.items():
        #     for k_ep, ep_values in ed_values.items():
        #         for k_part, part_values in ep_values.items():

        #             # Open configuration file
        #             if k_part in K_GENERIQUES:
        #                 # Write into a single file in the generique directory
        #                 filepath = os.path.join(db['common']['directories']['config'], k_part, "%s_replace.ini" % (k_part))
        #             else:
        #                 filepath = os.path.join(db['common']['directories']['config'], k_ep, "%s_replace.ini" % (k_ep))
        #             if filepath.startswith("~/"):
        #                 filepath = os.path.join(PosixPath(Path.home()), filepath[2:])

        #             # Parse the file
        #             if os.path.exists(filepath):
        #                 config_replace = configparser.ConfigParser(dict_type=collections.OrderedDict)
        #                 config_replace.read(filepath)
        #             else:
        #                 config_replace = configparser.ConfigParser({}, collections.OrderedDict)

        #             # Update the config file, select section
        #             k_section = '%s.%s.%s' % (k_ed, k_ep, k_part)

        #             if not config_replace.has_section(k_section):
        #                 config_replace[k_section] = dict()

        #             # Update the values
        #             for frame_no, new_frame_no in part_values.items():
        #                 if new_frame_no == -1:
        #                     # Remove from the config file
        #                     if config_replace.has_option(k_section, str(frame_no)):
        #                         config_replace.remove_option(k_section, str(frame_no))
        #                     try: del self.db_replaced_frames_initial[k_ed][k_ep][k_part][frame_no]
        #                     except: pass
        #                 else:
        #                     # Set the new value
        #                     config_replace.set(k_section, str(frame_no), str(new_frame_no))
        #                     nested_dict_set(self.db_replaced_frames_initial,
        #                         new_frame_no, k_ed, k_ep, k_part, frame_no)


        #             # Write to the database
        #             with open(filepath, 'w') as config_file:
        #                 config_replace.write(config_file)

        # self.db_replaced_frames.clear()
        # self.is_replace_db_modified = False
        # return True
