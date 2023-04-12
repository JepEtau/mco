# -*- coding: utf-8 -*-

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGroupBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QScrollBar,
    QSpinBox,
    QTableWidget,
)

# Blue color: rgb(51, 102, 204)
# icons:
#   blue: 3366CC
#   grey: 3C3C3C
#   purple:

def update_selected_widget_stylesheet(widget, is_selected:bool):
    if is_selected:
        widget.setStyleSheet("""
            QFrame#frame {
                border: 1px solid rgb(51, 102, 204);
            }
        """)
    else:
        widget.setStyleSheet("""
            QFrame#frame {
                border: 1px solid rgb(35, 35, 35);
            }
        """)


def set_widget_stylesheet(widget, widget_type=''):
    if type(widget) is QCheckBox:
        widget.setStyleSheet("""
            QCheckBox {
                background-color: rgb(35, 35, 35);
                color: rgb(220, 220, 220);
            }
            QCheckBox::indicator {
                width: 13px;
                height: 13px;
                background-color: rgb(60, 60, 60);
                border: 1px;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: rgb(170, 170, 170);
            }
            QCheckBox::indicator:indeterminate {
                /* for debug: correct this */
                background-color: rgb(100, 100, 100);
            }
        """)
    elif type(widget) is QDoubleSpinBox:
        widget.setStyleSheet("""
            QDoubleSpinBox {
                background-color: rgb(35, 35, 35);
                color: rgb(220, 220, 220);
            }
        """)


    elif type(widget) is QMessageBox:
        widget.setStyleSheet("""
            QMessageBox {
                background-color: rgb(35, 35, 35);
                color: rgb(220, 220, 220);
            }
            QLabel {
                background-color: rgb(35, 35, 35);
                color: rgb(220, 220, 220);
            }
            QPushButton {
                background-color: rgb(60, 60, 60);
                color: rgb(220, 220, 220);
            }
        """)

    elif type(widget) is QLabel:
        if widget_type == 'message':
            # Customized label for message
            widget.setStyleSheet("""
                QLabel {
                    /* color: rgb(220, 220, 220);*/
                    color: rgb(51, 102, 204);
                    /* font-weight:bold;*/
                }
            """)
        else:
            # Customized label with border
            widget.setStyleSheet("""
                QLabel {
                    background-color: rgb(35, 35, 35);
                    border: 1px solid rgb(60, 60, 60);
                    color: rgb(220, 220, 220);
                }
            """)



