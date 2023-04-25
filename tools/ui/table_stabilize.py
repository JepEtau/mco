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
                    _row = action['data']['row']
                    _column = action['data']['column']
                    _text = action['data']['old']
                    self.table.item(_row, _column).setText(_text)

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

        def saveCurrentData(self, data):
            log.info("save <%s>" % (data))
            self.saved_data = data

        def savedData(self):
            return self.saved_data

        def clearSavedData(self):
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
        if (self.rowCount() < 5):
            self.setRowCount(5)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.setVerticalHeaderItem(0, __qtablewidgetitem4)
        __qtablewidgetitem5 = QTableWidgetItem()
        self.setItem(0, 0, __qtablewidgetitem5)
        __qtablewidgetitem6 = QTableWidgetItem()
        self.setItem(0, 1, __qtablewidgetitem6)
        __qtablewidgetitem7 = QTableWidgetItem()
        self.setItem(0, 2, __qtablewidgetitem7)
        __qtablewidgetitem8 = QTableWidgetItem()
        self.setItem(0, 3, __qtablewidgetitem8)

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
        self.setRowCount(1)
        self.setColumnCount(4)


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
        headers = ["start", "end", "initial ref.", "mode"]
        default_col_width = [50, 50, 80, 200]
        for col_no, header_str, col_width in zip(range(len(headers)),
                                                    headers,
                                                    default_col_width):
            self.horizontalHeaderItem(col_no).setText(header_str)
            self.setColumnWidth(col_no, col_width)
        self.row_height = 40

        # Signals
        self.verticalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.verticalHeader().customContextMenuRequested[QPoint].connect(self.event_right_click)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested[QPoint].connect(self.event_right_click)

        self.clearContents()
        self.history = self.History(self)
        set_stylesheet(self)



    def clear_contents(self):
        self.clearContents()
        self.setRowCount(0)



    def set_content(self, segments):
        # When calling this function, history is cleared
        self.history.flush()
        self.clearContents()
        self.sortByColumn(-1, Qt.AscendingOrder)
        self.setRowCount(0)



        for row_no, segment in zip(range(len(segments)), segments):
            mode_str = ""
            self.insertRow(row_no)
            self.setRowHeight(row_no, self.row_height)
            self.setItem(row_no, 0, QTableWidgetItem(f"{segment['start']}"))
            self.setItem(row_no, 1, QTableWidgetItem(f"{segment['end']}"))
            for i in range(2):
                self.item(row_no, i).setTextAlignment(self.alignment[i])
                self.item(row_no, i).setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)

            # Frame used as the initial frame to start stabilization
            combobox_reference = QComboBox()
            combobox_reference.addItems(['start', 'middle', 'end'])
            combobox_reference.setCurrentText(segment['ref'])
            combobox_reference.setFocusPolicy(Qt.NoFocus)
            set_widget_stylesheet(combobox_reference)
            self.setCellWidget(row_no, 2, combobox_reference)

            # Stabilization mode
            widget = QWidget()
            horizontalLayout = QHBoxLayout(widget)
            for w_name in ["horizontal", "vertical", "rotation"]:
                w = QCheckBox(widget)
                w.setText(w_name)
                w.setObjectName(w_name)
                w.setChecked(segment['mode'][w_name])
                w.setFocusPolicy(Qt.NoFocus)
                set_widget_stylesheet(w)
                horizontalLayout.addWidget(w)
            self.setCellWidget(row_no, 3, widget)

        self.selectionModel().clearSelection()


    def get_content(self):
        segments = list()
        for row_no in range(self.rowCount()):
            try:
                start = int(self.item(row_no, 0).text())
            except:
                continue

            segment = {
                'start': start,
                'end': int(self.item(row_no, 1).text()),
                'ref': self.cellWidget(0, 2).currentText(),
                'alg': 'cv2_deshaker',
                'mode': {
                    'vertical': self.cellWidget(0, 3).findChild(QCheckBox, 'vertical').isChecked(),
                    'horizontal': self.cellWidget(0, 3).findChild(QCheckBox, 'horizontal').isChecked(),
                    'rotation': self.cellWidget(0, 3).findChild(QCheckBox, 'rotation').isChecked()
                },
            }
            segments.append(segment)
        pprint(segments)
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


    def remove_segment(self):
        row_nos = list(set([index.row() for index in self.selectedIndexes()]))
        if len(row_nos) == self.rowCount():
            self.remove_all_segments()
        else:
            segments = list()
            for row_no in sorted(row_nos, reverse=True):
                segments.append({
                    'row': row_no,
                    'values':[self.item(row_no, column_no).text() for column_no in range(self.columnCount())]
                })
                self.removeRow(row_no)
            self.history.add(self.History.Action.remove,
                {'segments': segments, 'alignment': self.alignment})



    def insert_segment(self):
        self.sortByColumn(-1, Qt.AscendingOrder)
        if self.currentItem() is not None:
            row_no = self.currentItem().row()
        else:
            row_no = self.rowCount()
        self.insertRow(row_no)
        self.setRowHeight(row_no, self.row_height)
        default_values = [""] * self.columnCount()
        for column_no, values, alignment in zip(range(self.columnCount()), default_values, self.alignment):
            item = QTableWidgetItem(values)
            item.setData(Qt.UserRole, values)
            self.setItem(row_no, column_no, item)
            self.item(row_no, column_no).setTextAlignment(alignment)
        self.history.add(self.History.Action.insert,
            {'rows': [row_no], 'alignement': self.alignment})


    def append_segment(self):
        self.sortByColumn(-1, Qt.AscendingOrder)
        if self.currentItem() is not None:
            row_no = self.currentItem().row() + 1
        else:
            row_no = self.rowCount()
        log.info("insert row (%d)" % (row_no))
        self.insertRow(row_no)
        self.setRowHeight(row_no, self.row_height)
        default_values = [""] * self.columnCount()
        for column_no, values, alignment in zip(range(self.columnCount()), default_values, self.alignment):
            item = QTableWidgetItem(values)
            item.setData(Qt.UserRole, values)
            self.setItem(row_no, column_no, item)
            self.item(row_no, column_no).setTextAlignment(alignment)
        self.history.add(self.History.Action.insert,
            {'rows': [row_no], 'alignement': self.alignment})


    def insert_segment_at(self):
        cursor_position = self.mapFromGlobal(QCursor.pos())
        item_position_x = cursor_position.x() + 5
        item_position_y = cursor_position.y() - self.horizontalHeader().size().height() * 2 + 5
        item = self.itemAt(item_position_x, item_position_y)
        if item is not None:
            self.clearSelection()
            self.setCurrentItem(item)
            self.insert_segment()
            self.clearSelection()
            self.setCurrentItem(self.item(-1, -1))
        else:
            self.setCurrentItem(None)
            self.insert_segment()
        self._isModified=True




    def event_right_click(self, qpoint):
        cursor_position = QCursor.pos()
        self.popMenu = QMenu(self)
        insert_action = self.popMenu.addAction('Insert')
        insert_action.triggered.connect(self.insert_segment_at)
        if len(self.selectedIndexes()) > 0:
            remove_action = self.popMenu.addAction('Remove')
            remove_action.triggered.connect(self.remove_segment)
        self.popMenu.exec_(cursor_position)




    def event_copy(self):
        if len(self.selectedIndexes())>0:
            previous_row_no = -1
            data_str = ""
            for item in self.selectedIndexes():
                if previous_row_no != item.row() and previous_row_no != -1:
                    data_str += '\n'
                elif previous_row_no!=-1:
                    data_str += '\t'
                data_str += self.item(item.row(), item.column()).text()
                previous_row_no = item.row()
            clipboard = QApplication.clipboard()
            clipboard.setText(data_str)


    def event_cut(self):
        previous_row_no = -1
        data_str = ""
        for item in self.selectedIndexes():
            if previous_row_no != item.row() and previous_row_no!=-1:
                data_str += '\n'
            elif previous_row_no!=-1:
                data_str += '\t'
            data_str += self.item(item.row(), item.column()).text()
            previous_row_no = item.row()

        indexes = [index.row() for index in self.selectedIndexes()]
        indexes = list(set(indexes))
        if len(indexes) == self.rowCount():
            self.remove_all_segments()
        else:
            segments = []
            for index in sorted(indexes, reverse=True):
                segments.append({'row': index,
                                    'values':[self.item(index, 0).text(),
                                        self.item(index, 1).text(),
                                        self.item(index, 2).text(),
                                        self.item(index, 3).text(),
                                        self.item(index, 4).text()]})
                self.removeRow(index)
            self._history.add(self.History.Action.remove, {
                'segments': segments,
                'alignment': self.alignment})

        self.clearSelection()
        self.setCurrentItem(self.item(-1, -1))

        clipboard = QApplication.clipboard()
        clipboard.setText(data_str)


    def event_paste(self):
        data_str = QApplication.clipboard().mimeData()
        if data_str.hasFormat('text/plain'):
            segments = []
            for segment_str in data_str.text().split('\n'):
                segment_property = segment_str.split('\t')
                if len(segment_property) > self.columnCount():
                    break
                else:
                    segment = [""] * self.columnCount()
                    for _item, _i in zip(segment_property, range(len(segment_property))):
                        segment[_i] = _item
                    if segment[0] != "":
                        segments.append(segment)

            segment_count = len(segments)
            if segment_count > 0:
                if self.currentRow() == -1:
                    index = self.rowCount()
                elif self.currentItem().isSelected():
                    index = self.currentItem().row()
                else:
                    index = self.rowCount()

                self.setSortingEnabled(False)
                self.sortByColumn(-1, Qt.AscendingOrder)

                rows = range(index, index + segment_count)
                for segment, row_no in zip(segments, rows):
                    log.info("paste: insert row (%d)" % (row_no))
                    self.insertRow(row_no)
                    self.setRowHeight(row_no, self.row_height)
                    for column_no, property, alignment in zip(range(self.columnCount()), segment, self.alignment):
                        self.setItem(row_no, column_no, QTableWidgetItem(property))
                        if column_no == 0:
                            self.item(row_no, column_no).setData(Qt.UserRole, property)
                        self.item(row_no, column_no).setTextAlignment(alignment)

                self.history.add(self.History.Action.insert, {
                    'rows': list(rows),
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
