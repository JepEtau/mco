from __future__ import annotations
from pprint import pprint
import time
from PySide6.QtCore import (
    Signal,
    Slot,
    QBasicTimer,
    Qt,
    QEvent,
    QObject,
    Slot,
)
from PySide6.QtGui import (
    QKeyEvent,
)
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMenu,
    QMessageBox,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
)

from utils.p_print import red

from .stylesheet import (
    set_stylesheet,
)

from .widget_player_ctrl import PlayerCtrlWidget
from .widget_preview import PreviewWidget
from .widget_selection import SelectionWidget

from logger import log

from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from backend.common_controller import CommonController
from backend._types import AppType
from parsers import (
    db,
    get_fps,
)



class CommonWindow(QMainWindow):
    signal_k_ep_p_refreshed = Signal(dict)
    signal_preview_modified = Signal(dict)


    def __init__(
        self,
        controller = None,
        app_type: AppType = '',
    ):
        super().__init__()
        self.controller: type[CommonController] = controller
        self.widgets: dict[str, QWidget] = {}

        self.current_frame_index = 0
        self.playing_frame_start_no = 0
        self.current_frame_no = 0
        self.timer: QBasicTimer = QBasicTimer()
        self.timer.stop()
        self.is_closing: bool = False


        self.app_type: AppType = app_type
        self.centralwidget = QWidget(self)

        # Common widgets
        self.widget_preview = PreviewWidget(self.centralwidget)
        self.widget_player_ctrl = PlayerCtrlWidget(
            self, controller, app_type=app_type
        )
        self.widget_selection = SelectionWidget(
            self, controller, app_type=app_type
        )

        self.widgets['selection'] = self.widget_selection

        self.widget_player_ctrl.signal_button_pushed[str].connect(
            self.event_control_button_pressed
        )
        self.widget_player_ctrl.signal_slider_moved[int].connect(
            self.event_move_to_frame_index
        )

        self.widget_player_ctrl.signal_slider_moved[int].connect(
            self.event_move_to_frame_index
        )
        self.controller.signal_ready_to_play.connect(self.event_ready_to_play)
        self.controller.signal_reload_frame.connect(self.event_reload_frame)
        self.controller.signal_error[str].connect(self.error_message)


    def apply_user_preferences(self, user_preferences: dict):
        try:
            w: list[int] = user_preferences['window']
            self.setGeometry(*w['geometry'])
        except:
            self.setGeometry(0,0,1920,1080)
        self.widget_selection.apply_user_preferences(user_preferences)


    def get_user_preferences(self) -> dict:
        # Get preferences from children, merge them and return it
        preferences = {
            'window': {
                'screen': 0,
                'geometry': self.geometry().getRect(),
            },
        }
        for e, w in self.widgets.items():
            preferences.update({e: w.get_user_preferences()})

        return preferences


    def closeEvent(self, event):
        # print("closeEvent")
        # self.event_editor_action('exit')
        self.event_close()


    def event_close(self):
        # print("%s:event_close" % (__name__))
        if not self.is_closing:
            self.is_closing = True
            self.timer.stop()
            self.controller.exit()
            return
        self.close()


    def refresh_available_selection(self, selection: dict):
        print("refresh selection selection")
        self.widget_selection.refresh_available_selection(selection)


    def display_frame(self):
        frame, original_frame = self.controller.get_frame_at_index(self.current_frame_index)
        self.widget_player_ctrl.refresh_values(frame, original_frame)
        self.widget_preview.display_frame(frame)


    @Slot()
    def event_reload_frame(self):
        log.info("reload frame")
        self.display_frame()


    @Slot()
    def event_ready_to_play(self):
        log.info("ready to play")
        playlist_properties = self.controller.playlist_properties()
        self.current_frame_index = 0
        self.playing_frame_count = playlist_properties.count
        f = self.controller.get_frame_at_index(self.current_frame_index)
        self.display_frame(f)


    @Slot(str)
    def event_control_button_pressed(self, action: str):
        if action == 'play':
            self.widget_selection.set_enabled(False)
            log.info("start playing")
            speed = self.widget_player_ctrl.get_playing_speed()
            self.timer_delay = int(1000/(get_fps(db)*speed))
            self.timer.start(self.timer_delay, Qt.TimerType.PreciseTimer, self)
            self.now = time.time()

        elif action == 'pause':
            self.timer.stop()
            self.widget_selection.set_enabled(True)

        elif action == 'stop':
            self.timer.stop()
            self.widget_selection.set_enabled(True)
            self.event_move_to_frame_index(0)


    def timerEvent(self, e=None):
        now = time.time()
        elasped_time = 1000 * (now - self.now)
        if elasped_time > 45:
            print(int(elasped_time))
        self.now = now

        self.current_frame_index += 1
        if self.current_frame_index >= self.playing_frame_count:
            if self.widget_player_ctrl.is_loop_enabled():
                # in loop mode restart from beginning
                self.current_frame_index = 0
            else:
                self.timer.stop()
                self.widget_player_ctrl.event_stop()
                return
        self.widget_player_ctrl.set_playing_frame_properties(self.current_frame_index)
        self.display_frame()


    @Slot()
    def event_ready_to_play(self):
        log.info("ready to play")
        playlist_properties = self.controller.playlist_properties()
        self.current_frame_index = 0
        self.playing_frame_count = playlist_properties.count
        self.display_frame()


    def event_move_to_frame_index(self, frame_index):
        # log.info(f"move to frame {frame_index}")
        self.current_frame_index = frame_index
        self.display_frame()


    def event_move_to_frame_no(self, frame_no):
        index = self.controller.get_index_from_frame_no(frame_no)
        # log.info(f"move to frame {frame_no} at index {index}")
        self.widget_player_ctrl.move_slider_to(index)


    @Slot(str)
    def error_message(self, message: str):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setText("Error")
        msg.setInformativeText(message)
        msg.setWindowTitle("Error")
        msg.exec_()
