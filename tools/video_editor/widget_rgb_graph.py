# -*- coding: utf-8 -*-

import sys
sys.path.append('../scripts')
from copy import deepcopy
import numpy as np

from logger import log
from pprint import pprint

from PySide6.QtCore import (
    QPoint,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QPainter,
    QPen,
    QPolygon,
)
from PySide6.QtWidgets import (
    QSizePolicy,
    QWidget,
)

from images.curve import Curve
from images.curve import Curve_point
from common.sylesheet import set_stylesheet
from video_editor.model_video_editor import Model_video_editor

class Widget_rgb_graph(QWidget):
    signal_point_selected = Signal(list)
    signal_graph_modified = Signal(dict)

    GRID_COLOR = QColor(255, 255, 255)
    GRID_AXIS_COLOR = QColor(255, 255, 255)
    GRID_AXIS_WIDTH = 1
    CURVE_PEN_WIDTH = 1
    SELECTED_POINT_COLOR = QColor(230, 230, 230)
    UNSELECTED_POINT_COLOR = QColor(210, 210, 210)
    GRAPH_WIDTH = 512


    def __init__(self, parent):
        super(Widget_rgb_graph, self).__init__()
        self.model = None

        self.setAttribute(Qt.WA_DeleteOnClose)

        # Initialize R, G, B, master channels
        self.channels = {
            'r': {'color': QColor('red')},
            'g': {'color': QColor('green')},
            'b': {'color': QColor('blue')},
            'm': {'color': QColor('white')},
        }

        # Initialize default curves
        for k in self.channels.keys():
            self.channels[k]['curve'] = Curve()
            self.channels[k]['lut'] = np.array([]).astype('int')
            self.channels[k]['polypoints'] = np.array([]).astype('int')
            self.channels[k]['is_selected'] = False

        # Update LUT for each channel

        # Current channel is master
        self.k_selected = 'm'
        self.channels[self.k_selected]['is_selected'] = True

        # Display a vertical line on this graph
        self.show_position = False
        self.current_position_x = 0
        self.current_position_rgb = {'r': 0, 'g': 0, 'b': 0, 'm': 0}

        self.is_enabled = True


    def set_model(self, model:Model_video_editor):
        self.model = model

        # Connect signals
        self.model.signal_load_curves[dict].connect(self.event_curves_loaded)


    def set_ui(self, ui):
        self.ui = ui


    def set_enabled(self, enabled):
        self.setEnabled(enabled)


    def set_style(self, grid_color:QColor=None, grid_axis_color:QColor=None, pen_width:int=None,
                    selected_point_color:QColor=None, unselected_point_color:QColor=None):
        log.info("set style")
        if grid_color is not None:
            self.GRID_COLOR = grid_color
        if grid_axis_color is not None:
            self.GRID_AXIS_COLOR = grid_axis_color
        if pen_width is not None:
            self.CURVE_PEN_WIDTH = pen_width
        if selected_point_color is not None:
            self.SELECTED_POINT_COLOR = selected_point_color
        if unselected_point_color is not None:
            self.UNSELECTED_POINT_COLOR = unselected_point_color


    def set_widget_width(self, width):
        self.setMinimumWidth(width)
        self.sample_count = width

        size_policy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.MinimumExpanding)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(size_policy)
        self.setMinimumHeight(width)
        self.adjustSize()


    def event_curves_loaded(self, curves:dict):
        if curves is not None:
            log.info("load curves in RGB graph")
            # print("%s.event_load_curves: load curves in RGB graph" % (__name__))
            for k in self.channels.keys():
                if self.channels[k]['curve'] is not None:
                    del self.channels[k]['curve']
                self.channels[k]['curve'] = deepcopy(curves['channels'][k])
                self.channels[k]['lut'] = np.array([]).astype('int')
                self.channels[k]['polypoints'] = np.array([]).astype('int')
                self.channels[k]['is_selected'] = False
        else:
            # log.info("reset RGB graph as there is no channels")
            for k in self.channels.keys():
                self.channels[k]['curve'] = Curve()
                self.channels[k]['lut'] = np.array([]).astype('int')
                self.channels[k]['polypoints'] = np.array([]).astype('int')
                self.channels[k]['is_selected'] = False
        self.update()


    def get_curves_channels(self):
        # Returns a dict of curves
        try:
            # print("get_curves_channels: !!!curves modified")
            rgb_curves = {
                'r': self.channels['r']['curve'],
                'g': self.channels['g']['curve'],
                'b': self.channels['b']['curve'],
                'm': self.channels['m']['curve'],
                'selected': self.k_selected,
            }
            return rgb_curves
        except:
            log.info("curves have not been modified or channels are None")
            # print("get_curves_channels: curves have not been modified")
            return None


    def refresh_rgb_value(self, bgr):
        self.show_position = False
        if bgr is not None:
            self.show_position = True
            b, g, r = list(map(lambda x:int(x), bgr))
            m = int((r + g + b) / 3.0)
            if self.k_selected == 'r':
                self.current_position_x = r
            elif self.k_selected == 'g':
                self.current_position_x = g
            elif self.k_selected == 'b':
                self.current_position_x = b
            elif self.k_selected == 'm':
                self.current_position_x = m
            self.current_position_rgb = {'r': r, 'g': g, 'b': b, 'm': m}
        self.update()


    def flush_polypoints(self):
        for k in ['r', 'g', 'b', 'm']:
            if self.k_selected == k or self.k_selected == 'm':
                del self.channels[k]['polypoints']
                self.channels[k]['polypoints'] = np.array([]).astype('int')


    def reset_channel(self, channel:str=''):
        # Reset the graph for a specified/all/current channel
        log.info("reset channel: %s" % (channel))
        if channel == 'all':
            for c in ['r', 'g', 'b', 'm']:
                self.channels[c]['curve'].reset()
                del self.channels[c]['polypoints']
                self.channels[c]['polypoints'] = np.array([]).astype('int')

        elif channel == 'current':
            self.channels[self.k_selected]['curve'].reset()
            self.flush_polypoints()

        self.update()

        self.signal_graph_modified.emit(self.get_curves_channels())
        self.signal_point_selected.emit([-1, 0])


    def point_to_coordinates(self, p:Curve_point):
        # Convert a Point to coordinates
        depth = 256.0
        x = int(p.x() * (depth - 1) + .5)
        y = int(p.y() * (depth - 1) + .5)
        return [x, y]


    def select_channel(self, channel:str='m'):
        # log.info("select channel [%s]" % (channel))
        # Deselect current channel
        self.channels[self.k_selected]['is_selected'] = False

        # Select the specified channel
        self.k_selected = channel
        self.current_position_x = self.current_position_rgb[self.k_selected]
        self.channels[self.k_selected]['is_selected'] = True

        self.update()


    def mousePressEvent(self, event):
        if not self.is_enabled:
            return

        if not self.ui.was_active():
            # Just changed editor, do not add a new point
            return

        w = float(self.width())
        h = float(self.height())
        x_max = w - 1
        y_max = h - 1
        x = float(event.pos().x())
        y = h - event.pos().y()

        # x(px) -> xf [0;1.0]
        # y(px) -> yf [0;1.0]
        # print("(%d; %d) in %d x %d" % (x, y, w, h))
        xf = np.float32(x) / x_max
        yf = np.float32(y) / y_max

        curve = self.channels[self.k_selected]['curve']
        if event.button() == Qt.LeftButton:
            # print("mousePressEvent: (%d; %d) in (%d;%d) -> (%f; %f)" % (x, y, x_max, y_max, xf, yf))
            is_selected = curve.select_point(xf, yf)
            if is_selected:
                self.update()
                selected_point = curve.selected_point()
                self.m_grab_offset_x_f = selected_point.x() - xf
                self.m_grab_offset_y_f = selected_point.y() - yf

                self.signal_point_selected.emit(self.point_to_coordinates(selected_point))

            else:
                x = float(event.pos().x() + (3))
                y = h - event.pos().y() - (3 + 2)

                # x(px) -> xf [0;1.0]
                # y(px) -> yf [0;1.0]
                xf = np.float32(x) / x_max
                yf = np.float32(y) / y_max


                if curve.add_point(xf, yf):
                    if curve.select_point(xf, yf):
                        selected_point = curve.selected_point()
                        self.m_grab_offset_x_f = selected_point.x() - xf
                        self.m_grab_offset_y_f = selected_point.y() - yf

                        self.flush_polypoints()
                        self.update()
                        # self.ui.set_curves_modification(True)

                        self.signal_point_selected.emit(self.point_to_coordinates(selected_point))
                        self.signal_graph_modified.emit(self.get_curves_channels())

                    else:
                        print("\terror: cannot select new added point @(%f, %f)" % (xf, yf))
                else:
                    print("\terror: creation failed @(%f, %f)" % (xf, yf))

        elif event.button() == Qt.RightButton:
            is_selected = curve.select_point(xf, yf)
            if is_selected:
                selected_point = curve.selected_point()
                if selected_point.x() != 0.0 and selected_point.x() != 1.0:
                    curve.remove_selected_point()
                    self.flush_polypoints()
                    self.update()
                    # self.ui.set_curves_modification(True)
                    self.signal_point_selected.emit([-1, 0])

                self.signal_graph_modified.emit(self.get_curves_channels())


    def mouseMoveEvent(self, event):
        verbose = False
        if not self.is_enabled:
            return
        w = float(self.width())
        h = float(self.height())
        x_max = w - 1
        y_max = h - 1
        x = np.float32(event.pos().x())
        y = h - event.pos().y()

        # x(px) -> xf [0;1.0]
        # y(px) -> yf [0;1.0]
        xf = np.float32(x) / x_max
        yf = np.float32(y) / y_max

        self.show_position = False

        curve = self.channels[self.k_selected]['curve']
        selected_point = curve.selected_point()
        if selected_point is not None:
            if verbose:
                print("mouseMoveEvent: offsets = [%.03f; %.03f]" % (self.m_grab_offset_x_f, self.m_grab_offset_y_f))
            xf += self.m_grab_offset_x_f
            yf -= self.m_grab_offset_y_f

            xLow = curve.grab_range()[0] + 1/(256.0 * x_max)
            xHigh = curve.grab_range()[1] - 1/(256.0 * x_max)

            if verbose:
                print("[xLow, xHigh] = [%.03f; %.03f]" % (xLow, xHigh))
            isOutside = False
            gap = 80
            if (xf < xLow - gap/w or xf > xHigh + gap/w
                or yf > 1.0 + gap/h or yf < -1*gap/h):
                isOutside = True
                print("\tisOutside, pointsCount=%d" % (curve.point_count()))

            xf = np.clip(xf, xLow, xHigh)
            yf = np.clip(yf, 0.0, 1.0)

            if not isOutside:
                # print("\t-> move: (%.03f; %.03f) -> (%.03f; %.03f)" % (selected_point.x(), selected_point.y(), xf, yf))
                curve.move_selected_point(xf, yf)
            else:
                # print("\t-> remove point")
                curve.remove_selected_point()
                self.signal_graph_modified.emit(self.get_curves_channels())

            self.flush_polypoints()
            self.update()

            current_selected_point = curve.selected_point()
            if current_selected_point is not None:
                self.signal_point_selected.emit(self.point_to_coordinates(selected_point))
            else:
                self.signal_point_selected.emit([-1, 0])
            self.signal_graph_modified.emit(self.get_curves_channels())


    def keyPressEvent(self, event):
        if self.event_key_pressed(event):
            event.accept()
            return True
        return self.ui.keyPressEvent(event)


    def event_key_pressed(self, event):
        key = event.key()

        if key == Qt.Key_Delete or key == Qt.Key_Backspace:
            curve = self.channels[self.k_selected]['curve']
            if not curve.selected_point():
                # do nothing
                return True
            curve.remove_selected_point()
            self.flush_polypoints()
            self.update()
            self.signal_graph_modified.emit(self.get_curves_channels())
            return True


        elif key == Qt.Key_C:
            curve = self.channels[self.k_selected]['curve']
            curve.reset()
            self.flush_polypoints()
            self.update()
            self.signal_graph_modified.emit(self.get_curves_channels())
            return True

        return False


    def paintEvent(self, event):
        w = self.width()
        h = self.height()
        x_max = w - 1
        y_max = h - 1

        # print("paintEvent: dimensions = (%d; %d)" % (w, h))

        painter = QPainter()
        if painter.begin(self):
            # Paint Borders and Grid
            pen = QPen(self.GRID_COLOR)
            pen.setWidth(self.GRID_AXIS_WIDTH)
            pen.setStyle(Qt.DotLine)
            painter.setPen(pen)
            painter.drawRect(0, 0, x_max, y_max)
            for i in range(1, 8):
                x = int(i * w/8) - 1
                y = int(i * h/8) - 1
                painter.drawLine(x, 0, x, y_max)
                painter.drawLine(0, y, x_max, y)

            painter.setRenderHint(QPainter.Antialiasing)

            # Draw unselected channels
            for curve in self.channels.values():
                if not curve['is_selected']:
                    if len(curve['polypoints']) != w:
                        lut = curve['curve'].calculate(sample_count=self.sample_count, verbose=False)
                        curve['polypoints'] = (y_max * (1.0 - lut)).astype(int)

                    pen = QPen(curve['color'])
                    pen.setWidth(self.CURVE_PEN_WIDTH)
                    painter.setPen(pen)
                    polygon = QPolygon()
                    for x in range(len(curve['polypoints'])):
                        px = int((np.float32(x) * x_max)/(self.sample_count-1))
                        py = int(curve['polypoints'][x])
                        polygon.append(QPoint(px, py))
                    painter.drawPolyline(polygon)


            # Draw selected channel
            curve = self.channels[self.k_selected]
            # print("----- %s -----" % (curve['color']))
            # for p in curve['curve'].points():
            #     print("\t[%f;%f]" % (p.x(), p.y()))

            # startTime = time.time()
            if len(curve['polypoints']) != w:
                lut = curve['curve'].calculate(sample_count=self.sample_count, verbose=False)
                curve['polypoints'] = (y_max * (1.0 - lut)).astype(int)

            pen = QPen(curve['color'])
            pen.setWidth(self.CURVE_PEN_WIDTH)
            pen.setStyle(Qt.SolidLine)
            painter.setPen(pen)
            polygon = QPolygon()
            for x in range(len(curve['polypoints'])):
                px = int((np.float32(x) * x_max)/(self.sample_count-1))
                py = int(curve['polypoints'][x])
                polygon.append(QPoint(px, py))
                # print("    x=%.1f    p.x()=%.1f    y=%.1f\    p.y()=%.1f" % (x, px, curve['polypoints'][x], py))
            painter.drawPolyline(polygon)

            # Draw points
            pen.setWidth(2)
            painter.setPen(pen)
            for p in curve['curve'].points():
                if p == curve['curve'].selected_point():
                    painter.setBrush(QBrush(self.SELECTED_POINT_COLOR))
                else:
                    painter.setBrush(Qt.NoBrush)
                px = p.x() * x_max
                py = int(h * (1 - p.y()))
                painter.drawEllipse(QPoint(px, py), 3, 3)
            painter.setBrush(Qt.NoBrush)

            # Draw position line on this graph
            if self.show_position:
                # log.info("show position")
                # curve = self.channels[self.k_selected]['curve']
                # self.channels[self.k_selected]['polypoints'][self.current_position_x*w/256]
                # y = h *  (1 - curve.value(float(self.current_position_x) / (self.sample_count-1)))

                painter.setRenderHint(QPainter.Antialiasing, False)
                pen = QPen(QColor(255, 255, 255))
                pen.setWidth(1)
                pen.setStyle(Qt.DotLine)
                painter.setPen(pen)
                # painter.drawLine(0, int(y), w-1, int(y))
                position_x = int((w-1) * (self.current_position_x / (self.sample_count-1)) * (self.sample_count / 256))
                # print("x=%f, position_x=%f" % (self.current_position_x, position_x))
                painter.drawLine(position_x, 0, position_x, y_max)

            painter.end()