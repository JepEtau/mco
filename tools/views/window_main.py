# -*- coding: utf-8 -*-
import platform
import sys

sys.path.append('scripts')
from utils.pretty_print import *

from functools import partial
import gc
import time
import os
import numpy as np

from pprint import pprint
from logger import log

from PySide6.QtCore import (
    QPoint,
    QSize,
    Qt,
    Signal,
    QEvent,
    QObject,
)
from PySide6.QtGui import (
    QColor,
    QImage,
    QPen,
    QPainter,
    QKeyEvent,
    QWheelEvent,
)
from PySide6.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QSizePolicy,
)

from views.window_common import (
    Window_common,
    PAINTER_MARGIN_LEFT,
    PAINTER_MARGIN_TOP,
)
from filters.python_geometry import IMG_BORDER_HIGH_RES
from filters.utils import (
    FINAL_FRAME_HEIGHT,
    FINAL_FRAME_WIDTH,
    get_dimensions_from_crop_values,
)
from views.widget_controls import Widget_controls
from views.widget_selection import Widget_selection
from views.widget_curves import Widget_curves
from views.widget_replace import Widget_replace
from views.widget_geometry import Widget_geometry
from views.widget_stabilize import Widget_stabilize
from views.widget_painter import Widget_painter
from views.widget_graphics_view import Widget_graphics_view

from controllers.controller import Controller_video_editor


COLOR_PART_CROP_RECT = QColor(30, 230, 30)
COLOR_CROP_RECT = QColor(230, 30, 30)
COLOR_FINAL_RECT = QColor(0, 255, 0)
COLOR_DISPLAY_RECT = QColor(255, 255, 255)
# PEN_CROP_SIZE must be equal to 1 or 2
PEN_CROP_SIZE = 1


