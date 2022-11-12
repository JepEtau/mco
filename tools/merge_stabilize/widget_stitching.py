# -*- coding: utf-8 -*-

import sys
sys.path.append('../scripts')
from copy import deepcopy

from logger import log
from pprint import pprint

from PySide6.QtCore import (
    Qt,
    Signal,
    QObject,
    QEvent,
)
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
)
from common.widget_common import Widget_common
from common.sylesheet import set_stylesheet

from merge_stabilize.model_merge_stabilize import Model_merge_stabilize
from merge_stabilize.ui.widget_stitching_ui import Ui_widget_stitching
from parsers.parser_stitching import STITCHING_SHOT_PARAMETERS_DEFAULT


class Widget_stitching(Widget_common, Ui_widget_stitching):
    signal_calculation_requested = Signal(dict)
    signal_enabled_modified = Signal(bool)
    signal_previous_parameters = Signal(str)
    signal_save = Signal()
    signal_preview_options_changed = Signal()


    def __init__(self, ui, model:Model_merge_stabilize):
        super(Widget_stitching, self).__init__(ui)
        self.model = model
        self.ui = ui
        self.setObjectName('stitching')

        # Stitching parameters
        self.radioButton_shot_homography.clicked.connect(self.event_select_default_homography)
        self.radioButton_frame_homography.clicked.connect(self.event_select_custom_homography)

        self.pushButton_roi_edition.setFocusPolicy(Qt.NoFocus)
        self.pushButton_roi_edition.toggled[bool].connect(self.event_roi_edition_changed)
        self.lineEdit_roi_rectangle.clear()
        self.lineEdit_roi_rectangle.setFocusPolicy(Qt.NoFocus)
        self.pushButton_roi_discard_modifications.setFocusPolicy(Qt.NoFocus)
        self.pushButton_roi_discard_modifications.toggled[bool].connect(self.event_roi_discard_modifications)


        self.spinBox_sharpen_radius.setFocusPolicy(Qt.NoFocus)
        # self.spinBox_sharpen_radius.installEventFilter(self)
        self.doubleSpinBox_sharpen_amount.installEventFilter(self)
        # self.doubleSpinBox_sharpen_amount.setFocusPolicy(Qt.NoFocus)


        self.radioButton_sift.clicked.connect(self.event_select_sift)
        self.radioButton_surf.clicked.connect(self.event_select_surf)
        self.radioButton_brisk.clicked.connect(self.event_select_brisk)
        self.radioButton_orb.clicked.connect(self.event_select_orb)

        self.radioButton_bf.clicked.connect(self.event_select_best_match)
        self.radioButton_knn.clicked.connect(self.event_select_radioButton_knn)

        self.doubleSpinBox_knn_ratio.installEventFilter(self)
        self.doubleSpinBox_ransac_reproj_threshold.installEventFilter(self)

        self.pushButton_ransac.setCheckable(False)
        self.pushButton_ransac.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.pushButton_ransac.setFocusPolicy(Qt.NoFocus)


        self.pushButton_load_default.clicked.connect(self.event_load_default)
        self.pushButton_undo.clicked.connect(self.event_undo)

        self.pushButton_calculate.clicked.connect(self.event_calculate)
        self.model.signal_stitching_calculated.connect(self.event_calculation_ended)
        # self.model.signal_is_saved[list].connect(self.event_is_saved)


        self.pushButton_crop_edition.setFocusPolicy(Qt.NoFocus)
        self.pushButton_crop_edition.toggled[bool].connect(self.event_crop_edition_changed)
        self.lineEdit_crop_rectangle.clear()
        self.lineEdit_crop_rectangle.setFocusPolicy(Qt.NoFocus)


        self.groupBox_stitching.toggled[bool].connect(self.event_enabled_changed)
        self.groupBox_detection_method.setEnabled(True)
        self.groupBox_match_descriptors.setEnabled(True)
        self.groupBox_find_homography.setEnabled(True)


        # Used to select between roi, stitching only and crop
        self.current_roi = [0, 0, 0, 0]
        self.current_crop = [0, 0, 0, 0]
        self.current_edition_mode = ''
        self.is_save_action_allowed = False

        self.previous_position = None

        set_stylesheet(self)
        self.adjustSize()


    def set_initial_options(self, preferences:dict):
        log.info("set_initial_options")
        s = preferences['stitching']

        # Geometry
        self.move(s['geometry'][0], s['geometry'][1])
        self.adjustSize()



    def backup_loaded_parameters(self, parameters):
        # Used to restore the previous parameters
        # Add to historic in model
        self.saved_loaded_parameters = deepcopy(parameters)

    def update_roi(self, roi):
        self.current_roi = roi
        if roi[2] == 0 and roi[3] == 0:
            self.lineEdit_roi_rectangle.setText('image')
        else:
            self.lineEdit_roi_rectangle.setText("(%s)" % (':'.join(map(lambda x: "%d" % (x), roi))))


    def set_crop(self, crop):
        self.current_crop = crop
        pprint(crop)
        self.lineEdit_crop_rectangle.setText("t:%d, d:%d, l:%d, r:%d" % (crop[0], crop[1], crop[2], crop[3]))


    def set_crop_edition_enabled(self, enabled):
        self.pushButton_crop_edition.blockSignals(True)
        self.pushButton_crop_edition.setEnabled(enabled)
        self.pushButton_crop_edition.blockSignals(False)


    def set_parameters(self, parameters, do_backup=True, do_reset_coordinates=True):
        log.info("set stitching parameters")
        print("stitching parameters")
        self.is_save_action_allowed = False

        # Enable/disable buttons
        self.block_signals(True)

        # Save parameters for undo
        if do_backup:
            self.backup_loaded_parameters(parameters)

        self.groupBox_stitching.setEnabled(parameters['is_enabled'])
        self.radioButton_shot_homography.setChecked(parameters['is_shot'])

        if do_reset_coordinates:
            self.update_roi(parameters['roi'])

        sharpen = parameters['sharpen']
        self.spinBox_sharpen_radius.setValue(sharpen[0])
        self.doubleSpinBox_sharpen_amount.setValue(sharpen[1])

        extractor = parameters['extractor']
        if extractor == 'sift':
            self.radioButton_sift.setEnabled(True)
        elif extractor == 'surf':
            self.radioButton_surf.setEnabled(True)
        elif extractor == 'brisk':
            self.radioButton_brisk.setEnabled(True)
        elif extractor == 'orb':
            self.radioButton_orb.setEnabled(True)

        matching = parameters['matching']
        if matching == 'bf':
            self.radioButton_bf.setChecked(True)
        elif matching == 'knn':
            self.radioButton_bf.setChecked(True)

        self.doubleSpinBox_knn_ratio.setValue(parameters['knn_ratio'])
        self.doubleSpinBox_ransac_reproj_threshold.setValue(parameters['reproj_threshold'])


        # Enable/disable buttons
        self.pushButton_calculate.setEnabled(False)
        self.pushButton_load_default.setEnabled(True)
        self.pushButton_undo.setEnabled(False)
        self.set_crop_edition_enabled(False)

        self.block_signals(False)


    def is_enabled(self):
        # Returns true if stitching is enabled
        return self.groupBox_stitching.isChecked()


    def get_parameters(self):
        parameters = dict()

        parameters['is_enabled'] = self.isEnabled()
        parameters['is_shot'] = self.radioButton_shot_homography.isChecked()

        parameters['roi'] = self.current_roi
        parameters['sharpen'] = [
            self.spinBox_sharpen_radius.value(),
            self.doubleSpinBox_sharpen_amount.value()
        ]

        if self.radioButton_sift.isChecked():
            extractor = 'sift'
        elif self.radioButton_surf.isChecked():
            extractor = 'surf'
        elif self.radioButton_brisk.isChecked():
            extractor = 'brisk'
        elif self.radioButton_orb.isChecked():
            extractor = 'orb'
        parameters['extractor'] = extractor

        if self.radioButton_bf.isChecked():
            matching = 'bf'
        elif self.radioButton_knn.isChecked():
            matching = 'knn'
        parameters['matching'] = matching

        parameters['knn_ratio'] = self.doubleSpinBox_knn_ratio.value()
        parameters['method'] = STITCHING_SHOT_PARAMETERS_DEFAULT['method']
        parameters['reproj_threshold'] = self.doubleSpinBox_ransac_reproj_threshold.value()

        parameters['fgd_crop'] = self.current_crop
        return parameters



    def event_parameters_modified(self):
        # Preview is not allowed
        self.pushButton_set_preview.setEnabled(False)
        self.set_crop_edition_enabled(False)

        # Calculation button is now enabled
        self.pushButton_calculate.setEnabled(True)

        # Load default parameters is now allowed
        self.pushButton_load_default.setEnabled(True)


    def event_roi_discard_modifications(self, state):
        print("todo: reset ROI to initial values")
        self.event_parameters_modified()


    def event_select_default_homography(self):
        self.event_parameters_modified()

    def event_select_custom_homography(self):
        self.event_parameters_modified()

    def event_select_sift(self):
        self.deselect_spinbox()
        self.radioButton_sift.setFocus()
        self.event_parameters_modified()

    def event_select_surf(self):
        self.deselect_spinbox()
        self.radioButton_surf.setFocus()
        self.event_parameters_modified()

    def event_select_brisk(self):
        self.deselect_spinbox()
        self.radioButton_brisk.setFocus()
        self.event_parameters_modified()

    def event_select_orb(self):
        self.deselect_spinbox()
        self.radioButton_orb.setFocus()
        self.event_parameters_modified()
        self.event_parameters_modified()

    def event_select_best_match(self):
        self.doubleSpinBox_knn_ratio.setEnabled(False)
        self.deselect_spinbox()
        self.radioButton_bf.setFocus()
        self.event_parameters_modified()

    def event_select_radioButton_knn(self):
        self.deselect_spinbox()
        self.doubleSpinBox_knn_ratio.setEnabled(True)
        self.doubleSpinBox_knn_ratio.lineEdit().selectAll()
        self.doubleSpinBox_knn_ratio.setFocus()
        self.event_parameters_modified()

    def event_select_doubleSpinBox_ransac_reproj_threshold(self):
        self.deselect_spinbox()
        self.doubleSpinBox_ransac_reproj_threshold.lineEdit().selectAll()
        self.doubleSpinBox_ransac_reproj_threshold.setFocus()
        self.event_parameters_modified()

    def deselect_spinbox(self):
        self.doubleSpinBox_knn_ratio.lineEdit().deselect()
        self.doubleSpinBox_ransac_reproj_threshold.lineEdit().deselect()
        self.event_parameters_modified()


    def block_signals(self, is_enabled):
        for w in [self.groupBox_stitching,
                    self.radioButton_shot_homography,
                    self.radioButton_frame_homography,
                    self.spinBox_sharpen_radius,
                    self.doubleSpinBox_sharpen_amount,
                    self.radioButton_sift,
                    self.radioButton_surf,
                    self.radioButton_brisk,
                    self.radioButton_orb,
                    self.radioButton_bf,
                    self.radioButton_knn,
                    self.doubleSpinBox_knn_ratio,
                    self.doubleSpinBox_ransac_reproj_threshold,
                    self.pushButton_ransac]:
            w.blockSignals(is_enabled)



    def event_undo(self):
        # Replace by historical implementation in model
        parameters = self.saved_loaded_parameters

        # Restore previous parameters except roi and crop
        self.block_signals(True)
        self.set_parameters(parameters==self.saved_loaded_parameters, do_backup=False, do_reset_coordinates=False)
        self.block_signals(False)

        self.event_is_modified()
        # patch the buttons state/enabled
        self.pushButton_load_default.setEnabled(True)
        self.pushButton_undo.setEnabled(False)
        self.set_crop_edition_enabled(False)



    def event_discard_modifications(self):
        log.info("discard modifications")
        parameters = self.model.reset_and_get_initial_shot_stitching_parameters()
        self.set_parameters(parameters, do_backup=False)
        self.pushButton_undo.setEnabled(True)
        self.pushButton_calculate.setEnabled(True)
        self.pushButton_crop_edition.setEnabled(False)

        self.pushButton_save.setEnabled(False)
        self.pushButton_discard.setEnabled(False)
        self.signal_discard.emit()



    def event_is_modified(self, parameter='', value=0):
        log.info("parameter has been modified: %s, %d" % (parameter, value))
        self.is_save_action_allowed = False
        self.pushButton_calculate.setEnabled(True)
        self.pushButton_set_preview.setEnabled(False)
        # if self.pushButton_calculate.isEnabled():

        self.set_crop_edition_enabled(False)
        self.pushButton_undo.setEnabled(True)
        self.pushButton_discard.setEnabled(True)



    def event_enabled_changed(self, is_enabled):
        log.info("stitching changed to:", is_enabled)
        if is_enabled:
            # Changed to "do stitching"
            self.pushButton_calculate.setEnabled(True)
            self.pushButton_set_preview.setEnabled(False)
            self.set_crop_edition_enabled(False)
        else:
            # Changed to "no stitching"
            self.pushButton_calculate.setEnabled(False)
            self.pushButton_save.setEnabled(True)

            for w in [self.pushButton_set_preview,
                        self.pushButton_roi_edition,
                        self.pushButton_crop_edition]:
                w.blockSignals(True)
                w.setChecked(False)
                w.blockSignals(False)

            self.pushButton_set_preview.setEnabled(False)
            self.set_crop_edition_enabled(False)

        self.pushButton_discard.setEnabled(True)
        self.signal_enabled_modified.emit(is_enabled)
        self.signal_preview_options_changed.emit()


    def get_preview_options(self):
        preview_options = {
            'is_enabled': self.pushButton_set_preview.isChecked(),
            'roi_edition': self.pushButton_roi_edition.isChecked(),
            'crop_edition': self.pushButton_crop_edition.isChecked(),
            # Blend or replace
            'blend_images': True,
        }
        return preview_options


    def event_global_preview_changed(self, state:bool=False):
        if self.pushButton_calculate.isEnabled():
            return
        print("global")
        if state:
            if self.pushButton_roi_edition.isChecked():
                self.pushButton_roi_edition.blockSignals(True)
                self.pushButton_roi_edition.setChecked(False)
                self.pushButton_roi_edition.blockSignals(False)

                self.pushButton_set_preview.blockSignals(True)
                self.pushButton_set_preview.setEnabled(True)
                self.pushButton_set_preview.blockSignals(False)

            self.pushButton_crop_edition.blockSignals(True)
            self.pushButton_crop_edition.setEnabled(True)
            self.pushButton_crop_edition.blockSignals(False)
        else:
            # Preview is disabled, we cannot edit crop
            self.pushButton_crop_edition.blockSignals(True)
            self.pushButton_crop_edition.setEnabled(False)
            self.pushButton_crop_edition.blockSignals(False)

        self.event_preview_changed()


    def event_crop_preview_changed(self, state:bool=False):
        if self.pushButton_roi_edition.isChecked():
            # Disable ROI used for stitching
            self.pushButton_roi_edition.blockSignals(True)
            self.pushButton_roi_edition.setChecked(False)
            self.pushButton_roi_edition.blockSignals(False)
        self.event_preview_changed()


    def event_roi_edition_changed(self, state):
        self.pushButton_crop_edition.blockSignals(True)
        if state:
            self.pushButton_crop_edition.setChecked(False)
            if self.pushButton_set_preview.isChecked():
                self.pushButton_set_preview.blockSignals(True)
                self.pushButton_set_preview.setChecked(False)
                self.pushButton_set_preview.blockSignals(False)

        self.pushButton_crop_edition.blockSignals(False)
        self.event_preview_changed()


    def event_crop_edition_changed(self, state):
        if (not self.pushButton_calculate.isChecked()
            and self.pushButton_set_preview.isChecked()):
            # Calculations have been done and preview is checked,
            #  -> crop edition is allowed
            self.pushButton_roi_edition.blockSignals(True)
            if state:
                self.pushButton_roi_edition.setChecked(False)
            self.pushButton_roi_edition.blockSignals(False)
            self.event_preview_changed()



    def event_load_default(self):
        self.block_signals(True)
        self.radioButton_shot_homography.setChecked(True)
        # self.radioButton_frame_homography

        default_parameters = deepcopy(STITCHING_SHOT_PARAMETERS_DEFAULT)
        default_parameters['is_enabled'] = True

        self.set_parameters(parameters=default_parameters, do_backup=False, do_reset_coordinates=False)
        self.pushButton_calculate.setEnabled(True)
        self.set_crop_edition_enabled(False)
        self.pushButton_load_default.setEnabled(False)
        self.pushButton_undo.setEnabled(False)



    def event_calculate(self):
        log.info("event_calculate")
        parameters = self.get_parameters()
        # self.backup_loaded_parameters(parameters)
        self.pushButton_calculate.setEnabled(False)
        self.pushButton_save.setEnabled(False)
        self.setEnabled(False)
        self.signal_calculation_requested.emit(parameters)


    def event_calculation_ended(self):
        log.info("event_calculation_ended")
        self.setEnabled(True)
        self.pushButton_set_preview.setEnabled(True)
        self.pushButton_crop_edition.setEnabled(True)
        self.pushButton_save.setEnabled(True)
        self.is_save_action_allowed = True


    def event_key_pressed(self, event):
        key = event.key()
        modifiers = event.modifiers()
        # print("%s.keyPressEvent: %d" % (__name__, event.key))

        if modifiers & Qt.ControlModifier:
            if key == Qt.Key_S:
                self.event_save_modifications()
                return True

        elif key == Qt.Key_F5:
            self.signal_calculation_requested.emit(self.get_parameters())
            return True


        # Homography
        elif key == Qt.Key_D:
            self.radioButton_shot_homography.click()
            return True
        elif key == Qt.Key_E:
            self.checkBox_edit_default_homography.click()
            return True
        elif key == Qt.Key_C:
            self.radioButton_frame_homography.click()
            return True

        # (1) Extract keypoints: detection method
        elif key == Qt.Key_S:
            self.radioButton_sift.click()
            return True
        elif key == Qt.Key_U:
            self.radioButton_surf.click()
            return True
        elif key == Qt.Key_B:
            self.radioButton_brisk.click()
            return True
        elif key == Qt.Key_O:
            self.radioButton_orb.click()
            return True
        # (2) Match descriptors
        elif key == Qt.Key_M:
            if self.radioButton_bf.isChecked():
                self.radioButton_knn.click()
            else:
                self.radioButton_bf.click()
            return True
        # (3) Find Homography (RANSAC)
        elif key == Qt.Key_R:
            self.event_select_doubleSpinBox_ransac_reproj_threshold()
            return True
        return False



    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        # Filter press/release events
        focus_object = QApplication.focusObject()
        if focus_object in [self.doubleSpinBox_knn_ratio,
                            self.doubleSpinBox_ransac_reproj_threshold]:
            if event.type() == QEvent.KeyPress:
                key = event.key()
                if key in [Qt.Key_D, Qt.Key_E, Qt.Key_C,
                            Qt.Key_S, Qt.Key_U, Qt.Key_B, Qt.Key_O,
                            Qt.Key_M, Qt.Key_R]:
                    # print("self.doubleSpinBox:", focus_object)
                    self.keyPressEvent(event)
                    event.accept()
                    return True
                else:
                    print("eventFilter")
                    focus_object.eventFilter(watched, event)
                    return False

        return super().eventFilter(watched, event)

