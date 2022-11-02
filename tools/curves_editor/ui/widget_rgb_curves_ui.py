# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_widget_rgb_curves.ui'
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
from PySide6.QtWidgets import (QApplication, QGridLayout, QHBoxLayout, QLabel,
    QLayout, QLineEdit, QPushButton, QRadioButton,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

class Ui_widget_rgb_curves(object):
    def setupUi(self, widget_rgb_curves):
        if not widget_rgb_curves.objectName():
            widget_rgb_curves.setObjectName(u"widget_rgb_curves")
        widget_rgb_curves.resize(501, 262)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(widget_rgb_curves.sizePolicy().hasHeightForWidth())
        widget_rgb_curves.setSizePolicy(sizePolicy)
        self.mainLayout = QVBoxLayout(widget_rgb_curves)
        self.mainLayout.setObjectName(u"mainLayout")
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.widget_rgb_graph_tmp = QWidget(widget_rgb_curves)
        self.widget_rgb_graph_tmp.setObjectName(u"widget_rgb_graph_tmp")
        self.widget_rgb_graph_tmp.setEnabled(True)
        sizePolicy1 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.widget_rgb_graph_tmp.sizePolicy().hasHeightForWidth())
        self.widget_rgb_graph_tmp.setSizePolicy(sizePolicy1)
        self.widget_rgb_graph_tmp.setMinimumSize(QSize(200, 200))
        self.widget_rgb_graph_tmp.setStyleSheet(u"background-color: rgb(220, 255, 255);")

        self.mainLayout.addWidget(self.widget_rgb_graph_tmp)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.radioButton_select_m_channel = QRadioButton(widget_rgb_curves)
        self.radioButton_select_m_channel.setObjectName(u"radioButton_select_m_channel")

        self.horizontalLayout_2.addWidget(self.radioButton_select_m_channel)

        self.horizontalSpacer1_4 = QSpacerItem(10, 20, QSizePolicy.Preferred, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer1_4)

        self.radioButton_select_r_channel = QRadioButton(widget_rgb_curves)
        self.radioButton_select_r_channel.setObjectName(u"radioButton_select_r_channel")

        self.horizontalLayout_2.addWidget(self.radioButton_select_r_channel)

        self.radioButton_select_g_channel = QRadioButton(widget_rgb_curves)
        self.radioButton_select_g_channel.setObjectName(u"radioButton_select_g_channel")

        self.horizontalLayout_2.addWidget(self.radioButton_select_g_channel)

        self.radioButton_select_b_channel = QRadioButton(widget_rgb_curves)
        self.radioButton_select_b_channel.setObjectName(u"radioButton_select_b_channel")

        self.horizontalLayout_2.addWidget(self.radioButton_select_b_channel)

        self.horizontalSpacer1_3 = QSpacerItem(20, 20, QSizePolicy.Preferred, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer1_3)

        self.lineEdit_coordinates = QLineEdit(widget_rgb_curves)
        self.lineEdit_coordinates.setObjectName(u"lineEdit_coordinates")
        sizePolicy2 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.lineEdit_coordinates.sizePolicy().hasHeightForWidth())
        self.lineEdit_coordinates.setSizePolicy(sizePolicy2)
        self.lineEdit_coordinates.setMaximumSize(QSize(100, 16777215))
        self.lineEdit_coordinates.setFrame(False)
        self.lineEdit_coordinates.setAlignment(Qt.AlignCenter)
        self.lineEdit_coordinates.setReadOnly(True)

        self.horizontalLayout_2.addWidget(self.lineEdit_coordinates)

        self.horizontalSpacer_4 = QSpacerItem(10, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_4)

        self.label_out_4 = QLabel(widget_rgb_curves)
        self.label_out_4.setObjectName(u"label_out_4")
        sizePolicy3 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.label_out_4.sizePolicy().hasHeightForWidth())
        self.label_out_4.setSizePolicy(sizePolicy3)
        self.label_out_4.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_2.addWidget(self.label_out_4)

        self.pushButton_reset_current_channel = QPushButton(widget_rgb_curves)
        self.pushButton_reset_current_channel.setObjectName(u"pushButton_reset_current_channel")
        sizePolicy4 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.pushButton_reset_current_channel.sizePolicy().hasHeightForWidth())
        self.pushButton_reset_current_channel.setSizePolicy(sizePolicy4)
        self.pushButton_reset_current_channel.setMaximumSize(QSize(70, 16777215))

        self.horizontalLayout_2.addWidget(self.pushButton_reset_current_channel)

        self.pushButton_reset_all_channels = QPushButton(widget_rgb_curves)
        self.pushButton_reset_all_channels.setObjectName(u"pushButton_reset_all_channels")
        sizePolicy4.setHeightForWidth(self.pushButton_reset_all_channels.sizePolicy().hasHeightForWidth())
        self.pushButton_reset_all_channels.setSizePolicy(sizePolicy4)
        self.pushButton_reset_all_channels.setMaximumSize(QSize(50, 16777215))

        self.horizontalLayout_2.addWidget(self.pushButton_reset_all_channels)


        self.mainLayout.addLayout(self.horizontalLayout_2)

        self.layout_in_out = QGridLayout()
        self.layout_in_out.setObjectName(u"layout_in_out")
        self.layout_in_out.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.spacer_in_out = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.layout_in_out.addItem(self.spacer_in_out, 0, 2, 1, 1)

        self.lineEdit_rgb = QLineEdit(widget_rgb_curves)
        self.lineEdit_rgb.setObjectName(u"lineEdit_rgb")
        sizePolicy.setHeightForWidth(self.lineEdit_rgb.sizePolicy().hasHeightForWidth())
        self.lineEdit_rgb.setSizePolicy(sizePolicy)
        self.lineEdit_rgb.setFrame(False)
        self.lineEdit_rgb.setAlignment(Qt.AlignCenter)
        self.lineEdit_rgb.setReadOnly(True)

        self.layout_in_out.addWidget(self.lineEdit_rgb, 0, 1, 1, 1)

        self.label_in = QLabel(widget_rgb_curves)
        self.label_in.setObjectName(u"label_in")
        sizePolicy3.setHeightForWidth(self.label_in.sizePolicy().hasHeightForWidth())
        self.label_in.setSizePolicy(sizePolicy3)
        self.label_in.setAlignment(Qt.AlignCenter)

        self.layout_in_out.addWidget(self.label_in, 0, 0, 1, 1)


        self.mainLayout.addLayout(self.layout_in_out)


        self.retranslateUi(widget_rgb_curves)

        QMetaObject.connectSlotsByName(widget_rgb_curves)
    # setupUi

    def retranslateUi(self, widget_rgb_curves):
        widget_rgb_curves.setWindowTitle(QCoreApplication.translate("widget_rgb_curves", u"Form", None))
        self.radioButton_select_m_channel.setText(QCoreApplication.translate("widget_rgb_curves", u"M", None))
        self.radioButton_select_r_channel.setText(QCoreApplication.translate("widget_rgb_curves", u"R", None))
        self.radioButton_select_g_channel.setText(QCoreApplication.translate("widget_rgb_curves", u"G", None))
        self.radioButton_select_b_channel.setText(QCoreApplication.translate("widget_rgb_curves", u"B", None))
        self.lineEdit_coordinates.setText(QCoreApplication.translate("widget_rgb_curves", u"x:255  y:255", None))
        self.label_out_4.setText(QCoreApplication.translate("widget_rgb_curves", u"Reset", None))
        self.pushButton_reset_current_channel.setText(QCoreApplication.translate("widget_rgb_curves", u"channel", None))
        self.pushButton_reset_all_channels.setText(QCoreApplication.translate("widget_rgb_curves", u"all", None))
        self.lineEdit_rgb.setText(QCoreApplication.translate("widget_rgb_curves", u"(255, 255, 255)", None))
        self.label_in.setText(QCoreApplication.translate("widget_rgb_curves", u"(R, G, B):", None))
    # retranslateUi

