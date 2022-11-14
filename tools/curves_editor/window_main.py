# -*- coding: utf-8 -*-

import cv2
import gc
import os
import os.path

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

from common.window_common import Window_common
from curves_editor.model_curves_editor import Model_curves_editor
from curves_editor.widget_curves_editor import Widget_curves_editor


class Window_main(Window_common):
    signal_reload_folder = Signal()

    def __init__(self, model:Model_curves_editor):
        super(Window_main, self).__init__(self, model)

        # Get preferences from model
        p = self.model.get_preferences()

        # Widget: curves editor
        self.widget_curves_editor = Widget_curves_editor(self, self.model)
        # self.widget_curves_editor.refresh_browsing_folder(self.model.get_available_episode_and_parts())
        self.widget_curves_editor.set_preview_options('preview')
        self.widget_curves_editor.signal_action[str].connect(self.event_editor_action)
        self.widget_curves_editor.widget_rgb_curves.widget_rgb_graph.signal_graph_modified.connect(self.event_curves_modified)
        self.widget_curves_editor.widget_app_controls.signal_action[str].connect(self.event_editor_action)
        self.widget_curves_editor.set_initial_options(p)
        self.widget_curves_editor.show()

        # Set initial values
        self.set_initial_options(p)

        # Initial display mode
        self.do_display_preview_image = True
        self.do_display_split_preview_image = False
        self.is_grabbing_split_line = False
        self.split_x = int(self.width() / 2)

        # Signals/events
        self.model.signal_display_frame[dict].connect(self.display_frame)
        self.model.signal_folders_parsed[dict].connect(self.event_folders_parsed)


    def event_activated(self):
        self.widget_curves_editor.activateWindow()

    def event_show_fullscreen(self):
        self.widget_curves_editor.showNormal()


    def event_folders_parsed(self, episodes_and_parts):
        log.info("folders have been parsed to update combobox")
        print("folders have been parsed to update combobox")
        pprint(episodes_and_parts)
        self.widget_curves_editor.refresh_browsing_folder(episodes_and_parts)


    def event_editor_action(self, event):
        # print("event_editor_action")
        # log.info("event=%s" % (event))
        if event == 'exit':
            if not self.is_closing:
                # print("\t skip, already closing")
                self.event_close()
        elif event == 'minimize':
            self.widget_curves_editor.showMinimized()
            self.showMinimized()
        elif event == 'repaint':
            self.repaint()


    def closeEvent(self, event):
        # print("closeEvent")
        if not self.is_closing:
            self.event_editor_action('exit')


    def event_close(self):
        # print("event_close")
        if not self.is_closing:
            self.is_closing = True
            self.model.exit()
            self.close_all_widgets()
        # else:
        #     print("skip, already closing")


    def close_all_widgets(self):
        # print("close_all_widgets")
        for widget in QApplication.topLevelWidgets():
            # print("\tclosing", widget)
            # pprint(widget)
            if widget is not self:
                widget.close()
        self.close()


    def set_initial_options(self, preferences:dict):
        s = preferences['viewer']
        self.setGeometry(s['geometry'][0],
            s['geometry'][1],
            s['geometry'][2],
            s['geometry'][3])



    def get_preferences(self) -> dict:
        # print("%s:get_preferences" % (__name__))
        # get preferences from children, merge them and return it
        new_preferences = {
            'viewer': {
                'screen': 0,
                'geometry': self.geometry().getRect()
            }
        }
        p = self.widget_curves_editor.get_preferences()
        new_preferences.update(p)
        return new_preferences



    def flush_image(self):
        log.info("flush image")
        del self.image
        self.image = None
        gc.collect()

        self.is_grabbing_split_line = False

        # Deselect curve
        self.widget_curves_editor.widget_curves_browser.deselect_curve_name()
        self.widget_curves_editor.widget_rgb_curves.reset_all_channels()


        if self.is_repainting:
            log.error("error: flush while repainting")
        self.is_repainting = False



    def display_frame(self, frame: dict):
        if frame is None or not os.path.exists(frame['filepath']):
            self.flush_image()
        else:
            if self.image is not None:
                del self.image
                self.image = None
                gc.collect()

            self.image = {
                'img': cv2.imread(frame['filepath'], cv2.IMREAD_COLOR),
                'qImage': None,
                'qImage_preview': None,
                # position and dimension
                'x': 0,
                'y': 0,
                'w': 0,
                'h': 0
            }

            self.image['h'], self.image['w'], channelCount = self.image['img'].shape
            self.image['qImage'] = QImage(self.image['img'].data,
                self.image['w'],
                self.image['h'],
                self.image['w']*3,
                QImage.Format_BGR888)

            # Global variables
            self.setMinimumWidth(1920)
            # self.setMinimumWidth(self.image.width())

            # Set split position
            w = min(self.image['qImage'].width(), self.width())
            # if w == self.image['qImage'].width():
            #     self.split_x = int(self.image['qImage'].width() / 2)
            # else:
            #     self.split_x = int(self.width() / 2)

            # Load curves
            # TODO!!!

            frame.update({
                'dimensions': {'w':self.image['qImage'].width(), 'h': self.image['qImage'].height()}
            })

            self.is_repainting = False

        gc.collect()
        self.repaint()



    def event_curves_modified(self, modification):
        # if not self.model.isCurveModified():
            # self.model.setModification('curve', enabled=True)
        # self.refreshCurvesInfo()
        self.repaint()


    def switch_to_original_image(self):
        if self.do_display_preview_image:
            # Switch back to original image
            log.info("preview: switch back to original image")
            self.widget_curves_editor.set_preview_options('original')
            self.do_display_preview_image = False
            self.do_display_split_preview_image = False
        else:
            log.info("preview: display preview image")
            self.widget_curves_editor.set_preview_options('preview')
            self.do_display_split_preview_image = False
            self.do_display_preview_image = True
        self.repaint()


    def switch_to_splitted_image(self):
        if self.do_display_split_preview_image:
            log.info("split: switch to preview")
            self.widget_curves_editor.set_preview_options('preview')
            self.do_display_split_preview_image = False
            self.do_display_preview_image = True
        else:
            log.info("split: display splitted image")
            self.widget_curves_editor.set_preview_options('splitted')
            self.do_display_split_preview_image = True
        self.repaint()


    def get_rgb_value(self, xr, yr):
        if self.image is None:
            # No frame loaded
            return

        if self.widget_curves_editor.is_fit_to_image_enabled():
            h = self.height()
            w = int((self.image['w'] * h) / float(self.image['h']))
            yr = int(yr * (self.image['h'] / h))
            xr = int(xr * (self.image['w'] / w))
        else:
            h = self.image['h']
            w = self.image['w']


        if (xr >= 0 and yr >= 0
                and xr < self.width() and yr < self.height()
                and xr < w and yr < h):

            c = self.image['qImage'].pixelColor(xr, yr)
            # print("(%d, %d) -> (%d, %d, %d)" % (xr, yr, c.red(), c.green(), c.blue()))
            self.widget_curves_editor.widget_rgb_curves.update_rgb_value(c.red(), c.green(), c.blue())
            # self.widget_rgb_curves.displayCurrenPosition(c.red(), c.green(), c.blue())
            self.setCursor(Qt.CrossCursor)
        else:
            self.widget_curves_editor.widget_rgb_curves.update_rgb_value(None, None, None)
            self.setCursor(Qt.ArrowCursor)



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





    def event_right_click(self, qpoint):
        cursor_position = QCursor.pos()
        pop_menu = QMenu(self)
        pop_menu.setStyleSheet("background-color: rgb(128, 128, 128);")
        action_exit = pop_menu.addAction('Exit')
        action_exit.triggered.connect(self.event_close)
        pop_menu.exec_(cursor_position)



    def mouseMoved(self, x, y):
        if self.is_grabbing_split_line:
            self.split_x = x + self.mouse_grabX
            self.setCursor(Qt.SplitHCursor)
        self.repaint()


    def mouseMoveEvent(self, event):
        if self.is_grabbing_split_line:
            self.split_x = event.x() + self.split_x_gap
            self.setCursor(Qt.SplitHCursor)
            self.repaint()
        else:
            self.get_rgb_value(event.x(), event.y())


    def mousePressEvent(self, event):
        x = event.x()
        y = event.y()
        b = event.button()

        # if b == Qt.MouseButton.BackButton or b == Qt.MouseButton.ForwardButton:
        #     self.mousePressEvent(event)

        if self.image is not None and self.image['qImage'] is not None:
            if (self.do_display_split_preview_image
                and x >= (self.split_x - 20) and x <= (self.split_x + 20)):
                self.split_x_gap = self.split_x - x
                self.is_grabbing_split_line = True
                self.setCursor(Qt.SplitHCursor)
            else:
                self.is_grabbing_split_line = False
                self.get_rgb_value(x, y)
            event.accept()
        else:
            event.ignore()


    def mouseReleaseEvent(self, event):
        self.setCursor(Qt.ArrowCursor)
        self.is_grabbing_split_line = False


    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.widget_curves_editor.select_previous_image()
        elif event.angleDelta().y() < 0:
            self.widget_curves_editor.select_next_image()
        event.accept()
        return True


    def keyPressEvent(self, event):
        key = event.key()
        modifier = event.modifiers()

        if modifier & Qt.AltModifier:
            if key == Qt.Key_F9:
                self.event_browser_action('minimize')

        elif modifier & Qt.ControlModifier:
            self.widget_curves_editor.keyPressEvent(event)

        elif key == Qt.Key_Space:
            self.switch_to_original_image()
            return True
        elif key == Qt.Key_S:
            self.switch_to_splitted_image()
            return True

        elif key == Qt.Key_F5:
            log.info("Reload")
            self.signal_reload_folder.emit()

        else:
            log.info("keyPressEvent: %d, propagate" % (key))
            # self.ui.keyPressEvent(event)
            self.widget_curves_editor.keyPressEvent(event)

        return False


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