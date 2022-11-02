# -*- coding: utf-8 -*-

import sys
sys.path.append('../scripts')

from logger import log
from pprint import pprint

from PySide6.QtCore import (
    Qt,
    Signal,
    QObject,
    QEvent,
)


from common.sylesheet import set_stylesheet, update_selected_widget_stylesheet

from video_editor.model_video_editor import Model_video_editor
from video_editor.ui.widget_geometry_ui import Ui_widget_geometry
from video_editor.widget_common import Widget_common

class Widget_geometry(Widget_common, Ui_widget_geometry):
    signal_geometry_modified = Signal(dict)

    def __init__(self, ui, model:Model_video_editor):
        super(Widget_geometry, self).__init__(ui)
        self.model = model
        self.ui = ui
        self.setObjectName('geometry')

        # Internal variables
        self.current_key_pressed = None
        self.current_modification_type = 'part'
        self.saved_preview_options = None


        # Disable focus
        self.lineEdit_part_crop_rectangle.setFocusPolicy(Qt.NoFocus)
        self.pushButton_part_crop_edition.setFocusPolicy(Qt.NoFocus)
        self.pushButton_part_crop_preview.setFocusPolicy(Qt.NoFocus)
        self.pushButton_part_resize_edition.setFocusPolicy(Qt.NoFocus)
        self.pushButton_part_resize_preview.setFocusPolicy(Qt.NoFocus)
        self.checkBox_part_keep_ratio.setFocusPolicy(Qt.NoFocus)

        self.lineEdit_part_crop_rectangle.clear()

        self.pushButton_part_crop_edition.toggled[bool].connect(self.event_part_crop_edition_changed)
        self.pushButton_part_crop_preview.toggled[bool].connect(self.event_part_crop_preview_changed)
        self.pushButton_part_resize_preview.toggled[bool].connect(self.event_part_resize_preview_changed)
        self.pushButton_part_resize_edition.toggled[bool].connect(self.event_part_resize_edition_changed)
        self.checkBox_part_keep_ratio.toggled[bool].connect(self.event_part_keep_ratio_changed)

        set_stylesheet(self)
        self.adjustSize()





    def set_initial_options(self, preferences:dict):
        log.info("set_initial_options")
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
            if w['part']['is_enabled']:
                log.info('enable part widget')
            else:
                log.info('enable st widget')

            self.block_signals(False)
        except:
            log.warning("cannot set inbitial options")
            pass

        # Geometry
        self.move(s['geometry'][0], s['geometry'][1])
        self.adjustSize()


    def refresh_values(self, frame:dict):
        geometry = frame['geometry']
        x_c, y_x, w_c, h_c = geometry['crop']
        crop_str = "x: %d, y: %d,  w: %d, h: %d" % (x_c, y_x, w_c, h_c)
        self.lineEdit_part_crop_rectangle.setText(crop_str)


    def set_geometry_edition_enabled(self, enabled):
        log.info("enable edition: %s" % ('true' if enabled else 'false'))
        print("TODO: enable edition: %s" % ('true' if enabled else 'false'))


    def event_undo(self):
        # Replace by historical implementation in model
        pass



    def event_is_modified(self, type, parameter, value):
        # log.info("parameter has been modified: %s: %s, %d" % (type, parameter, value))
        self.pushButton_discard.setEnabled(True)
        self.pushButton_save.setEnabled(True)
        self.pushButton_undo.setEnabled(True)

        self.signal_geometry_modified.emit({
            'type': type,
            'parameter': parameter,
            'value': value
        })


    def get_preview_options(self):
        preview_options = {
            'final_preview': self.pushButton_set_preview.isChecked(),
            'part': {
                'is_enabled': True,
                'crop_edition': self.pushButton_part_crop_edition.isChecked(),
                'crop_preview': self.pushButton_part_crop_preview.isChecked(),
                'resize_edition': self.pushButton_part_resize_edition.isChecked(),
                'resize_preview': self.pushButton_part_resize_preview.isChecked(),
            },
        }
        return preview_options


    def block_signals(self, enabled):
        self.pushButton_part_crop_preview.blockSignals(enabled)
        self.pushButton_part_resize_preview.blockSignals(enabled)
        self.pushButton_part_crop_edition.blockSignals(enabled)
        self.pushButton_part_resize_edition.blockSignals(enabled)
        self.checkBox_part_keep_ratio.blockSignals(enabled)



    def event_preview_changed(self, is_checked:bool=False):
        log.info("widget preview changed to %s" % ('true' if is_checked else 'false'))
        self.block_signals(True)
        if is_checked:
            # save current preview options
            self.saved_preview_options = {
                'part_crop_preview': self.pushButton_part_crop_preview.isChecked(),
                'part_resize_preview': self.pushButton_part_resize_preview.isChecked()
            }
            self.pushButton_part_crop_preview.setChecked(is_checked)
            self.pushButton_part_resize_preview.setChecked(is_checked)
        else:
            if self.saved_preview_options is not None:
                self.pushButton_part_crop_preview.setChecked(self.saved_preview_options['part_crop_preview'])
                self.pushButton_part_resize_preview.setChecked(self.saved_preview_options['part_resize_preview'])
        self.block_signals(False)
        self.signal_preview_options_changed.emit()


    def event_part_crop_edition_changed(self, is_checked:bool):
        log.info("crop edition changed to %s" % ('true' if is_checked else 'false'))
        if is_checked:
            # Disable final preview
            self.pushButton_set_preview.blockSignals(True)
            self.pushButton_set_preview.setChecked(False)
            self.saved_preview_options = None
            self.pushButton_set_preview.blockSignals(False)
        else:
            if not self.pushButton_part_crop_preview.isChecked():
                self.pushButton_part_resize_preview.blockSignals(True)
                self.pushButton_part_resize_preview.setChecked(False)
                self.pushButton_part_resize_preview.blockSignals(False)
        self.signal_preview_options_changed.emit()


    def event_part_crop_preview_changed(self, is_checked:bool):
        log.info("crop preview changed to %s" % ('true' if is_checked else 'false'))
        if not is_checked:
            # Disable final preview
            self.pushButton_set_preview.blockSignals(True)
            self.pushButton_set_preview.setChecked(False)
            self.saved_preview_options = None
            self.pushButton_set_preview.blockSignals(False)

            if (self.pushButton_part_resize_preview.isChecked()
            and not self.pushButton_part_crop_edition.isChecked()):
                self.pushButton_part_resize_preview.blockSignals(True)
                self.pushButton_part_resize_preview.setChecked(False)
                self.pushButton_part_resize_preview.blockSignals(False)
        self.signal_preview_options_changed.emit()


    def event_part_resize_edition_changed(self, is_checked:bool):
        log.info("resize edition changed to %s" % ('true' if is_checked else 'false'))
        if is_checked:
            # Force crop preview
            self.pushButton_part_crop_preview.blockSignals(True)
            self.pushButton_part_crop_preview.setChecked(True)
            self.pushButton_part_crop_preview.blockSignals(False)
        self.signal_preview_options_changed.emit()


    def event_part_resize_preview_changed(self, is_checked:bool):
        log.info("resize preview changed to %s" % ('true' if is_checked else 'false'))
        if not is_checked:
            # Disable final preview
            self.pushButton_set_preview.blockSignals(True)
            self.pushButton_set_preview.setChecked(False)
            self.pushButton_set_preview.blockSignals(False)
        else:
            if (not self.pushButton_part_crop_preview.isChecked()
            and not self.pushButton_part_crop_edition.isChecked()):
                self.pushButton_part_crop_preview.blockSignals(True)
                self.pushButton_part_crop_preview.setChecked(True)
                self.pushButton_part_crop_preview.blockSignals(False)
        self.signal_preview_options_changed.emit()


    def event_part_keep_ratio_changed(self, is_checked:bool):
        log.info("set final ratio: %s" % ('true' if is_checked else 'false'))
        self.signal_preview_options_changed.emit()



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
                type=self.current_modification_type,
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

        if key == Qt.Key_F2:
            if self.pushButton_set_preview.isEnabled():
                self.pushButton_set_preview.toggle()
                return True

        # Edit crop dimensions
        if key in [Qt.Key_Q, Qt.Key_D]:
            self.current_key_pressed = key
            return True
        elif key == Qt.Key_Z:
            # if key != self.current_key_pressed:
            #     self.signal_crop_enabled.emit('top')
            self.current_key_pressed = key
            return True
        elif key == Qt.Key_S:
            # if key != self.current_key_pressed:
                # self.signal_crop_enabled.emit('bottom')
            self.current_key_pressed = key
            return True
        return False



    def event_key_released(self, event):
        if self.current_key_pressed is not None:
            self.current_key_pressed = None
            return True
        return False

