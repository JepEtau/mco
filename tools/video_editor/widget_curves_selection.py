# -*- coding: utf-8 -*-

import sys
sys.path.append('../scripts')

from logger import log
from pprint import pprint

from PySide6.QtCore import (
    Qt,
    Signal,
    QEvent,
    QObject,
)
from PySide6.QtWidgets import (
    QListWidgetItem,
    QWidget,
)

from video_editor.ui.widget_curves_selection_ui import Ui_widget_curves_selection


class Widget_curves_selection(QWidget, Ui_widget_curves_selection):
    signal_curves_selection_changed = Signal(str)
    signal_save_rgb_curves_requested = Signal(dict)
    signal_save_curves_selection_requested = Signal()
    signal_discard_curves = Signal(str)
    signal_delete_curves = Signal(str)


    def __init__(self, parent):
        super(Widget_curves_selection, self).__init__(parent)
        self.setupUi(self)
        self.setObjectName('curves_selection')
        self.setAttribute(Qt.WA_DeleteOnClose)


        # Internal variables
        self.is_widget_active = False

        # Disable focus
        self.lineEdit_save.setFocusPolicy(Qt.ClickFocus)
        self.list_curves.setFocusPolicy(Qt.NoFocus)
        self.list_shots.setFocusPolicy(Qt.NoFocus)
        self.pushButton_save_rgb_curves.setFocusPolicy(Qt.NoFocus)
        self.pushButton_delete.setFocusPolicy(Qt.NoFocus)

        # Reset widgets
        self.lineEdit_save.clear()
        self.pushButton_save_rgb_curves.setEnabled(False)
        self.list_curves.clear()
        self.list_shots.clear()
        self.pushButton_discard.setEnabled(False)

        # Connect signals and filter events
        self.lineEdit_save.returnPressed.connect(self.event_save_rgb_curves_as)
        self.lineEdit_save.textChanged.connect(self.event_save_filename_entered)
        self.pushButton_save_rgb_curves.clicked.connect(self.event_save_rgb_curves_as)
        self.pushButton_discard.clicked.connect(self.event_discard)
        self.pushButton_delete.clicked.connect(self.event_delete)


        self.list_curves.itemSelectionChanged.connect(self.event_curves_selection_changed)

        self.list_curves.installEventFilter(self)
        self.list_curves.verticalScrollBar().installEventFilter(self)

        self.lineEdit_save.clearFocus()
        self.set_list_stylesheet()
        self.adjustSize()


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


    def set_model(self, model):
        self.model = model

        # Connect signals
        self.model.signal_curves_library_modified[dict].connect(self.event_curves_library_modified)
        self.model.signal_load_curves[dict].connect(self.event_curves_selected)
        self.model.signal_shot_per_curves_modified[list].connect(self.event_shots_per_curves_modified)


    def set_ui(self, ui):
        self.ui = ui


    def set_enabled(self, enabled):
        self.setEnabled(enabled)

    def is_active(self):
        return self.is_widget_active

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
        self.pushButton_save_rgb_curves.setEnabled(False)

        self.list_curves.blockSignals(False)


    def event_shots_per_curves_modified(self, shots_per_curves):
        self.list_shots.clear()
        try:
            for shot_no in shots_per_curves:
                item = QListWidgetItem("%03d" % (shot_no))
                item.setTextAlignment(Qt.AlignRight)
                self.list_shots.addItem(item)
        except:
            pass


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
            self.pushButton_save_rgb_curves.setEnabled(True)
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
            self.pushButton_save_rgb_curves.setEnabled(False)
        else:
            self.pushButton_save_rgb_curves.setEnabled(True)




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


    def event_save_rgb_curves_as(self):
        log.info("requested to save RGB curves or selection?")
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
            log.info("save new RGB curve as [%s]" % (k_curves_new))
            self.signal_save_rgb_curves_requested.emit({
                'current': k_curves.replace('*', ''),
                'new': k_curves_new,
            })

        elif self.list_curves.currentItem() is not None:
            # 'Save'
            if k_curves.startswith('*'):
                k_curves = k_curves.replace('*', '')
                log.info("overwrite RGB curves [%s]" % (k_curves))
                self.list_curves.currentItem().text().replace('*', '')
                self.signal_save_rgb_curves_requested.emit({
                    'current': k_curves,
                    'new': None,
                })
            else:
                log.info("current RGB curves are not modified [%s]" % (k_curves))
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


    def keyPressEvent(self, event):
        if self.event_key_pressed(event):
            event.accept()
            return True
        return self.ui.keyPressEvent(event)


    def event_key_pressed(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            self.lineEdit_save.clear()
            self.lineEdit_save.clearFocus()
            self.pushButton_save_rgb_curves.setEnabled(False)
            return True
        elif key == Qt.Key_Delete:
            self.event_delete()
            return True
        return False


    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Wheel:
            if event.angleDelta().y() > 0:
                self.select_previous_curves()
            else:
                self.select_next_curves()
            event.accept()
            return True

        if event.type() == QEvent.Enter:
            self.is_widget_active = True

        elif event.type() == QEvent.Leave:
            self.is_widget_active = False

        return super().eventFilter(watched, event)

