import sys
import os

from pprint import pprint
from logger import log

from PySide6.QtCore import (
    QObject,
    Signal,
)
from utils.p_print import *
from import_parsers import *
from parsers import (
    all_chapter_keys,
    credit_chapter_keys,
    key
)

class CommonController(QObject):
    signal_close = Signal()
    signal_scenes_modified = Signal(dict)

    signal_shot_modified = Signal(dict)

    def __init__(self):
        super(CommonController, self).__init__()
        self.view = None

        # Internal variables
        self.scenes = {}
        self.frames = {}

        self.playlist_properties = {}
        self.playlist_frames = []

        self.current_selection = {}
        self.current_frame = None

        self.preview_options = None


    def exit(self):
        # print("%s:exit" % (__name__))
        p = self.view.get_preferences()
        self.preferences.save(p)
        try:
            log.handlers[0].close()
        except:
            pass
        # print("model: exit")


    def get_preferences(self):
        p = self.preferences.get_preferences()
        return p


    def save_preferences(self, preferences:dict):
        preferences = self.view.get_preferences()
        self.preferences.save(preferences)


    def get_available_episode_and_parts(self):
        episode_and_parts = {}
        path_cache = self.model_database.get_cache_path()
        if os.path.exists(path_cache):
            # Rather than walking through, try every possibilities
            # another option would be to select a folder, then the combobox
            # will be disabled

            for no in range(1, 39):
                k_ep = key(no)
                if os.path.exists(os.path.join(path_cache, k_ep)):
                    episode_and_parts[k_ep] = []

                    for k_part in all_chapter_keys():
                        if os.path.exists(os.path.join(path_cache, k_ep, k_part)):
                            episode_and_parts[k_ep].append(k_part)

                    # g_asuivre, g_documentaire
                    episode_and_parts[k_ep].append('g_asuivre')
                    episode_and_parts[k_ep].append('g_documentaire')

            episode_and_parts[' '] = []
            for k_part_g in credit_chapter_keys():
                if os.path.exists(os.path.join(path_cache, k_part_g)):
                    episode_and_parts[' '].append(k_part_g)

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

    def get_shot_no_from_index(self, index:int):
        return self.playlist_frames[index]['shot_no']


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



    def current_shot(self):
        try:
            return self.scenes[self.current_shot_no]
        except:
            print(orange("\tget current shot: current shot is None"))
            log.warning("get current shot: current shot is None")
            pass
        # self.shots[self.current_frame['shot_no']]
        return None


    def get_current_frame_no(self, initial=False):
        # pprint(self.current_frame)
        if 'replace' in self.current_frame.keys():
            return self.current_frame['replace']
        return self.current_frame['frame_no']


    def set_modification_status(self, modification_type, is_modified:bool=False):
        shot = self.current_shot()
        try: shot['modifications']['list'].remove(modification_type)
        except: pass
        if is_modified:
            shot['modifications']['list'].append(modification_type)
        self.signal_shot_modified.emit({
            'shot_no': shot['no'],
            'modifications': shot['modifications']['list']
        })
