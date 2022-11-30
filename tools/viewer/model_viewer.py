# -*- coding: utf-8 -*-

import sys
sys.path.append('../scripts')
import os
import os.path

from pprint import pprint
from logger import log

from PySide6.QtCore import (
    QObject,
    Signal,
)

from viewer.preferences import Preferences
from viewer.model_framelist import Model_framelist

from utils.get_filters import FILTER_BASE_NO
from utils.common import K_ALL_PARTS
from utils.common import K_GENERIQUES


class Model_viewer(QObject):
    signal_refresh_browser = Signal(dict)
    signal_refresh_framelist = Signal(list)
    signal_display_frame = Signal(dict)
    signal_shotlist_modified = Signal(dict)

    def __init__(self):
        super(Model_viewer, self).__init__()
        self.view = None

        # Load saved preferences
        self.preferences = Preferences()

        # Variables
        self.framelist = Model_framelist()
        self.step_labels = [k for k, v in sorted(FILTER_BASE_NO.items(), key=lambda item: item[1])]



    def exit(self):
        # print("%s:exit" % (__name__))
        p = self.view.get_preferences()
        self.preferences.save(p)
        try:
            log.handlers[0].close()
        except:
            pass


    def set_view(self, view):
        self.view = view
        self.view.widget_browser.signal_directory_changed[dict].connect(self.directory_changed)
        self.view.widget_browser.signal_filter_by_changed[dict].connect(self.update_filter_by)
        self.view.widget_browser.signal_select_image[str].connect(self.select_frame)

        p = self.preferences.get_preferences()
        k_ep = 'ep%02d' % (p['browser']['episode']) if p['browser']['episode'] != '' else ''
        self.framelist.set_new_filter_by(p['hide'])
        self.directory_changed({
            'k_ep': k_ep,
            'k_part': p['browser']['part']
        })


    def get_widget_list(self):
        return list()


    def get_preferences(self):
        p = self.preferences.get_preferences()
        return p


    def save_preferences(self, preferences:dict):
        preferences = self.ui.get_preferences()
        self.preferences.save(preferences)


    def get_available_episode_and_parts(self):
        episode_and_parts = dict()
        path_images = self.framelist.get_images_path()
        log.info("Parse the images folder: %s" % (path_images))
        if os.path.exists(path_images):
            # Rather than walking through, try every possibilities
            # another option would be to select a folder, then the combobox
            # will be disabled

            for ep_no in range(1, 39):
                k_ep = 'ep%02d' % (ep_no)
                if os.path.exists(os.path.join(path_images, k_ep)):
                    episode_and_parts[k_ep] = list()

                    for k_part in K_ALL_PARTS:
                        if os.path.exists(os.path.join(path_images, k_ep, k_part)):
                            episode_and_parts[k_ep].append(k_part)

            episode_and_parts[' '] = list()
            for k_part_g in K_GENERIQUES:
                if os.path.exists(os.path.join(path_images, k_part_g)):
                    episode_and_parts[' '].append(k_part_g)

        # pprint(episode_and_parts)
        # sys.exit()
        return episode_and_parts



    def directory_changed(self, values:dict):
        k_ep = values['k_ep']
        k_part = values['k_part']
        log.info("directory_changed: %s:%s" % (k_ep, k_part))
        # pprint(values)

        self.framelist.clear()
        path_images = self.framelist.get_images_path()

        if not (k_part == '' and k_ep != ''):
            # self.framelist.consolidate_database(k_ep, k_part)
            if os.path.exists(path_images):
                if k_part in K_GENERIQUES:
                    path = os.path.join(path_images, k_part)
                    if os.path.exists(path):
                        for f in os.listdir(path):
                            if f.endswith(".png"):
                                self.framelist.append(k_ep, k_part, f)
                else:
                    if os.path.exists(os.path.join(path_images, k_ep)):
                        path = os.path.join(path_images, k_ep, k_part)
                        if os.path.exists(path):
                            for f in os.listdir(path):
                                # print(os.path.split(filename))
                                if f.endswith(".png"):
                                    self.framelist.append(k_ep, k_part, f)
                    # else:
                    #   cannot parse this folder, refresh and set all to default values ?
                # else:
                #   cannot parse this folder, refresh and set all to default values ?

        # self.framelist.print()
        new_widget_values = {
            'k_ep': k_ep,
            'k_part': k_part,
            'editions': self.framelist.editions(),
            'filter_ids': self.framelist.filter_ids(),
            'hide': self.framelist.get_hide_struct(),
        }
        self.signal_refresh_browser.emit(new_widget_values)



    def update_filter_by(self, filter_by):
        log.info("update filter_by in model and send the new list to the browser")
        # print("%s:update_filter_by" % (__name__))
        # pprint(filter_by)

        # update filter_by in framelist
        self.framelist.set_new_filter_by(filter_by)

        # get the list of images
        filtered_imagelist = self.framelist.get_filtered_imagelist()
        self.signal_refresh_framelist.emit(filtered_imagelist)



    def get_step_labels(self):
        return self.step_labels


    def select_frame(self, image_name=''):
        # log.info("select frame: %s" % (image_name))
        frame = self.framelist.get_frame(image_name)
        self.signal_display_frame.emit(frame)

