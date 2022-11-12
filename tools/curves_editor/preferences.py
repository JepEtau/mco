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
            "mco", "curves_editor")

        self.preferences = {
            'viewer': dict(),
            'tools': dict(),
            'selected': dict(),
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

        # tools widget
        self.preferences['tools']['geometry'] = [(1920-600), 50, 0, 0]
        if self.settings.contains('tools/geometry'):
            self.preferences['tools']['geometry'] = list(map(lambda x: int(x),
                self.settings.value("tools/geometry").split(':')))

        self.preferences['tools']['episode'] = ''
        if self.settings.contains('tools/episode'):
            ep_no_str = self.settings.value('tools/episode')
            self.preferences['tools']['episode'] = ep_no_str if ep_no_str == '' else int(ep_no_str)

        self.preferences['tools']['part'] = ''
        if self.settings.contains('tools/part'):
            self.preferences['tools']['part'] = self.settings.value('tools/part')


        # Filtering images by...
        self.preferences['selected']['k_ed'] = ''
        if self.settings.contains('selected/edition'):
            if self.settings.value('selected/edition') != '':
                self.preferences['selected']['k_ed'] = self.settings.value('selected/edition')

        self.preferences['selected']['step'] = ''
        if self.settings.contains('selected/step'):
            if self.settings.value('selected/step') != '':
                self.preferences['selected']['step'] = self.settings.value('selected/step')

        self.preferences['selected']['filter_id'] = list()
        if self.settings.contains('selected/filter_id'):
            self.preferences['selected']['filter_id'] = self.settings.value('selected/filter_id')

        self.preferences['selected']['shots'] = list()
        if self.settings.contains('selected/shots'):
            self.preferences['selected']['shots'] = self.settings.value('selected/shots').split(',')



    def save(self, preferences):
        # print("%s.save settings" % (__name__))
        # pprint(preferences)

        # viewer
        self.settings.setValue('viewer/geometry',
            ':'.join(map(lambda x: "%d" % (x), preferences['viewer']['geometry'])))
        self.settings.setValue('viewer/screen', 0)

        # tools
        self.settings.setValue('tools/geometry',
            ':'.join(map(lambda x: "%d" % (x), preferences['tools']['geometry'])))
        self.settings.setValue('tools/episode', preferences['tools']['episode'])
        self.settings.setValue('tools/part', preferences['tools']['part'])
        # self.settings.setValue('tools/fit_image_to_window', preferences['tools']['fit_image_to_window'])

        # "filters by"
        self.settings.setValue('selected/edition', preferences['selected']['k_ed'])
        self.settings.setValue('selected/step', preferences['selected']['step'])
        self.settings.setValue('selected/filter_id', preferences['selected']['filter_id'])
        self.settings.setValue('selected/shots',
            ','.join(map(lambda x: "%s" % (x), preferences['selected']['shots'])))



    def get_preferences(self):
        return self.preferences
