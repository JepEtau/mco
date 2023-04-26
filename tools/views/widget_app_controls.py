# -*- coding: utf-8 -*-

import sys

from pprint import pprint
from logger import log

from PySide6.QtCore import (
    QEvent,
    QPoint,
    Qt,
    Signal,
)
from PySide6.QtWidgets import QWidget

from .ui.widget_app_controls_ui import Ui_widget_app_controls


class Widget_app_controls(QWidget, Ui_widget_app_controls):
    signal_action = Signal(str)

    def __init__(self, ui):
        super(Widget_app_controls, self).__init__()
        self.ui = ui

        # Setup and patch ui
        self.setupUi(self)

        self.pushButton_minimize.setFocusPolicy(Qt.NoFocus)
        self.pushButton_minimize.clicked.connect(self.event_minimize)

        self.pushButton_exit.setFocusPolicy(Qt.NoFocus)
        self.pushButton_exit.clicked.connect(self.event_exit)

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




    def set_save_discard_enabled(self, enabled:bool):
        self.pushButton_discard_modifications.setEnabled(enabled)
        self.pushButton_save_modifications.setEnabled(enabled)