def set_stylesheet(widget):
    # Widget
    widget.setStyleSheet("""QWidget {
        background-color: rgb(35, 35, 35);
        border-color: rgb(192, 192, 192);
        font-size: 13px;
        }
    """)


    # QFrame
    for w in widget.findChildren(QFrame, options=Qt.FindChildrenRecursively):
        w.setStyleSheet("""QFrame {
            border-color: rgb(255, 255, 255);
            color: rgb(220, 220, 220);
            }
        """)

    # QGroupBox
    for w in widget.findChildren(QGroupBox, options=Qt.FindChildrenRecursively):
        w.setStyleSheet("""
            QGroupBox {
                border: 1px solid rgb(60, 60, 60);
                color: rgb(220, 220, 220);
                margin-top: 9px;  /*leave space at the top for the title */
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 7px;
                padding: 0px 3px;
            }
        """)

    # QLabel
    for w in widget.findChildren(QLabel, options=Qt.FindChildrenRecursively):
        w.setStyleSheet("""
            QLabel {
                background-color: rgb(35, 35, 35);
                color: rgb(220, 220, 220);
            }
        """)

    # QLineEdit
    for w in widget.findChildren(QLineEdit, options=Qt.FindChildrenRecursively):
        w.setStyleSheet("""QLineEdit {
            background-color: rgb(60, 60, 60);
            color: rgb(220, 220, 220);
            border: 1px solid rgb(60, 60, 60);
            }
        """)

    # QCheckBox
    for w in widget.findChildren(QCheckBox, options=Qt.FindChildrenRecursively):
        set_widget_stylesheet(w)


    # QListWidget
    for w in widget.findChildren(QListWidget, options=Qt.FindChildrenRecursively):
        w.setStyleSheet("""
            QListWidget {
                background-color: rgb(60, 60, 60);
                color: rgb(220, 220, 220);
                border: 1px solid rgb(80, 80, 80);
            }
            QListWidget::item {
                background-color: rgb(60, 60, 60);
                color: rgb(220, 220, 220);
            }
            QListWidget::item:selected {
                background-color: rgb(51, 102, 204);
                color: rgb(220, 220, 220);
            }
        """)


    # QPushButton
    for w in widget.findChildren(QPushButton, options=Qt.FindChildrenRecursively):
        w.setStyleSheet("""
            QPushButton {
                background-color: rgb(35, 35, 35);
                color: rgb(220, 220, 220);
            }
        """)


    # QScrollBar
    for w in widget.findChildren(QScrollBar, options=Qt.FindChildrenRecursively):
        w.setStyleSheet("""
            QScrollBar:vertical {
                background-color: rgb(35, 35, 35);
                color: rgb(220, 220, 220);
                margin: 1px;
                border-color: rgb(15, 15, 15);
                border-radius: 3px;
            }

            QScrollBar::handle:vertical {
                background-color: rgb(50, 50, 50);
                border: 1px solid rgb(70, 70, 70);
                border-radius: 3px;
            }

            QScrollBar::handle:vertical:hover {
                background-color: rgb(128, 128, 128);
                border: 1px solid rgb(140, 140, 140);
            }

            QScrollBar::add-line:vertical {
                height: 0px;
            }

            QScrollBar::sub-line:vertical {
                height: 0px;
            }

            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                height: 0px;
                background: none;
            }
        """)


    # QComboBox
    for w in widget.findChildren(QComboBox, options=Qt.FindChildrenRecursively):
        w.setStyleSheet("""
            QComboBox {
                background-color: rgb(60, 60, 60);
                color: rgb(220, 220, 220);
                border-radius: 3px;
                height: 23px;
            }

            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 15px;

                border-left-width: 1px;
                border-left-color: rgb(35, 35, 35);
                border-left-style: solid;           /* just a single line */
                border-top-right-radius: 3px;       /* same radius as the QComboBox */
                border-bottom-right-radius: 3px;
            }

            QComboBox::down-arrow {
                image: url(./icons/drop_down_arrow_gray.svg);
                margin: 0px;
            }

            QComboBox::down-arrow:on {
                /* shift the arrow when popup is open */
                top: 2px;
            }

            QComboBox:on {
                /* shift the text when the popup opens */
                padding-top: 1px;
                padding-left: 1px;
            }

            QAbstractItemView {
                background-color: rgb(70, 70, 70);
            }

        """)



    # QRadioButton
    for w in widget.findChildren(QRadioButton, options=Qt.FindChildrenRecursively):
        w.setStyleSheet("""
            QRadioButton {
                background-color: rgb(35, 35, 35);
                color: rgb(220, 220, 220);
            }

            QRadioButton::indicator {
                width: 7px;
                height: 7px;
                margin: 2px;
                border-radius: 6px;
            }

            QRadioButton::indicator:checked {
                background-color: rgb(170, 170, 170);
                border: 3px solid rgb(60, 60, 60);
            }

            QRadioButton::indicator:unchecked {
                background-color: rgb(60, 60, 60);
                width: 13px;
                height: 13px;
            }
        """)


    # QTableWidget
    for w in widget.findChildren(QTableWidget, options=Qt.FindChildrenRecursively):
        w.setStyleSheet("""
            QTableWidget {
                background-color: rgb(35, 35, 35);
                color: rgb(220, 220, 220);
                gridline-color: rgb(80, 80, 80);

                selection-background-color: rgb(53, 142, 198);
                selection-color: rgb(220, 220, 220);
            }

            QHeaderView::section {
                background-color: rgb(35, 35, 35);
                color: rgb(220, 220, 220);
                gridline-color: rgb(80, 80, 80);
            }

            QTableWidget::item {
                background-color: rgb(60, 60, 60);
                color: rgb(220, 220, 220);
            }
            QTableWidget::item:selected {
                background-color: rgb(51, 102, 204);
                color: rgb(220, 220, 220);
            }

        """)


    # QDoubleSpinBox
    for w in widget.findChildren(QDoubleSpinBox, options=Qt.FindChildrenRecursively):
        w.setStyleSheet("""
            QDoubleSpinBox {
                background-color: rgb(35, 35, 35);
                color: rgb(220, 220, 220);
            }
        """)

    # QSpinBox
    for w in widget.findChildren(QSpinBox, options=Qt.FindChildrenRecursively):
        w.setStyleSheet("""
            QSpinBox {
                background-color: rgb(35, 35, 35);
                color: rgb(220, 220, 220);
            }
        """)



