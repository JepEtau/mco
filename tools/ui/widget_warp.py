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
)
from PySide6.QtWidgets import (
    QTableWidgetItem,
    QWidget,
    QPushButton,
)

from .ui.ui_widget_warp import Ui_WarpWidget
from .stylesheet import set_stylesheet
if TYPE_CHECKING:
    from backend.replace_controller import ReplaceController
from backend.frame_cache import Frame
from backend._types import CurrentFrame, WarpAction
from parsers import (
    Warp
)

class WarpWidget(QWidget, Ui_WarpWidget):
    signal_save = Signal()
    signal_discard = Signal()
    signal_undo = Signal()
    signal_preview_toggled = Signal(bool)
    signal_warp_values_changed = Signal(WarpAction)


    def __init__(self, ui, controller: ReplaceController):
        super().__init__(ui)
        self.setupUi(self)

        self.controller: ReplaceController = controller
        self.ui = ui
        self.setObjectName('warp')

        self._is_modified: bool = False
        self.current_frame: CurrentFrame | None = None

        self.checkBox_enabled.setChecked(False)
        self.pushButton_set_preview.setChecked(True)
        self.set_default_values()

        self.checkBox_enabled.toggled.connect(self.event_settings_changed)
        self.pushButton_set_preview.toggled.connect(self.event_settings_changed)
        self.radioButton_bf.toggled.connect(self.event_settings_changed)
        self.radioButton_knn.toggled.connect(self.event_settings_changed)
        self.spinBox_knn_ratio.valueChanged.connect(self.event_settings_changed)
        self.spinBox_max_distance_ratio.valueChanged.connect(self.event_settings_changed)
        self.radioButton_next.toggled.connect(self.event_settings_changed)
        self.radioButton_prev.toggled.connect(self.event_settings_changed)
        self.pushButton_default_values.released.connect(self.event_default_values)

        set_stylesheet(self)
        self.adjustSize()


    def set_default_values(self) -> None:
        self.radioButton_knn.setChecked(True)
        self.spinBox_knn_ratio.setValue(75)
        self.spinBox_max_distance_ratio.setValue(20)
        self.radioButton_next.setChecked(True)


    def block_signals(self, enabled):
        # self.pushButton_set_preview.blockSignals(enabled)
        # self.pushButton_discard.blockSignals(enabled)
        # self.pushButton_save.blockSignals(enabled)
        # for b in self.shape_buttons.values():
        #     b.blockSignals(enabled)
        self.pushButton_set_preview.blockSignals(enabled)
        self.checkBox_enabled.blockSignals(enabled)
        self.radioButton_bf.blockSignals(enabled)
        self.radioButton_knn.blockSignals(enabled)
        self.spinBox_knn_ratio.blockSignals(enabled)
        self.spinBox_max_distance_ratio.blockSignals(enabled)
        self.radioButton_next.blockSignals(enabled)
        self.radioButton_prev.blockSignals(enabled)
        self.pushButton_default_values.blockSignals(enabled)


    def apply_user_preferences(self, preferences: dict):
        self.block_signals(True)

        self.block_signals(False)
        self.adjustSize()


    def get_user_preferences(self) -> dict[str, Any]:
        return {}


    def event_key_released(self, event: QKeyEvent) -> bool:
        return False


    def event_key_pressed(self, event: QKeyEvent) -> bool:
        key, modifiers = event.key(), event.modifiers()
        # print(f"{time.time()} {__name__}.event_key_pressed: {key}, modifiers={modifiers}")
        if key in (Qt.Key.Key_F3, ):
            print("waepenabled")
            return True

        return False


    def is_modified(self) -> bool:
        return self._is_modified


    def set_enabled(self, enabled: bool) -> None:
        self.radioButton_knn.setEnabled(enabled)
        self.radioButton_bf.setEnabled(enabled)
        self.spinBox_knn_ratio.setEnabled(enabled)
        self.spinBox_max_distance_ratio.setEnabled(enabled)
        self.radioButton_next.setEnabled(enabled)
        self.radioButton_prev.setEnabled(enabled)
        self.pushButton_default_values.setEnabled(enabled)
        if enabled:
            self.spinBox_knn_ratio.setEnabled(self.radioButton_knn.isChecked())


    def set_current_frame(self, frame: Frame, original_frame: Frame) -> None:
        if original_frame is not None:
            # Frame replaced
            self.current_frame = CurrentFrame(no=frame.by, frame=original_frame)
            # Disable action
            self.set_enabled(False)
            self.checkBox_enabled.setEnabled(False)
        else:
            self.current_frame = CurrentFrame(no=frame.no, frame=frame)
            self.set_enabled(True)
            self.checkBox_enabled.setEnabled(True)
        print(red(f"WARP: set_current_frame: {self.current_frame.no}"))
        pprint(self.current_frame)

        self.block_signals(True)
        if self.current_frame.frame.warp is not None:
            warp: Warp = self.current_frame.frame.warp
            self.checkBox_enabled.setChecked(warp.enabled)
            self.radioButton_knn.setChecked(bool(warp.matcher == 'knn'))
            self.spinBox_knn_ratio.setValue(int(warp.knn_ratio * 100))
            self.spinBox_max_distance_ratio.setValue(int(warp.max_distance_ratio * 100))
            self.radioButton_next.setChecked(bool(warp.ref_frame == 'next'))

        else:
            self.set_default_values()
            self.checkBox_enabled.setChecked(False)
            self.set_enabled(False)
        self.block_signals(False)


    def get_action(self) -> WarpAction:
        values: WarpAction = WarpAction(
            frame=self.current_frame,
            warp=Warp(
                enabled=self.checkBox_enabled.isChecked(),
                matcher='knn' if self.radioButton_knn else 'bf',
                knn_ratio=float(self.spinBox_knn_ratio.value()) / 100.,
                max_distance_ratio=float(self.spinBox_max_distance_ratio.value()) / 100.,
                ref_frame='previous' if self.radioButton_prev else 'next'
            )
        )
        return values


    def event_settings_changed(self) -> None:
        self.block_signals(True)
        enabled: bool = self.checkBox_enabled.isChecked()
        self.set_enabled(enabled=enabled)

        self.block_signals(False)
        self.signal_warp_values_changed.emit(self.get_action())


    def event_default_values(self) -> None:
        self.block_signals(True)
        self.set_default_values()
        self.block_signals(False)
        self.event_settings_changed()

