# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_widget_warp.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
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
from PySide6.QtWidgets import (QAbstractItemView, QAbstractSpinBox, QApplication, QButtonGroup,
    QCheckBox, QFrame, QHBoxLayout, QHeaderView,
    QLabel, QPushButton, QRadioButton, QSizePolicy,
    QSpacerItem, QSpinBox, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget)

class Ui_WarpWidget(object):
    def setupUi(self, WarpWidget):
        if not WarpWidget.objectName():
            WarpWidget.setObjectName(u"WarpWidget")
        WarpWidget.resize(292, 310)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(WarpWidget.sizePolicy().hasHeightForWidth())
        WarpWidget.setSizePolicy(sizePolicy)
        WarpWidget.setMinimumSize(QSize(0, 280))
        WarpWidget.setMaximumSize(QSize(16777215, 310))
        self.verticalLayout_3 = QVBoxLayout(WarpWidget)
        self.verticalLayout_3.setSpacing(3)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.frame = QFrame(WarpWidget)
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
        self.shortcut.setText(u"(F4)")

        self.horizontalLayout.addWidget(self.shortcut)

        self.horizontalSpacer = QSpacerItem(5, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)


        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(-1, -1, -1, 0)
        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.checkBox_enabled = QCheckBox(self.frame)
        self.checkBox_enabled.setObjectName(u"checkBox_enabled")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.checkBox_enabled.sizePolicy().hasHeightForWidth())
        self.checkBox_enabled.setSizePolicy(sizePolicy2)

        self.horizontalLayout_6.addWidget(self.checkBox_enabled)

        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_6)

        self.pushButton_default_values = QPushButton(self.frame)
        self.pushButton_default_values.setObjectName(u"pushButton_default_values")
        sizePolicy2.setHeightForWidth(self.pushButton_default_values.sizePolicy().hasHeightForWidth())
        self.pushButton_default_values.setSizePolicy(sizePolicy2)

        self.horizontalLayout_6.addWidget(self.pushButton_default_values)


        self.verticalLayout.addLayout(self.horizontalLayout_6)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(18, -1, -1, -1)
        self.radioButton_knn = QRadioButton(self.frame)
        self.matching = QButtonGroup(WarpWidget)
        self.matching.setObjectName(u"matching")
        self.matching.addButton(self.radioButton_knn)
        self.radioButton_knn.setObjectName(u"radioButton_knn")

        self.horizontalLayout_2.addWidget(self.radioButton_knn)

        self.spinBox_knn_ratio = QSpinBox(self.frame)
        self.spinBox_knn_ratio.setObjectName(u"spinBox_knn_ratio")
        self.spinBox_knn_ratio.setMaximumSize(QSize(80, 16777215))
        self.spinBox_knn_ratio.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.spinBox_knn_ratio.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.spinBox_knn_ratio.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        self.spinBox_knn_ratio.setSuffix(u"")
        self.spinBox_knn_ratio.setPrefix(u"")
        self.spinBox_knn_ratio.setMaximum(100)
        self.spinBox_knn_ratio.setValue(15)

        self.horizontalLayout_2.addWidget(self.spinBox_knn_ratio)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(18, -1, -1, -1)
        self.radioButton_bf = QRadioButton(self.frame)
        self.matching.addButton(self.radioButton_bf)
        self.radioButton_bf.setObjectName(u"radioButton_bf")

        self.horizontalLayout_5.addWidget(self.radioButton_bf)


        self.verticalLayout.addLayout(self.horizontalLayout_5)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.label_2 = QLabel(self.frame)
        self.label_2.setObjectName(u"label_2")

        self.horizontalLayout_4.addWidget(self.label_2)

        self.spinBox_max_distance_ratio = QSpinBox(self.frame)
        self.spinBox_max_distance_ratio.setObjectName(u"spinBox_max_distance_ratio")
        self.spinBox_max_distance_ratio.setMaximumSize(QSize(80, 16777215))
        self.spinBox_max_distance_ratio.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.spinBox_max_distance_ratio.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.spinBox_max_distance_ratio.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        self.spinBox_max_distance_ratio.setSuffix(u"")
        self.spinBox_max_distance_ratio.setPrefix(u"")
        self.spinBox_max_distance_ratio.setMaximum(100)
        self.spinBox_max_distance_ratio.setValue(15)

        self.horizontalLayout_4.addWidget(self.spinBox_max_distance_ratio)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_4)


        self.verticalLayout.addLayout(self.horizontalLayout_4)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label = QLabel(self.frame)
        self.label.setObjectName(u"label")

        self.horizontalLayout_3.addWidget(self.label)

        self.radioButton_next = QRadioButton(self.frame)
        self.buttonGroup = QButtonGroup(WarpWidget)
        self.buttonGroup.setObjectName(u"buttonGroup")
        self.buttonGroup.addButton(self.radioButton_next)
        self.radioButton_next.setObjectName(u"radioButton_next")

        self.horizontalLayout_3.addWidget(self.radioButton_next)

        self.radioButton_prev = QRadioButton(self.frame)
        self.buttonGroup.addButton(self.radioButton_prev)
        self.radioButton_prev.setObjectName(u"radioButton_prev")

        self.horizontalLayout_3.addWidget(self.radioButton_prev)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_3)


        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.tableWidget_warp = QTableWidget(self.frame)
        if (self.tableWidget_warp.columnCount() < 2):
            self.tableWidget_warp.setColumnCount(2)
        __qtablewidgetitem = QTableWidgetItem()
        self.tableWidget_warp.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.tableWidget_warp.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        if (self.tableWidget_warp.rowCount() < 2):
            self.tableWidget_warp.setRowCount(2)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.tableWidget_warp.setItem(0, 0, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.tableWidget_warp.setItem(0, 1, __qtablewidgetitem3)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.tableWidget_warp.setItem(1, 0, __qtablewidgetitem4)
        __qtablewidgetitem5 = QTableWidgetItem()
        self.tableWidget_warp.setItem(1, 1, __qtablewidgetitem5)
        self.tableWidget_warp.setObjectName(u"tableWidget_warp")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Maximum)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.tableWidget_warp.sizePolicy().hasHeightForWidth())
        self.tableWidget_warp.setSizePolicy(sizePolicy3)
        self.tableWidget_warp.setMinimumSize(QSize(0, 25))
        self.tableWidget_warp.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.tableWidget_warp.setFrameShape(QFrame.Shape.StyledPanel)
        self.tableWidget_warp.setFrameShadow(QFrame.Shadow.Sunken)
        self.tableWidget_warp.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tableWidget_warp.setEditTriggers(QAbstractItemView.EditTrigger.SelectedClicked)
        self.tableWidget_warp.setProperty(u"showDropIndicator", False)
        self.tableWidget_warp.setDragDropOverwriteMode(False)
        self.tableWidget_warp.setSelectionMode(QAbstractItemView.SelectionMode.ContiguousSelection)
        self.tableWidget_warp.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableWidget_warp.setSortingEnabled(False)
        self.tableWidget_warp.setRowCount(2)
        self.tableWidget_warp.horizontalHeader().setDefaultSectionSize(90)
        self.tableWidget_warp.horizontalHeader().setStretchLastSection(True)
        self.tableWidget_warp.verticalHeader().setVisible(False)
        self.tableWidget_warp.verticalHeader().setMinimumSectionSize(22)
        self.tableWidget_warp.verticalHeader().setDefaultSectionSize(22)

        self.verticalLayout.addWidget(self.tableWidget_warp)


        self.verticalLayout_2.addLayout(self.verticalLayout)


        self.verticalLayout_3.addWidget(self.frame)


        self.retranslateUi(WarpWidget)

        QMetaObject.connectSlotsByName(WarpWidget)
    # setupUi

    def retranslateUi(self, WarpWidget):
        self.pushButton_set_preview.setText("")
        self.checkBox_enabled.setText(QCoreApplication.translate("WarpWidget", u"enable (F3)", None))
        self.pushButton_default_values.setText(QCoreApplication.translate("WarpWidget", u"default", None))
        self.radioButton_knn.setText(QCoreApplication.translate("WarpWidget", u"knn, filter ratio (%)", None))
        self.radioButton_bf.setText(QCoreApplication.translate("WarpWidget", u"Brute Force", None))
        self.label_2.setText(QCoreApplication.translate("WarpWidget", u"max distance ratio  (%)", None))
        self.label.setText(QCoreApplication.translate("WarpWidget", u"Ref.", None))
        self.radioButton_next.setText(QCoreApplication.translate("WarpWidget", u"following", None))
        self.radioButton_prev.setText(QCoreApplication.translate("WarpWidget", u"previous", None))
        ___qtablewidgetitem = self.tableWidget_warp.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("WarpWidget", u"frame", None));
        ___qtablewidgetitem1 = self.tableWidget_warp.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("WarpWidget", u"params", None));

        __sortingEnabled = self.tableWidget_warp.isSortingEnabled()
        self.tableWidget_warp.setSortingEnabled(False)
        ___qtablewidgetitem2 = self.tableWidget_warp.item(0, 0)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("WarpWidget", u"123456", None));
        ___qtablewidgetitem3 = self.tableWidget_warp.item(0, 1)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("WarpWidget", u"knn, 75%, bf", None));
        self.tableWidget_warp.setSortingEnabled(__sortingEnabled)

        pass
    # retranslateUi

