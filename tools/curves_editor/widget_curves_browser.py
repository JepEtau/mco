# -*- coding: utf-8 -*-

from logger import log
from pprint import pprint

from PySide6.QtCore import (
    Qt,
    Signal,
)
from PySide6.QtWidgets import (
    QListWidgetItem,
    QWidget,
)

from curves_editor.ui.widget_curves_browser_ui import Ui_widget_curves_browser
from common.sylesheet import set_stylesheet


class Widget_curves_browser(QWidget, Ui_widget_curves_browser):
    signal_select_curves = Signal(str)
    signal_backup_curves = Signal(str)
    signal_save_curves_as = Signal(str)

    def __init__(self, ui, model):
        super(Widget_curves_browser, self).__init__()
        self.model = model
        self.ui = ui

        # Create and patch UI
        self.setupUi(self)
        self.list_curve_names.clear()
        self.list_shots_using_same_curves.clear()
        self.lineEdit_save_name.clear()

        self.list_curve_names.setFocusPolicy(Qt.NoFocus)
        self.pushButton_save.setFocusPolicy(Qt.NoFocus)

        # Variables
        self.previous_k_curves = ''

        # Connect signals
        self.list_curve_names.itemSelectionChanged.connect(self.event_select_curve)
        self.list_curve_names.itemClicked.connect(self.event_set_focus)

        self.lineEdit_save_name.editingFinished.connect(self.event_save_as)
        self.pushButton_save.released.connect(self.event_save_as)

        self.model.signal_refresh_curves_list[list].connect(self.event_refresh_curve_list)
        self.model.signal_refresh_curves_shot_list[list].connect(self.event_refresh_shot_list)

        set_stylesheet(self)


    def set_enabled(self, enabled):
        log.info("set enabled: %s" % ('true' if enabled else 'false'))
        self.setEnabled(enabled)
        self.list_curve_names.setEnabled(enabled)


    def event_refresh_curve_list(self, curve_list:list):
        """ Refresh the widget that contains available curves
        """
        log.info("refresh list of curves")
        self.list_curve_names.blockSignals(True)

        # Save previous curve name
        saved_k_curves = ''
        if len(self.list_curve_names.selectedIndexes()) != 0:
            if self.list_curve_names.currentItem() is not None:
                saved_k_curves = self.list_curve_names.currentItem().text()
                saved_k_curves.replace('*', '')

        # Refresh list of curves
        self.list_curve_names.clear()
        for name in curve_list:
            self.list_curve_names.addItem(QListWidgetItem(name))

        # Restore previous selected curves name
        if saved_k_curves != '':
            items = self.list_curve_names.findItems(saved_k_curves, Qt.MatchExactly)
            if len(items) == 0:
                items = self.list_curve_names.findItems('*' + saved_k_curves, Qt.MatchExactly)
            if len(items) != 0:
                items[0].setSelected(True)
                self.list_curve_names.setCurrentItem(items[0])

        self.list_curve_names.blockSignals(False)


    def event_refresh_shot_list(self, shot_list:list):
        """ Refresh the widget that contains shots for the current curves
        """
        log.info("refresh list of shots")
        self.list_shots_using_same_curves.clear()
        for s in shot_list:
            self.list_shots_using_same_curves.addItem('%05d' % (s))

    def event_set_focus(self):
        log.info("set focus on list_curve_names")
        self.list_curve_names.setFocus()

    def event_select_curve(self):
        if self.list_curve_names.currentItem() is None:
            return
        curve_name = self.list_curve_names.currentItem().text()
        curve_name = curve_name.replace('*', '')
        log.info("event: select a curve [%s]" % (curve_name))
        self.lineEdit_save_name.clear()
        self.signal_backup_curves.emit(self.previous_k_curves)
        self.signal_select_curves.emit(curve_name)
        self.previous_k_curves = curve_name


    def get_selected_curve_name(self):
        if self.list_curve_names.currentItem() is not None:
            curve_name = self.list_curve_names.currentItem().text()
            return curve_name.replace('*', '')
        return ''

    def deselect_curve_name(self):
        if len(self.list_curve_names.selectedIndexes()) == 0:
            log.info("cannot deselect curve as none is selected")
            return
        log.info("deselect curve")
        self.list_curve_names.blockSignals(True)
        self.list_curve_names.currentItem().setSelected(False)
        self.list_curve_names.blockSignals(False)


    def set_current_curve_name(self, k_curves):
        log.info("select curve in list: %s" % (k_curves))
        # deselect current curves before selecting a new one (if possible)
        self.deselect_curve_name()
        self.list_curve_names.blockSignals(True)
        if k_curves != '':
            items = self.list_curve_names.findItems(k_curves, Qt.MatchExactly)
            if len(items) == 0:
                items = self.list_curve_names.findItems('*' + k_curves, Qt.MatchExactly)
                log.info("found modified curves")
            if len(items) != 0:
                items[0].setSelected(True)
                self.list_curve_names.setCurrentItem(items[0])
        # self.list_curve_names.setFocus()
        self.list_curve_names.blockSignals(False)
        self.previous_k_curves = k_curves


    def mark_curve_as_modified(self, is_modified=True):
        # log.info("mark current as modified")
        if len(self.list_curve_names.selectedIndexes()) == 0:
            return

        self.list_curve_names.blockSignals(True)
        curve_name = self.list_curve_names.currentItem().text()
        if is_modified and not curve_name.startswith('*'):
            self.list_curve_names.currentItem().setText("*%s" % (curve_name))
        elif not is_modified:
            self.list_curve_names.currentItem().setText(curve_name.replace('*', ''))
        self.list_curve_names.blockSignals(False)



    # def event_filename_modified(self):
    #     self.lineEdit_save_name.blockSignals(True)
    #     new_curve_name = self.lineEdit_save_name.text()
    #     log.info("new name: %s" % (new_curve_name))
    #     if len(new_curve_name) > 0:
    #         if len(self.list_curve_names.selectedIndexes()) != 0:
    #             self.list_curve_names.blockSignals(True)
    #             self.list_curve_names.currentItem().setSelected(False)
    #             self.list_curve_names.blockSignals(False)
    #         self.lineEdit_save_name.clear()
    #         self.signal_save_curves_as.emit(new_curve_name)
    #     self.lineEdit_save_name.blockSignals(False)


    def event_save_as(self):
        self.lineEdit_save_name.blockSignals(True)
        new_curve_name = self.lineEdit_save_name.text()
        log.info("save curve as %s" % (new_curve_name))

        if len(new_curve_name) > 0:
            self.deselect_curve_name()
            self.lineEdit_save_name.clear()
            self.signal_save_curves_as.emit(new_curve_name)

        elif self.list_curve_names.currentItem() is not None:
            curve_name = self.list_curve_names.currentItem().text()
            curve_name = curve_name.replace('*', '')
            self.signal_save_curves_as.emit(curve_name)
        else:
            log.info("missing filename")
        self.lineEdit_save_name.blockSignals(False)


    def wheelEvent(self, event):
        row_no = self.list_curve_names.currentRow()
        if event.angleDelta().y() > 0:
            if row_no == 0:
                self.list_curve_names.setCurrentRow(self.list_curve_names.count()-1)
            else:
                self.list_curve_names.setCurrentRow(row_no - 1)

        elif event.angleDelta().y() < 0:
            if row_no >= self.list_curve_names.count()-1:
                self.list_curve_names.setCurrentRow(0)
            else:
                self.list_curve_names.setCurrentRow(row_no + 1)
        event.accept()
        return True


    # def keyPressEvent(self, event):
    #     return self.ui.keyPressEvent(event)
