# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_widget_replace.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QFrame, QGroupBox,
    QHBoxLayout, QHeaderView, QLineEdit, QPushButton,
    QSizePolicy, QSpacerItem, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget)

class Ui_widget_replace(object):
    def setupUi(self, widget_replace):
        if not widget_replace.objectName():
            widget_replace.setObjectName(u"widget_replace")
        widget_replace.resize(270, 370)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(widget_replace.sizePolicy().hasHeightForWidth())
        widget_replace.setSizePolicy(sizePolicy)
        widget_replace.setMinimumSize(QSize(0, 370))
        self.mainLayout = QVBoxLayout(widget_replace)
        self.mainLayout.setSpacing(0)
        self.mainLayout.setObjectName(u"mainLayout")
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.frame = QFrame(widget_replace)
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
        icon = QIcon()
        icon.addFile(u"tools/icons/grey/eye.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon.addFile(u"tools/icons/blue/eye.svg", QSize(), QIcon.Normal, QIcon.On)
        icon.addFile(u"tools/icons/grey/eye.svg", QSize(), QIcon.Disabled, QIcon.Off)
        icon.addFile(u"tools/icons/grey/eye.svg", QSize(), QIcon.Disabled, QIcon.On)
        self.pushButton_set_preview.setIcon(icon)
        self.pushButton_set_preview.setCheckable(True)
        self.pushButton_set_preview.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_set_preview)

        self.horizontalSpacer = QSpacerItem(5, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.pushButton_discard = QPushButton(self.frame)
        self.pushButton_discard.setObjectName(u"pushButton_discard")
        sizePolicy1.setHeightForWidth(self.pushButton_discard.sizePolicy().hasHeightForWidth())
        self.pushButton_discard.setSizePolicy(sizePolicy1)
        icon1 = QIcon()
        icon1.addFile(u"tools/icons/grey/undo.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon1.addFile(u"tools/icons/purple/undo.svg", QSize(), QIcon.Normal, QIcon.On)
        self.pushButton_discard.setIcon(icon1)
        self.pushButton_discard.setCheckable(False)
        self.pushButton_discard.setAutoDefault(False)
        self.pushButton_discard.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_discard)

        self.pushButton_save = QPushButton(self.frame)
        self.pushButton_save.setObjectName(u"pushButton_save")
        sizePolicy1.setHeightForWidth(self.pushButton_save.sizePolicy().hasHeightForWidth())
        self.pushButton_save.setSizePolicy(sizePolicy1)
        icon2 = QIcon()
        icon2.addFile(u"tools/icons/purple/save.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_save.setIcon(icon2)
        self.pushButton_save.setCheckable(False)
        self.pushButton_save.setAutoDefault(False)
        self.pushButton_save.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_save)

        self.pushButton_close = QPushButton(self.frame)
        self.pushButton_close.setObjectName(u"pushButton_close")
        sizePolicy1.setHeightForWidth(self.pushButton_close.sizePolicy().hasHeightForWidth())
        self.pushButton_close.setSizePolicy(sizePolicy1)
        icon3 = QIcon()
        icon3.addFile(u"tools/icons/grey/x-square.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon3.addFile(u"tools/icons/purple/x-square.svg", QSize(), QIcon.Normal, QIcon.On)
        self.pushButton_close.setIcon(icon3)
        self.pushButton_close.setCheckable(False)
        self.pushButton_close.setAutoDefault(False)
        self.pushButton_close.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_close)


        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.groupBox_replace = QGroupBox(self.frame)
        self.groupBox_replace.setObjectName(u"groupBox_replace")
        sizePolicy2 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.groupBox_replace.sizePolicy().hasHeightForWidth())
        self.groupBox_replace.setSizePolicy(sizePolicy2)
        self.groupBox_replace.setCheckable(False)
        self.groupBox_replace.setChecked(False)
        self.horizontalLayout_2 = QHBoxLayout(self.groupBox_replace)
        self.horizontalLayout_2.setSpacing(4)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(3, 9, 3, 3)
        self.pushButton_copy = QPushButton(self.groupBox_replace)
        self.pushButton_copy.setObjectName(u"pushButton_copy")
        self.pushButton_copy.setMaximumSize(QSize(70, 16777215))
        icon4 = QIcon()
        icon4.addFile(u"tools/icons/blue/copy.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_copy.setIcon(icon4)
        self.pushButton_copy.setFlat(True)

        self.horizontalLayout_2.addWidget(self.pushButton_copy)

        self.lineEdit_frame_no = QLineEdit(self.groupBox_replace)
        self.lineEdit_frame_no.setObjectName(u"lineEdit_frame_no")
        sizePolicy3 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.lineEdit_frame_no.sizePolicy().hasHeightForWidth())
        self.lineEdit_frame_no.setSizePolicy(sizePolicy3)
        self.lineEdit_frame_no.setMinimumSize(QSize(60, 0))
        self.lineEdit_frame_no.setMaximumSize(QSize(70, 16777215))
        self.lineEdit_frame_no.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.lineEdit_frame_no.setReadOnly(True)

        self.horizontalLayout_2.addWidget(self.lineEdit_frame_no)

        self.pushButton_paste = QPushButton(self.groupBox_replace)
        self.pushButton_paste.setObjectName(u"pushButton_paste")
        icon5 = QIcon()
        icon5.addFile(u"tools/icons/grey/arrow-left.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon5.addFile(u"tools/icons/blue/arrow-left.svg", QSize(), QIcon.Normal, QIcon.On)
        self.pushButton_paste.setIcon(icon5)
        self.pushButton_paste.setFlat(True)

        self.horizontalLayout_2.addWidget(self.pushButton_paste)

        self.lineEdit_replaced_by = QLineEdit(self.groupBox_replace)
        self.lineEdit_replaced_by.setObjectName(u"lineEdit_replaced_by")
        sizePolicy3.setHeightForWidth(self.lineEdit_replaced_by.sizePolicy().hasHeightForWidth())
        self.lineEdit_replaced_by.setSizePolicy(sizePolicy3)
        self.lineEdit_replaced_by.setMaximumSize(QSize(70, 16777215))
        self.lineEdit_replaced_by.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.lineEdit_replaced_by.setReadOnly(True)

        self.horizontalLayout_2.addWidget(self.lineEdit_replaced_by)

        self.pushButton_remove = QPushButton(self.groupBox_replace)
        self.pushButton_remove.setObjectName(u"pushButton_remove")
        icon6 = QIcon()
        icon6.addFile(u"tools/icons/grey/eraser.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon6.addFile(u"tools/icons/blue/eraser.svg", QSize(), QIcon.Normal, QIcon.On)
        self.pushButton_remove.setIcon(icon6)
        self.pushButton_remove.setFlat(True)

        self.horizontalLayout_2.addWidget(self.pushButton_remove)


        self.verticalLayout_2.addWidget(self.groupBox_replace)

        self.tableWidget_replace = QTableWidget(self.frame)
        if (self.tableWidget_replace.columnCount() < 3):
            self.tableWidget_replace.setColumnCount(3)
        __qtablewidgetitem = QTableWidgetItem()
        self.tableWidget_replace.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.tableWidget_replace.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.tableWidget_replace.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        if (self.tableWidget_replace.rowCount() < 10):
            self.tableWidget_replace.setRowCount(10)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.tableWidget_replace.setVerticalHeaderItem(0, __qtablewidgetitem3)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.tableWidget_replace.setItem(0, 1, __qtablewidgetitem4)
        __qtablewidgetitem5 = QTableWidgetItem()
        self.tableWidget_replace.setItem(0, 2, __qtablewidgetitem5)
        self.tableWidget_replace.setObjectName(u"tableWidget_replace")
        sizePolicy4 = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Expanding)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.tableWidget_replace.sizePolicy().hasHeightForWidth())
        self.tableWidget_replace.setSizePolicy(sizePolicy4)
        self.tableWidget_replace.setFrameShape(QFrame.StyledPanel)
        self.tableWidget_replace.setFrameShadow(QFrame.Sunken)
        self.tableWidget_replace.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tableWidget_replace.setEditTriggers(QAbstractItemView.SelectedClicked)
        self.tableWidget_replace.setProperty("showDropIndicator", False)
        self.tableWidget_replace.setDragDropOverwriteMode(False)
        self.tableWidget_replace.setSelectionMode(QAbstractItemView.ContiguousSelection)
        self.tableWidget_replace.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableWidget_replace.setSortingEnabled(False)
        self.tableWidget_replace.setRowCount(10)
        self.tableWidget_replace.horizontalHeader().setDefaultSectionSize(90)
        self.tableWidget_replace.horizontalHeader().setStretchLastSection(True)
        self.tableWidget_replace.verticalHeader().setVisible(False)
        self.tableWidget_replace.verticalHeader().setMinimumSectionSize(22)
        self.tableWidget_replace.verticalHeader().setDefaultSectionSize(22)

        self.verticalLayout_2.addWidget(self.tableWidget_replace)


        self.mainLayout.addWidget(self.frame)


        self.retranslateUi(widget_replace)

        QMetaObject.connectSlotsByName(widget_replace)
    # setupUi

    def retranslateUi(self, widget_replace):
        self.pushButton_set_preview.setText("")
        self.pushButton_discard.setText("")
        self.pushButton_save.setText("")
        self.pushButton_close.setText("")
        self.groupBox_replace.setTitle(QCoreApplication.translate("widget_replace", u"Replace frames", None))
        self.pushButton_copy.setText("")
        self.lineEdit_frame_no.setText(QCoreApplication.translate("widget_replace", u"123456", None))
        self.pushButton_paste.setText("")
        self.pushButton_remove.setText("")
        ___qtablewidgetitem = self.tableWidget_replace.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("widget_replace", u"shot", None));
        ___qtablewidgetitem1 = self.tableWidget_replace.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("widget_replace", u"frame", None));
        ___qtablewidgetitem2 = self.tableWidget_replace.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("widget_replace", u"replaced by", None));
        ___qtablewidgetitem3 = self.tableWidget_replace.verticalHeaderItem(0)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("widget_replace", u"1", None));

        __sortingEnabled = self.tableWidget_replace.isSortingEnabled()
        self.tableWidget_replace.setSortingEnabled(False)
        ___qtablewidgetitem4 = self.tableWidget_replace.item(0, 1)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("widget_replace", u"123456", None));
        ___qtablewidgetitem5 = self.tableWidget_replace.item(0, 2)
        ___qtablewidgetitem5.setText(QCoreApplication.translate("widget_replace", u"654321", None));
        self.tableWidget_replace.setSortingEnabled(__sortingEnabled)

        pass
    # retranslateUi

