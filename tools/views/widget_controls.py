# -*- coding: utf-8 -*-
import sys

from pprint import pprint
from logger import log

from PySide6.QtCore import (
    QEvent,
    QObject,
    QPoint,
    QSize,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QCursor,
    QIcon,
    QKeyEvent,
    QWheelEvent,
    QMouseEvent,
)
from PySide6.QtWidgets import (
    QSlider,
    QWidget,
)
from utils.pretty_print import *

from utils.stylesheet import (
    set_stylesheet,
    set_widget_stylesheet,
)
from .ui.widget_controls_ui import Ui_widget_controls
from controllers.controller import Controller_video_editor


class Widget_controls(QWidget, Ui_widget_controls):
    signal_widget_selected = Signal(str)
    signal_button_pushed = Signal(str)
    signal_slider_moved = Signal(int)
    signal_frame_replaced = Signal(dict)
    signal_preview_options_changed = Signal(dict)
    signal_save_modifications = Signal(bool)
    signal_close = Signal()

    def __init__(self, parent, controller:Controller_video_editor):
        super(Widget_controls, self).__init__()

        self.setupUi(self)
        self.controller = controller
        self.__parent = parent
        self.setObjectName('controls')
        # Setup and patch ui
        self.setAutoFillBackground(True)
        self.setWindowFlags(Qt.Tool)
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setWindowModality(Qt.NonModal)

        self.slider_frames.setMinimumSize(QSize(1400, 30))
        self.slider_frames.setMaximum(200)
        self.slider_frames.setOrientation(Qt.Horizontal)
        self.slider_frames.setTickPosition(QSlider.NoTicks)
        self.slider_frames.setTickInterval(1)
        self.slider_frames.setFocusPolicy(Qt.NoFocus)

        self.set_enabled(False)

        self.icon_play = QIcon()
        self.icon_play.addFile("tools/icons/blue/play.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_play_pause.setIcon(self.icon_play)

        self.icon_pause = QIcon()
        self.icon_pause.addFile("tools/icons/blue/pause.svg", QSize(), QIcon.Normal, QIcon.Off)
        # self.pushButton_play_pause.setIcon(self.icon_pause)

        self.label_ed_ep_part.clear()
        self.lineEdit_frame_no.clear()
        self.lineEdit_frame_index.clear()

        # variables
        self.previous_position = None
        self.refresh_status('stopped')
        self.ticks = list()
        self.is_shift_key_pressed = False
        self.frames_start = 0
        self.frame_nos = list()

        self.copied_frame_no = -1
        self.backup_preview_options = dict()
        self.current_key_pressed = None

        # Signals
        self.pushButton_play_pause.toggled.connect(self.event_play_pause)
        self.pushButton_loop.toggled.connect(self.event_loop_toggled)
        self.slider_frames.valueChanged.connect(self.event_slider_moved)

        self.controller.signal_ready_to_play[dict].connect(self.event_refresh_slider)

        self.slider_frames.installEventFilter(self)
        self.installEventFilter(self)

        self.set_selected(False)
        set_stylesheet(self)
        set_widget_stylesheet(self.label_ed_ep_part)
        self.adjustSize()


    def leave_widget(self):
        pass


    def closeEvent(self, event):
        self.signal_close.emit()

    def event_close(self):
        self.close()


    def set_selected(self, is_selected):
        pass


    def get_preferences(self):
        preferences = {
            'geometry': self.geometry().getRect(),
            'widget': {
                'loop': self.pushButton_loop.isChecked()
            },
        }
        return preferences


    def set_initial_options(self, preferences:dict):
        log.info("set_initial_options")
        s = preferences['controls']

        self.pushButton_loop.blockSignals(True)
        try:
            w = preferences[self.objectName()]['widget']
            self.pushButton_loop.setChecked(w['loop']['enabled'])
        except:
            self.pushButton_loop.setChecked(False)
        self.pushButton_loop.blockSignals(False)


        self.adjustSize()

        # Geometry
        self.move(s['geometry'][0], s['geometry'][1])


    def get_preview_options(self):
        return None

    def set_widget_enabled(self, enabled):
        self.setEnabled(enabled)

    def set_enabled(self, enabled):
        self.pushButton_play_pause.setEnabled(enabled)
        self.slider_frames.setEnabled(enabled)


    def refresh_values(self, frame:dict):
        self.label_ed_ep_part.setText(f"{frame['k_ed']}:{frame['k_ep']}:{frame['k_part']}:{frame['shot_no']:03d}")
        self.lineEdit_frame_no.setText(f"{frame['frame_no']}")
        self.lineEdit_frame_index.setText(f"{frame['index']}")


    def refresh(self, values:dict):
        self.lineEdit_frame_no.setText(f"{values['frame_no']}")
        self.lineEdit_frame_index.setText(f"{values['frame_index']}")
        self.slider_frames.setMaximum(values['count'])
        self.slider_frames.setTickPosition(values['position'])
        self.refresh_status(values['status'])


    def refresh_status(self, status:str):
        self.status = status
        if self.status == 'stopped' or self.status == 'paused':
            self.pushButton_play_pause.setEnabled(True)
            self.slider_frames.setEnabled(True)
        elif self.status == 'playing':
            self.pushButton_play_pause.setEnabled(True)
            self.slider_frames.setEnabled(False)


    def move_slider_to(self, index:int):
        # log.info(f"move_slider_to: {index}")
        if index >= len(self.frame_nos):
            log.info("out of range: %d" % (index))
            index = len(self.frame_nos) - 1
        self.slider_frames.setValue(index)


    def set_slider_value(self, value):
        # log.info(f"set_slider_value: {value}")
        self.slider_frames.blockSignals(True)
        self.move_slider_to(value)
        self.slider_frames.blockSignals(False)



    def set_playing_frame_properties(self, current_index):
        self.move_slider_to(current_index)


    def set_slider_to_previous_tick(self):
        current_clider_value = self.slider_frames.value()
        for i in range(len(self.ticks) - 1):
            if self.ticks[i] <= current_clider_value <= self.ticks[i+1]:
                break
        self.move_slider_to(self.ticks[i])


    def set_slider_to_following_tick(self):
        current_clider_value = self.slider_frames.value()
        for i in range(len(self.ticks) - 1):
            if self.ticks[i] <= current_clider_value < self.ticks[i+1]:
                break
        self.move_slider_to(self.ticks[i+1])


    def get_playing_speed(self):
        return 1


    def event_refresh_slider(self, playlist_properties):
        log.info("ready to play, refresh slider")

        self.slider_frames.blockSignals(True)
        self.slider_frames.setMaximum(playlist_properties['count'] - 1)
        self.frame_nos = playlist_properties['frame_nos']
        self.copied_frame_no = -1

        self.slider_frames.setValue(0)
        try:
            self.lineEdit_frame_no.setText(f"{self.frame_nos[0]}")
        except:
            self.lineEdit_frame_no.clear()

        try:
            self.lineEdit_frame_index.setText(f"0")
        except:
            self.lineEdit_frame_index.clear()

        # Save the list of tick position
        self.ticks = playlist_properties['ticks']

        self.slider_frames.blockSignals(False)
        self.set_enabled(True)
        self.clearFocus()


    def event_slider_moved(self, value):
        # log.info(f"event, slider moved to {value}")
        if self.status == 'paused':
            self.pushButton_play_pause.blockSignals(True)
            self.pushButton_play_pause.setChecked(True)
            self.pushButton_play_pause.setIcon(self.icon_play)
            self.pushButton_play_pause.blockSignals(False)
        frame_index = self.slider_frames.value()
        frame_no = self.frame_nos[frame_index]
        self.lineEdit_frame_no.setText(f"{frame_no}")
        self.lineEdit_frame_index.setText(f"frame_index")
        # log.info(f"event, slider moved to frame {frame_no}")
        self.signal_slider_moved.emit(self.slider_frames.value())


    def event_previous_frame(self, delta=1):
        # log.info("event_previous_frame: %d" % (self.slider_frames.value()))
        self.move_slider_to(
            max(0, self.slider_frames.value() - delta))


    def event_next_frame(self, delta=1):
        self.move_slider_to(
            min(self.slider_frames.value() + delta, self.slider_frames.maximum()))


    def event_play_pause(self, checked):
        if not self.pushButton_play_pause.isChecked():
            log.info("event: pause")
            self.refresh_status('paused')
            self.pushButton_play_pause.setIcon(self.icon_play)
            self.pushButton_play_pause.setFocus()
            self.slider_frames.blockSignals(False)
            self.signal_button_pushed.emit('pause')
        else:
            log.info("event: playing")
            self.refresh_status('playing')
            self.pushButton_play_pause.setIcon(self.icon_pause)
            self.pushButton_play_pause.setFocus()
            self.slider_frames.blockSignals(True)
            self.signal_button_pushed.emit('play')



    def event_stop(self):
        self.refresh_status('stopped')
        self.pushButton_play_pause.blockSignals(True)
        self.pushButton_play_pause.setChecked(False)
        self.pushButton_play_pause.setIcon(self.icon_play)
        self.pushButton_play_pause.blockSignals(False)
        self.slider_frames.blockSignals(True)
        self.slider_frames.setValue(0)
        self.slider_frames.blockSignals(False)
        # self.slider_frames.setFocus()
        self.signal_button_pushed.emit('stop')

    def toggle_play_pause(self):
        log.info(f"Toggle play/pause, current status: {self.status}")
        self.pushButton_play_pause.blockSignals(True)
        if self.status == 'playing':
            log.info("playing -> pause")
            self.refresh_status('paused')
            self.pushButton_play_pause.setChecked(False)
            self.pushButton_play_pause.setIcon(self.icon_play)
            self.pushButton_play_pause.setFocus()
            self.slider_frames.blockSignals(False)
            self.signal_button_pushed.emit('pause')
        else:
            log.info("pause/stop -> playing")
            self.refresh_status('playing')
            self.pushButton_play_pause.setChecked(True)
            self.pushButton_play_pause.setIcon(self.icon_pause)
            self.pushButton_play_pause.setFocus()
            self.slider_frames.blockSignals(True)
            self.signal_button_pushed.emit('play')
        self.pushButton_play_pause.blockSignals(False)


    def event_loop_toggled(self, checked):
        pass

    def is_loop_enabled(self):
        return self.pushButton_loop.isChecked()

    def event_key_pressed(self, event:QKeyEvent) -> bool:
        key = event.key()
        modifiers = event.modifiers()
        self.current_key_pressed = None

        # action
        if key == Qt.Key.Key_Space:
            log.info("Space key")
            if self.status == 'playing':
                log.info("playing -> pause")
                self.pushButton_play_pause.setChecked(False)
                self.event_play_pause(False)
            else:
                log.info("pause/stop -> playing")
                self.pushButton_play_pause.setChecked(True)
                self.event_play_pause(False)
            return True

        if not self.slider_frames.isEnabled():
            # Do not test any other keys if the app. is playing
            return False

        elif key == Qt.Key.Key_Shift:
            # log.info("shift key is pressed")
            self.is_shift_key_pressed = True
            return True

        # modify slider value
        elif key in [Qt.Key.Key_Home, Qt.Key.Key_End]:
            self.slider_frames.keyPressEvent(event)
            return True
        elif key == Qt.Key.Key_Left:
            self.event_previous_frame()
            return True
        elif key == Qt.Key.Key_Right:
            self.event_next_frame()
            return True
        elif key == Qt.Key.Key_Up or key == Qt.Key.Key_PageUp:
            self.event_previous_frame(10)
            return True
        elif key == Qt.Key.Key_Down or key == Qt.Key.Key_PageDown:
            self.event_next_frame(10)
            return True



    def event_key_released(self, event:QKeyEvent) -> bool:
        key = event.key()
        if key == Qt.Key.Key_Shift:
            # log.info("shift key is released")
            self.is_shift_key_pressed = False
            self.current_key_pressed = None
            return True
        return False


    def event_wheel(self, event: QWheelEvent) -> bool:
        if not self.slider_frames.isEnabled():
            print("\controls: slider is disabled")
            return False

        # # Do not accept event if not in paused mode
        # if self.status == 'stopped':
        #     self.refresh_status('paused')
        #     return True

        if self.status not in ['paused', 'stopped']:
            print("\controls: slider is disabled")
            return False

        if self.is_shift_key_pressed:
            # move to next/previous tick
            if event.angleDelta().y() > 0:
                self.set_slider_to_previous_tick()
            elif event.angleDelta().y() < 0:
                self.set_slider_to_following_tick()
            return True
        else:
            # Select next/previous frame
            if event.angleDelta().y() > 0:
                self.event_previous_frame()
            elif event.angleDelta().y() < 0:
                self.event_next_frame()
            return True

        return False


    def mousePressEvent(self, event:QMouseEvent) -> bool:
        self.previous_position = QCursor().pos()


    def mouseMoveEvent(self, event):
        if self.previous_position is not None:
            cursor_position = QCursor().pos()
            delta = QPoint(cursor_position - self.previous_position)
            self.previous_position = cursor_position
            self.move(self.pos() + delta)
            event.accept()



    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.KeyPress:
            print_lightcyan(f"eventFilter: widget_{self.objectName()}: keypress {event.key()}")
            if self.event_key_pressed(event):
                print(f"\taccepted")
                event.accept()
                return True
            else:
                print(f"\tforward to parent")
                return self.__parent.event_key_pressed(event)

        elif event.type() == QEvent.Type.KeyRelease:
            if self.event_key_released(event):
                event.accept()
                return True
            else:
                return self.__parent.event_key_released(event)

        elif event.type() == QEvent.Type.Wheel:
            print_lightcyan(f"eventFilter: widget_controls: wheel")
            if self.event_wheel(event):
                print(f"\twheel: accepted")
                event.accept()
                return True
            else:
                print(f"\twheel: send to parent")
                if self.__parent.event_wheel(event):
                    event.accept()
                    return

        return super().eventFilter(watched, event)
    # def eventFilter(self, watched: QObject, event: QEvent) -> bool:
    #     # print("  * eventFilter: widget_%s: " % (self.objectName()), event.type())
    #     if event.type() == QEvent.Wheel:
    #         return self.wheel_event(event)
    #

