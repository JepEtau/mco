#!/usr/bin/env python3
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

    def __init__(self, editors:list=None):
        super(Preferences, self).__init__()

        self.editors = editors
        if self.editors is None:
            self.editors = [
                'controls',
                'curves',
                'replace',
                'geometry',
            ]

        self.settings = QSettings(
            QSettings.Format.IniFormat,
            QSettings.Scope.UserScope,
            "mco", "video_editor")

        self.preferences = {
            'viewer': dict(),
            'selection': dict(),
        }

        for editor in self.editors:
            self.preferences.update({editor: dict()})

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

        if self.settings.contains('viewer/current_editor'):
            self.preferences['viewer']['current_editor'] = self.settings.value('viewer/current_editor')
        else:
            self.preferences['viewer']['current_editor'] = 'selection'

        # selection widget
        self.preferences['selection']['geometry'] = [screen_width-500, 20, 0, 0]
        if self.settings.contains('selection/geometry'):
            self.preferences['selection']['geometry'] = list(map(lambda x: int(x),
                self.settings.value("selection/geometry").split(':')))

        self.preferences['selection']['episode'] = ''
        if self.settings.contains('selection/episode'):
            ep_no_str = self.settings.value('selection/episode')
            self.preferences['selection']['episode'] = ep_no_str if ep_no_str == '' else int(ep_no_str)

        self.preferences['selection']['part'] = ''
        if self.settings.contains('selection/part'):
            self.preferences['selection']['part'] = self.settings.value('selection/part')

        self.preferences['selection']['step'] = ''
        if self.settings.contains('selection/step'):
            if self.settings.value('selection/step') != '':
                self.preferences['selection']['step'] = self.settings.value('selection/step')

        # default widget position
        try: self.preferences['controls']['geometry'] = [100, screen_height-150, 0, 0]
        except: pass
        try: self.preferences['curves']['geometry'] = [(screen_width-500), screen_height-300, 0, 0]
        except: pass
        try: self.preferences['replace']['geometry'] = [(screen_width-500), screen_height-300, 0, 0]
        except: pass
        try: self.preferences['geometry']['geometry'] = [(screen_width-500), screen_height-300, 0, 0]
        except: pass

        # use the preferences save in the file
        for editor in self.editors:
            try:
                self.preferences[editor]['geometry'] = list(map(lambda x: int(x),
                    self.settings.value('%s/geometry' % (editor)).split(':')))
                self.preferences[editor]['widget'] =  self.settings.value('%s/widget' % (editor))
            except:
                print("preferences for widget [%s]cannot be loader" % (editor))
                pass



    def save(self, preferences):
        # print("%s.save preferences" % (__name__))
        # pprint(preferences)

        # viewer
        self.settings.setValue('viewer/geometry',
            ':'.join(map(lambda x: "%d" % (x), preferences['viewer']['geometry'])))
        self.settings.setValue('viewer/screen', 0)

        self.settings.setValue('viewer/current_editor', preferences['viewer']['current_editor'])

        # selection
        self.settings.setValue('selection/geometry',
            ':'.join(map(lambda x: "%d" % (x), preferences['selection']['geometry'])))
        self.settings.setValue('selection/episode', preferences['selection']['episode'])
        self.settings.setValue('selection/part', preferences['selection']['part'])
        self.settings.setValue('selection/step', preferences['selection']['step'])

        for editor in self.editors:
            try:
                self.settings.setValue('%s/geometry' % (editor),
                    ':'.join(map(lambda x: "%d" % (x), preferences[editor]['geometry'])))
                self.settings.setValue('%s/widget' % (editor), preferences[editor]['widget'])
            except:
                print("preferences for widget [%s] cannot be saved" % (editor))
                pass


    def get_preferences(self):
        return self.preferences
