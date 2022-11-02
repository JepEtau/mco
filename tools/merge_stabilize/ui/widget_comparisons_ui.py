# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_widget_comparisons.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QAbstractScrollArea, QApplication, QCheckBox,
    QComboBox, QFrame, QHBoxLayout, QHeaderView,
    QLabel, QSizePolicy, QSpacerItem, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget)

class Ui_widget_selection(object):
    def setupUi(self, widget_selection):
        if not widget_selection.objectName():
            widget_selection.setObjectName(u"widget_selection")
        widget_selection.resize(310, 540)
        self.verticalLayout_3 = QVBoxLayout(widget_selection)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.comboBox = QComboBox(widget_selection)
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.setObjectName(u"comboBox")
        sizePolicy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.comboBox.sizePolicy().hasHeightForWidth())
        self.comboBox.setSizePolicy(sizePolicy)

        self.verticalLayout.addWidget(self.comboBox)

        self.comboBox_2 = QComboBox(widget_selection)
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.setObjectName(u"comboBox_2")
        sizePolicy.setHeightForWidth(self.comboBox_2.sizePolicy().hasHeightForWidth())
        self.comboBox_2.setSizePolicy(sizePolicy)

        self.verticalLayout.addWidget(self.comboBox_2)

        self.comboBox_3 = QComboBox(widget_selection)
        self.comboBox_3.addItem("")
        self.comboBox_3.setObjectName(u"comboBox_3")
        sizePolicy.setHeightForWidth(self.comboBox_3.sizePolicy().hasHeightForWidth())
        self.comboBox_3.setSizePolicy(sizePolicy)

        self.verticalLayout.addWidget(self.comboBox_3)

        self.tableWidget = QTableWidget(widget_selection)
        if (self.tableWidget.columnCount() < 2):
            self.tableWidget.setColumnCount(2)
        __qtablewidgetitem = QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        if (self.tableWidget.rowCount() < 15):
            self.tableWidget.setRowCount(15)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.tableWidget.setVerticalHeaderItem(0, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.tableWidget.setVerticalHeaderItem(1, __qtablewidgetitem3)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.tableWidget.setItem(0, 0, __qtablewidgetitem4)
        __qtablewidgetitem5 = QTableWidgetItem()
        self.tableWidget.setItem(0, 1, __qtablewidgetitem5)
        __qtablewidgetitem6 = QTableWidgetItem()
        self.tableWidget.setItem(1, 0, __qtablewidgetitem6)
        __qtablewidgetitem7 = QTableWidgetItem()
        self.tableWidget.setItem(1, 1, __qtablewidgetitem7)
        self.tableWidget.setObjectName(u"tableWidget")
        self.tableWidget.setMinimumSize(QSize(0, 400))
        self.tableWidget.setMaximumSize(QSize(140, 16777215))
        self.tableWidget.setFrameShape(QFrame.StyledPanel)
        self.tableWidget.setFrameShadow(QFrame.Sunken)
        self.tableWidget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tableWidget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tableWidget.setSizeAdjustPolicy(QAbstractScrollArea.AdjustIgnored)
        self.tableWidget.setEditTriggers(QAbstractItemView.SelectedClicked)
        self.tableWidget.setProperty("showDropIndicator", False)
        self.tableWidget.setDragDropOverwriteMode(False)
        self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableWidget.setShowGrid(True)
        self.tableWidget.setWordWrap(False)
        self.tableWidget.setCornerButtonEnabled(False)
        self.tableWidget.setRowCount(15)
        self.tableWidget.horizontalHeader().setVisible(False)
        self.tableWidget.horizontalHeader().setMinimumSectionSize(28)
        self.tableWidget.horizontalHeader().setDefaultSectionSize(50)
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.verticalHeader().setMinimumSectionSize(22)
        self.tableWidget.verticalHeader().setDefaultSectionSize(22)
        self.tableWidget.verticalHeader().setHighlightSections(True)
        self.tableWidget.verticalHeader().setProperty("showSortIndicator", False)
        self.tableWidget.verticalHeader().setStretchLastSection(False)

        self.verticalLayout.addWidget(self.tableWidget)


        self.horizontalLayout.addLayout(self.verticalLayout)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.label = QLabel(widget_selection)
        self.label.setObjectName(u"label")
        self.label.setMinimumSize(QSize(0, 24))

        self.verticalLayout_2.addWidget(self.label)

        self.label_2 = QLabel(widget_selection)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setMinimumSize(QSize(0, 24))

        self.verticalLayout_2.addWidget(self.label_2)

        self.verticalSpacer = QSpacerItem(20, 24, QSizePolicy.Minimum, QSizePolicy.Fixed)

        self.verticalLayout_2.addItem(self.verticalSpacer)

        self.tableWidget_2 = QTableWidget(widget_selection)
        if (self.tableWidget_2.columnCount() < 2):
            self.tableWidget_2.setColumnCount(2)
        __qtablewidgetitem8 = QTableWidgetItem()
        self.tableWidget_2.setHorizontalHeaderItem(0, __qtablewidgetitem8)
        __qtablewidgetitem9 = QTableWidgetItem()
        self.tableWidget_2.setHorizontalHeaderItem(1, __qtablewidgetitem9)
        if (self.tableWidget_2.rowCount() < 15):
            self.tableWidget_2.setRowCount(15)
        __qtablewidgetitem10 = QTableWidgetItem()
        self.tableWidget_2.setVerticalHeaderItem(0, __qtablewidgetitem10)
        __qtablewidgetitem11 = QTableWidgetItem()
        self.tableWidget_2.setVerticalHeaderItem(1, __qtablewidgetitem11)
        __qtablewidgetitem12 = QTableWidgetItem()
        self.tableWidget_2.setItem(0, 0, __qtablewidgetitem12)
        __qtablewidgetitem13 = QTableWidgetItem()
        self.tableWidget_2.setItem(0, 1, __qtablewidgetitem13)
        __qtablewidgetitem14 = QTableWidgetItem()
        self.tableWidget_2.setItem(1, 0, __qtablewidgetitem14)
        __qtablewidgetitem15 = QTableWidgetItem()
        self.tableWidget_2.setItem(1, 1, __qtablewidgetitem15)
        self.tableWidget_2.setObjectName(u"tableWidget_2")
        self.tableWidget_2.setMaximumSize(QSize(140, 16777215))
        self.tableWidget_2.setFrameShape(QFrame.StyledPanel)
        self.tableWidget_2.setFrameShadow(QFrame.Sunken)
        self.tableWidget_2.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tableWidget_2.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tableWidget_2.setSizeAdjustPolicy(QAbstractScrollArea.AdjustIgnored)
        self.tableWidget_2.setEditTriggers(QAbstractItemView.SelectedClicked)
        self.tableWidget_2.setProperty("showDropIndicator", False)
        self.tableWidget_2.setDragDropOverwriteMode(False)
        self.tableWidget_2.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableWidget_2.setShowGrid(True)
        self.tableWidget_2.setWordWrap(False)
        self.tableWidget_2.setCornerButtonEnabled(False)
        self.tableWidget_2.setRowCount(15)
        self.tableWidget_2.horizontalHeader().setVisible(False)
        self.tableWidget_2.horizontalHeader().setMinimumSectionSize(28)
        self.tableWidget_2.horizontalHeader().setDefaultSectionSize(50)
        self.tableWidget_2.horizontalHeader().setStretchLastSection(True)
        self.tableWidget_2.verticalHeader().setVisible(False)
        self.tableWidget_2.verticalHeader().setMinimumSectionSize(22)
        self.tableWidget_2.verticalHeader().setDefaultSectionSize(22)
        self.tableWidget_2.verticalHeader().setHighlightSections(True)
        self.tableWidget_2.verticalHeader().setProperty("showSortIndicator", False)
        self.tableWidget_2.verticalHeader().setStretchLastSection(False)

        self.verticalLayout_2.addWidget(self.tableWidget_2)


        self.horizontalLayout.addLayout(self.verticalLayout_2)


        self.verticalLayout_3.addLayout(self.horizontalLayout)

        self.checkBox = QCheckBox(widget_selection)
        self.checkBox.setObjectName(u"checkBox")

        self.verticalLayout_3.addWidget(self.checkBox)


        self.retranslateUi(widget_selection)

        QMetaObject.connectSlotsByName(widget_selection)
    # setupUi

    def retranslateUi(self, widget_selection):
        widget_selection.setWindowTitle(QCoreApplication.translate("widget_selection", u"Form", None))
        self.comboBox.setItemText(0, "")
        self.comboBox.setItemText(1, QCoreApplication.translate("widget_selection", u"ep01", None))

        self.comboBox_2.setItemText(0, QCoreApplication.translate("widget_selection", u"precedemment", None))
        self.comboBox_2.setItemText(1, QCoreApplication.translate("widget_selection", u"g_debut", None))
        self.comboBox_2.setItemText(2, QCoreApplication.translate("widget_selection", u"episode", None))
        self.comboBox_2.setItemText(3, QCoreApplication.translate("widget_selection", u"g_asuivre", None))
        self.comboBox_2.setItemText(4, QCoreApplication.translate("widget_selection", u"asuivre", None))
        self.comboBox_2.setItemText(5, QCoreApplication.translate("widget_selection", u"g_reportage", None))
        self.comboBox_2.setItemText(6, QCoreApplication.translate("widget_selection", u"reportage", None))
        self.comboBox_2.setItemText(7, QCoreApplication.translate("widget_selection", u"g_fin", None))

        self.comboBox_3.setItemText(0, QCoreApplication.translate("widget_selection", u"deinterlace", None))

        ___qtablewidgetitem = self.tableWidget.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("widget_selection", u"shot no.", None));
        ___qtablewidgetitem1 = self.tableWidget.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("widget_selection", u"frame no.", None));
        ___qtablewidgetitem2 = self.tableWidget.verticalHeaderItem(0)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("widget_selection", u"001", None));
        ___qtablewidgetitem3 = self.tableWidget.verticalHeaderItem(1)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("widget_selection", u"002", None));

        __sortingEnabled = self.tableWidget.isSortingEnabled()
        self.tableWidget.setSortingEnabled(False)
        ___qtablewidgetitem4 = self.tableWidget.item(0, 0)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("widget_selection", u"001", None));
        ___qtablewidgetitem5 = self.tableWidget.item(0, 1)
        ___qtablewidgetitem5.setText(QCoreApplication.translate("widget_selection", u"0", None));
        ___qtablewidgetitem6 = self.tableWidget.item(1, 0)
        ___qtablewidgetitem6.setText(QCoreApplication.translate("widget_selection", u"002", None));
        ___qtablewidgetitem7 = self.tableWidget.item(1, 1)
        ___qtablewidgetitem7.setText(QCoreApplication.translate("widget_selection", u"920", None));
        self.tableWidget.setSortingEnabled(__sortingEnabled)

        self.label.setText(QCoreApplication.translate("widget_selection", u"TextLabel", None))
        self.label_2.setText(QCoreApplication.translate("widget_selection", u"TextLabel", None))
        ___qtablewidgetitem8 = self.tableWidget_2.horizontalHeaderItem(0)
        ___qtablewidgetitem8.setText(QCoreApplication.translate("widget_selection", u"shot no.", None));
        ___qtablewidgetitem9 = self.tableWidget_2.horizontalHeaderItem(1)
        ___qtablewidgetitem9.setText(QCoreApplication.translate("widget_selection", u"frame no.", None));
        ___qtablewidgetitem10 = self.tableWidget_2.verticalHeaderItem(0)
        ___qtablewidgetitem10.setText(QCoreApplication.translate("widget_selection", u"001", None));
        ___qtablewidgetitem11 = self.tableWidget_2.verticalHeaderItem(1)
        ___qtablewidgetitem11.setText(QCoreApplication.translate("widget_selection", u"002", None));

        __sortingEnabled1 = self.tableWidget_2.isSortingEnabled()
        self.tableWidget_2.setSortingEnabled(False)
        ___qtablewidgetitem12 = self.tableWidget_2.item(0, 0)
        ___qtablewidgetitem12.setText(QCoreApplication.translate("widget_selection", u"001", None));
        ___qtablewidgetitem13 = self.tableWidget_2.item(0, 1)
        ___qtablewidgetitem13.setText(QCoreApplication.translate("widget_selection", u"0", None));
        ___qtablewidgetitem14 = self.tableWidget_2.item(1, 0)
        ___qtablewidgetitem14.setText(QCoreApplication.translate("widget_selection", u"002", None));
        ___qtablewidgetitem15 = self.tableWidget_2.item(1, 1)
        ___qtablewidgetitem15.setText(QCoreApplication.translate("widget_selection", u"920", None));
        self.tableWidget_2.setSortingEnabled(__sortingEnabled1)

        self.checkBox.setText(QCoreApplication.translate("widget_selection", u"previous + next", None))
    # retranslateUi

