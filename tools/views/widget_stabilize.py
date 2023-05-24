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
    QPoint,
)
from PySide6.QtGui import (
    QKeyEvent,
)
from PySide6.QtWidgets import (
    QApplication,
    QTableWidgetItem,
)
from views.guidelines import Guidelines
from views.widget_segments import Widget_segments

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
        self.widget_segments.selectionModel().selectionChanged.connect(self.event_segment_selected)
        self.widget_segments.itemDoubleClicked[QTableWidgetItem].connect(self.event_segment_double_clicked)
        self.widget_segments.signal_segment_modified[int].connect(self.event_segment_modified)

        # Buttons, etc.
        self.groupBox_stabilize.clicked.connect(self.event_settings_enable_toggled)
        self.label_message.clear()
        self.lineEdit_coordinates.clear()
        self.pushButton_show_tracker.toggled[bool].connect(self.event_show_tracker_toggled)


        # Signals
        self.pushButton_stabilize.clicked.connect(self.event_stabilize_requested)
        self.pushButton_guidelines.toggled[bool].connect(self.guidelines_state_changed)
        self.groupBox_stabilize.installEventFilter(self)
        self.groupBox_stabilize.blockSignals(True)
        self.widget_segments.installEventFilter(self)
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
        self.widget_segments.clear_contents()

        # Push button is used to calculate then display
        self.is_obsolete = True
        try:
            self.pushButton_set_preview.setEnabled(s['widget']['allowed'])
            self.pushButton_set_preview.setChecked(s['widget']['enabled'])
            self.previous_preview_state = s['widget']['enabled']
            self.initial_preview_state = s['widget']['enabled']
            self.pushButton_show_tracker.setChecked(s['widget']['show_tracker'])
            self.pushButton_show_tracker.setEnabled(s['widget']['allowed'])
        except:
            self.pushButton_set_preview.setEnabled(False)
            self.pushButton_set_preview.setChecked(False)
            self.previous_preview_state = False
            self.initial_preview_state = False
            self.pushButton_show_tracker.setChecked(False)
            self.pushButton_show_tracker.setEnabled(False)

        self.pushButton_stabilize.setEnabled(False)

        # Geometry
        self.move(s['geometry'][0], s['geometry'][1])
        self.block_signals(False)
        self.adjustSize()



    def refresh_preview_options(self, new_preview_settings):
        self.is_edition_allowed = new_preview_settings['stabilize']['allowed']
        enabled = new_preview_settings['stabilize']['enabled']

        self.pushButton_set_preview.blockSignals(True)
        self.pushButton_set_preview.setEnabled(self.is_edition_allowed)
        self.pushButton_show_tracker.setEnabled(self.is_edition_allowed)
        # self.pushButton_set_preview.setChecked(enabled)
        # self.previous_preview_state = enabled
        is_checked = self.pushButton_set_preview.isChecked()
        self.pushButton_set_preview.blockSignals(False)
        # log.info(f"enable: {is_checked}, allowed: {self.is_edition_allowed}")


    def get_preview_options(self):
        # log.info(f"{self.objectName()}: get_preview_options")
        preview_options = {
            'allowed': self.is_edition_allowed,
            'enabled': self.pushButton_set_preview.isChecked(),
            'show_tracker': self.pushButton_show_tracker.isChecked(),
        }
        return preview_options



    def refresh_values(self, frame:dict):
        # Refresh some specific values refreshed and stored in the frame struct
        pass


    def block_signals(self, enabled:bool):
        self.pushButton_set_preview.blockSignals(enabled)
        self.pushButton_stabilize.blockSignals(enabled)
        self.groupBox_stabilize.blockSignals(enabled)
        self.widget_segments.blockSignals(enabled)


    def get_current_settings(self) -> dict:
        # Get new settings
        settings = {
            'enable': self.groupBox_stabilize.isChecked(),
            'segments' : self.widget_segments.get_content()
        }
        return settings


    def event_settings_enable_toggled(self, is_checked:bool=False):
        log.info(f"changed settings enable to {is_checked}")
        self.widget_segments.setEnabled(is_checked)

        if self.is_enabled_initial != is_checked:
            self.pushButton_discard.setEnabled(True)
            self.pushButton_save.setEnabled(True)
            self.event_segment_modified(segment_no=-1)

        self.pushButton_save.setEnabled(True)


    def event_stabilize_settings_refreshed(self, stabilize_settings):
        log.info("Refresh the widget table")

        self.block_signals(True)

        if stabilize_settings is None or len(stabilize_settings) == 0:
            self.groupBox_stabilize.setChecked(False)
            self.widget_segments.clear_contents()
            self.widget_segments.setEnabled(False)
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

        segments = stabilize_settings['segments']

        self.widget_segments.clear_contents()
        if len(segments) > 0:
            self.widget_segments.set_content(segments)
        else:
            row_no = 0
            self.pushButton_stabilize.setEnabled(False)
            self.is_obsolete = True
            # self.pushButton_set_preview.setEnabled(False)

        self.widget_segments.setEnabled(is_enabled)
        if is_enabled:
            self.widget_segments.selectRow(0)

        if 'error' in stabilize_settings.keys() and stabilize_settings['error']:
            self.label_message.setText("ERROR!")
            # Disable calculations/preview
            self.pushButton_stabilize.setEnabled(False)
            # self.pushButton_set_preview.setEnabled(False)
            # self.pushButton_set_preview.setChecked(False)
            self.previous_preview_state = False
            log.info('disable preview')
        elif self.is_obsolete:
            self.label_message.setText("Obsolete")
            self.pushButton_save.setEnabled(True)
            self.pushButton_discard.setEnabled(True)
            self.pushButton_stabilize.setEnabled(True)
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
        self.widget_segments.select_segment()


    def event_segment_double_clicked(self, item:QTableWidgetItem):
        frame_no = self.widget_segments.get_frame_no(item)
        if frame_no != -1:
            log.info(f"signal_frame_selected: {frame_no}")
            self.signal_frame_selected.emit(frame_no)


    def event_segment_modified(self, segment_no:int):
        # if segment_no == -1:
        #     # All table has been modified, get all table values
        #     print_lightcyan(f"Table is completely modified")
        # else:
        #     # Get only the modified segment
        settings = self.get_current_settings()
        self.signal_edition_started.emit()
        self.signal_settings_modified.emit(settings)


    def edition_started(self):
        log.info("stabilization is obsolete")
        self.is_obsolete = True
        self.label_message.setText("Obsolete")
        self.pushButton_save.setEnabled(True)
        self.pushButton_discard.setEnabled(True)
        self.pushButton_stabilize.setEnabled(True)

        # Send a signal to inform that the edition started
        self.signal_edition_started.emit()

    def event_start_modified(self):
        frame_no = self.controller.get_current_frame_no()
        self.widget_segments.set_frame_no('start', frame_no)


    def event_end_modified(self):
        frame_no = self.controller.get_current_frame_no()
        self.widget_segments.set_frame_no('end', frame_no)


    def event_from_modified(self):
        self.widget_segments.select_next_reference()

    def event_ref_modified(self):
        frame_no = self.controller.get_current_frame_no()
        self.widget_segments.set_frame_no('ref', frame_no)


    def event_mode_modified(self, key):
        option = ''
        if key == Qt.Key.Key_V:
            option = 'vertical'
        if key == Qt.Key.Key_H:
            option = 'horizontal'
        if key == Qt.Key.Key_R:
            option = 'rotation'
        self.widget_segments.select_mode_option(option)


    def event_stabilize_requested(self):
        log.info(f"Event: stabilize requested")
        print(f"Event: stabilize requested")
        if not self.pushButton_set_preview.isChecked():
            log.info("preview is not enabled, resquest stabilization=None")
            print("\tpreview is not enabled, resquest stabilization=None")
            settings = self.get_current_settings()
            self.signal_stabilization_requested.emit(settings)
        else:
            if (self.widget_segments.is_content_modified() or
                self.groupBox_stabilize.isChecked() != self.is_enabled_initial
                or self.is_obsolete):
                print(f"{self.widget_segments.is_content_modified()},"
                      f"{self.groupBox_stabilize.isChecked()} != {self.is_enabled_initial}",
                      f"{self.is_obsolete}")
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


    def event_show_tracker_toggled(self, is_checked:bool=False):
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

        if state and not self.__parent.is_widget_active(self.objectName()):
            # Enter this widget if not already active, otherwise, cannot move guidelines
            self.__parent.set_current_widget(self.objectName())

        self.signal_show_guidelines_changed.emit(state)


    def event_save_modifications(self):
        if self.pushButton_save.isEnabled():
            print_purple("Save stabilize")
            log.info(f"save widget_{self.objectName()}")
            self.pushButton_save.setEnabled(False)
            if (self.widget_segments.is_content_modified() or
                self.groupBox_stabilize.isChecked() != self.is_enabled_initial):
                settings = self.get_current_settings()
                self.signal_stabilization_requested.emit(settings)
                self.signal_save_settings.emit(settings)
            else:
                self.signal_save_settings.emit(None)
        else:
            log.info("cannot save, reason: button is disabled")


    def update_coordinates(self, position:QPoint):
        self.lineEdit_coordinates.setText(f"({position.x()}, {position.y()})")

    def event_key_pressed(self, event:QKeyEvent) -> bool:
        key = event.key()
        modifiers = event.modifiers()
        # print("%s.event_key_pressed: %d, modifiers=" % (__name__, key), modifiers)


        if modifiers & Qt.ControlModifier:
            if key == Qt.Key.Key_S:
                self.event_save_modifications()
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
        elif key == Qt.Key.Key_F:
            self.event_from_modified()
            return True
        elif key == Qt.Key.Key_N:
            self.event_ref_modified()
            return True
        elif key in [Qt.Key.Key_V, Qt.Key.Key_H, Qt.Key.Key_R]:
            self.event_mode_modified(key)
            return True

        elif key == Qt.Key.Key_Insert:
            self.widget_segments.append_segment()
            return True
        elif key == Qt.Key.Key_Delete:
            self.widget_segments.remove_segment()
            return True

        elif key == Qt.Key.Key_F2:
            if self.pushButton_set_preview.isEnabled():
                self.pushButton_set_preview.toggle()
                return True
        elif key == Qt.Key.Key_F7:
            # Force stabilization
            settings = self.get_current_settings()
            self.signal_stabilization_requested.emit(settings)
            return True

        if QApplication.focusObject() is self.widget_segments:
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
    #     #         self.widget_segments.select_all()
    #     #         event.accept()
    #     #         return True
    #     #     elif key == Qt.Key.Key_Delete:
    #     #         self.event_remove_segment_requested()
    #     #         return True
    #     #     return self.__parent.keyPressEvent(event)

    # #     # print(event.type())
    # #     # if event.type() == QEvent.FocusOut:
    # #     #     self.widget_segments.clearSelection()

    # #     if event.type() == QEvent.Enter:
    # #         self.is_entered = True
    # #     elif event.type() == QEvent.Leave:
    # #         self.is_entered = False
    #     # return super(Widget_stabilize, self).eventFilter(watched, event)

    #     return super().eventFilter(watched, event)

