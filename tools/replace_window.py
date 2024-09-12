from __future__ import annotations
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QWidget
from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QHeaderView, QMainWindow,
    QSizePolicy, QTableWidget, QTableWidgetItem, QWidget)

if TYPE_CHECKING:
    from .replace_controller import ReplaceController


class ReplaceWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.centralwidget = QWidget(self)
        self.centralwidget.setObjectName(u"centralwidget")
        self.horizontalLayout = QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.image_viewer = QWidget(self.centralwidget)
        self.image_viewer.setObjectName(u"image_viewer")

        self.horizontalLayout.addWidget(self.image_viewer)

        self.table_replace = QTableWidget(self.centralwidget)
        if (self.table_replace.columnCount() < 2):
            self.table_replace.setColumnCount(2)
        __qtablewidgetitem = QTableWidgetItem()
        self.table_replace.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.table_replace.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        if (self.table_replace.rowCount() < 1):
            self.table_replace.setRowCount(1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.table_replace.setVerticalHeaderItem(0, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.table_replace.setItem(0, 0, __qtablewidgetitem3)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.table_replace.setItem(0, 1, __qtablewidgetitem4)
        self.table_replace.setObjectName(u"table_replace")

        self.horizontalLayout.addWidget(self.table_replace)

        self.table_scenes = QTableWidget(self.centralwidget)
        if (self.table_scenes.columnCount() < 4):
            self.table_scenes.setColumnCount(4)
        __qtablewidgetitem5 = QTableWidgetItem()
        self.table_scenes.setHorizontalHeaderItem(0, __qtablewidgetitem5)
        __qtablewidgetitem6 = QTableWidgetItem()
        self.table_scenes.setHorizontalHeaderItem(1, __qtablewidgetitem6)
        __qtablewidgetitem7 = QTableWidgetItem()
        self.table_scenes.setHorizontalHeaderItem(2, __qtablewidgetitem7)
        __qtablewidgetitem8 = QTableWidgetItem()
        self.table_scenes.setHorizontalHeaderItem(3, __qtablewidgetitem8)
        if (self.table_scenes.rowCount() < 1):
            self.table_scenes.setRowCount(1)
        __qtablewidgetitem9 = QTableWidgetItem()
        self.table_scenes.setVerticalHeaderItem(0, __qtablewidgetitem9)
        __qtablewidgetitem10 = QTableWidgetItem()
        self.table_scenes.setItem(0, 0, __qtablewidgetitem10)
        __qtablewidgetitem11 = QTableWidgetItem()
        self.table_scenes.setItem(0, 1, __qtablewidgetitem11)
        __qtablewidgetitem12 = QTableWidgetItem()
        self.table_scenes.setItem(0, 2, __qtablewidgetitem12)
        __qtablewidgetitem13 = QTableWidgetItem()
        self.table_scenes.setItem(0, 3, __qtablewidgetitem13)
        self.table_scenes.setObjectName(u"table_scenes")

        self.horizontalLayout.addWidget(self.table_scenes)

        self.setCentralWidget(self.centralwidget)
        self.controller: ReplaceController = None

    def set_controller(self, controller: ReplaceController) -> None:
        self.controller: ReplaceController = controller
