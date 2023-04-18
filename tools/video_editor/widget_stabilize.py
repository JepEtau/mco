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

from common.stylesheet import (
    set_stylesheet,
    set_widget_stylesheet,
)
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
    signal_preview_requested = Signal()
    signal_show_guidelines_changed = Signal(bool)


    def __init__(self, ui, controller:Controller_video_editor):
        super(Widget_stabilize, self).__init__(ui)
        self.controller = controller
        self.ui = ui
        self.setObjectName('stabilize')

        # Internal variables
        self.previous_position = None
        self.removed_segment = None
        self.segment_count = 0
        self.is_edition_allowed = False
        self.previous_preview_state = False

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
        self.groupBox_stabilize.clicked.connect(self.event_settings_enable_toggled)
        self.checkBox_mode = {
            'horizontal': self.checkBox_horizontal,
            'vertical': self.checkBox_vertical,
            'rotation': self.checkBox_rotation,
        }
        self.ref_list = ['start', 'middle', 'end']
        self.radioButton_ref = {
            'start': self.radioButton_start,
            'middle': self.radioButton_middle,
            'end': self.radioButton_end,
            'frame_no': self.radioButton_frame_no
        }

        self.label_message.clear()

        # Signals
        self.pushButton_guidelines.toggled[bool].connect(self.event_guidelines_changed)
        self.pushButton_set_start.clicked.connect(self.event_start_modified)
        self.pushButton_set_end.clicked.connect(self.event_end_modified)
        self.pushButton_switch_ref.clicked.connect(self.event_ref_modified)
        self.pushButton_set_segment.clicked.connect(self.event_set_segment_requested)
        self.groupBox_stabilize.installEventFilter(self)
        self.installEventFilter(self)


        self.controller.signal_stabilize_settings_refreshed[dict].connect(self.event_stabilize_settings_refreshed)
        self.controller.signal_is_saved[str].connect(self.event_is_saved)

        set_stylesheet(self)
        set_widget_stylesheet(self.pushButton_set_start)
        set_widget_stylesheet(self.pushButton_set_end)
        set_widget_stylesheet(self.pushButton_switch_ref)
        set_widget_stylesheet(self.label_message, 'message')
        self.adjustSize()



    def set_initial_options(self, preferences:dict):
        log.info("set_initial_options")
        s = preferences['stabilize']
        self.block_signals(True)

        self.groupBox_stabilize.setChecked(False)
        self.tableWidget_stabilize.clearContents()
        self.tableWidget_stabilize.setRowCount(0)
        self.clear_inputs()

        # Push button is used to calculate then display
        self.pushButton_set_preview.setEnabled(False)
        self.pushButton_set_preview.setChecked(False)
        self.previous_preview_state = False

        self.block_signals(False)

        # Geometry
        self.move(s['geometry'][0], s['geometry'][1])
        self.adjustSize()



    def refresh_preview_options(self, new_preview_settings):
        self.is_edition_allowed = new_preview_settings['stabilize']['allowed']
        enabled = new_preview_settings['stabilize']['enabled']

        self.pushButton_set_preview.blockSignals(True)
        self.pushButton_set_preview.setEnabled(self.is_edition_allowed)
        self.pushButton_set_preview.setChecked(enabled)
        self.previous_preview_state = enabled
        self.pushButton_set_preview.blockSignals(False)
        log.info(f"enable: {enabled}, allowed: {self.is_edition_allowed}")


    def get_preview_options(self):
        preview_options = {
            'allowed': self.is_edition_allowed,
            'enabled': self.pushButton_set_preview.isChecked(),
        }
        return preview_options



    def refresh_values(self, frame:dict):
        # Refresh some specific values refreshed and stored in the frame struct
        pass


    def grab_guidelines(self, x, y):
        # print(f"x={x}, Vline={self.vertical_line_x}")
        # print(f"y={y}, Hline={self.horizontal_line_y}")
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
            self.signal_show_guidelines_changed.emit(True)

            # print_cyan(f"grabbed {self.moving_guidelines}")
            return self.moving_guidelines

        self.is_moving_guidelines = False
        self.signal_show_guidelines_changed.emit(False)
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

            self.signal_show_guidelines_changed.emit(True)
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

            self.signal_show_guidelines_changed.emit(True)
            return self.moving_guidelines
        return None


    def guidelines_released(self, x, y):
        self.is_moving_guidelines = False
        self.is_moving_vertical_line = False
        self.is_moving_horizontal_line = False
        self.signal_show_guidelines_changed.emit(True)


    def guidelines_coordinates(self):
        return (self.vertical_line_x, self.horizontal_line_y)


    def event_guidelines_changed(self, is_checked:bool=False):
        self.signal_show_guidelines_changed.emit(is_checked)



    def block_signals(self, enabled:bool):
        self.pushButton_set_preview.blockSignals(enabled)
        self.groupBox_stabilize.blockSignals(enabled)
        self.tableWidget_stabilize.blockSignals(enabled)
        self.pushButton_set_end.blockSignals(enabled)
        self.pushButton_set_start.blockSignals(enabled)
        self.pushButton_set_ref.blockSignals(enabled)
        self.pushButton_set_segment.blockSignals(enabled)
        for w in self.checkBox_mode.values():
            w.blockSignals(enabled)
        for w in self.radioButton_ref.values():
            w.blockSignals(enabled)


    def clear_inputs(self):
        self.lineEdit_start.setText("0")
        self.lineEdit_end.setText("0")
        self.lineEdit_ref_frame_no.clear()
        self.radioButton_start.blockSignals(True)
        self.radioButton_start.setChecked(True)
        self.radioButton_start.blockSignals(False)
        for w in self.checkBox_mode.values():
            w.setChecked(False)


    def set_controls_enabled(self, enabled:bool=False):
        self.tableWidget_stabilize.setEnabled(enabled)
        self.pushButton_set_end.setEnabled(enabled)
        self.pushButton_set_start.setEnabled(enabled)
        self.pushButton_set_ref.setEnabled(enabled)
        self.pushButton_set_segment.setEnabled(enabled)
        for w in self.checkBox_mode.values():
            w.setEnabled(enabled)
        for w in self.radioButton_ref.values():
            w.setEnabled(enabled)


    def get_current_settings(self) -> dict:
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
        return settings


    def event_settings_enable_toggled(self, is_checked:bool=False):
        self.set_controls_enabled(is_checked)
        settings = self.get_current_settings()
        # print_lightcyan("event_settings_enable_toggled")
        # pprint(settings)
        self.edition_started()
        self.signal_settings_modified.emit(settings)
        self.pushButton_save.setEnabled(True)


    def event_stabilize_settings_refreshed(self, stabilize_settings):
        log.info("event_stabilize_settings_refreshed")
        # pprint(stabilize_settings)

        self.removed_segment = None

        self.block_signals(True)
        if stabilize_settings is None or len(stabilize_settings) == 0:
            self.groupBox_stabilize.setChecked(False)
            self.tableWidget_stabilize.clearContents()
            self.tableWidget_stabilize.setRowCount(0)
            self.set_controls_enabled(False)

            # Disable calculations/preview
            self.pushButton_set_preview.setEnabled(False)
            self.pushButton_set_preview.setChecked(False)
            self.previous_preview_state = False

            self.block_signals(False)
            self.label_message.setText("")
            return

        is_enabled = stabilize_settings['enable']
        self.groupBox_stabilize.setChecked(is_enabled)

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
            self.pushButton_set_preview.setEnabled(False)

        self.segment_count = len(segments)
        for row_no in range(len(segments), SEGMENTS_MAX_COUNT):
            table.insertRow(row_no)

        self.clear_inputs()
        self.set_controls_enabled(is_enabled)

        if is_enabled:
            table.selectRow(0)

        if 'error' in stabilize_settings.keys() and stabilize_settings['error']:
            self.label_message.setText("ERROR!")
            # Disable calculations/preview
            self.pushButton_set_preview.setEnabled(False)
            self.pushButton_set_preview.setChecked(False)
            self.previous_preview_state = False
            log.info('disable preview')
        else:
            self.label_message.clear()
            # Enable preview
            self.pushButton_set_preview.setEnabled(True)
            log.info('enable preview')

        self.block_signals(False)


    def event_segment_selected(self):
        log.info("segment selected")
        table = self.tableWidget_stabilize
        row_no = table.currentRow()
        try:
            start = int(table.item(row_no, 0).text())
        except:
            return

        self.clear_inputs()
        self.lineEdit_start.setText(table.item(row_no, 0).text())
        self.lineEdit_end.setText(table.item(row_no, 1).text())
        ref = table.item(row_no, 2).text()
        try:
            self.radioButton_ref[ref].setChecked(True)
        except:
            self.radioButton_ref['frame_no'].setChecked(True)
            self.lineEdit_ref_frame_no.setText(ref)
        mode_list = table.item(row_no, 3).text().split('+')
        try:
            for m in mode_list:
                self.checkBox_mode[m].setChecked(True)
        except:
            print_yellow(f"mode_list={','.join(mode_list)}")
            self.checkBox_mode['vertical'].setChecked(True)
            pass

        self.tableWidget_stabilize.setEnabled(True)
        self.pushButton_set_end.setEnabled(True)
        self.pushButton_set_start.setEnabled(True)
        self.pushButton_set_ref.setEnabled(True)
        self.pushButton_set_segment.setEnabled(True)


    def event_segment_double_clicked(self, item:QTableWidgetItem):
        row_no = item.row()
        col_no = item.column()
        log.info(f"selected frame at row={row_no}, col={col_no}")
        if col_no == 1:
            # Select end of the selected segment
            try: frame_no = int(self.tableWidget_stabilize.item(row_no, col_no).text())
            except: return
        else:
            # Select start of the selected segment
            try: frame_no = int(self.tableWidget_stabilize.item(row_no, 0).text())
            except: return
        self.signal_frame_selected.emit(frame_no)


    def event_start_modified(self):
        frame_no = self.controller.get_current_frame_no()
        end_no = int(self.lineEdit_end.text())
        if frame_no > end_no and end_no != 0:
            self.lineEdit_start.setText(f"{end_no}")
            self.lineEdit_end.setText(f"{frame_no}")
        else:
            self.lineEdit_start.setText(f"{frame_no}")
        if frame_no != end_no:
            self.pushButton_set_segment.setEnabled(True)
        else:
            self.pushButton_set_segment.setEnabled(False)
        self.edition_started()


    def event_end_modified(self):
        frame_no = self.controller.get_current_frame_no()
        start_no = int(self.lineEdit_start.text())
        if frame_no < start_no:
            self.lineEdit_start.setText(f"{frame_no}")
            self.lineEdit_end.setText(f"{start_no}")
        else:
            self.lineEdit_end.setText(f"{frame_no}")
        if frame_no != start_no:
            self.pushButton_set_segment.setEnabled(True)
        else:
            self.pushButton_set_segment.setEnabled(False)
        self.edition_started()


    def event_ref_modified(self):
        for i, k in zip(range(len(self.ref_list)), self.ref_list):
            print(f"{i}: ", end='')
            if self.radioButton_ref[k].isChecked():
                next_i = i + 1 if i < len(self.ref_list)-1 else 0
                w = self.radioButton_ref[self.ref_list[next_i]]
                w.blockSignals(True)
                w.setChecked(True)
                w.blockSignals(False)
                break
        self.edition_started()


    def event_set_segment_requested(self):
        print_lightcyan("Set Segment")
        table = self.tableWidget_stabilize

        # First selected row no
        selected_indexes = table.selectedIndexes()
        try: row_no = list(set([i.row() for i in selected_indexes]))[0]
        except: row_no = -1

        if self.segment_count == SEGMENTS_MAX_COUNT and row_no == -1:
            # Cannot append segment
            print_yellow("Error: cannot append new segment. Reason: max count and none selected")
            return

        # Get the new segment settings
        start = self.lineEdit_start.text()
        end = self.lineEdit_end.text()
        if start == end:
            log.info("cannot append, start=end")
            return
        for k, w in self.radioButton_ref.items():
            if w.isChecked():
                ref = k
                break
        mode_str = ""
        for k, w in self.checkBox_mode.items():
            if w.isChecked():
                mode_str += f"+{k}"

        # Modify the table
        table.setItem(row_no, 0, QTableWidgetItem(start))
        table.setItem(row_no, 1, QTableWidgetItem(end))
        table.setItem(row_no, 2, QTableWidgetItem(ref))
        table.setItem(row_no, 3, QTableWidgetItem(mode_str[1:]))

        for col_no in range(len(self.alignment)):
            table.item(row_no, col_no).setTextAlignment(self.alignment[col_no])
            table.item(row_no, col_no).setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)

        # Get current segments
        settings = self.get_current_settings()

        # print_lightgreen("event_set_segment_requested")
        # pprint(settings)
        self.pushButton_save.setEnabled(True)
        self.pushButton_set_preview.setEnabled(False)
        self.pushButton_set_preview.setChecked(False)
        self.previous_preview_state = False
        self.signal_settings_modified.emit(settings)


    def event_remove_segment_requested(self):
        table = self.tableWidget_stabilize
        row_no = table.currentRow()
        self.clear_inputs()
        try:
            start = int(table.item(row_no, 0).text())
        except:
            print(table.item(row_no, 0).text())
            return
        # Save for history
        k = f"{row_no}"
        self.removed_segment = {k: list()}
        for col_no in range(len(self.alignment)):
            self.removed_segment[k].append(table.item(row_no, col_no).text())
            table.setItem(row_no, col_no, QTableWidgetItem(""))
        self.edition_started()


    def restore_segment(self):
        if self.removed_segment is None:
            return
        table = self.tableWidget_stabilize
        row_no_str = list(self.removed_segment.keys())[0]
        row_no = int(row_no_str)
        values_str = self.removed_segment[row_no_str]
        for col_no, value_str in zip(range(len(values_str)), values_str):
            table.setItem(row_no, col_no, QTableWidgetItem(value_str))
            for i in range(len(self.alignment)):
                table.item(row_no, i).setTextAlignment(self.alignment[i])
                table.item(row_no, i).setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)
        self.removed_segment = None
        self.edition_started()


    def edition_started(self):
        # Start edition, disable preview
        self.pushButton_set_preview.blockSignals(True)
        self.pushButton_set_preview.setEnabled(False)
        self.pushButton_set_preview.setChecked(False)
        self.previous_preview_state = False
        self.pushButton_set_preview.blockSignals(False)



    def event_set_preview_toggled(self, is_checked:bool=False):
        log.info(f"preview button changed to {is_checked}")
        if is_checked:
            print_purple("event_set_preview_toggled: request to calculate")
            self.signal_preview_requested.emit()
        elif self.previous_preview_state != is_checked:
            self.signal_preview_options_changed.emit()
        self.previous_preview_state = is_checked


    def event_key_pressed(self, event):
        key = event.key()
        modifiers = event.modifiers()
        # print("%s.event_key_pressed: %d, modifiers=" % (__name__, key), modifiers)

        if modifiers & Qt.ControlModifier:
            if key == Qt.Key_S:
                self.event_save_modifications()
                return True
            elif key == Qt.Key_Z:
                self.restore_segment()
                return True

        elif key == Qt.Key_F3:
            self.pushButton_guidelines.toggle()
            return True
        elif key == Qt.Key_S:
            self.event_start_modified()
            return True
        elif key == Qt.Key_E:
            self.event_end_modified()
            return True
        elif key == Qt.Key_I:
            self.event_ref_modified()
            return True
        elif key == Qt.Key_V:
            self.checkBox_vertical.toggle()
            return True
        elif key == Qt.Key_H:
            self.checkBox_horizontal.toggle()
            return True
        elif key == Qt.Key_R:
            self.checkBox_rotation.toggle()
            return True
        elif key == Qt.Key_Enter or key == Qt.Key_Return:
            self.event_set_segment_requested()
            return True


        if key == Qt.Key_F2:
            if self.pushButton_set_preview.isEnabled():
                self.pushButton_set_preview.toggle()
                return True
        if key == Qt.Key_F7:
            self.event_stabilize_requested()
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
                self.event_remove_segment_requested()
                return True
            return self.ui.keyPressEvent(event)

        # print(event.type())
        # if event.type() == QEvent.FocusOut:
        #     self.tableWidget_stabilize.clearSelection()

        elif event.type() == QEvent.Enter:
            self.is_entered = True
        elif event.type() == QEvent.Leave:
            self.is_entered = False

        return super().eventFilter(watched, event)

