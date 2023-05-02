# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_widget_color_balance.ui'
##
## Created by: Qt User Interface Compiler version 6.5.0
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
from PySide6.QtWidgets import (QApplication, QGridLayout, QLabel, QSizePolicy,
    QSlider, QSpinBox, QWidget)

class Ui_widget_color_balance(object):
    def setupUi(self, widget_color_balance):
        if not widget_color_balance.objectName():
            widget_color_balance.setObjectName(u"widget_color_balance")
        widget_color_balance.resize(244, 132)
        self.gridLayout = QGridLayout(widget_color_balance)
        self.gridLayout.setObjectName(u"gridLayout")
        self.slider_red = QSlider(widget_color_balance)
        self.slider_red.setObjectName(u"slider_red")
        self.slider_red.setFocusPolicy(Qt.WheelFocus)
        self.slider_red.setMinimum(-127)
        self.slider_red.setMaximum(127)
        self.slider_red.setOrientation(Qt.Horizontal)
        self.slider_red.setTickPosition(QSlider.TicksBelow)
        self.slider_red.setTickInterval(32)

        self.gridLayout.addWidget(self.slider_red, 0, 1, 1, 1)

        self.label_red = QLabel(widget_color_balance)
        self.label_red.setObjectName(u"label_red")
        self.label_red.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)

        self.gridLayout.addWidget(self.label_red, 0, 3, 1, 1)

        self.label_blue = QLabel(widget_color_balance)
        self.label_blue.setObjectName(u"label_blue")
        self.label_blue.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)

        self.gridLayout.addWidget(self.label_blue, 2, 3, 1, 1)

        self.slider_green = QSlider(widget_color_balance)
        self.slider_green.setObjectName(u"slider_green")
        self.slider_green.setFocusPolicy(Qt.WheelFocus)
        self.slider_green.setMinimum(-127)
        self.slider_green.setMaximum(127)
        self.slider_green.setTracking(True)
        self.slider_green.setOrientation(Qt.Horizontal)
        self.slider_green.setTickPosition(QSlider.TicksBelow)
        self.slider_green.setTickInterval(32)

        self.gridLayout.addWidget(self.slider_green, 1, 1, 1, 1)

        self.label_green = QLabel(widget_color_balance)
        self.label_green.setObjectName(u"label_green")
        self.label_green.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)

        self.gridLayout.addWidget(self.label_green, 1, 3, 1, 1)

        self.slider_blue = QSlider(widget_color_balance)
        self.slider_blue.setObjectName(u"slider_blue")
        self.slider_blue.setFocusPolicy(Qt.WheelFocus)
        self.slider_blue.setMinimum(-127)
        self.slider_blue.setMaximum(127)
        self.slider_blue.setTracking(True)
        self.slider_blue.setOrientation(Qt.Horizontal)
        self.slider_blue.setTickPosition(QSlider.TicksBelow)
        self.slider_blue.setTickInterval(32)

        self.gridLayout.addWidget(self.slider_blue, 2, 1, 1, 1)

        self.label_luminance = QLabel(widget_color_balance)
        self.label_luminance.setObjectName(u"label_luminance")
        self.label_luminance.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)

        self.gridLayout.addWidget(self.label_luminance, 3, 3, 1, 1)

        self.slider_luminance = QSlider(widget_color_balance)
        self.slider_luminance.setObjectName(u"slider_luminance")
        self.slider_luminance.setFocusPolicy(Qt.WheelFocus)
        self.slider_luminance.setMinimum(-127)
        self.slider_luminance.setMaximum(127)
        self.slider_luminance.setTracking(True)
        self.slider_luminance.setOrientation(Qt.Horizontal)
        self.slider_luminance.setTickPosition(QSlider.TicksBelow)
        self.slider_luminance.setTickInterval(32)

        self.gridLayout.addWidget(self.slider_luminance, 3, 1, 1, 1)

        self.spinBox_red = QSpinBox(widget_color_balance)
        self.spinBox_red.setObjectName(u"spinBox_red")
        self.spinBox_red.setFrame(True)
        self.spinBox_red.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
        self.spinBox_red.setMinimum(-127)
        self.spinBox_red.setMaximum(127)

        self.gridLayout.addWidget(self.spinBox_red, 0, 0, 1, 1)

        self.spinBox_green = QSpinBox(widget_color_balance)
        self.spinBox_green.setObjectName(u"spinBox_green")
        self.spinBox_green.setFrame(True)
        self.spinBox_green.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
        self.spinBox_green.setMinimum(-127)
        self.spinBox_green.setMaximum(127)

        self.gridLayout.addWidget(self.spinBox_green, 1, 0, 1, 1)

        self.spinBox_blue = QSpinBox(widget_color_balance)
        self.spinBox_blue.setObjectName(u"spinBox_blue")
        self.spinBox_blue.setFrame(True)
        self.spinBox_blue.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
        self.spinBox_blue.setMinimum(-127)
        self.spinBox_blue.setMaximum(127)

        self.gridLayout.addWidget(self.spinBox_blue, 2, 0, 1, 1)

        self.spinBox_luminance = QSpinBox(widget_color_balance)
        self.spinBox_luminance.setObjectName(u"spinBox_luminance")
        self.spinBox_luminance.setFrame(True)
        self.spinBox_luminance.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
        self.spinBox_luminance.setMinimum(-127)
        self.spinBox_luminance.setMaximum(127)

        self.gridLayout.addWidget(self.spinBox_luminance, 3, 0, 1, 1)


        self.retranslateUi(widget_color_balance)

        QMetaObject.connectSlotsByName(widget_color_balance)
    # setupUi

    def retranslateUi(self, widget_color_balance):
        widget_color_balance.setWindowTitle(QCoreApplication.translate("widget_color_balance", u"Form", None))
        self.label_red.setText(QCoreApplication.translate("widget_color_balance", u"R", None))
        self.label_blue.setText(QCoreApplication.translate("widget_color_balance", u"B", None))
        self.label_green.setText(QCoreApplication.translate("widget_color_balance", u"G", None))
        self.label_luminance.setText(QCoreApplication.translate("widget_color_balance", u"Luminance", None))
    # retranslateUi

