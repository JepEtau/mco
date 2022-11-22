# -*- coding: utf-8 -*-

import sys
sys.path.append('../scripts')
from functools import partial
from copy import deepcopy

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
)
from PySide6.QtWidgets import (
    QApplication,
    QTableWidgetItem,
    QListWidgetItem,
    QWidget,
)


from common.sylesheet import (
    set_stylesheet,
    update_selected_widget_stylesheet,
)

from utils.common import K_GENERIQUES, K_PARTS, K_ALL_PARTS
from curves_editor.ui.widget_selection_ui import Ui_widget_selection


class Widget_selection(QWidget, Ui_widget_selection):
    signal_selection_changed = Signal(dict)
    signal_selected_shots_changed = Signal(dict)
    signal_preview_options_changed = Signal()
    signal_close = Signal()
    signal_image_selected = Signal(str)


    def __init__(self, ui, model):
        super(Widget_selection, self).__init__()


        self.setupUi(self)
        self.model = model
        self.ui = ui
        self.setObjectName('selection')

        # Setup and patch ui
        self.setAutoFillBackground(True)
        self.setWindowFlags(Qt.Tool)
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setWindowModality(Qt.NonModal)
        self.setAttribute(Qt.WA_DeleteOnClose)

        # Internal variables
        self.k_eps_parts = dict()
        self.comboBox_episode.clear()
        self.comboBox_part.clear()
        self.previous_position = None
        self.is_modified = False
        self.previous_selection = [0]

        # Initialize widgets
        self.comboBox_episode.setFocusPolicy(Qt.NoFocus)
        self.comboBox_part.setFocusPolicy(Qt.NoFocus)
        self.comboBox_step.setFocusPolicy(Qt.NoFocus)
        # self.tableWidget_shots.setFocusPolicy(Qt.NoFocus)


        self.comboBox_edition.currentIndexChanged['int'].connect(partial(self.event_selection_changed, 'k_ed'))
        self.comboBox_episode.currentIndexChanged['int'].connect(partial(self.event_selection_changed, 'k_ep'))
        self.comboBox_part.currentIndexChanged['int'].connect(partial(self.event_selection_changed, 'k_part'))
        self.comboBox_step.currentIndexChanged['int'].connect(partial(self.event_selection_changed, 'k_step'))

        self.list_images.setMinimumHeight(500)
        self.list_images.setAutoScroll(True)
        self.list_images.clear()

        self.tableWidget_shots.clearContents()
        self.tableWidget_shots.setRowCount(0)
        self.alignment = [Qt.AlignCenter| Qt.AlignVCenter,
                            Qt.AlignCenter | Qt.AlignVCenter,
                            Qt.AlignRight | Qt.AlignVCenter,
                            Qt.AlignRight | Qt.AlignVCenter,
                            Qt.AlignRight | Qt.AlignVCenter,
                            Qt.AlignRight | Qt.AlignVCenter]
        headers = ["ed", "ep", "shot", "start", "curves", "new curves"]
        default_col_width = [25, 25, 45, 55, 60, 60]
        for col_no, header_str, col_width in zip(range(len(headers)),
                                                    headers,
                                                    default_col_width):
            self.tableWidget_shots.horizontalHeaderItem(col_no).setText(header_str)
            # self.tableWidget_shots.horizontalHeaderItem(col_no).setTextAlignment(align)
            self.tableWidget_shots.setColumnWidth(col_no, col_width)
        self.tableWidget_shots.horizontalHeader().setStretchLastSection(True)

        # Connect signals and filter events
        self.list_images.itemSelectionChanged.connect(self.event_image_selected)


        self.checkBox_fit_image_to_window.stateChanged['int'].connect(self.event_fit_image_to_window_changed)

        # self.tableWidget_shots.selectionModel().selectionChanged.connect(self.event_ep_or_part_selection_changed)
        # self.tableWidget_shots.installEventFilter(self)

        # self.model.signal_shotlist_modified[dict].connect(self.event_refresh_shotlist)
        # self.model.signal_is_modified[dict].connect(self.refresh_modification_status)
        self.model.signal_framelist_modified[dict].connect(self.event_framelist_modified)
        self.model.signal_current_shot_modified[dict].connect(self.event_current_shot_modified)


        self.installEventFilter(self)
        self.list_images.installEventFilter(self)
        self.list_images.verticalScrollBar().installEventFilter(self)

        set_stylesheet(self)
        self.set_selected(False)
        self.adjustSize()



    def set_selected(self, is_selected):
        update_selected_widget_stylesheet(self.frame, is_selected=is_selected)


    def closeEvent(self, event):
        self.signal_close.emit()


    def get_preferences(self):
        k_ed = self.comboBox_edition.currentText().replace(' ', '')
        k_ep = self.comboBox_episode.currentText().replace(' ', '')
        k_part = self.comboBox_part.currentText().replace(' ', '')
        preferences = {
            'geometry': self.geometry().getRect(),
            'edition': k_ed,
            'episode': k_ep,
            'part': k_part,
            'step': self.comboBox_step.currentText(),
            'k_filter_ids': list(),
            'k_shots': list(),
            'widget': {
                self.checkBox_fit_image_to_window.isChecked()
            }

        }
        return preferences


    def block_signals(self, enabled):
        self.comboBox_edition.blockSignals(enabled)
        self.comboBox_episode.blockSignals(enabled)
        self.comboBox_part.blockSignals(enabled)
        self.comboBox_step.blockSignals(enabled)
        self.tableWidget_shots.setEnabled(enabled)


    def set_initial_options(self, preferences:dict):
        log.info("set_initial_options")
        s = preferences['selection']
        print("%s:set_initial_options: " % (__name__))
        pprint(s)
        pprint(self.k_eps_parts)

        self.block_signals(True)

        # Edition
        saved_ed_no = s['edition']
        if saved_ed_no == 0:
            # print("none selected")
            self.comboBox_edition.setCurrentText('')
        else:
            index = self.comboBox_edition.findText(str(saved_ed_no))
            self.comboBox_edition.setCurrentIndex(index)

        # Episode
        self.refresh_combobox_episode()
        saved_ep_no = s['episode']
        if saved_ep_no == 0:
            # print("none selected")
            self.comboBox_episode.setCurrentText('')
        else:
            index = self.comboBox_episode.findText(str(saved_ep_no))
            self.comboBox_episode.setCurrentIndex(index)

        # Part
        self.refresh_combobox_part()
        self.comboBox_part.setCurrentText(s['part'])
        if s['part'] in K_ALL_PARTS:
            index = self.comboBox_part.findText(s['part'])
            self.comboBox_part.setCurrentIndex(index)

        # Step
        index = self.comboBox_step.findText(s['step'])
        index = 0 if index == -1 else index
        self.comboBox_step.setCurrentIndex(index)

        # Shots
        self.tableWidget_shots.clearContents()
        self.tableWidget_shots.setRowCount(0)

        self.block_signals(False)

        # Geometry
        self.move(s['geometry'][0], s['geometry'][1])
        self.adjustSize()

        selection = self.get_selection('k_ep', -1)
        self.signal_selection_changed.emit(selection)



    def refresh_combobox_episode(self):
        is_signal_blocked = self.comboBox_episode.signalsBlocked()
        if not is_signal_blocked:
            self.comboBox_episode.blockSignals(True)
        k_eps = sorted(list(self.k_eps_parts.keys()))
        self.comboBox_episode.clear()
        self.comboBox_episode.addItem(' ')
        for k_ep in k_eps:
            try: self.comboBox_episode.addItem(str(int(k_ep[2:])))
            except: continue
        if not is_signal_blocked:
            self.comboBox_episode.blockSignals(False)


    def refresh_combobox_part(self, index=-1):
        is_signal_blocked = self.comboBox_part.signalsBlocked()
        if not is_signal_blocked:
            self.comboBox_part.blockSignals(True)

        k_part_current = self.comboBox_part.currentText()

        self.comboBox_part.clear()
        if index != -1:
            # index is the new selected episode
            k_ep_current = self.comboBox_episode.itemText(index).replace(' ', '')
        else:
            k_ep_current = self.comboBox_episode.currentText().replace(' ', '')

        if k_ep_current == '':
            for k_part in self.k_eps_parts[' ']:
                if k_part in K_GENERIQUES:
                    self.comboBox_part.addItem(k_part)
        elif k_ep_current != '':
            k_ep = 'ep%02d' % (int(k_ep_current))
            for k_part in self.k_eps_parts[k_ep]:
                if k_part in K_PARTS:
                    self.comboBox_part.addItem(k_p)

        # Restore the previous selected part if exists
        i = self.comboBox_part.findText(k_part_current)
        new_index = i if i != -1 else 0
        self.comboBox_part.setCurrentIndex(new_index)

        if self.comboBox_part.count() > 0:
            self.comboBox_part.setEnabled(True)
        else:
            self.comboBox_part.setEnabled(False)

        if not is_signal_blocked:
            self.comboBox_part.blockSignals(False)


    def event_folders_parsed(self, available_selection):
        # Update these combobox after having parsed the 'frames' directory
        log.info("event_folders_parsed: save ep and parts for later use")
        print("event_folders_parsed: save ep and parts for later use")
        # pprint(available_selection)
        self.block_signals(True)
        try:
            k_eds = available_selection['k_eds']
            k_ed_current = self.comboBox_edition.currentText()
            self.comboBox_edition.clear()
            self.comboBox_edition.addItem(' ')
            for k_ed in k_eds:
                self.comboBox_edition.addItem(k_ed)
        except:
            pass

        try:
            steps = available_selection['steps']
            step_current = self.comboBox_step.currentText()
            self.comboBox_step.clear()
            self.comboBox_step.addItem(' ')
            for step in steps:
                self.comboBox_step.addItem(step)
        except:
            pass

        self.k_eps_parts = deepcopy(available_selection['k_eps_parts'])
        self.block_signals(False)


    def event_framelist_modified(self, frames) -> dict:
        log.info("directory has been parsed, refresh list of images")
        print("directory has been parsed, refresh list of images")
        # print("-> %s:event_refresh:" % (__name__))
        # pprint(frames.keys())
        # print("---")

        # Save current selected image
        if self.list_images.count() > 0 and len(frames.keys()) > 0:
            saved_image_name = self.list_images.currentItem().text()
            log.info("current frame: %s" % (saved_image_name))
        else:
            log.info("no frames currently selected")
            saved_image_name = ''

        self.list_images.blockSignals(True)

        # Remove all names
        self.list_images.clear()

        # Update list of images
        row_no = -1
        frame_names = sorted(list(frames.keys()))
        for name, i in zip(frame_names, range(len(frame_names))):
            self.list_images.addItem(QListWidgetItem(name))
            if name == saved_image_name:
                row_no = i

        # Select previous image
        image_name = ''
        log.info('%d' % (self.list_images.count()))
        if self.list_images.count() > 0:
            if row_no == -1:
                row_no = 0
            log.info("set current frame, no=%d, nb of frames=%d" % (row_no, self.list_images.count()))
            self.list_images.setCurrentRow(row_no)
            self.list_images.item(row_no).setSelected(True)
            image_name = self.list_images.currentItem().text()

        self.list_images.blockSignals(False)
        self.signal_image_selected.emit(image_name)


    def event_shotlist_modified(self, shotlist):
        print("widget_selection: event_shotlist_modified")
        self.tableWidget_shots.blockSignals(True)
        self.tableWidget_shots.setRowCount(0)

        row_no = 0
        for no, shot in shotlist.items():
            self.tableWidget_shots.insertRow(row_no)
            self.tableWidget_shots.setItem(row_no, 0, QTableWidgetItem(shot['k_ed']))
            self.tableWidget_shots.setItem(row_no, 1, QTableWidgetItem(str(int(shot['k_ep'][2:]))))
            self.tableWidget_shots.setItem(row_no, 2, QTableWidgetItem('%03d' % (shot['no'])))
            self.tableWidget_shots.setItem(row_no, 3, QTableWidgetItem(str(shot['start'])))

            # # Curves
            # if shot['curves'] is not None:
            #     self.tableWidget_shots.setItem(row_no, 4, QTableWidgetItem(shot['curves']['k_curves']))
            # else:
            #     self.tableWidget_shots.setItem(row_no, 4, QTableWidgetItem(''))

            self.tableWidget_shots.setItem(row_no, 5, QTableWidgetItem(''))
            k_initial_curves = shot['modifications']['curves']['initial']
            k_new_curves = shot['modifications']['curves']['new']

            # Initial curves
            try:
                self.tableWidget_shots.setItem(row_no, 4, QTableWidgetItem(k_initial_curves.replace('~', '')))
                f = self.tableWidget_shots.item(row_no, 4).font()
                if (k_initial_curves.startswith('~')
                or k_new_curves is not None):
                    f.setStrikeOut(True)
                else:
                    f.setStrikeOut(False)
                self.tableWidget_shots.item(row_no, 4).setFont(f)
            except:
                self.tableWidget_shots.setItem(row_no, 4, QTableWidgetItem(''))

            # New curves
            try: self.tableWidget_shots.setItem(row_no, 5, QTableWidgetItem(k_new_curves))
            except: self.tableWidget_shots.setItem(row_no, 5, QTableWidgetItem(''))

            user_role = "%s.%s.%s" % (shot['k_ed'], shot['k_ep'], shot['no'])
            self.tableWidget_shots.item(row_no, 0).setData(Qt.UserRole, user_role)


            for i in range(len(self.alignment)):
                self.tableWidget_shots.item(row_no, i).setTextAlignment(self.alignment[i])
                self.tableWidget_shots.item(row_no, i).setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)
            row_no += 1

        self.tableWidget_shots.selectionModel().clearSelection()
        self.tableWidget_shots.blockSignals(False)




    def event_current_shot_modified(self, modifications:dict):
        self.tableWidget_shots.blockSignals(True)
        row_no = self.tableWidget_shots.currentRow()

        # Curves
        k_initial_curves = modifications['curves']['initial']
        k_new_curves = modifications['curves']['new']

        # Initial curves
        try:
            self.tableWidget_shots.setItem(row_no, 4, QTableWidgetItem(k_initial_curves.replace('~', '')))
            f = self.tableWidget_shots.item(row_no, 4).font()
            if (k_initial_curves.startswith('~')
            or k_new_curves is not None):
                f.setStrikeOut(True)
            else:
                f.setStrikeOut(False)
            self.tableWidget_shots.item(row_no, 4).setFont(f)
        except:
            self.tableWidget_shots.setItem(row_no, 4, QTableWidgetItem(''))

        # New curves
        try: self.tableWidget_shots.setItem(row_no, 5, QTableWidgetItem(k_new_curves))
        except: self.tableWidget_shots.setItem(row_no, 5, QTableWidgetItem(''))


        for i in [4, 5]:
            self.tableWidget_shots.item(row_no, i).setTextAlignment(self.alignment[i])
            self.tableWidget_shots.item(row_no, i).setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)


        self.tableWidget_shots.blockSignals(False)



    def get_selection(self, widget, index) -> dict:
        log.info("get new selection")
        print("get_selection")

        k_ep = self.comboBox_episode.currentText().replace(' ', '')
        k_ep = 'ep%02d' % (int(k_ep)) if k_ep != '' else ''

        if widget == 'k_ed':
            log.info("edition changed")
        elif widget == 'k_ep':
            log.info("episode changed to %s" % (k_ep))
        elif widget == 'k_part':
            log.info("part changed")
        elif widget == 'k_step':
            log.info("step changed")

        selection = {
            'k_ed': self.comboBox_edition.currentText().replace(' ', ''),
            'k_ep': k_ep,
            'k_part': self.comboBox_part.currentText().replace(' ', ''),
            'k_step': self.comboBox_step.currentText().replace(' ', ''),
            'filter_ids': list(),
            'shot_nos': list(),
        }
        pprint(selection)
        return selection



    def event_selection_changed(self, widget, index):
        log.info("selection changed, widget=%s, index = %d" % (widget, index))
        print("selection changed, widget=%s, index = %d" % (widget, index))

        self.block_signals(True)
        if widget == 'k_ep':
            k_ep_current = self.comboBox_episode.currentText().replace(' ', '')

            self.comboBox_part.clear()
            if k_ep_current == '':
                for k_part in self.k_eps_parts[' ']:
                    if k_part in K_GENERIQUES:
                        # Add only supported folders, usefull
                        self.comboBox_part.addItem(k_part)
            else:
                k_ep = 'ep%02d' % (int(k_ep_current))
                for k_part in self.k_eps_parts[k_ep]:
                    if k_part in K_PARTS:
                        # Add only supported folders, usefull
                        self.comboBox_part.addItem(k_part)

        self.block_signals(False)

        selection = self.get_selection(widget, index)
        self.signal_selection_changed.emit(selection)



    def event_image_selected(self):
        image_name = self.list_images.currentItem().text()
        current_item = self.list_images.currentItem()
        # print("event_image_selected: is selected?", current_item.isSelected())
        # log.info("select [%s]" % (image_name))
        self.signal_image_selected.emit(image_name)
        return True

    def select_next_image(self):
        if self.list_images.count() == 0:
            return True
        self.list_images.item(self.list_images.currentRow()).setSelected(False)
        no = self.list_images.currentRow() + 1
        if no >= self.list_images.count():
            no = 0
        # log.info("select row no. %d" % (no))
        self.list_images.setCurrentRow(no)
        self.list_images.item(no).setSelected(True)


    def select_previous_image(self):
        if self.list_images.count() == 0:
            return True
        self.list_images.item(self.list_images.currentRow()).setSelected(False)
        no = self.list_images.currentRow()
        if no == 0:
            no = self.list_images.count() - 1
        else:
            no = no - 1
        # log.info("select row no. %d" % (no))
        self.list_images.setCurrentRow(no)
        self.list_images.item(no).setSelected(True)



    def select_first_image(self):
        if self.list_images.count() > 0:
            self.list_images.setCurrentRow(0)
            self.list_images.item(0).setSelected(True)
        return True


    def select_last_image(self):
        if self.list_images.count() > 0:
            row_no = self.list_images.count() - 1
            self.list_images.setCurrentRow(row_no)
            self.list_images.item(row_no).setSelected(True)
        return True

    def event_page_up(self, event):
        return self.list_images.keyPressEvent(event)

    def event_page_down(self, event):
        return self.list_images.keyPressEvent(event)



    def event_refresh_shotlist(self, values:dict):
        log.info("directory has been parsed, refresh shot list")
        print("%s:event_refresh:" % (__name__))
        pprint(values)
        print("---")
        sys.exit()
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
        # shots = values['shots']
        # self.tableWidget_shots.clearContents()
        # self.tableWidget_shots.setRowCount(0)
        # row_no = 0
        # for k_shot, shot in shots.items():
        #     self.tableWidget_shots.insertRow(row_no)
        #     self.tableWidget_shots.setItem(row_no, 0, QTableWidgetItem('%05d' % (k_shot)))
        #     src_txt = ""
        #     if 'src' in shot.keys():
        #         src_txt = "%s:%s" % (shot['src']['k_ed'], shot['src']['k_ep'])
        #     self.tableWidget_shots.setItem(row_no, 1, QTableWidgetItem(src_txt))

        #     self.tableWidget_shots.setItem(row_no, 2, QTableWidgetItem(str(shot['src']['start'])))
        #     self.tableWidget_shots.setItem(row_no, 3, QTableWidgetItem(str(shot['src']['count'])))

        #     # Curves
        #     k_initial_curves = shot['modifications']['curves']['initial']
        #     k_new_curves = shot['modifications']['curves']['new']

        #     # Initial curves
        #     try:
        #         self.tableWidget_shots.setItem(row_no, 4, QTableWidgetItem(k_initial_curves.replace('~', '')))
        #         f = self.tableWidget_shots.item(row_no, 4).font()
        #         if (k_initial_curves.startswith('~')
        #         or k_new_curves is not None):
        #             f.setStrikeOut(True)
        #         else:
        #             f.setStrikeOut(False)
        #         self.tableWidget_shots.item(row_no, 4).setFont(f)
        #     except:
        #         self.tableWidget_shots.setItem(row_no, 4, QTableWidgetItem(''))

        #     # New curves
        #     try: self.tableWidget_shots.setItem(row_no, 5, QTableWidgetItem(k_new_curves))
        #     except: self.tableWidget_shots.setItem(row_no, 5, QTableWidgetItem(''))


        #     for i in range(len(self.alignment)):
        #         self.tableWidget_shots.item(row_no, i).setTextAlignment(self.alignment[i])
        #         self.tableWidget_shots.item(row_no, i).setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)

        #     if not shot['is_valid']:
        #         # If true, it means that all pictures are present in the folder
        #         # Bug: this does not work
        #         self.tableWidget_shots.item(row_no, 0).setData(Qt.FontRole, QColor(Qt.red))
        #     row_no += 1

        # self.tableWidget_shots.selectionModel().clearSelection()
        # self.tableWidget_shots.blockSignals(False)

        # self.tableWidget_shots.setEnabled(True)
        self.set_enabled(True)

        # if len(shots) > 0:
        #     log.info("select shot no. 0")
        #     self.tableWidget_shots.selectRow(0)




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
            'k_step': self.comboBox_step.currentText(),
            'shotlist': selected_shot_nos
        }
        self.signal_preview_options_changed.emit(preview_options)



    def refresh_modification_status(self, modifications:dict):
        # Something has been modified, disable selection until saving or discard
        self.is_modified = modifications['status']
        if self.is_modified:
            self.set_enabled(False)
            self.widget_app_controls.set_save_discard_enabled(True)
        else:
            self.set_enabled(True)
            self.widget_app_controls.set_save_discard_enabled(False)

        if modifications['shot_no'] is not None:
            log.info("shot no. %d has been modified" % (modifications['shot_no']))


    def event_fit_image_to_window_changed(self, state):
        self.signal_preview_options_changed.emit()


    def get_preview_options(self):
        preview_options = {
            'is_fit_image_to_screen': self.checkBox_fit_image_to_window.isChecked(),
        }
        return preview_options


    def refresh_values(self, frame:dict):
        print("%s: todo: refresh values" % (self.objectName()))
        # pprint(frame)
        log.info("todo: refresh values")

        frame_user_role = "%s.%s.%s" % (frame['k_ed'], frame['k_ep'], frame['shot_no'])

        # Refresh the list of shots: select current shot
        for row_no in range(self.tableWidget_shots.rowCount()):
            font = self.tableWidget_shots.item(row_no, 0).font()
            user_role = self.tableWidget_shots.item(row_no, 0).data(Qt.UserRole)
            if user_role == frame_user_role:
                font.setBold(True)
            else:
                font.setBold(False)
            for col_no in range(len(self.alignment)):
                self.tableWidget_shots.item(row_no, col_no).setFont(font)
            row_no += 1



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
        # if modifiers & Qt.ControlModifier and key == Qt.Key_A:
        #     self.tableWidget_shots.selectAll()
        #     event.accept()
        #     return True
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
        # print("  * eventFilter: widget_%s: " % (self.objectName()), event.type())
        # Filter press/release events
        if QApplication.focusObject() is self.list_images:
            if event.type() == QEvent.KeyPress:
                if event.key() == Qt.Key_F:
                    self.ui.setFocus()
                    self.ui.keyPressEvent(event)
                    return True

                self.list_images.keyPressEvent(event)

        if event.type() == QEvent.Wheel:
            # log.info("%s:eventFilter: wheel event" % (__name__))
            if event.angleDelta().y() > 0:
                # log.info("wheelEvent:Previous")
                self.select_previous_image()
            else:
                # log.info("wheelEvent:Next")
                self.select_next_image()
            event.accept()
            return True

        elif event.type() == QEvent.Enter:
            # print("         QEvent.Enter")
            self.is_entered = True
            return True
        elif event.type() == QEvent.Leave:
            # print("         QEvent.Leave")
            self.is_entered = False
            return True
        # return super().eventFilter(watched, event)

        return self.ui.eventFilter(watched, event)




    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.ActivationChange:
            if self.isActiveWindow():
                self.ui.set_current_editor('selection')
                event.accept()
                return True
        return False
        # super().changeEvent(event)




    def enter(self):
        self.is_entered = True


