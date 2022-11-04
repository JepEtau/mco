# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_widget_app_controls.ui'
##
## Created by: Qt User Interface Compiler version 6.4.0
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QPushButton, QSizePolicy,
    QSpacerItem, QWidget)

class Ui_widget_app_controls(object):
    def setupUi(self, widget_app_controls):
        if not widget_app_controls.objectName():
            widget_app_controls.setObjectName(u"widget_app_controls")
        widget_app_controls.resize(193, 24)
        self.horizontalLayout = QHBoxLayout(widget_app_controls)
        self.horizontalLayout.setSpacing(3)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.pushButton_save_modifications = QPushButton(widget_app_controls)
        self.pushButton_save_modifications.setObjectName(u"pushButton_save_modifications")
        sizePolicy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton_save_modifications.sizePolicy().hasHeightForWidth())
        self.pushButton_save_modifications.setSizePolicy(sizePolicy)
        icon = QIcon()
        icon.addFile(u"icons/grey/save.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon.addFile(u"icons/purple/save.svg", QSize(), QIcon.Normal, QIcon.On)
        self.pushButton_save_modifications.setIcon(icon)
        self.pushButton_save_modifications.setCheckable(False)
        self.pushButton_save_modifications.setAutoDefault(False)
        self.pushButton_save_modifications.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_save_modifications)

        self.pushButton_discard_modifications = QPushButton(widget_app_controls)
        self.pushButton_discard_modifications.setObjectName(u"pushButton_discard_modifications")
        sizePolicy.setHeightForWidth(self.pushButton_discard_modifications.sizePolicy().hasHeightForWidth())
        self.pushButton_discard_modifications.setSizePolicy(sizePolicy)
        icon1 = QIcon()
        icon1.addFile(u"icons/grey/undo.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon1.addFile(u"icons/purple/undo.svg", QSize(), QIcon.Normal, QIcon.On)
        self.pushButton_discard_modifications.setIcon(icon1)
        self.pushButton_discard_modifications.setCheckable(False)
        self.pushButton_discard_modifications.setAutoDefault(False)
        self.pushButton_discard_modifications.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_discard_modifications)

        self.horizontalSpacer = QSpacerItem(5, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.pushButton_minimize = QPushButton(widget_app_controls)
        self.pushButton_minimize.setObjectName(u"pushButton_minimize")
        icon2 = QIcon()
        icon2.addFile(u"icons/purple/minus-square.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon2.addFile(u"icons/purple/minus-square.svg", QSize(), QIcon.Normal, QIcon.On)
        self.pushButton_minimize.setIcon(icon2)
        self.pushButton_minimize.setCheckable(False)
        self.pushButton_minimize.setAutoDefault(False)
        self.pushButton_minimize.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_minimize)

        self.pushButton_exit = QPushButton(widget_app_controls)
        self.pushButton_exit.setObjectName(u"pushButton_exit")
        sizePolicy.setHeightForWidth(self.pushButton_exit.sizePolicy().hasHeightForWidth())
        self.pushButton_exit.setSizePolicy(sizePolicy)
        icon3 = QIcon()
        icon3.addFile(u"icons/purple/x-square.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon3.addFile(u"icons/purple/x-square.svg", QSize(), QIcon.Normal, QIcon.On)
        self.pushButton_exit.setIcon(icon3)
        self.pushButton_exit.setCheckable(False)
        self.pushButton_exit.setAutoDefault(False)
        self.pushButton_exit.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_exit)


        self.retranslateUi(widget_app_controls)

        QMetaObject.connectSlotsByName(widget_app_controls)
    # setupUi

    def retranslateUi(self, widget_app_controls):
        widget_app_controls.setWindowTitle(QCoreApplication.translate("widget_app_controls", u"Form", None))
        self.pushButton_save_modifications.setText("")
        self.pushButton_discard_modifications.setText("")
        self.pushButton_minimize.setText("")
        self.pushButton_exit.setText("")
    # retranslateUi

