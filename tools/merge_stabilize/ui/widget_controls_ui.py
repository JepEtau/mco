# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_widget_controls.ui'
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

        self.layout_frames_no = QHBoxLayout()
        self.layout_frames_no.setObjectName(u"layout_frames_no")
        self.layout_frames_no.setContentsMargins(-1, -1, -1, 0)
        self.horizontalSpacer_6 = QSpacerItem(5, 10, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.layout_frames_no.addItem(self.horizontalSpacer_6)

        self.lineEdit_frame_no = QLineEdit(widget_controls)
        self.lineEdit_frame_no.setObjectName(u"lineEdit_frame_no")
        sizePolicy2 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.lineEdit_frame_no.sizePolicy().hasHeightForWidth())
        self.lineEdit_frame_no.setSizePolicy(sizePolicy2)
        self.lineEdit_frame_no.setMaximumSize(QSize(100, 16777215))
        self.lineEdit_frame_no.setReadOnly(True)

        self.layout_frames_no.addWidget(self.lineEdit_frame_no)

        self.horizontalSpacer_5 = QSpacerItem(5, 10, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.layout_frames_no.addItem(self.horizontalSpacer_5)

        self.label_2 = QLabel(widget_controls)
        self.label_2.setObjectName(u"label_2")

        self.layout_frames_no.addWidget(self.label_2)

        self.lineEdit_new_frame_no = QLineEdit(widget_controls)
        self.lineEdit_new_frame_no.setObjectName(u"lineEdit_new_frame_no")
        sizePolicy2.setHeightForWidth(self.lineEdit_new_frame_no.sizePolicy().hasHeightForWidth())
        self.lineEdit_new_frame_no.setSizePolicy(sizePolicy2)
        self.lineEdit_new_frame_no.setMaximumSize(QSize(100, 16777215))
        self.lineEdit_new_frame_no.setReadOnly(True)

        self.layout_frames_no.addWidget(self.lineEdit_new_frame_no)


        self.verticalLayout.addLayout(self.layout_frames_no)

        self.verticalSpacer_2 = QSpacerItem(20, 12, QSizePolicy.Minimum, QSizePolicy.Fixed)

        self.verticalLayout.addItem(self.verticalSpacer_2)


        self.horizontalLayout_6.addLayout(self.verticalLayout)

        self.layout_player_control = QVBoxLayout()
        self.layout_player_control.setSpacing(0)
        self.layout_player_control.setObjectName(u"layout_player_control")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.pushButton_play_pause = QPushButton(widget_controls)
        self.pushButton_play_pause.setObjectName(u"pushButton_play_pause")
        icon = QIcon()
        icon.addFile(u"../../../../.designer/backup/img/play.png", QSize(), QIcon.Normal, QIcon.Off)
        icon.addFile(u"../../../../.designer/backup/img/play.png", QSize(), QIcon.Selected, QIcon.Off)
        icon.addFile(u"../../../../.designer/backup/img/pause.png", QSize(), QIcon.Selected, QIcon.On)
        self.pushButton_play_pause.setIcon(icon)
        self.pushButton_play_pause.setCheckable(True)
        self.pushButton_play_pause.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_play_pause)

        self.pushButton_previous_frame = QPushButton(widget_controls)
        self.pushButton_previous_frame.setObjectName(u"pushButton_previous_frame")
        icon1 = QIcon()
        icon1.addFile(u"../../../../.designer/backup/img/go-first-view.png", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_previous_frame.setIcon(icon1)
        self.pushButton_previous_frame.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_previous_frame)

        self.pushButton_next_frame = QPushButton(widget_controls)
        self.pushButton_next_frame.setObjectName(u"pushButton_next_frame")
        icon2 = QIcon()
        icon2.addFile(u"../../../../.designer/backup/img/go-last-view.png", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_next_frame.setIcon(icon2)
        self.pushButton_next_frame.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_next_frame)

        self.horizontalSpacer_3 = QSpacerItem(5, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_3)


        self.layout_player_control.addLayout(self.horizontalLayout)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.pushButton_stop = QPushButton(widget_controls)
        self.pushButton_stop.setObjectName(u"pushButton_stop")
        icon3 = QIcon()
        icon3.addFile(u"../../../../.designer/backup/img/stop.png", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_stop.setIcon(icon3)
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


        self.layout_player_control.addLayout(self.horizontalLayout_7)

        self.verticalSpacer_4 = QSpacerItem(20, 1, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.layout_player_control.addItem(self.verticalSpacer_4)


        self.horizontalLayout_6.addLayout(self.layout_player_control)

        self.groupBox_preview = QGroupBox(widget_controls)
        self.groupBox_preview.setObjectName(u"groupBox_preview")
        sizePolicy3 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.groupBox_preview.sizePolicy().hasHeightForWidth())
        self.groupBox_preview.setSizePolicy(sizePolicy3)
        self.groupBox_preview.setFlat(False)
        self.verticalLayout_5 = QVBoxLayout(self.groupBox_preview)
        self.verticalLayout_5.setSpacing(0)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(1, 1, 1, 1)
        self.checkBox_preview_rgb = QCheckBox(self.groupBox_preview)
        self.checkBox_preview_rgb.setObjectName(u"checkBox_preview_rgb")

        self.verticalLayout_5.addWidget(self.checkBox_preview_rgb)

        self.checkBox_preview_replace = QCheckBox(self.groupBox_preview)
        self.checkBox_preview_replace.setObjectName(u"checkBox_preview_replace")

        self.verticalLayout_5.addWidget(self.checkBox_preview_replace)

        self.checkBox_preview_final = QCheckBox(self.groupBox_preview)
        self.checkBox_preview_final.setObjectName(u"checkBox_preview_final")

        self.verticalLayout_5.addWidget(self.checkBox_preview_final)


        self.horizontalLayout_6.addWidget(self.groupBox_preview)


        self.retranslateUi(widget_controls)

        QMetaObject.connectSlotsByName(widget_controls)
    # setupUi

    def retranslateUi(self, widget_controls):
        widget_controls.setWindowTitle(QCoreApplication.translate("widget_controls", u"Form", None))
        self.label_2.setText(QCoreApplication.translate("widget_controls", u"replaced by", None))
        self.pushButton_play_pause.setText("")
        self.pushButton_previous_frame.setText("")
        self.pushButton_next_frame.setText("")
        self.pushButton_stop.setText("")
        self.groupBox_preview.setTitle(QCoreApplication.translate("widget_controls", u"preview", None))
        self.checkBox_preview_rgb.setText(QCoreApplication.translate("widget_controls", u"RGB curves", None))
        self.checkBox_preview_replace.setText(QCoreApplication.translate("widget_controls", u"replace", None))
        self.checkBox_preview_final.setText(QCoreApplication.translate("widget_controls", u"final", None))
    # retranslateUi

