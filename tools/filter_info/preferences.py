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
            "mco", "filter_info")

        # Default
        self.preferences = {
            'main_window': dict(),
        }

        # Default geometry
        screens = QApplication.screens()
        screens_count = len(screens)
        screen_width = screens[0].size().width()
        screen_height = screens[0].size().height()

        # Main_window
        if self.settings.contains('main_window/screen'):
            self.preferences['main_window']['screen'] = 0
        else:
            self.preferences['main_window']['screen'] = 0

        # Default window geometry
        self.preferences['main_window']['geometry'] = [50, 50, int(screen_width/2), int(screen_height/2)]

        # Use the saved preferences
        try:
            self.preferences['main_window']['geometry'] = list(map(lambda x: int(x),
                self.settings.value('main_window/geometry').split(':')))
            if self.preferences['main_window']['geometry'][0] > screen_width and screens_count < 2:
                self.preferences['main_window']['geometry'][0] -= screen_width
        except:
            print("preferences cannot be loaded")
            pass


    def save(self, preferences):
        # print("%s.save preferences" % (__name__))
        # pprint(preferences)

        # (Mandatory) main_window
        self.settings.setValue('main_window/geometry',
            ':'.join(map(lambda x: "%d" % (x), preferences['main_window']['geometry'])))
        self.settings.setValue('main_window/screen', 0)


    def get_preferences(self):
        return self.preferences
