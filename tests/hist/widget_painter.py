# -*- coding: utf-8 -*-
from pprint import pprint
import numpy as np
import cv2

from PySide6.QtCore import (
    QPoint,
    Qt,
    Signal,
    QRect,
    QSize,
)
from PySide6.QtGui import (
    QColor,
    QImage,
    QPainter,
    QPen,
    QKeyEvent,
    QWheelEvent,
    QMouseEvent,
    QPaintEvent,
    QDropEvent,
)
from PySide6.QtWidgets import (
    QWidget,
)
from stylesheet import (
    set_stylesheet,
    set_widget_stylesheet,
)



class Widget_painter(QWidget):
    signal_urls_dropped = Signal(dict)
    signal_wheel_event = Signal(QWheelEvent)
    signal_mouse_left_button_pressed = Signal(QPoint)
    signal_mouse_left_button_released = Signal(QPoint)
    signal_cursor_moved_to = Signal(QPoint)

    def __init__(self, parent):
        super(Widget_painter, self).__init__()

        self.setAcceptDrops(True)
        self.setMouseTracking(True)

        self.q_image = None
        self.is_control_key_pressed = False
        self.__slider = None

        self.__image_position = None

        # Save for future use
        # self.installEventFilter(self)
        set_stylesheet(self)
        self.adjustSize()

    def dropEvent(self, event: QDropEvent) -> None:
        urls = event.mimeData().urls()
        filepaths = [urls[i].toLocalFile() for i in range(len(urls))]
        dropped_urls = {
            'filepaths': filepaths,
            'position': event.pos(),
        }
        self.signal_urls_dropped.emit(dropped_urls)


    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            # print("drag event")
            # pprint(urls)
            if len(urls) == 2:
                event.acceptProposedAction()

    def get_geometry(self) -> QRect:
        x0, y0, w, h = self.geometry().getRect()
        geometry = QRect(x0, y0, w, h)
        print(f"\tpainter geometry: ({geometry[0]}, {geometry[1]}) {geometry[2]}x{geometry[3]}")
        return geometry

    def get_size(self) -> QSize:

        print(f"rect: {self.geometry().getRect()}")
        print(f"size: {self.size()}")
        return self.size()

    def show_image(self, img:cv2.Mat) -> None:
        try:
            height, width, channel_count = img.shape
        except:
            return
        self.q_image = QImage(img.data,
            width, height, channel_count * width, QImage.Format_BGR888)
        self.repaint()


    def draw_slider_line(self, slider:dict) -> None:
        self.__slider = slider
        self.repaint()


    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        self.is_control_key_pressed = False
        return super().keyReleaseEvent(event)


    def keyPressEvent(self, event: QKeyEvent) -> None:
        print("key_pressed")
        key = event.key()
        if key == Qt.Key.Key_Control:
            self.is_control_key_pressed = True
            event.accept()
            return
        else:
            self.is_control_key_pressed = False

        return super().keyPressEvent(event)


    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        cursor_position = event.position().toPoint()
        self.signal_mouse_left_button_released.emit(cursor_position)
        return super().mouseReleaseEvent(event)


    def mouseMoveEvent(self, event):
        cursor_position = event.position().toPoint()
        self.signal_cursor_moved_to.emit(cursor_position)
        return super().mouseMoveEvent(event)


    def mousePressEvent(self, event: QMouseEvent) -> None:
        cursor_position = event.position().toPoint()
        print(f"[{cursor_position.x()}, {cursor_position.y()}]")
        self.signal_mouse_left_button_pressed.emit(cursor_position)
        return super().mousePressEvent(event)


    def wheelEvent(self, event: QWheelEvent) -> None:
        print(event.position().toPoint())
        self.signal_wheel_event.emit(event)
        # print(event.globalPosition())

        # factor = 1.1
        # if event.angleDelta().y() < 0:
        #     factor = 0.9
        # view_pos = event.pos()
        # scene_pos = self.mapToScene(view_pos)
        # self.centerOn(scene_pos)
        # self.scale(factor, factor)
        # delta = self.mapToScene(view_pos) - self.mapToScene(self.viewport().rect().center())
        # self.centerOn(scene_pos - delta)



    # def wheelEvent(self, event: QWheelEvent) -> None:
    #     print(self.pos())
    #     print(QCursor().pos())
    #     # print(QCursor().pos())
    #     # event_position =
    #     # QCursor.pos() - this->window()->pos();
    #     # coordinates = [event_position.x(), event_position.y()]
    #     coordinates = list()
    #     if event.angleDelta().y() > 0:
    #         self.signal_zoom_changed.emit({
    #             'type': 'in',
    #             'coordinates': coordinates
    #         })
    #     elif event.angleDelta().y() < 0:
    #         self.signal_zoom_changed.emit({
    #             'type': 'out',
    #             'coordinates': coordinates
    #         })
    #     return True

    #     return super().wheelEvent(event)



    # def wheel_event(self, event):
    #     if not self.slider_frames.isEnabled():
    #         return False

    #     # Do not accept event if not in paused mode
    #     if self.status == 'stopped':
    #         self.refresh_status('paused')
    #     if self.status != 'paused':
    #         return False

    #     if self.is_shift_key_pressed:
    #         # move to next/previous tick
    #         if event.angleDelta().y() > 0:
    #             self.set_slider_to_previous_tick()
    #         elif event.angleDelta().y() < 0:
    #             self.set_slider_to_following_tick()
    #         return True
    #     else:
    #         # Select next/previous frame
    #         if event.angleDelta().y() > 0:
    #             self.event_previous_frame()
    #         elif event.angleDelta().y() < 0:
    #             self.event_next_frame()
    #         return True

    #     return False


    # Save for future use
    # def eventFilter(self, watched: QObject, event: QEvent) -> bool:
    #     # print(f"  * eventFilter: {self.objectName()}:", event.type())
    #     if event.type() == QEvent.Type.Leave:
    #         print_lightcyan(f"eventFilter: leave")
    #     return super().eventFilter(watched, event)

    def event_image_position_changed(self, position:QPoint) -> None:
        # print(f"image position changed to {position}")
        self.__image_position = position
        self.repaint()

    def paintEvent(self, event:QPaintEvent):
        # print("\tpaintEvent")
        # if self.q_image is None:
        #     print("No image loaded")
        #     # TODO display an error message?
        #     return
        # Get geometry
        x0, y0, w, h = self.geometry().getRect()
        x1, y1 = w, h
        # if self.__image_position is not None:
        #     x0 -= self.__image_position.x()
        #     y0 -= self.__image_position.y()

        pen_width = 1
        painter = QPainter()
        if painter.begin(self):

            # Display image
            try:
                painter.drawImage(QPoint(x0, y0), self.q_image)
            except:
                pass

            # Draw the slider line
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            try:
                pen = QPen(self.__slider['pen']['color'].rgb())
                pen.setWidth(self.__slider['pen']['width'])
                pen.setStyle(self.__slider['pen']['style'])
                painter.setPen(pen)
                painter.drawLine(self.__slider['geometry'][0], self.__slider['geometry'][1])
            except:
                pass


            if False:
                # For debug
                painter.setRenderHint(QPainter.Antialiasing, False)
                pen = QPen(QColor(255,255,255))
                pen.setWidth(pen_width)
                pen.setStyle(Qt.SolidLine)
                painter.setPen(pen)
                painter.drawRect(x0, y0, w - pen_width, h - pen_width)

                painter.setRenderHint(QPainter.Antialiasing, True)
                pen = QPen(QColor(0,255,0))
                pen.setWidth(pen_width)
                pen.setStyle(Qt.SolidLine)
                painter.setPen(pen)
                painter.drawLine(x0, y0, x1 - pen_width, y1 - pen_width)
                painter.drawLine(x0, y1 - pen_width, x1 - pen_width, y0)


                # painter.setRenderHint(QPainter.Antialiasing, False)
                # pen = QPen(QColor(255,0,0))
                # pen.setWidth(pen_width)
                # pen.setStyle(Qt.SolidLine)
                # painter.setPen(pen)
                # painter.drawRect(self.geometry().getRect()[0], self.geometry().getRect()[1],
                #                  w - pen_width, h - pen_width)


            painter.end()
