# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_widget_geometry.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QFrame, QGridLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QRadioButton, QSizePolicy, QSpacerItem,
    QSpinBox, QVBoxLayout, QWidget)

class Ui_widget_geometry(object):
    def setupUi(self, widget_geometry):
        if not widget_geometry.objectName():
            widget_geometry.setObjectName(u"widget_geometry")
        widget_geometry.resize(411, 314)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(widget_geometry.sizePolicy().hasHeightForWidth())
        widget_geometry.setSizePolicy(sizePolicy)
        self.mainLayout = QVBoxLayout(widget_geometry)
        self.mainLayout.setSpacing(0)
        self.mainLayout.setObjectName(u"mainLayout")
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.frame = QFrame(widget_geometry)
        self.frame.setObjectName(u"frame")
        sizePolicy1 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
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
        self.pushButton_set_preview = QPushButton(self.frame)
        self.pushButton_set_preview.setObjectName(u"pushButton_set_preview")
        sizePolicy1.setHeightForWidth(self.pushButton_set_preview.sizePolicy().hasHeightForWidth())
        self.pushButton_set_preview.setSizePolicy(sizePolicy1)
        icon = QIcon()
        icon.addFile(u"icons/grey/eye.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon.addFile(u"icons/blue/eye.svg", QSize(), QIcon.Normal, QIcon.On)
        self.pushButton_set_preview.setIcon(icon)
        self.pushButton_set_preview.setCheckable(True)
        self.pushButton_set_preview.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_set_preview)

        self.pushButton_save = QPushButton(self.frame)
        self.pushButton_save.setObjectName(u"pushButton_save")
        sizePolicy1.setHeightForWidth(self.pushButton_save.sizePolicy().hasHeightForWidth())
        self.pushButton_save.setSizePolicy(sizePolicy1)
        icon1 = QIcon()
        icon1.addFile(u"icons/purple/save.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_save.setIcon(icon1)
        self.pushButton_save.setCheckable(False)
        self.pushButton_save.setAutoDefault(False)
        self.pushButton_save.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_save)

        self.pushButton_discard = QPushButton(self.frame)
        self.pushButton_discard.setObjectName(u"pushButton_discard")
        sizePolicy1.setHeightForWidth(self.pushButton_discard.sizePolicy().hasHeightForWidth())
        self.pushButton_discard.setSizePolicy(sizePolicy1)
        icon2 = QIcon()
        icon2.addFile(u"icons/grey/undo.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon2.addFile(u"icons/purple/undo.svg", QSize(), QIcon.Normal, QIcon.On)
        self.pushButton_discard.setIcon(icon2)
        self.pushButton_discard.setCheckable(False)
        self.pushButton_discard.setAutoDefault(False)
        self.pushButton_discard.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_discard)

        self.horizontalSpacer_2 = QSpacerItem(22, 10, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)

        self.label_message = QLabel(self.frame)
        self.label_message.setObjectName(u"label_message")

        self.horizontalLayout.addWidget(self.label_message)

        self.horizontalSpacer = QSpacerItem(5, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.pushButton_close = QPushButton(self.frame)
        self.pushButton_close.setObjectName(u"pushButton_close")
        sizePolicy1.setHeightForWidth(self.pushButton_close.sizePolicy().hasHeightForWidth())
        self.pushButton_close.setSizePolicy(sizePolicy1)
        icon3 = QIcon()
        icon3.addFile(u"icons/purple/x-square.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon3.addFile(u"icons/purple/x-square.svg", QSize(), QIcon.Normal, QIcon.On)
        self.pushButton_close.setIcon(icon3)
        self.pushButton_close.setCheckable(False)
        self.pushButton_close.setAutoDefault(False)
        self.pushButton_close.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_close)


        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.radioButton_part = QRadioButton(self.frame)
        self.radioButton_part.setObjectName(u"radioButton_part")
        self.radioButton_part.setChecked(True)

        self.horizontalLayout_2.addWidget(self.radioButton_part)

        self.radioButton_shot = QRadioButton(self.frame)
        self.radioButton_shot.setObjectName(u"radioButton_shot")

        self.horizontalLayout_2.addWidget(self.radioButton_shot)

        self.pushButton_remove_shot_geometry = QPushButton(self.frame)
        self.pushButton_remove_shot_geometry.setObjectName(u"pushButton_remove_shot_geometry")
        self.pushButton_remove_shot_geometry.setEnabled(False)
        sizePolicy1.setHeightForWidth(self.pushButton_remove_shot_geometry.sizePolicy().hasHeightForWidth())
        self.pushButton_remove_shot_geometry.setSizePolicy(sizePolicy1)
        self.pushButton_remove_shot_geometry.setIcon(icon3)
        self.pushButton_remove_shot_geometry.setCheckable(False)
        self.pushButton_remove_shot_geometry.setFlat(True)

        self.horizontalLayout_2.addWidget(self.pushButton_remove_shot_geometry)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_3)


        self.verticalLayout_2.addLayout(self.horizontalLayout_2)

        self.groupBox_part_geometry = QGroupBox(self.frame)
        self.groupBox_part_geometry.setObjectName(u"groupBox_part_geometry")
        sizePolicy2 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.groupBox_part_geometry.sizePolicy().hasHeightForWidth())
        self.groupBox_part_geometry.setSizePolicy(sizePolicy2)
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
        sizePolicy3 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.spinBox_part_width.sizePolicy().hasHeightForWidth())
        self.spinBox_part_width.setSizePolicy(sizePolicy3)
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
        sizePolicy3.setHeightForWidth(self.spinBox_part_height.sizePolicy().hasHeightForWidth())
        self.spinBox_part_height.setSizePolicy(sizePolicy3)
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
        sizePolicy4 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.pushButton_undo.sizePolicy().hasHeightForWidth())
        self.pushButton_undo.setSizePolicy(sizePolicy4)
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
        sizePolicy5 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.lineEdit_part_crop_rectangle.sizePolicy().hasHeightForWidth())
        self.lineEdit_part_crop_rectangle.setSizePolicy(sizePolicy5)
        self.lineEdit_part_crop_rectangle.setMinimumSize(QSize(190, 0))
        self.lineEdit_part_crop_rectangle.setMaximumSize(QSize(190, 16777215))
        self.lineEdit_part_crop_rectangle.setFrame(False)
        self.lineEdit_part_crop_rectangle.setAlignment(Qt.AlignCenter)
        self.lineEdit_part_crop_rectangle.setReadOnly(True)

        self.gridLayout.addWidget(self.lineEdit_part_crop_rectangle, 0, 3, 1, 1)


        self.verticalLayout_2.addWidget(self.groupBox_part_geometry)

        self.groupBox_shot_geometry = QGroupBox(self.frame)
        self.groupBox_shot_geometry.setObjectName(u"groupBox_shot_geometry")
        sizePolicy2.setHeightForWidth(self.groupBox_shot_geometry.sizePolicy().hasHeightForWidth())
        self.groupBox_shot_geometry.setSizePolicy(sizePolicy2)
        self.groupBox_shot_geometry.setCheckable(False)
        self.groupBox_shot_geometry.setChecked(False)
        self.gridLayout_2 = QGridLayout(self.groupBox_shot_geometry)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setContentsMargins(3, 5, 3, 3)
        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.label_17 = QLabel(self.groupBox_shot_geometry)
        self.label_17.setObjectName(u"label_17")
        self.label_17.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_6.addWidget(self.label_17)

        self.spinBox_shot_width = QSpinBox(self.groupBox_shot_geometry)
        self.spinBox_shot_width.setObjectName(u"spinBox_shot_width")
        self.spinBox_shot_width.setEnabled(False)
        sizePolicy3.setHeightForWidth(self.spinBox_shot_width.sizePolicy().hasHeightForWidth())
        self.spinBox_shot_width.setSizePolicy(sizePolicy3)
        self.spinBox_shot_width.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.spinBox_shot_width.setMinimum(0)
        self.spinBox_shot_width.setMaximum(1920)
        self.spinBox_shot_width.setSingleStep(1)
        self.spinBox_shot_width.setValue(0)

        self.horizontalLayout_6.addWidget(self.spinBox_shot_width)

        self.label_18 = QLabel(self.groupBox_shot_geometry)
        self.label_18.setObjectName(u"label_18")
        self.label_18.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_6.addWidget(self.label_18)

        self.spinBox_shot_height = QSpinBox(self.groupBox_shot_geometry)
        self.spinBox_shot_height.setObjectName(u"spinBox_shot_height")
        self.spinBox_shot_height.setEnabled(False)
        sizePolicy3.setHeightForWidth(self.spinBox_shot_height.sizePolicy().hasHeightForWidth())
        self.spinBox_shot_height.setSizePolicy(sizePolicy3)
        self.spinBox_shot_height.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.spinBox_shot_height.setMinimum(0)
        self.spinBox_shot_height.setMaximum(1152)
        self.spinBox_shot_height.setSingleStep(1)
        self.spinBox_shot_height.setValue(0)

        self.horizontalLayout_6.addWidget(self.spinBox_shot_height)


        self.gridLayout_2.addLayout(self.horizontalLayout_6, 2, 3, 1, 1)

        self.pushButton_shot_crop_edition = QPushButton(self.groupBox_shot_geometry)
        self.pushButton_shot_crop_edition.setObjectName(u"pushButton_shot_crop_edition")
        self.pushButton_shot_crop_edition.setIcon(icon4)
        self.pushButton_shot_crop_edition.setCheckable(True)
        self.pushButton_shot_crop_edition.setAutoDefault(False)
        self.pushButton_shot_crop_edition.setFlat(True)

        self.gridLayout_2.addWidget(self.pushButton_shot_crop_edition, 0, 1, 1, 1)

        self.label_19 = QLabel(self.groupBox_shot_geometry)
        self.label_19.setObjectName(u"label_19")
        self.label_19.setLineWidth(0)

        self.gridLayout_2.addWidget(self.label_19, 1, 0, 1, 1)

        self.pushButton_shot_resize_preview = QPushButton(self.groupBox_shot_geometry)
        self.pushButton_shot_resize_preview.setObjectName(u"pushButton_shot_resize_preview")
        self.pushButton_shot_resize_preview.setIcon(icon)
        self.pushButton_shot_resize_preview.setCheckable(True)
        self.pushButton_shot_resize_preview.setFlat(True)

        self.gridLayout_2.addWidget(self.pushButton_shot_resize_preview, 1, 2, 1, 1)

        self.pushButton_shot_discard = QPushButton(self.groupBox_shot_geometry)
        self.pushButton_shot_discard.setObjectName(u"pushButton_shot_discard")
        sizePolicy4.setHeightForWidth(self.pushButton_shot_discard.sizePolicy().hasHeightForWidth())
        self.pushButton_shot_discard.setSizePolicy(sizePolicy4)
        self.pushButton_shot_discard.setIcon(icon2)
        self.pushButton_shot_discard.setFlat(True)

        self.gridLayout_2.addWidget(self.pushButton_shot_discard, 0, 4, 1, 1)

        self.pushButton_shot_resize_edition = QPushButton(self.groupBox_shot_geometry)
        self.pushButton_shot_resize_edition.setObjectName(u"pushButton_shot_resize_edition")
        self.pushButton_shot_resize_edition.setEnabled(False)
        self.pushButton_shot_resize_edition.setIcon(icon5)
        self.pushButton_shot_resize_edition.setCheckable(True)
        self.pushButton_shot_resize_edition.setAutoDefault(False)
        self.pushButton_shot_resize_edition.setFlat(True)

        self.gridLayout_2.addWidget(self.pushButton_shot_resize_edition, 1, 1, 1, 1)

        self.pushButton_shot_crop_preview = QPushButton(self.groupBox_shot_geometry)
        self.pushButton_shot_crop_preview.setObjectName(u"pushButton_shot_crop_preview")
        self.pushButton_shot_crop_preview.setIcon(icon)
        self.pushButton_shot_crop_preview.setCheckable(True)
        self.pushButton_shot_crop_preview.setFlat(True)

        self.gridLayout_2.addWidget(self.pushButton_shot_crop_preview, 0, 2, 1, 1)

        self.label_10 = QLabel(self.groupBox_shot_geometry)
        self.label_10.setObjectName(u"label_10")
        self.label_10.setLineWidth(0)

        self.gridLayout_2.addWidget(self.label_10, 0, 0, 1, 1)

        self.lineEdit_shot_crop_rectangle = QLineEdit(self.groupBox_shot_geometry)
        self.lineEdit_shot_crop_rectangle.setObjectName(u"lineEdit_shot_crop_rectangle")
        sizePolicy5.setHeightForWidth(self.lineEdit_shot_crop_rectangle.sizePolicy().hasHeightForWidth())
        self.lineEdit_shot_crop_rectangle.setSizePolicy(sizePolicy5)
        self.lineEdit_shot_crop_rectangle.setMinimumSize(QSize(190, 0))
        self.lineEdit_shot_crop_rectangle.setMaximumSize(QSize(190, 16777215))
        self.lineEdit_shot_crop_rectangle.setFrame(False)
        self.lineEdit_shot_crop_rectangle.setAlignment(Qt.AlignCenter)
        self.lineEdit_shot_crop_rectangle.setReadOnly(True)

        self.gridLayout_2.addWidget(self.lineEdit_shot_crop_rectangle, 0, 3, 1, 1)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.checkBox_shot_keep_ratio = QCheckBox(self.groupBox_shot_geometry)
        self.checkBox_shot_keep_ratio.setObjectName(u"checkBox_shot_keep_ratio")
        self.checkBox_shot_keep_ratio.setEnabled(False)
        self.checkBox_shot_keep_ratio.setChecked(True)

        self.horizontalLayout_3.addWidget(self.checkBox_shot_keep_ratio)

        self.checkBox_fit_to_part = QCheckBox(self.groupBox_shot_geometry)
        self.checkBox_fit_to_part.setObjectName(u"checkBox_fit_to_part")
        self.checkBox_fit_to_part.setEnabled(False)

        self.horizontalLayout_3.addWidget(self.checkBox_fit_to_part)


        self.gridLayout_2.addLayout(self.horizontalLayout_3, 1, 3, 1, 1)


        self.verticalLayout_2.addWidget(self.groupBox_shot_geometry)


        self.mainLayout.addWidget(self.frame)


        self.retranslateUi(widget_geometry)

        QMetaObject.connectSlotsByName(widget_geometry)
    # setupUi

    def retranslateUi(self, widget_geometry):
        self.pushButton_set_preview.setText("")
        self.pushButton_save.setText("")
        self.pushButton_discard.setText("")
        self.label_message.setText(QCoreApplication.translate("widget_geometry", u"disabled", None))
        self.pushButton_close.setText("")
        self.radioButton_part.setText(QCoreApplication.translate("widget_geometry", u"part", None))
        self.radioButton_shot.setText(QCoreApplication.translate("widget_geometry", u"shot", None))
        self.groupBox_part_geometry.setTitle(QCoreApplication.translate("widget_geometry", u"Part", None))
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
        self.groupBox_shot_geometry.setTitle(QCoreApplication.translate("widget_geometry", u"Shot", None))
        self.label_17.setText(QCoreApplication.translate("widget_geometry", u"w", None))
        self.label_18.setText(QCoreApplication.translate("widget_geometry", u"h", None))
        self.pushButton_shot_crop_edition.setText("")
        self.label_19.setText(QCoreApplication.translate("widget_geometry", u"resize", None))
        self.pushButton_shot_resize_preview.setText("")
        self.pushButton_shot_discard.setText("")
        self.pushButton_shot_resize_edition.setText("")
        self.pushButton_shot_crop_preview.setText("")
        self.label_10.setText(QCoreApplication.translate("widget_geometry", u"crop", None))
        self.lineEdit_shot_crop_rectangle.setText(QCoreApplication.translate("widget_geometry", u"x:10, y:10, w:5000, h:5000", None))
        self.checkBox_shot_keep_ratio.setText(QCoreApplication.translate("widget_geometry", u"keep ratio", None))
        self.checkBox_fit_to_part.setText(QCoreApplication.translate("widget_geometry", u"auto", None))
        pass
    # retranslateUi

