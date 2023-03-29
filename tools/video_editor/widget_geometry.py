# -*- coding: utf-8 -*-

import sys
sys.path.append('../scripts')


from functools import partial
from logger import log
from pprint import pprint

from PySide6.QtCore import (
    Qt,
    Signal,
)
from PySide6.QtWidgets import (
    QPushButton,
    QLineEdit,
    QRadioButton,
    QCheckBox,
)

from utils.common import K_GENERIQUES, nested_dict_get

from common.widget_common import Widget_common
from common.sylesheet import set_stylesheet, set_widget_stylesheet

from video_editor.model_video_editor import Model_video_editor
from video_editor.ui.widget_geometry_ui import Ui_widget_geometry


class Widget_geometry(Widget_common, Ui_widget_geometry):
    signal_geometry_modified = Signal(dict)
    signal_position_changed = Signal(str)

    def __init__(self, ui, model:Model_video_editor):
        super(Widget_geometry, self).__init__(ui)
        self.model = model
        self.ui = ui
        self.setObjectName('geometry')

        # Internal variables
        self.current_key_pressed = None
        self.saved_preview_options = None
        self.saved_states = dict()
        self.current_edition_and_preview_enabled = True

        self.is_shot_geometry_enabled = False

        # Common
        self.pushButton_remove_shot_geometry.setFocusPolicy(Qt.NoFocus)
        self.radioButton_part.setFocusPolicy(Qt.NoFocus)
        self.radioButton_shot.setFocusPolicy(Qt.NoFocus)
        self.pushButton_remove_shot_geometry.clicked.connect(self.event_remove_shot_geometry)
        self.radioButton_part.clicked.connect(self.event_part_edition_selected)
        self.radioButton_shot.clicked.connect(self.event_shot_edition_selected)

        # Part
        self.lineEdit_part_crop_rectangle.setFocusPolicy(Qt.NoFocus)
        self.pushButton_part_crop_edition.setFocusPolicy(Qt.NoFocus)
        self.pushButton_part_crop_preview.setFocusPolicy(Qt.NoFocus)
        self.pushButton_part_resize_edition.setFocusPolicy(Qt.NoFocus)
        self.pushButton_part_resize_preview.setFocusPolicy(Qt.NoFocus)
        self.checkBox_part_keep_ratio.setFocusPolicy(Qt.NoFocus)

        self.lineEdit_part_crop_rectangle.clear()

        self.pushButton_part_crop_edition.toggled[bool].connect(partial(self.event_crop_edition_changed, 'part'))
        self.pushButton_part_crop_preview.toggled[bool].connect(partial(self.event_crop_preview_changed, 'part'))
        self.pushButton_part_resize_preview.toggled[bool].connect(partial(self.event_resize_preview_changed, 'part'))
        self.pushButton_part_resize_edition.toggled[bool].connect(partial(self.event_resize_edition_changed, 'part'))
        self.checkBox_part_keep_ratio.toggled[bool].connect(partial(self.event_keep_ratio_changed, 'part'))

        # Shot
        self.lineEdit_shot_crop_rectangle.setFocusPolicy(Qt.NoFocus)
        self.pushButton_shot_crop_edition.setFocusPolicy(Qt.NoFocus)
        self.pushButton_shot_crop_preview.setFocusPolicy(Qt.NoFocus)
        self.pushButton_shot_resize_edition.setFocusPolicy(Qt.NoFocus)
        self.pushButton_shot_resize_preview.setFocusPolicy(Qt.NoFocus)
        self.checkBox_shot_keep_ratio.setFocusPolicy(Qt.NoFocus)
        self.checkBox_fit_to_part.setFocusPolicy(Qt.NoFocus)

        self.lineEdit_shot_crop_rectangle.clear()

        self.pushButton_shot_crop_edition.toggled[bool].connect(partial(self.event_crop_edition_changed, 'shot'))
        self.pushButton_shot_crop_preview.toggled[bool].connect(partial(self.event_crop_preview_changed, 'shot'))
        self.pushButton_shot_resize_preview.toggled[bool].connect(partial(self.event_resize_preview_changed, 'shot'))
        self.pushButton_shot_resize_edition.toggled[bool].connect(partial(self.event_resize_edition_changed, 'shot'))
        self.checkBox_shot_keep_ratio.toggled[bool].connect(partial(self.event_keep_ratio_changed, 'shot'))
        self.checkBox_fit_to_part.toggled[bool].connect(partial(self.event_fit_to_part_changed, 'shot'))
        self.checkBox_fit_to_part.setEnabled(False)

        self.label_message.clear()

        set_stylesheet(self)
        set_widget_stylesheet(self.label_message, 'message')
        self.adjustSize()

        # Signals from model
        self.model.signal_shotlist_modified[dict].connect(self.event_shotlist_modified)


    def set_initial_options(self, preferences:dict):
        log.info("%s: set_initial_options" % (self.objectName()))
        s = preferences[self.objectName()]

        self.lineEdit_part_crop_rectangle.clear()

        try:
            w = preferences[self.objectName()]['widget']

            self.pushButton_set_preview.blockSignals(True)
            self.pushButton_set_preview.setChecked(w['final_preview'])
            self.pushButton_set_preview.blockSignals(False)

            self.block_signals(True)
            self.pushButton_part_crop_edition.setChecked(w['part']['crop_edition'])
            self.pushButton_part_crop_preview.setChecked(w['part']['crop_preview'])
            self.pushButton_part_resize_edition.setChecked(w['part']['resize_edition'])
            self.pushButton_part_resize_preview.setChecked(w['part']['resize_preview'])

            self.pushButton_shot_crop_edition.setChecked(w['shot']['crop_edition'])
            self.pushButton_shot_crop_preview.setChecked(w['shot']['crop_preview'])
            self.pushButton_shot_resize_edition.setChecked(w['shot']['resize_edition'])
            self.pushButton_shot_resize_preview.setChecked(w['shot']['resize_preview'])
            self.block_signals(False)

        except:
            log.warning("cannot set initial options")
            pass

        # Force enabled/disable to save the current states for all widgets
        self.set_edition_and_preview_enabled(False)
        self.set_edition_and_preview_enabled(True)

        # Geometry
        self.move(s['geometry'][0], s['geometry'][1])
        self.adjustSize()


    def event_shotlist_modified(self, values:dict):
        # Disable modification of shot geometry if there is only one shot
        if values['k_part'] in ['g_asuivre', 'g_reportage']:
            self.radioButton_shot.setEnabled(True)
            self.pushButton_remove_shot_geometry.setEnabled(False)
        else:
            if len(values['shots']) > 1:
                self.radioButton_shot.setEnabled(True)
            else:
                self.radioButton_shot.setEnabled(False)
            self.checkBox_fit_to_part.setEnabled(False)

        if values['k_part'] in K_GENERIQUES:
            self.checkBox_fit_to_part.setEnabled(True)
        self.radioButton_part.setEnabled(True)


    def refresh_values(self, frame:dict):
        # print("widget_geometry: refresh_values")
        # pprint(frame['geometry'])
        is_preview_mode_changed = False

        if frame['geometry']['error']:
            self.label_message.setText("ERROR!")
        else:
            self.label_message.clear()

        try:
            part_geometry = frame['geometry']['part']
            c_t, c_b, c_l, c_r = part_geometry['crop']
            crop_str = "t: %d, b: %d,  l: %d, r: %d" % (c_t, c_b, c_l, c_r)
            self.lineEdit_part_crop_rectangle.setText(crop_str)
        except:
            self.lineEdit_part_crop_rectangle.clear()

        try:
            shot_geometry = frame['geometry']['shot']
            c_t, c_b, c_l, c_r = shot_geometry['crop']
            crop_str = "t: %d, b: %d,  l: %d, r: %d" % (c_t, c_b, c_l, c_r)
            self.lineEdit_shot_crop_rectangle.setText(crop_str)
        except:
            self.lineEdit_shot_crop_rectangle.clear()

        self.checkBox_shot_keep_ratio.blockSignals(True)
        self.checkBox_fit_to_part.blockSignals(True)
        try:
            do_fit_to_part = frame['geometry']['shot']['resize']['fit_to_part']
            if do_fit_to_part:
                self.checkBox_shot_keep_ratio.setChecked(False)
                self.checkBox_fit_to_part.setChecked(True)
        except:
                self.checkBox_shot_keep_ratio.setChecked(True)
                self.checkBox_fit_to_part.setChecked(False)
        self.checkBox_shot_keep_ratio.blockSignals(False)
        self.checkBox_fit_to_part.blockSignals(False)


        # Geometry: shot or part
        if 'shot' in frame['geometry'].keys() and frame['geometry']['shot'] is not None:
            self.groupBox_shot_geometry.setEnabled(True)

            # Edit shot geometry
            self.radioButton_part.setEnabled(False)
            self.pushButton_remove_shot_geometry.setEnabled(True)

            # Disable widgets used for part
            self.block_signals(True)
            self.radioButton_shot.setChecked(True)
            self.pushButton_part_crop_edition.setEnabled(True)

            self.pushButton_part_crop_preview.setEnabled(False)
            self.pushButton_part_crop_preview.setChecked(False)

            self.pushButton_part_resize_edition.setEnabled(False)
            self.pushButton_part_resize_edition.setChecked(False)

            self.pushButton_part_resize_preview.setEnabled(True)
            # self.pushButton_part_resize_preview.setChecked(True)

            self.checkBox_part_keep_ratio.setEnabled(False)
            self.checkBox_shot_keep_ratio.setEnabled(False)

            if self.pushButton_set_preview.isChecked():
                self.pushButton_shot_crop_preview.setChecked(True)
                self.pushButton_shot_resize_preview.setChecked(True)
                if not self.is_shot_geometry_enabled:
                    # changed from part to shot
                    is_preview_mode_changed = True
            self.is_shot_geometry_enabled = True
            self.block_signals(False)

        else:
            # Edit part geometry
            self.groupBox_shot_geometry.setEnabled(False)

            self.pushButton_remove_shot_geometry.setEnabled(False)

            self.block_signals(True)
            self.radioButton_part.setChecked(False)
            self.pushButton_part_crop_edition.setEnabled(True)
            self.pushButton_part_crop_preview.setEnabled(True)
            # self.pushButton_part_resize_edition.setEnabled(True)
            self.pushButton_part_resize_preview.setEnabled(True)
            self.checkBox_part_keep_ratio.setEnabled(False)
            self.checkBox_shot_keep_ratio.setEnabled(False)

            if self.pushButton_set_preview.isChecked():
                self.pushButton_part_crop_preview.setChecked(True)
                self.pushButton_part_resize_preview.setChecked(True)
                if self.is_shot_geometry_enabled:
                    # changed from shot to part
                    is_preview_mode_changed = True
            self.is_shot_geometry_enabled = False
            self.block_signals(False)

        if frame['k_part'] in ['g_asuivre', 'g_reportage']:
            self.radioButton_shot.setEnabled(False)
            self.radioButton_part.setEnabled(False)
            self.pushButton_remove_shot_geometry.setEnabled(False)

        if is_preview_mode_changed:
            self.signal_preview_options_changed.emit()



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
            log.info("disable edition and preview")
            self.saved_states['push_buttons'] = dict()
            for w in self.findChildren(QPushButton, options=Qt.FindChildrenRecursively):
                w.blockSignals(True)
                self.saved_states['push_buttons'][w.objectName()] = {
                    'is_enabled': w.isEnabled(),
                    'is_checked': w.isChecked(),
                }
                w.setEnabled(False)
                w.setChecked(False)

            self.saved_states['line_edit'] = dict()
            for w in self.findChildren(QLineEdit, options=Qt.FindChildrenRecursively):
                w.blockSignals(True)
                self.saved_states['line_edit'][w.objectName()] = {
                    'is_enabled': w.isEnabled(),
                    'is_read_only': w.isReadOnly(),
                }
                w.setEnabled(False)
                w.setReadOnly(False)

            self.saved_states['radio_buttons'] = dict()
            for w in self.findChildren(QRadioButton, options=Qt.FindChildrenRecursively):
                w.blockSignals(True)
                self.saved_states['radio_buttons'][w.objectName()] = {
                    'is_enabled': w.isEnabled(),
                }
                w.setEnabled(False)

            self.saved_states['check_box'] = dict()
            for w in self.findChildren(QCheckBox, options=Qt.FindChildrenRecursively):
                w.blockSignals(True)
                self.saved_states['check_box'][w.objectName()] = {
                    'is_enabled': w.isEnabled(),
                }
                w.setEnabled(False)

        else:
            log.info("enable edition and preview")

            current_preview_state = self.pushButton_set_preview.isChecked()
            try:
                for w in self.findChildren(QPushButton, options=Qt.FindChildrenRecursively):
                    w.setEnabled(self.saved_states['push_buttons'][w.objectName()]['is_enabled'])
                    w.setChecked(self.saved_states['push_buttons'][w.objectName()]['is_checked'])
                    w.blockSignals(False)

                for w in self.findChildren(QLineEdit, options=Qt.FindChildrenRecursively):
                    w.setEnabled(self.saved_states['line_edit'][w.objectName()]['is_enabled'])
                    w.setReadOnly(self.saved_states['line_edit'][w.objectName()]['is_read_only'])
                    w.blockSignals(False)

                for w in self.findChildren(QRadioButton, options=Qt.FindChildrenRecursively):
                    w.setEnabled(self.saved_states['radio_buttons'][w.objectName()]['is_enabled'])
                    w.blockSignals(False)

                for w in self.findChildren(QCheckBox, options=Qt.FindChildrenRecursively):
                    w.setEnabled(self.saved_states['check_box'][w.objectName()]['is_enabled'])
                    w.blockSignals(False)
            except:
                print("warning: state was not saved")

            self.pushButton_set_preview.blockSignals(True)
            self.pushButton_set_preview.setChecked(current_preview_state)
            self.pushButton_set_preview.blockSignals(False)





    def set_geometry_edition_enabled(self, enabled):
        log.info("enable edition: %s" % ('true' if enabled else 'false'))
        # print("TODO: %s: enable edition: %s" % (self.objectName(), 'true' if enabled else 'false'))


    def event_undo(self):
        # Replace by historical implementation in model
        pass



    def event_is_modified(self, type, parameter, value):
        # log.info("parameter has been modified: %s: %s, %d" % (type, parameter, value))
        self.pushButton_discard.setEnabled(True)
        self.pushButton_save.setEnabled(True)
        self.pushButton_undo.setEnabled(True)

        self.signal_geometry_modified.emit({
            # type in 'part', 'shot'
            'type': type,
            # parameter in 'crop_top', 'crop_right', 'crop_left', 'crop_down'
            # but also: 'remove'
            'parameter': parameter,
            'value': value
        })


    def get_preview_options(self):
        preview_options = {
            'final_preview': self.pushButton_set_preview.isChecked(),
            'part': {
                'is_enabled': not self.is_shot_geometry_enabled,
                'crop_edition': self.pushButton_part_crop_edition.isChecked(),
                'crop_preview': self.pushButton_part_crop_preview.isChecked(),
                'resize_edition': self.pushButton_part_resize_edition.isChecked(),
                'resize_preview': self.pushButton_part_resize_preview.isChecked(),
            },
            'shot': {
                'is_enabled': self.is_shot_geometry_enabled,
                'crop_edition': self.pushButton_shot_crop_edition.isChecked(),
                'crop_preview': self.pushButton_shot_crop_preview.isChecked(),
                'resize_edition': self.pushButton_shot_resize_edition.isChecked(),
                'resize_preview': self.pushButton_shot_resize_preview.isChecked(),
            },

        }
        return preview_options


    def block_signals(self, enabled):
        self.radioButton_part.blockSignals(enabled)
        self.radioButton_shot.blockSignals(enabled)

        self.pushButton_part_crop_preview.blockSignals(enabled)
        self.pushButton_part_resize_preview.blockSignals(enabled)
        self.pushButton_part_crop_edition.blockSignals(enabled)
        self.pushButton_part_resize_edition.blockSignals(enabled)
        self.checkBox_part_keep_ratio.blockSignals(enabled)

        self.pushButton_shot_crop_preview.blockSignals(enabled)
        self.pushButton_shot_resize_preview.blockSignals(enabled)
        self.pushButton_shot_crop_edition.blockSignals(enabled)
        self.pushButton_shot_resize_edition.blockSignals(enabled)
        self.checkBox_shot_keep_ratio.blockSignals(enabled)
        self.checkBox_fit_to_part.blockSignals(enabled)


    def event_preview_changed(self, is_checked:bool=False):
        log.info("widget preview changed to %s" % ('true' if is_checked else 'false'))
        self.block_signals(True)
        if is_checked:
            # save current preview options
            self.saved_preview_options = {
                'part_crop_preview': self.pushButton_part_crop_preview.isChecked(),
                'part_resize_preview': self.pushButton_part_resize_preview.isChecked(),
                'shot_crop_preview': self.pushButton_shot_crop_preview.isChecked(),
                'shot_resize_preview': self.pushButton_shot_resize_preview.isChecked(),
            }
            self.pushButton_part_crop_preview.setChecked(is_checked)
            self.pushButton_part_resize_preview.setChecked(is_checked)
            self.pushButton_shot_crop_preview.setChecked(is_checked)
            self.pushButton_shot_resize_preview.setChecked(is_checked)
        else:
            if self.saved_preview_options is not None:
                self.pushButton_part_crop_preview.setChecked(self.saved_preview_options['part_crop_preview'])
                self.pushButton_part_resize_preview.setChecked(self.saved_preview_options['part_resize_preview'])
                self.pushButton_shot_crop_preview.setChecked(self.saved_preview_options['shot_crop_preview'])
                self.pushButton_shot_resize_preview.setChecked(self.saved_preview_options['shot_resize_preview'])
        self.block_signals(False)
        self.signal_preview_options_changed.emit()


    def event_part_edition_selected(self):
        pass


    def event_shot_edition_selected(self):
        self.pushButton_remove_shot_geometry.setEnabled(True)
        self.event_is_modified(
            type='shot',
            parameter='copy',
            value=None)


    def event_remove_shot_geometry(self):
        # Remove geometry for this shot, so it will use the default one: part
        self.pushButton_remove_shot_geometry.setEnabled(False)
        self.block_signals(True)
        self.radioButton_part.setChecked(True)
        self.block_signals(False)
        self.is_shot_geometry_enabled = False
        self.event_is_modified(type='shot', parameter='remove', value=None)




    def event_crop_edition_changed(self, type, is_checked:bool):
        log.info("%s: crop edition changed to %s" % (type, 'true' if is_checked else 'false'))
        if is_checked:
            # Disable final preview
            self.pushButton_set_preview.blockSignals(True)
            self.pushButton_set_preview.setChecked(False)
            self.saved_preview_options = None
            self.pushButton_set_preview.blockSignals(False)
        elif type == 'part':
            if not self.pushButton_part_crop_preview.isChecked():
                self.pushButton_part_resize_preview.blockSignals(True)
                self.pushButton_part_resize_preview.setChecked(False)
                self.pushButton_part_resize_preview.blockSignals(False)
        elif type == 'shot':
            if not self.pushButton_shot_crop_preview.isChecked():
                self.pushButton_shot_resize_preview.blockSignals(True)
                self.pushButton_shot_resize_preview.setChecked(False)
                self.pushButton_shot_resize_preview.blockSignals(False)
        self.signal_preview_options_changed.emit()


    def event_crop_preview_changed(self, type, is_checked:bool):
        log.info("%s: crop preview changed to %s" % (type, 'true' if is_checked else 'false'))
        if not is_checked:
            # Disable final preview
            self.pushButton_set_preview.blockSignals(True)
            self.pushButton_set_preview.setChecked(False)
            self.saved_preview_options = None
            self.pushButton_set_preview.blockSignals(False)

            if type == 'part':
                if (self.pushButton_part_resize_preview.isChecked()
                and not self.pushButton_part_crop_edition.isChecked()):
                    self.pushButton_part_resize_preview.blockSignals(True)
                    self.pushButton_part_resize_preview.setChecked(False)
                    self.pushButton_part_resize_preview.blockSignals(False)
            elif type == 'shot':
                if (self.pushButton_shot_resize_preview.isChecked()
                and not self.pushButton_shot_crop_edition.isChecked()):
                    self.pushButton_shot_resize_preview.blockSignals(True)
                    self.pushButton_shot_resize_preview.setChecked(False)
                    self.pushButton_shot_resize_preview.blockSignals(False)
        self.signal_preview_options_changed.emit()


    def event_resize_edition_changed(self, type, is_checked:bool):
        log.info("%s: resize edition changed to %s" % (type, 'true' if is_checked else 'false'))
        if is_checked:
            # Force crop preview
            if type == 'part':
                self.pushButton_part_crop_preview.blockSignals(True)
                self.pushButton_part_crop_preview.setChecked(True)
                self.pushButton_part_crop_preview.blockSignals(False)
            elif type == 'shot':
                self.pushButton_shot_crop_preview.blockSignals(True)
                self.pushButton_shot_crop_preview.setChecked(True)
                self.pushButton_shot_crop_preview.blockSignals(False)
        self.signal_preview_options_changed.emit()


    def event_resize_preview_changed(self, type, is_checked:bool):
        log.info("%s: resize preview changed to %s" % (type, 'true' if is_checked else 'false'))
        if not is_checked:
            # Disable final preview
            self.pushButton_set_preview.blockSignals(True)
            self.pushButton_set_preview.setChecked(False)
            self.pushButton_set_preview.blockSignals(False)
        elif type == 'part':
            if (not self.pushButton_part_crop_preview.isChecked()
            and not self.pushButton_part_crop_edition.isChecked()):
                self.pushButton_part_crop_preview.blockSignals(True)
                self.pushButton_part_crop_preview.setChecked(True)
                self.pushButton_part_crop_preview.blockSignals(False)
        elif type == 'shot':
            if (not self.pushButton_shot_crop_preview.isChecked()
            and not self.pushButton_shot_crop_edition.isChecked()):
                self.pushButton_shot_crop_preview.blockSignals(True)
                self.pushButton_shot_crop_preview.setChecked(True)
                self.pushButton_shot_crop_preview.blockSignals(False)
        self.signal_preview_options_changed.emit()


    def event_keep_ratio_changed(self, type, is_checked:bool):
        log.info("%s: set final ratio: %s" % (type, 'true' if is_checked else 'false'))
        self.signal_preview_options_changed.emit()

    def event_fit_to_part_changed(self, type, is_checked:bool):
        log.info("%s: fit to part: %s" % (type, 'true' if is_checked else 'false'))
        self.checkBox_shot_keep_ratio.blockSignals(True)
        self.checkBox_shot_keep_ratio.setChecked(not is_checked)
        self.checkBox_shot_keep_ratio.blockSignals(False)
        self.event_is_modified(
            type='shot' if self.is_shot_geometry_enabled else 'part',
            parameter='fit_to_part',
            value=is_checked)
        return True


    def wheelEvent(self, event):
        if self.current_key_pressed is not None:
            if self.current_key_pressed == Qt.Key_Z:
                parameter = 'crop_top'
            elif self.current_key_pressed == Qt.Key_S:
                parameter = 'crop_bottom'
            elif self.current_key_pressed == Qt.Key_Q:
                parameter = 'crop_left'
            elif self.current_key_pressed == Qt.Key_D:
                parameter = 'crop_right'
            if event.angleDelta().y() > 0:
                value = -1
            else:
                value = +1
            event.accept()
            self.event_is_modified(
                type='shot' if self.is_shot_geometry_enabled else 'part',
                parameter=parameter,
                value=value)
            return True
        return False



    def event_key_pressed(self, event):
        key = event.key()
        modifiers = event.modifiers()
        # print("%s.event_key_pressed: %d, modifiers=" % (__name__, key), modifiers)

        if modifiers & Qt.ControlModifier:
            if key == Qt.Key_S:
                self.event_save_modifications()
                return True
            else:
                return False

        if modifiers & Qt.AltModifier:
            if key == Qt.Key_S:
                if self.current_key_pressed != Qt.Key_S:
                    self.signal_position_changed.emit('switch')
                self.current_key_pressed = Qt.Key_S
                return True
            else:
                return False

        if key == Qt.Key_F2:
            if self.pushButton_set_preview.isEnabled():
                self.pushButton_set_preview.toggle()
                return True

        # Edit crop dimensions
        if key in [Qt.Key_Q, Qt.Key_D]:
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



    def event_key_released(self, event):
        if self.current_key_pressed is not None:
            self.current_key_pressed = None
            return True
        return False

