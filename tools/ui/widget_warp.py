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
    from .window_replace import ReplaceWindow

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
    signal_warp_update = Signal(CurrentFrame)
    signal_frame_selected = Signal(int)


    def __init__(self, ui: ReplaceWindow, controller: ReplaceController):
        super().__init__(ui)
        self.setupUi(self)

        self.controller: ReplaceController = controller
        self.ui: ReplaceWindow = ui
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

        self.tableWidget_warp.clearContents()
        self.tableWidget_warp.setRowCount(0)

        self.alignment = [
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
        ]
        headers = ["frame", "values"]
        default_col_width = [60, 80]
        for col_no, header_str, col_width in zip(
            range(len(headers)),
            headers,
            default_col_width
        ):
            self.tableWidget_warp.horizontalHeaderItem(col_no).setText(header_str)
            self.tableWidget_warp.setColumnWidth(col_no, col_width)
        self.tableWidget_warp.horizontalHeader().setStretchLastSection(True)

        # Connect signals and filter events
        self.tableWidget_warp.selectionModel().selectionChanged.connect(self.event_warp_selected)
        self.tableWidget_warp.itemDoubleClicked[QTableWidgetItem].connect(
            self.event_move_to_frame_no
        )
        self.tableWidget_warp.installEventFilter(self)


        self.controller.signal_scene_warps_refreshed.connect(self.event_warp_list_refreshed)


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
            if self.current_frame.frame.no == self.current_frame.frame.by:
                self.block_signals(True)
                if self.checkBox_enabled.isChecked():
                    self.checkBox_enabled.setChecked(False)
                    self.set_enabled(False)
                    self.signal_warp_values_changed.emit(self.get_action())
                else:
                    self.checkBox_enabled.setChecked(True)
                    self.set_enabled(True)
                    self.signal_warp_values_changed.emit(self.get_action())
                self.block_signals(False)
            return True


        elif key == Qt.Key.Key_F4:
            self.process_warp()
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
        print(red(
            f"WARP: set_current_frame: {self.current_frame.frame.no}, by {self.current_frame.frame.by}"
        ))

        if self.current_frame.frame.no == self.current_frame.frame.by:
            # Frame is the original one
            self.block_signals(True)
            warp: Warp | None = self.controller.frame_warp(frame_no=self.current_frame.no)
            if warp is not None:
                print(warp)
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

        self.tableWidget_warp.clearSelection()


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


    @Slot()
    def event_warp_selected(self):
        self.tableWidget_warp.setFocus()


    @Slot()
    def event_warp_list_refreshed(self):
        print(lightgreen("refresh list of frames to warp"))
        warps = self.controller.playlist_warp()
        self.tableWidget_warp.blockSignals(True)

        self.tableWidget_warp.clearContents()
        self.tableWidget_warp.setRowCount(0)

        row_no: int = 0
        for f_no, frame_warp in warps.items():
            if frame_warp.enabled:
                self.tableWidget_warp.insertRow(row_no)
                self.tableWidget_warp.setItem(row_no, 0, QTableWidgetItem(str(f_no)))
                self.tableWidget_warp.setItem(row_no, 1, QTableWidgetItem(str(frame_warp)))
                for i in range(len(self.alignment)):
                    self.tableWidget_warp.item(row_no, i).setTextAlignment(self.alignment[i])
                    self.tableWidget_warp.item(row_no, i).setFlags(
                        Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
                    )
                row_no += 1
        
        self.tableWidget_warp.selectionModel().clearSelection()
        self.tableWidget_warp.blockSignals(False)
        self.ui.set_focus()
        self.tableWidget_warp.setEnabled(True)


    def event_default_values(self) -> None:
        self.block_signals(True)
        self.set_default_values()
        self.block_signals(False)
        self.event_settings_changed()


    def process_warp(self) -> None:
        if self.checkBox_enabled.isChecked():
            self.signal_warp_update.emit(self.current_frame)



    @Slot(QTableWidgetItem)
    def event_move_to_frame_no(self, item: QTableWidgetItem):
        # double-click to jump to the frame no.
        row_no = item.row()
        # column_no = item.column()
        # if column_no == 0:
        #     return
        # log.info(f"selected frame at row={row_no}, column {row_no}")
        frame_no = int(self.tableWidget_warp.item(row_no, 0).text())
        self.ui.set_focus()
        self.signal_frame_selected.emit(frame_no)
