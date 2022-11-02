#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gc
from pprint import pprint
from logger import log

from PySide6.QtCore import (
    QEvent,
    QPoint,
    Qt,
)
from PySide6.QtGui import (
    QCursor,
    QIcon,
    QImage,
    QPainter,
)
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMenu,
)

from common.window_common import Window_common
from viewer.model_viewer import Model_viewer
from viewer.widget_browser import Widget_browser

PAINTER_MARGIN_LEFT = 20
PAINTER_MARGIN_TOP = 20

class Window_main(Window_common, QMainWindow):

    def __init__(self, model:Model_viewer):
        super(Window_main, self).__init__()

        # Set model
        self.model = model

        # Reset variables
        self.image = None
        self.is_repainting = False
        self.is_closing = False

        self.setWindowIcon(QIcon("img/icon.png"))

        # Add painter
        self.painter = QPainter()

        self.patch_ui()
        self.setWindowFlags(Qt.Window)
        self.setStyleSheet("background-color: black")
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)

        # Verify that folder exists

        # Get preferences from model
        p = self.model.get_preferences()

        # Widget: browser
        self.widget_browser = Widget_browser(self, self.model)
        self.widget_browser.refresh_browsing_folder(self.model.get_available_episode_and_parts())
        self.widget_browser.signal_action[str].connect(self.event_browser_action)
        self.widget_browser.set_initial_options(p)

        # Events
        self.model.signal_display_frame[dict].connect(self.display_frame)

        # Right click
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested[QPoint].connect(self.event_right_click)

        # Set initial values
        self.set_initial_options(p)

        # Install event filter
        self.installEventFilter(self)
        self.widget_browser.show()


    def event_activated(self):
        self.widget_browser.activateWindow()

    def event_show_fullscreen(self):
        self.widget_browser.showNormal()

    def event_browser_action(self, event):
        # log.info("event=%s" % (event))
        if event == 'exit':
            self.event_close()
        elif event == 'minimize':
            self.widget_browser.showMinimized()
            self.showMinimized()
        elif event == 'repaint':
            self.repaint()


    def closeEvent(self, event):
        self.event_browser_action('exit')


    def event_close(self):
        if not self.is_closing:
            self.is_closing = True
            self.model.exit()
            self.close_all_widgets()


    def close_all_widgets(self):
        for widget in QApplication.topLevelWidgets():
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
        # get preferences from children and merge them
        new_preferences = {
            'viewer': {
                'screen': 0,
                'geometry': self.geometry().getRect()
            }
        }
        p = self.widget_browser.get_preferences()
        new_preferences.update(p)
        return new_preferences


    def flush_image(self):
        log.info("flush image")
        del self.image
        self.image = None
        gc.collect()

        if self.is_repainting:
            log.error("error: flush while repainting")
        self.is_repainting = False


    def display_frame(self, frame: dict):
        if frame is None:
            self.flush_image()
        else:
            self.image = QImage(frame['filepath'])
            # log.info("image size: %dx%d" % (self.image.width(), self.image.height()))
            self.is_repainting = False
            self.setMinimumWidth(self.image.width())

            frame.update({
                'dimensions': {'w':self.image.width(), 'h': self.image.height()}
            })
        self.widget_browser.display_frame_properties(frame)
        gc.collect()
        self.repaint()


    def paintEvent(self, event):
        # log.info("repainting")
        if self.image is None:
            log.info("no image loaded")
            return

        if self.is_repainting:
            log.error("error: self.is_repainting is True!!")
            return
        self.is_repainting = True

        # w = min(self.image.width(), self.width())
        # h = min(self.image.height(), self.height())
        # log.info("viewer size: %dx%d" % (self.width(), self.height()))
        # log.info("image size: %dx%d" % (w, h))

        if self.painter.begin(self):
            self.is_repainting = True
            if self.widget_browser.is_fit_to_image_enabled():
                self.painter.drawImage(QPoint(PAINTER_MARGIN_LEFT, PAINTER_MARGIN_TOP),
                    self.image.scaled(min(self.width(), 1920), min(self.height(), 1080), Qt.KeepAspectRatio))
            else:
                self.painter.drawImage(QPoint(PAINTER_MARGIN_LEFT, PAINTER_MARGIN_TOP), self.image)
            self.painter.end()
            # self.setFocus()
        self.is_repainting = False



    def event_right_click(self, qpoint):
        cursor_position = QCursor.pos()
        pop_menu = QMenu(self)
        pop_menu.setStyleSheet("background-color: rgb(128, 128, 128);")
        action_exit = pop_menu.addAction('Exit')
        action_exit.triggered.connect(self.event_close)
        pop_menu.exec_(cursor_position)


    def wheelEvent(self, event):
        # print(event.angleDelta())
        if event.angleDelta().y() > 0:
            self.widget_browser.select_previous_image()
        elif event.angleDelta().y() < 0:
            self.widget_browser.select_next_image()


    def keyPressEvent(self, event):
        key = event.key()
        modifier = event.modifiers()

        if modifier & Qt.AltModifier:
            if key == Qt.Key_F9:
                self.event_browser_action('minimize')

        elif key == Qt.Key_Up:
            # log.info("previous")
            self.widget_browser.select_previous_image()

        elif key == Qt.Key_Down:
            # log.info("next")
            self.widget_browser.select_next_image()

        elif key == Qt.Key_F5:
            # log.info("reload")
            self.widget_browser.event_episode_changed()
            return True

        elif key == Qt.Key_F:
            self.widget_browser.switch_fit_image_state()

        elif key == Qt.Key_Home:
            return self.widget_browser.select_first_image()

        elif key == Qt.Key_End:
            return self.widget_browser.select_last_image()

        elif key == Qt.Key_PageUp:
            return self.widget_browser.event_page_up(event)

        elif key == Qt.Key_PageDown:
            return self.widget_browser.event_page_down(event)

        else:
            log.info("keyPressEvent: %d, propagate" % (key))


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