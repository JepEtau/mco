# -*- coding: utf-8 -*-

# Based on gimp/app/core/gimpcurve.c
# modified for python/numpy

# GIMP - The GNU Image Manipulation Program
# Copyright (C) 1995 Spencer Kimball and Peter Mattis
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

import numpy as np
from pprint import pprint

from utils.pretty_print import print_purple, print_yellow

EPSILON = 1e-6

class Curve_point(object):
    def __init__(self, x:np.float32, y:np.float32):
        self._x = np.round(np.clip(x, 0.0, 1.0, dtype=np.float32), decimals=6)
        self._y = np.round(np.clip(y, 0.0, 1.0, dtype=np.float32), decimals=6)

    def set_x(self, x:np.float32):
        self._x = np.round(np.clip(x, 0.0, 1.0, dtype=np.float32), decimals=6)

    def set_y(self, y:np.float32):
        self._y = np.round(np.clip(y, 0.0, 1.0, dtype=np.float32), decimals=6)


    def set_x_y(self, x:np.float32, y:np.float32):
        self._x = np.round(np.clip(x, 0.0, 1.0, dtype=np.float32), decimals=6)
        self._y = np.round(np.clip(y, 0.0, 1.0, dtype=np.float32), decimals=6)

    def x(self):
        return self._x

    def y(self):
        return self._y

    def __repr__(self):
        return '[{}, {}]'.format(np.format_float_positional(self._x), np.format_float_positional(self._y))


