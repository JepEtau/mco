#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import signal
import sys
import cv2
from PySide6.QtCore import (
    QPoint,
    Qt,
    QRectF,

)
from PySide6.QtGui import (
    QBrush,
    QPen,
    QPixmap,
    QPolygonF,
    QKeyEvent,
)
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QGraphicsScene,
    QGraphicsPolygonItem,
    QGraphicsView,
    QGraphicsPixmapItem,
    QGraphicsItem,

)

# https://stackoverflow.com/questions/69421799/how-to-resize-polygon-by-dragging-its-corners

from pprint import pprint

class CustomGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        scene = QGraphicsScene(self)
        self.setScene(scene)

        self._pixmap_item = QGraphicsPixmapItem()
        scene.addItem(self.pixmap_item)

        self.roi = list()
        # _polygon = QGraphicsPolygonItem(self.pixmap_item)
        # _polygon.setPen(QPen(Qt.red, 2, Qt.SolidLine))
        # self.roi.append({
        #     'polygon': _polygon,
        #     'points': list()
        # })
        self.selected = None
        self.__is_editing = False
        # self.polygon_item.setBrush(QBrush(Qt.red, Qt.VerPattern))

    @property
    def pixmap_item(self):
        return self._pixmap_item


    def setPixmap(self, pixmap):
        self.pixmap_item.setPixmap(pixmap)

    def resizeEvent(self, event):
        self.fitInView(self.pixmap_item, Qt.KeepAspectRatio)
        super().resizeEvent(event)


    def mouseMoveEvent(self, event) -> None:
        super(CustomGraphicsView, self).mouseMoveEvent(event)
        if self.__is_editing:

        if self.selected_corner:
            self.__s
            self.poly_points[self.selected_corner[1]] = QPointF(event.scenePos())
            self.selected.setPolygon(QPolygonF(self.poly_points))


    def mousePressEvent(self, event):
        # lp =
        point = self.mapToScene(event.position().toPoint())

        if self.__is_editing:
            roi = self.roi[self.selected]
            roi['points'].append(lp)
            # roi['polygon'].add(lp)
            poly = roi['polygon'].polygon()
            poly.append(point)
            roi['polygon'].setPolygon(poly)
            return

        # Catch the point
        for roi in self.roi:
            for point in roi['points']:
                if point[0].contains(event.scenePos()):
                    self.selected_corner = point
                    return

        # lp = self.pixmap_item.mapFromScene(sp)
        try:
            roi = self.roi[self.selected]
        except:
            for point in self.corner_points:
                if point[0].contains(event.position()):
                    self.selected_corner = point
                    return

            return



    def add_point(self):
        if self.selected is not None:
            polygon = self.addPolygon(QPolygonF(self.points_lst))
            polygon.setFlags(QGraphicsItem.ItemIsSelectable)
            self.points_lst = []



    def mouseReleaseEvent(self, event) -> None:
        super(CustomGraphicsView, self).mouseReleaseEvent(event)
        self.selected_corner = None


    def keyPressEvent(self, event: QKeyEvent) -> None:
        print("key_pressed")
        key = event.key()
        if key in [Qt.Key.Key_Enter, Qt.Key.Key_Return]:
            # pprint(self.items())
            # for item in self.items():
            #     if type(item) is QGraphicsPolygonItem:
            #         print(item.shape())
            print(self.roi[self.selected]['points'])
            self.selected = None
            self.__is_editing = False

        if key == Qt.Key.Key_N:
            print("create a new polygon")
            _polygon = QGraphicsPolygonItem(self.pixmap_item)
            _polygon.setPen(QPen(Qt.red, 2, Qt.SolidLine))
            _polygon.setFlags(QGraphicsItem.ItemIsSelectable)
            self.roi.append({
                'polygon': _polygon,
                'points': list()
            })
            self.selected = len(self.roi) - 1

            self.__is_editing = True

            event.accept()
            return



        return super().keyPressEvent(event)


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        view = CustomGraphicsView()
        self.setCentralWidget(view)

        view.setPixmap(QPixmap("mask.png"))

        self.resize(640, 480)



def main():
    application = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(application.exec())



if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()

