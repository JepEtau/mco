# -*- coding: utf-8 -*-
import sys
from pprint import pprint
import numpy as np
import cv2

from PySide6.QtCore import (
    QEvent,
    QPoint,
    QSize,
    Qt,
    Signal,
    QRect,
)
from PySide6.QtGui import (
    QCursor,
    QDropEvent,
    QKeyEvent,
    QWheelEvent,
    QColor,
)

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMenu,
    QWidget,
    QSizePolicy,
    QVBoxLayout,
    QHBoxLayout,
    QSpacerItem,
    QLayout,
    QPushButton,
    QSizeGrip,
    QListWidgetItem,
)
from window_main_ui import Ui_window_main
from widget_painter import Widget_painter
from hist import Hist
from stylesheet import (
    set_stylesheet,
    set_widget_stylesheet,
)


GRID_COLOR = QColor(110, 110, 110)
GRID_AXIS_COLOR = QColor(110, 110, 110)
WIDGET_MARGIN = 5
GRAPH_WIDTH = 512





class Window_main(QMainWindow, Ui_window_main):
    signal_urls_dropped = Signal(dict)
    signal_curves_modified = Signal(dict)
    signal_channel_selected = Signal(str)

    def __init__(self, backend:Hist):
        super(Window_main, self).__init__()
        self.setupUi(self)

        self.setWindowTitle("Histogram editor")

        # window_icon = QIcon()
        # window_icon.addFile("icons/icon_16.png", QSize(16,16))
        # window_icon.addFile("icons/icon_24.png", QSize(24,24))
        # window_icon.addFile("icons/icon_32.png", QSize(32,32))
        # window_icon.addFile("icons/icon_48.png", QSize(48,48))
        # window_icon.addFile("icons/icon_64.png", QSize(64,64))
        # window_icon.addFile("icons/icon_128.png", QSize(128,128))
        # window_icon.addFile("icons/icon_256.png", QSize(256,256))
        # self.setWindowIcon(window_icon)

        # Right click
        # self.setContextMenuPolicy(Qt.CustomContextMenu)
        # self.customContextMenuRequested[QPoint].connect(self.event_right_click)

        # Accept drop
        self.widget_painter.signal_urls_dropped.connect(self.event_urls_dropped)

        # Signals coming from backend
        backend.signal_image_refreshed[cv2.Mat].connect(self.event_image_refreshed)
        # backend.signal_cursor_shape_changed[Qt.CursorShape].connect(self.event_cursor_shape_changed)
        # backend.signal_slider_moved[dict].connect(self.event_slider_moved)
        # backend.signal_image_position_changed[QPoint].connect(self.widget_painter.event_image_position_changed)

        # Signals and events
        # self.widget_painter.signal_wheel_event[QWheelEvent].connect(self.event_painter_wheel_event)

        # backend.signal_stitching_curves_list_modified[dict].connect(self.event_refresh_curves_list)
        backend.signal_stitching_curves_selected[dict].connect(self.load_curves)
        backend.signal_histogram_refreshed[dict].connect(self.event_histogram_refreshed)


        # self.signal_channel_selected.connect(self.event_stitching_curves_channel_selected)
        self.widget_hist_curves.signal_curves_editing.connect(self.event_curves_modified)




        self.refresh_current_coordinates([-1,0])

        # Curves edition: select default channel and connect signals
        self.radioButton_select_r_channel.setChecked(True)
        self.select_channel()

        for w in [self.radioButton_select_r_channel,
                self.radioButton_select_g_channel,
                self.radioButton_select_b_channel,
                self.lineEdit_coordinates,
                self.pushButton_reset_current_channel,
                self.pushButton_reset_all_channels]:
            w.setFocusPolicy(Qt.NoFocus)

        self.radioButton_select_r_channel.clicked.connect(self.select_channel)
        self.radioButton_select_g_channel.clicked.connect(self.select_channel)
        self.radioButton_select_b_channel.clicked.connect(self.select_channel)

        # Reset button
        self.pushButton_reset_current_channel.clicked.connect(self.reset_current_channel)
        self.pushButton_reset_all_channels.clicked.connect(self.reset_all_channels)


        # Histogram
        self.widget_hist_graph.set_widget_width(GRAPH_WIDTH)
        self.widget_hist_graph.set_style(
            grid_color=GRID_COLOR,
            grid_axis_color=GRID_AXIS_COLOR,
            pen_width=1)

        # Curves which controls the histogram modifications
        self.widget_hist_curves.set_widget_width(GRAPH_WIDTH)
        self.widget_hist_curves.set_style(
            grid_color=GRID_COLOR,
            grid_axis_color=GRID_AXIS_COLOR,
            pen_width=1,
            selected_point_color=QColor(230, 230, 230),
            unselected_point_color=None)
        self.widget_hist_curves.signal_point_selected[list].connect(self.refresh_current_coordinates)
        self.widget_hist_curves.signal_curves_modified[str].connect(self.event_curves_modified)


        set_stylesheet(self)
        self.adjustSize()

        self.setGeometry(50, 50, 1900, 900)
        self.move(50,50)




    def event_cursor_shape_changed(self, cursor_shape:Qt.CursorShape) -> None:
        self.widget_painter.setCursor(cursor_shape)


    def event_slider_moved(self, slider:dict) -> None:
        self.widget_painter.draw_slider_line(slider)


    def event_urls_dropped(self, urls) -> None:
        # Force refresh of the geometry (used when no image is loaded at startup)
        # self.signal_painter_size_changed.emit(self.widget_painter.get_size())
        self.signal_urls_dropped.emit(urls)


    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        self.is_control_key_pressed = False
        return super().keyReleaseEvent(event)


    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = event.key()
        modifiers = event.modifiers()


        if key == Qt.Key.Key_R:
            self.radioButton_select_r_channel.click()
            return True
        elif key == Qt.Key.Key_G:
            self.radioButton_select_g_channel.click()
            return True
        elif key == Qt.Key.Key_B:
            self.radioButton_select_b_channel.click()
            return True

        elif key == Qt.Key.Key_Delete or key == Qt.Key.Key_Backspace:
            # Delete a single point
            self.widget_hist_curves.remove_selected_point()
            return True


        return super().keyPressEvent(event)



    def event_image_refreshed(self, img:cv2.Mat) -> None:
        self.widget_painter.show_image(img)





    def event_histogram_refreshed(self, histogram):
        print(f"refresh histogram")
        self.widget_hist_graph.display(histogram)







    def load_curves(self, curves):
        # Save the previous to undo the selection
        # if self.previous_k_curves != '':
        #     self.pushButton_undo.setEnabled(True)
        # else:
        #     self.pushButton_undo.setEnabled(False)
        # print("load: previous: %s" % (self.previous_k_curves))
        # self.previous_k_curves = self.k_curves

        # Load the selected curves
        # if curves is not None:
        #     self.k_curves = curves['k_curves']
        #     print("load k_curves=%s" % (self.k_curves))
        #     if self.k_curves != '':
        #         self.set_current_curves_name(self.k_curves)
        #         self.pushButton_remove_selection.setEnabled(True)
        # else:
        #     print("No curves")
        #     self.k_curves = ''
        #     self.deselect_curves_name()
        #     self.pushButton_remove_selection.setEnabled(False)

        # print("\t-> load: previous= %s" % (self.previous_k_curves))

        self.k_curves = curves['k_curves']
        self.widget_hist_curves.load_curves(curves)
        # self.lineEdit_current_curves_selection.setText(self.k_curves)
        # self.refresh_curves_actions_status()




    def get_curve_luts(self):
        return self.widget_hist_curves.get_curve_luts()

    def get_current_channel(self):
        return self.current_channel



    def select_channel(self):
        if self.radioButton_select_r_channel.isChecked():
            self.widget_hist_graph.select_channel('r')
            self.widget_hist_curves.select_channel('r')
            self.current_channel = 'r'
        elif self.radioButton_select_g_channel.isChecked():
            self.widget_hist_graph.select_channel('g')
            self.widget_hist_curves.select_channel('g')
            self.current_channel = 'g'
        elif self.radioButton_select_b_channel.isChecked():
            self.widget_hist_graph.select_channel('b')
            self.widget_hist_curves.select_channel('b')
            self.current_channel = 'b'
        # Emit a signal so that the histogram is calculated
        self.signal_channel_selected.emit(self.current_channel)


    def reset_current_channel(self):
        self.widget_hist_curves.reset_channel('current')
        self.is_save_action_allowed = True
        if self.k_curves != '':
            self.pushButton_save.setEnabled(True)
            self.pushButton_discard.setEnabled(True)


    def reset_all_channels(self):
        self.widget_hist_curves.reset_channel('all')
        if self.k_curves != '':
            self.pushButton_save.setEnabled(True)
            self.pushButton_discard.setEnabled(True)


    def refresh_current_coordinates(self, coordinates:list):
        if coordinates[0] < 0:
            self.lineEdit_coordinates.clear()
        else:
            delta = ""
            if coordinates[1] > 0:
                delta = "+"
            delta += "%.1f" % (coordinates[1])
            self.lineEdit_coordinates.setText("x=%d: %s" % (coordinates[0], delta))



    def event_curves_modified(self):
        curves = self.widget_hist_curves.get_curves()
        channel = self.get_current_channel()
        self.signal_curves_modified.emit(curves)

    #     if type == 'modified':
    #         if self.k_curves != '':
    #             self.signal_curves_modified.emit(self.widget_hist_curves.get_curves())

    #             # Update the global save/discard buttons
    #             self.pushButton_save.setEnabled(True)
    #             self.pushButton_discard.setEnabled(True)

    #             # Mark the current curves as modified
    #             self.mark_current_k_curves_as_modified(is_modified=True)

    #             # Update buttons to save/discard curves
    #             self.refresh_curves_actions_status()


    def resizeEvent(self, event):
        self.widget_painter.adjustSize()
        return super(Window_main, self).resizeEvent(event)
