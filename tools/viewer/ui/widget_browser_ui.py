# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_widget_browser.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QAbstractScrollArea, QApplication, QCheckBox,
    QComboBox, QFrame, QHBoxLayout, QLayout,
    QListView, QListWidget, QListWidgetItem, QPushButton,
    QScrollArea, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class Ui_widget_browser(object):
    def setupUi(self, widget_browser):
        if not widget_browser.objectName():
            widget_browser.setObjectName(u"widget_browser")
        widget_browser.resize(320, 567)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(widget_browser.sizePolicy().hasHeightForWidth())
        widget_browser.setSizePolicy(sizePolicy)
        widget_browser.setWindowTitle(u"Image viewer")
        widget_browser.setStyleSheet(u"")
        self.verticalLayout = QVBoxLayout(widget_browser)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.layout_buttons = QHBoxLayout()
        self.layout_buttons.setSpacing(0)
        self.layout_buttons.setObjectName(u"layout_buttons")
        self.horizontalSpacer = QSpacerItem(5, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.layout_buttons.addItem(self.horizontalSpacer)

        self.pushButton_minimize = QPushButton(widget_browser)
        self.pushButton_minimize.setObjectName(u"pushButton_minimize")
        sizePolicy1 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.pushButton_minimize.sizePolicy().hasHeightForWidth())
        self.pushButton_minimize.setSizePolicy(sizePolicy1)
        icon = QIcon()
        icon.addFile(u"icons/purple/minus-square.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon.addFile(u"icons/purple/minus-square.svg", QSize(), QIcon.Normal, QIcon.On)
        self.pushButton_minimize.setIcon(icon)
        self.pushButton_minimize.setCheckable(False)
        self.pushButton_minimize.setAutoDefault(False)
        self.pushButton_minimize.setFlat(True)

        self.layout_buttons.addWidget(self.pushButton_minimize)

        self.pushButton_exit = QPushButton(widget_browser)
        self.pushButton_exit.setObjectName(u"pushButton_exit")
        sizePolicy1.setHeightForWidth(self.pushButton_exit.sizePolicy().hasHeightForWidth())
        self.pushButton_exit.setSizePolicy(sizePolicy1)
        icon1 = QIcon()
        icon1.addFile(u"icons/purple/x-square.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon1.addFile(u"icons/purple/x-square.svg", QSize(), QIcon.Normal, QIcon.On)
        self.pushButton_exit.setIcon(icon1)
        self.pushButton_exit.setCheckable(False)
        self.pushButton_exit.setAutoDefault(False)
        self.pushButton_exit.setFlat(True)

        self.layout_buttons.addWidget(self.pushButton_exit)


        self.verticalLayout.addLayout(self.layout_buttons)

        self.layout_tools = QVBoxLayout()
        self.layout_tools.setSpacing(6)
        self.layout_tools.setObjectName(u"layout_tools")
        self.layout_tools.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.layout_episode_part = QHBoxLayout()
        self.layout_episode_part.setObjectName(u"layout_episode_part")
        self.layout_episode_part.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.combobox_episode = QComboBox(widget_browser)
        self.combobox_episode.addItem("")
        self.combobox_episode.addItem("")
        self.combobox_episode.addItem("")
        self.combobox_episode.setObjectName(u"combobox_episode")
        sizePolicy2 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.combobox_episode.sizePolicy().hasHeightForWidth())
        self.combobox_episode.setSizePolicy(sizePolicy2)
        self.combobox_episode.setMinimumSize(QSize(60, 0))
        self.combobox_episode.setAcceptDrops(False)
        self.combobox_episode.setStyleSheet(u"")
        self.combobox_episode.setEditable(True)
        self.combobox_episode.setCurrentText(u"1")
        self.combobox_episode.setMaxVisibleItems(20)
        self.combobox_episode.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.combobox_episode.setFrame(True)

        self.layout_episode_part.addWidget(self.combobox_episode)

        self.combobox_part = QComboBox(widget_browser)
        self.combobox_part.addItem("")
        self.combobox_part.addItem("")
        self.combobox_part.addItem("")
        self.combobox_part.addItem("")
        self.combobox_part.addItem("")
        self.combobox_part.addItem("")
        self.combobox_part.addItem("")
        self.combobox_part.setObjectName(u"combobox_part")
        sizePolicy2.setHeightForWidth(self.combobox_part.sizePolicy().hasHeightForWidth())
        self.combobox_part.setSizePolicy(sizePolicy2)
        self.combobox_part.setMinimumSize(QSize(0, 0))
        self.combobox_part.setAcceptDrops(False)
        self.combobox_part.setEditable(False)
        self.combobox_part.setCurrentText(u"Episode")
        self.combobox_part.setMaxVisibleItems(10)
        self.combobox_part.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.combobox_part.setFrame(True)

        self.layout_episode_part.addWidget(self.combobox_part)

        self.horizontalSpacer_7 = QSpacerItem(5, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.layout_episode_part.addItem(self.horizontalSpacer_7)


        self.layout_tools.addLayout(self.layout_episode_part)

        self.layout_editions_all = QHBoxLayout()
        self.layout_editions_all.setSpacing(20)
        self.layout_editions_all.setObjectName(u"layout_editions_all")
        self.layout_editions_all.setSizeConstraint(QLayout.SetMaximumSize)
        self.layout_editions_all.setContentsMargins(0, -1, -1, 6)
        self.checkBox_editions_all_none = QCheckBox(widget_browser)
        self.checkBox_editions_all_none.setObjectName(u"checkBox_editions_all_none")
        sizePolicy2.setHeightForWidth(self.checkBox_editions_all_none.sizePolicy().hasHeightForWidth())
        self.checkBox_editions_all_none.setSizePolicy(sizePolicy2)
        self.checkBox_editions_all_none.setTristate(True)

        self.layout_editions_all.addWidget(self.checkBox_editions_all_none)

        self.widget_editions = QWidget(widget_browser)
        self.widget_editions.setObjectName(u"widget_editions")
        sizePolicy3 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.widget_editions.sizePolicy().hasHeightForWidth())
        self.widget_editions.setSizePolicy(sizePolicy3)
        self.layout_editions = QHBoxLayout(self.widget_editions)
        self.layout_editions.setObjectName(u"layout_editions")
        self.layout_editions.setContentsMargins(10, -1, -1, -1)
        self.checkBox_k = QCheckBox(self.widget_editions)
        self.checkBox_k.setObjectName(u"checkBox_k")

        self.layout_editions.addWidget(self.checkBox_k)

        self.checkBox_s = QCheckBox(self.widget_editions)
        self.checkBox_s.setObjectName(u"checkBox_s")

        self.layout_editions.addWidget(self.checkBox_s)

        self.checkBox_a = QCheckBox(self.widget_editions)
        self.checkBox_a.setObjectName(u"checkBox_a")

        self.layout_editions.addWidget(self.checkBox_a)

        self.checkBox_s0 = QCheckBox(self.widget_editions)
        self.checkBox_s0.setObjectName(u"checkBox_s0")

        self.layout_editions.addWidget(self.checkBox_s0)


        self.layout_editions_all.addWidget(self.widget_editions)

        self.horizontalSpacer_3 = QSpacerItem(0, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.layout_editions_all.addItem(self.horizontalSpacer_3)


        self.layout_tools.addLayout(self.layout_editions_all)

        self.layout_steps_filters = QHBoxLayout()
        self.layout_steps_filters.setSpacing(20)
        self.layout_steps_filters.setObjectName(u"layout_steps_filters")
        self.layout_steps_filters.setSizeConstraint(QLayout.SetMinimumSize)
        self.editions_all = QFrame(widget_browser)
        self.editions_all.setObjectName(u"editions_all")
        self.editions_all.setFrameShape(QFrame.StyledPanel)
        self.editions_all.setFrameShadow(QFrame.Raised)
        self.verticalLayout_3 = QVBoxLayout(self.editions_all)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, -1, -1)
        self.layout_steps_all = QVBoxLayout()
        self.layout_steps_all.setSpacing(2)
        self.layout_steps_all.setObjectName(u"layout_steps_all")
        self.checkBox_steps_all_none = QCheckBox(self.editions_all)
        self.checkBox_steps_all_none.setObjectName(u"checkBox_steps_all_none")
        self.checkBox_steps_all_none.setChecked(True)
        self.checkBox_steps_all_none.setTristate(True)

        self.layout_steps_all.addWidget(self.checkBox_steps_all_none)

        self.layout_steps = QVBoxLayout()
        self.layout_steps.setObjectName(u"layout_steps")
        self.layout_steps.setContentsMargins(12, -1, -1, -1)

        self.layout_steps_all.addLayout(self.layout_steps)


        self.verticalLayout_3.addLayout(self.layout_steps_all)

        self.verticalSpacer_2 = QSpacerItem(20, 5, QSizePolicy.Minimum, QSizePolicy.Preferred)

        self.verticalLayout_3.addItem(self.verticalSpacer_2)


        self.layout_steps_filters.addWidget(self.editions_all)

        self.widget_filters_all = QWidget(widget_browser)
        self.widget_filters_all.setObjectName(u"widget_filters_all")
        self.layout_filters_id_all = QVBoxLayout(self.widget_filters_all)
        self.layout_filters_id_all.setSpacing(0)
        self.layout_filters_id_all.setObjectName(u"layout_filters_id_all")
        self.layout_filters_id_all.setSizeConstraint(QLayout.SetMinimumSize)
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.checkBox_filter_ids_all_none = QCheckBox(self.widget_filters_all)
        self.checkBox_filter_ids_all_none.setObjectName(u"checkBox_filter_ids_all_none")
        sizePolicy2.setHeightForWidth(self.checkBox_filter_ids_all_none.sizePolicy().hasHeightForWidth())
        self.checkBox_filter_ids_all_none.setSizePolicy(sizePolicy2)
        self.checkBox_filter_ids_all_none.setTristate(True)

        self.horizontalLayout_2.addWidget(self.checkBox_filter_ids_all_none)

        self.horizontalSpacer_5 = QSpacerItem(5, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_5)


        self.layout_filters_id_all.addLayout(self.horizontalLayout_2)

        self.scrollArea_filter_ids = QScrollArea(self.widget_filters_all)
        self.scrollArea_filter_ids.setObjectName(u"scrollArea_filter_ids")
        sizePolicy4 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.scrollArea_filter_ids.sizePolicy().hasHeightForWidth())
        self.scrollArea_filter_ids.setSizePolicy(sizePolicy4)
        self.scrollArea_filter_ids.setMinimumSize(QSize(100, 0))
        self.scrollArea_filter_ids.setMaximumSize(QSize(16777215, 150))
        self.scrollArea_filter_ids.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.scrollArea_filter_ids.setWidgetResizable(True)
        self.widget_filter_ids = QWidget()
        self.widget_filter_ids.setObjectName(u"widget_filter_ids")
        self.widget_filter_ids.setGeometry(QRect(0, 0, 84, 176))
        sizePolicy5 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.widget_filter_ids.sizePolicy().hasHeightForWidth())
        self.widget_filter_ids.setSizePolicy(sizePolicy5)
        self.layout_filtersNo = QVBoxLayout(self.widget_filter_ids)
        self.layout_filtersNo.setSpacing(0)
        self.layout_filtersNo.setObjectName(u"layout_filtersNo")
        self.layout_filtersNo.setContentsMargins(12, 0, -1, 0)
        self.checkBox = QCheckBox(self.widget_filter_ids)
        self.checkBox.setObjectName(u"checkBox")

        self.layout_filtersNo.addWidget(self.checkBox)

        self.checkBox_2 = QCheckBox(self.widget_filter_ids)
        self.checkBox_2.setObjectName(u"checkBox_2")

        self.layout_filtersNo.addWidget(self.checkBox_2)

        self.checkBox_4 = QCheckBox(self.widget_filter_ids)
        self.checkBox_4.setObjectName(u"checkBox_4")

        self.layout_filtersNo.addWidget(self.checkBox_4)

        self.checkBox_12 = QCheckBox(self.widget_filter_ids)
        self.checkBox_12.setObjectName(u"checkBox_12")

        self.layout_filtersNo.addWidget(self.checkBox_12)

        self.checkBox_8 = QCheckBox(self.widget_filter_ids)
        self.checkBox_8.setObjectName(u"checkBox_8")

        self.layout_filtersNo.addWidget(self.checkBox_8)

        self.checkBox_11 = QCheckBox(self.widget_filter_ids)
        self.checkBox_11.setObjectName(u"checkBox_11")

        self.layout_filtersNo.addWidget(self.checkBox_11)

        self.checkBox_10 = QCheckBox(self.widget_filter_ids)
        self.checkBox_10.setObjectName(u"checkBox_10")

        self.layout_filtersNo.addWidget(self.checkBox_10)

        self.checkBox_9 = QCheckBox(self.widget_filter_ids)
        self.checkBox_9.setObjectName(u"checkBox_9")

        self.layout_filtersNo.addWidget(self.checkBox_9)

        self.scrollArea_filter_ids.setWidget(self.widget_filter_ids)

        self.layout_filters_id_all.addWidget(self.scrollArea_filter_ids)

        self.verticalSpacer = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.MinimumExpanding)

        self.layout_filters_id_all.addItem(self.verticalSpacer)


        self.layout_steps_filters.addWidget(self.widget_filters_all)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.layout_steps_filters.addItem(self.horizontalSpacer_2)


        self.layout_tools.addLayout(self.layout_steps_filters)

        self.list_images = QListWidget(widget_browser)
        self.list_images.setObjectName(u"list_images")
        sizePolicy6 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy6.setHorizontalStretch(0)
        sizePolicy6.setVerticalStretch(0)
        sizePolicy6.setHeightForWidth(self.list_images.sizePolicy().hasHeightForWidth())
        self.list_images.setSizePolicy(sizePolicy6)
        self.list_images.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.list_images.setProperty("showDropIndicator", False)
        self.list_images.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list_images.setViewMode(QListView.ListMode)

        self.layout_tools.addWidget(self.list_images)

        self.checkBox_fit_image_to_window = QCheckBox(widget_browser)
        self.checkBox_fit_image_to_window.setObjectName(u"checkBox_fit_image_to_window")
        sizePolicy2.setHeightForWidth(self.checkBox_fit_image_to_window.sizePolicy().hasHeightForWidth())
        self.checkBox_fit_image_to_window.setSizePolicy(sizePolicy2)

        self.layout_tools.addWidget(self.checkBox_fit_image_to_window)


        self.verticalLayout.addLayout(self.layout_tools)


        self.retranslateUi(widget_browser)

        self.combobox_part.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(widget_browser)
    # setupUi

    def retranslateUi(self, widget_browser):
        self.pushButton_minimize.setText("")
        self.pushButton_exit.setText("")
        self.combobox_episode.setItemText(0, QCoreApplication.translate("widget_browser", u"1", None))
        self.combobox_episode.setItemText(1, QCoreApplication.translate("widget_browser", u"2", None))
        self.combobox_episode.setItemText(2, QCoreApplication.translate("widget_browser", u"39", None))

        self.combobox_part.setItemText(0, QCoreApplication.translate("widget_browser", u"Pr\u00e9c\u00e9demment", None))
        self.combobox_part.setItemText(1, QCoreApplication.translate("widget_browser", u"Episode", None))
        self.combobox_part.setItemText(2, QCoreApplication.translate("widget_browser", u"A suivre", None))
        self.combobox_part.setItemText(3, QCoreApplication.translate("widget_browser", u"Reportage", None))
        self.combobox_part.setItemText(4, QCoreApplication.translate("widget_browser", u"G\u00e9n\u00e9rique d\u00e9but", None))
        self.combobox_part.setItemText(5, QCoreApplication.translate("widget_browser", u"G\u00e9n\u00e9rique fin", None))
        self.combobox_part.setItemText(6, QCoreApplication.translate("widget_browser", u"G\u00e9n\u00e9rique \u00e0 suivre", None))

        self.checkBox_editions_all_none.setText(QCoreApplication.translate("widget_browser", u"all/none", None))
        self.checkBox_k.setText(QCoreApplication.translate("widget_browser", u"K", None))
        self.checkBox_s.setText(QCoreApplication.translate("widget_browser", u"S", None))
        self.checkBox_a.setText(QCoreApplication.translate("widget_browser", u"A", None))
        self.checkBox_s0.setText(QCoreApplication.translate("widget_browser", u"S0", None))
        self.checkBox_steps_all_none.setText(QCoreApplication.translate("widget_browser", u"all/none", None))
        self.checkBox_filter_ids_all_none.setText(QCoreApplication.translate("widget_browser", u"all/none", None))
        self.checkBox.setText(QCoreApplication.translate("widget_browser", u"000", None))
        self.checkBox_2.setText(QCoreApplication.translate("widget_browser", u"001", None))
        self.checkBox_4.setText(QCoreApplication.translate("widget_browser", u"002", None))
        self.checkBox_12.setText(QCoreApplication.translate("widget_browser", u"003", None))
        self.checkBox_8.setText(QCoreApplication.translate("widget_browser", u"004", None))
        self.checkBox_11.setText(QCoreApplication.translate("widget_browser", u"005", None))
        self.checkBox_10.setText(QCoreApplication.translate("widget_browser", u"006", None))
        self.checkBox_9.setText(QCoreApplication.translate("widget_browser", u"007", None))
        self.checkBox_fit_image_to_window.setText(QCoreApplication.translate("widget_browser", u"Fit image to window", None))
        pass
    # retranslateUi

