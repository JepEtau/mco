# -*- coding: utf-8 -*-
import sys
import gc
from pprint import pprint
from logger import log

from PySide6.QtCore import (
    QEvent,
    QPoint,
    QSize,
    Qt,
)
from PySide6.QtGui import (
    QCursor,
    QIcon,
    QImage,
)
from PySide6.QtWidgets import (
    QApplication,
    QMenu,
)

from common.window_common import Window_common
from viewer.model_viewer import Model_viewer
from viewer.widget_browser import Widget_browser

PAINTER_MARGIN_LEFT = 20
PAINTER_MARGIN_TOP = 20

class Window_main(Window_common):

    def __init__(self, model:Model_viewer):
        super(Window_main, self).__init__(self, model)

        # Get preferences from model
        p = self.model.get_preferences()

        # Widget: browser
        self.widget_browser = Widget_browser(self, self.model)
        self.widget_browser.refresh_browsing_folder(self.model.get_available_episode_and_parts())
        self.widget_browser.signal_action[str].connect(self.event_browser_action)
        self.widget_browser.set_initial_options(p)

        # Events
        self.model.signal_display_frame[dict].connect(self.display_frame)

        # Set initial values
        self.set_initial_options(p)

        # Install event filter
        self.installEventFilter(self)
        self.widget_browser.show()


    def event_activated(self):
        self.widget_browser.activateWindow()

    def event_show_fullscreen(self):
        self.widget_browser.showNormal()


    def event_show_fullscreen(self):
        self.blockSignals(True)
        self.widget_browser.blockSignals(True)
        self.widget_browser.showNormal()
        self.widget_browser.activateWindow()
        self.widget_browser.blockSignals(False)
        self.blockSignals(False)




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
        # Not clean but avoid ghost processes: clean this
        sys.exit()



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
            frame.update({
                'dimensions': {'w':self.image.width(), 'h': self.image.height()}
            })
        # self.widget_browser.display_frame_properties(frame)
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

        if self.painter.begin(self):
            if self.widget_browser.is_fit_to_image_enabled():
                self.painter.drawImage(QPoint(PAINTER_MARGIN_LEFT, PAINTER_MARGIN_TOP),
                    self.image.scaled(min(self.width(), 1920), min(self.height(), 1080), Qt.KeepAspectRatio))
            else:
                self.painter.drawImage(QPoint(PAINTER_MARGIN_LEFT, PAINTER_MARGIN_TOP), self.image)
            self.painter.end()
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

        elif key == Qt.Key_F9:
            self.event_browser_action('minimize')
            event.accept()
            return True

        elif key == Qt.Key_Up:
            # log.info("previous")
            self.widget_browser.select_previous_image()

        elif key == Qt.Key_Down:
            # log.info("next")
            self.widget_browser.select_next_image()

        elif key == Qt.Key_F5:
            # log.info("reload")
            self.widget_browser.event_reload()
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


    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.ActivationChange:
            if self.windowState() == Qt.WindowState().WindowNoState:
                self.setWindowState(Qt.WindowActive)
                self.event_show_fullscreen()
                event.accept()
                return True

            if self.windowState() & Qt.WindowState().WindowActive:
                self.setWindowState(Qt.WindowActive)
                self.event_show_fullscreen()
                event.accept()
                return True

            if (self.windowState() & Qt.WindowState().WindowMinimized
            and not self.isActiveWindow()):
                self.setWindowState(Qt.WindowActive)
                self.event_show_fullscreen()
                event.accept()
                return True

        return super().changeEvent(event)
