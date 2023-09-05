# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_window_main.ui'
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QPushButton, QRadioButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

from widget_hist_curves import Widget_hist_curves
from widget_hist_graph import Widget_hist_graph
from widget_painter import Widget_painter

class Ui_window_main(object):
    def setupUi(self, window_main):
        if not window_main.objectName():
            window_main.setObjectName(u"window_main")
        window_main.resize(1311, 212)
        self.widget_window_main = QWidget(window_main)
        self.widget_window_main.setObjectName(u"widget_window_main")
        self.horizontalLayout = QHBoxLayout(self.widget_window_main)
        self.horizontalLayout.setSpacing(12)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(6, 6, 6, 6)
        self.widget_painter = Widget_painter(self.widget_window_main)
        self.widget_painter.setObjectName(u"widget_painter")
        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget_painter.sizePolicy().hasHeightForWidth())
        self.widget_painter.setSizePolicy(sizePolicy)
        self.widget_painter.setMinimumSize(QSize(800, 200))
        self.widget_painter.setStyleSheet(u"background-color: rgb(0, 0, 0);")

        self.horizontalLayout.addWidget(self.widget_painter)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setSpacing(10)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.widget_hist_graph = Widget_hist_graph(self.widget_window_main)
        self.widget_hist_graph.setObjectName(u"widget_hist_graph")
        self.widget_hist_graph.setEnabled(True)
        sizePolicy1 = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.widget_hist_graph.sizePolicy().hasHeightForWidth())
        self.widget_hist_graph.setSizePolicy(sizePolicy1)
        self.widget_hist_graph.setStyleSheet(u"background-color: rgb(220, 255, 255);")

        self.verticalLayout.addWidget(self.widget_hist_graph)

        self.widget_hist_curves = Widget_hist_curves(self.widget_window_main)
        self.widget_hist_curves.setObjectName(u"widget_hist_curves")
        self.widget_hist_curves.setEnabled(True)
        self.widget_hist_curves.setStyleSheet(u"background-color: rgb(220, 255, 255);")

        self.verticalLayout.addWidget(self.widget_hist_curves)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(10)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.radioButton_select_r_channel = QRadioButton(self.widget_window_main)
        self.radioButton_select_r_channel.setObjectName(u"radioButton_select_r_channel")

        self.horizontalLayout_2.addWidget(self.radioButton_select_r_channel)

        self.radioButton_select_g_channel = QRadioButton(self.widget_window_main)
        self.radioButton_select_g_channel.setObjectName(u"radioButton_select_g_channel")

        self.horizontalLayout_2.addWidget(self.radioButton_select_g_channel)

        self.radioButton_select_b_channel = QRadioButton(self.widget_window_main)
        self.radioButton_select_b_channel.setObjectName(u"radioButton_select_b_channel")

        self.horizontalLayout_2.addWidget(self.radioButton_select_b_channel)

        self.horizontalSpacer1_5 = QSpacerItem(20, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer1_5)

        self.lineEdit_coordinates = QLineEdit(self.widget_window_main)
        self.lineEdit_coordinates.setObjectName(u"lineEdit_coordinates")
        sizePolicy2 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.lineEdit_coordinates.sizePolicy().hasHeightForWidth())
        self.lineEdit_coordinates.setSizePolicy(sizePolicy2)
        self.lineEdit_coordinates.setMaximumSize(QSize(100, 16777215))
        self.lineEdit_coordinates.setAlignment(Qt.AlignCenter)
        self.lineEdit_coordinates.setReadOnly(True)

        self.horizontalLayout_2.addWidget(self.lineEdit_coordinates)

        self.horizontalSpacer_4 = QSpacerItem(20, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_4)

        self.label_out_4 = QLabel(self.widget_window_main)
        self.label_out_4.setObjectName(u"label_out_4")
        sizePolicy3 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.label_out_4.sizePolicy().hasHeightForWidth())
        self.label_out_4.setSizePolicy(sizePolicy3)
        self.label_out_4.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_2.addWidget(self.label_out_4)

        self.pushButton_reset_current_channel = QPushButton(self.widget_window_main)
        self.pushButton_reset_current_channel.setObjectName(u"pushButton_reset_current_channel")
        sizePolicy4 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.pushButton_reset_current_channel.sizePolicy().hasHeightForWidth())
        self.pushButton_reset_current_channel.setSizePolicy(sizePolicy4)
        self.pushButton_reset_current_channel.setMaximumSize(QSize(70, 16777215))

        self.horizontalLayout_2.addWidget(self.pushButton_reset_current_channel)

        self.pushButton_reset_all_channels = QPushButton(self.widget_window_main)
        self.pushButton_reset_all_channels.setObjectName(u"pushButton_reset_all_channels")
        sizePolicy4.setHeightForWidth(self.pushButton_reset_all_channels.sizePolicy().hasHeightForWidth())
        self.pushButton_reset_all_channels.setSizePolicy(sizePolicy4)
        self.pushButton_reset_all_channels.setMaximumSize(QSize(50, 16777215))

        self.horizontalLayout_2.addWidget(self.pushButton_reset_all_channels)


        self.verticalLayout.addLayout(self.horizontalLayout_2)


        self.horizontalLayout.addLayout(self.verticalLayout)

        window_main.setCentralWidget(self.widget_window_main)

        self.retranslateUi(window_main)

        QMetaObject.connectSlotsByName(window_main)
    # setupUi

    def retranslateUi(self, window_main):
        window_main.setWindowTitle(QCoreApplication.translate("window_main", u"Histogram editor", None))
        self.radioButton_select_r_channel.setText(QCoreApplication.translate("window_main", u"R", None))
        self.radioButton_select_g_channel.setText(QCoreApplication.translate("window_main", u"G", None))
        self.radioButton_select_b_channel.setText(QCoreApplication.translate("window_main", u"B", None))
        self.lineEdit_coordinates.setText(QCoreApplication.translate("window_main", u"x=255: +16", None))
        self.label_out_4.setText(QCoreApplication.translate("window_main", u"reset:", None))
        self.pushButton_reset_current_channel.setText(QCoreApplication.translate("window_main", u"channel", None))
        self.pushButton_reset_all_channels.setText(QCoreApplication.translate("window_main", u"all", None))
    # retranslateUi

