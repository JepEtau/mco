# -*- coding: utf-8 -*-
import sys
sys.path.append('../scripts')

from pprint import pprint
from logger import log

from PySide6.QtCore import (
    QEvent,
    QObject,
    QPoint,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QColor,
    QCursor,
)
from PySide6.QtWidgets import (
    QTableWidgetItem,
    QWidget,
)

from common.sylesheet import (
    set_stylesheet,
    update_selected_widget_stylesheet,
)

from utils.common import K_GENERIQUES, K_PARTS, K_ALL_PARTS
from filters_editor.ui.widget_selection_ui import Ui_widget_selection


class Widget_selection(QWidget, Ui_widget_selection):
    signal_ep_or_part_selection_changed = Signal(dict)
    signal_selected_shots_changed = Signal(dict)
    signal_close = Signal()


    def __init__(self, ui, model):
        super(Widget_selection, self).__init__()
        self.setupUi(self)
        self.model = model
        self.ui = ui

        # Setup and patch ui
        self.setAutoFillBackground(True)
        self.setWindowFlags(Qt.Tool)
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setWindowModality(Qt.NonModal)
        self.setAttribute(Qt.WA_DeleteOnClose)

        # Internal variables
        self.episodes_and_parts = dict()
        self.comboBox_episode.clear()
        self.comboBox_part.clear()
        self.previous_position = None
        self.is_modified = False
        self.previous_selection = [0]

        # Initialize widgets
        self.comboBox_episode.setFocusPolicy(Qt.NoFocus)
        self.comboBox_part.setFocusPolicy(Qt.NoFocus)
        self.comboBox_step.setFocusPolicy(Qt.NoFocus)
        self.tableWidget_shots.setFocusPolicy(Qt.NoFocus)


        step_labels = self.model.get_step_labels()
        self.comboBox_step.clear()
        for s in step_labels:
            self.comboBox_step.addItem(s)

        self.comboBox_episode.currentIndexChanged['int'].connect(self.event_episode_changed)
        self.comboBox_part.currentIndexChanged['int'].connect(self.event_part_changed)
        self.comboBox_step.currentIndexChanged['int'].connect(self.event_step_changed)


        self.tableWidget_shots.clearContents()
        self.tableWidget_shots.setRowCount(0)

        self.alignment = [Qt.AlignRight | Qt.AlignVCenter,
                            Qt.AlignCenter | Qt.AlignVCenter,
                            Qt.AlignRight | Qt.AlignVCenter,
                            Qt.AlignCenter | Qt.AlignVCenter,
                            Qt.AlignLeft | Qt.AlignVCenter]
        headers = ["shot", "src", "start", "count", "filters ID"]
        default_col_width = [50, 60, 65, 60, 60]
        for col_no, header_str, col_width in zip(range(len(headers)),
                                                    headers,
                                                    default_col_width):
            self.tableWidget_shots.horizontalHeaderItem(col_no).setText(header_str)
            # self.tableWidget_shots.horizontalHeaderItem(col_no).setTextAlignment(align)
            self.tableWidget_shots.setColumnWidth(col_no, col_width)

        self.tableWidget_shots.horizontalHeader().setStretchLastSection(True)

        # Connect signals and filter events
        self.tableWidget_shots.selectionModel().selectionChanged.connect(self.event_ep_or_part_selection_changed)
        self.tableWidget_shots.installEventFilter(self)

        self.model.signal_shotlist_modified[dict].connect(self.event_refresh_shotlist)
        self.model.signal_is_modified[dict].connect(self.refresh_modification_status)
        self.model.signal_current_shot_modified[dict].connect(self.event_current_shot_modified)

        self.set_enabled(False)
        set_stylesheet(self)
        self.set_selected(False)
        self.adjustSize()


    def closeEvent(self, event):
        self.signal_close.emit()


    def get_preferences(self):
        k_ep = ''
        if (self.comboBox_episode.currentText() != ' '
        and self.comboBox_episode.currentText() != ''):
            k_ep = int(self.comboBox_episode.currentText())
        preferences = {
            'geometry': self.geometry().getRect(),
            'episode': k_ep,
            'part': self.comboBox_part.currentText(),
            'step': self.comboBox_step.currentText(),
        }
        return preferences


    def set_initial_options(self, preferences:dict):
        log.info("set_initial_options")
        s = preferences['selection']
        # print("%s:set_initial_options: " % (__name__), s)

        self.set_enabled(False)
        self.tableWidget_shots.setEnabled(False)

        # Episode
        self.refresh_combobox_episode()
        self.comboBox_episode.blockSignals(True)
        saved_ep_no = s['episode']
        if saved_ep_no == 0:
            # print("none selected")
            self.comboBox_episode.setCurrentText(" ")
        else:
            index = self.comboBox_episode.findText(str(saved_ep_no))
            self.comboBox_episode.setCurrentIndex(index)
        # self.comboBox_episode.blockSignals(False)

        # Part
        self.refresh_combobox_part()
        self.comboBox_part.blockSignals(True)
        self.comboBox_part.setCurrentText(s['part'])
        if s['part'] in K_ALL_PARTS:
            index = self.comboBox_part.findText(s['part'])
            self.comboBox_part.setCurrentIndex(index)
        # self.comboBox_part.blockSignals(False)

        # Step
        self.comboBox_part.blockSignals(True)
        index = self.comboBox_part.findText(s['step'])
        index = 0 if index == -1 else index
        self.comboBox_part.setCurrentIndex(index)
        self.comboBox_part.blockSignals(False)

        # Shots
        self.tableWidget_shots.blockSignals(True)
        self.tableWidget_shots.clearContents()
        self.tableWidget_shots.setRowCount(0)
        # self.tableWidget_shots.blockSignals(False)

        # Geometry
        self.move(s['geometry'][0], s['geometry'][1])
        self.adjustSize()

        self.event_episode_changed()


    def set_selected(self, is_selected):
        update_selected_widget_stylesheet(self.frame, is_selected=is_selected)


    def refresh_modification_status(self, modifications:dict):
        # Something has been modified, disable selection until saving or discard
        self.is_modified = modifications['status']
        if self.is_modified:
            self.set_enabled(False)
            self.widget_app_controls.set_save_discard_enabled(True)
        else:
            self.set_enabled(True)
            self.widget_app_controls.set_save_discard_enabled(False)

        if 'geometry' in modifications.keys():
            self.set_crop_coordinates(modifications['geometry'])

        if modifications['shot_no'] is not None:
            log.info("shot no. %d has been modified" % (modifications['shot_no']))


    def refresh_browsing_folder(self, episodes_and_parts:dict):
        log.info("refresh combobox_episode")
        # print("%s:refresh_browsing_folder: " % (__name__), episodes_and_parts)
        self.episodes_and_parts = episodes_and_parts



    def refresh_combobox_episode(self):
        episodes = sorted(list(self.episodes_and_parts.keys()))
        self.comboBox_episode.blockSignals(True)
        self.comboBox_episode.clear()
        for k_ep in episodes:
            if k_ep == ' ' or k_ep == '':
                self.comboBox_episode.addItem(' ')
            else:
                self.comboBox_episode.addItem(str(int(k_ep[2:])))
        self.comboBox_episode.setEnabled(True)
        self.comboBox_episode.blockSignals(False)



    def refresh_combobox_part(self, index=-1):
        self.comboBox_part.blockSignals(True)

        saved_part = self.comboBox_part.currentText()

        self.comboBox_part.clear()
        if index != -1:
            # index is the new selected episode
            selected_ep_str = self.comboBox_episode.itemText(index)
        else:
            selected_ep_str = self.comboBox_episode.currentText()

        if selected_ep_str == ' ' or selected_ep_str == '':
            for k_p in K_GENERIQUES:
                if k_p in self.episodes_and_parts[' ']:
                    self.comboBox_part.addItem(k_p)
                    # print("\t[%s]" % (k_p))
        elif selected_ep_str != '':
            k_ep = 'ep%02d' % (int(selected_ep_str))
            for k_p in K_PARTS:
                if k_p in self.episodes_and_parts[k_ep]:
                    self.comboBox_part.addItem(k_p)
                    # print("\t[%s]" % (k_p))

        # Restore the previous part if exists
        i = self.comboBox_part.findText(saved_part)
        new_index = i if i != -1 else 0
        self.comboBox_part.setCurrentIndex(index)

        if self.comboBox_part.count() > 0:
            self.comboBox_part.setEnabled(True)
        else:
            self.comboBox_part.setEnabled(False)
        self.comboBox_part.blockSignals(False)
        self.comboBox_episode.blockSignals(False)


    def event_current_shot_modified(self, modifications:dict):
        self.tableWidget_shots.blockSignals(True)
        row_no = self.tableWidget_shots.currentRow()

        self.tableWidget_shots.blockSignals(False)




    def event_refresh_shotlist(self, values:dict):
        log.info("directory has been parsed, refresh shot list")
        # print("%s:event_refresh:" % (__name__))
        # pprint(values)
        # print("---")
        # sys.exit()
        self.set_enabled(False)
        self.tableWidget_shots.blockSignals(True)


        # Episode
        k_ep = values['k_ep']
        ep_no_str = str(int(k_ep[2:])) if (k_ep != '' and  k_ep != ' ') else ''
        if self.comboBox_episode.currentText() != ep_no_str:
            i = self.comboBox_episode.findText(ep_no_str)
            self.comboBox_episode.blockSignals(True)
            new_index = i if i != -1 else 0
            self.comboBox_episode.setCurrentIndex(new_index)
            self.comboBox_episode.blockSignals(False)

        # Part
        if self.comboBox_part.currentText() != values['k_part']:
            i = self.comboBox_part.findText(values['k_part'])
            self.comboBox_part.blockSignals(True)
            new_index = i if i != -1 else 0
            self.comboBox_part.setCurrentIndex(new_index)
            self.comboBox_part.blockSignals(False)

        # Steps
        i = self.comboBox_step.findText(values['k_step'])
        self.comboBox_step.blockSignals(True)
        new_index = i if i != -1 else 0
        self.comboBox_step.setCurrentIndex(i)
        self.comboBox_step.blockSignals(False)

        # Shots
        shots = values['shots']
        self.tableWidget_shots.clearContents()
        self.tableWidget_shots.setRowCount(0)
        row_no = 0
        for k_shot, shot in shots.items():
            self.tableWidget_shots.insertRow(row_no)
            self.tableWidget_shots.setItem(row_no, 0, QTableWidgetItem('%05d' % (k_shot)))
            src_txt = ""
            if 'src' in shot.keys():
                src_txt = "%s:%s" % (shot['src']['k_ed'], shot['src']['k_ep'])
            self.tableWidget_shots.setItem(row_no, 1, QTableWidgetItem(src_txt))

            self.tableWidget_shots.setItem(row_no, 2, QTableWidgetItem(str(shot['start'])))
            self.tableWidget_shots.setItem(row_no, 3, QTableWidgetItem(str(shot['count'])))

            self.tableWidget_shots.setItem(row_no, 4, QTableWidgetItem(''))

            for i in range(len(self.alignment)):
                self.tableWidget_shots.item(row_no, i).setTextAlignment(self.alignment[i])
                self.tableWidget_shots.item(row_no, i).setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)

            if not shot['is_valid']:
                # If true, it means that all pictures are present in the folder
                # Bug: this does not work
                self.tableWidget_shots.item(row_no, 0).setData(Qt.FontRole, QColor(Qt.red))
            row_no += 1

        self.tableWidget_shots.selectionModel().clearSelection()
        self.tableWidget_shots.blockSignals(False)

        self.tableWidget_shots.setEnabled(True)
        self.set_enabled(True)

        if len(shots) > 0:
            log.info("select shot no. 0")
            self.tableWidget_shots.selectRow(0)


    def event_episode_changed(self, index=0):
        log.info("select ep: %s, part: %s" % (self.comboBox_episode.currentText(), self.comboBox_part.currentText()))
        self.refresh_combobox_part(-1)
        # Generate a signal to inform that the following shall be updated:
        #   - editions
        #   - filter ids
        #   - list of frames
        k_ep = ''
        selected_ep_str = self.comboBox_episode.currentText()
        if selected_ep_str not in ['', ' ']:
            k_ep = 'ep%02d' % (int(self.comboBox_episode.currentText()))

        values = {
            'k_ep': k_ep,
            'k_part': self.comboBox_part.itemText(0),
            'k_step': self.comboBox_step.currentText()
        }

        # if values['k_part'] != '':
        self.signal_ep_or_part_selection_changed.emit(values)
        return True



    def event_part_changed(self, index):
        log.info("select ep: %s, part: %s" % (self.comboBox_episode.currentText(), self.comboBox_part.currentText()))

        k_ep = ''
        selected_ep_str = self.comboBox_episode.currentText()
        if selected_ep_str not in ['', ' ']:
            k_ep = 'ep%02d' % (int(self.comboBox_episode.currentText()))

        values = {
            'k_ep': k_ep,
            'k_part': self.comboBox_part.currentText(),
            'k_step': self.comboBox_step.currentText()
        }

        # if values['k_part'] != '':
        self.signal_ep_or_part_selection_changed.emit(values)
        return True


    def event_step_changed(self, index):
        log.info("changed step")
        self.event_part_changed(index)


    def event_ep_or_part_selection_changed(self, selected):
        # print("event_ep_or_part_selection_changed")
        selected_indexes = self.tableWidget_shots.selectedIndexes()
        selected_row_no = sorted(list(set([i.row() for i in selected_indexes])))
        if len(selected_row_no) == 0:
            # No selection, restore previous selection
            self.tableWidget_shots.blockSignals(True)
            self.tableWidget_shots.selectionModel().blockSignals(True)
            # self.tableWidget_shots.selectionModel().select(self.previous_selection, QtGui.QItemSelectionModel.Rows | QtGui.QItemSelectionModel.Select)
            # selectedRows(self.previous_selection)
            self.tableWidget_shots.selectionModel().blockSignals(False)
            self.tableWidget_shots.blockSignals(False)
            log.error("Restore previous selection")
            return
        self.previous_selection = selected_indexes

        log.info("event_ep_or_part_selection_changed: %s" % (', '.join(map(lambda x: "%s" % (x), selected_row_no))))

        selected_shots_no = list()
        for row_no in selected_row_no:
            shot_no_str = self.tableWidget_shots.item(row_no, 0).text()
            selected_shots_no.append(int(shot_no_str))

        k_ep = ''
        if self.comboBox_episode.currentText() not in ['', ' ']:
            k_ep = 'ep%02d' % (int(self.comboBox_episode.currentText()))
        selected_shots = {
            'k_ep': k_ep,
            'k_part': self.comboBox_part.currentText(),
            'k_step': self.comboBox_step.currentText(),
            'shotlist': selected_shots_no
        }
        self.signal_selected_shots_changed.emit(selected_shots)


    def set_enabled(self, enabled):
        if self.is_modified and enabled:
            # do not allow selection until all modifications are saved or discarded
            return

        self.comboBox_episode.setEnabled(enabled)
        self.comboBox_part.setEnabled(enabled)
        self.comboBox_step.setEnabled(enabled)
        # self.tableWidget_shots.setEnabled(enabled)



    def refresh_values(self, frame:dict):
        pass

    def get_preview_options(self):
        return None



    def select_next_shot(self):
        if len(self.tableWidget_shots.selectionModel().selectedRows()) > 1:
            return
        try:
            row_no = self.tableWidget_shots.currentRow() + 1
            if row_no >= self.tableWidget_shots.rowCount():
                row_no = 0
            self.tableWidget_shots.clearSelection()
            self.tableWidget_shots.selectRow(row_no)
        except:
            pass

    def select_previous_shot(self):
        if len(self.tableWidget_shots.selectionModel().selectedRows()) > 1:
            return
        try:
            row_no = self.tableWidget_shots.currentRow()
            if row_no == 0:
                row_no = self.tableWidget_shots.rowCount() - 1
            else:
                row_no -= 1
            self.tableWidget_shots.clearSelection()
            self.tableWidget_shots.selectRow(row_no)
        except:
            pass


    def mousePressEvent(self, event):
        self.previous_position = QCursor().pos()

    def mouseMoveEvent(self, event):
        if self.previous_position is not None:
            cursor_position = QCursor().pos()
            delta = QPoint(cursor_position - self.previous_position)
            self.previous_position = cursor_position
            self.move(self.pos() + delta)
            event.accept()


    def keyPressEvent(self, event):
        # print("event_key_pressed")
        if self.event_key_pressed(event):
            event.accept()
            return True
        return self.ui.keyPressEvent(event)


    def event_key_pressed(self, event):
        key = event.key()
        modifiers = event.modifiers()
        if modifiers & Qt.ControlModifier and key == Qt.Key_A:
            self.tableWidget_shots.selectAll()
            event.accept()
            return True
        return False

    def keyReleaseEvent(self, event):
        # print("event_key_released")
        if self.event_key_released(event):
            event.accept()
            return True
        return self.ui.keyReleaseEvent(event)


    def event_key_released(self, event):
        return False




    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        # return super().eventFilter(watched, event)
        # # Filter press/release events
        if event.type() == QEvent.KeyPress:
            event.accept()
            return self.ui.keyPressEvent(event)
        elif event.type() == QEvent.KeyRelease:
            event.accept()
            return self.ui.keyReleaseEvent(event)

        if event.type() == QEvent.Wheel:
            if event.angleDelta().y() > 0:
                self.select_previous_shot()
            else:
                self.select_next_shot()
            event.accept()
            return True

        return super().eventFilter(watched, event)
        # return True




    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.ActivationChange:
            if self.isActiveWindow():
                self.ui.set_current_editor('selection')
                event.accept()
                return True
        return False
        # super().changeEvent(event)


