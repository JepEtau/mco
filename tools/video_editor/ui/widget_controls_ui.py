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
    QLineEdit, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

from video_editor.widget_custom_qslider import Widget_custom_qslider

class Ui_widget_controls(object):
    def setupUi(self, widget_controls):
        if not widget_controls.objectName():
            widget_controls.setObjectName(u"widget_controls")
        widget_controls.resize(938, 61)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(widget_controls.sizePolicy().hasHeightForWidth())
        widget_controls.setSizePolicy(sizePolicy)
        self.horizontalLayout_6 = QHBoxLayout(widget_controls)
        self.horizontalLayout_6.setSpacing(3)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(3, 3, 9, 3)
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
        self.pushButton_play_pause = QPushButton(widget_controls)
        self.pushButton_play_pause.setObjectName(u"pushButton_play_pause")
        icon = QIcon()
        icon.addFile(u"img/play.png", QSize(), QIcon.Normal, QIcon.Off)
        icon.addFile(u"img/play.png", QSize(), QIcon.Selected, QIcon.Off)
        icon.addFile(u"img/pause.png", QSize(), QIcon.Selected, QIcon.On)
        self.pushButton_play_pause.setIcon(icon)
        self.pushButton_play_pause.setCheckable(True)
        self.pushButton_play_pause.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_play_pause)

        self.pushButton_previous_frame = QPushButton(widget_controls)
        self.pushButton_previous_frame.setObjectName(u"pushButton_previous_frame")
        icon1 = QIcon()
        icon1.addFile(u"img/go-first-view.png", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_previous_frame.setIcon(icon1)
        self.pushButton_previous_frame.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_previous_frame)

        self.pushButton_next_frame = QPushButton(widget_controls)
        self.pushButton_next_frame.setObjectName(u"pushButton_next_frame")
        icon2 = QIcon()
        icon2.addFile(u"img/go-last-view.png", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_next_frame.setIcon(icon2)
        self.pushButton_next_frame.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_next_frame)

        self.horizontalSpacer_3 = QSpacerItem(5, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_3)


        self.verticalLayout_4.addLayout(self.horizontalLayout)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.pushButton_stop = QPushButton(widget_controls)
        self.pushButton_stop.setObjectName(u"pushButton_stop")
        icon3 = QIcon()
        icon3.addFile(u"img/stop.png", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_stop.setIcon(icon3)
        self.pushButton_stop.setCheckable(False)
        self.pushButton_stop.setFlat(True)

        self.horizontalLayout_7.addWidget(self.pushButton_stop)

        self.horizontalSpacer_2 = QSpacerItem(10, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.horizontalLayout_7.addItem(self.horizontalSpacer_2)

        self.spinBox_speed = QDoubleSpinBox(widget_controls)
        self.spinBox_speed.setObjectName(u"spinBox_speed")
        self.spinBox_speed.setWrapping(False)
        self.spinBox_speed.setFrame(True)
        self.spinBox_speed.setAlignment(Qt.AlignCenter)
        self.spinBox_speed.setKeyboardTracking(False)
        self.spinBox_speed.setDecimals(1)
        self.spinBox_speed.setMinimum(0.500000000000000)
        self.spinBox_speed.setMaximum(1.500000000000000)
        self.spinBox_speed.setSingleStep(0.500000000000000)
        self.spinBox_speed.setValue(1.000000000000000)

        self.horizontalLayout_7.addWidget(self.spinBox_speed)


        self.verticalLayout_4.addLayout(self.horizontalLayout_7)

        self.verticalSpacer_4 = QSpacerItem(20, 1, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_4.addItem(self.verticalSpacer_4)


        self.horizontalLayout_6.addLayout(self.verticalLayout_4)


        self.retranslateUi(widget_controls)

        QMetaObject.connectSlotsByName(widget_controls)
    # setupUi

    def retranslateUi(self, widget_controls):
        widget_controls.setWindowTitle(QCoreApplication.translate("widget_controls", u"Form", None))
        self.lineEdit_frame_no.setText(QCoreApplication.translate("widget_controls", u"123456", None))
        self.pushButton_play_pause.setText("")
        self.pushButton_previous_frame.setText("")
        self.pushButton_next_frame.setText("")
        self.pushButton_stop.setText("")
    # retranslateUi

