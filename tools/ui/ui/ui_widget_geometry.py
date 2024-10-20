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
from PySide6.QtWidgets import (QAbstractSpinBox, QApplication, QCheckBox, QFormLayout,
    QFrame, QGridLayout, QGroupBox, QHBoxLayout,
    QLabel, QLayout, QLineEdit, QPushButton,
    QSizePolicy, QSpacerItem, QSpinBox, QVBoxLayout,
    QWidget)

class Ui_GeometryWidget(object):
    def setupUi(self, GeometryWidget):
        if not GeometryWidget.objectName():
            GeometryWidget.setObjectName(u"GeometryWidget")
        GeometryWidget.resize(317, 627)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(GeometryWidget.sizePolicy().hasHeightForWidth())
        GeometryWidget.setSizePolicy(sizePolicy)
        self.mainLayout = QVBoxLayout(GeometryWidget)
        self.mainLayout.setSpacing(9)
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

        self.shortcut = QLabel(self.frame)
        self.shortcut.setObjectName(u"shortcut")
        sizePolicy1.setHeightForWidth(self.shortcut.sizePolicy().hasHeightForWidth())
        self.shortcut.setSizePolicy(sizePolicy1)
        font = QFont()
        font.setPointSize(8)
        font.setItalic(False)
        self.shortcut.setFont(font)

        self.horizontalLayout.addWidget(self.shortcut)

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
        self._2 = QGridLayout(self.groupBox_target_geometry)
        self._2.setObjectName(u"_2")
        self.pushButton_target_width_edition = QPushButton(self.groupBox_target_geometry)
        self.pushButton_target_width_edition.setObjectName(u"pushButton_target_width_edition")
        self.pushButton_target_width_edition.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        icon3 = QIcon()
        icon3.addFile(u"./icons/grey/box-select.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        icon3.addFile(u"./icons/blue/box-select.svg", QSize(), QIcon.Mode.Normal, QIcon.State.On)
        icon3.addFile(u"./icons/grey/box-select.svg", QSize(), QIcon.Mode.Disabled, QIcon.State.Off)
        icon3.addFile(u"./icons/grey/box-select.svg", QSize(), QIcon.Mode.Disabled, QIcon.State.On)
        self.pushButton_target_width_edition.setIcon(icon3)
        self.pushButton_target_width_edition.setCheckable(True)
        self.pushButton_target_width_edition.setFlat(True)

        self._2.addWidget(self.pushButton_target_width_edition, 0, 1, 1, 1)

        self.pushButton_target_discard = QPushButton(self.groupBox_target_geometry)
        self.pushButton_target_discard.setObjectName(u"pushButton_target_discard")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.pushButton_target_discard.sizePolicy().hasHeightForWidth())
        self.pushButton_target_discard.setSizePolicy(sizePolicy2)
        self.pushButton_target_discard.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        icon4 = QIcon()
        icon4.addFile(u"./icons/purple/undo.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        icon4.addFile(u"./icons/purple/undo.svg", QSize(), QIcon.Mode.Normal, QIcon.State.On)
        self.pushButton_target_discard.setIcon(icon4)
        self.pushButton_target_discard.setFlat(True)

        self._2.addWidget(self.pushButton_target_discard, 0, 4, 1, 1)

        self.pushButton_target_save = QPushButton(self.groupBox_target_geometry)
        self.pushButton_target_save.setObjectName(u"pushButton_target_save")
        sizePolicy1.setHeightForWidth(self.pushButton_target_save.sizePolicy().hasHeightForWidth())
        self.pushButton_target_save.setSizePolicy(sizePolicy1)
        self.pushButton_target_save.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.pushButton_target_save.setIcon(icon2)
        self.pushButton_target_save.setCheckable(False)
        self.pushButton_target_save.setAutoDefault(False)
        self.pushButton_target_save.setFlat(True)

        self._2.addWidget(self.pushButton_target_save, 0, 5, 1, 1)

        self.lineEdit_target_width = QLineEdit(self.groupBox_target_geometry)
        self.lineEdit_target_width.setObjectName(u"lineEdit_target_width")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.lineEdit_target_width.sizePolicy().hasHeightForWidth())
        self.lineEdit_target_width.setSizePolicy(sizePolicy3)
        self.lineEdit_target_width.setMinimumSize(QSize(40, 0))
        self.lineEdit_target_width.setMaximumSize(QSize(40, 16777215))
        self.lineEdit_target_width.setFrame(False)
        self.lineEdit_target_width.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lineEdit_target_width.setReadOnly(True)

        self._2.addWidget(self.lineEdit_target_width, 0, 3, 1, 1)

        self.label_9 = QLabel(self.groupBox_target_geometry)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setLineWidth(0)

        self._2.addWidget(self.label_9, 0, 0, 1, 1)

        self.shortcut_2 = QLabel(self.groupBox_target_geometry)
        self.shortcut_2.setObjectName(u"shortcut_2")
        font1 = QFont()
        font1.setPointSize(8)
        self.shortcut_2.setFont(font1)

        self._2.addWidget(self.shortcut_2, 1, 1, 1, 1)


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
        self._3 = QGridLayout(self.groupBox_scene_default_geometry_2)
        self._3.setObjectName(u"_3")
        self.horizontalSpacer_3 = QSpacerItem(20, 10, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self._3.addItem(self.horizontalSpacer_3, 0, 3, 1, 1)

        self.shortcut_3 = QLabel(self.groupBox_scene_default_geometry_2)
        self.shortcut_3.setObjectName(u"shortcut_3")
        self.shortcut_3.setFont(font1)

        self._3.addWidget(self.shortcut_3, 1, 1, 1, 1)

        self.shortcut_4 = QLabel(self.groupBox_scene_default_geometry_2)
        self.shortcut_4.setObjectName(u"shortcut_4")
        self.shortcut_4.setFont(font1)

        self._3.addWidget(self.shortcut_4, 1, 2, 1, 1)

        self.label_12 = QLabel(self.groupBox_scene_default_geometry_2)
        self.label_12.setObjectName(u"label_12")
        self.label_12.setLineWidth(0)

        self._3.addWidget(self.label_12, 0, 0, 1, 1)

        self.pushButton_scene_crop_preview = QPushButton(self.groupBox_scene_default_geometry_2)
        self.pushButton_scene_crop_preview.setObjectName(u"pushButton_scene_crop_preview")
        self.pushButton_scene_crop_preview.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.pushButton_scene_crop_preview.setIcon(icon)
        self.pushButton_scene_crop_preview.setCheckable(True)
        self.pushButton_scene_crop_preview.setFlat(True)

        self._3.addWidget(self.pushButton_scene_crop_preview, 0, 2, 1, 1)

        self.label_21 = QLabel(self.groupBox_scene_default_geometry_2)
        self.label_21.setObjectName(u"label_21")
        self.label_21.setLineWidth(0)

        self._3.addWidget(self.label_21, 0, 4, 1, 1)

        self.shortcut_5 = QLabel(self.groupBox_scene_default_geometry_2)
        self.shortcut_5.setObjectName(u"shortcut_5")
        self.shortcut_5.setFont(font1)

        self._3.addWidget(self.shortcut_5, 1, 5, 1, 1)

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

        self._3.addWidget(self.pushButton_scene_crop_edition, 0, 1, 1, 1)

        self.pushButton_scene_resize_preview = QPushButton(self.groupBox_scene_default_geometry_2)
        self.pushButton_scene_resize_preview.setObjectName(u"pushButton_scene_resize_preview")
        self.pushButton_scene_resize_preview.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.pushButton_scene_resize_preview.setIcon(icon)
        self.pushButton_scene_resize_preview.setCheckable(True)
        self.pushButton_scene_resize_preview.setFlat(True)

        self._3.addWidget(self.pushButton_scene_resize_preview, 0, 5, 1, 1)


        self.verticalLayout_2.addWidget(self.groupBox_scene_default_geometry_2)

        self.groupBox_scene_geometry = QGroupBox(self.frame)
        self.groupBox_scene_geometry.setObjectName(u"groupBox_scene_geometry")
        sizePolicy4.setHeightForWidth(self.groupBox_scene_geometry.sizePolicy().hasHeightForWidth())
        self.groupBox_scene_geometry.setSizePolicy(sizePolicy4)
        self.groupBox_scene_geometry.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.groupBox_scene_geometry.setCheckable(False)
        self.groupBox_scene_geometry.setChecked(False)
        self.gridLayout_2 = QGridLayout(self.groupBox_scene_geometry)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.pushButton_scene_discard = QPushButton(self.groupBox_scene_geometry)
        self.pushButton_scene_discard.setObjectName(u"pushButton_scene_discard")
        sizePolicy2.setHeightForWidth(self.pushButton_scene_discard.sizePolicy().hasHeightForWidth())
        self.pushButton_scene_discard.setSizePolicy(sizePolicy2)
        self.pushButton_scene_discard.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        icon6 = QIcon()
        icon6.addFile(u"./icons/grey/undo.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        icon6.addFile(u"./icons/purple/undo.svg", QSize(), QIcon.Mode.Normal, QIcon.State.On)
        self.pushButton_scene_discard.setIcon(icon6)
        self.pushButton_scene_discard.setFlat(True)

        self.gridLayout_2.addWidget(self.pushButton_scene_discard, 0, 2, 1, 1)

        self.label_10 = QLabel(self.groupBox_scene_geometry)
        self.label_10.setObjectName(u"label_10")
        self.label_10.setEnabled(True)
        self.label_10.setLineWidth(0)

        self.gridLayout_2.addWidget(self.label_10, 0, 0, 1, 1)

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


        self.gridLayout_2.addLayout(self.horizontalLayout_3, 1, 1, 1, 1)

        self.lineEdit_scene_crop_rectangle = QLineEdit(self.groupBox_scene_geometry)
        self.lineEdit_scene_crop_rectangle.setObjectName(u"lineEdit_scene_crop_rectangle")
        self.lineEdit_scene_crop_rectangle.setEnabled(True)
        sizePolicy3.setHeightForWidth(self.lineEdit_scene_crop_rectangle.sizePolicy().hasHeightForWidth())
        self.lineEdit_scene_crop_rectangle.setSizePolicy(sizePolicy3)
        self.lineEdit_scene_crop_rectangle.setMinimumSize(QSize(190, 0))
        self.lineEdit_scene_crop_rectangle.setMaximumSize(QSize(190, 16777215))
        self.lineEdit_scene_crop_rectangle.setFrame(False)
        self.lineEdit_scene_crop_rectangle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lineEdit_scene_crop_rectangle.setReadOnly(True)

        self.gridLayout_2.addWidget(self.lineEdit_scene_crop_rectangle, 0, 1, 1, 1)

        self.label_19 = QLabel(self.groupBox_scene_geometry)
        self.label_19.setObjectName(u"label_19")
        self.label_19.setEnabled(True)
        self.label_19.setLineWidth(0)

        self.gridLayout_2.addWidget(self.label_19, 1, 0, 1, 1)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.shortcut_6 = QLabel(self.groupBox_scene_geometry)
        self.shortcut_6.setObjectName(u"shortcut_6")
        sizePolicy4.setHeightForWidth(self.shortcut_6.sizePolicy().hasHeightForWidth())
        self.shortcut_6.setSizePolicy(sizePolicy4)
        self.shortcut_6.setFont(font1)

        self.horizontalLayout_4.addWidget(self.shortcut_6)

        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_5)

        self.shortcut_7 = QLabel(self.groupBox_scene_geometry)
        self.shortcut_7.setObjectName(u"shortcut_7")
        sizePolicy4.setHeightForWidth(self.shortcut_7.sizePolicy().hasHeightForWidth())
        self.shortcut_7.setSizePolicy(sizePolicy4)
        self.shortcut_7.setFont(font1)

        self.horizontalLayout_4.addWidget(self.shortcut_7)

        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_6)


        self.gridLayout_2.addLayout(self.horizontalLayout_4, 3, 1, 1, 1)


        self.verticalLayout_2.addWidget(self.groupBox_scene_geometry)

        self.groupBox_autocrop = QGroupBox(self.frame)
        self.groupBox_autocrop.setObjectName(u"groupBox_autocrop")
        self.verticalLayout = QVBoxLayout(self.groupBox_autocrop)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.formLayout_3 = QFormLayout()
        self.formLayout_3.setObjectName(u"formLayout_3")
        self.formLayout_3.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.label = QLabel(self.groupBox_autocrop)
        self.label.setObjectName(u"label")

        self.formLayout_3.setWidget(0, QFormLayout.LabelRole, self.label)

        self.spinBox_threshold_min = QSpinBox(self.groupBox_autocrop)
        self.spinBox_threshold_min.setObjectName(u"spinBox_threshold_min")
        self.spinBox_threshold_min.setMaximumSize(QSize(60, 16777215))
        self.spinBox_threshold_min.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.spinBox_threshold_min.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.spinBox_threshold_min.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        self.spinBox_threshold_min.setMaximum(127)
        self.spinBox_threshold_min.setValue(10)

        self.formLayout_3.setWidget(0, QFormLayout.FieldRole, self.spinBox_threshold_min)

        self.label_2 = QLabel(self.groupBox_autocrop)
        self.label_2.setObjectName(u"label_2")

        self.formLayout_3.setWidget(1, QFormLayout.LabelRole, self.label_2)

        self.spinBox_morph_kernel_radius = QSpinBox(self.groupBox_autocrop)
        self.spinBox_morph_kernel_radius.setObjectName(u"spinBox_morph_kernel_radius")
        self.spinBox_morph_kernel_radius.setMaximumSize(QSize(60, 16777215))
        self.spinBox_morph_kernel_radius.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.spinBox_morph_kernel_radius.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.spinBox_morph_kernel_radius.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        self.spinBox_morph_kernel_radius.setMinimum(0)
        self.spinBox_morph_kernel_radius.setMaximum(11)
        self.spinBox_morph_kernel_radius.setValue(3)

        self.formLayout_3.setWidget(1, QFormLayout.FieldRole, self.spinBox_morph_kernel_radius)

        self.label_3 = QLabel(self.groupBox_autocrop)
        self.label_3.setObjectName(u"label_3")

        self.formLayout_3.setWidget(2, QFormLayout.LabelRole, self.label_3)

        self.spinBox_erode_kernel_radius = QSpinBox(self.groupBox_autocrop)
        self.spinBox_erode_kernel_radius.setObjectName(u"spinBox_erode_kernel_radius")
        self.spinBox_erode_kernel_radius.setMaximumSize(QSize(60, 16777215))
        self.spinBox_erode_kernel_radius.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.spinBox_erode_kernel_radius.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.spinBox_erode_kernel_radius.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        self.spinBox_erode_kernel_radius.setMaximum(11)

        self.formLayout_3.setWidget(2, QFormLayout.FieldRole, self.spinBox_erode_kernel_radius)

        self.label_4 = QLabel(self.groupBox_autocrop)
        self.label_4.setObjectName(u"label_4")

        self.formLayout_3.setWidget(3, QFormLayout.LabelRole, self.label_4)

        self.spinBox_erode_iterations = QSpinBox(self.groupBox_autocrop)
        self.spinBox_erode_iterations.setObjectName(u"spinBox_erode_iterations")
        self.spinBox_erode_iterations.setMaximumSize(QSize(60, 16777215))
        self.spinBox_erode_iterations.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.spinBox_erode_iterations.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.spinBox_erode_iterations.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        self.spinBox_erode_iterations.setMaximum(3)
        self.spinBox_erode_iterations.setValue(2)

        self.formLayout_3.setWidget(3, QFormLayout.FieldRole, self.spinBox_erode_iterations)

        self.label_5 = QLabel(self.groupBox_autocrop)
        self.label_5.setObjectName(u"label_5")

        self.formLayout_3.setWidget(4, QFormLayout.LabelRole, self.label_5)

        self.checkBox_do_add_borders = QCheckBox(self.groupBox_autocrop)
        self.checkBox_do_add_borders.setObjectName(u"checkBox_do_add_borders")
        self.checkBox_do_add_borders.setMaximumSize(QSize(60, 16777215))
        self.checkBox_do_add_borders.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.checkBox_do_add_borders.setText(u"")

        self.formLayout_3.setWidget(4, QFormLayout.FieldRole, self.checkBox_do_add_borders)

        self.pushButton_calculate = QPushButton(self.groupBox_autocrop)
        self.pushButton_calculate.setObjectName(u"pushButton_calculate")
        sizePolicy2.setHeightForWidth(self.pushButton_calculate.sizePolicy().hasHeightForWidth())
        self.pushButton_calculate.setSizePolicy(sizePolicy2)
        self.pushButton_calculate.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.formLayout_3.setWidget(5, QFormLayout.FieldRole, self.pushButton_calculate)

        self.pushButton_default = QPushButton(self.groupBox_autocrop)
        self.pushButton_default.setObjectName(u"pushButton_default")
        self.pushButton_default.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.pushButton_default.setText(u"default")

        self.formLayout_3.setWidget(5, QFormLayout.LabelRole, self.pushButton_default)


        self.verticalLayout.addLayout(self.formLayout_3)

        self.lineEdit_scene_autocrop = QLineEdit(self.groupBox_autocrop)
        self.lineEdit_scene_autocrop.setObjectName(u"lineEdit_scene_autocrop")
        self.lineEdit_scene_autocrop.setEnabled(True)
        sizePolicy3.setHeightForWidth(self.lineEdit_scene_autocrop.sizePolicy().hasHeightForWidth())
        self.lineEdit_scene_autocrop.setSizePolicy(sizePolicy3)
        self.lineEdit_scene_autocrop.setMinimumSize(QSize(190, 0))
        self.lineEdit_scene_autocrop.setMaximumSize(QSize(190, 16777215))
        self.lineEdit_scene_autocrop.setFrame(False)
        self.lineEdit_scene_autocrop.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lineEdit_scene_autocrop.setReadOnly(True)

        self.verticalLayout.addWidget(self.lineEdit_scene_autocrop)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(-1, -1, -1, 0)
        self.pushButton_copy_to_scene = QPushButton(self.groupBox_autocrop)
        self.pushButton_copy_to_scene.setObjectName(u"pushButton_copy_to_scene")
        sizePolicy2.setHeightForWidth(self.pushButton_copy_to_scene.sizePolicy().hasHeightForWidth())
        self.pushButton_copy_to_scene.setSizePolicy(sizePolicy2)
        self.pushButton_copy_to_scene.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.horizontalLayout_2.addWidget(self.pushButton_copy_to_scene)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_4)

        self.label_6 = QLabel(self.groupBox_autocrop)
        self.label_6.setObjectName(u"label_6")

        self.horizontalLayout_2.addWidget(self.label_6)

        self.checkBox_use_autocrop = QCheckBox(self.groupBox_autocrop)
        self.checkBox_use_autocrop.setObjectName(u"checkBox_use_autocrop")
        self.checkBox_use_autocrop.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.checkBox_use_autocrop.setText(u"")

        self.horizontalLayout_2.addWidget(self.checkBox_use_autocrop)


        self.verticalLayout.addLayout(self.horizontalLayout_2)


        self.verticalLayout_2.addWidget(self.groupBox_autocrop)


        self.mainLayout.addWidget(self.frame)


        self.retranslateUi(GeometryWidget)

        QMetaObject.connectSlotsByName(GeometryWidget)
    # setupUi

    def retranslateUi(self, GeometryWidget):
        self.pushButton_set_preview.setText("")
        self.shortcut.setText(QCoreApplication.translate("GeometryWidget", u"(F2)", None))
        self.label_message.setText(QCoreApplication.translate("GeometryWidget", u"disabled", None))
        self.pushButton_discard.setText("")
        self.pushButton_save.setText("")
        self.groupBox_target_geometry.setTitle(QCoreApplication.translate("GeometryWidget", u"Target", None))
        self.pushButton_target_width_edition.setText("")
        self.pushButton_target_discard.setText("")
        self.pushButton_target_save.setText("")
        self.lineEdit_target_width.setText(QCoreApplication.translate("GeometryWidget", u"1440", None))
        self.label_9.setText(QCoreApplication.translate("GeometryWidget", u"width", None))
        self.shortcut_2.setText(QCoreApplication.translate("GeometryWidget", u"(F3)", None))
        self.groupBox_scene_default_geometry_2.setTitle(QCoreApplication.translate("GeometryWidget", u"Preview", None))
        self.shortcut_3.setText(QCoreApplication.translate("GeometryWidget", u"(F4)", None))
        self.shortcut_4.setText(QCoreApplication.translate("GeometryWidget", u"(F5)", None))
        self.label_12.setText(QCoreApplication.translate("GeometryWidget", u"crop", None))
        self.pushButton_scene_crop_preview.setText("")
        self.label_21.setText(QCoreApplication.translate("GeometryWidget", u"resize", None))
        self.shortcut_5.setText(QCoreApplication.translate("GeometryWidget", u"(F6)", None))
        self.pushButton_scene_crop_edition.setText("")
        self.pushButton_scene_resize_preview.setText("")
        self.groupBox_scene_geometry.setTitle(QCoreApplication.translate("GeometryWidget", u"Scene", None))
        self.pushButton_scene_discard.setText("")
        self.label_10.setText(QCoreApplication.translate("GeometryWidget", u"crop", None))
        self.checkBox_scene_keep_ratio.setText(QCoreApplication.translate("GeometryWidget", u"keep ratio", None))
        self.checkBox_scene_fit_to_width.setText(QCoreApplication.translate("GeometryWidget", u"fit_to_width", None))
        self.lineEdit_scene_crop_rectangle.setText(QCoreApplication.translate("GeometryWidget", u"x:10, y:10, w:5000, h:5000", None))
        self.label_19.setText(QCoreApplication.translate("GeometryWidget", u"resize", None))
        self.shortcut_6.setText(QCoreApplication.translate("GeometryWidget", u"(R)", None))
        self.shortcut_7.setText(QCoreApplication.translate("GeometryWidget", u"(F)", None))
        self.groupBox_autocrop.setTitle(QCoreApplication.translate("GeometryWidget", u"Autocrop", None))
        self.label.setText(QCoreApplication.translate("GeometryWidget", u"Threshold (min)", None))
        self.label_2.setText(QCoreApplication.translate("GeometryWidget", u"Morph kernel radius", None))
        self.label_3.setText(QCoreApplication.translate("GeometryWidget", u"Erode kernel radius", None))
        self.label_4.setText(QCoreApplication.translate("GeometryWidget", u"Erode iterations", None))
        self.label_5.setText(QCoreApplication.translate("GeometryWidget", u"Add borders before", None))
        self.pushButton_calculate.setText(QCoreApplication.translate("GeometryWidget", u"Calculate (F7)", None))
        self.lineEdit_scene_autocrop.setText(QCoreApplication.translate("GeometryWidget", u"x:10, y:10, w:5000, h:5000", None))
        self.pushButton_copy_to_scene.setText(QCoreApplication.translate("GeometryWidget", u"copy to scene", None))
        self.label_6.setText(QCoreApplication.translate("GeometryWidget", u"use", None))
        pass
    # retranslateUi

