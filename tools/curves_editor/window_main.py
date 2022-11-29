# -*- coding: utf-8 -*-

import sys
sys.path.append('../scripts')

import cv2
from functools import partial
import gc
import os

from pprint import pprint
from logger import log

from PySide6.QtCore import (
    QEvent,
    QPoint,
    QRect,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QColor,
    QCursor,
    QImage,
    QPen,
)
from PySide6.QtWidgets import (
    QApplication,
    QMenu,
)

from common.window_common import (
    Window_common,
    PAINTER_MARGIN_LEFT,
    PAINTER_MARGIN_TOP,
)
from curves_editor.model_curves_editor import Model_curves_editor
# from curves_editor.widget_curves_editor import Widget_curves_editor
from curves_editor.widget_selection import Widget_selection

from video_editor.widget_curves import Widget_curves


COLOR_PART_CROP_RECT = QColor(30, 230, 30)
COLOR_CROP_RECT = QColor(230, 30, 30)
COLOR_FINAL_RECT = QColor(0, 255, 0)
COLOR_DISPLAY_RECT = QColor(255, 255, 255)
# PEN_CROP_SIZE must be equal to 1 or 2
PEN_CROP_SIZE = 1

class Window_main(Window_common):
    signal_preview_options_changed = Signal(dict)
    signal_reload_directories_and_frames = Signal()
    signal_save_and_close = Signal()

    def __init__(self, model:Model_curves_editor):
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


        # Selection of episode/part/shot
        self.widget_selection = Widget_selection(self, self.model)
        self.widgets['selection'] = self.widget_selection
        self.widget_selection.signal_selection_changed[dict].connect(self.event_selection_changed)
        self.widget_selection.widget_app_controls.signal_action[str].connect(self.event_editor_action)
        self.widget_selection.signal_selected_shots_changed[dict].connect(self.event_selected_shots_changed)
        self.widget_selection.signal_preview_options_changed.connect(partial(self.event_preview_options_changed, 'selection'))
        # Update the UI and only after, try to select the preferred selection
        self.widget_selection.event_folders_parsed(self.model.get_available_selection())
        self.widget_selection.set_initial_options(p)
        self.widget_selection.signal_image_selected[str].connect(self.event_image_selected)


        # Model
        self.model.signal_reload_frame.connect(self.event_reload_frame)
        self.model.signal_close.connect(self.event_close_without_saving)


        # Show window/widgets and connect signals
        for w in self.widgets.values():
            w.signal_close.connect(self.event_editor_action)
            w.show()

        # Set initial values
        self.set_initial_options(p)
        self.event_show_fullscreen()

        # Initial display mode
        self.split_x = int(self.width() / 2)


        self.model.signal_folders_parsed[dict].connect(self.widget_selection.event_folders_parsed)


    def flush_image(self):
        log.info("flush image")
        del self.image
        self.image = None
        gc.collect()

        if self.is_repainting:
            log.error("error: flush while repainting")
        self.is_repainting = False


    def event_reload_frame(self):
        f = self.model.get_frame_from_name('reload')
        self.display_frame(f)


    def event_image_selected(self, image_name):
        # self.model.get_frame(name)
        # log.info("get image [%s]" % (image_name))
        f = self.model.get_frame_from_name(image_name)
        self.display_frame(f)



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
        # print("get_rgb_value")

        # Previous: to enabled
        # if self.widget_curves_editor.is_fit_to_image_enabled():
        #     h = self.height()
        #     w = int((self.image['w'] * h) / float(self.image['h']))
        #     yr = int(yr * (self.image['h'] / h))
        #     xr = int(xr * (self.image['w'] / w))
        # else:
        #     h = self.image['h']
        #     w = self.image['w']


        # if (xr >= 0 and yr >= 0
        #         and xr < self.width() and yr < self.height()
        #         and xr < w and yr < h):

        #     c = self.image['qImage'].pixelColor(xr, yr)
        #     # print("(%d, %d) -> (%d, %d, %d)" % (xr, yr, c.red(), c.green(), c.blue()))
        #     self.widget_curves_editor.widget_rgb_curves.update_rgb_value(c.red(), c.green(), c.blue())
        #     # self.widget_rgb_curves.displayCurrenPosition(c.red(), c.green(), c.blue())
        #     self.setCursor(Qt.CrossCursor)
        # else:
        #     self.widget_curves_editor.widget_rgb_curves.update_rgb_value(None, None, None)
        #     self.setCursor(Qt.ArrowCursor)
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

        # if self.image is not None and self.image['qImage'] is not None:
        #     if (self.do_display_split_preview_image
        #         and x >= (self.split_x - 20) and x <= (self.split_x + 20)):
        #         self.split_x_gap = self.split_x - x
        #         self.is_grabbing_split_line = True
        #         self.setCursor(Qt.SplitHCursor)
        #     else:
        #         self.is_grabbing_split_line = False
        #         self.get_rgb_value(x, y)




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


        # if self.is_grabbing_split_line:
        #     self.split_x = x + self.mouse_grabX
        #     self.setCursor(Qt.SplitHCursor)
        # self.repaint()



    def mouseMoved(self, x, y):
        if self.widget_curves.split_line_moved(x, self.mouse_grabX):
            self.setCursor(Qt.SplitHCursor)
            self.event_reload_frame()

        # if self.is_grabbing_split_line:
        #     self.split_x = event.x() + self.split_x_gap
        #     self.setCursor(Qt.SplitHCursor)
        #     self.repaint()
        # else:
        #     self.get_rgb_value(event.x(), event.y())


    def mouseReleaseEvent(self, event):
        self.setCursor(Qt.ArrowCursor)
        self.widget_curves.split_line_released(event.x())

        # self.is_grabbing_split_line = False


    def wheelEvent(self, event):
        if self.widget_selection.list_images.wheelEvent(event):
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
                self.signal_reload_directories_and_frames.emit()
                event.accept()
                return True

            elif key == Qt.Key_Up:
                # log.info("previous")
                self.widget_selection.select_previous_image()

            elif key == Qt.Key_Down:
                # log.info("next")
                self.widget_selection.select_next_image()

            elif key == Qt.Key_Home:
                return self.widget_selection.select_first_image()

            elif key == Qt.Key_End:
                return self.widget_selection.select_last_image()

            elif key == Qt.Key_PageUp:
                return self.widget_selection.event_page_up(event)

            elif key == Qt.Key_PageDown:
                return self.widget_selection.event_page_down(event)


        for e, w in self.widgets.items():
            if self.current_editor == e:
                is_accepted = w.event_key_pressed(event)
                if is_accepted:
                    event.accept()
                    return True


        event.accept()
        return True


    def keyReleaseEvent(self, event):
        key = event.key()

        if self.current_editor == 'curves':
            is_accepted = self.widget_curves.event_key_released(event)
            if is_accepted:
                event.accept()
                return True

        # return self.widget_controls.keyReleaseEvent(event)





    # def event_activated(self):
    #     self.widget_curves_editor.activateWindow()

    # def event_show_fullscreen(self):
    #     self.widget_curves_editor.showNormal()


    def event_folders_parsed(self, available_selection):
        log.info("folders have been parsed to update combobox")
        print("folders have been parsed to update combobox")
        self.widget_selection.event_folders_parsed(available_selection)


    def event_shotlist_modified(self, shotlist):
        self.widget_selection.event_shotlist_modified(shotlist=shotlist)




    def paintEvent(self, event):
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


            self.painter.drawImage(
                QPoint(PAINTER_MARGIN_LEFT, PAINTER_MARGIN_TOP - delta_y), q_image)


            if options['curves']['split']:
                pen = QPen(QColor(255,255,255))
                pen.setStyle(Qt.DashLine)
                self.painter.setPen(pen)
                self.painter.drawLine(
                    options['curves']['split_x'] + PAINTER_MARGIN_LEFT, PAINTER_MARGIN_TOP,
                    options['curves']['split_x'] + PAINTER_MARGIN_LEFT, PAINTER_MARGIN_TOP + max(h, h_final))


            self.painter.end()
            # ??? to verify:
            self.setFocus()
        self.is_repainting = False






    # def changeEvent(self, event: QEvent) -> None:
    #     if event.type() == QEvent.ActivationChange:
    #         if self.isActiveWindow():
    #             self.event_activated()
    #             event.accept()
    #             return True
    #     elif event.type() == QEvent.WindowStateChange:
    #         if self.windowState() & Qt.WindowFullScreen:
    #             # From minimized to normal
    #             self.event_show_fullscreen()
    #         event.accept()
    #         return True
    #     return super().changeEvent(event)