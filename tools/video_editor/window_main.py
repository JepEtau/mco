# -*- coding: utf-8 -*-
import sys
sys.path.append('../scripts')

from utils.pretty_print import *

from functools import partial
import gc
import time
import os

from pprint import pprint
from logger import log

from PySide6.QtCore import (
    QPoint,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QColor,
    QImage,
    QPen,
)
from common.window_common import (
    Window_common,
    PAINTER_MARGIN_LEFT,
    PAINTER_MARGIN_TOP,
)
from filters.deshakers import STABILIZE_BORDER_HIGH_RES
from filters.utils import (
    FINAL_FRAME_HEIGHT,
    FINAL_FRAME_WIDTH,
    get_dimensions_from_crop_values,
)
from common.widget_controls import Widget_controls
from video_editor.widget_selection import Widget_selection
from video_editor.widget_curves import Widget_curves
from video_editor.widget_replace import Widget_replace
from video_editor.widget_geometry import Widget_geometry
from video_editor.widget_stabilize import Widget_stabilize

from video_editor.controller import Controller_video_editor


COLOR_PART_CROP_RECT = QColor(30, 230, 30)
COLOR_CROP_RECT = QColor(230, 30, 30)
COLOR_FINAL_RECT = QColor(0, 255, 0)
COLOR_DISPLAY_RECT = QColor(255, 255, 255)
# PEN_CROP_SIZE must be equal to 1 or 2
PEN_CROP_SIZE = 1