class Window_main(Window_common):
    signal_preview_options_changed = Signal(dict)
    signal_save_and_close = Signal()


    def __init__(self, controller:Controller_video_editor):
        super(Window_main, self).__init__(self, controller)
        # Get preferences from model
        p = self.controller.get_preferences()

        # RGB Curves
        if 'curves' in self.widgets.keys():
            self.widget_curves = Widget_curves(self, self.controller)
            self.widgets['curves'] = self.widget_curves
            self.widget_curves.set_initial_options(p)
            self.widget_curves.signal_preview_options_changed.connect(partial(self.event_preview_options_changed, 'curves'))

        # Replace frames
        if 'replace' in self.widgets.keys():
            self.widget_replace = Widget_replace(self, self.controller)
            self.widgets['replace'] = self.widget_replace
            self.widget_replace.set_initial_options(p)
            self.widget_replace.signal_preview_options_changed.connect(partial(self.event_preview_options_changed, 'replace'))
            self.widget_replace.signal_frame_selected[int].connect(self.event_move_to_frame_no)

        # Geometry: crop and resize
        if 'geometry' in self.widgets.keys():
            self.widget_geometry = Widget_geometry(self, self.controller)
            self.widgets['geometry'] = self.widget_geometry
            self.widget_geometry.set_initial_options(p)
            self.widget_geometry.signal_preview_options_changed.connect(partial(self.event_preview_options_changed, 'geometry'))
            if self.display_height <= 1080:
                self.widget_geometry.signal_position_changed[str].connect(self.event_screen_position_changed)

        # Stabilize
        if 'stabilize' in self.widgets.keys():
            self.widget_stabilize = Widget_stabilize(self, self.controller)
            self.widgets['stabilize'] = self.widget_stabilize
            self.widget_stabilize.set_initial_options(p)
            self.widget_stabilize.signal_preview_options_changed.connect(partial(self.event_preview_options_changed, 'stabilize'))
            self.widget_stabilize.signal_frame_selected[int].connect(self.event_move_to_frame_no)
            self.widget_stabilize.signal_show_guidelines_changed.connect(self.event_show_guidelines_changed)
            self.widget_stabilize.signal_edition_started.connect(self.event_edition_started)
        self.show_guidelines = False

        # Player controls
        if 'controls' in self.widgets.keys():
            self.widget_controls = Widget_controls(self, self.controller)
            self.widgets['controls'] = self.widget_controls
            self.widget_controls.set_initial_options(p)
            self.widget_controls.signal_button_pushed[str].connect(self.event_control_button_pressed)
            self.widget_controls.signal_slider_moved[int].connect(self.event_move_to_frame_index)
            self.widget_controls.signal_preview_options_changed.connect(partial(self.event_preview_options_changed, 'controls'))

        # Selection of episode/part/shot
        self.widget_selection = Widget_selection(self, self.controller)
        self.widgets['selection'] = self.widget_selection
        self.widget_selection.refresh_browsing_folder(self.controller.get_available_episode_and_parts())
        self.widget_selection.signal_selection_changed[dict].connect(self.event_selection_changed)
        self.widget_selection.set_initial_options(p)
        self.widget_selection.widget_app_controls.signal_action[str].connect(self.event_editor_action)
        self.widget_selection.signal_selected_shots_changed[dict].connect(self.event_selected_shots_changed)
        self.widget_selection.signal_widget_selected[str].connect(self.set_current_widget)

        # Controller
        self.controller.signal_ready_to_play[dict].connect(self.event_ready_to_play)
        self.controller.signal_reload_frame.connect(self.event_reload_frame)
        self.controller.signal_close.connect(self.event_close_without_saving)
        self.controller.signal_preview_options_consolidated.connect(self.event_preview_options_consolidated)

        # Connect signals
        for w in self.widgets.values():
            w.signal_close.connect(self.event_editor_action)
            w.signal_widget_selected[str].connect(self.set_current_widget)

        # Qpainter widget
        self.widget_window_main = QWidget(self)
        self.layout_window = QVBoxLayout(self.widget_window_main)
        self.layout_window.setSpacing(0)
        self.layout_window.setObjectName(u"layout_window")
        self.layout_window.setContentsMargins(PAINTER_MARGIN_LEFT, PAINTER_MARGIN_TOP, 0, 0)
        # self.widget_painter = Widget_painter(self.widget_window_main, self)

        self.widget_painter = Widget_graphics_view(self.widget_window_main, self)


        # sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # sizePolicy.setHorizontalStretch(0)
        # sizePolicy.setVerticalStretch(0)
        # sizePolicy.setHeightForWidth(self.widget_painter.sizePolicy().hasHeightForWidth())
        # self.widget_painter.setSizePolicy(sizePolicy)
        # self.widget_painter.setMinimumSize(QSize(800, 600))

        self.layout_window.addWidget(self.widget_painter)
        self.setCentralWidget(self.widget_window_main)


        # Set initial values
        self.is_repainting = False
        self.current_entered_widget = ''

        # user preferences
        self.set_initial_options(p)

        for w in self.widgets.values():
            w.blockSignals(True)
            w.hide()
            w.blockSignals(False)
        self.widget_selection.hide()
        self.hide()

        self.installEventFilter(self)



    def show_all(self):
        # print_lightcyan(f"show_all")
        self.previous_state = self.windowState()
        self.show()
        for w in self.widgets.values():
            # print(f"show {w.objectName()}")
            w.blockSignals(True)
            w.show()
            # w.activateWindow()
            w.raise_()
            w.blockSignals(False)

    def event_edition_started(self):
        self.widget_selection.edition_started(True)


    def changeEvent(self, event: QEvent) -> None:
        # print_lightgreen(f"window_main: changeEvent {event.type()}")
        if event.type() == QEvent.ActivationChange:
    #         print("* QEvent.ActivationChange", flush=True)
            print(f"changeEvent: window state:", self.windowState())
            print(f"\tis active: {self.isActiveWindow()}")
            if self.isActiveWindow():
                self.show_all()
    #         # print("\t is active? ", self.isActiveWindow(), flush=True)
    #         if self.previous_state != self.windowState():

    #             if self.windowState() == Qt.WindowState().WindowNoState:
    #                 print("\tWindowNoState -> show fullscreen")
    #                 self.setWindowState(Qt.WindowActive)
    #                 # self.show_fullscreen()
    #                 # print("-------------------------------------")
    #                 self.previous_state = self.windowState()
    #                 event.accept()
    #                 return True

    #             if self.windowState() & Qt.WindowState().WindowActive:
    #                 print("\tWindowMinimized -> show fullscreen")
    #                 self.setWindowState(Qt.WindowActive)
    #                 # self.show_fullscreen()
    #                 # print("-------------------------------------")
    #                 self.previous_state = self.windowState()
    #                 event.accept()
    #                 return True

    #             if (self.windowState() & Qt.WindowState().WindowMinimized
    #             and not self.isActiveWindow()):
    #                 print("\tWindowMinimized -> show fullscreen")
    #                 self.setWindowState(Qt.WindowActive)
    #                 # self.show_fullscreen()
    #                 # print("-------------------------------------")
    #                 self.previous_state = self.windowState()
    #                 event.accept()
    #                 return True

        return super().changeEvent(event)


    def set_current_widget(self, current_widget):
        # print_yellow(f"set current widget: {current_widget}")
        # Set the new current widget
        self.current_widget = current_widget

        for e, w in self.widgets.items():
            if self.current_widget != e:
                # change style of the widget
                w.leave_widget()
                try:
                    w.set_activate_state(False)
                except:
                    pass

        for e, w in self.widgets.items():
            if self.current_widget == e:
                w.activateWindow()
                # Change style of the widget
                w.activate_widget()
                break
        # print_yellow(f"set current widget: done")

    def is_widget_active(self, widget_name):
        # Indicates if this widget is currently used to modify something
        return True if self.current_widget == widget_name else False


    def event_widget_entered(self, widget_name):
        # Usefull to save without selecting widget
        self.current_entered_widget = widget_name


    def event_widget_leaved(self, widget_name):
        if widget_name == self.current_entered_widget:
            self.current_entered_widget = ''





    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        # print("* eventFilter: widget_%s: " % (self.objectName()), event.type())

        # Filter press/release events
        if event.type() == QEvent.Type.KeyPress:
            print(f"keypress: catched in main window {event.key()}")
            print(f"\tforward to [{self.current_widget}]")
            if self.current_widget != '':
                isAccepted = self.widgets[self.current_widget].event_key_pressed(event)
            else:
                isAccepted = False

            if not isAccepted:
                print_orange(f"event not acepted by widget: {event.key()}, send to main")
                isAccepted = self.event_key_pressed(event)

            if isAccepted:
                print_green(f"event accepted")
                event.accept()
                return True
            else:
                print_orange(f"event not acepted: {event.key()}, send to super")
                # return super().keyPressEvent(event)

        # Filter press/release events
        if event.type() == QEvent.Type.KeyRelease:
            print(f"keyrelease: catched in main window {event.key()}")
            print(f"\tforward to [{self.current_widget}]")
            if self.current_widget != '':
                isAccepted = self.widgets[self.current_widget].event_key_released(event)
            else:
                isAccepted = False

            if not isAccepted:
                print_orange(f"event not acepted by widget: {event.key()}, send to main")
                isAccepted = self.event_key_released(event)

            if isAccepted:
                print_green(f"event accepted")
                event.accept()
                return True
            else:
                print_orange(f"event not acepted: {event.key()}, send to super")
                # return super().keyReleaseEvent(event)


        # Filter wheel events
        elif event.type() == QEvent.Type.Wheel:
            # print(f"wheel event: catched in main window")
            # print(f"\tforward to [{self.current_widget}]")
            if self.current_widget != '':
                isAccepted = self.widgets[self.current_widget].event_wheel(event)
            else:
                isAccepted = False

            if not isAccepted:
                # print_orange(f"wheel: event not acepted by widget: send to control")
                isAccepted = self.widget_controls.event_wheel(event)

            if isAccepted:
                # print_green(f"\twheel: event accepted")
                event.accept()
                return True
            else:
                print_orange(f"\twheel: event not acepted, send to super")
                # return super().wheelEvent(event)


        # elif platform.system() != "Windows":
        elif event.type() == QEvent.Type.FocusIn:
            print("main focus in")
            self.activateWindow()
            event.accept()
            return True

        return super().eventFilter(watched, event)






    def get_preview_options(self):
        log.info("get preview options")
        preview_options = dict()
        for e, w in self.widgets.items():
            preview_options.update({e: w.get_preview_options()})
        return preview_options


    def event_preview_options_consolidated(self, new_preview_settings):
        # log.info("preview options have been consolidated, refresh widgets")
        self.widget_replace.refresh_preview_options(new_preview_settings)
        self.widget_stabilize.refresh_preview_options(new_preview_settings)
        self.widget_geometry.refresh_preview_options(new_preview_settings)



    def flush_image(self):
        log.info("flush image")
        del self.image
        self.image = None
        gc.collect()

        self.is_grabbing_split_line = False



    def display_frame(self, frame: dict):
        # now = time.time()
        # print_lightcyan("display frame: %s" % (frame['filepath']))
        if frame is None or not os.path.exists(frame['filepath']):
            self.flush_image()
        else:
            if self.image is not None:
                del self.image
                self.image = None

            # Get preview options
            options = self.controller.get_preview_options()
            if options is None:
                sys.exit("preview options are not set!")

            # Set an internal image object
            self.image = {
                'cache': frame['cache'],
                'geometry': frame['geometry'],
                'geometry_values': frame['geometry_values'],
                'stabilize': frame['stabilize'],
                'curves': {
                    'lut': None
                },
                'preview_options': options,
                'origin': [0, 0],
            }

            if options['stabilize']['enabled'] and frame['stabilize']['enable']:
                self.image['cache_initial'] = frame['cache_deshake']
            else:
                self.image['cache_initial'] = frame['cache_initial']


            # Update info in the other widgets
            for e, w in self.widgets.items():
                w.refresh_values(frame)

        self.widget_painter.show_image(self.image)
        # self.repaint()
        # print("\t\t%f" % int(1000 * (time.time() - now)))


    def event_show_guidelines_changed(self):
        self.widget_painter.repaint_frame()


    def get_rgb_value(self, cursor_position:QPoint):
        if self.image is None:
            # No frame loaded
            return

        x, y = cursor_position.x(), cursor_position.y()

        pick_initial_value = True
        if pick_initial_value:
            try:
                # print("get_color from (%d, %d)" % (xr, yr))
                h, w, c = self.image['cache'].shape
                if (0 <= x < self.width()
                    and 0 <= y < self.height()
                    and x < w and y < h):

                    # TODO: correct this!
                    bgr = self.image['cache_initial'][y-self.image['origin'][1], x-self.image['origin'][0]]
                    # print("\t(%d, %d) -> (%d, %d, %d)" % (
                    #     xr-self.image['origin'][0],
                    #     yr-self.image['origin'][1],
                    #     bgr[2], bgr[1], bgr[0]))

                    self.widget_curves.set_color_values(bgr)
                    self.widget_painter.setCursor(Qt.CursorShape.CrossCursor)
                else:
                    self.widget_curves.set_color_values(None)
                    self.widget_painter.setCursor(Qt.CursorShape.ArrowCursor)
            except:
                # print("error!")
                pass
        else:
            try:
                # print("get_color from (%d, %d)" % (xr, yr))
                h, w, c = self.image['cache'].shape
                if (0 <= x < self.width()
                    and 0 <= y < self.height()
                    and x < w and y < h):

                    bgr = self.image['cache'][y-self.image['origin'][1],
                                            x-self.image['origin'][0]]

                    self.widget_curves.set_color_values(bgr)
                    self.widget_painter.setCursor(Qt.CursorShape.CrossCursor)
                else:
                    self.widget_curves.set_color_values(None)
                    self.widget_painter.setCursor(Qt.CursorShape.ArrowCursor)
            except:
                # print("error!")
                pass


    def mousePressEvent(self, event):
        cursor_position = event.position().toPoint() - QPoint(PAINTER_MARGIN_LEFT, PAINTER_MARGIN_TOP)
        self.widget_stabilize.update_coordinates(cursor_position)

        if (self.image is not None
        and self.image['cache_initial'] is not None):
            if self.current_widget == 'curves':
                if self.widget_curves.grab_split_line(cursor_position):
                    self.widget_painter.setCursor(Qt.CursorShape.SplitHCursor)
                else:
                    print("\t-> cache_initial: ", self.image['cache_initial'].shape)
                    self.get_rgb_value(cursor_position=cursor_position)
                event.accept()
                return True
            elif self.current_widget == 'stabilize':
                line = self.widget_stabilize.guidelines.grab(cursor_position=cursor_position)
                if line == 'vertical':
                    self.widget_painter.setCursor(Qt.CursorShape.SplitHCursor)
                elif line == 'horizontal':
                    self.widget_painter.setCursor(Qt.CursorShape.SplitVCursor)
                elif line == "both":
                    self.widget_painter.setCursor(Qt.CursorShape.SizeAllCursor)
                else:
                    self.get_rgb_value(cursor_position=cursor_position)
                if line is not None:
                    self.widget_painter.repaint_frame()
                event.accept()
                return True
            else:
                print("\t-> cache_initial: ", self.image['cache_initial'].shape)
                self.get_rgb_value(cursor_position=cursor_position)
            event.accept()
        else:
            event.ignore()


    def mouseMoveEvent(self, event):
        cursor_position = event.position().toPoint() - QPoint(PAINTER_MARGIN_LEFT, PAINTER_MARGIN_TOP)
        self.widget_stabilize.update_coordinates(cursor_position)
        if self.current_widget == 'stabilize':
            line = self.widget_stabilize.guidelines.move(cursor_position)
            if line is None:
                self.get_rgb_value(cursor_position)
                event.ignore()
                return
            if line == 'vertical':
                self.widget_painter.setCursor(Qt.CursorShape.SplitHCursor)
            elif line == 'horizontal':
                self.widget_painter.setCursor(Qt.CursorShape.SplitVCursor)
            elif line == "both":
                self.widget_painter.setCursor(Qt.CursorShape.SizeAllCursor)
            event.accept()
            if line is not None:
                self.widget_painter.repaint_frame()


        elif self.current_widget == 'curves':
            if self.widget_curves.move_split_line(cursor_position):
                self.widget_painter.setCursor(Qt.CursorShape.SplitHCursor)
                event.accept()
                self.event_reload_frame()
            else:
                self.get_rgb_value(cursor_position)
                event.ignore()



    def mouseMoved(self, x, y):
        if self.current_widget == 'curves':
            if self.widget_curves.split_line_moved(x, self.mouse_grabX):
                self.widget_painter.setCursor(Qt.CursorShape.SplitHCursor)
                self.event_reload_frame()

        elif self.current_widget == 'stabilize':
            line = self.widget_stabilize.guidelines.moved(x, self.mouse_grabX, y, self.mouse_grabY)
            if line == 'vertical':
                self.widget_painter.setCursor(Qt.CursorShape.SplitHCursor)
            elif line == 'horizontal':
                self.widget_painter.setCursor(Qt.CursorShape.SplitVCursor)
            elif line == "both":
                self.widget_painter.setCursor(Qt.CursorShape.SizeAllCursor)
            else:
                self.get_rgb_value(x, y)
            if line is not None:
                self.widget_painter.repaint_frame()


    def mouseReleaseEvent(self, event):
        self.widget_painter.setCursor(Qt.ArrowCursor)
        self.widget_curves.split_line_released(event.x())
        self.widget_stabilize.guidelines.released(event.x(), event.y())
        self.widget_painter.repaint_frame()



    def event_wheel(self, event: QWheelEvent) -> bool:
        is_accepted = False
        if self.current_widget == 'geometry':
            is_accepted = self.widget_geometry.event_wheel(event)

        if not is_accepted:
            is_accepted = self.widget_controls.event_wheel(event)

        return is_accepted



    def event_key_released(self, event:QKeyEvent) -> bool:
        key = event.key()
        modifiers = event.modifiers()
        if self.current_widget != '':
            return self.widgets[self.current_widget].event_key_released(event)


    def event_key_pressed(self, event:QKeyEvent) -> bool:
    #     # log.info("key event in main window")
        key = event.key()
        modifiers = event.modifiers()
        print_lightgreen(f"main.event_key_pressed: {key}, modifiers=", modifiers)


        # Save currently enterd widget
        if self.current_entered_widget !=  '':
            if modifiers & Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_S:
                    return self.widgets[self.current_widget].event_key_pressed(event)


        # Controls
        if key == Qt.Key.Key_Space:
            log.info("Space key event detected")
            self.widget_controls.toggle_play_pause()
            return True
        if key in [Qt.Key.Key_Home, Qt.Key.Key_End]:
            return self.widget_controls.event_key_pressed(event)


        # Replace
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            if key in [Qt.Key.Key_C, Qt.Key.Key_V]:
                return self.widget_replace.event_key_pressed(event)



        if self.current_widget != '':
            return self.widgets[self.current_widget].event_key_pressed(event)

    #     if modifiers & Qt.AltModifier:
    #         if key == Qt.Key_F4:
    #             event.accept()
    #             return True
    #         elif key == Qt.Key_F9:
    #             self.showMinimized()
    #             event.accept()
    #             return True
    #         elif key == Qt.Key_S:
    #             self.switch_display_side()
    #             event.accept()
    #             return True
    #     else:
    #         if key == Qt.Key_F5:
    #             log.info("Reload")
    #             self.widget_selection.event_episode_changed()
    #             event.accept()
    #             return True

    #     # for e, w in self.widgets.items():
    #     #     if self.current_widget == e:
    #     #         is_accepted = w.event_key_pressed(event)
    #     #         if is_accepted:
    #     #             event.accept()
    #     #             return True
    #     print(f"forward to widget {self.current_widget}")
    #     return self.widgets[self.current_widget].event_key_pressed(event)


        return False

