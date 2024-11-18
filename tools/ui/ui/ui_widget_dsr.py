# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_widget_dsr.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QAbstractSpinBox, QApplication, QComboBox,
    QFrame, QGridLayout, QGroupBox, QHBoxLayout,
    QHeaderView, QLabel, QLayout, QPushButton,
    QSizePolicy, QSpacerItem, QSpinBox, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget)

class Ui_DsrWidget(object):
    def setupUi(self, DsrWidget):
        if not DsrWidget.objectName():
            DsrWidget.setObjectName(u"DsrWidget")
        DsrWidget.resize(738, 1015)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(DsrWidget.sizePolicy().hasHeightForWidth())
        DsrWidget.setSizePolicy(sizePolicy)
        self.frame = QFrame(DsrWidget)
        self.frame.setObjectName(u"frame")
        self.frame.setGeometry(QRect(20, 450, 318, 505))
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
        self.frame.setSizePolicy(sizePolicy1)
        self.frame.setFrameShape(QFrame.Shape.Panel)
        self.frame.setFrameShadow(QFrame.Shadow.Plain)
        self.verticalLayout_2 = QVBoxLayout(self.frame)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(6, 6, 6, 6)
        self.groupBox_method_1 = QGroupBox(self.frame)
        self.groupBox_method_1.setObjectName(u"groupBox_method_1")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.groupBox_method_1.sizePolicy().hasHeightForWidth())
        self.groupBox_method_1.setSizePolicy(sizePolicy2)
        self.groupBox_method_1.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.groupBox_method_1.setCheckable(True)
        self.groupBox_method_1.setChecked(True)
        self.verticalLayout_3 = QVBoxLayout(self.groupBox_method_1)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.label_11 = QLabel(self.groupBox_method_1)
        self.label_11.setObjectName(u"label_11")
        self.label_11.setEnabled(True)
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.label_11.sizePolicy().hasHeightForWidth())
        self.label_11.setSizePolicy(sizePolicy3)
        self.label_11.setLineWidth(0)

        self.horizontalLayout_7.addWidget(self.label_11)

        self.comboBox = QComboBox(self.groupBox_method_1)
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.setObjectName(u"comboBox")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.comboBox.sizePolicy().hasHeightForWidth())
        self.comboBox.setSizePolicy(sizePolicy4)

        self.horizontalLayout_7.addWidget(self.comboBox)

        self.horizontalSpacer_9 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_7.addItem(self.horizontalSpacer_9)


        self.verticalLayout_3.addLayout(self.horizontalLayout_7)


        self.verticalLayout_2.addWidget(self.groupBox_method_1)

        self.groupBox_method_2 = QGroupBox(self.frame)
        self.groupBox_method_2.setObjectName(u"groupBox_method_2")
        sizePolicy2.setHeightForWidth(self.groupBox_method_2.sizePolicy().hasHeightForWidth())
        self.groupBox_method_2.setSizePolicy(sizePolicy2)
        self.groupBox_method_2.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.groupBox_method_2.setCheckable(True)
        self.groupBox_method_2.setChecked(False)
        self.verticalLayout_4 = QVBoxLayout(self.groupBox_method_2)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.label_13 = QLabel(self.groupBox_method_2)
        self.label_13.setObjectName(u"label_13")
        self.label_13.setEnabled(False)
        sizePolicy3.setHeightForWidth(self.label_13.sizePolicy().hasHeightForWidth())
        self.label_13.setSizePolicy(sizePolicy3)
        self.label_13.setLineWidth(0)

        self.horizontalLayout_8.addWidget(self.label_13)

        self.comboBox_2 = QComboBox(self.groupBox_method_2)
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.setObjectName(u"comboBox_2")
        sizePolicy4.setHeightForWidth(self.comboBox_2.sizePolicy().hasHeightForWidth())
        self.comboBox_2.setSizePolicy(sizePolicy4)

        self.horizontalLayout_8.addWidget(self.comboBox_2)

        self.horizontalSpacer_10 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_8.addItem(self.horizontalSpacer_10)


        self.verticalLayout_4.addLayout(self.horizontalLayout_8)

        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.shortcut_10 = QLabel(self.groupBox_method_2)
        self.shortcut_10.setObjectName(u"shortcut_10")
        sizePolicy3.setHeightForWidth(self.shortcut_10.sizePolicy().hasHeightForWidth())
        self.shortcut_10.setSizePolicy(sizePolicy3)
        font = QFont()
        font.setPointSize(8)
        self.shortcut_10.setFont(font)

        self.horizontalLayout_9.addWidget(self.shortcut_10)

        self.horizontalSpacer_11 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_9.addItem(self.horizontalSpacer_11)

        self.shortcut_11 = QLabel(self.groupBox_method_2)
        self.shortcut_11.setObjectName(u"shortcut_11")
        sizePolicy3.setHeightForWidth(self.shortcut_11.sizePolicy().hasHeightForWidth())
        self.shortcut_11.setSizePolicy(sizePolicy3)
        self.shortcut_11.setFont(font)

        self.horizontalLayout_9.addWidget(self.shortcut_11)

        self.horizontalSpacer_12 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_9.addItem(self.horizontalSpacer_12)


        self.verticalLayout_4.addLayout(self.horizontalLayout_9)


        self.verticalLayout_2.addWidget(self.groupBox_method_2)

        self.widget = QWidget(DsrWidget)
        self.widget.setObjectName(u"widget")
        self.widget.setGeometry(QRect(10, 10, 304, 26))
        self.horizontalLayout = QHBoxLayout(self.widget)
        self.horizontalLayout.setSpacing(3)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.pushButton_set_preview = QPushButton(self.widget)
        self.pushButton_set_preview.setObjectName(u"pushButton_set_preview")
        sizePolicy5 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.pushButton_set_preview.sizePolicy().hasHeightForWidth())
        self.pushButton_set_preview.setSizePolicy(sizePolicy5)
        self.pushButton_set_preview.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        icon = QIcon()
        icon.addFile(u"./icons/grey/eye.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        icon.addFile(u"./icons/blue/eye.svg", QSize(), QIcon.Mode.Normal, QIcon.State.On)
        self.pushButton_set_preview.setIcon(icon)
        self.pushButton_set_preview.setCheckable(True)
        self.pushButton_set_preview.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_set_preview)

        self.shortcut = QLabel(self.widget)
        self.shortcut.setObjectName(u"shortcut")
        sizePolicy5.setHeightForWidth(self.shortcut.sizePolicy().hasHeightForWidth())
        self.shortcut.setSizePolicy(sizePolicy5)
        font1 = QFont()
        font1.setPointSize(8)
        font1.setItalic(False)
        self.shortcut.setFont(font1)

        self.horizontalLayout.addWidget(self.shortcut)

        self.horizontalSpacer_2 = QSpacerItem(22, 10, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)

        self.label_message = QLabel(self.widget)
        self.label_message.setObjectName(u"label_message")

        self.horizontalLayout.addWidget(self.label_message)

        self.horizontalSpacer = QSpacerItem(5, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.pushButton_discard = QPushButton(self.widget)
        self.pushButton_discard.setObjectName(u"pushButton_discard")
        sizePolicy5.setHeightForWidth(self.pushButton_discard.sizePolicy().hasHeightForWidth())
        self.pushButton_discard.setSizePolicy(sizePolicy5)
        self.pushButton_discard.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        icon1 = QIcon()
        icon1.addFile(u"./icons/purple/undo.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.pushButton_discard.setIcon(icon1)
        self.pushButton_discard.setCheckable(False)
        self.pushButton_discard.setAutoDefault(False)
        self.pushButton_discard.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_discard)

        self.pushButton_save = QPushButton(self.widget)
        self.pushButton_save.setObjectName(u"pushButton_save")
        sizePolicy5.setHeightForWidth(self.pushButton_save.sizePolicy().hasHeightForWidth())
        self.pushButton_save.setSizePolicy(sizePolicy5)
        self.pushButton_save.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        icon2 = QIcon()
        icon2.addFile(u"./icons/purple/save.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.pushButton_save.setIcon(icon2)
        self.pushButton_save.setCheckable(False)
        self.pushButton_save.setAutoDefault(False)
        self.pushButton_save.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_save)

        self.groupBox_preview = QGroupBox(DsrWidget)
        self.groupBox_preview.setObjectName(u"groupBox_preview")
        self.groupBox_preview.setEnabled(True)
        self.groupBox_preview.setGeometry(QRect(10, 50, 324, 112))
        sizePolicy3.setHeightForWidth(self.groupBox_preview.sizePolicy().hasHeightForWidth())
        self.groupBox_preview.setSizePolicy(sizePolicy3)
        self.groupBox_preview.setCheckable(False)
        self.groupBox_preview.setChecked(False)
        self.layout_preview = QVBoxLayout(self.groupBox_preview)
        self.layout_preview.setObjectName(u"layout_preview")
        self.layout_preview.setContentsMargins(6, 6, 6, 6)
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.horizontalSpacer_3 = QSpacerItem(20, 10, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer_3, 0, 2, 1, 1)

        self.label_12 = QLabel(self.groupBox_preview)
        self.label_12.setObjectName(u"label_12")
        self.label_12.setLineWidth(0)
        self.label_12.setText(u"overlay")
        self.label_12.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout.addWidget(self.label_12, 0, 0, 1, 1)

        self.pushButton_scene_crop_preview = QPushButton(self.groupBox_preview)
        self.pushButton_scene_crop_preview.setObjectName(u"pushButton_scene_crop_preview")
        self.pushButton_scene_crop_preview.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.pushButton_scene_crop_preview.setText(u"")
        self.pushButton_scene_crop_preview.setIcon(icon)
        self.pushButton_scene_crop_preview.setCheckable(True)
        self.pushButton_scene_crop_preview.setFlat(True)

        self.gridLayout.addWidget(self.pushButton_scene_crop_preview, 0, 1, 1, 1)

        self.pushButton_scene_resize_preview = QPushButton(self.groupBox_preview)
        self.pushButton_scene_resize_preview.setObjectName(u"pushButton_scene_resize_preview")
        self.pushButton_scene_resize_preview.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.pushButton_scene_resize_preview.setText(u"")
        self.pushButton_scene_resize_preview.setIcon(icon)
        self.pushButton_scene_resize_preview.setCheckable(True)
        self.pushButton_scene_resize_preview.setFlat(True)

        self.gridLayout.addWidget(self.pushButton_scene_resize_preview, 0, 4, 1, 1)

        self.label_21 = QLabel(self.groupBox_preview)
        self.label_21.setObjectName(u"label_21")
        self.label_21.setLineWidth(0)
        self.label_21.setText(u"mask")
        self.label_21.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout.addWidget(self.label_21, 0, 3, 1, 1)

        self.shortcut_4 = QLabel(self.groupBox_preview)
        self.shortcut_4.setObjectName(u"shortcut_4")
        sizePolicy.setHeightForWidth(self.shortcut_4.sizePolicy().hasHeightForWidth())
        self.shortcut_4.setSizePolicy(sizePolicy)
        self.shortcut_4.setFont(font)
        self.shortcut_4.setText(u"(F3)")
        self.shortcut_4.setAlignment(Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignTop)

        self.gridLayout.addWidget(self.shortcut_4, 1, 1, 1, 1)

        self.shortcut_5 = QLabel(self.groupBox_preview)
        self.shortcut_5.setObjectName(u"shortcut_5")
        sizePolicy.setHeightForWidth(self.shortcut_5.sizePolicy().hasHeightForWidth())
        self.shortcut_5.setSizePolicy(sizePolicy)
        self.shortcut_5.setFont(font)
        self.shortcut_5.setText(u"F4")
        self.shortcut_5.setAlignment(Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignTop)

        self.gridLayout.addWidget(self.shortcut_5, 1, 4, 1, 1)


        self.layout_preview.addLayout(self.gridLayout)

        self.line = QFrame(self.groupBox_preview)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.layout_preview.addWidget(self.line)

        self.widget_channel_preview = QWidget(self.groupBox_preview)
        self.widget_channel_preview.setObjectName(u"widget_channel_preview")
        sizePolicy6 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        sizePolicy6.setHorizontalStretch(0)
        sizePolicy6.setVerticalStretch(0)
        sizePolicy6.setHeightForWidth(self.widget_channel_preview.sizePolicy().hasHeightForWidth())
        self.widget_channel_preview.setSizePolicy(sizePolicy6)
        self.widget_channel_preview.setMinimumSize(QSize(300, 0))

        self.layout_preview.addWidget(self.widget_channel_preview)

        self.horizontalLayoutWidget = QWidget(DsrWidget)
        self.horizontalLayoutWidget.setObjectName(u"horizontalLayoutWidget")
        self.horizontalLayoutWidget.setGeometry(QRect(10, 170, 311, 41))
        self.layout_passes = QHBoxLayout(self.horizontalLayoutWidget)
        self.layout_passes.setObjectName(u"layout_passes")
        self.layout_passes.setContentsMargins(0, 0, 0, 0)
        self.widget_pass1 = QWidget(self.horizontalLayoutWidget)
        self.widget_pass1.setObjectName(u"widget_pass1")
        self.verticalLayout_5 = QVBoxLayout(self.widget_pass1)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.label_2 = QLabel(self.widget_pass1)
        self.label_2.setObjectName(u"label_2")
        sizePolicy1.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy1)
        self.label_2.setMaximumSize(QSize(16777215, 100))
        self.label_2.setAlignment(Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignTop)

        self.verticalLayout_5.addWidget(self.label_2)


        self.layout_passes.addWidget(self.widget_pass1)

        self.widget_pass2 = QWidget(self.horizontalLayoutWidget)
        self.widget_pass2.setObjectName(u"widget_pass2")
        sizePolicy7 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy7.setHorizontalStretch(0)
        sizePolicy7.setVerticalStretch(0)
        sizePolicy7.setHeightForWidth(self.widget_pass2.sizePolicy().hasHeightForWidth())
        self.widget_pass2.setSizePolicy(sizePolicy7)
        self.verticalLayout = QVBoxLayout(self.widget_pass2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label_3 = QLabel(self.widget_pass2)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setAlignment(Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignTop)

        self.verticalLayout.addWidget(self.label_3)


        self.layout_passes.addWidget(self.widget_pass2)

        self.tableWidget_dsr = QTableWidget(DsrWidget)
        if (self.tableWidget_dsr.columnCount() < 3):
            self.tableWidget_dsr.setColumnCount(3)
        __qtablewidgetitem = QTableWidgetItem()
        self.tableWidget_dsr.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.tableWidget_dsr.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.tableWidget_dsr.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        if (self.tableWidget_dsr.rowCount() < 10):
            self.tableWidget_dsr.setRowCount(10)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.tableWidget_dsr.setItem(0, 1, __qtablewidgetitem3)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.tableWidget_dsr.setItem(0, 2, __qtablewidgetitem4)
        self.tableWidget_dsr.setObjectName(u"tableWidget_dsr")
        self.tableWidget_dsr.setGeometry(QRect(370, 590, 304, 315))
        sizePolicy8 = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding)
        sizePolicy8.setHorizontalStretch(0)
        sizePolicy8.setVerticalStretch(0)
        sizePolicy8.setHeightForWidth(self.tableWidget_dsr.sizePolicy().hasHeightForWidth())
        self.tableWidget_dsr.setSizePolicy(sizePolicy8)
        self.tableWidget_dsr.setFrameShape(QFrame.Shape.StyledPanel)
        self.tableWidget_dsr.setFrameShadow(QFrame.Shadow.Sunken)
        self.tableWidget_dsr.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tableWidget_dsr.setEditTriggers(QAbstractItemView.EditTrigger.SelectedClicked)
        self.tableWidget_dsr.setProperty(u"showDropIndicator", False)
        self.tableWidget_dsr.setDragDropOverwriteMode(False)
        self.tableWidget_dsr.setSelectionMode(QAbstractItemView.SelectionMode.ContiguousSelection)
        self.tableWidget_dsr.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableWidget_dsr.setSortingEnabled(False)
        self.tableWidget_dsr.setRowCount(10)
        self.tableWidget_dsr.horizontalHeader().setDefaultSectionSize(90)
        self.tableWidget_dsr.horizontalHeader().setStretchLastSection(True)
        self.tableWidget_dsr.verticalHeader().setVisible(False)
        self.tableWidget_dsr.verticalHeader().setMinimumSectionSize(22)
        self.tableWidget_dsr.verticalHeader().setDefaultSectionSize(22)
        self.horizontalLayoutWidget_2 = QWidget(DsrWidget)
        self.horizontalLayoutWidget_2.setObjectName(u"horizontalLayoutWidget_2")
        self.horizontalLayoutWidget_2.setGeometry(QRect(440, 300, 199, 26))
        self.layout_gaussian = QHBoxLayout(self.horizontalLayoutWidget_2)
        self.layout_gaussian.setObjectName(u"layout_gaussian")
        self.layout_gaussian.setContentsMargins(0, 0, 0, 0)
        self.label_gaussian = QLabel(self.horizontalLayoutWidget_2)
        self.label_gaussian.setObjectName(u"label_gaussian")
        self.label_gaussian.setText(u"Gaussian blur, radius")
        self.label_gaussian.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.layout_gaussian.addWidget(self.label_gaussian)

        self.spinBox_gaussian_radius = QSpinBox(self.horizontalLayoutWidget_2)
        self.spinBox_gaussian_radius.setObjectName(u"spinBox_gaussian_radius")
        self.spinBox_gaussian_radius.setMaximumSize(QSize(60, 16777215))
        self.spinBox_gaussian_radius.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.spinBox_gaussian_radius.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.spinBox_gaussian_radius.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        self.spinBox_gaussian_radius.setSuffix(u"")
        self.spinBox_gaussian_radius.setPrefix(u"")
        self.spinBox_gaussian_radius.setMaximum(255)
        self.spinBox_gaussian_radius.setValue(15)

        self.layout_gaussian.addWidget(self.spinBox_gaussian_radius)


        self.retranslateUi(DsrWidget)

        QMetaObject.connectSlotsByName(DsrWidget)
    # setupUi

    def retranslateUi(self, DsrWidget):
        self.groupBox_method_1.setTitle(QCoreApplication.translate("DsrWidget", u"method 1", None))
        self.label_11.setText(QCoreApplication.translate("DsrWidget", u"Adaptative threshold", None))
        self.comboBox.setItemText(0, QCoreApplication.translate("DsrWidget", u"Mean", None))
        self.comboBox.setItemText(1, QCoreApplication.translate("DsrWidget", u"Gaussian", None))

        self.groupBox_method_2.setTitle(QCoreApplication.translate("DsrWidget", u"method 2", None))
        self.label_13.setText(QCoreApplication.translate("DsrWidget", u"Adaptative threshold", None))
        self.comboBox_2.setItemText(0, QCoreApplication.translate("DsrWidget", u"Mean", None))
        self.comboBox_2.setItemText(1, QCoreApplication.translate("DsrWidget", u"Gaussian", None))

        self.shortcut_10.setText(QCoreApplication.translate("DsrWidget", u"(R)", None))
        self.shortcut_11.setText(QCoreApplication.translate("DsrWidget", u"(F)", None))
        self.pushButton_set_preview.setText("")
        self.shortcut.setText(QCoreApplication.translate("DsrWidget", u"(F2)", None))
        self.label_message.setText(QCoreApplication.translate("DsrWidget", u"disabled", None))
        self.pushButton_discard.setText("")
        self.pushButton_save.setText("")
        self.groupBox_preview.setTitle(QCoreApplication.translate("DsrWidget", u"Preview", None))
        self.label_2.setText(QCoreApplication.translate("DsrWidget", u"Pass1", None))
        self.label_3.setText(QCoreApplication.translate("DsrWidget", u"Pass2", None))
        ___qtablewidgetitem = self.tableWidget_dsr.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("DsrWidget", u"scene", None));
        ___qtablewidgetitem1 = self.tableWidget_dsr.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("DsrWidget", u"frame", None));
        ___qtablewidgetitem2 = self.tableWidget_dsr.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("DsrWidget", u"patches", None));

        __sortingEnabled = self.tableWidget_dsr.isSortingEnabled()
        self.tableWidget_dsr.setSortingEnabled(False)
        ___qtablewidgetitem3 = self.tableWidget_dsr.item(0, 1)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("DsrWidget", u"123456", None));
        ___qtablewidgetitem4 = self.tableWidget_dsr.item(0, 2)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("DsrWidget", u"654321", None));
        self.tableWidget_dsr.setSortingEnabled(__sortingEnabled)

        pass
    # retranslateUi

