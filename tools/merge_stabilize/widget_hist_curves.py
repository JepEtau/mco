#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
sys.path.append('../scripts')
import numpy as np
from pprint import pprint
from logger import log

from PySide6.QtCore import (
    QPoint,
    Qt,
    Signal,
)
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import (
    QBrush,
    QColor,
    QPainter,
    QPen,
    QPolygon,
)
from common.widget_common import Widget_common
from common.sylesheet import set_stylesheet

from images.curve import (
    Curve,
    Curve_point,
    calculate_lut_for_bgd,
)


class Widget_hist_curve(Widget_common):
    signal_point_selected = Signal(list)
    # Current curves have been modified, the model shall be updated
    signal_curves_modified = Signal(str)
    # Current is being edited, update image but not the model to optimize time processing
    signal_curves_editing = Signal()

    GRID_COLOR = QColor(255, 255, 255)
    GRID_AXIS_COLOR = QColor(255, 255, 255)
    GRID_AXIS_WIDTH = 1
    CURVE_PEN_WIDTH = 1
    SELECTED_POINT_COLOR = QColor(230, 230, 230)
    UNSELECTED_POINT_COLOR = QColor(210, 210, 210)
    GRAPH_WIDTH = 256

    def __init__(self, ui):
        super(Widget_hist_curve, self).__init__()
        self.ui = ui
        self.setObjectName('hist_curves')

        # default width and sample count
        self.set_widget_width(self.GRAPH_WIDTH)
        self.setMinimumHeight(255)

        self.curves = {
            'k_curves': ''
        }
        for c in ['red', 'green', 'blue']:
            self.curves.update({
                c[0]: {
                    'color': QColor(c),
                    'curve': Curve(is_default_constant=True),
                    'polypoints': np.array([]).astype('int'),
                    'lut': np.array([]).astype('int'),
                }
            })

        self.k_selected_channel = 'r'
        self.k_curves = ''
        self.set_enabled(False)
        self.is_modified = False
        self.is_moving_point = False

        self.update_lookup_tables()
        set_stylesheet(self)
        self.adjustSize()


    def set_style(self, grid_color:QColor=None, grid_axis_color:QColor=None, pen_width:int=None,
                    selected_point_color:QColor=None, unselected_point_color:QColor=None,
                    margin:int=None):
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
        # self.adjustSize()


    def set_enabled(self, enabled:bool):
        self.is_enabled = enabled


    def select_channel(self, k_channel):
        self.k_selected_channel = k_channel
        self.update()


    def load_curves(self, curves:dict):
        if curves is not None:
            log.info("load stitching curves: %s" % (curves['k_curves']))
            print("%s.event_load_curves: load curves [%s] in RGB graph" % (__name__, curves['k_curves']))
            points = curves['points']
            for c in ['r', 'g', 'b']:
                curve = self.curves[c]['curve']
                if curve is not None:
                    curve.remove_all_points()
                else:
                    self.curves[c]['curve'] = Curve(is_default_constant=True)
                    curve = self.curves[c]['curve']
                for p in points[c]:
                    if type(p) is Curve_point:
                        curve.add_point(p.x(), p.y())
                    else:
                        curve.add_point(p[0], p[1])
                self.curves[c]['lut'] = np.array([]).astype('int')
                self.curves[c]['polypoints'] = np.array([]).astype('int')
                self.curves[c]['is_selected'] = False
            self.curves['k_curves'] = curves['k_curves']
        else:
            log.info("use empty stitching curves")
            self.k_curves = ''
            for c in ['r', 'g', 'b']:
                self.curves[c]['curve'] = Curve(is_default_constant=True)
                self.curves[c]['lut'] = np.array([]).astype('int')
                self.curves[c]['polypoints'] = np.array([]).astype('int')
                self.curves[c]['is_selected'] = False
            self.curves['k_curves'] = ''

        self.curves[self.k_selected_channel]['is_selected'] = True
        self.is_modified = False

        # Calculate LUTs
        self.update_lookup_tables()

        self.repaint()


    def remove_selected_point(self):
        self.curves[self.k_selected_channel]['curve'].remove_selected_point(min_points_count=1)
        self.flush_polypoints()
        self.update_lookup_tables()
        self.update()
        self.is_modified = True
        self.signal_curves_modified.emit('modified')


    def get_curves(self):
        # if not self.is_modified:
        #     # log.info("curves have not been modified")
        #     print("\n!!!error: curves have not been modified!")
        #     return None

        curves = {
            'k_curves': self.curves['k_curves'],
            'points': {
                'r': self.curves['r']['curve'].points(),
                'g': self.curves['g']['curve'].points(),
                'b': self.curves['b']['curve'].points(),
            },
            'lut': {
                'r': self.curves['r']['lut'],
                'g': self.curves['g']['lut'],
                'b': self.curves['b']['lut'],
            }
        }
        return curves


    def get_curve_luts(self):
        return {
                'r': self.curves['r']['lut'],
                'g': self.curves['g']['lut'],
                'b': self.curves['b']['lut'],
        }

    # def channel_lut(self, k_channel):
    #     # Return the lut of a channel
    #     return self.curves[k_channel]['lut']



    def reset_channel(self, channel:str=None):
        # Reset the graph for a specified/all/current channel
        log.info("reset channel: %s" % (channel))
        if channel == 'all':
            for c in ['r', 'g', 'b']:
                self.curves[c]['curve'].reset(is_default_constant=True)
        else:
            # Reset current channel only
            self.curves[self.k_selected_channel]['curve'].reset(is_default_constant=True)
        self.flush_polypoints()
        self.update_lookup_tables()
        self.update()
        self.is_modified = True
        self.signal_curves_modified.emit('modified')
        self.signal_point_selected.emit([-1, 0])


    def paintEvent(self, e):
        w = self.width()
        h = self.height()
        x_max = w - 1
        # print("paintEvent: hist_curve: dimensions = (%d; %d), x_max=%d" % (w, h, x_max))

        # Current channel
        k_channel = self.k_selected_channel

        # Curves
        curve = self.curves[k_channel]

        painter = QPainter()
        if painter.begin(self):

            # Paint Borders and Grid
            pen = QPen(self.GRID_COLOR)
            pen.setWidth(self.GRID_AXIS_WIDTH)
            pen.setStyle(Qt.DotLine)
            painter.setPen(pen)
            painter.drawRect(0, 0, w-1, h-1)
            for i in range(0, 8):
                # vertical axis
                x = int(i * w/8)-1
                painter.drawLine(x, 0, x, h-1)
                # horizontal axis
                y = max(0, int(i * h/8)-1)
                painter.drawLine(0, y, w-1, y)

            pen.setStyle(Qt.SolidLine)
            pen.setWidth(self.GRID_AXIS_WIDTH)
            pen.setColor(self.GRID_AXIS_COLOR)
            painter.setPen(pen)
            painter.drawLine(0, int(h/2) - 1, w, int(h/2) - 1)

            if self.is_enabled:
                painter.setRenderHint(QPainter.Antialiasing)

                # Draw selected channel
                pen = QPen(QColor('white'))
                pen.setWidth(self.CURVE_PEN_WIDTH)
                pen.setStyle(Qt.SolidLine)
                painter.setPen(pen)
                polygon = QPolygon()

                if len(curve['polypoints']) != w:
                    # width/points have been modified, update the array of polypoints
                    lut = curve['curve'].calculate(sample_count=self.sample_count, verbose=False)
                    curve['polypoints'] = lut - 0.5
                    # print("polypoints (%d) = " % (len(curve['polypoints'])), curve['polypoints'])

                pen = QPen(curve['color'])
                pen.setWidth(self.CURVE_PEN_WIDTH)
                pen.setStyle(Qt.SolidLine)
                painter.setPen(pen)
                polygon = QPolygon()
                for x in range(len(curve['polypoints'])):
                    px = int((np.float32(x) * x_max)/(self.sample_count-1))
                    py = (0.5 - curve['polypoints'][x]) * h
                    polygon.append(QPoint(px, py))
                    # print("    x=%.1f    p.x()=%.1f    y=%.1f\    p.y()=%.1f" % (x, px, curve['polypoints'][x], py))
                painter.drawPolyline(polygon)

                # Draw points
                for p in curve['curve'].points():
                    if p == curve['curve'].selected_point():
                        painter.setBrush(QBrush(self.SELECTED_POINT_COLOR))
                    else:
                        painter.setBrush(Qt.NoBrush)
                    px = p.x() * x_max
                    py = int(h * (1 - p.y()))
                    painter.drawEllipse(QPoint(px, py), 3, 3)
                painter.setBrush(Qt.NoBrush)

            painter.end()


    def select_channel(self, k_channel):
        # Select a channel (and unselect previous)
        self.k_selected_channel = k_channel
        self.update()


    def flush_polypoints(self):
        for k in ['r', 'g', 'b']:
            if self.k_selected_channel == k:
                del self.curves[k]['polypoints']
                self.curves[k]['polypoints'] = np.array([]).astype('int')


    def update_lookup_tables(self, verbose=False):
        depth = 256.0
        for k in ['r', 'g', 'b']:
            self.curves[k]['lut'] = calculate_lut_for_bgd(self.curves[k]['curve'])

        if verbose:
            for k in ['r', 'g', 'b']:
                print("--------------- update_lookup_tables: %s (%d) -------------------" % (k, len(self.curves[k]['lut'])))
                points = self.curves[k]['curve'].points()
                pprint(points)
                for p in points:
                    print("%d->%d" % (int(255 * p.x()), ((p.y()*depth) - depth/2) / 8))
                # pprint(self.curves[k]['lut'])



    def point_to_coordinates(self, p):
        depth = 256.0
        x = int(p.x() * (depth-1))
        delta = ((p.y() * (depth-1)) - (depth-1)/2) / 10
        return [x, delta]


    def mousePressEvent(self, event):
        if not self.is_enabled:
            return

        w = float(self.width())
        h = float(self.height())
        x_max = w - 1
        y_max = (h/2) - 1
        x = float(event.pos().x())
        y = h/2 - event.pos().y()

        # x(px) -> xf [0;1.0]
        # y(px) -> yf [0;1.0]
        xf = np.float32(x) / x_max
        yf = (1 + np.float32(y) / y_max)/2

        curve = self.curves[self.k_selected_channel]['curve']
        if event.button() == Qt.LeftButton:
            # print("mousePressEvent: (%d; %d) in (%d;%d) -> (%f; %f)" % (x, y, x_max, y_max, xf, yf))
            is_selected = curve.select_point(xf, yf)
            if is_selected:
                self.update()
                selected_point = curve.selected_point()
                self.m_grab_offset_x_f = selected_point.x() - xf
                self.m_grab_offset_y_f = selected_point.y() - yf

                self.signal_point_selected.emit(self.point_to_coordinates(selected_point))

                # print("\tgrab point@(%.1f;%.1f)" % (self.m_grab_offset_x_f, self.m_grab_offset_y_f))
            else:
                # Add a new point and select it
                # print("\tno point selected, create a new point")
                x = float(event.pos().x() + (3))
                y = h/2 - event.pos().y() - (3 + 2)

                # x(px) -> xf [0;1.0]
                # y(px) -> yf [0;1.0]
                xf = np.float32(x) / x_max
                yf = (1 + np.float32(y) / y_max)/2

                if curve.add_point(xf, yf):
                    if curve.select_point(xf, yf):
                        selected_point = curve.selected_point()
                        self.m_grab_offset_x_f = selected_point.x() - xf
                        self.m_grab_offset_y_f = selected_point.y() - yf

                        self.flush_polypoints()
                        self.update_lookup_tables()
                        self.update()
                        self.is_modified = True
                        self.signal_point_selected.emit(self.point_to_coordinates(selected_point))
                        # self.signal_curves_modified.emit('modified')
                        self.is_moving_point = True


                    else:
                        print("\terror: cannot select new added point @(%f, %f)" % (xf, yf))
                else:
                    print("\terror: creation failed @(%f, %f)" % (xf, yf))


        elif event.button() == Qt.RightButton:
            is_selected = curve.select_point(xf, yf)
            if is_selected:
                selected_point = curve.selected_point()
                if selected_point.x() != 0.0 and selected_point.x() != 1.0:
                    is_removed = curve.remove_selected_point(min_points_count=1)
                    if is_removed:
                        self.flush_polypoints()
                        self.update_lookup_tables()
                        self.update()
                        self.is_modified = True
                        self.signal_point_selected.emit([-1, 0])
                        self.signal_curves_modified.emit('modified')
                        self.is_moving_point = False
                # else:
                #     print("\tdo not remove the initial point")


    def mouseReleaseEvent(self, event):
        if self.is_moving_point:
            self.is_moving_point = False
            self.signal_curves_modified.emit('modified')


    def mouseMoveEvent(self, event):
        if not self.is_enabled:
            return
        w = np.float32(self.width())
        h = np.float32(self.height())
        x_max = w - 1
        y_max = (h/2) - 1
        x = np.float32(event.pos().x())
        y = h/2 - event.pos().y()

        # x(px) -> xf [0;1.0]
        # y(px) -> yf [0;1.0]
        xf = np.float32(x) / x_max
        yf = (1 + np.float32(y) / y_max)/2

        self.show_position = False
        curve = self.curves[self.k_selected_channel]['curve']
        selected_point = curve.selected_point()
        if selected_point is not None:

            # print("mouseMoveEvent: offsets = [%.1f; %.1f]" % (self.m_grab_offset_x_f, self.m_grab_offset_y_f))
            xf += self.m_grab_offset_x_f
            yf -= self.m_grab_offset_y_f

            xLow = curve.grab_range()[0] + 1/(256.0 * x_max)
            xHigh = curve.grab_range()[1] - 1/(256.0 * x_max)

            # print("\t[xLow, xHigh] = [%.03f; %.03f]" % (xLow, xHigh))
            isOutside = False
            gap = 40
            if (xf < xLow - gap/w or xf > xHigh + gap/w
                or yf > 1.0 + gap/h or yf < -1*gap/h):
                isOutside = True
                # print("\tisOutside, pointsCount=%d" % (curve.point_count()))

            xf = np.clip(xf, xLow, xHigh)
            yf = np.clip(yf, 0.0, 1.0)

            if not isOutside:
                # print("\t-> move: (%.03f; %.03f) -> (%.03f; %.03f)" % (selected_point.x(), selected_point.y(), xf, yf))
                curve.move_selected_point(xf, yf)
            else:
                # print("\t-> remove point")
                curve.remove_selected_point(min_points_count=1)


            self.flush_polypoints()
            self.update_lookup_tables()
            self.update()
            self.is_modified = True
            self.is_moving_point = True

            current_selected_point = curve.selected_point()
            if current_selected_point is not None:
                self.signal_point_selected.emit(self.point_to_coordinates(selected_point))
            else:
                self.signal_point_selected.emit([-1, 0])
            self
            self.signal_curves_editing.emit()


