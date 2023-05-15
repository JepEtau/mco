# -*- coding: utf-8 -*-
from copy import deepcopy
import sys
from enum import IntEnum

from pprint import pprint
from logger import log

from PySide6.QtCore import (
    Qt,
    QPoint,
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

class Widget_segments(QWidget):


    class History(object):
        class Action(IntEnum):
            insert = 1
            remove = 2
            delete = 3
            modify = 4
            sort = 5
            clear = 6

        def __init__(self, parent=None, depth=20):
            super(Widget_segments.History, self).__init__()
            self.table = parent
            self.actions = []
            self.redo = []
            self.saved_data = None
            if depth is not None:
                self.buffer_depth = depth

        def setDepth(self, depth=40):
            self.buffer_depth = depth

        def flush(self):
            self.actions.clear()
            self.redo.clear()
            self.saved_data = None

        def add(self, type=None, data=None):
            log.info("type=%s, data=%s" % (type, data))
            # Todo: verify action is managed
            if type is not None:
                _action = {'type': type, 'data': data}
                self.actions.insert(0, _action)
                self.redo.clear()
                if len(self.actions) > self.buffer_depth:
                    self.actions.pop()


        def undo(self):
            if len(self.actions):
                action = self.actions.pop(0)
                log.info("type=%s, data=%s" % (action['type'], action['data']))

                if action['type'] == self.Action.modify:
                    row_no = action['data']['row']
                    segment = action['data']['segment']
                    self.table.set_segment(row_no, segment)

                elif action['type'] == self.Action.delete:
                    for _cell in action['data']:
                        self.table.item(_cell['row'], _cell['column']).setText(_cell['old'])

                elif action['type'] == self.Action.insert:
                    for _row in reversed(action['data']['rows']):
                        self.table.removeRow(_row)

                elif action['type'] == self.Action.remove:
                    _alignment = action['data']['alignment']
                    segments = action['data']['segments']
                    self.table.sortByColumn(-1, Qt.AscendingOrder)
                    for _index in reversed(range(len(segments))):
                        row_no = segments[_index]['row']
                        self.table.insertRow(row_no)
                        self.table.setRowHeight(row_no, self.row_height)
                        column_count = self.table.columnCount()
                        for _column, _str, _align in zip(range(column_count), segments[_index]['values'], _alignment):
                            _item = QTableWidgetItem(_str)
                            _item.setData(Qt.UserRole, _str)
                            self.table.setItem(row_no, _column, _item)
                            self.table.item(row_no, _column).setTextAlignment(_align)

                elif action['type'] == self.Action.sort:
                    self.table.sortByColumn(4, Qt.AscendingOrder)
                    self.table.sortByColumn(-1, Qt.AscendingOrder)
                    for _row, _text in zip(range(self.table.rowCount()), action['data']['old']):
                        self.table.item(_row, 4).setText(_text)

                elif action['type'] == self.Action.clear:
                    self.table.sortByColumn(-1, Qt.AscendingOrder)
                    self.table.setRowCount(0)
                    if action['data']['segments'] is not None:
                        if len(action['data']['segments']) > 0:
                            for _row, _variable in zip(range(len(action['data']['segments'])),
                                                        action['data']['segments']):
                                self.table.insertRow(_row)
                                for _column, _str, _align in zip(range(column_count), _variable, action['data']['alignment']):
                                    self.table.setItem(_row, _column, QTableWidgetItem(_str))
                                    if _column == 0:
                                        self.table.item(_row, _column).setData(Qt.UserRole, _str)
                                    self.table.item(_row, _column).setTextAlignment(_align)

                self.redo.insert(0, action)


        def redo(self):
            if len(self.redo):
                action = self.redo.pop(0)
                log.info("type=%s, data=%s" % (action['type'], action['data']))
                if action['type'] == self.Action.modify:
                    _row = action['data']['row']
                    _column = action['data']['column']
                    _text = action['data']['new']
                    self.table.item(_row, _column).setText(_text)

                elif action['type'] == self.Action.delete:
                    for _cell in action['data']:
                        self.table.item(_cell['row'], _cell['column']).setText("")

                elif action['type'] == self.Action.insert:
                    self.table.setSortingEnabled(False)
                    self.table.sortByColumn(-1, Qt.AscendingOrder)
                    if 'segments' in action['data']:
                        for _variable, _row in zip(action['data']['segments'], action['data']['rows']):
                            self.table.insertRow(_row)
                            for _column, _str, _align in zip(range(5), _variable, action['data']['alignment']):
                                self.table.setItem(_row, _column, QTableWidgetItem(_str))
                                if _column == 0:
                                    self.table.item(_row, _column).setData(Qt.UserRole, _str)
                                self.table.item(_row, _column).setTextAlignment(_align)
                    else:
                        for _row in action['data']['rows']:
                            self.table.insertRow(_row)
                            for _column, _str, _align in zip(range(5), [u"",u"",u"",u"",u""], action['data']['alignment']):
                                _item = QTableWidgetItem(_str)
                                _item.setData(Qt.UserRole, _str)
                                self.table.setItem(_row, _column, _item)
                                self.table.item(_row, _column).setTextAlignment(_align)

                elif action['type'] == self.Action.remove:
                    for _variable in action['data']['segments']:
                        self.table.removeRow(_variable['row'])

                elif action['type'] == self.Action.sort:
                    self.table.sortByColumn(-1, Qt.AscendingOrder)
                    self.table.sortByColumn(action['data']['column'], Qt.AscendingOrder)
                    for _row, _text in zip(range(self.table.rowCount()), action['data']['new']):
                        self.table.item(_row, 4).setText(_text)

                elif action['type'] == self.Action.clear:
                    self.table.sortByColumn(-1, Qt.AscendingOrder)
                    self.table.clearContents()
                    self.table.setRowCount(0)

                self.actions.insert(0, action)
                if len(self.actions) > self.buffer_depth:
                    self.actions.pop()

        def save_current_segment_values(self, data):
            log.info("save <%s>" % (data))
            self.saved_data = data

        def saved_segment_values(self):
            return self.saved_data

        def clear_saved_segment_values(self):
            log.info("clear")
            self.saved_data = None


    def __init__(self, parent):
        super(Widget_segments, self).__init__(parent)


        self.mainLayout = QHBoxLayout(self)
        self.mainLayout.setSpacing(0)
        self.mainLayout.setObjectName(u"mainLayout")
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(6)


        # Table of segments
        self.table_segments_alignment = [
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        ]
        headers = ["Start", "End", "From", "Mode"]
        default_col_width = [60, 60, 75, 300]


        self.table_segments = QTableWidget()
        self.table_segments.setColumnCount(len(self.table_segments_alignment))
        for column_no in range(len(self.table_segments_alignment)):
            self.table_segments.setHorizontalHeaderItem(column_no, QTableWidgetItem())
        self.table_segments.setVerticalHeaderItem(0, QTableWidgetItem())

        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.table_segments.sizePolicy().hasHeightForWidth())
        self.table_segments.setSizePolicy(size_policy)
        self.table_segments.setMinimumSize(QSize(530, 300))

        self.table_segments.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table_segments.setFrameShape(QFrame.StyledPanel)
        self.table_segments.setFrameShadow(QFrame.Sunken)
        self.table_segments.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table_segments.setSizeAdjustPolicy(QAbstractScrollArea.AdjustIgnored)
        self.table_segments.setEditTriggers(QAbstractItemView.SelectedClicked)
        self.table_segments.setProperty("showDropIndicator", False)
        self.table_segments.setDragDropOverwriteMode(False)
        self.table_segments.setAlternatingRowColors(True)
        self.table_segments.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_segments.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_segments.setWordWrap(False)
        self.table_segments.setCornerButtonEnabled(False)
        self.table_segments.setMinimumHeight(305)

        self.table_segments.horizontalHeader().setCascadingSectionResizes(False)
        self.table_segments.horizontalHeader().setDefaultSectionSize(90)
        self.table_segments.horizontalHeader().setHighlightSections(True)
        self.table_segments.horizontalHeader().setSortIndicatorShown(True)
        self.table_segments.horizontalHeader().setStretchLastSection(True)
        self.table_segments.verticalHeader().setDefaultSectionSize(25)
        self.table_segments.verticalHeader().setSortIndicatorShown(False)
        self.table_segments.verticalHeader().setStretchLastSection(False)
        self.table_segments.setSortingEnabled(True)
        self.table_segments.setFocusPolicy(Qt.NoFocus)
        self.table_segments.clearContents()
        self.table_segments.setRowCount(6)
        for col_no, header_str, col_width in zip(range(len(headers)), headers, default_col_width):
            self.table_segments.horizontalHeaderItem(col_no).setText(header_str)
            self.table_segments.setColumnWidth(col_no, col_width)
        self.table_segments.adjustSize()
        # Signals
        self.table_segments.verticalHeader().customContextMenuRequested[QPoint].connect(self.event_segments_right_click)
        self.table_segments.verticalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_segments.customContextMenuRequested[QPoint].connect(self.event_segments_right_click)
        self.table_segments.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_segments.clearContents()

        self.mainLayout.addWidget(self.table_segments)


        # Table of ROI for each segment
        self.table_roi_alignment = [
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        ]
        headers = ["enabled", "inside", "coordinates"]
        default_col_width = [30, 30, 30]
        self.table_roi = QTableWidget()
        self.table_roi.setColumnCount(len(self.table_roi_alignment))
        for column_no in range(len(self.table_roi_alignment)):
            self.table_roi.setHorizontalHeaderItem(column_no, QTableWidgetItem())
        self.table_roi.setVerticalHeaderItem(0, QTableWidgetItem())

        size_policy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Expanding)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.table_roi.sizePolicy().hasHeightForWidth())
        self.table_roi.setSizePolicy(size_policy)
        self.table_roi.setMaximumSize(QSize(120, 800))

        self.table_roi.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table_roi.setFrameShape(QFrame.StyledPanel)
        self.table_roi.setFrameShadow(QFrame.Sunken)
        self.table_roi.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table_roi.setSizeAdjustPolicy(QAbstractScrollArea.AdjustIgnored)
        self.table_roi.setEditTriggers(QAbstractItemView.SelectedClicked)
        self.table_roi.setProperty("showDropIndicator", False)
        self.table_roi.setDragDropOverwriteMode(False)
        self.table_roi.setAlternatingRowColors(True)
        self.table_roi.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_roi.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_roi.setWordWrap(False)
        self.table_roi.setCornerButtonEnabled(False)
        self.table_roi.setMinimumHeight(200)

        self.table_roi.horizontalHeader().setCascadingSectionResizes(False)
        self.table_roi.horizontalHeader().setDefaultSectionSize(90)
        self.table_roi.horizontalHeader().setHighlightSections(True)
        self.table_roi.horizontalHeader().setSortIndicatorShown(True)
        self.table_roi.horizontalHeader().setStretchLastSection(False)
        self.table_roi.verticalHeader().setDefaultSectionSize(25)
        self.table_roi.verticalHeader().setSortIndicatorShown(False)
        self.table_roi.verticalHeader().setStretchLastSection(False)
        self.table_roi.setSortingEnabled(True)
        self.table_roi.setFocusPolicy(Qt.NoFocus)
        self.table_roi.clearContents()
        self.table_roi.setRowCount(6)
        for col_no, header_str, col_width in zip(range(len(headers)), headers, default_col_width):
            self.table_roi.horizontalHeaderItem(col_no).setText(header_str)
            self.table_roi.setColumnWidth(col_no, col_width)
        self.table_segments.adjustSize()
        # Signals
        self.table_roi.verticalHeader().customContextMenuRequested[QPoint].connect(self.event_roi_right_click)
        self.table_roi.verticalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_roi.customContextMenuRequested[QPoint].connect(self.event_roi_right_click)
        self.table_roi.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_roi.clearContents()

        self.mainLayout.addWidget(self.table_roi)

        self.row_height = 35
        self.row_roi_height = 25
        self.initial_str = ""
        self.__roi_list = list()
        self.history = self.History(self)
        set_stylesheet(self)
        self.__parent = parent
        self.adjustSize()



    def set_parent(self, parent):
        self.__parent = parent


    def set_frame_no(self, point, frame_no):
        column_no = 0 if point == 'start' else 1
        previous_item = self.table_segments.item(self.table_segments.currentRow(), column_no)
        previous_value = previous_item.text()
        new_value = f"{frame_no}"
        if new_value != previous_value:
            log.info(f"detected modification: {frame_no} -> {point}")
            self.table_segments.item(self.table_segments.currentRow(), column_no).setText(f"{frame_no}")
            self.history.add(self.History.Action.modify, {
                'row': self.table_segments.currentRow(),
                'column': column_no,
                'old': previous_value,
                'new': new_value,
            })
            if previous_item.column() == 0:
                previous_item.setData(Qt.UserRole, previous_item.text())


    def get_current_segment_values(self):
        return self.get_segment_values(self.table_segments.currentRow())


    def get_segment_values(self, row_no):
        segment_values = {
            'start': self.table_segments.item(row_no, 0).text(),
            'end': self.table_segments.item(row_no, 1).text(),
            'ref': self.table_segments.cellWidget(row_no, 2).currentText(),
            'alg': 'cv2_deshaker',
            'mode': {
                'horizontal': self.table_segments.cellWidget(row_no, 3).findChild(QCheckBox, 'horizontal').isChecked(),
                'vertical': self.table_segments.cellWidget(row_no, 3).findChild(QCheckBox, 'vertical').isChecked(),
                'rotation': self.table_segments.cellWidget(row_no, 3).findChild(QCheckBox, 'rotation').isChecked()
            },
            'roi': self.get_roi_values(row_no),
        }
        return segment_values

    def select_segment(self):
        row_no = self.table_segments.currentRow()
        log.info(f"new segment selected: {row_no}")
        selected_rows = list(set([index.row() for index in self.table_segments.selectedIndexes()]))
        if len(selected_rows) == 0:
            log.info(f"Do not save new selection")
            self.table_segments.selectionModel().blockSignals(True)
            self.blockSignals(True)
            self.table_segments.selectRow(row_no)
            # Update table of ROI
            self.set_roi_table_content(row_no)
            self.blockSignals(False)
            self.table_segments.selectionModel().blockSignals(False)
        else:
            log.info(f"new segment selected: {row_no}")
            segment_values = self.get_segment_values(row_no=row_no)
            self.set_roi_table_content(row_no)
            self.history.save_current_segment_values(segment_values)

    def event_current_cell_changed(self, row_no, column_no, previous_row_no, previous_column_no):
        log.info(f"new cell selected: {row_no}, {column_no}")
        segment_values = self.get_segment_values(row_no=row_no)
        self.history.save_current_segment_values(segment_values)


    def clear_contents(self):
        self.table_segments.clearContents()
        self.table_segments.setRowCount(0)
        self.table_roi.clearContents()
        self.table_roi.setRowCount(0)


    def is_content_modified(self):
        # Convert segments to str
        new_str = self.convert_to_str(selected_rows=list(range(self.table_segments.rowCount())))
        if new_str != self.initial_str:
            return True

        # Add Table of ROI
        return False


    def set_segment_values(self, row_no, segment):
        log.info(f"set single segment at row no. {row_no}")
        print_lightcyan(f"set single segmentat row no. {row_no}")
        pprint(segment)

        self.table_segments.setItem(row_no, 0, QTableWidgetItem(f"{segment['start']}"))
        self.table_segments.setItem(row_no, 1, QTableWidgetItem(f"{segment['end']}"))
        for i in range(2):
            self.table_segments.item(row_no, i).setTextAlignment(self.table_segments_alignment[i])
            self.table_segments.item(row_no, i).setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)

        # Frame used as the initial frame to start stabilization
        combobox_reference = QComboBox()
        combobox_reference.clear()
        combobox_reference.addItems(['start', 'middle', 'end'])
        index = combobox_reference.findText(segment['ref'])
        combobox_reference.setCurrentIndex(index)
        combobox_reference.setFocusPolicy(Qt.NoFocus)
        set_widget_stylesheet(combobox_reference)
        combobox_reference.currentIndexChanged[int].connect(self.event_reference_changed)
        self.table_segments.setCellWidget(row_no, 2, combobox_reference)

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
        self.table_segments.setCellWidget(row_no, 3, widget)

        # Update ROI table




    def set_content(self, segments):
        log.info(f"set content")
        print_lightcyan(f"set content")
        pprint(segments)
        self.table_segments.clearContents()
        self.table_segments.sortByColumn(-1, Qt.AscendingOrder)
        self.table_segments.setRowCount(0)

        for row_no, segment in zip(range(len(segments)), segments):
            self.table_segments.insertRow(row_no)
            self.table_segments.setRowHeight(row_no, self.row_height)
            self.set_segment_values(row_no=row_no, segment=segment)

        # Set internal values for ROI
        self.__roi_list = list([s['roi'] for s in segments])

        # Select first segment
        self.table_segments.selectionModel().blockSignals(True)
        self.blockSignals(True)
        self.table_segments.selectRow(0)
        self.set_roi_table_content(segment_no=0)


        self.blockSignals(False)
        self.table_segments.selectionModel().blockSignals(False)

        # When calling this function, history is cleared
        self.history.flush()

        # Set the initial str to indicates if content is modified
        self.initial_str = self.convert_to_str(selected_rows=list(range(len(segments))))


    def select_next_reference(self):
        combobox = self.table_segments.cellWidget(self.table_segments.currentRow(), 2)
        current_index = combobox.currentIndex()
        new_index = current_index+1 if current_index < combobox.count()-1 else 0
        self.table_segments.cellWidget(self.table_segments.currentRow(), 2).setCurrentIndex(new_index)


    def select_mode_option(self, option):
        current_row = self.table_segments.currentRow()
        segment_values = self.get_segment_values(row_no=current_row)
        self.table_segments.cellWidget(current_row, 3).findChild(QCheckBox, option).toggle()
        self.history.add(self.History.Action.modify, {
            'row': current_row,
            'segment': segment_values,
            'alignment': self.table_segments_alignment})

    def get_content(self):
        segments = list()
        for row_no in range(self.table_segments.rowCount()):
            segments.append(self.get_segment_values(row_no=row_no))

        # Modify settings as start and end are str
        for segment in segments:
            segment['start'] = int(segment['start'])
            segment['end'] = int(segment['end'])

        return segments


    def append_empty_segments(self, count):
        row_count = self.table_segments.rowCount()
        for row_no in range(row_count, row_count + count):
            self.table_segments.insertRow(row_no)
            self.table_segments.setRowHeight(row_no, self.row_height)


    def remove_all_segments(self):
        if self.table_segments.rowCount()>0:
            log.info("remove all")
            segments = list()
            row_nos = list(range(self.table_segments.rowCount()))
            for row_no in sorted(row_nos, reverse=True):
                segments.append(self.get_segment_values(row_no=row_no))
                self.table_segments.removeRow(row_no)
            self.history.add(self.History.Action.clear,
                {'segments': segments, 'alignment': self.table_segments_alignment})
        self.table_segments.clearContents()
        self.table_segments.setRowCount(0)
        self.__parent.edition_started()

    def remove_segment(self):
        row_nos = list(set([index.row() for index in self.table_segments.selectedIndexes()]))
        if len(row_nos) == self.table_segments.rowCount():
            self.remove_all_segments()
        else:
            segments = list()
            for row_no in sorted(row_nos, reverse=True):
                segments.append(self.get_segment_values(row_no=row_no))
                self.table_segments.removeRow(row_no)
            self.history.add(self.History.Action.remove,
                {'segments': segments, 'alignment': self.table_segments_alignment})
        self.__parent.edition_started()

    def insert_segment(self, row_no=None):
        self.table_segments.sortByColumn(-1, Qt.AscendingOrder)
        row_no = self.table_segments.rowCount()
        if row_no is None and self.table_segments.currentItem() is not None:
            row_no = self.table_segments.currentItem().row()
        elif self.table_segments.currentItem() is not None:
                row_no = self.table_segments.currentItem().row() + 1
        else:
            log.info("cannot insert a new segment")

        self.table_segments.insertRow(row_no)
        self.table_segments.setRowHeight(row_no, self.row_height)
        self.table_segments.setItem(row_no, 0, QTableWidgetItem(""))
        self.table_segments.setItem(row_no, 1, QTableWidgetItem(""))
        for i in range(2):
            self.table_segments.item(row_no, i).setTextAlignment(self.table_segments_alignment[i])
            self.table_segments.item(row_no, i).setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)

        # Frame used as the initial frame to start stabilization
        combobox_reference = QComboBox()
        combobox_reference.addItems(['start', 'middle', 'end'])
        combobox_reference.setCurrentIndex(1)
        combobox_reference.setFocusPolicy(Qt.NoFocus)
        combobox_reference.currentIndexChanged[int].connect(self.event_reference_changed)
        set_widget_stylesheet(combobox_reference)
        self.table_segments.setCellWidget(row_no, 2, combobox_reference)

        # Stabilization mode
        widget = QWidget()
        __layout = QHBoxLayout(widget)
        for w_name in ["vertical", "horizontal", "rotation"]:
            w = QCheckBox(widget)
            w.setText(w_name)
            w.setObjectName(w_name)
            w.setChecked(True)
            w.setFocusPolicy(Qt.NoFocus)
            w.toggled[bool].connect(self.event_mode_changed)
            set_widget_stylesheet(w)
            __layout.addWidget(w)
        self.table_segments.setCellWidget(row_no, 3, widget)
        self.history.add(self.History.Action.insert,
            {'rows': [row_no], 'alignement': self.table_segments_alignment})
        self.table_segments.selectRow(row_no)


    def append_segment(self):
        self.table_segments.sortByColumn(-1, Qt.AscendingOrder)
        # APpend, i.e. set row_no to None, not clean but not time to refactor
        self.insert_segment(row_no=None)


    def insert_segment_at(self):
        cursor_position = self.mapFromGlobal(QCursor.pos())
        item_position_x = cursor_position.x() + 5
        item_position_y = cursor_position.y() - self.table_segments.horizontalHeader().size().height() * 2 + 5
        item = self.table_segments.itemAt(item_position_x, item_position_y)
        if item is not None:
            self.table_segments.clearSelection()
            self.table_segments.setCurrentItem(item)
            self.insert_segment(item.row())
            self.table_segments.clearSelection()
            self.table_segments.setCurrentItem(self.table_segments.item(-1, -1))
        else:
            self.table_segments.setCurrentItem(None)
            self.insert_segment(None)



    def event_segments_right_click(self, qpoint):
        cursor_position = QCursor.pos()
        self.popMenu = QMenu(self)
        insert_action = self.popMenu.addAction('Insert')
        insert_action.triggered.connect(self.insert_segment_at)
        if len(self.table_segments.selectedIndexes()) > 0:
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

    def event_copy(self):
        indexes = list(set([index.row() for index in self.table_segments.selectedIndexes()]))

        if len(self.table_segments.selectedIndexes())>0:
            previous_row_no = -1
            data_str = ""
            for item in self.table_segments.selectedIndexes():
                self.get_segment_values(row_no=item.row())
                previous_row_no = item.row()
            clipboard = QApplication.clipboard()
            clipboard.setText(data_str)


    def event_cut(self):
        previous_row_no = -1
        indexes = list(set([index.row() for index in self.table_segments.selectedIndexes()]))

        segments = list()
        # Convert dict into a str
        data_str = self.convert_to_str(indexes)

        for row_no in indexes:
            segments.append(self.get_segment_values(row_no=row_no))
            previous_row_no = row_no

        if len(indexes) == self.table_segments.rowCount():
            self.remove_all_segments()
        else:
            for row_no in sorted(indexes, reverse=True):
                self.table_segments.removeRow(row_no)
            self.history.add(self.History.Action.remove, {
                'segments': segments,
                'alignment': self.table_segments_alignment})

        self.__parent.edition_started()
        self.table_segments.clearSelection()
        self.table_segments.setCurrentItem(self.table_segments.item(-1, -1))
        clipboard = QApplication.clipboard()
        clipboard.setText(data_str)


    def event_paste(self):
        data_str = QApplication.clipboard().mimeData()
        if data_str.hasFormat('text/plain'):
            segments_str = data_str.text().split('\r')
            segments = [eval(segment_str) for segment_str in segments_str]

            segment_count = len(segments)
            if segment_count > 0:
                if self.table_segments.currentRow() == -1:
                    row_no = self.table_segments.rowCount()
                elif self.table_segments.currentItem().isSelected():
                    row_no = self.table_segments.currentItem().row()
                else:
                    row_no = self.table_segments.rowCount()

                self.set_content(segments=segments)

                self.history.add(self.History.Action.insert, {
                    'rows': list(row_no),
                    'segments': segments,
                    'alignment': self.table_segments_alignment})

                self.table_segments.setSortingEnabled(True)
        else:
            log.info("cannot paste, not a plain text")



    def undo(self):
        self.history.undo()

    def redo(self):
        self.history.redo()

    def copy(self):
        self.event_copy()

    def cut(self):
        self.event_copy()

    def paste(self):
        self.event_paste()

    def event_reference_changed(self, index:int) -> None:
        self.__parent.edition_started()

    def event_mode_changed(self, state:bool) -> None:
        self.__parent.edition_started()



    # Table of ROI

    def event_roi_right_click(self, qpoint):
        cursor_position = QCursor.pos()
        self.popMenu = QMenu(self)
        append_action = self.popMenu.addAction('Append')
        append_action.triggered.connect(self.append_roi)
        if len(self.table_roi.selectedIndexes()) > 0:
            remove_action = self.popMenu.addAction('Remove')
            remove_action.triggered.connect(self.remove_roi)
        self.popMenu.exec_(cursor_position)


    def append_roi(self):
        # ["enabled", "inside", "coordinates"]
        self.table_roi.sortByColumn(-1, Qt.AscendingOrder)
        row_no = self.table_roi.rowCount()
        self.table_roi.insertRow(row_no)
        self.table_roi.setRowHeight(row_no, self.row_height)
        self.table_roi.setItem(row_no, 2, QTableWidgetItem(""))
        self.table_roi.item(row_no, 2).setTextAlignment(self.table_roi_alignment[i])
        self.table_roi.item(row_no, 2).setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)

        # modes
        for i, w_name in zip(range(2), ["enabled", "inside"]):
            w = QCheckBox()
            w.setObjectName(w_name)
            w.setChecked(True)
            w.setFocusPolicy(Qt.NoFocus)
            w.toggled[bool].connect(self.event_roi_mode_changed)
            set_widget_stylesheet(w)
            self.table_roi.setCellWidget(row_no, i, w)
        self.table_roi.selectRow(row_no)


    def event_roi_mode_changed(self, state:bool) -> None:
        self.__parent.edition_started()


    def remove_roi(self):
        row_nos = list(set([index.row() for index in self.table_roi.selectedIndexes()]))
        if len(row_nos) == self.table_roi.rowCount():
            self.remove_all_roi()
        else:
            for row_no in sorted(row_nos, reverse=True):
                self.table_roi.removeRow(row_no)
        self.__parent.edition_started()

    def remove_all_roi(self):
        if self.table_roi.rowCount() > 0:
            log.info("remove all")
            row_nos = list(range(self.table_roi.rowCount()))
            for row_no in sorted(row_nos, reverse=True):
                self.table_roi.removeRow(row_no)
        self.table_roi.clearContents()
        self.table_roi.setRowCount(0)
        self.__parent.edition_started()


    def convert_roi_to_str(self, selected_rows:list) -> str:
        data_str = ""
        for row_no in selected_rows:
            roi_values = self.get_roi_values(row_no=row_no)
            data_str += str(roi_values) + '\n'
        data_str = data_str[:-1]
        return data_str

    def append_empty_roi(self, count):
        row_count = self.table_roi.rowCount()
        for row_no in range(row_count, row_count + count):
            self.table_roi.insertRow(row_no)
            self.table_roi.setRowHeight(row_no, self.row_height)

    def get_roi_content(self):
        # segments = list()
        # for row_no in range(self.table_segments.rowCount()):
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


    def set_roi_table_content(self, segment_no:int):
        pprint(self.__roi_list)
        self.table_roi.clearContents()
        row_count = len(self.__roi_list[segment_no])
        if row_count > 0:
            for row_no, roi in zip(range(row_count), self.__roi_list[segment_no]):
                self.table_roi.insertRow(row_no)
                self.table_roi.setRowHeight(row_no, self.row_roi_height)

                # Modes
                for i, w_name in zip(range(2), ["enabled", "inside"]):
                    w = QCheckBox()
                    w.setObjectName(w_name)
                    w.setChecked(True)
                    w.setFocusPolicy(Qt.NoFocus)
                    w.toggled[bool].connect(self.event_roi_mode_changed)
                    set_widget_stylesheet(w)
                    self.table_roi.setCellWidget(row_no, i, w)

                # Points
                self.table_roi.setItem(row_no, 2, QTableWidgetItem(""))
                self.table_roi.item(row_no, 2).setTextAlignment(self.table_roi_alignment[2])
                self.table_roi.item(row_no, 2).setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)

                self.table_roi.selectRow(row_no)




    def get_roi_values(self, segment_no:int):
        return list()