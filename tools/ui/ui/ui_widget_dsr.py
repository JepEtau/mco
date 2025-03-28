# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_widget_dsr.ui'
##
## Created by: Qt User Interface Compiler version 6.8.3
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
    QPushButton, QSizePolicy, QSpacerItem, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget)

class Ui_DsrWidget(object):
    def setupUi(self, DsrWidget):
        if not DsrWidget.objectName():
            DsrWidget.setObjectName(u"DsrWidget")
        DsrWidget.resize(314, 363)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
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
        sizePolicy.setHeightForWidth(self.pushButton_set_preview.sizePolicy().hasHeightForWidth())
        self.pushButton_set_preview.setSizePolicy(sizePolicy)
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
        sizePolicy.setHeightForWidth(self.shortcut.sizePolicy().hasHeightForWidth())
        self.shortcut.setSizePolicy(sizePolicy)
        font = QFont()
        font.setPointSize(8)
        font.setItalic(False)
        self.shortcut.setFont(font)
        self.shortcut.setText(u"(F2)")

        self.horizontalLayout.addWidget(self.shortcut)

        self.horizontalSpacer_2 = QSpacerItem(22, 10, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)

        self.pushButton_set_edition = QPushButton(self.frame)
        self.pushButton_set_edition.setObjectName(u"pushButton_set_edition")
        sizePolicy.setHeightForWidth(self.pushButton_set_edition.sizePolicy().hasHeightForWidth())
        self.pushButton_set_edition.setSizePolicy(sizePolicy)
        self.pushButton_set_edition.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        icon1 = QIcon()
        icon1.addFile(u"./icons/grey/edit_off.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        icon1.addFile(u"./icons/blue/edit.svg", QSize(), QIcon.Mode.Normal, QIcon.State.On)
        icon1.addFile(u"./icons/blue/edit.svg", QSize(), QIcon.Mode.Disabled, QIcon.State.Off)
        icon1.addFile(u"./icons/blue/edit.svg", QSize(), QIcon.Mode.Disabled, QIcon.State.On)
        self.pushButton_set_edition.setIcon(icon1)
        self.pushButton_set_edition.setCheckable(True)
        self.pushButton_set_edition.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_set_edition)

        self.shortcut_3 = QLabel(self.frame)
        self.shortcut_3.setObjectName(u"shortcut_3")
        sizePolicy.setHeightForWidth(self.shortcut_3.sizePolicy().hasHeightForWidth())
        self.shortcut_3.setSizePolicy(sizePolicy)
        self.shortcut_3.setFont(font)
        self.shortcut_3.setText(u"(F3)")

        self.horizontalLayout.addWidget(self.shortcut_3)

        self.horizontalSpacer = QSpacerItem(5, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.pushButton_discard = QPushButton(self.frame)
        self.pushButton_discard.setObjectName(u"pushButton_discard")
        sizePolicy.setHeightForWidth(self.pushButton_discard.sizePolicy().hasHeightForWidth())
        self.pushButton_discard.setSizePolicy(sizePolicy)
        self.pushButton_discard.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        icon2 = QIcon()
        icon2.addFile(u"./icons/purple/undo.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.pushButton_discard.setIcon(icon2)
        self.pushButton_discard.setCheckable(False)
        self.pushButton_discard.setAutoDefault(False)
        self.pushButton_discard.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_discard)

        self.pushButton_save = QPushButton(self.frame)
        self.pushButton_save.setObjectName(u"pushButton_save")
        sizePolicy.setHeightForWidth(self.pushButton_save.sizePolicy().hasHeightForWidth())
        self.pushButton_save.setSizePolicy(sizePolicy)
        self.pushButton_save.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        icon3 = QIcon()
        icon3.addFile(u"./icons/purple/save.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.pushButton_save.setIcon(icon3)
        self.pushButton_save.setCheckable(False)
        self.pushButton_save.setAutoDefault(False)
        self.pushButton_save.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_save)


        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.gridLayout_2 = QGridLayout()
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.pushButton_mask_preview = QPushButton(self.frame)
        self.pushButton_mask_preview.setObjectName(u"pushButton_mask_preview")
        self.pushButton_mask_preview.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.pushButton_mask_preview.setText(u"")
        self.pushButton_mask_preview.setIcon(icon)
        self.pushButton_mask_preview.setCheckable(True)
        self.pushButton_mask_preview.setFlat(True)

        self.gridLayout_2.addWidget(self.pushButton_mask_preview, 0, 1, 1, 1)

        self.label_9 = QLabel(self.frame)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setLineWidth(0)
        self.label_9.setText(u"mask")

        self.gridLayout_2.addWidget(self.label_9, 0, 0, 1, 1)

        self.shortcut_2 = QLabel(self.frame)
        self.shortcut_2.setObjectName(u"shortcut_2")
        font1 = QFont()
        font1.setPointSize(8)
        self.shortcut_2.setFont(font1)
        self.shortcut_2.setText(u"(F3)")

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
        self.pushButton_circle = QPushButton(self.frame)
        self.pushButton_circle.setObjectName(u"pushButton_circle")
        self.pushButton_circle.setMaximumSize(QSize(30, 16777215))
        self.pushButton_circle.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.pushButton_circle.setText(u"")
        icon4 = QIcon()
        icon4.addFile(u"./icons/grey/circle.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        icon4.addFile(u"./icons/blue/circle.svg", QSize(), QIcon.Mode.Normal, QIcon.State.On)
        self.pushButton_circle.setIcon(icon4)
        self.pushButton_circle.setCheckable(True)
        self.pushButton_circle.setAutoExclusive(True)
        self.pushButton_circle.setFlat(False)

        self.horizontalLayout_3.addWidget(self.pushButton_circle)

        self.pushButton_ellipse = QPushButton(self.frame)
        self.pushButton_ellipse.setObjectName(u"pushButton_ellipse")
        self.pushButton_ellipse.setMaximumSize(QSize(30, 16777215))
        self.pushButton_ellipse.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.pushButton_ellipse.setText(u"")
        icon5 = QIcon()
        icon5.addFile(u"./icons/grey/ellipse.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        icon5.addFile(u"./icons/blue/ellipse.svg", QSize(), QIcon.Mode.Normal, QIcon.State.On)
        self.pushButton_ellipse.setIcon(icon5)
        self.pushButton_ellipse.setCheckable(True)
        self.pushButton_ellipse.setAutoExclusive(True)
        self.pushButton_ellipse.setFlat(False)

        self.horizontalLayout_3.addWidget(self.pushButton_ellipse)

        self.pushButton_oblong = QPushButton(self.frame)
        self.pushButton_oblong.setObjectName(u"pushButton_oblong")
        self.pushButton_oblong.setMaximumSize(QSize(30, 16777215))
        self.pushButton_oblong.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.pushButton_oblong.setText(u"oblong")
        self.pushButton_oblong.setCheckable(True)
        self.pushButton_oblong.setAutoExclusive(True)
        self.pushButton_oblong.setFlat(False)

        self.horizontalLayout_3.addWidget(self.pushButton_oblong)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_3)

        self.pushButton_yellow = QPushButton(self.frame)
        self.pushButton_yellow.setObjectName(u"pushButton_yellow")
        self.pushButton_yellow.setMaximumSize(QSize(30, 16777215))
        self.pushButton_yellow.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.pushButton_yellow.setText(u"yellow")
        self.pushButton_yellow.setCheckable(True)
        self.pushButton_yellow.setFlat(False)

        self.horizontalLayout_3.addWidget(self.pushButton_yellow)

        self.pushButton_red = QPushButton(self.frame)
        self.pushButton_red.setObjectName(u"pushButton_red")
        self.pushButton_red.setMaximumSize(QSize(30, 16777215))
        self.pushButton_red.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.pushButton_red.setText(u"red")
        self.pushButton_red.setCheckable(True)
        self.pushButton_red.setFlat(False)

        self.horizontalLayout_3.addWidget(self.pushButton_red)

        self.pushButton_cyan = QPushButton(self.frame)
        self.pushButton_cyan.setObjectName(u"pushButton_cyan")
        self.pushButton_cyan.setMaximumSize(QSize(30, 16777215))
        self.pushButton_cyan.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.pushButton_cyan.setText(u"cyan")
        self.pushButton_cyan.setCheckable(True)
        self.pushButton_cyan.setFlat(False)

        self.horizontalLayout_3.addWidget(self.pushButton_cyan)


        self.verticalLayout.addLayout(self.horizontalLayout_3)


        self.verticalLayout_2.addLayout(self.verticalLayout)

        self.tableWidget_dsr = QTableWidget(self.frame)
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
        self.tableWidget_dsr.setObjectName(u"tableWidget_dsr")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Expanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.tableWidget_dsr.sizePolicy().hasHeightForWidth())
        self.tableWidget_dsr.setSizePolicy(sizePolicy2)
        self.tableWidget_dsr.setMinimumSize(QSize(300, 0))
        self.tableWidget_dsr.setFocusPolicy(Qt.FocusPolicy.NoFocus)
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
        self.pushButton_set_edition.setText("")
        self.pushButton_discard.setText("")
        self.pushButton_save.setText("")
        ___qtablewidgetitem = self.tableWidget_dsr.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("DsrWidget", u"shape", None));
        ___qtablewidgetitem1 = self.tableWidget_dsr.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("DsrWidget", u"center", None));
        ___qtablewidgetitem2 = self.tableWidget_dsr.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("DsrWidget", u"geometry", None));

        __sortingEnabled = self.tableWidget_dsr.isSortingEnabled()
        self.tableWidget_dsr.setSortingEnabled(False)
        ___qtablewidgetitem3 = self.tableWidget_dsr.item(0, 1)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("DsrWidget", u"(50,30) 500x20 -10\u00b0", None));
        self.tableWidget_dsr.setSortingEnabled(__sortingEnabled)

        pass
    # retranslateUi

