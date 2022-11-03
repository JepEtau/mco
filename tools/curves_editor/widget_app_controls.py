#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pprint import pprint
from logger import log

from PySide6.QtCore import (
    QSize,
    Qt,
    Signal,
)
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QWidget,
)


class Widget_app_controls(QWidget):
    signal_action = Signal(str)

    def __init__(self, ui, modifications_enabled:bool=False):
        super(Widget_app_controls, self).__init__()
        self.ui = ui

        # Setup and patch ui
        # self.setupUi(self)
        if not self.objectName():
            self.setObjectName(u"widget_app_controls")
        self.resize(258, 24)
        self.horizontalLayout = QHBoxLayout(self)
        self.horizontalLayout.setSpacing(3)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)

        sizePolicy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)

        if modifications_enabled:
            self.pushButton_discard_modifications = QPushButton(self)
            self.pushButton_discard_modifications.setObjectName(u"pushButton_discard_modifications")
            sizePolicy.setHeightForWidth(self.pushButton_discard_modifications.sizePolicy().hasHeightForWidth())
            self.pushButton_discard_modifications.setSizePolicy(sizePolicy)
            icon = QIcon()
            icon.addFile(u"img/purple/undo.svg", QSize(), QIcon.Normal, QIcon.Off)
            self.pushButton_discard_modifications.setIcon(icon)
            self.pushButton_discard_modifications.setCheckable(False)
            self.pushButton_discard_modifications.setAutoDefault(False)
            self.pushButton_discard_modifications.setFlat(True)

            self.horizontalLayout.addWidget(self.pushButton_discard_modifications)

            self.pushButton_save_modifications = QPushButton(self)
            self.pushButton_save_modifications.setObjectName(u"pushButton_save_modifications")
            sizePolicy.setHeightForWidth(self.pushButton_save_modifications.sizePolicy().hasHeightForWidth())
            self.pushButton_save_modifications.setSizePolicy(sizePolicy)
            icon1 = QIcon()
            icon1.addFile(u"img/purple/save.svg", QSize(), QIcon.Normal, QIcon.Off)
            self.pushButton_save_modifications.setIcon(icon1)
            self.pushButton_save_modifications.setCheckable(False)
            self.pushButton_save_modifications.setAutoDefault(False)
            self.pushButton_save_modifications.setFlat(True)

            self.horizontalLayout.addWidget(self.pushButton_save_modifications)

        self.horizontalSpacer = QSpacerItem(5, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.pushButton_minimize = QPushButton(self)
        self.pushButton_minimize.setObjectName(u"pushButton_minimize")
        sizePolicy.setHeightForWidth(self.pushButton_minimize.sizePolicy().hasHeightForWidth())
        self.pushButton_minimize.setSizePolicy(sizePolicy)
        icon2 = QIcon()
        icon2.addFile(u"img/purple/minus-square.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_minimize.setIcon(icon2)
        self.pushButton_minimize.setCheckable(False)
        self.pushButton_minimize.setAutoDefault(False)
        self.pushButton_minimize.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_minimize)

        self.pushButton_exit = QPushButton(self)
        self.pushButton_exit.setObjectName(u"pushButton_exit")
        sizePolicy.setHeightForWidth(self.pushButton_exit.sizePolicy().hasHeightForWidth())
        self.pushButton_exit.setSizePolicy(sizePolicy)
        icon3 = QIcon()
        icon3.addFile(u"img/purple/x-square.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_exit.setIcon(icon3)
        self.pushButton_exit.setCheckable(False)
        self.pushButton_exit.setAutoDefault(False)
        self.pushButton_exit.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_exit)


        self.pushButton_minimize.setFocusPolicy(Qt.NoFocus)
        self.pushButton_minimize.clicked.connect(self.event_minimize)

        self.pushButton_exit.setFocusPolicy(Qt.NoFocus)
        self.pushButton_exit.clicked.connect(self.event_exit)

        if modifications_enabled:
            self.pushButton_discard_modifications.setFocusPolicy(Qt.NoFocus)
            self.pushButton_discard_modifications.clicked.connect(self.event_discard_modifications)

            self.pushButton_save_modifications.setFocusPolicy(Qt.NoFocus)
            self.pushButton_save_modifications.clicked.connect(self.event_save_modifications)

            self.set_save_discard_enabled(False)

        self.adjustSize()


    def event_discard_modifications(self):
        self.signal_action.emit('discard')


    def event_save_modifications(self):
        self.signal_action.emit('save')


    def event_minimize(self):
        log.info("minimize button clicked")
        self.signal_action.emit('minimize')


    def event_exit(self):
        log.info("exit button clicked")
        self.signal_action.emit('exit')


    def closeEvent(self, event):
        self.signal_action.emit('exit')


    def set_save_discard_enabled(self, enabled:bool):
        self.pushButton_discard_modifications.setEnabled(enabled)
        self.pushButton_save_modifications.setEnabled(enabled)
