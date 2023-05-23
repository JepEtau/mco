# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_widget_stabilize.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QGroupBox, QHBoxLayout,
    QLabel, QLayout, QLineEdit, QPushButton,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

from views.widget_segments import Widget_segments

class Ui_widget_stabilize(object):
    def setupUi(self, widget_stabilize):
        if not widget_stabilize.objectName():
            widget_stabilize.setObjectName(u"widget_stabilize")
        widget_stabilize.resize(715, 172)
        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(widget_stabilize.sizePolicy().hasHeightForWidth())
        widget_stabilize.setSizePolicy(sizePolicy)
        self.mainLayout = QVBoxLayout(widget_stabilize)
        self.mainLayout.setSpacing(0)
        self.mainLayout.setObjectName(u"mainLayout")
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.frame = QFrame(widget_stabilize)
        self.frame.setObjectName(u"frame")
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
        self.frame.setSizePolicy(sizePolicy1)
        self.frame.setFrameShape(QFrame.Panel)
        self.frame.setFrameShadow(QFrame.Plain)
        self.verticalLayout_2 = QVBoxLayout(self.frame)
        self.verticalLayout_2.setSpacing(4)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(6, 6, 6, 6)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(3)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setSizeConstraint(QLayout.SetMaximumSize)
        self.pushButton_set_preview = QPushButton(self.frame)
        self.pushButton_set_preview.setObjectName(u"pushButton_set_preview")
        sizePolicy2 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.pushButton_set_preview.sizePolicy().hasHeightForWidth())
        self.pushButton_set_preview.setSizePolicy(sizePolicy2)
        self.pushButton_set_preview.setFocusPolicy(Qt.NoFocus)
        icon = QIcon()
        icon.addFile(u"tools/icons/grey/eye.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon.addFile(u"tools/icons/blue/eye.svg", QSize(), QIcon.Normal, QIcon.On)
        icon.addFile(u"tools/icons/grey/eye.svg", QSize(), QIcon.Disabled, QIcon.Off)
        icon.addFile(u"tools/icons/grey/eye.svg", QSize(), QIcon.Disabled, QIcon.On)
        self.pushButton_set_preview.setIcon(icon)
        self.pushButton_set_preview.setCheckable(True)
        self.pushButton_set_preview.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_set_preview)

        self.pushButton_stabilize = QPushButton(self.frame)
        self.pushButton_stabilize.setObjectName(u"pushButton_stabilize")
        sizePolicy2.setHeightForWidth(self.pushButton_stabilize.sizePolicy().hasHeightForWidth())
        self.pushButton_stabilize.setSizePolicy(sizePolicy2)
        self.pushButton_stabilize.setFocusPolicy(Qt.NoFocus)
        icon1 = QIcon()
        icon1.addFile(u"tools/icons/purple/refresh-cw.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon1.addFile(u"tools/icons/purple/refresh-cw.svg", QSize(), QIcon.Normal, QIcon.On)
        icon1.addFile(u"tools/icons/grey/refresh-cw.svg", QSize(), QIcon.Disabled, QIcon.Off)
        icon1.addFile(u"tools/icons/grey/refresh-cw.svg", QSize(), QIcon.Disabled, QIcon.On)
        self.pushButton_stabilize.setIcon(icon1)
        self.pushButton_stabilize.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_stabilize)

        self.pushButton_guidelines = QPushButton(self.frame)
        self.pushButton_guidelines.setObjectName(u"pushButton_guidelines")
        sizePolicy2.setHeightForWidth(self.pushButton_guidelines.sizePolicy().hasHeightForWidth())
        self.pushButton_guidelines.setSizePolicy(sizePolicy2)
        self.pushButton_guidelines.setFocusPolicy(Qt.NoFocus)
        icon2 = QIcon()
        icon2.addFile(u"tools/icons/grey/frame.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon2.addFile(u"tools/icons/blue/frame.svg", QSize(), QIcon.Normal, QIcon.On)
        self.pushButton_guidelines.setIcon(icon2)
        self.pushButton_guidelines.setCheckable(True)
        self.pushButton_guidelines.setAutoDefault(False)
        self.pushButton_guidelines.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_guidelines)

        self.horizontalSpacer = QSpacerItem(5, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.label_message = QLabel(self.frame)
        self.label_message.setObjectName(u"label_message")
        sizePolicy3 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.label_message.sizePolicy().hasHeightForWidth())
        self.label_message.setSizePolicy(sizePolicy3)

        self.horizontalLayout.addWidget(self.label_message)

        self.horizontalSpacer_8 = QSpacerItem(5, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_8)

        self.pushButton_discard = QPushButton(self.frame)
        self.pushButton_discard.setObjectName(u"pushButton_discard")
        sizePolicy2.setHeightForWidth(self.pushButton_discard.sizePolicy().hasHeightForWidth())
        self.pushButton_discard.setSizePolicy(sizePolicy2)
        self.pushButton_discard.setFocusPolicy(Qt.NoFocus)
        icon3 = QIcon()
        icon3.addFile(u"tools/icons/purple/undo.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_discard.setIcon(icon3)
        self.pushButton_discard.setCheckable(False)
        self.pushButton_discard.setAutoDefault(False)
        self.pushButton_discard.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_discard)

        self.pushButton_save = QPushButton(self.frame)
        self.pushButton_save.setObjectName(u"pushButton_save")
        sizePolicy2.setHeightForWidth(self.pushButton_save.sizePolicy().hasHeightForWidth())
        self.pushButton_save.setSizePolicy(sizePolicy2)
        self.pushButton_save.setFocusPolicy(Qt.NoFocus)
        icon4 = QIcon()
        icon4.addFile(u"tools/icons/purple/save.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_save.setIcon(icon4)
        self.pushButton_save.setCheckable(False)
        self.pushButton_save.setAutoDefault(False)
        self.pushButton_save.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_save)

        self.pushButton_close = QPushButton(self.frame)
        self.pushButton_close.setObjectName(u"pushButton_close")
        sizePolicy2.setHeightForWidth(self.pushButton_close.sizePolicy().hasHeightForWidth())
        self.pushButton_close.setSizePolicy(sizePolicy2)
        self.pushButton_close.setFocusPolicy(Qt.NoFocus)
        icon5 = QIcon()
        icon5.addFile(u"tools/icons/grey/x-square.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon5.addFile(u"tools/icons/purple/x-square.svg", QSize(), QIcon.Normal, QIcon.On)
        self.pushButton_close.setIcon(icon5)
        self.pushButton_close.setCheckable(False)
        self.pushButton_close.setAutoDefault(False)
        self.pushButton_close.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_close)


        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.groupBox_stabilize = QGroupBox(self.frame)
        self.groupBox_stabilize.setObjectName(u"groupBox_stabilize")
        self.groupBox_stabilize.setFocusPolicy(Qt.NoFocus)
        self.groupBox_stabilize.setCheckable(True)
        self.horizontalLayout_2 = QHBoxLayout(self.groupBox_stabilize)
        self.horizontalLayout_2.setSpacing(3)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(9, 12, 3, 3)
        self.widget_segments = Widget_segments(self.groupBox_stabilize)
        self.widget_segments.setObjectName(u"widget_segments")
        self.widget_segments.setMinimumSize(QSize(650, 0))

        self.horizontalLayout_2.addWidget(self.widget_segments)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.pushButton_show_tracker = QPushButton(self.groupBox_stabilize)
        self.pushButton_show_tracker.setObjectName(u"pushButton_show_tracker")
        sizePolicy2.setHeightForWidth(self.pushButton_show_tracker.sizePolicy().hasHeightForWidth())
        self.pushButton_show_tracker.setSizePolicy(sizePolicy2)
        self.pushButton_show_tracker.setFocusPolicy(Qt.NoFocus)
        icon6 = QIcon()
        icon6.addFile(u"./tools/icons/grey/box-select.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon6.addFile(u"./tools/icons/blue/box-select.svg", QSize(), QIcon.Normal, QIcon.On)
        self.pushButton_show_tracker.setIcon(icon6)
        self.pushButton_show_tracker.setCheckable(True)
        self.pushButton_show_tracker.setFlat(True)

        self.verticalLayout_3.addWidget(self.pushButton_show_tracker)

        self.verticalSpacer = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer)

        self.pushButton_roi_remove = QPushButton(self.groupBox_stabilize)
        self.pushButton_roi_remove.setObjectName(u"pushButton_roi_remove")
        sizePolicy2.setHeightForWidth(self.pushButton_roi_remove.sizePolicy().hasHeightForWidth())
        self.pushButton_roi_remove.setSizePolicy(sizePolicy2)
        self.pushButton_roi_remove.setFocusPolicy(Qt.NoFocus)
        icon7 = QIcon()
        icon7.addFile(u"./tools/icons/blue/eraser.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_roi_remove.setIcon(icon7)
        self.pushButton_roi_remove.setCheckable(False)
        self.pushButton_roi_remove.setFlat(True)

        self.verticalLayout_3.addWidget(self.pushButton_roi_remove)


        self.horizontalLayout_2.addLayout(self.verticalLayout_3)


        self.verticalLayout_2.addWidget(self.groupBox_stabilize)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.lineEdit_coordinates = QLineEdit(self.frame)
        self.lineEdit_coordinates.setObjectName(u"lineEdit_coordinates")
        self.lineEdit_coordinates.setMaximumSize(QSize(100, 16777215))
        self.lineEdit_coordinates.setFocusPolicy(Qt.NoFocus)
        self.lineEdit_coordinates.setFrame(False)
        self.lineEdit_coordinates.setAlignment(Qt.AlignCenter)
        self.lineEdit_coordinates.setReadOnly(True)
        self.lineEdit_coordinates.setClearButtonEnabled(False)

        self.horizontalLayout_3.addWidget(self.lineEdit_coordinates)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_2)


        self.verticalLayout_2.addLayout(self.horizontalLayout_3)


        self.mainLayout.addWidget(self.frame)


        self.retranslateUi(widget_stabilize)

        QMetaObject.connectSlotsByName(widget_stabilize)
    # setupUi

    def retranslateUi(self, widget_stabilize):
        self.pushButton_set_preview.setText("")
        self.pushButton_stabilize.setText("")
        self.pushButton_guidelines.setText("")
        self.label_message.setText(QCoreApplication.translate("widget_stabilize", u"error", None))
        self.pushButton_discard.setText("")
        self.pushButton_save.setText("")
        self.pushButton_close.setText("")
        self.groupBox_stabilize.setTitle(QCoreApplication.translate("widget_stabilize", u"Stabilize/deshake", None))
        self.pushButton_show_tracker.setText("")
        self.pushButton_roi_remove.setText("")
        self.lineEdit_coordinates.setText(QCoreApplication.translate("widget_stabilize", u"(1200, 1400)", None))
        pass
    # retranslateUi

