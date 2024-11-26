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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QFrame, QGridLayout,
    QHBoxLayout, QHeaderView, QLabel, QLayout,
    QLineEdit, QPushButton, QSizePolicy, QSpacerItem,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

class Ui_DsrWidget(object):
    def setupUi(self, DsrWidget):
        if not DsrWidget.objectName():
            DsrWidget.setObjectName(u"DsrWidget")
        DsrWidget.resize(314, 352)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(DsrWidget.sizePolicy().hasHeightForWidth())
        DsrWidget.setSizePolicy(sizePolicy)
        self.verticalLayout_3 = QVBoxLayout(DsrWidget)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.frame = QFrame(DsrWidget)
        self.frame.setObjectName(u"frame")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
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
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.pushButton_set_preview.sizePolicy().hasHeightForWidth())
        self.pushButton_set_preview.setSizePolicy(sizePolicy2)
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
        sizePolicy2.setHeightForWidth(self.shortcut.sizePolicy().hasHeightForWidth())
        self.shortcut.setSizePolicy(sizePolicy2)
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
        sizePolicy2.setHeightForWidth(self.pushButton_discard.sizePolicy().hasHeightForWidth())
        self.pushButton_discard.setSizePolicy(sizePolicy2)
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
        sizePolicy2.setHeightForWidth(self.pushButton_save.sizePolicy().hasHeightForWidth())
        self.pushButton_save.setSizePolicy(sizePolicy2)
        self.pushButton_save.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        icon2 = QIcon()
        icon2.addFile(u"./icons/purple/save.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.pushButton_save.setIcon(icon2)
        self.pushButton_save.setCheckable(False)
        self.pushButton_save.setAutoDefault(False)
        self.pushButton_save.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_save)


        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.gridLayout_2 = QGridLayout()
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.pushButton_scene_resize_preview_2 = QPushButton(self.frame)
        self.pushButton_scene_resize_preview_2.setObjectName(u"pushButton_scene_resize_preview_2")
        self.pushButton_scene_resize_preview_2.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.pushButton_scene_resize_preview_2.setText(u"")
        self.pushButton_scene_resize_preview_2.setIcon(icon)
        self.pushButton_scene_resize_preview_2.setCheckable(True)
        self.pushButton_scene_resize_preview_2.setFlat(True)

        self.gridLayout_2.addWidget(self.pushButton_scene_resize_preview_2, 0, 1, 1, 1)

        self.label_9 = QLabel(self.frame)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setLineWidth(0)

        self.gridLayout_2.addWidget(self.label_9, 0, 0, 1, 1)

        self.shortcut_2 = QLabel(self.frame)
        self.shortcut_2.setObjectName(u"shortcut_2")
        font1 = QFont()
        font1.setPointSize(8)
        self.shortcut_2.setFont(font1)

        self.gridLayout_2.addWidget(self.shortcut_2, 1, 1, 1, 1)

        self.horizontalSpacer_5 = QSpacerItem(20, 10, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_2.addItem(self.horizontalSpacer_5, 1, 2, 1, 1)


        self.verticalLayout_2.addLayout(self.gridLayout_2)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(-1, -1, 30, -1)
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setSpacing(3)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.pushButton_3 = QPushButton(self.frame)
        self.pushButton_3.setObjectName(u"pushButton_3")
        self.pushButton_3.setMaximumSize(QSize(30, 16777215))
        self.pushButton_3.setCheckable(True)
        self.pushButton_3.setFlat(False)

        self.horizontalLayout_3.addWidget(self.pushButton_3)

        self.pushButton_2 = QPushButton(self.frame)
        self.pushButton_2.setObjectName(u"pushButton_2")
        self.pushButton_2.setMaximumSize(QSize(30, 16777215))
        self.pushButton_2.setCheckable(True)
        self.pushButton_2.setFlat(False)

        self.horizontalLayout_3.addWidget(self.pushButton_2)

        self.pushButton = QPushButton(self.frame)
        self.pushButton.setObjectName(u"pushButton")
        self.pushButton.setMaximumSize(QSize(30, 16777215))
        self.pushButton.setCheckable(True)
        self.pushButton.setFlat(False)

        self.horizontalLayout_3.addWidget(self.pushButton)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_3)

        self.pushButton_4 = QPushButton(self.frame)
        self.pushButton_4.setObjectName(u"pushButton_4")
        self.pushButton_4.setMaximumSize(QSize(30, 16777215))
        self.pushButton_4.setCheckable(True)
        self.pushButton_4.setFlat(False)

        self.horizontalLayout_3.addWidget(self.pushButton_4)

        self.pushButton_6 = QPushButton(self.frame)
        self.pushButton_6.setObjectName(u"pushButton_6")
        self.pushButton_6.setMaximumSize(QSize(30, 16777215))
        self.pushButton_6.setCheckable(True)
        self.pushButton_6.setFlat(False)

        self.horizontalLayout_3.addWidget(self.pushButton_6)

        self.pushButton_5 = QPushButton(self.frame)
        self.pushButton_5.setObjectName(u"pushButton_5")
        self.pushButton_5.setMaximumSize(QSize(30, 16777215))
        self.pushButton_5.setCheckable(True)
        self.pushButton_5.setFlat(False)

        self.horizontalLayout_3.addWidget(self.pushButton_5)


        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(-1, -1, -1, 10)
        self.lineEdit_2 = QLineEdit(self.frame)
        self.lineEdit_2.setObjectName(u"lineEdit_2")
        self.lineEdit_2.setMaximumSize(QSize(100, 16777215))
        self.lineEdit_2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lineEdit_2.setReadOnly(True)

        self.horizontalLayout_4.addWidget(self.lineEdit_2)

        self.lineEdit = QLineEdit(self.frame)
        self.lineEdit.setObjectName(u"lineEdit")
        self.lineEdit.setMaximumSize(QSize(100, 16777215))
        self.lineEdit.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_4.addWidget(self.lineEdit)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_4)


        self.verticalLayout.addLayout(self.horizontalLayout_4)


        self.verticalLayout_2.addLayout(self.verticalLayout)

        self.tableWidget_dsr = QTableWidget(self.frame)
        if (self.tableWidget_dsr.columnCount() < 5):
            self.tableWidget_dsr.setColumnCount(5)
        __qtablewidgetitem = QTableWidgetItem()
        self.tableWidget_dsr.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.tableWidget_dsr.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.tableWidget_dsr.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.tableWidget_dsr.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.tableWidget_dsr.setHorizontalHeaderItem(4, __qtablewidgetitem4)
        if (self.tableWidget_dsr.rowCount() < 10):
            self.tableWidget_dsr.setRowCount(10)
        __qtablewidgetitem5 = QTableWidgetItem()
        self.tableWidget_dsr.setItem(0, 1, __qtablewidgetitem5)
        __qtablewidgetitem6 = QTableWidgetItem()
        self.tableWidget_dsr.setItem(0, 3, __qtablewidgetitem6)
        self.tableWidget_dsr.setObjectName(u"tableWidget_dsr")
        self.tableWidget_dsr.setMinimumSize(QSize(300, 0))
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

        self.verticalLayout_2.addWidget(self.tableWidget_dsr)


        self.verticalLayout_3.addWidget(self.frame)


        self.retranslateUi(DsrWidget)

        QMetaObject.connectSlotsByName(DsrWidget)
    # setupUi

    def retranslateUi(self, DsrWidget):
        self.pushButton_set_preview.setText("")
        self.shortcut.setText(QCoreApplication.translate("DsrWidget", u"(F2)", None))
        self.label_message.setText(QCoreApplication.translate("DsrWidget", u"disabled", None))
        self.pushButton_discard.setText("")
        self.pushButton_save.setText("")
        self.label_9.setText(QCoreApplication.translate("DsrWidget", u"mask", None))
        self.shortcut_2.setText(QCoreApplication.translate("DsrWidget", u"(F3)", None))
        self.pushButton_3.setText(QCoreApplication.translate("DsrWidget", u"circle", None))
        self.pushButton_2.setText(QCoreApplication.translate("DsrWidget", u"ellipse", None))
        self.pushButton.setText(QCoreApplication.translate("DsrWidget", u"oblong", None))
        self.pushButton_4.setText(QCoreApplication.translate("DsrWidget", u"yellow", None))
        self.pushButton_6.setText(QCoreApplication.translate("DsrWidget", u"red", None))
        self.pushButton_5.setText(QCoreApplication.translate("DsrWidget", u"cyan", None))
        self.lineEdit_2.setText(QCoreApplication.translate("DsrWidget", u"(1440,1080)", None))
        self.lineEdit.setText(QCoreApplication.translate("DsrWidget", u"100x50, -45\u00b0", None))
        ___qtablewidgetitem = self.tableWidget_dsr.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("DsrWidget", u"scene", None));
        ___qtablewidgetitem1 = self.tableWidget_dsr.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("DsrWidget", u"frame", None));
        ___qtablewidgetitem2 = self.tableWidget_dsr.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("DsrWidget", u"type", None));
        ___qtablewidgetitem3 = self.tableWidget_dsr.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("DsrWidget", u"coord.", None));
        ___qtablewidgetitem4 = self.tableWidget_dsr.horizontalHeaderItem(4)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("DsrWidget", u"geometry", None));

        __sortingEnabled = self.tableWidget_dsr.isSortingEnabled()
        self.tableWidget_dsr.setSortingEnabled(False)
        ___qtablewidgetitem5 = self.tableWidget_dsr.item(0, 1)
        ___qtablewidgetitem5.setText(QCoreApplication.translate("DsrWidget", u"123456", None));
        ___qtablewidgetitem6 = self.tableWidget_dsr.item(0, 3)
        ___qtablewidgetitem6.setText(QCoreApplication.translate("DsrWidget", u"(50,30) 500x20 -10\u00b0", None));
        self.tableWidget_dsr.setSortingEnabled(__sortingEnabled)

        pass
    # retranslateUi

