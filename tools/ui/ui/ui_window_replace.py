# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_window_replace.ui'
##
## Created by: Qt User Interface Compiler version 6.7.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QMainWindow, QSizePolicy,
    QVBoxLayout, QWidget)

from ui.widget_player_ctrl import PlayerCtrlWidget
from ui.widget_preview import PreviewWidget
from ui.widget_replace import ReplaceWidget
from ui.widget_selection import SelectionWidget

class Ui_ReplaceWindow(object):
    def setupUi(self, ReplaceWindow):
        if not ReplaceWindow.objectName():
            ReplaceWindow.setObjectName(u"ReplaceWindow")
        ReplaceWindow.resize(501, 284)
        self.centralwidget = QWidget(ReplaceWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout_2 = QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.widget_preview = PreviewWidget(self.centralwidget)
        self.widget_preview.setObjectName(u"widget_preview")

        self.verticalLayout.addWidget(self.widget_preview)

        self.widget_player_ctrl = PlayerCtrlWidget(self.centralwidget)
        self.widget_player_ctrl.setObjectName(u"widget_player_ctrl")

        self.verticalLayout.addWidget(self.widget_player_ctrl)


        self.horizontalLayout.addLayout(self.verticalLayout)

        self.widget_replace = ReplaceWidget(self.centralwidget)
        self.widget_replace.setObjectName(u"widget_replace")

        self.horizontalLayout.addWidget(self.widget_replace)

        self.widget_selection = SelectionWidget(self.centralwidget)
        self.widget_selection.setObjectName(u"widget_selection")

        self.horizontalLayout.addWidget(self.widget_selection)


        self.verticalLayout_2.addLayout(self.horizontalLayout)

        ReplaceWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(ReplaceWindow)

        QMetaObject.connectSlotsByName(ReplaceWindow)
    # setupUi

    def retranslateUi(self, ReplaceWindow):
        ReplaceWindow.setWindowTitle(QCoreApplication.translate("ReplaceWindow", u"MainWindow", None))
    # retranslateUi

