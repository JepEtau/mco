# -*- coding: utf-8 -*-

import sys
sys.path.append('../scripts')

from logger import log
from pprint import pprint

from PySide6.QtCore import (
    Qt,
    Signal,
    QEvent,
)
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QWidget

from common.widget_common import Widget_common
from common.sylesheet import set_stylesheet

from merge_stabilize.model_merge_stabilize import Model_merge_stabilize
from merge_stabilize.ui.widget_geometry_ui import Ui_widget_geometry


class Widget_geometry(Widget_common, Ui_widget_geometry):
    signal_calculation_requested = Signal(dict)
    signal_enabled_modified = Signal(bool)
    signal_previous_parameters = Signal(str)
    signal_save = Signal()
    signal_preview_options_changed = Signal()


    def __init__(self, ui, model:Model_merge_stabilize):
        super(Widget_geometry, self).__init__(ui)
        self.model = model
        self.ui = ui
        self.setObjectName('geometry')

        # Disable focus
        self.lineEdit_st_crop_rectangle.setFocusPolicy(Qt.NoFocus)
        self.spinBox_st_width.setFocusPolicy(Qt.NoFocus)
        self.spinBox_st_height.setFocusPolicy(Qt.NoFocus)
        self.lineEdit_final_crop_rectangle.setFocusPolicy(Qt.NoFocus)
        self.pushButton_st_crop_edition.setFocusPolicy(Qt.NoFocus)
        self.pushButton_st_crop_preview.setFocusPolicy(Qt.NoFocus)
        self.pushButton_st_resize_edition.setFocusPolicy(Qt.NoFocus)
        self.pushButton_st_resize_preview.setFocusPolicy(Qt.NoFocus)
        self.pushButton_final_crop_edition.setFocusPolicy(Qt.NoFocus)
        self.pushButton_final_crop_preview.setFocusPolicy(Qt.NoFocus)
        self.pushButton_final_resize_preview.setFocusPolicy(Qt.NoFocus)
        self.checkBox_keep_ratio.setFocusPolicy(Qt.NoFocus)


        self.pushButton_st_crop_edition.toggled[bool].connect(self.event_st_crop_edition_changed)
        self.pushButton_st_crop_preview.toggled[bool].connect(self.event_st_crop_preview_changed)
        self.pushButton_st_resize_edition.toggled[bool].connect(self.event_st_resize_edition_changed)
        self.pushButton_st_resize_preview.toggled[bool].connect(self.event_st_resize_preview_changed)
        self.pushButton_final_crop_edition.toggled[bool].connect(self.event_crop_edition_changed)
        self.pushButton_final_crop_preview.toggled[bool].connect(self.event_crop_preview_changed)
        self.pushButton_final_resize_preview.toggled[bool].connect(self.event_resize_edition_changed)
        self.checkBox_keep_ratio.toggled[bool].connect(self.event_keep_ratio_changed)


        self.set_edition_mode('st')
        # self.model.signal_is_saved[list].connect(self.event_is_saved)

        set_stylesheet(self)
        self.adjustSize()



    def set_initial_options(self, preferences:dict):
        log.info("set_initial_options")
        s = preferences['geometry']

        # Geometry
        self.move(s['geometry'][0], s['geometry'][1])
        self.adjustSize()


    def set_edition_and_preview_enabled(self, enabled):
        pass

    def set_parameters(self, parameters, do_backup=True):
        log.info("set geometry parameters")
        self.is_save_action_allowed = False

        # self.pushButton_load_default.setEnabled(True)
        # self.pushButton_undo.setEnabled(False)

        # self.block_signals(False)


    def event_undo(self):
        # Replace by historical implementation in model
        pass


    def get_parameters(self):
        log.info("get parameters")
        return None


    def event_is_modified(self, parameter='', value=0):
        log.info("parameter has been modified: %s, %d" % (parameter, value))
        # self.is_save_action_allowed = False
        # if self.spinBox_frame_start.value() >= self.spinBox_frame_end.value():
        #     log.info("start > end")
        #     self.pushButton_calculate.setEnabled(False)
        #     self.pushButton_save.setEnabled(False)
        # else:
        #     self.pushButton_calculate.setEnabled(True)
        #     self.pushButton_set_preview.setEnabled(False)
        # self.pushButton_undo.setEnabled(True)
        # self.pushButton_discard.setEnabled(True)


    def event_load_default(self):
        # self.block_signals(True)
        # self.block_signals(False)
        # self.pushButton_calculate.setEnabled(True)
        # self.pushButton_set_preview.setEnabled(False)
        return


    def set_edition_mode(self, mode:str):
        log.info("change edition to: %s" % (mode))
        if mode == 'st':
            self.mode = mode
            self.groupBox_st_geometry.setEnabled(True)
            self.pushButton_st_crop_edition.blockSignals(False)
            self.pushButton_st_crop_preview.blockSignals(False)
            self.pushButton_st_resize_edition.blockSignals(False)
            self.pushButton_st_resize_preview.blockSignals(False)
            self.groupBox_final_geometry.setEnabled(False)
            self.pushButton_final_crop_edition.blockSignals(True)
            self.pushButton_final_crop_preview.blockSignals(True)
            self.pushButton_final_resize_preview.blockSignals(True)

        elif mode == 'final':
            self.mode = mode
            self.groupBox_st_geometry.setEnabled(False)
            self.pushButton_st_crop_edition.blockSignals(True)
            self.pushButton_st_crop_preview.blockSignals(True)
            self.pushButton_st_resize_edition.blockSignals(True)
            self.pushButton_st_resize_preview.blockSignals(True)
            self.groupBox_final_geometry.setEnabled(True)
            self.pushButton_final_crop_edition.blockSignals(False)
            self.pushButton_final_crop_preview.blockSignals(False)
            self.pushButton_final_resize_preview.blockSignals(False)




    def get_preview_options(self):
        preview_options = {
            'is_enabled': self.pushButton_set_preview.isChecked(),
            'st': {
                'is_enabled': True if self.mode == 'st' else False,
                'crop_edition': self.pushButton_st_crop_edition.isChecked(),
                'crop_preview': self.pushButton_st_crop_preview.isChecked(),
                'resize_edition': self.pushButton_st_resize_edition.isChecked(),
                'resize_preview': self.pushButton_st_resize_preview.isChecked(),
            },
            'final': {
                'is_enabled': True if self.mode == 'final' else False,
                'crop_edition': self.pushButton_final_crop_edition.isChecked(),
                'crop_preview': self.pushButton_final_crop_preview.isChecked(),
                'resize_preview': self.pushButton_final_resize_preview.isChecked(),
            },
        }


        return preview_options


    def event_preview_changed(self, state:bool=False):
        # if self.pushButton_calculate.isEnabled():
        #     self.groupBox_stabilize.blockSignals(True)
        #     self.groupBox_stabilize.setEnabled(True)
        #     self.groupBox_stabilize.blockSignals(False)
        # else:
        #     self.groupBox_stabilize.blockSignals(True)
        #     self.groupBox_stabilize.setEnabled(True)
        #     self.groupBox_stabilize.blockSignals(False)
        self.signal_preview_options_changed.emit()




    def event_st_crop_edition_changed(self, state:bool):
        if state:
            if not self.pushButton_st_crop_preview.isChecked():
                # show rect
                # -> disable resize preview
                self.pushButton_st_resize_preview.blockSignals(True)
                self.pushButton_st_resize_preview.setChecked(False)
                self.pushButton_st_resize_preview.blockSignals(False)
                # -> disable resize edition
                self.pushButton_st_resize_edition.blockSignals(True)
                self.pushButton_st_resize_edition.setChecked(False)
                self.pushButton_st_resize_edition.blockSignals(False)
        self.event_preview_changed()


    def event_st_crop_preview_changed(self, state:bool):
        if not state:
            # Do not preview crop
            self.pushButton_st_crop_preview.blockSignals(True)
            self.pushButton_st_crop_preview.setChecked(False)
            self.pushButton_st_crop_preview.blockSignals(False)
            if self.pushButton_st_crop_edition.isChecked():
                # -> disable resize preview
                self.pushButton_st_resize_preview.blockSignals(True)
                self.pushButton_st_resize_preview.setChecked(False)
                self.pushButton_st_resize_preview.blockSignals(False)
                # -> disable resize edition
                self.pushButton_st_resize_edition.blockSignals(True)
                self.pushButton_st_resize_edition.setChecked(False)
                self.pushButton_st_resize_edition.blockSignals(False)

        self.event_preview_changed()


    def event_st_resize_edition_changed(self, state:bool):
        if state:
            # Force crop preview
            self.pushButton_st_crop_preview.blockSignals(True)
            self.pushButton_st_crop_preview.setChecked(True)
            self.pushButton_st_crop_preview.blockSignals(False)
        self.event_preview_changed()


    def event_st_resize_preview_changed(self, state:bool):
        if state:
            # Force crop preview
            self.pushButton_st_crop_preview.blockSignals(True)
            self.pushButton_st_crop_preview.setChecked(True)
            self.pushButton_st_crop_preview.blockSignals(False)
        self.event_preview_changed()


    def event_crop_edition_changed(self, state:bool):
        self.event_preview_changed()

    def event_crop_preview_changed(self, state:bool):
        self.event_preview_changed()

    def event_resize_edition_changed(self, state:bool):
        self.event_preview_changed()


    def event_keep_ratio_changed(self, state:bool):
        log.info("set ratio: %s" % ('true' if state else 'false'))
        self.event_preview_changed()


    def event_is_saved(self, k_type):
        if k_type == 'geometry':
            log.info("parameters and values saved")
            self.is_save_action_allowed = False
            self.pushButton_discard.setEnabled(False)


    def event_discard_modifications(self):
        log.info("discard modifications")
        # parameters = self.model.reset_and_get_initial_shot_stabilize_parameters()
        # self.set_parameters(parameters, do_backup=False)
        # self.pushButton_undo.setEnabled(True)
        # self.pushButton_calculate.setEnabled(True)
        # self.pushButton_discard.setEnabled(False)


    def event_save(self):
        if self.is_save_action_allowed:
            self.signal_save.emit()

    def event_close(self):
        log.info("close button clicked")
        # self.signal_action.emit('close')



    def event_key_pressed(self, event):
        key = event.key()
        modifiers = event.modifiers()
        # print("%s.keyPressEvent: %d" % (__name__, event.key))

        if modifiers & Qt.ControlModifier:
            if key == Qt.Key_S:
                self.event_save()
                return True

        return False


