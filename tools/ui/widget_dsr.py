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
    QGraphicsEllipseItem,
)

from .ui.ui_widget_dsr import Ui_DsrWidget
from .stylesheet import set_stylesheet
if TYPE_CHECKING:
    from backend.replace_controller import ReplaceController
from backend.frame_cache import Frame
from backend._types import CurrentFrame, DsrAction
from parsers import (
    MaskShape,
    DsrPatch,
)



@dataclass(slots=True)
class DsrScenePatch:
    shape: MaskShape
    center: list[float | int, float | int]
    axes: list[float | int, float | int]
    angle: float
    item: QGraphicsEllipseItem | None = None
    start: int = -1
    end: int = -1

    def map_to_scene(self, size: list[float, float]) -> DsrScenePatch:
        w, h = size
        return DsrScenePatch(
            shape=self.shape,
            center=[int(self.center[0] * w), int(self.center[1] * h)],
            axes=[int(self.axes[0] * w), int(self.axes[1] * h)],
            angle=self.angle,
            item=self.item,
            start=self.start,
            end=self.end,
        )

    def copy(self) -> DsrScenePatch:
        return DsrScenePatch(
            shape=self.shape,
            center=self.center,
            axes=self.axes,
            angle=self.angle,
            item=self.item,
            start=self.start,
            end=self.end,
        )


def dsr_mask_to_scene(p: DsrPatch) -> DsrScenePatch:
    return DsrScenePatch(
        shape=p.shape,
        center=p.center,
        axes=p.axes,
        angle=p.angle,
        start=p.start,
        end=p.end,
    )


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

    signal_dsr_modified = Signal(DsrAction)

    signal_shape_changed = Signal(str)


    def __init__(self, ui, controller: ReplaceController):
        super().__init__(ui)
        self.setupUi(self)

        self.controller: ReplaceController = controller
        self.ui = ui
        self.setObjectName('dsr')

        self.shape_buttons: dict[MaskShape, QPushButton] = {
            'circle': self.pushButton_circle,
            'ellipse': self.pushButton_ellipse,
            'line': self.pushButton_line,
        }
        self.shape_buttons['circle'].setChecked(True)
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
        self.controller.signal_replacements_refreshed.connect(self.event_dsr_list_refreshed)

        self._is_modified: bool = False
        self.current_frame: CurrentFrame | None = None

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


    def set_current_frame(self, frame: Frame, original_frame: Frame) -> None:
        if original_frame is not None:
            self.current_frame = CurrentFrame(no=frame.by, frame=original_frame)
        else:
            self.current_frame = CurrentFrame(no=frame.no, frame=frame)
        # print(red(f"set_current_frame: {self.current_frame.no}"))
        self.event_dsr_list_refreshed()


    def event_set_preview_toggled(self, is_checked: bool=False):
        log.info(f"widget preview changed to {is_checked}")
        self.signal_preview_toggled.emit(is_checked)


    def set_edition(self, enabled: bool):
        # self.pushButton_set_edition.setEnabled(not enabled)
        pass


    def event_shape_type_changed(self, shape_name: MaskShape):
        # print(f"current: shape: {shape_name}")
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

        if key in (Qt.Key.Key_C, Qt.Key.Key_9):
            self.pushButton_circle.click()
            return True

        elif key in (Qt.Key.Key_3, ):
            self.pushButton_ellipse.click()
            return True

        if key == Qt.Key.Key_1:
            self.pushButton_line.click()
            return True

        return False


    @Slot()
    def event_dsr_list_refreshed(self):
        # print(lightcyan("event_dsr_list_refreshed"))
        dsr_shapes: list[DsrScenePatch] = []
        if self.current_frame is not None:
            dsr_shapes = self.controller.playlist_dsr(
                frame_no=self.current_frame.no
            )
        # pprint(dsr_shapes)
        self.refresh_dsr_list(
            dsr_shapes=dsr_shapes,
            event=False
        )


    def refresh_dsr_list(self, dsr_shapes: list[DsrScenePatch], event: bool = False) -> None:
        self.tableWidget_dsr.clearContents()
        self.tableWidget_dsr.setRowCount(0)
        for i, region in enumerate(dsr_shapes):
            self.tableWidget_dsr.insertRow(i)

            region.shape

            self.tableWidget_dsr.setItem(
                i, 0, QTableWidgetItem(region.shape)
            )
            center: str = f"({region.center[0]:.03}, {region.center[1]:.03})"
            self.tableWidget_dsr.setItem(
                i, 1,
                QTableWidgetItem(center)
            )

            geometry: str = ""
            if region.shape == 'circle':
                geometry = f"{region.axes[0]:.03}"
            else:
                geometry = f"{region.axes[0]:.03}x{region.axes[1]:.03}, {region.angle}°"
            self.tableWidget_dsr.setItem(
                i, 2,
                QTableWidgetItem(geometry)
            )

            for j, h in enumerate(self.headers):
                self.tableWidget_dsr.item(i, j).setTextAlignment(h.alignement)
                self.tableWidget_dsr.item(i, j).setFlags(
                    Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
                )

        # print(lightblue(f"refresh_dsr_list:"),  f"event: {event}")
        if event:
            self._is_modified = True

            regions: list[DsrPatch] = []
            for p in dsr_shapes:
                regions.append(
                        DsrPatch(
                        shape=p.shape,
                        center=p.center,
                        axes=p.axes,
                        angle=p.angle,
                        start=p.start,
                        end=p.end,
                    )
                )

            print(lightcyan("refresh_dsr_list:"), f"send signal_dsr_modified")
            pprint(regions)
            self.signal_dsr_modified.emit(
                DsrAction(
                    type='update',
                    frame=self.current_frame.frame,
                    regions=regions
                )
            )


    def is_modified(self) -> bool:
        return self._is_modified
