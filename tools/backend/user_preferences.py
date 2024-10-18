import os
import os.path

from pprint import pprint
import sys
from typing import Any

from PySide6.QtCore import (
    QSettings,
    QObject,
)
from PySide6.QtWidgets import QApplication


class UserPreferences(QObject):

    def __init__(self, tool:str, widget_list: list = []):
        super().__init__()

        if widget_list is None or tool == '':
            raise Exception("Error: tool and widget list must be specified")

        self.editors = widget_list

        settings = QSettings(
            QSettings.Format.IniFormat,
            QSettings.Scope.UserScope,
            "mco", tool)
        self.tool = tool

        # Default
        self.preferences = {
            'window': dict(),
            'selection': dict(),
        }

        # for editor in self.editors:
        #     self.preferences.update({editor: dict()})

        # Default geometry
        screens = QApplication.screens()
        screens_count = len(screens)
        screen_width = screens[0].size().width()
        screen_height = screens[0].size().height()

        # (Mandatory) Main window
        if settings.contains('window/screen'):
            self.preferences['window']['screen'] = settings.value('window/screen')
        else:
            self.preferences['window']['screen'] = 0

        self.preferences['window']['geometry'] = [0, 0, screen_width, screen_height]
        try:
            self.preferences['window']['geometry'] = list(
                map(lambda x: int(x), settings.value('window/geometry').split(':'))
            )
        except:
            pass

        # Selection
        try:
            self.preferences['selection']['edition'] = ''
            if settings.contains('selection/edition'):
                self.preferences['selection']['edition'] = settings.value('selection/edition')
        except:
            self.preferences['selection']['edition'] = ''

        self.preferences['selection']['episode'] = ''
        if settings.contains('selection/episode'):
            ep_no_str = settings.value('selection/episode')
            self.preferences['selection']['episode'] = ep_no_str if ep_no_str == '' else int(ep_no_str)

        self.preferences['selection']['k_ch'] = ''
        if settings.contains('selection/part'):
            self.preferences['selection']['k_ch'] = settings.value('selection/part')

        self.preferences['selection']['scene_no'] = 0
        if settings.contains('selection/scene_no'):
            if settings.value('selection/scene_no') != '':
                self.preferences['selection']['scene_no'] = int(settings.value('selection/scene_no'))


        # use the preferences save in the file
        for editor in self.editors:
            try:
                self.preferences[editor]['geometry'] = list(map(lambda x: int(x),
                    settings.value('%s/geometry' % (editor)).split(':')))
                if self.preferences[editor]['geometry'][0] > screen_width and screens_count < 2:
                    self.preferences[editor]['geometry'][0] -= screen_width

                if self.preferences[editor]['geometry'][0] < 0:
                    self.preferences[editor]['geometry'][0] = 0
                if self.preferences[editor]['geometry'][1] < 0:
                    self.preferences[editor]['geometry'][1] = 0

                self.preferences[editor]['widget'] =  settings.value('%s/widget' % (editor))
            except:
                print("preferences for widget [%s]cannot be loaded" % (editor))
                pass

        for group in settings.childGroups():
            if group in ('selection', 'window'):
                continue
            settings.beginGroup(group)
            self.preferences[group] = {}
            for k in settings.childKeys():
                print(k)
                v: str = settings.value(k)
                print(v)
                if v == 'true':
                    value = True
                elif v == 'false':
                    value = False
                self.preferences[group][k] = value
        pprint(self.preferences)



    def save(self, preferences: dict[str, dict[str, Any] | str]):
        print(f"{__name__}.save preferences")
        pprint(preferences)

        settings = QSettings(
            QSettings.Format.IniFormat,
            QSettings.Scope.UserScope,
            "mco", self.tool)

        # (Mandatory) Viewer
        settings.setValue(
            'window/geometry',
            ':'.join(map(lambda x: "%d" % (x), preferences['window']['geometry']))
        )
        settings.setValue('window/screen', 0)


        # (Special) Selection
        settings.setValue('selection/episode', preferences['selection']['episode'])
        settings.setValue('selection/part', preferences['selection']['k_ch'])
        try:
            settings.setValue('selection/scene_no', preferences['selection']['scene_no'])
        except:
            pass

        w = 'geometry'
        if w in preferences:
            settings.beginGroup(w)
            for name, value in preferences['geometry'].items():
                settings.setValue(name, value)


        # # Other widgets (editors)
        # for editor in self.editors:
        #     if editor == 'selection':
        #         # Selection is a special case because and already saved before
        #         continue
        #     try:
        #         settings.setValue('%s/geometry' % (editor),
        #             ':'.join(map(lambda x: "%d" % (x), preferences[editor]['geometry'])))
        #         settings.setValue('%s/widget' % (editor), preferences[editor]['widget'])
        #     except:
        #         print("preferences for widget [%s] cannot be saved" % (editor))
        #         pass


    def get_preferences(self):
        return self.preferences
