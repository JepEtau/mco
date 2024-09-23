from __future__ import annotations
import sys
import os

from pprint import pprint
from logger import log

from PySide6.QtCore import (
    QObject,
    Signal,
)

from ui.window_replace import ReplaceWindow
from .user_preferences import UserPreferences
from utils.p_print import *
from import_parsers import *
from parsers import (
    all_chapter_keys,
    credit_chapter_keys,
    key
)

class CommonController(QObject):
    signal_close = Signal()
    signal_scenelist = Signal(dict)

    signal_scene_modified = Signal(dict)

    def __init__(self):
        super().__init__()
        self.view: ReplaceWindow = None

        # Internal variables
        self.scenes = {}
        self.frames = {}

        self.playlist_properties = {}
        self.playlist_frames = []

        self.current_selection = {}
        self.current_frame = None

        self.preview_options = None

        self.preferences: UserPreferences = None
        self.current_scene_no: int = 0


    def exit(self):
        # print("%s:exit" % (__name__))
        p = self.view.get_preferences()
        self.preferences.save(p)
        try:
            log.handlers[0].close()
        except:
            pass
        # print("model: exit")


    def apply_user_preferences(self, user_preferences:dict):
        try:
            s = user_preferences['window_main']
            self.setGeometry(s['geometry'][0],
                s['geometry'][1],
                s['geometry'][2],
                s['geometry'][3])
        except:
            pass
        self.setGeometry(100,100,2000,800)



    def get_preferences(self):
        p = self.preferences.get_preferences()
        return p


    def save_preferences(self, preferences:dict):
        preferences = self.view.get_preferences()
        self.preferences.save(preferences)


    def get_available_episode_and_parts(self) -> dict[str, list]:
        episode_and_parts: dict[str, list] = {}
        # path_cache = self.model_database.get_cache_path()
        # if os.path.exists(path_cache):
        #     # Rather than walking through, try every possibilities
        #     # another option would be to select a folder, then the combobox
        #     # will be disabled

        for no in range(1, 40):
            k_ep = key(no)
            # if os.path.exists(os.path.join(path_cache, k_ep)):
            episode_and_parts[k_ep] = list(all_chapter_keys())

                # for k_part in all_chapter_keys():
                #     # if os.path.exists(os.path.join(path_cache, k_ep, k_part)):
                #     #     episode_and_parts[k_ep].append(k_part)

                # # g_asuivre, g_documentaire
                # episode_and_parts[k_ep].append('g_asuivre')
                # episode_and_parts[k_ep].append('g_documentaire')

        #     episode_and_parts[' '] = []
        #     for k_part_g in credit_chapter_keys():
        #         if os.path.exists(os.path.join(path_cache, k_part_g)):
        #             episode_and_parts[' '].append(k_part_g)

        episode_and_parts['ep01'].remove('precedemment')
        episode_and_parts['ep39'].remove('g_asuivre')
        episode_and_parts['ep39'].remove('asuivre')

        return episode_and_parts


    def get_current_frame(self):
        return self.current_frame

    def set_current_frame_cache(self, img):
        self.current_frame['cache'] = img

    def purge_current_frame_cache(self):
        try:
            del self.current_frame['cache']
            self.current_frame['cache'] = None
        except:
            pass

    def get_scene_no_from_index(self, index:int):
        return self.playlist_frames[index]['scene_no']


    def get_preview_options(self):
        return self.preview_options

    def event_preview_options_changed(self, preview_options):
        # log.info("preview has changed")
        if False:
            print("\nchanged preview mode:" % (preview_options))
            print("---------------------------------------")
            pprint(preview_options)
            print("")
        self.preview_options = preview_options
        self.signal_reload_frame.emit()



    def current_scene(self):
        try:
            return self.scenes[self.current_scene_no]
        except:
            print(orange("\tget current scene: current scene is None"))
            log.warning("get current scene: current scene is None")
            pass
        # self.scenes[self.current_frame['scene_no']]
        return None


    def get_current_frame_no(self, initial=False):
        # pprint(self.current_frame)
        if 'replace' in self.current_frame.keys():
            return self.current_frame['replace']
        return self.current_frame['frame_no']


    def set_modification_status(self, modification_type, is_modified:bool=False):
        scene = self.current_scene()
        try: scene['modifications']['list'].remove(modification_type)
        except: pass
        if is_modified:
            scene['modifications']['list'].append(modification_type)
        self.signal_scene_modified.emit({
            'scene_no': scene['no'],
            'modifications': scene['modifications']['list']
        })
