#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
sys.path.append('../scripts')
from logger import log
from pprint import pprint

from PySide6.QtCore import (
    Qt,
    QPoint,
    Signal,
    QEvent,
)
from PySide6.QtGui import (
    QCursor,
    QColor,
)
from PySide6.QtWidgets import (
    QApplication,
    QListWidgetItem,
    QWidget,
)

from common.sylesheet import set_stylesheet

from merge_stabilize.model_merge_stabilize import Model_merge_stabilize
from merge_stabilize.ui.widget_stitching_curves_ui import Ui_widget_stitching_curves

GRID_COLOR = QColor(110, 110, 110)
GRID_AXIS_COLOR = QColor(110, 110, 110)
WIDGET_MARGIN = 5
GRAPH_WIDTH = 512

class Widget_stitching_curves(QWidget, Ui_widget_stitching_curves):
    signal_curves_modified = Signal(dict)
    signal_channel_selected = Signal()
    signal_discard_curves_modifications = Signal(str)
    signal_save_curves_as = Signal(dict)
    signal_selection_changed = Signal(str)
    signal_reset_selection = Signal()
    signal_remove_selection = Signal()
    signal_save_selection = Signal()
    signal_preview_options_changed = Signal()

    def __init__(self, ui, model:Model_merge_stabilize):
        super(Widget_stitching_curves, self).__init__()

        self.setupUi(self)
        self.model = model
        self.ui = ui

        # Setup and patch ui
        self.setAutoFillBackground(True)
        self.setWindowFlags(Qt.Tool)
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setWindowModality(Qt.NonModal)


        # Header
        self.pushButton_set_preview.setFocusPolicy(Qt.NoFocus)
        self.pushButton_set_preview.toggled[bool].connect(self.event_preview_changed)

        self.lineEdit_current_curves_selection.clear()
        self.lineEdit_current_curves_selection.setFocusPolicy(Qt.NoFocus)

        self.pushButton_save_modifications.setFocusPolicy(Qt.NoFocus)
        self.pushButton_save_modifications.clicked.connect(self.event_save_modifications)
        self.pushButton_save_modifications.setEnabled(False)

        self.pushButton_remove_selection.setFocusPolicy(Qt.NoFocus)
        self.pushButton_remove_selection.clicked.connect(self.event_remove_selection)
        self.pushButton_remove_selection.setEnabled(False)

        self.pushButton_discard_modifications.setFocusPolicy(Qt.NoFocus)
        self.pushButton_discard_modifications.clicked.connect(self.event_discard_modifications)
        self.pushButton_discard_modifications.setEnabled(False)

        self.pushButton_undo_selection.setFocusPolicy(Qt.NoFocus)
        self.pushButton_undo_selection.clicked.connect(self.event_undo_selection)
        self.pushButton_undo_selection.setEnabled(False)

        self.pushButton_close.setFocusPolicy(Qt.NoFocus)
        self.pushButton_close.clicked.connect(self.event_close)
        self.pushButton_close.setEnabled(False)

        self.is_save_action_allowed = False


        # List of curves
        self.list_curves_names.clear()
        self.lineEdit_save_name.clear()
        self.lineEdit_save_name.setFocusPolicy(Qt.NoFocus)
        self.list_curves_names.setFocusPolicy(Qt.NoFocus)
        self.pushButton_save_curves_modifications.setFocusPolicy(Qt.NoFocus)
        self.pushButton_discard_curves_modifications.setFocusPolicy(Qt.NoFocus)
        self.pushButton_save_curves_as.setFocusPolicy(Qt.NoFocus)


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
        self.widget_hist_curve.set_widget_width(GRAPH_WIDTH)
        self.widget_hist_curve.set_style(
            grid_color=GRID_COLOR,
            grid_axis_color=GRID_AXIS_COLOR,
            pen_width=1,
            selected_point_color=QColor(230, 230, 230),
            unselected_point_color=None)
        self.widget_hist_curve.signal_point_selected[list].connect(self.refresh_current_coordinates)
        self.widget_hist_curve.signal_curves_modified[str].connect(self.event_curves_modified)


        # Curves selection: connect signals
        self.list_curves_names.itemSelectionChanged.connect(self.event_select_curve)
        self.list_curves_names.itemClicked.connect(self.event_set_focus)

        self.lineEdit_save_name.returnPressed.connect(self.event_save_stitching_curves_as)
        self.pushButton_save_curves_as.released.connect(self.event_save_stitching_curves_as)

        self.pushButton_discard_curves_modifications.released.connect(self.event_discard_curves_modifications)
        self.pushButton_save_curves_modifications.released.connect(self.event_save_stitching_curves)

        self.pushButton_save_modifications.released.connect(self.event_save_modifications)

        # Connect signals emitted by model
        self.model.signal_stitching_curves_list_modified[dict].connect(self.event_refresh_curves_list)
        self.model.signal_stitching_curves_selected[dict].connect(self.load_curves)


        self.k_curves = ''
        self.previous_k_curves = ''

        self.set_enabled(True)
        set_stylesheet(self)
        self.adjustSize()



    def set_enabled(self, enabled:bool):
        self.widget_hist_graph.set_enabled(enabled)
        self.widget_hist_curve.set_enabled(enabled)
        # todo: block signals


    def display(self, histogram):
        self.widget_hist_graph.display(histogram)


    def load_curves(self, curves):
        # Save the previous to undo the selection
        if self.previous_k_curves != '':
            self.pushButton_undo_selection.setEnabled(True)
        else:
            self.pushButton_undo_selection.setEnabled(False)
        print("load: previous: %s" % (self.previous_k_curves))
        self.previous_k_curves = self.k_curves

        # Load the selected curves
        if curves is not None:
            self.k_curves = curves['k_curves']
            log.info("load k_curves=%s" % (self.k_curves))
            if self.k_curves != '':
                self.set_current_curves_name(self.k_curves)
                self.pushButton_remove_selection.setEnabled(True)
        else:
            log.info("No curves")
            self.k_curves = ''
            self.deselect_curves_name()
            self.pushButton_remove_selection.setEnabled(False)

        print("\t-> load: previous= %s" % (self.previous_k_curves))

        self.widget_hist_curve.load_curves(curves)
        self.lineEdit_current_curves_selection.setText(self.k_curves)
        self.refresh_curves_actions_status()


    def get_curve_luts(self):
        return self.widget_hist_curve.get_curve_luts()

    def get_current_channel(self):
        return self.current_channel


    def select_channel(self):
        if self.radioButton_select_r_channel.isChecked():
            self.widget_hist_graph.select_channel('r')
            self.widget_hist_curve.select_channel('r')
            self.current_channel = 'r'
        elif self.radioButton_select_g_channel.isChecked():
            self.widget_hist_graph.select_channel('g')
            self.widget_hist_curve.select_channel('g')
            self.current_channel = 'g'
        elif self.radioButton_select_b_channel.isChecked():
            self.widget_hist_graph.select_channel('b')
            self.widget_hist_curve.select_channel('b')
            self.current_channel = 'b'
        # Emit a signal so that the histogram is calculated
        self.signal_channel_selected.emit()


    def reset_current_channel(self):
        self.widget_hist_curve.reset_channel('current')
        self.is_save_action_allowed = True
        if self.k_curves != '':
            self.pushButton_save_modifications.setEnabled(True)
            self.pushButton_discard_modifications.setEnabled(True)


    def reset_all_channels(self):
        self.widget_hist_curve.reset_channel('all')
        if self.k_curves != '':
            self.pushButton_save_modifications.setEnabled(True)
            self.pushButton_discard_modifications.setEnabled(True)



    def refresh_current_coordinates(self, coordinates:list):
        if coordinates[0] < 0:
            self.lineEdit_coordinates.clear()
        else:
            delta = ""
            if coordinates[1] > 0:
                delta = "+"
            delta += "%.1f" % (coordinates[1])
            self.lineEdit_coordinates.setText("x=%d: %s" % (coordinates[0], delta))


    def set_palette(self, palette):
        self.setPalette(palette)


    def get_preferences(self):
        preferences = {
            'stitching_curves': {
                'geometry': self.geometry().getRect(),
            },
        }
        return preferences


    def set_initial_options(self, preferences:dict):
        log.info("set_initial_options")
        s = preferences['stitching_curves']

        # Geometry
        self.move(s['geometry'][0], s['geometry'][1])

        self.adjustSize()


    def event_curves_modified(self, type:str):
        if type == 'modified':
            log.info("curves have been modified")
            if self.k_curves != '':
                self.signal_curves_modified.emit(self.widget_hist_curve.get_curves())

                # Update the global save/discard buttons
                self.pushButton_save_modifications.setEnabled(True)
                self.pushButton_discard_modifications.setEnabled(True)

                # Mark the current curves as modified
                self.mark_current_k_curves_as_modified(is_modified=True)

                # Update buttons to save/discard curves
                self.refresh_curves_actions_status()


    def event_is_saved(self, k_type):
        if k_type == 'stitching_curves':
            log.info("parameters saved")
            self.is_save_action_allowed = False
            self.pushButton_discard_modifications.setEnabled(False)


    def event_remove_selection(self):
        log.info("remove selection")

        self.signal_remove_selection.emit()
        self.pushButton_discard_modifications.setEnabled(True)
        self.pushButton_save_modifications.setEnabled(True)


    def event_discard_modifications(self):
        log.info("discard modifications")
        self.signal_reset_selection.emit()
        self.pushButton_undo_selection.setEnabled(False)
        self.pushButton_discard_modifications.setEnabled(False)
        self.pushButton_save_modifications.setEnabled(False)


    def event_save_modifications(self):
        # if self.is_save_action_allowed and self.k_curves != '':
        log.info("save all modifications: selection and curves")
        self.pushButton_save_modifications.setEnabled(False)
        self.event_save_stitching_curves()
        self.signal_save_selection.emit()


    def event_close(self):
        log.info("close button clicked")
        # self.signal_action.emit('close')


    def event_refresh_curves_list(self, curves_names:dict):
        """ Refresh the widget that contains available curves
        """
        log.info("refresh list of curves")
        self.list_curves_names.blockSignals(True)

        # Save previous curves names
        selected_k_curves = ''
        if len(self.list_curves_names.selectedIndexes()) != 0:
            if self.list_curves_names.currentItem() is not None:
                selected_k_curves = self.list_curves_names.currentItem().text()
                selected_k_curves.replace('*', '')

        # Refresh list of curves
        self.list_curves_names.clear()
        for k_curves in curves_names['all']:
            if k_curves in curves_names['modified']:
                # This on is modified, add the modification mark
                self.list_curves_names.addItem(QListWidgetItem("*%s" % k_curves))
            else:
                # Not modified
                self.list_curves_names.addItem(QListWidgetItem(k_curves))

        # Restore previous selected curves name
        if selected_k_curves != '':
            items = self.list_curves_names.findItems(selected_k_curves, Qt.MatchExactly)
            if len(items) == 0:
                items = self.list_curves_names.findItems('*' + selected_k_curves, Qt.MatchExactly)
            if len(items) != 0:
                items[0].setSelected(True)
                self.list_curves_names.setCurrentItem(items[0])

        self.list_curves_names.blockSignals(False)


    def refresh_curves_actions_status(self):
        k_curves = self.list_curves_names.currentItem().text()
        if self.k_curves != '' and '*' in k_curves:
            # log.info("%s is modified" % (k_curves))
            self.pushButton_discard_curves_modifications.setEnabled(True)
            self.pushButton_save_curves_modifications.setEnabled(True)
            self.pushButton_discard_modifications.setEnabled(True)
            self.pushButton_save_modifications.setEnabled(True)
        else:
            # log.info("%s is initial" % (k_curves))
            self.pushButton_discard_curves_modifications.setEnabled(False)
            self.pushButton_save_curves_modifications.setEnabled(False)

        #     log.info("No curves: correct this when no curves where defined at first")
            # self.pushButton_discard_modifications.setEnabled(True)
            # self.pushButton_save_modifications.setEnabled(True)




    def refresh_actions_status(self, enabled):
        k_curves = self.list_curves_names.currentItem().text()
        if self.k_curves != '' and '*' in k_curves:
            log.info("%s is modified" % (k_curves))
            self.pushButton_discard_curves_modifications.setEnabled(True)
            self.pushButton_save_curves_modifications.setEnabled(True)

        else:
            log.info("%s is initial" % (k_curves))
            self.pushButton_discard_curves_modifications.setEnabled(False)
            self.pushButton_save_curves_modifications.setEnabled(False)


    def event_set_focus(self):
        log.info("set focus on list_curves_names")
        self.list_curves_names.setFocus()



    def event_select_curve(self):
        if self.list_curves_names.currentItem() is None:
            return
        k_curves = self.list_curves_names.currentItem().text()
        log.info("event: select a curve [%s]" % (k_curves))
        self.set_current_curves_name(k_curves)

        k_curves = k_curves.replace('*', '')
        self.lineEdit_save_name.blockSignals(True)
        self.lineEdit_save_name.clear()
        self.lineEdit_save_name.blockSignals(False)

        # Enable save/discard buttons
        self.pushButton_save_modifications.setEnabled(True)
        self.pushButton_discard_modifications.setEnabled(True)

        self.signal_selection_changed.emit(k_curves)


    def event_undo_selection(self):
        print("undo: previous: %s" % (self.previous_k_curves))
        if self.previous_k_curves != '':
            k_curves = self.previous_k_curves
            self.set_current_curves_name(k_curves)
            log.info("event: undo selection [%s]" % (k_curves))
            self.set_current_curves_name(k_curves)

            k_curves = k_curves.replace('*', '')
            self.lineEdit_save_name.blockSignals(True)
            self.lineEdit_save_name.clear()
            self.lineEdit_save_name.blockSignals(False)

            # Enable save/discard buttons
            self.pushButton_save_modifications.setEnabled(True)
            self.pushButton_discard_modifications.setEnabled(True)

            print("\t-> undo: new: %s" % (k_curves))
            self.signal_selection_changed.emit(k_curves)
            self.pushButton_undo_selection.setEnabled(False)
        print("\t-> undo: previous: %s" % (self.previous_k_curves))




    def get_selected_curves_name(self):
        return self.list_curves_names.currentItem().text().replace('*', '')


    def deselect_curves_name(self):
        if len(self.list_curves_names.selectedIndexes()) == 0:
            log.info("cannot deselect curves as none is selected")
            return
        log.info("deselect curve")
        self.list_curves_names.blockSignals(True)
        self.list_curves_names.currentItem().setSelected(False)
        self.list_curves_names.blockSignals(False)



    def set_current_curves_name(self, k_curves):
        log.info("select curve in list: %s" % (k_curves))
        # deselect current curves before selecting a new one (if possible)
        self.deselect_curves_name()
        self.list_curves_names.blockSignals(True)
        if k_curves != '':
            items = self.list_curves_names.findItems(k_curves, Qt.MatchExactly)
            if len(items) == 0:
                items = self.list_curves_names.findItems('*' + k_curves, Qt.MatchExactly)

            if len(items) != 0:
                items[0].setSelected(True)
                self.list_curves_names.setCurrentItem(items[0])

            self.refresh_curves_actions_status()
        self.lineEdit_current_curves_selection.setText(k_curves)

        # self.list_curves_names.setFocus()
        self.list_curves_names.blockSignals(False)


    def mark_current_k_curves_as_modified(self, is_modified=True):
        # log.info("mark current as modified")
        if len(self.list_curves_names.selectedIndexes()) == 0:
            return

        self.list_curves_names.blockSignals(True)
        curve_name = self.list_curves_names.currentItem().text()
        if is_modified and not curve_name.startswith('*'):
            self.list_curves_names.currentItem().setText("*%s" % (curve_name))
        elif not is_modified:
            self.list_curves_names.currentItem().setText(curve_name.replace('*', ''))
        self.list_curves_names.blockSignals(False)


    def event_discard_curves_modifications(self):
        self.signal_discard_curves_modifications.emit(self.k_curves)


    def event_save_stitching_curves_as(self):
        self.lineEdit_save_name.blockSignals(True)
        k_curves_new = self.lineEdit_save_name.text()
        log.info("save curves as %s" % (k_curves_new))
        curves = self.widget_hist_curve.get_curves()

        if len(k_curves_new) > 0:
            # Save curves as...
            self.deselect_curves_name()
            self.lineEdit_save_name.clear()
            curves['k_curves'] = k_curves_new

            # self.event_discard_curves_modifications()
            if curves is not None:
                self.signal_save_curves_as.emit(curves)

        # elif self.list_curves_names.currentItem() is not None:
        #     log.info("overwrite current")
        #     # Save current selected curves
        #     k_curves = self.list_curves_names.currentItem().text()
        #     k_curves = k_curves.replace('*', '')
        #     curves['k_curves'] = k_curves
        #     self.signal_save_curves_as.emit(curves)
        else:
            log.info("missing filename")
        self.lineEdit_save_name.blockSignals(False)


    def event_save_stitching_curves(self):
        curves = self.widget_hist_curve.get_curves()
        if curves is not None:
            log.info("save curves %s" % (self.k_curves))
            self.signal_save_curves_as.emit(curves)


    def get_preview_options(self):
        preview_options = {
            'is_enabled': self.pushButton_set_preview.isChecked(),
        }
        return preview_options


    def event_preview_changed(self, state:bool=False):
        self.signal_preview_options_changed.emit()


    def mousePressEvent(self, event):
        self.previous_position = QCursor().pos()



    def mouseMoveEvent(self, event):
        if self.previous_position is not None:
            cursor_position = QCursor().pos()
            delta = QPoint(cursor_position - self.previous_position)
            self.previous_position = cursor_position
            self.move(self.pos() + delta)
            event.accept()


    def wheelEvent(self, event):
        return self.ui.wheelEvent(event)


    def keyPressEvent(self, event):
        key = event.key()
        modifier = event.modifiers()
        # print("%s.keyPressEvent: %d" % (__name__, event.key))

        if (not modifier & Qt.ControlModifier
            and key == Qt.Key_C):
            self.widget_hist_curve.reset_channel('current')
            event.accept()
            return True

        if key == Qt.Key_R:
            self.radioButton_select_r_channel.click()
            event.accept()
        elif key == Qt.Key_G:
            self.radioButton_select_g_channel.click()
            event.accept()
        elif key == Qt.Key_B:
            self.radioButton_select_b_channel.click()
            event.accept()

        elif key == Qt.Key_Delete or key == Qt.Key_Backspace:
            # Delete a single point
            self.widget_hist_curve.remove_selected_point()
            event.accept()

        elif modifier & Qt.ControlModifier:
            focus_object = QApplication.focusObject()
            if key == Qt.Key_S:
                if (focus_object is self.list_curves_names
                    or focus_object is self.widget_hist_curve):
                    self.event_save_stitching_curves()
                else:
                    self.signal_save_selection.emit()
                # log.info("discard saving as we do not know what to do")
                event.accept()
                return True
            elif key == Qt.Key_Z:
                if (focus_object is self.list_curves_names
                    or focus_object is self.widget_hist_curve):
                    self.event_discard_curves_modifications()
                else:
                    self.signal_reset_selection.emit()
                # log.info("discard saving as we do not know what to do")
                event.accept()
                return True

        return self.ui.keyPressEvent(event)



    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.ActivationChange:
            if self.isActiveWindow():
                self.ui.set_current_editor('stitching curves')
                event.accept()
                return True
        return super().changeEvent(event)