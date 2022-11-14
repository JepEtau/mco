# -*- coding: utf-8 -*-

import time

from pprint import pprint
from logger import log

from PySide6.QtCore import (
    QPoint,
    Qt,
)
from PySide6.QtGui import (
    QPainter,
    QPen,
    QPolygon,
    QColor,
)
from PySide6.QtWidgets import QWidget


from common.sylesheet import set_stylesheet

class Widget_hist_graph(QWidget):
    GRID_COLOR = QColor(255, 255, 255)
    GRID_AXIS_COLOR = QColor(255, 255, 255)
    GRID_AXIS_WIDTH = 1
    CUVRE_PEN_WIDTH = 1
    GRAPH_WIDTH = 256

    def __init__(self, ui):
        super(Widget_hist_graph, self).__init__()

        # default width and sample count
        self.set_widget_width(self.GRAPH_WIDTH)
        self.setMinimumHeight(2*self.GRAPH_WIDTH)

        self.histograms = {'selected_channel': 'r',}
        for color in ['red', 'green', 'blue']:
            self.histograms.update({
                color[0]: {
                    'target': {
                        'curve': None,
                        'color': QColor(color)
                    },
                    'modified': {
                        'curve': None,
                        'color': QColor('white')
                    },
                }
            })

        self.set_enabled(False)
        self.set_time_tracking(False)
        set_stylesheet(self)
        self.adjustSize()

    def set_style(self, grid_color:QColor=None, grid_axis_color:QColor=None, pen_width:int=None):
        if grid_color is not None:
            self.GRID_COLOR = grid_color
        if grid_axis_color is not None:
            self.GRID_AXIS_COLOR = grid_axis_color
        if pen_width is not None:
            self.CUVRE_PEN_WIDTH = pen_width


    def set_widget_width(self, width):
        self.setMinimumWidth(width)
        self.sample_count = width
        self.adjustSize()


    def set_enabled(self, enabled:bool):
        self.is_enabled = enabled


    def set_time_tracking(self, enabled:bool):
        # print time consumption when refreshing this widget
        self.display_time_tracking = enabled


    def select_channel(self, k_channel):
        self.histograms['selected_channel'] = k_channel


    def display(self, histogram):
        if not self.is_enabled:
            return

        if histogram is not None:
            for k_channel in histogram.keys():
                self.histograms[k_channel]['target']['curve'] = histogram[k_channel]['target']
                self.histograms[k_channel]['modified']['curve'] = histogram[k_channel]['modified']
        self.repaint()


    def paintEvent(self, e):
        if self.display_time_tracking:
            timestamp = time.time()

        w = self.width()
        h = self.height()
        x_max = w - 1
        y_max = (h)
        # print("paintEvent: hist_graph: dimensions = (%d; %d)" % (w, h))

        # Current channel
        k_channel = self.histograms['selected_channel']

        # Histogram
        histogram = self.histograms[k_channel]

        painter = QPainter()
        if painter.begin(self):

            # Paint Borders and Grid
            pen = QPen(self.GRID_COLOR)
            pen.setWidth(self.GRID_AXIS_WIDTH)
            pen.setStyle(Qt.DotLine)
            painter.setPen(pen)
            for i in range(1, 9):
                x = int(i * w/8) - 1
                y = max(0, int((8-i) * h/8) - 1)
                # vertical axis
                painter.drawLine(x, 0, x, h-1)
                # horizontal axis
                painter.drawLine(0, y, w-1, y)

            pen.setStyle(Qt.SolidLine)
            pen.setColor(self.GRID_AXIS_COLOR)
            pen.setWidth(self.GRID_AXIS_WIDTH)
            painter.setPen(pen)
            painter.drawLine(0, 0, 0, h-1)
            painter.drawLine(0, h-1, w-1, h-1)

            if self.is_enabled:
                painter.setRenderHint(QPainter.Antialiasing)

                # Target and Source which is modified
                for k_curve in ['target', 'modified']:
                    pen = QPen(histogram[k_curve]['color'])
                    pen.setWidth(self.CUVRE_PEN_WIDTH)
                    pen.setStyle(Qt.SolidLine)
                    painter.setPen(pen)
                    polygon = QPolygon()

                    if histogram[k_curve]['curve'] is not None:
                        y_max = max(histogram[k_curve]['curve'])
                        # print("y_max = %d" % (y_max))
                        for x in range(len(histogram[k_curve]['curve'])):
                            px = int((x * self.sample_count) / len(histogram[k_curve]['curve']))
                            py = int(h * (1 - (histogram[k_curve]['curve'][x] / y_max)))
                            polygon.append(QPoint(px, py))
                            # print("x=%f\t p.x()=%f\tp.y()=%f" % (x, px, py))
                    else:
                        polygon.append(QPoint(0, 0))
                        polygon.append(QPoint(int((255 * w)/(self.sample_count)), 0))
                    painter.drawPolyline(polygon)

            painter.end()

            if self.display_time_tracking:
                print("histogram: %.1f" % (1000* (time.time() - timestamp)))


