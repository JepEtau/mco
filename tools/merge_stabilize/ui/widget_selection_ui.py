# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_widget_selection.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QAbstractScrollArea, QApplication, QComboBox,
    QFrame, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QSizePolicy, QSpacerItem, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget)

from common.widget_app_controls import Widget_app_controls

class Ui_widget_selection(object):
    def setupUi(self, widget_selection):
        if not widget_selection.objectName():
            widget_selection.setObjectName(u"widget_selection")
        widget_selection.resize(453, 734)
        widget_selection.setMaximumSize(QSize(500, 16777215))
        self.verticalLayout_2 = QVBoxLayout(widget_selection)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.frame = QFrame(widget_selection)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.Panel)
        self.frame.setFrameShadow(QFrame.Plain)
        self.verticalLayout = QVBoxLayout(self.frame)
        self.verticalLayout.setSpacing(4)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(6, 6, 6, 6)
        self.widget_app_controls = Widget_app_controls(self.frame)
        self.widget_app_controls.setObjectName(u"widget_app_controls")

        self.verticalLayout.addWidget(self.widget_app_controls)

        self.comboBox_episode = QComboBox(self.frame)
        self.comboBox_episode.addItem("")
        self.comboBox_episode.addItem("")
        self.comboBox_episode.setObjectName(u"comboBox_episode")
        sizePolicy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.comboBox_episode.sizePolicy().hasHeightForWidth())
        self.comboBox_episode.setSizePolicy(sizePolicy)

        self.verticalLayout.addWidget(self.comboBox_episode)

        self.comboBox_part = QComboBox(self.frame)
        self.comboBox_part.addItem("")
        self.comboBox_part.addItem("")
        self.comboBox_part.addItem("")
        self.comboBox_part.addItem("")
        self.comboBox_part.addItem("")
        self.comboBox_part.addItem("")
        self.comboBox_part.addItem("")
        self.comboBox_part.addItem("")
        self.comboBox_part.setObjectName(u"comboBox_part")
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.comboBox_part.sizePolicy().hasHeightForWidth())
        self.comboBox_part.setSizePolicy(sizePolicy1)
        self.comboBox_part.setMaximumSize(QSize(140, 16777215))

        self.verticalLayout.addWidget(self.comboBox_part)

        self.comboBox_step = QComboBox(self.frame)
        self.comboBox_step.addItem("")
        self.comboBox_step.setObjectName(u"comboBox_step")
        sizePolicy1.setHeightForWidth(self.comboBox_step.sizePolicy().hasHeightForWidth())
        self.comboBox_step.setSizePolicy(sizePolicy1)
        self.comboBox_step.setMaximumSize(QSize(120, 16777215))

        self.verticalLayout.addWidget(self.comboBox_step)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(-1, -1, -1, 0)
        self.label = QLabel(self.frame)
        self.label.setObjectName(u"label")

        self.horizontalLayout.addWidget(self.label)

        self.lineEdit_crop_coordinates = QLineEdit(self.frame)
        self.lineEdit_crop_coordinates.setObjectName(u"lineEdit_crop_coordinates")
        self.lineEdit_crop_coordinates.setMaximumSize(QSize(150, 16777215))
        self.lineEdit_crop_coordinates.setReadOnly(True)

        self.horizontalLayout.addWidget(self.lineEdit_crop_coordinates)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.tableWidget_shots = QTableWidget(self.frame)
        if (self.tableWidget_shots.columnCount() < 5):
            self.tableWidget_shots.setColumnCount(5)
        __qtablewidgetitem = QTableWidgetItem()
        self.tableWidget_shots.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.tableWidget_shots.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.tableWidget_shots.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.tableWidget_shots.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.tableWidget_shots.setHorizontalHeaderItem(4, __qtablewidgetitem4)
        if (self.tableWidget_shots.rowCount() < 20):
            self.tableWidget_shots.setRowCount(20)
        __qtablewidgetitem5 = QTableWidgetItem()
        self.tableWidget_shots.setVerticalHeaderItem(0, __qtablewidgetitem5)
        __qtablewidgetitem6 = QTableWidgetItem()
        self.tableWidget_shots.setVerticalHeaderItem(1, __qtablewidgetitem6)
        __qtablewidgetitem7 = QTableWidgetItem()
        __qtablewidgetitem7.setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled);
        self.tableWidget_shots.setItem(0, 0, __qtablewidgetitem7)
        __qtablewidgetitem8 = QTableWidgetItem()
        self.tableWidget_shots.setItem(0, 1, __qtablewidgetitem8)
        __qtablewidgetitem9 = QTableWidgetItem()
        self.tableWidget_shots.setItem(1, 0, __qtablewidgetitem9)
        __qtablewidgetitem10 = QTableWidgetItem()
        self.tableWidget_shots.setItem(1, 1, __qtablewidgetitem10)
        self.tableWidget_shots.setObjectName(u"tableWidget_shots")
        sizePolicy2 = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Expanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.tableWidget_shots.sizePolicy().hasHeightForWidth())
        self.tableWidget_shots.setSizePolicy(sizePolicy2)
        self.tableWidget_shots.setMinimumSize(QSize(0, 600))
        self.tableWidget_shots.setFrameShape(QFrame.StyledPanel)
        self.tableWidget_shots.setFrameShadow(QFrame.Sunken)
        self.tableWidget_shots.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tableWidget_shots.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContentsOnFirstShow)
        self.tableWidget_shots.setEditTriggers(QAbstractItemView.SelectedClicked)
        self.tableWidget_shots.setProperty("showDropIndicator", False)
        self.tableWidget_shots.setDragDropOverwriteMode(False)
        self.tableWidget_shots.setSelectionMode(QAbstractItemView.ContiguousSelection)
        self.tableWidget_shots.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableWidget_shots.setShowGrid(True)
        self.tableWidget_shots.setWordWrap(False)
        self.tableWidget_shots.setCornerButtonEnabled(False)
        self.tableWidget_shots.setRowCount(20)
        self.tableWidget_shots.setColumnCount(5)
        self.tableWidget_shots.horizontalHeader().setVisible(True)
        self.tableWidget_shots.horizontalHeader().setMinimumSectionSize(28)
        self.tableWidget_shots.horizontalHeader().setDefaultSectionSize(50)
        self.tableWidget_shots.horizontalHeader().setStretchLastSection(True)
        self.tableWidget_shots.verticalHeader().setVisible(False)
        self.tableWidget_shots.verticalHeader().setMinimumSectionSize(22)
        self.tableWidget_shots.verticalHeader().setDefaultSectionSize(22)
        self.tableWidget_shots.verticalHeader().setHighlightSections(True)
        self.tableWidget_shots.verticalHeader().setProperty("showSortIndicator", False)
        self.tableWidget_shots.verticalHeader().setStretchLastSection(False)

        self.verticalLayout.addWidget(self.tableWidget_shots)


        self.verticalLayout_2.addWidget(self.frame)


        self.retranslateUi(widget_selection)

        QMetaObject.connectSlotsByName(widget_selection)
    # setupUi

    def retranslateUi(self, widget_selection):
        widget_selection.setWindowTitle(QCoreApplication.translate("widget_selection", u"Form", None))
        self.comboBox_episode.setItemText(0, "")
        self.comboBox_episode.setItemText(1, QCoreApplication.translate("widget_selection", u"ep01", None))

        self.comboBox_part.setItemText(0, QCoreApplication.translate("widget_selection", u"precedemment", None))
        self.comboBox_part.setItemText(1, QCoreApplication.translate("widget_selection", u"g_debut", None))
        self.comboBox_part.setItemText(2, QCoreApplication.translate("widget_selection", u"episode", None))
        self.comboBox_part.setItemText(3, QCoreApplication.translate("widget_selection", u"g_asuivre", None))
        self.comboBox_part.setItemText(4, QCoreApplication.translate("widget_selection", u"asuivre", None))
        self.comboBox_part.setItemText(5, QCoreApplication.translate("widget_selection", u"g_reportage", None))
        self.comboBox_part.setItemText(6, QCoreApplication.translate("widget_selection", u"reportage", None))
        self.comboBox_part.setItemText(7, QCoreApplication.translate("widget_selection", u"g_fin", None))

        self.comboBox_step.setItemText(0, QCoreApplication.translate("widget_selection", u"deinterlace", None))

        self.label.setText(QCoreApplication.translate("widget_selection", u"crop coordinates:", None))
        self.lineEdit_crop_coordinates.setText(QCoreApplication.translate("widget_selection", u"(10;12;1400;1120)", None))
        ___qtablewidgetitem = self.tableWidget_shots.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("widget_selection", u"shot", None));
        ___qtablewidgetitem1 = self.tableWidget_shots.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("widget_selection", u"start", None));
        ___qtablewidgetitem2 = self.tableWidget_shots.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("widget_selection", u"count", None));
        ___qtablewidgetitem3 = self.tableWidget_shots.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("widget_selection", u"src", None));
        ___qtablewidgetitem4 = self.tableWidget_shots.horizontalHeaderItem(4)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("widget_selection", u"curves", None));
        ___qtablewidgetitem5 = self.tableWidget_shots.verticalHeaderItem(0)
        ___qtablewidgetitem5.setText(QCoreApplication.translate("widget_selection", u"001", None));
        ___qtablewidgetitem6 = self.tableWidget_shots.verticalHeaderItem(1)
        ___qtablewidgetitem6.setText(QCoreApplication.translate("widget_selection", u"002", None));

        __sortingEnabled = self.tableWidget_shots.isSortingEnabled()
        self.tableWidget_shots.setSortingEnabled(False)
        ___qtablewidgetitem7 = self.tableWidget_shots.item(0, 0)
        ___qtablewidgetitem7.setText(QCoreApplication.translate("widget_selection", u"001", None));
        ___qtablewidgetitem8 = self.tableWidget_shots.item(0, 1)
        ___qtablewidgetitem8.setText(QCoreApplication.translate("widget_selection", u"0", None));
        ___qtablewidgetitem9 = self.tableWidget_shots.item(1, 0)
        ___qtablewidgetitem9.setText(QCoreApplication.translate("widget_selection", u"002", None));
        ___qtablewidgetitem10 = self.tableWidget_shots.item(1, 1)
        ___qtablewidgetitem10.setText(QCoreApplication.translate("widget_selection", u"920", None));
        self.tableWidget_shots.setSortingEnabled(__sortingEnabled)

    # retranslateUi

