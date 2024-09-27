from dataclasses import dataclass
from pprint import pprint
from logger import log
from import_parsers import *
from typing import TYPE_CHECKING, Any
from utils.p_print import *

from PySide6.QtCore import (
    Qt,
    Signal,
    Slot,
)
from PySide6.QtGui import(
    QKeyEvent,
    QWheelEvent,
)
from PySide6.QtWidgets import (
    QTableWidgetItem,
    QWidget,
    QApplication,
)

from .ui.ui_widget_geometry import Ui_GeometryWidget
from .stylesheet import (
    set_stylesheet,
    set_widget_stylesheet,
)
if TYPE_CHECKING:
    from backend.geometry_controller import GeometryController
from backend.frame_cache import Frame
from backend._types import Selection



@dataclass(slots=True)
class CurrentFrame:
    no: int
    frame: Frame
    original: Frame



class GeometryWidget(QWidget, Ui_GeometryWidget):
    signal_save = Signal()
    signal_discard = Signal()
    signal_undo = Signal()
    signal_preview_toggled = Signal(bool)
    signal_edition_started = Signal()


    def __init__(self, ui, controller):
        super().__init__(ui)
        self.setupUi(self)

        self.controller: GeometryController = controller
        self.ui = ui
        self.setObjectName('geometry')

        # Disable focus
        self.pushButton_set_preview.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.pushButton_save.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.pushButton_discard.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.controller.signal_selection_modified[dict].connect(self.event_scenelist_modified)

        set_stylesheet(self)
        set_widget_stylesheet(self.label_message, 'message')
        self.adjustSize()


    def block_signals(self, enabled):
        self.pushButton_set_preview.blockSignals(enabled)
        self.pushButton_discard.blockSignals(enabled)
        self.pushButton_save.blockSignals(enabled)

        # Target
        self.pushButton_target_width_edition.blockSignals(enabled)
        # self.pushButton_target_width_copy_from_scene.blockSignals(enabled)
        self.pushButton_target_discard.blockSignals(enabled)
        self.pushButton_target_save.blockSignals(enabled)

        # Scene
        self.pushButton_scene_crop_edition.blockSignals(enabled)
        self.pushButton_scene_crop_preview.blockSignals(enabled)
        # self.pushButton_scene_resize_edition.blockSignals(enabled)
        self.pushButton_scene_resize_preview.blockSignals(enabled)

        # Scene: default
        self.lineEdit_default_scene_crop_rectangle.blockSignals(enabled)
        self.checkBox_default_scene_keep_ratio.blockSignals(enabled)
        self.checkBox_default_scene_fit_to_width.blockSignals(enabled)
        self.pushButton_default_scene_discard.blockSignals(enabled)

        # Scene: custom
        self.lineEdit_scene_crop_rectangle.blockSignals(enabled)
        self.checkBox_scene_keep_ratio.blockSignals(enabled)
        self.checkBox_scene_fit_to_width.blockSignals(enabled)
        self.pushButton_scene_discard.blockSignals(enabled)




    def apply_user_preferences(self, preferences: dict):
        log.info("%s: set_initial_options" % (self.objectName()))
        s = preferences[self.objectName()]

        self.lineEdit_default_scene_crop_rectangle.clear()

        self.block_signals(True)
        try:
            w = preferences[self.objectName()]['widget']

            self.pushButton_set_preview.blockSignals(True)
            self.pushButton_set_preview.setChecked(w['final_preview'])
            self.pushButton_set_preview.blockSignals(False)

            self.pushButton_target_width_edition.setChecked(w['target']['width_edition'])

            self.pushButton_scene_crop_edition.setChecked(w['scene']['crop_edition'])
            self.pushButton_scene_crop_preview.setChecked(w['scene']['crop_preview'])
            # self.pushButton_scene_resize_edition.setChecked(w['scene']['resize_edition'])
            self.pushButton_scene_resize_preview.setChecked(w['scene']['resize_preview'])

        except:
            log.warning("cannot set initial options")
            pass

        self.pushButton_target_discard.setEnabled(False)
        self.pushButton_target_save.setEnabled(False)
        self.is_edition_allowed = True

        self.block_signals(False)

        # Force enabled/disable to save the current states for all widgets
        self.set_edition_and_preview_enabled(False)
        self.set_edition_and_preview_enabled(True)

        # Geometry
        self.move(s['geometry'][0], s['geometry'][1])
        self.adjustSize()


    def get_user_preferences(self) -> dict[str, Any]:
        return {}



    @Slot()
    def event_refresh_scenelist(self):
        log.info("directory has been parsed, refresh scene list")
        selection: Selection = self.controller.selection()
        self.groupBox_scene_geometry.setEnabled(True)

        # ? Disable modification of scene geometry if there is only one shot ???


    def refresh_values(self, frame: Frame):
        # log.info("widget_geometry: refresh_values")
        geometry = frame['geometry']
        # print_lightgreen(geometry)

        # if geometry['error']:
        #     self.label_message.setText("ERROR!")
        # else:
        #     self.label_message.clear()

        # # Width before padding
        # self.lineEdit_target_width.setText(str(geometry['target']['w']))

        # if frame['k_part'] in ['g_asuivre', 'g_documentaire']:
        # #     self.groupBox_scene_geometry.setEnabled(False)
        # #     # self.pushButton_target_width_copy_from_scene.setEnabled(False)
        #     self.is_target_disabled = True
        # else:
        #     self.is_target_disabled = False
        # self.groupBox_scene_geometry.setEnabled(True)
        # # self.pushButton_target_width_copy_from_scene.setEnabled(True)


        # # Default shot geometry
        # try:
        #     crop_top, crop_bottom, crop_left, crop_right = geometry['default']['crop']
        #     crop_str = "t: %d, b: %d,  l: %d, r: %d" % (crop_top, crop_bottom, crop_left, crop_right)
        #     self.lineEdit_default_scene_crop_rectangle.setText(crop_str)
        # except:
        #     self.lineEdit_default_scene_crop_rectangle.clear()

        # self.checkBox_default_scene_keep_ratio.blockSignals(True)
        # try:
        #     keep_ratio = geometry['default']['keep_ratio']
        #     self.checkBox_default_scene_keep_ratio.setChecked(keep_ratio)
        # except:
        #     self.checkBox_default_scene_keep_ratio.setChecked(False)
        # self.checkBox_default_scene_keep_ratio.blockSignals(False)

        # self.checkBox_default_scene_fit_to_width.blockSignals(True)
        # try:
        #     fit_to_width = geometry['default']['fit_to_width']
        #     self.checkBox_default_scene_fit_to_width.setChecked(fit_to_width)
        # except:
        #     self.checkBox_default_scene_fit_to_width.setChecked(False)
        # self.checkBox_default_scene_fit_to_width.blockSignals(False)


        # # Shot geometry
        # try:
        #     crop_top, crop_bottom, crop_left, crop_right = geometry['shot']['crop']
        #     crop_str = "t: %d, b: %d,  l: %d, r: %d" % (crop_top, crop_bottom, crop_left, crop_right)
        #     self.lineEdit_scene_crop_rectangle.setText(crop_str)
        # except:
        #     self.lineEdit_scene_crop_rectangle.clear()

        # self.checkBox_scene_keep_ratio.blockSignals(True)
        # try:
        #     keep_ratio = geometry['shot']['keep_ratio']
        #     self.checkBox_scene_keep_ratio.setChecked(keep_ratio)
        # except:
        #     self.checkBox_scene_keep_ratio.setChecked(False)
        # self.checkBox_scene_keep_ratio.blockSignals(False)

        # self.checkBox_scene_fit_to_width.blockSignals(True)
        # try:
        #     fit_to_width = geometry['shot']['fit_to_width']
        #     self.checkBox_scene_fit_to_width.setChecked(fit_to_width)
        # except:
        #     self.checkBox_scene_fit_to_width.setChecked(False)
        # self.checkBox_scene_fit_to_width.blockSignals(False)


        # # Select shot/default
        # self.groupBox_default_scene_geometry.blockSignals(True)
        # self.groupBox_scene_geometry.blockSignals(True)

        # if geometry['shot'] is None:
        #     # Use default geometry
        #     self.groupBox_default_scene_geometry.setChecked(True)
        #     self.groupBox_scene_geometry.setChecked(False)
        # else:
        #     # Use custom geometry
        #     self.groupBox_default_scene_geometry.setChecked(False)
        #     self.groupBox_scene_geometry.setChecked(True)

        # self.groupBox_default_scene_geometry.blockSignals(False)
        # self.groupBox_scene_geometry.blockSignals(False)



    def event_scene_selected(self, selected):
        # Changed default <-> shot
        self.groupBox_default_shot_geometry.blockSignals(True)
        self.groupBox_shot_geometry.blockSignals(True)

        # Change states: simulate radio buttons
        if selected == 'default_shot':
            state = self.groupBox_shot_geometry.isChecked()
            self.groupBox_default_shot_geometry.setChecked(True)
            self.groupBox_shot_geometry.setChecked(False)
            if not state:
                # No changes
                self.groupBox_default_shot_geometry.blockSignals(False)
                self.groupBox_shot_geometry.blockSignals(False)
                return

        elif selected == 'shot':
            state = self.groupBox_default_shot_geometry.isChecked()
            self.groupBox_shot_geometry.setChecked(True)
            self.groupBox_default_shot_geometry.setChecked(False)
            if not state:
                # No changes
                self.groupBox_default_shot_geometry.blockSignals(False)
                self.groupBox_shot_geometry.blockSignals(False)
                return

        # Actions
        self.event_is_modified(element='shot', event_type='select', parameter='shot', value=selected)

        self.groupBox_default_shot_geometry.blockSignals(False)
        self.groupBox_shot_geometry.blockSignals(False)
