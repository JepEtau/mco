from __future__ import annotations

from pprint import pprint
import sys
import time
from PySide6.QtCore import (
    Signal,
    Slot,
)

from scene.src_scene import SrcScene


from ._types import (
    CurrentFrame,
    DsrAction,
    DsrProcessParams,
    PlaylistProperties,
    ReplaceAction,
    Selection,
    WarpAction,
)
from .replace_database import ReplaceDatabase
from .dsr_database import DsrDatabase
from .warp_database import WarpDatabase

from .frame_cache import FrameCache, Frame
from .common_controller import CommonController
from .user_preferences import UserPreferences

from logger import log
from ui.window_replace import ReplaceWindow
from utils.mco_types import Scene
from utils.p_print import *
from parsers import (
    DsrPatch,
    SceneDsr,
    TaskName,
    Warp,
)


class ReplaceController(CommonController):
    signal_preview_options_consolidated = Signal(dict)
    signal_replacements_refreshed = Signal()
    signal_dsr_shapes_refreshed = Signal()
    signal_scene_warps_refreshed = Signal()

    def __init__(
        self,
        task_name: bool = False,
        ep_no: int = 0,
        scene: int = -1,
    ):
        super().__init__()

        # Load saved preferences
        self.user_preferences: UserPreferences = UserPreferences(tool='replace')

        self.current_task = ''
        self.task_name: TaskName = task_name
        self.replace_db = ReplaceDatabase()
        self.dsr_db = DsrDatabase()
        self.warp_db = WarpDatabase()
        self.frame_cache: FrameCache = FrameCache(
            self.replace_db,
            self.dsr_db,
            self.warp_db,
        )

        # scene_no: {frame_no: replaced_by}
        self.selection_replacements: dict[int, dict[int, int]] = {}
        # scene_no: dsr regions for each frame
        self.selection_dsr: dict[int, SceneDsr] = {}
        self.selection_warp: dict[int, dict[int, Warp]] = {}

        print("ReplaceController::init", self.user_preferences.settings)
        print(f"\tep_no={ep_no}, scene={scene}")
        if 1 <= ep_no <= 39:
            self.user_preferences.settings['selection']['episode'] = ep_no
            self.user_preferences.settings['selection']['scene_no'] = 0
        if scene > 0:
            self.user_preferences.settings['selection']['scene_no'] = scene


    def set_view(self, view: ReplaceWindow):
        super().set_view(view)
        self.view: ReplaceWindow

        # Replace
        self.view.widget_replace.signal_replace_modified[ReplaceAction].connect(self.event_frame_replaced)
        self.view.widget_replace.signal_replace_removed.connect(self.event_replace_removed)
        self.view.widget_replace.signal_undo.connect(self.event_replace_undo)
        self.view.widget_replace.signal_save.connect(self.event_replace_dsr_save)
        self.view.widget_replace.signal_discard.connect(self.event_replace_discard)

        # Warp
        self.view.widget_warp.signal_warp_values_changed.connect(self.event_warp_modified)
        self.view.widget_warp.signal_warp_update.connect(self.event_warp_process)

        # Dsr
        self.view.widget_dsr.signal_dsr_modified.connect(self.event_dsr_modified)
        self.view.widget_dsr.signal_undo.connect(self.event_dsr_undo)
        self.view.widget_dsr.signal_discard.connect(self.event_dsr_discard)


    def k_ep_p_changed(self, selection: Selection):
        super().k_ep_p_changed(selection)
        self.signal_selection_modified.emit()
        self.send_modified_scene_signal()


    def event_selected_scene_changed(self, selected: dict):
        log.info(f"select {len(selected['scenes'])} scenes, start:{selected['scenes'][0]}")
        verbose = True
        if verbose:
            print(lightgreen(f"selected scenes: {selected['k_ep']}:{selected['k_ch']}, %s" % (
                ','.join(map(lambda x: str(x), selected['scenes'])))))

        log.info(f"selected scenes: {selected['k_ep']}:{selected['k_ch']}, %s" % (
            ','.join(map(lambda x: str(x), selected['scenes']))))

        if len(selected['scenes']) == 0:
            return

        scene = self.current_scene()
        print("event_selected_scene_changed, selected:", selected)

        # Create a list of frames for each selected scene
        frame_nos = []
        ticklist = [0]

        self.playlist_frames.clear()
        for scene_no in selected['scenes']:
            scene: Scene = self.scenes[scene_no]
            if verbose:
                print(lightgrey("extract frames:"), end=' ')
                start_time = time.time()
            scene_frames = self.frame_cache.get(scene=scene)
            if scene_frames is None:
                break
            self.playlist_frames.extend(scene_frames)
            if verbose:
                print(f"{time.time() - start_time:.2f}")
            ticklist.append(ticklist[-1] + len(scene_frames))

        if scene_frames is None:
            print(red(f"Missing input file for scene {scene_no}"))
            self.signal_error.emit(f"Missing input file for scene {scene_no}")

        frame_nos = [f.no for f in self.playlist_frames]
        self._playlist_properties: PlaylistProperties = PlaylistProperties(
            frame_nos=frame_nos,
            count=len(self.playlist_frames),
            ticks=ticklist,
            scenes=selected['scenes'],
        )

        # Set current to None to refresh widgets
        self.current_frame = None
        self.current_scene_no = selected['scenes'][0]

        # Selection: update replacements and dsr regions for each frame
        self.selection_replacements.clear()
        for scene_no in selected['scenes']:
            scene: Scene = self.scenes[scene_no]
            self.selection_replacements.update(self.replace_db.scene_replacements(scene))
            self.selection_dsr.update(self.dsr_db.get_scene_dsr(scene))
            self.selection_warp.update(self.warp_db.get_scene_warp(scene))

        # Update widgets' tables
        self.signal_replacements_refreshed.emit()
        self.signal_dsr_shapes_refreshed.emit()
        self.signal_scene_warps_refreshed.emit()

        # self.signal_preview_options_consolidated.emit(self.preview_options)
        self.signal_ready_to_play.emit()


    def playlist_replacements(self) -> dict[int, dict[int, int]]:
        return self.selection_replacements


    def get_frame_at_index(self, index: int) -> tuple[Frame, Frame | None]:
        original_frame: Frame = self.playlist_frames[index]
        frame = original_frame
        if self.preview_enabled:
            frame = self.playlist_frames[
                self.get_index_from_frame_no(original_frame.by)
            ]
        return (
            frame,
            original_frame if original_frame.no != frame.no else None
        )


    def get_original_frame(self, index: int) -> Frame:
        frame: Frame = self.playlist_frames[index]
        if frame.by != frame.no:
            frame = self.playlist_frames[
                self.get_index_from_frame_no(frame.by)
            ]
        return frame


    def get_scene_dsr(self, frame: Frame) -> SceneDsr:
        # print(lightcyan(f"get_scene_dr: {frame.scene_key}, {frame.src_scene_key}"))
        return self.selection_dsr[frame.scene_key]


    def preview_modified(self, preview_settings: dict):
        self.preview_enabled = preview_settings['enabled']


    def is_frame_used_for_replace(self, frame: Frame) -> bool:
        scene_no = int(frame.scene_key.split(':')[-1])
        return bool(frame.no in list(self.selection_replacements[scene_no].values()))


    @Slot(ReplaceAction)
    def event_frame_replaced(self, replace_action: ReplaceAction):
        print(yellow("event_frame_replaced"))

        scene_no: int = int(replace_action.current.scene_key.split(':')[-1])
        # if isinstance(replace.by, Frame):
        log.info(f"replace: {replace_action.current.no} <- {replace_action.by.no}")
        by: int = (
            replace_action.by.by
            if replace_action.by.by != replace_action.current.no
            else replace_action.by.no
        )
        log.info(f"replace (consolidated): {replace_action.current.no} <- {by}")

        scene: Scene = self.scenes[scene_no]
        self.replace_db.add(
            scene,
            replace_action.current.src_scene_key,
            replace_action.current.no,
            by
        )
        replace_action.current.by = replace_action.by.no

        print(self.replace_db.modified_scene_nos())
        del self.selection_replacements[scene_no]
        self.selection_replacements.update(
            self.replace_db.scene_replacements(scene)
        )
        self.signal_replacements_refreshed.emit()
        self.signal_dsr_shapes_refreshed.emit()
        self.signal_scene_warps_refreshed.emit()
        self.signal_reload_frame.emit()
        print(f"modified_scenes: {self.replace_db.modified_scene_nos()}")
        self.send_modified_scene_signal()


    @Slot(dict)
    def event_replace_removed(self, remove_dict: dict[str, list[int]]) -> None:
        removed_frame_no: list[int] = []
        for scene_no, frame_nos in remove_dict.items():
            removed_frame_no.extend(frame_nos)
            scene_no = int(scene_no)
            scene: Scene = self.scenes[scene_no]
            self.replace_db.remove_multiple(scene, frame_nos)
            del self.selection_replacements[scene_no]
            self.selection_replacements.update(self.replace_db.scene_replacements(scene))

        for f in self.playlist_frames:
            if f.no in removed_frame_no:
                f.by = f.no
                removed_frame_no.remove(f.by)

        self.signal_replacements_refreshed.emit()
        self.signal_dsr_shapes_refreshed.emit()
        self.signal_scene_warps_refreshed.emit()
        self.signal_reload_frame.emit()
        print(f"modified_scenes: {self.replace_db.modified_scene_nos()}")
        self.send_modified_scene_signal()


    @Slot()
    def event_replace_undo(self):
        log.info("undo signal received")
        self.replace_db.undo()
        self.selection_replacements.clear()
        for scene_no in self.playlist_properties().scenes:
            scene: Scene = self.scenes[scene_no]
            self.selection_replacements.update(
                self.replace_db.scene_replacements(scene)
            )
        self.signal_replacements_refreshed.emit()
        self.signal_dsr_shapes_refreshed.emit()
        self.signal_scene_warps_refreshed.emit()
        self.signal_reload_frame.emit()
        self.send_modified_scene_signal()




    def event_replace_discard(self):
        log.info("discard modifications requested")
        self.selection_replacements.clear()
        for scene_no in self.playlist_properties().scenes:
            scene: Scene = self.scenes[scene_no]
            self.replace_db.discard(scene)
            self.selection_replacements.update(
                self.replace_db.scene_replacements(scene)
            )
        self.signal_replacements_refreshed.emit()
        self.signal_dsr_shapes_refreshed.emit()
        self.signal_scene_warps_refreshed.emit()
        self.signal_reload_frame.emit()
        print(f"modified_scenes: {self.replace_db.modified_scene_nos()}")
        self.send_modified_scene_signal()



    def get_nb_of_replacements(self, scene: Scene) -> int:
        return self.replace_db.get_nb_of_replacements(scene)



    # DSR
    def playlist_dsr(self, frame_no: int) -> list[DsrPatch]:
        # print(f"request playlist_dsr for frame: {frame_no}")
        patches: list[DsrPatch] = []
        scene_dsr: dict[int, list[DsrPatch]] = self.selection_dsr[self.current_scene_no]
        if frame_no in scene_dsr:
            patches = scene_dsr[frame_no]

        if -1 in scene_dsr.keys():
            # print(f"add shared patches for frame: {frame_no}")
            for p in scene_dsr[-1]:
                if p.start <= frame_no <= p.end:
                    if p not in patches:
                        patches.append(p)

        # pprint(patches)
        return patches



    @Slot(DsrAction)
    def event_dsr_modified(self, modification: DsrAction) -> None:
        scene_no: int = int(modification.frame.scene_key.split(':')[-1])
        scene: Scene = self.scenes[scene_no]

        print(yellow("dsr modification:"),
              f"{modification.type}: scene={scene_no}:{modification.frame.no}"
        )
        for r in modification.regions:
            print(r)

        # pprint(self.selection_dsr[scene_no])
        if modification.type == 'update':
            self.dsr_db.update_scene_dsr(
                scene=scene, modification=modification
            )
        print(yellow(f"refresh selection scene no. {scene_no}"))
        del self.selection_dsr[scene_no]
        self.selection_dsr.update(
            self.dsr_db.get_scene_dsr(scene=scene)
        )
        # self.selection_dsr.update(self.dsr_db.get_scene_dsr(scene))
        # print(yellow(f" -> "))
        # pprint(self.selection_dsr[scene_no])


        self.signal_dsr_shapes_refreshed.emit()
        # print(yellow(f"modified scenes: {self.dsr_db.modified_scene_nos()}"))
        self.send_modified_scene_signal()



    @Slot(DsrProcessParams)
    def event_dsr_process(self, params: DsrProcessParams) -> None:
        scene_no: int = int(self.current_frame.scene_key.split(':')[-1])
        scene: Scene = self.scenes[scene_no]
        self.dsr_db.update_scene_dsr(
            scene, DsrAction(type='set', parameter='detection', value=params)
        )

        log.info("Start detecting inner rect")
        start_time: int = time.time()


        elapsed_time = time.time() - start_time
        print(f"executed in {elapsed_time:.02f}s ({scene['dst']['count']/elapsed_time:.1f}fps)")

        self.signal_reload_frame.emit()



    @Slot()
    def event_dsr_undo(self):
        log.info("undo signal received")
        self.dsr_db.undo()
        # ...
        self.signal_reload_frame.emit()
        self.send_modified_scene_signal()


    @Slot()
    def event_dsr_discard(self):
        log.info("discard modifications requested")
        # ...
        self.signal_reload_frame.emit()
        print(f"modified_scenes: {self.dsr_db.modified_scene_nos()}")
        self.send_modified_scene_signal()



    def send_modified_scene_signal(self):
        modified_nos: list[int] = (
            self.replace_db.modified_scene_nos()
            + self.dsr_db.modified_scene_nos()
            + self.warp_db.modified_scene_nos()
        )
        self.signal_modified_scenes.emit(list(set(modified_nos)))



    @Slot()
    def event_replace_dsr_save(self):
        print(f"selected scenes: {self.playlist_properties().scenes}")
        print(self.replace_db.modified_scene_nos())
        for scene_no in self.playlist_properties().scenes:
            print(f"save no.{scene_no}")
            scene: Scene = self.current_selection.scenes[scene_no]
            self.replace_db.save(scene)
            self.dsr_db.save(scene)
            self.warp_db.save(scene)

        self.signal_is_saved.emit('replace')
        self.signal_is_saved.emit('dsr')
        self.signal_is_saved.emit('warp')
        self.send_modified_scene_signal()


    # WARP
    def playlist_warp(self) -> dict[int, Warp]:
        scene_warp: dict[int, Warp] = self.selection_warp[self.current_scene_no]
        return scene_warp


    def frame_warp(self, frame_no: int) -> Warp:
        print(f"request warp for frame: {frame_no}")
        scene_warp: dict[int, Warp] = self.selection_warp[self.current_scene_no]
        if frame_no in scene_warp:
            return scene_warp[frame_no]
        return None
    

    @Slot()
    def event_warp_modified(self, warp_action: WarpAction) -> None:
        # warp_action.frame
        print("event_warp_modified")

        scene_no: int = int(warp_action.frame.frame.scene_key.split(':')[-1])
        scene: Scene = self.scenes[scene_no]

        print(yellow("warp modification:"), f"warp: scene={scene_no}:{warp_action.frame.no}")
        self.warp_db.modify(
            scene=scene,
            src_scene_key=warp_action.frame.frame.src_scene_key,
            frame_no=warp_action.frame.no,
            warp=warp_action.warp
        )
        del self.selection_warp[scene_no]
        self.selection_warp.update(
            self.warp_db.get_scene_warp(scene=scene)
        )

        del self.selection_warp[scene_no]
        self.selection_warp.update(
            self.warp_db.get_scene_warp(scene)
        )
        self.signal_scene_warps_refreshed.emit()
        # self.signal_reload_frame.emit()
        print(f"modified_scenes: {self.warp_db.modified_scene_nos()}")
        self.send_modified_scene_signal()


    @Slot()
    def event_warp_process(self, frame: CurrentFrame) -> None:
        frame.frame.src_scene_key
        scene_no: int = int(frame.frame.scene_key.split(':')[-1])
        print(lightcyan(f"warp process: {scene_no}"))
        if frame.frame.no != frame.frame.by:
            print(f"   not to be warped")
            return
        else:
            print("   warp")
        # pprint(frame)

        print(self.playlist_properties().count)

        scene: Scene = self.scenes[scene_no]
        if frame.frame.i > self.playlist_properties().count:
            print(red(f"Cannot apply warp on next frame"))
            return
        
        # Get warp
        scene_no: int = int(frame.frame.scene_key.split(':')[-1])
        scene: Scene = self.scenes[scene_no]
        src_scene_key = frame.frame.src_scene_key
        pprint(self.warp_db.get_scene_warp(scene))


        # self.dsr_db.update_scene_dsr(
        #     scene, DsrAction(type='set', parameter='detection', value=params)
        # )

        # print(lightgreen("DSR db: modify src scene:"), src_scene_key)
        # if src_scene_key not in self._db:
        #     self._db[src_scene_key] = SceneDsr()


        # # self.scenes[frame.frame.src_scene_key]
        # src_scene: SrcScene = scene['src']
        # warp: Warp = self.warp_db.get_scene_warp(scene=scene, f_no=frame.frame.no)
        # print(warp)



