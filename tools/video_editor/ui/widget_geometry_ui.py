# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_widget_geometry.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QFrame, QGridLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class Ui_widget_geometry(object):
    def setupUi(self, widget_geometry):
        if not widget_geometry.objectName():
            widget_geometry.setObjectName(u"widget_geometry")
        widget_geometry.resize(289, 336)
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
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(6, 6, 6, 6)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(3)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.pushButton_set_preview = QPushButton(self.frame)
        self.pushButton_set_preview.setObjectName(u"pushButton_set_preview")
        sizePolicy1.setHeightForWidth(self.pushButton_set_preview.sizePolicy().hasHeightForWidth())
        self.pushButton_set_preview.setSizePolicy(sizePolicy1)
        self.pushButton_set_preview.setFocusPolicy(Qt.NoFocus)
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
        self.pushButton_save.setFocusPolicy(Qt.NoFocus)
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
        self.pushButton_discard.setFocusPolicy(Qt.NoFocus)
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
        self.pushButton_close.setFocusPolicy(Qt.NoFocus)
        icon3 = QIcon()
        icon3.addFile(u"icons/purple/x-square.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon3.addFile(u"icons/purple/x-square.svg", QSize(), QIcon.Normal, QIcon.On)
        self.pushButton_close.setIcon(icon3)
        self.pushButton_close.setCheckable(False)
        self.pushButton_close.setAutoDefault(False)
        self.pushButton_close.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_close)


        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.groupBox_target_geometry = QGroupBox(self.frame)
        self.groupBox_target_geometry.setObjectName(u"groupBox_target_geometry")
        sizePolicy1.setHeightForWidth(self.groupBox_target_geometry.sizePolicy().hasHeightForWidth())
        self.groupBox_target_geometry.setSizePolicy(sizePolicy1)
        self.groupBox_target_geometry.setCheckable(False)
        self.groupBox_target_geometry.setChecked(False)
        self.gridLayout = QGridLayout(self.groupBox_target_geometry)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(3, 9, 3, 3)
        self.pushButton_target_discard = QPushButton(self.groupBox_target_geometry)
        self.pushButton_target_discard.setObjectName(u"pushButton_target_discard")
        sizePolicy2 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.pushButton_target_discard.sizePolicy().hasHeightForWidth())
        self.pushButton_target_discard.setSizePolicy(sizePolicy2)
        self.pushButton_target_discard.setFocusPolicy(Qt.NoFocus)
        icon4 = QIcon()
        icon4.addFile(u"icons/purple/undo.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon4.addFile(u"icons/purple/undo.svg", QSize(), QIcon.Normal, QIcon.On)
        self.pushButton_target_discard.setIcon(icon4)
        self.pushButton_target_discard.setFlat(True)

        self.gridLayout.addWidget(self.pushButton_target_discard, 0, 5, 1, 1)

        self.pushButton_target_width_edition = QPushButton(self.groupBox_target_geometry)
        self.pushButton_target_width_edition.setObjectName(u"pushButton_target_width_edition")
        self.pushButton_target_width_edition.setFocusPolicy(Qt.NoFocus)
        icon5 = QIcon()
        icon5.addFile(u"icons/grey/box-select.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon5.addFile(u"icons/blue/box-select.svg", QSize(), QIcon.Normal, QIcon.On)
        icon5.addFile(u"icons/grey/box-select.svg", QSize(), QIcon.Disabled, QIcon.Off)
        icon5.addFile(u"icons/grey/box-select.svg", QSize(), QIcon.Disabled, QIcon.On)
        self.pushButton_target_width_edition.setIcon(icon5)
        self.pushButton_target_width_edition.setCheckable(True)
        self.pushButton_target_width_edition.setFlat(True)

        self.gridLayout.addWidget(self.pushButton_target_width_edition, 0, 1, 1, 1)

        self.lineEdit_target_width = QLineEdit(self.groupBox_target_geometry)
        self.lineEdit_target_width.setObjectName(u"lineEdit_target_width")
        sizePolicy3 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.lineEdit_target_width.sizePolicy().hasHeightForWidth())
        self.lineEdit_target_width.setSizePolicy(sizePolicy3)
        self.lineEdit_target_width.setMinimumSize(QSize(40, 0))
        self.lineEdit_target_width.setMaximumSize(QSize(40, 16777215))
        self.lineEdit_target_width.setFrame(False)
        self.lineEdit_target_width.setAlignment(Qt.AlignCenter)
        self.lineEdit_target_width.setReadOnly(True)

        self.gridLayout.addWidget(self.lineEdit_target_width, 0, 3, 1, 1)

        self.label_9 = QLabel(self.groupBox_target_geometry)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setLineWidth(0)

        self.gridLayout.addWidget(self.label_9, 0, 0, 1, 1)

        self.pushButton_target_width_copy_from_shot = QPushButton(self.groupBox_target_geometry)
        self.pushButton_target_width_copy_from_shot.setObjectName(u"pushButton_target_width_copy_from_shot")
        sizePolicy2.setHeightForWidth(self.pushButton_target_width_copy_from_shot.sizePolicy().hasHeightForWidth())
        self.pushButton_target_width_copy_from_shot.setSizePolicy(sizePolicy2)
        self.pushButton_target_width_copy_from_shot.setFocusPolicy(Qt.NoFocus)
        icon6 = QIcon()
        icon6.addFile(u"icons/blue/corner-up-left.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon6.addFile(u"icons/blue/corner-up-left.svg", QSize(), QIcon.Normal, QIcon.On)
        self.pushButton_target_width_copy_from_shot.setIcon(icon6)
        self.pushButton_target_width_copy_from_shot.setFlat(True)

        self.gridLayout.addWidget(self.pushButton_target_width_copy_from_shot, 0, 4, 1, 1)


        self.verticalLayout_2.addWidget(self.groupBox_target_geometry)

        self.groupBox_shot_default_geometry_2 = QGroupBox(self.frame)
        self.groupBox_shot_default_geometry_2.setObjectName(u"groupBox_shot_default_geometry_2")
        self.groupBox_shot_default_geometry_2.setEnabled(True)
        sizePolicy4 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.groupBox_shot_default_geometry_2.sizePolicy().hasHeightForWidth())
        self.groupBox_shot_default_geometry_2.setSizePolicy(sizePolicy4)
        self.groupBox_shot_default_geometry_2.setCheckable(False)
        self.groupBox_shot_default_geometry_2.setChecked(False)
        self.gridLayout_4 = QGridLayout(self.groupBox_shot_default_geometry_2)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.gridLayout_4.setContentsMargins(3, 9, 3, 3)
        self.pushButton_shot_crop_preview = QPushButton(self.groupBox_shot_default_geometry_2)
        self.pushButton_shot_crop_preview.setObjectName(u"pushButton_shot_crop_preview")
        self.pushButton_shot_crop_preview.setFocusPolicy(Qt.NoFocus)
        self.pushButton_shot_crop_preview.setIcon(icon)
        self.pushButton_shot_crop_preview.setCheckable(True)
        self.pushButton_shot_crop_preview.setFlat(True)

        self.gridLayout_4.addWidget(self.pushButton_shot_crop_preview, 0, 2, 1, 1)

        self.horizontalSpacer_3 = QSpacerItem(20, 10, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.gridLayout_4.addItem(self.horizontalSpacer_3, 0, 3, 1, 1)

        self.pushButton_shot_resize_preview = QPushButton(self.groupBox_shot_default_geometry_2)
        self.pushButton_shot_resize_preview.setObjectName(u"pushButton_shot_resize_preview")
        self.pushButton_shot_resize_preview.setFocusPolicy(Qt.NoFocus)
        self.pushButton_shot_resize_preview.setIcon(icon)
        self.pushButton_shot_resize_preview.setCheckable(True)
        self.pushButton_shot_resize_preview.setFlat(True)

        self.gridLayout_4.addWidget(self.pushButton_shot_resize_preview, 0, 5, 1, 1)

        self.label_21 = QLabel(self.groupBox_shot_default_geometry_2)
        self.label_21.setObjectName(u"label_21")
        self.label_21.setLineWidth(0)

        self.gridLayout_4.addWidget(self.label_21, 0, 4, 1, 1)

        self.label_12 = QLabel(self.groupBox_shot_default_geometry_2)
        self.label_12.setObjectName(u"label_12")
        self.label_12.setLineWidth(0)

        self.gridLayout_4.addWidget(self.label_12, 0, 0, 1, 1)

        self.pushButton_shot_crop_edition = QPushButton(self.groupBox_shot_default_geometry_2)
        self.pushButton_shot_crop_edition.setObjectName(u"pushButton_shot_crop_edition")
        self.pushButton_shot_crop_edition.setFocusPolicy(Qt.NoFocus)
        icon7 = QIcon()
        icon7.addFile(u"icons/grey/crop.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon7.addFile(u"icons/blue/crop.svg", QSize(), QIcon.Normal, QIcon.On)
        self.pushButton_shot_crop_edition.setIcon(icon7)
        self.pushButton_shot_crop_edition.setCheckable(True)
        self.pushButton_shot_crop_edition.setAutoDefault(False)
        self.pushButton_shot_crop_edition.setFlat(True)

        self.gridLayout_4.addWidget(self.pushButton_shot_crop_edition, 0, 1, 1, 1)


        self.verticalLayout_2.addWidget(self.groupBox_shot_default_geometry_2)

        self.groupBox_default_shot_geometry = QGroupBox(self.frame)
        self.groupBox_default_shot_geometry.setObjectName(u"groupBox_default_shot_geometry")
        self.groupBox_default_shot_geometry.setEnabled(True)
        sizePolicy4.setHeightForWidth(self.groupBox_default_shot_geometry.sizePolicy().hasHeightForWidth())
        self.groupBox_default_shot_geometry.setSizePolicy(sizePolicy4)
        self.groupBox_default_shot_geometry.setFocusPolicy(Qt.NoFocus)
        self.groupBox_default_shot_geometry.setCheckable(True)
        self.groupBox_default_shot_geometry.setChecked(True)
        self.gridLayout_3 = QGridLayout(self.groupBox_default_shot_geometry)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.gridLayout_3.setContentsMargins(3, 9, 3, 3)
        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.checkBox_default_shot_keep_ratio = QCheckBox(self.groupBox_default_shot_geometry)
        self.checkBox_default_shot_keep_ratio.setObjectName(u"checkBox_default_shot_keep_ratio")
        self.checkBox_default_shot_keep_ratio.setEnabled(True)
        self.checkBox_default_shot_keep_ratio.setFocusPolicy(Qt.NoFocus)
        self.checkBox_default_shot_keep_ratio.setChecked(True)

        self.horizontalLayout_4.addWidget(self.checkBox_default_shot_keep_ratio)

        self.checkBox_default_shot_fit_to_width = QCheckBox(self.groupBox_default_shot_geometry)
        self.checkBox_default_shot_fit_to_width.setObjectName(u"checkBox_default_shot_fit_to_width")
        self.checkBox_default_shot_fit_to_width.setEnabled(True)
        self.checkBox_default_shot_fit_to_width.setFocusPolicy(Qt.NoFocus)

        self.horizontalLayout_4.addWidget(self.checkBox_default_shot_fit_to_width)


        self.gridLayout_3.addLayout(self.horizontalLayout_4, 1, 1, 1, 1)

        self.label_20 = QLabel(self.groupBox_default_shot_geometry)
        self.label_20.setObjectName(u"label_20")
        self.label_20.setLineWidth(0)

        self.gridLayout_3.addWidget(self.label_20, 1, 0, 1, 1)

        self.lineEdit_default_shot_crop_rectangle = QLineEdit(self.groupBox_default_shot_geometry)
        self.lineEdit_default_shot_crop_rectangle.setObjectName(u"lineEdit_default_shot_crop_rectangle")
        sizePolicy3.setHeightForWidth(self.lineEdit_default_shot_crop_rectangle.sizePolicy().hasHeightForWidth())
        self.lineEdit_default_shot_crop_rectangle.setSizePolicy(sizePolicy3)
        self.lineEdit_default_shot_crop_rectangle.setMinimumSize(QSize(190, 0))
        self.lineEdit_default_shot_crop_rectangle.setMaximumSize(QSize(190, 16777215))
        self.lineEdit_default_shot_crop_rectangle.setFrame(False)
        self.lineEdit_default_shot_crop_rectangle.setAlignment(Qt.AlignCenter)
        self.lineEdit_default_shot_crop_rectangle.setReadOnly(True)

        self.gridLayout_3.addWidget(self.lineEdit_default_shot_crop_rectangle, 0, 1, 1, 1)

        self.pushButton_default_shot_discard = QPushButton(self.groupBox_default_shot_geometry)
        self.pushButton_default_shot_discard.setObjectName(u"pushButton_default_shot_discard")
        sizePolicy2.setHeightForWidth(self.pushButton_default_shot_discard.sizePolicy().hasHeightForWidth())
        self.pushButton_default_shot_discard.setSizePolicy(sizePolicy2)
        self.pushButton_default_shot_discard.setFocusPolicy(Qt.NoFocus)
        self.pushButton_default_shot_discard.setIcon(icon2)
        self.pushButton_default_shot_discard.setFlat(True)

        self.gridLayout_3.addWidget(self.pushButton_default_shot_discard, 0, 2, 1, 1)

        self.label_11 = QLabel(self.groupBox_default_shot_geometry)
        self.label_11.setObjectName(u"label_11")
        self.label_11.setLineWidth(0)

        self.gridLayout_3.addWidget(self.label_11, 0, 0, 1, 1)


        self.verticalLayout_2.addWidget(self.groupBox_default_shot_geometry)

        self.groupBox_shot_geometry = QGroupBox(self.frame)
        self.groupBox_shot_geometry.setObjectName(u"groupBox_shot_geometry")
        sizePolicy4.setHeightForWidth(self.groupBox_shot_geometry.sizePolicy().hasHeightForWidth())
        self.groupBox_shot_geometry.setSizePolicy(sizePolicy4)
        self.groupBox_shot_geometry.setFocusPolicy(Qt.NoFocus)
        self.groupBox_shot_geometry.setCheckable(True)
        self.groupBox_shot_geometry.setChecked(True)
        self.gridLayout_2 = QGridLayout(self.groupBox_shot_geometry)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setContentsMargins(3, 9, 3, 3)
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.checkBox_shot_keep_ratio = QCheckBox(self.groupBox_shot_geometry)
        self.checkBox_shot_keep_ratio.setObjectName(u"checkBox_shot_keep_ratio")
        self.checkBox_shot_keep_ratio.setEnabled(True)
        self.checkBox_shot_keep_ratio.setFocusPolicy(Qt.NoFocus)
        self.checkBox_shot_keep_ratio.setChecked(True)

        self.horizontalLayout_3.addWidget(self.checkBox_shot_keep_ratio)

        self.checkBox_shot_fit_to_width = QCheckBox(self.groupBox_shot_geometry)
        self.checkBox_shot_fit_to_width.setObjectName(u"checkBox_shot_fit_to_width")
        self.checkBox_shot_fit_to_width.setEnabled(True)
        self.checkBox_shot_fit_to_width.setFocusPolicy(Qt.NoFocus)

        self.horizontalLayout_3.addWidget(self.checkBox_shot_fit_to_width)


        self.gridLayout_2.addLayout(self.horizontalLayout_3, 1, 1, 1, 1)

        self.label_19 = QLabel(self.groupBox_shot_geometry)
        self.label_19.setObjectName(u"label_19")
        self.label_19.setEnabled(True)
        self.label_19.setLineWidth(0)

        self.gridLayout_2.addWidget(self.label_19, 1, 0, 1, 1)

        self.lineEdit_shot_crop_rectangle = QLineEdit(self.groupBox_shot_geometry)
        self.lineEdit_shot_crop_rectangle.setObjectName(u"lineEdit_shot_crop_rectangle")
        self.lineEdit_shot_crop_rectangle.setEnabled(True)
        sizePolicy3.setHeightForWidth(self.lineEdit_shot_crop_rectangle.sizePolicy().hasHeightForWidth())
        self.lineEdit_shot_crop_rectangle.setSizePolicy(sizePolicy3)
        self.lineEdit_shot_crop_rectangle.setMinimumSize(QSize(190, 0))
        self.lineEdit_shot_crop_rectangle.setMaximumSize(QSize(190, 16777215))
        self.lineEdit_shot_crop_rectangle.setFrame(False)
        self.lineEdit_shot_crop_rectangle.setAlignment(Qt.AlignCenter)
        self.lineEdit_shot_crop_rectangle.setReadOnly(True)

        self.gridLayout_2.addWidget(self.lineEdit_shot_crop_rectangle, 0, 1, 1, 1)

        self.label_10 = QLabel(self.groupBox_shot_geometry)
        self.label_10.setObjectName(u"label_10")
        self.label_10.setEnabled(True)
        self.label_10.setLineWidth(0)

        self.gridLayout_2.addWidget(self.label_10, 0, 0, 1, 1)

        self.pushButton_shot_discard = QPushButton(self.groupBox_shot_geometry)
        self.pushButton_shot_discard.setObjectName(u"pushButton_shot_discard")
        sizePolicy2.setHeightForWidth(self.pushButton_shot_discard.sizePolicy().hasHeightForWidth())
        self.pushButton_shot_discard.setSizePolicy(sizePolicy2)
        self.pushButton_shot_discard.setFocusPolicy(Qt.NoFocus)
        self.pushButton_shot_discard.setIcon(icon2)
        self.pushButton_shot_discard.setFlat(True)

        self.gridLayout_2.addWidget(self.pushButton_shot_discard, 0, 2, 1, 1)


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
        self.groupBox_target_geometry.setTitle(QCoreApplication.translate("widget_geometry", u"Target", None))
        self.pushButton_target_discard.setText("")
        self.pushButton_target_width_edition.setText("")
        self.lineEdit_target_width.setText(QCoreApplication.translate("widget_geometry", u"1440", None))
        self.label_9.setText(QCoreApplication.translate("widget_geometry", u"width", None))
        self.pushButton_target_width_copy_from_shot.setText("")
        self.groupBox_shot_default_geometry_2.setTitle(QCoreApplication.translate("widget_geometry", u"Preview", None))
        self.pushButton_shot_crop_preview.setText("")
        self.pushButton_shot_resize_preview.setText("")
        self.label_21.setText(QCoreApplication.translate("widget_geometry", u"resize", None))
        self.label_12.setText(QCoreApplication.translate("widget_geometry", u"crop", None))
        self.pushButton_shot_crop_edition.setText("")
        self.groupBox_default_shot_geometry.setTitle(QCoreApplication.translate("widget_geometry", u"Shot (default)", None))
        self.checkBox_default_shot_keep_ratio.setText(QCoreApplication.translate("widget_geometry", u"keep ratio", None))
        self.checkBox_default_shot_fit_to_width.setText(QCoreApplication.translate("widget_geometry", u"fit to width", None))
        self.label_20.setText(QCoreApplication.translate("widget_geometry", u"resize", None))
        self.lineEdit_default_shot_crop_rectangle.setText(QCoreApplication.translate("widget_geometry", u"x:10, y:10, w:5000, h:5000", None))
        self.pushButton_default_shot_discard.setText("")
        self.label_11.setText(QCoreApplication.translate("widget_geometry", u"crop", None))
        self.groupBox_shot_geometry.setTitle(QCoreApplication.translate("widget_geometry", u"Shot (custom)", None))
        self.checkBox_shot_keep_ratio.setText(QCoreApplication.translate("widget_geometry", u"keep ratio", None))
        self.checkBox_shot_fit_to_width.setText(QCoreApplication.translate("widget_geometry", u"fit_to_width", None))
        self.label_19.setText(QCoreApplication.translate("widget_geometry", u"resize", None))
        self.lineEdit_shot_crop_rectangle.setText(QCoreApplication.translate("widget_geometry", u"x:10, y:10, w:5000, h:5000", None))
        self.label_10.setText(QCoreApplication.translate("widget_geometry", u"crop", None))
        self.pushButton_shot_discard.setText("")
        pass
    # retranslateUi

