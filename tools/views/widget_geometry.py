# -*- coding: utf-8 -*-
import sys


from utils.pretty_print import *


from functools import partial
from logger import log
from pprint import pprint

from PySide6.QtCore import (
    Qt,
    Signal
)
from PySide6.QtWidgets import (
    QPushButton,
    QLineEdit,
    QRadioButton,
    QCheckBox,
    QApplication,

)
from PySide6.QtGui import (
    QKeyEvent,
    QWheelEvent,
)

from utils.common import K_GENERIQUES

from views.widget_common import Widget_common
from utils.stylesheet import set_stylesheet, set_widget_stylesheet, update_selected_widget_stylesheet

from controllers.controller import Controller_video_editor
from views.ui.widget_geometry_ui import Ui_widget_geometry


class Widget_geometry(Widget_common, Ui_widget_geometry):
    signal_geometry_modified = Signal(dict)
    signal_position_changed = Signal(str)
    signal_save_target_requested = Signal()
    signal_discard_target_requested = Signal()

    def __init__(self, ui, controller:Controller_video_editor):
        super(Widget_geometry, self).__init__(ui)
        self.controller = controller
        self.ui = ui
        self.setObjectName('geometry')

        # Internal variables
        self.current_key_pressed = None
        self.saved_preview_options = None
        self.saved_states = dict()
        self.current_edition_and_preview_enabled = True
        self.is_target_disabled = False
        self.is_edition_allowed = False


        # Target
        self.pushButton_target_width_edition.toggled[bool].connect(partial(self.event_shot_preview_changed, 'target_preview'))
        # self.pushButton_target_width_copy_from_shot.clicked.connect(partial(self.event_target, 'copy_from_shot'))
        self.pushButton_target_discard.clicked.connect(partial(self.event_target, 'discard'))
        self.pushButton_target_save.clicked.connect(partial(self.event_target, 'save'))

        # Shot
        self.pushButton_shot_crop_edition.toggled[bool].connect(partial(self.event_shot_preview_changed, 'crop_edition'))
        self.pushButton_shot_crop_preview.toggled[bool].connect(partial(self.event_shot_preview_changed, 'crop_preview'))
        self.pushButton_shot_resize_preview.toggled[bool].connect(partial(self.event_shot_preview_changed, 'resize_preview'))

        # Shot (default)
        self.groupBox_default_shot_geometry.clicked.connect(partial(self.event_shot_selected, 'default_shot'))
        self.lineEdit_default_shot_crop_rectangle.clear()
        self.checkBox_default_shot_keep_ratio.toggled[bool].connect(partial(self.event_keep_ratio_changed, 'default_shot'))
        self.checkBox_default_shot_fit_to_width.toggled[bool].connect(partial(self.event_fit_to_width_changed, 'default_shot'))

        # Shot (custom)
        self.groupBox_shot_geometry.clicked.connect(partial(self.event_shot_selected, 'shot'))
        self.lineEdit_shot_crop_rectangle.clear()
        self.checkBox_shot_keep_ratio.toggled[bool].connect(partial(self.event_keep_ratio_changed, 'shot'))
        self.checkBox_shot_fit_to_width.toggled[bool].connect(partial(self.event_fit_to_width_changed, 'shot'))

        # Message
        self.label_message.clear()

        # Set stylesheet
        set_stylesheet(self)
        set_widget_stylesheet(self.label_message, 'message')
        self.event_shot_selected(selected='default_shot')
        self.adjustSize()

        # Signals from model
        self.controller.signal_shotlist_modified[dict].connect(self.event_shotlist_modified)

        self.frame.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.installEventFilter(self)


    def set_initial_options(self, preferences:dict):
        log.info("%s: set_initial_options" % (self.objectName()))
        s = preferences[self.objectName()]

        self.lineEdit_default_shot_crop_rectangle.clear()

        self.block_all_signals(True)
        try:
            w = preferences[self.objectName()]['widget']

            self.pushButton_set_preview.blockSignals(True)
            self.pushButton_set_preview.setChecked(w['final_preview'])
            self.pushButton_set_preview.blockSignals(False)

            self.pushButton_target_width_edition.setChecked(w['target']['width_edition'])

            self.pushButton_shot_crop_edition.setChecked(w['shot']['crop_edition'])
            self.pushButton_shot_crop_preview.setChecked(w['shot']['crop_preview'])
            # self.pushButton_shot_resize_edition.setChecked(w['shot']['resize_edition'])
            self.pushButton_shot_resize_preview.setChecked(w['shot']['resize_preview'])

        except:
            log.warning("cannot set initial options")
            pass

        self.pushButton_target_discard.setEnabled(False)
        self.pushButton_target_save.setEnabled(False)
        self.is_edition_allowed = True

        self.block_all_signals(False)

        # Force enabled/disable to save the current states for all widgets
        self.set_edition_and_preview_enabled(False)
        self.set_edition_and_preview_enabled(True)

        # Geometry
        self.move(s['geometry'][0], s['geometry'][1])
        self.adjustSize()




    def event_shotlist_modified(self, values:dict):
        # Disable modification of shot geometry if there is only one shot
        # if (values['k_part'] in ['g_asuivre', 'g_reportage']
        #     or len(values['shots']) == 1):
        #     self.groupBox_shot_geometry.setEnabled(False)
        # else:
        # Enable custom only if more than 1 shot and not g_asuivre/g_reportage
        self.groupBox_shot_geometry.setEnabled(True)


    def refresh_values(self, frame:dict):
        # log.info("widget_geometry: refresh_values")
        geometry = frame['geometry']
        # print_lightgreen(geometry)

        if geometry['error']:
            self.label_message.setText("ERROR!")
        else:
            self.label_message.clear()

        # Width before padding
        self.lineEdit_target_width.setText(str(geometry['target']['w']))

        if frame['k_part'] in ['g_asuivre', 'g_reportage']:
        #     self.groupBox_shot_geometry.setEnabled(False)
        #     # self.pushButton_target_width_copy_from_shot.setEnabled(False)
            self.is_target_disabled = True
        else:
            self.is_target_disabled = False
        self.groupBox_shot_geometry.setEnabled(True)
        # self.pushButton_target_width_copy_from_shot.setEnabled(True)


        # Default shot geometry
        try:
            crop_top, crop_bottom, crop_left, crop_right = geometry['default']['crop']
            crop_str = "t: %d, b: %d,  l: %d, r: %d" % (crop_top, crop_bottom, crop_left, crop_right)
            self.lineEdit_default_shot_crop_rectangle.setText(crop_str)
        except:
            self.lineEdit_default_shot_crop_rectangle.clear()

        self.checkBox_default_shot_keep_ratio.blockSignals(True)
        try:
            keep_ratio = geometry['default']['keep_ratio']
            self.checkBox_default_shot_keep_ratio.setChecked(keep_ratio)
        except:
            self.checkBox_default_shot_keep_ratio.setChecked(False)
        self.checkBox_default_shot_keep_ratio.blockSignals(False)

        self.checkBox_default_shot_fit_to_width.blockSignals(True)
        try:
            fit_to_width = geometry['default']['fit_to_width']
            self.checkBox_default_shot_fit_to_width.setChecked(fit_to_width)
        except:
            self.checkBox_default_shot_fit_to_width.setChecked(False)
        self.checkBox_default_shot_fit_to_width.blockSignals(False)


        # Shot geometry
        try:
            crop_top, crop_bottom, crop_left, crop_right = geometry['shot']['crop']
            crop_str = "t: %d, b: %d,  l: %d, r: %d" % (crop_top, crop_bottom, crop_left, crop_right)
            self.lineEdit_shot_crop_rectangle.setText(crop_str)
        except:
            self.lineEdit_shot_crop_rectangle.clear()

        self.checkBox_shot_keep_ratio.blockSignals(True)
        try:
            keep_ratio = geometry['shot']['keep_ratio']
            self.checkBox_shot_keep_ratio.setChecked(keep_ratio)
        except:
            self.checkBox_shot_keep_ratio.setChecked(False)
        self.checkBox_shot_keep_ratio.blockSignals(False)

        self.checkBox_shot_fit_to_width.blockSignals(True)
        try:
            fit_to_width = geometry['shot']['fit_to_width']
            self.checkBox_shot_fit_to_width.setChecked(fit_to_width)
        except:
            self.checkBox_shot_fit_to_width.setChecked(False)
        self.checkBox_shot_fit_to_width.blockSignals(False)


        # Select shot/default
        self.groupBox_default_shot_geometry.blockSignals(True)
        self.groupBox_shot_geometry.blockSignals(True)

        if geometry['shot'] is None:
            # Use default geometry
            self.groupBox_default_shot_geometry.setChecked(True)
            self.groupBox_shot_geometry.setChecked(False)
        else:
            # Use custom geometry
            self.groupBox_default_shot_geometry.setChecked(False)
            self.groupBox_shot_geometry.setChecked(True)

        self.groupBox_default_shot_geometry.blockSignals(False)
        self.groupBox_shot_geometry.blockSignals(False)


    def refresh_preview_options(self, new_preview_settings):
        try:
            self.is_edition_allowed = new_preview_settings['geometry']['allowed']
        except:
            self.is_edition_allowed = False

        self.pushButton_set_preview.blockSignals(True)
        if self.is_edition_allowed:
            self.pushButton_set_preview.setEnabled(True)
        else:
            self.pushButton_set_preview.setEnabled(False)
            self.pushButton_set_preview.setChecked(False)
        self.pushButton_set_preview.blockSignals(False)


    def event_is_modified(self, element, event_type, parameter, value):
        # log.info("parameter has been modified: %s: %s, %d" % (type, parameter, value))
        self.pushButton_discard.setEnabled(True)
        self.pushButton_save.setEnabled(True)
        if element == 'default_shot':
            self.pushButton_default_shot_discard.setEnabled(True)
        elif element == 'shot':
            self.pushButton_shot_discard.setEnabled(True)
        elif element == 'target':
            self.pushButton_target_discard.setEnabled(True)
            self.pushButton_target_save.setEnabled(True)

        self.signal_geometry_modified.emit({
            # element in 'default_shot', 'shot', 'target'
            'element': element,
            # type in 'select', 'remove', 'set', 'discard'
            'type': event_type,
            # parameter in 'crop_top', 'crop_right', 'crop_left', 'crop_down', 'width'
            'parameter': parameter,
            'value': value
        })


    def event_target(self, action):
        log.info("action=%s" % (action))
        self.pushButton_target_discard.setEnabled(False)
        self.pushButton_target_save.setEnabled(False)
        if action == 'save':
            self.signal_save_target_requested.emit()
        elif action == 'discard':
            self.signal_discard_target_requested.emit()


    def event_target_width_changed(self, value):
        print_lightgreen("width=%d" % (value))



    def set_edition_and_preview_enabled(self, enabled):
        # TODO reactivate once completely verified
        return
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
            log.info("disable edition and preview")
            self.saved_states['push_buttons'] = dict()
            for w in self.findChildren(QPushButton, options=Qt.FindChildrenRecursively):
                w.blockSignals(True)
                self.saved_states['push_buttons'][w.objectName()] = {
                    'enabled': w.isEnabled(),
                    'is_checked': w.isChecked(),
                }
                w.setEnabled(False)
                w.setChecked(False)

            self.saved_states['line_edit'] = dict()
            for w in self.findChildren(QLineEdit, options=Qt.FindChildrenRecursively):
                w.blockSignals(True)
                self.saved_states['line_edit'][w.objectName()] = {
                    'enabled': w.isEnabled(),
                    'is_read_only': w.isReadOnly(),
                }
                w.setEnabled(False)
                w.setReadOnly(False)

            self.saved_states['radio_buttons'] = dict()
            for w in self.findChildren(QRadioButton, options=Qt.FindChildrenRecursively):
                w.blockSignals(True)
                self.saved_states['radio_buttons'][w.objectName()] = {
                    'enabled': w.isEnabled(),
                }
                w.setEnabled(False)

            self.saved_states['check_box'] = dict()
            for w in self.findChildren(QCheckBox, options=Qt.FindChildrenRecursively):
                w.blockSignals(True)
                self.saved_states['check_box'][w.objectName()] = {
                    'enabled': w.isEnabled(),
                }
                w.setEnabled(False)

        else:
            log.info("enable edition and preview")

            current_preview_state = self.pushButton_set_preview.isChecked()
            try:
                for w in self.findChildren(QPushButton, options=Qt.FindChildrenRecursively):
                    w.setEnabled(self.saved_states['push_buttons'][w.objectName()]['enabled'])
                    w.setChecked(self.saved_states['push_buttons'][w.objectName()]['is_checked'])
                    w.blockSignals(False)

                for w in self.findChildren(QLineEdit, options=Qt.FindChildrenRecursively):
                    w.setEnabled(self.saved_states['line_edit'][w.objectName()]['enabled'])
                    w.setReadOnly(self.saved_states['line_edit'][w.objectName()]['is_read_only'])
                    w.blockSignals(False)

                for w in self.findChildren(QRadioButton, options=Qt.FindChildrenRecursively):
                    w.setEnabled(self.saved_states['radio_buttons'][w.objectName()]['enabled'])
                    w.blockSignals(False)

                for w in self.findChildren(QCheckBox, options=Qt.FindChildrenRecursively):
                    w.setEnabled(self.saved_states['check_box'][w.objectName()]['enabled'])
                    w.blockSignals(False)
            except:
                print("warning: state was not saved")

            self.pushButton_set_preview.blockSignals(True)
            self.pushButton_set_preview.setChecked(current_preview_state)
            self.pushButton_set_preview.blockSignals(False)



    def set_geometry_edition_enabled(self, enabled):
        log.info("enable edition: %s" % ('true' if enabled else 'false'))
        # print("TODO: %s: enable edition: %s" % (self.objectName(), 'true' if enabled else 'false'))



    def get_preview_options(self):
        log.info(f"{self.objectName()}: get_preview_options")
        preview_options = {
            'allowed': self.is_edition_allowed,
            'final_preview': self.pushButton_set_preview.isChecked(),
            'target': {
                'width_edition': self.pushButton_target_width_edition.isChecked(),
            },
            'shot': {
                'is_default': self.groupBox_default_shot_geometry.isChecked(),
                'crop_edition': self.pushButton_shot_crop_edition.isChecked(),
                'crop_preview': self.pushButton_shot_crop_preview.isChecked(),
                'resize_preview': self.pushButton_shot_resize_preview.isChecked(),
            },
        }
        return preview_options




    def block_all_signals(self, enabled:bool):

        # Target
        self.pushButton_target_width_edition.blockSignals(enabled)
        # self.pushButton_target_width_copy_from_shot.blockSignals(enabled)
        self.pushButton_target_discard.blockSignals(enabled)
        self.pushButton_target_save.blockSignals(enabled)

        # Shot
        self.pushButton_shot_crop_edition.blockSignals(enabled)
        self.pushButton_shot_crop_preview.blockSignals(enabled)
        # self.pushButton_shot_resize_edition.blockSignals(enabled)
        self.pushButton_shot_resize_preview.blockSignals(enabled)

        # Shot: default
        self.lineEdit_default_shot_crop_rectangle.blockSignals(enabled)
        self.checkBox_default_shot_keep_ratio.blockSignals(enabled)
        self.checkBox_default_shot_fit_to_width.blockSignals(enabled)
        self.pushButton_default_shot_discard.blockSignals(enabled)

        # Shot: custom
        self.lineEdit_shot_crop_rectangle.blockSignals(enabled)
        self.checkBox_shot_keep_ratio.blockSignals(enabled)
        self.checkBox_shot_fit_to_width.blockSignals(enabled)
        self.pushButton_shot_discard.blockSignals(enabled)



    # def event_preview_changed(self, is_checked:bool=False):
    #     log.info("widget preview changed to %s" % ('true' if is_checked else 'false'))
    #     self.block_all_signals(True)
    #     if is_checked:
    #         # save current preview options
    #         self.saved_preview_options = {
    #             'part_crop_preview': self.pushButton_default_shot_crop_preview.isChecked(),
    #             'part_resize_preview': self.pushButton_default_shot_resize_preview.isChecked(),
    #             'shot_crop_preview': self.pushButton_shot_crop_preview.isChecked(),
    #             'shot_resize_preview': self.pushButton_shot_resize_preview.isChecked(),
    #         }
    #         self.pushButton_default_shot_crop_preview.setChecked(is_checked)
    #         self.pushButton_default_shot_resize_preview.setChecked(is_checked)
    #         self.pushButton_shot_crop_preview.setChecked(is_checked)
    #         self.pushButton_shot_resize_preview.setChecked(is_checked)
    #     else:
    #         if self.saved_preview_options is not None:
    #             self.pushButton_default_shot_crop_preview.setChecked(self.saved_preview_options['part_crop_preview'])
    #             self.pushButton_default_shot_resize_preview.setChecked(self.saved_preview_options['part_resize_preview'])
    #             self.pushButton_shot_crop_preview.setChecked(self.saved_preview_options['shot_crop_preview'])
    #             self.pushButton_shot_resize_preview.setChecked(self.saved_preview_options['shot_resize_preview'])
    #     self.block_all_signals(False)
    #     self.signal_preview_options_changed.emit()



    def event_shot_selected(self, selected):
        # Changed default <-> shot
        self.groupBox_default_shot_geometry.blockSignals(True)
        self.groupBox_shot_geometry.blockSignals(True)

        # Change states: simulate radio buttons
        if selected == 'default_shot':
            state = self.groupBox_shot_geometry.isChecked()
            self.groupBox_default_shot_geometry.setChecked(True)
            self.groupBox_shot_geometry.setChecked(False)
            if not state:
                # No changes
                self.groupBox_default_shot_geometry.blockSignals(False)
                self.groupBox_shot_geometry.blockSignals(False)
                return

        elif selected == 'shot':
            state = self.groupBox_default_shot_geometry.isChecked()
            self.groupBox_shot_geometry.setChecked(True)
            self.groupBox_default_shot_geometry.setChecked(False)
            if not state:
                # No changes
                self.groupBox_default_shot_geometry.blockSignals(False)
                self.groupBox_shot_geometry.blockSignals(False)
                return

        # Actions
        self.event_is_modified(element='shot', event_type='select', parameter='shot', value=selected)

        self.groupBox_default_shot_geometry.blockSignals(False)
        self.groupBox_shot_geometry.blockSignals(False)


    def event_shot_preview_changed(self, selected, value):
        # A button has been clicked
        # log.info("button [%s] clicked" % (selected))
        # print_yellow("button [%s] clicked" % (selected))
        # if selected == 'target_preview':
        # elif selected == 'target_show_edition':
        # elif selected == 'crop_edition':
        # elif selected == 'crop_preview':
        # elif selected == 'resize_preview':

        # Disable final preview
        self.pushButton_set_preview.blockSignals(True)
        self.pushButton_set_preview.setChecked(False)
        self.saved_preview_options = None
        self.pushButton_set_preview.blockSignals(False)
        self.signal_preview_options_changed.emit()



    def event_keep_ratio_changed(self, element, is_checked:bool):
        if element == 'default_shot':
            w = self.checkBox_default_shot_fit_to_width
            w_self = self.checkBox_default_shot_keep_ratio
        else:
            w = self.checkBox_shot_fit_to_width
            w_self = self.checkBox_shot_keep_ratio

        if not is_checked and not w.isChecked():
            w_self.blockSignals(True)
            w_self.setChecked(True)
            w_self.blockSignals(False)
            return

        log.info("%s: keep ratio: %s" % (type, 'true' if is_checked else 'false'))
        self.event_is_modified(element=element, event_type='set', parameter='keep_ratio', value=is_checked)



    def event_fit_to_width_changed(self, element, is_checked:bool):
        if element == 'default_shot':
            w_self = self.checkBox_default_shot_fit_to_width
            w = self.checkBox_default_shot_keep_ratio
        else:
            w_self = self.checkBox_shot_fit_to_width
            w = self.checkBox_shot_keep_ratio

        if not is_checked and not w.isChecked():
            w_self.blockSignals(True)
            w_self.setChecked(True)
            w_self.blockSignals(False)
            return

        log.info("%s: fit to width: %s" % (type, 'true' if is_checked else 'false'))
        self.event_is_modified(element=element, event_type='set', parameter='fit_to_width', value=is_checked)



    def event_wheel(self, event: QWheelEvent) -> bool:
        if self.current_key_pressed is not None:
            modifiers = QApplication.keyboardModifiers()
            # print_lightgrey(f"wheelEvent: key: {self.current_key_pressed}")
            # print_lightgrey(f"{modifiers}")


            is_default_shot_selected = self.groupBox_default_shot_geometry.isChecked()

            if self.current_key_pressed == Qt.Key_Z:
                element = 'default_shot' if is_default_shot_selected else 'shot'
                parameter = 'crop_top'
            elif self.current_key_pressed == Qt.Key_S:
                element = 'default_shot' if is_default_shot_selected else 'shot'
                parameter = 'crop_bottom'
            elif self.current_key_pressed == Qt.Key_Q:
                element = 'default_shot' if is_default_shot_selected else 'shot'
                parameter = 'crop_left'
            elif self.current_key_pressed == Qt.Key_D:
                element = 'default_shot' if is_default_shot_selected else 'shot'
                parameter = 'crop_right'
            elif (self.current_key_pressed == Qt.Key_W
                and not self.is_target_disabled):
                element = 'target'
                parameter = 'width'
            else:
                return False

            value = -1 if event.angleDelta().y() > 0 else +1

            # self.current_key_pressed = None
            if self.is_edition_allowed:
                self.event_is_modified(
                    element=element,
                    event_type='set',
                    parameter=parameter,
                    value=value)
                return True

        return False


    def event_key_pressed(self, event:QKeyEvent) -> bool:
        key = event.key()
        modifiers = event.modifiers()
        print_green(f"widget_geometry: event_key_pressed: {key}")

        if key == Qt.Key.Key_Space:
            print("main window: keyPressEvent")
            log.info("Space key event detected")
            return False

        if modifiers & Qt.ControlModifier:
            if key == Qt.Key_S:
                print_purple("Save geometry")
                self.event_save_modifications()
                return True

        # if modifiers & Qt.AltModifier:
        #     if key == Qt.Key_S:
        #         if self.current_key_pressed != Qt.Key_S:
        #             self.signal_position_changed.emit('switch')
        #         self.current_key_pressed = Qt.Key_S
        #         return True
        #     else:
        #         return False

        if key == Qt.Key_F2:
            if self.pushButton_set_preview.isEnabled():
                self.pushButton_set_preview.toggle()
                return True

        # Edit crop dimensions
        elif key in [Qt.Key_Q, Qt.Key_D, Qt.Key_W]:
            self.current_key_pressed = key
            return True

        elif key == Qt.Key_Z:
            if key != self.current_key_pressed:
                self.signal_position_changed.emit('top')
            self.current_key_pressed = key
            return True

        elif key == Qt.Key_S:
            if key != self.current_key_pressed:
                self.signal_position_changed.emit('bottom')
            self.current_key_pressed = key
            return True

        return False



    def event_key_released(self, event:QKeyEvent) -> bool:
        self.current_key_pressed = None
        return False

