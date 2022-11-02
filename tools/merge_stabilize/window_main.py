#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
sys.path.append('../scripts')
import cv2
import gc
import numpy as np
import time
from pprint import pprint
from logger import log

from PySide6.QtCore import (
    QBasicTimer,
    QEvent,
    Qt,
    QPoint,
    QSize,
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
    QMenu
)

from utils.common import FPS

from common.window_common import Window_common
from merge_stabilize.model_merge_stabilize import Model_merge_stabilize
from merge_stabilize.model_merge_stabilize import process_single_frame
from merge_stabilize.widget_selection import Widget_selection
from common.widget_controls import Widget_controls
from merge_stabilize.widget_stitching_curves import Widget_stitching_curves
from merge_stabilize.widget_stitching import Widget_stitching
from merge_stabilize.widget_stabilize import Widget_stabilize
from merge_stabilize.widget_geometry import Widget_geometry


COLOR_CROP_RECT = QColor(250, 50, 50)
COLOR_STITCHING_AREA_RECT = QColor(50, 255, 50)
COLOR_STITCHING_FGD_CROP_RECT = QColor(255, 50, 50)
PEN_CROP_SIZE = 1


class Window_main(QMainWindow):
    signal_generate_cache = Signal(list)
    signal_save_modifications = Signal(bool)
    signal_preview_options_changed = Signal(dict)

    def __init__(self, model:Model_merge_stabilize):
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
            'stitching_curves': None,
            'stitching': None,
            'stabilize': None,
            'geometry': None,
            'selection': None,
        }

        # Reset variables
        self.image = None
        self.image_bgd = None

        self.is_repainting = False
        self.is_closing = False

        self.show_side = 'top'
        self.current_editor = ''

        self.current_frame_index = -1
        self.current_frame_no = 0
        self.timer = QBasicTimer()
        self.timer.stop()


        self.do_display_rect_for_stitching = False
        self.do_display_crop_for_stitching = False
        self.do_display_crop_rect_for_stitching = False

        self.is_cache_ready = False

        # Get preferences from model
        p = self.model.get_preferences()

        # Controls
        if 'controls' in self.widgets.keys():
            self.widget_controls = Widget_controls(self, self.model)
            self.widgets['controls'] = self.widget_controls
            self.widget_controls.set_initial_options(p)
            self.widget_controls.signal_button_pushed[str].connect(self.event_control_button_pressed)
            self.widget_controls.signal_slider_moved[int].connect(self.event_move_to_frame_no)
            self.widget_controls.signal_preview_options_changed.connect(self.event_preview_options_changed)

        # Stitching
        if 'stitching' in self.widgets.keys():
            self.widget_stitching = Widget_stitching(self, self.model)
            self.widgets['stitching'] = self.widget_stitching
            self.widget_stitching.set_initial_options(p)
            self.widget_stitching.signal_preview_options_changed.connect(self.event_preview_options_changed)
            self.widget_stitching.signal_enabled_modified[bool].connect(self.event_st_enabled_changed)

        # Stitching curves: histogram, curves edition and selection
        if 'stitching_curves' in self.widgets.keys():
            self.widget_stitching_curves = Widget_stitching_curves(self, self.model)
            self.widgets['stitching_curves'] = self.widget_stitching_curves
            self.widget_stitching_curves.set_initial_options(p)
            self.widget_stitching_curves.signal_channel_selected.connect(self.event_stitching_curves_channel_selected)
            self.widget_stitching_curves.signal_preview_options_changed.connect(self.event_preview_options_changed)
            self.widget_stitching_curves.widget_hist_curve.signal_curves_editing.connect(self.event_refresh_image)

        # Stabilization
        if 'stabilize' in self.widgets.keys():
            self.widget_stabilize = Widget_stabilize(self, self.model)
            self.widgets['stabilize'] = self.widget_stabilize
            self.widget_stabilize.set_initial_options(p)
            self.widget_stabilize.signal_preview_options_changed.connect(self.event_preview_options_changed)
            self.widget_stabilize.signal_enabled_modified[bool].connect(self.event_st_enabled_changed)

        # Crop and resize
        if 'geometry' in self.widgets.keys():
            self.widget_geometry = Widget_geometry(self, self.model)
            self.widgets['geometry'] = self.widget_geometry
            self.widget_geometry.set_initial_options(p)
            self.widget_geometry.signal_preview_options_changed.connect(self.event_preview_options_changed)

        # Selection
        self.widget_selection = Widget_selection(self, self.model)
        self.widgets['selection'] = self.widget_selection
        self.widget_selection.refresh_browsing_folder(self.model.get_available_episode_and_parts())
        self.widget_selection.set_initial_options(p)
        self.widget_selection.widget_app_controls.signal_action[str].connect(self.event_editor_action)

        # Events
        self.model.signal_ready_to_play[dict].connect(self.event_ready_to_play)
        self.model.signal_reload_frame.connect(self.event_reload_frame)
        self.model.signal_cache_is_ready.connect(self.event_cache_is_ready)
        self.model.signal_refresh_image.connect(self.event_refresh_image)

        # Right click
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested[QPoint].connect(self.event_right_click)

        # Show window/widgets and connect signals
        for w in self.widgets.values():
            w.signal_close.connect(self.event_editor_action)
            w.show()


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


    def event_activated(self):
        self.widget_selection.activateWindow()
        self.widget_controls.activateWindow()
        self.widget_stitching.activateWindow()
        self.widget_stitching_curves.activateWindow()
        self.widget_stabilize.activateWindow()
        self.widget_geometry.activateWindow()



    def event_refresh_image(self):
        self.repaint()


    def event_stitching_curves_channel_selected(self):
        # todo: flush current cache image
        print("event_stitching_curves_channel_selected")
        self.repaint()

    def event_editor_action(self, event):
        print("event=%s" % (event))
        if event == 'exit':
            if self.model.model_database.is_db_modified():
                log.info("Changes are not saved")
                print("Changes are not saved")
                return
            self.event_close()
        elif event == 'minimize':
            self.widget_selection.showMinimized()
            self.widget_controls.showMinimized()
            self.showMinimized()
        elif event == 'save':
            self.widget_controls.signal_save_modifications.emit(True)
        elif event == 'discard':
            self.widget_controls.signal_save_modifications.emit(False)
        elif event == 'repaint':
            self.repaint()


    def closeEvent(self, event):
        print("close_event")
        self.event_editor_action('exit')


    def event_close(self):
        print("%s:event_close" % (__name__))
        if not self.is_closing:
            self.is_closing = True
            self.model.exit()
            self.close_all_widgets()


    def close_all_widgets(self):
        print("close_all_widgets")
        for widget in QApplication.topLevelWidgets():
            widget.close()
        self.close()


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

        self.do_display_rgb_image = preferences['controls']['preview_rgb']
        self.do_display_replaced_image = preferences['controls']['preview_replace']
        self.do_display_cropped_image = preferences['controls']['preview_crop']
        self.do_display_crop_rect = preferences['controls']['show_crop_rect']
        self.do_display_final = preferences['controls']['preview_final']



    def get_preferences(self) -> dict:
        # print("%s:get_preferences" % (__name__))
        # get preferences from children, merge them and return it
        new_preferences = {
            'viewer': {
                'screen': 0,
                'geometry': self.geometry().getRect()
            }
        }
        new_preferences.update(self.widget_selection.get_preferences())
        new_preferences.update(self.widget_controls.get_preferences())
        new_preferences.update(self.widget_stitching_curves.get_preferences())
        new_preferences.update(self.widget_stabilize.get_preferences())
        new_preferences.update(self.widget_stitching.get_preferences())
        new_preferences.update(self.widget_geometry.get_preferences())
        return new_preferences


    def set_current_editor(self, current_editor):
        self.current_editor = current_editor
        print("editor: %s" % (current_editor))


    def event_ready_to_play(self, playlist_properties):
        # log.info("ready to play")
        self.current_frame_index = 0
        self.playing_frame_count = playlist_properties['count']
        self.playing_frame_start_no = playlist_properties['start']
        f = self.model.get_frame(self.current_frame_index + self.playing_frame_start_no,
            original=not self.do_display_replaced_image)
        self.display_frame(f)


    def event_move_to_frame_no(self, frame_index):
        # log.info("move to frame %d" % (frame_index))
        self.current_frame_index = frame_index
        f = self.model.get_frame(self.current_frame_index + self.playing_frame_start_no,
            original=not self.do_display_replaced_image)
        self.display_frame(f)


    def event_reload_frame(self):
        # log.info("refresh frame %d" % (self.current_frame_index + self.playing_frame_start_no))
        f = self.model.get_frame(self.current_frame_index + self.playing_frame_start_no,
            original=not self.do_display_replaced_image)
        # self.widget_controls.refresh_frame_replace_no(f['replaced_by'])
        self.display_frame(f)


    # def event_shot_changed(self):
    #     # Get current shot settings to update the UI
    #     details = self.model.get_current_shot_parameters(['stitching', 'stabilize'])
    #     if details is not None:
    #         self.widget_stitching_curves.load_curves(details['stitching']['curves'])



    def flush_image(self):
        log.info("flush image")
        del self.image
        self.image = None

        del self.image_bgd
        self.image_bgd = None

        gc.collect()

        self.is_grabbing_split_line = False

        if self.is_repainting:
            log.error("error: flush while repainting")
        self.is_repainting = False



    def event_cache_is_ready(self):
        if not self.timer.isActive():
            self.is_cache_ready = True
            speed = self.widget_controls.get_playing_speed()
            self.timer_delay = int(1000/(FPS*speed))
            self.timer.start(self.timer_delay, self)
            self.now = time.time()

    def event_control_button_pressed(self, action):
        if action == 'play':
            self.widget_selection.set_enabled(False)
            log.info("start playing")
            print("start playing")
            if self.is_cache_ready:
                self.event_cache_is_ready()
            else:
                self.signal_generate_cache.emit([self.model.get_preview_options(), self.current_frame_index])
            return True

        elif action == 'pause':
            self.timer.stop()
            self.widget_selection.set_enabled(True)

        elif action == 'stop':
            self.timer.stop()
            self.widget_selection.set_enabled(True)
            self.event_move_to_frame_no(0)


    def event_st_enabled_changed(self):
        log.info("stitching/stabilization enabled state changed, update crop widget")
        log.info("stitching state: %s" % ('true' if self.widget_stitching.is_enabled() else 'false'))
        log.info("stabilization state: %s" % ('true' if self.widget_stabilize.is_enabled() else 'false'))

        if (self.widget_stitching.is_enabled()
            or self.widget_stabilize.is_enabled()):
            self.widget_geometry.set_edition_mode('st')
        else:
            self.widget_geometry.set_edition_mode('final')


    def event_preview_options_changed(self):
        log.info("change preview: editor: %s" % (self.current_editor))
        print("\nchange preview: editor: %s" % (self.current_editor))
        preview_options = {
            'stitching': self.widget_stitching.get_preview_options(),
            'stitching_curves': self.widget_stitching_curves.get_preview_options(),
            'stabilize': self.widget_stabilize.get_preview_options(),
            'geometry': self.widget_geometry.get_preview_options(),
        }

        if self.current_editor == 'stitching':
            if preview_options['stitching']['crop_edition']:
                print("edit fgd crop")
            elif preview_options['stitching']['roi_edition']:
                print("edit fgd roi")
        elif self.current_editor == 'stitching_curves':
            print("edit fgd curves")

        elif self.current_editor == 'stabilize':
            print("edit stabilization")

        elif self.current_editor == 'geometry':
            print("edit crop and resize")
                #

        self.signal_preview_options_changed.emit(preview_options)




    def event_upper_lower_preview_changed(self, side:str):
        self.show_side = side
        self.repaint()


    def event_crop_enabled(self, side:str):
        self.show_side = side
        if not self.timer.isActive() and self.current_frame_index!= -1:
            self.event_refresh_frame()
        # if side == 'top':
            # change view to see the upper part of the image when the screen size is < image size
        # elif side == 'bottom':
            # change view to see the lower part of the image when the screen size is < image size


    def timerEvent(self, e=None):
        now = time.time()
        print("elapsed:", int(1000 * (now - self.now)))
        self.now = now

        self.current_frame_index += 1
        if self.current_frame_index >= self.playing_frame_count:
            self.timer.stop()
            self.widget_controls.event_stop()
        else:
            self.widget_controls.set_playing_frame_properties(self.current_frame_index)
            f = self.model.get_frame(self.current_frame_index + self.playing_frame_start_no,
                original=not self.do_display_replaced_image)
            # if f['cache'] is None:
            #     print("regenerate cache")
            self.display_frame(f)



    def event_right_click(self, qpoint):
        cursor_position = QCursor.pos()
        pop_menu = QMenu(self)
        pop_menu.setStyleSheet("background-color: rgb(128, 128, 128);")
        action_exit = pop_menu.addAction('Exit')
        action_exit.triggered.connect(self.event_close)
        pop_menu.exec_(cursor_position)



    def wheelEvent(self, event):
        # print("window_main: wheel event, forward to widget_control")
        self.widget_controls.wheelEvent(event)


    def keyReleaseEvent(self, event):
        return self.widget_controls.keyReleaseEvent(event)

    def keyPressEvent(self, event):
        key = event.key()
        modifier = event.modifiers()

        if modifier & Qt.ControlModifier:
            if key == Qt.Key_S:
                log.info("key event: save modifications")
                self.signal_save_modifications.emit(True)
                event.accept()
                return True


    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.ActivationChange:
            if self.isActiveWindow():
                self.event_activated()
                event.accept()
                return True
        elif event.type() == QEvent.WindowStateChange:
            if self.windowState() & Qt.WindowFullScreen:
                # From minimized to normal
                self.event_show_fullscreen()
            event.accept()
            return True
        return super().changeEvent(event)



    def display_frame(self, frame: dict):
        if frame is None:
            self.flush_image()
        else:

            # Foreground image
            if self.image is not None:
                del self.image
                self.image = None

            self.image = {
                # position and dimension
                'x': 0,
                'y': 0,
                'w': 0,
                'h': 0,
                # geometry: crop and resize
                'geometry': frame['geometry'],
                'curves': {
                    'lut': None
                },
                # 'stitching': frame['stitching'],
                # 'shot_stitching': frame['shot_stitching'],
                'stabilize': frame['stabilize'],
            }

            if frame['curves'] is not None and self.do_display_rgb_image:
                self.image['curves']['lut'] = frame['curves']['lut']


            # Background image
            if self.image_bgd is not None:
                del self.image_bgd
                self.image_bgd = None
            self.image_bgd = {
                # position and dimension
                'x': 0,
                'y': 0,
                'w': 0,
                'h': 0,
                'curves': {
                    'lut': None
                },
            }

            # self.image['img'] = cv2.imread(frame['filepath'], cv2.IMREAD_COLOR)
            self.image['cache_fgd'] = frame['cache_fgd']
            if frame['cache'] is not None:
                self.image['cache'] = frame['cache']
            else:
                # self.image_bgd['img_bgd'] = cv2.imread(frame['filepath_bgd'], cv2.IMREAD_COLOR)
                self.image['cache'] = None


            # Global variables
            self.setMinimumWidth(1920)

            if frame['reload_parameters']:
                parameters = self.model.get_current_shot_parameters(['stitching', 'stabilize'])
                if parameters is not None:
                    self.widget_stitching_curves.load_curves(parameters['stitching']['curves'])
                    self.widget_stabilize.set_parameters(parameters['stabilize'])
                    self.widget_stitching.set_parameters(parameters['stitching']['parameters'])
                    self.widget_stitching.set_crop(parameters['stitching']['fgd_crop'])

            self.is_repainting = False
        self.repaint()



    def paintEvent(self, event):
        print("paint")
        # log.info("repainting")
        if self.image is None:
            log.info("no image loaded")
            return

        if self.is_repainting:
            log.error("error: self.is_repainting is True!!")
            return
        self.is_repainting = True

        # display: x0, y0
        display_x0 = 10
        display_y0 = 10

        preview_options = self.model.get_preview_options()

        self.do_display_stitching_roi = False
        self.do_display_crop_for_stitching = False
        self.do_display_crop_rect_for_stitching = False
        self.do_display_stabilized = False
        self.do_display_initial = False
        self.do_display_fgd_cropped = False

        if (self.image['cache'] is not None
            and not self.do_display_initial
            and not self.do_display_crop_rect_for_stitching
            and not self.do_display_crop_for_stitching
            and preview_options != 'fgd_crop_edition'):
            # print("paintEvent: use cached img")
            image_fgd = self.image['cache']
            is_cached = True
        else:
            image_fgd = self.image['cache_fgd']
            is_cached = False
        height_fgd, width_fgd, channels_count = image_fgd.shape
        if self.show_side == 'top':
            delta_y = 0
        elif self.show_side == 'bottom':
            delta_y = display_y0 + height_fgd - 1080 + 50


        hist = None

        if self.painter.begin(self):

            if preview_options == 'initial' or is_cached:
                # print("paintEvent: display cached image")
                qImage_fgd = QImage(image_fgd.data, image_fgd.shape[1], image_fgd.shape[0], image_fgd.shape[1] * 3, QImage.Format_BGR888)
                self.painter.drawImage(QPoint(display_x0, display_y0 - delta_y), qImage_fgd)

            elif self.model.get_preview_options() == 'fgd_crop_edition':
                f = self.model.get_current_frame()
                # pprint(f)
                crop_fgd_top, crop_fgd_bottom, crop_fgd_left, crop_fgd_right = f['stitching']['geometry']['fgd']
                roi_width = width_fgd - (crop_fgd_right + crop_fgd_left)
                roi_height = height_fgd - (crop_fgd_bottom + crop_fgd_top)

                if True:
                    # Do display a rect
                    qImage_fgd = QImage(image_fgd.data, image_fgd.shape[1], image_fgd.shape[0], image_fgd.shape[1] * 3, QImage.Format_BGR888)
                    self.painter.drawImage(QPoint(display_x0, display_y0 - delta_y), qImage_fgd)

                    pen = QPen(COLOR_STITCHING_FGD_CROP_RECT)
                    pen.setWidth(PEN_CROP_SIZE)
                    pen.setStyle(Qt.SolidLine)
                    self.painter.setPen(pen)
                    self.painter.drawRect(
                        display_x0 + crop_fgd_left, display_y0 + crop_fgd_top - delta_y,
                        roi_width, roi_height)
                else:
                    # Do display a cropped image whish is the roi for stiching
                    image_cropped = np.ascontiguousarray(image_fgd[
                        roi_top:roi_top+crop_height,
                        roi_left:roi_left+roi_width], dtype=np.uint8)

                    qImage_fgd = QImage(image_cropped.data, image_cropped.shape[1], image_cropped.shape[0], image_cropped.shape[1] * 3, QImage.Format_BGR888)
                    self.painter.drawImage(QPoint(display_x0 + roi_left, display_y0 + roi_top - delta_y), qImage_fgd)


            elif self.model.get_preview_options() == 'stitching':
                print_time = False
                if print_time:
                    initial_time = time.time()

                f = self.model.get_current_frame()
                if f is not None:
                    (no, image_fgd, hist) = process_single_frame(f,
                        preview_options='stitching',
                        bgd_curve_luts=self.widget_stitching_curves.get_curve_luts(),
                        current_channel=self.widget_stitching_curves.get_current_channel())
                    # self.model.set_current_frame_cache(image_fgd)

                    qImage_fgd = QImage(image_fgd.data, image_fgd.shape[1], image_fgd.shape[0], image_fgd.shape[1] * 3, QImage.Format_BGR888)
                    self.painter.drawImage(QPoint(display_x0, display_y0 - delta_y), qImage_fgd)

                if print_time:
                    print("\t->: %.1f" % (1000* (time.time() - initial_time)))


            elif preview_options == 'stabilized':
                f = self.model.get_current_frame()
                if f is not None:
                    (no, image_fgd, hist) = process_single_frame(f, preview_options=preview_options)
                    # self.model.set_current_frame_cache(image_fgd)

                    qImage_fgd = QImage(image_fgd.data, image_fgd.shape[1], image_fgd.shape[0], image_fgd.shape[1] * 3, QImage.Format_BGR888)
                    self.painter.drawImage(QPoint(display_x0, display_y0 - delta_y), qImage_fgd)


            elif self.model.get_preview_options() == 'fgd_cropped':
                f = self.model.get_current_frame()
                if f is not None:
                    (no, image_fgd_cropped, hist) = process_single_frame(f, preview_options='fgd_cropped')
                    self.model.set_current_frame_cache(image_fgd_cropped)

                    if self.show_side == 'top':
                        delta_y = 0
                    elif self.show_side == 'bottom':
                        delta_y = display_y0 + image_fgd_cropped.shape[0] - 1080 + 50

                    qImage_fgd_cropped = QImage(image_fgd_cropped.data, image_fgd_cropped.shape[1], image_fgd_cropped.shape[0], image_fgd_cropped.shape[1] * 3, QImage.Format_BGR888)
                    self.painter.drawImage(QPoint(display_x0, display_y0 - delta_y), qImage_fgd_cropped)




            # elif self.model.get_preview_options() in ['fgd_cropped', 'fgd_roi_edition']:
            #     f = self.model.get_current_frame()
            #     if f is not None:
            #         (no, image_fgd_cropped, hist) = process_single_frame(-1, f, preview_options='fgd_cropped')
            #         self.model.set_current_frame_cache(image_fgd_cropped)

            #         qImage_fgd_cropped = QImage(image_fgd_cropped.data, image_fgd_cropped.shape[1], image_fgd_cropped.shape[0], image_fgd_cropped.shape[1] * 3, QImage.Format_BGR888)
            #         self.painter.drawImage(QPoint(display_x0, display_y0 - delta_y), qImage_fgd_cropped)



            if self.do_display_rect_for_stitching:
                # Draw a rect used for detection points stitching
                stitching_area_fgd_left = 30
                stitching_area_fgd_right = 25
                stitching_area_fgd_top = 15
                stitching_area_fgd_down = 10
                stitching_area_fgd_width = width_fgd - stitching_area_fgd_left - stitching_area_fgd_right
                stitching_area_fgd_height = height_fgd - stitching_area_fgd_top - stitching_area_fgd_down


                # Draw the rect
                pen = QPen(COLOR_STITCHING_AREA_RECT)
                pen.setWidth(PEN_CROP_SIZE)
                pen.setStyle(Qt.SolidLine)
                self.painter.setPen(pen)
                self.painter.drawRect(
                    display_x0 + stitching_area_fgd_left, display_y0 + stitching_area_fgd_top - delta_y,
                    stitching_area_fgd_width, stitching_area_fgd_height)

            elif self.do_display_crop_for_stitching:
                # Draw a rect/cropped image used for detection points stitching

                # print(self.image['stitching'])
                # print(self.image['shot_stitching'])
                if not is_cached:
                    fgd_crop_list = self.image['shot_stitching']['fgd_crop']
                    fgd_crop_x0 = fgd_crop_list[0]
                    fgd_crop_y0 = fgd_crop_list[1]
                    fgd_crop_w = width_fgd - (fgd_crop_list[2] + fgd_crop_x0)
                    fgd_crop_h = height_fgd - (fgd_crop_list[3] + fgd_crop_y0)


                    # 1. Generate the translated image
                    pad_w_l = 40
                    pad_w_r = 20
                    pad_h = 80
                    pad_h_b = 20

                    #   1.1. Add padding to the initial image
                    width = width_fgd + 30 + pad_w_l + pad_w_r
                    height = height_fgd + 40+ pad_h + pad_h_b
                    image_fgd_with_borders = cv2.copyMakeBorder(image_fgd,
                        pad_h, pad_h_b,
                        pad_w_l, pad_w_r,
                        cv2.BORDER_CONSTANT,
                        value=[0, 0, 0])

                    # cv2.imwrite("test.png", image_fgd_with_borders)


                    # print("image_fgd_with_borders: %dx%d" % (image_fgd_with_borders.shape[1], image_fgd_with_borders.shape[0]))

                    #   1.2. Generate a stabilized image
                    transformation_matrix = np.float32([
                        [1, 0, self.image['stitching']['T']['dx']],
                        [0, 1, self.image['stitching']['T']['dy']]
                    ])
                    # transformation_matrix = np.float32([
                    #     [1, 0, 0],
                    #     [0, 1, 0]
                    # ])

                    img_fgd_stabilized = cv2.warpAffine(
                        image_fgd_with_borders,
                        transformation_matrix,
                        (width, height),
                        flags=cv2.INTER_LANCZOS4,
                        borderMode=cv2.BORDER_CONSTANT,
                        borderValue=(0,0,0))

                # 2. Draw rect/cropped foreground image
                if self.do_display_crop_rect_for_stitching:
                    # Draw a rect used for detection points stitching
                    # print("display rect")

                    if is_cached:
                        # Draw the original fgd image only
                        # print("qImage_fgd: (%d x %d), delta_y=%d" % (width_fgd, height_fgd, delta_y))
                        qImage_fgd = QImage(image_fgd.data, width_fgd, height_fgd, width_fgd * 3, QImage.Format_BGR888)
                        self.painter.drawImage(QPoint(display_x0, display_y0 - delta_y), qImage_fgd)
                    elif False:
                        # Draw the original fgd image only
                        # print("qImage_fgd: (%d x %d), delta_y=%d" % (width_fgd, height_fgd, delta_y))
                        qImage_fgd = QImage(image_fgd.data, width_fgd, height_fgd, width_fgd * 3, QImage.Format_BGR888)
                        self.painter.drawImage(QPoint(display_x0, display_y0 - delta_y), qImage_fgd)
                    elif False:
                        qImage_fgd_with_borders = QImage(image_fgd_with_borders.data,
                            image_fgd_with_borders.shape[1],
                            image_fgd_with_borders.shape[0],
                            image_fgd_with_borders.shape[1] * 3, QImage.Format_BGR888)
                        self.painter.drawImage(QPoint(display_x0, display_y0 - delta_y), qImage_fgd_with_borders)
                    else:
                        qImage_fgd_stabilized = QImage(img_fgd_stabilized.data,
                            img_fgd_stabilized.shape[1],
                            img_fgd_stabilized.shape[0],
                            img_fgd_stabilized.shape[1] * 3, QImage.Format_BGR888)
                        self.painter.drawImage(QPoint(display_x0, display_y0 - delta_y), qImage_fgd_stabilized)

                    # Draw the rect
                    # pen = QPen(COLOR_STITCHING_FGD_CROP_RECT)
                    # pen.setWidth(PEN_CROP_SIZE)
                    # pen.setStyle(Qt.SolidLine)
                    # self.painter.setPen(pen)
                    # self.painter.drawRect(
                    #     display_x0 + fgd_crop_x0, display_y0 + fgd_crop_y0 - delta_y,
                    #     fgd_crop_w, fgd_crop_h)
                else:
                    # Display the cropped image for detection points stitching
                    print("display cropped")

            # else:
            #     print("nothing to paint")

            self.painter.end()
            self.setFocus()
        self.is_repainting = False

        self.widget_stitching_curves.display(hist)

