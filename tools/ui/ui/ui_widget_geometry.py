# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_widget_geometry.ui'
##
## Created by: Qt User Interface Compiler version 6.7.3
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

class Ui_GeometryWidget(object):
    def setupUi(self, GeometryWidget):
        if not GeometryWidget.objectName():
            GeometryWidget.setObjectName(u"GeometryWidget")
        GeometryWidget.resize(305, 394)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(GeometryWidget.sizePolicy().hasHeightForWidth())
        GeometryWidget.setSizePolicy(sizePolicy)
        self.mainLayout = QVBoxLayout(GeometryWidget)
        self.mainLayout.setSpacing(0)
        self.mainLayout.setObjectName(u"mainLayout")
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.frame = QFrame(GeometryWidget)
        self.frame.setObjectName(u"frame")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
        self.frame.setSizePolicy(sizePolicy1)
        self.frame.setFrameShape(QFrame.Shape.Panel)
        self.frame.setFrameShadow(QFrame.Shadow.Plain)
        self.verticalLayout_2 = QVBoxLayout(self.frame)
        self.verticalLayout_2.setSpacing(12)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(6, 6, 6, 6)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(3)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.pushButton_set_preview = QPushButton(self.frame)
        self.pushButton_set_preview.setObjectName(u"pushButton_set_preview")
        sizePolicy1.setHeightForWidth(self.pushButton_set_preview.sizePolicy().hasHeightForWidth())
        self.pushButton_set_preview.setSizePolicy(sizePolicy1)
        self.pushButton_set_preview.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        icon = QIcon()
        icon.addFile(u"./icons/grey/eye.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        icon.addFile(u"./icons/blue/eye.svg", QSize(), QIcon.Mode.Normal, QIcon.State.On)
        self.pushButton_set_preview.setIcon(icon)
        self.pushButton_set_preview.setCheckable(True)
        self.pushButton_set_preview.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_set_preview)

        self.horizontalSpacer_2 = QSpacerItem(22, 10, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)

        self.label_message = QLabel(self.frame)
        self.label_message.setObjectName(u"label_message")

        self.horizontalLayout.addWidget(self.label_message)

        self.horizontalSpacer = QSpacerItem(5, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.pushButton_discard = QPushButton(self.frame)
        self.pushButton_discard.setObjectName(u"pushButton_discard")
        sizePolicy1.setHeightForWidth(self.pushButton_discard.sizePolicy().hasHeightForWidth())
        self.pushButton_discard.setSizePolicy(sizePolicy1)
        self.pushButton_discard.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        icon1 = QIcon()
        icon1.addFile(u"./icons/purple/undo.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.pushButton_discard.setIcon(icon1)
        self.pushButton_discard.setCheckable(False)
        self.pushButton_discard.setAutoDefault(False)
        self.pushButton_discard.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_discard)

        self.pushButton_save = QPushButton(self.frame)
        self.pushButton_save.setObjectName(u"pushButton_save")
        sizePolicy1.setHeightForWidth(self.pushButton_save.sizePolicy().hasHeightForWidth())
        self.pushButton_save.setSizePolicy(sizePolicy1)
        self.pushButton_save.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        icon2 = QIcon()
        icon2.addFile(u"./icons/purple/save.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.pushButton_save.setIcon(icon2)
        self.pushButton_save.setCheckable(False)
        self.pushButton_save.setAutoDefault(False)
        self.pushButton_save.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_save)


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
        self.label_9 = QLabel(self.groupBox_target_geometry)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setLineWidth(0)

        self.gridLayout.addWidget(self.label_9, 0, 0, 1, 1)

        self.lineEdit_target_width = QLineEdit(self.groupBox_target_geometry)
        self.lineEdit_target_width.setObjectName(u"lineEdit_target_width")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.lineEdit_target_width.sizePolicy().hasHeightForWidth())
        self.lineEdit_target_width.setSizePolicy(sizePolicy2)
        self.lineEdit_target_width.setMinimumSize(QSize(40, 0))
        self.lineEdit_target_width.setMaximumSize(QSize(40, 16777215))
        self.lineEdit_target_width.setFrame(False)
        self.lineEdit_target_width.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lineEdit_target_width.setReadOnly(True)

        self.gridLayout.addWidget(self.lineEdit_target_width, 0, 3, 1, 1)

        self.pushButton_target_discard = QPushButton(self.groupBox_target_geometry)
        self.pushButton_target_discard.setObjectName(u"pushButton_target_discard")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.pushButton_target_discard.sizePolicy().hasHeightForWidth())
        self.pushButton_target_discard.setSizePolicy(sizePolicy3)
        self.pushButton_target_discard.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        icon3 = QIcon()
        icon3.addFile(u"./icons/purple/undo.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        icon3.addFile(u"./icons/purple/undo.svg", QSize(), QIcon.Mode.Normal, QIcon.State.On)
        self.pushButton_target_discard.setIcon(icon3)
        self.pushButton_target_discard.setFlat(True)

        self.gridLayout.addWidget(self.pushButton_target_discard, 0, 4, 1, 1)

        self.pushButton_target_width_edition = QPushButton(self.groupBox_target_geometry)
        self.pushButton_target_width_edition.setObjectName(u"pushButton_target_width_edition")
        self.pushButton_target_width_edition.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        icon4 = QIcon()
        icon4.addFile(u"./icons/grey/box-select.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        icon4.addFile(u"./icons/blue/box-select.svg", QSize(), QIcon.Mode.Normal, QIcon.State.On)
        icon4.addFile(u"./icons/grey/box-select.svg", QSize(), QIcon.Mode.Disabled, QIcon.State.Off)
        icon4.addFile(u"./icons/grey/box-select.svg", QSize(), QIcon.Mode.Disabled, QIcon.State.On)
        self.pushButton_target_width_edition.setIcon(icon4)
        self.pushButton_target_width_edition.setCheckable(True)
        self.pushButton_target_width_edition.setFlat(True)

        self.gridLayout.addWidget(self.pushButton_target_width_edition, 0, 1, 1, 1)

        self.pushButton_target_save = QPushButton(self.groupBox_target_geometry)
        self.pushButton_target_save.setObjectName(u"pushButton_target_save")
        sizePolicy1.setHeightForWidth(self.pushButton_target_save.sizePolicy().hasHeightForWidth())
        self.pushButton_target_save.setSizePolicy(sizePolicy1)
        self.pushButton_target_save.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.pushButton_target_save.setIcon(icon2)
        self.pushButton_target_save.setCheckable(False)
        self.pushButton_target_save.setAutoDefault(False)
        self.pushButton_target_save.setFlat(True)

        self.gridLayout.addWidget(self.pushButton_target_save, 0, 5, 1, 1)


        self.verticalLayout_2.addWidget(self.groupBox_target_geometry)

        self.groupBox_scene_default_geometry_2 = QGroupBox(self.frame)
        self.groupBox_scene_default_geometry_2.setObjectName(u"groupBox_scene_default_geometry_2")
        self.groupBox_scene_default_geometry_2.setEnabled(True)
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.groupBox_scene_default_geometry_2.sizePolicy().hasHeightForWidth())
        self.groupBox_scene_default_geometry_2.setSizePolicy(sizePolicy4)
        self.groupBox_scene_default_geometry_2.setCheckable(False)
        self.groupBox_scene_default_geometry_2.setChecked(False)
        self.gridLayout_4 = QGridLayout(self.groupBox_scene_default_geometry_2)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.gridLayout_4.setContentsMargins(3, 9, 3, 3)
        self.pushButton_scene_crop_preview = QPushButton(self.groupBox_scene_default_geometry_2)
        self.pushButton_scene_crop_preview.setObjectName(u"pushButton_scene_crop_preview")
        self.pushButton_scene_crop_preview.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.pushButton_scene_crop_preview.setIcon(icon)
        self.pushButton_scene_crop_preview.setCheckable(True)
        self.pushButton_scene_crop_preview.setFlat(True)

        self.gridLayout_4.addWidget(self.pushButton_scene_crop_preview, 0, 2, 1, 1)

        self.horizontalSpacer_3 = QSpacerItem(20, 10, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.gridLayout_4.addItem(self.horizontalSpacer_3, 0, 3, 1, 1)

        self.pushButton_scene_resize_preview = QPushButton(self.groupBox_scene_default_geometry_2)
        self.pushButton_scene_resize_preview.setObjectName(u"pushButton_scene_resize_preview")
        self.pushButton_scene_resize_preview.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.pushButton_scene_resize_preview.setIcon(icon)
        self.pushButton_scene_resize_preview.setCheckable(True)
        self.pushButton_scene_resize_preview.setFlat(True)

        self.gridLayout_4.addWidget(self.pushButton_scene_resize_preview, 0, 5, 1, 1)

        self.label_21 = QLabel(self.groupBox_scene_default_geometry_2)
        self.label_21.setObjectName(u"label_21")
        self.label_21.setLineWidth(0)

        self.gridLayout_4.addWidget(self.label_21, 0, 4, 1, 1)

        self.label_12 = QLabel(self.groupBox_scene_default_geometry_2)
        self.label_12.setObjectName(u"label_12")
        self.label_12.setLineWidth(0)

        self.gridLayout_4.addWidget(self.label_12, 0, 0, 1, 1)

        self.pushButton_scene_crop_edition = QPushButton(self.groupBox_scene_default_geometry_2)
        self.pushButton_scene_crop_edition.setObjectName(u"pushButton_scene_crop_edition")
        self.pushButton_scene_crop_edition.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        icon5 = QIcon()
        icon5.addFile(u"./icons/grey/crop.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        icon5.addFile(u"./icons/blue/crop.svg", QSize(), QIcon.Mode.Normal, QIcon.State.On)
        self.pushButton_scene_crop_edition.setIcon(icon5)
        self.pushButton_scene_crop_edition.setCheckable(True)
        self.pushButton_scene_crop_edition.setAutoDefault(False)
        self.pushButton_scene_crop_edition.setFlat(True)

        self.gridLayout_4.addWidget(self.pushButton_scene_crop_edition, 0, 1, 1, 1)


        self.verticalLayout_2.addWidget(self.groupBox_scene_default_geometry_2)

        self.groupBox_default_scene_geometry = QGroupBox(self.frame)
        self.groupBox_default_scene_geometry.setObjectName(u"groupBox_default_scene_geometry")
        self.groupBox_default_scene_geometry.setEnabled(True)
        sizePolicy4.setHeightForWidth(self.groupBox_default_scene_geometry.sizePolicy().hasHeightForWidth())
        self.groupBox_default_scene_geometry.setSizePolicy(sizePolicy4)
        self.groupBox_default_scene_geometry.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.groupBox_default_scene_geometry.setCheckable(True)
        self.groupBox_default_scene_geometry.setChecked(True)
        self.gridLayout_3 = QGridLayout(self.groupBox_default_scene_geometry)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.gridLayout_3.setContentsMargins(3, 9, 3, 3)
        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.checkBox_default_scene_keep_ratio = QCheckBox(self.groupBox_default_scene_geometry)
        self.checkBox_default_scene_keep_ratio.setObjectName(u"checkBox_default_scene_keep_ratio")
        self.checkBox_default_scene_keep_ratio.setEnabled(True)
        self.checkBox_default_scene_keep_ratio.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.checkBox_default_scene_keep_ratio.setChecked(True)

        self.horizontalLayout_4.addWidget(self.checkBox_default_scene_keep_ratio)

        self.checkBox_default_scene_fit_to_width = QCheckBox(self.groupBox_default_scene_geometry)
        self.checkBox_default_scene_fit_to_width.setObjectName(u"checkBox_default_scene_fit_to_width")
        self.checkBox_default_scene_fit_to_width.setEnabled(True)
        self.checkBox_default_scene_fit_to_width.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.horizontalLayout_4.addWidget(self.checkBox_default_scene_fit_to_width)


        self.gridLayout_3.addLayout(self.horizontalLayout_4, 1, 1, 1, 1)

        self.label_20 = QLabel(self.groupBox_default_scene_geometry)
        self.label_20.setObjectName(u"label_20")
        self.label_20.setLineWidth(0)

        self.gridLayout_3.addWidget(self.label_20, 1, 0, 1, 1)

        self.lineEdit_default_scene_crop_rectangle = QLineEdit(self.groupBox_default_scene_geometry)
        self.lineEdit_default_scene_crop_rectangle.setObjectName(u"lineEdit_default_scene_crop_rectangle")
        sizePolicy2.setHeightForWidth(self.lineEdit_default_scene_crop_rectangle.sizePolicy().hasHeightForWidth())
        self.lineEdit_default_scene_crop_rectangle.setSizePolicy(sizePolicy2)
        self.lineEdit_default_scene_crop_rectangle.setMinimumSize(QSize(190, 0))
        self.lineEdit_default_scene_crop_rectangle.setMaximumSize(QSize(190, 16777215))
        self.lineEdit_default_scene_crop_rectangle.setFrame(False)
        self.lineEdit_default_scene_crop_rectangle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lineEdit_default_scene_crop_rectangle.setReadOnly(True)

        self.gridLayout_3.addWidget(self.lineEdit_default_scene_crop_rectangle, 0, 1, 1, 1)

        self.pushButton_default_scene_discard = QPushButton(self.groupBox_default_scene_geometry)
        self.pushButton_default_scene_discard.setObjectName(u"pushButton_default_scene_discard")
        sizePolicy3.setHeightForWidth(self.pushButton_default_scene_discard.sizePolicy().hasHeightForWidth())
        self.pushButton_default_scene_discard.setSizePolicy(sizePolicy3)
        self.pushButton_default_scene_discard.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        icon6 = QIcon()
        icon6.addFile(u"./icons/grey/undo.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        icon6.addFile(u"./icons/purple/undo.svg", QSize(), QIcon.Mode.Normal, QIcon.State.On)
        self.pushButton_default_scene_discard.setIcon(icon6)
        self.pushButton_default_scene_discard.setFlat(True)

        self.gridLayout_3.addWidget(self.pushButton_default_scene_discard, 0, 2, 1, 1)

        self.label_11 = QLabel(self.groupBox_default_scene_geometry)
        self.label_11.setObjectName(u"label_11")
        self.label_11.setLineWidth(0)

        self.gridLayout_3.addWidget(self.label_11, 0, 0, 1, 1)


        self.verticalLayout_2.addWidget(self.groupBox_default_scene_geometry)

        self.groupBox_scene_geometry = QGroupBox(self.frame)
        self.groupBox_scene_geometry.setObjectName(u"groupBox_scene_geometry")
        sizePolicy4.setHeightForWidth(self.groupBox_scene_geometry.sizePolicy().hasHeightForWidth())
        self.groupBox_scene_geometry.setSizePolicy(sizePolicy4)
        self.groupBox_scene_geometry.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.groupBox_scene_geometry.setCheckable(True)
        self.groupBox_scene_geometry.setChecked(True)
        self.gridLayout_2 = QGridLayout(self.groupBox_scene_geometry)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setContentsMargins(3, 9, 3, 3)
        self.label_19 = QLabel(self.groupBox_scene_geometry)
        self.label_19.setObjectName(u"label_19")
        self.label_19.setEnabled(True)
        self.label_19.setLineWidth(0)

        self.gridLayout_2.addWidget(self.label_19, 2, 0, 1, 1)

        self.label_10 = QLabel(self.groupBox_scene_geometry)
        self.label_10.setObjectName(u"label_10")
        self.label_10.setEnabled(True)
        self.label_10.setLineWidth(0)

        self.gridLayout_2.addWidget(self.label_10, 0, 0, 1, 1)

        self.lineEdit_scene_crop_rectangle = QLineEdit(self.groupBox_scene_geometry)
        self.lineEdit_scene_crop_rectangle.setObjectName(u"lineEdit_scene_crop_rectangle")
        self.lineEdit_scene_crop_rectangle.setEnabled(True)
        sizePolicy2.setHeightForWidth(self.lineEdit_scene_crop_rectangle.sizePolicy().hasHeightForWidth())
        self.lineEdit_scene_crop_rectangle.setSizePolicy(sizePolicy2)
        self.lineEdit_scene_crop_rectangle.setMinimumSize(QSize(190, 0))
        self.lineEdit_scene_crop_rectangle.setMaximumSize(QSize(190, 16777215))
        self.lineEdit_scene_crop_rectangle.setFrame(False)
        self.lineEdit_scene_crop_rectangle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lineEdit_scene_crop_rectangle.setReadOnly(True)

        self.gridLayout_2.addWidget(self.lineEdit_scene_crop_rectangle, 0, 1, 1, 1)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.checkBox_scene_keep_ratio = QCheckBox(self.groupBox_scene_geometry)
        self.checkBox_scene_keep_ratio.setObjectName(u"checkBox_scene_keep_ratio")
        self.checkBox_scene_keep_ratio.setEnabled(True)
        self.checkBox_scene_keep_ratio.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.checkBox_scene_keep_ratio.setChecked(True)

        self.horizontalLayout_3.addWidget(self.checkBox_scene_keep_ratio)

        self.checkBox_scene_fit_to_width = QCheckBox(self.groupBox_scene_geometry)
        self.checkBox_scene_fit_to_width.setObjectName(u"checkBox_scene_fit_to_width")
        self.checkBox_scene_fit_to_width.setEnabled(True)
        self.checkBox_scene_fit_to_width.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.horizontalLayout_3.addWidget(self.checkBox_scene_fit_to_width)


        self.gridLayout_2.addLayout(self.horizontalLayout_3, 2, 1, 1, 1)

        self.pushButton_scene_discard = QPushButton(self.groupBox_scene_geometry)
        self.pushButton_scene_discard.setObjectName(u"pushButton_scene_discard")
        sizePolicy3.setHeightForWidth(self.pushButton_scene_discard.sizePolicy().hasHeightForWidth())
        self.pushButton_scene_discard.setSizePolicy(sizePolicy3)
        self.pushButton_scene_discard.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.pushButton_scene_discard.setIcon(icon6)
        self.pushButton_scene_discard.setFlat(True)

        self.gridLayout_2.addWidget(self.pushButton_scene_discard, 0, 2, 1, 1)

        self.lineEdit_scene_crop_rectangle_2 = QLineEdit(self.groupBox_scene_geometry)
        self.lineEdit_scene_crop_rectangle_2.setObjectName(u"lineEdit_scene_crop_rectangle_2")
        self.lineEdit_scene_crop_rectangle_2.setEnabled(True)
        sizePolicy2.setHeightForWidth(self.lineEdit_scene_crop_rectangle_2.sizePolicy().hasHeightForWidth())
        self.lineEdit_scene_crop_rectangle_2.setSizePolicy(sizePolicy2)
        self.lineEdit_scene_crop_rectangle_2.setMinimumSize(QSize(190, 0))
        self.lineEdit_scene_crop_rectangle_2.setMaximumSize(QSize(190, 16777215))
        self.lineEdit_scene_crop_rectangle_2.setFrame(False)
        self.lineEdit_scene_crop_rectangle_2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lineEdit_scene_crop_rectangle_2.setReadOnly(True)

        self.gridLayout_2.addWidget(self.lineEdit_scene_crop_rectangle_2, 1, 1, 1, 1)

        self.label_13 = QLabel(self.groupBox_scene_geometry)
        self.label_13.setObjectName(u"label_13")
        self.label_13.setEnabled(True)
        self.label_13.setLineWidth(0)

        self.gridLayout_2.addWidget(self.label_13, 1, 0, 1, 1)

        self.pushButton_autocrop = QPushButton(self.groupBox_scene_geometry)
        self.pushButton_autocrop.setObjectName(u"pushButton_autocrop")
        sizePolicy3.setHeightForWidth(self.pushButton_autocrop.sizePolicy().hasHeightForWidth())
        self.pushButton_autocrop.setSizePolicy(sizePolicy3)
        self.pushButton_autocrop.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        icon7 = QIcon()
        icon7.addFile(u"./icons/grey/undo.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        icon7.addFile(u"./icons/blue/calculator.svg", QSize(), QIcon.Mode.Normal, QIcon.State.On)
        self.pushButton_autocrop.setIcon(icon7)
        self.pushButton_autocrop.setFlat(True)

        self.gridLayout_2.addWidget(self.pushButton_autocrop, 1, 2, 1, 1)


        self.verticalLayout_2.addWidget(self.groupBox_scene_geometry)


        self.mainLayout.addWidget(self.frame)


        self.retranslateUi(GeometryWidget)

        QMetaObject.connectSlotsByName(GeometryWidget)
    # setupUi

    def retranslateUi(self, GeometryWidget):
        self.pushButton_set_preview.setText("")
        self.label_message.setText(QCoreApplication.translate("GeometryWidget", u"disabled", None))
        self.pushButton_discard.setText("")
        self.pushButton_save.setText("")
        self.groupBox_target_geometry.setTitle(QCoreApplication.translate("GeometryWidget", u"Target", None))
        self.label_9.setText(QCoreApplication.translate("GeometryWidget", u"width", None))
        self.lineEdit_target_width.setText(QCoreApplication.translate("GeometryWidget", u"1440", None))
        self.pushButton_target_discard.setText("")
        self.pushButton_target_width_edition.setText("")
        self.pushButton_target_save.setText("")
        self.groupBox_scene_default_geometry_2.setTitle(QCoreApplication.translate("GeometryWidget", u"Preview", None))
        self.pushButton_scene_crop_preview.setText("")
        self.pushButton_scene_resize_preview.setText("")
        self.label_21.setText(QCoreApplication.translate("GeometryWidget", u"resize", None))
        self.label_12.setText(QCoreApplication.translate("GeometryWidget", u"crop", None))
        self.pushButton_scene_crop_edition.setText("")
        self.groupBox_default_scene_geometry.setTitle(QCoreApplication.translate("GeometryWidget", u"scene (default)", None))
        self.checkBox_default_scene_keep_ratio.setText(QCoreApplication.translate("GeometryWidget", u"keep ratio", None))
        self.checkBox_default_scene_fit_to_width.setText(QCoreApplication.translate("GeometryWidget", u"fit to width", None))
        self.label_20.setText(QCoreApplication.translate("GeometryWidget", u"resize", None))
        self.lineEdit_default_scene_crop_rectangle.setText(QCoreApplication.translate("GeometryWidget", u"x:10, y:10, w:5000, h:5000", None))
        self.pushButton_default_scene_discard.setText("")
        self.label_11.setText(QCoreApplication.translate("GeometryWidget", u"crop", None))
        self.groupBox_scene_geometry.setTitle(QCoreApplication.translate("GeometryWidget", u"scene (custom)", None))
        self.label_19.setText(QCoreApplication.translate("GeometryWidget", u"resize", None))
        self.label_10.setText(QCoreApplication.translate("GeometryWidget", u"crop", None))
        self.lineEdit_scene_crop_rectangle.setText(QCoreApplication.translate("GeometryWidget", u"x:10, y:10, w:5000, h:5000", None))
        self.checkBox_scene_keep_ratio.setText(QCoreApplication.translate("GeometryWidget", u"keep ratio", None))
        self.checkBox_scene_fit_to_width.setText(QCoreApplication.translate("GeometryWidget", u"fit_to_width", None))
        self.pushButton_scene_discard.setText("")
        self.lineEdit_scene_crop_rectangle_2.setText(QCoreApplication.translate("GeometryWidget", u"x:10, y:10, w:5000, h:5000", None))
        self.label_13.setText(QCoreApplication.translate("GeometryWidget", u"auto", None))
        self.pushButton_autocrop.setText("")
        pass
    # retranslateUi

