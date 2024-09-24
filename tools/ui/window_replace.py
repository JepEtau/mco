from __future__ import annotations
from functools import partial
from pprint import pprint
from PySide6.QtCore import (
    Signal,
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
from .stylesheet import (
    set_stylesheet,
    set_widget_stylesheet,
)

from .ui.ui_window_replace import Ui_ReplaceWindow

from .widget_player_ctrl import PlayerCtrlWidget
from .widget_preview import PreviewWidget
from .widget_replace import ReplaceWidget
from .widget_selection import SelectionWidget

from logger import log

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from backend.controller_replace import ReplaceController



class ReplaceWindow(QMainWindow, Ui_ReplaceWindow):
    signal_k_ep_p_refreshed = Signal(dict)


    def __init__(
        self,
        ui=None,
        controller: ReplaceController=None
    ):
        super().__init__()
        self.widgets: dict[str, QWidget] = {}


        self.centralwidget = QWidget(self)
        self.verticalLayout_2 = QVBoxLayout(self.centralwidget)
        self.horizontalLayout = QHBoxLayout()
        self.verticalLayout = QVBoxLayout()

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


        # self.widget_selection.signal_selection_changed[dict].connect(
        #     self.event_selection_changed
        # )
        # self.signal_k_ep_p_refreshed[dict].connect(
        #     self.event_k_ep_p_refreshed
        # )



        # self.widget_replace.signal_preview_options_changed.connect(
        #     partial(self.event_preview_options_changed, 'replace')
        # )
        # self.widget_replace.signal_frame_selected[int].connect(
        #     self.event_move_to_frame_no
        # )

        # self.widget_player_ctrl.set_initial_options(p)
        # self.widget_player_ctrl.signal_button_pushed[str].connect(self.event_control_button_pressed)
        # self.widget_player_ctrl.signal_slider_moved[int].connect(self.event_move_to_frame_index)
        # self.widget_player_ctrl.signal_preview_options_changed.connect(partial(self.event_preview_options_changed, 'controls'))



        # for w in self.widgets.values():
        #     w.blockSignals(True)
        #     w.hide()
        #     w.blockSignals(False)

        self.show()
        # self.installEventFilter(self)
        set_stylesheet(self)


    def apply_user_preferences(self, user_preferences:dict):
        try:
            s = user_preferences['window']
            self.setGeometry(
                s['geometry'][0],
                s['geometry'][1],
                s['geometry'][2],
                s['geometry'][3]
            )
        except:
            self.setGeometry(0,0,1920,1080)
        self.setGeometry(50,50,1800,800)

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


    def get_preview_options(self):
        log.info("get preview options")
        preview_options = dict()
        for e, w in self.widgets.items():
            preview_options.update({e: w.get_preview_options()})
        return preview_options


    def event_preview_options_consolidated(self, new_preview_settings):
        # log.info("preview options have been consolidated, refresh widgets")
        self.widget_replace.refresh_preview_options(new_preview_settings)
        # self.widget_painter.refresh_preview_options(new_preview_settings)


    # def flush_image(self):
    #     log.info("flush image")
    #     del self.image
    #     self.image = None
    #     self.is_grabbing_split_line = False