def set_curves_radiobutton_stylesheet(channel, w):
    if channel == 'r':
        w.setStyleSheet("""
            QRadioButton#radioButton_select_r_channel {
                background-color: rgb(35, 35, 35);
                color: red;
            }
            QRadioButton#radioButton_select_r_channel::indicator {
                width: 7px;
                height: 7px;
                margin: 2px;
                border-radius: 6px;
            }
            QRadioButton#radioButton_select_r_channel::indicator:checked {
                background-color: red;
                border: 3px solid rgb(60, 60, 60);
            }
            QRadioButton#radioButton_select_r_channel::indicator:unchecked {
                background-color: rgb(60, 60, 60);
                border: 3px solid rgb(60, 60, 60);
            }
        """)
    elif channel == 'g':
        w.setStyleSheet("""
            QRadioButton#radioButton_select_g_channel {
                background-color: rgb(35, 35, 35);
                color: green;
            }
            QRadioButton#radioButton_select_g_channel::indicator {
                width: 7px;
                height: 7px;
                margin: 2px;
                border-radius: 6px;
            }
            QRadioButton#radioButton_select_g_channel::indicator:checked {
                background-color: green;
                border: 3px solid rgb(60, 60, 60);
            }
            QRadioButton#radioButton_select_g_channel::indicator:unchecked {
                background-color: rgb(60, 60, 60);
                border: 3px solid rgb(60, 60, 60);
            }
        """)
    elif channel == 'b':
        w.setStyleSheet("""
            QRadioButton#radioButton_select_b_channel {
                background-color: rgb(35, 35, 35);
                color: blue;
            }
            QRadioButton#radioButton_select_b_channel::indicator {
                width: 7px;
                height: 7px;
                margin: 2px;
                border-radius: 6px;
            }
            QRadioButton#radioButton_select_b_channel::indicator:checked {
                background-color: blue;
                border: 3px solid rgb(60, 60, 60);
            }
            QRadioButton#radioButton_select_b_channel::indicator:unchecked {
                background-color: rgb(60, 60, 60);
                border: 3px solid rgb(60, 60, 60);
            }
        """)
    elif channel == 'm':
        w.setStyleSheet("""
            QRadioButton#radioButton_select_m_channel {
                background-color: rgb(35, 35, 35);
                color: white;
            }
            QRadioButton#radioButton_select_m_channel::indicator {
                width: 7px;
                height: 7px;
                margin: 2px;
                border-radius: 6px;
            }
            QRadioButton#radioButton_select_m_channel::indicator:checked {
                background-color: white;
                border: 3px solid rgb(60, 60, 60);
            }
            QRadioButton#radioButton_select_m_channel::indicator:unchecked {
                background-color: rgb(60, 60, 60);
                border: 3px solid rgb(60, 60, 60);
            }
        """)
