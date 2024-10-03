from dataclasses import dataclass
from pprint import pprint
from logger import log
from import_parsers import *
from typing import TYPE_CHECKING, Any
from utils.mco_types import DetectInnerRectParams, SceneGeometry
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
from backend._types import Selection, TargetSceneGeometry



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

        self.controller.signal_selection_modified.connect(self.event_scenelist_modified)

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

        # Scene
        self.lineEdit_scene_crop_rectangle.blockSignals(enabled)
        self.checkBox_scene_keep_ratio.blockSignals(enabled)
        self.checkBox_scene_fit_to_width.blockSignals(enabled)
        self.pushButton_scene_discard.blockSignals(enabled)



    def apply_user_preferences(self, preferences: dict):
        log.info(f"{self.objectName()}: set_initial_options")

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
        self.adjustSize()


    def get_user_preferences(self) -> dict[str, Any]:
        return {}


    @Slot()
    def event_scenelist_modified(self):
        log.info("to implement")
        log.info("directory has been parsed, refresh scene list")
        selection: Selection = self.controller.selection()
        self.groupBox_scene_geometry.setEnabled(True)


    def set_edition_and_preview_enabled(self, enabled):
        # TODO reactivate once completely verified
        return


    def refresh_values(self, frame: Frame):
        target_geometry: TargetSceneGeometry = self.controller.get_scene_geometry(frame)
        pprint(target_geometry)

        if target_geometry.is_erroneous:
            self.label_message.setText("ERROR!")
        else:
            self.label_message.clear()

        # Width before padding
        self.lineEdit_target_width.setText(str(target_geometry.chapter.width))

        frame.scene_key
        if frame.k_ep_ch_no[1] in ('g_asuivre', 'g_documentaire'):
        #     self.groupBox_scene_geometry.setEnabled(False)
        #     # self.pushButton_target_width_copy_from_scene.setEnabled(False)
            self.is_target_disabled = True
        else:
            self.is_target_disabled = False
        self.groupBox_scene_geometry.setEnabled(True)
        # self.pushButton_target_width_copy_from_scene.setEnabled(True)


        # Scene geometry
        scene_geometry: SceneGeometry = target_geometry.scene
        try:
            t, b, l, r = scene_geometry.crop
            self.lineEdit_scene_crop_rectangle.setText(f"t: {t}, b: {b},  l: {l}, r: {r}")
        except:
            self.lineEdit_scene_crop_rectangle.clear()

        self.checkBox_scene_keep_ratio.blockSignals(True)
        try:
            keep_ratio = scene_geometry.keep_ratio
            self.checkBox_scene_keep_ratio.setChecked(keep_ratio)
        except:
            self.checkBox_scene_keep_ratio.setChecked(False)
        self.checkBox_scene_keep_ratio.blockSignals(False)

        self.checkBox_scene_fit_to_width.blockSignals(True)
        try:
            fit_to_width = scene_geometry.fit_to_width
            self.checkBox_scene_fit_to_width.setChecked(fit_to_width)
        except:
            self.checkBox_scene_fit_to_width.setChecked(False)
        self.checkBox_scene_fit_to_width.blockSignals(False)


        autocrop_params: DetectInnerRectParams = scene_geometry.detection_params
        self.spinBox_threshold_min.setValue(autocrop_params.threshold_min)
        self.spinBox_morph_kernel_radius.setValue(autocrop_params.morph_kernel_radius)
        self.spinBox_erode_kernel_radius.setValue(autocrop_params.erode_kernel_radius)
        self.spinBox_erode_iterations.setValue(autocrop_params.erode_iterations)
        self.checkBox_do_add_borders.setChecked(autocrop_params.do_add_borders)
        self.checkBox_use_as_crop_method.setChecked(scene_geometry.use_autocrop)
        try:
            t, b, l, r = scene_geometry.autocrop
            self.lineEdit_scene_autocrop.setText(f"t: {t}, b: {b},  l: {l}, r: {r}")
        except:
            self.lineEdit_scene_autocrop.clear()


    def event_scene_selected(self, selected):
        log.info("detected scene selection changed")
