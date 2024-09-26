from dataclasses import dataclass
from pprint import pprint
from logger import log
from import_parsers import *
from backend._types import ReplaceAction, ReplaceActionType
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

from .ui.ui_widget_replace import Ui_ReplaceWidget
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from tools.backend.replace_controller import ReplaceController
from .stylesheet import (
    set_stylesheet,
    set_widget_stylesheet,
)
from backend.frame_cache import Frame

@dataclass(slots=True)
class CurrentFrame:
    no: int
    frame: Frame
    original: Frame




class ReplaceWidget(QWidget, Ui_ReplaceWidget):
    signal_replace_modified = Signal(ReplaceAction)
    signal_replace_removed = Signal(dict)
    signal_frame_selected = Signal(int)
    signal_save = Signal()
    signal_discard = Signal()
    signal_undo = Signal()
    signal_preview_toggled = Signal(bool)
    signal_edition_started = Signal()


    def __init__(self, ui, controller):
        super().__init__(ui)
        self.setupUi(self)

        self.controller: ReplaceController = controller
        self.ui = ui
        self.setObjectName('replace')

        # Internal variables
        self.previous_position = None
        self.current_frame: CurrentFrame | None = None
        self.copied: CurrentFrame | None = None

        # Disable focus
        self.pushButton_set_preview.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.pushButton_save.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.pushButton_discard.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.lineEdit_frame_no.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.lineEdit_replaced_by.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.pushButton_copy.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.pushButton_paste.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.pushButton_remove.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.tableWidget_replace.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.lineEdit_frame_no.clear()
        self.lineEdit_replaced_by.clear()

        self.pushButton_copy.clicked.connect(self.event_copy)
        self.pushButton_paste.clicked.connect(self.event_paste)
        self.pushButton_remove.clicked.connect(self.event_remove)

        # Table
        self.tableWidget_replace.clearContents()
        self.tableWidget_replace.setRowCount(0)


        self.alignment = [
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        ]
        headers = ["scene", "frame", "by"]
        default_col_width = [60, 80, 80]
        for col_no, header_str, col_width in zip(
            range(len(headers)),
            headers,
            default_col_width
        ):
            self.tableWidget_replace.horizontalHeaderItem(col_no).setText(header_str)
            self.tableWidget_replace.setColumnWidth(col_no, col_width)
        self.tableWidget_replace.horizontalHeader().setStretchLastSection(True)

        # Connect signals and filter events
        self.tableWidget_replace.selectionModel().selectionChanged.connect(self.event_replace_selected)
        self.tableWidget_replace.itemDoubleClicked[QTableWidgetItem].connect(
            self.event_move_to_frame_no
        )
        self.tableWidget_replace.installEventFilter(self)
        self.pushButton_set_preview.toggled[bool].connect(self.event_set_preview_toggled)
        self.pushButton_discard.clicked.connect(self.event_discard_modifications)
        self.pushButton_discard.setEnabled(False)
        self.pushButton_save.clicked.connect(self.event_save_modifications)
        self.pushButton_save.setEnabled(False)

        self.controller.signal_replacements_refreshed.connect(self.event_replace_list_refreshed)
        self.controller.signal_modified_scenes[list].connect(self.event_modified_scenes)

        # self.controller.signal_is_saved[str].connect(self.event_is_saved)

        # self.installEventFilter(self)

        set_stylesheet(self)
        self.adjustSize()




    def block_signals(self, enabled):
        self.pushButton_copy.blockSignals(enabled)
        self.pushButton_paste.blockSignals(enabled)
        self.pushButton_remove.blockSignals(enabled)
        self.pushButton_set_preview.blockSignals(enabled)
        self.pushButton_discard.blockSignals(enabled)
        self.pushButton_save.blockSignals(enabled)


    def apply_user_preferences(self, preferences: dict):
        self.block_signals(True)
        self.lineEdit_frame_no.clear()
        self.lineEdit_replaced_by.clear()
        self.tableWidget_replace.blockSignals(True)
        self.tableWidget_replace.clearContents()
        self.tableWidget_replace.setRowCount(0)

        self.pushButton_remove.setEnabled(False)
        self.pushButton_paste.setEnabled(False)
        self.pushButton_copy.setEnabled(False)

        self.pushButton_set_preview.setChecked(True)

        # Geometry
        # self.move(s['geometry'][0], s['geometry'][1])
        self.block_signals(False)
        self.adjustSize()


    def get_user_preferences(self) -> dict[str, Any]:
        return {}


    def event_set_preview_toggled(self, is_checked: bool=False):
        log.info(f"widget preview changed to {is_checked}")
        self.signal_preview_toggled.emit(is_checked)


    def refresh_preview_options(self, new_preview_settings):
        try:
            enabled = new_preview_settings['replace']['enabled']
        except:
            enabled = False

        if not enabled:
            self.lineEdit_frame_no.clear()
            self.lineEdit_replaced_by.clear()


    @Slot()
    def event_replace_list_refreshed(self):
        log.info("refresh list of frames to replace")
        replacements = self.controller.playlist_replacements()
        self.tableWidget_replace.blockSignals(True)

        self.tableWidget_replace.clearContents()
        self.tableWidget_replace.setRowCount(0)

        row_no: int = 0
        for scene_no, scene_replacements in replacements.items():
            scene_no_str: str = f"{scene_no:03}"
            for no, by in scene_replacements.items():
                self.tableWidget_replace.insertRow(row_no)
                self.tableWidget_replace.setItem(row_no, 0, QTableWidgetItem(scene_no_str))
                self.tableWidget_replace.setItem(row_no, 1, QTableWidgetItem(str(no)))
                self.tableWidget_replace.setItem(row_no, 2, QTableWidgetItem(str(by)))
                for i in range(len(self.alignment)):
                    self.tableWidget_replace.item(row_no, i).setTextAlignment(self.alignment[i])
                    self.tableWidget_replace.item(row_no, i).setFlags(
                        Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
                    )
                row_no += 1

        self.tableWidget_replace.selectionModel().clearSelection()
        self.tableWidget_replace.blockSignals(False)
        self.tableWidget_replace.setEnabled(True)


    def event_replace_selected(self):
        log.info("event_replace_selected")
        self.tableWidget_replace.setFocus()


    @Slot(QTableWidgetItem)
    def event_move_to_frame_no(self, item: QTableWidgetItem):
        # double-click to jump to the frame no.
        row_no = item.row()
        column_no = item.column()
        if column_no == 0:
            return
        # log.info(f"selected frame at row={row_no}, column {row_no}")
        frame_no = int(self.tableWidget_replace.item(row_no, column_no).text())
        self.signal_frame_selected.emit(frame_no)


    def set_current_frame(
        self,
        frame: Frame,
        original_frame: Frame | None,
    ) -> None:
        self.lineEdit_frame_no.setText(
            str(original_frame.no if original_frame is not None else frame.no)
        )
        if original_frame is not None:
            self.lineEdit_replaced_by.setText(str(frame.no))
            self.pushButton_remove.setEnabled(True)
            src_frame_no = original_frame.no
            self.current_frame = frame

        else:
            # self.lineEdit_frame_no.clear()
            try:
                self.lineEdit_replaced_by.clear()
                # self.lineEdit_replaced_by.setText(str(frame.no))
                self.pushButton_remove.setEnabled(True)
            except:
                self.lineEdit_replaced_by.clear()
                self.pushButton_remove.setEnabled(False)
            src_frame_no = frame.no

        self.current_frame = CurrentFrame(
            no=src_frame_no,
            frame=frame,
            original=original_frame
        )


    def event_copy(self):
        self.copied = self.current_frame
        print("copied")
        pprint(self.copied)
        self.pushButton_paste.setEnabled(True)


    def event_paste(self):
        if self.copied is None:
            log.error(f"circular reference")
            return
        log.info(f"event: paste: {self.current_frame.no} <- {self.copied.frame.no}")
        if (
            int(self.copied.frame.scene_key.split(':')[-1])
            != int(self.current_frame.frame.scene_key.split(':')[-1])
        ):
            print(red("Error: cannot paste in a different scene"))
            return

        if self.controller.is_frame_used_for_replace(self.current_frame.frame):
            print(red("cannot paste to a frame whic is the source of other frames"))
            return False

        print(yellow("copied:"))
        pprint(self.copied)
        print(yellow("paste to:"))
        pprint(self.current_frame)

        log.info(f"event: paste to {self.current_frame.no}")
        self.pushButton_discard.setEnabled(True)
        self.pushButton_save.setEnabled(True)
        replace_action = ReplaceAction(
            type='replace',
            current=self.current_frame.frame,
            by=self.copied.frame,
        )
        self.signal_replace_modified.emit(replace_action)


    def event_undo(self):
        log.info('undo requested')
        self.signal_undo.emit()


    def event_remove(self):
        selected_indexes = self.tableWidget_replace.selectedIndexes()
        selected_row_nos = list(set([i.row() for i in selected_indexes]))
        remove_dict: dict[int, list[int]] = {}
        for row in selected_row_nos:
            scene_no = self.tableWidget_replace.item(row, 0).text()
            if scene_no not in remove_dict:
                remove_dict[scene_no] = []
            remove_dict[scene_no].append(int(self.tableWidget_replace.item(row, 1).text()))

        self.pushButton_discard.setEnabled(True)
        self.pushButton_save.setEnabled(True)

        print(f"event_remove: {remove_dict}")
        self.signal_replace_removed.emit(remove_dict)


    def block_signals(self, enabled):
        self.pushButton_copy.blockSignals(enabled)
        self.pushButton_paste.blockSignals(enabled)
        self.pushButton_remove.blockSignals(enabled)
        self.pushButton_set_preview.blockSignals(enabled)
        self.pushButton_discard.blockSignals(enabled)
        self.pushButton_save.blockSignals(enabled)


    @Slot(list)
    def event_modified_scenes(self, modified_scenes: list[int]) -> None:
        enabled = True if len(modified_scenes) > 0 else False
        self.pushButton_discard.setEnabled(enabled)
        self.pushButton_save.setEnabled(enabled)


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



    def event_key_pressed(self, event: QKeyEvent) -> bool:
        key = event.key()
        modifiers = event.modifiers()
        print(green(f"widget_replace: event_key_pressed: {key}"))
        print("%s.event_key_pressed: %d, modifiers=" % (__name__, key), modifiers)

        if modifiers & Qt.KeyboardModifier.ControlModifier:
            if key == Qt.Key.Key_S:
                print(purple("Save replace"))
                self.event_save_modifications()
                return True

            elif key == Qt.Key.Key_C:
                self.event_copy()
                return True

            elif key == Qt.Key.Key_V:
                self.event_paste()
                return True

            elif key == Qt.Key.Key_Z:
                self.event_undo()
                return True

        if key == Qt.Key.Key_F2:
            if self.pushButton_set_preview.isEnabled():
                self.pushButton_set_preview.toggle()
                return True

        if QApplication.focusObject() is self.tableWidget_replace:
            if key == Qt.Key.Key_Delete:
                self.event_remove()
                return True

        # elif key == Qt.Key_R:
        #     new_index = self.controller.get_next_replaced_frame_index(index=self.slider_frames.value())
        #     if new_index != -1:
        #         self.move_slider_to(new_index)

        return False


    def wheelEvent(self, event: QWheelEvent) -> None:
        return True
        return super().wheelEvent(event)
