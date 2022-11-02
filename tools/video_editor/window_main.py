# -*- coding: utf-8 -*-

import sys



sys.path.append('../scripts')
import cv2
import gc
import time
import numpy as np
import os
from pprint import pprint
from logger import log

from PySide6.QtCore import (
    QBasicTimer,
    QEvent,
    QPoint,
    QSize,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QColor,
    QCursor,
    QIcon,
    QImage,
    QPainter,
    QPen,
)
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMenu,
    QMessageBox,
)

from common.sylesheet import set_widget_stylesheet
from common.window_common import Window_common
from video_editor.model_video_editor import Model_video_editor
from video_editor.widget_selection import Widget_selection
from common.widget_controls import Widget_controls
from video_editor.widget_curves import Widget_curves
from video_editor.widget_replace import Widget_replace
from video_editor.widget_geometry import Widget_geometry

from utils.common import FPS

COLOR_CROP_RECT = QColor(230, 30, 30)
COLOR_FINAL_RECT = QColor(0, 255, 0)
COLOR_DISPLAY_RECT = QColor(255, 255, 255)
# PEN_CROP_SIZE must be equal to 1 or 2
PEN_CROP_SIZE = 1
PAINTER_MARGIN_LEFT = 20
PAINTER_MARGIN_TOP = 20
class Window_main(QMainWindow):
    signal_preview_options_changed = Signal(dict)
    signal_save_and_close = Signal()

    def __init__(self, model:Model_video_editor):
        super(Window_main, self).__init__()

        window_icon = QIcon()
        window_icon.addFile("img/icon_16.png", QSize(16,16))
        window_icon.addFile("img/icon_24.png", QSize(24,24))
        window_icon.addFile("img/icon_32.png", QSize(32,32))
        window_icon.addFile("img/icon_48.png", QSize(48,48))
        window_icon.addFile("img/icon_64.png", QSize(64,64))
        window_icon.addFile("img/icon_128.png", QSize(128,128))
        window_icon.addFile("img/icon_256.png", QSize(256,256))
        self.setWindowIcon(window_icon)

        self.setWindowFlags(Qt.Window)
        self.setStyleSheet("background-color: black")
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)

        # Add painter
        self.painter = QPainter()


        # Internal variables
        self.model = model
        self.widgets = {
            'controls': None,
            'replace': None,
            'geometry': None,
            'selection': None,
            'curves': None,
        }

        self.image = None
        self.is_repainting = False
        self.is_activated = False

        self.is_closing = False
        self.discard_modifications = False


        self.show_side = 'top'
        self.current_editor = ''
        self.current_widget = self.current_editor
        self.current_frame_index = -1
        self.playing_frame_start_no = 0
        self.current_frame_no = 0
        self.timer = QBasicTimer()
        self.timer.stop()




        # Get preferences from model
        p = self.model.get_preferences()

        # RGB Curves
        if 'curves' in self.widgets.keys():
            self.widget_curves = Widget_curves(self, self.model)
            self.widgets['curves'] = self.widget_curves
            self.widget_curves.set_initial_options(p)
            self.widget_curves.set_main_window_margin(PAINTER_MARGIN_LEFT)
            self.widget_curves.signal_preview_options_changed.connect(self.event_preview_options_changed)

        # Replace frames
        if 'replace' in self.widgets.keys():
            self.widget_replace = Widget_replace(self, self.model)
            self.widgets['replace'] = self.widget_replace
            self.widget_replace.set_initial_options(p)
            self.widget_replace.signal_preview_options_changed.connect(self.event_preview_options_changed)
            self.widget_replace.signal_frame_selected[dict].connect(self.event_replace_frame_selected)

        # Crop and resize
        if 'geometry' in self.widgets.keys():
            self.widget_geometry = Widget_geometry(self, self.model)
            self.widgets['geometry'] = self.widget_geometry
            self.widget_geometry.set_initial_options(p)
            self.widget_geometry.signal_preview_options_changed.connect(self.event_preview_options_changed)

        # Player controls
        if 'controls' in self.widgets.keys():
            self.widget_controls = Widget_controls(self, self.model)
            self.widgets['controls'] = self.widget_controls
            self.widget_controls.set_initial_options(p)
            self.widget_controls.signal_button_pushed[str].connect(self.event_control_button_pressed)
            self.widget_controls.signal_slider_moved[int].connect(self.event_move_to_frame_no)
            self.widget_controls.signal_preview_options_changed.connect(self.event_preview_options_changed)

        # Selection of episode/part/shot
        self.widget_selection = Widget_selection(self, self.model)
        self.widgets['selection'] = self.widget_selection
        self.widget_selection.refresh_browsing_folder(self.model.get_available_episode_and_parts())

        self.widget_selection.signal_ep_or_part_selection_changed[dict].connect(self.event_selection_changed)
        self.widget_selection.set_initial_options(p)
        self.widget_selection.widget_app_controls.signal_action[str].connect(self.event_editor_action)

        # Model
        self.model.signal_ready_to_play[dict].connect(self.event_ready_to_play)
        self.model.signal_reload_frame.connect(self.event_reload_frame)
        self.model.signal_close.connect(self.event_close_without_saving)

        # Right click
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested[QPoint].connect(self.event_right_click)

        # Show window/widgets and connect signals
        for w in self.widgets.values():
            w.signal_close.connect(self.event_editor_action)
            w.show()

        # Set initial values
        self.set_initial_options(p)
        self.event_show_fullscreen()



    def event_show_fullscreen(self):
        self.blockSignals(True)
        # print("window_main: event_show_fullscreen (required for w11)")
        saved_current_editor = self.current_editor
        for w in self.widgets.values():
            w.blockSignals(True)
            w.showNormal()
            w.activateWindow()
            # w.blockSignals(False)
        self.set_current_editor(saved_current_editor)

        for w in self.widgets.values():
            w.blockSignals(False)

        self.widgets[saved_current_editor].blockSignals(True)
        self.widgets[saved_current_editor].showNormal()
        self.widgets[saved_current_editor].activateWindow()
        self.widgets[saved_current_editor].blockSignals(False)

        self.is_activated = True
        self.blockSignals(False)



    def event_selection_changed(self, selection):
        # Disable crop edition if image is not >= HD
        print("event_selection_changed")
        if selection['k_step'] in ['', 'deinterlace', 'pre_upscale']:
            self.widget_geometry.set_geometry_edition_enabled(False)
        else:
            self.widget_geometry.set_geometry_edition_enabled(True)
        self.event_preview_options_changed()


    def event_editor_action(self, event='exit'):
        # log.info("event=%s" % (event))
        # print("event=%s" % (event))
        if event == 'exit':
            if self.is_closing:
                return

            if self.discard_modifications:
                # print("discard modifications")
                self.event_close()
                return

            if self.model.model_database.is_db_modified():
                log.info("Changes are not saved")
                message_box = QMessageBox()
                message_box.setIcon(QMessageBox.Warning)
                message_box.setWindowTitle("Save before closing?")
                message_box.setText("Some modifications have not been change.");
                message_box.setInformativeText("Do you want to close before saving?");
                message_box.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
                message_box.setDefaultButton(QMessageBox.Save)
                set_widget_stylesheet(message_box)

                answer = message_box.exec()
                if answer == QMessageBox.Save:
                    self.signal_save_and_close.emit()
                elif answer == QMessageBox.Discard:
                    # print("discard modifications")
                    self.discard_modifications = True
                    self.event_close()
                return
            else:
                self.discard_modifications = True
                self.event_close()
        elif event == 'minimize':
            self.widget_selection.showMinimized()
            self.widget_controls.showMinimized()
            self.showMinimized()
        elif event == 'repaint':
            self.repaint()
        else:
            print("Error: action [%s] is deprecated, discard action")

    def closeEvent(self, event):
        # print("closeEvent")
        self.event_editor_action('exit')

    def event_close_without_saving(self):
        self.discard_modifications = True


    def event_close(self):
        # print("%s:event_close" % (__name__))
        if not self.is_closing:
            self.is_closing = True
            self.model.exit()
            self.close_all_widgets()


    def close_all_widgets(self):
        # print("close_all_widgets")
        self.timer.stop()
        for widget in QApplication.topLevelWidgets():
            widget.close()
        self.close()
        # Not clean but avoid ghost processes: clean this
        sys.exit()


    def set_initial_options(self, preferences:dict):
        s = preferences['viewer']
        if False:
            self.setGeometry(s['geometry'][0],
                s['geometry'][1],
                s['geometry'][2],
                s['geometry'][3])
        else:
            # For debug purpose
            self.setGeometry(s['geometry'][0],
                s['geometry'][1],
                1600,
                s['geometry'][3]-200)
        log.info("set current editor: %s" % (s['current_editor']))
        self.set_current_editor(s['current_editor'])


    def get_preferences(self) -> dict:
        # Get preferences from children, merge them and return it
        preferences = {
            'viewer': {
                'screen': 0,
                'geometry': self.geometry().getRect(),
                'current_editor': self.current_editor,
            },
        }
        for e, w in self.widgets.items():
            preferences.update({e: w.get_preferences()})
        return preferences


    def select_next_editor(self):
        # rework this: use a list of widgets
        print("select next editor from: %s" % (self.current_editor))
        # todo: clean this by using the table of editors
        for i in range(len(self.widgets.keys())):
            if self.current_editor == 'curves':
                try:
                    self.widget_replace.activateWindow()
                    log.info("changed to: %s" % (self.current_editor))
                    return
                except:
                    self.current_editor = 'replace'

            if self.current_editor == 'replace':
                try:
                    self.widget_geometry.activateWindow()
                    log.info("changed to: %s" % (self.current_editor))
                    return
                except:
                    self.current_editor = 'geometry'

            if self.current_editor == 'geometry':
                try:
                    self.widget_curves.activateWindow()
                    log.info("changed to: %s" % (self.current_editor))
                    return
                except:
                    self.current_editor = 'curves'

            if self.current_editor in ['selection', 'controls']:
                try:
                    self.widget_curves.activateWindow()
                    log.info("changed to: %s" % (self.current_editor))
                    return
                except:
                    self.current_editor = 'curves'


    def get_current_widget(self):
        return self.current_widget


    def set_current_editor(self, current_editor):
        # Set current widget and editor
        # print("Change widget from [%s] to [%s], editor from [%s] to [%s]" %
        #     (self.current_widget, current_editor, self.current_editor, current_editor))

        if current_editor == 'selection':
            # Do not select this widget
            return

        self.current_widget = current_editor


        for e, w in self.widgets.items():
            if self.current_editor == e:
                w.set_selected(False)

        self.current_editor = current_editor

        # Activate the selected editor widget
        for e, w in self.widgets.items():
            if self.current_editor == e:
                w.set_selected(True)
                break


    def event_preview_options_changed(self):
        # log.info("change preview: editor: %s" % (self.current_editor))
        preview_options = dict()
        for e, w in self.widgets.items():
            preview_options.update({e: w.get_preview_options()})
        self.signal_preview_options_changed.emit(preview_options)



    def event_ready_to_play(self, playlist_properties):
        log.info("ready to play")
        self.current_frame_index = 0
        self.playing_frame_count = playlist_properties['count']
        self.playing_frame_start_no = playlist_properties['start']
        f = self.model.get_frame(self.current_frame_index + self.playing_frame_start_no)
        self.display_frame(f)


    def event_move_to_frame_no(self, frame_index):
        # log.info("move to frame %d" % (frame_index))
        self.current_frame_index = frame_index
        f = self.model.get_frame(self.current_frame_index + self.playing_frame_start_no)
        self.display_frame(f)


    def event_replace_frame_selected(self, item):
        frame_no = item['frame_no']
        log.info("move to frame %d" % (frame_no))
        index = (frame_no - self.playing_frame_start_no)
        self.widget_controls.update_slider_value(index)


    def event_reload_frame(self):
        if self.current_frame_index == -1:
            return
        # log.info("refresh frame %d" % (self.current_frame_index + self.playing_frame_start_no))
        f = self.model.get_frame(self.current_frame_index + self.playing_frame_start_no)
        self.display_frame(f)


    def event_control_button_pressed(self, action):
        if action == 'play':
            self.widget_selection.set_enabled(False)
            log.info("start playing")
            speed = self.widget_controls.get_playing_speed()
            self.timer_delay = int(1000/(FPS*speed))
            # self.timer_delay = 25
            print("timer: %dms" % (self.timer_delay))
            self.timer.start(self.timer_delay, Qt.PreciseTimer, self)
            self.now = time.time()

        elif action == 'pause':
            self.timer.stop()
            self.widget_selection.set_enabled(True)

        elif action == 'stop':
            self.timer.stop()
            self.widget_selection.set_enabled(True)
            self.event_move_to_frame_no(0)



    def timerEvent(self, e=None):
        now = time.time()
        print(int(1000 * (now - self.now)))
        self.now = now

        self.current_frame_index += 1
        if self.current_frame_index >= self.playing_frame_count:
            self.timer.stop()
            self.widget_controls.event_stop()
        else:
            self.widget_controls.set_playing_frame_properties(self.current_frame_index)
            f = self.model.get_frame(self.current_frame_index + self.playing_frame_start_no)
            self.display_frame(f)



    def flush_image(self):
        log.info("flush image")
        del self.image
        self.image = None
        gc.collect()

        self.is_grabbing_split_line = False
        if self.is_repainting:
            log.error("error: flush while repainting")
        self.is_repainting = False



    def display_frame(self, frame: dict):
        # now = time.time()
        # log.info("display frame: %s" % (frame['filepath']))
        if frame is None or not os.path.exists(frame['filepath']):
            self.flush_image()
        else:
            if self.image is not None:
                del self.image
                self.image = None

            # Get preview options
            options = self.model.get_preview_options()
            if options is None:
                sys.exit("preview options are not set!")

            # Set an internal image object
            self.image = {
                'cache_fgd': frame['cache_fgd'],
                'cache': frame['cache'],
                'geometry': frame['geometry'],
                'curves': {
                    'lut': None
                },
                'preview_options': options,
            }


            # Update info in the other widgets
            for e, w in self.widgets.items():
                w.refresh_values(frame)

        self.repaint()
        # print("\t\t%f" % int(1000 * (time.time() - now)))



    def get_rgb_value(self, xr, yr):
        if self.image is None:
            # No frame loaded
            return

        pick_initial_value = True
        if pick_initial_value:
            try:
                # print("get_color from (%d, %d)" % (xr, yr))
                h, w, c = self.image['cache'].shape
                if (PAINTER_MARGIN_LEFT <= xr < self.width()+PAINTER_MARGIN_LEFT
                    and PAINTER_MARGIN_TOP <= yr < self.height()+PAINTER_MARGIN_TOP
                    and xr < w+PAINTER_MARGIN_LEFT and yr < h+PAINTER_MARGIN_TOP):

                    # TODO: correct this!
                    bgr = self.image['cache_fgd'][yr-self.image['origin'][1], xr-self.image['origin'][0]]
                    # print("\t(%d, %d) -> (%d, %d, %d)" % (
                    #     xr-self.image['origin'][0],
                    #     yr-self.image['origin'][1],
                    #     bgr[2], bgr[1], bgr[0]))

                    self.widget_curves.set_color_values(bgr)
                    self.setCursor(Qt.CrossCursor)
                else:
                    self.widget_curves.set_color_values(None)
                    self.setCursor(Qt.ArrowCursor)
            except:
                # print("error!")
                pass
        else:
            try:
                # print("get_color from (%d, %d)" % (xr, yr))
                h, w, c = self.image['cache'].shape
                if (PAINTER_MARGIN_LEFT <= xr < self.width()+PAINTER_MARGIN_LEFT
                    and PAINTER_MARGIN_TOP <= yr < self.height()+PAINTER_MARGIN_TOP
                    and xr < w+PAINTER_MARGIN_LEFT and yr < h+PAINTER_MARGIN_TOP):

                    bgr = self.image['cache'][yr-self.image['origin'][1] + PAINTER_MARGIN_TOP,
                                            xr-self.image['origin'][0] + PAINTER_MARGIN_LEFT]

                    self.widget_curves.set_color_values(bgr)
                    self.setCursor(Qt.CrossCursor)
                else:
                    self.widget_curves.set_color_values(None)
                    self.setCursor(Qt.ArrowCursor)
            except:
                # print("error!")
                pass



    def event_right_click(self, qpoint):
        cursor_position = QCursor.pos()
        pop_menu = QMenu(self)
        pop_menu.setStyleSheet("background-color: rgb(128, 128, 128);")
        action_exit = pop_menu.addAction('Exit')
        action_exit.triggered.connect(self.event_close)
        pop_menu.exec_(cursor_position)



    def mousePressEvent(self, event):
        x = event.x()
        y = event.y()

        if (self.image is not None
        and self.image['cache_fgd'] is not None):
            if self.widget_curves.grab_split_line(x):
                self.setCursor(Qt.SplitHCursor)
            else:
                print("\t-> cache_fgd: ", self.image['cache_fgd'].shape)
                self.get_rgb_value(x, y)
            event.accept()
            return True
        else:
            event.ignore()


    def mouseMoveEvent(self, event):
        x = event.x()
        y = event.y()
        if self.widget_curves.move_split_line(x):
            self.setCursor(Qt.SplitHCursor)
            event.accept()
            self.event_reload_frame()
        else:
            self.get_rgb_value(x, y)
            event.ignore()


    def mouseMoved(self, x, y):
        if self.widget_curves.split_line_moved(x, self.mouse_grabX):
            self.setCursor(Qt.SplitHCursor)
            self.event_reload_frame()


    def mouseReleaseEvent(self, event):
        self.setCursor(Qt.ArrowCursor)
        self.widget_curves.split_line_released(event.x())


    def wheelEvent(self, event):
        if self.current_editor == 'geometry':
            is_accepted = self.widget_geometry.wheelEvent(event)
            if is_accepted:
                event.accept()
                return True

        if self.widget_controls.wheel_event(event):
            event.accept()
            return True

        return super().wheelEvent(event)


    def keyPressEvent(self, event):
        # log.info("key event in main window")
        key = event.key()
        modifiers = event.modifiers()
        # print("%s.event_key_pressed: %d, modifiers=" % (__name__, key), modifiers)

        if modifiers & Qt.ControlModifier:
            if key == Qt.Key_Tab:
                self.select_next_editor()
                event.accept()
                return True
        elif modifiers & Qt.AltModifier:
            if key == Qt.Key_F4:
                event.accept()
                return True
            elif key == Qt.Key_F9:
                self.showMinimized()
                event.accept()
                return True
        else:
            if key == Qt.Key_F5:
                log.info("Reload")
                self.widget_selection.event_episode_changed()
                event.accept()
                return True

        for e, w in self.widgets.items():
            if self.current_editor == e:
                is_accepted = w.event_key_pressed(event)
                if is_accepted:
                    event.accept()
                    return True

        if self.widget_controls.event_key_pressed(event):
            print("forwarded to controls", key)
            event.accept()
            return True

        event.accept()
        return True


    def keyReleaseEvent(self, event):
        key = event.key()
        # print("keyReleaseEvent: main window")
        self.widget_controls.event_key_released(event)


        if self.current_editor == 'curves':
            is_accepted = self.widget_curves.event_key_released(event)
            if is_accepted:
                event.accept()
                return True
        elif self.current_editor == 'replace':
            is_accepted = self.widget_replace.event_key_released(event)
            if is_accepted:
                event.accept()
                return True
        if self.current_editor == 'geometry':
            is_accepted = self.widget_geometry.event_key_released(event)
            if is_accepted:
                event.accept()
                return True

        if self.widget_controls.event_key_released(event):
            event.accept()
            return True
        # return self.widget_controls.keyReleaseEvent(event)



    def changeEvent(self, event: QEvent) -> None:
        # print("\nwindow_main: changeEvent", event.type(), flush=True)
        if event.type() == QEvent.ActivationChange:
            # print("* QEvent.ActivationChange", flush=True)
            # print("\twindow state:", self.windowState(), flush=True)
            # print("\t is active? ", self.isActiveWindow(), flush=True)


            if self.windowState() == Qt.WindowState().WindowNoState:
                # print("\tWindowNoState -> show fullscreen")
                self.setWindowState(Qt.WindowActive)
                self.event_show_fullscreen()
                # print("-------------------------------------")
                event.accept()
                return True


            if self.windowState() & Qt.WindowState().WindowActive:
                # print("\tWindowMinimized -> show fullscreen")
                self.setWindowState(Qt.WindowActive)
                self.event_show_fullscreen()
                # print("-------------------------------------")
                event.accept()
                return True


            if (self.windowState() & Qt.WindowState().WindowMinimized
            and not self.isActiveWindow()):
                # print("\tWindowMinimized -> show fullscreen")
                self.setWindowState(Qt.WindowActive)
                self.event_show_fullscreen()
                # print("-------------------------------------")
                event.accept()
                return True

        # elif event.type() == QEvent.WindowStateChange:
        #     print("///* QEvent.WindowStateChange", flush=True)
        #     print("\twindow state:", self.windowState(), flush=True)
        #     print("\t is active? ", self.isActiveWindow(), flush=True)
        #     event.accept()
        #     return True

        return super().changeEvent(event)



    def paintEvent(self, event):
        # now = time.time()
        # log.info("repainting")
        if self.image is None:
            log.info("no image loaded")
            return

        img = self.image['cache']
        if img is None:
            return

        if self.is_repainting:
            log.error("error: self.is_repainting is True!!")
            return
        self.is_repainting = True
        delta_y = 0

        options = self.image['preview_options']
        h, w, c = img.shape
        q_image = QImage(img.data, w, h, w * 3, QImage.Format_BGR888)
        w_final, h_final = (1440, 1080)

        self.image['origin'] = [PAINTER_MARGIN_LEFT, PAINTER_MARGIN_TOP - delta_y]
        if self.painter.begin(self):

            if options['geometry']['final_preview']:
                # print("paintEvent: display final_preview")
                self.painter.drawImage(
                    QPoint(PAINTER_MARGIN_LEFT, PAINTER_MARGIN_TOP - delta_y), q_image)
            else:
                part_options = options['geometry']['part']

                if part_options['crop_edition'] and not part_options['crop_preview']:
                    if not part_options['resize_preview']:
                        # print("paintEvent: draw rect crop on the original image")
                        # Original
                        self.painter.drawImage(
                            QPoint(PAINTER_MARGIN_LEFT, PAINTER_MARGIN_TOP - delta_y), q_image)

                        # Add a rect for the crop
                        c_x0, c_y0, c_w, c_h = self.image['geometry']['crop']
                        pen = QPen(COLOR_CROP_RECT)
                        pen.setWidth(PEN_CROP_SIZE)
                        pen.setStyle(Qt.SolidLine)
                        self.painter.setPen(pen)
                        # https://doc.qt.io/qt-6/qrect.html, PEN_CROP_SIZE = 1
                        # print("\timg: %dx%d" % (img.data.shape[1], img.data.shape[0]))
                        # print("\trect: (%d;%d) w=%d, h=%d" % (c_x0 - 1, c_y0 - delta_y - 1, c_w + 1, c_h + 1))
                        self.painter.drawRect(
                            PAINTER_MARGIN_LEFT + c_x0 - 1,
                            PAINTER_MARGIN_LEFT + c_y0 - delta_y - 1,
                            c_w + 1,
                            c_h + 1)
                    else:
                        # print("paintEvent: draw rect crop on the resized image")

                        # Image is resized, add the recalculated crop
                        c_x0, c_y0, c_w, c_h = self.image['geometry']['crop']
                        w_tmp = int((c_w * h_final) / float(c_h))
                        pad_left = int((w_final - w_tmp) / 2)
                        c_l = int((c_x0 * h_final) / float(c_h))
                        c_t = int((c_y0 * h_final) / float(c_h))

                        self.image['origin'] = [
                            PAINTER_MARGIN_LEFT + pad_left - c_l,
                            PAINTER_MARGIN_TOP - c_t - delta_y]
                        self.painter.drawImage(
                                QPoint(PAINTER_MARGIN_LEFT + pad_left - c_l,
                                        PAINTER_MARGIN_TOP - c_t - delta_y),
                                q_image)

                        # Add the cropped resized rect
                        pen = QPen(COLOR_CROP_RECT)
                        pen.setWidth(PEN_CROP_SIZE)
                        pen.setStyle(Qt.SolidLine)
                        self.painter.setPen(pen)
                        self.painter.drawRect(
                            PAINTER_MARGIN_LEFT + pad_left - 1,
                            PAINTER_MARGIN_LEFT - delta_y - 1,
                            w_tmp + 1,
                            h_final + 1)

                        # Add the final 1080p rect
                        pen = QPen(COLOR_DISPLAY_RECT)
                        pen.setWidth(PEN_CROP_SIZE)
                        pen.setStyle(Qt.SolidLine)
                        self.painter.setPen(pen)
                        self.painter.drawRect(
                            PAINTER_MARGIN_LEFT - 1,
                            PAINTER_MARGIN_LEFT - delta_y - 1,
                            w_final + 1,
                            h_final + 1)

                elif part_options['crop_preview']:
                    if part_options['resize_preview']:
                        # print("paintEvent: draw cropped image and resized")

                        c_x0, c_y0, c_w, c_h = self.image['geometry']['crop']
                        w_tmp = int((c_w * h_final) / float(c_h))
                        pad_left = int((w_final - w_tmp) / 2)

                        self.image['origin'] = [
                            PAINTER_MARGIN_LEFT + pad_left,
                            PAINTER_MARGIN_TOP - delta_y]
                        self.painter.drawImage(
                            QPoint(
                                PAINTER_MARGIN_LEFT + pad_left,
                                PAINTER_MARGIN_TOP - delta_y),
                            q_image)

                        # Add the final 1080p rect
                        pen = QPen(COLOR_DISPLAY_RECT)
                        pen.setWidth(PEN_CROP_SIZE)
                        pen.setStyle(Qt.SolidLine)
                        self.painter.setPen(pen)
                        self.painter.drawRect(
                            PAINTER_MARGIN_LEFT - 1,
                            PAINTER_MARGIN_LEFT - delta_y - 1,
                            w_final + 1,
                            h_final + 1)
                    else:
                        # print("paintEvent: draw cropped image and not resized")
                        # Crop and no rect
                        c_x0, c_y0, c_w, c_h = self.image['geometry']['crop']
                        self.painter.drawImage(
                            QPoint(PAINTER_MARGIN_LEFT + c_x0,
                                PAINTER_MARGIN_TOP + c_y0 - delta_y),
                            q_image)

                else:
                    # original
                    # print("paintEvent: draw original image")
                    self.painter.drawImage(
                        QPoint(PAINTER_MARGIN_LEFT, PAINTER_MARGIN_TOP - delta_y), q_image)

            if options['curves']['split']:
                try: c_t = 0 if part_options['resize_preview'] else (-1*c_y0)
                except:  c_t = 0
                pen = QPen(QColor(255,255,255))
                pen.setStyle(Qt.DashLine)
                self.painter.setPen(pen)
                self.painter.drawLine(
                    options['curves']['split_x'] + PAINTER_MARGIN_LEFT, PAINTER_MARGIN_TOP - c_t,
                    options['curves']['split_x'] + PAINTER_MARGIN_LEFT, PAINTER_MARGIN_TOP - c_t + max(h, h_final))



            self.painter.end()
        self.is_repainting = False
        # print("\t%f" % int(1000 * (time.time() - now)))
