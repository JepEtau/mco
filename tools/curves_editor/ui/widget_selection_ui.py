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
from PySide6.QtWidgets import (QAbstractItemView, QAbstractScrollArea, QApplication, QCheckBox,
    QComboBox, QFrame, QHBoxLayout, QHeaderView,
    QLabel, QListView, QListWidget, QListWidgetItem,
    QPushButton, QSizePolicy, QSpacerItem, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget)

from common.widget_app_controls import Widget_app_controls

class Ui_widget_selection(object):
    def setupUi(self, widget_selection):
        if not widget_selection.objectName():
            widget_selection.setObjectName(u"widget_selection")
        widget_selection.resize(500, 727)
        widget_selection.setMaximumSize(QSize(500, 16777215))
        self.verticalLayout_5 = QVBoxLayout(widget_selection)
        self.verticalLayout_5.setSpacing(0)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.frame = QFrame(widget_selection)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.Panel)
        self.frame.setFrameShadow(QFrame.Plain)
        self.verticalLayout_4 = QVBoxLayout(self.frame)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(6, 6, 6, 6)
        self.widget_app_controls = Widget_app_controls(self.frame)
        self.widget_app_controls.setObjectName(u"widget_app_controls")

        self.verticalLayout_4.addWidget(self.widget_app_controls)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.comboBox_episode = QComboBox(self.frame)
        self.comboBox_episode.addItem("")
        self.comboBox_episode.addItem("")
        self.comboBox_episode.addItem("")
        self.comboBox_episode.setObjectName(u"comboBox_episode")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.comboBox_episode.sizePolicy().hasHeightForWidth())
        self.comboBox_episode.setSizePolicy(sizePolicy)
        self.comboBox_episode.setMinimumSize(QSize(50, 0))
        self.comboBox_episode.setAcceptDrops(False)
        self.comboBox_episode.setEditable(False)
        self.comboBox_episode.setCurrentText(u"1")
        self.comboBox_episode.setMaxVisibleItems(20)
        self.comboBox_episode.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.comboBox_episode.setFrame(True)

        self.horizontalLayout.addWidget(self.comboBox_episode)

        self.comboBox_part = QComboBox(self.frame)
        self.comboBox_part.addItem("")
        self.comboBox_part.addItem("")
        self.comboBox_part.addItem("")
        self.comboBox_part.addItem("")
        self.comboBox_part.addItem("")
        self.comboBox_part.addItem("")
        self.comboBox_part.addItem("")
        self.comboBox_part.setObjectName(u"comboBox_part")
        sizePolicy1 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.comboBox_part.sizePolicy().hasHeightForWidth())
        self.comboBox_part.setSizePolicy(sizePolicy1)
        self.comboBox_part.setMinimumSize(QSize(140, 0))
        self.comboBox_part.setAcceptDrops(False)
        self.comboBox_part.setEditable(False)
        self.comboBox_part.setCurrentText(u"precedemment")
        self.comboBox_part.setMaxVisibleItems(10)
        self.comboBox_part.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.comboBox_part.setFrame(True)

        self.horizontalLayout.addWidget(self.comboBox_part)

        self.comboBox_edition = QComboBox(self.frame)
        self.comboBox_edition.addItem("")
        self.comboBox_edition.addItem("")
        self.comboBox_edition.addItem("")
        self.comboBox_edition.setObjectName(u"comboBox_edition")
        sizePolicy.setHeightForWidth(self.comboBox_edition.sizePolicy().hasHeightForWidth())
        self.comboBox_edition.setSizePolicy(sizePolicy)
        self.comboBox_edition.setMinimumSize(QSize(50, 0))
        self.comboBox_edition.setAcceptDrops(False)
        self.comboBox_edition.setEditable(False)
        self.comboBox_edition.setCurrentText(u"s")
        self.comboBox_edition.setMaxVisibleItems(10)
        self.comboBox_edition.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.comboBox_edition.setFrame(True)

        self.horizontalLayout.addWidget(self.comboBox_edition)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(-1, 0, -1, -1)
        self.comboBox_step = QComboBox(self.frame)
        self.comboBox_step.addItem("")
        self.comboBox_step.setObjectName(u"comboBox_step")
        sizePolicy.setHeightForWidth(self.comboBox_step.sizePolicy().hasHeightForWidth())
        self.comboBox_step.setSizePolicy(sizePolicy)
        self.comboBox_step.setMinimumSize(QSize(120, 0))

        self.horizontalLayout_6.addWidget(self.comboBox_step)

        self.comboBox_filter_id = QComboBox(self.frame)
        self.comboBox_filter_id.setObjectName(u"comboBox_filter_id")

        self.horizontalLayout_6.addWidget(self.comboBox_filter_id)

        self.horizontalSpacer = QSpacerItem(10, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer)


        self.verticalLayout.addLayout(self.horizontalLayout_6)

        self.list_images = QListWidget(self.frame)
        self.list_images.setObjectName(u"list_images")
        sizePolicy2 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.list_images.sizePolicy().hasHeightForWidth())
        self.list_images.setSizePolicy(sizePolicy2)
        self.list_images.setMinimumSize(QSize(0, 500))
        self.list_images.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.list_images.setProperty("showDropIndicator", False)
        self.list_images.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list_images.setViewMode(QListView.ListMode)

        self.verticalLayout.addWidget(self.list_images)

        self.checkBox_fit_image_to_window = QCheckBox(self.frame)
        self.checkBox_fit_image_to_window.setObjectName(u"checkBox_fit_image_to_window")

        self.verticalLayout.addWidget(self.checkBox_fit_image_to_window)


        self.horizontalLayout_5.addLayout(self.verticalLayout)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(-1, 40, -1, -1)
        self.label_edition_5 = QLabel(self.frame)
        self.label_edition_5.setObjectName(u"label_edition_5")

        self.verticalLayout_3.addWidget(self.label_edition_5)

        self.tableWidget_shots = QTableWidget(self.frame)
        if (self.tableWidget_shots.columnCount() < 6):
            self.tableWidget_shots.setColumnCount(6)
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
        __qtablewidgetitem5 = QTableWidgetItem()
        self.tableWidget_shots.setHorizontalHeaderItem(5, __qtablewidgetitem5)
        if (self.tableWidget_shots.rowCount() < 20):
            self.tableWidget_shots.setRowCount(20)
        __qtablewidgetitem6 = QTableWidgetItem()
        self.tableWidget_shots.setVerticalHeaderItem(0, __qtablewidgetitem6)
        __qtablewidgetitem7 = QTableWidgetItem()
        self.tableWidget_shots.setVerticalHeaderItem(1, __qtablewidgetitem7)
        __qtablewidgetitem8 = QTableWidgetItem()
        __qtablewidgetitem8.setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled);
        self.tableWidget_shots.setItem(0, 2, __qtablewidgetitem8)
        __qtablewidgetitem9 = QTableWidgetItem()
        self.tableWidget_shots.setItem(0, 3, __qtablewidgetitem9)
        __qtablewidgetitem10 = QTableWidgetItem()
        self.tableWidget_shots.setItem(1, 2, __qtablewidgetitem10)
        __qtablewidgetitem11 = QTableWidgetItem()
        self.tableWidget_shots.setItem(1, 3, __qtablewidgetitem11)
        self.tableWidget_shots.setObjectName(u"tableWidget_shots")
        sizePolicy3 = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Expanding)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.tableWidget_shots.sizePolicy().hasHeightForWidth())
        self.tableWidget_shots.setSizePolicy(sizePolicy3)
        self.tableWidget_shots.setMinimumSize(QSize(0, 600))
        self.tableWidget_shots.setFrameShape(QFrame.StyledPanel)
        self.tableWidget_shots.setFrameShadow(QFrame.Sunken)
        self.tableWidget_shots.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tableWidget_shots.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContentsOnFirstShow)
        self.tableWidget_shots.setEditTriggers(QAbstractItemView.SelectedClicked)
        self.tableWidget_shots.setProperty("showDropIndicator", False)
        self.tableWidget_shots.setDragDropOverwriteMode(False)
        self.tableWidget_shots.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tableWidget_shots.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableWidget_shots.setShowGrid(True)
        self.tableWidget_shots.setWordWrap(False)
        self.tableWidget_shots.setCornerButtonEnabled(False)
        self.tableWidget_shots.setRowCount(20)
        self.tableWidget_shots.setColumnCount(6)
        self.tableWidget_shots.horizontalHeader().setVisible(True)
        self.tableWidget_shots.horizontalHeader().setMinimumSectionSize(28)
        self.tableWidget_shots.horizontalHeader().setDefaultSectionSize(40)
        self.tableWidget_shots.horizontalHeader().setStretchLastSection(True)
        self.tableWidget_shots.verticalHeader().setVisible(False)
        self.tableWidget_shots.verticalHeader().setMinimumSectionSize(22)
        self.tableWidget_shots.verticalHeader().setDefaultSectionSize(22)
        self.tableWidget_shots.verticalHeader().setHighlightSections(True)
        self.tableWidget_shots.verticalHeader().setProperty("showSortIndicator", False)
        self.tableWidget_shots.verticalHeader().setStretchLastSection(False)

        self.verticalLayout_3.addWidget(self.tableWidget_shots)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.pushButton_save_shot_curves_selection = QPushButton(self.frame)
        self.pushButton_save_shot_curves_selection.setObjectName(u"pushButton_save_shot_curves_selection")
        sizePolicy1.setHeightForWidth(self.pushButton_save_shot_curves_selection.sizePolicy().hasHeightForWidth())
        self.pushButton_save_shot_curves_selection.setSizePolicy(sizePolicy1)
        icon = QIcon()
        icon.addFile(u"icons/purple/save.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_save_shot_curves_selection.setIcon(icon)
        self.pushButton_save_shot_curves_selection.setIconSize(QSize(16, 16))
        self.pushButton_save_shot_curves_selection.setFlat(True)

        self.horizontalLayout_2.addWidget(self.pushButton_save_shot_curves_selection)

        self.pushButton_remove_shot_curves_selection = QPushButton(self.frame)
        self.pushButton_remove_shot_curves_selection.setObjectName(u"pushButton_remove_shot_curves_selection")
        sizePolicy1.setHeightForWidth(self.pushButton_remove_shot_curves_selection.sizePolicy().hasHeightForWidth())
        self.pushButton_remove_shot_curves_selection.setSizePolicy(sizePolicy1)
        icon1 = QIcon()
        icon1.addFile(u"icons/purple/x-square.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_remove_shot_curves_selection.setIcon(icon1)
        self.pushButton_remove_shot_curves_selection.setIconSize(QSize(16, 16))
        self.pushButton_remove_shot_curves_selection.setFlat(True)

        self.horizontalLayout_2.addWidget(self.pushButton_remove_shot_curves_selection)

        self.pushButton_discard_shot_curves_selection = QPushButton(self.frame)
        self.pushButton_discard_shot_curves_selection.setObjectName(u"pushButton_discard_shot_curves_selection")
        sizePolicy1.setHeightForWidth(self.pushButton_discard_shot_curves_selection.sizePolicy().hasHeightForWidth())
        self.pushButton_discard_shot_curves_selection.setSizePolicy(sizePolicy1)
        icon2 = QIcon()
        icon2.addFile(u"icons/purple/undo.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_discard_shot_curves_selection.setIcon(icon2)
        self.pushButton_discard_shot_curves_selection.setIconSize(QSize(16, 16))
        self.pushButton_discard_shot_curves_selection.setFlat(True)

        self.horizontalLayout_2.addWidget(self.pushButton_discard_shot_curves_selection)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)


        self.verticalLayout_3.addLayout(self.horizontalLayout_2)


        self.horizontalLayout_5.addLayout(self.verticalLayout_3)


        self.verticalLayout_4.addLayout(self.horizontalLayout_5)


        self.verticalLayout_5.addWidget(self.frame)


        self.retranslateUi(widget_selection)

        self.comboBox_part.setCurrentIndex(0)
        self.comboBox_edition.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(widget_selection)
    # setupUi

    def retranslateUi(self, widget_selection):
        widget_selection.setWindowTitle(QCoreApplication.translate("widget_selection", u"Form", None))
        self.comboBox_episode.setItemText(0, QCoreApplication.translate("widget_selection", u"1", None))
        self.comboBox_episode.setItemText(1, QCoreApplication.translate("widget_selection", u"2", None))
        self.comboBox_episode.setItemText(2, QCoreApplication.translate("widget_selection", u"39", None))

        self.comboBox_part.setItemText(0, QCoreApplication.translate("widget_selection", u"precedemment", None))
        self.comboBox_part.setItemText(1, QCoreApplication.translate("widget_selection", u"episode", None))
        self.comboBox_part.setItemText(2, QCoreApplication.translate("widget_selection", u"a_suivre", None))
        self.comboBox_part.setItemText(3, QCoreApplication.translate("widget_selection", u"reportage", None))
        self.comboBox_part.setItemText(4, QCoreApplication.translate("widget_selection", u"g_debut", None))
        self.comboBox_part.setItemText(5, QCoreApplication.translate("widget_selection", u"g_fin", None))
        self.comboBox_part.setItemText(6, QCoreApplication.translate("widget_selection", u"g_asuivre", None))

        self.comboBox_edition.setItemText(0, QCoreApplication.translate("widget_selection", u"s", None))
        self.comboBox_edition.setItemText(1, QCoreApplication.translate("widget_selection", u"k", None))
        self.comboBox_edition.setItemText(2, QCoreApplication.translate("widget_selection", u"a", None))

        self.comboBox_step.setItemText(0, QCoreApplication.translate("widget_selection", u"deinterlaced", None))

        self.checkBox_fit_image_to_window.setText(QCoreApplication.translate("widget_selection", u"Fit to window", None))
        self.label_edition_5.setText(QCoreApplication.translate("widget_selection", u"Shots", None))
        ___qtablewidgetitem = self.tableWidget_shots.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("widget_selection", u"ed", None));
        ___qtablewidgetitem1 = self.tableWidget_shots.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("widget_selection", u"ep", None));
        ___qtablewidgetitem2 = self.tableWidget_shots.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("widget_selection", u"shot", None));
        ___qtablewidgetitem3 = self.tableWidget_shots.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("widget_selection", u"start", None));
        ___qtablewidgetitem4 = self.tableWidget_shots.horizontalHeaderItem(4)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("widget_selection", u"curves", None));
        ___qtablewidgetitem5 = self.tableWidget_shots.horizontalHeaderItem(5)
        ___qtablewidgetitem5.setText(QCoreApplication.translate("widget_selection", u"new_curves", None));
        ___qtablewidgetitem6 = self.tableWidget_shots.verticalHeaderItem(0)
        ___qtablewidgetitem6.setText(QCoreApplication.translate("widget_selection", u"001", None));
        ___qtablewidgetitem7 = self.tableWidget_shots.verticalHeaderItem(1)
        ___qtablewidgetitem7.setText(QCoreApplication.translate("widget_selection", u"002", None));

        __sortingEnabled = self.tableWidget_shots.isSortingEnabled()
        self.tableWidget_shots.setSortingEnabled(False)
        ___qtablewidgetitem8 = self.tableWidget_shots.item(0, 2)
        ___qtablewidgetitem8.setText(QCoreApplication.translate("widget_selection", u"001", None));
        ___qtablewidgetitem9 = self.tableWidget_shots.item(0, 3)
        ___qtablewidgetitem9.setText(QCoreApplication.translate("widget_selection", u"0", None));
        ___qtablewidgetitem10 = self.tableWidget_shots.item(1, 2)
        ___qtablewidgetitem10.setText(QCoreApplication.translate("widget_selection", u"002", None));
        ___qtablewidgetitem11 = self.tableWidget_shots.item(1, 3)
        ___qtablewidgetitem11.setText(QCoreApplication.translate("widget_selection", u"920", None));
        self.tableWidget_shots.setSortingEnabled(__sortingEnabled)

        self.pushButton_save_shot_curves_selection.setText("")
        self.pushButton_remove_shot_curves_selection.setText("")
        self.pushButton_discard_shot_curves_selection.setText("")
    # retranslateUi

