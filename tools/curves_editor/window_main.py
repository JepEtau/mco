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
    signal_save_and_close = Signal()

    def __init__(self, model:Model_curves_editor):
        super(Window_main, self).__init__(self, model)
        # Get preferences from model
        p = self.model.get_preferences()


        # # Widget: curves editor
        # self.widget_curves_editor = Widget_curves_editor(self, self.model)
        # # self.widget_curves_editor.refresh_browsing_folder(self.model.get_available_episode_and_parts())
        # self.widget_curves_editor.set_preview_options('preview')
        # self.widget_curves_editor.signal_action[str].connect(self.event_editor_action)
        # self.widget_curves_editor.widget_rgb_curves.widget_rgb_graph.signal_graph_modified.connect(self.event_curves_modified)
        # self.widget_curves_editor.widget_app_controls.signal_action[str].connect(self.event_editor_action)
        # self.widget_curves_editor.set_initial_options(p)
        # self.widget_curves_editor.show()


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
        # Update the UI and only after, try to select the preferred selection
        self.widget_selection.event_folders_parsed(self.model.get_available_selection())
        self.widget_selection.set_initial_options(p)


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
        self.do_display_preview_image = True
        self.do_display_split_preview_image = False
        self.is_grabbing_split_line = False
        self.split_x = int(self.width() / 2)


        if False:
            # previously
            # Signals/events
            self.model.signal_display_frame[dict].connect(self.display_frame)

        self.model.signal_folders_parsed[dict].connect(self.widget_selection.event_folders_parsed)
        self.model.signal_shotlist_modified[dict].connect(self.widget_selection.event_shotlist_modified)


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
        print("get_rgb_value")

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


    # def event_editor_action(self, event):
    #     # print("event_editor_action")
    #     # log.info("event=%s" % (event))
    #     if event == 'exit':
    #         if not self.is_closing:
    #             # print("\t skip, already closing")
    #             self.event_close()
    #     elif event == 'minimize':
    #         self.widget_curves_editor.showMinimized()
    #         self.showMinimized()
    #     elif event == 'repaint':
    #         self.repaint()


    # def event_curves_modified(self, modification):
    #     # if not self.model.isCurveModified():
    #         # self.model.setModification('curve', enabled=True)
    #     # self.refreshCurvesInfo()
    #     self.repaint()


    # def switch_to_original_image(self):
    #     if self.do_display_preview_image:
    #         # Switch back to original image
    #         log.info("preview: switch back to original image")
    #         self.widget_curves_editor.set_preview_options('original')
    #         self.do_display_preview_image = False
    #         self.do_display_split_preview_image = False
    #     else:
    #         log.info("preview: display preview image")
    #         self.widget_curves_editor.set_preview_options('preview')
    #         self.do_display_split_preview_image = False
    #         self.do_display_preview_image = True
    #     self.repaint()


    # def switch_to_splitted_image(self):
    #     if self.do_display_split_preview_image:
    #         log.info("split: switch to preview")
    #         self.widget_curves_editor.set_preview_options('preview')
    #         self.do_display_split_preview_image = False
    #         self.do_display_preview_image = True
    #     else:
    #         log.info("split: display splitted image")
    #         self.widget_curves_editor.set_preview_options('splitted')
    #         self.do_display_split_preview_image = True
    #     self.repaint()


    # def get_rgb_value(self, xr, yr):
    #     if self.image is None:
    #         # No frame loaded
    #         return





    def paintEvent(self, event):
        # log.info("repainting")
        if self.image is None:
            log.info("no image loaded")
            return

        if self.is_repainting:
            log.error("error: self.is_repainting is True!!")
            return
        self.is_repainting = True

        if self.widget_curves_editor.is_fit_to_image_enabled():
            h = min(self.height(), 1080)
            w = int((self.image['w'] * h) / float(self.image['h']))
            image_resized = cv2.resize(self.image['img'], (w, h))
            qImage_resized = QImage(image_resized.data, w, h, w * 3, QImage.Format_BGR888)
        else:
            image_resized = self.image['img']
            h = self.image['h']
            w = self.image['w']
            qImage_resized = self.image['qImage']


        if self.do_display_preview_image or self.do_display_split_preview_image:
            b, g, r = cv2.split(image_resized)
            matrix_r = self.widget_curves_editor.widget_rgb_curves.widget_rgb_graph.channel_lut('r')
            matrix_g = self.widget_curves_editor.widget_rgb_curves.widget_rgb_graph.channel_lut('g')
            matrix_b = self.widget_curves_editor.widget_rgb_curves.widget_rgb_graph.channel_lut('b')

            rrp = matrix_r[r.flat].reshape(r.shape)
            ggp = matrix_g[g.flat].reshape(g.shape)
            bbp = matrix_b[b.flat].reshape(b.shape)

            image_preview = cv2.merge((bbp, ggp, rrp))
            del self.image['qImage_preview']
            self.image['qImage_preview'] = QImage(image_preview.data, w, h, w * 3, QImage.Format_BGR888)
        else:
            log.info("display original image")


        if self.image['qImage_preview'] is None:
            log.error("flush image previewImage is None")
            return

        # w = min(self.image['w'], self.width())
        # h = min(self.image['h'], self.height())
        # log.info ("(w, h) = (%d; %d)" % (w, h))
        if self.painter.begin(self):
            if self.do_display_split_preview_image:
                # log.info("do_display_split_preview_image")
                self.painter.drawImage(
                    QPoint(self.split_x, 0),
                    qImage_resized,
                    QRect(self.split_x, 0, w - self.split_x, h))
                self.painter.drawImage(
                    QPoint(0, 0),
                    self.image['qImage_preview'],
                    QRect(0, 0, self.split_x, h))

                pen = QPen(QColor(0, 0, 0))
                pen.setStyle(Qt.DashLine)
                self.painter.setPen(pen)
                self.painter.drawLine(self.split_x, 0, self.split_x, (h-1))
                # log.info("ImageWidget::line [(%d,%d);(%d,%d)]" % (self.split_x, 0, self.split_x, (h-1)))

            elif self.do_display_preview_image:
                # log.info("do_display_preview_image")
                self.painter.drawImage(QPoint(0, 0), self.image['qImage_preview'])
            else:
                # log.info("original image")
                self.painter.drawImage(QPoint(0, 0), qImage_resized)

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