#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
sys.path.append('../scripts')

from pprint import pprint
from logger import log

from PySide6.QtCore import (
    QEvent,
    QObject,
    QPoint,
    QSize,
    Qt,
    Signal
)
from PySide6.QtGui import (
    QCursor,
    QIcon
)
from PySide6.QtWidgets import (
    QApplication,
    QSlider,
    QWidget
)

from common.sylesheet import set_stylesheet

from merge_stabilize.model_merge_stabilize import Model_merge_stabilize
from merge_stabilize.ui.widget_controls_ui import Ui_widget_controls


class Widget_controls(QWidget, Ui_widget_controls):
    signal_button_pushed = Signal(str)
    signal_slider_moved = Signal(int)
    signal_frame_replaced = Signal(dict)
    signal_preview_options_changed = Signal(dict)

    signal_crop_enabled = Signal(str)
    signal_crop_modified = Signal(dict)
    signal_upper_lower_preview_changed = Signal(str)

    def __init__(self, ui, model:Model_merge_stabilize):
        super(Widget_controls, self).__init__()

        self.setupUi(self)
        self.model = model
        self.ui = ui

        # Setup and patch ui
        self.setAutoFillBackground(True)
        self.setWindowFlags(Qt.Tool)
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setWindowModality(Qt.NonModal)

        self.slider_frames.setMinimumSize(QSize(960, 30))
        self.slider_frames.setMaximum(200)
        self.slider_frames.setOrientation(Qt.Horizontal)
        self.slider_frames.setTickPosition(QSlider.NoTicks)
        self.slider_frames.setTickInterval(1)

        self.set_enabled(False)

        self.icon_play = QIcon()
        self.icon_play.addFile("img/arrow-right.png", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_play_pause.setIcon(self.icon_play)

        self.icon_pause = QIcon()
        self.icon_pause.addFile("img/pause.png", QSize(), QIcon.Normal, QIcon.Off)
        # self.pushButton_play_pause.setIcon(self.icon_pause)


        self.spinBox_speed.setFocusPolicy(Qt.NoFocus)

        # variables
        self.previous_position = None
        self.refresh_status('stopped')
        self.ticks = list()
        self.is_shift_key_pressed = False
        self.frames_start = 0
        self.frames_no = list()

        self.copied_frame_no = -1
        self.copied_shot_crop = -1
        self.backup_preview_options = dict()
        self.current_key_pressed = None

        # Signals
        self.pushButton_previous_frame.clicked.connect(self.event_previous_frame)
        self.pushButton_next_frame.clicked.connect(self.event_next_frame)
        self.pushButton_play_pause.toggled.connect(self.event_play_pause)
        self.pushButton_stop.clicked.connect(self.event_stop)
        self.slider_frames.valueChanged.connect(self.event_slider_moved)

        self.checkBox_preview_rgb.stateChanged.connect(self.event_preview_changed)
        self.checkBox_preview_rgb.setFocusPolicy(Qt.NoFocus)

        self.checkBox_preview_replace.stateChanged.connect(self.event_preview_changed)
        self.checkBox_preview_replace.setFocusPolicy(Qt.NoFocus)

        self.checkBox_preview_final.stateChanged.connect(self.event_final_preview_changed)
        self.checkBox_preview_final.setFocusPolicy(Qt.NoFocus)


        self.model.signal_ready_to_play[dict].connect(self.event_refresh_slider)
        self.model.signal_shotlist_modified[dict].connect(self.event_directory_changed)


        set_stylesheet(self)
        self.adjustSize()


    def set_palette(self, palette):
        self.setPalette(palette)

    def get_preferences(self):
        preferences = {
            'controls': {
                'geometry': self.geometry().getRect(),
                'preview_replace': self.checkBox_preview_replace.isChecked(),
                'preview_rgb': self.checkBox_preview_rgb.isChecked(),
                'preview_final': self.checkBox_preview_final.isChecked(),
                'speed': self.spinBox_speed.value(),
            },
        }
        return preferences


    def set_initial_options(self, preferences:dict):
        log.info("set_initial_options")
        s = preferences['controls']
        for w in [self.checkBox_preview_rgb,
            self.checkBox_preview_replace,
            self.checkBox_preview_final,
            self.spinBox_speed]:
            w.blockSignals(True)

        self.checkBox_preview_rgb.setChecked(s['preview_rgb'])
        self.checkBox_preview_replace.setChecked(s['preview_replace'])
        self.checkBox_preview_final.setChecked(s['preview_final'])

        self.spinBox_speed.setValue(s['speed'])

        self.backup_preview_options = {
            'preview_rgb': self.checkBox_preview_rgb.isChecked(),
            'preview_replace': self.checkBox_preview_replace.isChecked(),
            'preview_final': self.checkBox_preview_final.isChecked()
        }

        self.adjustSize()

        # Geometry
        self.move(s['geometry'][0], s['geometry'][1])

        for w in [self.checkBox_preview_rgb,
            self.checkBox_preview_replace,
            self.checkBox_preview_final,
            self.spinBox_speed]:
            w.blockSignals(False)


    def event_directory_changed(self, values:dict):
        log.info("directory has been parsed, reset variables")
        self.copied_frame_no = -1
        self.copied_shot_crop = -1

    def set_enabled(self, enabled):
        self.pushButton_previous_frame.setEnabled(enabled)
        self.pushButton_next_frame.setEnabled(enabled)
        self.pushButton_play_pause.setEnabled(enabled)
        self.pushButton_stop.setEnabled(enabled)
        self.spinBox_speed.setEnabled(enabled)
        self.slider_frames.setEnabled(enabled)


    def refresh(self, values:dict):
        self.lineEdit_frame_no.setText(str(values['frame_no']))
        self.lineEdit_new_frame_no.setText(str(values['new_frame_no']))
        self.slider_frames.setMaximum(values['count'])
        self.slider_frames.setTickPosition(values['position'])
        self.refresh_status(values['status'])


    def refresh_status(self, status:str):
        self.status = status
        if self.status == 'stopped' or self.status == 'paused':
            self.pushButton_previous_frame.setEnabled(True)
            self.pushButton_next_frame.setEnabled(True)
            self.pushButton_play_pause.setEnabled(True)
            self.pushButton_stop.setEnabled(True)
            self.spinBox_speed.setEnabled(True)
            self.slider_frames.setEnabled(True)
        elif self.status == 'playing':
            self.pushButton_previous_frame.setEnabled(False)
            self.pushButton_next_frame.setEnabled(False)
            self.pushButton_play_pause.setEnabled(True)
            self.pushButton_stop.setEnabled(True)
            self.spinBox_speed.setEnabled(False)
            self.slider_frames.setEnabled(False)


    def update_slider_value(self, index:int):
        f_no = self.frames_no[index]
        self.lineEdit_frame_no.setText(str(f_no))
        # self.lineEdit_new_frame_no.setText(self.model.get_replace_frame_no_str(index))
        self.slider_frames.setValue(index)


    def set_slider_value(self, value):
        self.slider_frames.blockSignals(True)
        self.update_slider_value(value)
        self.slider_frames.blockSignals(False)



    def set_playing_frame_properties(self, current_index):
        self.update_slider_value(current_index)
        f_no = self.frames_no[current_index]
        self.lineEdit_frame_no.setText(str(f_no))
        self.lineEdit_new_frame_no.setText(self.model.get_replace_frame_no_str(current_index))


    def set_slider_to_previous_tick(self):
        current_clider_value = self.slider_frames.value()
        for i in range(len(self.ticks) - 1):
            if self.ticks[i] <= current_clider_value <= self.ticks[i+1]:
                break
        self.update_slider_value(self.ticks[i])


    def set_slider_to_following_tick(self):
        current_clider_value = self.slider_frames.value()
        for i in range(len(self.ticks) - 1):
            if self.ticks[i] <= current_clider_value < self.ticks[i+1]:
                break
        self.update_slider_value(self.ticks[i+1])


    def is_replace_preview_enabled(self):
        return self.checkBox_preview_replace.isChecked()


    def is_rgb_preview_enabled(self):
        return self.checkBox_preview_rgb.isChecked()


    def refresh_frame_replace_no(self, frame_no):
        if frame_no == -1:
            self.lineEdit_new_frame_no.clear()
        else:
            self.lineEdit_new_frame_no.setText(str(frame_no))


    def get_playing_speed(self):
        return self.spinBox_speed.value()


    def event_refresh_slider(self, playlist_properties):
        # log.info("ready to play, refresh slider")

        self.slider_frames.blockSignals(True)
        self.slider_frames.setMaximum(playlist_properties['count'] - 1)
        self.frames_no = playlist_properties['frames_no']
        # self.frames_end = self.frames_start + playlist_properties['count']
        self.copied_frame_no = -1

        self.update_slider_value(0)
        self.lineEdit_frame_no.setText(str(self.frames_no[0]))
        # self.lineEdit_new_frame_no.setText(self.model.get_replace_frame_no_str(0))

        # Save the list of tick position
        self.ticks = playlist_properties['ticks']

        self.slider_frames.blockSignals(False)
        self.set_enabled(True)
        self.clearFocus()


    def event_slider_moved(self, value):
        if self.status == 'paused':
            self.pushButton_play_pause.blockSignals(True)
            self.pushButton_play_pause.setChecked(True)
            self.pushButton_play_pause.setIcon(self.icon_play)
            self.pushButton_play_pause.blockSignals(False)
        f_no = self.frames_no[self.slider_frames.value()]
        # log.info("event: moved to %d" % (f_no))
        self.lineEdit_frame_no.setText(str(f_no))
        # self.lineEdit_new_frame_no.setText(self.model.get_replace_frame_no_str(self.slider_frames.value()))
        self.signal_slider_moved.emit(self.slider_frames.value())


    def event_previous_frame(self, delta=1):
        self.update_slider_value(
            max(0, self.slider_frames.value() - delta))


    def event_next_frame(self, delta=1):
        self.update_slider_value(
            min(self.slider_frames.value() + delta, self.slider_frames.maximum()))


    def event_play_pause(self, checked):
        if not self.pushButton_play_pause.isChecked():
            log.info("event: pause")
            self.refresh_status('paused')
            self.pushButton_play_pause.setIcon(self.icon_play)
            self.pushButton_play_pause.setFocus()
            self.slider_frames.blockSignals(False)
            self.signal_button_pushed.emit('pause')
        else:
            log.info("event: playing")
            self.refresh_status('playing')
            self.pushButton_play_pause.setIcon(self.icon_pause)
            self.pushButton_play_pause.setFocus()
            self.slider_frames.blockSignals(True)
            self.signal_button_pushed.emit('play')
            return True



    def event_stop(self):
        self.refresh_status('stopped')
        self.pushButton_play_pause.blockSignals(True)
        self.pushButton_play_pause.setChecked(False)
        self.pushButton_play_pause.setIcon(self.icon_play)
        self.pushButton_play_pause.blockSignals(False)
        self.slider_frames.blockSignals(True)
        self.slider_frames.setValue(0)
        self.slider_frames.blockSignals(False)
        self.slider_frames.setFocus()

        self.signal_button_pushed.emit('stop')


    def event_copy_frame_no(self):
        log.info("event: copy")
        self.copied_frame_no = int(self.lineEdit_frame_no.text())
        # self.signal_button_pushed.emit('copy')

    def event_paste_frame_no(self):
        log.info("event: paste")
        if self.copied_frame_no == -1:
            return
        shot_no_src = self.model.get_shot_no_from_frame_no(self.copied_frame_no)
        frame_no = int(self.lineEdit_frame_no.text())
        shot_no_dst = self.model.get_shot_no_from_frame_no(frame_no)
        if shot_no_dst != shot_no_src:
            log.info("cannot replace a frame from shot no. %d to %d" % (shot_no_src, shot_no_dst))
            return
        self.signal_frame_replaced.emit({
            'type': 'replace',
            'src': self.copied_frame_no,
            'dst': frame_no
        })

    def event_undo_replace(self):
        log.info("event: undo")
        frame_no = int(self.lineEdit_frame_no.text())
        self.signal_frame_replaced.emit({
            'type': 'undo',
            'dst': frame_no
        })

    def event_remove_replace(self):
        log.info("event: remove")
        self.signal_frame_replaced.emit({
            'type': 'remove',
            'dst': int(self.lineEdit_frame_no.text())
        })


    def event_preview_changed(self):
        # Set/unset preview mode
        log.info("changed preview detected")

        self.checkBox_show_crop_rect.blockSignals(True)
        if self.pushButton_crop_edition.isChecked() and not self.checkBox_preview_final.isChecked():
            self.checkBox_show_crop_rect.setEnabled(True)
        else:
            self.checkBox_show_crop_rect.setEnabled(False)
        self.checkBox_show_crop_rect.blockSignals(False)

        self.signal_preview_options_changed.emit({
            'preview_replace': self.checkBox_preview_replace.isChecked(),
            'preview_rgb': self.checkBox_preview_rgb.isChecked(),
            'preview_crop': self.pushButton_crop_edition.isChecked(),
            'show_crop_rect': self.checkBox_show_crop_rect.isChecked(),
            'preview_final': self.checkBox_preview_final.isChecked(),
        })



    def event_crop_edition_changed(self):
        log.info("changed crop edition")
        self.checkBox_show_crop_rect.blockSignals(True)

        if self.checkBox_preview_final.isChecked():
            log.info("deactivate final")
            self.checkBox_preview_rgb.blockSignals(True)
            self.checkBox_preview_replace.blockSignals(True)
            self.checkBox_preview_final.blockSignals(True)
            self.checkBox_preview_final.setChecked(False)
            self.checkBox_preview_rgb.setChecked(self.backup_preview_options['preview_rgb'])
            self.checkBox_preview_rgb.setEnabled(True)
            self.checkBox_preview_replace.setChecked(self.backup_preview_options['preview_replace'])
            self.checkBox_preview_replace.setEnabled(True)
            self.checkBox_show_crop_rect.setChecked(self.backup_preview_options['show_crop_rect'])
            self.checkBox_preview_rgb.blockSignals(False)
            self.checkBox_preview_replace.blockSignals(False)
            self.checkBox_preview_final.blockSignals(False)

        if self.pushButton_crop_edition.isChecked():
            self.checkBox_show_crop_rect.setEnabled(True)
        else:
            self.checkBox_show_crop_rect.setEnabled(False)
        self.checkBox_show_crop_rect.blockSignals(False)

        self.signal_preview_options_changed.emit({
            'preview_replace': self.checkBox_preview_replace.isChecked(),
            'preview_rgb': self.checkBox_preview_rgb.isChecked(),
            'preview_crop': self.pushButton_crop_edition.isChecked(),
            'show_crop_rect': self.checkBox_show_crop_rect.isChecked(),
            'preview_final': self.checkBox_preview_final.isChecked(),
        })



    def event_final_preview_changed(self):
        log.info("final preview changed")
        self.pushButton_crop_edition.blockSignals(True)
        self.checkBox_preview_rgb.blockSignals(True)
        self.checkBox_preview_replace.blockSignals(True)
        self.checkBox_show_crop_rect.blockSignals(True)

        if self.checkBox_preview_final.isChecked():
            self.backup_preview_options = {
                'preview_rgb': self.checkBox_preview_rgb.isChecked(),
                'preview_replace': self.checkBox_preview_replace.isChecked(),
                'preview_crop': self.pushButton_crop_edition.isChecked(),
                'show_crop_rect': self.checkBox_show_crop_rect.isChecked(),
                'preview_final': self.checkBox_preview_final.isChecked()
            }

            # self.checkBox_preview_rgb.setEnabled(False)
            # self.checkBox_preview_rgb.setChecked(True)

            self.checkBox_preview_replace.setEnabled(False)
            self.checkBox_preview_replace.setChecked(True)
            self.pushButton_crop_edition.setChecked(True)
            # self.pushButton_crop_edition.setEnabled(False)
            self.checkBox_show_crop_rect.setChecked(False)
            self.checkBox_show_crop_rect.setEnabled(False)
        else:
            # self.checkBox_preview_rgb.setChecked(self.backup_preview_options['preview_rgb'])
            # self.checkBox_preview_rgb.setEnabled(True)

            self.checkBox_preview_replace.setChecked(self.backup_preview_options['preview_replace'])
            self.checkBox_preview_replace.setEnabled(True)

            self.pushButton_crop_edition.setChecked(self.backup_preview_options['preview_crop'])
            # self.pushButton_crop_edition.setEnabled(True)

            self.checkBox_show_crop_rect.setChecked(self.backup_preview_options['show_crop_rect'])
            if self.pushButton_crop_edition.isChecked():
                self.checkBox_show_crop_rect.setEnabled(True)
            else:
                self.checkBox_show_crop_rect.setEnabled(False)

        self.pushButton_crop_edition.blockSignals(False)
        self.checkBox_preview_rgb.blockSignals(False)
        self.checkBox_preview_replace.blockSignals(False)
        self.checkBox_show_crop_rect.blockSignals(False)

        self.signal_preview_options_changed.emit({
            'preview_rgb': self.checkBox_preview_rgb.isChecked(),
            'preview_replace': self.checkBox_preview_replace.isChecked(),
            'preview_crop': self.pushButton_crop_edition.isChecked(),
            'show_crop_rect': self.checkBox_show_crop_rect.isChecked(),
            'preview_final': self.checkBox_preview_final.isChecked(),
        })







    def keyReleaseEvent(self, event):
        key = event.key()
        if key == Qt.Key_Shift:
            # log.info("shift key is released")
            self.is_shift_key_pressed = False
            self.current_key_pressed = None
            return True
        elif key in [Qt.Key_Z, Qt.Key_Q, Qt.Key_S, Qt.Key_D]:
            # print("released ZQSD")
            self.current_key_pressed = None
        return super(Widget_controls, self).keyReleaseEvent(event)


    def keyPressEvent(self, event):
        key = event.key()
        modifier = event.modifiers()

        self.current_key_pressed = None

        # action
        if key == Qt.Key_Space:
            log.info("Space key")
            if self.status == 'playing':
                log.info("playing -> pause")
                self.pushButton_play_pause.setChecked(False)
                self.event_play_pause(False)
            else:
                log.info("pause/stop -> playing")
                self.pushButton_play_pause.setChecked(True)
                self.event_play_pause(False)
            return True

        if not self.slider_frames.isEnabled():
            # Do not test any other keys if the app. is playing
            return False


        # copy/paste/save/ etc.
        if modifier & Qt.ControlModifier:
            # if key == Qt.Key_S:
            #     log.info("key event: save modifications")
            #     self.signal_save_modifications.emit(True)
            #     event.accept()
            #     return True

            if key == Qt.Key_C:
                self.event_copy_frame_no()
                event.accept()
                return True
            elif key == Qt.Key_V:
                self.event_paste_frame_no()
                event.accept()
                return True
            elif key == Qt.Key_Z:
                self.event_undo_replace()
                event.accept()
                return True
            elif key == Qt.Key_X:
                self.event_remove_replace()
                event.accept()
                return True

            elif key == Qt.Key_S:
                log.info("widget_controls: key event: save modifications")
                return self.ui.keyPressEvent(event)

        # elif key == Qt.Key_C:
        #     self.pushButton_crop_edition.click()

        elif key == Qt.Key_Delete:
            self.event_remove_replace()

        elif key == Qt.Key_F:
            self.checkBox_preview_final.setChecked(not self.checkBox_preview_final.isChecked())

        # elif key == Qt.Key_R:
        #     new_index = self.model.get_next_replaced_frame_index(index=self.slider_frames.value())
        #     if new_index != -1:
        #         self.update_slider_value(new_index)

        elif key == Qt.Key_P:
            self.checkBox_preview_replace.toggle()

        elif key == Qt.Key_Shift:
            # log.info("shift key is pressed")
            self.is_shift_key_pressed = True

        # modify slider value
        elif key in [Qt.Key_Home, Qt.Key_End]:
            self.slider_frames.keyPressEvent(event)
            event.accept()
        elif key == Qt.Key_Left:
            self.event_previous_frame()
            event.accept()
        elif key == Qt.Key_Right:
            self.event_next_frame()
            event.accept()
        elif key == Qt.Key_Up or key == Qt.Key_PageUp:
            self.event_previous_frame(10)
            event.accept()
        elif key == Qt.Key_Down or key == Qt.Key_PageDown:
            self.event_next_frame(10)
            event.accept()

        # ticks
        # elif key == Qt.Key_Q:
        #     log.info("previous tick")
        #     self.set_slider_to_previous_tick()
        # elif key == Qt.Key_D:
        #     log.info("next tick")
        #     self.set_slider_to_following_tick()

        # # crop edition
        # elif key in [Qt.Key_Q, Qt.Key_D]:
        #     self.current_key_pressed = key

        elif key == Qt.Key_Z:
            if key != self.current_key_pressed:
                self.signal_upper_lower_preview_changed.emit('top')
            self.current_key_pressed = key
            return True
        elif key == Qt.Key_S:
            if key != self.current_key_pressed:
                self.signal_upper_lower_preview_changed.emit('bottom')
            self.current_key_pressed = key
            return True

        # self.setFocus()





    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        # Filter press/release events
        focus_object = QApplication.focusObject()
        if focus_object in [self.doubleSpinBox_knn_ratio,
                            self.doubleSpinBox_ransac_reproj_threshold]:
            if event.type() == QEvent.KeyPress:
                key = event.key()
                if key in [Qt.Key_D, Qt.key_E, Qt.key_C,
                            Qt.Key_S, Qt.Key_U, Qt.Key_B, Qt.Key_O,
                            Qt.Key_M, Qt.Key_R]:
                    # print("self.doubleSpinBox:", focus_object)
                    self.keyPressEvent(event)
                    event.accept()
                    return True
                elif key == Qt.Key_Escape:
                    self.deselect_spinbox()
                    self.slider_frames.setFocus()
                    event.accept()
                    return True
                else:
                    print("eventFilter")
                    focus_object.eventFilter(watched, event)
                    return False

        return super().eventFilter(watched, event)








    def wheelEvent(self, event):
        if not self.slider_frames.isEnabled():
            return

        if self.current_key_pressed is not None:
            if self.current_key_pressed == Qt.Key_Z:
                side = 'top'
            elif self.current_key_pressed == Qt.Key_S:
                side = 'bottom'
            elif self.current_key_pressed == Qt.Key_Q:
                side = 'left'
            elif self.current_key_pressed == Qt.Key_D:
                side = 'right'
            if event.angleDelta().y() > 0:
                value = -1
            else:
                value = +1
            event.accept()
            self.signal_crop_modified.emit({
                'side': side,
                'value': value
            })
            return


        # Do not accept event if not in paused mode
        if self.status == 'stopped':
            self.refresh_status('paused')
        if self.status != 'paused':
            return

        if self.is_shift_key_pressed:
            # move to next/previous tick
            if event.angleDelta().y() > 0:
                self.set_slider_to_previous_tick()
            elif event.angleDelta().y() < 0:
                self.set_slider_to_following_tick()
        else:
            # Select next/previous frame
            if event.angleDelta().y() > 0:
                self.event_previous_frame()
            elif event.angleDelta().y() < 0:
                self.event_next_frame()

        event.accept()



    def mousePressEvent(self, event):
        self.previous_position = QCursor().pos()

    def mouseMoveEvent(self, event):
        if self.previous_position is not None:
            cursor_position = QCursor().pos()
            delta = QPoint(cursor_position - self.previous_position)
            self.previous_position = cursor_position
            self.move(self.pos() + delta)
            event.accept()



