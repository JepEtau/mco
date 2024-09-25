# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_widget_selection.ui'
##
## Created by: Qt User Interface Compiler version 6.7.2
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
    QFrame, QHBoxLayout, QHeaderView, QPushButton,
    QSizePolicy, QSpacerItem, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget)

class Ui_SelectionWidget(object):
    def setupUi(self, SelectionWidget):
        if not SelectionWidget.objectName():
            SelectionWidget.setObjectName(u"SelectionWidget")
        SelectionWidget.resize(400, 646)
        SelectionWidget.setMaximumSize(QSize(400, 16777215))
        self.verticalLayout_2 = QVBoxLayout(SelectionWidget)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.frame = QFrame(SelectionWidget)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.Shape.Panel)
        self.frame.setFrameShadow(QFrame.Shadow.Plain)
        self.verticalLayout = QVBoxLayout(self.frame)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(6, 6, 6, 6)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(-1, -1, -1, 0)
        self.comboBox_episode = QComboBox(self.frame)
        self.comboBox_episode.addItem("")
        self.comboBox_episode.addItem("")
        self.comboBox_episode.setObjectName(u"comboBox_episode")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.comboBox_episode.sizePolicy().hasHeightForWidth())
        self.comboBox_episode.setSizePolicy(sizePolicy)
        self.comboBox_episode.setMinimumSize(QSize(50, 0))
        self.comboBox_episode.setEditable(True)

        self.horizontalLayout.addWidget(self.comboBox_episode)

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
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.comboBox_part.sizePolicy().hasHeightForWidth())
        self.comboBox_part.setSizePolicy(sizePolicy1)
        self.comboBox_part.setMinimumSize(QSize(140, 0))
        self.comboBox_part.setMaximumSize(QSize(140, 16777215))

        self.horizontalLayout.addWidget(self.comboBox_part)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.pushButton_save = QPushButton(self.frame)
        self.pushButton_save.setObjectName(u"pushButton_save")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.pushButton_save.sizePolicy().hasHeightForWidth())
        self.pushButton_save.setSizePolicy(sizePolicy2)
        icon = QIcon()
        icon.addFile(u"./icons/grey/save.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        icon.addFile(u"./icons/purple/save.svg", QSize(), QIcon.Mode.Normal, QIcon.State.On)
        self.pushButton_save.setIcon(icon)
        self.pushButton_save.setCheckable(False)
        self.pushButton_save.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_save)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.tableWidget_scenes = QTableWidget(self.frame)
        if (self.tableWidget_scenes.columnCount() < 7):
            self.tableWidget_scenes.setColumnCount(7)
        __qtablewidgetitem = QTableWidgetItem()
        self.tableWidget_scenes.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.tableWidget_scenes.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.tableWidget_scenes.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.tableWidget_scenes.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.tableWidget_scenes.setHorizontalHeaderItem(4, __qtablewidgetitem4)
        __qtablewidgetitem5 = QTableWidgetItem()
        self.tableWidget_scenes.setHorizontalHeaderItem(5, __qtablewidgetitem5)
        __qtablewidgetitem6 = QTableWidgetItem()
        self.tableWidget_scenes.setHorizontalHeaderItem(6, __qtablewidgetitem6)
        if (self.tableWidget_scenes.rowCount() < 20):
            self.tableWidget_scenes.setRowCount(20)
        __qtablewidgetitem7 = QTableWidgetItem()
        self.tableWidget_scenes.setVerticalHeaderItem(0, __qtablewidgetitem7)
        __qtablewidgetitem8 = QTableWidgetItem()
        self.tableWidget_scenes.setVerticalHeaderItem(1, __qtablewidgetitem8)
        __qtablewidgetitem9 = QTableWidgetItem()
        __qtablewidgetitem9.setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled);
        self.tableWidget_scenes.setItem(0, 0, __qtablewidgetitem9)
        __qtablewidgetitem10 = QTableWidgetItem()
        self.tableWidget_scenes.setItem(0, 2, __qtablewidgetitem10)
        __qtablewidgetitem11 = QTableWidgetItem()
        self.tableWidget_scenes.setItem(1, 0, __qtablewidgetitem11)
        __qtablewidgetitem12 = QTableWidgetItem()
        self.tableWidget_scenes.setItem(1, 2, __qtablewidgetitem12)
        self.tableWidget_scenes.setObjectName(u"tableWidget_scenes")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.tableWidget_scenes.sizePolicy().hasHeightForWidth())
        self.tableWidget_scenes.setSizePolicy(sizePolicy3)
        self.tableWidget_scenes.setMinimumSize(QSize(0, 600))
        self.tableWidget_scenes.setFrameShape(QFrame.Shape.StyledPanel)
        self.tableWidget_scenes.setFrameShadow(QFrame.Shadow.Sunken)
        self.tableWidget_scenes.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tableWidget_scenes.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContentsOnFirstShow)
        self.tableWidget_scenes.setEditTriggers(QAbstractItemView.EditTrigger.SelectedClicked)
        self.tableWidget_scenes.setProperty("showDropIndicator", False)
        self.tableWidget_scenes.setDragDropOverwriteMode(False)
        self.tableWidget_scenes.setSelectionMode(QAbstractItemView.SelectionMode.ContiguousSelection)
        self.tableWidget_scenes.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableWidget_scenes.setShowGrid(True)
        self.tableWidget_scenes.setWordWrap(False)
        self.tableWidget_scenes.setCornerButtonEnabled(False)
        self.tableWidget_scenes.setRowCount(20)
        self.tableWidget_scenes.setColumnCount(7)
        self.tableWidget_scenes.horizontalHeader().setVisible(True)
        self.tableWidget_scenes.horizontalHeader().setMinimumSectionSize(28)
        self.tableWidget_scenes.horizontalHeader().setDefaultSectionSize(40)
        self.tableWidget_scenes.horizontalHeader().setStretchLastSection(True)
        self.tableWidget_scenes.verticalHeader().setVisible(False)
        self.tableWidget_scenes.verticalHeader().setMinimumSectionSize(24)
        self.tableWidget_scenes.verticalHeader().setDefaultSectionSize(24)
        self.tableWidget_scenes.verticalHeader().setHighlightSections(True)
        self.tableWidget_scenes.verticalHeader().setProperty("showSortIndicator", False)
        self.tableWidget_scenes.verticalHeader().setStretchLastSection(False)

        self.verticalLayout.addWidget(self.tableWidget_scenes)


        self.verticalLayout_2.addWidget(self.frame)


        self.retranslateUi(SelectionWidget)

        QMetaObject.connectSlotsByName(SelectionWidget)
    # setupUi

    def retranslateUi(self, SelectionWidget):
        SelectionWidget.setWindowTitle(QCoreApplication.translate("SelectionWidget", u"Form", None))
        self.comboBox_episode.setItemText(0, QCoreApplication.translate("SelectionWidget", u"ep01", None))
        self.comboBox_episode.setItemText(1, QCoreApplication.translate("SelectionWidget", u"ep02", None))

        self.comboBox_part.setItemText(0, QCoreApplication.translate("SelectionWidget", u"g_debut", None))
        self.comboBox_part.setItemText(1, QCoreApplication.translate("SelectionWidget", u"precedemment", None))
        self.comboBox_part.setItemText(2, QCoreApplication.translate("SelectionWidget", u"episode", None))
        self.comboBox_part.setItemText(3, QCoreApplication.translate("SelectionWidget", u"g_asuivre", None))
        self.comboBox_part.setItemText(4, QCoreApplication.translate("SelectionWidget", u"asuivre", None))
        self.comboBox_part.setItemText(5, QCoreApplication.translate("SelectionWidget", u"g_documentaire", None))
        self.comboBox_part.setItemText(6, QCoreApplication.translate("SelectionWidget", u"documentaire", None))
        self.comboBox_part.setItemText(7, QCoreApplication.translate("SelectionWidget", u"g_fin", None))

        self.pushButton_save.setText("")
        ___qtablewidgetitem = self.tableWidget_scenes.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("SelectionWidget", u"scene", None));
        ___qtablewidgetitem1 = self.tableWidget_scenes.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("SelectionWidget", u"src", None));
        ___qtablewidgetitem2 = self.tableWidget_scenes.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("SelectionWidget", u"start", None));
        ___qtablewidgetitem3 = self.tableWidget_scenes.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("SelectionWidget", u"count", None));
        ___qtablewidgetitem4 = self.tableWidget_scenes.horizontalHeaderItem(4)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("SelectionWidget", u"stab.", None));
        ___qtablewidgetitem5 = self.tableWidget_scenes.horizontalHeaderItem(5)
        ___qtablewidgetitem5.setText(QCoreApplication.translate("SelectionWidget", u"Fit", None));
        ___qtablewidgetitem6 = self.tableWidget_scenes.horizontalHeaderItem(6)
        ___qtablewidgetitem6.setText(QCoreApplication.translate("SelectionWidget", u"Ratio", None));
        ___qtablewidgetitem7 = self.tableWidget_scenes.verticalHeaderItem(0)
        ___qtablewidgetitem7.setText(QCoreApplication.translate("SelectionWidget", u"001", None));
        ___qtablewidgetitem8 = self.tableWidget_scenes.verticalHeaderItem(1)
        ___qtablewidgetitem8.setText(QCoreApplication.translate("SelectionWidget", u"002", None));

        __sortingEnabled = self.tableWidget_scenes.isSortingEnabled()
        self.tableWidget_scenes.setSortingEnabled(False)
        ___qtablewidgetitem9 = self.tableWidget_scenes.item(0, 0)
        ___qtablewidgetitem9.setText(QCoreApplication.translate("SelectionWidget", u"001", None));
        ___qtablewidgetitem10 = self.tableWidget_scenes.item(0, 2)
        ___qtablewidgetitem10.setText(QCoreApplication.translate("SelectionWidget", u"0", None));
        ___qtablewidgetitem11 = self.tableWidget_scenes.item(1, 0)
        ___qtablewidgetitem11.setText(QCoreApplication.translate("SelectionWidget", u"002", None));
        ___qtablewidgetitem12 = self.tableWidget_scenes.item(1, 2)
        ___qtablewidgetitem12.setText(QCoreApplication.translate("SelectionWidget", u"920", None));
        self.tableWidget_scenes.setSortingEnabled(__sortingEnabled)

    # retranslateUi

