# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_widget_player_ctrl.ui'
##
## Created by: Qt User Interface Compiler version 6.6.0
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

from ui.widget_custom_qslider import CustomQSliderWidget

class Ui_PlayerControlWidget(object):
    def setupUi(self, PlayerControlWidget):
        if not PlayerControlWidget.objectName():
            PlayerControlWidget.setObjectName(u"PlayerControlWidget")
        PlayerControlWidget.resize(840, 79)
        self.verticalLayout = QVBoxLayout(PlayerControlWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.slider_frames = CustomQSliderWidget(PlayerControlWidget)
        self.slider_frames.setObjectName(u"slider_frames")
        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.slider_frames.sizePolicy().hasHeightForWidth())
        self.slider_frames.setSizePolicy(sizePolicy)
        self.slider_frames.setMinimumSize(QSize(750, 30))

        self.horizontalLayout_4.addWidget(self.slider_frames)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.pushButton_play_pause = QPushButton(PlayerControlWidget)
        self.pushButton_play_pause.setObjectName(u"pushButton_play_pause")
        self.pushButton_play_pause.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        icon = QIcon()
        icon.addFile(u"./icons/blue/play.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_play_pause.setIcon(icon)
        self.pushButton_play_pause.setCheckable(True)
        self.pushButton_play_pause.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_play_pause)

        self.pushButton_loop = QPushButton(PlayerControlWidget)
        self.pushButton_loop.setObjectName(u"pushButton_loop")
        self.pushButton_loop.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        icon1 = QIcon()
        icon1.addFile(u"./icons/grey/repeat.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon1.addFile(u"./icons/blue/repeat.svg", QSize(), QIcon.Normal, QIcon.On)
        self.pushButton_loop.setIcon(icon1)
        self.pushButton_loop.setCheckable(True)
        self.pushButton_loop.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_loop)


        self.horizontalLayout_4.addLayout(self.horizontalLayout)


        self.verticalLayout.addLayout(self.horizontalLayout_4)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setSpacing(12)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label_ed_ep_part = QLabel(PlayerControlWidget)
        self.label_ed_ep_part.setObjectName(u"label_ed_ep_part")
        self.label_ed_ep_part.setMinimumSize(QSize(170, 0))
        self.label_ed_ep_part.setMaximumSize(QSize(180, 16777215))
        self.label_ed_ep_part.setFrameShape(QFrame.Shape.Panel)
        self.label_ed_ep_part.setFrameShadow(QFrame.Shadow.Plain)
        self.label_ed_ep_part.setLineWidth(1)

        self.horizontalLayout_3.addWidget(self.label_ed_ep_part)

        self.horizontalSpacer_2 = QSpacerItem(10, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_2)

        self.lineEdit_frame_no = QLineEdit(PlayerControlWidget)
        self.lineEdit_frame_no.setObjectName(u"lineEdit_frame_no")
        sizePolicy1 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.lineEdit_frame_no.sizePolicy().hasHeightForWidth())
        self.lineEdit_frame_no.setSizePolicy(sizePolicy1)
        self.lineEdit_frame_no.setMinimumSize(QSize(55, 0))
        self.lineEdit_frame_no.setMaximumSize(QSize(60, 16777215))
        self.lineEdit_frame_no.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.lineEdit_frame_no.setFrame(False)
        self.lineEdit_frame_no.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.lineEdit_frame_no.setReadOnly(True)

        self.horizontalLayout_3.addWidget(self.lineEdit_frame_no)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer)

        self.lineEdit_frame_index = QLineEdit(PlayerControlWidget)
        self.lineEdit_frame_index.setObjectName(u"lineEdit_frame_index")
        sizePolicy1.setHeightForWidth(self.lineEdit_frame_index.sizePolicy().hasHeightForWidth())
        self.lineEdit_frame_index.setSizePolicy(sizePolicy1)
        self.lineEdit_frame_index.setMinimumSize(QSize(55, 0))
        self.lineEdit_frame_index.setMaximumSize(QSize(60, 16777215))
        self.lineEdit_frame_index.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.lineEdit_frame_index.setFrame(False)
        self.lineEdit_frame_index.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.lineEdit_frame_index.setReadOnly(True)

        self.horizontalLayout_3.addWidget(self.lineEdit_frame_index)


        self.verticalLayout.addLayout(self.horizontalLayout_3)


        self.retranslateUi(PlayerControlWidget)

        QMetaObject.connectSlotsByName(PlayerControlWidget)
    # setupUi

    def retranslateUi(self, PlayerControlWidget):
        PlayerControlWidget.setWindowTitle(QCoreApplication.translate("PlayerControlWidget", u"Form", None))
        self.pushButton_play_pause.setText("")
        self.pushButton_loop.setText("")
        self.label_ed_ep_part.setText(QCoreApplication.translate("PlayerControlWidget", u"s:ep11:g_documentaire:999", None))
        self.lineEdit_frame_no.setText(QCoreApplication.translate("PlayerControlWidget", u"123456", None))
        self.lineEdit_frame_index.setText(QCoreApplication.translate("PlayerControlWidget", u"123456", None))
    # retranslateUi

