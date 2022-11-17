# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_widget_curves_selection.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QHBoxLayout, QLabel,
    QLineEdit, QListView, QListWidget, QListWidgetItem,
    QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class Ui_widget_curves_selection(object):
    def setupUi(self, widget_curves_selection):
        if not widget_curves_selection.objectName():
            widget_curves_selection.setObjectName(u"widget_curves_selection")
        widget_curves_selection.resize(171, 344)
        self.verticalLayout_3 = QVBoxLayout(widget_curves_selection)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.list_curves = QListWidget(widget_curves_selection)
        self.list_curves.setObjectName(u"list_curves")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.list_curves.sizePolicy().hasHeightForWidth())
        self.list_curves.setSizePolicy(sizePolicy)
        self.list_curves.setMaximumSize(QSize(100, 16777215))
        self.list_curves.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.list_curves.setProperty("showDropIndicator", False)
        self.list_curves.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list_curves.setViewMode(QListView.ListMode)

        self.horizontalLayout_3.addWidget(self.list_curves)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.pushButton_discard = QPushButton(widget_curves_selection)
        self.pushButton_discard.setObjectName(u"pushButton_discard")
        sizePolicy1 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.pushButton_discard.sizePolicy().hasHeightForWidth())
        self.pushButton_discard.setSizePolicy(sizePolicy1)
        icon = QIcon()
        icon.addFile(u"icons/blue/undo.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_discard.setIcon(icon)
        self.pushButton_discard.setFlat(True)

        self.verticalLayout_2.addWidget(self.pushButton_discard)

        self.pushButton_delete = QPushButton(widget_curves_selection)
        self.pushButton_delete.setObjectName(u"pushButton_delete")
        sizePolicy2 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.pushButton_delete.sizePolicy().hasHeightForWidth())
        self.pushButton_delete.setSizePolicy(sizePolicy2)
        icon1 = QIcon()
        icon1.addFile(u"icons/purple/x-square.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_delete.setIcon(icon1)
        self.pushButton_delete.setFlat(True)

        self.verticalLayout_2.addWidget(self.pushButton_delete)

        self.verticalSpacer_2 = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.MinimumExpanding)

        self.verticalLayout_2.addItem(self.verticalSpacer_2)

        self.label_edition_6 = QLabel(widget_curves_selection)
        self.label_edition_6.setObjectName(u"label_edition_6")
        sizePolicy3 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.label_edition_6.sizePolicy().hasHeightForWidth())
        self.label_edition_6.setSizePolicy(sizePolicy3)

        self.verticalLayout_2.addWidget(self.label_edition_6)

        self.list_shots = QListWidget(widget_curves_selection)
        __qlistwidgetitem = QListWidgetItem(self.list_shots)
        __qlistwidgetitem.setTextAlignment(Qt.AlignTrailing|Qt.AlignVCenter);
        QListWidgetItem(self.list_shots)
        self.list_shots.setObjectName(u"list_shots")
        self.list_shots.setEnabled(False)
        sizePolicy4 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Expanding)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.list_shots.sizePolicy().hasHeightForWidth())
        self.list_shots.setSizePolicy(sizePolicy4)
        self.list_shots.setMinimumSize(QSize(0, 0))
        self.list_shots.setMaximumSize(QSize(40, 16777215))
        self.list_shots.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.list_shots.setProperty("showDropIndicator", False)
        self.list_shots.setSelectionMode(QAbstractItemView.NoSelection)
        self.list_shots.setViewMode(QListView.ListMode)
        self.list_shots.setItemAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.verticalLayout_2.addWidget(self.list_shots)

        self.verticalSpacer = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)


        self.horizontalLayout_3.addLayout(self.verticalLayout_2)


        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(4)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.lineEdit_save = QLineEdit(widget_curves_selection)
        self.lineEdit_save.setObjectName(u"lineEdit_save")
        self.lineEdit_save.setMaximumSize(QSize(90, 16777215))
        self.lineEdit_save.setFrame(False)

        self.horizontalLayout_2.addWidget(self.lineEdit_save)

        self.label = QLabel(widget_curves_selection)
        self.label.setObjectName(u"label")
        sizePolicy3.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy3)

        self.horizontalLayout_2.addWidget(self.label)

        self.pushButton_save_rgb_curves = QPushButton(widget_curves_selection)
        self.pushButton_save_rgb_curves.setObjectName(u"pushButton_save_rgb_curves")
        sizePolicy1.setHeightForWidth(self.pushButton_save_rgb_curves.sizePolicy().hasHeightForWidth())
        self.pushButton_save_rgb_curves.setSizePolicy(sizePolicy1)
        icon2 = QIcon()
        icon2.addFile(u"icons/grey/save.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon2.addFile(u"icons/purple/save.svg", QSize(), QIcon.Normal, QIcon.On)
        self.pushButton_save_rgb_curves.setIcon(icon2)
        self.pushButton_save_rgb_curves.setFlat(True)

        self.horizontalLayout_2.addWidget(self.pushButton_save_rgb_curves)


        self.verticalLayout.addLayout(self.horizontalLayout_2)


        self.verticalLayout_3.addLayout(self.verticalLayout)


        self.retranslateUi(widget_curves_selection)

        QMetaObject.connectSlotsByName(widget_curves_selection)
    # setupUi

    def retranslateUi(self, widget_curves_selection):
        widget_curves_selection.setWindowTitle(QCoreApplication.translate("widget_curves_selection", u"Form", None))
        self.pushButton_discard.setText("")
        self.pushButton_delete.setText("")
        self.label_edition_6.setText(QCoreApplication.translate("widget_curves_selection", u"Shots", None))

        __sortingEnabled = self.list_shots.isSortingEnabled()
        self.list_shots.setSortingEnabled(False)
        ___qlistwidgetitem = self.list_shots.item(0)
        ___qlistwidgetitem.setText(QCoreApplication.translate("widget_curves_selection", u"002", None));
        ___qlistwidgetitem1 = self.list_shots.item(1)
        ___qlistwidgetitem1.setText(QCoreApplication.translate("widget_curves_selection", u"004", None));
        self.list_shots.setSortingEnabled(__sortingEnabled)

        self.label.setText(QCoreApplication.translate("widget_curves_selection", u".crv", None))
        self.pushButton_save_rgb_curves.setText("")
    # retranslateUi

