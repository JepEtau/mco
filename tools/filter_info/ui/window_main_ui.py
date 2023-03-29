# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_window_main.ui'
##
## Created by: Qt User Interface Compiler version 6.4.2
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
from PySide6.QtWidgets import (QAbstractItemView, QAbstractScrollArea, QApplication, QFrame,
    QHeaderView, QLabel, QLineEdit, QMainWindow,
    QSizePolicy, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(262, 227)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setSpacing(9)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(6, 6, 6, 6)
        self.lineEdit_filename = QLineEdit(self.centralwidget)
        self.lineEdit_filename.setObjectName(u"lineEdit_filename")
        sizePolicy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineEdit_filename.sizePolicy().hasHeightForWidth())
        self.lineEdit_filename.setSizePolicy(sizePolicy)
        self.lineEdit_filename.setMinimumSize(QSize(250, 0))
        self.lineEdit_filename.setDragEnabled(True)
        self.lineEdit_filename.setReadOnly(True)

        self.verticalLayout.addWidget(self.lineEdit_filename)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(9, 0, -1, -1)
        self.label_folder = QLabel(self.centralwidget)
        self.label_folder.setObjectName(u"label_folder")
        self.label_folder.setFrameShape(QFrame.NoFrame)

        self.verticalLayout_2.addWidget(self.label_folder)

        self.label_ed_ep_part = QLabel(self.centralwidget)
        self.label_ed_ep_part.setObjectName(u"label_ed_ep_part")
        self.label_ed_ep_part.setFrameShape(QFrame.NoFrame)

        self.verticalLayout_2.addWidget(self.label_ed_ep_part)

        self.label_shot_no = QLabel(self.centralwidget)
        self.label_shot_no.setObjectName(u"label_shot_no")

        self.verticalLayout_2.addWidget(self.label_shot_no)


        self.verticalLayout.addLayout(self.verticalLayout_2)

        self.tableWidget_filters = QTableWidget(self.centralwidget)
        if (self.tableWidget_filters.columnCount() < 2):
            self.tableWidget_filters.setColumnCount(2)
        __qtablewidgetitem = QTableWidgetItem()
        self.tableWidget_filters.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.tableWidget_filters.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        if (self.tableWidget_filters.rowCount() < 3):
            self.tableWidget_filters.setRowCount(3)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.tableWidget_filters.setVerticalHeaderItem(0, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.tableWidget_filters.setVerticalHeaderItem(1, __qtablewidgetitem3)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.tableWidget_filters.setVerticalHeaderItem(2, __qtablewidgetitem4)
        self.tableWidget_filters.setObjectName(u"tableWidget_filters")
        self.tableWidget_filters.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tableWidget_filters.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.tableWidget_filters.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableWidget_filters.setDragDropMode(QAbstractItemView.DropOnly)
        self.tableWidget_filters.setSelectionMode(QAbstractItemView.NoSelection)
        self.tableWidget_filters.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.verticalLayout.addWidget(self.tableWidget_filters)

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.label_folder.setText(QCoreApplication.translate("MainWindow", u"folder", None))
        self.label_ed_ep_part.setText(QCoreApplication.translate("MainWindow", u"edition:\u00e9pisode:part", None))
        self.label_shot_no.setText(QCoreApplication.translate("MainWindow", u"shot: shot_no", None))
        ___qtablewidgetitem = self.tableWidget_filters.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("MainWindow", u"filter", None));
        ___qtablewidgetitem1 = self.tableWidget_filters.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("MainWindow", u"hash", None));
        ___qtablewidgetitem2 = self.tableWidget_filters.verticalHeaderItem(0)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("MainWindow", u"0", None));
        ___qtablewidgetitem3 = self.tableWidget_filters.verticalHeaderItem(1)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("MainWindow", u"1", None));
        ___qtablewidgetitem4 = self.tableWidget_filters.verticalHeaderItem(2)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("MainWindow", u"3", None));
    # retranslateUi

