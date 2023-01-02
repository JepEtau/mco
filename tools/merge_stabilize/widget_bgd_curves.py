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
from PySide6.QtGui import (
    QColor,
)
from PySide6.QtWidgets import (
    QApplication,
    QListWidgetItem,
)
from common.widget_common import Widget_common
from common.sylesheet import set_curves_radiobutton_stylesheet, set_stylesheet, update_selected_widget_stylesheet

from merge_stabilize.model_merge_stabilize import Model_merge_stabilize
from merge_stabilize.ui.widget_bgd_curves_ui import Ui_widget_bgd_curves

GRID_COLOR = QColor(110, 110, 110)
GRID_AXIS_COLOR = QColor(110, 110, 110)
WIDGET_MARGIN = 5
GRAPH_WIDTH = 512

class Widget_bgd_curves(Widget_common, Ui_widget_bgd_curves):
    signal_curves_modified = Signal(dict)
    signal_channel_selected = Signal()
    signal_save_curves_as = Signal(dict)
    signal_selection_changed = Signal(str)
    signal_reset_selection = Signal()
    signal_remove_selection = Signal()
    signal_save_selection = Signal()

    def __init__(self, ui, model):
        super(Widget_bgd_curves, self).__init__(ui)
        self.ui = ui
        self.model = model
        self.setObjectName('bgd_curves')
        self.setAttribute(Qt.WA_DeleteOnClose)

        # Internal variables
        self.is_widget_active = False

        # Header
        self.lineEdit_current_curves_selection.clear()
        self.lineEdit_current_curves_selection.setFocusPolicy(Qt.NoFocus)

        # self.pushButton_remove_selection.setFocusPolicy(Qt.NoFocus)
        # self.pushButton_remove_selection.clicked.connect(self.event_remove_selection)
        # self.pushButton_remove_selection.setEnabled(False)

        # self.pushButton_undo.setFocusPolicy(Qt.NoFocus)
        # self.pushButton_undo.clicked.connect(self.event_undo_selection)
        # self.pushButton_undo.setEnabled(False)

        self.is_save_action_allowed = False


        for w in [self.radioButton_select_r_channel,
                self.radioButton_select_g_channel,
                self.radioButton_select_b_channel,
                self.pushButton_reset_current_channel,
                self.pushButton_reset_all_channels]:
            w.setFocusPolicy(Qt.NoFocus)

        self.radioButton_select_r_channel.clicked.connect(partial(self.event_select_channel, 'r'))
        self.radioButton_select_g_channel.clicked.connect(partial(self.event_select_channel, 'g'))
        self.radioButton_select_b_channel.clicked.connect(partial(self.event_select_channel, 'b'))
        self.pushButton_reset_current_channel.clicked.connect(partial(self.event_reset_channel, 'current'))
        self.pushButton_reset_all_channels.clicked.connect(partial(self.event_reset_channel, 'all'))

        # Curves edition: select default channel
        self.refresh_current_coordinates([-1,0])
        self.radioButton_select_r_channel.setChecked(True)


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
        # self.widget_hist_curves.signal_point_selected[list].connect(self.refresh_current_coordinates)
        # self.widget_hist_curves.signal_graph_modified[dict].connect(self.event_curves_modified)


        # Selection of curves
        self.list_curves.clear()
        self.list_curves.setFocusPolicy(Qt.NoFocus)
        # self.pushButton_discard_curves_modifications.setFocusPolicy(Qt.NoFocus)
        # self.pushButton_save_curves_as.setFocusPolicy(Qt.NoFocus)
        self.list_curves.itemSelectionChanged.connect(self.event_curves_selection_changed)
        self.list_curves.installEventFilter(self)
        self.list_curves.verticalScrollBar().installEventFilter(self)
        self.set_list_stylesheet()

        self.lineEdit_save.clear()
        self.lineEdit_save.setFocusPolicy(Qt.NoFocus)
        self.lineEdit_save.returnPressed.connect(self.event_save_curves_as)
        self.lineEdit_save.textChanged.connect(self.event_save_filename_entered)
        self.lineEdit_save.clearFocus()

        self.pushButton_save_curves.setFocusPolicy(Qt.NoFocus)


        # Signals used to refresh selection of curves
        self.model.signal_bgd_curves_library_modified[dict].connect(self.event_curves_library_modified)
        self.model.signal_load_bgd_curves[dict].connect(self.event_curves_selected)
        self.model.signal_is_saved[str].connect(self.event_is_saved)

        # Graph
        self.widget_hist_curves.signal_curves_modified[dict].connect(self.event_hist_curves_modified)


        self.k_curves = ''
        self.previous_k_curves = ''

        self.set_enabled(True)
        set_stylesheet(self)
        for c, w in zip(['r', 'g', 'b'], [
                    self.radioButton_select_r_channel,
                    self.radioButton_select_g_channel,
                    self.radioButton_select_b_channel]):
            set_curves_radiobutton_stylesheet(c, w)
        self.adjustSize()


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


    def set_enabled(self, enabled:bool):
        self.widget_hist_graph.set_enabled(enabled)
        self.widget_hist_curves.set_enabled(enabled)
        self.setEnabled(enabled)


    def is_active(self):
        return self.is_widget_active

    def get_preview_options(self):
        preview_options = {
            'is_enabled': self.pushButton_set_preview.isChecked(),
            'selected_channel': self.widget_hist_curves.selected_channel(),
        }
        return preview_options


    def refresh_values(self, frame:dict):
        print("%s: refresh_values" % (self.objectName()))
        # pprint(frame['histogram'])
        self.widget_hist_graph.select_channel(k_channel=self.widget_hist_curves.selected_channel())
        self.widget_hist_graph.refresh_values(frame)



    def event_is_saved(self, editor):
        log.info("%s: event is saved" % (self.objectName()))
        self.pushButton_save.setEnabled(True)
        pass



    def event_close(self):
        log.info("close button clicked")


    def event_hist_curves_modified(self, channels):
        self.mark_current_as_modified(True)





    def event_reset_channel(self, channel):
        self.widget_hist_curves.reset_channel(channel=channel)


    def event_select_channel(self, channel):
        # log.info("event_select_channel: %s" % (channel))
        if channel == 'r':
            self.widget_hist_curves.select_channel('r')
        elif  channel == 'g':
            self.widget_hist_curves.select_channel('g')
        elif  channel == 'b':
            self.widget_hist_curves.select_channel('b')
        elif  channel == 'm':
            self.widget_hist_curves.select_channel('m')
        self.signal_preview_options_changed.emit()















    # Curves selection
    #----------------------------------------------
    def set_list_stylesheet(self):
        self.list_curves.setStyleSheet("""
            QListWidget#list_curves {
                background-color: rgb(60, 60, 60);
                color: rgb(220, 220, 220);
                border: 1px solid rgb(80, 80, 80);
            }

            QListWidget#list_curves:hover {
                background-color: rgb(60, 60, 60);
                color: rgb(220, 220, 220);
                border: 1px solid rgb(51, 102, 204);
            }

            QListWidget#list_curves::item {
                background-color: rgb(60, 60, 60);
                color: rgb(220, 220, 220);
            }
            QListWidget#list_curves::item:selected {
                background-color: rgb(51, 102, 204);
                color: rgb(220, 220, 220);
            }
        """)


    def event_curves_library_modified(self, curves_library:dict):
        # curves_library is a simplified library which indicates if the curves are modified
        log.info("refresh the list of available curves")

        self.list_curves.blockSignals(True)

        # Save previous curve name
        saved_k_curves = ''
        if len(self.list_curves.selectedIndexes()) != 0:
            if self.list_curves.currentItem() is not None:
                saved_k_curves = self.list_curves.currentItem().text().replace('*', '')
                log.info("  save current k_curves [%s]" % (saved_k_curves))

        # Refresh the list of curves
        self.list_curves.clear()
        k_curves_list = sorted(list(curves_library.keys()))
        for k_curves in k_curves_list:
            k_curves_str = "*%s" % (k_curves) if curves_library[k_curves] else k_curves
            item = QListWidgetItem(k_curves_str)
            self.list_curves.addItem(item)

        # Restore previous selected curves name
        if saved_k_curves != '':
            items = self.list_curves.findItems(saved_k_curves, Qt.MatchExactly)
            if len(items) == 0:
                items = self.list_curves.findItems('*' + saved_k_curves, Qt.MatchExactly)
            if len(items) != 0:
                items[0].setSelected(True)
                self.list_curves.setCurrentItem(items[0])

        self.set_list_stylesheet()

        # self.lineEdit_save.setFocusPolicy(Qt.Focus)
        self.lineEdit_save.clear()
        self.lineEdit_save.clearFocus()
        self.pushButton_save_curves.setEnabled(False)

        self.list_curves.blockSignals(False)


    def deselect_current_k_curves(self):
        if len(self.list_curves.selectedIndexes()) == 0:
            # log.info("cannot deselect curves as none is selected")
            return
        self.list_curves.blockSignals(True)
        self.list_curves.currentItem().setSelected(False)
        self.list_curves.setCurrentItem(self.list_curves.item(-1))
        self.lineEdit_save.clearFocus()
        self.list_curves.blockSignals(False)


    def event_curves_selected(self, curves):
        # deselect current curves before selecting a new one
        self.deselect_current_k_curves()
        if curves is None:
            return

        self.list_curves.blockSignals(True)
        try:
            k_curves = curves['k_curves']
            if k_curves != '':
                items = self.list_curves.findItems(k_curves, Qt.MatchExactly)
                if len(items) == 0:
                    items = self.list_curves.findItems('*' + k_curves, Qt.MatchExactly)
                if len(items) != 0:
                    items[0].setSelected(True)
                    self.list_curves.setCurrentItem(items[0])

                self.previous_selected_k_curves = k_curves
        except:
            # No curves loaded
            log.info("no curves loaded")
            pass
        self.lineEdit_save.clearFocus()
        self.list_curves.blockSignals(False)


    def event_curves_selection_changed(self):
        if len(self.list_curves.selectedIndexes()) == 0:
            self.list_curves.blockSignals(True)
            self.list_curves.currentItem().setSelected(True)
            self.list_curves.blockSignals(False)
            return

        k_curves = self.list_curves.currentItem().text()
        k_curves = k_curves.replace('*', '')
        log.info("select new curves for this shot [%s]" % (k_curves))
        self.lineEdit_save.clear()
        self.lineEdit_save.clearFocus()
        # self.signal_backup_curves.emit(self.previous_k_curves)
        self.signal_curves_selection_changed.emit(k_curves)
        self.previous_k_curves = k_curves



    def mark_current_as_modified(self, is_modified):
        if len(self.list_curves.selectedIndexes()) == 0:
            return
        if is_modified:
            # log.info("set current as modified, enable save fields")
            self.lineEdit_save.setReadOnly(False)
            self.lineEdit_save.setEnabled(True)
            self.pushButton_save_curves.setEnabled(True)
            self.pushButton_discard.setEnabled(True)
        else:
            self.pushButton_discard.setEnabled(False)
        try:
            self.list_curves.blockSignals(True)
            k_curves = self.list_curves.currentItem().text()
            if is_modified and not k_curves.startswith('*'):
                self.list_curves.currentItem().setText("*%s" % (k_curves))
            elif not is_modified:
                self.list_curves.currentItem().setText(k_curves.replace('*', ''))
            self.list_curves.blockSignals(False)
        except:
            # Empty curves
            pass
        self.lineEdit_save.clearFocus()


    def event_save_filename_entered(self):
        if self.lineEdit_save.text() == '':
            self.pushButton_save_curves.setEnabled(False)
        else:
            self.pushButton_save_curves.setEnabled(True)


    def event_save_selection(self):
        # Discard new name
        self.lineEdit_save.blockSignals(True)
        self.lineEdit_save.clearFocus()
        self.lineEdit_save.blockSignals(False)

        # Get the current selected k_curves for debug only
        try: k_curves = self.list_curves.currentItem().text()
        except: k_curves = ''
        log.info("save selected curves (for debug: %s)" % (k_curves))
        self.signal_save_curves_selection_requested.emit()



    def event_save_curves_as(self):
        log.info("requested to save BGD curves or selection?")
        self.lineEdit_save.blockSignals(True)

        # Get the current selected k_curves
        try: k_curves = self.list_curves.currentItem().text()
        except: k_curves = ''

        k_curves_new = self.lineEdit_save.text()
        if len(k_curves_new) > 0:
            # 'Save as' to a new curves file
            self.deselect_current_k_curves()
            self.lineEdit_save.clear()
            # self.pushButton_save_rgb_curves.setEnabled(False)
            log.info("save new BGD curve as [%s]" % (k_curves_new))
            self.signal_save_rgb_curves_requested.emit({
                'current': k_curves.replace('*', ''),
                'new': k_curves_new,
            })

        elif self.list_curves.currentItem() is not None:
            # 'Save'
            if k_curves.startswith('*'):
                k_curves = k_curves.replace('*', '')
                log.info("overwrite BGD curves [%s]" % (k_curves))
                self.list_curves.currentItem().text().replace('*', '')
                self.signal_save_rgb_curves_requested.emit({
                    'current': k_curves,
                    'new': None,
                })
            else:
                log.info("current BGD curves are not modified [%s]" % (k_curves))
        else:
            log.info("missing filename")
        self.lineEdit_save.clearFocus()
        self.lineEdit_save.blockSignals(False)


    def event_discard(self):
        # Discard curves modifications:
        try:
            k_curves = self.list_curves.currentItem().text()
            if k_curves.startswith('*'):
                self.pushButton_discard.setEnabled(False)
                self.signal_discard_curves.emit(k_curves.replace('*', ''))
        except:
            log.info("cannot discard curves")
            pass


    def event_delete(self):
        if self.list_shots.count() > 0:
            log.info("cannot delete the selected curves")
            return
        try:
            k_curves = self.list_curves.currentItem().text().replace('*', '')
            self.signal_delete_curves.emit(k_curves)
        except:
            log.info("cannot delete curves")
            pass


    def select_next_curves(self):
        if self.list_curves.count() == 0:
            return True
        # self.list_curves.currentItem().setSelected(False)
        # self.list_curves.item(self.list_curves.currentRow()).setSelected(False)
        no = self.list_curves.currentRow() + 1
        if no >= self.list_curves.count():
            no = 0
        # log.info("select row no. %d" % (no))
        self.list_curves.setCurrentRow(no)
        self.list_curves.item(no).setSelected(True)


    def select_previous_curves(self):
        if self.list_curves.count() == 0:
            return True
        # self.list_curves.currentItem().setSelected(False)
        # self.list_curves.item(self.list_curves.currentRow()).setSelected(False)
        no = self.list_curves.currentRow()
        if no == 0:
            no = self.list_curves.count() - 1
        else:
            no = no - 1
        # log.info("select row no. %d" % (no))
        self.list_curves.setCurrentRow(no)
        self.list_curves.item(no).setSelected(True)



    def wheelEvent(self, event):
        row_no = self.list_curves.currentRow()
        if event.angleDelta().y() > 0:
            if row_no == 0:
                self.list_curves.setCurrentRow(self.list_curves.count()-1)
            else:
                self.list_curves.setCurrentRow(row_no - 1)

        elif event.angleDelta().y() < 0:
            if row_no >= self.list_curves.count()-1:
                self.list_curves.setCurrentRow(0)
            else:
                self.list_curves.setCurrentRow(row_no + 1)
        event.accept()
        return True





    # def get_current_channel(self):
    #     return self.current_channel



    # def load_curves(self, curves):
    #     # Save the previous to undo the selection
    #     if self.previous_k_curves != '':
    #         self.pushButton_undo.setEnabled(True)
    #     else:
    #         self.pushButton_undo.setEnabled(False)
    #     print("load: previous: %s" % (self.previous_k_curves))
    #     self.previous_k_curves = self.k_curves

    #     # Load the selected curves
    #     if curves is not None:
    #         self.k_curves = curves['k_curves']
    #         log.info("load k_curves=%s" % (self.k_curves))
    #         if self.k_curves != '':
    #             self.set_current_curves_name(self.k_curves)
    #             self.pushButton_remove_selection.setEnabled(True)
    #     else:
    #         log.info("No curves")
    #         self.k_curves = ''
    #         self.deselect_curves_name()
    #         self.pushButton_remove_selection.setEnabled(False)

    #     print("\t-> load: previous= %s" % (self.previous_k_curves))

    #     self.widget_hist_curves.load_curves(curves)
    #     self.lineEdit_current_curves_selection.setText(self.k_curves)
    #     self.refresh_curves_actions_status()




    # def select_channel(self):
    #     if self.radioButton_select_r_channel.isChecked():
    #         self.widget_hist_graph.select_channel('r')
    #         self.widget_hist_curves.select_channel('r')
    #         self.current_channel = 'r'
    #     elif self.radioButton_select_g_channel.isChecked():
    #         self.widget_hist_graph.select_channel('g')
    #         self.widget_hist_curves.select_channel('g')
    #         self.current_channel = 'g'
    #     elif self.radioButton_select_b_channel.isChecked():
    #         self.widget_hist_graph.select_channel('b')
    #         self.widget_hist_curves.select_channel('b')
    #         self.current_channel = 'b'
    #     # Emit a signal so that the histogram is calculated
    #     self.signal_channel_selected.emit()


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



    # def event_remove_selection(self):
    #     log.info("remove selection")

    #     self.signal_remove_selection.emit()
    #     self.pushButton_discard.setEnabled(True)
    #     self.pushButton_save.setEnabled(True)


    # def event_discard_modifications(self):
    #     log.info("discard modifications")
    #     self.signal_reset_selection.emit()
    #     self.pushButton_undo.setEnabled(False)
    #     self.pushButton_discard.setEnabled(False)
    #     self.pushButton_save.setEnabled(False)


    # def event_save_modifications(self):
    #     # if self.is_save_action_allowed and self.k_curves != '':
    #     log.info("save all modifications: selection and curves")
    #     self.pushButton_save.setEnabled(False)
    #     self.event_save_bgd_curves()
    #     self.signal_save_selection.emit()


    # def refresh_curves_actions_status(self):
    #     k_curves = self.list_curves.currentItem().text()
    #     if self.k_curves != '' and '*' in k_curves:
    #         # log.info("%s is modified" % (k_curves))
    #         self.pushButton_discard_curves_modifications.setEnabled(True)
    #         self.pushButton_save_curves_modifications.setEnabled(True)
    #         self.pushButton_discard.setEnabled(True)
    #         self.pushButton_save.setEnabled(True)
    #     else:
    #         # log.info("%s is initial" % (k_curves))
    #         self.pushButton_discard_curves_modifications.setEnabled(False)
    #         self.pushButton_save_curves_modifications.setEnabled(False)

    #     #     log.info("No curves: correct this when no curves where defined at first")
    #         # self.pushButton_discard.setEnabled(True)
    #         # self.pushButton_save.setEnabled(True)


    # def refresh_actions_status(self, enabled):
    #     k_curves = self.list_curves.currentItem().text()
    #     if self.k_curves != '' and '*' in k_curves:
    #         log.info("%s is modified" % (k_curves))
    #         self.pushButton_discard_curves_modifications.setEnabled(True)
    #         self.pushButton_save_curves_modifications.setEnabled(True)

    #     else:
    #         log.info("%s is initial" % (k_curves))
    #         self.pushButton_discard_curves_modifications.setEnabled(False)
    #         self.pushButton_save_curves_modifications.setEnabled(False)


    # def event_set_focus(self):
    #     log.info("set focus on list_curves")
    #     self.list_curves.setFocus()


    # def event_select_curve(self):
    #     if self.list_curves.currentItem() is None:
    #         return
    #     k_curves = self.list_curves.currentItem().text()
    #     log.info("event: select a curve [%s]" % (k_curves))
    #     self.set_current_curves_name(k_curves)

    #     k_curves = k_curves.replace('*', '')
    #     self.lineEdit_save.blockSignals(True)
    #     self.lineEdit_save.clear()
    #     self.lineEdit_save.blockSignals(False)

    #     # Enable save/discard buttons
    #     self.pushButton_save.setEnabled(True)
    #     self.pushButton_discard.setEnabled(True)

    #     self.signal_selection_changed.emit(k_curves)


    # def event_undo_selection(self):
    #     print("undo: previous: %s" % (self.previous_k_curves))
    #     if self.previous_k_curves != '':
    #         k_curves = self.previous_k_curves
    #         self.set_current_curves_name(k_curves)
    #         log.info("event: undo selection [%s]" % (k_curves))
    #         self.set_current_curves_name(k_curves)

    #         k_curves = k_curves.replace('*', '')
    #         self.lineEdit_save.blockSignals(True)
    #         self.lineEdit_save.clear()
    #         self.lineEdit_save.blockSignals(False)

    #         # Enable save/discard buttons
    #         self.pushButton_save.setEnabled(True)
    #         self.pushButton_discard.setEnabled(True)

    #         print("\t-> undo: new: %s" % (k_curves))
    #         self.signal_selection_changed.emit(k_curves)
    #         self.pushButton_undo.setEnabled(False)
    #     print("\t-> undo: previous: %s" % (self.previous_k_curves))


    # def get_selected_curves_name(self):
    #     return self.list_curves.currentItem().text().replace('*', '')


    # def deselect_curves_name(self):
    #     if len(self.list_curves.selectedIndexes()) == 0:
    #         log.info("cannot deselect curves as none is selected")
    #         return
    #     log.info("deselect curve")
    #     self.list_curves.blockSignals(True)
    #     self.list_curves.currentItem().setSelected(False)
    #     self.list_curves.blockSignals(False)


    # def set_current_curves_name(self, k_curves):
    #     log.info("select curve in list: %s" % (k_curves))
    #     # deselect current curves before selecting a new one (if possible)
    #     self.deselect_curves_name()
    #     self.list_curves.blockSignals(True)
    #     if k_curves != '':
    #         items = self.list_curves.findItems(k_curves, Qt.MatchExactly)
    #         if len(items) == 0:
    #             items = self.list_curves.findItems('*' + k_curves, Qt.MatchExactly)

    #         if len(items) != 0:
    #             items[0].setSelected(True)
    #             self.list_curves.setCurrentItem(items[0])

    #         self.refresh_curves_actions_status()
    #     self.lineEdit_current_curves_selection.setText(k_curves)

    #     # self.list_curves.setFocus()
    #     self.list_curves.blockSignals(False)


    # def mark_current_k_curves_as_modified(self, is_modified=True):
    #     # log.info("mark current as modified")
    #     if len(self.list_curves.selectedIndexes()) == 0:
    #         return

    #     self.list_curves.blockSignals(True)
    #     curve_name = self.list_curves.currentItem().text()
    #     if is_modified and not curve_name.startswith('*'):
    #         self.list_curves.currentItem().setText("*%s" % (curve_name))
    #     elif not is_modified:
    #         self.list_curves.currentItem().setText(curve_name.replace('*', ''))
    #     self.list_curves.blockSignals(False)


    # def event_save_bgd_curves_as(self):
    #     self.lineEdit_save.blockSignals(True)
    #     k_curves_new = self.lineEdit_save.text()
    #     log.info("save curves as %s" % (k_curves_new))
    #     curves = self.widget_hist_curves.get_curves()

    #     if len(k_curves_new) > 0:
    #         # Save curves as...
    #         self.deselect_curves_name()
    #         self.lineEdit_save.clear()
    #         curves['k_curves'] = k_curves_new

    #         # self.event_discard_curves_modifications()
    #         if curves is not None:
    #             self.signal_save_curves_as.emit(curves)

    #     # elif self.list_curves.currentItem() is not None:
    #     #     log.info("overwrite current")
    #     #     # Save current selected curves
    #     #     k_curves = self.list_curves.currentItem().text()
    #     #     k_curves = k_curves.replace('*', '')
    #     #     curves['k_curves'] = k_curves
    #     #     self.signal_save_curves_as.emit(curves)
    #     else:
    #         log.info("missing filename")
    #     self.lineEdit_save.blockSignals(False)


    # def event_save_bgd_curves(self):
    #     curves = self.widget_hist_curves.get_curves()
    #     if curves is not None:
    #         log.info("save curves %s" % (self.k_curves))
    #         self.signal_save_curves_as.emit(curves)


    # def event_rgb_graph_modified(self, channels):
    #     self.widget_curves_selection.mark_current_as_modified(True)



    # Key and mouse events
    #----------------------------------------------


    def event_key_pressed(self, event):
        key = event.key()
        modifiers = event.modifiers()

        if modifiers & Qt.ControlModifier:
            if key == Qt.Key_S:
                if self.widget_curves_selection.is_active():
                    log.info("Save RGB curves")
                    self.widget_curves_selection.event_save_curves_as()
                    return True
                else:
                    log.info("Save selected curves for this shot")
                    self.widget_curves_selection.event_save_selection()
                    return True

        if key == Qt.Key_F2:
            if self.pushButton_set_preview.isEnabled():
                self.pushButton_set_preview.toggle()
                return True

        if (not modifiers & Qt.ControlModifier
            and key == Qt.Key_C):
            self.widget_hist_curves.reset_channel('current')
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


        elif modifiers & Qt.ControlModifier:
            focus_object = QApplication.focusObject()
            if key == Qt.Key_Z:
                if (focus_object is self.list_curves
                    or focus_object is self.widget_hist_curve):
                    self.event_discard_curves_modifications()
                else:
                    self.signal_reset_selection.emit()
                # log.info("discard saving as we do not know what to do")
                return True

        # if self.widget_curves_selection.is_active():
        #     if self.widget_curves_selection.event_key_pressed(event):
        #         return True

        return self.widget_hist_curves.event_key_pressed(event)



    def event_key_released(self, event):
        return False




