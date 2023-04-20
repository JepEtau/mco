# -*- coding: utf-8 -*-
import sys
sys.path.append('../scripts')

from utils.pretty_print import *

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

from common.stylesheet import set_stylesheet, update_selected_widget_stylesheet

from video_editor.controller import Controller_video_editor
from video_editor.ui.widget_replace_ui import Ui_widget_replace
from common.widget_common import Widget_common

class Widget_replace(Widget_common, Ui_widget_replace):
    signal_replace_modified = Signal(dict)
    signal_frame_selected = Signal(int)

    def __init__(self, ui, controller:Controller_video_editor):
        super(Widget_replace, self).__init__(ui)
        self.controller = controller
        self.ui = ui
        self.setObjectName('replace')

        # Internal variables
        self.copied_frame_no = -1
        self.previous_position = None
        self.is_edition_allowed = False

        # Disable focus
        self.lineEdit_frame_no.setFocusPolicy(Qt.NoFocus)
        self.lineEdit_replaced_by.setFocusPolicy(Qt.NoFocus)
        self.pushButton_copy.setFocusPolicy(Qt.NoFocus)
        self.pushButton_paste.setFocusPolicy(Qt.NoFocus)
        self.pushButton_remove.setFocusPolicy(Qt.NoFocus)
        self.tableWidget_replace.setFocusPolicy(Qt.NoFocus)

        self.lineEdit_frame_no.clear()
        self.lineEdit_replaced_by.clear()

        self.pushButton_copy.clicked.connect(self.event_frame_no_copied)
        self.pushButton_paste.clicked.connect(self.event_frame_no_paste)
        self.pushButton_remove.clicked.connect(self.event_removed)

        # Table
        self.tableWidget_replace.clearContents()
        self.tableWidget_replace.setRowCount(0)


        self.alignment = [Qt.AlignRight | Qt.AlignVCenter,
                            Qt.AlignRight | Qt.AlignVCenter,
                            Qt.AlignRight | Qt.AlignVCenter]
        headers = ["shot", "frame", "by"]
        default_col_width = [60, 80, 80]
        for col_no, header_str, col_width in zip(range(len(headers)),
                                                    headers,
                                                    default_col_width):
            self.tableWidget_replace.horizontalHeaderItem(col_no).setText(header_str)
            self.tableWidget_replace.setColumnWidth(col_no, col_width)
        self.tableWidget_replace.horizontalHeader().setStretchLastSection(True)

        # Connect signals and filter events
        self.tableWidget_replace.selectionModel().selectionChanged.connect(self.event_replace_selected)
        self.tableWidget_replace.itemDoubleClicked[QTableWidgetItem].connect(self.event_move_to_frame_no)
        self.tableWidget_replace.installEventFilter(self)

        self.controller.signal_replace_list_refreshed[dict].connect(self.event_replace_list_refreshed)
        self.controller.signal_is_saved[str].connect(self.event_is_saved)

        self.installEventFilter(self)

        set_stylesheet(self)
        self.adjustSize()



    def set_initial_options(self, preferences:dict):
        log.info("set_initial_options")
        s = preferences['replace']

        self.is_edition_allowed = False

        self.block_signals(True)
        self.lineEdit_frame_no.clear()
        self.lineEdit_replaced_by.clear()
        self.tableWidget_replace.blockSignals(True)
        self.tableWidget_replace.clearContents()
        self.tableWidget_replace.setRowCount(0)

        self.pushButton_remove.setEnabled(False)
        self.pushButton_paste.setEnabled(False)
        self.pushButton_copy.setEnabled(False)

        self.pushButton_set_preview.setChecked(s['widget']['enabled'])
        self.block_signals(False)

        # Geometry
        self.move(s['geometry'][0], s['geometry'][1])
        self.adjustSize()


    def refresh_preview_options(self, new_preview_settings):
        try:
            enabled = new_preview_settings['replace']['enabled']
        except:
            enabled = False
        try:
            allowed = new_preview_settings['replace']['allowed']
        except:
            allowed = False
        self.is_edition_allowed = allowed

        if not enabled or not allowed:
            self.lineEdit_frame_no.clear()
            self.lineEdit_replaced_by.clear()

        self.lineEdit_frame_no.setEnabled(allowed)
        self.lineEdit_replaced_by.setEnabled(allowed)
        self.pushButton_copy.setEnabled(allowed)
        self.pushButton_paste.setEnabled(allowed)
        self.pushButton_remove.setEnabled(allowed)

        self.pushButton_set_preview.blockSignals(True)
        self.pushButton_set_preview.setEnabled(allowed)
        self.pushButton_set_preview.blockSignals(False)


    def event_replace_list_refreshed(self, values:dict):
        log.info("refresh list of frames to replace")
        self.tableWidget_replace.blockSignals(True)

        self.tableWidget_replace.clearContents()
        self.tableWidget_replace.setRowCount(0)
        for row_no, v in zip(range(len(values)), values):
            self.tableWidget_replace.insertRow(row_no)
            self.tableWidget_replace.setItem(row_no, 0, QTableWidgetItem(str(v['shot_no'])))
            self.tableWidget_replace.setItem(row_no, 1, QTableWidgetItem(str(v['dst'])))
            self.tableWidget_replace.setItem(row_no, 2, QTableWidgetItem(str(v['src'])))

            for i in range(len(self.alignment)):
                self.tableWidget_replace.item(row_no, i).setTextAlignment(self.alignment[i])
                self.tableWidget_replace.item(row_no, i).setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)

        self.tableWidget_replace.selectionModel().clearSelection()
        self.tableWidget_replace.blockSignals(False)
        self.tableWidget_replace.setEnabled(True)


    def event_replace_selected(self):
        if not self.is_edition_allowed:
            return
        log.info("event_replace_selected")
        self.tableWidget_replace.setFocus()


    def event_move_to_frame_no(self, item:QTableWidgetItem):
        # double-click
        row_no = item.row()
        column_no = item.column()
        if column_no == 0:
            return
        # log.info(f"selected frame at row={row_no}, column {row_no}")
        frame_no = int(self.tableWidget_replace.item(row_no, column_no).text())
        self.signal_frame_selected.emit(frame_no)


    def event_selection_removed(self):
        if not self.is_edition_allowed:
            return
        print("event_selection_removed")
        selected_indexes = self.tableWidget_replace.selectedIndexes()
        selected_row_nos = list(set([i.row() for i in selected_indexes]))
        selected_frame_nos = list(map(lambda x: int(self.tableWidget_replace.item(x,1).text()),
                selected_row_nos))

        if len(selected_frame_nos) > 0:
            self.pushButton_discard.setEnabled(True)
            self.pushButton_save.setEnabled(True)

        for frame_no in selected_frame_nos:
            self.signal_replace_modified.emit({
                'action': 'remove',
                'dst': frame_no
            })


    def refresh_values(self, frame:dict):
        if 'replaces' in frame.keys():
            # print("this frame (%d) replaces %d" % (frame['frame_no'], frame['replace']))
            self.lineEdit_frame_no.setText(str(frame['replace']))
            self.lineEdit_replaced_by.setText(str(frame['frame_no']))
            self.pushButton_remove.setEnabled(True)
        else:
            self.lineEdit_frame_no.setText(str(frame['frame_no']))
            try:
                self.lineEdit_replaced_by.setText(str(frame['replaced_by']))
                self.pushButton_remove.setEnabled(True)
            except:
                self.lineEdit_replaced_by.clear()
                self.pushButton_remove.setEnabled(False)


    def event_frame_no_copied(self):
        if not self.is_edition_allowed:
            return

        self.copied_frame_no = int(self.lineEdit_frame_no.text())
        log.info("event: copy %d" % (self.copied_frame_no))
        self.pushButton_paste.setEnabled(True)


    def event_frame_no_paste(self):
        if not self.is_edition_allowed:
            return

        log.info("event: paste")
        frame_no = int(self.lineEdit_frame_no.text())
        if (self.copied_frame_no != -1
        and frame_no != self.copied_frame_no):
            log.info("event: paste to %d" % (frame_no))
            self.pushButton_discard.setEnabled(True)
            self.pushButton_save.setEnabled(True)
            self.signal_replace_modified.emit({
                'src': self.copied_frame_no,
                'dst': frame_no,
                'action': 'replace'
            })


    def event_undo_replace(self):
        if not self.is_edition_allowed:
            return
        log.info("event: undo for frame_no: %d")
        self.signal_replace_modified.emit({
            'action': 'undo',
            'dst': int(self.lineEdit_frame_no.text())
        })


    def event_removed(self):
        if not self.is_edition_allowed:
            return
        log.info("event: remove")
        self.pushButton_discard.setEnabled(True)
        self.pushButton_save.setEnabled(True)
        self.signal_replace_modified.emit({
            'action': 'remove',
            'dst': int(self.lineEdit_frame_no.text())
        })


    def get_preview_options(self):
        preview_options = {
            'allowed': self.is_edition_allowed,
            'enabled': self.pushButton_set_preview.isChecked(),
        }
        return preview_options


    def block_signals(self, enabled):
        self.pushButton_copy.blockSignals(enabled)
        self.pushButton_paste.blockSignals(enabled)
        self.pushButton_remove.blockSignals(enabled)
        self.pushButton_set_preview.blockSignals(enabled)
        self.pushButton_discard.blockSignals(enabled)
        self.pushButton_save.blockSignals(enabled)


    def event_key_pressed(self, event):
        if not self.is_edition_allowed:
            return False

        key = event.key()
        modifiers = event.modifiers()
        # print("%s.event_key_pressed: %d, modifiers=" % (__name__, key), modifiers)

        if modifiers & Qt.ControlModifier:
            if key == Qt.Key_S:
                self.event_save_modifications()
                return True

            elif key == Qt.Key_C:
                self.event_frame_no_copied()
                return True
            elif key == Qt.Key_V:
                self.event_frame_no_paste()
                return True
            # elif key == Qt.Key_Z:
            #     self.event_undo()
            #     return True

        if key == Qt.Key_F2:
            if self.pushButton_set_preview.isEnabled():
                self.pushButton_set_preview.toggle()
                return True

        if QApplication.focusObject() is self.tableWidget_replace:
            if key == Qt.Key_Delete:
                self.event_selection_removed()
                return True

        # elif key == Qt.Key_R:
        #     new_index = self.controller.get_next_replaced_frame_index(index=self.slider_frames.value())
        #     if new_index != -1:
        #         self.move_slider_to(new_index)

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
                self.tableWidget_replace.selectAll()
                event.accept()
                return True
            elif key == Qt.Key_Delete:
                self.event_selection_removed()
                return True

            return self.ui.keyPressEvent(event)

        # print(event.type())
        if event.type() == QEvent.FocusOut:
            self.tableWidget_replace.clearSelection()

        elif event.type() == QEvent.Enter:
            self.is_entered = True
        elif event.type() == QEvent.Leave:
            self.is_entered = False

        return super().eventFilter(watched, event)

