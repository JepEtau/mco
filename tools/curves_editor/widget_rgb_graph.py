#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import numpy as np
from copy import deepcopy
import gc

from pprint import pprint
from logger import log

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

class Widget_rgb_graph(QWidget):
    signal_point_selected = Signal(list)
    signal_graph_modified = Signal(str)


    GRID_COLOR = QColor(255, 255, 255)
    GRID_AXIS_COLOR = QColor(255, 255, 255)
    GRID_AXIS_WIDTH = 1
    CURVE_PEN_WIDTH = 1
    SELECTED_POINT_COLOR = QColor(230, 230, 230)
    UNSELECTED_POINT_COLOR = QColor(210, 210, 210)
    GRAPH_WIDTH = 512


    def __init__(self, ui):
        super(Widget_rgb_graph, self).__init__()

        self.ui = ui
        # palette = Tools_palette()
        # self.setPalette(palette.get_palette())

        # Initialize R, G, B, master channels
        self.channels = {
            'r': {'color': QColor('red')},
            'g': {'color': QColor('green')},
            'b': {'color': QColor('blue')},
            'm': {'color': QColor('white')},
        }
        for k in self.channels.keys():
            self.channels[k]['curve'] = Curve()
            self.channels[k]['lut'] = np.array([]).astype('int')
            self.channels[k]['polypoints'] = np.array([]).astype('int')
            self.channels[k]['is_selected'] = False
        # Update 'lut' for each channel
        self.update_lookup_tables()

        # Current channel is master, in normal mode
        self.k_selected = 'm'
        self.channels[self.k_selected]['is_selected'] = True
        self.m_state = 'normal'

        # Display a vertical line on this graph
        self.show_position = False
        self.current_position_x = 0
        self.current_position_rgb = {'r': 0, 'g': 0, 'b': 0, 'm': 0}

        self.is_modified = False
        self.is_enabled = True

    def set_model(self, model):
        self.model = model
        # Connect signals
        self.model.signal_load_curves[dict].connect(self.event_load_curves)

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


    def event_load_curves(self, channels:dict):
        if channels is not None:
            log.info("load curves in RGB graph")
            # print("%s.event_load_curves: load curves in RGB graph" % (__name__))
            # pprint(channels)
            for k in self.channels.keys():
                if self.channels[k]['curve'] is not None:
                    del self.channels[k]['curve']
                self.channels[k]['curve'] = deepcopy(channels[k])
                self.channels[k]['lut'] = np.array([]).astype('int')
                self.channels[k]['polypoints'] = np.array([]).astype('int')
                self.channels[k]['is_selected'] = False
        else:
            log.info("reset RGB graph as none channels provided")
            for k in self.channels.keys():
                self.channels[k]['curve'] = Curve()
                self.channels[k]['lut'] = np.array([]).astype('int')
                self.channels[k]['polypoints'] = np.array([]).astype('int')
                self.channels[k]['is_selected'] = False
        self.update_lookup_tables()
        self.is_modified = False

        # Current channel is master, in normal mode
        if channels is not None and 'selected' in channels.keys():
            self.k_selected = channels['selected']
        else:
            self.k_selected = 'm'
        self.channels[self.k_selected]['is_selected'] = True
        self.m_state = 'normal'

        # Display a vertical line on this graphe when clicking on image
        self.show_position = False
        self.current_position_x = 0
        self.current_position_rgb = {'r': 0, 'g': 0, 'b': 0, 'm': 0}

        self.repaint()
        self.signal_graph_modified.emit('loaded')



    def get_curves_channels(self):
        if not self.is_modified:
            log.info("curves have not been edited")
            return None
        # return curves channels
        if self.channels is not None:
            # print("get_curves_channels: !!!curves modified")
            tmpDict = {
                'r': self.channels['r']['curve'],
                'g': self.channels['g']['curve'],
                'b': self.channels['b']['curve'],
                'm': self.channels['m']['curve'],
                'selected': self.k_selected,
            }
            return tmpDict
        else:
            log.info("curves have not been modified")
            # print("get_curves_channels: curves have not been modified")
            return None

    def print_points(self):
        # Print points for debug purpose
        for k in self.channels:
            print("[%s]" % (k))
            for p in self.channels[k]['curve'].points():
                print("\t[%f;%f]" % (p.x(), p.y()))


    def reset_channel(self, channel=''):
        # Reset the graph for a specified/all/current channel
        log.info("reset channel: %s" % (channel))
        if channel == 'all':
            for c in ['r', 'g', 'b', 'm']:
                self.channels[c]['curve'].reset()
                self.select('m')
        elif channel == 'current':
            self.channels[self.k_selected]['curve'].reset()
        self.flush_polypoints()
        self.update_lookup_tables()
        self.update()
        self.is_modified = True

        self.signal_graph_modified.emit('reset_%s' % (channel))
        self.signal_point_selected.emit([-1, 0])


    def paintEvent(self, e):
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
            # painter.setPen()
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


    def update_rgb_value(self, r, g, b):
        if r is None or g is None or b is None:
            # hide position lines
            self.show_position = False
        else:
            self.show_position = True
            m = int((r+g+b) / 3.0)
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
                # del self.channels[k]['lut']
                # self.channels[k]['lut'] = np.array([]).astype('int')
        gc.collect()


    def update_lookup_tables(self, verbose=False):
        lut_m = np.clip(((255 * self.channels['m']['curve'].calculate(256, depth=1000) + 0.5) / 1000),0,255).astype('int')
        if verbose:
            print("--------------- update_lookup_tables: master (%d) -------------------" % (len(lut_m)))
            pprint.pprint(lut_m)
            # sys.exit()

        for k in ['r', 'g', 'b']:
            _lut = np.clip(((255 * self.channels[k]['curve'].calculate(256, depth=1000) + 0.5) / 1000), 0, 255).astype('int')
            try:
                self.channels[k]['lut'] = _lut[lut_m].astype('uint8')
            except:
                print("error")
                print("--------------- update_lookup_tables: master (%d) -------------------" % (len(lut_m)))
                pprint.pprint(lut_m)

                print("--------------- update_lookup_tables: %s (%d) -------------------" % (k, len(_lut)))
                pprint.pprint(_lut)

                # print("--------------- update_lookup_tables: _lut[lut_m] (%d) -------------------" % (len(_lut[lut_m])))
                # pprint.pprint(_lut[lut_m])
                sys.exit()

        if verbose:
            for k in ['r', 'g', 'b']:
                print("--------------- update_lookup_tables: %s (%d) -------------------" % (k, len(self.channels[k]['lut'])))
                pprint.pprint(self.channels[k]['lut'])


    def channel_lut(self, channel):
        # Return the lut for a channel
        # print("--------------- %s -------------------" % (channel))
        # pprint.pprint(self.channels[channel]['lut'])
        return self.channels[channel]['lut']


    def point_to_coordinates(self, p):
        depth = 256.0
        x = int(p.x() * (depth - 1) + .5)
        y = int(p.y() * (depth - 1) + .5)
        return [x, y]


    def mousePressEvent(self, event):
        if not self.is_enabled:
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
                        self.update_lookup_tables()
                        self.update()
                        self.is_modified = True
                        # self.ui.set_curves_modification(True)

                        self.signal_point_selected.emit(self.point_to_coordinates(selected_point))
                        self.signal_graph_modified.emit('modified')

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
                    self.update_lookup_tables()
                    self.update()
                    self.is_modified = True
                    # self.ui.set_curves_modification(True)
                    self.signal_point_selected.emit([-1, 0])

                self.signal_graph_modified.emit('modified')


    # def mouseReleaseEvent(self, event):
    #     print("mouse button release, send a signal to update the model")
    #     self.signal_graph_modified.emit('modified')


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
                self.signal_graph_modified.emit('modified')


            self.flush_polypoints()
            self.update_lookup_tables()
            self.update()
            self.is_modified = True

            current_selected_point = curve.selected_point()
            if current_selected_point is not None:
                self.signal_point_selected.emit(self.point_to_coordinates(selected_point))
            else:
                self.signal_point_selected.emit([-1, 0])
            self.signal_graph_modified.emit('modified')



    def select(self, channel):
        # Select a channel (and unselect previous)
        self.channels[self.k_selected]['is_selected'] = False
        self.k_selected = channel
        self.current_position_x = self.current_position_rgb[self.k_selected]
        self.channels[self.k_selected]['is_selected'] = True
        self.update()





    def keyPressEvent(self, event):
        key = event.key()
        modifiers = event.modifiers()
        print("%s.keyPressEvent: %d" % (__name__, event.key))
        curve = self.channels[self.k_selected]['curve']

        if key == Qt.Key_Delete or key == Qt.Key_Backspace:
            curve.remove_selected_point()
            self.flush_polypoints()
            self.update_lookup_tables()
            self.update()
            self.is_modified = True
            self.signal_graph_modified.emit('modified')
            event.accept()

        elif key == Qt.Key_R:
            self.select('r')
            event.accept()
        elif key == Qt.Key_G:
            self.select('g')
            event.accept()
        elif key == Qt.Key_B:
            self.select('b')
            event.accept()
        elif key == Qt.Key_A or key == Qt.Key_M:
            self.select('m')
            event.accept()

        elif key == Qt.Key_C:
            curve.reset()

            self.flush_polypoints()
            self.update_lookup_tables()
            self.update()
            self.is_modified = True
            self.signal_graph_modified.emit()
            event.accept()

        else:
            print("Widget_rgb_graph::key=%d" % (key))
            super().keyPressEvent(event)