# -*- coding: utf-8 -*-
import sys


from PySide6.QtCore import (
    Signal,
)
from PySide6.QtWidgets import (
    QWidget,
)

GUIDELINES_X_MAX = 1800
GUIDELINES_Y_MAX = 1200
GUIDELINES_GRAB_OFFSET = 30


class Guidelines(QWidget):


    def __init__(self) -> None:
        super(Guidelines, self).__init__()
        self.is_moving_guidelines = False
        self.moving_guidelines = None
        self.vertical_line_x = 800
        self.vertical_line_x_gap = 0
        self.is_moving_vertical_line = False
        self.horizontal_line_y = 600
        self.horizontal_line_y_gap = 0
        self.is_moving_horizontal_line = False
        self.show_guidelines = False


    def set_enabled(self, is_enabled):
        self.show_guidelines = is_enabled


    def is_enabled(self):
        return self.show_guidelines


    def grab(self, x, y):
        # print(f"x={x}, Vline={self.vertical_line_x}")
        # print(f"y={y}, Hline={self.horizontal_line_y}")
        if not self.show_guidelines:
            return None

        if (self.vertical_line_x - GUIDELINES_GRAB_OFFSET) <= x <= (self.vertical_line_x + GUIDELINES_GRAB_OFFSET):
            self.vertical_line_x_gap = self.vertical_line_x - x
            self.is_moving_vertical_line = True
        else:
            self.is_moving_vertical_line = False

        if (self.horizontal_line_y - GUIDELINES_GRAB_OFFSET) <= y <= (self.horizontal_line_y + GUIDELINES_GRAB_OFFSET):
            self.horizontal_line_y_gap = self.horizontal_line_y - y
            self.is_moving_horizontal_line = True
        else:
            self.is_moving_horizontal_line = False

        if self.is_moving_horizontal_line and self.is_moving_vertical_line:
            self.moving_guidelines = "both"
        elif self.is_moving_horizontal_line:
            self.moving_guidelines = "horizontal"
        elif self.is_moving_vertical_line:
            self.moving_guidelines = "vertical"
        else:
            self.is_moving_guidelines = False
            return None

        self.is_moving_guidelines = True

        # print_cyan(f"grabbed {self.moving_guidelines}")
        return self.moving_guidelines



    def move(self, x, y):
        if not self.is_moving_guidelines or not self.show_guidelines:
            return None

        if ( (x + self.vertical_line_x_gap) < 5
            or (x + self.vertical_line_x_gap) > 5 + GUIDELINES_X_MAX):
            return None

        if ( (x + self.horizontal_line_y_gap) < 5
            or (x + self.horizontal_line_y_gap) > 5 + GUIDELINES_Y_MAX):
            return None

        if self.is_moving_horizontal_line:
            self.horizontal_line_y = y + self.horizontal_line_y_gap
        if self.is_moving_vertical_line:
            self.vertical_line_x = x + self.vertical_line_x_gap

        return self.moving_guidelines


    def moved(self, x, grab_x, y, grab_y):
        if not self.is_moving_guidelines or not self.show_guidelines:
            return None

        if self.is_moving_horizontal_line:
            self.horizontal_line_y = y + grab_y
        if self.is_moving_vertical_line:
            self.vertical_line_x = x + grab_x

        return self.moving_guidelines


    def released(self, x, y):
        if not self.show_guidelines:
            return None

        self.is_moving_guidelines = False
        self.is_moving_vertical_line = False
        self.is_moving_horizontal_line = False


    def coordinates(self):
        return (self.vertical_line_x, self.horizontal_line_y)




