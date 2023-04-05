# -*- coding: utf-8 -*-

import os
import os.path

from pprint import pprint

from PySide6.QtCore import (
    QSettings,
    QObject,
)
from PySide6.QtWidgets import QApplication


class Preferences(QObject):

    def __init__(self):
        super(Preferences, self).__init__()

        self.settings = QSettings(
            QSettings.Format.IniFormat,
            QSettings.Scope.UserScope,
            "mco", "viewer")

        self.preferences = {
            'viewer': dict(),
            'browser': dict(),
            'hide': dict(),
        }

        # Default geometry
        screens = QApplication.screens()
        screen_width = screens[0].size().width()
        screen_height = screens[0].size().height()

        # viewer
        if self.settings.contains('viewer/screen'):
            self.preferences['viewer']['screen'] = 0
        else:
            self.preferences['viewer']['screen'] = 0

        self.preferences['viewer']['geometry'] = [0, 0, screen_width, screen_height]

        # Browser widget
        self.preferences['browser']['geometry'] = [(1920-400), 50, 0, 0]
        if self.settings.contains('browser/geometry'):
            self.preferences['browser']['geometry'] = list(map(lambda x: int(x),
                self.settings.value("browser/geometry").split(':')))

        self.preferences['browser']['episode'] = ''
        if self.settings.contains('browser/episode'):
            ep_no_str = self.settings.value('browser/episode')
            self.preferences['browser']['episode'] = ep_no_str if ep_no_str == '' else int(ep_no_str)

        self.preferences['browser']['k_part'] = ''
        if self.settings.contains('browser/part'):
            self.preferences['browser']['k_part'] = self.settings.value('browser/part')

        self.preferences['browser']['fit_image_to_window'] =  False
        if self.settings.contains('browser/fit_image_to_window'):
            self.preferences['browser']['fit_image_to_window'] = self.settings.value('browser/fit_image_to_window', True, type=bool)

        # Filtering images by...
        self.preferences['hide']['editions'] = list()
        if self.settings.contains('hide/editions'):
            if self.settings.value('hide/editions') != '':
                self.preferences['hide']['editions'] = self.settings.value('hide/editions').split(',')

        self.preferences['hide']['steps'] = list()
        if self.settings.contains('hide/steps'):
            if self.settings.value('hide/steps') != '':
                self.preferences['hide']['steps'] = self.settings.value('hide/steps').split(',')

        self.preferences['hide']['filter_ids'] = list()
        if self.settings.contains('hide/filter_ids'):
            self.preferences['hide']['filter_ids'] = self.settings.value('hide/filter_ids').split(',')

        # pprint(self.preferences)



    def save(self, preferences):
        # print("%s.save settings" % (__name__))
        # pprint(preferences)

        # viewer
        self.settings.setValue('viewer/geometry',
            ':'.join(map(lambda x: "%d" % (x), preferences['viewer']['geometry'])))
        self.settings.setValue('viewer/screen', 0)

        # browser
        self.settings.setValue('browser/geometry',
            ':'.join(map(lambda x: "%d" % (x), preferences['browser']['geometry'])))
        self.settings.setValue('browser/episode', preferences['browser']['episode'])
        self.settings.setValue('browser/part', preferences['browser']['k_part'])
        self.settings.setValue('browser/fit_image_to_window', preferences['browser']['fit_image_to_window'])

        # "filters by"
        self.settings.setValue('hide/editions',
            ','.join(map(lambda x: "%s" % (x), preferences['hide']['editions'])))

        self.settings.setValue('hide/steps',
            ','.join(map(lambda x: "%s" % (x), preferences['hide']['steps'])))


    def get_preferences(self):
        return self.preferences
