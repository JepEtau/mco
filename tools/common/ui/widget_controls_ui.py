# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_widget_controls.ui'
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
from PySide6.QtWidgets import (QApplication, QDoubleSpinBox, QHBoxLayout, QLayout,
    QLineEdit, QPushButton, QSizePolicy, QVBoxLayout,
    QWidget)

from common.widget_custom_qslider import Widget_custom_qslider

class Ui_widget_controls(object):
    def setupUi(self, widget_controls):
        if not widget_controls.objectName():
            widget_controls.setObjectName(u"widget_controls")
        widget_controls.resize(959, 40)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(widget_controls.sizePolicy().hasHeightForWidth())
        widget_controls.setSizePolicy(sizePolicy)
        widget_controls.setMaximumSize(QSize(16777215, 40))
        self.horizontalLayout_6 = QHBoxLayout(widget_controls)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setSizeConstraint(QLayout.SetMaximumSize)
        self.horizontalLayout_2.setContentsMargins(-1, -1, -1, 0)
        self.lineEdit_frame_no = QLineEdit(widget_controls)
        self.lineEdit_frame_no.setObjectName(u"lineEdit_frame_no")
        sizePolicy1 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.lineEdit_frame_no.sizePolicy().hasHeightForWidth())
        self.lineEdit_frame_no.setSizePolicy(sizePolicy1)
        self.lineEdit_frame_no.setMinimumSize(QSize(60, 0))
        self.lineEdit_frame_no.setMaximumSize(QSize(80, 16777215))
        self.lineEdit_frame_no.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.lineEdit_frame_no.setReadOnly(True)

        self.horizontalLayout_2.addWidget(self.lineEdit_frame_no)

        self.slider_frames = Widget_custom_qslider(widget_controls)
        self.slider_frames.setObjectName(u"slider_frames")
        sizePolicy2 = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Maximum)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.slider_frames.sizePolicy().hasHeightForWidth())
        self.slider_frames.setSizePolicy(sizePolicy2)
        self.slider_frames.setMinimumSize(QSize(750, 30))

        self.horizontalLayout_2.addWidget(self.slider_frames)


        self.horizontalLayout_6.addLayout(self.horizontalLayout_2)

        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setSpacing(0)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.spinBox_speed = QDoubleSpinBox(widget_controls)
        self.spinBox_speed.setObjectName(u"spinBox_speed")
        sizePolicy1.setHeightForWidth(self.spinBox_speed.sizePolicy().hasHeightForWidth())
        self.spinBox_speed.setSizePolicy(sizePolicy1)
        self.spinBox_speed.setWrapping(False)
        self.spinBox_speed.setFrame(True)
        self.spinBox_speed.setAlignment(Qt.AlignCenter)
        self.spinBox_speed.setKeyboardTracking(False)
        self.spinBox_speed.setDecimals(1)
        self.spinBox_speed.setMinimum(0.500000000000000)
        self.spinBox_speed.setMaximum(1.500000000000000)
        self.spinBox_speed.setSingleStep(0.500000000000000)
        self.spinBox_speed.setValue(1.000000000000000)

        self.horizontalLayout.addWidget(self.spinBox_speed)

        self.pushButton_play_pause = QPushButton(widget_controls)
        self.pushButton_play_pause.setObjectName(u"pushButton_play_pause")
        icon = QIcon()
        icon.addFile(u"img/blue/play.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_play_pause.setIcon(icon)
        self.pushButton_play_pause.setCheckable(True)
        self.pushButton_play_pause.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_play_pause)


        self.verticalLayout_4.addLayout(self.horizontalLayout)


        self.horizontalLayout_6.addLayout(self.verticalLayout_4)


        self.retranslateUi(widget_controls)

        QMetaObject.connectSlotsByName(widget_controls)
    # setupUi

    def retranslateUi(self, widget_controls):
        widget_controls.setWindowTitle(QCoreApplication.translate("widget_controls", u"Form", None))
        self.lineEdit_frame_no.setText(QCoreApplication.translate("widget_controls", u"123456", None))
        self.pushButton_play_pause.setText("")
    # retranslateUi

