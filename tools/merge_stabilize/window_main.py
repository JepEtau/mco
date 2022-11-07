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
    Qt,
    QPoint,
    Signal,
)
from PySide6.QtGui import (
    QColor,
    QImage,
    QPen,
)

from utils.common import FPS

from common.window_common import Window_common
from common.widget_controls import Widget_controls

from merge_stabilize.model_merge_stabilize import Model_merge_stabilize
from merge_stabilize.model_merge_stabilize import process_single_frame

from merge_stabilize.widget_selection import Widget_selection
from merge_stabilize.widget_stitching_curves import Widget_stitching_curves
from merge_stabilize.widget_stitching import Widget_stitching
from merge_stabilize.widget_stabilize import Widget_stabilize
from merge_stabilize.widget_geometry import Widget_geometry


COLOR_CROP_RECT = QColor(250, 50, 50)
COLOR_STITCHING_AREA_RECT = QColor(50, 255, 50)
COLOR_STITCHING_FGD_CROP_RECT = QColor(255, 50, 50)
PEN_CROP_SIZE = 1


class Window_main(Window_common):
    signal_preview_options_changed = Signal(dict)
    signal_save_and_close = Signal()

    signal_generate_cache = Signal(list)
    signal_save_modifications = Signal(bool)


    def __init__(self, model:Model_merge_stabilize):
        super(Window_main, self).__init__(self, model)

        # Internal variables
        self.image_bgd = None
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
            self.widget_stitching_curves.widget_hist_curves.signal_curves_editing.connect(self.event_refresh_image)

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
        self.widget_selection.signal_ep_or_part_selection_changed[dict].connect(self.event_selection_changed)
        self.widget_selection.set_initial_options(p)
        self.widget_selection.widget_app_controls.signal_action[str].connect(self.event_editor_action)

        # Events
        self.model.signal_ready_to_play[dict].connect(self.event_ready_to_play)
        self.model.signal_reload_frame.connect(self.event_reload_frame)
        self.model.signal_cache_is_ready.connect(self.event_cache_is_ready)
        self.model.signal_refresh_image.connect(self.event_refresh_image)

        # Show window/widgets and connect signals
        for w in self.widgets.values():
            w.signal_close.connect(self.event_editor_action)
            w.show()

        # Set initial values
        self.set_initial_options(p)
        self.event_show_fullscreen()



    def event_refresh_image(self):
        self.repaint()


    def event_stitching_curves_channel_selected(self):
        # todo: flush current cache image
        print("event_stitching_curves_channel_selected")
        self.repaint()





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
        preview_options = dict()
        for e, w in self.widgets.items():
            preview_options.update({e: w.get_preview_options()})

        # TODO: add pushbuttons for curves/replace
        preview_options.update({
            'replace': {'is_enabled': False},
            'curves': {'is_enabled': False},
        })
        pprint(preview_options)
        self.signal_preview_options_changed.emit(preview_options)




    def event_preview_options_changed(self):
        log.info("change preview: editor: %s" % (self.current_editor))
        print("\nchange preview: editor: %s" % (self.current_editor))
        preview_options = {
            'stitching': self.widget_stitching.get_preview_options(),
            'stitching_curves': self.widget_stitching_curves.get_preview_options(),
            'stabilize': self.widget_stabilize.get_preview_options(),
            'geometry': self.widget_geometry.get_preview_options(),
        }

        self.signal_preview_options_changed.emit(preview_options)


    def event_crop_enabled(self, side:str):
        self.show_side = side
        if not self.timer.isActive() and self.current_frame_index!= -1:
            self.event_refresh_frame()
        # if side == 'top':
            # change view to see the upper part of the image when the screen size is < image size
        # elif side == 'bottom':
            # change view to see the lower part of the image when the screen size is < image size



    def wheelEvent(self, event):
        # print("window_main: wheel event, forward to widget_control")
        self.widget_controls.wheelEvent(event)



    def keyPressEvent(self, event):
        key = event.key()
        modifiers = event.modifiers()


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

        for e, w in self.widgets.items():
            if self.current_editor == e:
                is_accepted = w.event_key_pressed(event)
                if is_accepted:
                    event.accept()
                    return True

        event.accept()
        return True


    def keyReleaseEvent(self, event):
        self.widget_controls.event_key_released(event)

        # Forward to current widget

        if self.widget_controls.event_key_released(event):
            event.accept()
            return True







    def display_frame(self, frame: dict):
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

            # Update info in the other widgets
            # for e, w in self.widgets.items():
            #     w.refresh_values(frame)

            if frame['reload_parameters']:
                # TODO: replace by values provided in frame
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

