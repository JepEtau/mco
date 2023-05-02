# -*- coding: utf-8 -*-
import sys

from functools import partial

from logger import log
from pprint import pprint

from PySide6.QtCore import (
    QObject,
    Qt,
    Signal,
    QEvent,
)
from PySide6.QtGui import (
    QKeyEvent,
)
from PySide6.QtWidgets import (
    QApplication,
    QTableWidgetItem,
)
from views.guidelines import Guidelines
from views.table_stabilize import Table_stabilize

from utils.stylesheet import (
    set_stylesheet,
    set_widget_stylesheet,
)
from controllers.controller import Controller_video_editor
from views.ui.widget_stabilize_ui import Ui_widget_stabilize
from views.widget_common import Widget_common
from utils.pretty_print import *


class Widget_stabilize(Widget_common, Ui_widget_stabilize):
    signal_settings_modified = Signal(dict)
    signal_segment_selected = Signal(dict)
    signal_frame_selected = Signal(int)
    signal_stabilization_requested = Signal(dict)
    signal_show_guidelines_changed = Signal(bool)
    signal_save_settings = Signal(dict)

    def __init__(self, parent, controller:Controller_video_editor):
        super(Widget_stabilize, self).__init__(parent)
        self.controller = controller
        self.__parent = parent
        self.setObjectName('stabilize')

        # Internal variables
        self.previous_position = None
        self.removed_segment = None
        self.segment_count = 0
        self.is_edition_allowed = False
        self.previous_preview_state = False
        self.initial_preview_state = False
        self.is_obsolete = True

        # Guidelines
        self.guidelines = Guidelines()

        # Table
        self.tableWidget_stabilize.selectionModel().selectionChanged.connect(self.event_segment_selected)
        self.tableWidget_stabilize.itemDoubleClicked[QTableWidgetItem].connect(self.event_segment_double_clicked)

        # Buttons, etc.
        self.groupBox_stabilize.clicked.connect(self.event_settings_enable_toggled)
        self.label_message.clear()

        # Signals
        self.pushButton_stabilize.clicked.connect(self.event_stabilize_requested)
        self.pushButton_guidelines.toggled[bool].connect(self.guidelines_state_changed)
        self.groupBox_stabilize.installEventFilter(self)
        self.groupBox_stabilize.blockSignals(True)
        self.tableWidget_stabilize.installEventFilter(self)
        self.tableWidget_stabilize.set_parent(self)
        self.installEventFilter(self)

        self.controller.signal_stabilize_settings_refreshed[dict].connect(self.event_stabilize_settings_refreshed)
        self.controller.signal_stabilization_done.connect(self.event_stabilization_done)
        self.controller.signal_is_saved[str].connect(self.event_is_saved)

        set_stylesheet(self)
        set_widget_stylesheet(self.label_message, 'message')
        self.adjustSize()



    def set_initial_options(self, preferences:dict):
        log.info("set_initial_options")
        s = preferences['stabilize']
        self.block_signals(True)

        self.groupBox_stabilize.setChecked(False)
        self.tableWidget_stabilize.clear_contents()

        # Push button is used to calculate then display
        self.pushButton_set_preview.setEnabled(s['widget']['allowed'])
        self.pushButton_set_preview.setChecked(s['widget']['enabled'])
        self.previous_preview_state = s['widget']['enabled']
        self.initial_preview_state = s['widget']['enabled']
        self.pushButton_stabilize.setEnabled(False)
        self.is_obsolete = True



        # Geometry
        self.move(s['geometry'][0], s['geometry'][1])
        self.block_signals(False)
        self.adjustSize()



    def refresh_preview_options(self, new_preview_settings):
        self.is_edition_allowed = new_preview_settings['stabilize']['allowed']
        enabled = new_preview_settings['stabilize']['enabled']

        self.pushButton_set_preview.blockSignals(True)
        self.pushButton_set_preview.setEnabled(self.is_edition_allowed)
        self.pushButton_set_preview.setChecked(enabled)
        # self.previous_preview_state = enabled
        self.pushButton_set_preview.blockSignals(False)
        log.info(f"enable: {enabled}, allowed: {self.is_edition_allowed}")


    def get_preview_options(self):
        log.info(f"{self.objectName()}: get_preview_options")
        preview_options = {
            'allowed': self.is_edition_allowed,
            'enabled': self.pushButton_set_preview.isChecked(),
        }
        return preview_options



    def refresh_values(self, frame:dict):
        # Refresh some specific values refreshed and stored in the frame struct
        pass


    def block_signals(self, enabled:bool):
        self.pushButton_set_preview.blockSignals(enabled)
        self.pushButton_stabilize.blockSignals(enabled)
        self.groupBox_stabilize.blockSignals(enabled)
        self.tableWidget_stabilize.blockSignals(enabled)


    def get_current_settings(self) -> dict:
        # Get new settings
        settings = {
            'enable': self.groupBox_stabilize.isChecked(),
            'segments' : self.tableWidget_stabilize.get_content()
        }
        return settings


    def event_settings_enable_toggled(self, is_checked:bool=False):
        log.info(f"changed settings enable to {is_checked}")
        self.tableWidget_stabilize.setEnabled(is_checked)
        if self.is_enabled_initial != is_checked:
            if self.tableWidget_stabilize.is_content_modified():
                log.info("segments have been modified")
                settings = self.get_current_settings()
                self.edition_started()
                self.signal_settings_modified.emit(settings)
            else:
                log.info("segments have NOT been modified")
                self.pushButton_discard.setEnabled(False)
                self.pushButton_save.setEnabled(False)

        self.pushButton_save.setEnabled(True)


    def event_stabilize_settings_refreshed(self, stabilize_settings):
        log.info("Refresh the widget table")

        self.block_signals(True)

        if stabilize_settings is None or len(stabilize_settings) == 0:
            self.groupBox_stabilize.setChecked(False)
            self.tableWidget_stabilize.clear_contents()
            self.tableWidget_stabilize.setEnabled(False)
            # self.pushButton_set_preview.setEnabled(False)
            # self.pushButton_set_preview.setChecked(False)
            # self.previous_preview_state = False
            self.is_enabled_initial = False
            self.block_signals(False)
            self.label_message.setText("")
            return

        is_enabled = stabilize_settings['enable']
        self.is_enabled_initial = is_enabled
        self.groupBox_stabilize.setChecked(is_enabled)

        table = self.tableWidget_stabilize
        segments = stabilize_settings['segments']

        self.tableWidget_stabilize.clear_contents()
        if len(segments) > 0:
            self.tableWidget_stabilize.set_content(segments)
        else:
            row_no = 0
            self.pushButton_stabilize.setEnabled(False)
            self.is_obsolete = True
            # self.pushButton_set_preview.setEnabled(False)

        self.tableWidget_stabilize.setEnabled(is_enabled)
        if is_enabled:
            table.selectRow(0)

        if 'error' in stabilize_settings.keys() and stabilize_settings['error']:
            self.label_message.setText("ERROR!")
            # Disable calculations/preview
            self.pushButton_stabilize.setEnabled(False)
            # self.pushButton_set_preview.setEnabled(False)
            # self.pushButton_set_preview.setChecked(False)
            self.previous_preview_state = False
            log.info('disable preview')
        elif self.is_obsolete:
            self.edition_started()
        else:
            log.info('disable stabilize button')
            self.label_message.clear()
            self.pushButton_stabilize.setEnabled(False)

        self.block_signals(False)
        if (self.initial_preview_state and self.is_obsolete):
            # Initial preview option
            log.info("initial preview option: stabilize")
            self.initial_preview_state = False
            self.event_stabilize_requested()
            # self.event_set_preview_toggled(True)


    def event_segment_selected(self):
        log.info("segment selected")
        self.tableWidget_stabilize.select_segment()


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
        log.info(f"signal_frame_selected: {frame_no}")
        self.signal_frame_selected.emit(frame_no)




    def edition_started(self):
        log.info("stabilization is obsolete")
        self.is_obsolete = True
        self.label_message.setText("Obsolete")
        self.pushButton_save.setEnabled(True)
        self.pushButton_discard.setEnabled(True)
        self.pushButton_stabilize.setEnabled(True)


    def event_start_modified(self):
        frame_no = self.controller.get_current_frame_no()
        self.tableWidget_stabilize.set_frame_no('start', frame_no)
        self.edition_started()


    def event_end_modified(self):
        frame_no = self.controller.get_current_frame_no()
        self.tableWidget_stabilize.set_frame_no('end', frame_no)
        self.edition_started()


    def event_ref_modified(self):
        self.tableWidget_stabilize.select_next_reference()
        self.edition_started()


    def event_mode_modified(self, key):
        option = ''
        if key == Qt.Key.Key_V:
            option = 'vertical'
        if key == Qt.Key.Key_H:
            option = 'horizontal'
        if key == Qt.Key.Key_R:
            option = 'rotation'
        self.tableWidget_stabilize.select_mode_option(option)
        self.edition_started()


    def undo_requested(self):
        self.tableWidget_stabilize.undo()
        if self.tableWidget_stabilize.is_content_modified():
            self.edition_started()
        else:
            self.pushButton_discard.setEnabled(False)
            self.pushButton_save.setEnabled(False)


    def event_stabilize_requested(self):
        log.info(f"Event: stabilize requested")
        print(f"Event: stabilize requested")
        if not self.pushButton_set_preview.isChecked():
            log.info("preview is not enabled, resquest stabilization=None")
            print("\tpreview is not enabled, resquest stabilization=None")
            settings = self.get_current_settings()
            self.signal_stabilization_requested.emit(settings)
        else:
            if (self.tableWidget_stabilize.is_content_modified() or
                self.groupBox_stabilize.isChecked() != self.is_enabled_initial):
                # Settings have been modified, request to stabilize
                # If initial state was disabled, stabilize has not been done
                log.info(f"Request to stabilize")
                print(f"\tRequest to stabilize")
                self.pushButton_discard.setEnabled(True)
                self.pushButton_save.setEnabled(True)
                settings = self.get_current_settings()
                self.signal_stabilization_requested.emit(settings)
            else:
                # Settings have not been modified, just refresh
                log.info(f"Request to refresh without recalculate")
                print(f"\tRequest to refresh without recalculate")
                self.pushButton_discard.setEnabled(False)
                self.pushButton_save.setEnabled(False)
                self.signal_preview_options_changed.emit()


    def event_stabilization_done(self):
        log.info('stabilization done')
        self.pushButton_stabilize.setEnabled(False)
        self.is_obsolete = False
        self.initial_preview_state = False
        self.label_message.clear()


    def event_set_preview_toggled(self, is_checked:bool=False):
        log.info(f"preview button changed to {is_checked}")
        if not is_checked:
            self.previous_preview_state = is_checked
            self.is_obsolete = True
            self.signal_preview_options_changed.emit()
        else:
            self.previous_preview_state = is_checked
            print_purple("Changed preview to enabled, request to calculate")
            self.event_stabilize_requested()


    def guidelines_state_changed(self, state):
        self.guidelines.set_enabled(state)
        self.signal_show_guidelines_changed.emit(state)


    def event_save_modifications(self):
        if self.pushButton_save.isEnabled():
            print_purple("Save stabilize")
            log.info(f"save widget_{self.objectName()}")
            self.pushButton_save.setEnabled(False)
            if (self.tableWidget_stabilize.is_content_modified() or
                self.groupBox_stabilize.isChecked() != self.is_enabled_initial):
                settings = self.get_current_settings()
                self.signal_stabilization_requested.emit(settings)
                self.signal_save_settings.emit(settings)
            else:
                self.signal_save_settings.emit(None)
        else:
            log.info("cannot save, reason: button is disabled")


    def event_key_pressed(self, event:QKeyEvent) -> bool:
        key = event.key()
        modifiers = event.modifiers()
        # print("%s.event_key_pressed: %d, modifiers=" % (__name__, key), modifiers)


        if modifiers & Qt.ControlModifier:
            if key == Qt.Key.Key_S:
                self.event_save_modifications()
                return True
            elif key == Qt.Key.Key_Z:
                self.undo_requested()
                return True

        elif key == Qt.Key.Key_F3:
            self.pushButton_guidelines.toggle()
            return True
        elif key == Qt.Key.Key_S:
            self.event_start_modified()
            return True
        elif key == Qt.Key.Key_E:
            self.event_end_modified()
            return True
        elif key == Qt.Key.Key_I:
            self.event_ref_modified()
            return True
        elif key in [Qt.Key.Key_V, Qt.Key.Key_H, Qt.Key.Key_R]:
            self.event_mode_modified(key)
            return True

        elif key == Qt.Key.Key_Insert:
            self.tableWidget_stabilize.append_segment()
            return True


        elif key == Qt.Key.Key_F2:
            if self.pushButton_set_preview.isEnabled():
                self.pushButton_set_preview.toggle()
                return True
        elif key == Qt.Key.Key_F7:
            self.event_stabilize_requested()
            return True

        if QApplication.focusObject() is self.tableWidget_stabilize:
            if key == Qt.Key.Key_Delete:
                log.info("delete segment")
                return True

        return False



    # def eventFilter(self, watched: QObject, event: QEvent) -> bool:
    #     # print("* eventFilter: widget_%s: " % (self.objectName()), event.type())

    #     # Filter press/release events
    #     if event.type() == QEvent.KeyPress:
    #         key = event.key()
    #         if key == Qt.Key.Key_Space:
    #             return self.__parent.keyPressEvent(event)
    #         else:
    #             return super(Widget_stabilize, self).eventFilter(watched, event)
    #     #     if modifier & Qt.ControlModifier and key == Qt.Key.Key_A:
    #     #         self.tableWidget_stabilize.select_all()
    #     #         event.accept()
    #     #         return True
    #     #     elif key == Qt.Key.Key_Delete:
    #     #         self.event_remove_segment_requested()
    #     #         return True
    #     #     return self.__parent.keyPressEvent(event)

    # #     # print(event.type())
    # #     # if event.type() == QEvent.FocusOut:
    # #     #     self.tableWidget_stabilize.clearSelection()

    # #     if event.type() == QEvent.Enter:
    # #         self.is_entered = True
    # #     elif event.type() == QEvent.Leave:
    # #         self.is_entered = False
    #     # return super(Widget_stabilize, self).eventFilter(watched, event)

    #     return super().eventFilter(watched, event)