class Window_main(Window_common):
    signal_preview_options_changed = Signal(dict)
    signal_save_and_close = Signal()


    def __init__(self, controller:Controller_video_editor):
        super(Window_main, self).__init__(self, controller)
        # Get preferences from model
        p = self.controller.get_preferences()

        # RGB Curves
        if 'curves' in self.widgets.keys():
            self.widget_curves = Widget_curves(self, self.controller)
            self.widgets['curves'] = self.widget_curves
            self.widget_curves.set_initial_options(p)
            self.widget_curves.set_main_window_margin(PAINTER_MARGIN_LEFT)
            self.widget_curves.signal_preview_options_changed.connect(partial(self.event_preview_options_changed, 'curves'))

        # Replace frames
        if 'replace' in self.widgets.keys():
            self.widget_replace = Widget_replace(self, self.controller)
            self.widgets['replace'] = self.widget_replace
            self.widget_replace.set_initial_options(p)
            self.widget_replace.signal_preview_options_changed.connect(partial(self.event_preview_options_changed, 'replace'))
            self.widget_replace.signal_frame_selected[int].connect(self.event_move_to_frame_no)

        # Geometry: crop and resize
        if 'geometry' in self.widgets.keys():
            self.widget_geometry = Widget_geometry(self, self.controller)
            self.widgets['geometry'] = self.widget_geometry
            self.widget_geometry.set_initial_options(p)
            self.widget_geometry.signal_preview_options_changed.connect(partial(self.event_preview_options_changed, 'geometry'))
            if self.display_height <= 1080:
                self.widget_geometry.signal_position_changed[str].connect(self.event_screen_position_changed)

        # Stabilize
        if 'stabilize' in self.widgets.keys():
            self.widget_stabilize = Widget_stabilize(self, self.controller)
            self.widgets['stabilize'] = self.widget_stabilize
            self.widget_stabilize.set_initial_options(p)
            self.widget_stabilize.signal_preview_options_changed.connect(partial(self.event_preview_options_changed, 'stabilize'))
            self.widget_stabilize.signal_frame_selected[int].connect(self.event_move_to_frame_no)
            self.widget_stabilize.signal_show_guidelines_changed[bool].connect(self.event_show_guidelines_changed)
        self.show_guidelines = False

        # Player controls
        if 'controls' in self.widgets.keys():
            self.widget_controls = Widget_controls(self, self.controller)
            self.widgets['controls'] = self.widget_controls
            self.widget_controls.set_initial_options(p)
            self.widget_controls.signal_button_pushed[str].connect(self.event_control_button_pressed)
            self.widget_controls.signal_slider_moved[int].connect(self.event_move_to_frame_index)
            self.widget_controls.signal_preview_options_changed.connect(partial(self.event_preview_options_changed, 'controls'))

        # Selection of episode/part/shot
        self.widget_selection = Widget_selection(self, self.controller)
        self.widgets['selection'] = self.widget_selection
        self.widget_selection.refresh_browsing_folder(self.controller.get_available_episode_and_parts())
        self.widget_selection.signal_selection_changed[dict].connect(self.event_selection_changed)
        self.widget_selection.set_initial_options(p)
        self.widget_selection.widget_app_controls.signal_action[str].connect(self.event_editor_action)
        self.widget_selection.signal_selected_shots_changed[dict].connect(self.event_selected_shots_changed)

        # Controller
        self.controller.signal_ready_to_play[dict].connect(self.event_ready_to_play)
        self.controller.signal_reload_frame.connect(self.event_reload_frame)
        self.controller.signal_close.connect(self.event_close_without_saving)
        self.controller.signal_preview_options_consolidated.connect(self.event_preview_options_consolidated)

        # Show window/widgets and connect signals
        for w in self.widgets.values():
            w.signal_close.connect(self.event_editor_action)
            w.show()

        # Set initial values
        self.set_initial_options(p)
        self.event_show_fullscreen()



    def get_preview_options(self):
        log.info("get preview options")
        preview_options = dict()
        for e, w in self.widgets.items():
            preview_options.update({e: w.get_preview_options()})
        return preview_options


    def event_preview_options_consolidated(self, new_preview_settings):
        log.info("preview options have been consolidated, refresh widgets")
        self.widget_replace.refresh_preview_options(new_preview_settings)
        self.widget_stabilize.refresh_preview_options(new_preview_settings)
        self.widget_geometry.refresh_preview_options(new_preview_settings)



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
            options = self.controller.get_preview_options()
            if options is None:
                sys.exit("preview options are not set!")

            # Set an internal image object
            self.image = {
                'cache': frame['cache'],
                'geometry': frame['geometry'],
                'geometry_values': frame['geometry_values'],
                'curves': {
                    'lut': None
                },
                'preview_options': options,
            }

            if options['stabilize']['enabled'] and frame['stabilize']['enable']:
                self.image['cache_initial'] = frame['cache_deshake']
            else:
                self.image['cache_initial'] = frame['cache_initial']


            # Update info in the other widgets
            for e, w in self.widgets.items():
                w.refresh_values(frame)

        self.repaint()
        # print("\t\t%f" % int(1000 * (time.time() - now)))


    def event_show_guidelines_changed(self, enabled):
        self.show_guidelines = enabled
        self.repaint()


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
                    bgr = self.image['cache_initial'][yr-self.image['origin'][1], xr-self.image['origin'][0]]
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



    def mousePressEvent(self, event):
        x = event.x()
        y = event.y()

        if (self.image is not None
        and self.image['cache_initial'] is not None):
            if self.current_editor == 'curves':
                if self.widget_curves.grab_split_line(x):
                    self.setCursor(Qt.SplitHCursor)
                else:
                    print("\t-> cache_initial: ", self.image['cache_initial'].shape)
                    self.get_rgb_value(x, y)
                event.accept()
                return True
            elif self.current_editor == 'stabilize':
                line = self.widget_stabilize.grab_guidelines(x, y)
                if line == 'vertical':
                    self.setCursor(Qt.SplitHCursor)
                elif line == 'horizontal':
                    self.setCursor(Qt.SplitVCursor)
                elif line == "both":
                    self.setCursor(Qt.SizeAllCursor)
                else:
                    self.get_rgb_value(x, y)
                if line is not None:
                    self.repaint()
                event.accept()
                return True
            else:
                print("\t-> cache_initial: ", self.image['cache_initial'].shape)
                self.get_rgb_value(x, y)
            event.accept()
        else:
            event.ignore()


    def mouseMoveEvent(self, event):
        x = event.x()
        y = event.y()
        if self.current_editor == 'stabilize':
            line = self.widget_stabilize.move_guidelines(x, y)
            if line is None:
                self.get_rgb_value(x, y)
                event.ignore()
                return
            if line == 'vertical':
                self.setCursor(Qt.SplitHCursor)
            elif line == 'horizontal':
                self.setCursor(Qt.SplitVCursor)
            elif line == "both":
                self.setCursor(Qt.SizeAllCursor)
            event.accept()
            if line is not None:
                self.repaint()


        elif self.current_editor == 'curves':
            if self.widget_curves.move_split_line(x):
                self.setCursor(Qt.SplitHCursor)
                event.accept()
                self.event_reload_frame()
            else:
                self.get_rgb_value(x, y)
                event.ignore()


    def mouseMoved(self, x, y):
        if self.current_editor == 'curves':
            if self.widget_curves.split_line_moved(x, self.mouse_grabX):
                self.setCursor(Qt.SplitHCursor)
                self.event_reload_frame()

        elif self.current_editor == 'stabilize':
            line = self.widget_stabilize.guidelines_moved(x, self.mouse_grabX, y, self.mouse_grabY)
            if line == 'vertical':
                self.setCursor(Qt.SplitHCursor)
            elif line == 'horizontal':
                self.setCursor(Qt.SplitVCursor)
            elif line == "both":
                self.setCursor(Qt.SizeAllCursor)
            else:
                self.get_rgb_value(x, y)
            if line is not None:
                self.repaint()


    def mouseReleaseEvent(self, event):
        self.setCursor(Qt.ArrowCursor)
        self.widget_curves.split_line_released(event.x())
        self.widget_stabilize.guidelines_released(event.x(), event.y())
        self.repaint()

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
            elif key == Qt.Key_S:
                self.switch_display_side()
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
            # print("forwarded to controls", key)
            event.accept()
            return True

        event.accept()
        return True


    def keyReleaseEvent(self, event):
        # print_yellow(f"keyReleaseEvent: {event.key()}")
        for w in self.widgets.values():
            w.event_key_released(event)

        self.widget_controls.event_key_released(event)
        event.accept()
        return True
        # return self.widget_controls.keyReleaseEvent(event)




    def paintEvent(self, event):
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
        delta_y = self.display_position_y

        preview = self.image['preview_options']
        # print_lightgreen("paintEvent: preview")
        # pprint(preview)
        initial_img_height, initial_img_width, c = self.image['cache_initial'].shape
        # print("paintEvent: initial image = %dx%d" % (initial_img_height, initial_img_width))
        img_height, img_width, c = img.shape
        q_image = QImage(img.data, img_width, img_height, img_width * 3, QImage.Format_BGR888)

        # Shot geometry
        geometry = self.image['geometry']
        shot_geometry = geometry['shot']
        if shot_geometry is None and 'default' in geometry.keys():
            shot_geometry = geometry['default']


        self.image['origin'] = [PAINTER_MARGIN_LEFT, PAINTER_MARGIN_TOP - delta_y]
        if self.painter.begin(self):

            if preview['geometry']['final_preview']:
                # print("paintEvent: display final_preview")
                self.painter.drawImage(
                    QPoint(PAINTER_MARGIN_LEFT, PAINTER_MARGIN_TOP - delta_y), q_image)
            else:
                preview_shot_geometry = preview['geometry']['shot']

                if preview_shot_geometry['crop_edition'] and not preview_shot_geometry['crop_preview']:
                    # Crop editon: rectangle but no preview

                    if preview_shot_geometry['resize_preview']:
                        # Crop editon: rectangle + resize
                        # Draw rect on the resized image
                        x0 = PAINTER_MARGIN_LEFT
                        y0 = PAINTER_MARGIN_TOP - delta_y

                        # Patch the crop value if displaying deshaked shot
                        crop = shot_geometry['crop']
                        if preview['stabilize']['enabled']:
                            crop = list(map(lambda x: x + STABILIZE_BORDER_HIGH_RES, shot_geometry['crop']))

                        # Image is resized, add the recalculated crop
                        crop_top, crop_bottom, crop_left, crop_right, cropped_width, cropped_height = get_dimensions_from_crop_values(
                            width=initial_img_width, height=initial_img_height, crop=crop)
                        w_tmp = int((cropped_width * FINAL_FRAME_HEIGHT) / float(cropped_height))
                        pad_left = int(((FINAL_FRAME_WIDTH - w_tmp) / 2)+0.5)
                        crop_left = int((crop_left * FINAL_FRAME_HEIGHT) / float(cropped_height))
                        crop_top = int((crop_top * FINAL_FRAME_HEIGHT) / float(cropped_height))

                        # print("\t-> w=%d, c_w=%d, w_tmp=%d, pad: %d" % (w, c_w, w_tmp, pad_left))
                        # print("\t-> crop_left=%d, crop_top=%d" % (c_l, crop_top))

                        self.image['origin'] = [x0 + pad_left - crop_left, y0 - crop_top]

                        self.painter.drawImage(
                            QPoint(x0 + pad_left - crop_left, y0 - crop_top),
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
                            FINAL_FRAME_HEIGHT + 1)

                        # Add the final 1080p rect
                        pen = QPen(COLOR_DISPLAY_RECT)
                        pen.setWidth(PEN_CROP_SIZE)
                        pen.setStyle(Qt.SolidLine)
                        self.painter.setPen(pen)
                        self.painter.drawRect(
                            PAINTER_MARGIN_LEFT - 1,
                            PAINTER_MARGIN_LEFT - delta_y - 1,
                            FINAL_FRAME_WIDTH + 1,
                            FINAL_FRAME_HEIGHT + 1)

                    else:
                        # print("paintEvent: draw rect crop on the original image")
                        # Original
                        x0 = PAINTER_MARGIN_LEFT
                        y0 = PAINTER_MARGIN_TOP - delta_y
                        crop = shot_geometry['crop']
                        if preview['stabilize']['enabled']:
                            crop = list(map(lambda x: x + STABILIZE_BORDER_HIGH_RES, shot_geometry['crop']))
                        self.painter.drawImage(QPoint(x0, y0), q_image)

                        # Add a red rect for the crop
                        crop_top, crop_bottom, crop_left, crop_right, cropped_width, cropped_height = get_dimensions_from_crop_values(
                            width=initial_img_width, height=initial_img_height, crop=crop)

                        pen = QPen(COLOR_CROP_RECT)
                        pen.setWidth(PEN_CROP_SIZE)
                        pen.setStyle(Qt.SolidLine)
                        self.painter.setPen(pen)
                        # https://doc.qt.io/qt-6/qrect.html, PEN_CROP_SIZE = 1
                        # print("\timg: %dx%d" % (img.data.shape[1], img.data.shape[0]))
                        # print("\trect: (%d;%d) w=%d, h=%d" % (c_l - 1, c_t - delta_y - 1, c_w + 1, c_h + 1))



                        self.painter.drawRect(
                            PAINTER_MARGIN_LEFT + crop_left - 1,
                            PAINTER_MARGIN_LEFT + crop_top - delta_y - 1,
                            cropped_width + 1,
                            cropped_height + 1)

                elif preview_shot_geometry['crop_preview']:
                    if preview_shot_geometry['resize_preview']:
                        # print("paintEvent: draw cropped image and resized")
                        crop_top, crop_bottom, crop_left, crop_right, cropped_width, cropped_height = get_dimensions_from_crop_values(
                            width=initial_img_width, height=initial_img_height, crop=shot_geometry['crop'])

                        w_tmp = int((cropped_width * FINAL_FRAME_HEIGHT) / float(cropped_height))
                        pad_left = int(((FINAL_FRAME_WIDTH - img_width) / 2) + 0.5)
                        # print("paintEvent: pad=%d" % (pad_left))

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
                            FINAL_FRAME_WIDTH + 1,
                            FINAL_FRAME_HEIGHT + 1)
                    else:
                        # print("paintEvent: draw cropped image on the original image")
                        # Crop and no rect
                        crop = shot_geometry['crop']
                        if preview['stabilize']['enabled']:
                            crop = list(map(lambda x: x + STABILIZE_BORDER_HIGH_RES, shot_geometry['crop']))
                        crop_top, crop_bottom, crop_left, crop_right, cropped_width, cropped_height = get_dimensions_from_crop_values(
                            width=initial_img_width, height=initial_img_height, crop=crop)

                        self.painter.drawImage(
                            QPoint(PAINTER_MARGIN_LEFT + crop_left,
                                PAINTER_MARGIN_TOP + crop_top - delta_y),
                            q_image)

                else:
                    # original
                    # print("paintEvent: draw original image")
                    self.painter.drawImage(
                        QPoint(PAINTER_MARGIN_LEFT, PAINTER_MARGIN_TOP - delta_y), q_image)

                if (preview['geometry']['target']['width_edition']
                    and preview_shot_geometry['crop_edition']
                    and preview_shot_geometry['resize_preview']):

                    # Image is resized, add the recalculated crop
                    crop = shot_geometry['crop']
                    if preview['stabilize']['enabled']:
                        crop = list(map(lambda x: x + STABILIZE_BORDER_HIGH_RES, shot_geometry['crop']))

                    crop_top, crop_bottom, crop_left, crop_right, cropped_width, cropped_height = get_dimensions_from_crop_values(
                            width=initial_img_width, height=initial_img_height, crop=crop)
                    w_tmp = int((cropped_width * FINAL_FRAME_HEIGHT) / float(cropped_height))
                    pad_left = int(((FINAL_FRAME_WIDTH - w_tmp) / 2) + 0.5)
                    # print("\t-> w=%d, c_w=%d, w_tmp=%d, pad: %d" % (w, c_w, w_tmp, pad_left))

                    crop_left = int((crop_left * FINAL_FRAME_HEIGHT) / float(cropped_height))
                    crop_top = int((crop_top * FINAL_FRAME_HEIGHT) / float(cropped_height))

                    final_pad = self.image['geometry_values']['pad']

                    # Add the target rect
                    pen = QPen(COLOR_PART_CROP_RECT)
                    pen.setWidth(PEN_CROP_SIZE)
                    pen.setStyle(Qt.SolidLine)
                    self.painter.setPen(pen)
                    self.painter.drawRect(
                        PAINTER_MARGIN_LEFT + final_pad['left'] - 1,
                        PAINTER_MARGIN_LEFT - delta_y - 1,
                        geometry['target']['w'] + 1,
                        FINAL_FRAME_HEIGHT + 1)

                    # Add the final 1080p rect
                    pen = QPen(COLOR_DISPLAY_RECT)
                    pen.setWidth(PEN_CROP_SIZE)
                    pen.setStyle(Qt.SolidLine)
                    self.painter.setPen(pen)
                    self.painter.drawRect(
                        PAINTER_MARGIN_LEFT - 1,
                        PAINTER_MARGIN_LEFT - delta_y - 1,
                        FINAL_FRAME_WIDTH + 1,
                        FINAL_FRAME_HEIGHT + 1)



            if preview['curves']['split']:
                try: crop_top = 0 if preview_shot_geometry['resize_preview'] else (-1*crop_top)
                except:  crop_top = 0
                pen = QPen(QColor(255,255,255))
                pen.setStyle(Qt.DashLine)
                self.painter.setPen(pen)
                self.painter.drawLine(
                    preview['curves']['split_x'] + PAINTER_MARGIN_LEFT, PAINTER_MARGIN_TOP - crop_top,
                    preview['curves']['split_x'] + PAINTER_MARGIN_LEFT, PAINTER_MARGIN_TOP - crop_top + max(img_height, FINAL_FRAME_HEIGHT))

            if self.show_guidelines:
                x, y = self.widget_stabilize.guidelines_coordinates()

                pen = QPen(QColor(255,255,255))
                pen.setStyle(Qt.SolidLine)
                self.painter.setPen(pen)
                self.painter.drawLine(
                    x, 10,
                    x, 10 + max(img_height, FINAL_FRAME_HEIGHT))

                self.painter.drawLine(
                    10, y,
                    10 + max(img_width, FINAL_FRAME_WIDTH), y)


            self.painter.end()
        self.is_repainting = False
