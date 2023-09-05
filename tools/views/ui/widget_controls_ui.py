# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_widget_controls.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

from views.widget_custom_qslider import Widget_custom_qslider

class Ui_widget_controls(object):
    def setupUi(self, widget_controls):
        if not widget_controls.objectName():
            widget_controls.setObjectName(u"widget_controls")
        widget_controls.resize(762, 88)
        self.verticalLayout = QVBoxLayout(widget_controls)
        self.verticalLayout.setSpacing(3)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(6, 6, 6, 21)
        self.slider_frames = Widget_custom_qslider(widget_controls)
        self.slider_frames.setObjectName(u"slider_frames")
        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.slider_frames.sizePolicy().hasHeightForWidth())
        self.slider_frames.setSizePolicy(sizePolicy)
        self.slider_frames.setMinimumSize(QSize(750, 30))

        self.verticalLayout.addWidget(self.slider_frames)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setSpacing(12)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.pushButton_play_pause = QPushButton(widget_controls)
        self.pushButton_play_pause.setObjectName(u"pushButton_play_pause")
        self.pushButton_play_pause.setFocusPolicy(Qt.NoFocus)
        icon = QIcon()
        icon.addFile(u"./tools/icons/blue/play.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_play_pause.setIcon(icon)
        self.pushButton_play_pause.setCheckable(True)
        self.pushButton_play_pause.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_play_pause)

        self.pushButton_loop = QPushButton(widget_controls)
        self.pushButton_loop.setObjectName(u"pushButton_loop")
        self.pushButton_loop.setFocusPolicy(Qt.NoFocus)
        icon1 = QIcon()
        icon1.addFile(u"./tools/icons/grey/repeat.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon1.addFile(u"./tools/icons/blue/repeat.svg", QSize(), QIcon.Normal, QIcon.On)
        self.pushButton_loop.setIcon(icon1)
        self.pushButton_loop.setCheckable(True)
        self.pushButton_loop.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_loop)


        self.horizontalLayout_3.addLayout(self.horizontalLayout)

        self.label_ed_ep_part = QLabel(widget_controls)
        self.label_ed_ep_part.setObjectName(u"label_ed_ep_part")
        self.label_ed_ep_part.setMinimumSize(QSize(170, 0))
        self.label_ed_ep_part.setMaximumSize(QSize(180, 16777215))
        self.label_ed_ep_part.setFrameShape(QFrame.Panel)
        self.label_ed_ep_part.setFrameShadow(QFrame.Plain)
        self.label_ed_ep_part.setLineWidth(1)

        self.horizontalLayout_3.addWidget(self.label_ed_ep_part)

        self.horizontalSpacer_2 = QSpacerItem(10, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_2)

        self.lineEdit_frame_no = QLineEdit(widget_controls)
        self.lineEdit_frame_no.setObjectName(u"lineEdit_frame_no")
        sizePolicy1 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.lineEdit_frame_no.sizePolicy().hasHeightForWidth())
        self.lineEdit_frame_no.setSizePolicy(sizePolicy1)
        self.lineEdit_frame_no.setMinimumSize(QSize(55, 0))
        self.lineEdit_frame_no.setMaximumSize(QSize(60, 16777215))
        self.lineEdit_frame_no.setFocusPolicy(Qt.NoFocus)
        self.lineEdit_frame_no.setFrame(False)
        self.lineEdit_frame_no.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.lineEdit_frame_no.setReadOnly(True)

        self.horizontalLayout_3.addWidget(self.lineEdit_frame_no)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer)

        self.lineEdit_frame_index = QLineEdit(widget_controls)
        self.lineEdit_frame_index.setObjectName(u"lineEdit_frame_index")
        sizePolicy1.setHeightForWidth(self.lineEdit_frame_index.sizePolicy().hasHeightForWidth())
        self.lineEdit_frame_index.setSizePolicy(sizePolicy1)
        self.lineEdit_frame_index.setMinimumSize(QSize(55, 0))
        self.lineEdit_frame_index.setMaximumSize(QSize(60, 16777215))
        self.lineEdit_frame_index.setFocusPolicy(Qt.NoFocus)
        self.lineEdit_frame_index.setFrame(False)
        self.lineEdit_frame_index.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.lineEdit_frame_index.setReadOnly(True)

        self.horizontalLayout_3.addWidget(self.lineEdit_frame_index)


        self.verticalLayout.addLayout(self.horizontalLayout_3)


        self.retranslateUi(widget_controls)

        QMetaObject.connectSlotsByName(widget_controls)
    # setupUi

    def retranslateUi(self, widget_controls):
        widget_controls.setWindowTitle(QCoreApplication.translate("widget_controls", u"Form", None))
        self.pushButton_play_pause.setText("")
        self.pushButton_loop.setText("")
        self.label_ed_ep_part.setText(QCoreApplication.translate("widget_controls", u"s:ep11:g_documentaire:999", None))
        self.lineEdit_frame_no.setText(QCoreApplication.translate("widget_controls", u"123456", None))
        self.lineEdit_frame_index.setText(QCoreApplication.translate("widget_controls", u"123456", None))
    # retranslateUi

