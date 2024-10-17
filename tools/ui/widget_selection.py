from copy import copy
from pprint import pprint
import sys
from logger import log
from PySide6.QtCore import (
    QEvent,
    QObject,
    Qt,
    Signal,
    Slot,
    QItemSelection,
    QSize,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QKeyEvent,
    QWheelEvent,
)
from PySide6.QtWidgets import (
    QTableWidgetItem,
    QWidget,
    QAbstractItemView,
)

from scene.consolidate import is_scene_stabilized
from utils.geometry_utils import SceneGeometryStat

from .stylesheet import (
    COLOR_ERROR,
    COLOR_PURPLE,
    COLOR_TEXT,
    set_stylesheet,
)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from backend.replace_controller import ReplaceController
    from backend.geometry_controller import GeometryController

from backend._types import (
    AppType,
    Selection,
)

from utils.mco_types import Scene
from .ui.ui_widget_selection import Ui_SelectionWidget
from import_parsers import *
from utils.p_print import *
from parsers import (
    all_chapter_keys,
    key
)



class SelectionWidget(QWidget, Ui_SelectionWidget):
    signal_widget_selected = Signal(str)
    signal_ep_p_changed = Signal(Selection)
    signal_selected_scene_changed = Signal(dict)
    signal_close = Signal()

    def __init__(
        self,
        parent: QWidget | None,
        controller,
        app_type: AppType
    ) -> None:
        super().__init__()
        self.setupUi(self)
        self.controller: ReplaceController | GeometryController = controller
        self.app_type = app_type
        self.setObjectName('selection')

        # Setup and patch ui
        self.setAutoFillBackground(True)

        # Internal variables
        self._parent = parent
        self.episodes_and_parts = {}
        self.comboBox_episode.clear()
        self.comboBox_part.clear()

        self.previous_position = None
        self.is_modified = False
        self.initial_scene_no: int = -1
        self.previous_selection = [0]

        # Initialize widgets
        self.pushButton_save.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.comboBox_episode.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.comboBox_part.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.tableWidget_scenes.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.comboBox_episode.currentIndexChanged[int].connect(self.event_ep_p_changed)
        self.comboBox_part.currentIndexChanged[int].connect(self.event_ep_p_changed)

        self.tableWidget_scenes.clearContents()
        self.tableWidget_scenes.setRowCount(0)

        self.columns = [
            ['scene', 50, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter],
            ['src', 60, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter],
            ['start', 65, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter],
            ['count', 60, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter]
        ]

        if self.app_type == 'geometry':
            # geometry
            # - st
            # - defined
            # - ac
            # - width
            # - max_width
            # - fit
            # - ratio
            # - anamorphic
            self.columns.extend([
                ['st', 30, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter],
                ['def', 30, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter],
                ['ac', 30, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter],
                ['w', 60, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter],
                ['max_w', 60, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter],
                ['fit', 30, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter],
                ['k.r.', 30, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter],
                ['err', 30, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter]
            ])


        self.tableWidget_scenes.setColumnCount(len(self.columns))
        for c_no, column in enumerate(self.columns):
            self.tableWidget_scenes.setHorizontalHeaderItem(c_no, QTableWidgetItem())
            self.tableWidget_scenes.horizontalHeaderItem(c_no).setText(column[0])
            self.tableWidget_scenes.horizontalHeaderItem(c_no).setTextAlignment(column[2])
            self.tableWidget_scenes.setColumnWidth(c_no, column[1])

        self.tableWidget_scenes.setSelectionMode(
            QAbstractItemView.SelectionMode.ContiguousSelection
        )
        self.tableWidget_scenes.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        # Connect signals and filter events
        self.tableWidget_scenes.selectionModel().selectionChanged.connect(self.event_scene_selected)
        self.tableWidget_scenes.installEventFilter(self)

        self.controller.signal_selection_modified.connect(
            self.event_refresh_scenelist
        )
        self.controller.signal_modified_scenes[list].connect(self.refresh_modified_scenes)
        # self.controller.signal_current_scene_modified[dict].connect(self.event_current_scene_modified)

        self.set_enabled(True)
        set_stylesheet(self)

        # Install events for this widget
        # self.installEventFilter(self)

        # self.set_selected(False)

        width = (
            sum([c[1] for c in self.columns])
            + self.verticalLayout.contentsMargins().left()
            + self.verticalLayout.contentsMargins().right()
        )
        self.setMaximumSize(QSize(width, 16777215))
        self.adjustSize()


    def closeEvent(self, event):
        self.signal_close.emit()


    def get_user_preferences(self):
        k_ep = ''
        if (self.comboBox_episode.currentText() != ' '
        and self.comboBox_episode.currentText() != ''):
            k_ep = int(self.comboBox_episode.currentText())

        # First selected row no
        selected_indexes = self.tableWidget_scenes.selectedIndexes()
        try:
            row_no = list(set([i.row() for i in selected_indexes]))[0]
        except:
            row_no = 0

        preferences = {
            'episode': k_ep,
            'scene_no': int(self.tableWidget_scenes.item(row_no, 0).text().replace('*', '')),
            'k_ch': self.comboBox_part.currentText(),
        }
        return preferences



    def apply_user_preferences(self, preferences:dict):
        s = preferences['selection']
        log.info(f"set_initial_options: {s['episode']}, {s['k_ch']}")
        print("%s:set_initial_options: " % (__name__), s)

        self.set_enabled(True)
        # self.tableWidget_scenes.setEnabled(False)

        # Episode
        # self.refresh_combobox_episode()
        self.comboBox_episode.blockSignals(True)
        saved_ep_no = s['episode']
        if saved_ep_no == 0:
            # print("none selected")
            self.comboBox_episode.setCurrentText(" ")
        else:
            index = self.comboBox_episode.findText(str(saved_ep_no))
            self.comboBox_episode.setCurrentIndex(index)
        self.comboBox_episode.blockSignals(False)

        # Part
        # self.refresh_combobox_part()
        self.comboBox_part.blockSignals(True)
        self.comboBox_part.setCurrentText(s['k_ch'])
        index = self.comboBox_part.findText(s['k_ch'])
        self.comboBox_part.setCurrentIndex(index)
        self.comboBox_part.blockSignals(False)

        # Scenes
        self.tableWidget_scenes.blockSignals(True)
        self.tableWidget_scenes.clearContents()
        self.tableWidget_scenes.setRowCount(0)
        self.tableWidget_scenes.blockSignals(False)

        # Current scene no
        try:
            self.initial_scene_no = s['scene_no']
        except:
            pass

        self.adjustSize()


    def event_current_scene_modified(self, modifications:dict):
        print(red("event_current_scene_modified: modified!!!!!!!!"))
        self.tableWidget_scenes.blockSignals(True)
        row_no = self.tableWidget_scenes.currentRow()

        for column, column_no in zip(self.columns, range(len(self.columns))):
            if column[0] == 'st.':
                try:
                    self.tableWidget_scenes.cellWidget(row_no, column_no).setChecked(modifications['stabilization'])
                except:
                    continue
                    # self.tableWidget_scenes.cellWidget(row_no, column_no).setChecked(False)

            elif column[0] == 'geo.':
                try:
                    self.tableWidget_scenes.cellWidget(row_no, column_no).setChecked(modifications['geometry'])
                except:
                    continue
                    # self.tableWidget_scenes.cellWidget(row_no, column_no).setChecked(False)

            elif column[0] == 'other':
                try:
                    self.tableWidget_scenes.setItem(row_no, 0, QTableWidgetItem(modifications['comment']))
                except:
                    continue
                    # self.tableWidget_scenes.setItem(row_no, 0, QTableWidgetItem(""))

            else:
                continue

        self.tableWidget_scenes.blockSignals(False)





    def edition_started(self, is_started):
        row_no = self.tableWidget_scenes.currentRow()
        print(f"edition_started: {row_no} is_started: {is_started}")
        item = self.tableWidget_scenes.item(row_no, 0)
        if is_started:
            self.tableWidget_scenes.item(row_no, 0).setForeground(QBrush(COLOR_PURPLE))
        else:
            self.tableWidget_scenes.item(row_no, 0).setForeground(QBrush(COLOR_TEXT))


    @Slot(list)
    def refresh_modified_scenes(self, modified_scenes: list[int]):
        # Something has been modified, disable selection until saving or discard
        log.info(f"refresh modification status, modified scenes: {modified_scenes}")
        for row_no in range(self.tableWidget_scenes.rowCount()):
            scene_str = self.tableWidget_scenes.item(row_no, 0).text().replace('*', '')
            if row_no in modified_scenes:
                self.tableWidget_scenes.item(row_no, 0).setText(f"{scene_str}*")
            else:
                self.tableWidget_scenes.item(row_no, 0).setText(scene_str)

        scene_no: int = self.tableWidget_scenes.currentRow()
        self.set_enabled(bool(len(modified_scenes) == 0))
        self.edition_started(bool(scene_no in modified_scenes))

        if self.app_type == 'geometry':
            print(f"selection: refresh: {scene_no}")
            scene: Scene = self.controller.selection().scenes[scene_no]
            row_no = scene_no

            sc_geometry: SceneGeometryStat = self.controller.scene_geometry_stats(scene_no)
            if sc_geometry is not None:
                for column_no, column in enumerate(self.columns):
                    item: QTableWidgetItem = self.tableWidget_scenes.item(row_no, column_no)

                    # Stabilized
                    if column[0] == 'st':
                        item_text: str = "x" if is_scene_stabilized(scene) else ""
                        self.tableWidget_scenes.setItem(row_no, column_no, QTableWidgetItem(item_text))

                    # Is defined
                    elif column[0] == 'def':
                        item_text: str = "x" if sc_geometry is not None and sc_geometry.is_defined() else "-"
                        self.tableWidget_scenes.setItem(row_no, column_no, QTableWidgetItem(item_text))

                    # autocrop
                    elif column[0] == 'ac':
                        item_text: str = "x" if sc_geometry is not None and sc_geometry.autocrop else ""
                        # self.tableWidget_scenes.setItem(row_no, column_no, QTableWidgetItem(item_text))
                        item.setText(item_text)
                        print(f"    refresh autocrop to [{item_text}]")

                    # width
                    elif column[0] == 'w':
                        item_text: str = f"{sc_geometry.resized_to()[0]}" if sc_geometry is not None else ""
                        self.tableWidget_scenes.setItem(row_no, column_no, QTableWidgetItem(item_text))

                    # max width
                    elif column[0] == 'max_w':
                        item_text: str = f"{sc_geometry.max_width}" if sc_geometry is not None else ""
                        self.tableWidget_scenes.setItem(row_no, column_no, QTableWidgetItem(item_text))

                    # fit to width
                    elif column[0] == 'fit':
                        item_text: str = "x" if sc_geometry is not None and sc_geometry.fit_to_width else ""
                        self.tableWidget_scenes.setItem(row_no, column_no, QTableWidgetItem(item_text))

                    # keep_ratio
                    elif column[0] == 'k.r.':
                        item_text: str = "x" if sc_geometry is not None and sc_geometry.keep_ratio else ""
                        self.tableWidget_scenes.setItem(row_no, column_no, QTableWidgetItem(item_text))

                    elif column[0] == 'err':
                        error: bool = bool(sc_geometry is None or sc_geometry.is_erroneous())
                        item_text: str = "x" if error else ""
                        self.tableWidget_scenes.setItem(row_no, column_no, QTableWidgetItem(item_text))
                        item: QTableWidgetItem = self.tableWidget_scenes.item(row_no, column_no)
                        item.setFlags(
                            Qt.ItemFlag.ItemIsSelectable|Qt.ItemFlag.ItemIsEnabled & ~Qt.ItemFlag.ItemIsEditable)
                        # self.tableWidget_scenes.item(row_no, 0).setData(Qt.ItemDataRole.FontRole, QColor.red())
                        if error:
                            # self.tableWidget_scenes.item(row_no, 0).setForeground(QBrush(QColor(255, 0, 0)))
                            self.tableWidget_scenes.item(row_no, 0).setForeground(QBrush(COLOR_ERROR))

                    item: QTableWidgetItem = self.tableWidget_scenes.item(row_no, column_no)
                    item.setTextAlignment(column[2])
                    item.setFlags(
                        Qt.ItemFlag.ItemIsSelectable|Qt.ItemFlag.ItemIsEnabled & ~Qt.ItemFlag.ItemIsEditable)


    def refresh_browsing_folder(self, episodes_and_parts:dict):
        log.info("refresh combobox_episode")
        # print("%s:refresh_browsing_folder: " % (__name__), episodes_and_parts)
        self.episodes_and_parts = episodes_and_parts


    def refresh_available_selection(self, available: dict):
        log.info("refresh available episode/parts")
        self.episodes_and_parts = available
        self.comboBox_episode.blockSignals(True)
        self.comboBox_part.blockSignals(True)

        saved_episode = self.comboBox_episode.currentText()
        saved_part = self.comboBox_part.currentText()
        log.info(f"saved ep:part: {saved_episode}:{saved_part}")

        self.comboBox_episode.clear()
        self.comboBox_part.clear()

        if False:
            eps = [f"{ep}" for ep in range(1, 40)]
            self.comboBox_episode.addItems(eps)
            self.comboBox_part.addItems(all_chapter_keys())

        else:
            eps = sorted(list(self.episodes_and_parts.keys()))
            self.comboBox_episode.addItems([f"{int(x[2:])}" for x in eps])

            # Restore the previous episode
            print(saved_episode)
            i = self.comboBox_episode.findText(saved_episode)
            new_index = i if i != -1 else 0
            print(new_index)
            self.comboBox_episode.setCurrentIndex(new_index)

            k_ep = eps[new_index]
            self.comboBox_part.addItems(self.episodes_and_parts[k_ep])
            # Restore the previous part if exists
            i = self.comboBox_part.findText(saved_part)
            new_index = i if i != -1 else 0
            self.comboBox_part.setCurrentIndex(new_index)


        self.comboBox_episode.setEnabled(True)
        self.comboBox_part.setEnabled(True)
        self.comboBox_episode.blockSignals(False)
        self.comboBox_part.blockSignals(False)



    @Slot()
    def event_refresh_scenelist(self):
        log.info("directory has been parsed, refresh scene list")
        # print("%s:event_refresh:" % (__name__))
        # pprint(values)
        # print("---")
        # sys.exit()
        # self.set_enabled(False)
        self.tableWidget_scenes.selectionModel().blockSignals(True)
        self.tableWidget_scenes.blockSignals(True)

        selection: Selection = self.controller.selection()

        # Episode
        k_ep = selection.k_ep
        ep_no_str = str(int(k_ep[2:])) if (k_ep != '' and  k_ep != ' ') else ''
        if self.comboBox_episode.currentText() != ep_no_str:
            i = self.comboBox_episode.findText(ep_no_str)
            self.comboBox_episode.blockSignals(True)
            new_index = i if i != -1 else 0
            self.comboBox_episode.setCurrentIndex(new_index)
            self.comboBox_episode.blockSignals(False)

        # Chapter
        if self.comboBox_part.currentText() != selection.k_ch:
            i = self.comboBox_part.findText(selection.k_ch)
            self.comboBox_part.blockSignals(True)
            new_index = i if i != -1 else 0
            self.comboBox_part.setCurrentIndex(new_index)
            self.comboBox_part.blockSignals(False)


        # Scenes
        scenes: list[Scene] = selection.scenes
        self.tableWidget_scenes.clearContents()
        self.tableWidget_scenes.setRowCount(0)
        row_no = 0
        for scene_no, scene in enumerate(scenes):
            if self.app_type == 'geometry':
                sc_geometry: SceneGeometryStat = self.controller.scene_geometry_stats(scene_no)
            else:
                sc_geometry = None
            self.tableWidget_scenes.insertRow(row_no)

            for column_no, column in enumerate(self.columns):
                item: QTableWidgetItem = self.tableWidget_scenes.item(row_no, column_no)

                if column[0] == 'scene':
                    self.tableWidget_scenes.setItem(row_no, column_no, QTableWidgetItem(f"{scene_no:03}"))
                    item: QTableWidgetItem = self.tableWidget_scenes.item(row_no, column_no)
                    item.setFlags(
                        Qt.ItemFlag.ItemIsSelectable|Qt.ItemFlag.ItemIsEnabled & ~Qt.ItemFlag.ItemIsEditable)

                elif column[0] == 'src':
                    k_ed, k_ep, _, _ = scene['src'].primary_scene()['k_ed_ep_ch_no']
                    src_txt = f"{k_ed}:{k_ep}"

                    self.tableWidget_scenes.setItem(row_no, column_no, QTableWidgetItem(src_txt))
                    item: QTableWidgetItem = self.tableWidget_scenes.item(row_no, column_no)
                    item.setTextAlignment(column[2])
                    item.setFlags(
                        Qt.ItemFlag.ItemIsSelectable|Qt.ItemFlag.ItemIsEnabled & ~Qt.ItemFlag.ItemIsEditable)

                elif column[0] == 'start':
                    self.tableWidget_scenes.setItem(
                        row_no, column_no,
                        QTableWidgetItem(f"{scene['src'].primary_scene()['start']}")
                    )
                    item: QTableWidgetItem = self.tableWidget_scenes.item(row_no, column_no)
                    item.setTextAlignment(column[2])
                    item.setFlags(
                        Qt.ItemFlag.ItemIsSelectable|Qt.ItemFlag.ItemIsEnabled & ~Qt.ItemFlag.ItemIsEditable)

                elif column[0] == 'count':
                    self.tableWidget_scenes.setItem(
                        row_no, column_no,
                        QTableWidgetItem(f"{scene['src'].frame_count()}")
                    )
                    item: QTableWidgetItem = self.tableWidget_scenes.item(row_no, column_no)
                    item.setTextAlignment(column[2])
                    item.setFlags(
                        Qt.ItemFlag.ItemIsSelectable|Qt.ItemFlag.ItemIsEnabled & ~Qt.ItemFlag.ItemIsEditable)

                # Stabilized
                elif column[0] == 'st':
                    item_text: str = "x" if is_scene_stabilized(scene) else ""
                    self.tableWidget_scenes.setItem(row_no, column_no, QTableWidgetItem(item_text))
                    item: QTableWidgetItem = self.tableWidget_scenes.item(row_no, column_no)
                    item.setTextAlignment(column[2])
                    item.setFlags(
                        Qt.ItemFlag.ItemIsSelectable
                        | Qt.ItemFlag.ItemIsEnabled & ~Qt.ItemFlag.ItemIsEditable
                    )

                # Is defined
                elif column[0] == 'def':
                    item_text: str = "x" if sc_geometry is not None and sc_geometry.is_defined() else "-"
                    self.tableWidget_scenes.setItem(row_no, column_no, QTableWidgetItem(item_text))
                    item: QTableWidgetItem = self.tableWidget_scenes.item(row_no, column_no)
                    item.setTextAlignment(column[2])
                    item.setFlags(
                        Qt.ItemFlag.ItemIsSelectable|Qt.ItemFlag.ItemIsEnabled & ~Qt.ItemFlag.ItemIsEditable)

                # autocrop
                elif column[0] == 'ac':
                    item_text: str = "x" if sc_geometry is not None and sc_geometry.autocrop else ""
                    self.tableWidget_scenes.setItem(row_no, column_no, QTableWidgetItem(item_text))
                    item: QTableWidgetItem = self.tableWidget_scenes.item(row_no, column_no)
                    item.setTextAlignment(column[2])
                    item.setFlags(
                        Qt.ItemFlag.ItemIsSelectable|Qt.ItemFlag.ItemIsEnabled & ~Qt.ItemFlag.ItemIsEditable)

                # width
                elif column[0] == 'w':
                    item_text: str = f"{sc_geometry.resized_to()[0]}" if sc_geometry is not None else ""
                    self.tableWidget_scenes.setItem(row_no, column_no, QTableWidgetItem(item_text))
                    item: QTableWidgetItem = self.tableWidget_scenes.item(row_no, column_no)
                    item.setTextAlignment(column[2])
                    item.setFlags(
                        Qt.ItemFlag.ItemIsSelectable|Qt.ItemFlag.ItemIsEnabled & ~Qt.ItemFlag.ItemIsEditable)

                # max width
                elif column[0] == 'max_w':
                    item_text: str = f"{sc_geometry.max_width}" if sc_geometry is not None else ""
                    self.tableWidget_scenes.setItem(row_no, column_no, QTableWidgetItem(item_text))
                    item: QTableWidgetItem = self.tableWidget_scenes.item(row_no, column_no)
                    item.setTextAlignment(column[2])
                    item.setFlags(
                        Qt.ItemFlag.ItemIsSelectable|Qt.ItemFlag.ItemIsEnabled & ~Qt.ItemFlag.ItemIsEditable)

                # fit to width
                elif column[0] == 'fit':
                    item_text: str = "x" if sc_geometry is not None and sc_geometry.fit_to_width else ""
                    self.tableWidget_scenes.setItem(row_no, column_no, QTableWidgetItem(item_text))
                    item: QTableWidgetItem = self.tableWidget_scenes.item(row_no, column_no)
                    item.setTextAlignment(column[2])
                    item.setFlags(
                        Qt.ItemFlag.ItemIsSelectable|Qt.ItemFlag.ItemIsEnabled & ~Qt.ItemFlag.ItemIsEditable)

                # keep_ratio
                elif column[0] == 'k.r.':
                    item_text: str = "x" if sc_geometry is not None and sc_geometry.keep_ratio else ""
                    self.tableWidget_scenes.setItem(row_no, column_no, QTableWidgetItem(item_text))
                    item: QTableWidgetItem = self.tableWidget_scenes.item(row_no, column_no)
                    item.setTextAlignment(column[2])
                    item.setFlags(
                        Qt.ItemFlag.ItemIsSelectable|Qt.ItemFlag.ItemIsEnabled & ~Qt.ItemFlag.ItemIsEditable)

                elif column[0] == 'err':
                    error: bool = bool(sc_geometry is None or sc_geometry.is_erroneous())
                    item_text: str = "x" if error else ""
                    self.tableWidget_scenes.setItem(row_no, column_no, QTableWidgetItem(item_text))
                    item: QTableWidgetItem = self.tableWidget_scenes.item(row_no, column_no)
                    item.setTextAlignment(column[2])
                    item.setFlags(
                        Qt.ItemFlag.ItemIsSelectable|Qt.ItemFlag.ItemIsEnabled & ~Qt.ItemFlag.ItemIsEditable)
                    # self.tableWidget_scenes.item(row_no, 0).setData(Qt.ItemDataRole.FontRole, QColor.red())
                    if error:
                        # self.tableWidget_scenes.item(row_no, 0).setForeground(QBrush(QColor(255, 0, 0)))
                        self.tableWidget_scenes.item(row_no, 0).setForeground(QBrush(COLOR_ERROR))

                elif column[0] == 'g_d':
                    self.tableWidget_scenes.setItem(row_no, column_no, QTableWidgetItem(f""))
                    item: QTableWidgetItem = self.tableWidget_scenes.item(row_no, column_no)
                    item.setTextAlignment(column[2])
                    item.setFlags(
                        Qt.ItemFlag.ItemIsSelectable|Qt.ItemFlag.ItemIsEnabled & ~Qt.ItemFlag.ItemIsEditable)


                elif column[0] == 'r':
                    self.tableWidget_scenes.setItem(row_no, column_no, QTableWidgetItem(f""))

                try:
                    item: QTableWidgetItem = self.tableWidget_scenes.item(row_no, column_no)
                    item.setTextAlignment(column[2])
                    item.setFlags(
                        Qt.ItemFlag.ItemIsSelectable|Qt.ItemFlag.ItemIsEnabled & ~Qt.ItemFlag.ItemIsEditable)
                except:
                    pass

            # Append invalid scenes
            # if scene['no'] in selection.invalid:
            #     # If true, it means that all pictures are present in the folder
            #     # Bug: this does not work
            #     self.tableWidget_scenes.item(row_no, 0).setData(Qt.FontRole, QColor(Qt.red))
            row_no += 1

        self.tableWidget_scenes.selectionModel().clearSelection()
        self.tableWidget_scenes.setSelectionMode(
            QAbstractItemView.SelectionMode.ContiguousSelection
        )
        self.tableWidget_scenes.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.tableWidget_scenes.selectionModel().blockSignals(False)
        self.tableWidget_scenes.blockSignals(False)

        self.tableWidget_scenes.setEnabled(True)
        self.set_enabled(True)

        if len(scenes) > 0:
            if self.initial_scene_no != -1:
                log.info(f"initial: select scene no. {self.initial_scene_no}")
                self.tableWidget_scenes.selectRow(self.initial_scene_no)
                self.initial_scene_no = -1
            else:
                log.info("initial: select scene no. 0")
                self.tableWidget_scenes.selectRow(0)

        self.comboBox_episode.blockSignals(False)
        self.comboBox_part.blockSignals(False)



    def event_ep_p_changed(self, index=0):
        log.info(f"select {self.comboBox_episode.currentText()}:{self.comboBox_part.currentText()}")
        k_ep = ''
        selected_ep_str = self.comboBox_episode.currentText()
        if selected_ep_str not in ['', ' ']:
            k_ep = key(int(self.comboBox_episode.currentText()))

        selection: Selection = Selection(
            k_ep=k_ep,
            k_ch=self.comboBox_part.currentText(),
        )

        self.comboBox_episode.setEnabled(False)
        self.comboBox_part.setEnabled(False)
        self.comboBox_episode.blockSignals(True)
        self.comboBox_part.blockSignals(True)

        self.signal_ep_p_changed.emit(selection)
        return True



    def event_scene_selected(self, selected: QItemSelection):
        selected_indexes = self.tableWidget_scenes.selectedIndexes()
        selected_row_no = sorted(list(set([i.row() for i in selected_indexes])))

        # I selection is empty, restore previous selection
        if len(selected_row_no) == 0:
            self.tableWidget_scenes.blockSignals(True)
            self.tableWidget_scenes.selectionModel().blockSignals(True)
            for r in self.previous_selection:
                self.tableWidget_scenes.selectRow(r)
            self.tableWidget_scenes.selectionModel().blockSignals(False)
            self.tableWidget_scenes.blockSignals(False)
            log.error("Restore previous selection")
            return
        self.previous_selection = copy(selected_row_no)

        log.info(f"event_selection_changed: {', '.join(map(lambda x: f"{x}", selected_row_no))}")

        selected_scene_nos = list()
        for row_no in selected_row_no:
            scene_no_str = self.tableWidget_scenes.item(row_no, 0).text()
            selected_scene_nos.append(int(scene_no_str.replace('*', '')))

        k_ep = ''
        if self.comboBox_episode.currentText() not in ['', ' ']:
            k_ep = f"ep{int(self.comboBox_episode.currentText()):02}"
        selected_scenes = {
            'k_ep': k_ep,
            'k_ch': self.comboBox_part.currentText(),
            'scenes': selected_scene_nos
        }
        self.signal_selected_scene_changed.emit(selected_scenes)


    def set_enabled(self, enabled: bool):
        log.info(f"set enabled to {enabled}")
        print(purple(f"set selection enabled to {enabled}"))
        # if self.is_modified and enabled:
        #     # do not allow selection until all modifications are saved or discarded
        #     return
        # self.setEnabled(enabled)
        self.comboBox_episode.setEnabled(enabled)
        self.comboBox_part.setEnabled(enabled)
        self.tableWidget_scenes.blockSignals(not enabled)
        self.tableWidget_scenes.selectionModel().blockSignals(not enabled)
        self.tableWidget_scenes.setSelectionMode(
            QAbstractItemView.SelectionMode.ContiguousSelection
            if enabled
            else QAbstractItemView.SelectionMode.NoSelection
        )


    def refresh_values(self, frame:dict):
        pass


    def get_preview_options(self):
        return None



    def select_next_scene(self):
        if len(self.tableWidget_scenes.selectionModel().selectedRows()) > 1:
            return
        try:
            row_no = self.tableWidget_scenes.currentRow() + 1
            if row_no >= self.tableWidget_scenes.rowCount():
                row_no = 0
            self.tableWidget_scenes.clearSelection()
            self.tableWidget_scenes.selectRow(row_no)
        except:
            pass


    def select_previous_scene(self):
        if len(self.tableWidget_scenes.selectionModel().selectedRows()) > 1:
            return
        try:
            row_no = self.tableWidget_scenes.currentRow()
            if row_no == 0:
                row_no = self.tableWidget_scenes.rowCount() - 1
            else:
                row_no -= 1
            self.tableWidget_scenes.clearSelection()
            self.tableWidget_scenes.selectRow(row_no)
        except:
            pass




    def event_key_pressed(self, event: QKeyEvent) -> bool:
        key = event.key()
        modifiers = event.modifiers()
        if modifiers & Qt.ControlModifier:
            if key == Qt.Key.Key_A:
                self.tableWidget_scenes.selectAll()
                return True

        return False


    def event_wheel(self, event: QWheelEvent) -> bool:
        print(lightgreen("\tDefault selection fct"))
        return False



    def event_key_released(self, event: QKeyEvent) -> bool:
        return False




    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        # return super().eventFilter(watched, event)
        # # Filter press/release events
        if event.type() == QEvent.Type.KeyPress:
            print(f"{__name__}: eventFilter key press")
            if self.event_key_pressed(event):
                event.accept()
                return True
            else:
                return self._parent.event_key_pressed(event)


        if event.type() == QEvent.Type.KeyRelease:
            print(f"{__name__}: eventFilter key release")
            if self.event_key_released(event):
                event.accept()
                return True
            else:
                return self._parent.event_key_released(event)

        if event.type() == QEvent.Type.Wheel:
            if event.angleDelta().y() > 0:
                self.select_previous_scene()
            else:
                self.select_next_scene()
            event.accept()
            return True

        # elif event.type() == QEvent.Type.FocusIn:
        #     self.signal_widget_selected.emit(self.objectName())
        #     event.accept()
        #     return True
        # elif event.type() == QEvent.HoverEnter:
        #     update_selected_widget_stylesheet(self.frame, is_selected=True)
        #     print_purple(f"selection: HoverEnter")
        # elif event.type() == QEvent.HoverLeave:
        #     update_selected_widget_stylesheet(self.frame, is_selected=False)
        #     print_purple(f"selection: HoverLeave")

        # elif event.type() == QEvent.ActivationChange:
        #     event.accept()
        #     self.signal_widget_selected.emit(self.objectName())
        #     return True

        # elif event.type() == QEvent.Leave:
        #     update_selected_widget_stylesheet(self.frame, is_selected=False)
        #     print_purple(f"selection: Leave")

        return super().eventFilter(watched, event)
        # return True
