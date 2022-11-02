#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
sys.path.append('../scripts')

from copy import deepcopy
from functools import partial

from logger import log
from pprint import pprint

from PySide6.QtCore import (
    Qt,
    Signal,
    QEvent,
)
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QWidget

from common.sylesheet import set_stylesheet


from merge_stabilize.model_merge_stabilize import Model_merge_stabilize
from merge_stabilize.ui.widget_stabilize_ui import Ui_widget_stabilize
from parsers.parser_stabilize import STABILIZATION_SHOT_PARAMETERS_DEFAULT


class Widget_stabilize(QWidget, Ui_widget_stabilize):
    signal_calculation_requested = Signal(dict)
    signal_enabled_modified = Signal(bool)
    signal_previous_parameters = Signal(str)
    signal_save = Signal()
    signal_preview_options_changed = Signal()


    def __init__(self, ui, model:Model_merge_stabilize):
        super(Widget_stabilize, self).__init__()

        self.setupUi(self)
        self.model = model
        self.ui = ui

        # Setup and patch ui
        self.setAutoFillBackground(True)
        self.setWindowFlags(Qt.Tool)
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setWindowModality(Qt.NonModal)

        # Header
        self.pushButton_set_preview.setFocusPolicy(Qt.NoFocus)
        self.pushButton_set_preview.toggled[bool].connect(self.event_preview_changed)
        self.pushButton_save_modifications.setFocusPolicy(Qt.NoFocus)
        self.pushButton_save_modifications.clicked.connect(self.event_save_modifications)
        self.pushButton_discard_modifications.setFocusPolicy(Qt.NoFocus)
        self.pushButton_discard_modifications.clicked.connect(self.event_discard_modifications)
        self.pushButton_close.setFocusPolicy(Qt.NoFocus)
        self.pushButton_close.clicked.connect(self.event_close)


        self.pushButton_set_start.setFocusPolicy(Qt.NoFocus)
        self.pushButton_set_start.clicked.connect(self.event_set_start)
        self.pushButton_set_end.setFocusPolicy(Qt.NoFocus)
        self.pushButton_set_end.clicked.connect(self.event_set_end)
        self.pushButton_set_ref.setFocusPolicy(Qt.NoFocus)
        self.pushButton_set_ref.clicked.connect(self.event_set_ref)
        self.pushButton_load_default.setFocusPolicy(Qt.NoFocus)
        self.pushButton_undo.setFocusPolicy(Qt.NoFocus)

        self.set_enabled(False)

        self.groupBox_stabilize.toggled[bool].connect(self.event_enabled_changed)
        self.pushButton_load_default.clicked.connect(self.event_load_default)
        self.pushButton_undo.clicked.connect(self.event_undo)

        self.pushButton_calculate.clicked.connect(self.event_calculate)

        self.spinBox_frame_start.valueChanged.connect(partial(self.event_is_modified, 'frame_start'))
        self.spinBox_frame_end.valueChanged.connect(partial(self.event_is_modified, 'frame_end'))
        self.spinBox_frame_ref.valueChanged.connect(partial(self.event_is_modified, 'frame_ref'))
        self.spinBox_block_size.valueChanged.connect(partial(self.event_is_modified, 'block_size'))
        self.spinBox_max_corners.valueChanged.connect(partial(self.event_is_modified, 'max_corners'))
        self.spinBox_min_distance.valueChanged.connect(partial(self.event_is_modified, 'min_distance'))
        self.spinBox_quality_level.valueChanged.connect(partial(self.event_is_modified, 'quality_level'))

        self.previous_position = None
        self.is_save_action_allowed = False

        self.model.signal_stabilize_calculated.connect(self.event_calculation_ended)
        self.model.signal_is_saved[list].connect(self.event_is_saved)


        self.pushButton_close.setEnabled(False)
        self.pushButton_save_modifications.setEnabled(False)
        self.pushButton_discard_modifications.setEnabled(False)

        set_stylesheet(self)
        self.adjustSize()


    def set_enabled(self, enabled:bool):
        self.groupBox_stabilize.setChecked(enabled)
        if enabled:
            self.pushButton_calculate.setEnabled(True)
        else:
            self.pushButton_calculate.setEnabled(False)
            self.pushButton_save_modifications.setEnabled(True)




    def set_palette(self, palette):
        self.setPalette(palette)

    def get_preferences(self):
        preferences = {
            'stabilize': {
                'geometry': self.geometry().getRect(),
            },
        }
        return preferences

    def set_initial_options(self, preferences:dict):
        log.info("set_initial_options")
        s = preferences['stabilize']

        # Geometry
        self.move(s['geometry'][0], s['geometry'][1])
        self.adjustSize()


    def set_limits(self, frame_min, frame_max):
        for s in [self.spinBox_frame_start,
                    self.spinBox_frame_end,
                    self.spinBox_frame_ref]:
            s.blockSignals(True)
            s.setMinimum(frame_min)
            s.setMaximum(frame_max)
            s.blockSignals(False)


    def block_signals(self, is_enabled):
        for w in [self.spinBox_frame_start,
                    self.spinBox_frame_end,
                    self.spinBox_frame_ref,
                    self.spinBox_block_size,
                    self.spinBox_max_corners,
                    self.spinBox_min_distance,
                    self.spinBox_quality_level,
                    self.pushButton_calculate,
                    self.groupBox_stabilize,
                    ]:
            w.blockSignals(is_enabled)


    def set_parameters(self, parameters, do_backup=True):
        log.info("set stabilization parameters")
        self.is_save_action_allowed = False

        if type(parameters) is dict:
            segment = parameters['parameters'][0]
            if 'shot_start' in parameters.keys():
                self.set_limits(parameters['shot_start'], parameters['shot_start'] + parameters['shot_count'] - 1)
        else:
            segment = parameters[0]

        # Save parameters for undo
        if do_backup:
            self.save_loaded_parameters(parameters)

        self.block_signals(True)

        # Segment
        self.spinBox_frame_start.setValue(segment['start'])
        self.spinBox_frame_end.setValue(segment['end'])
        self.spinBox_frame_ref.setValue(segment['ref'])

        # Parameters for cv2.goodFeaturesToTrack
        self.spinBox_block_size.setValue(segment['block_size'])
        self.spinBox_max_corners.setValue(segment['max_corners'])
        self.spinBox_min_distance.setValue(segment['min_distance'])
        self.spinBox_quality_level.setValue(segment['quality_level'])

        # Set enabled state
        self.set_enabled(segment['is_enabled'])
        self.pushButton_calculate.setEnabled(False)

        self.pushButton_load_default.setEnabled(True)
        self.pushButton_undo.setEnabled(False)

        self.block_signals(False)


    def save_loaded_parameters(self, parameters):
        # Used to restore the previous parameters
        # Add to historic in model
        if type(parameters) is dict:
            self.saved_loaded_parameters = deepcopy(parameters['parameters'])
        else:
            self.saved_loaded_parameters = deepcopy(parameters)


    def event_set_start(self):
        current_frame = self.model.get_current_frame()
        self.spinBox_frame_start.setValue(current_frame['frame_no'])

    def event_set_end(self):
        current_frame = self.model.get_current_frame()
        self.spinBox_frame_end.setValue(current_frame['frame_no'])

    def event_set_ref(self):
        current_frame = self.model.get_current_frame()
        self.spinBox_frame_ref.setValue(current_frame['frame_no'])



    def event_undo(self):
        # Replace by historical implementation in model

        segment = self.saved_loaded_parameters[0]
        # Segment
        self.spinBox_frame_start.setValue(segment['start'])
        self.spinBox_frame_end.setValue(segment['end'])
        self.spinBox_frame_ref.setValue(segment['ref'])

        # Parameters for cv2.goodFeaturesToTrack
        self.spinBox_block_size.setValue(segment['block_size'])
        self.spinBox_max_corners.setValue(segment['max_corners'])
        self.spinBox_min_distance.setValue(segment['min_distance'])
        self.spinBox_quality_level.setValue(segment['quality_level'])


    def is_enabled(self):
        # Returns true if stabilization is enabled
        return self.groupBox_stabilize.isChecked()

    def get_parameters(self):
        log.info("get stabilization parameters")
        segment = {
            'is_enabled': self.is_enabled(),
            'start': self.spinBox_frame_start.value(),
            'end': self.spinBox_frame_end.value(),
            'ref': self.spinBox_frame_ref.value(),
            'block_size': self.spinBox_min_distance.value(),
            'max_corners': self.spinBox_max_corners.value(),
            'min_distance': self.spinBox_min_distance.value(),
            'quality_level': self.spinBox_quality_level.value(),
        }
        return [segment]


    def event_is_modified(self, parameter='', value=0):
        log.info("parameter has been modified: %s, %d" % (parameter, value))
        self.is_save_action_allowed = False
        if self.spinBox_frame_start.value() >= self.spinBox_frame_end.value():
            log.info("start > end")
            self.pushButton_calculate.setEnabled(False)
            self.pushButton_save_modifications.setEnabled(False)
        else:
            self.pushButton_calculate.setEnabled(True)
            self.pushButton_set_preview.setEnabled(False)
        self.pushButton_undo.setEnabled(True)
        self.pushButton_discard_modifications.setEnabled(True)


    def event_enabled_changed(self, is_enabled):
        log.info("stabilization changed to:", is_enabled)
        if is_enabled:
            self.pushButton_calculate.setEnabled(True)
            self.pushButton_set_preview.setEnabled(False)
        else:
            self.pushButton_calculate.setEnabled(False)
            self.pushButton_save_modifications.setEnabled(True)
        self.pushButton_discard_modifications.setEnabled(True)
        self.signal_enabled_modified.emit(is_enabled)


    def event_load_default(self):
        self.block_signals(True)
        self.spinBox_block_size.setValue(STABILIZATION_SHOT_PARAMETERS_DEFAULT['block_size'])
        self.spinBox_max_corners.setValue(STABILIZATION_SHOT_PARAMETERS_DEFAULT['max_corners'])
        self.spinBox_min_distance.setValue(STABILIZATION_SHOT_PARAMETERS_DEFAULT['min_distance'])
        self.spinBox_quality_level.setValue(STABILIZATION_SHOT_PARAMETERS_DEFAULT['quality_level'])
        self.block_signals(False)
        self.pushButton_calculate.setEnabled(True)
        self.pushButton_set_preview.setEnabled(False)


    def event_calculate(self):
        log.info("event_calculate")
        parameters = self.get_parameters()
        self.save_loaded_parameters(parameters)
        self.pushButton_calculate.setEnabled(False)
        self.pushButton_save_modifications.setEnabled(False)
        self.setEnabled(False)
        self.signal_calculation_requested.emit(parameters)


    def event_calculation_ended(self):
        log.info("event_calculation_ended")
        self.setEnabled(True)
        self.pushButton_set_preview.setEnabled(True)
        self.pushButton_save_modifications.setEnabled(True)
        self.is_save_action_allowed = True


    def get_preview_options(self):
        # 'crop': {
        #     'merged': {
        #         'is_enabled': False,
        #         'edition': False,
        #     },
        #     'aspect_ratio': True,
        #     'final': {
        #         'is_enabled': False,
        #         'edition': False,
        #     },
        # },
        # 'final': {
        #     'is_enabled': False,
        #     'edition': True,
        # }

        preview_options = {
            'is_enabled': self.pushButton_set_preview.isChecked(),
        }
        return preview_options


    def event_preview_changed(self, state:bool=False):
        if self.pushButton_calculate.isEnabled():
            self.groupBox_stabilize.blockSignals(True)
            self.groupBox_stabilize.setEnabled(True)
            self.groupBox_stabilize.blockSignals(False)
        else:
            self.groupBox_stabilize.blockSignals(True)
            self.groupBox_stabilize.setEnabled(True)
            self.groupBox_stabilize.blockSignals(False)
        self.signal_preview_options_changed.emit()



    def event_is_saved(self, k_type):
        if k_type == 'stabilize':
            log.info("parameters and values saved")
            self.is_save_action_allowed = False
            self.pushButton_discard_modifications.setEnabled(False)


    def event_discard_modifications(self):
        log.info("discard modifications")
        parameters = self.model.reset_and_get_initial_shot_stabilize_parameters()
        self.set_parameters(parameters, do_backup=False)
        self.pushButton_undo.setEnabled(True)
        self.pushButton_calculate.setEnabled(True)
        self.pushButton_discard_modifications.setEnabled(False)


    def event_save_modifications(self):
        if self.is_save_action_allowed:
            self.signal_save.emit()

    def event_close(self):
        log.info("close button clicked")
        # self.signal_action.emit('close')


    def wheelEvent(self, event):
        # print("window_main: wheel event, forward to widget_control")
        self.ui.wheelEvent(event)


    def mousePressEvent(self, event):
        self.previous_position = QCursor().pos()


    def mouseMoveEvent(self, event):
        if self.previous_position is not None:
            cursor_position = QCursor().pos()
            delta = cursor_position - self.previous_position
            self.move(self.pos() + delta)
            self.previous_position = cursor_position


    def keyPressEvent(self, event):
        key = event.key()
        modifiers = event.modifiers()
        # print("%s.keyPressEvent: %d" % (__name__, event.key))

        if modifiers & Qt.ControlModifier:
            if key == Qt.Key_S:
                self.event_save_modifications()
                event.accept()
                return True

        if key == Qt.Key_F5:
            self.signal_calculation_requested.emit(self.get_parameters())


        return self.ui.keyPressEvent(event)


    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.ActivationChange:
            if self.isActiveWindow():
                self.ui.set_current_editor('stabilize')
                event.accept()
                return True
        return super().changeEvent(event)

