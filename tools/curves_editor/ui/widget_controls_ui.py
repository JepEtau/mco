# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_widget_controls.ui'
##
## Created by: Qt User Interface Compiler version 6.2.3
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QDoubleSpinBox, QGroupBox,
    QHBoxLayout, QLabel, QLayout, QLineEdit,
    QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

from video_editor.widget_custom_qslider import Widget_custom_qslider

class Ui_widget_controls(object):
    def setupUi(self, widget_controls):
        if not widget_controls.objectName():
            widget_controls.setObjectName(u"widget_controls")
        widget_controls.resize(1003, 98)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(widget_controls.sizePolicy().hasHeightForWidth())
        widget_controls.setSizePolicy(sizePolicy)
        self.horizontalLayout_6 = QHBoxLayout(widget_controls)
        self.horizontalLayout_6.setSpacing(3)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(3, 3, 9, 3)
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setSizeConstraint(QLayout.SetMaximumSize)
        self.verticalLayout.setContentsMargins(-1, -1, -1, 0)
        self.slider_frames = Widget_custom_qslider(widget_controls)
        self.slider_frames.setObjectName(u"slider_frames")
        sizePolicy1 = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Maximum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.slider_frames.sizePolicy().hasHeightForWidth())
        self.slider_frames.setSizePolicy(sizePolicy1)
        self.slider_frames.setMinimumSize(QSize(750, 30))

        self.verticalLayout.addWidget(self.slider_frames)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.lineEdit_frame_no = QLineEdit(widget_controls)
        self.lineEdit_frame_no.setObjectName(u"lineEdit_frame_no")
        sizePolicy2 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.lineEdit_frame_no.sizePolicy().hasHeightForWidth())
        self.lineEdit_frame_no.setSizePolicy(sizePolicy2)
        self.lineEdit_frame_no.setMaximumSize(QSize(100, 16777215))
        self.lineEdit_frame_no.setReadOnly(True)

        self.horizontalLayout_2.addWidget(self.lineEdit_frame_no)

        self.pushButton_copy = QPushButton(widget_controls)
        self.pushButton_copy.setObjectName(u"pushButton_copy")
        self.pushButton_copy.setMaximumSize(QSize(70, 16777215))
        icon = QIcon()
        icon.addFile(u"img/page_copy.png", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_copy.setIcon(icon)
        self.pushButton_copy.setFlat(True)

        self.horizontalLayout_2.addWidget(self.pushButton_copy)

        self.label = QLabel(widget_controls)
        self.label.setObjectName(u"label")

        self.horizontalLayout_2.addWidget(self.label)

        self.lineEdit_new_frame_no = QLineEdit(widget_controls)
        self.lineEdit_new_frame_no.setObjectName(u"lineEdit_new_frame_no")
        sizePolicy2.setHeightForWidth(self.lineEdit_new_frame_no.sizePolicy().hasHeightForWidth())
        self.lineEdit_new_frame_no.setSizePolicy(sizePolicy2)
        self.lineEdit_new_frame_no.setMaximumSize(QSize(100, 16777215))
        self.lineEdit_new_frame_no.setReadOnly(True)

        self.horizontalLayout_2.addWidget(self.lineEdit_new_frame_no)

        self.pushButton_paste = QPushButton(widget_controls)
        self.pushButton_paste.setObjectName(u"pushButton_paste")
        icon1 = QIcon()
        icon1.addFile(u"img/page_paste.png", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_paste.setIcon(icon1)
        self.pushButton_paste.setFlat(True)

        self.horizontalLayout_2.addWidget(self.pushButton_paste)

        self.pushButton_remove = QPushButton(widget_controls)
        self.pushButton_remove.setObjectName(u"pushButton_remove")
        icon2 = QIcon()
        icon2.addFile(u"img/edit-delete.png", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_remove.setIcon(icon2)
        self.pushButton_remove.setFlat(True)

        self.horizontalLayout_2.addWidget(self.pushButton_remove)

        self.horizontalSpacer_5 = QSpacerItem(5, 10, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_5)

        self.groupBox_2 = QGroupBox(widget_controls)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.groupBox_2.setCheckable(False)
        self.horizontalLayout_8 = QHBoxLayout(self.groupBox_2)
        self.horizontalLayout_8.setSpacing(6)
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.horizontalLayout_8.setSizeConstraint(QLayout.SetMaximumSize)
        self.horizontalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.pushButton_crop_edition = QPushButton(self.groupBox_2)
        self.pushButton_crop_edition.setObjectName(u"pushButton_crop_edition")
        icon3 = QIcon()
        icon3.addFile(u"img/transform-crop.png", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_crop_edition.setIcon(icon3)
        self.pushButton_crop_edition.setCheckable(True)
        self.pushButton_crop_edition.setFlat(True)

        self.horizontalLayout_8.addWidget(self.pushButton_crop_edition)

        self.checkBox_show_crop_rect = QCheckBox(self.groupBox_2)
        self.checkBox_show_crop_rect.setObjectName(u"checkBox_show_crop_rect")

        self.horizontalLayout_8.addWidget(self.checkBox_show_crop_rect)


        self.horizontalLayout_2.addWidget(self.groupBox_2)

        self.horizontalSpacer_6 = QSpacerItem(5, 10, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_6)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.verticalSpacer = QSpacerItem(20, 1, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)


        self.horizontalLayout_6.addLayout(self.verticalLayout)

        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setSpacing(0)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.pushButton_play_pause = QPushButton(widget_controls)
        self.pushButton_play_pause.setObjectName(u"pushButton_play_pause")
        icon4 = QIcon()
        icon4.addFile(u"img/play.png", QSize(), QIcon.Normal, QIcon.Off)
        icon4.addFile(u"img/play.png", QSize(), QIcon.Selected, QIcon.Off)
        icon4.addFile(u"img/pause.png", QSize(), QIcon.Selected, QIcon.On)
        self.pushButton_play_pause.setIcon(icon4)
        self.pushButton_play_pause.setCheckable(True)
        self.pushButton_play_pause.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_play_pause)

        self.pushButton_previous_frame = QPushButton(widget_controls)
        self.pushButton_previous_frame.setObjectName(u"pushButton_previous_frame")
        icon5 = QIcon()
        icon5.addFile(u"img/go-first-view.png", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_previous_frame.setIcon(icon5)
        self.pushButton_previous_frame.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_previous_frame)

        self.pushButton_next_frame = QPushButton(widget_controls)
        self.pushButton_next_frame.setObjectName(u"pushButton_next_frame")
        icon6 = QIcon()
        icon6.addFile(u"img/go-last-view.png", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_next_frame.setIcon(icon6)
        self.pushButton_next_frame.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_next_frame)

        self.horizontalSpacer_3 = QSpacerItem(5, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_3)


        self.verticalLayout_4.addLayout(self.horizontalLayout)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.pushButton_stop = QPushButton(widget_controls)
        self.pushButton_stop.setObjectName(u"pushButton_stop")
        icon7 = QIcon()
        icon7.addFile(u"img/stop.png", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_stop.setIcon(icon7)
        self.pushButton_stop.setCheckable(False)
        self.pushButton_stop.setFlat(True)

        self.horizontalLayout_7.addWidget(self.pushButton_stop)

        self.horizontalSpacer_2 = QSpacerItem(10, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.horizontalLayout_7.addItem(self.horizontalSpacer_2)

        self.spinBox_speed = QDoubleSpinBox(widget_controls)
        self.spinBox_speed.setObjectName(u"spinBox_speed")
        self.spinBox_speed.setWrapping(False)
        self.spinBox_speed.setFrame(True)
        self.spinBox_speed.setAlignment(Qt.AlignCenter)
        self.spinBox_speed.setKeyboardTracking(False)
        self.spinBox_speed.setDecimals(1)
        self.spinBox_speed.setMinimum(0.500000000000000)
        self.spinBox_speed.setMaximum(2.000000000000000)
        self.spinBox_speed.setSingleStep(0.500000000000000)

        self.horizontalLayout_7.addWidget(self.spinBox_speed)


        self.verticalLayout_4.addLayout(self.horizontalLayout_7)

        self.verticalSpacer_4 = QSpacerItem(20, 1, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_4.addItem(self.verticalSpacer_4)


        self.horizontalLayout_6.addLayout(self.verticalLayout_4)

        self.groupBox = QGroupBox(widget_controls)
        self.groupBox.setObjectName(u"groupBox")
        sizePolicy3 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy3)
        self.groupBox.setFlat(False)
        self.verticalLayout_3 = QVBoxLayout(self.groupBox)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(1, 1, 1, 1)
        self.checkBox_preview_rgb = QCheckBox(self.groupBox)
        self.checkBox_preview_rgb.setObjectName(u"checkBox_preview_rgb")

        self.verticalLayout_3.addWidget(self.checkBox_preview_rgb)

        self.checkBox_preview_replace = QCheckBox(self.groupBox)
        self.checkBox_preview_replace.setObjectName(u"checkBox_preview_replace")

        self.verticalLayout_3.addWidget(self.checkBox_preview_replace)

        self.checkBox_preview_final = QCheckBox(self.groupBox)
        self.checkBox_preview_final.setObjectName(u"checkBox_preview_final")

        self.verticalLayout_3.addWidget(self.checkBox_preview_final)


        self.horizontalLayout_6.addWidget(self.groupBox, 0, Qt.AlignTop)


        self.retranslateUi(widget_controls)

        self.pushButton_crop_edition.setDefault(False)


        QMetaObject.connectSlotsByName(widget_controls)
    # setupUi

    def retranslateUi(self, widget_controls):
        widget_controls.setWindowTitle(QCoreApplication.translate("widget_controls", u"Form", None))
        self.pushButton_copy.setText("")
        self.label.setText(QCoreApplication.translate("widget_controls", u"replaced by", None))
        self.pushButton_paste.setText("")
        self.pushButton_remove.setText("")
        self.groupBox_2.setTitle("")
        self.pushButton_crop_edition.setText(QCoreApplication.translate("widget_controls", u"crop", None))
        self.checkBox_show_crop_rect.setText(QCoreApplication.translate("widget_controls", u"rectangle", None))
        self.pushButton_play_pause.setText("")
        self.pushButton_previous_frame.setText("")
        self.pushButton_next_frame.setText("")
        self.pushButton_stop.setText("")
        self.groupBox.setTitle(QCoreApplication.translate("widget_controls", u"preview", None))
        self.checkBox_preview_rgb.setText(QCoreApplication.translate("widget_controls", u"RGB curves", None))
        self.checkBox_preview_replace.setText(QCoreApplication.translate("widget_controls", u"replace", None))
        self.checkBox_preview_final.setText(QCoreApplication.translate("widget_controls", u"final", None))
    # retranslateUi

