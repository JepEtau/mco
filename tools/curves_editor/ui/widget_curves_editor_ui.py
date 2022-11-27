# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_widget_curves_editor.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QComboBox,
    QFrame, QGroupBox, QHBoxLayout, QLabel,
    QLayout, QListView, QListWidget, QListWidgetItem,
    QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

from common.widget_app_controls import Widget_app_controls

class Ui_widget_curves_editor(object):
    def setupUi(self, widget_curves_editor):
        if not widget_curves_editor.objectName():
            widget_curves_editor.setObjectName(u"widget_curves_editor")
        widget_curves_editor.resize(640, 1124)
        widget_curves_editor.setWindowTitle(u"Curves editor")
        self.main_layout = QVBoxLayout(widget_curves_editor)
        self.main_layout.setObjectName(u"main_layout")
        self.widget_app_controls = Widget_app_controls(widget_curves_editor)
        self.widget_app_controls.setObjectName(u"widget_app_controls")

        self.main_layout.addWidget(self.widget_app_controls)

        self.layout_curves_editor = QHBoxLayout()
        self.layout_curves_editor.setSpacing(6)
        self.layout_curves_editor.setObjectName(u"layout_curves_editor")
        self.layout_curves_editor.setContentsMargins(0, 0, 0, -1)
        self.layout_rgb_curves = QVBoxLayout()
        self.layout_rgb_curves.setSpacing(12)
        self.layout_rgb_curves.setObjectName(u"layout_rgb_curves")
        self.layout_rgb_curves.setSizeConstraint(QLayout.SetNoConstraint)
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.curves_browser_layout = QVBoxLayout()
        self.curves_browser_layout.setSpacing(3)
        self.curves_browser_layout.setObjectName(u"curves_browser_layout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.combobox_episode = QComboBox(widget_curves_editor)
        self.combobox_episode.addItem("")
        self.combobox_episode.addItem("")
        self.combobox_episode.addItem("")
        self.combobox_episode.setObjectName(u"combobox_episode")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.combobox_episode.sizePolicy().hasHeightForWidth())
        self.combobox_episode.setSizePolicy(sizePolicy)
        self.combobox_episode.setMinimumSize(QSize(50, 0))
        self.combobox_episode.setAcceptDrops(False)
        self.combobox_episode.setEditable(False)
        self.combobox_episode.setCurrentText(u"1")
        self.combobox_episode.setMaxVisibleItems(20)
        self.combobox_episode.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.combobox_episode.setFrame(True)

        self.horizontalLayout.addWidget(self.combobox_episode)

        self.combobox_part = QComboBox(widget_curves_editor)
        self.combobox_part.addItem("")
        self.combobox_part.addItem("")
        self.combobox_part.addItem("")
        self.combobox_part.addItem("")
        self.combobox_part.addItem("")
        self.combobox_part.addItem("")
        self.combobox_part.addItem("")
        self.combobox_part.setObjectName(u"combobox_part")
        sizePolicy.setHeightForWidth(self.combobox_part.sizePolicy().hasHeightForWidth())
        self.combobox_part.setSizePolicy(sizePolicy)
        self.combobox_part.setMinimumSize(QSize(140, 0))
        self.combobox_part.setAcceptDrops(False)
        self.combobox_part.setEditable(False)
        self.combobox_part.setCurrentText(u"precedemment")
        self.combobox_part.setMaxVisibleItems(10)
        self.combobox_part.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.combobox_part.setFrame(True)

        self.horizontalLayout.addWidget(self.combobox_part)

        self.combobox_edition = QComboBox(widget_curves_editor)
        self.combobox_edition.addItem("")
        self.combobox_edition.addItem("")
        self.combobox_edition.addItem("")
        self.combobox_edition.setObjectName(u"combobox_edition")
        sizePolicy.setHeightForWidth(self.combobox_edition.sizePolicy().hasHeightForWidth())
        self.combobox_edition.setSizePolicy(sizePolicy)
        self.combobox_edition.setMinimumSize(QSize(40, 0))
        self.combobox_edition.setAcceptDrops(False)
        self.combobox_edition.setEditable(False)
        self.combobox_edition.setCurrentText(u"s")
        self.combobox_edition.setMaxVisibleItems(10)
        self.combobox_edition.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.combobox_edition.setFrame(True)

        self.horizontalLayout.addWidget(self.combobox_edition)

        self.horizontalSpacer_2 = QSpacerItem(5, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)


        self.curves_browser_layout.addLayout(self.horizontalLayout)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(-1, 0, -1, -1)
        self.comboBox_step = QComboBox(widget_curves_editor)
        self.comboBox_step.addItem("")
        self.comboBox_step.setObjectName(u"comboBox_step")
        sizePolicy1 = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.comboBox_step.sizePolicy().hasHeightForWidth())
        self.comboBox_step.setSizePolicy(sizePolicy1)
        self.comboBox_step.setMinimumSize(QSize(120, 0))

        self.horizontalLayout_6.addWidget(self.comboBox_step)

        self.comboBox_filter_id = QComboBox(widget_curves_editor)
        self.comboBox_filter_id.setObjectName(u"comboBox_filter_id")

        self.horizontalLayout_6.addWidget(self.comboBox_filter_id)

        self.horizontalSpacer = QSpacerItem(10, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer)


        self.curves_browser_layout.addLayout(self.horizontalLayout_6)

        self.list_images = QListWidget(widget_curves_editor)
        self.list_images.setObjectName(u"list_images")
        sizePolicy2 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.list_images.sizePolicy().hasHeightForWidth())
        self.list_images.setSizePolicy(sizePolicy2)
        self.list_images.setMinimumSize(QSize(0, 500))
        self.list_images.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.list_images.setProperty("showDropIndicator", False)
        self.list_images.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list_images.setViewMode(QListView.ListMode)

        self.curves_browser_layout.addWidget(self.list_images)


        self.horizontalLayout_2.addLayout(self.curves_browser_layout)

        self.curves_browser_shots_layout = QVBoxLayout()
        self.curves_browser_shots_layout.setSpacing(3)
        self.curves_browser_shots_layout.setObjectName(u"curves_browser_shots_layout")
        self.label_edition_5 = QLabel(widget_curves_editor)
        self.label_edition_5.setObjectName(u"label_edition_5")

        self.curves_browser_shots_layout.addWidget(self.label_edition_5)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setSpacing(3)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(-1, -1, -1, 0)
        self.pushButton_reset_filter_by_shot = QPushButton(widget_curves_editor)
        self.pushButton_reset_filter_by_shot.setObjectName(u"pushButton_reset_filter_by_shot")
        sizePolicy3 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.pushButton_reset_filter_by_shot.sizePolicy().hasHeightForWidth())
        self.pushButton_reset_filter_by_shot.setSizePolicy(sizePolicy3)
        self.pushButton_reset_filter_by_shot.setMaximumSize(QSize(45, 16777215))
        self.pushButton_reset_filter_by_shot.setCheckable(True)

        self.horizontalLayout_4.addWidget(self.pushButton_reset_filter_by_shot)

        self.pushButton_filter_by_shot_todo = QPushButton(widget_curves_editor)
        self.pushButton_filter_by_shot_todo.setObjectName(u"pushButton_filter_by_shot_todo")
        sizePolicy3.setHeightForWidth(self.pushButton_filter_by_shot_todo.sizePolicy().hasHeightForWidth())
        self.pushButton_filter_by_shot_todo.setSizePolicy(sizePolicy3)
        self.pushButton_filter_by_shot_todo.setMaximumSize(QSize(45, 16777215))

        self.horizontalLayout_4.addWidget(self.pushButton_filter_by_shot_todo)


        self.curves_browser_shots_layout.addLayout(self.horizontalLayout_4)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setSpacing(3)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(-1, -1, -1, 0)
        self.list_shots = QListWidget(widget_curves_editor)
        QListWidgetItem(self.list_shots)
        self.list_shots.setObjectName(u"list_shots")
        sizePolicy4 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Expanding)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.list_shots.sizePolicy().hasHeightForWidth())
        self.list_shots.setSizePolicy(sizePolicy4)
        self.list_shots.setMaximumSize(QSize(60, 16777215))
        self.list_shots.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.list_shots.setProperty("showDropIndicator", False)
        self.list_shots.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list_shots.setViewMode(QListView.ListMode)

        self.horizontalLayout_3.addWidget(self.list_shots)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(-1, -1, -1, 0)
        self.pushButton_reset_to_initial_curves = QPushButton(widget_curves_editor)
        self.pushButton_reset_to_initial_curves.setObjectName(u"pushButton_reset_to_initial_curves")
        sizePolicy5 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.pushButton_reset_to_initial_curves.sizePolicy().hasHeightForWidth())
        self.pushButton_reset_to_initial_curves.setSizePolicy(sizePolicy5)
        icon = QIcon()
        icon.addFile(u"icons/purple/undo.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_reset_to_initial_curves.setIcon(icon)
        self.pushButton_reset_to_initial_curves.setFlat(True)

        self.verticalLayout.addWidget(self.pushButton_reset_to_initial_curves)

        self.pushButton_remove_shot_curve = QPushButton(widget_curves_editor)
        self.pushButton_remove_shot_curve.setObjectName(u"pushButton_remove_shot_curve")
        sizePolicy5.setHeightForWidth(self.pushButton_remove_shot_curve.sizePolicy().hasHeightForWidth())
        self.pushButton_remove_shot_curve.setSizePolicy(sizePolicy5)
        icon1 = QIcon()
        icon1.addFile(u"icons/purple/x-square.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_remove_shot_curve.setIcon(icon1)
        self.pushButton_remove_shot_curve.setFlat(True)

        self.verticalLayout.addWidget(self.pushButton_remove_shot_curve)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_2)

        self.pushButton_save_database = QPushButton(widget_curves_editor)
        self.pushButton_save_database.setObjectName(u"pushButton_save_database")
        sizePolicy5.setHeightForWidth(self.pushButton_save_database.sizePolicy().hasHeightForWidth())
        self.pushButton_save_database.setSizePolicy(sizePolicy5)
        icon2 = QIcon()
        icon2.addFile(u"icons/purple/save.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_save_database.setIcon(icon2)
        self.pushButton_save_database.setFlat(True)

        self.verticalLayout.addWidget(self.pushButton_save_database)


        self.horizontalLayout_3.addLayout(self.verticalLayout)


        self.curves_browser_shots_layout.addLayout(self.horizontalLayout_3)


        self.horizontalLayout_2.addLayout(self.curves_browser_shots_layout)

        self.frame = QFrame(widget_curves_editor)
        self.frame.setObjectName(u"frame")
        sizePolicy6 = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        sizePolicy6.setHorizontalStretch(0)
        sizePolicy6.setVerticalStretch(0)
        sizePolicy6.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
        self.frame.setSizePolicy(sizePolicy6)
        self.frame.setMinimumSize(QSize(120, 0))
        self.verticalLayout_7 = QVBoxLayout(self.frame)
        self.verticalLayout_7.setSpacing(0)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.verticalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.groupBox = QGroupBox(self.frame)
        self.groupBox.setObjectName(u"groupBox")
        self.verticalLayout_9 = QVBoxLayout(self.groupBox)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.label_frame_no = QLabel(self.groupBox)
        self.label_frame_no.setObjectName(u"label_frame_no")

        self.verticalLayout_9.addWidget(self.label_frame_no)

        self.label_shot_no = QLabel(self.groupBox)
        self.label_shot_no.setObjectName(u"label_shot_no")

        self.verticalLayout_9.addWidget(self.label_shot_no)

        self.label_step = QLabel(self.groupBox)
        self.label_step.setObjectName(u"label_step")

        self.verticalLayout_9.addWidget(self.label_step)

        self.label_filter_id = QLabel(self.groupBox)
        self.label_filter_id.setObjectName(u"label_filter_id")

        self.verticalLayout_9.addWidget(self.label_filter_id)

        self.label_dimension = QLabel(self.groupBox)
        self.label_dimension.setObjectName(u"label_dimension")

        self.verticalLayout_9.addWidget(self.label_dimension)

        self.label_curve = QLabel(self.groupBox)
        self.label_curve.setObjectName(u"label_curve")
        sizePolicy7 = QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        sizePolicy7.setHorizontalStretch(0)
        sizePolicy7.setVerticalStretch(0)
        sizePolicy7.setHeightForWidth(self.label_curve.sizePolicy().hasHeightForWidth())
        self.label_curve.setSizePolicy(sizePolicy7)
        font = QFont()
        font.setStrikeOut(False)
        self.label_curve.setFont(font)
        self.label_curve.setText(u"curve_which_name_is_very_long")
        self.label_curve.setScaledContents(False)
        self.label_curve.setWordWrap(False)

        self.verticalLayout_9.addWidget(self.label_curve)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_9.addItem(self.verticalSpacer_3)


        self.verticalLayout_7.addWidget(self.groupBox)

        self.checkBox_fit_image_to_window = QCheckBox(self.frame)
        self.checkBox_fit_image_to_window.setObjectName(u"checkBox_fit_image_to_window")

        self.verticalLayout_7.addWidget(self.checkBox_fit_image_to_window)

        self.pushButton_change_preview_options = QPushButton(self.frame)
        self.pushButton_change_preview_options.setObjectName(u"pushButton_change_preview_options")
        self.pushButton_change_preview_options.setCheckable(False)
        self.pushButton_change_preview_options.setAutoDefault(False)
        self.pushButton_change_preview_options.setFlat(True)

        self.verticalLayout_7.addWidget(self.pushButton_change_preview_options)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_7.addItem(self.verticalSpacer)


        self.horizontalLayout_2.addWidget(self.frame)


        self.layout_rgb_curves.addLayout(self.horizontalLayout_2)

        self.widget_rgb_curves_tmp = QWidget(widget_curves_editor)
        self.widget_rgb_curves_tmp.setObjectName(u"widget_rgb_curves_tmp")
        sizePolicy8 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy8.setHorizontalStretch(0)
        sizePolicy8.setVerticalStretch(0)
        sizePolicy8.setHeightForWidth(self.widget_rgb_curves_tmp.sizePolicy().hasHeightForWidth())
        self.widget_rgb_curves_tmp.setSizePolicy(sizePolicy8)
        self.widget_rgb_curves_tmp.setMinimumSize(QSize(512, 512))
        self.widget_rgb_curves_tmp.setMaximumSize(QSize(16777215, 16777215))
        self.widget_rgb_curves_tmp.setStyleSheet(u"background-color: rgb(200, 200, 200);")

        self.layout_rgb_curves.addWidget(self.widget_rgb_curves_tmp)


        self.layout_curves_editor.addLayout(self.layout_rgb_curves)

        self.widget_curves_browser_tmp = QWidget(widget_curves_editor)
        self.widget_curves_browser_tmp.setObjectName(u"widget_curves_browser_tmp")
        sizePolicy9 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy9.setHorizontalStretch(0)
        sizePolicy9.setVerticalStretch(0)
        sizePolicy9.setHeightForWidth(self.widget_curves_browser_tmp.sizePolicy().hasHeightForWidth())
        self.widget_curves_browser_tmp.setSizePolicy(sizePolicy9)
        self.widget_curves_browser_tmp.setMinimumSize(QSize(100, 0))
        self.widget_curves_browser_tmp.setStyleSheet(u"background-color: rgb(150, 150, 150);")

        self.layout_curves_editor.addWidget(self.widget_curves_browser_tmp)


        self.main_layout.addLayout(self.layout_curves_editor)


        self.retranslateUi(widget_curves_editor)

        self.combobox_part.setCurrentIndex(0)
        self.combobox_edition.setCurrentIndex(0)
        self.pushButton_change_preview_options.setDefault(False)


        QMetaObject.connectSlotsByName(widget_curves_editor)
    # setupUi

    def retranslateUi(self, widget_curves_editor):
        self.combobox_episode.setItemText(0, QCoreApplication.translate("widget_curves_editor", u"1", None))
        self.combobox_episode.setItemText(1, QCoreApplication.translate("widget_curves_editor", u"2", None))
        self.combobox_episode.setItemText(2, QCoreApplication.translate("widget_curves_editor", u"39", None))

        self.combobox_part.setItemText(0, QCoreApplication.translate("widget_curves_editor", u"precedemment", None))
        self.combobox_part.setItemText(1, QCoreApplication.translate("widget_curves_editor", u"episode", None))
        self.combobox_part.setItemText(2, QCoreApplication.translate("widget_curves_editor", u"a_suivre", None))
        self.combobox_part.setItemText(3, QCoreApplication.translate("widget_curves_editor", u"reportage", None))
        self.combobox_part.setItemText(4, QCoreApplication.translate("widget_curves_editor", u"g_debut", None))
        self.combobox_part.setItemText(5, QCoreApplication.translate("widget_curves_editor", u"g_fin", None))
        self.combobox_part.setItemText(6, QCoreApplication.translate("widget_curves_editor", u"g_asuivre", None))

        self.combobox_edition.setItemText(0, QCoreApplication.translate("widget_curves_editor", u"s", None))
        self.combobox_edition.setItemText(1, QCoreApplication.translate("widget_curves_editor", u"k", None))
        self.combobox_edition.setItemText(2, QCoreApplication.translate("widget_curves_editor", u"a", None))

        self.comboBox_step.setItemText(0, QCoreApplication.translate("widget_curves_editor", u"deinterlaced", None))

        self.label_edition_5.setText(QCoreApplication.translate("widget_curves_editor", u"Shot no.", None))
        self.pushButton_reset_filter_by_shot.setText(QCoreApplication.translate("widget_curves_editor", u"all", None))
        self.pushButton_filter_by_shot_todo.setText(QCoreApplication.translate("widget_curves_editor", u"todo", None))

        __sortingEnabled = self.list_shots.isSortingEnabled()
        self.list_shots.setSortingEnabled(False)
        ___qlistwidgetitem = self.list_shots.item(0)
        ___qlistwidgetitem.setText(QCoreApplication.translate("widget_curves_editor", u"999", None));
        self.list_shots.setSortingEnabled(__sortingEnabled)

        self.pushButton_reset_to_initial_curves.setText("")
        self.pushButton_remove_shot_curve.setText("")
        self.pushButton_save_database.setText("")
        self.groupBox.setTitle(QCoreApplication.translate("widget_curves_editor", u"Frame info", None))
        self.label_frame_no.setText(QCoreApplication.translate("widget_curves_editor", u"frame no.", None))
        self.label_shot_no.setText(QCoreApplication.translate("widget_curves_editor", u"shot no. 999", None))
        self.label_step.setText(QCoreApplication.translate("widget_curves_editor", u"sharpened", None))
        self.label_filter_id.setText(QCoreApplication.translate("widget_curves_editor", u"   990", None))
        self.label_dimension.setText(QCoreApplication.translate("widget_curves_editor", u"1440 x 1080", None))
        self.checkBox_fit_image_to_window.setText(QCoreApplication.translate("widget_curves_editor", u"Fit to window", None))
        self.pushButton_change_preview_options.setText(QCoreApplication.translate("widget_curves_editor", u"original", None))
        pass
    # retranslateUi

