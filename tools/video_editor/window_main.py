# -*- coding: utf-8 -*-

import sys
sys.path.append('../scripts')

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
from utils.common import get_dimensions_from_crop_values

from common.widget_controls import Widget_controls
from video_editor.widget_selection import Widget_selection
from video_editor.widget_curves import Widget_curves
from video_editor.widget_replace import Widget_replace
from video_editor.widget_geometry import Widget_geometry

from video_editor.model_video_editor import Model_video_editor


COLOR_PART_CROP_RECT = QColor(30, 230, 30)
COLOR_CROP_RECT = QColor(230, 30, 30)
COLOR_FINAL_RECT = QColor(0, 255, 0)
COLOR_DISPLAY_RECT = QColor(255, 255, 255)
# PEN_CROP_SIZE must be equal to 1 or 2
PEN_CROP_SIZE = 1


class Window_main(Window_common):
    signal_preview_options_changed = Signal(dict)
    signal_save_and_close = Signal()


    def __init__(self, model:Model_video_editor):
        super(Window_main, self).__init__(self, model)
        # Get preferences from model
        p = self.model.get_preferences()

        # RGB Curves
        if 'curves' in self.widgets.keys():
            self.widget_curves = Widget_curves(self, self.model)
            self.widgets['curves'] = self.widget_curves
            self.widget_curves.set_initial_options(p)
            self.widget_curves.set_main_window_margin(PAINTER_MARGIN_LEFT)
            self.widget_curves.signal_preview_options_changed.connect(partial(self.event_preview_options_changed, 'curves'))

        # Replace frames
        if 'replace' in self.widgets.keys():
            self.widget_replace = Widget_replace(self, self.model)
            self.widgets['replace'] = self.widget_replace
            self.widget_replace.set_initial_options(p)
            self.widget_replace.signal_preview_options_changed.connect(partial(self.event_preview_options_changed, 'replace'))
            self.widget_replace.signal_frame_selected[dict].connect(self.event_replace_frame_selected)

        # Crop and resize
        if 'geometry' in self.widgets.keys():
            self.widget_geometry = Widget_geometry(self, self.model)
            self.widgets['geometry'] = self.widget_geometry
            self.widget_geometry.set_initial_options(p)
            self.widget_geometry.signal_preview_options_changed.connect(partial(self.event_preview_options_changed, 'geometry'))
            if self.display_height <= 1080:
                self.widget_geometry.signal_position_changed[str].connect(self.event_screen_position_changed)

        # Player controls
        if 'controls' in self.widgets.keys():
            self.widget_controls = Widget_controls(self, self.model)
            self.widgets['controls'] = self.widget_controls
            self.widget_controls.set_initial_options(p)
            self.widget_controls.signal_button_pushed[str].connect(self.event_control_button_pressed)
            self.widget_controls.signal_slider_moved[int].connect(self.event_move_to_frame_no)
            self.widget_controls.signal_preview_options_changed.connect(partial(self.event_preview_options_changed, 'controls'))

        # Selection of episode/part/shot
        self.widget_selection = Widget_selection(self, self.model)
        self.widgets['selection'] = self.widget_selection
        self.widget_selection.refresh_browsing_folder(self.model.get_available_episode_and_parts())
        self.widget_selection.signal_ep_or_part_selection_changed[dict].connect(self.event_selection_changed)
        self.widget_selection.set_initial_options(p)
        self.widget_selection.widget_app_controls.signal_action[str].connect(self.event_editor_action)
        self.widget_selection.signal_selected_shots_changed[dict].connect(self.event_selected_shots_changed)

        # Model
        self.model.signal_ready_to_play[dict].connect(self.event_ready_to_play)
        self.model.signal_reload_frame.connect(self.event_reload_frame)
        self.model.signal_close.connect(self.event_close_without_saving)


        # Show window/widgets and connect signals
        for w in self.widgets.values():
            w.signal_close.connect(self.event_editor_action)
            w.show()

        # Set initial values
        self.set_initial_options(p)
        self.event_show_fullscreen()



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
        key = event.key()
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
        delta_y = self.display_position_y

        options = self.image['preview_options']
        h_i, w_i, c = self.image['cache_fgd'].shape
        # print("paintEvent: initial image = %dx%d" % (h_i, w_i))
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
                type = 'custom' if self.image['geometry']['custom'] is not None else 'part'
                # print("paintEvent: type = %s" % (type))
                geometry_options = options['geometry'][type]

                if geometry_options['crop_edition'] and not geometry_options['crop_preview']:
                    # Crop editon: rectangle but no preview
                    if geometry_options['resize_preview']:
                        print("paintEvent: draw rect crop on the resized image")

                        # Image is resized, add the recalculated crop
                        c_t, c_b, c_l, c_r, c_w, c_h = get_dimensions_from_crop_values(w_i, h_i,
                            self.image['geometry'][type]['crop'])
                        w_tmp = int((c_w * h_final) / float(c_h))
                        pad_left = int((w_final - w_tmp) / 2)
                        c_l = int((c_l * h_final) / float(c_h))
                        c_t = int((c_t * h_final) / float(c_h))


                        print("\t-> w=%d, c_w=%d, w_tmp=%d, pad: %d" % (w, c_w, w_tmp, pad_left))
                        print("\t-> cl=%d, c_t=%d" % (c_l, c_t))

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

                    else:
                        # print("paintEvent: draw rect crop on the original image")
                        # Original
                        self.painter.drawImage(
                            QPoint(PAINTER_MARGIN_LEFT, PAINTER_MARGIN_TOP - delta_y), q_image)

                        # Add a red rect for the crop
                        c_t, c_b, c_l, c_r, c_w, c_h = get_dimensions_from_crop_values(w_i, h_i,
                            self.image['geometry'][type]['crop'])
                        pen = QPen(COLOR_CROP_RECT)
                        pen.setWidth(PEN_CROP_SIZE)
                        pen.setStyle(Qt.SolidLine)
                        self.painter.setPen(pen)
                        # https://doc.qt.io/qt-6/qrect.html, PEN_CROP_SIZE = 1
                        # print("\timg: %dx%d" % (img.data.shape[1], img.data.shape[0]))
                        # print("\trect: (%d;%d) w=%d, h=%d" % (c_l - 1, c_t - delta_y - 1, c_w + 1, c_h + 1))
                        self.painter.drawRect(
                            PAINTER_MARGIN_LEFT + c_l - 1,
                            PAINTER_MARGIN_LEFT + c_t - delta_y - 1,
                            c_w + 1,
                            c_h + 1)

                elif geometry_options['crop_preview']:
                    if geometry_options['resize_preview']:
                        # print("paintEvent: draw cropped image and resized")
                        c_t, c_b, c_l, c_r, c_w, c_h = get_dimensions_from_crop_values(w_i, h_i, self.image['geometry']['part']['crop'])

                        w_tmp = int((c_w * h_final) / float(c_h))
                        pad_left = int((w_final - w) / 2)
                        print("paintEvent: pad=%d" % (pad_left))

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
                        # print("paintEvent: draw cropped image on the original image")
                        # Crop and no rect
                        c_t, c_b, c_l, c_r, c_w, c_h = get_dimensions_from_crop_values(w_i, h_i, self.image['geometry']['part']['crop'])

                        self.painter.drawImage(
                            QPoint(PAINTER_MARGIN_LEFT + c_l,
                                PAINTER_MARGIN_TOP + c_t - delta_y),
                            q_image)

                else:
                    # original
                    # print("paintEvent: draw original image")
                    self.painter.drawImage(
                        QPoint(PAINTER_MARGIN_LEFT, PAINTER_MARGIN_TOP - delta_y), q_image)



                if type == 'custom' and options['geometry']['part']['crop_edition']:
                    if geometry_options['resize_preview']:
                        # Image is resized, add the recalculated crop
                        c_t, c_b, c_l, c_r, c_w, c_h = get_dimensions_from_crop_values(w_i, h_i,
                            self.image['geometry']['part']['crop'])
                        w_tmp = int((c_w * h_final) / float(c_h))
                        pad_left = int((w_final - w_tmp) / 2)
                        print("\t-> w=%d, c_w=%d, w_tmp=%d, pad: %d" % (w, c_w, w_tmp, pad_left))

                        c_l = int((c_l * h_final) / float(c_h))
                        c_t = int((c_t * h_final) / float(c_h))

                        # Add the cropped resized rect
                        pen = QPen(COLOR_PART_CROP_RECT)
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



            if options['curves']['split']:
                try: c_t = 0 if geometry_options['resize_preview'] else (-1*c_t)
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
