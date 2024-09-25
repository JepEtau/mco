from pprint import pprint
from logger import log
from import_parsers import *
from utils.p_print import *

from PySide6.QtCore import (
    Qt,
    Signal,
    Slot,
)
from PySide6.QtGui import(
    QKeyEvent,
)
from PySide6.QtWidgets import (
    QTableWidgetItem,
    QWidget,
    QApplication,
)

from .ui.ui_widget_replace import Ui_ReplaceWidget
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from backend.controller_replace import ReplaceController
from .stylesheet import (
    set_stylesheet,
    set_widget_stylesheet,
)
from backend.frame_cache import Frame



class ReplaceWidget(QWidget, Ui_ReplaceWidget):
    signal_replace_modified = Signal(dict)
    signal_frame_selected = Signal(int)
    signal_save = Signal()
    signal_discard = Signal()
    signal_preview_options_changed = Signal()
    signal_edition_started = Signal()


    def __init__(self, ui, controller):
        super().__init__(ui)
        self.setupUi(self)

        self.controller: ReplaceController = controller
        self.ui = ui
        self.setObjectName('replace')

        # Internal variables
        self.copied_frame_no = -1
        self.previous_position = None
        self.is_edition_allowed = False

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

        self.pushButton_copy.clicked.connect(self.event_frame_no_copied)
        self.pushButton_paste.clicked.connect(self.event_frame_no_paste)
        self.pushButton_remove.clicked.connect(self.event_removed)

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
        self.tableWidget_replace.itemDoubleClicked[QTableWidgetItem].connect(self.event_move_to_frame_no)
        self.tableWidget_replace.installEventFilter(self)

        self.controller.signal_replacements_refreshed.connect(
            self.event_replace_list_refreshed
        )
        # self.controller.signal_is_saved[str].connect(self.event_is_saved)

        # self.installEventFilter(self)

        # self.frame.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

        set_stylesheet(self)
        self.adjustSize()




    def block_signals(self, enabled):
        self.pushButton_copy.blockSignals(enabled)
        self.pushButton_paste.blockSignals(enabled)
        self.pushButton_remove.blockSignals(enabled)
        self.pushButton_set_preview.blockSignals(enabled)
        self.pushButton_discard.blockSignals(enabled)
        self.pushButton_save.blockSignals(enabled)


    def set_initial_options(self, preferences:dict):
        s = preferences['replace']

        self.is_edition_allowed = False

        self.block_signals(True)
        self.lineEdit_frame_no.clear()
        self.lineEdit_replaced_by.clear()
        self.tableWidget_replace.blockSignals(True)
        self.tableWidget_replace.clearContents()
        self.tableWidget_replace.setRowCount(0)

        self.pushButton_remove.setEnabled(False)
        self.pushButton_paste.setEnabled(False)
        self.pushButton_copy.setEnabled(False)

        self.pushButton_set_preview.setChecked(s['widget']['enabled'])

        # Geometry
        # self.move(s['geometry'][0], s['geometry'][1])
        self.block_signals(False)
        self.adjustSize()


    def get_user_preferences(self) -> dict[str, Any]:
        return {}


    def refresh_preview_options(self, new_preview_settings):
        try:
            enabled = new_preview_settings['replace']['enabled']
        except:
            enabled = False
        try:
            allowed = new_preview_settings['replace']['allowed']
        except:
            allowed = False
        self.is_edition_allowed = allowed

        if not enabled or not allowed:
            self.lineEdit_frame_no.clear()
            self.lineEdit_replaced_by.clear()

        self.lineEdit_frame_no.setEnabled(allowed)
        self.lineEdit_replaced_by.setEnabled(allowed)
        self.pushButton_copy.setEnabled(allowed)
        self.pushButton_paste.setEnabled(allowed)
        self.pushButton_remove.setEnabled(allowed)

        self.pushButton_set_preview.blockSignals(True)
        self.pushButton_set_preview.setEnabled(allowed)
        self.pushButton_set_preview.blockSignals(False)


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


    def event_move_to_frame_no(self, item:QTableWidgetItem):
        # double-click
        row_no = item.row()
        column_no = item.column()
        if column_no == 0:
            return
        # log.info(f"selected frame at row={row_no}, column {row_no}")
        frame_no = int(self.tableWidget_replace.item(row_no, column_no).text())
        self.signal_frame_selected.emit(frame_no)


    def event_selection_removed(self):
        print("event_selection_removed")
        selected_indexes = self.tableWidget_replace.selectedIndexes()
        selected_row_nos = list(set([i.row() for i in selected_indexes]))
        selected_frame_nos = list(map(lambda x: int(self.tableWidget_replace.item(x,1).text()),
                selected_row_nos))

        if len(selected_frame_nos) > 0:
            self.pushButton_discard.setEnabled(True)
            self.pushButton_save.setEnabled(True)

        for frame_no in selected_frame_nos:
            self.signal_replace_modified.emit({
                'action': 'remove',
                'dst': frame_no
            })


    def refresh_values(self, frame: Frame):
        if frame.by > 0 and frame.by != frame.no:
            # print("this frame (%d) replaces %d" % (frame['frame_no'], frame['replace']))
            self.lineEdit_frame_no.setText(str(frame['replace']))
            self.lineEdit_replaced_by.setText(str(frame['frame_no']))
            self.pushButton_remove.setEnabled(True)
        else:
            self.lineEdit_frame_no.setText(str(frame['frame_no']))
            try:
                self.lineEdit_replaced_by.setText(str(frame['replaced_by']))
                self.pushButton_remove.setEnabled(True)
            except:
                self.lineEdit_replaced_by.clear()
                self.pushButton_remove.setEnabled(False)


    def event_frame_no_copied(self):
        self.copied_frame_no = int(self.lineEdit_frame_no.text())
        log.info("event: copy %d" % (self.copied_frame_no))
        self.pushButton_paste.setEnabled(True)


    def event_frame_no_paste(self):
        log.info("event: paste")
        frame_no = int(self.lineEdit_frame_no.text())
        if (self.copied_frame_no != -1
        and frame_no != self.copied_frame_no):
            log.info("event: paste to %d" % (frame_no))
            self.pushButton_discard.setEnabled(True)
            self.pushButton_save.setEnabled(True)
            self.signal_replace_modified.emit({
                'src': self.copied_frame_no,
                'dst': frame_no,
                'action': 'replace'
            })



    def event_undo_replace(self):
        log.info("event: undo for frame_no: %d")
        self.signal_replace_modified.emit({
            'action': 'undo',
            'dst': int(self.lineEdit_frame_no.text())
        })


    def event_removed(self):
        log.info("event: remove")
        self.pushButton_discard.setEnabled(True)
        self.pushButton_save.setEnabled(True)
        self.signal_replace_modified.emit({
            'action': 'remove',
            'dst': int(self.lineEdit_frame_no.text())
        })


    def get_preview_options(self):
        preview_options = {
            'allowed': self.is_edition_allowed,
            'enabled': self.pushButton_set_preview.isChecked(),
        }
        return preview_options


    def block_signals(self, enabled):
        self.pushButton_copy.blockSignals(enabled)
        self.pushButton_paste.blockSignals(enabled)
        self.pushButton_remove.blockSignals(enabled)
        self.pushButton_set_preview.blockSignals(enabled)
        self.pushButton_discard.blockSignals(enabled)
        self.pushButton_save.blockSignals(enabled)



    def event_key_pressed(self, event: QKeyEvent) -> bool:
        key = event.key()
        modifiers = event.modifiers()
        print(green(f"widget_replace: event_key_pressed: {key}"))
        # print("%s.event_key_pressed: %d, modifiers=" % (__name__, key), modifiers)

        if modifiers & Qt.KeyboardModifier.ControlModifier:
            if key == Qt.Key.Key_S:
                print(purple("Save replace"))
                self.event_save_modifications()
                return True

            elif key == Qt.Key.Key_C:
                self.event_frame_no_copied()
                return True
            elif key == Qt.Key.Key_V:
                self.event_frame_no_paste()
                return True
            # elif key == Qt.Key_Z:
            #     self.event_undo()
            #     return True

        if key == Qt.Key.Key_F2:
            if self.pushButton_set_preview.isEnabled():
                self.pushButton_set_preview.toggle()
                return True

        if QApplication.focusObject() is self.tableWidget_replace:
            if key == Qt.Key.Key_Delete:
                self.event_selection_removed()
                return True

        # elif key == Qt.Key_R:
        #     new_index = self.controller.get_next_replaced_frame_index(index=self.slider_frames.value())
        #     if new_index != -1:
        #         self.move_slider_to(new_index)

        return False


