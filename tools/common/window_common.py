# -*- coding: utf-8 -*-
import sys

from filters.utils import FINAL_FRAME_HEIGHT
sys.path.append('../scripts')

import time

from pprint import pprint
from logger import log

from PySide6.QtCore import (
    QBasicTimer,
    QEvent,
    QPoint,
    QSize,
    Qt,
)
from PySide6.QtGui import (
    QCursor,
    QIcon,
    QPainter,
)
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMenu,
    QMessageBox,
)

from common.sylesheet import set_widget_stylesheet
from utils.common import FPS

PAINTER_MARGIN_LEFT = 30
PAINTER_MARGIN_TOP = 30

class Window_common(QMainWindow):

    def __init__(self, ui, controller):
        super(Window_common, self).__init__()


        window_icon = QIcon()
        window_icon.addFile("icons/icon_16.png", QSize(16,16))
        window_icon.addFile("icons/icon_24.png", QSize(24,24))
        window_icon.addFile("icons/icon_32.png", QSize(32,32))
        window_icon.addFile("icons/icon_48.png", QSize(48,48))
        window_icon.addFile("icons/icon_64.png", QSize(64,64))
        window_icon.addFile("icons/icon_128.png", QSize(128,128))
        window_icon.addFile("icons/icon_256.png", QSize(256,256))
        self.setWindowIcon(window_icon)

        self.setWindowFlags(Qt.Window)
        self.setStyleSheet("background-color: black")
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)


        # Add painter
        self.painter = QPainter()

        # Internal variables
        self.controller = controller

        widget_list = self.controller.get_widget_list()
        self.widgets = dict()
        for w in widget_list:
            self.widgets.update({w: None})

        self.image = None

        self.is_repainting = False
        self.is_activated = False
        self.is_closing = False
        self.discard_modifications = False

        self.current_editor = ''
        self.current_widget = self.current_editor

        # This is used  when the screen height is <= 1080 to display
        # the bottom side
        self.display_position_y = 0
        self.display_height = QApplication.screens()[0].size().height()

        self.current_frame_index = -1
        self.playing_frame_start_no = 0
        self.current_frame_no = 0
        self.timer = QBasicTimer()
        self.timer.stop()

        # Right click
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested[QPoint].connect(self.event_right_click)

        # Connect signals coming from model
        self.controller.signal_shotlist_modified[dict].connect(self.event_shotlist_modified)



    def set_initial_options(self, preferences:dict):
        s = preferences['viewer']
        if True:
            self.setGeometry(s['geometry'][0],
                s['geometry'][1],
                s['geometry'][2],
                s['geometry'][3])
        else:
            # For debug purpose
            self.setGeometry(s['geometry'][0],
                s['geometry'][1],
                1800,
                s['geometry'][3])
        try:
            log.info("set current editor: %s" % (s['current_editor']))
            self.set_current_editor(s['current_editor'])
        except:
            pass


    def event_show_fullscreen(self):
        self.blockSignals(True)
        # print("window_main: event_show_fullscreen (required for w11)")
        saved_current_editor = self.current_editor
        for w in self.widgets.values():
            w.blockSignals(True)
            w.showNormal()
            w.activateWindow()
            # w.blockSignals(False)

        # print("saved_current_editor", saved_current_editor)
        if saved_current_editor == '':
            saved_current_editor = self.controller.get_selectable_widgets()[0]
        self.set_current_editor(saved_current_editor)

        for w in self.widgets.values():
            w.blockSignals(False)

        self.widgets[saved_current_editor].blockSignals(True)
        self.widgets[saved_current_editor].showNormal()
        self.widgets[saved_current_editor].activateWindow()
        self.widgets[saved_current_editor].blockSignals(False)

        self.is_activated = True
        self.blockSignals(False)



    def event_selection_changed(self, selection):
        log.info("event: selection changed, update preview options")
        # Disable crop/resize edition if image is not >= HD
        self.current_frame_index = 0
        self.playing_frame_start_no = 0

        # if 'controls' in self.controller.get_widget_list():
        #     log.info("selection changed, reset slider position")
        #     self.widget_controls.set_slider_value(0)


        if 'geometry' in self.controller.get_widget_list():
            if selection['k_step'] in ['', 'deinterlace', 'pre_upscale', 'geometry']:
                self.widget_geometry.set_geometry_edition_enabled(False)
            else:
                self.widget_geometry.set_geometry_edition_enabled(True)
        # self.event_preview_options_changed('model')


    def event_editor_action(self, event='exit'):
        pass


    def closeEvent(self, event):
        # print("closeEvent")
        self.event_editor_action('exit')

    def event_close_without_saving(self):
        self.discard_modifications = True

    def event_close(self):
        # print("%s:event_close" % (__name__))
        if not self.is_closing:
            self.is_closing = True
            self.controller.exit()
            self.close_all_widgets()

    def close_all_widgets(self):
        # print("close_all_widgets")
        self.timer.stop()
        for widget in QApplication.topLevelWidgets():
            widget.close()
        self.close()
        # Not clean but avoid ghost processes: clean this
        sys.exit()


    def event_editor_action(self, event='exit'):
        # log.info("event=%s" % (event))
        # print("event=%s" % (event))
        if event == 'exit':
            if self.is_closing:
                return

            if self.discard_modifications:
                self.event_close()
                return

            if self.controller.model_database.is_db_modified():
                log.info("Changes are not saved")
                message_box = QMessageBox()
                message_box.setIcon(QMessageBox.Warning)
                message_box.setWindowTitle("Save before closing?")
                text = "Some modifications have not been saved:"
                for s in self.controller.get_modified_db():
                    text += "\n  - %s" % (s)
                message_box.setText(text)
                message_box.setInformativeText("Do you want to save before closing?")
                message_box.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
                message_box.setDefaultButton(QMessageBox.Save)
                set_widget_stylesheet(message_box)

                answer = message_box.exec()
                if answer == QMessageBox.Save:
                    self.signal_save_and_close.emit()
                elif answer == QMessageBox.Discard:
                    self.discard_modifications = True
                    self.event_close()
                return
            else:
                self.discard_modifications = True
                self.event_close()
        elif event == 'minimize':
            self.widget_selection.showMinimized()
            try: self.widget_controls.showMinimized()
            except: pass
            self.showMinimized()
        else:
            raise Exception("Error: action [%s] is deprecated, discard action")



    def get_preferences(self) -> dict:
        # Get preferences from children, merge them and return it
        preferences = {
            'viewer': {
                'screen': 0,
                'geometry': self.geometry().getRect(),
                'current_editor': self.current_editor,
            },
        }
        for e, w in self.widgets.items():
            preferences.update({e: w.get_preferences()})
        return preferences




    def event_shotlist_modified(self, shotlist):
        # episode/part has been changed
        enabled = True if len(shotlist['shots']) > 0 else False
        for widget_name in self.controller.get_widget_list():
            log.info("%s: set enabled: %s" % (self.widgets[widget_name].objectName(), 'true' if enabled else 'false'))

            if widget_name == 'geometry':
                if shotlist['k_step'] in ['deinterlace', 'pre_upscale']:
                    self.widgets[widget_name].set_edition_and_preview_enabled(False)
                else:
                    self.widgets[widget_name].set_edition_and_preview_enabled(enabled)

            if widget_name not in ['geometry']:
                try:
                    self.widgets[widget_name].set_widget_enabled(enabled)
                except:
                    pass


    def switch_display_side(self):
        if self.display_height > FINAL_FRAME_HEIGHT:
            return
        self.event_screen_position_changed('switch')
        self.repaint()


    def event_screen_position_changed(self, side):
        # log.info("change side to %s" % (side))
        if side == 'switch':
            new_side = 'bottom' if self.display_position_y == 0 else 'top'
        else:
            new_side = side

        if new_side == 'bottom':
            self.display_position_y = 1152 - FINAL_FRAME_HEIGHT + 2*PAINTER_MARGIN_TOP
        else:
            self.display_position_y = 0
        self.repaint()


    def get_current_widget(self):
        return self.current_widget



    def select_next_editor(self):
        # print("\nselect next editor from: %s" % (self.current_editor))
        selectable_widgets = self.controller.get_selectable_widgets()
        widget_index = selectable_widgets.index(self.current_editor)

        try:
            new_selected_widget_str = selectable_widgets[widget_index + 1]
        except:
            new_selected_widget_str = selectable_widgets[0]

        self.widgets[new_selected_widget_str].enter()
        self.widgets[new_selected_widget_str].activateWindow()

        # print("  changed to: %s" % (new_selected_widget_str))



    def set_current_editor(self, current_editor):
        # Set current widget and editor
        # print("set_current_editor: change widget from [%s] to [%s], editor from [%s] to [%s]" %
        #     (self.current_widget, current_editor, self.current_editor, current_editor))

        if current_editor == 'selection':
            # Do not select this widget
            return

        self.current_widget = current_editor

        for e, w in self.widgets.items():
            if self.current_editor == e:
                w.set_selected(False)

        self.current_editor = current_editor

        # Activate the selected editor widget
        for e, w in self.widgets.items():
            if self.current_editor == e:
                w.set_selected(True)
                break


    def event_selected_shots_changed(self, selection):
        self.event_preview_options_changed('selection')


    def event_preview_options_changed(self, widget):
        log.info("change preview: editor: %s" % (widget))
        preview_options = dict()
        for e, w in self.widgets.items():
            preview_options.update({e: w.get_preview_options()})
        self.signal_preview_options_changed.emit(preview_options)


    def event_ready_to_play(self, playlist_properties):
        log.info("ready to play")
        self.current_frame_index = 0
        self.playing_frame_count = playlist_properties['count']
        f = self.controller.get_frame_from_index(self.current_frame_index)
        self.display_frame(f)


    def event_move_to_frame_no(self, frame_index):
        # log.info("move to frame %d" % (frame_index))
        self.current_frame_index = frame_index
        f = self.controller.get_frame_from_index(self.current_frame_index)
        self.display_frame(f)


    def event_frame_no_selected(self, frame_no):
        log.info(f"move to frame {frame_no}")
        # index = frame_no - self.playing_frame_start_no
        log.warning("TODO: move to selected frame")
        self.widget_controls.update_slider_value(frame_no)


    def event_reload_frame(self):
        if self.current_frame_index == -1:
            return
        f = self.controller.get_frame_from_index(self.current_frame_index)
        self.display_frame(f)


    def event_control_button_pressed(self, action):
        if action == 'play':
            self.widget_selection.set_enabled(False)
            log.info("start playing")
            speed = self.widget_controls.get_playing_speed()
            self.timer_delay = int(1000/(FPS*speed))
            # self.timer_delay = 25
            print("timer: %dms" % (self.timer_delay))
            self.timer.start(self.timer_delay, Qt.PreciseTimer, self)
            self.now = time.time()

        elif action == 'pause':
            self.timer.stop()
            self.widget_selection.set_enabled(True)

        elif action == 'stop':
            self.timer.stop()
            self.widget_selection.set_enabled(True)
            self.event_move_to_frame_no(0)



    def timerEvent(self, e=None):
        now = time.time()
        elasped_time = 1000 * (now - self.now)
        if elasped_time > 45:
            print(int(elasped_time))
        self.now = now

        self.current_frame_index += 1
        if self.current_frame_index >= self.playing_frame_count:
            self.timer.stop()
            self.widget_controls.event_stop()
        else:
            self.widget_controls.set_playing_frame_properties(self.current_frame_index)
            f = self.controller.get_frame_from_index(self.current_frame_index)
            self.display_frame(f)


    def event_right_click(self, qpoint):
        cursor_position = QCursor.pos()
        pop_menu = QMenu(self)
        pop_menu.setStyleSheet("background-color: rgb(128, 128, 128);")
        action_exit = pop_menu.addAction('Exit')
        action_exit.triggered.connect(self.event_close)
        pop_menu.exec_(cursor_position)



    def changeEvent(self, event: QEvent) -> None:
        # print("\nwindow_main: changeEvent", event.type(), flush=True)
        if event.type() == QEvent.ActivationChange:
            # print("* QEvent.ActivationChange", flush=True)
            # print("\twindow state:", self.windowState(), flush=True)
            # print("\t is active? ", self.isActiveWindow(), flush=True)

            if self.windowState() == Qt.WindowState().WindowNoState:
                # print("\tWindowNoState -> show fullscreen")
                self.setWindowState(Qt.WindowActive)
                self.event_show_fullscreen()
                # print("-------------------------------------")
                event.accept()
                return True

            if self.windowState() & Qt.WindowState().WindowActive:
                # print("\tWindowMinimized -> show fullscreen")
                self.setWindowState(Qt.WindowActive)
                self.event_show_fullscreen()
                # print("-------------------------------------")
                event.accept()
                return True

            if (self.windowState() & Qt.WindowState().WindowMinimized
            and not self.isActiveWindow()):
                # print("\tWindowMinimized -> show fullscreen")
                self.setWindowState(Qt.WindowActive)
                self.event_show_fullscreen()
                # print("-------------------------------------")
                event.accept()
                return True

        return super().changeEvent(event)