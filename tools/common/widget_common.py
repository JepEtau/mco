# -*- coding: utf-8 -*-

import sys
sys.path.append('../scripts')

from logger import log
from pprint import pprint

from PySide6.QtCore import (
    Qt,
    Signal,
    QEvent,
    QObject,
)
from PySide6.QtGui import (
    QCursor,
    QFocusEvent,
    QEnterEvent,
)
from PySide6.QtWidgets import (
    QWidget,
)

from common.sylesheet import set_stylesheet, update_selected_widget_stylesheet

class Widget_common(QWidget):
    signal_save = Signal()
    signal_discard = Signal()
    signal_preview_options_changed = Signal()
    signal_close = Signal()

    def __init__(self, ui):
        super(Widget_common, self).__init__()
        self.setupUi(self)

        # Setup and patch ui
        self.setAutoFillBackground(True)
        self.setWindowFlags(Qt.Tool)
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setWindowModality(Qt.NonModal)
        self.setAttribute(Qt.WA_DeleteOnClose)

        # Disable focus
        self.pushButton_set_preview.setFocusPolicy(Qt.NoFocus)
        self.pushButton_save.setFocusPolicy(Qt.NoFocus)
        self.pushButton_discard.setFocusPolicy(Qt.NoFocus)
        self.pushButton_close.setFocusPolicy(Qt.NoFocus)

        # Connect signals and filter events
        self.pushButton_set_preview.toggled[bool].connect(self.event_preview_changed)
        self.pushButton_save.clicked.connect(self.event_save_modifications)
        self.pushButton_discard.clicked.connect(self.event_discard_modifications)
        self.pushButton_close.clicked.connect(self.event_close)

        # Disable push buttons
        self.pushButton_close.setEnabled(False)
        self.pushButton_save.setEnabled(False)
        self.pushButton_discard.setEnabled(False)

        # Hide the close buttons
        self.pushButton_close.hide()

        # Internal variables
        self.previous_active_widget = ''
        self.is_entered = False
        self.previous_position = None

        # Set stylesheet,  adjust size
        set_stylesheet(self)
        self.set_selected(False)
        self.adjustSize()

        # Install events for this widget
        self.installEventFilter(self)



    def closeEvent(self, event):
        self.signal_close.emit()


    def event_close(self):
        self.close()


    def get_preferences(self):
        preferences = {
            'geometry': self.geometry().getRect(),
            'widget': self.get_preview_options()
        }
        return preferences


    def set_selected(self, is_selected):
        update_selected_widget_stylesheet(self.frame, is_selected=is_selected)
        self.setFocus()


    def was_active(self):
        # Call this only one time after activation
        current_widget = self.ui.get_current_widget()
        return_value = True if current_widget == self.previous_active_widget else False
        self.previous_active_widget = current_widget
        return return_value

    def set_widget_enabled(self, enabled):
        self.blockSignals(True)
        self.frame.setEnabled(enabled)
        self.blockSignals(False)

    def get_preview_options(self):
        raise Exception("Error: override this function")


    def event_preview_changed(self, is_checked:bool=False):
        # log.info("widget preview changed to %s" % ('true' if is_checked else 'false'))
        self.signal_preview_options_changed.emit()


    def event_is_saved(self, editor):
        if editor == self.objectName() or editor == 'all':
            log.info(f"values saved: {editor}")
            self.pushButton_save.setEnabled(False)
            self.pushButton_discard.setEnabled(False)


    def event_discard_modifications(self):
        log.info("discard modifications")
        self.pushButton_save.setEnabled(False)
        self.pushButton_discard.setEnabled(False)
        self.signal_discard.emit()


    def event_save_modifications(self):
        if self.pushButton_save.isEnabled():
            self.pushButton_save.setEnabled(False)
            self.signal_save.emit()
        else:
            log.info("cannot save, reason: button is disabled")


    def keyPressEvent(self, event):
        if self.event_key_pressed(event):
            event.accept()
            return True
        # return self.ui.keyPressEvent(event)
        return False


    def event_key_pressed(self, event):
        return False


    def keyReleaseEvent(self, event):
        if self.event_key_released(event):
            event.accept()
            return True
        # return self.ui.keyReleaseEvent(event)
        return False


    # def event_key_released(self, event):
    #     return False


    def changeEvent(self, event: QEvent) -> None:
        # print("* widget_%s: QEvent.changeEvent" % (self.objectName()), event.type())
        if event.type() == QEvent.ActivationChange:
            if self.is_entered:
                # print("   changeEvent: %s: widget_common: entered, window state:" % (self.objectName()), self.windowState())
                if self.isActiveWindow():
                    self.previous_active_widget = self.ui.get_current_widget()
                    # print("* widget_%s: QEvent.WindowStateChange, previous widget=%s" % (self.objectName(), self.previous_active_widget))
                    self.ui.set_current_editor(self.objectName())
                    event.accept()
                    return True
            # else:
            #     print("   changeEvent: %s: widget_common: leaved, window state:" % (self.objectName()), self.windowState())
        return super().changeEvent(event)


    def mousePressEvent(self, event):
        self.previous_position = QCursor().pos()


    def mouseMoveEvent(self, event):
        if self.previous_position is not None:
            cursor_position = QCursor().pos()
            delta = cursor_position - self.previous_position
            self.move(self.pos() + delta)
            self.previous_position = cursor_position



    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        # print("  * eventFilter: widget_%s: " % (self.objectName()), event.type())
        if event.type() == QEvent.Enter:
            # print("         QEvent.Enter")
            self.is_entered = True
            return True
        elif event.type() == QEvent.Leave:
            # print("         QEvent.Leave")
            self.is_entered = False
            return True
        return super().eventFilter(watched, event)

    def enter(self):
        self.is_entered = True