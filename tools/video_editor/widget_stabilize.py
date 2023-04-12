# -*- coding: utf-8 -*-
import sys
sys.path.append('../scripts')

from logger import log
from pprint import pprint

from PySide6.QtCore import (
    QObject,
    Qt,
    Signal,
    QEvent,
)
from PySide6.QtWidgets import (
    QApplication,
    QTableWidgetItem,
)

from common.sylesheet import set_stylesheet, update_selected_widget_stylesheet

from tools.video_editor.controller import Controller_video_editor
from video_editor.ui.widget_stabilize_ui import Ui_widget_stabilize
from common.widget_common import Widget_common

class Widget_stabilize(Widget_common, Ui_widget_stabilize):
    signal_stabilize_modified = Signal(dict)
    signal_segment_selected = Signal(dict)

    def __init__(self, ui, controller:Controller_video_editor):
        super(Widget_stabilize, self).__init__(ui)
        self.controller = controller
        self.ui = ui
        self.setObjectName('stabilize')

        # Internal variables
        self.previous_position = None

        # Disable focus
        self.tableWidget_stabilize.setFocusPolicy(Qt.NoFocus)

        self.pushButton_calculate.clicked.connect(self.event_stabilize_requested)

        # Table
        self.tableWidget_stabilize.clearContents()
        self.tableWidget_stabilize.setRowCount(0)


        self.alignment = [Qt.AlignRight | Qt.AlignVCenter,
                            Qt.AlignRight | Qt.AlignVCenter,
                            Qt.AlignRight | Qt.AlignVCenter]
        headers = ["start", "end", "used"]
        default_col_width = [70, 80, 80, 100]
        for col_no, header_str, col_width in zip(range(len(headers)),
                                                    headers,
                                                    default_col_width):
            self.tableWidget_stabilize.horizontalHeaderItem(col_no).setText(header_str)
            self.tableWidget_stabilize.setColumnWidth(col_no, col_width)
        self.tableWidget_stabilize.horizontalHeader().setStretchLastSection(True)

        # Connect signals and filter events
        self.tableWidget_stabilize.selectionModel().selectionChanged.connect(self.event_segment_selected)
        # self.tableWidget_stabilize.itemDoubleClicked[QTableWidgetItem].connect(self.event_)
        self.tableWidget_stabilize.installEventFilter(self)

        self.model.signal_stabilize_parameters_loaded[dict].connect(self.event_stabilize_parameters_loaded)
        self.model.signal_is_saved[str].connect(self.event_is_saved)

        self.installEventFilter(self)

        set_stylesheet(self)
        self.adjustSize()



    def set_initial_options(self, preferences:dict):
        log.info("set_initial_options")
        s = preferences['stabilize']

        self.tableWidget_stabilize.blockSignals(True)
        self.tableWidget_stabilize.clearContents()
        self.tableWidget_stabilize.setRowCount(0)

        # self.pushButton_remove.setEnabled(False)
        # self.pushButton_paste.setEnabled(False)
        # self.pushButton_copy.setEnabled(True)

        # Geometry
        self.move(s['geometry'][0], s['geometry'][1])
        self.adjustSize()



    def refresh_values(self, frame:dict):
        pass


    def get_preview_options(self):
        preview_options = {
            'is_enabled': self.pushButton_set_preview.isChecked(),
        }
        return preview_options


    def block_signals(self, enabled):
        pass

    def event_stabilize_requested(self):
        log.info("calculate")

    def event_stabilize_parameters_loaded(self, parameters):
        log.info("parameters changed")



    def event_segment_selected(self):
        log.info("segment selected")


    def event_key_pressed(self, event):
        key = event.key()
        modifiers = event.modifiers()
        # print("%s.event_key_pressed: %d, modifiers=" % (__name__, key), modifiers)

        if modifiers & Qt.ControlModifier:
            if key == Qt.Key_S:
                self.event_save_modifications()
                return True

        elif key == Qt.Key_S:
            log.info("start")
            return True
        elif key == Qt.Key_E:
            log.info("end")
            return True
        elif key == Qt.Key_R:
            log.info("reference")
            return True

        if key == Qt.Key_F2:
            if self.pushButton_set_preview.isEnabled():
                self.pushButton_set_preview.toggle()
                return True

        if QApplication.focusObject() is self.tableWidget_stabilize:
            if key == Qt.Key_Delete:
                log.info("delete segment")
                return True

        return False


    def event_key_released(self, event):
        return False


    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        # print("* eventFilter: widget_%s: " % (self.objectName()), event.type())

        # Filter press/release events
        if event.type() == QEvent.KeyPress:
            key = event.key()
            modifier = event.modifiers()
            if modifier & Qt.ControlModifier and key == Qt.Key_A:
                self.tableWidget_stabilize.selectAll()
                event.accept()
                return True
            elif key == Qt.Key_Delete:
                self.event_selection_removed()
                return True

            return self.ui.keyPressEvent(event)

        # print(event.type())
        if event.type() == QEvent.FocusOut:
            self.tableWidget_stabilize.clearSelection()

        elif event.type() == QEvent.Enter:
            self.is_entered = True
        elif event.type() == QEvent.Leave:
            self.is_entered = False

        return super().eventFilter(watched, event)

