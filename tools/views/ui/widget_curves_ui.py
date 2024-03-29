# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_widget_curves.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QLayout, QLineEdit, QPushButton,
    QRadioButton, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

from views.widget_curves_selection import Widget_curves_selection
from views.widget_rgb_graph import Widget_rgb_graph

class Ui_widget_curves(object):
    def setupUi(self, widget_curves):
        if not widget_curves.objectName():
            widget_curves.setObjectName(u"widget_curves")
        widget_curves.resize(563, 660)
        self.mainLayout = QVBoxLayout(widget_curves)
        self.mainLayout.setSpacing(0)
        self.mainLayout.setObjectName(u"mainLayout")
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.frame = QFrame(widget_curves)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.Panel)
        self.frame.setFrameShadow(QFrame.Plain)
        self.verticalLayout_2 = QVBoxLayout(self.frame)
        self.verticalLayout_2.setSpacing(10)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(15, 15, 15, 15)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(3)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.pushButton_set_preview = QPushButton(self.frame)
        self.pushButton_set_preview.setObjectName(u"pushButton_set_preview")
        icon = QIcon()
        icon.addFile(u"tools/icons/grey/eye.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon.addFile(u"tools/icons/blue/eye.svg", QSize(), QIcon.Normal, QIcon.On)
        self.pushButton_set_preview.setIcon(icon)
        self.pushButton_set_preview.setCheckable(True)
        self.pushButton_set_preview.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_set_preview)

        self.pushButton_split_line = QPushButton(self.frame)
        self.pushButton_split_line.setObjectName(u"pushButton_split_line")
        sizePolicy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton_split_line.sizePolicy().hasHeightForWidth())
        self.pushButton_split_line.setSizePolicy(sizePolicy)
        self.pushButton_split_line.setFocusPolicy(Qt.NoFocus)
        icon1 = QIcon()
        icon1.addFile(u"tools/icons/grey/flip-horizontal.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon1.addFile(u"tools/icons/blue/flip-horizontal.svg", QSize(), QIcon.Normal, QIcon.On)
        self.pushButton_split_line.setIcon(icon1)
        self.pushButton_split_line.setCheckable(True)
        self.pushButton_split_line.setAutoDefault(False)
        self.pushButton_split_line.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_split_line)

        self.horizontalSpacer_2 = QSpacerItem(22, 10, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)

        self.label_message = QLabel(self.frame)
        self.label_message.setObjectName(u"label_message")

        self.horizontalLayout.addWidget(self.label_message)

        self.horizontalSpacer = QSpacerItem(5, 10, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.pushButton_discard = QPushButton(self.frame)
        self.pushButton_discard.setObjectName(u"pushButton_discard")
        icon2 = QIcon()
        icon2.addFile(u"tools/icons/grey/undo.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon2.addFile(u"tools/icons/purple/undo.svg", QSize(), QIcon.Normal, QIcon.On)
        self.pushButton_discard.setIcon(icon2)
        self.pushButton_discard.setCheckable(False)
        self.pushButton_discard.setAutoDefault(False)
        self.pushButton_discard.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_discard)

        self.pushButton_save = QPushButton(self.frame)
        self.pushButton_save.setObjectName(u"pushButton_save")
        icon3 = QIcon()
        icon3.addFile(u"tools/icons/purple/save.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_save.setIcon(icon3)
        self.pushButton_save.setCheckable(False)
        self.pushButton_save.setAutoDefault(False)
        self.pushButton_save.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_save)

        self.pushButton_close = QPushButton(self.frame)
        self.pushButton_close.setObjectName(u"pushButton_close")
        icon4 = QIcon()
        icon4.addFile(u"tools/icons/grey/x-square.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon4.addFile(u"tools/icons/purple/x-square.svg", QSize(), QIcon.Normal, QIcon.On)
        self.pushButton_close.setIcon(icon4)
        self.pushButton_close.setCheckable(False)
        self.pushButton_close.setAutoDefault(False)
        self.pushButton_close.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_close)


        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setSpacing(15)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.widget_rgb_graph = Widget_rgb_graph(self.frame)
        self.widget_rgb_graph.setObjectName(u"widget_rgb_graph")
        self.widget_rgb_graph.setMinimumSize(QSize(512, 512))
        self.widget_rgb_graph.setMaximumSize(QSize(1024, 1024))

        self.verticalLayout.addWidget(self.widget_rgb_graph)

        self.verticalSpacer = QSpacerItem(20, 9, QSizePolicy.Minimum, QSizePolicy.Fixed)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.radioButton_select_m_channel = QRadioButton(self.frame)
        self.radioButton_select_m_channel.setObjectName(u"radioButton_select_m_channel")
        self.radioButton_select_m_channel.setFocusPolicy(Qt.NoFocus)

        self.horizontalLayout_2.addWidget(self.radioButton_select_m_channel)

        self.horizontalSpacer1_4 = QSpacerItem(10, 20, QSizePolicy.Preferred, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer1_4)

        self.radioButton_select_r_channel = QRadioButton(self.frame)
        self.radioButton_select_r_channel.setObjectName(u"radioButton_select_r_channel")
        self.radioButton_select_r_channel.setFocusPolicy(Qt.NoFocus)

        self.horizontalLayout_2.addWidget(self.radioButton_select_r_channel)

        self.radioButton_select_g_channel = QRadioButton(self.frame)
        self.radioButton_select_g_channel.setObjectName(u"radioButton_select_g_channel")
        self.radioButton_select_g_channel.setFocusPolicy(Qt.NoFocus)

        self.horizontalLayout_2.addWidget(self.radioButton_select_g_channel)

        self.radioButton_select_b_channel = QRadioButton(self.frame)
        self.radioButton_select_b_channel.setObjectName(u"radioButton_select_b_channel")
        self.radioButton_select_b_channel.setFocusPolicy(Qt.NoFocus)

        self.horizontalLayout_2.addWidget(self.radioButton_select_b_channel)

        self.horizontalSpacer1_3 = QSpacerItem(20, 20, QSizePolicy.Preferred, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer1_3)

        self.lineEdit_coordinates = QLineEdit(self.frame)
        self.lineEdit_coordinates.setObjectName(u"lineEdit_coordinates")
        sizePolicy1 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.lineEdit_coordinates.sizePolicy().hasHeightForWidth())
        self.lineEdit_coordinates.setSizePolicy(sizePolicy1)
        self.lineEdit_coordinates.setMaximumSize(QSize(100, 16777215))
        self.lineEdit_coordinates.setFocusPolicy(Qt.NoFocus)
        self.lineEdit_coordinates.setFrame(False)
        self.lineEdit_coordinates.setAlignment(Qt.AlignCenter)
        self.lineEdit_coordinates.setReadOnly(True)

        self.horizontalLayout_2.addWidget(self.lineEdit_coordinates)

        self.horizontalSpacer_4 = QSpacerItem(10, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_4)

        self.label_out_4 = QLabel(self.frame)
        self.label_out_4.setObjectName(u"label_out_4")
        sizePolicy2 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.label_out_4.sizePolicy().hasHeightForWidth())
        self.label_out_4.setSizePolicy(sizePolicy2)
        self.label_out_4.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_2.addWidget(self.label_out_4)

        self.pushButton_reset_current_channel = QPushButton(self.frame)
        self.pushButton_reset_current_channel.setObjectName(u"pushButton_reset_current_channel")
        self.pushButton_reset_current_channel.setEnabled(True)
        sizePolicy3 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.pushButton_reset_current_channel.sizePolicy().hasHeightForWidth())
        self.pushButton_reset_current_channel.setSizePolicy(sizePolicy3)
        self.pushButton_reset_current_channel.setMaximumSize(QSize(70, 16777215))
        self.pushButton_reset_current_channel.setFocusPolicy(Qt.NoFocus)

        self.horizontalLayout_2.addWidget(self.pushButton_reset_current_channel)

        self.pushButton_reset_all_channels = QPushButton(self.frame)
        self.pushButton_reset_all_channels.setObjectName(u"pushButton_reset_all_channels")
        self.pushButton_reset_all_channels.setEnabled(True)
        sizePolicy3.setHeightForWidth(self.pushButton_reset_all_channels.sizePolicy().hasHeightForWidth())
        self.pushButton_reset_all_channels.setSizePolicy(sizePolicy3)
        self.pushButton_reset_all_channels.setMaximumSize(QSize(50, 16777215))
        self.pushButton_reset_all_channels.setFocusPolicy(Qt.NoFocus)

        self.horizontalLayout_2.addWidget(self.pushButton_reset_all_channels)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.layout_in_out = QGridLayout()
        self.layout_in_out.setObjectName(u"layout_in_out")
        self.layout_in_out.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.spacer_in_out = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.layout_in_out.addItem(self.spacer_in_out, 0, 4, 1, 1)

        self.lineEdit_rgb_values = QLineEdit(self.frame)
        self.lineEdit_rgb_values.setObjectName(u"lineEdit_rgb_values")
        sizePolicy4 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.lineEdit_rgb_values.sizePolicy().hasHeightForWidth())
        self.lineEdit_rgb_values.setSizePolicy(sizePolicy4)
        self.lineEdit_rgb_values.setFocusPolicy(Qt.NoFocus)
        self.lineEdit_rgb_values.setFrame(False)
        self.lineEdit_rgb_values.setAlignment(Qt.AlignCenter)
        self.lineEdit_rgb_values.setReadOnly(True)

        self.layout_in_out.addWidget(self.lineEdit_rgb_values, 0, 1, 1, 1)

        self.lineEdit_rgb_values_new = QLineEdit(self.frame)
        self.lineEdit_rgb_values_new.setObjectName(u"lineEdit_rgb_values_new")
        sizePolicy4.setHeightForWidth(self.lineEdit_rgb_values_new.sizePolicy().hasHeightForWidth())
        self.lineEdit_rgb_values_new.setSizePolicy(sizePolicy4)
        self.lineEdit_rgb_values_new.setFocusPolicy(Qt.NoFocus)
        self.lineEdit_rgb_values_new.setFrame(False)
        self.lineEdit_rgb_values_new.setAlignment(Qt.AlignCenter)
        self.lineEdit_rgb_values_new.setReadOnly(True)

        self.layout_in_out.addWidget(self.lineEdit_rgb_values_new, 0, 3, 1, 1)

        self.label_in = QLabel(self.frame)
        self.label_in.setObjectName(u"label_in")
        sizePolicy2.setHeightForWidth(self.label_in.sizePolicy().hasHeightForWidth())
        self.label_in.setSizePolicy(sizePolicy2)
        self.label_in.setAlignment(Qt.AlignCenter)

        self.layout_in_out.addWidget(self.label_in, 0, 0, 1, 1)

        self.label = QLabel(self.frame)
        self.label.setObjectName(u"label")

        self.layout_in_out.addWidget(self.label, 0, 2, 1, 1)


        self.verticalLayout.addLayout(self.layout_in_out)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.label_3 = QLabel(self.frame)
        self.label_3.setObjectName(u"label_3")

        self.horizontalLayout_4.addWidget(self.label_3)

        self.lineEdit_luma_initial = QLineEdit(self.frame)
        self.lineEdit_luma_initial.setObjectName(u"lineEdit_luma_initial")
        sizePolicy1.setHeightForWidth(self.lineEdit_luma_initial.sizePolicy().hasHeightForWidth())
        self.lineEdit_luma_initial.setSizePolicy(sizePolicy1)
        self.lineEdit_luma_initial.setMaximumSize(QSize(60, 16777215))
        self.lineEdit_luma_initial.setFocusPolicy(Qt.NoFocus)
        self.lineEdit_luma_initial.setFrame(False)
        self.lineEdit_luma_initial.setAlignment(Qt.AlignCenter)
        self.lineEdit_luma_initial.setReadOnly(True)

        self.horizontalLayout_4.addWidget(self.lineEdit_luma_initial)

        self.label_2 = QLabel(self.frame)
        self.label_2.setObjectName(u"label_2")

        self.horizontalLayout_4.addWidget(self.label_2)

        self.lineEdit_luma_modified = QLineEdit(self.frame)
        self.lineEdit_luma_modified.setObjectName(u"lineEdit_luma_modified")
        sizePolicy1.setHeightForWidth(self.lineEdit_luma_modified.sizePolicy().hasHeightForWidth())
        self.lineEdit_luma_modified.setSizePolicy(sizePolicy1)
        self.lineEdit_luma_modified.setMaximumSize(QSize(60, 16777215))
        self.lineEdit_luma_modified.setFocusPolicy(Qt.NoFocus)
        self.lineEdit_luma_modified.setFrame(False)
        self.lineEdit_luma_modified.setAlignment(Qt.AlignCenter)
        self.lineEdit_luma_modified.setReadOnly(True)

        self.horizontalLayout_4.addWidget(self.lineEdit_luma_modified)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_3)


        self.verticalLayout.addLayout(self.horizontalLayout_4)


        self.horizontalLayout_3.addLayout(self.verticalLayout)

        self.widget_curves_selection = Widget_curves_selection(self.frame)
        self.widget_curves_selection.setObjectName(u"widget_curves_selection")

        self.horizontalLayout_3.addWidget(self.widget_curves_selection)


        self.verticalLayout_2.addLayout(self.horizontalLayout_3)


        self.mainLayout.addWidget(self.frame)


        self.retranslateUi(widget_curves)

        QMetaObject.connectSlotsByName(widget_curves)
    # setupUi

    def retranslateUi(self, widget_curves):
        self.pushButton_set_preview.setText("")
        self.pushButton_split_line.setText("")
        self.label_message.setText(QCoreApplication.translate("widget_curves", u"disabled", None))
        self.pushButton_discard.setText("")
        self.pushButton_save.setText("")
        self.pushButton_close.setText("")
        self.radioButton_select_m_channel.setText(QCoreApplication.translate("widget_curves", u"M", None))
        self.radioButton_select_r_channel.setText(QCoreApplication.translate("widget_curves", u"R", None))
        self.radioButton_select_g_channel.setText(QCoreApplication.translate("widget_curves", u"G", None))
        self.radioButton_select_b_channel.setText(QCoreApplication.translate("widget_curves", u"B", None))
        self.lineEdit_coordinates.setText(QCoreApplication.translate("widget_curves", u"x:255  y:255", None))
        self.label_out_4.setText(QCoreApplication.translate("widget_curves", u"Reset", None))
        self.pushButton_reset_current_channel.setText(QCoreApplication.translate("widget_curves", u"channel", None))
        self.pushButton_reset_all_channels.setText(QCoreApplication.translate("widget_curves", u"all", None))
        self.lineEdit_rgb_values.setText(QCoreApplication.translate("widget_curves", u"(255, 255, 255)", None))
        self.lineEdit_rgb_values_new.setText(QCoreApplication.translate("widget_curves", u"(255, 255, 255)", None))
        self.label_in.setText(QCoreApplication.translate("widget_curves", u"(R, G, B):", None))
        self.label.setText(QCoreApplication.translate("widget_curves", u" --> ", None))
        self.label_3.setText(QCoreApplication.translate("widget_curves", u"Luma(mean, x100)", None))
        self.lineEdit_luma_initial.setText(QCoreApplication.translate("widget_curves", u"60.12", None))
        self.label_2.setText(QCoreApplication.translate("widget_curves", u" --> ", None))
        self.lineEdit_luma_modified.setText(QCoreApplication.translate("widget_curves", u"54.34", None))
        pass
    # retranslateUi

