# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_widget_curves_browser.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QHBoxLayout,
    QLabel, QLineEdit, QListView, QListWidget,
    QListWidgetItem, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_widget_curves_browser(object):
    def setupUi(self, widget_curves_browser):
        if not widget_curves_browser.objectName():
            widget_curves_browser.setObjectName(u"widget_curves_browser")
        widget_curves_browser.resize(320, 664)
        self.horizontalLayout = QHBoxLayout(widget_curves_browser)
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setSpacing(5)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.verticalLayout_5 = QVBoxLayout()
        self.verticalLayout_5.setSpacing(3)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label_edition_4 = QLabel(widget_curves_browser)
        self.label_edition_4.setObjectName(u"label_edition_4")

        self.horizontalLayout_3.addWidget(self.label_edition_4)

        self.horizontalSpacer_3 = QSpacerItem(5, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_3)

        self.combobox_filter_by_episode = QComboBox(widget_curves_browser)
        self.combobox_filter_by_episode.addItem("")
        self.combobox_filter_by_episode.addItem("")
        self.combobox_filter_by_episode.addItem("")
        self.combobox_filter_by_episode.setObjectName(u"combobox_filter_by_episode")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.combobox_filter_by_episode.sizePolicy().hasHeightForWidth())
        self.combobox_filter_by_episode.setSizePolicy(sizePolicy)
        self.combobox_filter_by_episode.setMinimumSize(QSize(0, 0))
        self.combobox_filter_by_episode.setAcceptDrops(False)
        self.combobox_filter_by_episode.setEditable(True)
        self.combobox_filter_by_episode.setCurrentText(u"1")
        self.combobox_filter_by_episode.setMaxVisibleItems(20)
        self.combobox_filter_by_episode.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.combobox_filter_by_episode.setFrame(True)

        self.horizontalLayout_3.addWidget(self.combobox_filter_by_episode)


        self.verticalLayout_5.addLayout(self.horizontalLayout_3)

        self.list_curve_names = QListWidget(widget_curves_browser)
        self.list_curve_names.setObjectName(u"list_curve_names")
        sizePolicy1 = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.list_curve_names.sizePolicy().hasHeightForWidth())
        self.list_curve_names.setSizePolicy(sizePolicy1)
        self.list_curve_names.setMinimumSize(QSize(120, 600))
        self.list_curve_names.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.list_curve_names.setProperty("showDropIndicator", False)
        self.list_curve_names.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list_curve_names.setViewMode(QListView.ListMode)

        self.verticalLayout_5.addWidget(self.list_curve_names)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(-1, -1, -1, 0)
        self.lineEdit_save_name = QLineEdit(widget_curves_browser)
        self.lineEdit_save_name.setObjectName(u"lineEdit_save_name")
        self.lineEdit_save_name.setMaximumSize(QSize(100, 16777215))
        self.lineEdit_save_name.setFrame(False)

        self.horizontalLayout_2.addWidget(self.lineEdit_save_name)

        self.label = QLabel(widget_curves_browser)
        self.label.setObjectName(u"label")

        self.horizontalLayout_2.addWidget(self.label)

        self.pushButton_save = QPushButton(widget_curves_browser)
        self.pushButton_save.setObjectName(u"pushButton_save")
        sizePolicy2 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.pushButton_save.sizePolicy().hasHeightForWidth())
        self.pushButton_save.setSizePolicy(sizePolicy2)
        icon = QIcon()
        icon.addFile(u"img/document-save-as.png", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_save.setIcon(icon)
        self.pushButton_save.setFlat(True)

        self.horizontalLayout_2.addWidget(self.pushButton_save)


        self.verticalLayout_5.addLayout(self.horizontalLayout_2)


        self.horizontalLayout_4.addLayout(self.verticalLayout_5)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setSpacing(3)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(-1, 0, -1, 60)
        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer)

        self.label_edition_6 = QLabel(widget_curves_browser)
        self.label_edition_6.setObjectName(u"label_edition_6")
        sizePolicy3 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.label_edition_6.sizePolicy().hasHeightForWidth())
        self.label_edition_6.setSizePolicy(sizePolicy3)

        self.verticalLayout_3.addWidget(self.label_edition_6)

        self.list_shots_using_same_curves = QListWidget(widget_curves_browser)
        QListWidgetItem(self.list_shots_using_same_curves)
        QListWidgetItem(self.list_shots_using_same_curves)
        self.list_shots_using_same_curves.setObjectName(u"list_shots_using_same_curves")
        self.list_shots_using_same_curves.setEnabled(True)
        sizePolicy4 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Expanding)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.list_shots_using_same_curves.sizePolicy().hasHeightForWidth())
        self.list_shots_using_same_curves.setSizePolicy(sizePolicy4)
        self.list_shots_using_same_curves.setMinimumSize(QSize(0, 0))
        self.list_shots_using_same_curves.setMaximumSize(QSize(50, 16777215))
        self.list_shots_using_same_curves.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.list_shots_using_same_curves.setProperty("showDropIndicator", False)
        self.list_shots_using_same_curves.setSelectionMode(QAbstractItemView.NoSelection)
        self.list_shots_using_same_curves.setViewMode(QListView.ListMode)

        self.verticalLayout_3.addWidget(self.list_shots_using_same_curves)


        self.horizontalLayout_4.addLayout(self.verticalLayout_3)


        self.verticalLayout_4.addLayout(self.horizontalLayout_4)


        self.horizontalLayout.addLayout(self.verticalLayout_4)


        self.retranslateUi(widget_curves_browser)

        QMetaObject.connectSlotsByName(widget_curves_browser)
    # setupUi

    def retranslateUi(self, widget_curves_browser):
        widget_curves_browser.setWindowTitle(QCoreApplication.translate("widget_curves_browser", u"Form", None))
        self.label_edition_4.setText(QCoreApplication.translate("widget_curves_browser", u"curves", None))
        self.combobox_filter_by_episode.setItemText(0, QCoreApplication.translate("widget_curves_browser", u"1", None))
        self.combobox_filter_by_episode.setItemText(1, QCoreApplication.translate("widget_curves_browser", u"2", None))
        self.combobox_filter_by_episode.setItemText(2, QCoreApplication.translate("widget_curves_browser", u"39", None))

        self.label.setText(QCoreApplication.translate("widget_curves_browser", u".crv", None))
        self.pushButton_save.setText("")
        self.label_edition_6.setText(QCoreApplication.translate("widget_curves_browser", u"Shots", None))

        __sortingEnabled = self.list_shots_using_same_curves.isSortingEnabled()
        self.list_shots_using_same_curves.setSortingEnabled(False)
        ___qlistwidgetitem = self.list_shots_using_same_curves.item(0)
        ___qlistwidgetitem.setText(QCoreApplication.translate("widget_curves_browser", u"002", None));
        ___qlistwidgetitem1 = self.list_shots_using_same_curves.item(1)
        ___qlistwidgetitem1.setText(QCoreApplication.translate("widget_curves_browser", u"004", None));
        self.list_shots_using_same_curves.setSortingEnabled(__sortingEnabled)

    # retranslateUi

