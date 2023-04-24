# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_widget_controls.ui'
##
## Created by: Qt User Interface Compiler version 6.4.2
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
from PySide6.QtWidgets import (QAbstractSpinBox, QApplication, QDoubleSpinBox, QFrame,
    QHBoxLayout, QLabel, QLayout, QLineEdit,
    QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

from ui.widget_custom_qslider import Widget_custom_qslider

class Ui_widget_controls(object):
    def setupUi(self, widget_controls):
        if not widget_controls.objectName():
            widget_controls.setObjectName(u"widget_controls")
        self.verticalLayout = QVBoxLayout(widget_controls)
        self.verticalLayout.setSpacing(3)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(6, 6, 6, 21)
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(4)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setSizeConstraint(QLayout.SetMaximumSize)
        self.horizontalLayout_2.setContentsMargins(-1, -1, -1, 0)
        self.slider_frames = Widget_custom_qslider(widget_controls)
        self.slider_frames.setObjectName(u"slider_frames")
        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.slider_frames.sizePolicy().hasHeightForWidth())
        self.slider_frames.setSizePolicy(sizePolicy)
        self.slider_frames.setMinimumSize(QSize(750, 30))

        self.horizontalLayout_2.addWidget(self.slider_frames)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.spinBox_speed = QDoubleSpinBox(widget_controls)
        self.spinBox_speed.setObjectName(u"spinBox_speed")
        sizePolicy1 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.spinBox_speed.sizePolicy().hasHeightForWidth())
        self.spinBox_speed.setSizePolicy(sizePolicy1)
        self.spinBox_speed.setWrapping(False)
        self.spinBox_speed.setFrame(True)
        self.spinBox_speed.setAlignment(Qt.AlignCenter)
        self.spinBox_speed.setReadOnly(False)
        self.spinBox_speed.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
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
        icon.addFile(u"tools/icons/blue/play.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_play_pause.setIcon(icon)
        self.pushButton_play_pause.setCheckable(True)
        self.pushButton_play_pause.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_play_pause)


        self.horizontalLayout_2.addLayout(self.horizontalLayout)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label_ed_ep_part = QLabel(widget_controls)
        self.label_ed_ep_part.setObjectName(u"label_ed_ep_part")
        self.label_ed_ep_part.setMinimumSize(QSize(140, 0))
        self.label_ed_ep_part.setMaximumSize(QSize(140, 16777215))
        self.label_ed_ep_part.setFrameShape(QFrame.Panel)
        self.label_ed_ep_part.setFrameShadow(QFrame.Plain)
        self.label_ed_ep_part.setLineWidth(1)

        self.horizontalLayout_3.addWidget(self.label_ed_ep_part)

        self.label_shot_no = QLabel(widget_controls)
        self.label_shot_no.setObjectName(u"label_shot_no")
        self.label_shot_no.setMinimumSize(QSize(40, 0))
        self.label_shot_no.setMaximumSize(QSize(40, 16777215))
        self.label_shot_no.setStyleSheet(u"gridline-color: rgb(38, 162, 105);\n"
"border-color: rgb(145, 65, 172);")
        self.label_shot_no.setFrameShape(QFrame.Panel)

        self.horizontalLayout_3.addWidget(self.label_shot_no)

        self.horizontalSpacer_2 = QSpacerItem(10, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_2)

        self.lineEdit_frame_no = QLineEdit(widget_controls)
        self.lineEdit_frame_no.setObjectName(u"lineEdit_frame_no")
        sizePolicy1.setHeightForWidth(self.lineEdit_frame_no.sizePolicy().hasHeightForWidth())
        self.lineEdit_frame_no.setSizePolicy(sizePolicy1)
        self.lineEdit_frame_no.setMinimumSize(QSize(55, 0))
        self.lineEdit_frame_no.setMaximumSize(QSize(60, 16777215))
        self.lineEdit_frame_no.setFrame(False)
        self.lineEdit_frame_no.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.lineEdit_frame_no.setReadOnly(True)

        self.horizontalLayout_3.addWidget(self.lineEdit_frame_no)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer)


        self.verticalLayout.addLayout(self.horizontalLayout_3)


        self.retranslateUi(widget_controls)

        QMetaObject.connectSlotsByName(widget_controls)
    # setupUi

    def retranslateUi(self, widget_controls):
        widget_controls.setWindowTitle(QCoreApplication.translate("widget_controls", u"Form", None))
        self.pushButton_play_pause.setText("")
        self.label_ed_ep_part.setText(QCoreApplication.translate("widget_controls", u"s:ep11:g_reportage", None))
        self.label_shot_no.setText(QCoreApplication.translate("widget_controls", u"130", None))
        self.lineEdit_frame_no.setText(QCoreApplication.translate("widget_controls", u"123456", None))
    # retranslateUi

