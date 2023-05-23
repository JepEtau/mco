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
)
from utils.pretty_print import *

from utils.stylesheet import (
    set_stylesheet,
    set_widget_stylesheet
)

class Widget_segments(QTableWidget):
    signal_segment_modified = Signal(int)

    def __init__(self, parent):
        super(Widget_segments, self).__init__(parent)

        # Table of segments
        self.cell_alignment = [
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        ]
        headers = ["Start", "End", "From", "Mode", "Trackers"]
        default_col_width = [60, 60, 75, 260, 150]


        self.setColumnCount(len(self.cell_alignment))
        for column_no in range(len(self.cell_alignment)):
            self.setHorizontalHeaderItem(column_no, QTableWidgetItem())
        self.setVerticalHeaderItem(0, QTableWidgetItem())

        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(size_policy)
        self.setMinimumSize(QSize(530, 300))

        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Sunken)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setSizeAdjustPolicy(QAbstractScrollArea.AdjustIgnored)
        self.setEditTriggers(QAbstractItemView.SelectedClicked)
        self.setProperty("showDropIndicator", False)
        self.setDragDropOverwriteMode(False)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setWordWrap(False)
        self.setCornerButtonEnabled(False)
        self.setMinimumHeight(305)

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
        self.setRowCount(6)
        for col_no, header_str, col_width in zip(range(len(headers)), headers, default_col_width):
            self.horizontalHeaderItem(col_no).setText(header_str)
            self.setColumnWidth(col_no, col_width)
        self.adjustSize()
        # Signals
        self.verticalHeader().customContextMenuRequested[QPoint].connect(self.event_segments_right_click)
        self.verticalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested[QPoint].connect(self.event_segments_right_click)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.clearContents()

        self.row_height = 35
        self.initial_str = ""
        self.__roi_list = list()
        set_stylesheet(self)
        self.__parent = parent
        self.adjustSize()
        self.setMinimumWidth(560)


    def set_parent(self, parent):
        self.__parent = parent


    def set_frame_no(self, point, frame_no):
        column_no = 0 if point == 'start' else 1
        previous_item = self.item(self.currentRow(), column_no)
        previous_value = previous_item.text()
        new_value = f"{frame_no}"
        if new_value != previous_value:
            log.info(f"detected modification: {frame_no} -> {point}")
            self.item(self.currentRow(), column_no).setText(f"{frame_no}")
            if previous_item.column() == 0:
                previous_item.setData(Qt.UserRole, previous_item.text())
            self.signal_segment_modified.emit(self.currentRow())

    def get_current_segment_values(self):
        return self.get_segment_values(self.currentRow())


    def get_segment_values(self, row_no):
        segment_values = {
            'start': self.item(row_no, 0).text(),
            'end': self.item(row_no, 1).text(),
            'ref': self.cellWidget(row_no, 2).currentText(),
            'alg': 'cv2_deshaker',
            'mode': {
                'horizontal': self.cellWidget(row_no, 3).findChild(QCheckBox, 'horizontal').isChecked(),
                'vertical': self.cellWidget(row_no, 3).findChild(QCheckBox, 'vertical').isChecked(),
                'rotation': self.cellWidget(row_no, 3).findChild(QCheckBox, 'rotation').isChecked()
            },
            'roi': {
                'enable': self.cellWidget(row_no, 4).findChild(QCheckBox, 'enable').isChecked(),
                'inside': self.cellWidget(row_no, 4).findChild(QCheckBox, 'inside').isChecked(),
                'regions': self.__trackers[row_no],
            }
        }
        return segment_values




    def select_segment(self):
        row_no = self.currentRow()
        log.info(f"new segment selected: {row_no}")
        selected_rows = list(set([index.row() for index in self.selectedIndexes()]))
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
            self.set_roi_table_content(row_no)

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


    def set_segment_values(self, row_no, segment):
        log.info(f"set single segment at row no. {row_no}")
        print_lightcyan(f"set single segmentat row no. {row_no}")
        pprint(segment)

        self.setItem(row_no, 0, QTableWidgetItem(f"{segment['start']}"))
        self.setItem(row_no, 1, QTableWidgetItem(f"{segment['end']}"))
        for i in range(2):
            self.item(row_no, i).setTextAlignment(self.cell_alignment[i])
            self.item(row_no, i).setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)

        # Frame used as the initial frame to start stabilization
        combobox_reference = QComboBox()
        combobox_reference.clear()
        combobox_reference.addItems(['start', 'middle', 'end'])
        index = combobox_reference.findText(segment['ref'])
        combobox_reference.setCurrentIndex(index)
        combobox_reference.setFocusPolicy(Qt.NoFocus)
        set_widget_stylesheet(combobox_reference)
        combobox_reference.currentIndexChanged[int].connect(self.event_reference_changed)
        self.setCellWidget(row_no, 2, combobox_reference)

        # Stabilization mode
        widget = QWidget()
        __layout = QHBoxLayout(widget)
        for w_name in ["vertical", "horizontal", "rotation"]:
            w = QCheckBox(widget)
            w.setText(w_name)
            w.setObjectName(w_name)
            w.setChecked(segment['mode'][w_name])
            w.setFocusPolicy(Qt.NoFocus)
            set_widget_stylesheet(w)
            w.toggled[bool].connect(self.event_mode_changed)
            __layout.addWidget(w)
        self.setCellWidget(row_no, 3, widget)


        # Tracking regions
        widget = QWidget()
        __layout = QHBoxLayout(widget)
        for w_name in ['enable', 'inside']:
            w = QCheckBox(widget)
            w.setText(w_name)
            w.setObjectName(w_name)
            w.setChecked(segment['tracker'][w_name])
            w.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            w.toggled[bool].connect(self.event_tracker_changed)
            set_widget_stylesheet(w)
            __layout.addWidget(w)
        self.setCellWidget(row_no, 4, widget)





    def set_content(self, segments):
        log.info(f"set content")
        print_lightcyan(f"set content")
        pprint(segments)
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
        self.initial_str = self.convert_to_str(selected_rows=list(range(len(segments))))


    def select_next_reference(self):
        combobox = self.cellWidget(self.currentRow(), 2)
        current_index = combobox.currentIndex()
        new_index = current_index+1 if current_index < combobox.count()-1 else 0
        self.cellWidget(self.currentRow(), 2).setCurrentIndex(new_index)
        self.signal_segment_modified.emit(self.currentRow())


    def select_mode_option(self, option):
        current_row = self.currentRow()
        segment_values = self.get_segment_values(row_no=current_row)
        self.cellWidget(current_row, 3).findChild(QCheckBox, option).toggle()
        self.signal_segment_modified.emit(self.currentRow())


    def get_content(self):
        segments = list()
        for row_no in range(self.rowCount()):
            segments.append(self.get_segment_values(row_no=row_no))

        # Modify settings as start and end are str
        for segment in segments:
            segment['start'] = int(segment['start'])
            segment['end'] = int(segment['end'])

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
        self.setItem(row_no, 0, QTableWidgetItem(""))
        self.setItem(row_no, 1, QTableWidgetItem(""))
        for i in range(2):
            self.item(row_no, i).setTextAlignment(self.cell_alignment[i])
            self.item(row_no, i).setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)

        # Frame used as the initial frame to start stabilization
        combobox_reference = QComboBox()
        combobox_reference.addItems(['start', 'middle', 'end'])
        combobox_reference.setCurrentIndex(1)
        combobox_reference.setFocusPolicy(Qt.NoFocus)
        combobox_reference.currentIndexChanged[int].connect(self.event_reference_changed)
        set_widget_stylesheet(combobox_reference)
        self.setCellWidget(row_no, 2, combobox_reference)

        # Stabilization mode
        widget = QWidget()
        __layout = QHBoxLayout(widget)
        for w_name in ["vertical", "horizontal", "rotation"]:
            w = QCheckBox(widget)
            w.setText(w_name)
            w.setObjectName(w_name)
            w.setChecked(True)
            w.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            w.toggled[bool].connect(self.event_mode_changed)
            set_widget_stylesheet(w)
            __layout.addWidget(w)
        self.setCellWidget(row_no, 3, widget)


        # Tracking regions
        widget = QWidget()
        __layout = QHBoxLayout(widget)
        for w_name, set_checked in zip(['enable', 'inside'],
                                    [False, True]):
            w = QCheckBox(widget)
            w.setText(w_name)
            w.setObjectName(w_name)
            w.setChecked(set_checked)
            w.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            w.toggled[bool].connect(self.event_tracker_changed)
            set_widget_stylesheet(w)
            __layout.addWidget(w)
        self.setCellWidget(row_no, 4, widget)



        # Tracker: regions
        widget = QWidget()
        __layout = QHBoxLayout(widget)
        for w_name in ["enable", "inside"]:
            w = QCheckBox(widget)
            w.setText(w_name)
            w.setObjectName(w_name)
            if w_name == 'enable':
                w.setChecked(False)
            else:
                w.setChecked(True)
            w.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            w.toggled[bool].connect(self.event_mode_changed)
            set_widget_stylesheet(w)
            __layout.addWidget(w)
        self.setCellWidget(row_no, 3, widget)

        self.selectRow(row_no)


    def append_segment(self):
        self.sortByColumn(-1, Qt.AscendingOrder)
        # APpend, i.e. set row_no to None, not clean but not time to refactor
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


    def event_reference_changed(self, index:int) -> None:
        # self.__parent.edition_started()
        self.signal_segment_modified.emit(self.currentRow())

    def event_mode_changed(self, state:bool) -> None:
        # self.__parent.edition_started()
        self.signal_segment_modified.emit(self.currentRow())

    def event_tracker_changed(self, state:bool) -> None:
        # self.__parent.edition_started()
        self.signal_segment_modified.emit(self.currentRow())



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