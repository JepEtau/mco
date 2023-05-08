# -*- coding: utf-8 -*-
import platform
import sys


from functools import partial

from utils.pretty_print import *
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
    QBrush,
    QColor,
    QCursor,
    QKeyEvent,
    QWheelEvent,
)
from PySide6.QtWidgets import (
    QTableWidgetItem,
    QWidget,
    QCheckBox,
    QHBoxLayout,
)

from utils.stylesheet import (
    COLOR_PURPLE,
    COLOR_TEXT,
    set_stylesheet,
    set_widget_stylesheet,
    update_selected_widget_stylesheet,
)

from utils.common import K_GENERIQUES, K_PARTS, K_ALL_PARTS
from views.ui.widget_selection_ui import Ui_widget_selection
from views.widget_common import Widget_common


class Widget_selection(QWidget, Ui_widget_selection):
    signal_widget_selected = Signal(str)
    signal_selection_changed = Signal(dict)
    signal_selected_shots_changed = Signal(dict)
    signal_selected_step_changed = Signal(str)
    signal_close = Signal()


    def __init__(self, parent, controller):
        super(Widget_selection, self).__init__()
        self.setupUi(self)
        self.controller = controller
        self.setObjectName('selection')

        # Setup and patch ui
        self.setAutoFillBackground(True)
        self.setWindowFlags(Qt.Tool)
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setWindowModality(Qt.NonModal)
        self.setAttribute(Qt.WA_DeleteOnClose)

        # Internal variables
        self.__parent = parent
        self.episodes_and_parts = dict()
        self.comboBox_episode.clear()
        self.comboBox_part.clear()
        self.previous_position = None
        self.is_modified = False
        self.initial_shot_no = None
        self.previous_selection = [0]

        # Initialize widgets
        self.comboBox_episode.setFocusPolicy(Qt.NoFocus)
        self.comboBox_part.setFocusPolicy(Qt.NoFocus)
        self.tableWidget_shots.setFocusPolicy(Qt.NoFocus)

        self.comboBox_episode.currentIndexChanged['int'].connect(self.event_episode_changed)
        self.comboBox_part.currentIndexChanged['int'].connect(self.event_part_changed)

        self.radioButtons_steps = {
            'deinterlace': self.radioButton_task_deinterlace,
            'pre_upscale': self.radioButton_task_pre_upscale,
            'upscale': self.radioButton_task_upscale,
            'sharpen': self.radioButton_task_sharpen,
            'edition': self.radioButton_task_edition,
        }
        for step_str, w in self.radioButtons_steps.items():
            w.clicked.connect(partial(self.event_step_changed, step_str))

        self.tableWidget_shots.clearContents()
        self.tableWidget_shots.setRowCount(0)

        self.columns = [
            ['shot',    50, Qt.AlignRight | Qt.AlignVCenter],
            ['src',     60, Qt.AlignCenter | Qt.AlignVCenter],
            ['start',   65, Qt.AlignRight | Qt.AlignVCenter],
            ['count',   60, Qt.AlignCenter | Qt.AlignVCenter],
            ['curves',  60, Qt.AlignLeft | Qt.AlignVCenter],
            ['new c.',  60, Qt.AlignLeft | Qt.AlignVCenter],
            # ['stab.',   30, Qt.AlignCenter | Qt.AlignVCenter],
            # ['geo.',    30, Qt.AlignCenter | Qt.AlignVCenter],
            # ['other',   60, Qt.AlignLeft | Qt.AlignVCenter],
        ]
        self.tableWidget_shots.setColumnCount(len(self.columns))
        for column_no, column in zip(range(len(self.columns)), self.columns):
            self.tableWidget_shots.horizontalHeaderItem(column_no).setText(column[0])
            self.tableWidget_shots.horizontalHeaderItem(column_no).setTextAlignment(column[2])
            self.tableWidget_shots.setColumnWidth(column_no, column[1])

        self.tableWidget_shots.horizontalHeader().setStretchLastSection(True)

        # Connect signals and filter events
        self.tableWidget_shots.selectionModel().selectionChanged.connect(self.event_selection_changed)
        self.tableWidget_shots.installEventFilter(self)

        self.controller.signal_shotlist_modified[dict].connect(self.event_refresh_shotlist)
        self.controller.signal_is_modified[dict].connect(self.refresh_modification_status)
        self.controller.signal_current_shot_modified[dict].connect(self.event_current_shot_modified)

        self.set_enabled(False)
        set_stylesheet(self)
        set_widget_stylesheet(self.pushButton_replace)
        set_widget_stylesheet(self.pushButton_stabilize)
        set_widget_stylesheet(self.pushButton_rgb_curves)
        set_widget_stylesheet(self.pushButton_geometry)

        # Install events for this widget
        self.installEventFilter(self)

        # self.set_selected(False)
        self.adjustSize()



    def set_activate_state(self, state:bool):
        self.__is_activated = state

    def is_activated(self):
        return self.__is_activated

    def leave_widget(self):
        update_selected_widget_stylesheet(self.frame, is_selected=False)
        # self.repaint()


    def closeEvent(self, event):
        self.signal_close.emit()


    def get_preferences(self):
        k_ep = ''
        if (self.comboBox_episode.currentText() != ' '
        and self.comboBox_episode.currentText() != ''):
            k_ep = int(self.comboBox_episode.currentText())

        # First selected row no
        selected_indexes = self.tableWidget_shots.selectedIndexes()
        try:
            row_no = list(set([i.row() for i in selected_indexes]))[0]
        except:
            row_no = 0

        preferences = {
            'geometry': self.geometry().getRect(),
            'episode': k_ep,
            'shot_no': int(self.tableWidget_shots.item(row_no, 0).text()),
            'part': self.comboBox_part.currentText(),
            'step': self.get_current_step(),
        }
        return preferences


    def set_initial_options(self, preferences:dict):
        s = preferences['selection']
        log.info(f"set_initial_options: {s['episode']}, {s['part']}, {s['step']}")
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
        for w in self.radioButtons_steps.values():
            w.blockSignals(True)
        self.radioButtons_steps[s['step']].setChecked(True)
        for w in self.radioButtons_steps.values():
            w.blockSignals(False)

        # Shots
        self.tableWidget_shots.blockSignals(True)
        self.tableWidget_shots.clearContents()
        self.tableWidget_shots.setRowCount(0)
        self.tableWidget_shots.blockSignals(False)

        # Current shot no
        try:
            self.initial_shot_no = s['shot_no']
        except:
            self.initial_shot_no = None

        # Geometry
        self.move(s['geometry'][0], s['geometry'][1])
        self.adjustSize()

        # self.event_episode_changed()


    # def set_selected(self, is_selected):
    #     update_selected_widget_stylesheet(self.frame, is_selected=is_selected)


    def event_current_shot_modified(self, modifications:dict):
        self.tableWidget_shots.blockSignals(True)
        row_no = self.tableWidget_shots.currentRow()

        # Curves
        k_initial_curves = modifications['curves']['initial']
        k_new_curves = modifications['curves']['new']

        for column, column_no in zip(self.columns, range(len(self.columns))):
            if column[0] == 'curves':
                # Initial curves
                try:
                    self.tableWidget_shots.setItem(row_no, column_no, QTableWidgetItem(k_initial_curves.replace('~', '')))
                    f = self.tableWidget_shots.item(row_no, column_no).font()
                    if (k_initial_curves.startswith('~')
                    or k_new_curves is not None):
                        f.setStrikeOut(True)
                    else:
                        f.setStrikeOut(False)
                    self.tableWidget_shots.item(row_no, column_no).setFont(f)
                except:
                    self.tableWidget_shots.setItem(row_no, column_no, QTableWidgetItem(''))
                self.tableWidget_shots.item(row_no, column_no).setTextAlignment(self.columns[column_no][2])
                self.tableWidget_shots.item(row_no, column_no).setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)

            elif column[0] == 'new c.':
                # New curves
                try:
                    self.tableWidget_shots.setItem(row_no, column_no, QTableWidgetItem(k_new_curves))
                except:
                    self.tableWidget_shots.setItem(row_no, column_no, QTableWidgetItem(''))
                self.tableWidget_shots.item(row_no, column_no).setTextAlignment(self.columns[column_no][2])
                self.tableWidget_shots.item(row_no, column_no).setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)

            elif column[0] == 'stab.':
                try:
                    self.tableWidget_shots.cellWidget(row_no, column_no).setChecked(modifications['stabilization'])
                except:
                    continue
                    # self.tableWidget_shots.cellWidget(row_no, column_no).setChecked(False)

            elif column[0] == 'geo.':
                try:
                    self.tableWidget_shots.cellWidget(row_no, column_no).setChecked(modifications['geometry'])
                except:
                    continue
                    # self.tableWidget_shots.cellWidget(row_no, column_no).setChecked(False)

            elif column[0] == 'other':
                try:
                    self.tableWidget_shots.setItem(row_no, 0, QTableWidgetItem(modifications['comment']))
                except:
                    continue
                    # self.tableWidget_shots.setItem(row_no, 0, QTableWidgetItem(""))

            else:
                continue



        self.tableWidget_shots.blockSignals(False)


    def edition_started(self, is_started):
        row_no = self.tableWidget_shots.currentRow()
        print(f"edition_started: {row_no} is_started: {is_started}")
        item = self.tableWidget_shots.item(row_no, 0)
        if is_started:
            self.tableWidget_shots.item(row_no, 0).setForeground(QBrush(COLOR_PURPLE))
        else:
            self.tableWidget_shots.item(row_no, 0).setForeground(QBrush(COLOR_TEXT))


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
        w = self.radioButtons_steps['deinterlace']
        w.blockSignals(True)
        w.setChecked(True)
        w.blockSignals(False)
        for step_str, w in self.radioButtons_steps.items():
            if step_str == values['k_step']:
                w.blockSignals(True)
                w.setChecked(True)
                w.blockSignals(False)

        # Shots
        shots = values['shots']
        self.tableWidget_shots.clearContents()
        self.tableWidget_shots.setRowCount(0)
        row_no = 0
        for k_shot, shot in shots.items():
            self.tableWidget_shots.insertRow(row_no)

            # Curves
            k_initial_curves = shot['modifications']['curves']['initial']
            k_new_curves = shot['modifications']['curves']['new']

            for column_no, column in zip(range(len(self.columns)), self.columns):

                if column[0] == 'shot':
                    self.tableWidget_shots.setItem(row_no, column_no, QTableWidgetItem(str(k_shot)))
                elif column[0] == 'src':
                    try:
                        src_txt = f"{shot['src']['k_ed']}:{shot['src']['k_ep']}"
                    except:
                        print_red("ERROR: event_refresh_shotlist: k_ed/k_ep shall be defined in shot src. correct this ASAP")
                    self.tableWidget_shots.setItem(row_no, column_no, QTableWidgetItem(src_txt))
                    self.tableWidget_shots.item(row_no, column_no).setTextAlignment(column[2])
                    self.tableWidget_shots.item(row_no, column_no).setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)
                elif column[0] == 'start':
                    self.tableWidget_shots.setItem(row_no, column_no, QTableWidgetItem(f"{shot['src']['start']}"))
                    self.tableWidget_shots.item(row_no, column_no).setTextAlignment(column[2])
                    self.tableWidget_shots.item(row_no, column_no).setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)

                elif column[0] == 'count':
                    self.tableWidget_shots.setItem(row_no, column_no, QTableWidgetItem(f"{shot['src']['count']}"))
                    self.tableWidget_shots.item(row_no, column_no).setTextAlignment(column[2])
                    self.tableWidget_shots.item(row_no, column_no).setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)

                elif column[0] == 'curves':
                    # Initial curves
                    try:
                        self.tableWidget_shots.setItem(row_no, column_no, QTableWidgetItem(k_initial_curves.replace('~', '')))
                        f = self.tableWidget_shots.item(row_no, column_no).font()
                        if (k_initial_curves.startswith('~')
                        or k_new_curves is not None):
                            f.setStrikeOut(True)
                        else:
                            f.setStrikeOut(False)
                        self.tableWidget_shots.item(row_no, column_no).setFont(f)
                    except:
                        self.tableWidget_shots.setItem(row_no, column_no, QTableWidgetItem(''))

                    self.tableWidget_shots.item(row_no, column_no).setTextAlignment(column[2])
                    self.tableWidget_shots.item(row_no, column_no).setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)
                elif column[0] == 'new c.':
                    # New curves
                    try: self.tableWidget_shots.setItem(row_no, column_no, QTableWidgetItem(k_new_curves))
                    except: self.tableWidget_shots.setItem(row_no, column_no, QTableWidgetItem(''))

                    self.tableWidget_shots.item(row_no, column_no).setTextAlignment(column[2])
                    self.tableWidget_shots.item(row_no, column_no).setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)

                elif column[0] == 'stab.':
                    widget = QWidget()
                    __layout = QHBoxLayout(widget)
                    w = QCheckBox(widget)
                    w.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                    set_widget_stylesheet(w, 'small')
                    __layout.addWidget(w)
                    self.tableWidget_shots.setCellWidget(row_no, column_no, widget)
                    self.tableWidget_shots.cellWidget(row_no, column_no).setFocusPolicy(Qt.FocusPolicy.NoFocus)
                elif column[0] == 'geo.':
                    widget = QWidget()
                    __layout = QHBoxLayout(widget)
                    w = QCheckBox(widget)
                    w.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                    set_widget_stylesheet(w, 'small')
                    __layout.addWidget(w)
                    self.tableWidget_shots.setCellWidget(row_no, column_no, widget)
                    self.tableWidget_shots.cellWidget(row_no, column_no).setFocusPolicy(Qt.FocusPolicy.NoFocus)

                elif column[0] == 'other':
                    widget = QWidget()
                    __layout = QHBoxLayout(widget)
                    w = QCheckBox(widget)
                    w.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                    set_widget_stylesheet(w, 'small')
                    __layout.addWidget(w)
                    self.tableWidget_shots.setCellWidget(row_no, column_no, widget)
                    self.tableWidget_shots.cellWidget(row_no, column_no).setFocusPolicy(Qt.FocusPolicy.NoFocus)


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
            if self.initial_shot_no is not None:
                log.info(f"select shot no. {self.initial_shot_no}")
                self.tableWidget_shots.selectRow(self.initial_shot_no)
                self.initial_shot_no = None
            else:
                log.info("select shot no. 0")
                self.tableWidget_shots.selectRow(0)



    def event_episode_changed(self, index=0):
        log.info(f"select {self.comboBox_episode.currentText()}:{self.comboBox_part.currentText()}, {self.get_current_step()}")
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
            'k_part': '',
            'k_step': self.get_current_step()
        }

        # if values['k_part'] != '':
        self.signal_selection_changed.emit(values)
        return True



    def event_part_changed(self, index=-1):
        log.info("select ep: %s, part: %s" % (self.comboBox_episode.currentText(), self.comboBox_part.currentText()))

        k_ep = ''
        selected_ep_str = self.comboBox_episode.currentText()
        if selected_ep_str not in ['', ' ']:
            k_ep = 'ep%02d' % (int(self.comboBox_episode.currentText()))

        values = {
            'k_ep': k_ep,
            'k_part': self.comboBox_part.currentText(),
            'k_step': self.get_current_step()
        }
        self.signal_selection_changed.emit(values)
        return True

    def get_current_step(self):
        for step_str, w in self.radioButtons_steps.items():
            if w.isChecked():
                return step_str
        return 'deinterlace'

    def event_step_changed(self, step_str):
        log.info("step changed")
        # First selected row no
        selected_indexes = self.tableWidget_shots.selectedIndexes()
        try:
            row_no = list(set([i.row() for i in selected_indexes]))[0]
        except:
            row_no = 0
        self.initial_shot_no = int(self.tableWidget_shots.item(row_no, 0).text())
        self.signal_selected_step_changed.emit(self.get_current_step())



    def event_selection_changed(self, selected):
        print_lightcyan("event_selection_changed")
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

        log.info("event_selection_changed: %s" % (', '.join(map(lambda x: "%s" % (x), selected_row_no))))

        selected_shot_nos = list()
        for row_no in selected_row_no:
            shot_no_str = self.tableWidget_shots.item(row_no, 0).text()
            selected_shot_nos.append(int(shot_no_str))

        k_ep = ''
        if self.comboBox_episode.currentText() not in ['', ' ']:
            k_ep = 'ep%02d' % (int(self.comboBox_episode.currentText()))
        selected_shots = {
            'k_ep': k_ep,
            'k_part': self.comboBox_part.currentText(),
            'k_step': self.get_current_step(),
            'shotlist': selected_shot_nos
        }
        print("send signal")
        pprint(selected_shots)
        log.info(f"send signal: signal_selected_shots_changed")
        self.signal_selected_shots_changed.emit(selected_shots)


    def set_enabled(self, enabled):
        if self.is_modified and enabled:
            # do not allow selection until all modifications are saved or discarded
            return

        self.comboBox_episode.setEnabled(enabled)
        self.comboBox_part.setEnabled(enabled)
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
        # if platform.system() != "Windows":
        if not self.is_activated():
            self.set_activate_state(True)
            self.signal_widget_selected.emit(self.objectName())

    def mouseMoveEvent(self, event):
        if self.previous_position is not None:
            cursor_position = QCursor().pos()
            delta = QPoint(cursor_position - self.previous_position)
            self.previous_position = cursor_position
            self.move(self.pos() + delta)
            event.accept()


    def event_key_pressed(self, event:QKeyEvent) -> bool:
        key = event.key()
        modifiers = event.modifiers()
        if modifiers & Qt.ControlModifier:
            if key == Qt.Key.Key_A:
                self.tableWidget_shots.selectAll()
                return True

        return False


    def event_wheel(self, event: QWheelEvent) -> bool:
        print_lightgreen("\tDefault selection fct")
        return False



    def event_key_released(self, event:QKeyEvent) -> bool:
        return False



    # def changeEvent(self, event: QEvent) -> None:
    #     if event.type() == QEvent.ActivationChange:
    #         if self.isActiveWindow():

    #             event.accept()
    #             return True
    #     return False
        # super().changeEvent(event)
    def activate_widget(self):
        update_selected_widget_stylesheet(self.frame, is_selected=True)
        self.setFocus()




    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        # return super().eventFilter(watched, event)
        # # Filter press/release events
        if event.type() == QEvent.Type.KeyPress:
            if self.event_key_pressed(event):
                event.accept()
                return True
            else:
                return self.__parent.event_key_pressed(event)


        if event.type() == QEvent.Type.KeyRelease:
            if self.event_key_released(event):
                event.accept()
                return True
            else:
                return self.__parent.event_key_released(event)

        if event.type() == QEvent.Type.Wheel:
            if event.angleDelta().y() > 0:
                self.select_previous_shot()
            else:
                self.select_next_shot()
            event.accept()
            return True

        # elif event.type() == QEvent.Type.FocusIn:
        #     self.signal_widget_selected.emit(self.objectName())
        #     event.accept()
        #     return True
        # elif event.type() == QEvent.HoverEnter:
        #     update_selected_widget_stylesheet(self.frame, is_selected=True)
        #     print_purple(f"selection: HoverEnter")
        # elif event.type() == QEvent.HoverLeave:
        #     update_selected_widget_stylesheet(self.frame, is_selected=False)
        #     print_purple(f"selection: HoverLeave")

        # elif event.type() == QEvent.ActivationChange:
        #     event.accept()
        #     self.signal_widget_selected.emit(self.objectName())
        #     return True

        # elif event.type() == QEvent.Leave:
        #     update_selected_widget_stylesheet(self.frame, is_selected=False)
        #     print_purple(f"selection: Leave")

        return super().eventFilter(watched, event)
        # return True
