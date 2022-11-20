#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import logging.config
import os.path
import re
from subprocess import call
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog
from PySide6.QtWidgets import QTableWidgetItem

from logger.ui_logger import Ui_logger

_log_iniFilename = 'log'

class Qdialog_NoClose(QDialog):
    """ This class avoids the closing of the QDialog from user """
    def __init__(self, *args, **kwargs):
        super(Qdialog_NoClose, self).__init__(*args, **kwargs)

    def keyPressEvent(self, event):
        if not event.key() == Qt.Key_Escape:
            super(Qdialog_NoClose, self).keyPressEvent(event)

    # def closeEvent(self, event):
    #     if event.spontaneous():
    #         event.ignore()


class CustomHandler(logging.StreamHandler):

    def __init__(self, *args, **kwargs):
        super(CustomHandler, self).__init__(*args, **kwargs)

        self._uiDialog = Qdialog_NoClose(parent=None, modal=False)
        self._ui = Ui_logger()
        self._ui.setupUi(self._uiDialog)
        if sys.platform == 'win32':
            self._uiDialog.move(1700, 100)
        else:
            self._uiDialog.move(2500, 100)

        # self.resize(1200, 900)

        # Table widget
        self._tableAlignment = [Qt.AlignHCenter,
                                Qt.AlignHCenter,
                                Qt.AlignLeft,
                                Qt.AlignHCenter,
                                Qt.AlignLeft,
                                Qt.AlignLeft]
        _defaultWidth = [100, 80, 200, 40, 250]
        self._ui.tableWidget.clearContents()
        self.__files = []
        for _column, _align, _width in zip(range(6), self._tableAlignment, _defaultWidth):
            self._ui.tableWidget.horizontalHeaderItem(_column).setTextAlignment(_align)
            self._ui.tableWidget.setColumnWidth(_column, _width)

        # Actions
        self._ui.button_clear.pressed.connect(self._eventClearTable)
        self._ui.tableWidget.cellDoubleClicked['int','int'].connect(self._eventCellDoubleClicked)

        self._uiDialog.show()

    def emit(self, record):
        try:
            if self._uiDialog is not None:
                # print(u"record type=[%s], record=%s" % (type(record), record))
                _msg = self.format(record)
                _s = re.split('¤', _msg)
                if _s is not None:
                    _row = self._ui.tableWidget.rowCount()
                    self._ui.tableWidget.insertRow(_row)
                    for _column, _str, _align in zip(range(6), _s, self._tableAlignment):
                        self._ui.tableWidget.setItem(_row, _column, QTableWidgetItem(_str))
                        self._ui.tableWidget.item(_row, _column).setTextAlignment(_align)
                    self._ui.tableWidget.scrollToItem(self._ui.tableWidget.item(_row, _column))
                    self.__files.append((_s[6], _s[3]))
                    # print(_s[6]+ "(" + _s[3] + ")")
        except:
            pass
        self.flush()

    def close(self):
        try:
            self._uiDialog.close()
        except:
            pass

    def _eventClearTable(self):
        self._ui.tableWidget.clearContents()
        self._ui.tableWidget.setRowCount(0)
        self.__files.clear()


    def _eventCellDoubleClicked(self, row, col):
        _file = self.__files[row][0]
        _lineNo = self.__files[row][1]
        _exe = "code"
        if sys.platform == 'win32':
            command_line = "%s -g %s:%s" % (_exe, _file, _lineNo)
            os.system(command_line)
        elif sys.platform == 'linux':
            call([_exe, "-g", _file + ":" + _lineNo])


if os.path.isfile(_log_iniFilename):
    log = logging.getLogger()
    log.setLevel(logging.INFO)

    _customHandler = CustomHandler()
    _formatter = logging.Formatter(fmt='%(asctime)s.%(msecs)03d¤%(levelname)s¤%(filename)s¤%(lineno)d¤%(funcName)s¤%(message)s¤%(pathname)s',
                                    datefmt='%H:%M:%S')
    _customHandler.setFormatter(_formatter)
    log.addHandler(_customHandler)
else:
    logging.basicConfig(level=logging.CRITICAL, format='%(filename)s (%(lineno)d): %(funcName)s: %(message)s')
    log = logging.getLogger()
    _customHandler = None
