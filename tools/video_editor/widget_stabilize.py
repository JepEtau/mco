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

from video_editor.controller import Controller_video_editor
from video_editor.ui.widget_stabilize_ui import Ui_widget_stabilize
from common.widget_common import Widget_common
from utils.pretty_print import *
from parsers.parser_stabilize import SEGMENTS_MAX_COUNT


class Widget_stabilize(Widget_common, Ui_widget_stabilize):
    signal_settings_modified = Signal(dict)
    signal_segment_selected = Signal(dict)


    def __init__(self, ui, controller:Controller_video_editor):
        super(Widget_stabilize, self).__init__(ui)
        self.controller = controller
        self.ui = ui
        self.setObjectName('stabilize')

        # Internal variables
        self.previous_position = None

        # Table
        table = self.tableWidget_stabilize
        table.setFocusPolicy(Qt.NoFocus)
        table.clearContents()
        table.setRowCount(0)
        self.alignment = [Qt.AlignRight | Qt.AlignVCenter,
                            Qt.AlignRight | Qt.AlignVCenter,
                            Qt.AlignCenter | Qt.AlignVCenter,
                            Qt.AlignLeft | Qt.AlignVCenter]
        headers = ["start", "end", "initial ref.", "mode"]
        default_col_width = [50, 50, 80, 200]
        for col_no, header_str, col_width in zip(range(len(headers)),
                                                    headers,
                                                    default_col_width):
            table.horizontalHeaderItem(col_no).setText(header_str)
            table.setColumnWidth(col_no, col_width)
        table.selectionModel().selectionChanged.connect(self.event_segment_selected)
        table.installEventFilter(self)


        # Buttons, etc.
        self.groupBox_stabilize.clicked.connect(self.event_stabilize_modified)


        self.controller.signal_stabilize_settings_refreshed[dict].connect(self.event_stabilize_settings_refreshed)
        self.controller.signal_is_saved[str].connect(self.event_is_saved)

        self.installEventFilter(self)

        set_stylesheet(self)
        self.adjustSize()



    def set_initial_options(self, preferences:dict):
        log.info("set_initial_options")
        s = preferences['stabilize']

        self.groupBox_stabilize.blockSignals(True)
        self.groupBox_stabilize.setChecked(False)
        self.groupBox_stabilize.blockSignals(False)

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


    def event_stabilize_requested(self):
        log.info("calculate")



    def event_segment_selected(self):
        log.info("segment selected")


    def event_stabilize_modified(self):
        # Get new settings
        settings = {
            'enable': self.groupBox_stabilize.isChecked(),
            'segments' : list()
        }

        table = self.tableWidget_stabilize
        for row_no in range(SEGMENTS_MAX_COUNT):
            try:
                start = int(table.item(row_no, 0).text())
            except:
                continue

            segment = {
                'start': start,
                'end': int(table.item(row_no, 1).text()),
                'ref': table.item(row_no, 2).text(),
                'alg': 'cv2_deshake',
                'mode': {
                    'vertical': True,
                    'horizontal': False,
                    'rotation': False
                },
            }
            mode_list = table.item(row_no, 3).text().split('+')
            for k in mode_list:
                segment['mode'][k] = True
            settings['segments'].append(segment)
        self.signal_settings_modified.emit(settings)

        self.pushButton_save.setEnabled(True)


    def block_all_signals(self, enabled:bool):
        self.groupBox_stabilize.blockSignals(enabled)
        self.tableWidget_stabilize.blockSignals(enabled)
        self.pushButton_calculate.blockSignals(enabled)



    def event_stabilize_settings_refreshed(self, stabilize_settings):
        # print_lightcyan("event_stabilize_settings_refreshed")
        # pprint(stabilize_settings)

        self.block_all_signals(True)
        if stabilize_settings is None:
            self.groupBox_stabilize.setChecked(False)
            self.tableWidget_stabilize.clearContents()
            self.tableWidget_stabilize.setRowCount(0)
            self.block_all_signals(False)
            return

        self.groupBox_stabilize.setChecked(stabilize_settings['enable'])

        table = self.tableWidget_stabilize
        segments = stabilize_settings['segments']

        table.clearContents()
        table.setRowCount(0)
        if len(segments) > 0:
            for row_no, segment in zip(range(len(segments)), segments):
                mode_str = ""
                # Ordered
                for k in ['vertical', 'horizontal', 'rotation']:
                    mode_str += f"+{k}" if segment['mode'][k] else ''

                table.insertRow(row_no)
                table.setItem(row_no, 0, QTableWidgetItem(f"{segment['start']}"))
                table.setItem(row_no, 1, QTableWidgetItem(f"{segment['end']}"))
                table.setItem(row_no, 2, QTableWidgetItem(f"{segment['ref']}"))
                table.setItem(row_no, 3, QTableWidgetItem(mode_str[1:]))


                for i in range(len(self.alignment)):
                    table.item(row_no, i).setTextAlignment(self.alignment[i])
                    table.item(row_no, i).setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)



            table.selectionModel().clearSelection()
        else:
            row_no = 0
            self.pushButton_calculate.setEnabled(False)

        for row_no in range(len(segments), SEGMENTS_MAX_COUNT):
            table.insertRow(row_no)

        self.block_all_signals(False)



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

