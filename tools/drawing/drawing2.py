#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import signal
import sys
import cv2
from operator import itemgetter
from PySide6.QtCore import (
    QPoint,
    Qt,
    QRectF,
    QPointF,

)
from PySide6.QtGui import (
    QBrush,
    QPen,
    QPixmap,
    QPolygonF,
    QKeyEvent,
    QColor,
)
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QGraphicsScene,
    QGraphicsPolygonItem,
    QGraphicsView,
    QGraphicsPixmapItem,
    QGraphicsItem,
    QWidget,
    QVBoxLayout,
    QPushButton,

)

# https://stackoverflow.com/questions/69421799/how-to-resize-polygon-by-dragging-its-corners

from pprint import pprint

class CustomGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.__scene = QGraphicsScene(self)
        self.setScene(self.__scene)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._pixmap_item = QGraphicsPixmapItem()
        self.__scene.addItem(self._pixmap_item)

        self.record_points = True
        self.__current_polygon = None  # the selected polygon
        self.points_lst = []  # points that are stored when recording
        self.corner_points = []  # This contains corner point and control point mapping
        self.selected_corner = None
        self.poly_points = [] # points that are stored when resizing (You could instead reuse points_lst)


        # Debug
        self.points_lst.append(QPointF(50,50))
        self.points_lst.append(QPointF(50,389))
        self.points_lst.append(QPointF(400,400))
        self.points_lst.append(QPointF(400,123))
        self.draw_polygon()

        self.control_key_pressed = False



    def setPixmap(self, pixmap):
        self._pixmap_item.setPixmap(pixmap)

    def record(self):
        print("record")
        self.record_points = True

    def delete(self):
        if self.selected_corner:
            print(f"delete corner: {self.__current_polygon.polygon().count()}")
            if self.__current_polygon.polygon().count() > 3:
                print("delete corner")
                self.remove_control_points()
                polygon = self.__current_polygon.polygon()
                polygon.remove(self.selected_corner[1])
                self.__current_polygon.setPolygon(polygon)
                self.selected_corner = None

        elif self.selected is not None:
            print("delete current")
            pprint(self.corner_points)
            for point, _ in self.corner_points:
                self.__scene.removeItem(point)
            self.__scene.removeItem(self.selected)
            self.selected = None



    def remove_control_points(self):
        """ removes the control points (i,e the ellipse)"""
        print("remove_control_points")
        for ellipse, _ in self.corner_points:
            self.__scene.removeItem(ellipse)
        self.corner_points = []

    def mousePressEvent(self, event):
        # super(CustomGraphicsScene, self).mousePressEvent(event)
        cursor_position = self.mapToScene(event.position().toPoint())
        print("cursor positon:", cursor_position)



        if (event.button() == Qt.MouseButton.LeftButton
            and self.control_key_pressed
            and not self.record_points):
            print("add a new point at position:" , cursor_position)
            if self.__current_polygon is not None:
                x, y = cursor_position.x(), cursor_position.y()
                # ellipse = self.__scene.addEllipse(QRectF(x - 3, y - 3, 5, 5),
                #     brush=QBrush(QColor("yellow")))

                # print(self.__current_polygon)
                points_list = self.__current_polygon.polygon().toVector()
                distances = list()
                for i, p in zip(range(len(points_list)), points_list):
                    diff = p - cursor_position
                    distance = diff.x()**2 + diff.y()**2
                    distances.append([distance, i])
                distances = sorted(distances, key=itemgetter(0))
                pprint(distances)

                poly_points = [self.__current_polygon.mapToScene(x) for x in self.__current_polygon.polygon()]
                if ((distances[0][1] == 0 and distances[1][1] == len(poly_points) - 1)
                    or (distances[0][1] == len(poly_points) - 1 and distances[1][1] == 0)):
                    poly_points.append(cursor_position)
                else:
                    index = max(distances[0][1], distances[1][1])
                    poly_points.insert(index, cursor_position)
                self.__current_polygon.setPolygon(QPolygonF(poly_points))
                # self.control_key_pressed = False


        if self.record_points:
            self.selected_corner = None
            if event.button() == Qt.MouseButton.RightButton:
                self.draw_polygon()
            elif event.button() == Qt.MouseButton.LeftButton:
                print("recording point")
                self.points_lst.append(cursor_position)
            return

        if event.button() == Qt.MouseButton.RightButton:
            self.selected_corner = None
            return

        # self.__scene.mousePressEvent(event)
        super(CustomGraphicsView, self).mousePressEvent(event)

        # pprint(self.corner_points)
        for point in self.corner_points:
            if point[0].contains(cursor_position):
                print("point selected")
                self.selected_corner = point
                return

        if self.__scene.selectedItems():
            print("items selected:", end ='')
            self.remove_control_points()

            self.__current_polygon = self.__scene.selectedItems()[0]
            # print(self.__current_polygon)
            self.poly_points = [self.__current_polygon.mapToScene(x) for x in self.__current_polygon.polygon()]

            for index, point in enumerate(self.poly_points):
                x, y = point.x(), point.y()
                ellipse = self.__scene.addEllipse(QRectF(x - 4, y - 4, 7, 7),
                                                  pen=QPen(QColor("red")))
                    # brush=QBrush(QColor("red")))
                ellipse.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
                self.corner_points.append((ellipse, index))
        else:
            self.__current_polygon = None
            self.remove_control_points()
            self.corner_points = []
            self.poly_points = []
            self.selected_corner = None


    def mouseMoveEvent(self, event) -> None:
        super(CustomGraphicsView, self).mouseMoveEvent(event)
        cursor_position = self.mapToScene(event.position().toPoint())
        if cursor_position.x() < 0:
            cursor_position.setX(0)
        if cursor_position.y() < 0:
            cursor_position.setY(0)
        if cursor_position.x() > self.size().width():
            cursor_position.setX(self.size().width())
        if cursor_position.y() > self.size().height():
            cursor_position.setY(self.size().height())
        # print("move:", cursor_position)

        if self.selected_corner:
            self.poly_points[self.selected_corner[1]] = QPointF(cursor_position)
            self.__current_polygon.setPolygon(QPolygonF(self.poly_points))

    # def mouseReleaseEvent(self, event) -> None:
    #     super(CustomGraphicsView, self).mouseReleaseEvent(event)
    #     self.selected_corner = None

    def draw_polygon(self):  # adds the polygon to the scene
        print("draw polygon")
        self.record_points = False

        if len(self.points_lst) > 2:
            polygon = self.__scene.addPolygon(QPolygonF(self.points_lst))
            polygon.setPen(QPen(Qt.red, 1, Qt.SolidLine))
            polygon.setFlags(QGraphicsItem.ItemIsSelectable)
            self.__current_polygon = polygon

        self.points_lst = []


    def keyPressEvent(self, event: QKeyEvent) -> None:
        print("key_pressed")
        key = event.key()
        if key in [Qt.Key.Key_Enter, Qt.Key.Key_Return]:
            self.draw_polygon()

        elif key == Qt.Key.Key_Insert:
            print("create a new polygon")
            self.record()

        elif key == Qt.Key.Key_Delete:
            print("delete a selected polygon")
            self.delete()

        if key == Qt.Key.Key_Control:
            self.control_key_pressed = True
        else:
            self.control_key_pressed = False

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        print("released")
        self.control_key_pressed = False

class MainWindow(QWidget):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.setLayout(QVBoxLayout())

        view = CustomGraphicsView()
        # scene = CustomGraphicsView()
        # view.setScene(scene)
        view.setPixmap(QPixmap("mask.png"))

        # record_btn = QPushButton(text="Record", clicked=view.record)
        # finish_btn = QPushButton(text="Finish", clicked=view.draw_polygon)

        self.layout().addWidget(view)
        # self.layout().addWidget(record_btn)
        # self.layout().addWidget(finish_btn)
        self.move(100,100)


def main():
    application = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(application.exec())



if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()