class Curve(object):
    def __init__(self, point_count=12, is_default_constant=False):
        super().__init__()

        self._points = None

        # maximum nb of points for this curve
        self._points_max_count = point_count

        # is_default_constant is to
        # define this curve as an horizontal line when reset
        self.reset(is_default_constant=is_default_constant)


    def reset(self, is_default_constant=False):
        """ This curve may be used as gain for histogram modification
        or rgb curve corrections
        """
        if self._points is not None:
            self._points.clear()

        self._selected_point = None
        self._points = list()

        if is_default_constant:
            self.add_point(0.5, 0.5)
        else:
            self.add_point(0.0, 0.0)
            self.add_point(1.0, 1.0)
        self._grab_range = [0.0, 1.0]


    def remove_all_points(self):
        self._points.clear()

    def points(self):
        return self._points


    def point_count(self):
        return len(self._points)


    def add_point(self, x:np.float32, y:np.float32):
        if len(self._points) < self._points_max_count:
            self._points.append(Curve_point(x, y))
            self._points.sort(key=lambda p: p.x())
            return True
        return False


    def plot(self, lut, p1, p2, p3, p4, sample_count:int=256, depth=1.0):
        # This function calculates the curve values between the control points
        # p2 and p3, taking the potentially existing neighbors p1 and p4 into
        # account.
        #
        # This function uses a cubic bezier curve for the individual segments and
        # calculates the necessary intermediate control points depending on the
        # neighbor curve control points.
        indexMax = sample_count - 1

        # the outer control points for the bezier curve.
        x0 = self._points[p2].x()
        y0 = depth * self._points[p2].y()
        x3 = self._points[p3].x()
        y3 = depth * self._points[p3].y()

        # the x values of the inner control points are fixed at
        # x1 = 2/3*x0 + 1/3*x3   and  x2 = 1/3*x0 + 2/3*x3
        # this ensures that the x values increase linearly with the
        # parameter t and enables us to skip the calculation of the x
        # values altogether - just calculate y(t) evenly spaced.
        dx = x3 - x0
        dy = y3 - y0

        x_count = int((dx * sample_count) + 1)
        x_start = int((x0 * sample_count))
        if (x_start + x_count) > sample_count:
            x_count = sample_count - x_start

        # print("plot::x_count=%d, x_start=%d" % (x_count, x_start))

        # Interpolate from x0 to x3
        _lut = np.array([0] * x_count, dtype=np.float32)

        if dx <= EPSILON:
            print("error, dx is less than %f: x0=%f, x3=%f" % (EPSILON, x0, x3))
            lut[x_start:x_start + x_count] = y3

        p4x = self._points[p4].x()
        p4y = depth * self._points[p4].y()
        p1x = self._points[p1].x()
        p1y = depth * self._points[p1].y()

        if p1 == p2 and p3 == p4:
            # No information about the neighbors,
            # calculate y1 and y2 to get a straight line
            y1 = y0 + dy / 3.0
            y2 = y0 + dy * 2.0 / 3.0

            # print("calculate y1 and y2 to get a straight line.")
            # print("dx=%f, dy=%f, y1=%f, y2=%f" % (dx, dy, y1, y2))

        elif p1 == p2 and p3 != p4:
            # only the right neighbor is available. Make the tangent at the
            # right endpoint parallel to the line between the left endpoint
            # and the right neighbor. Then point the tangent at the left towards
            # the control handle of the right tangent, to ensure that the curve
            # does not have an inflection point.
            #
            slope = (p4y - y0) / (p4x - x0)
            y2 = y3 - slope * dx / 3.0
            y1 = y0 + (y2 - y0) / 2.0

            # print("only the right neighbor is available")

        elif p1 != p2 and p3 == p4:
            # see previous case
            slope = (y3 - p1y) / (x3 - p1x)
            y1 = y0 + slope * dx / 3.0
            y2 = y3 + (y1 - y3) / 2.0

            # print("only the left neighbor is available")

        else:
            # p1 != p2 and p3 != p4

            # Both neighbors are available. Make the tangents at the endpoints
            # parallel to the line between the opposite endpoint and the adjacent
            # neighbor.
            slope = (y3 - p1y) / (x3 - p1x)
            y1 = y0 + slope * dx / 3.0

            slope = (p4y - y0) / (p4x - x0)
            y2 = y3 - slope * dx / 3.0

            # print("Both neighbors are available")

        # finally calculate the y(t) values for the given bezier values. We can
        # use homogeneously distributed values for t, since x(t) increases linearly.
        array_i = np.arange(0, x_count, dtype=np.float32)
        array_t = array_i / (dx * indexMax)
        array_1_t = 1 - array_t
        array_y = np.clip(( y0 * array_1_t * array_1_t * array_1_t +
                3 * y1 * array_1_t * array_1_t * array_t   +
                3 * y2 * array_1_t * array_t   * array_t   +
                    y3 * array_t   * array_t   * array_t), 0.0, depth)

        # print("plot::array_y (%d)" % (len(array_y)))
        # for i in range(len(array_y)):
        #     print("\t(%d;\t%f)" % (i, array_y[i]))

        # print("---------------------------------------------------")
        # print("plot::lut (%d)" % (len(lut)))
        # for i in range(len(lut)):
        #     print("\t(%d;\t%f)" % (i, lut[i]))

        lut[x_start:x_start + len(array_y)] = array_y

        # print("plot:lut: (%d)" % (sample_count))
        # for i in range(sample_count):
        #     print("\t(%d;%03f)" % (i, lut[i]))
        # return _lut


    def calculate(self, sample_count=256, depth=1.0, verbose=False):
        if verbose:
            print("calculate: sample_count=%d, depth=%f" % (sample_count, depth))
        if len(self._points) == 1:
            p_x0 = self._points[0].x()
            p_y0 = depth * self._points[0].y()
            if verbose:
                print("\thorizontal line: (%d;%d)" % (p_x0, p_y0))
            lut = np.array([p_y0] * sample_count, dtype=np.float32)

        elif len(self._points) == 2:
            # Simple affine function
            p_x0 = self._points[0].x()
            p_y0 = depth * self._points[0].y()
            p_x1 = self._points[1].x()
            p_y1 = depth * self._points[1].y()

            if verbose:
                print("\taffine: (%d;%d) -> (%d; %d)" % (p_x0, p_y0, p_x1, p_y1))

            lut_0_sample_count = int(sample_count * p_x0)
            lut_2_sample_count = int(sample_count - (sample_count * p_x1))
            lut_1_sample_count = sample_count - (lut_2_sample_count + lut_0_sample_count)
            if verbose:
                print("\tlut(%d) + lut(%d) + lut(%d)" % (lut_0_sample_count, lut_1_sample_count, lut_2_sample_count))

            lut_0 = np.array([p_y0] * lut_0_sample_count, dtype=np.float32)
            lut_1 = np.arange(0, lut_1_sample_count, dtype=np.float32)
            lut_1 = p_y0 + lut_1 * (p_y1 - p_y0) / lut_1_sample_count
            lut_2 = np.array([p_y1] * lut_2_sample_count, dtype=np.float32)

            if verbose:
                print("\t merge: %d %d %d" % (len(lut_0), len(lut_1), len(lut_2)))

            lut = np.concatenate((lut_0, lut_1, lut_2))
            lut = np.clip(lut, 0.0, depth)

            if verbose:
                print("\tlut (%d)" % (len(lut)))
                pprint(lut)
                # for i, v in zip(range(len(lut_1)), lut_1):
                #     print("\tf(%d) = %.f" % (i, v))

        elif len(self._points) >= 2:
            # bezier curve
            lut = np.array([0.0] * sample_count, dtype=np.float32)

            # print("points (%d):" % (len(self._points)))
            # for p in self._points:
            #     print("\t(%0.3f;%03f)" % (p.x(), p.y()))

            # Initialize boundary curve points
            p = self._points[0]
            if p.x() > 0:
                xTmp = int(p.x() * sample_count)
                lut[0:xTmp] = np.array([depth * p.y()] * xTmp, dtype=np.float32)

            for i in range(0, len(self._points) - 1):
                p1 = max(i-1, 0)
                p2 = i
                p3 = i + 1
                p4 = min(i+2, len(self._points) - 1)

                # print("samples no. %d/%d: [%d, %d, %d, %d]" % (i, len(self._points), p1, p2, p3, p4))
                if p2 == 0:
                    p1 = p2

                # if self._points[p3].type() == 'corner':
                if p3 == len(self._points):
                    p4 = p3

                self.plot(lut, p1, p2, p3, p4, sample_count, depth)

            # print("=======================================================")
            # print("calculate::lut (%d)" % (sample_count))
            # for i in range(sample_count):
            #     print("\t(%d;%f)" % (i, lut[i]))
            # sys.exit()

            p = self._points[len(self._points)-1]
            if p.x() < (sample_count-1):
                xTmp = int((1-p.x()) * sample_count)
                lut[sample_count - xTmp - 1:sample_count] = np.array([depth * p.y()] * (xTmp + 1), dtype=np.float32)

        # ensure that the control points are defined correclty
        for p in self._points:
            # print("\t(%f-> %f;%f)" % (p.x(), int((sample_count-1)*p.x()+0.5), p.y()))
            lut[int((sample_count-1)*p.x()+0.5)] = depth * p.y()

        return lut


    def get_lut(self, sample_count=256):
        lut = self.lut * float(sample_count-1)
        return lut


    def select_point(self, xf:np.float32, yf:np.float32, distance=25):
        """returns True if point is found """
        mult = 500.0
        _xf = mult * np.clip(xf, 0.0, 1.0)
        _yf = mult * np.clip(yf, 0.0, 1.0)
        # print("\nselect_point: xf=%f, yf=%f" % (xf, yf))

        # Get closest point
        nearest_distance = 4 * mult**2
        selected_point = None
        for p, i in zip(self._points, range(len(self._points))):
            # print("point=[%f;%f] vs [%f;%f]" % (xf, yf, p.x(), p.y()))
            d = ((_xf - (mult * p.x())) ** 2) + ((_yf - (mult * p.y())) ** 2)
            # print("\t distance=%f" % (d))
            if d < nearest_distance:
                selected_point = p
                selected_point_index = i
                nearest_distance = d
                # print("\tfound nearest: i=%d" % (i))
        # print("nearest point index=%d, distance=%f:" % (selected_point_index, nearest_distance))
        # print("\t(%f;%f)" % (selected_point.x(), selected_point.y()))

        # Calculate distance to the found point
        dx = _xf - mult * selected_point.x()
        dy = _yf - mult * selected_point.y()
        # print("\tdistance (dx=%d, dy=%d) ->  %d vs %d" % (dx, dy, dx**2 + dy**2, distance**2))
        if (dx**2 + dy**2) <= (distance ** 2):
            self._selected_point = selected_point

            lowLimit = 0.0
            highLimit = 1.0
            if len(self._points) > 1:
                if selected_point_index == 0:
                    highLimit = self._points[selected_point_index+1].x()
                elif selected_point_index == len(self._points)-1:
                    lowLimit = self._points[selected_point_index-1].x()
                else:
                    lowLimit = self._points[selected_point_index-1].x()
                    highLimit = self._points[selected_point_index+1].x()

            self._grab_range = [lowLimit, highLimit]
            # print("x=%.03f, limits=[%.03f; %.03f]" % (selected_point.x(), lowLimit, highLimit))
            # print("selected_point: %d (%f; %f)" % (selected_point_index, selected_point.x(), selected_point.y()))
            return True

        # print("\t-> no selected point")
        self._selected_point = None
        return False


    def selected_point(self):
        """Returns the current selected point
        """
        return self._selected_point


    def grab_range(self):
        """Returns the allowed range to add a new point
        """
        return self._grab_range


    def remove_selected_point(self, min_points_count=2):
        """Remove the select point if possible (at least one point
        is allowed
        """
        if len(self._points) > min_points_count and self._selected_point is not None:
            self._points.remove(self._selected_point)
            self._selected_point = None
            self._grab_range = [0.0, 1.0]
            return True
        return False


    def move_selected_point(self, x:np.float32, y:np.float32):
        """Move the selected point to new coordinates
        """
        # print("move selected point (%d: %f) -> (%f: %f)" % (self._selected_point.x(), self._selected_point.y(), x, y))
        self._selected_point.set_x(x)
        self._selected_point.set_y(y)


    def apply_translation(self,  delta_x:np.float32, delta_y:np.float32, sample_count=256):

        if ((delta_x < 0 and delta_y < 0)
            or (delta_x > 0 and delta_y > 0)):
            return True

        delta_abs = np.sqrt(delta_x**2 + delta_y**2)
        shift = delta_abs * np.cos(45)
        if (delta_x < 0 and delta_y > 0):
            delta = -1 * delta_abs
            shift *= -1
        else:
            delta = delta_abs

        if delta_abs < 1/sample_count:
            return False

        # print_yellow(f"delta: {delta_x:.04f}")

        for point in self._points:
            x = point.x()
            y = point.y()
            # print(f"\tpoint: [{x:.04f}, {y:.04f}]", end='')

            if x == 0 and y == 0:
                if delta < 0:
                    point.set_y(delta_abs)
                    # print(f" -> [{point.x():.04f}, {point.y():.04f}] (move from origin, delta < 0)")
                else:
                    point.set_x(delta_abs)
                    # print(f" -> [{point.x():.04f}, {point.y():.04f}] (move from origin), delta > 0")
                continue

            # on x_min axis
            elif y == 0:
                if x < delta_abs and delta < 0:
                    # x_min axis -> y_min axis
                    point.set_x(0)
                    point.set_y(delta_abs - x)
                    # print(f" -> [{point.x():.04f}, {point.y():.04f}] (x_min axis -> y_min axis)")
                else:
                    # stay on x_min axis
                    point.set_x(x + delta)
                    # print(f" -> [{point.x():.04f}, {point.y():.04f}] (stay on x_min axis)")
                continue

            # on y_min axis
            elif x == 0:
                if y < delta_abs and delta > 0:
                    # y_min axis -> x_min axis
                    point.set_x(delta_abs - y)
                    point.set_y(0)
                    # print(f" -> [{point.x():.04f}, {point.y():.04f}] (y_min axis -> x_min axis)")
                else:
                    # stay on y_min axis
                    point.set_y(y - delta)
                    # print(f" -> [{point.x():.04f}, {point.y():.04f}] (stay on y_min axis)")
                continue


            if x == 1 and y == 1:
                if delta < 0:
                    point.set_x(1 - delta_abs)
                    # print(f" -> [{point.x():.04f}, {point.y():.04f}] (move from origin, delta < 0)")
                else:
                    point.set_y(1 - delta_abs)
                    # print(f" -> [{point.x():.04f}, {point.y():.04f}] (move from origin), delta > 0")
                continue

            # on x_max axis
            elif y == 1:
                if x + delta_abs > 1 and delta > 0:
                    point.set_x(1)
                    point.set_y(2 - (x + delta_abs))
                    # print_purple(f" -> [{point.x():.04f}, {point.y():.04f}] (x_max axis -> y_max axis)")
                else:
                    # stay on x_max axis
                    point.set_x(x + delta)
                    # print(f" -> [{point.x():.04f}, {point.y():.04f}] (stay on x_min axis)")
                continue

            # on y_max axis
            elif x == 1:
                if y + delta_abs > 1 and delta < 0:
                    point.set_x(2 - (y + delta_abs))
                    point.set_y(1)
                    # print(f" -> [{point.x():.04f}, {point.y():.04f}] (y_max axis -> x_max axis)")
                else:
                    # stay on y_max axis
                    point.set_y(y - delta)
                    # print(f" -> [{point.x():.04f}, {point.y():.04f}] (stay on y_max axis)")
                continue

            point.set_x_y(x + shift, y - shift)
            # print(f" ({shift:.04} -> [{x + shift:.04f}, {y - shift:.04f}] (normal)")

        return True

