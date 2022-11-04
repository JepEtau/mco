# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_widget_stabilize.ui'
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
from PySide6.QtWidgets import (QApplication, QDoubleSpinBox, QFrame, QGridLayout,
    QGroupBox, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QSpacerItem, QSpinBox, QVBoxLayout,
    QWidget)

class Ui_widget_stabilize(object):
    def setupUi(self, widget_stabilize):
        if not widget_stabilize.objectName():
            widget_stabilize.setObjectName(u"widget_stabilize")
        widget_stabilize.resize(177, 354)
        self.verticalLayout = QVBoxLayout(widget_stabilize)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.frame = QFrame(widget_stabilize)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.Panel)
        self.frame.setFrameShadow(QFrame.Plain)
        self.verticalLayout_2 = QVBoxLayout(self.frame)
        self.verticalLayout_2.setSpacing(4)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(6, 6, 6, 6)
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(3)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.pushButton_set_preview = QPushButton(self.frame)
        self.pushButton_set_preview.setObjectName(u"pushButton_set_preview")
        sizePolicy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton_set_preview.sizePolicy().hasHeightForWidth())
        self.pushButton_set_preview.setSizePolicy(sizePolicy)
        icon = QIcon()
        icon.addFile(u"icons/grey/eye.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon.addFile(u"icons/blue/eye.svg", QSize(), QIcon.Normal, QIcon.On)
        self.pushButton_set_preview.setIcon(icon)
        self.pushButton_set_preview.setCheckable(True)
        self.pushButton_set_preview.setFlat(True)

        self.horizontalLayout_2.addWidget(self.pushButton_set_preview)

        self.pushButton_save = QPushButton(self.frame)
        self.pushButton_save.setObjectName(u"pushButton_save")
        sizePolicy.setHeightForWidth(self.pushButton_save.sizePolicy().hasHeightForWidth())
        self.pushButton_save.setSizePolicy(sizePolicy)
        icon1 = QIcon()
        icon1.addFile(u"icons/grey/save.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon1.addFile(u"icons/purple/save.svg", QSize(), QIcon.Normal, QIcon.On)
        self.pushButton_save.setIcon(icon1)
        self.pushButton_save.setCheckable(False)
        self.pushButton_save.setAutoDefault(False)
        self.pushButton_save.setFlat(True)

        self.horizontalLayout_2.addWidget(self.pushButton_save)

        self.pushButton_discard = QPushButton(self.frame)
        self.pushButton_discard.setObjectName(u"pushButton_discard")
        sizePolicy.setHeightForWidth(self.pushButton_discard.sizePolicy().hasHeightForWidth())
        self.pushButton_discard.setSizePolicy(sizePolicy)
        icon2 = QIcon()
        icon2.addFile(u"icons/grey/undo.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon2.addFile(u"icons/purple/undo.svg", QSize(), QIcon.Normal, QIcon.On)
        self.pushButton_discard.setIcon(icon2)
        self.pushButton_discard.setCheckable(False)
        self.pushButton_discard.setAutoDefault(False)
        self.pushButton_discard.setFlat(True)

        self.horizontalLayout_2.addWidget(self.pushButton_discard)

        self.horizontalSpacer_2 = QSpacerItem(5, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)

        self.pushButton_close = QPushButton(self.frame)
        self.pushButton_close.setObjectName(u"pushButton_close")
        sizePolicy.setHeightForWidth(self.pushButton_close.sizePolicy().hasHeightForWidth())
        self.pushButton_close.setSizePolicy(sizePolicy)
        icon3 = QIcon()
        icon3.addFile(u"icons/purple/x-square.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon3.addFile(u"icons/purple/x-square.svg", QSize(), QIcon.Normal, QIcon.On)
        self.pushButton_close.setIcon(icon3)
        self.pushButton_close.setCheckable(False)
        self.pushButton_close.setAutoDefault(False)
        self.pushButton_close.setFlat(True)

        self.horizontalLayout_2.addWidget(self.pushButton_close)


        self.verticalLayout_2.addLayout(self.horizontalLayout_2)

        self.groupBox_stabilize = QGroupBox(self.frame)
        self.groupBox_stabilize.setObjectName(u"groupBox_stabilize")
        sizePolicy1 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.groupBox_stabilize.sizePolicy().hasHeightForWidth())
        self.groupBox_stabilize.setSizePolicy(sizePolicy1)
        self.groupBox_stabilize.setCheckable(True)
        self.groupBox_stabilize.setChecked(True)
        self.verticalLayout_8 = QVBoxLayout(self.groupBox_stabilize)
        self.verticalLayout_8.setSpacing(3)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.verticalLayout_8.setContentsMargins(3, 3, 3, 3)
        self.groupBox = QGroupBox(self.groupBox_stabilize)
        self.groupBox.setObjectName(u"groupBox")
        sizePolicy1.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy1)
        self.verticalLayout_4 = QVBoxLayout(self.groupBox)
        self.verticalLayout_4.setSpacing(3)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(9, 3, 3, 3)
        self.gridLayout = QGridLayout()
        self.gridLayout.setSpacing(3)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, -1, -1, -1)
        self.pushButton_set_ref = QPushButton(self.groupBox)
        self.pushButton_set_ref.setObjectName(u"pushButton_set_ref")
        sizePolicy2 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.pushButton_set_ref.sizePolicy().hasHeightForWidth())
        self.pushButton_set_ref.setSizePolicy(sizePolicy2)
        self.pushButton_set_ref.setMaximumSize(QSize(25, 16777215))
        icon4 = QIcon()
        icon4.addFile(u"icons/page_white_pick.png", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_set_ref.setIcon(icon4)
        self.pushButton_set_ref.setFlat(True)

        self.gridLayout.addWidget(self.pushButton_set_ref, 2, 2, 1, 1)

        self.label_3 = QLabel(self.groupBox)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout.addWidget(self.label_3, 1, 0, 1, 1)

        self.pushButton_set_start = QPushButton(self.groupBox)
        self.pushButton_set_start.setObjectName(u"pushButton_set_start")
        sizePolicy2.setHeightForWidth(self.pushButton_set_start.sizePolicy().hasHeightForWidth())
        self.pushButton_set_start.setSizePolicy(sizePolicy2)
        self.pushButton_set_start.setMaximumSize(QSize(25, 16777215))
        self.pushButton_set_start.setIcon(icon4)
        self.pushButton_set_start.setFlat(True)

        self.gridLayout.addWidget(self.pushButton_set_start, 0, 2, 1, 1)

        self.label = QLabel(self.groupBox)
        self.label.setObjectName(u"label")
        sizePolicy1.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy1)

        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.label_4 = QLabel(self.groupBox)
        self.label_4.setObjectName(u"label_4")

        self.gridLayout.addWidget(self.label_4, 2, 0, 1, 1)

        self.pushButton_set_end = QPushButton(self.groupBox)
        self.pushButton_set_end.setObjectName(u"pushButton_set_end")
        sizePolicy2.setHeightForWidth(self.pushButton_set_end.sizePolicy().hasHeightForWidth())
        self.pushButton_set_end.setSizePolicy(sizePolicy2)
        self.pushButton_set_end.setMaximumSize(QSize(25, 16777215))
        self.pushButton_set_end.setIcon(icon4)
        self.pushButton_set_end.setFlat(True)

        self.gridLayout.addWidget(self.pushButton_set_end, 1, 2, 1, 1)

        self.spinBox_frame_start = QSpinBox(self.groupBox)
        self.spinBox_frame_start.setObjectName(u"spinBox_frame_start")
        sizePolicy3 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.spinBox_frame_start.sizePolicy().hasHeightForWidth())
        self.spinBox_frame_start.setSizePolicy(sizePolicy3)
        self.spinBox_frame_start.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.spinBox_frame_start.setMinimum(-1)
        self.spinBox_frame_start.setMaximum(99999)
        self.spinBox_frame_start.setSingleStep(1)
        self.spinBox_frame_start.setValue(0)

        self.gridLayout.addWidget(self.spinBox_frame_start, 0, 1, 1, 1)

        self.spinBox_frame_end = QSpinBox(self.groupBox)
        self.spinBox_frame_end.setObjectName(u"spinBox_frame_end")
        sizePolicy3.setHeightForWidth(self.spinBox_frame_end.sizePolicy().hasHeightForWidth())
        self.spinBox_frame_end.setSizePolicy(sizePolicy3)
        self.spinBox_frame_end.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.spinBox_frame_end.setMinimum(-1)
        self.spinBox_frame_end.setMaximum(99999)
        self.spinBox_frame_end.setSingleStep(1)
        self.spinBox_frame_end.setValue(0)

        self.gridLayout.addWidget(self.spinBox_frame_end, 1, 1, 1, 1)

        self.spinBox_frame_ref = QSpinBox(self.groupBox)
        self.spinBox_frame_ref.setObjectName(u"spinBox_frame_ref")
        sizePolicy3.setHeightForWidth(self.spinBox_frame_ref.sizePolicy().hasHeightForWidth())
        self.spinBox_frame_ref.setSizePolicy(sizePolicy3)
        self.spinBox_frame_ref.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.spinBox_frame_ref.setMinimum(-1)
        self.spinBox_frame_ref.setMaximum(99999)
        self.spinBox_frame_ref.setSingleStep(1)
        self.spinBox_frame_ref.setValue(0)

        self.gridLayout.addWidget(self.spinBox_frame_ref, 2, 1, 1, 1)


        self.verticalLayout_4.addLayout(self.gridLayout)


        self.verticalLayout_8.addWidget(self.groupBox)

        self.groupBox_2 = QGroupBox(self.groupBox_stabilize)
        self.groupBox_2.setObjectName(u"groupBox_2")
        sizePolicy1.setHeightForWidth(self.groupBox_2.sizePolicy().hasHeightForWidth())
        self.groupBox_2.setSizePolicy(sizePolicy1)
        self.verticalLayout_9 = QVBoxLayout(self.groupBox_2)
        self.verticalLayout_9.setSpacing(3)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.verticalLayout_9.setContentsMargins(9, 3, 3, 3)
        self.gridLayout_2 = QGridLayout()
        self.gridLayout_2.setSpacing(3)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.label_6 = QLabel(self.groupBox_2)
        self.label_6.setObjectName(u"label_6")

        self.gridLayout_2.addWidget(self.label_6, 1, 0, 1, 1)

        self.spinBox_min_distance = QSpinBox(self.groupBox_2)
        self.spinBox_min_distance.setObjectName(u"spinBox_min_distance")
        sizePolicy3.setHeightForWidth(self.spinBox_min_distance.sizePolicy().hasHeightForWidth())
        self.spinBox_min_distance.setSizePolicy(sizePolicy3)
        self.spinBox_min_distance.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.spinBox_min_distance.setMinimum(1)
        self.spinBox_min_distance.setMaximum(21)
        self.spinBox_min_distance.setSingleStep(2)
        self.spinBox_min_distance.setValue(7)

        self.gridLayout_2.addWidget(self.spinBox_min_distance, 2, 1, 1, 1)

        self.label_5 = QLabel(self.groupBox_2)
        self.label_5.setObjectName(u"label_5")
        sizePolicy1.setHeightForWidth(self.label_5.sizePolicy().hasHeightForWidth())
        self.label_5.setSizePolicy(sizePolicy1)

        self.gridLayout_2.addWidget(self.label_5, 0, 0, 1, 1)

        self.label_8 = QLabel(self.groupBox_2)
        self.label_8.setObjectName(u"label_8")

        self.gridLayout_2.addWidget(self.label_8, 3, 0, 1, 1)

        self.spinBox_quality_level = QDoubleSpinBox(self.groupBox_2)
        self.spinBox_quality_level.setObjectName(u"spinBox_quality_level")
        sizePolicy2.setHeightForWidth(self.spinBox_quality_level.sizePolicy().hasHeightForWidth())
        self.spinBox_quality_level.setSizePolicy(sizePolicy2)
        self.spinBox_quality_level.setFrame(True)
        self.spinBox_quality_level.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.spinBox_quality_level.setDecimals(2)
        self.spinBox_quality_level.setSingleStep(0.010000000000000)
        self.spinBox_quality_level.setValue(0.010000000000000)

        self.gridLayout_2.addWidget(self.spinBox_quality_level, 1, 1, 1, 1)

        self.spinBox_max_corners = QSpinBox(self.groupBox_2)
        self.spinBox_max_corners.setObjectName(u"spinBox_max_corners")
        sizePolicy3.setHeightForWidth(self.spinBox_max_corners.sizePolicy().hasHeightForWidth())
        self.spinBox_max_corners.setSizePolicy(sizePolicy3)
        self.spinBox_max_corners.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.spinBox_max_corners.setMinimum(0)
        self.spinBox_max_corners.setMaximum(50)
        self.spinBox_max_corners.setSingleStep(1)
        self.spinBox_max_corners.setValue(0)

        self.gridLayout_2.addWidget(self.spinBox_max_corners, 0, 1, 1, 1)

        self.spinBox_block_size = QSpinBox(self.groupBox_2)
        self.spinBox_block_size.setObjectName(u"spinBox_block_size")
        sizePolicy3.setHeightForWidth(self.spinBox_block_size.sizePolicy().hasHeightForWidth())
        self.spinBox_block_size.setSizePolicy(sizePolicy3)
        self.spinBox_block_size.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.spinBox_block_size.setMinimum(1)
        self.spinBox_block_size.setMaximum(21)
        self.spinBox_block_size.setSingleStep(2)
        self.spinBox_block_size.setValue(7)

        self.gridLayout_2.addWidget(self.spinBox_block_size, 3, 1, 1, 1)

        self.label_7 = QLabel(self.groupBox_2)
        self.label_7.setObjectName(u"label_7")

        self.gridLayout_2.addWidget(self.label_7, 2, 0, 1, 1)

        self.pushButton_load_default = QPushButton(self.groupBox_2)
        self.pushButton_load_default.setObjectName(u"pushButton_load_default")
        sizePolicy2.setHeightForWidth(self.pushButton_load_default.sizePolicy().hasHeightForWidth())
        self.pushButton_load_default.setSizePolicy(sizePolicy2)

        self.gridLayout_2.addWidget(self.pushButton_load_default, 4, 0, 1, 1)


        self.verticalLayout_9.addLayout(self.gridLayout_2)


        self.verticalLayout_8.addWidget(self.groupBox_2)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setSpacing(5)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalSpacer_10 = QSpacerItem(10, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_10)

        self.pushButton_undo = QPushButton(self.groupBox_stabilize)
        self.pushButton_undo.setObjectName(u"pushButton_undo")
        sizePolicy2.setHeightForWidth(self.pushButton_undo.sizePolicy().hasHeightForWidth())
        self.pushButton_undo.setSizePolicy(sizePolicy2)
        icon5 = QIcon()
        icon5.addFile(u"icons/purple/undo.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_undo.setIcon(icon5)
        self.pushButton_undo.setFlat(True)

        self.horizontalLayout_3.addWidget(self.pushButton_undo)

        self.pushButton_calculate = QPushButton(self.groupBox_stabilize)
        self.pushButton_calculate.setObjectName(u"pushButton_calculate")

        self.horizontalLayout_3.addWidget(self.pushButton_calculate)


        self.verticalLayout_8.addLayout(self.horizontalLayout_3)


        self.verticalLayout_2.addWidget(self.groupBox_stabilize)


        self.verticalLayout.addWidget(self.frame)

        QWidget.setTabOrder(self.spinBox_frame_start, self.spinBox_frame_end)
        QWidget.setTabOrder(self.spinBox_frame_end, self.spinBox_frame_ref)
        QWidget.setTabOrder(self.spinBox_frame_ref, self.spinBox_max_corners)
        QWidget.setTabOrder(self.spinBox_max_corners, self.spinBox_quality_level)
        QWidget.setTabOrder(self.spinBox_quality_level, self.spinBox_min_distance)
        QWidget.setTabOrder(self.spinBox_min_distance, self.spinBox_block_size)
        QWidget.setTabOrder(self.spinBox_block_size, self.pushButton_calculate)
        QWidget.setTabOrder(self.pushButton_calculate, self.pushButton_load_default)
        QWidget.setTabOrder(self.pushButton_load_default, self.pushButton_set_ref)
        QWidget.setTabOrder(self.pushButton_set_ref, self.pushButton_set_end)
        QWidget.setTabOrder(self.pushButton_set_end, self.pushButton_set_start)

        self.retranslateUi(widget_stabilize)

        QMetaObject.connectSlotsByName(widget_stabilize)
    # setupUi

    def retranslateUi(self, widget_stabilize):
        widget_stabilize.setWindowTitle(QCoreApplication.translate("widget_stabilize", u"Form", None))
        self.pushButton_set_preview.setText("")
        self.pushButton_save.setText("")
        self.pushButton_discard.setText("")
        self.pushButton_close.setText("")
        self.groupBox_stabilize.setTitle(QCoreApplication.translate("widget_stabilize", u"(1)Stabilize", None))
        self.groupBox.setTitle(QCoreApplication.translate("widget_stabilize", u"Frames", None))
        self.pushButton_set_ref.setText("")
        self.label_3.setText(QCoreApplication.translate("widget_stabilize", u"end", None))
        self.pushButton_set_start.setText("")
        self.label.setText(QCoreApplication.translate("widget_stabilize", u"start", None))
        self.label_4.setText(QCoreApplication.translate("widget_stabilize", u"ref.", None))
        self.pushButton_set_end.setText("")
        self.groupBox_2.setTitle(QCoreApplication.translate("widget_stabilize", u"cv2.goodFeaturesToTrack", None))
        self.label_6.setText(QCoreApplication.translate("widget_stabilize", u"quality level", None))
        self.label_5.setText(QCoreApplication.translate("widget_stabilize", u"max. corners", None))
        self.label_8.setText(QCoreApplication.translate("widget_stabilize", u"max. block size", None))
        self.label_7.setText(QCoreApplication.translate("widget_stabilize", u"min. distance", None))
        self.pushButton_load_default.setText(QCoreApplication.translate("widget_stabilize", u"default", None))
        self.pushButton_undo.setText("")
        self.pushButton_calculate.setText(QCoreApplication.translate("widget_stabilize", u"calculate (F5)", None))
    # retranslateUi

