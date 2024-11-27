from __future__ import annotations
from dataclasses import dataclass
from functools import partial
from pprint import pprint
from logger import log
from typing import TYPE_CHECKING, Any
from utils.p_print import *

from PySide6.QtCore import (
    Qt,
    Signal,
    Slot,
)
from PySide6.QtGui import(
    QKeyEvent,
    QWheelEvent,
)
from PySide6.QtWidgets import (
    QTableWidgetItem,
    QWidget,
    QApplication,
    QPushButton,
)

from .ui.ui_widget_dsr import Ui_DsrWidget
from .stylesheet import set_stylesheet
if TYPE_CHECKING:
    from backend.replace_controller import ReplaceController
from backend.frame_cache import Frame
from backend._types import DsrAction
from parsers import (
    SceneGeometry,
    MaskShape,
)


class DsrWidget(QWidget, Ui_DsrWidget):
    signal_save = Signal()
    signal_discard = Signal()
    signal_undo = Signal()
    signal_preview_toggled = Signal(bool)
    signal_edition_started = Signal()

    signal_dsr_selected = Signal(DsrAction)
    signal_dsr_modified = Signal(DsrAction)
    signal_dsr_removed = Signal(dict)

    def __init__(self, ui, controller):
        super().__init__(ui)
        self.setupUi(self)

        self.controller: ReplaceController = controller
        self.ui = ui
        self.setObjectName('dsr')

        self.shape_buttons: dict[MaskShape, QPushButton] = {
            'circle': self.pushButton_circle,
            'ellipse': self.pushButton_ellipse,
            'oblong': self.pushButton_oblong,
        }
        self.shape_buttons['ellipse'].setChecked(True)
        for shape_name, b in self.shape_buttons.items():
            b.pressed.connect(partial(self.event_shape_type_modified, shape_name))

        set_stylesheet(self)
        self.adjustSize()


    def block_signals(self, enabled):
        self.pushButton_set_preview.blockSignals(enabled)
        self.pushButton_discard.blockSignals(enabled)
        self.pushButton_save.blockSignals(enabled)
        for b in self.shape_buttons.values():
            b.blockSignals(enabled)


    def apply_user_preferences(self, preferences: dict):
        self.block_signals(True)

        self.block_signals(False)
        self.adjustSize()


    def get_user_preferences(self) -> dict[str, Any]:
        return {}


    def event_set_preview_toggled(self, is_checked: bool=False):
        log.info(f"widget preview changed to {is_checked}")
        self.signal_preview_toggled.emit(is_checked)


    def event_shape_type_modified(self, shape_name):
        for b in self.shape_buttons.values():
            b.blockSignals(True)

        for name, button in self.shape_buttons.items():
            if name != shape_name:
                button.setChecked(False)

        for b in self.shape_buttons.values():
            b.blockSignals(False)


    def get_current_shape(self) -> MaskShape:
        for name, button in self.shape_buttons.items():
            if button.isChecked():
                return name


