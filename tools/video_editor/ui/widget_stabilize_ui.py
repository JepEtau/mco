# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_widget_stabilize.ui'
##
## Created by: Qt User Interface Compiler version 6.4.3
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
from PySide6.QtWidgets import (QAbstractItemView, QAbstractScrollArea, QApplication, QCheckBox,
    QFrame, QGridLayout, QGroupBox, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QPushButton,
    QRadioButton, QSizePolicy, QSpacerItem, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget)

class Ui_widget_stabilize(object):
    def setupUi(self, widget_stabilize):
        if not widget_stabilize.objectName():
            widget_stabilize.setObjectName(u"widget_stabilize")
        widget_stabilize.resize(492, 370)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(widget_stabilize.sizePolicy().hasHeightForWidth())
        widget_stabilize.setSizePolicy(sizePolicy)
        widget_stabilize.setMinimumSize(QSize(0, 370))
        self.mainLayout = QVBoxLayout(widget_stabilize)
        self.mainLayout.setSpacing(0)
        self.mainLayout.setObjectName(u"mainLayout")
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.frame = QFrame(widget_stabilize)
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
        sizePolicy1 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.pushButton_set_preview.sizePolicy().hasHeightForWidth())
        self.pushButton_set_preview.setSizePolicy(sizePolicy1)
        self.pushButton_set_preview.setFocusPolicy(Qt.NoFocus)
        icon = QIcon()
        icon.addFile(u"icons/blue/eye.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon.addFile(u"icons/blue/eye.svg", QSize(), QIcon.Normal, QIcon.On)
        self.pushButton_set_preview.setIcon(icon)
        self.pushButton_set_preview.setCheckable(True)
        self.pushButton_set_preview.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_set_preview)

        self.pushButton_guidelines = QPushButton(self.frame)
        self.pushButton_guidelines.setObjectName(u"pushButton_guidelines")
        sizePolicy1.setHeightForWidth(self.pushButton_guidelines.sizePolicy().hasHeightForWidth())
        self.pushButton_guidelines.setSizePolicy(sizePolicy1)
        self.pushButton_guidelines.setFocusPolicy(Qt.NoFocus)
        icon1 = QIcon()
        icon1.addFile(u"icons/grey/frame.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon1.addFile(u"icons/blue/frame.svg", QSize(), QIcon.Normal, QIcon.On)
        self.pushButton_guidelines.setIcon(icon1)
        self.pushButton_guidelines.setCheckable(True)
        self.pushButton_guidelines.setAutoDefault(False)
        self.pushButton_guidelines.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_guidelines)

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

        self.pushButton_save = QPushButton(self.frame)
        self.pushButton_save.setObjectName(u"pushButton_save")
        sizePolicy1.setHeightForWidth(self.pushButton_save.sizePolicy().hasHeightForWidth())
        self.pushButton_save.setSizePolicy(sizePolicy1)
        self.pushButton_save.setFocusPolicy(Qt.NoFocus)
        icon3 = QIcon()
        icon3.addFile(u"icons/purple/save.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_save.setIcon(icon3)
        self.pushButton_save.setCheckable(False)
        self.pushButton_save.setAutoDefault(False)
        self.pushButton_save.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_save)

        self.horizontalSpacer = QSpacerItem(5, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.label_message = QLabel(self.frame)
        self.label_message.setObjectName(u"label_message")

        self.horizontalLayout.addWidget(self.label_message)

        self.horizontalSpacer_8 = QSpacerItem(5, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_8)

        self.pushButton_close = QPushButton(self.frame)
        self.pushButton_close.setObjectName(u"pushButton_close")
        sizePolicy1.setHeightForWidth(self.pushButton_close.sizePolicy().hasHeightForWidth())
        self.pushButton_close.setSizePolicy(sizePolicy1)
        self.pushButton_close.setFocusPolicy(Qt.NoFocus)
        icon4 = QIcon()
        icon4.addFile(u"icons/grey/x-square.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon4.addFile(u"icons/purple/x-square.svg", QSize(), QIcon.Normal, QIcon.On)
        self.pushButton_close.setIcon(icon4)
        self.pushButton_close.setCheckable(False)
        self.pushButton_close.setAutoDefault(False)
        self.pushButton_close.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_close)


        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.groupBox_stabilize = QGroupBox(self.frame)
        self.groupBox_stabilize.setObjectName(u"groupBox_stabilize")
        self.groupBox_stabilize.setFocusPolicy(Qt.NoFocus)
        self.groupBox_stabilize.setCheckable(True)
        self.verticalLayout_4 = QVBoxLayout(self.groupBox_stabilize)
        self.verticalLayout_4.setSpacing(3)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(9, 12, 3, 3)
        self.gridLayout = QGridLayout()
        self.gridLayout.setSpacing(3)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, -1, -1, -1)
        self.pushButton_set_start = QPushButton(self.groupBox_stabilize)
        self.pushButton_set_start.setObjectName(u"pushButton_set_start")
        self.pushButton_set_start.setFocusPolicy(Qt.NoFocus)
        self.pushButton_set_start.setLayoutDirection(Qt.RightToLeft)
        icon5 = QIcon()
        icon5.addFile(u"icons/blue/log-out.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon5.addFile(u"icons/blue/log-out.svg", QSize(), QIcon.Normal, QIcon.On)
        self.pushButton_set_start.setIcon(icon5)
        self.pushButton_set_start.setFlat(True)

        self.gridLayout.addWidget(self.pushButton_set_start, 0, 0, 1, 1)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setSpacing(9)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.checkBox_vertical = QCheckBox(self.groupBox_stabilize)
        self.checkBox_vertical.setObjectName(u"checkBox_vertical")

        self.horizontalLayout_6.addWidget(self.checkBox_vertical)

        self.checkBox_horizontal = QCheckBox(self.groupBox_stabilize)
        self.checkBox_horizontal.setObjectName(u"checkBox_horizontal")

        self.horizontalLayout_6.addWidget(self.checkBox_horizontal)

        self.checkBox_rotation = QCheckBox(self.groupBox_stabilize)
        self.checkBox_rotation.setObjectName(u"checkBox_rotation")

        self.horizontalLayout_6.addWidget(self.checkBox_rotation)

        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_6)


        self.gridLayout.addLayout(self.horizontalLayout_6, 3, 3, 1, 1)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.lineEdit_end = QLineEdit(self.groupBox_stabilize)
        self.lineEdit_end.setObjectName(u"lineEdit_end")
        self.lineEdit_end.setMaximumSize(QSize(40, 16777215))
        self.lineEdit_end.setFocusPolicy(Qt.NoFocus)

        self.horizontalLayout_3.addWidget(self.lineEdit_end)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_3)


        self.gridLayout.addLayout(self.horizontalLayout_3, 1, 3, 1, 1)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.lineEdit_start = QLineEdit(self.groupBox_stabilize)
        self.lineEdit_start.setObjectName(u"lineEdit_start")
        self.lineEdit_start.setMaximumSize(QSize(40, 16777215))
        self.lineEdit_start.setFocusPolicy(Qt.NoFocus)

        self.horizontalLayout_5.addWidget(self.lineEdit_start)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_4)


        self.gridLayout.addLayout(self.horizontalLayout_5, 0, 3, 1, 1)

        self.label_5 = QLabel(self.groupBox_stabilize)
        self.label_5.setObjectName(u"label_5")

        self.gridLayout.addWidget(self.label_5, 3, 0, 1, 1)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setSpacing(9)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.radioButton_start = QRadioButton(self.groupBox_stabilize)
        self.radioButton_start.setObjectName(u"radioButton_start")
        self.radioButton_start.setFocusPolicy(Qt.NoFocus)

        self.horizontalLayout_4.addWidget(self.radioButton_start)

        self.radioButton_middle = QRadioButton(self.groupBox_stabilize)
        self.radioButton_middle.setObjectName(u"radioButton_middle")
        self.radioButton_middle.setFocusPolicy(Qt.NoFocus)

        self.horizontalLayout_4.addWidget(self.radioButton_middle)

        self.radioButton_end = QRadioButton(self.groupBox_stabilize)
        self.radioButton_end.setObjectName(u"radioButton_end")
        self.radioButton_end.setFocusPolicy(Qt.NoFocus)

        self.horizontalLayout_4.addWidget(self.radioButton_end)

        self.radioButton_frame_no = QRadioButton(self.groupBox_stabilize)
        self.radioButton_frame_no.setObjectName(u"radioButton_frame_no")
        self.radioButton_frame_no.setEnabled(False)
        self.radioButton_frame_no.setFocusPolicy(Qt.NoFocus)

        self.horizontalLayout_4.addWidget(self.radioButton_frame_no)

        self.lineEdit_ref_frame_no = QLineEdit(self.groupBox_stabilize)
        self.lineEdit_ref_frame_no.setObjectName(u"lineEdit_ref_frame_no")
        self.lineEdit_ref_frame_no.setEnabled(False)
        self.lineEdit_ref_frame_no.setMaximumSize(QSize(40, 16777215))
        self.lineEdit_ref_frame_no.setFocusPolicy(Qt.NoFocus)
        self.lineEdit_ref_frame_no.setReadOnly(True)

        self.horizontalLayout_4.addWidget(self.lineEdit_ref_frame_no)

        self.pushButton_set_ref = QPushButton(self.groupBox_stabilize)
        self.pushButton_set_ref.setObjectName(u"pushButton_set_ref")
        self.pushButton_set_ref.setEnabled(False)
        sizePolicy2 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.pushButton_set_ref.sizePolicy().hasHeightForWidth())
        self.pushButton_set_ref.setSizePolicy(sizePolicy2)
        self.pushButton_set_ref.setMaximumSize(QSize(25, 16777215))
        self.pushButton_set_ref.setFocusPolicy(Qt.NoFocus)
        icon6 = QIcon()
        icon6.addFile(u"icons/blue/arrow-left-right.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon6.addFile(u"icons/blue/arrow-left-right.svg", QSize(), QIcon.Normal, QIcon.On)
        icon6.addFile(u"icons/grey/arrow-left-right.svg", QSize(), QIcon.Disabled, QIcon.Off)
        icon6.addFile(u"icons/grey/arrow-left-right.svg", QSize(), QIcon.Disabled, QIcon.On)
        self.pushButton_set_ref.setIcon(icon6)
        self.pushButton_set_ref.setFlat(True)

        self.horizontalLayout_4.addWidget(self.pushButton_set_ref)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_2)


        self.gridLayout.addLayout(self.horizontalLayout_4, 2, 3, 1, 1)

        self.pushButton_set_end = QPushButton(self.groupBox_stabilize)
        self.pushButton_set_end.setObjectName(u"pushButton_set_end")
        self.pushButton_set_end.setFocusPolicy(Qt.NoFocus)
        self.pushButton_set_end.setLayoutDirection(Qt.RightToLeft)
        icon7 = QIcon()
        icon7.addFile(u"icons/blue/log-in.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon7.addFile(u"icons/blue/log-in.svg", QSize(), QIcon.Normal, QIcon.On)
        self.pushButton_set_end.setIcon(icon7)
        self.pushButton_set_end.setFlat(True)

        self.gridLayout.addWidget(self.pushButton_set_end, 1, 0, 1, 1)

        self.pushButton_switch_ref = QPushButton(self.groupBox_stabilize)
        self.pushButton_switch_ref.setObjectName(u"pushButton_switch_ref")
        self.pushButton_switch_ref.setEnabled(True)
        self.pushButton_switch_ref.setFocusPolicy(Qt.NoFocus)
        self.pushButton_switch_ref.setLayoutDirection(Qt.LeftToRight)
        self.pushButton_switch_ref.setFlat(True)

        self.gridLayout.addWidget(self.pushButton_switch_ref, 2, 0, 1, 1)


        self.verticalLayout_4.addLayout(self.gridLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.pushButton_undo = QPushButton(self.groupBox_stabilize)
        self.pushButton_undo.setObjectName(u"pushButton_undo")
        sizePolicy2.setHeightForWidth(self.pushButton_undo.sizePolicy().hasHeightForWidth())
        self.pushButton_undo.setSizePolicy(sizePolicy2)
        self.pushButton_undo.setFocusPolicy(Qt.NoFocus)
        icon8 = QIcon()
        icon8.addFile(u"icons/purple/undo.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_undo.setIcon(icon8)
        self.pushButton_undo.setFlat(True)

        self.horizontalLayout_2.addWidget(self.pushButton_undo)

        self.horizontalSpacer_7 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_7)

        self.pushButton_set_segment = QPushButton(self.groupBox_stabilize)
        self.pushButton_set_segment.setObjectName(u"pushButton_set_segment")
        self.pushButton_set_segment.setEnabled(False)
        sizePolicy2.setHeightForWidth(self.pushButton_set_segment.sizePolicy().hasHeightForWidth())
        self.pushButton_set_segment.setSizePolicy(sizePolicy2)
        self.pushButton_set_segment.setMaximumSize(QSize(25, 16777215))
        self.pushButton_set_segment.setFocusPolicy(Qt.NoFocus)
        icon9 = QIcon()
        icon9.addFile(u"icons/blue/arrow-big-down.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon9.addFile(u"icons/blue/arrow-big-down.svg", QSize(), QIcon.Normal, QIcon.On)
        icon9.addFile(u"icons/grey/arrow-big-down.svg", QSize(), QIcon.Disabled, QIcon.Off)
        icon9.addFile(u"icons/grey/arrow-big-down.svg", QSize(), QIcon.Disabled, QIcon.On)
        self.pushButton_set_segment.setIcon(icon9)
        self.pushButton_set_segment.setFlat(True)

        self.horizontalLayout_2.addWidget(self.pushButton_set_segment)

        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_5)

        self.pushButton_calculate = QPushButton(self.groupBox_stabilize)
        self.pushButton_calculate.setObjectName(u"pushButton_calculate")
        self.pushButton_calculate.setFocusPolicy(Qt.NoFocus)

        self.horizontalLayout_2.addWidget(self.pushButton_calculate)


        self.verticalLayout_4.addLayout(self.horizontalLayout_2)


        self.verticalLayout_2.addWidget(self.groupBox_stabilize)

        self.tableWidget_stabilize = QTableWidget(self.frame)
        if (self.tableWidget_stabilize.columnCount() < 4):
            self.tableWidget_stabilize.setColumnCount(4)
        __qtablewidgetitem = QTableWidgetItem()
        self.tableWidget_stabilize.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.tableWidget_stabilize.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.tableWidget_stabilize.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.tableWidget_stabilize.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        if (self.tableWidget_stabilize.rowCount() < 5):
            self.tableWidget_stabilize.setRowCount(5)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.tableWidget_stabilize.setVerticalHeaderItem(0, __qtablewidgetitem4)
        __qtablewidgetitem5 = QTableWidgetItem()
        self.tableWidget_stabilize.setItem(0, 0, __qtablewidgetitem5)
        __qtablewidgetitem6 = QTableWidgetItem()
        self.tableWidget_stabilize.setItem(0, 1, __qtablewidgetitem6)
        __qtablewidgetitem7 = QTableWidgetItem()
        self.tableWidget_stabilize.setItem(0, 2, __qtablewidgetitem7)
        __qtablewidgetitem8 = QTableWidgetItem()
        self.tableWidget_stabilize.setItem(0, 3, __qtablewidgetitem8)
        self.tableWidget_stabilize.setObjectName(u"tableWidget_stabilize")
        sizePolicy3 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.tableWidget_stabilize.sizePolicy().hasHeightForWidth())
        self.tableWidget_stabilize.setSizePolicy(sizePolicy3)
        self.tableWidget_stabilize.setFocusPolicy(Qt.NoFocus)
        self.tableWidget_stabilize.setFrameShape(QFrame.StyledPanel)
        self.tableWidget_stabilize.setFrameShadow(QFrame.Sunken)
        self.tableWidget_stabilize.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tableWidget_stabilize.setSizeAdjustPolicy(QAbstractScrollArea.AdjustIgnored)
        self.tableWidget_stabilize.setEditTriggers(QAbstractItemView.SelectedClicked)
        self.tableWidget_stabilize.setProperty("showDropIndicator", False)
        self.tableWidget_stabilize.setDragDropOverwriteMode(False)
        self.tableWidget_stabilize.setAlternatingRowColors(True)
        self.tableWidget_stabilize.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tableWidget_stabilize.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableWidget_stabilize.setSortingEnabled(False)
        self.tableWidget_stabilize.setWordWrap(False)
        self.tableWidget_stabilize.setCornerButtonEnabled(False)
        self.tableWidget_stabilize.setRowCount(5)
        self.tableWidget_stabilize.setColumnCount(4)
        self.tableWidget_stabilize.horizontalHeader().setDefaultSectionSize(90)
        self.tableWidget_stabilize.horizontalHeader().setStretchLastSection(True)
        self.tableWidget_stabilize.verticalHeader().setVisible(True)
        self.tableWidget_stabilize.verticalHeader().setCascadingSectionResizes(False)
        self.tableWidget_stabilize.verticalHeader().setMinimumSectionSize(22)
        self.tableWidget_stabilize.verticalHeader().setDefaultSectionSize(22)
        self.tableWidget_stabilize.verticalHeader().setHighlightSections(True)
        self.tableWidget_stabilize.verticalHeader().setStretchLastSection(False)

        self.verticalLayout_2.addWidget(self.tableWidget_stabilize)


        self.mainLayout.addWidget(self.frame)


        self.retranslateUi(widget_stabilize)

        QMetaObject.connectSlotsByName(widget_stabilize)
    # setupUi

    def retranslateUi(self, widget_stabilize):
        self.pushButton_set_preview.setText("")
        self.pushButton_guidelines.setText("")
        self.pushButton_discard.setText("")
        self.pushButton_save.setText("")
        self.label_message.setText(QCoreApplication.translate("widget_stabilize", u"error", None))
        self.pushButton_close.setText("")
        self.groupBox_stabilize.setTitle(QCoreApplication.translate("widget_stabilize", u"Stabilize/deshake", None))
        self.pushButton_set_start.setText(QCoreApplication.translate("widget_stabilize", u"&Start", None))
        self.checkBox_vertical.setText(QCoreApplication.translate("widget_stabilize", u"&vertical", None))
        self.checkBox_horizontal.setText(QCoreApplication.translate("widget_stabilize", u"&horizontal", None))
        self.checkBox_rotation.setText(QCoreApplication.translate("widget_stabilize", u"&rotation", None))
        self.label_5.setText(QCoreApplication.translate("widget_stabilize", u"Mode", None))
        self.radioButton_start.setText(QCoreApplication.translate("widget_stabilize", u"start", None))
        self.radioButton_middle.setText(QCoreApplication.translate("widget_stabilize", u"middle", None))
        self.radioButton_end.setText(QCoreApplication.translate("widget_stabilize", u"end", None))
        self.radioButton_frame_no.setText(QCoreApplication.translate("widget_stabilize", u"frame no.", None))
        self.pushButton_set_ref.setText("")
        self.pushButton_set_end.setText(QCoreApplication.translate("widget_stabilize", u"&End", None))
        self.pushButton_switch_ref.setText(QCoreApplication.translate("widget_stabilize", u"&Initial ref.", None))
        self.pushButton_undo.setText("")
        self.pushButton_set_segment.setText("")
        self.pushButton_calculate.setText(QCoreApplication.translate("widget_stabilize", u"calculate (F5)", None))
        ___qtablewidgetitem = self.tableWidget_stabilize.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("widget_stabilize", u"start", None));
        ___qtablewidgetitem1 = self.tableWidget_stabilize.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("widget_stabilize", u"end", None));
        ___qtablewidgetitem2 = self.tableWidget_stabilize.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("widget_stabilize", u"ref.", None));
        ___qtablewidgetitem3 = self.tableWidget_stabilize.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("widget_stabilize", u"mode", None));
        ___qtablewidgetitem4 = self.tableWidget_stabilize.verticalHeaderItem(0)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("widget_stabilize", u"1", None));

        __sortingEnabled = self.tableWidget_stabilize.isSortingEnabled()
        self.tableWidget_stabilize.setSortingEnabled(False)
        ___qtablewidgetitem5 = self.tableWidget_stabilize.item(0, 0)
        ___qtablewidgetitem5.setText(QCoreApplication.translate("widget_stabilize", u"1", None));
        ___qtablewidgetitem6 = self.tableWidget_stabilize.item(0, 1)
        ___qtablewidgetitem6.setText(QCoreApplication.translate("widget_stabilize", u"8", None));
        ___qtablewidgetitem7 = self.tableWidget_stabilize.item(0, 2)
        ___qtablewidgetitem7.setText(QCoreApplication.translate("widget_stabilize", u"start", None));
        ___qtablewidgetitem8 = self.tableWidget_stabilize.item(0, 3)
        ___qtablewidgetitem8.setText(QCoreApplication.translate("widget_stabilize", u"vertical+horizontal+rotation", None));
        self.tableWidget_stabilize.setSortingEnabled(__sortingEnabled)

        pass
    # retranslateUi

