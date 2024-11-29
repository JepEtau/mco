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
    QGraphicsEllipseItem,
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



@dataclass(slots=True)
class DsrShape:
    shape: MaskShape
    center: list[float | int, float | int]
    axes: list[float | int, float | int]
    angle: float
    item: QGraphicsEllipseItem | None = None



@dataclass(slots=True)
class _TableHeaders:
    title: str
    width: int
    alignement: Qt.AlignmentFlag


class DsrWidget(QWidget, Ui_DsrWidget):
    signal_save = Signal()
    signal_discard = Signal()
    signal_undo = Signal()
    signal_preview_toggled = Signal(bool)
    signal_edition_started = Signal()

    signal_dsr_selected = Signal(DsrAction)
    signal_dsr_modified = Signal(DsrAction)
    signal_dsr_removed = Signal(dict)

    signal_shape_changed = Signal(str)

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
            b.clicked.connect(partial(self.event_shape_type_changed, shape_name))


        # Table
        self.tableWidget_dsr.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.tableWidget_dsr.clearContents()
        self.tableWidget_dsr.setRowCount(0)

        self.headers: list[_TableHeaders] = [
            _TableHeaders("shape", 80, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter),
            _TableHeaders("center", 80, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter),
            _TableHeaders("geometry", 80, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter),
        ]
        self.tableWidget_dsr.setColumnCount(len(self.headers))
        for j, header in enumerate(self.headers):
            self.tableWidget_dsr.horizontalHeaderItem(j).setText(header.title)
            self.tableWidget_dsr.setColumnWidth(j, header.width)
        self.tableWidget_dsr.horizontalHeader().setStretchLastSection(True)

        # Connect signals and filter events
        # self.tableWidget_dsr.selectionModel().selectionChanged.connect(self.event_shape_selected)
        # self.tableWidget_dsr.installEventFilter(self)

        self._is_modified: bool = False

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


    def event_shape_type_changed(self, shape_name: MaskShape):
        print(f"current: shape: {shape_name}")
        self.signal_shape_changed.emit(shape_name)


    def get_current_shape(self) -> MaskShape:
        for name, button in self.shape_buttons.items():
            if button.isChecked():
                return name


    def force_current_shape(self, shape_name: MaskShape):
        self.block_signals(True)
        self.shape_buttons[shape_name].setChecked(True)
        self.block_signals(False)


    def event_key_released(self, event: QKeyEvent) -> bool:
        return False



    def event_key_pressed(self, event: QKeyEvent) -> bool:
        key, modifiers = event.key(), event.modifiers()
        # print(f"{time.time()} {__name__}.event_key_pressed: {key}, modifiers={modifiers}")

        if key == Qt.Key.Key_C:
            self.pushButton_circle.click()
            return True

        elif key == Qt.Key.Key_E:
            self.pushButton_ellipse.click()
            return True

        if key == Qt.Key.Key_O:
            self.pushButton_oblong.click()
            return True

        return False


    def refresh_dsr_list(self, patches: list[DsrShape], event: bool = False) -> None:
        self.tableWidget_dsr.clearContents()
        self.tableWidget_dsr.setRowCount(0)
        for i, patch in enumerate(patches):
            self.tableWidget_dsr.insertRow(i)

            self.tableWidget_dsr.setItem(
                i, 0, QTableWidgetItem(patch.shape)
            )
            center: str = f"({int(patch.center[0])}, {int(patch.center[1])})"
            self.tableWidget_dsr.setItem(
                i, 1,
                QTableWidgetItem(center)
            )

            geometry: str = ""
            if patch.shape == 'circle':
                geometry = f"{patch.axes[0]}"
            else:
                geometry = f"{patch.axes[0]}x{patch.axes[1]}, {patch.angle}°"
            self.tableWidget_dsr.setItem(
                i, 2,
                QTableWidgetItem(geometry)
            )

            for j, h in enumerate(self.headers):
                self.tableWidget_dsr.item(i, j).setTextAlignment(h.alignement)
                self.tableWidget_dsr.item(i, j).setFlags(
                    Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
                )

        if event:
            self._is_modified = True


    def is_modified(self) -> bool:
        return self._is_modified
