#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

class Window_common(object):
    def patch_ui(self):
        self.setWindowIcon(QIcon("img/icon.png"))
        self.setWindowFlags(Qt.Window)
        self.setStyleSheet("background-color: black")
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)

