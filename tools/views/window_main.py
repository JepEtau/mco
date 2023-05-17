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
            self.widget_curves.set_main_window_margin(PAINTER_MARGIN_LEFT)
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
            print(f"wheel event: catched in main window")
            print(f"\tforward to [{self.current_widget}]")
            if self.current_widget != '':
                isAccepted = self.widgets[self.current_widget].event_wheel(event)
            else:
                isAccepted = False

            if not isAccepted:
                print_orange(f"wheel: event not acepted by widget: send to control")
                isAccepted = self.widget_controls.event_wheel(event)

            if isAccepted:
                print_green(f"\twheel: event accepted")
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


    def get_rgb_value(self, xr, yr):
        if self.image is None:
            # No frame loaded
            return

        pick_initial_value = True
        if pick_initial_value:
            try:
                # print("get_color from (%d, %d)" % (xr, yr))
                h, w, c = self.image['cache'].shape
                if (PAINTER_MARGIN_LEFT <= xr < self.width()+PAINTER_MARGIN_LEFT
                    and PAINTER_MARGIN_TOP <= yr < self.height()+PAINTER_MARGIN_TOP
                    and xr < w+PAINTER_MARGIN_LEFT and yr < h+PAINTER_MARGIN_TOP):

                    # TODO: correct this!
                    bgr = self.image['cache_initial'][yr-self.image['origin'][1], xr-self.image['origin'][0]]
                    # print("\t(%d, %d) -> (%d, %d, %d)" % (
                    #     xr-self.image['origin'][0],
                    #     yr-self.image['origin'][1],
                    #     bgr[2], bgr[1], bgr[0]))

                    self.widget_curves.set_color_values(bgr)
                    self.widget_painter.setCursor(Qt.CrossCursor)
                else:
                    self.widget_curves.set_color_values(None)
                    self.widget_painter.setCursor(Qt.ArrowCursor)
            except:
                # print("error!")
                pass
        else:
            try:
                # print("get_color from (%d, %d)" % (xr, yr))
                h, w, c = self.image['cache'].shape
                if (PAINTER_MARGIN_LEFT <= xr < self.width()+PAINTER_MARGIN_LEFT
                    and PAINTER_MARGIN_TOP <= yr < self.height()+PAINTER_MARGIN_TOP
                    and xr < w+PAINTER_MARGIN_LEFT and yr < h+PAINTER_MARGIN_TOP):

                    bgr = self.image['cache'][yr-self.image['origin'][1] + PAINTER_MARGIN_TOP,
                                            xr-self.image['origin'][0] + PAINTER_MARGIN_LEFT]

                    self.widget_curves.set_color_values(bgr)
                    self.widget_painter.setCursor(Qt.CrossCursor)
                else:
                    self.widget_curves.set_color_values(None)
                    self.widget_painter.setCursor(Qt.ArrowCursor)
            except:
                # print("error!")
                pass


    def mousePressEvent(self, event):
        x = event.x()
        y = event.y()
        self.widget_stabilize.update_coordinates(event.position().toPoint())

        if (self.image is not None
        and self.image['cache_initial'] is not None):
            if self.current_widget == 'curves':
                if self.widget_curves.grab_split_line(x):
                    self.widget_painter.setCursor(Qt.SplitHCursor)
                else:
                    print("\t-> cache_initial: ", self.image['cache_initial'].shape)
                    self.get_rgb_value(x, y)
                event.accept()
                return True
            elif self.current_widget == 'stabilize':
                line = self.widget_stabilize.guidelines.grab(x, y)
                if line == 'vertical':
                    self.widget_painter.setCursor(Qt.SplitHCursor)
                elif line == 'horizontal':
                    self.widget_painter.setCursor(Qt.SplitVCursor)
                elif line == "both":
                    self.widget_painter.setCursor(Qt.SizeAllCursor)
                else:
                    self.get_rgb_value(x, y)
                if line is not None:
                    self.widget_painter.repaint_frame()
                event.accept()
                return True
            else:
                print("\t-> cache_initial: ", self.image['cache_initial'].shape)
                self.get_rgb_value(x, y)
            event.accept()
        else:
            event.ignore()


    def mouseMoveEvent(self, event):
        x = event.x()
        y = event.y()
        self.widget_stabilize.update_coordinates(event.position().toPoint())
        if self.current_widget == 'stabilize':
            line = self.widget_stabilize.guidelines.move(x, y)
            if line is None:
                self.get_rgb_value(x, y)
                event.ignore()
                return
            if line == 'vertical':
                self.widget_painter.setCursor(Qt.SplitHCursor)
            elif line == 'horizontal':
                self.widget_painter.setCursor(Qt.SplitVCursor)
            elif line == "both":
                self.widget_painter.setCursor(Qt.SizeAllCursor)
            event.accept()
            if line is not None:
                self.widget_painter.repaint_frame()


        elif self.current_widget == 'curves':
            if self.widget_curves.move_split_line(x):
                self.widget_painter.setCursor(Qt.SplitHCursor)
                event.accept()
                self.event_reload_frame()
            else:
                self.get_rgb_value(x, y)
                event.ignore()



    def mouseMoved(self, x, y):
        if self.current_widget == 'curves':
            if self.widget_curves.split_line_moved(x, self.mouse_grabX):
                self.widget_painter.setCursor(Qt.SplitHCursor)
                self.event_reload_frame()

        elif self.current_widget == 'stabilize':
            line = self.widget_stabilize.guidelines.moved(x, self.mouse_grabX, y, self.mouse_grabY)
            if line == 'vertical':
                self.widget_painter.setCursor(Qt.SplitHCursor)
            elif line == 'horizontal':
                self.widget_painter.setCursor(Qt.SplitVCursor)
            elif line == "both":
                self.widget_painter.setCursor(Qt.SizeAllCursor)
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


    # def paintEvent(self, event):
    #     if self.image is None:
    #         log.info("no image loaded")
    #         return

    #     img = self.image['cache']
    #     if img is None:
    #         return
    #     if self.image['cache_initial'] is None:
    #         return

    #     if self.is_repainting:
    #         log.error("error: self.is_repainting is True!!")
    #         return
    #     self.is_repainting = True
    #     delta_y = self.display_position_y

    #     preview = self.image['preview_options']
    #     # print_lightgreen("paintEvent: preview")
    #     # pprint(preview)
    #     initial_img_height, initial_img_width, c = self.image['cache_initial'].shape
    #     # print("paintEvent: initial image = %dx%d" % (initial_img_height, initial_img_width))
    #     img_height, img_width, c = img.shape
    #     try:
    #         q_image = QImage(img.data, img_width, img_height, img_width * 3, QImage.Format_BGR888)
    #     except:
    #         print_red("paintEvent: cannot convert img to qImage")
    #         return

    #     # Shot geometry
    #     geometry = self.image['geometry']
    #     shot_geometry = geometry['shot']
    #     if shot_geometry is None and 'default' in geometry.keys():
    #         shot_geometry = geometry['default']



    #     self.image['origin'] = [PAINTER_MARGIN_LEFT, PAINTER_MARGIN_TOP - delta_y]
    #     # print_lightgreen(f"paintEvent: begin, delta: {delta_y}")
    #     # print(shot_geometry)
    #     if self.painter.begin(self):

    #         if preview['geometry']['final_preview']:
    #             # print("paintEvent: display final_preview")
    #             self.painter.drawImage(
    #                 QPoint(PAINTER_MARGIN_LEFT, PAINTER_MARGIN_TOP - delta_y), q_image)
    #         else:
    #             preview_shot_geometry = preview['geometry']['shot']

    #             if preview_shot_geometry['crop_edition'] and not preview_shot_geometry['crop_preview']:
    #                 # Add a red rectangle to the image

    #                 if preview_shot_geometry['resize_preview']:
    #                     # Resize the image (i.e. draw rect on the resized image)
    #                     x0 = PAINTER_MARGIN_LEFT
    #                     y0 = PAINTER_MARGIN_TOP - delta_y

    #                     # Patch the crop value if displaying deshaked shot
    #                     # crop = shot_geometry['crop']
    #                     # if not preview['geometry']['add_borders']:
    #                     #     crop = list(map(lambda x: x + IMG_BORDER_HIGH_RES, shot_geometry['crop']))

    #                     # # Image is resized, add the recalculated crop
    #                     # crop_top, crop_bottom, crop_left, crop_right, cropped_width, cropped_height = get_dimensions_from_crop_values(
    #                     #     width=initial_img_width, height=initial_img_height, crop=crop)
    #                     # w_tmp = int((cropped_width * FINAL_FRAME_HEIGHT) / float(cropped_height))
    #                     pprint(self.image['geometry_values'])
    #                     crop_left = self.image['geometry_values']['crop'][2]
    #                     crop_top = self.image['geometry_values']['crop'][0]
    #                     cropped_height = self.image['geometry_values']['initial']['h'] - (self.image['geometry_values']['crop'][0] + self.image['geometry_values']['crop'][1])

    #                     w_tmp = self.image['geometry_values']['resize']['w']
    #                     pad_left = int(((FINAL_FRAME_WIDTH - w_tmp) / 2))

    #                     ratio = np.float32(cropped_height) / FINAL_FRAME_HEIGHT
    #                     crop_left = int(crop_left / ratio)
    #                     crop_top = int(crop_top / ratio)

    #                     # print("\t-> w=%d, c_w=%d, w_tmp=%d, pad: %d" % (w, c_w, w_tmp, pad_left))
    #                     # print("\t-> crop_left=%d, crop_top=%d" % (c_l, crop_top))

    #                     self.image['origin'] = [x0 + pad_left - crop_left, y0 - crop_top]

    #                     self.painter.drawImage(
    #                         QPoint(x0 + pad_left - crop_left, y0 - crop_top),
    #                         q_image)

    #                     # Add the cropped resized rect
    #                     pen = QPen(COLOR_CROP_RECT)
    #                     pen.setWidth(PEN_CROP_SIZE)
    #                     pen.setStyle(Qt.SolidLine)
    #                     self.painter.setPen(pen)
    #                     self.painter.drawRect(
    #                         PAINTER_MARGIN_LEFT + pad_left - 1,
    #                         PAINTER_MARGIN_LEFT - delta_y - 1,
    #                         w_tmp + 1,
    #                         FINAL_FRAME_HEIGHT + 1)

    #                     # Add the final 1080p rect
    #                     pen = QPen(COLOR_DISPLAY_RECT)
    #                     pen.setWidth(PEN_CROP_SIZE)
    #                     pen.setStyle(Qt.SolidLine)
    #                     self.painter.setPen(pen)
    #                     self.painter.drawRect(
    #                         PAINTER_MARGIN_LEFT - 1,
    #                         PAINTER_MARGIN_LEFT - delta_y - 1,
    #                         FINAL_FRAME_WIDTH + 1,
    #                         FINAL_FRAME_HEIGHT + 1)

    #                 else:
    #                 # print("paintEvent: draw rect crop on the original image")
    #                     # Original
    #                     x0 = PAINTER_MARGIN_LEFT
    #                     y0 = PAINTER_MARGIN_TOP - delta_y
    #                     crop = shot_geometry['crop']
    #                     if not preview['geometry']['add_borders']:
    #                         crop = list(map(lambda x: x + IMG_BORDER_HIGH_RES, shot_geometry['crop']))
    #                     self.painter.drawImage(QPoint(x0, y0), q_image)

    #                     # Add a red rect for the crop
    #                     crop_top, crop_bottom, crop_left, crop_right, cropped_width, cropped_height = get_dimensions_from_crop_values(
    #                         width=initial_img_width, height=initial_img_height, crop=crop)

    #                     # print(f"({crop_left}, {crop_top}) -> ({cropped_width},{cropped_height})")

    #                     pen = QPen(COLOR_CROP_RECT)
    #                     pen.setWidth(PEN_CROP_SIZE)
    #                     pen.setStyle(Qt.SolidLine)
    #                     self.painter.setPen(pen)
    #                     # https://doc.qt.io/qt-6/qrect.html, PEN_CROP_SIZE = 1
    #                     # print("\timg: %dx%d" % (img.data.shape[1], img.data.shape[0]))
    #                     # print("\trect: (%d;%d) w=%d, h=%d" % (c_l - 1, c_t - delta_y - 1, c_w + 1, c_h + 1))

    #                     self.painter.drawRect(
    #                         PAINTER_MARGIN_LEFT + crop_left - 1,
    #                         PAINTER_MARGIN_LEFT + crop_top - delta_y - 1,
    #                         cropped_width + 1,
    #                         cropped_height + 1)

    #             elif preview_shot_geometry['crop_preview']:
    #                 # Image is cropped

    #                 if preview_shot_geometry['resize_preview']:
    #                     # Image is also resized

    #                     # if not preview['geometry']['add_borders']:
    #                     #     crop_top, crop_bottom, crop_left, crop_right, cropped_width, cropped_height = get_dimensions_from_crop_values(
    #                     #         width=initial_img_width, height=initial_img_height, crop=shot_geometry['crop'])

    #                     # w_tmp = int((cropped_width * FINAL_FRAME_HEIGHT) / float(cropped_height))
    #                     # pad_left = int(((FINAL_FRAME_WIDTH - img_width) / 2) + 0.5)
    #                     pad_left = (self.image['geometry_values']['pad']['left']
    #                                 + self.image['geometry_values']['pad_error'][2])

    #                     self.image['origin'] = [
    #                         PAINTER_MARGIN_LEFT + pad_left,
    #                         PAINTER_MARGIN_TOP - delta_y]
    #                     self.painter.drawImage(
    #                         QPoint(
    #                             PAINTER_MARGIN_LEFT + pad_left,
    #                             PAINTER_MARGIN_TOP - delta_y),
    #                         q_image)

    #                     # Add the final 1080p rect
    #                     pen = QPen(COLOR_DISPLAY_RECT)
    #                     pen.setWidth(PEN_CROP_SIZE)
    #                     pen.setStyle(Qt.SolidLine)
    #                     self.painter.setPen(pen)
    #                     self.painter.drawRect(
    #                         PAINTER_MARGIN_LEFT - 1,
    #                         PAINTER_MARGIN_LEFT - delta_y - 1,
    #                         FINAL_FRAME_WIDTH + 1,
    #                         FINAL_FRAME_HEIGHT + 1)
    #                 else:
    #                     # print("paintEvent: draw cropped image on the original image")
    #                     # Crop and no rect
    #                     crop = shot_geometry['crop']
    #                     if not preview['geometry']['add_borders']:
    #                         crop = list(map(lambda x: x + IMG_BORDER_HIGH_RES, shot_geometry['crop']))
    #                     crop_top, crop_bottom, crop_left, crop_right, cropped_width, cropped_height = get_dimensions_from_crop_values(
    #                         width=initial_img_width, height=initial_img_height, crop=crop)

    #                     self.painter.drawImage(
    #                         QPoint(PAINTER_MARGIN_LEFT + crop_left,
    #                             PAINTER_MARGIN_TOP + crop_top - delta_y),
    #                         q_image)

    #             else:
    #                 # original
    #                 # print("paintEvent: draw original image")

    #                 if preview['geometry']['add_borders']:
    #                     self.painter.drawImage(
    #                         QPoint(PAINTER_MARGIN_LEFT+IMG_BORDER_HIGH_RES, PAINTER_MARGIN_TOP+IMG_BORDER_HIGH_RES - delta_y),
    #                         q_image.scaled(q_image.width()*2, q_image.height()*2, aspectMode=Qt.KeepAspectRatio))

    #                 else:
    #                     self.painter.drawImage(
    #                         QPoint(PAINTER_MARGIN_LEFT, PAINTER_MARGIN_TOP - delta_y), q_image)

    #             if (preview['geometry']['target']['width_edition']
    #                 and preview_shot_geometry['crop_edition']
    #                 and preview_shot_geometry['resize_preview']):

    #                 # Add the target rect
    #                 pad_left = ((FINAL_FRAME_WIDTH - geometry['target']['w']) / 2) + 0.5
    #                 pen = QPen(COLOR_PART_CROP_RECT)
    #                 pen.setWidth(PEN_CROP_SIZE)
    #                 pen.setStyle(Qt.SolidLine)
    #                 self.painter.setPen(pen)
    #                 self.painter.drawRect(
    #                     PAINTER_MARGIN_LEFT + pad_left - 1,
    #                     PAINTER_MARGIN_LEFT - delta_y - 1,
    #                     geometry['target']['w'] + 1,
    #                     FINAL_FRAME_HEIGHT + 1)

    #                 # Add the final 1080p rect
    #                 pen = QPen(COLOR_DISPLAY_RECT)
    #                 pen.setWidth(PEN_CROP_SIZE)
    #                 pen.setStyle(Qt.SolidLine)
    #                 self.painter.setPen(pen)
    #                 self.painter.drawRect(
    #                     PAINTER_MARGIN_LEFT - 1,
    #                     PAINTER_MARGIN_LEFT - delta_y - 1,
    #                     FINAL_FRAME_WIDTH + 1,
    #                     FINAL_FRAME_HEIGHT + 1)



    #         if preview['curves']['split']:
    #             try: crop_top = 0 if preview_shot_geometry['resize_preview'] else (-1*crop_top)
    #             except:  crop_top = 0
    #             pen = QPen(QColor(255,255,255))
    #             pen.setStyle(Qt.DashLine)
    #             self.painter.setPen(pen)
    #             self.painter.drawLine(
    #                 preview['curves']['split_x'] + PAINTER_MARGIN_LEFT, PAINTER_MARGIN_TOP - crop_top,
    #                 preview['curves']['split_x'] + PAINTER_MARGIN_LEFT, PAINTER_MARGIN_TOP - crop_top + max(img_height, FINAL_FRAME_HEIGHT))

    #         guidelines = self.widget_stabilize.guidelines
    #         if guidelines.is_enabled():
    #             x, y = guidelines.coordinates()

    #             pen = QPen(QColor(255,255,255))
    #             pen.setStyle(Qt.SolidLine)
    #             self.painter.setPen(pen)
    #             self.painter.drawLine(
    #                 x, 10,
    #                 x, 10 + max(img_height, FINAL_FRAME_HEIGHT + PAINTER_MARGIN_TOP + IMG_BORDER_HIGH_RES))

    #             self.painter.drawLine(
    #                 10, y,
    #                 10 + max(img_width, FINAL_FRAME_WIDTH + PAINTER_MARGIN_LEFT + IMG_BORDER_HIGH_RES), y)


    #         self.painter.end()
    #     self.is_repainting = False

    #     # print("paintEvent: main end")

