# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_widget_stitching.ui'
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
from PySide6.QtWidgets import (QApplication, QDoubleSpinBox, QFrame, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QRadioButton, QSizePolicy, QSpacerItem, QSpinBox,
    QVBoxLayout, QWidget)

class Ui_widget_stitching(object):
    def setupUi(self, widget_stitching):
        if not widget_stitching.objectName():
            widget_stitching.setObjectName(u"widget_stitching")
        widget_stitching.resize(312, 532)
        self.verticalLayout_3 = QVBoxLayout(widget_stitching)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.frame = QFrame(widget_stitching)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.Panel)
        self.frame.setFrameShadow(QFrame.Plain)
        self.verticalLayout_5 = QVBoxLayout(self.frame)
        self.verticalLayout_5.setSpacing(4)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(6, 6, 6, 6)
        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setSpacing(3)
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.pushButton_set_preview = QPushButton(self.frame)
        self.pushButton_set_preview.setObjectName(u"pushButton_set_preview")
        sizePolicy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton_set_preview.sizePolicy().hasHeightForWidth())
        self.pushButton_set_preview.setSizePolicy(sizePolicy)
        icon = QIcon()
        icon.addFile(u"icons/grey/eye.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon.addFile(u"icons/blue/eye.svg", QSize(), QIcon.Normal, QIcon.On)
        self.pushButton_set_preview.setIcon(icon)
        self.pushButton_set_preview.setCheckable(True)
        self.pushButton_set_preview.setFlat(True)

        self.horizontalLayout_10.addWidget(self.pushButton_set_preview)

        self.pushButton_save = QPushButton(self.frame)
        self.pushButton_save.setObjectName(u"pushButton_save")
        sizePolicy.setHeightForWidth(self.pushButton_save.sizePolicy().hasHeightForWidth())
        self.pushButton_save.setSizePolicy(sizePolicy)
        icon1 = QIcon()
        icon1.addFile(u"icons/grey/save.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon1.addFile(u"icons/purple/save.svg", QSize(), QIcon.Normal, QIcon.On)
        self.pushButton_save.setIcon(icon1)
        self.pushButton_save.setCheckable(False)
        self.pushButton_save.setAutoDefault(False)
        self.pushButton_save.setFlat(True)

        self.horizontalLayout_10.addWidget(self.pushButton_save)

        self.pushButton_discard = QPushButton(self.frame)
        self.pushButton_discard.setObjectName(u"pushButton_discard")
        sizePolicy.setHeightForWidth(self.pushButton_discard.sizePolicy().hasHeightForWidth())
        self.pushButton_discard.setSizePolicy(sizePolicy)
        icon2 = QIcon()
        icon2.addFile(u"icons/grey/undo.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon2.addFile(u"icons/purple/undo.svg", QSize(), QIcon.Normal, QIcon.On)
        self.pushButton_discard.setIcon(icon2)
        self.pushButton_discard.setCheckable(False)
        self.pushButton_discard.setAutoDefault(False)
        self.pushButton_discard.setFlat(True)

        self.horizontalLayout_10.addWidget(self.pushButton_discard)

        self.horizontalSpacer_2 = QSpacerItem(5, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_10.addItem(self.horizontalSpacer_2)

        self.pushButton_close = QPushButton(self.frame)
        self.pushButton_close.setObjectName(u"pushButton_close")
        sizePolicy.setHeightForWidth(self.pushButton_close.sizePolicy().hasHeightForWidth())
        self.pushButton_close.setSizePolicy(sizePolicy)
        icon3 = QIcon()
        icon3.addFile(u"icons/purple/x-square.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon3.addFile(u"icons/purple/x-square.svg", QSize(), QIcon.Normal, QIcon.On)
        self.pushButton_close.setIcon(icon3)
        self.pushButton_close.setCheckable(False)
        self.pushButton_close.setAutoDefault(False)
        self.pushButton_close.setFlat(True)

        self.horizontalLayout_10.addWidget(self.pushButton_close)


        self.verticalLayout_5.addLayout(self.horizontalLayout_10)

        self.groupBox_stitching = QGroupBox(self.frame)
        self.groupBox_stitching.setObjectName(u"groupBox_stitching")
        self.groupBox_stitching.setCheckable(True)
        self.verticalLayout = QVBoxLayout(self.groupBox_stitching)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.horizontalLayout_8.setContentsMargins(-1, -1, -1, 0)
        self.radioButton_shot_homography = QRadioButton(self.groupBox_stitching)
        self.radioButton_shot_homography.setObjectName(u"radioButton_shot_homography")
        sizePolicy1 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.radioButton_shot_homography.sizePolicy().hasHeightForWidth())
        self.radioButton_shot_homography.setSizePolicy(sizePolicy1)
        self.radioButton_shot_homography.setChecked(True)

        self.horizontalLayout_8.addWidget(self.radioButton_shot_homography)

        self.radioButton_frame_homography = QRadioButton(self.groupBox_stitching)
        self.radioButton_frame_homography.setObjectName(u"radioButton_frame_homography")
        sizePolicy2 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.radioButton_frame_homography.sizePolicy().hasHeightForWidth())
        self.radioButton_frame_homography.setSizePolicy(sizePolicy2)
        self.radioButton_frame_homography.setCheckable(True)
        self.radioButton_frame_homography.setChecked(False)

        self.horizontalLayout_8.addWidget(self.radioButton_frame_homography)

        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_8.addItem(self.horizontalSpacer_5)


        self.verticalLayout.addLayout(self.horizontalLayout_8)

        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(15, -1, -1, 0)
        self.groupBox_detection_method_2 = QGroupBox(self.groupBox_stitching)
        self.groupBox_detection_method_2.setObjectName(u"groupBox_detection_method_2")
        sizePolicy3 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.groupBox_detection_method_2.sizePolicy().hasHeightForWidth())
        self.groupBox_detection_method_2.setSizePolicy(sizePolicy3)
        self.horizontalLayout_3 = QHBoxLayout(self.groupBox_detection_method_2)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(3, 3, 3, 3)
        self.pushButton_roi_edition = QPushButton(self.groupBox_detection_method_2)
        self.pushButton_roi_edition.setObjectName(u"pushButton_roi_edition")
        sizePolicy.setHeightForWidth(self.pushButton_roi_edition.sizePolicy().hasHeightForWidth())
        self.pushButton_roi_edition.setSizePolicy(sizePolicy)
        icon4 = QIcon()
        icon4.addFile(u"icons/grey/box-select.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon4.addFile(u"icons/blue/box-select.svg", QSize(), QIcon.Normal, QIcon.On)
        icon4.addFile(u"icons/grey/box-select.svg", QSize(), QIcon.Disabled, QIcon.Off)
        self.pushButton_roi_edition.setIcon(icon4)
        self.pushButton_roi_edition.setCheckable(True)
        self.pushButton_roi_edition.setAutoDefault(False)
        self.pushButton_roi_edition.setFlat(True)

        self.horizontalLayout_3.addWidget(self.pushButton_roi_edition)

        self.lineEdit_roi_rectangle = QLineEdit(self.groupBox_detection_method_2)
        self.lineEdit_roi_rectangle.setObjectName(u"lineEdit_roi_rectangle")
        sizePolicy2.setHeightForWidth(self.lineEdit_roi_rectangle.sizePolicy().hasHeightForWidth())
        self.lineEdit_roi_rectangle.setSizePolicy(sizePolicy2)
        self.lineEdit_roi_rectangle.setMinimumSize(QSize(140, 0))
        self.lineEdit_roi_rectangle.setMaximumSize(QSize(140, 16777215))
        self.lineEdit_roi_rectangle.setAlignment(Qt.AlignCenter)
        self.lineEdit_roi_rectangle.setReadOnly(True)

        self.horizontalLayout_3.addWidget(self.lineEdit_roi_rectangle)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_3)

        self.pushButton_roi_discard_modifications = QPushButton(self.groupBox_detection_method_2)
        self.pushButton_roi_discard_modifications.setObjectName(u"pushButton_roi_discard_modifications")
        sizePolicy1.setHeightForWidth(self.pushButton_roi_discard_modifications.sizePolicy().hasHeightForWidth())
        self.pushButton_roi_discard_modifications.setSizePolicy(sizePolicy1)
        icon5 = QIcon()
        icon5.addFile(u"icons/purple/undo.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_roi_discard_modifications.setIcon(icon5)
        self.pushButton_roi_discard_modifications.setFlat(True)

        self.horizontalLayout_3.addWidget(self.pushButton_roi_discard_modifications)


        self.verticalLayout_4.addWidget(self.groupBox_detection_method_2)

        self.groupBox_detection_method_3 = QGroupBox(self.groupBox_stitching)
        self.groupBox_detection_method_3.setObjectName(u"groupBox_detection_method_3")
        sizePolicy3.setHeightForWidth(self.groupBox_detection_method_3.sizePolicy().hasHeightForWidth())
        self.groupBox_detection_method_3.setSizePolicy(sizePolicy3)
        self.horizontalLayout_9 = QHBoxLayout(self.groupBox_detection_method_3)
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.horizontalLayout_9.setContentsMargins(3, 3, 3, 3)
        self.label = QLabel(self.groupBox_detection_method_3)
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_9.addWidget(self.label)

        self.spinBox_sharpen_radius = QSpinBox(self.groupBox_detection_method_3)
        self.spinBox_sharpen_radius.setObjectName(u"spinBox_sharpen_radius")
        sizePolicy4 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.spinBox_sharpen_radius.sizePolicy().hasHeightForWidth())
        self.spinBox_sharpen_radius.setSizePolicy(sizePolicy4)
        self.spinBox_sharpen_radius.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.spinBox_sharpen_radius.setMinimum(1)
        self.spinBox_sharpen_radius.setMaximum(11)
        self.spinBox_sharpen_radius.setSingleStep(2)
        self.spinBox_sharpen_radius.setValue(1)

        self.horizontalLayout_9.addWidget(self.spinBox_sharpen_radius)

        self.horizontalSpacer_7 = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_9.addItem(self.horizontalSpacer_7)

        self.label_2 = QLabel(self.groupBox_detection_method_3)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_9.addWidget(self.label_2)

        self.doubleSpinBox_sharpen_amount = QDoubleSpinBox(self.groupBox_detection_method_3)
        self.doubleSpinBox_sharpen_amount.setObjectName(u"doubleSpinBox_sharpen_amount")
        sizePolicy1.setHeightForWidth(self.doubleSpinBox_sharpen_amount.sizePolicy().hasHeightForWidth())
        self.doubleSpinBox_sharpen_amount.setSizePolicy(sizePolicy1)
        self.doubleSpinBox_sharpen_amount.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.doubleSpinBox_sharpen_amount.setDecimals(1)
        self.doubleSpinBox_sharpen_amount.setMaximum(3.000000000000000)
        self.doubleSpinBox_sharpen_amount.setSingleStep(0.100000000000000)
        self.doubleSpinBox_sharpen_amount.setValue(0.500000000000000)

        self.horizontalLayout_9.addWidget(self.doubleSpinBox_sharpen_amount)

        self.horizontalSpacer_6 = QSpacerItem(10, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_9.addItem(self.horizontalSpacer_6)


        self.verticalLayout_4.addWidget(self.groupBox_detection_method_3)

        self.groupBox_detection_method = QGroupBox(self.groupBox_stitching)
        self.groupBox_detection_method.setObjectName(u"groupBox_detection_method")
        sizePolicy3.setHeightForWidth(self.groupBox_detection_method.sizePolicy().hasHeightForWidth())
        self.groupBox_detection_method.setSizePolicy(sizePolicy3)
        self.verticalLayout_2 = QVBoxLayout(self.groupBox_detection_method)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(3, 3, 3, 3)
        self.radioButton_sift = QRadioButton(self.groupBox_detection_method)
        self.radioButton_sift.setObjectName(u"radioButton_sift")
        sizePolicy1.setHeightForWidth(self.radioButton_sift.sizePolicy().hasHeightForWidth())
        self.radioButton_sift.setSizePolicy(sizePolicy1)
        self.radioButton_sift.setChecked(True)

        self.verticalLayout_2.addWidget(self.radioButton_sift)

        self.radioButton_surf = QRadioButton(self.groupBox_detection_method)
        self.radioButton_surf.setObjectName(u"radioButton_surf")
        sizePolicy1.setHeightForWidth(self.radioButton_surf.sizePolicy().hasHeightForWidth())
        self.radioButton_surf.setSizePolicy(sizePolicy1)

        self.verticalLayout_2.addWidget(self.radioButton_surf)

        self.radioButton_brisk = QRadioButton(self.groupBox_detection_method)
        self.radioButton_brisk.setObjectName(u"radioButton_brisk")
        sizePolicy1.setHeightForWidth(self.radioButton_brisk.sizePolicy().hasHeightForWidth())
        self.radioButton_brisk.setSizePolicy(sizePolicy1)

        self.verticalLayout_2.addWidget(self.radioButton_brisk)

        self.radioButton_orb = QRadioButton(self.groupBox_detection_method)
        self.radioButton_orb.setObjectName(u"radioButton_orb")
        sizePolicy1.setHeightForWidth(self.radioButton_orb.sizePolicy().hasHeightForWidth())
        self.radioButton_orb.setSizePolicy(sizePolicy1)

        self.verticalLayout_2.addWidget(self.radioButton_orb)


        self.verticalLayout_4.addWidget(self.groupBox_detection_method)

        self.groupBox_match_descriptors = QGroupBox(self.groupBox_stitching)
        self.groupBox_match_descriptors.setObjectName(u"groupBox_match_descriptors")
        sizePolicy.setHeightForWidth(self.groupBox_match_descriptors.sizePolicy().hasHeightForWidth())
        self.groupBox_match_descriptors.setSizePolicy(sizePolicy)
        self.horizontalLayout_2 = QHBoxLayout(self.groupBox_match_descriptors)
        self.horizontalLayout_2.setSpacing(6)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(3, 3, 3, 3)
        self.radioButton_bf = QRadioButton(self.groupBox_match_descriptors)
        self.radioButton_bf.setObjectName(u"radioButton_bf")
        self.radioButton_bf.setChecked(True)

        self.horizontalLayout_2.addWidget(self.radioButton_bf)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setSpacing(0)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, -1, -1, -1)
        self.radioButton_knn = QRadioButton(self.groupBox_match_descriptors)
        self.radioButton_knn.setObjectName(u"radioButton_knn")

        self.horizontalLayout_4.addWidget(self.radioButton_knn)

        self.doubleSpinBox_knn_ratio = QDoubleSpinBox(self.groupBox_match_descriptors)
        self.doubleSpinBox_knn_ratio.setObjectName(u"doubleSpinBox_knn_ratio")
        sizePolicy1.setHeightForWidth(self.doubleSpinBox_knn_ratio.sizePolicy().hasHeightForWidth())
        self.doubleSpinBox_knn_ratio.setSizePolicy(sizePolicy1)
        self.doubleSpinBox_knn_ratio.setFrame(True)
        self.doubleSpinBox_knn_ratio.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.doubleSpinBox_knn_ratio.setDecimals(2)
        self.doubleSpinBox_knn_ratio.setSingleStep(0.050000000000000)
        self.doubleSpinBox_knn_ratio.setValue(0.750000000000000)

        self.horizontalLayout_4.addWidget(self.doubleSpinBox_knn_ratio)


        self.horizontalLayout_2.addLayout(self.horizontalLayout_4)


        self.verticalLayout_4.addWidget(self.groupBox_match_descriptors)

        self.groupBox_find_homography = QGroupBox(self.groupBox_stitching)
        self.groupBox_find_homography.setObjectName(u"groupBox_find_homography")
        sizePolicy.setHeightForWidth(self.groupBox_find_homography.sizePolicy().hasHeightForWidth())
        self.groupBox_find_homography.setSizePolicy(sizePolicy)
        self.horizontalLayout_5 = QHBoxLayout(self.groupBox_find_homography)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(3, 3, 3, 3)
        self.pushButton_ransac = QPushButton(self.groupBox_find_homography)
        self.pushButton_ransac.setObjectName(u"pushButton_ransac")
        self.pushButton_ransac.setCheckable(False)
        self.pushButton_ransac.setFlat(True)

        self.horizontalLayout_5.addWidget(self.pushButton_ransac)

        self.doubleSpinBox_ransac_reproj_threshold = QDoubleSpinBox(self.groupBox_find_homography)
        self.doubleSpinBox_ransac_reproj_threshold.setObjectName(u"doubleSpinBox_ransac_reproj_threshold")
        sizePolicy1.setHeightForWidth(self.doubleSpinBox_ransac_reproj_threshold.sizePolicy().hasHeightForWidth())
        self.doubleSpinBox_ransac_reproj_threshold.setSizePolicy(sizePolicy1)
        self.doubleSpinBox_ransac_reproj_threshold.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.doubleSpinBox_ransac_reproj_threshold.setDecimals(1)
        self.doubleSpinBox_ransac_reproj_threshold.setValue(3.000000000000000)

        self.horizontalLayout_5.addWidget(self.doubleSpinBox_ransac_reproj_threshold)

        self.horizontalSpacer = QSpacerItem(10, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer)


        self.verticalLayout_4.addWidget(self.groupBox_find_homography)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setSpacing(0)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.pushButton_load_default = QPushButton(self.groupBox_stitching)
        self.pushButton_load_default.setObjectName(u"pushButton_load_default")
        sizePolicy1.setHeightForWidth(self.pushButton_load_default.sizePolicy().hasHeightForWidth())
        self.pushButton_load_default.setSizePolicy(sizePolicy1)

        self.horizontalLayout_7.addWidget(self.pushButton_load_default)

        self.horizontalSpacer_10 = QSpacerItem(10, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_7.addItem(self.horizontalSpacer_10)

        self.pushButton_undo = QPushButton(self.groupBox_stitching)
        self.pushButton_undo.setObjectName(u"pushButton_undo")
        sizePolicy1.setHeightForWidth(self.pushButton_undo.sizePolicy().hasHeightForWidth())
        self.pushButton_undo.setSizePolicy(sizePolicy1)
        self.pushButton_undo.setIcon(icon5)
        self.pushButton_undo.setFlat(True)

        self.horizontalLayout_7.addWidget(self.pushButton_undo)

        self.pushButton_calculate = QPushButton(self.groupBox_stitching)
        self.pushButton_calculate.setObjectName(u"pushButton_calculate")

        self.horizontalLayout_7.addWidget(self.pushButton_calculate)


        self.verticalLayout_4.addLayout(self.horizontalLayout_7)


        self.verticalLayout.addLayout(self.verticalLayout_4)

        self.groupBox_crop = QGroupBox(self.groupBox_stitching)
        self.groupBox_crop.setObjectName(u"groupBox_crop")
        sizePolicy3.setHeightForWidth(self.groupBox_crop.sizePolicy().hasHeightForWidth())
        self.groupBox_crop.setSizePolicy(sizePolicy3)
        self.horizontalLayout_6 = QHBoxLayout(self.groupBox_crop)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(3, 3, 3, 3)
        self.pushButton_crop_edition = QPushButton(self.groupBox_crop)
        self.pushButton_crop_edition.setObjectName(u"pushButton_crop_edition")
        sizePolicy.setHeightForWidth(self.pushButton_crop_edition.sizePolicy().hasHeightForWidth())
        self.pushButton_crop_edition.setSizePolicy(sizePolicy)
        icon6 = QIcon()
        icon6.addFile(u"icons/grey/crop.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon6.addFile(u"icons/blue/crop.svg", QSize(), QIcon.Normal, QIcon.On)
        icon6.addFile(u"icons/grey/crop.svg", QSize(), QIcon.Disabled, QIcon.Off)
        self.pushButton_crop_edition.setIcon(icon6)
        self.pushButton_crop_edition.setCheckable(True)
        self.pushButton_crop_edition.setAutoDefault(False)
        self.pushButton_crop_edition.setFlat(True)

        self.horizontalLayout_6.addWidget(self.pushButton_crop_edition)

        self.lineEdit_crop_rectangle = QLineEdit(self.groupBox_crop)
        self.lineEdit_crop_rectangle.setObjectName(u"lineEdit_crop_rectangle")
        sizePolicy2.setHeightForWidth(self.lineEdit_crop_rectangle.sizePolicy().hasHeightForWidth())
        self.lineEdit_crop_rectangle.setSizePolicy(sizePolicy2)
        self.lineEdit_crop_rectangle.setMinimumSize(QSize(160, 0))
        self.lineEdit_crop_rectangle.setMaximumSize(QSize(160, 16777215))
        self.lineEdit_crop_rectangle.setAlignment(Qt.AlignCenter)
        self.lineEdit_crop_rectangle.setReadOnly(True)

        self.horizontalLayout_6.addWidget(self.lineEdit_crop_rectangle)

        self.horizontalSpacer_4 = QSpacerItem(1, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_4)

        self.pushButton_crop_reset_rectangle = QPushButton(self.groupBox_crop)
        self.pushButton_crop_reset_rectangle.setObjectName(u"pushButton_crop_reset_rectangle")
        sizePolicy1.setHeightForWidth(self.pushButton_crop_reset_rectangle.sizePolicy().hasHeightForWidth())
        self.pushButton_crop_reset_rectangle.setSizePolicy(sizePolicy1)
        self.pushButton_crop_reset_rectangle.setIcon(icon5)
        self.pushButton_crop_reset_rectangle.setFlat(True)

        self.horizontalLayout_6.addWidget(self.pushButton_crop_reset_rectangle)


        self.verticalLayout.addWidget(self.groupBox_crop)


        self.verticalLayout_5.addWidget(self.groupBox_stitching)


        self.verticalLayout_3.addWidget(self.frame)


        self.retranslateUi(widget_stitching)

        self.pushButton_ransac.setDefault(False)


        QMetaObject.connectSlotsByName(widget_stitching)
    # setupUi

    def retranslateUi(self, widget_stitching):
        widget_stitching.setWindowTitle(QCoreApplication.translate("widget_stitching", u"Form", None))
        self.pushButton_set_preview.setText("")
        self.pushButton_save.setText("")
        self.pushButton_discard.setText("")
        self.pushButton_close.setText("")
        self.groupBox_stitching.setTitle(QCoreApplication.translate("widget_stitching", u"(2) Stitching", None))
        self.radioButton_shot_homography.setText(QCoreApplication.translate("widget_stitching", u"Shot", None))
        self.radioButton_frame_homography.setText(QCoreApplication.translate("widget_stitching", u"Frame", None))
        self.groupBox_detection_method_2.setTitle(QCoreApplication.translate("widget_stitching", u"(2.1) ROI", None))
        self.pushButton_roi_edition.setText("")
        self.lineEdit_roi_rectangle.setText(QCoreApplication.translate("widget_stitching", u"(0, 0, 1950, 1150)", None))
        self.pushButton_roi_discard_modifications.setText("")
        self.groupBox_detection_method_3.setTitle(QCoreApplication.translate("widget_stitching", u"(2.2) Use sharpened images", None))
        self.label.setText(QCoreApplication.translate("widget_stitching", u"Radius", None))
        self.label_2.setText(QCoreApplication.translate("widget_stitching", u"Amount", None))
        self.groupBox_detection_method.setTitle(QCoreApplication.translate("widget_stitching", u"(2.3) Detection method", None))
        self.radioButton_sift.setText(QCoreApplication.translate("widget_stitching", u"&SIFT (B.F. matcher: L2)", None))
        self.radioButton_surf.setText(QCoreApplication.translate("widget_stitching", u"S&URF (B.F. matcher: L2)", None))
        self.radioButton_brisk.setText(QCoreApplication.translate("widget_stitching", u"&BRISK (B.F. matcher: Hamming)", None))
        self.radioButton_orb.setText(QCoreApplication.translate("widget_stitching", u"&ORB (B.F. matcher: Hamming)", None))
        self.groupBox_match_descriptors.setTitle(QCoreApplication.translate("widget_stitching", u"(2.4) &Match descriptors", None))
        self.radioButton_bf.setText(QCoreApplication.translate("widget_stitching", u"bf", None))
        self.radioButton_knn.setText(QCoreApplication.translate("widget_stitching", u"knn, ratio", None))
        self.groupBox_find_homography.setTitle(QCoreApplication.translate("widget_stitching", u"(2.5) Find Homography (RANSAC)", None))
        self.pushButton_ransac.setText(QCoreApplication.translate("widget_stitching", u"&RANSAC Reproj Threshold", None))
        self.pushButton_load_default.setText(QCoreApplication.translate("widget_stitching", u"default", None))
        self.pushButton_undo.setText("")
        self.pushButton_calculate.setText(QCoreApplication.translate("widget_stitching", u"calculate (F5)", None))
        self.groupBox_crop.setTitle(QCoreApplication.translate("widget_stitching", u"(2.6) Crop: foreground", None))
        self.pushButton_crop_edition.setText("")
        self.lineEdit_crop_rectangle.setText(QCoreApplication.translate("widget_stitching", u"t:10, d:10, l:50, r:50", None))
        self.pushButton_crop_reset_rectangle.setText("")
    # retranslateUi

