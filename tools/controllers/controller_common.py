# -*- coding: utf-8 -*-
import sys



import os

from pprint import pprint
from logger import log

from PySide6.QtCore import (
    QObject,
    Signal,
)


from img_toolbox.utils import FILTER_TAGS
from utils.common import (
    K_GENERIQUES,
    K_PARTS,
)
from utils.pretty_print import *



class Controller_common(QObject):
    signal_close = Signal()
    signal_shotlist_modified = Signal(dict)

    signal_shot_modified = Signal(dict)

    def __init__(self):
        super(Controller_common, self).__init__()
        self.view = None

        # Internal variables
        self.step_labels = FILTER_TAGS

        self.shots = dict()
        self.frames = dict()

        self.playlist_properties = dict()
        self.playlist_frames = list()

        self.current_selection = dict()
        self.current_frame = None

        self.preview_options = None


    def get_widget_list(self):
        try:
            return self.WIDGET_LIST
        except:
            raise Exception("Error: WIDGET_LIST shall be define in the model class")

    def get_selectable_widgets(self):
        try:
            # This list shall be ordered
            return self.SELECTABLE_WIDGET_LIST
        except:
            raise Exception("Error: SELECTABLE_WIDGET_LIST shalle be define in the model class")


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
        episode_and_parts = dict()
        path_cache = self.model_database.get_cache_path()
        if os.path.exists(path_cache):
            # Rather than walking through, try every possibilities
            # another option would be to select a folder, then the combobox
            # will be disabled

            for ep_no in range(1, 39):
                k_ep = 'ep%02d' % (ep_no)
                if os.path.exists(os.path.join(path_cache, k_ep)):
                    episode_and_parts[k_ep] = list()

                    for k_part in K_PARTS:
                        if os.path.exists(os.path.join(path_cache, k_ep, k_part)):
                            episode_and_parts[k_ep].append(k_part)

                    # g_asuivre, g_documentaire
                    episode_and_parts[k_ep].append('g_asuivre')
                    episode_and_parts[k_ep].append('g_documentaire')

            episode_and_parts[' '] = list()
            for k_part_g in K_GENERIQUES:
                if os.path.exists(os.path.join(path_cache, k_part_g)):
                    episode_and_parts[' '].append(k_part_g)

        return episode_and_parts


    def get_step_labels(self):
        return self.step_labels


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
            return self.shots[self.current_shot_no]
        except:
            print_orange("\tget current shot: current shot is None")
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
