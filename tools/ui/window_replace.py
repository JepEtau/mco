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

from .ui.ui_window_replace import Ui_ReplaceWindow

from .widget_player_ctrl import PlayerCtrlWidget
from .widget_preview import PreviewWidget
from .widget_replace import ReplaceWidget
from .widget_selection import SelectionWidget

from logger import log

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from tools.backend.replace_controller import ReplaceController

from parsers import (
    db,
    get_fps,
)


class ReplaceWindow(QMainWindow, Ui_ReplaceWindow):
    signal_k_ep_p_refreshed = Signal(dict)
    signal_preview_modified = Signal(dict)


    def __init__(
        self,
        ui=None,
        controller: ReplaceController=None
    ):
        super().__init__()
        self.widgets: dict[str, QWidget] = {}
        self.controller: ReplaceController = controller

        self.centralwidget = QWidget(self)
        self.verticalLayout_2 = QVBoxLayout(self.centralwidget)
        self.horizontalLayout = QHBoxLayout()
        self.verticalLayout = QVBoxLayout()

        set_stylesheet(self)

        # Preview
        self.widget_preview = PreviewWidget(self.centralwidget)
        self.verticalLayout.addWidget(self.widget_preview)

        # Player control
        self.widget_player_ctrl = PlayerCtrlWidget(self, controller)
        self.verticalLayout.addWidget(self.widget_player_ctrl)
        self.horizontalLayout.addLayout(self.verticalLayout)

        # self.widget_replace = ReplaceWidget(self.centralwidget)
        # Replace
        self.widget_replace = ReplaceWidget(self, controller)
        self.widgets['replace'] = self.widget_replace
        self.horizontalLayout.addWidget(self.widget_replace)

        # Selection
        self.widget_selection = SelectionWidget(self, controller)
        self.widgets['selection'] = self.widget_selection
        self.horizontalLayout.addWidget(self.widget_selection)

        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.setCentralWidget(self.centralwidget)

        self.widget_player_ctrl.signal_button_pushed[str].connect(
            self.event_control_button_pressed
        )
        self.widget_player_ctrl.signal_slider_moved[int].connect(
            self.event_move_to_frame_index
        )

        self.current_frame_index = 0
        self.playing_frame_start_no = 0
        self.current_frame_no = 0
        self.timer: QBasicTimer = QBasicTimer()
        self.timer.stop()
        self.is_closing: bool = False

        self.widget_replace.signal_preview_toggled[bool].connect(
            self.preview_modified
        )
        self.widget_replace.signal_frame_selected[int].connect(
            self.event_move_to_frame_no
        )

        self.widget_player_ctrl.signal_slider_moved[int].connect(
            self.event_move_to_frame_index
        )
        self.controller.signal_ready_to_play.connect(self.event_ready_to_play)
        self.controller.signal_reload_frame.connect(self.event_reload_frame)
        self.controller.signal_error[str].connect(self.error_message)

        self.show()
        self.installEventFilter(self)


    def apply_user_preferences(self, user_preferences: dict):
        try:
            w: list[int] = user_preferences['window']
            self.setGeometry(*w['geometry'])
        except:
            self.setGeometry(0,0,1920,1080)
        self.widget_replace.apply_user_preferences(user_preferences)
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

    def event_selection_scenes_refreshed(self):
        pass


    def refresh_available_selection(self, selection: dict):
        # self.widget_replace.
        print("refresh selection selection")
        # pprint(selection)
        self.widget_selection.refresh_available_selection(selection)



    def event_edition_started(self):
        log.info(f"Edition started")
        self.widget_selection.edition_started(True)


    @Slot(bool)
    def preview_modified(self, enabled: bool) -> None:
        log.info(f"widget preview changed to {enabled}")

        self.signal_preview_modified.emit({'enabled': enabled})

        self.preview_enabled = enabled
        self.widget_player_ctrl.set_preview_enabled(enabled)
        self.display_frame()

    # def get_preview_options(self):
    #     log.info("get preview options")
    #     preview_options = dict()
    #     for e, w in self.widgets.items():
    #         preview_options.update({e: w.get_preview_options()})
    #     return preview_options


    # def event_preview_options_consolidated(self, new_preview_settings):
    #     # log.info("preview options have been consolidated, refresh widgets")
    #     self.widget_replace.refresh_preview_options(new_preview_settings)
    #     # self.widget_painter.refresh_preview_options(new_preview_settings)


    def display_frame(self):
        frame, original_frame = self.controller.get_frame_at_index(self.current_frame_index)
        self.widget_replace.set_current_frame(frame, original_frame)
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
        log.info(f"move to frame {frame_index}")
        self.current_frame_index = frame_index
        self.display_frame()


    def event_move_to_frame_no(self, frame_no):
        index = self.controller.get_index_from_frame_no(frame_no)
        # log.info(f"move to frame {frame_no} at index {index}")
        self.widget_player_ctrl.move_slider_to(index)


    @Slot(str)
    def error_message(self, message: str):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Error")
        msg.setInformativeText(message)
        msg.setWindowTitle("Error")
        msg.exec_()


    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = event.key()
        modifiers = event.modifiers()
        self.current_key_pressed = None
        print(f"{__name__} received: {key}")

        for w in (
            self.widget_player_ctrl,
            self.widget_replace,
            # self.widget_preview,
            self.widget_selection
        ):
            if w.event_key_pressed(event):
                print(f"{__name__} {key} forwarded to {w.objectName()}")
                return True
        return super().keyPressEvent(event)


    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        for w in (
            self.widget_player_ctrl,
            self.widget_replace,
            # self.widget_preview,
            self.widget_selection
        ):
            try:
                w.event_key_released(event)
            except:
                pass

        return super().keyReleaseEvent(event)



    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Wheel:
            for w in (
                self.widget_player_ctrl,
                self.widget_replace,
                # self.widget_preview,
                # self.widget_selection
            ):
                if w.event_wheel(event):
                    return True

        return super().eventFilter(watched, event)
