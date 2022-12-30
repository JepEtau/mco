# -*- coding: utf-8 -*-

import sys
sys.path.append('../scripts')

from copy import deepcopy
import numpy as np
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

from images.curve import (
    Curve,
    Curve_point
)


class Widget_hist_curves(QWidget):
    signal_point_selected = Signal(list)
    # Current curves have been modified, the model shall be updated
    signal_curves_modified = Signal(dict)

    GRID_COLOR = QColor(255, 255, 255)
    GRID_AXIS_COLOR = QColor(255, 255, 255)
    GRID_AXIS_WIDTH = 1
    CURVE_PEN_WIDTH = 1
    SELECTED_POINT_COLOR = QColor(230, 230, 230)
    UNSELECTED_POINT_COLOR = QColor(210, 210, 210)
    GRAPH_WIDTH = 256

    def __init__(self, ui):
        super(Widget_hist_curves, self).__init__()
        self.ui = ui
        self.setObjectName('hist_curves')

        self.setAttribute(Qt.WA_DeleteOnClose)

        # default width and sample count
        self.set_widget_width(self.GRAPH_WIDTH)
        self.setMinimumHeight(255)


        # Initialize R, G, B, master channels
        self.channels = {
            'r': {'color': QColor('red')},
            'g': {'color': QColor('green')},
            'b': {'color': QColor('blue')}
        }

        # Initialize default curves
        for k in self.channels.keys():
            self.channels[k].update({
                'curve': Curve(is_default_constant=True),
                'lut': np.array([]).astype('int'),
                'polypoints': np.array([]).astype('int'),
                'is_selected': False,
            })

        # Current channel is red
        self.k_selected = 'r'
        self.channels[self.k_selected]['is_selected'] = True

        self.set_enabled(False)

        # self.is_modified = False
        # self.is_moving_point = False

        # set_stylesheet(self)
        # self.adjustSize()


    def set_model(self, model):
        self.model = model

        # Connect signals
        self.model.signal_load_curves[dict].connect(self.event_curves_loaded)


    def set_ui(self, ui):
        self.ui = ui


    def set_style(self, grid_color:QColor=None, grid_axis_color:QColor=None, pen_width:int=None,
                    selected_point_color:QColor=None, unselected_point_color:QColor=None,
                    margin:int=None):
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

        # size_policy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.MinimumExpanding)
        # size_policy.setHorizontalStretch(0)
        # size_policy.setVerticalStretch(0)
        # size_policy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        # self.setSizePolicy(size_policy)
        # self.setMinimumHeight(width)
        self.adjustSize()


    def set_enabled(self, enabled:bool):
        self.is_enabled = enabled


    def event_curves_loaded(self, curves:dict):
        print("load bgd curves: %s" % (curves['k_curves']))
        if curves is not None:
            log.info("load bgd curves: %s" % (curves['k_curves']))
            print("%s.event_load_curves: load curves [%s] in RGB graph" % (__name__, curves['k_curves']))
            for k in self.channels.keys():
                if self.channels[k]['curve'] is not None:
                    del self.channels[k]['curve']
                self.channels[k]['curve'] = deepcopy(curves['channels'][k])
                self.channels[k]['lut'] = np.array([]).astype('int')
                self.channels[k]['polypoints'] = np.array([]).astype('int')
                self.channels[k]['is_selected'] = False

            # Previously
            # points = curves['points']
            # for c in ['r', 'g', 'b']:
            #     curve = self.channels[c]['curve']
            #     if curve is not None:
            #         curve.remove_all_points()
            #     else:
            #         self.channels[c]['curve'] = Curve(is_default_constant=True)
            #         curve = self.channels[c]['curve']
            #     for p in points[c]:
            #         if type(p) is Curve_point:
            #             curve.add_point(p.x(), p.y())
            #         else:
            #             curve.add_point(p[0], p[1])
            #     self.channels[c]['lut'] = np.array([]).astype('int')
            #     self.channels[c]['polypoints'] = np.array([]).astype('int')
            #     self.channels[c]['is_selected'] = False
            # self.channels['k_curves'] = curves['k_curves']
        else:
            log.info("use empty bgd curves")
            for k in self.channels.keys():
                self.channels[k]['curve'] = Curve(is_default_constant=True)
                self.channels[k]['lut'] = np.array([]).astype('int')
                self.channels[k]['polypoints'] = np.array([]).astype('int')
                self.channels[k]['is_selected'] = False

        self.update()


    def remove_selected_point(self):
        self.channels[self.k_selected]['curve'].remove_selected_point(min_points_count=1)
        self.flush_polypoints()
        self.update()
        self.is_modified = True
        self.signal_curves_modified.emit('modified')


    def get_curves_channels(self):
        # Returns a dict of curves
        try:
            print("get_curves_channels: !!!curves modified")
            rgb_curves = {
                'r': self.channels['r']['curve'],
                'g': self.channels['g']['curve'],
                'b': self.channels['b']['curve'],
                'selected': self.k_selected,
            }
            return rgb_curves
        except:
            log.info("curves have not been modified or channels are None")
            # print("get_curves_channels: curves have not been modified")
            return None


    def flush_polypoints(self):
        for k in ['r', 'g', 'b']:
            if self.k_selected == k:
                del self.channels[k]['polypoints']
                self.channels[k]['polypoints'] = np.array([]).astype('int')


    def reset_channel(self, channel:str=''):
        # Reset the graph for a specified/all/current channel
        log.info("reset channel: %s (current: %s)" % (channel, self.k_selected))
        if channel == 'all':
            for c in ['r', 'g', 'b']:
                self.channels[c]['curve'].reset(is_default_constant=True)
                del self.channels[c]['polypoints']
                self.channels[c]['polypoints'] = np.array([]).astype('int')

        elif channel == 'current':
            self.channels[self.k_selected]['curve'].reset(is_default_constant=True)
            self.flush_polypoints()

        self.update()

        self.signal_curves_modified.emit(self.get_curves_channels())
        self.signal_point_selected.emit([-1, 0])


    def select_channel(self, channel:str='r'):
        log.info("select channel [%s]" % (channel))
        # Deselect current channel
        self.channels[self.k_selected]['is_selected'] = False

        # Select the specified channel
        self.k_selected = channel
        self.channels[self.k_selected]['is_selected'] = True

        self.update()



    def selected_channel(self):
        return self.k_selected


    def point_to_coordinates(self, p:Curve_point):
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
                        self.update()
                        self.signal_point_selected.emit(self.point_to_coordinates(selected_point))
                        self.signal_curves_modified.emit(self.get_curves_channels())
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
                        self.update()
                        self.signal_point_selected.emit([-1, 0])
                self.signal_curves_modified.emit(self.get_curves_channels())


    def mouseMoveEvent(self, event):
        verbose = False
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
        curve = self.channels[self.k_selected]['curve']
        selected_point = curve.selected_point()
        if selected_point is not None:

            if verbose:
                print("mouseMoveEvent: offsets = [%.1f; %.1f]" % (self.m_grab_offset_x_f, self.m_grab_offset_y_f))
            xf += self.m_grab_offset_x_f
            yf -= self.m_grab_offset_y_f

            xLow = curve.grab_range()[0] + 1/(256.0 * x_max)
            xHigh = curve.grab_range()[1] - 1/(256.0 * x_max)

            if verbose:
                print("\t[xLow, xHigh] = [%.03f; %.03f]" % (xLow, xHigh))
            isOutside = False
            gap = 40
            if (xf < xLow - gap/w or xf > xHigh + gap/w
                or yf > 1.0 + gap/h or yf < -1*gap/h):
                isOutside = True
                if verbose:
                    print("\tisOutside, pointsCount=%d" % (curve.point_count()))

            xf = np.clip(xf, xLow, xHigh)
            yf = np.clip(yf, 0.0, 1.0)

            if not isOutside:
                if verbose:
                    print("\t-> move: (%.03f; %.03f) -> (%.03f; %.03f)" % (selected_point.x(), selected_point.y(), xf, yf))
                curve.move_selected_point(xf, yf)
            else:
                if verbose:
                    print("\t-> remove point")
                curve.remove_selected_point(min_points_count=1)


            self.flush_polypoints()
            self.update()

            current_selected_point = curve.selected_point()
            if current_selected_point is not None:
                self.signal_point_selected.emit(self.point_to_coordinates(selected_point))
            else:
                self.signal_point_selected.emit([-1, 0])
            self.signal_curves_modified.emit(self.get_curves_channels())


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
            self.signal_curves_modified.emit(self.get_curves_channels())
            return True
        return False



    def paintEvent(self, e):
        w = self.width()
        h = self.height()
        x_max = w - 1
        # print("paintEvent: hist_curve: dimensions = (%d; %d), x_max=%d" % (w, h, x_max))

        # Current channel
        curve = self.channels[self.k_selected]

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

