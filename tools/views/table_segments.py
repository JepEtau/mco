# -*- coding: utf-8 -*-
from copy import deepcopy
import sys
from enum import IntEnum
from functools import partial
from pprint import pprint
from logger import log

from PySide6.QtCore import (
    Qt,
    QPoint,
    Signal,
    QSize,
)
from PySide6.QtGui import (
    QCursor
)
from PySide6.QtWidgets import (
    QAbstractScrollArea,
    QAbstractItemView,
    QFrame,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QApplication,
    QMenu,
    QComboBox,
    QRadioButton,
    QWidget,
    QCheckBox,
    QHBoxLayout,
    QLayout,
    QVBoxLayout,
    QLineEdit,
)
from parsers.parser_stabilize import DEFAULT_SEGMENT_VALUES
from utils.pretty_print import *

from utils.stylesheet import (
    set_stylesheet,
    set_widget_stylesheet
)

class Table_segments(QTableWidget):
    signal_segment_modified = Signal(int)

    def __init__(self, parent):
        super(Table_segments, self).__init__(parent)

        # Table of segments
        self.columns = [
            {
                'id': 'start',
                'title': 'Start',
                'alignment': Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                'width': 60,
            },
            {
                'id': 'end',
                'title': 'End',
                'alignment': Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                'width': 60,
            },
            {
                'id': 'from',
                'title': 'From',
                'alignment': Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter,
                'width': 75,
            },
            {
                'id': 'ref',
                'title': 'no.',
                'alignment': Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                'width': 60,
            },
            {
                'id': 'static',
                'title': 'Static',
                'alignment': Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                'width': 50,
            },
            {
                'id': 'mode',
                'title': 'Mode',
                'alignment': Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                'width': 150,
            },
            {
                'id': 'tracker',
                'title': 'Tracker',
                'alignment': Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                'width': 150,
            },
        ]

        self.button_labels = {
            'horizontal': 'H',
            'vertical': 'V',
            'rotation': 'R',

            'enable': 'en',
            'inside': 'in',

            # 'static': 's'
        }

        # Define a dict of columns to ease access
        for col_no, column in zip(range(len(self.columns)), self.columns):
            column['no'] = col_no
        self._column_dict = {column['id']:column for column in self.columns}


        self.setColumnCount(len(self.columns))
        for column_no in range(len(self.columns)):
            self.setHorizontalHeaderItem(column_no, QTableWidgetItem())
        self.setVerticalHeaderItem(0, QTableWidgetItem())

        size_policy = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(size_policy)

        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Sunken)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setSizeAdjustPolicy(QAbstractScrollArea.AdjustIgnored)
        self.setEditTriggers(QAbstractItemView.SelectedClicked)
        self.setProperty("showDropIndicator", False)
        self.setDragDropOverwriteMode(False)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setWordWrap(False)
        self.setCornerButtonEnabled(False)

        self.horizontalHeader().setCascadingSectionResizes(False)
        self.horizontalHeader().setDefaultSectionSize(90)
        self.horizontalHeader().setHighlightSections(True)
        self.horizontalHeader().setSortIndicatorShown(True)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setDefaultSectionSize(25)
        self.verticalHeader().setSortIndicatorShown(False)
        self.verticalHeader().setStretchLastSection(False)
        self.setSortingEnabled(True)
        self.setFocusPolicy(Qt.NoFocus)
        self.clearContents()
        self.setRowCount(1)

        for col_no, column in zip(range(len(self.columns)), self.columns):
            self.horizontalHeaderItem(col_no).setText(column['title'])
            self.setColumnWidth(col_no, column['width'])
        self.adjustSize()

        # Signals
        self.verticalHeader().customContextMenuRequested[QPoint].connect(self.event_segments_right_click)
        self.verticalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested[QPoint].connect(self.event_segments_right_click)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.clearContents()

        self.row_height = 35
        self.initial_str = ""
        set_stylesheet(self)

        # width = 0
        # for v in self.columns.values():
        #     width += v['width']

        width = sum([v['width'] for v in self.columns])
        print_red(width)
        self.setMinimumSize(QSize(width+30, 310))





    def set_segment_values(self, row_no, segment):
        # log.info(f"set single segment at row no. {row_no}")
        # print_lightcyan(f"set single segment at row no. {row_no}")
        # pprint(segment)

        for col_no, column in zip(range(len(self.columns)), self.columns):
            if column['id'] == 'start':
                self.setItem(row_no, col_no, QTableWidgetItem(f"{segment['start']}"))
                self.item(row_no, col_no).setTextAlignment(column['alignment'])
                self.item(row_no, col_no).setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)

            elif column['id'] == 'end':
                self.setItem(row_no, col_no, QTableWidgetItem(f"{segment['end']}"))
                self.item(row_no, col_no).setTextAlignment(column['alignment'])
                self.item(row_no, col_no).setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)

            elif column['id'] == 'from':
                # Frame used as the initial frame to start stabilization
                combobox_reference = QComboBox()
                combobox_reference.clear()
                combobox_reference.addItems(['start', 'middle', 'end', 'frame'])
                index = combobox_reference.findText(segment['from'])
                combobox_reference.setCurrentIndex(index)
                combobox_reference.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                set_widget_stylesheet(combobox_reference)
                combobox_reference.currentIndexChanged[int].connect(self.event_reference_changed)
                self.setCellWidget(row_no, col_no, combobox_reference)

            elif column['id'] == 'ref':
                if segment['ref'] != -1:
                    self.setItem(row_no, col_no, QTableWidgetItem(f"{segment['ref']}"))
                else:
                    self.setItem(row_no, col_no, QTableWidgetItem())
                self.item(row_no, col_no).setTextAlignment(column['alignment'])


            elif column['id'] == 'static':
                # Use the same frame to detect keypoints
                w_name = 'static'
                w = QCheckBox()
                w.setObjectName(w_name)
                w.setChecked(segment[w_name])
                w.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                w.setMaximumWidth(25)
                set_widget_stylesheet(w)
                w.toggled[bool].connect(self.event_static_changed)
                self.setCellWidget(row_no, col_no, w)

            elif column['id'] == 'mode':
                # Stabilization mode
                widget = QWidget()
                __layout = QHBoxLayout(widget)
                for w_name in ['vertical', 'horizontal', 'rotation']:
                    w = QCheckBox(widget)
                    w.setText(self.button_labels[w_name])
                    w.setObjectName(w_name)
                    w.setChecked(segment['mode'][w_name])
                    w.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                    set_widget_stylesheet(w)
                    w.toggled[bool].connect(self.event_mode_changed)
                    __layout.addWidget(w)
                self.setCellWidget(row_no, col_no, widget)

            elif column['id'] == 'tracker':
                # Tracking regions
                widget = QWidget()
                __layout = QHBoxLayout(widget)
                for w_name in ['enable', 'inside']:
                    w = QCheckBox(widget)
                    w.setText(self.button_labels[w_name])
                    w.setObjectName(w_name)
                    w.setChecked(segment['tracker'][w_name])
                    w.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                    w.toggled[bool].connect(self.event_tracker_changed)
                    set_widget_stylesheet(w)
                    __layout.addWidget(w)

                w_name = 'count'
                w = QLineEdit()
                w.setObjectName(w_name)
                w.setText(f"{len(segment['tracker']['regions'])}")
                w.setSizePolicy(QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed))
                w.setFixedWidth(20)
                # w.setMaximumSize(QSize(20, 16777215))
                w.setAlignment(Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignVCenter)
                w.setReadOnly(True)
                w.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                set_widget_stylesheet(w)
                __layout.addWidget(w)

                widget.setProperty('regions', segment['tracker']['regions'])

                self.setCellWidget(row_no, col_no, widget)


        ref_col_no = self._column_dict['ref']['no']
        self.blockSignals(True)
        if self.cellWidget(row_no, self._column_dict['from']['no']).currentText() == 'frame':
            self.item(row_no, ref_col_no).setFlags((Qt.ItemIsSelectable|Qt.ItemIsEnabled))
            self.item(row_no, ref_col_no).setSelected(True)
        else:
            self.item(row_no, ref_col_no).setFlags(~(Qt.ItemIsSelectable|Qt.ItemIsEnabled))
            self.item(row_no, ref_col_no).setSelected(False)
        self.blockSignals(False)



    def get_segment_values(self, row_no):
        if row_no == -1:
            return
        log.info("get_segment_values")
        segment_values = {
            'from': self.cellWidget(row_no, self._column_dict['from']['no']).currentText(),
            'alg': 'cv2_deshaker',
            'mode': dict(),
            'tracker': {
                'regions': self.cellWidget(row_no, self._column_dict['tracker']['no']).property('regions')
            }
        }

        for k in ['start', 'end', 'ref']:
            column_no = self._column_dict[k]['no']
            segment_values[k] = self.item(row_no, column_no).text(),

        column_no = self._column_dict['mode']['no']
        for m in ['horizontal', 'vertical', 'rotation']:
            segment_values['mode'][m] = self.cellWidget(row_no, column_no).findChild(QCheckBox, m).isChecked()

        column_no = self._column_dict['tracker']['no']
        for m in ['enable', 'inside']:
            segment_values['mode'][m] = self.cellWidget(row_no, column_no).findChild(QCheckBox, m).isChecked()

        m = 'static'
        column_no = self._column_dict[m]['no']
        segment_values[m] = self.cellWidget(row_no, column_no).findChild(QCheckBox, m).isChecked()


        return segment_values




    def set_frame_no(self, point, frame_no):
        try:
            column_no = self._column_dict[point]['no']
        except:
            return
        row_no = self.currentRow()

        previous_item = self.item(row_no, column_no)
        previous_value = previous_item.text()
        new_value = f"{frame_no}"
        if new_value != previous_value:
            log.info(f"detected modification: {frame_no} -> {point}")
            self.item(row_no, column_no).setText(f"{frame_no}")
            if previous_item.column() == 0:
                previous_item.setData(Qt.UserRole, previous_item.text())

            if point == 'ref':
                _col_no = self._column_dict['from']['no']
                w = self.cellWidget(row_no, _col_no)
                index = w.findText('frame')
                w.blockSignals(True)
                w.setCurrentIndex(index)
                w.blockSignals(False)
                self.item(row_no, column_no).setFlags((Qt.ItemIsSelectable|Qt.ItemIsEnabled))

            self.signal_segment_modified.emit(row_no)


    def get_frame_no(self, item:QTableWidgetItem):
        frame_no = -1
        row_no = item.row()
        col_no = item.column()
        # log.info(f"selected frame at row={row_no}, col={col_no}")
        if self.columns[col_no]['id'] in ['start', 'end', 'ref']:
            try:
                frame_no = int(self.item(row_no, col_no).text())
            except:
                pass
        return frame_no



    def get_current_segment_values(self):
        return self.get_segment_values(self.currentRow())

    def get_ref_frame_no(self, row_no):
        column_no = self._column_dict['from']['no']
        try:
            if self._column_dict['from']['no'] == 'frame':
                return int(self.cellWidget(row_no, column_no).currentText())
        except:
            pass
        return -1




    def select_segment(self):
        row_no = self.currentRow()
        selected_rows = list(set([index.row() for index in self.selectedIndexes()]))
        segment_values = None
        if len(selected_rows) == 0:
            log.info(f"Do not save new selection")
            self.selectionModel().blockSignals(True)
            self.blockSignals(True)
            self.selectRow(row_no)

            self.blockSignals(False)
            self.selectionModel().blockSignals(False)
        else:
            log.info(f"new segment selected: {row_no}")
            segment_values = self.get_segment_values(row_no=row_no)
        return segment_values

    def event_current_cell_changed(self, row_no, column_no, previous_row_no, previous_column_no):
        log.info(f"new cell selected: {row_no}, {column_no}")
        segment_values = self.get_segment_values(row_no=row_no)


    def clear_contents(self):
        self.clearContents()
        self.setRowCount(0)


    def is_content_modified(self):
        # Convert segments to str
        new_str = self.convert_to_str(selected_rows=list(range(self.rowCount())))
        if new_str != self.initial_str:
            return True

        # Add Table of ROI
        return False


    def set_content(self, segments):
        # log.info(f"set content")
        # print_lightcyan(f"set content")
        # pprint(segments)
        self.clearContents()
        self.sortByColumn(-1, Qt.AscendingOrder)
        self.setRowCount(0)

        for row_no, segment in zip(range(len(segments)), segments):
            self.insertRow(row_no)
            self.setRowHeight(row_no, self.row_height)
            self.set_segment_values(row_no=row_no, segment=segment)

        # Set internal values for ROI
        self.__trackers = list([s['tracker'] for s in segments])

        # Select first segment
        self.selectionModel().blockSignals(True)
        self.blockSignals(True)
        self.selectRow(0)

        self.blockSignals(False)
        self.selectionModel().blockSignals(False)

        # Set the initial str to indicates if content is modified
        # self.initial_str = self.convert_to_str(selected_rows=list(range(len(segments))))



    def select_next_reference(self):
        row_no = self.currentRow()
        col_no = self._column_dict['from']['no']
        combobox = self.cellWidget(row_no, col_no)
        current_index = combobox.currentIndex()
        new_index = current_index+1 if current_index < combobox.count()-1 else 0
        self.cellWidget(row_no, col_no).setCurrentIndex(new_index)

        ref_col_no = self._column_dict['ref']['no']
        self.blockSignals(True)
        if self.cellWidget(row_no, col_no).currentText() == 'frame':
            self.item(row_no, ref_col_no).setFlags((Qt.ItemIsSelectable|Qt.ItemIsEnabled))
        else:
            self.item(row_no, ref_col_no).setFlags(~(Qt.ItemIsSelectable|Qt.ItemIsEnabled))
            self.item(row_no, ref_col_no).setSelected(False)
        self.blockSignals(False)
        self.signal_segment_modified.emit(row_no)


    def select_mode_option(self, option):
        row_no = self.currentRow()
        col_no = self._column_dict['mode']['no']
        segment_values = self.get_segment_values(row_no=row_no)
        self.cellWidget(row_no, col_no).findChild(QCheckBox, option).toggle()
        self.signal_segment_modified.emit(self.currentRow())


    def get_content(self):
        segments = list()
        for row_no in range(self.rowCount()):
            segments.append(self.get_segment_values(row_no=row_no))

        # Modify settings as start and end are str
        for segment in segments:
            segment['start'] = int(segment['start'])
            segment['end'] = int(segment['end'])
            try:
                segment['ref'] = int(segment['ref'])
            except:
                segment['ref'] = -1
        return segments


    def append_empty_segments(self, count):
        row_count = self.rowCount()
        for row_no in range(row_count, row_count + count):
            self.insertRow(row_no)
            self.setRowHeight(row_no, self.row_height)


    def remove_all_segments(self):
        if self.rowCount()>0:
            log.info("remove all")
            segments = list()
            row_nos = list(range(self.rowCount()))
            for row_no in sorted(row_nos, reverse=True):
                segments.append(self.get_segment_values(row_no=row_no))
                self.removeRow(row_no)

        self.clearContents()
        self.setRowCount(0)
        self.signal_segment_modified.emit(-1)


    def remove_segment(self):
        row_nos = list(set([index.row() for index in self.selectedIndexes()]))
        if len(row_nos) == self.rowCount():
            self.remove_all_segments()
        else:
            segments = list()
            for row_no in sorted(row_nos, reverse=True):
                segments.append(self.get_segment_values(row_no=row_no))
                self.removeRow(row_no)
        self.signal_segment_modified.emit(-1)


    def insert_segment(self, row_no=None):
        self.sortByColumn(-1, Qt.AscendingOrder)
        row_no = self.rowCount()
        if row_no is None and self.currentItem() is not None:
            row_no = self.currentItem().row()
        elif self.currentItem() is not None:
                row_no = self.currentItem().row() + 1
        else:
            log.info("cannot insert a new segment")

        self.insertRow(row_no)
        self.setRowHeight(row_no, self.row_height)

        __segment = deepcopy(DEFAULT_SEGMENT_VALUES)
        self.set_segment_values(row_no=row_no, segment=__segment)
        self.selectRow(row_no)



    def append_segment(self):
        self.sortByColumn(-1, Qt.AscendingOrder)
        # Append, i.e. set row_no to None, not clean but not time to refactor
        self.insert_segment(row_no=None)



    def insert_segment_at(self):
        cursor_position = self.mapFromGlobal(QCursor.pos())
        item_position_x = cursor_position.x() + 5
        item_position_y = cursor_position.y() - self.horizontalHeader().size().height() * 2 + 5
        item = self.itemAt(item_position_x, item_position_y)
        if item is not None:
            self.clearSelection()
            self.setCurrentItem(item)
            self.insert_segment(item.row())
            self.clearSelection()
            self.setCurrentItem(self.item(-1, -1))
        else:
            self.setCurrentItem(None)
            self.insert_segment(None)



    def event_segments_right_click(self, qpoint):
        cursor_position = QCursor.pos()
        self.popMenu = QMenu(self)
        insert_action = self.popMenu.addAction('Insert')
        insert_action.triggered.connect(self.insert_segment_at)
        if len(self.selectedIndexes()) > 0:
            remove_action = self.popMenu.addAction('Remove')
            remove_action.triggered.connect(self.remove_segment)
        self.popMenu.exec_(cursor_position)


    def convert_to_str(self, selected_rows:list) -> str:
        data_str = ""
        for row_no in selected_rows:
            segment_values = self.get_segment_values(row_no=row_no)
            data_str += str(segment_values) + '\n'
        data_str = data_str[:-1]
        return data_str


    def event_static_changed(self, state:bool) -> None:
        self.signal_segment_modified.emit(self.currentRow())

    def event_reference_changed(self, index:int) -> None:
        self.signal_segment_modified.emit(self.currentRow())

    def event_mode_changed(self, state:bool) -> None:
        self.signal_segment_modified.emit(self.currentRow())

    def event_tracker_changed(self, state:bool) -> None:
        self.signal_segment_modified.emit(self.currentRow())

    def update_regions(self, regions:list) -> None:
        # pprint(regions)
        row_no = self.currentRow()
        col_no = self._column_dict['tracker']['no']
        widget = self.cellWidget(row_no, col_no)
        widget.setProperty('regions', regions)
        widget.findChild(QLineEdit, 'count').setText(f"{len(regions)}")



    def convert_roi_to_str(self, selected_rows:list) -> str:
        data_str = ""
        for row_no in selected_rows:
            roi_values = self.get_roi_values(row_no=row_no)
            data_str += str(roi_values) + '\n'
        data_str = data_str[:-1]
        return data_str

    def append_empty_roi(self, count):
        pass

    def get_roi_content(self):
        # segments = list()
        # for row_no in range(self.rowCount()):
        #     segments.append(self.get_segment_values(row_no=row_no))

        # # Modify settings as start and end are str
        # for segment in segments:
        #     segment['start'] = int(segment['start'])
        #     segment['end'] = int(segment['end'])

        # return segments

    # def get_roi_values(self, row_no:int):
    #     # row_no is the segment no
    #     self.__segment_roi[row_no]
        return ""




    def get_roi_values(self, segment_no:int):
        return list()