# -*- coding: utf-8 -*-

import sys
sys.path.append('../scripts')
from functools import partial

from logger import log
from pprint import pprint

from PySide6.QtCore import (
    Qt,
    Signal,
)
from PySide6.QtGui import QColor

from common.sylesheet import set_curves_radiobutton_stylesheet, set_stylesheet, set_widget_stylesheet

from video_editor.ui.widget_curves_ui import Ui_widget_curves
from common.widget_common import Widget_common


GRID_COLOR = QColor(110, 110, 110)
GRID_AXIS_COLOR = QColor(110, 110, 110)
WIDGET_MARGIN = 5
GRAPH_WIDTH = 512


class Widget_curves(Widget_common, Ui_widget_curves):
    signal_save_rgb_curves_as = Signal(dict)

    def __init__(self, ui, model):
        super(Widget_curves, self).__init__(ui)
        self.model = model
        self.ui = ui
        self.setObjectName('curves')

        self.widget_rgb_graph.set_model(model)
        self.widget_rgb_graph.set_ui(self)
        self.widget_curves_selection.set_model(model)
        self.widget_curves_selection.set_ui(self)

        # Internal variables
        self.split_x = 800
        self.split_x_gap = 0
        self.main_window_margin = 0
        self.is_moving_split_line = False
        self.show_split_line = False

        # Disable focus
        self.radioButton_select_b_channel.setFocusPolicy(Qt.NoFocus)
        self.radioButton_select_g_channel.setFocusPolicy(Qt.NoFocus)
        self.radioButton_select_r_channel.setFocusPolicy(Qt.NoFocus)
        self.radioButton_select_m_channel.setFocusPolicy(Qt.NoFocus)
        self.lineEdit_coordinates.setFocusPolicy(Qt.NoFocus)
        self.lineEdit_rgb_values.setFocusPolicy(Qt.NoFocus)
        self.lineEdit_rgb_values_new.setFocusPolicy(Qt.NoFocus)
        self.pushButton_reset_current_channel.setFocusPolicy(Qt.NoFocus)
        self.pushButton_reset_all_channels.setFocusPolicy(Qt.NoFocus)

        self.lineEdit_coordinates.clear()
        self.lineEdit_rgb_values.clear()
        self.lineEdit_rgb_values_new.clear()
        self.refresh_current_coordinates([-1,0])
        self.label_message.clear()


        self.widget_rgb_graph.set_widget_width(GRAPH_WIDTH)
        self.widget_rgb_graph.set_style(
            grid_color=GRID_COLOR,
            grid_axis_color=GRID_AXIS_COLOR,
            pen_width=1)

        self.pushButton_close.setEnabled(False)

        # Graph
        self.widget_rgb_graph.signal_point_selected[list].connect(self.refresh_current_coordinates)
        self.widget_rgb_graph.signal_graph_modified[dict].connect(self.event_rgb_graph_modified)

        # Connect signals and filter events
        self.radioButton_select_r_channel.clicked.connect(partial(self.event_select_channel, 'r'))
        self.radioButton_select_g_channel.clicked.connect(partial(self.event_select_channel, 'g'))
        self.radioButton_select_b_channel.clicked.connect(partial(self.event_select_channel, 'b'))
        self.radioButton_select_m_channel.clicked.connect(partial(self.event_select_channel, 'm'))
        self.pushButton_reset_current_channel.clicked.connect(partial(self.event_reset_channel, 'current'))
        self.pushButton_reset_all_channels.clicked.connect(partial(self.event_reset_channel, 'all'))


        self.widget_curves_selection.signal_curves_selection_changed[str].connect(self.event_curves_selection_changed)
        self.widget_curves_selection.signal_save_rgb_curves_requested[dict].connect(self.event_save_rgb_curves_as)

        self.model.signal_is_saved[str].connect(self.event_is_saved)


        # Default selection
        self.widget_rgb_graph.select_channel('m')
        self.radioButton_select_m_channel.setChecked(True)

        set_stylesheet(self)
        set_widget_stylesheet(self.label_message, 'message')
        for c, w in zip(['r', 'g', 'b', 'm'], [
                    self.radioButton_select_r_channel,
                    self.radioButton_select_g_channel,
                    self.radioButton_select_b_channel,
                    self.radioButton_select_m_channel]):
            set_curves_radiobutton_stylesheet(c, w)
        self.adjustSize()


    def event_curves_selection_changed(self, k_curves):
        # Modified curves selection for at least current shot
        self.pushButton_discard.setEnabled(True)
        self.pushButton_save.setEnabled(True)


    def set_initial_options(self, preferences:dict):
        log.info("%s: set_initial_options" % (self.objectName()))
        s = preferences[self.objectName()]

        try:
            w = preferences[self.objectName()]['widget']
            self.pushButton_set_preview.blockSignals(True)
            self.pushButton_set_preview.setChecked(w['is_enabled'])
            self.pushButton_set_preview.blockSignals(False)
        except:
            log.warning("cannot set initial options")
            pass

        # Geometry
        self.move(s['geometry'][0], s['geometry'][1])
        self.adjustSize()



    def refresh_values(self, frame:dict):
        # print("%s: refresh_values" % (self.objectName()))
        if ('dst' in frame.keys()
            and frame['k_part'] not in ['g_debut', 'g_fin']
            and frame['k_ep'] != frame['dst']['k_ep']):
            # Disable curves edition
            self.widget_rgb_graph.setEnabled(False)
            self.widget_curves_selection.setEnabled(False)
            self.radioButton_select_b_channel.setEnabled(False)
            self.radioButton_select_g_channel.setEnabled(False)
            self.radioButton_select_r_channel.setEnabled(False)
            self.radioButton_select_m_channel.setEnabled(False)
            self.pushButton_reset_current_channel.setEnabled(False)
            self.pushButton_reset_all_channels.setEnabled(False)
            self.label_message.setText("(read-only)")
        else:
            self.widget_rgb_graph.setEnabled(True)
            self.widget_curves_selection.setEnabled(True)
            self.radioButton_select_b_channel.setEnabled(True)
            self.radioButton_select_g_channel.setEnabled(True)
            self.radioButton_select_r_channel.setEnabled(True)
            self.radioButton_select_m_channel.setEnabled(True)
            self.pushButton_reset_current_channel.setEnabled(True)
            self.pushButton_reset_all_channels.setEnabled(True)
            self.label_message.clear()


    def get_preview_options(self):
        preview_options = {
            'is_enabled': self.pushButton_set_preview.isChecked(),
            'split': self.show_split_line,
            'split_x': self.split_x - self.main_window_margin,
        }
        return preview_options


    def event_reset_channel(self, channel):
        self.widget_rgb_graph.reset_channel(channel=channel)


    def event_select_channel(self, channel):
        # log.info("event_select_channel: %s" % (channel))
        if channel == 'r':
            self.widget_rgb_graph.select_channel('r')
        elif  channel == 'g':
            self.widget_rgb_graph.select_channel('g')
        elif  channel == 'b':
            self.widget_rgb_graph.select_channel('b')
        elif  channel == 'm':
            self.widget_rgb_graph.select_channel('m')


    def refresh_current_coordinates(self, coordinates:list):
        if coordinates[0] < 0:
            self.lineEdit_coordinates.clear()
        else:
            self.lineEdit_coordinates.setText("x:%d y:%d" % (coordinates[0], coordinates[1]))


    def set_color_values(self, bgr, bgr_new=[]):
        try:
            self.lineEdit_rgb_values.setText("(%d, %d, %d)" % (bgr[2], bgr[1], bgr[0]))
        except:
            self.lineEdit_rgb_values.clear()

        try:
            self.lineEdit_rgb_values_new.setText("(%d, %d, %d)" % (bgr_new[2], bgr_new[1], bgr_new[0]))
        except:
            self.lineEdit_rgb_values_new.clear()
        self.widget_rgb_graph.refresh_rgb_value(bgr)


    def set_main_window_margin(self, margin):
        # This margin corresponds to the main window margin and is used
        # when splitting the screen
        self.main_window_margin = margin


    def grab_split_line(self, x):
        # log.info("x=%d, split_x=%d" % (x, self.split_x))
        if (self.pushButton_set_preview.isChecked()
        and self.show_split_line):
            if (self.split_x - 30) <= x <= (self.split_x + 30):
                self.split_x_gap = self.split_x - x
                self.is_moving_split_line = True
                self.event_preview_changed(is_checked=True)
                return True
        self.is_moving_split_line = False
        return False


    def move_split_line(self, x):
        if not self.show_split_line:
            return False
        # log.info("move_split_line: x=%d, split_x=%d" % (x, self.split_x))
        if ( (x + self.split_x_gap) < self.main_window_margin
        or (x + self.split_x_gap) > self.main_window_margin + 1440):
            return False
        if (self.pushButton_set_preview.isChecked()
            and self.is_moving_split_line):
            self.split_x = x + self.split_x_gap
            self.event_preview_changed(is_checked=True)
            return True
        return False


    def split_line_moved(self, x, grab_x):
        if not self.show_split_line:
            return False

        # log.info("split_line_moved")
        if (self.pushButton_set_preview.isChecked()
            and self.is_moving_split_line):
            self.split_x = x + grab_x
            self.event_preview_changed(is_checked=True)
            return True
        return False


    def split_line_released(self, x):
        if self.show_split_line:
            # log.info("split_line_released: %d" % (self.split_x))
            self.is_moving_split_line = False


    def event_rgb_graph_modified(self, channels):
        self.widget_curves_selection.mark_current_as_modified(True)


    def event_save_rgb_curves_as(self, names):
        log.info("curves widget: save curves as: [%s] -> [%s]" % (names['current'], names['new']))
        # Get RGB curves
        # associate it to the provided name (by the curves selection)
        curves = {
            'k_curves_current': names['current'],
            'k_curves_new': names['new'],
            'channels': self.widget_rgb_graph.get_curves_channels(),
        }
        self.signal_save_rgb_curves_as.emit(curves)



    def event_is_saved(self, editor):
        log.info("%s: event is saved" % (self.objectName()))
        # Override fuction because the key is differs from this widget name
        # if editor == "curves_selection" or editor == 'all':
        #     print("widget_curves: event_is_saved")
        #     log.info("values saved")
        #     self.pushButton_save.setEnabled(False)
        #     self.pushButton_discard.setEnabled(False)

        # reenable save button, otherwise saving other shots is not possible.
        # save button should be enables/disables depending on the selected shot
        # but not yet implemented
        self.pushButton_save.setEnabled(True)
        pass


    def event_close(self):
        log.info("close button clicked")


    def event_key_pressed(self, event):
        key = event.key()
        modifiers = event.modifiers()

        if modifiers & Qt.ControlModifier:
            if key == Qt.Key_S:
                if self.widget_curves_selection.is_active():
                    log.info("Save RGB curves")
                    self.widget_curves_selection.event_save_rgb_curves_as()
                    return True
                else:
                    log.info("Save selected curves for this shot")
                    self.widget_curves_selection.event_save_selection()
                    return True

        if key == Qt.Key_F2:
            if self.pushButton_set_preview.isEnabled():
                self.pushButton_set_preview.toggle()
                return True

        if key == Qt.Key_R:
            self.radioButton_select_r_channel.click()
            return True

        if key == Qt.Key_G:
            self.radioButton_select_g_channel.click()
            return True

        if key == Qt.Key_B:
            self.radioButton_select_b_channel.click()
            return True

        if key == Qt.Key_A or key == Qt.Key_M:
            self.radioButton_select_m_channel.click()
            return True

        if key == Qt.Key_S and not modifiers & Qt.AltModifier:
            # Display/Hide split line
            if self.pushButton_set_preview.isChecked():
                self.show_split_line = not self.show_split_line
                log.info("display split line: %s" % ('true' if self.show_split_line else 'false'))
                self.event_preview_changed(is_checked=True)
            return True

        if self.widget_curves_selection.is_active():
            if self.widget_curves_selection.event_key_pressed(event):
                return True

        return self.widget_rgb_graph.event_key_pressed(event)


    def event_key_released(self, event):
        return False


