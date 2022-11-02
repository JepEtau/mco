# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_widget_stitching_curves.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QListView, QListWidget,
    QListWidgetItem, QPushButton, QRadioButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

from merge_stabilize.widget_hist_curves import Widget_hist_curves
from merge_stabilize.widget_hist_graph import Widget_hist_graph

class Ui_widget_stitching_curves(object):
    def setupUi(self, widget_stitching_curves):
        if not widget_stitching_curves.objectName():
            widget_stitching_curves.setObjectName(u"widget_stitching_curves")
        widget_stitching_curves.resize(614, 318)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(widget_stitching_curves.sizePolicy().hasHeightForWidth())
        widget_stitching_curves.setSizePolicy(sizePolicy)
        self.verticalLayout_5 = QVBoxLayout(widget_stitching_curves)
        self.verticalLayout_5.setSpacing(0)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.frame = QFrame(widget_stitching_curves)
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
        icon.addFile(u"img/grey/eye.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon.addFile(u"img/blue/eye.svg", QSize(), QIcon.Normal, QIcon.On)
        self.pushButton_set_preview.setIcon(icon)
        self.pushButton_set_preview.setCheckable(True)
        self.pushButton_set_preview.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_set_preview)

        self.label = QLabel(self.frame)
        self.label.setObjectName(u"label")

        self.horizontalLayout.addWidget(self.label)

        self.lineEdit_current_curves_selection = QLineEdit(self.frame)
        self.lineEdit_current_curves_selection.setObjectName(u"lineEdit_current_curves_selection")
        self.lineEdit_current_curves_selection.setMaximumSize(QSize(80, 16777215))
        self.lineEdit_current_curves_selection.setAlignment(Qt.AlignCenter)
        self.lineEdit_current_curves_selection.setDragEnabled(True)

        self.horizontalLayout.addWidget(self.lineEdit_current_curves_selection)

        self.pushButton_save = QPushButton(self.frame)
        self.pushButton_save.setObjectName(u"pushButton_save")
        sizePolicy1.setHeightForWidth(self.pushButton_save.sizePolicy().hasHeightForWidth())
        self.pushButton_save.setSizePolicy(sizePolicy1)
        icon1 = QIcon()
        icon1.addFile(u"img/grey/save.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon1.addFile(u"img/purple/save.svg", QSize(), QIcon.Normal, QIcon.On)
        self.pushButton_save.setIcon(icon1)
        self.pushButton_save.setCheckable(False)
        self.pushButton_save.setAutoDefault(False)
        self.pushButton_save.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_save)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_3)

        self.pushButton_discard = QPushButton(self.frame)
        self.pushButton_discard.setObjectName(u"pushButton_discard")
        sizePolicy1.setHeightForWidth(self.pushButton_discard.sizePolicy().hasHeightForWidth())
        self.pushButton_discard.setSizePolicy(sizePolicy1)
        icon2 = QIcon()
        icon2.addFile(u"img/grey/undo.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon2.addFile(u"img/purple/undo.svg", QSize(), QIcon.Normal, QIcon.On)
        self.pushButton_discard.setIcon(icon2)
        self.pushButton_discard.setCheckable(False)
        self.pushButton_discard.setAutoDefault(False)
        self.pushButton_discard.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_discard)

        self.pushButton_remove_selection = QPushButton(self.frame)
        self.pushButton_remove_selection.setObjectName(u"pushButton_remove_selection")
        sizePolicy1.setHeightForWidth(self.pushButton_remove_selection.sizePolicy().hasHeightForWidth())
        self.pushButton_remove_selection.setSizePolicy(sizePolicy1)
        icon3 = QIcon()
        icon3.addFile(u"img/edit-delete.png", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_remove_selection.setIcon(icon3)
        self.pushButton_remove_selection.setCheckable(False)
        self.pushButton_remove_selection.setAutoDefault(False)
        self.pushButton_remove_selection.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_remove_selection)

        self.pushButton_undo = QPushButton(self.frame)
        self.pushButton_undo.setObjectName(u"pushButton_undo")
        sizePolicy1.setHeightForWidth(self.pushButton_undo.sizePolicy().hasHeightForWidth())
        self.pushButton_undo.setSizePolicy(sizePolicy1)
        icon4 = QIcon()
        icon4.addFile(u"img/purple/undo.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_undo.setIcon(icon4)
        self.pushButton_undo.setCheckable(False)
        self.pushButton_undo.setAutoDefault(False)
        self.pushButton_undo.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_undo)

        self.horizontalSpacer = QSpacerItem(5, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.pushButton_close = QPushButton(self.frame)
        self.pushButton_close.setObjectName(u"pushButton_close")
        sizePolicy1.setHeightForWidth(self.pushButton_close.sizePolicy().hasHeightForWidth())
        self.pushButton_close.setSizePolicy(sizePolicy1)
        icon5 = QIcon()
        icon5.addFile(u"img/purple/x-square.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon5.addFile(u"img/purple/x-square.svg", QSize(), QIcon.Normal, QIcon.On)
        self.pushButton_close.setIcon(icon5)
        self.pushButton_close.setCheckable(False)
        self.pushButton_close.setAutoDefault(False)
        self.pushButton_close.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_close)


        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setSpacing(10)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(-1, -1, -1, 0)
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setSpacing(10)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.widget_hist_graph = Widget_hist_graph(self.frame)
        self.widget_hist_graph.setObjectName(u"widget_hist_graph")
        self.widget_hist_graph.setEnabled(True)
        sizePolicy2 = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.widget_hist_graph.sizePolicy().hasHeightForWidth())
        self.widget_hist_graph.setSizePolicy(sizePolicy2)
        self.widget_hist_graph.setStyleSheet(u"background-color: rgb(220, 255, 255);")

        self.verticalLayout.addWidget(self.widget_hist_graph)

        self.widget_hist_curves = Widget_hist_curves(self.frame)
        self.widget_hist_curves.setObjectName(u"widget_hist_curves")
        self.widget_hist_curves.setEnabled(True)
        self.widget_hist_curves.setStyleSheet(u"background-color: rgb(220, 255, 255);")

        self.verticalLayout.addWidget(self.widget_hist_curves)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(10)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.radioButton_select_r_channel = QRadioButton(self.frame)
        self.radioButton_select_r_channel.setObjectName(u"radioButton_select_r_channel")

        self.horizontalLayout_2.addWidget(self.radioButton_select_r_channel)

        self.radioButton_select_g_channel = QRadioButton(self.frame)
        self.radioButton_select_g_channel.setObjectName(u"radioButton_select_g_channel")

        self.horizontalLayout_2.addWidget(self.radioButton_select_g_channel)

        self.radioButton_select_b_channel = QRadioButton(self.frame)
        self.radioButton_select_b_channel.setObjectName(u"radioButton_select_b_channel")

        self.horizontalLayout_2.addWidget(self.radioButton_select_b_channel)

        self.horizontalSpacer1_5 = QSpacerItem(20, 20, QSizePolicy.Preferred, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer1_5)

        self.lineEdit_coordinates = QLineEdit(self.frame)
        self.lineEdit_coordinates.setObjectName(u"lineEdit_coordinates")
        sizePolicy3 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.lineEdit_coordinates.sizePolicy().hasHeightForWidth())
        self.lineEdit_coordinates.setSizePolicy(sizePolicy3)
        self.lineEdit_coordinates.setMaximumSize(QSize(100, 16777215))
        self.lineEdit_coordinates.setAlignment(Qt.AlignCenter)
        self.lineEdit_coordinates.setReadOnly(True)

        self.horizontalLayout_2.addWidget(self.lineEdit_coordinates)

        self.horizontalSpacer_4 = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_4)

        self.label_out_4 = QLabel(self.frame)
        self.label_out_4.setObjectName(u"label_out_4")
        sizePolicy4 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.label_out_4.sizePolicy().hasHeightForWidth())
        self.label_out_4.setSizePolicy(sizePolicy4)
        self.label_out_4.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_2.addWidget(self.label_out_4)

        self.pushButton_reset_current_channel = QPushButton(self.frame)
        self.pushButton_reset_current_channel.setObjectName(u"pushButton_reset_current_channel")
        sizePolicy5 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.pushButton_reset_current_channel.sizePolicy().hasHeightForWidth())
        self.pushButton_reset_current_channel.setSizePolicy(sizePolicy5)
        self.pushButton_reset_current_channel.setMaximumSize(QSize(70, 16777215))

        self.horizontalLayout_2.addWidget(self.pushButton_reset_current_channel)

        self.pushButton_reset_all_channels = QPushButton(self.frame)
        self.pushButton_reset_all_channels.setObjectName(u"pushButton_reset_all_channels")
        sizePolicy5.setHeightForWidth(self.pushButton_reset_all_channels.sizePolicy().hasHeightForWidth())
        self.pushButton_reset_all_channels.setSizePolicy(sizePolicy5)
        self.pushButton_reset_all_channels.setMaximumSize(QSize(50, 16777215))

        self.horizontalLayout_2.addWidget(self.pushButton_reset_all_channels)


        self.verticalLayout.addLayout(self.horizontalLayout_2)


        self.horizontalLayout_6.addLayout(self.verticalLayout)

        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setSpacing(50)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setSpacing(3)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.list_curves_names = QListWidget(self.frame)
        self.list_curves_names.setObjectName(u"list_curves_names")
        self.list_curves_names.setMinimumSize(QSize(1, 100))
        self.list_curves_names.setMaximumSize(QSize(80, 16777215))
        self.list_curves_names.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.list_curves_names.setProperty("showDropIndicator", False)
        self.list_curves_names.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list_curves_names.setViewMode(QListView.ListMode)

        self.horizontalLayout_5.addWidget(self.list_curves_names)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setSpacing(20)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(-1, -1, -1, 10)
        self.pushButton_save_curves_modifications = QPushButton(self.frame)
        self.pushButton_save_curves_modifications.setObjectName(u"pushButton_save_curves_modifications")
        sizePolicy3.setHeightForWidth(self.pushButton_save_curves_modifications.sizePolicy().hasHeightForWidth())
        self.pushButton_save_curves_modifications.setSizePolicy(sizePolicy3)
        icon6 = QIcon()
        icon6.addFile(u"img/purple/save.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_save_curves_modifications.setIcon(icon6)
        self.pushButton_save_curves_modifications.setFlat(True)

        self.verticalLayout_3.addWidget(self.pushButton_save_curves_modifications)

        self.pushButton_discard_curves_modifications = QPushButton(self.frame)
        self.pushButton_discard_curves_modifications.setObjectName(u"pushButton_discard_curves_modifications")
        sizePolicy3.setHeightForWidth(self.pushButton_discard_curves_modifications.sizePolicy().hasHeightForWidth())
        self.pushButton_discard_curves_modifications.setSizePolicy(sizePolicy3)
        self.pushButton_discard_curves_modifications.setIcon(icon4)
        self.pushButton_discard_curves_modifications.setFlat(True)

        self.verticalLayout_3.addWidget(self.pushButton_discard_curves_modifications)

        self.verticalSpacer = QSpacerItem(10, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer)


        self.horizontalLayout_5.addLayout(self.verticalLayout_3)


        self.verticalLayout_4.addLayout(self.horizontalLayout_5)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setSpacing(3)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.lineEdit_save_name = QLineEdit(self.frame)
        self.lineEdit_save_name.setObjectName(u"lineEdit_save_name")
        self.lineEdit_save_name.setMaximumSize(QSize(70, 16777215))

        self.horizontalLayout_4.addWidget(self.lineEdit_save_name)

        self.pushButton_save_curves_as = QPushButton(self.frame)
        self.pushButton_save_curves_as.setObjectName(u"pushButton_save_curves_as")
        sizePolicy3.setHeightForWidth(self.pushButton_save_curves_as.sizePolicy().hasHeightForWidth())
        self.pushButton_save_curves_as.setSizePolicy(sizePolicy3)
        self.pushButton_save_curves_as.setIcon(icon6)
        self.pushButton_save_curves_as.setFlat(True)

        self.horizontalLayout_4.addWidget(self.pushButton_save_curves_as)

        self.horizontalSpacer_2 = QSpacerItem(2, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_2)


        self.verticalLayout_4.addLayout(self.horizontalLayout_4)


        self.horizontalLayout_6.addLayout(self.verticalLayout_4)


        self.verticalLayout_2.addLayout(self.horizontalLayout_6)


        self.verticalLayout_5.addWidget(self.frame)


        self.retranslateUi(widget_stitching_curves)

        QMetaObject.connectSlotsByName(widget_stitching_curves)
    # setupUi

    def retranslateUi(self, widget_stitching_curves):
        widget_stitching_curves.setWindowTitle(QCoreApplication.translate("widget_stitching_curves", u"Form", None))
        self.pushButton_set_preview.setText("")
        self.label.setText(QCoreApplication.translate("widget_stitching_curves", u"Curves before stitching:", None))
        self.pushButton_save.setText("")
        self.pushButton_discard.setText("")
        self.pushButton_remove_selection.setText("")
        self.pushButton_undo.setText("")
        self.pushButton_close.setText("")
        self.radioButton_select_r_channel.setText(QCoreApplication.translate("widget_stitching_curves", u"R", None))
        self.radioButton_select_g_channel.setText(QCoreApplication.translate("widget_stitching_curves", u"G", None))
        self.radioButton_select_b_channel.setText(QCoreApplication.translate("widget_stitching_curves", u"B", None))
        self.lineEdit_coordinates.setText(QCoreApplication.translate("widget_stitching_curves", u"x=255: +16", None))
        self.label_out_4.setText(QCoreApplication.translate("widget_stitching_curves", u"reset:", None))
        self.pushButton_reset_current_channel.setText(QCoreApplication.translate("widget_stitching_curves", u"channel", None))
        self.pushButton_reset_all_channels.setText(QCoreApplication.translate("widget_stitching_curves", u"all", None))
        self.pushButton_save_curves_modifications.setText("")
        self.pushButton_discard_curves_modifications.setText("")
        self.lineEdit_save_name.setText(QCoreApplication.translate("widget_stitching_curves", u"025_001", None))
        self.pushButton_save_curves_as.setText("")
    # retranslateUi

