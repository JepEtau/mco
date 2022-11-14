# -*- coding: utf-8 -*-

import time

from logger import log
from pprint import pprint

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QSizePolicy,
    QWidget,
)

from common.sylesheet import set_stylesheet

from curves_editor.widget_rgb_graph import Widget_rgb_graph
from curves_editor.ui.widget_rgb_curves_ui import Ui_widget_rgb_curves

GRID_COLOR = QColor(110, 110, 110)
GRID_AXIS_COLOR = QColor(110, 110, 110)
WIDGET_MARGIN = 5
GRAPH_WIDTH = 512

class Widget_rgb_curves(QWidget, Ui_widget_rgb_curves):

    def __init__(self, ui):
        super(Widget_rgb_curves, self).__init__()
        self.setupUi(self)

        self.ui = ui


        # Curves Graph widget
        self.widget_rgb_graph = Widget_rgb_graph(self)
        self.widget_rgb_graph.set_widget_width(GRAPH_WIDTH)
        self.widget_rgb_graph.set_style(
            grid_color=GRID_COLOR,
            grid_axis_color=GRID_AXIS_COLOR,
            pen_width=1)
        self.widget_rgb_graph.signal_point_selected[list].connect(self.refresh_current_coordinates)



        size_policy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.MinimumExpanding)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.widget_rgb_graph.sizePolicy().hasHeightForWidth())
        self.widget_rgb_graph.setSizePolicy(size_policy)
        # self.widget_rgb_graph.setMinimumSize(QSize(GRAPH_WIDTH + 2* WIDGET_MARGIN, GRAPH_WIDTH + 2* WIDGET_MARGIN))
        self.widget_rgb_graph.adjustSize()
        self.widget_rgb_graph.setEnabled(True)

        # self.mainLayout.addWidget(self.widget_rgb_graph, 0, 0, 1, 1)
        self.mainLayout.replaceWidget(self.widget_rgb_graph_tmp, self.widget_rgb_graph)
        self.widget_rgb_graph_tmp.deleteLater()


        for w in [self.radioButton_select_r_channel,
                self.radioButton_select_g_channel,
                self.radioButton_select_b_channel,
                self.lineEdit_coordinates,
                self.pushButton_reset_current_channel,
                self.pushButton_reset_all_channels]:
            w.setFocusPolicy(Qt.NoFocus)

        self.lineEdit_rgb.clear()
        self.refresh_current_coordinates([-1,0])


        self.radioButton_select_r_channel.clicked.connect(self.select_channel)
        self.radioButton_select_g_channel.clicked.connect(self.select_channel)
        self.radioButton_select_b_channel.clicked.connect(self.select_channel)
        self.radioButton_select_m_channel.clicked.connect(self.select_channel)

        self.pushButton_reset_current_channel.clicked.connect(self.reset_current_channel)
        self.pushButton_reset_all_channels.clicked.connect(self.reset_all_channels)

        self.widget_rgb_graph.select('m')
        self.radioButton_select_m_channel.setChecked(True)

        set_stylesheet(self)


    def set_model(self, model):
        self.model = model
        self.widget_rgb_graph.set_model(model)


    def set_enabled(self, enabled):
        self.setEnabled(enabled)
        self.widget_rgb_graph.set_enabled(enabled)


    def set_initial_values(self, settings:dict):
        pass


    def load_curves(self, doLoadNewCurve=False):
        # if doLoadNewCurve:
        #     log.info("load others curves")
        #     self.widget_rgb_graph.load_curves(self.model.getNewCurves())
        # else:
        #     log.info("load initial curve")
        log.info("display curves in graph")
        c = self.model.getCurves()
        self.widget_rgb_graph.load_curves(c)


    def curve_lut(self, channel):
        return self.widget_rgb_graph.lut(channel)


    def rgb_graph(self):
        return self.widget_rgb_graph

        # self.widget_rgb_graph.setEnabled(False)
        # self.setEnabled(False)

    # def refreshImage(self):
    #     self.widget_image.updateImage()

    # def switch_OriginalPreviewImage(self):
    #     self.widget_image.switch_OriginalPreviewImage()

    def select_channel(self):
        if self.radioButton_select_r_channel.isChecked():
            self.widget_rgb_graph.select('r')
        elif self.radioButton_select_g_channel.isChecked():
            self.widget_rgb_graph.select('g')
        elif self.radioButton_select_b_channel.isChecked():
            self.widget_rgb_graph.select('b')
        elif self.radioButton_select_m_channel.isChecked():
            self.widget_rgb_graph.select('m')
        self.setFocus()


    def select(self, channel):
        self.widget_rgb_graph.select(channel)
        if channel == 'r':
            self.radioButton_select_r_channel.setChecked(True)
        elif channel == 'g':
            self.radioButton_select_g_channel.setChecked(True)
        elif channel == 'b':
            self.radioButton_select_b_channel.setChecked(True)
        elif channel == 'm':
            self.radioButton_select_m_channel.setChecked(True)


    def update_selected_channel(self, channel):
        if channel == 'r':
            self.radioButton_select_r_channel.setChecked(True)
        elif channel == 'g':
            self.radioButton_select_g_channel.setChecked(True)
        elif channel == 'b':
            self.radioButton_select_b_channel.setChecked(True)
        elif channel == 'm':
            self.radioButton_select_m_channel.setChecked(True)
        self.setFocus()

    def reset_current_channel(self):
        self.widget_rgb_graph.reset_channel('current')
        self.setFocus()

    def reset_all_channels(self):
        self.widget_rgb_graph.reset_channel('all')
        self.widget_rgb_graph.select('m')
        self.radioButton_select_m_channel.setChecked(True)
        self.setFocus()



    def update_rgb_value(self, r=None, g=None, b=None):
        if r is None or g is None or b is None:
            self.lineEdit_rgb.clear()
        else:
            self.lineEdit_rgb.setText("(%d, %d, %d)" % (r, g, b))
        self.widget_rgb_graph.update_rgb_value(r,g,b)


    def refresh_current_coordinates(self, coordinates:list):
        if coordinates[0] < 0:
            self.lineEdit_coordinates.clear()
        else:
            self.lineEdit_coordinates.setText("x:%d y:%d" % (coordinates[0], coordinates[1]))


    def keyPressEvent(self, event):
        key = event.key()
        if event.modifiers() | (Qt.ControlModifier & Qt.AltModifier):
            # log.info("ignore because ctrl or alt has been pressed")
            event.ignore()
            return
        # print("Widget_rgb_curves:keypressed %d" % (key))

        if key == Qt.Key_R:
            self.widget_rgb_graph.select('r')
            self.radioButton_select_r_channel.setChecked(True)
            self.setFocus()
            event.accept()

        elif key == Qt.Key_G:
            self.widget_rgb_graph.select('g')
            self.radioButton_select_g_channel.setChecked(True)
            self.setFocus()
            event.accept()

        elif key == Qt.Key_B:
            self.widget_rgb_graph.select('b')
            self.radioButton_select_b_channel.setChecked(True)
            self.setFocus()
            event.accept()

        elif key == Qt.Key_A or key == Qt.Key_M:
            self.widget_rgb_graph.select('m')
            self.radioButton_select_m_channel.setChecked(True)
            self.setFocus()
            event.accept()

        elif key == Qt.Key_Space:
            self.ui.switch_to_original_image()
            event.accept()

        elif key == Qt.Key_S:
            self.ui.switch_to_splitted_image()
            event.accept()

        elif key == Qt.UpArrow:
            self.widget_rgb_graph.moveUp()
            event.accept()

        elif key == Qt.DownArrow:
            self.widget_rgb_graph.moveDown()
            event.accept()

        elif key == Qt.Key_Return or key == Qt.Key_Enter:
            self.model.saveCurves()
            event.accept()

        # else:
        #     self.ui.keyPressEvent(event)
        else:
            return False
            print("Widget_rgb_curves:keypressed %d" % (key))

        return True

