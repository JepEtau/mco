from dataclasses import dataclass
from functools import partial
from pprint import pprint
from logger import log
from import_parsers import *
from typing import TYPE_CHECKING, Any, Literal
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
from backend._types import (
    GeometryAction,
    GeometryActionParameter,
    GeometryActionType,
    GeometryPreviewOptions,
    Selection,
    TargetSceneGeometry,
)



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
    signal_geometry_modified = Signal(GeometryAction)
    signal_detect_inner_rect = Signal(DetectInnerRectParams)
    signal_preview_options_changed = Signal(GeometryPreviewOptions)

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

        self.current_key_pressed: Qt.Key | None = None


        self.checkBox_scene_keep_ratio.toggled[bool].connect(self.event_keep_ratio_changed)
        self.checkBox_scene_fit_to_width.toggled[bool].connect(self.event_fit_to_width_changed)

        # Autocrop
        # Do not keep the history of modifications
        # self.spinBox_erode_iterations.valueChanged.connect(self.event_ac_params_changed)
        # self.spinBox_erode_kernel_radius.valueChanged.connect(self.event_ac_params_changed)
        # self.spinBox_morph_kernel_radius.valueChanged.connect(self.event_ac_params_changed)
        # self.spinBox_threshold_min.valueChanged.connect(self.event_ac_params_changed)
        # self.checkBox_do_add_borders.toggled[bool].connect(self.event_ac_params_changed)

        # self.checkBox_use_as_crop_method
        self.pushButton_calculate.released.connect(self.event_calculate)
        # self.pushButton_copy_to_scene

        self.pushButton_save.released.connect(self.event_save)

        # Edition/Preview
        self.pushButton_target_width_edition.toggled[bool].connect(
            partial(self.event_scene_preview_changed, 'target_preview')
        )
        self.pushButton_scene_crop_edition.toggled[bool].connect(
            partial(self.event_scene_preview_changed, 'crop_edition')
        )
        self.pushButton_scene_crop_preview.toggled[bool].connect(
            partial(self.event_scene_preview_changed, 'crop_preview')
        )
        self.pushButton_scene_resize_preview.toggled[bool].connect(
            partial(self.event_scene_preview_changed, 'resize_preview')
        )
        self.pushButton_set_preview.toggled[bool].connect(
            self.event_final_scene_preview_changed
        )
        self.checkBox_use_autocrop.toggled[bool].connect(self.event_use_autocrop)
        self.pushButton_copy_to_scene.released.connect(self.event_copy_to_scene)

        set_stylesheet(self)
        set_widget_stylesheet(self.label_message, 'message')
        self.adjustSize()


    def block_signals(self, block: bool):
        self.pushButton_set_preview.blockSignals(block)
        self.pushButton_discard.blockSignals(block)
        self.pushButton_save.blockSignals(block)

        # Target
        self.pushButton_target_width_edition.blockSignals(block)
        # self.pushButton_target_width_copy_from_scene.blockSignals(enabled)
        self.pushButton_target_discard.blockSignals(block)
        self.pushButton_target_save.blockSignals(block)

        # Scene
        self.pushButton_scene_crop_edition.blockSignals(block)
        self.pushButton_scene_crop_preview.blockSignals(block)
        # self.pushButton_scene_resize_edition.blockSignals(enabled)
        self.pushButton_scene_resize_preview.blockSignals(block)

        # Scene
        self.lineEdit_scene_crop_rectangle.blockSignals(block)
        self.checkBox_scene_keep_ratio.blockSignals(block)
        self.checkBox_scene_fit_to_width.blockSignals(block)
        self.pushButton_scene_discard.blockSignals(block)

        self.checkBox_use_autocrop.blockSignals(block)



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


    @Slot()
    def event_save(self) -> None:
        self.signal_save.emit()


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
            self.lineEdit_scene_crop_rectangle.setText(f"t: {t}, b: {b}, l: {l}, r: {r}")
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
        self.checkBox_use_autocrop.setChecked(scene_geometry.use_autocrop)
        try:
            t, b, l, r = scene_geometry.autocrop
            self.lineEdit_scene_autocrop.setText(f"t: {t}, b: {b},  l: {l}, r: {r}")
        except:
            self.lineEdit_scene_autocrop.clear()

        self.pushButton_calculate.setEnabled(True)


    def get_preview_options(self) -> GeometryPreviewOptions:
        preview_options: GeometryPreviewOptions = GeometryPreviewOptions(
            allowed=self.is_edition_allowed,
            final_preview=self.pushButton_set_preview.isChecked(),
            width_edition=self.pushButton_target_width_edition.isChecked(),
            crop_edition=self.pushButton_scene_crop_edition.isChecked(),
            crop_preview=self.pushButton_scene_crop_preview.isChecked(),
            resize_preview=self.pushButton_scene_resize_preview.isChecked(),
        )
        return preview_options


    @Slot()
    def event_final_scene_preview_changed(self):
        self.signal_preview_options_changed.emit(self.get_preview_options())


    def event_scene_preview_changed(self, selected, value):
        # A button has been clicked
        # log.info("button [%s] clicked" % (selected))
        # print_yellow("button [%s] clicked" % (selected))
        # if selected == 'target_preview':
        # elif selected == 'target_show_edition':
        # elif selected == 'crop_edition':
        # elif selected == 'crop_preview':
        # elif selected == 'resize_preview':

        # Disable final preview
        self.pushButton_set_preview.blockSignals(True)
        self.pushButton_set_preview.setChecked(False)
        self.saved_preview_options = None
        self.pushButton_set_preview.blockSignals(False)
        self.signal_preview_options_changed.emit(self.get_preview_options())



    def event_fit_to_width_changed(self, is_checked: bool):
        w_self = self.checkBox_scene_fit_to_width
        w = self.checkBox_scene_keep_ratio

        if not is_checked and not w.isChecked():
            w_self.blockSignals(True)
            w_self.setChecked(True)
            w_self.blockSignals(False)
            return

        log.info(f"fit to width: {'true' if is_checked else 'false'}")
        self.event_is_modified(
            event_type='set',
            parameter='fit_to_width',
            value=is_checked
        )


    def event_keep_ratio_changed(self, is_checked: bool):
        w = self.checkBox_scene_fit_to_width
        w_self = self.checkBox_scene_keep_ratio

        if not is_checked and not w.isChecked():
            w_self.blockSignals(True)
            w_self.setChecked(True)
            w_self.blockSignals(False)
            return

        log.info(f"keep ratio: {'true' if is_checked else 'false'}")
        self.event_is_modified(
            event_type='set',
            parameter='keep_ratio',
            value=is_checked
        )


    def event_is_modified(
        self,
        event_type: GeometryActionType,
        parameter: GeometryActionParameter,
        value: int
    ):
        # log.info(f"parameter has been modified: {event_type}: {parameter}, {value}")
        self.pushButton_discard.setEnabled(True)
        self.pushButton_save.setEnabled(True)
        if parameter == 'width':
            self.pushButton_target_discard.setEnabled(True)
            self.pushButton_target_save.setEnabled(True)

        self.signal_geometry_modified.emit(
            GeometryAction(
                type=event_type,
                parameter=parameter,
                value=value
            )
        )


    def event_ac_params_changed(self, arg: Any) -> None:
        print("ac params modified")
        self.pushButton_discard.setEnabled(True)
        self.pushButton_save.setEnabled(True)
        ac_params: DetectInnerRectParams = DetectInnerRectParams(
            threshold_min=self.spinBox_threshold_min.value(),
            morph_kernel_radius=self.spinBox_morph_kernel_radius.value(),
            erode_kernel_radius=self.spinBox_erode_kernel_radius.value(),
            erode_iterations=self.spinBox_erode_iterations.value(),
            do_add_borders=self.checkBox_do_add_borders.isChecked(),
        )
        self.signal_geometry_modified.emit(
            GeometryAction(
                type='set',
                parameter='autocrop',
                value=ac_params
            )
        )


    def event_calculate(self) -> None:
        self.pushButton_calculate.setEnabled(False)
        self.pushButton_discard.setEnabled(True)
        self.pushButton_save.setEnabled(True)
        ac_params: DetectInnerRectParams = DetectInnerRectParams(
            threshold_min=self.spinBox_threshold_min.value(),
            morph_kernel_radius=self.spinBox_morph_kernel_radius.value(),
            erode_kernel_radius=self.spinBox_erode_kernel_radius.value(),
            erode_iterations=self.spinBox_erode_iterations.value(),
            do_add_borders=self.checkBox_do_add_borders.isChecked(),
        )
        self.signal_detect_inner_rect.emit(ac_params)


    def event_use_autocrop(self) -> None:
        self.signal_geometry_modified.emit(
            GeometryAction(
                type='set',
                parameter='use_ac',
                value=self.checkBox_use_autocrop.isChecked(),
            )
        )

    def event_copy_to_scene(self) -> None:
        self.checkBox_use_autocrop.setChecked(False)
        self.signal_geometry_modified.emit(
            GeometryAction(
                type='set',
                parameter='copy_ac_to_crop',
                value=True
            )
        )

    def event_wheel(self, event: QWheelEvent) -> bool:
        if self.current_key_pressed is not None:
            modifiers = QApplication.keyboardModifiers()
            # print(lightgrey(f"wheelEvent: key: {self.current_key_pressed}"))
            # print(lightgrey(f"{modifiers}"))
            if self.checkBox_use_autocrop.isChecked():
                return True

            parameter: GeometryActionParameter
            if self.current_key_pressed == Qt.Key.Key_Z:
                parameter = 'crop_top'
            elif self.current_key_pressed == Qt.Key.Key_S:
                parameter = 'crop_bottom'
            elif self.current_key_pressed == Qt.Key.Key_Q:
                parameter = 'crop_left'
            elif self.current_key_pressed == Qt.Key.Key_D:
                parameter = 'crop_right'
            elif (
                self.current_key_pressed == Qt.Key.Key_W
                and not self.is_target_disabled
            ):
                parameter = 'width'
            else:
                return False

            value = -1 if event.angleDelta().y() > 0 else +1
            self.event_is_modified(
                event_type='set',
                parameter=parameter,
                value=value
            )
            return True

        return False


    def event_key_released(self, event: QKeyEvent) -> bool:
        self.current_key_pressed = None
        return False


    def event_key_pressed(self, event: QKeyEvent) -> bool:
        key = event.key()
        modifiers = event.modifiers()
        verbose = False
        if verbose:
            print(green(f"widget_geometry: event_key_pressed: {key}"))

        if key == Qt.Key.Key_Space:
            if verbose:
                print("main window: keyPressEvent")
                log.info("Space key event detected")
            return False

        if modifiers & Qt.KeyboardModifier.ControlModifier:
            if key == Qt.Key.Key_S:
                if verbose:
                    print(purple("Save geometry"))
                self.event_save()
                return True

        # if modifiers & Qt.AltModifier:
        #     if key == Qt.Key_S:
        #         if self.current_key_pressed != Qt.Key_S:
        #             self.signal_position_changed.emit('switch')
        #         self.current_key_pressed = Qt.Key_S
        #         return True
        #     else:
        #         return False

        if key == Qt.Key.Key_F2:
            if self.pushButton_set_preview.isEnabled():
                self.pushButton_set_preview.toggle()
                return True

        elif key == Qt.Key.Key_F3:
            self.pushButton_target_width_edition.toggle()
            return True

        elif key == Qt.Key.Key_F4:
            self.pushButton_scene_crop_edition.toggle()
            return True

        elif key == Qt.Key.Key_F5:
            self.pushButton_scene_crop_preview.toggle()
            return True

        elif key == Qt.Key.Key_F6:
            self.pushButton_scene_resize_preview.toggle()
            return True

        # Edit crop dimensions
        elif key in (Qt.Key.Key_Q, Qt.Key.Key_D, Qt.Key.Key_W):
            self.current_key_pressed = key
            return True

        elif key == Qt.Key.Key_Z:
            # if key != self.current_key_pressed:
            #     self.signal_position_changed.emit('top')
            self.current_key_pressed = key
            return True

        elif key == Qt.Key.Key_S:
            # if key != self.current_key_pressed:
            #     self.signal_position_changed.emit('bottom')
            self.current_key_pressed = key
            return True


        elif key == Qt.Key.Key_R:
            self.checkBox_scene_keep_ratio.toggle()
            return True

        elif key == Qt.Key.Key_F:
            self.checkBox_scene_fit_to_width.toggle()
            return True

        elif key == Qt.Key.Key_F7:
            self.pushButton_calculate.click()
            return True

        elif key == Qt.Key.Key_U:
            self.checkBox_use_autocrop.click()
            return True

        return False
