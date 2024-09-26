import os
import os.path

from pprint import pprint

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

        self.settings = QSettings(
            QSettings.Format.IniFormat,
            QSettings.Scope.UserScope,
            "mco", tool)

        # Default
        self.preferences = {
            'window': dict(),
            'selection': dict(),
        }

        for editor in self.editors:
            self.preferences.update({editor: dict()})

        # Default geometry
        screens = QApplication.screens()
        screens_count = len(screens)
        screen_width = screens[0].size().width()
        screen_height = screens[0].size().height()

        # (Mandatory) Main window
        if self.settings.contains('window/screen'):
            self.preferences['window']['screen'] = self.settings.value('window/screen')
        else:
            self.preferences['window']['screen'] = 0

        self.preferences['window']['geometry'] = [0, 0, screen_width, screen_height]
        try:
            self.preferences['window']['geometry'] = list(
                map(lambda x: int(x), self.settings.value('window/geometry').split(':'))
            )
        except:
            pass

        # Selection
        try:
            self.preferences['selection']['edition'] = ''
            if self.settings.contains('selection/edition'):
                self.preferences['selection']['edition'] = self.settings.value('selection/edition')
        except:
            self.preferences['selection']['edition'] = ''

        self.preferences['selection']['episode'] = ''
        if self.settings.contains('selection/episode'):
            ep_no_str = self.settings.value('selection/episode')
            self.preferences['selection']['episode'] = ep_no_str if ep_no_str == '' else int(ep_no_str)

        self.preferences['selection']['k_ch'] = ''
        if self.settings.contains('selection/part'):
            self.preferences['selection']['k_ch'] = self.settings.value('selection/part')

        self.preferences['selection']['scene_no'] = 0
        if self.settings.contains('selection/scene_no'):
            if self.settings.value('selection/scene_no') != '':
                self.preferences['selection']['scene_no'] = int(self.settings.value('selection/scene_no'))


        # use the preferences save in the file
        for editor in self.editors:
            try:
                self.preferences[editor]['geometry'] = list(map(lambda x: int(x),
                    self.settings.value('%s/geometry' % (editor)).split(':')))
                if self.preferences[editor]['geometry'][0] > screen_width and screens_count < 2:
                    self.preferences[editor]['geometry'][0] -= screen_width

                if self.preferences[editor]['geometry'][0] < 0:
                    self.preferences[editor]['geometry'][0] = 0
                if self.preferences[editor]['geometry'][1] < 0:
                    self.preferences[editor]['geometry'][1] = 0

                self.preferences[editor]['widget'] =  self.settings.value('%s/widget' % (editor))
            except:
                print("preferences for widget [%s]cannot be loaded" % (editor))
                pass


    def save(self, preferences):
        print(f"{__name__}.save preferences")
        pprint(preferences)

        # (Mandatory) Viewer
        self.settings.setValue(
            'window/geometry',
            ':'.join(map(lambda x: "%d" % (x), preferences['window']['geometry']))
        )
        self.settings.setValue('window/screen', 0)


        # (Special) Selection
        self.settings.setValue('selection/episode', preferences['selection']['episode'])
        self.settings.setValue('selection/part', preferences['selection']['k_ch'])
        try:
            self.settings.setValue('selection/scene_no', preferences['selection']['scene_no'])
        except:
            pass


        # Other widgets (editors)
        for editor in self.editors:
            if editor == 'selection':
                # Selection is a special case because and already saved before
                continue
            try:
                self.settings.setValue('%s/geometry' % (editor),
                    ':'.join(map(lambda x: "%d" % (x), preferences[editor]['geometry'])))
                self.settings.setValue('%s/widget' % (editor), preferences[editor]['widget'])
            except:
                print("preferences for widget [%s] cannot be saved" % (editor))
                pass


    def get_preferences(self):
        return self.preferences
