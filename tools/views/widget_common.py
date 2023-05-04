# -*- coding: utf-8 -*-
import platform
import sys

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
    QKeyEvent,
    QWheelEvent,
)
from PySide6.QtWidgets import (
    QWidget,
)
from utils.pretty_print import *

from utils.stylesheet import set_stylesheet, update_selected_widget_stylesheet

class Widget_common(QWidget):
    signal_widget_selected = Signal(str)
    signal_save = Signal()
    signal_discard = Signal()
    signal_preview_options_changed = Signal()
    signal_close = Signal()
    signal_edition_started = Signal()

    def __init__(self, parent):
        super(Widget_common, self).__init__()
        self.setupUi(self)

        # Setup and patch ui
        self.setAutoFillBackground(True)
        self.setWindowFlags(Qt.Tool)
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setWindowModality(Qt.NonModal)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

        self.pushButton_set_preview.setFocusPolicy(Qt.NoFocus)
        self.pushButton_set_preview.toggled[bool].connect(self.event_set_preview_toggled)

        self.pushButton_save.setFocusPolicy(Qt.NoFocus)
        self.pushButton_save.clicked.connect(self.event_save_modifications)
        self.pushButton_save.setEnabled(False)

        self.pushButton_discard.setFocusPolicy(Qt.NoFocus)
        self.pushButton_discard.clicked.connect(self.event_discard_modifications)
        self.pushButton_discard.setEnabled(False)

        self.pushButton_close.setFocusPolicy(Qt.NoFocus)
        self.pushButton_close.clicked.connect(self.event_close)
        self.pushButton_close.setEnabled(False)
        self.pushButton_close.hide()


        # Internal variables
        self.previous_active_widget = ''
        self.previous_position = None
        self.__parent = parent

        self.set_activate_state(False)

        # # Set stylesheet,  adjust size
        # set_stylesheet(self)
        # self.set_selected(False)
        # self.adjustSize()

        # # Install events for this widget
        # self.installEventFilter(self)

    def set_activate_state(self, state:bool):
        self.__is_activated = state

    def is_activated(self):
        return self.__is_activated

    def leave_widget(self):
        update_selected_widget_stylesheet(self.frame, is_selected=False)
        # self.repaint()


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


    def activate_widget(self):
        update_selected_widget_stylesheet(self.frame, is_selected=True)
        self.setFocus()

    def set_selected(self, is_selected):
        update_selected_widget_stylesheet(self.frame, is_selected=is_selected)
        self.setFocus()


    def was_active(self):
        # Call this only one time after activation

        current_widget = self.ui.get_current_widget()
        if self.previous_active_widget == current_widget:
            # Did not change editor
            return_value = True
        else:
            return_value = False

        self.previous_active_widget = current_widget
        return return_value


    def set_widget_enabled(self, enabled):
        self.blockSignals(True)
        self.frame.setEnabled(enabled)
        self.blockSignals(False)

    def get_preview_options(self):
        raise Exception("Error: override this function")


    def event_set_preview_toggled(self, is_checked:bool=False):
        log.info(f"widget preview changed to {is_checked}")
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
            log.info(f"save widget_{self.objectName()}")
            self.pushButton_save.setEnabled(False)
            self.signal_save.emit()
        else:
            log.info("cannot save, reason: button is disabled")

    # def keyPressEvent(self, event: QKeyEvent):
    #     key = event.key()
    #     if key == Qt.Key.Key_Space:
    #         return self.__parent.keyPressEvent(event)
    #     return super().keyPressEvent(event)




    # def event_key_released(self, event):
    #     return False


    # def changeEvent(self, event: QEvent) -> None:
    #     # print("* widget_%s: QEvent.changeEvent" % (self.objectName()), event.type())
    #     if event.type() == QEvent.ActivationChange:
    #         if self.is_entered:
    #             # print("   changeEvent: %s: widget_common: entered, window state:" % (self.objectName()), self.windowState())
    #             if self.isActiveWindow():
    #                 self.previous_active_widget = self.ui.get_current_widget()
    #                 # print("* widget_%s: QEvent.WindowStateChange, previous widget=%s" % (self.objectName(), self.previous_active_widget))

    #                 event.accept()
    #                 return True
    #         # else:
    #         #     print("   changeEvent: %s: widget_common: leaved, window state:" % (self.objectName()), self.windowState())
    #     return super().changeEvent(event)


    def mousePressEvent(self, event):
        self.previous_position = QCursor().pos()
        # if platform.system() == "Windows":
        if not self.is_activated():
            self.set_activate_state(True)
            self.signal_widget_selected.emit(self.objectName())


    def mouseMoveEvent(self, event):
        if self.previous_position is not None:
            cursor_position = QCursor().pos()
            delta = cursor_position - self.previous_position
            self.move(self.pos() + delta)
            self.previous_position = cursor_position

    def event_key_pressed(self, event) -> bool:
        print_lightgreen("\tDefault keypres fct")
        return False


    def event_key_released(self, event:QKeyEvent) -> bool:
        return False


    def event_wheel(self, event: QWheelEvent) -> bool:
        print_lightgreen("\tDefault wheel fct")
        return False


    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        # print(f"  * eventFilter: widget_{self.objectName()}:", event.type())
        # if event.type() == QEvent.Type.KeyPress:
        #     key = event.key()
        #     if key == Qt.Key.Key_Space:
        #         return self.__parent.keyPressEvent(event)
        if event.type() == QEvent.Type.KeyPress:
            print_lightcyan(f"eventFilter: widget_{self.objectName()}: keypress {event.key()}")
            if self.event_key_pressed(event):
                print(f"\taccepted")
                event.accept()
                return True
            else:
                print(f"\tsend to parent")
                return self.__parent.event_key_pressed(event)

        elif event.type() == QEvent.Type.KeyRelease:
            print_lightcyan(f"eventFilter: widget_{self.objectName()}: keyrelease {event.key()}")
            if self.event_key_released(event):
                print(f"\taccepted")
                event.accept()
                return True
            else:
                print(f"\tsend to parent")
                return self.__parent.event_key_released(event)

        elif event.type() == QEvent.Type.Wheel:
            print_lightcyan(f"eventFilter: widget_{self.objectName()}: wheel ")
            if self.event_wheel(event):
                print(f"\taccepted")
                event.accept()
                return True
            else:
                print(f"\tsend to parent")
                return self.__parent.event_wheel(event)


        elif watched.objectName() == self.objectName():
            # print_yellow(f"eventFilter: widget_{self.objectName()}: {event.type()}, {watched.objectName()}")

            # print(watched)
            # if platform.system() != "Windows":
            #     if event.type() == QEvent.Type.FocusIn:
            #         # print_lightcyan(f"eventFilter: widget_{self.objectName()}: FocusIn")
            #         self.signal_widget_selected.emit(self.objectName())
            #         event.accept()
            #         return True
            # #     # print("         QEvent.Enter")
            # else:
            if event.type() == QEvent.Type.Enter:
                # print_lightcyan(f"eventFilter: widget_{self.objectName()}: Enter")
                self.__parent.event_widget_entered(self.objectName())
                event.accept()
                return True
            elif event.type() == QEvent.Type.Leave:
                # print_lightcyan(f"eventFilter: widget_{self.objectName()}: Leave")
                self.__parent.event_widget_leaved(self.objectName())
                event.accept()
                return True

            # elif event.type() == QEvent.Type.WindowActivate:
            #     # print_lightgreen(f"eventFilter: widget_{self.objectName()}: ActivationChange")
            #     if not self.is_activated():
            #         self.set_activate_state(True)
            #         print_lightgreen(f"eventFilter: widget_{self.objectName()}: activate")
            #         self.signal_widget_selected.emit(self.objectName())
            #         event.accept()
            #         return True

            # elif event.type() == QEvent.Type.WindowDeactivate:
            #     self.set_activate_state(False)
            # else:
            #     print_lightgreen(f"eventFilter: widget_{self.objectName()}: {event.type()}, {watched.objectName()}")

                    # print("         QEvent.Leave")
        #     self.is_entered = False

            # eventFilter: widget_geometry: 24, geometry    WindowActivate
            # eventFilter: widget_geometry: 99, geometry
            # eventFilter: widget_geometry: 77, geometry
            # eventFilter: widget_geometry: 12, geometry
            # eventFilter: widget_geometry: 12, geometry
            # eventFilter: widget_geometry: 2, geometry
            # eventFilter: widget_geometry: 3, geometry
            # eventFilter: widget_geometry: 25, geometry
            # eventFilter: widget_geometry: 99, geometry
            # eventFilter: widget_geometry: 77, geometry
            # eventFilter: widget_geometry: 12, geometry
            # eventFilter: widget_geometry: 12, geometry




        # if event.type() == QEvent.ActivationChange:
        #     # update_selected_widget_stylesheet(self.frame, is_selected=True)
        #     # print_purple(f"{self.objectName()}: Enter")
        #     # self.raise_()
        #     self.signal_widget_selected.emit(self.objectName())
        #     event.accept()
        #     return True

        return super().eventFilter(watched, event)


    # def changeEvent(self, event: QEvent) -> None:
    #     # print("* widget_%s: QEvent.changeEvent" % (self.objectName()), event.type())
    #     if event.type() == QEvent.ActivationChange:
    #         if self.is_entered:
    #             # print("   changeEvent: %s: widget_common: entered, window state:" % (self.objectName()), self.windowState())
    #             if self.isActiveWindow():
    #                 self.previous_active_widget = self.ui.get_current_widget()
    #                 # print("* widget_%s: QEvent.WindowStateChange, previous widget=%s" % (self.objectName(), self.previous_active_widget))

    #                 event.accept()
    #                 return True
    #         # else:
    #         #     print("   changeEvent: %s: widget_common: leaved, window state:" % (self.objectName()), self.windowState())
    #     return super().changeEvent(event)
