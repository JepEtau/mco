from __future__ import annotations
from pprint import pprint
import time
from logger import log
from .stylesheet import (
    set_stylesheet,
    set_widget_stylesheet,
)
from utils.p_print import *

from PySide6.QtCore import (
    QEvent,
    QObject,
    QPoint,
    QSize,
    Qt,
    Signal,
    Slot,
)
from PySide6.QtGui import (
    QCursor,
    QIcon,
    QKeyEvent,
    QWheelEvent,
    QMouseEvent,
)
from PySide6.QtWidgets import (
    QTableWidgetItem,
    QWidget,
    QCheckBox,
    QHBoxLayout,
    QSlider,
)
from .ui.ui_widget_player_ctrl import Ui_PlayerControlWidget
from typing import TYPE_CHECKING, Any, Literal
if TYPE_CHECKING:
    from backend.replace_controller import ReplaceController
    from backend.geometry_controller import GeometryController
    from .window_replace import ReplaceWindow

from backend.frame_cache import Frame
from backend._types import AppType


class PlayerCtrlWidget(QWidget, Ui_PlayerControlWidget):
    signal_widget_selected = Signal(str)
    signal_button_pushed = Signal(str)
    signal_slider_moved = Signal(int)
    signal_flush_frame_cache = Signal()
    signal_speed_changed = Signal(float)


    def __init__(
        self,
        parent: QWidget | ReplaceWindow,
        controller,
        app_type: AppType
    ) -> None:
        super().__init__(parent)
        self.setupUi(self)

        self.slider_frames.setMinimumSize(QSize(600, 20))
        self.slider_frames.setMaximumHeight(30)
        self.slider_frames.setMaximum(200)
        self.slider_frames.setOrientation(Qt.Horizontal)
        self.slider_frames.setTickPosition(QSlider.NoTicks)
        self.slider_frames.setTickInterval(1)
        self.slider_frames.setFocusPolicy(Qt.NoFocus)
        self.setFocusPolicy(Qt.NoFocus)

        self.icon_play = QIcon()
        self.icon_play.addFile("./icons/blue/play.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_play_pause.setIcon(self.icon_play)

        self.icon_pause = QIcon()
        self.icon_pause.addFile("./icons/blue/pause.svg", QSize(), QIcon.Normal, QIcon.Off)
        # self.pushButton_play_pause.setIcon(self.icon_pause)

        self.label_ed_ep_part.clear()
        self.lineEdit_fno.clear()
        self.lineEdit_frame_no.clear()
        self.lineEdit_frame_index.clear()


        # variables
        self._parent = parent
        self.previous_position = None
        self.refresh_status('stopped')
        self.ticks = list()
        self.is_shift_key_pressed: bool = False
        # self.is_ctrl_key_pressed: bool = False
        self.frames_start = 0
        self.frame_nos = list()

        self.copied_frame_no = -1
        self.current_key_pressed = None
        self.preview_enabled: bool = True
        self.app_type: AppType = app_type


        # Signals
        self.pushButton_play_pause.toggled.connect(self.event_play_pause)
        self.pushButton_loop.toggled.connect(self.event_loop_toggled)
        self.pushButton_speed_0_5.toggled.connect(self.event_speed_changed)
        self.slider_frames.valueChanged.connect(self.event_slider_moved)

        self.controller: ReplaceController | GeometryController = controller
        self.controller.signal_ready_to_play.connect(
            self.event_refresh_slider
        )

        self.slider_frames.installEventFilter(self)
        self.installEventFilter(self)

        set_stylesheet(self)
        set_widget_stylesheet(self.label_ed_ep_part)
        self.slider_frames.update_stylesheet()

        self.pushButton_speed_0_5.setStyleSheet("""
            QPushButton {
                background-color: rgb(35, 35, 35);
                color: rgb(60, 60, 60);
                font-weight: bold;
                border: 0px;
            }
            QPushButton:checked {
                color: rgb(51, 102, 204);
                font-weight: bold;
                border: 0px;
            }
        """)

        self.normal_style: str = self.lineEdit_frame_no.styleSheet()
        self.replaced_style: str = self.normal_style.replace("rgb(220, 220, 220)", "yellow")
        self.initial_style: str = self.normal_style.replace("rgb(220, 220, 220)", "green")
        self.adjustSize()


    def get_user_preferences(self):
        preferences = {
            'loop': self.pushButton_loop.isChecked()
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


    def set_preview_enabled(self, enabled: bool):
        self.preview_enabled = enabled


    def set_enabled(self, enabled):
        self.pushButton_play_pause.setEnabled(enabled)
        self.slider_frames.setEnabled(enabled)


    def refresh_values(self, frame: Frame, original_frame: Frame):
        self.label_ed_ep_part.setText(f"{frame.src_scene_key}")
        if original_frame is not None:
            no, i = original_frame.no, original_frame.i
        else:
            no, i = frame.no, frame.i
        self.lineEdit_fno.setText(f"{no}")
        self.lineEdit_frame_index.setText(f"{i}")

        if self.app_type == 'replace':
            if original_frame is not None:
                self.lineEdit_fno.setStyleSheet(self.normal_style)
                self.lineEdit_frame_no.setText(f"{frame.no}")
                self.lineEdit_frame_no.setStyleSheet(self.replaced_style)

            elif self.controller.is_frame_used_for_replace(frame):
                self.lineEdit_fno.setStyleSheet(self.initial_style)
                self.lineEdit_frame_no.setStyleSheet(self.normal_style)
                self.lineEdit_frame_no.clear()

            else:
                self.lineEdit_fno.setStyleSheet(self.normal_style)
                self.lineEdit_frame_no.setStyleSheet(self.normal_style)
                self.lineEdit_frame_no.clear()


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


    def get_playing_speed(self) -> float:
        return 0.5 if self.pushButton_speed_0_5.isChecked() else 1.


    @Slot()
    def event_refresh_slider(self):
        playlist_properties = self.controller.playlist_properties()
        log.info(f"ready to play, refresh slider, count={playlist_properties.count}")
        self.slider_frames.blockSignals(True)
        self.slider_frames.setMaximum(playlist_properties.count - 1)
        self.frame_nos = playlist_properties.frame_nos
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
        self.ticks = playlist_properties.ticks

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
        self.lineEdit_frame_index.setText(f"-")
        # log.info(f"event, slider moved to frame {frame_no}")
        self.signal_slider_moved.emit(self.slider_frames.value())


    def event_previous_frame(self, delta=1):
        log.info(f"event_previous_frame: {self.slider_frames.value()}")
        self.move_slider_to(
            max(0, self.slider_frames.value() - delta))


    def event_next_frame(self, delta=1):
        log.info(f"event_next_frame: {self.slider_frames.value()}")
        self.move_slider_to(
            min(self.slider_frames.value() + delta, self.slider_frames.maximum()))


    def event_play_pause(self, checked):
        if not self.pushButton_play_pause.isChecked():
            log.info("event: pause")
            self.refresh_status('paused')
            self.pushButton_play_pause.setIcon(self.icon_play)
            # self.pushButton_play_pause.setFocus()
            self.slider_frames.blockSignals(False)
            self.signal_button_pushed.emit('pause')
        else:
            log.info("event: playing")
            self.refresh_status('playing')
            self.pushButton_play_pause.setIcon(self.icon_pause)
            # self.pushButton_play_pause.setFocus()
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


    def event_speed_changed(self):
        # if self.pushButton_speed_0_5.isChecked():
        print(f"speed: {0.5 if self.pushButton_speed_0_5.isChecked() else 1}")
        self.signal_speed_changed.emit(0.5)


    def event_loop_toggled(self, checked):
        pass


    def is_loop_enabled(self):
        return self.pushButton_loop.isChecked()


    def event_key_pressed(self, event: QKeyEvent) -> None:
        key = event.key()
        modifiers = event.modifiers()
        self.current_key_pressed = None
        # print(f"{__name__} key: {key}")

        # if modifiers & Qt.KeyboardModifier.ControlModifier:
        if key == Qt.Key.Key_F5:
            self.signal_flush_frame_cache.emit()
            return True

        # action
        if key in (Qt.Key.Key_Space, Qt.Key.Key_Enter):
            log.info("Space key")
            self.pushButton_play_pause.blockSignals(True)
            if self.status == 'playing':
                log.info("playing -> pause")
                self.pushButton_play_pause.setChecked(False)
                self.event_play_pause(False)
            else:
                log.info("pause/stop -> playing")
                self.pushButton_play_pause.setChecked(True)
                self.event_play_pause(False)
            self.pushButton_play_pause.blockSignals(False)
            return True

        if not self.slider_frames.isEnabled():
            # Do not test any other keys if the app. is playing
            return False

        elif key == Qt.Key.Key_Shift:
            self.is_shift_key_pressed = True
            print("widget player: shift key pressed")
            # if self._parent.is_editing_patches():
            # #     # log.info("shift key is pressed")
            #     print("editing, do not modify current frame")
            #     return False

        if (
            self.app_type == 'replace'
            and self._parent.is_editing_patches()
            and not self.is_shift_key_pressed
        ):
            return False

        # elif key == Qt.Key.Key_Control:
        #     print("Control")
        #     self.is_ctrl_key_pressed = True
        #     return False
        elif key == Qt.Key.Key_L:
            self.pushButton_loop.toggle()
            return True

        # modify slider value
        elif key in [Qt.Key.Key_Home, Qt.Key.Key_End]:
            self.slider_frames.keyPressEvent(event)
            return True

        elif key == Qt.Key.Key_Left:
            log.info("key_pressed: pressed frame")
            self.event_previous_frame()
            return True

        elif key == Qt.Key.Key_Right:
            log.info("key_pressed: next frame")
            self.event_next_frame()
            return True

        elif key == Qt.Key.Key_PageUp:
            self.event_previous_frame(10)
            return True

        elif key == Qt.Key.Key_PageDown:
            self.event_next_frame(10)
            return True
        return False


    def event_key_released(self, event: QKeyEvent) -> bool:
        key = event.key()
        # if key == Qt.Key.Key_Control:
        #     self.is_ctrl_key_pressed = False

        if key == Qt.Key.Key_Shift:
            # log.info("shift key is released")
            self.is_shift_key_pressed = False
            print("widget player: shift key released")
            self.current_key_pressed = None
            return True
        return False


    def event_wheel(self, event: QWheelEvent) -> bool:
        log.info("wheel event")
        if not self.slider_frames.isEnabled():
            print("controls: slider is disabled")
            return False

        # # Do not accept event if not in paused mode
        # if self.status == 'stopped':
        #     self.refresh_status('paused')
        #     return True

        if self.status not in ['paused', 'stopped']:
            print("controls: slider is disabled")
            return False

        # if self.app_type == 'replace':
        #     print(f"player control, editing: {self._parent.is_editing_patches()}, shift key: {self.is_shift_key_pressed}")
        if (
            self.app_type == 'geometry'
            or not self._parent.is_editing_patches()
            or (self._parent.is_editing_patches() and self.is_shift_key_pressed)
        ):
            # Select next/previous frame
            log.info("not editing or shift key")
            if event.angleDelta().y() > 0:
                self.event_previous_frame()
            elif event.angleDelta().y() < 0:
                self.event_next_frame()
            return True

        print("player ctrl, not for self")
        return False


    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        verbose = False
        if event.type() == QEvent.Type.KeyPress:
            if verbose:
                print(lightcyan(f"eventFilter: widget_{self.objectName()}: keypress {event.key()}"))
            if self.event_key_pressed(event):
                if verbose:
                    print(f"\taccepted")
                event.accept()
                return True
            else:
                if verbose:
                    print(f"\tforward to parent")
                return self._parent.keyPressEvent(event)

        elif event.type() == QEvent.Type.KeyRelease:
            if self.event_key_released(event):
                event.accept()
                return True
            else:
                return self._parent.keyPressEvent(event)

        elif event.type() == QEvent.Type.Wheel:
            print(lightcyan(time.time()), f"player ctrl, eventFilter: wheel")

            if self.event_wheel(event):
                event.accept()
                return True
            else:
                if verbose:
                    print(f"\twheel: send to parent")
                if self._parent.wheelEvent(event):
                    event.accept()
                    return

        elif event.type() == QMouseEvent:
            if self._parent.mousePressEvent(event):
                event.accept()
                return

        return super().eventFilter(watched, event)
