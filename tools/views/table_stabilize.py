# -*- coding: utf-8 -*-
import sys
from enum import IntEnum

from pprint import pprint
from logger import log

from PySide6.QtCore import (
    Qt,
    QPoint,

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
    QHBoxLayout
)
from utils.pretty_print import *

from utils.stylesheet import (
    set_stylesheet,
    set_widget_stylesheet
)

class Table_stabilize(QTableWidget):


    class History(object):
        class Action(IntEnum):
            insert = 1
            remove = 2
            delete = 3
            modify = 4
            sort = 5
            clear = 6

        def __init__(self, parent=None, depth=20):
            super(Table_stabilize.History, self).__init__()
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
        super(Table_stabilize, self).__init__(parent)


        if (self.columnCount() < 4):
            self.setColumnCount(4)
        __qtablewidgetitem = QTableWidgetItem()
        self.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.setHorizontalHeaderItem(3, __qtablewidgetitem3)


        __qtablewidgetitem4 = QTableWidgetItem()
        self.setVerticalHeaderItem(0, __qtablewidgetitem4)

        sizePolicy3 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy3)
        self.setFocusPolicy(Qt.NoFocus)
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
        self.setRowCount(0)


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
        self.setRowCount(0)
        self.alignment = [Qt.AlignRight | Qt.AlignVCenter,
                            Qt.AlignRight | Qt.AlignVCenter,
                            Qt.AlignCenter | Qt.AlignVCenter,
                            Qt.AlignLeft | Qt.AlignVCenter]
        headers = ["Start", "End", "Initial frame", "Mode"]
        default_col_width = [50, 50, 80, 300]
        for col_no, header_str, col_width in zip(range(len(headers)),
                                                    headers,
                                                    default_col_width):
            self.horizontalHeaderItem(col_no).setText(header_str)
            self.setColumnWidth(col_no, col_width)
        self.row_height = 35
        self.initial_str = ""

        self.__parent = parent
        # Signals
        # self.currentCellChanged['int','int','int','int'].connect(self.event_current_cell_changed)

        self.verticalHeader().customContextMenuRequested[QPoint].connect(self.event_right_click)
        self.verticalHeader().setContextMenuPolicy(Qt.CustomContextMenu)

        self.customContextMenuRequested[QPoint].connect(self.event_right_click)
        self.setContextMenuPolicy(Qt.CustomContextMenu)

        self.clearContents()
        self.history = self.History(self)
        set_stylesheet(self)
        self.adjustSize()


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
            self.history.add(self.History.Action.modify, {
                'row': self.currentRow(),
                'column': column_no,
                'old': previous_value,
                'new': new_value,
            })
            if previous_item.column() == 0:
                previous_item.setData(Qt.UserRole, previous_item.text())


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
            self.history.save_current_segment_values(segment_values)

    def event_current_cell_changed(self, row_no, column_no, previous_row_no, previous_column_no):
        log.info(f"new cell selected: {row_no}, {column_no}")
        segment_values = self.get_segment_values(row_no=row_no)
        self.history.save_current_segment_values(segment_values)


    def clear_contents(self):
        self.clearContents()
        self.setRowCount(0)

    def is_content_modified(self):
        # Convert segments to str
        new_str = self.convert_to_str(selected_rows=list(range(self.rowCount())))
        if new_str != self.initial_str:
            return True
        return False


    def set_segment_values(self, row_no, segment):
        log.info(f"set single segment at row no. {row_no}")
        print_lightcyan(f"set single segmentat row no. {row_no}")
        pprint(segment)

        self.setItem(row_no, 0, QTableWidgetItem(f"{segment['start']}"))
        self.setItem(row_no, 1, QTableWidgetItem(f"{segment['end']}"))
        for i in range(2):
            self.item(row_no, i).setTextAlignment(self.alignment[i])
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

        # Select first segment
        self.selectionModel().blockSignals(True)
        self.blockSignals(True)
        self.selectRow(0)
        self.blockSignals(False)
        self.selectionModel().blockSignals(False)

        # When calling this function, history is cleared
        self.history.flush()

        # Set the initial str to indicates if content is modified
        self.initial_str = self.convert_to_str(selected_rows=list(range(len(segments))))


    def select_next_reference(self):
        combobox = self.cellWidget(self.currentRow(), 2)
        current_index = combobox.currentIndex()
        new_index = current_index+1 if current_index < combobox.count()-1 else 0
        self.cellWidget(self.currentRow(), 2).setCurrentIndex(new_index)


    def select_mode_option(self, option):
        current_row = self.currentRow()
        segment_values = self.get_segment_values(row_no=current_row)
        self.cellWidget(current_row, 3).findChild(QCheckBox, option).toggle()
        self.history.add(self.History.Action.modify, {
            'row': current_row,
            'segment': segment_values,
            'alignment': self.alignment})

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
            segments = []
            for _row in range(self.rowCount()):
                _variable = []
                for _column in range(5):
                    _variable.append(self.item(_row, _column).text())
                segments.append(_variable)
            self.history.add(self.History.Action.clear,
                {'segments': segments, 'alignment': self.alignment})
        self.clearContents()
        self.setRowCount(0)
        self.__parent.edition_started()

    def remove_segment(self):
        row_nos = list(set([index.row() for index in self.selectedIndexes()]))
        if len(row_nos) == self.rowCount():
            self.remove_all_segments()
        else:
            segments = list()
            for row_no in sorted(row_nos, reverse=True):
                segments.append(self.get_segment_values(row_no=row_no))
                self.removeRow(row_no)
            self.history.add(self.History.Action.remove,
                {'segments': segments, 'alignment': self.alignment})
        self.__parent.edition_started()

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
            self.item(row_no, i).setTextAlignment(self.alignment[i])
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
            w.setFocusPolicy(Qt.NoFocus)
            w.toggled[bool].connect(self.event_mode_changed)
            set_widget_stylesheet(w)
            __layout.addWidget(w)
        self.setCellWidget(row_no, 3, widget)
        self.history.add(self.History.Action.insert,
            {'rows': [row_no], 'alignement': self.alignment})
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



    def event_right_click(self, qpoint):
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

    def event_copy(self):
        indexes = list(set([index.row() for index in self.selectedIndexes()]))

        if len(self.selectedIndexes())>0:
            previous_row_no = -1
            data_str = ""
            for item in self.selectedIndexes():
                self.get_segment_values(row_no=item.row())
                previous_row_no = item.row()
            clipboard = QApplication.clipboard()
            clipboard.setText(data_str)


    def event_cut(self):
        previous_row_no = -1
        indexes = list(set([index.row() for index in self.selectedIndexes()]))

        segments = list()
        # Convert dict into a str
        data_str = self.convert_to_str(indexes)

        for row_no in indexes:
            segments.append(self.get_segment_values(row_no=row_no))
            previous_row_no = row_no

        if len(indexes) == self.rowCount():
            self.remove_all_segments()
        else:
            for row_no in sorted(indexes, reverse=True):
                self.removeRow(row_no)
            self.history.add(self.History.Action.remove, {
                'segments': segments,
                'alignment': self.alignment})

        self.__parent.edition_started()
        self.clearSelection()
        self.setCurrentItem(self.item(-1, -1))
        clipboard = QApplication.clipboard()
        clipboard.setText(data_str)


    def event_paste(self):
        data_str = QApplication.clipboard().mimeData()
        if data_str.hasFormat('text/plain'):
            segments_str = data_str.text().split('\r')
            segments = [eval(segment_str) for segment_str in segments_str]

            segment_count = len(segments)
            if segment_count > 0:
                if self.currentRow() == -1:
                    row_no = self.rowCount()
                elif self.currentItem().isSelected():
                    row_no = self.currentItem().row()
                else:
                    row_no = self.rowCount()

                self.set_content(segments=segments)

                self.history.add(self.History.Action.insert, {
                    'rows': list(row_no),
                    'segments': segments,
                    'alignment': self.alignment})

                self.setSortingEnabled(True)
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
