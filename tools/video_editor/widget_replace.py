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

from video_editor.model_video_editor import Model_video_editor
from video_editor.ui.widget_replace_ui import Ui_widget_replace
from common.widget_common import Widget_common

class Widget_replace(Widget_common, Ui_widget_replace):
    signal_replace_modified = Signal(dict)
    signal_frame_selected = Signal(dict)

    def __init__(self, ui, model:Model_video_editor):
        super(Widget_replace, self).__init__(ui)
        self.model = model
        self.ui = ui
        self.setObjectName('replace')

        # Internal variables
        self.copied_frame_no = -1
        self.previous_position = None
        self.current_edition_and_preview_enabled = True

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
        headers = ["shot no.", "frame no.", "new"]
        default_col_width = [70, 100, 100]
        for col_no, header_str, col_width in zip(range(len(headers)),
                                                    headers,
                                                    default_col_width):
            self.tableWidget_replace.horizontalHeaderItem(col_no).setText(header_str)
            self.tableWidget_replace.setColumnWidth(col_no, col_width)
        self.tableWidget_replace.horizontalHeader().setStretchLastSection(True)

        # Connect signals and filter events
        self.tableWidget_replace.selectionModel().selectionChanged.connect(self.event_replace_selected)
        self.tableWidget_replace.itemDoubleClicked[QTableWidgetItem].connect(self.event_replace_frame_selected)
        self.tableWidget_replace.installEventFilter(self)

        self.model.signal_replace_list_refreshed[dict].connect(self.event_replace_list_refreshed)
        self.model.signal_is_saved[str].connect(self.event_is_saved)

        self.installEventFilter(self)

        set_stylesheet(self)
        self.adjustSize()



    def set_initial_options(self, preferences:dict):
        log.info("set_initial_options")
        s = preferences['replace']

        self.lineEdit_frame_no.clear()
        self.lineEdit_replaced_by.clear()
        self.tableWidget_replace.blockSignals(True)
        self.tableWidget_replace.clearContents()
        self.tableWidget_replace.setRowCount(0)

        self.pushButton_remove.setEnabled(False)
        self.pushButton_paste.setEnabled(False)
        self.pushButton_copy.setEnabled(True)

        # Geometry
        self.move(s['geometry'][0], s['geometry'][1])
        self.adjustSize()


    def set_edition_and_preview_enabled(self, enabled):
        # Disable all action button because it cannot be applied for this
        # Save current state to reenable it
        if (not self.current_edition_and_preview_enabled
        and not enabled):
            log.info("already disabled")
            # already disabled, do not save another time
            return

        if (self.current_edition_and_preview_enabled
        and enabled):
            log.info("already enabled")
            # already disabled, do not save another time
            return

        self.current_edition_and_preview_enabled = enabled
        if not enabled:
            log.info("disable edition")
            self



        self.pushButton_set_preview.blockSignals(True)
        self.pushButton_set_preview.setChecked(enabled)
        self.pushButton_set_preview.blockSignals(False)



    def event_replace_list_refreshed(self, values:dict):
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
        log.info("event_replace_selected")
        self.tableWidget_replace.setFocus()


    def event_replace_frame_selected(self, item:QTableWidgetItem):
        # double-click
        row_no = item.row()
        log.info("selected frame at row=%d" % (row_no))
        frame_no = int(self.tableWidget_replace.item(row_no, 1).text())
        shot_no = int(self.tableWidget_replace.item(row_no, 0).text())
        self.signal_frame_selected.emit({
            'shot_no': shot_no,
            'frame_no': frame_no,
        })


    def event_selection_removed(self):
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
            if frame['replaced_by'] == -1:
                self.lineEdit_replaced_by.clear()
                self.pushButton_remove.setEnabled(False)
            else:
                self.lineEdit_replaced_by.setText(str(frame['replaced_by']))
                self.pushButton_remove.setEnabled(True)


    def event_frame_no_copied(self):
        self.copied_frame_no = int(self.lineEdit_frame_no.text())
        log.info("event: copy %d" % (self.copied_frame_no))
        self.pushButton_paste.setEnabled(True)


    def event_frame_no_paste(self):
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
        log.info("event: undo for frame_no: %d")
        self.signal_replace_modified.emit({
            'action': 'undo',
            'dst': int(self.lineEdit_frame_no.text())
        })


    def event_removed(self):
        log.info("event: remove")
        self.pushButton_discard.setEnabled(True)
        self.pushButton_save.setEnabled(True)
        self.signal_replace_modified.emit({
            'action': 'remove',
            'dst': int(self.lineEdit_frame_no.text())
        })


    def get_preview_options(self):
        preview_options = {
            'is_enabled': self.pushButton_set_preview.isChecked(),
        }
        return preview_options


    def block_signals(self, enabled):
        self.pushButton_copy.blockSignals(enabled)
        self.pushButton_paste.blockSignals(enabled)
        self.pushButton_remove.blockSignals(enabled)


    def event_key_pressed(self, event):
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
        #     new_index = self.model.get_next_replaced_frame_index(index=self.slider_frames.value())
        #     if new_index != -1:
        #         self.update_slider_value(new_index)

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

