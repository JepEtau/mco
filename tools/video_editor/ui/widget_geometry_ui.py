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
        widget_geometry.resize(411, 162)
        self.mainLayout = QVBoxLayout(widget_geometry)
        self.mainLayout.setSpacing(0)
        self.mainLayout.setObjectName(u"mainLayout")
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.frame = QFrame(widget_geometry)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.Panel)
        self.frame.setFrameShadow(QFrame.Plain)
        self.verticalLayout_2 = QVBoxLayout(self.frame)
        self.verticalLayout_2.setSpacing(4)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(6, 6, 6, 6)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(3)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
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

        self.horizontalLayout.addWidget(self.pushButton_set_preview)

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

        self.horizontalLayout.addWidget(self.pushButton_save)

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

        self.horizontalLayout.addWidget(self.pushButton_discard)

        self.horizontalSpacer = QSpacerItem(5, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

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

        self.horizontalLayout.addWidget(self.pushButton_close)


        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.groupBox_part_geometry = QGroupBox(self.frame)
        self.groupBox_part_geometry.setObjectName(u"groupBox_part_geometry")
        sizePolicy1 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.groupBox_part_geometry.sizePolicy().hasHeightForWidth())
        self.groupBox_part_geometry.setSizePolicy(sizePolicy1)
        self.groupBox_part_geometry.setCheckable(False)
        self.groupBox_part_geometry.setChecked(False)
        self.gridLayout = QGridLayout(self.groupBox_part_geometry)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(3, 5, 3, 3)
        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.label_15 = QLabel(self.groupBox_part_geometry)
        self.label_15.setObjectName(u"label_15")
        self.label_15.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_5.addWidget(self.label_15)

        self.spinBox_part_width = QSpinBox(self.groupBox_part_geometry)
        self.spinBox_part_width.setObjectName(u"spinBox_part_width")
        self.spinBox_part_width.setEnabled(False)
        sizePolicy2 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.spinBox_part_width.sizePolicy().hasHeightForWidth())
        self.spinBox_part_width.setSizePolicy(sizePolicy2)
        self.spinBox_part_width.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.spinBox_part_width.setMinimum(0)
        self.spinBox_part_width.setMaximum(1920)
        self.spinBox_part_width.setSingleStep(1)
        self.spinBox_part_width.setValue(0)

        self.horizontalLayout_5.addWidget(self.spinBox_part_width)

        self.label_16 = QLabel(self.groupBox_part_geometry)
        self.label_16.setObjectName(u"label_16")
        self.label_16.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_5.addWidget(self.label_16)

        self.spinBox_part_height = QSpinBox(self.groupBox_part_geometry)
        self.spinBox_part_height.setObjectName(u"spinBox_part_height")
        self.spinBox_part_height.setEnabled(False)
        sizePolicy2.setHeightForWidth(self.spinBox_part_height.sizePolicy().hasHeightForWidth())
        self.spinBox_part_height.setSizePolicy(sizePolicy2)
        self.spinBox_part_height.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.spinBox_part_height.setMinimum(0)
        self.spinBox_part_height.setMaximum(1152)
        self.spinBox_part_height.setSingleStep(1)
        self.spinBox_part_height.setValue(0)

        self.horizontalLayout_5.addWidget(self.spinBox_part_height)


        self.gridLayout.addLayout(self.horizontalLayout_5, 2, 3, 1, 1)

        self.pushButton_part_crop_edition = QPushButton(self.groupBox_part_geometry)
        self.pushButton_part_crop_edition.setObjectName(u"pushButton_part_crop_edition")
        icon4 = QIcon()
        icon4.addFile(u"icons/grey/crop.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon4.addFile(u"icons/blue/crop.svg", QSize(), QIcon.Normal, QIcon.On)
        self.pushButton_part_crop_edition.setIcon(icon4)
        self.pushButton_part_crop_edition.setCheckable(True)
        self.pushButton_part_crop_edition.setAutoDefault(False)
        self.pushButton_part_crop_edition.setFlat(True)

        self.gridLayout.addWidget(self.pushButton_part_crop_edition, 0, 1, 1, 1)

        self.label_14 = QLabel(self.groupBox_part_geometry)
        self.label_14.setObjectName(u"label_14")
        self.label_14.setLineWidth(0)

        self.gridLayout.addWidget(self.label_14, 1, 0, 1, 1)

        self.pushButton_part_resize_preview = QPushButton(self.groupBox_part_geometry)
        self.pushButton_part_resize_preview.setObjectName(u"pushButton_part_resize_preview")
        self.pushButton_part_resize_preview.setIcon(icon)
        self.pushButton_part_resize_preview.setCheckable(True)
        self.pushButton_part_resize_preview.setFlat(True)

        self.gridLayout.addWidget(self.pushButton_part_resize_preview, 1, 2, 1, 1)

        self.pushButton_undo = QPushButton(self.groupBox_part_geometry)
        self.pushButton_undo.setObjectName(u"pushButton_undo")
        sizePolicy3 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.pushButton_undo.sizePolicy().hasHeightForWidth())
        self.pushButton_undo.setSizePolicy(sizePolicy3)
        self.pushButton_undo.setIcon(icon2)
        self.pushButton_undo.setFlat(True)

        self.gridLayout.addWidget(self.pushButton_undo, 0, 4, 1, 1)

        self.checkBox_part_keep_ratio = QCheckBox(self.groupBox_part_geometry)
        self.checkBox_part_keep_ratio.setObjectName(u"checkBox_part_keep_ratio")
        self.checkBox_part_keep_ratio.setEnabled(False)
        self.checkBox_part_keep_ratio.setChecked(True)

        self.gridLayout.addWidget(self.checkBox_part_keep_ratio, 1, 3, 1, 1)

        self.pushButton_part_resize_edition = QPushButton(self.groupBox_part_geometry)
        self.pushButton_part_resize_edition.setObjectName(u"pushButton_part_resize_edition")
        self.pushButton_part_resize_edition.setEnabled(False)
        icon5 = QIcon()
        icon5.addFile(u"icons/blue/scaling.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_part_resize_edition.setIcon(icon5)
        self.pushButton_part_resize_edition.setCheckable(True)
        self.pushButton_part_resize_edition.setAutoDefault(False)
        self.pushButton_part_resize_edition.setFlat(True)

        self.gridLayout.addWidget(self.pushButton_part_resize_edition, 1, 1, 1, 1)

        self.pushButton_part_crop_preview = QPushButton(self.groupBox_part_geometry)
        self.pushButton_part_crop_preview.setObjectName(u"pushButton_part_crop_preview")
        self.pushButton_part_crop_preview.setIcon(icon)
        self.pushButton_part_crop_preview.setCheckable(True)
        self.pushButton_part_crop_preview.setFlat(True)

        self.gridLayout.addWidget(self.pushButton_part_crop_preview, 0, 2, 1, 1)

        self.label_9 = QLabel(self.groupBox_part_geometry)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setLineWidth(0)

        self.gridLayout.addWidget(self.label_9, 0, 0, 1, 1)

        self.lineEdit_part_crop_rectangle = QLineEdit(self.groupBox_part_geometry)
        self.lineEdit_part_crop_rectangle.setObjectName(u"lineEdit_part_crop_rectangle")
        sizePolicy4 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.lineEdit_part_crop_rectangle.sizePolicy().hasHeightForWidth())
        self.lineEdit_part_crop_rectangle.setSizePolicy(sizePolicy4)
        self.lineEdit_part_crop_rectangle.setMinimumSize(QSize(190, 0))
        self.lineEdit_part_crop_rectangle.setMaximumSize(QSize(190, 16777215))
        self.lineEdit_part_crop_rectangle.setFrame(False)
        self.lineEdit_part_crop_rectangle.setAlignment(Qt.AlignCenter)
        self.lineEdit_part_crop_rectangle.setReadOnly(True)

        self.gridLayout.addWidget(self.lineEdit_part_crop_rectangle, 0, 3, 1, 1)


        self.verticalLayout_2.addWidget(self.groupBox_part_geometry)


        self.mainLayout.addWidget(self.frame)


        self.retranslateUi(widget_geometry)

        QMetaObject.connectSlotsByName(widget_geometry)
    # setupUi

    def retranslateUi(self, widget_geometry):
        self.pushButton_set_preview.setText("")
        self.pushButton_save.setText("")
        self.pushButton_discard.setText("")
        self.pushButton_close.setText("")
        self.groupBox_part_geometry.setTitle(QCoreApplication.translate("widget_geometry", u"Part: crop and resize", None))
        self.label_15.setText(QCoreApplication.translate("widget_geometry", u"w", None))
        self.label_16.setText(QCoreApplication.translate("widget_geometry", u"h", None))
        self.pushButton_part_crop_edition.setText("")
        self.label_14.setText(QCoreApplication.translate("widget_geometry", u"resize", None))
        self.pushButton_part_resize_preview.setText("")
        self.pushButton_undo.setText("")
        self.checkBox_part_keep_ratio.setText(QCoreApplication.translate("widget_geometry", u"keep ratio", None))
        self.pushButton_part_resize_edition.setText("")
        self.pushButton_part_crop_preview.setText("")
        self.label_9.setText(QCoreApplication.translate("widget_geometry", u"crop", None))
        self.lineEdit_part_crop_rectangle.setText(QCoreApplication.translate("widget_geometry", u"x:10, y:10, w:5000, h:5000", None))
        pass
    # retranslateUi

