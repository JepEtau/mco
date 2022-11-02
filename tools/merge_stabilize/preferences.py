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

    def __init__(self):
        super(Preferences, self).__init__()

        self.settings = QSettings(
            QSettings.Format.IniFormat,
            QSettings.Scope.UserScope,
            "mco", "merge_stabilize")

        self.preferences = {
            'viewer': dict(),
            'selection': dict(),
            'controls': dict(),
            'stitching': dict(),
            'stitching_curves': dict(),
            'stabilize': dict(),
            'geometry': dict(),
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

        # selection widget
        self.preferences['selection']['geometry'] = [(1920-600), 50, 0, 0]
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


        # controls widget
        self.preferences['controls']['geometry'] = [(1920-600), 50, 0, 0]
        if self.settings.contains('controls/geometry'):
            self.preferences['controls']['geometry'] = list(map(lambda x: int(x),
                self.settings.value("controls/geometry").split(':')))

        self.preferences['controls']['preview_rgb'] =  False
        if self.settings.contains('controls/preview_rgb'):
            self.preferences['controls']['preview_rgb'] = self.settings.value('controls/preview_rgb', True, type=bool)

        self.preferences['controls']['preview_replace'] =  False
        if self.settings.contains('controls/preview_replace'):
            self.preferences['controls']['preview_replace'] = self.settings.value('controls/preview_replace', True, type=bool)

        self.preferences['controls']['preview_crop'] =  False
        if self.settings.contains('controls/preview_crop'):
            self.preferences['controls']['preview_crop'] = self.settings.value('controls/preview_crop', True, type=bool)

        self.preferences['controls']['show_crop_rect'] =  False
        if self.settings.contains('controls/show_crop_rect'):
            self.preferences['controls']['show_crop_rect'] = self.settings.value('controls/show_crop_rect', True, type=bool)

        self.preferences['controls']['preview_final'] =  False
        if self.settings.contains('controls/preview_final'):
            self.preferences['controls']['preview_final'] = self.settings.value('controls/preview_final', True, type=bool)

        self.preferences['controls']['speed'] = 1
        if self.settings.contains('controls/speed'):
            self.preferences['controls']['speed'] = float(self.settings.value("controls/speed"))

        # stitching widget
        self.preferences['stitching']['geometry'] = [(1920-1024), 50, 0, 0]
        if self.settings.contains('stitching/geometry'):
            self.preferences['stitching']['geometry'] = list(map(lambda x: int(x),
                self.settings.value("stitching/geometry").split(':')))


        # stitching_curves widget
        self.preferences['stitching_curves']['geometry'] = [(1920-1024), 50, 0, 0]
        if self.settings.contains('stitching_curves/geometry'):
            self.preferences['stitching_curves']['geometry'] = list(map(lambda x: int(x),
                self.settings.value("stitching_curves/geometry").split(':')))

        # stabilization widget
        self.preferences['stabilize']['geometry'] = [(1920-1024), 50, 0, 0]
        if self.settings.contains('stabilization/geometry'):
            self.preferences['stabilize']['geometry'] = list(map(lambda x: int(x),
                self.settings.value("stabilization/geometry").split(':')))

        # geometry widget
        self.preferences['geometry']['geometry'] = [(1920-1024), 50, 0, 0]
        if self.settings.contains('geometry/geometry'):
            self.preferences['geometry']['geometry'] = list(map(lambda x: int(x),
                self.settings.value("geometry/geometry").split(':')))



    def save(self, preferences):
        # print("%s.save settings" % (__name__))
        # pprint(preferences)

        # viewer
        self.settings.setValue('viewer/geometry',
            ':'.join(map(lambda x: "%d" % (x), preferences['viewer']['geometry'])))
        self.settings.setValue('viewer/screen', 0)

        # selection
        self.settings.setValue('selection/geometry',
            ':'.join(map(lambda x: "%d" % (x), preferences['selection']['geometry'])))
        self.settings.setValue('selection/episode', preferences['selection']['episode'])
        self.settings.setValue('selection/part', preferences['selection']['part'])
        self.settings.setValue('selection/step', preferences['selection']['step'])

        # controls
        self.settings.setValue('controls/geometry',
            ':'.join(map(lambda x: "%d" % (x), preferences['controls']['geometry'])))
        self.settings.setValue('controls/preview_rgb', preferences['controls']['preview_rgb'])
        self.settings.setValue('controls/preview_replace', preferences['controls']['preview_replace'])

        if 'preview_crop' in preferences['controls'].keys():
            self.settings.setValue('controls/preview_crop', preferences['controls']['preview_crop'])

        if 'show_crop_rect' in preferences['controls'].keys():
            self.settings.setValue('controls/show_crop_rect', preferences['controls']['show_crop_rect'])

        self.settings.setValue('controls/preview_final', preferences['controls']['preview_final'])
        self.settings.setValue('controls/speed', preferences['controls']['speed'])

        # stitching
        self.settings.setValue('stitching/geometry',
            ':'.join(map(lambda x: "%d" % (x), preferences['stitching']['geometry'])))

        # stitching_curves
        self.settings.setValue('stitching_curves/geometry',
            ':'.join(map(lambda x: "%d" % (x), preferences['stitching_curves']['geometry'])))

        # stabilization
        self.settings.setValue('stabilization/geometry',
            ':'.join(map(lambda x: "%d" % (x), preferences['stabilize']['geometry'])))

        # geometry
        self.settings.setValue('geometry/geometry',
            ':'.join(map(lambda x: "%d" % (x), preferences['geometry']['geometry'])))



    def get_preferences(self):
        return self.preferences
