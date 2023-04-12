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

GUIDELINES_X_MAX = 1600
GUIDELINES_Y_MAX = 1200
GUIDELINES_GRAB_OFFSET = 30

class Widget_stabilize(Widget_common, Ui_widget_stabilize):
    signal_settings_modified = Signal(dict)
    signal_segment_selected = Signal(dict)
    signal_frame_selected = Signal(int)


    def __init__(self, ui, controller:Controller_video_editor):
        super(Widget_stabilize, self).__init__(ui)
        self.controller = controller
        self.ui = ui
        self.setObjectName('stabilize')

        # Internal variables
        self.previous_position = None

        # Guidelines
        self.is_moving_guidelines = False
        self.moving_guidelines = None
        self.vertical_line_x = 800
        self.vertical_line_x_gap = 0
        self.is_moving_vertical_line = False
        self.horizontal_line_y = 600
        self.horizontal_line_y_gap = 0
        self.is_moving_horizontal_line = False


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
        table.itemDoubleClicked[QTableWidgetItem].connect(self.event_segment_double_clicked)
        table.installEventFilter(self)


        # Buttons, etc.
        self.groupBox_stabilize.clicked.connect(self.event_stabilize_modified)
        self.checkBox_mode = {
            'horizontal': self.checkBox_horizontal,
            'vertical': self.checkBox_vertical,
            'rotation': self.checkBox_rotation,
        }
        self.radioButton_ref = {
            'start': self.radioButton_start,
            'middle': self.radioButton_middle,
            'end': self.radioButton_end,
            'frame_no': self.radioButton_frame_no
        }

        self.pushButton_guidelines.toggled[bool].connect(self.event_preview_changed)

        # Signals
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

        self.clear_inputs()

        # Geometry
        self.move(s['geometry'][0], s['geometry'][1])
        self.adjustSize()



    def refresh_values(self, frame:dict):
        pass


    def get_preview_options(self):
        preview_options = {
            'is_enabled': self.pushButton_set_preview.isChecked(),
            'guidelines': self.pushButton_guidelines.isChecked(),
            'vertical_line_x': self.vertical_line_x,
            'horizontal_line_y': self.horizontal_line_y,
        }
        return preview_options



    def grab_guidelines(self, x, y):
        print(f"x={x}, Vline={self.vertical_line_x}")
        print(f"y={y}, Hline={self.horizontal_line_y}")

        if self.pushButton_guidelines.isChecked():
            if (self.vertical_line_x - GUIDELINES_GRAB_OFFSET) <= x <= (self.vertical_line_x + GUIDELINES_GRAB_OFFSET):
                self.vertical_line_x_gap = self.vertical_line_x - x
                self.is_moving_vertical_line = True
            else:
                self.is_moving_vertical_line = False

            if (self.horizontal_line_y - GUIDELINES_GRAB_OFFSET) <= y <= (self.horizontal_line_y + GUIDELINES_GRAB_OFFSET):
                self.horizontal_line_y_gap = self.horizontal_line_y - y
                self.is_moving_horizontal_line = True
            else:
                self.is_moving_horizontal_line = False

            if self.is_moving_horizontal_line and self.is_moving_vertical_line:
                self.moving_guidelines = "both"
            elif self.is_moving_horizontal_line:
                self.moving_guidelines = "horizontal"
            elif self.is_moving_vertical_line:
                self.moving_guidelines = "vertical"
            else:
                self.is_moving_guidelines = False
                return None

            self.is_moving_guidelines = True
            self.event_preview_changed(is_checked=True)

            print_cyan(f"grabbed {self.moving_guidelines}")
            return self.moving_guidelines

        self.is_moving_guidelines = False
        return None


    def move_guidelines(self, x, y):
        if not self.is_moving_guidelines:
            return None

        if ( (x + self.vertical_line_x_gap) < 5
            or (x + self.vertical_line_x_gap) > 5 + GUIDELINES_X_MAX):
            return None

        if ( (x + self.horizontal_line_y_gap) < 5
            or (x + self.horizontal_line_y_gap) > 5 + GUIDELINES_Y_MAX):
            return None

        if (self.pushButton_guidelines.isChecked()
            and self.is_moving_guidelines):
            if self.is_moving_horizontal_line:
                self.horizontal_line_y = y + self.horizontal_line_y_gap
            if self.is_moving_vertical_line:
                self.vertical_line_x = x + self.vertical_line_x_gap

            self.event_preview_changed(is_checked=True)
            return self.moving_guidelines
        return None


    def guidelines_moved(self, x, grab_x, y, grab_y):
        if not self.is_moving_guidelines:
            return None

        if (self.pushButton_guidelines.isChecked()
            and self.is_moving_guidelines):

            if self.is_moving_horizontal_line:
                self.horizontal_line_y = y + grab_y
            if self.is_moving_vertical_line:
                self.vertical_line_x = x + grab_x

            self.event_preview_changed(is_checked=True)
            return True
        return False



    def guidelines_released(self, x, y):
        self.is_moving_guidelines = False
        self.is_moving_vertical_line = False
        self.is_moving_horizontal_line = False



    def event_stabilize_requested(self):
        log.info("calculate")


    def clear_inputs(self):
        self.lineEdit_start.clear()
        self.lineEdit_end.clear()
        self.lineEdit_ref_frame_no.clear()
        self.radioButton_start.blockSignals(True)
        self.radioButton_start.setChecked(True)
        self.radioButton_start.blockSignals(False)
        for w in self.checkBox_mode.values():
            w.setChecked(False)


    def event_segment_selected(self):
        log.info("segment selected")
        table = self.tableWidget_stabilize
        row_no = table.currentRow()
        self.clear_inputs()
        try:
            start = int(table.item(row_no, 0).text())
        except:
            return

        self.lineEdit_start.setText(table.item(row_no, 0).text())
        self.lineEdit_end.setText(table.item(row_no, 1).text())
        ref = table.item(row_no, 2).text()
        try:
            self.radioButton_ref[ref].setChecked(True)
        except:
            self.radioButton_ref['frame_no'].setChecked(True)
            self.lineEdit_ref_frame_no.setText(ref)
        mode_list = table.item(row_no, 3).text().split('+')
        for m in mode_list:
            self.checkBox_mode[m].setChecked(True)


    def event_segment_double_clicked(self, item:QTableWidgetItem):
        row_no = item.row()
        log.info(f"selected frame at row={row_no}")
        try:
            frame_no = int(self.tableWidget_stabilize.item(row_no, 0).text())
        except:
            return
        self.signal_frame_selected.emit(frame_no)



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
                'alg': 'cv2_deshaker',
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

        table.selectRow(0)
        self.block_all_signals(False)



    def event_key_pressed(self, event):
        key = event.key()
        modifiers = event.modifiers()
        # print("%s.event_key_pressed: %d, modifiers=" % (__name__, key), modifiers)

        if modifiers & Qt.ControlModifier:
            if key == Qt.Key_S:
                self.event_save_modifications()
                return True

        elif key == Qt.Key_F3:
            self.pushButton_guidelines.toggle()
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

