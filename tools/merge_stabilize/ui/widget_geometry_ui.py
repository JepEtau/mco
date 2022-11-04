# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_widget_geometry.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QFrame, QGridLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QSpacerItem, QSpinBox,
    QVBoxLayout, QWidget)

class Ui_widget_geometry(object):
    def setupUi(self, widget_geometry):
        if not widget_geometry.objectName():
            widget_geometry.setObjectName(u"widget_geometry")
        widget_geometry.resize(316, 234)
        self.verticalLayout = QVBoxLayout(widget_geometry)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.frame = QFrame(widget_geometry)
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

        self.groupBox_st_geometry = QGroupBox(self.frame)
        self.groupBox_st_geometry.setObjectName(u"groupBox_st_geometry")
        sizePolicy1 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.groupBox_st_geometry.sizePolicy().hasHeightForWidth())
        self.groupBox_st_geometry.setSizePolicy(sizePolicy1)
        self.groupBox_st_geometry.setCheckable(False)
        self.groupBox_st_geometry.setChecked(False)
        self.gridLayout_2 = QGridLayout(self.groupBox_st_geometry)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setContentsMargins(3, 3, 3, 3)
        self.lineEdit_st_crop_rectangle = QLineEdit(self.groupBox_st_geometry)
        self.lineEdit_st_crop_rectangle.setObjectName(u"lineEdit_st_crop_rectangle")
        sizePolicy2 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.lineEdit_st_crop_rectangle.sizePolicy().hasHeightForWidth())
        self.lineEdit_st_crop_rectangle.setSizePolicy(sizePolicy2)
        self.lineEdit_st_crop_rectangle.setMinimumSize(QSize(160, 0))
        self.lineEdit_st_crop_rectangle.setMaximumSize(QSize(160, 16777215))
        self.lineEdit_st_crop_rectangle.setAlignment(Qt.AlignCenter)
        self.lineEdit_st_crop_rectangle.setReadOnly(True)

        self.gridLayout_2.addWidget(self.lineEdit_st_crop_rectangle, 0, 3, 1, 1)

        self.pushButton_st_resize_edition = QPushButton(self.groupBox_st_geometry)
        self.pushButton_st_resize_edition.setObjectName(u"pushButton_st_resize_edition")
        sizePolicy.setHeightForWidth(self.pushButton_st_resize_edition.sizePolicy().hasHeightForWidth())
        self.pushButton_st_resize_edition.setSizePolicy(sizePolicy)
        icon4 = QIcon()
        icon4.addFile(u"icons/blue/scaling.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_st_resize_edition.setIcon(icon4)
        self.pushButton_st_resize_edition.setCheckable(True)
        self.pushButton_st_resize_edition.setAutoDefault(False)
        self.pushButton_st_resize_edition.setFlat(False)

        self.gridLayout_2.addWidget(self.pushButton_st_resize_edition, 1, 1, 1, 1)

        self.pushButton_st_resize_preview = QPushButton(self.groupBox_st_geometry)
        self.pushButton_st_resize_preview.setObjectName(u"pushButton_st_resize_preview")
        sizePolicy3 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.pushButton_st_resize_preview.sizePolicy().hasHeightForWidth())
        self.pushButton_st_resize_preview.setSizePolicy(sizePolicy3)
        self.pushButton_st_resize_preview.setMaximumSize(QSize(25, 16777215))
        self.pushButton_st_resize_preview.setIcon(icon)
        self.pushButton_st_resize_preview.setCheckable(True)
        self.pushButton_st_resize_preview.setFlat(False)

        self.gridLayout_2.addWidget(self.pushButton_st_resize_preview, 1, 2, 1, 1)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.label_11 = QLabel(self.groupBox_st_geometry)
        self.label_11.setObjectName(u"label_11")
        self.label_11.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_4.addWidget(self.label_11)

        self.spinBox_st_width = QSpinBox(self.groupBox_st_geometry)
        self.spinBox_st_width.setObjectName(u"spinBox_st_width")
        sizePolicy4 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.spinBox_st_width.sizePolicy().hasHeightForWidth())
        self.spinBox_st_width.setSizePolicy(sizePolicy4)
        self.spinBox_st_width.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.spinBox_st_width.setMinimum(0)
        self.spinBox_st_width.setMaximum(1920)
        self.spinBox_st_width.setSingleStep(1)
        self.spinBox_st_width.setValue(0)

        self.horizontalLayout_4.addWidget(self.spinBox_st_width)

        self.label_12 = QLabel(self.groupBox_st_geometry)
        self.label_12.setObjectName(u"label_12")
        self.label_12.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_4.addWidget(self.label_12)

        self.spinBox_st_height = QSpinBox(self.groupBox_st_geometry)
        self.spinBox_st_height.setObjectName(u"spinBox_st_height")
        sizePolicy4.setHeightForWidth(self.spinBox_st_height.sizePolicy().hasHeightForWidth())
        self.spinBox_st_height.setSizePolicy(sizePolicy4)
        self.spinBox_st_height.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.spinBox_st_height.setMinimum(0)
        self.spinBox_st_height.setMaximum(1152)
        self.spinBox_st_height.setSingleStep(1)
        self.spinBox_st_height.setValue(0)

        self.horizontalLayout_4.addWidget(self.spinBox_st_height)


        self.gridLayout_2.addLayout(self.horizontalLayout_4, 2, 3, 1, 1)

        self.label_10 = QLabel(self.groupBox_st_geometry)
        self.label_10.setObjectName(u"label_10")

        self.gridLayout_2.addWidget(self.label_10, 1, 0, 1, 1)

        self.label_13 = QLabel(self.groupBox_st_geometry)
        self.label_13.setObjectName(u"label_13")

        self.gridLayout_2.addWidget(self.label_13, 0, 0, 1, 1)

        self.pushButton_st_crop_edition = QPushButton(self.groupBox_st_geometry)
        self.pushButton_st_crop_edition.setObjectName(u"pushButton_st_crop_edition")
        sizePolicy.setHeightForWidth(self.pushButton_st_crop_edition.sizePolicy().hasHeightForWidth())
        self.pushButton_st_crop_edition.setSizePolicy(sizePolicy)
        icon5 = QIcon()
        icon5.addFile(u"icons/grey/crop.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon5.addFile(u"icons/blue/crop.svg", QSize(), QIcon.Normal, QIcon.On)
        icon5.addFile(u"icons/grey/crop.svg", QSize(), QIcon.Disabled, QIcon.Off)
        self.pushButton_st_crop_edition.setIcon(icon5)
        self.pushButton_st_crop_edition.setCheckable(True)
        self.pushButton_st_crop_edition.setAutoDefault(False)
        self.pushButton_st_crop_edition.setFlat(False)

        self.gridLayout_2.addWidget(self.pushButton_st_crop_edition, 0, 1, 1, 1)

        self.pushButton_st_crop_preview = QPushButton(self.groupBox_st_geometry)
        self.pushButton_st_crop_preview.setObjectName(u"pushButton_st_crop_preview")
        sizePolicy3.setHeightForWidth(self.pushButton_st_crop_preview.sizePolicy().hasHeightForWidth())
        self.pushButton_st_crop_preview.setSizePolicy(sizePolicy3)
        self.pushButton_st_crop_preview.setMaximumSize(QSize(25, 16777215))
        self.pushButton_st_crop_preview.setIcon(icon)
        self.pushButton_st_crop_preview.setCheckable(True)
        self.pushButton_st_crop_preview.setFlat(False)

        self.gridLayout_2.addWidget(self.pushButton_st_crop_preview, 0, 2, 1, 1)

        self.checkBox_keep_ratio = QCheckBox(self.groupBox_st_geometry)
        self.checkBox_keep_ratio.setObjectName(u"checkBox_keep_ratio")
        self.checkBox_keep_ratio.setChecked(True)

        self.gridLayout_2.addWidget(self.checkBox_keep_ratio, 1, 3, 1, 1)


        self.verticalLayout_2.addWidget(self.groupBox_st_geometry)

        self.groupBox_final_geometry = QGroupBox(self.frame)
        self.groupBox_final_geometry.setObjectName(u"groupBox_final_geometry")
        sizePolicy1.setHeightForWidth(self.groupBox_final_geometry.sizePolicy().hasHeightForWidth())
        self.groupBox_final_geometry.setSizePolicy(sizePolicy1)
        self.groupBox_final_geometry.setCheckable(False)
        self.groupBox_final_geometry.setChecked(False)
        self.gridLayout = QGridLayout(self.groupBox_final_geometry)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(3, 3, 3, 3)
        self.pushButton_final_resize_preview = QPushButton(self.groupBox_final_geometry)
        self.pushButton_final_resize_preview.setObjectName(u"pushButton_final_resize_preview")
        sizePolicy3.setHeightForWidth(self.pushButton_final_resize_preview.sizePolicy().hasHeightForWidth())
        self.pushButton_final_resize_preview.setSizePolicy(sizePolicy3)
        self.pushButton_final_resize_preview.setMaximumSize(QSize(25, 16777215))
        self.pushButton_final_resize_preview.setIcon(icon)
        self.pushButton_final_resize_preview.setCheckable(True)
        self.pushButton_final_resize_preview.setFlat(False)

        self.gridLayout.addWidget(self.pushButton_final_resize_preview, 1, 1, 1, 1)

        self.pushButton_final_crop_preview = QPushButton(self.groupBox_final_geometry)
        self.pushButton_final_crop_preview.setObjectName(u"pushButton_final_crop_preview")
        sizePolicy3.setHeightForWidth(self.pushButton_final_crop_preview.sizePolicy().hasHeightForWidth())
        self.pushButton_final_crop_preview.setSizePolicy(sizePolicy3)
        self.pushButton_final_crop_preview.setMaximumSize(QSize(25, 16777215))
        self.pushButton_final_crop_preview.setIcon(icon)
        self.pushButton_final_crop_preview.setCheckable(True)
        self.pushButton_final_crop_preview.setFlat(False)

        self.gridLayout.addWidget(self.pushButton_final_crop_preview, 0, 2, 1, 1)

        self.pushButton_undo = QPushButton(self.groupBox_final_geometry)
        self.pushButton_undo.setObjectName(u"pushButton_undo")
        sizePolicy3.setHeightForWidth(self.pushButton_undo.sizePolicy().hasHeightForWidth())
        self.pushButton_undo.setSizePolicy(sizePolicy3)
        icon6 = QIcon()
        icon6.addFile(u"icons/purple/undo.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_undo.setIcon(icon6)
        self.pushButton_undo.setFlat(True)

        self.gridLayout.addWidget(self.pushButton_undo, 0, 4, 1, 1)

        self.label_14 = QLabel(self.groupBox_final_geometry)
        self.label_14.setObjectName(u"label_14")

        self.gridLayout.addWidget(self.label_14, 1, 0, 1, 1)

        self.label_9 = QLabel(self.groupBox_final_geometry)
        self.label_9.setObjectName(u"label_9")

        self.gridLayout.addWidget(self.label_9, 0, 0, 1, 1)

        self.pushButton_final_crop_edition = QPushButton(self.groupBox_final_geometry)
        self.pushButton_final_crop_edition.setObjectName(u"pushButton_final_crop_edition")
        sizePolicy.setHeightForWidth(self.pushButton_final_crop_edition.sizePolicy().hasHeightForWidth())
        self.pushButton_final_crop_edition.setSizePolicy(sizePolicy)
        self.pushButton_final_crop_edition.setIcon(icon5)
        self.pushButton_final_crop_edition.setCheckable(True)
        self.pushButton_final_crop_edition.setAutoDefault(False)
        self.pushButton_final_crop_edition.setFlat(False)

        self.gridLayout.addWidget(self.pushButton_final_crop_edition, 0, 1, 1, 1)

        self.lineEdit_final_crop_rectangle = QLineEdit(self.groupBox_final_geometry)
        self.lineEdit_final_crop_rectangle.setObjectName(u"lineEdit_final_crop_rectangle")
        sizePolicy2.setHeightForWidth(self.lineEdit_final_crop_rectangle.sizePolicy().hasHeightForWidth())
        self.lineEdit_final_crop_rectangle.setSizePolicy(sizePolicy2)
        self.lineEdit_final_crop_rectangle.setMinimumSize(QSize(160, 0))
        self.lineEdit_final_crop_rectangle.setMaximumSize(QSize(160, 16777215))
        self.lineEdit_final_crop_rectangle.setAlignment(Qt.AlignCenter)
        self.lineEdit_final_crop_rectangle.setReadOnly(True)

        self.gridLayout.addWidget(self.lineEdit_final_crop_rectangle, 0, 3, 1, 1)


        self.verticalLayout_2.addWidget(self.groupBox_final_geometry)


        self.verticalLayout.addWidget(self.frame)


        self.retranslateUi(widget_geometry)

        QMetaObject.connectSlotsByName(widget_geometry)
    # setupUi

    def retranslateUi(self, widget_geometry):
        widget_geometry.setWindowTitle(QCoreApplication.translate("widget_geometry", u"Form", None))
        self.pushButton_set_preview.setText("")
        self.pushButton_save.setText("")
        self.pushButton_discard.setText("")
        self.pushButton_close.setText("")
        self.groupBox_st_geometry.setTitle(QCoreApplication.translate("widget_geometry", u"(3) After stabilization/stitching", None))
        self.lineEdit_st_crop_rectangle.setText(QCoreApplication.translate("widget_geometry", u"t:10, d:10, l:50, r:50", None))
        self.pushButton_st_resize_edition.setText("")
        self.pushButton_st_resize_preview.setText("")
        self.label_11.setText(QCoreApplication.translate("widget_geometry", u"w", None))
        self.label_12.setText(QCoreApplication.translate("widget_geometry", u"h", None))
        self.label_10.setText(QCoreApplication.translate("widget_geometry", u"resize", None))
        self.label_13.setText(QCoreApplication.translate("widget_geometry", u"crop", None))
        self.pushButton_st_crop_edition.setText("")
        self.pushButton_st_crop_preview.setText("")
        self.checkBox_keep_ratio.setText(QCoreApplication.translate("widget_geometry", u"keep ratio", None))
        self.groupBox_final_geometry.setTitle(QCoreApplication.translate("widget_geometry", u"(4) Final", None))
        self.pushButton_final_resize_preview.setText("")
        self.pushButton_final_crop_preview.setText("")
        self.pushButton_undo.setText("")
        self.label_14.setText(QCoreApplication.translate("widget_geometry", u"resize", None))
        self.label_9.setText(QCoreApplication.translate("widget_geometry", u"crop", None))
        self.pushButton_final_crop_edition.setText("")
        self.lineEdit_final_crop_rectangle.setText(QCoreApplication.translate("widget_geometry", u"t:10, d:10, l:50, r:50", None))
    # retranslateUi

