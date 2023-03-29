# -*- coding: utf-8 -*-
import sys
sys.path.append('../scripts')
from pprint import pprint

from PySide6.QtCore import (
    QEvent,
    QSize,
    Qt,
)
from PySide6.QtGui import (
    QAction,
    QIcon,
)
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMenu,
    QAbstractScrollArea,
    QTableWidgetItem,
)

from filter_info.model_filter_info import Model_filter_info
from filter_info.ui.window_main_ui import Ui_MainWindow
from utils.pretty_print import *


class Window_main(QMainWindow, Ui_MainWindow):

    def __init__(self, model:Model_filter_info):
        super(Window_main, self).__init__()

        # Create and Patch UI
        self.setupUi(self)

        window_icon = QIcon()
        window_icon.addFile("icons/icon_16.png", QSize(16,16))
        window_icon.addFile("icons/icon_24.png", QSize(24,24))
        window_icon.addFile("icons/icon_32.png", QSize(32,32))
        window_icon.addFile("icons/icon_48.png", QSize(48,48))
        window_icon.addFile("icons/icon_64.png", QSize(64,64))
        window_icon.addFile("icons/icon_128.png", QSize(128,128))
        window_icon.addFile("icons/icon_256.png", QSize(256,256))
        self.setWindowIcon(window_icon)
        self.setWindowFlags(Qt.Window)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.move(20, 20)

        # Internal variables
        self.model = model
        self.is_closing = False

        # Widget properties
        self.tableWidget_filters.setFocusPolicy(Qt.NoFocus)
        self.lineEdit_filename.setFocusPolicy(Qt.NoFocus)

        # Set initial values
        self.clear_widgets()

        self.tableWidget_filters.setEnabled(False)
        # Install event filter
        # self.installEventFilter(self)

        # Enable drop
        self.setAcceptDrops(True)
        # self.lineEdit_filename.setAcceptDrops(True)

        # Events
        self.action_exit = QAction(u"Exit")
        self.action_exit.setEnabled(True)
        self.action_exit.setShortcut(u"Ctrl+Q")
        self.action_exit.triggered.connect(self.event_close)

        self.model.signal_refresh_filters[dict].connect(self.event_refresh_filters)


    def init_filter_table(self):
        self.tableWidget_filters.clearContents()
        self.tableWidget_filters.setRowCount(0)
        self.tableWidget_filters_columns = [
            {'name': 'hash', 'width': 90, 'alignment': Qt.AlignCenter | Qt.AlignVCenter},
            {'name': 'Filter', 'width': 200, 'alignment': Qt.AlignLeft | Qt.AlignTop },
        ]
        column_count = len(self.tableWidget_filters_columns)

        self.tableWidget_filters.setColumnCount(column_count)
        self.tableWidget_filters.horizontalHeader().setCascadingSectionResizes(False)
        self.tableWidget_filters.horizontalHeader().setDefaultSectionSize(25)
        self.tableWidget_filters.horizontalHeader().setHighlightSections(False)
        self.tableWidget_filters.horizontalHeader().setSortIndicatorShown(False)

        for col_no, properties in zip(range(column_count), self.tableWidget_filters_columns):
            self.tableWidget_filters.setHorizontalHeaderItem(col_no, QTableWidgetItem())
            self.tableWidget_filters.horizontalHeaderItem(col_no).setText(properties['name'])
            self.tableWidget_filters.setColumnWidth(col_no, properties['width'])
            self.tableWidget_filters.horizontalHeaderItem(col_no).setTextAlignment(properties['alignment'])

        self.tableWidget_filters.horizontalHeader().setStretchLastSection(True)
        # self.tableWidget_filters.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        # self.tableWidget_filters.resizeColumnsToContents()
        self.adjustSize()

    def clear_widgets(self):
        self.lineEdit_filename.clear()
        self.label_folder.clear()
        self.label_ed_ep_part.clear()
        self.label_shot_no.clear()
        self.tableWidget_filters.setEnabled(False)
        self.tableWidget_filters.clear()
        self.tableWidget_filters.clearContents()
        self.tableWidget_filters.setRowCount(0)
        self.tableWidget_filters.setColumnCount(0)


    def event_refresh_filters(self, properties):
        pprint(properties)
        self.lineEdit_filename.setText(properties['filename'])
        self.label_folder.setText(properties['folder'])
        if properties['hash'] is None:
            self.tableWidget_filters.clear()
            self.tableWidget_filters.clearContents()
            self.tableWidget_filters.setRowCount(0)
            self.tableWidget_filters.setColumnCount(0)
            self.tableWidget_filters.setEnabled(False)
            return

        ed_ep_part = "%s:%s:%s" % (properties['k_ed'], properties['k_ep'], properties['k_part'])
        self.label_ed_ep_part.setText(ed_ep_part)
        self.label_shot_no.setText("shot no. %d" % properties['shot_no'])

        self.init_filter_table()

        if properties['filters'] is not None:
            self.tableWidget_filters.setEnabled(True)
        else:
            self.tableWidget_filters.setEnabled(False)

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        filepath = urls[0].toLocalFile()
        self.model.event_new_file(filepath)


    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            print(u"Oh noooo!!!")


    def closeEvent(self, event):
        self.event_close()


    def event_close(self):
        if not self.is_closing:
            self.is_closing = True
            self.model.exit()
            self.close_all_widgets()


    def close_all_widgets(self):
        for widget in QApplication.topLevelWidgets():
            widget.close()
        self.close()
        # Not clean but avoid ghost processes: clean this
        sys.exit()


    def keyPressEvent(self, event):
        key = event.key()
        modifier = event.modifiers()

        if modifier & Qt.AltModifier:
            if key == Qt.Key_F9:
                self.showMinimized()

        elif key == Qt.Key_F9:
            self.showMinimized()
            event.accept()
            return True

        else:
            print_lightgrey("keyPressEvent: %d, propagate" % (key))



    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.ActivationChange:
            if self.windowState() == Qt.WindowState().WindowNoState:
                self.setWindowState(Qt.WindowActive)
                event.accept()
                return True

            if self.windowState() & Qt.WindowState().WindowActive:
                self.setWindowState(Qt.WindowActive)
                event.accept()
                return True

            if (self.windowState() & Qt.WindowState().WindowMinimized
            and not self.isActiveWindow()):
                self.setWindowState(Qt.WindowActive)
                event.accept()
                return True

        return super().changeEvent(event)
