from __future__ import annotations
import sys
from typing import override

import numpy as np

from pprint import pprint
import time
from PySide6.QtCore import (
    Signal,
    Slot,
)

from processing.detect_inner_rect import detect_inner_rect
from tools.backend.deshake_database import DeshakeDatabase
from video.consolidate_scenes import get_chapter_video

from ._types import (
    DeshakeAction,
    PlaylistProperties,
    Selection,
    TargetSceneDeshake,
)
from .frame_cache import FrameCache, Frame
from .common_controller import CommonController
from .user_preferences import UserPreferences
from logger import log
from ui.window_deshake import DeshakeWindow
from utils.mco_types import ChapterVideo, Scene
from utils.p_print import *
from parsers import (
    db,
    TaskName,
)


class DeshakeController(CommonController):
    signal_preview_options_consolidated = Signal(dict)
    signal_replacements_refreshed = Signal()

    def __init__(self, task_name: bool = False):
        super().__init__()

        # Load saved preferences
        self.user_preferences: UserPreferences = UserPreferences(tool='deshake')

        self.task_name: TaskName = task_name
        self.deshake_db = DeshakeDatabase()
        self.frame_cache: FrameCache = FrameCache(replace_db=None)

        self.selection_deshake: dict[int, TargetSceneDeshake] = {}


    def set_view(self, view: DeshakeWindow):
        super().set_view(view)

        self.view: DeshakeWindow

        # self.view.widget_deshake.signal_undo.connect(self.event_deshake_undo)
        # self.view.widget_deshake.signal_save.connect(self.event_deshake_save)
        # self.view.widget_deshake.signal_discard.connect(self.event_deshake_discard)
        self.view.widget_deshake.signal_deshake_modified.connect(self.event_deshake_modified)
        self.view.widget_deshake.signal_detect_inner_rect.connect(self.event_detect_inner_rect)
        self.view.widget_deshake.signal_save.connect(self.event_deshake_save)


    @override
    def exit(self, force: bool = False):
        if len(self.deshake_db.modified_scene_nos()) > 0 and not force:
            self.signal_save_before_exit.emit()
        else:
            super().exit()


    def k_ep_p_changed(self, selection: Selection):
        super().k_ep_p_changed(selection)

        # Let's consolidate all deshake from all scenes
        log.info("Initialize deshake database")
        selection: Selection = self.selection()
        self.deshake_db.clear()
        self.deshake_db.initialize(selection)
        self.signal_selection_modified.emit()


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
        print("selected:", selected)

        # Create a list of frames for each selected scene
        frame_nos = []
        ticklist = [0]

        # Modify frame cache for scene after upscale
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

        # Deshake
        self.selection_deshake.clear()
        for scene_no in selected['scenes']:
            scene: Scene = self.scenes[scene_no]
            self.selection_deshake.update(
                self.deshake_db.get_deshake(scene)
            )

        # self.signal_preview_options_consolidated.emit(self.preview_options)
        self.signal_ready_to_play.emit()


    def get_frame_at_index(self, index: int) -> tuple[Frame, Frame | None]:
        self.current_frame = self.playlist_frames[index]
        return self.current_frame, None


    def preview_modified(self, preview_settings: dict):
        self.preview_enabled = preview_settings['enabled']


    def get_scene_deshake(self, frame: Frame) -> TargetSceneDeshake:
        # print(lightcyan(f"get_scene_deshake: {frame.scene_key}, {frame.src_scene_key}"))
        return self.selection_deshake[frame.scene_key]


    @Slot(DeshakeAction)
    def event_deshake_modified(self, modification: DeshakeAction) -> None:
        print("deshake modification:", modification)
        scene_no: int = int(self.current_frame.scene_key.split(':')[-1])
        scene: Scene = self.scenes[scene_no]
        self.deshake_db.update_scene_deshake(scene, modification)
        new_deshake = self.deshake_db.get_deshake(scene)
        self.selection_deshake.update(new_deshake)
        k = list(new_deshake.keys())[0]
        self.deshake_stats.update(
            {'no': scene_no, 'deshake': new_deshake[k].scene}
        )
        # TODO: update erroneous margins
        self.signal_reload_frame.emit()
        print(yellow(f"modified scenes: {self.deshake_db.modified_scene_nos()}"))
        self.signal_modified_scenes.emit(self.deshake_db.modified_scene_nos())


    @Slot(DetectInnerRectParams)
    def event_detect_inner_rect(self, params: DetectInnerRectParams) -> None:
        scene_no: int = int(self.current_frame.scene_key.split(':')[-1])
        scene: Scene = self.scenes[scene_no]
        self.deshake_db.update_scene_deshake(
            scene, DeshakeAction(type='set', parameter='detection', value=params)
        )

        log.info("Start detecting inner rect")
        coordinates: list[np.ndarray] = []
        pprint(params)
        start_time: int = time.time()
        for i, f in enumerate(self.frame_cache.get(scene=scene)):
            # start a thread for detection
            coords, _ = detect_inner_rect(
                img=f.img,
                params=params,
                index=i,
                do_output_img=False,
            )
            coordinates.append(coords)

        elapsed_time = time.time() - start_time
        in_h, in_w = f.img.shape[:2]

        pprint(coordinates)
        print("min:", np.min(coordinates, axis=0))
        print("max:", np.max(coordinates, axis=0))
        print("in_shape:", f.img.shape[:2])
        min_coords: np.ndarray = np.min(coordinates, axis=0)
        max_coords: np.ndarray = np.max(coordinates, axis=0)
        x0, x1 = max_coords[0], min_coords[1]
        y0, y1 = max_coords[2], min_coords[3]
        autocrop = [y0,  in_h - y1, x0, in_w - x1]
        print(yellow("final, autocrop:"), f"{autocrop}")
        print(f"executed in {elapsed_time:.02f}s ({scene['dst']['count']/elapsed_time:.1f}fps)")

        self.deshake_db.update_scene_deshake(
            scene,
            DeshakeAction(type='set', parameter='autocrop', value=autocrop)
        )

        new_deshake = self.deshake_db.get_deshake(scene)
        k = list(new_deshake.keys())[0]
        self.deshake_stats.update(
            {'no': scene_no, 'deshake': new_deshake[k].scene}
        )
        self.signal_reload_frame.emit()


    @Slot()
    def event_deshake_save(self):
        print(f"selected scenes: {self.playlist_properties().scenes}")
        print(self.deshake_db.modified_scene_nos())
        for scene_no in self.playlist_properties().scenes:
            print(f"save no.{scene_no}")
            scene: Scene = self.current_selection.scenes[scene_no]
            self.deshake_db.save(scene)

        self.signal_is_saved.emit('deshake_db')
        print(f"modified_scenes: {self.deshake_db.modified_scene_nos()}")
        self.signal_modified_scenes.emit(self.deshake_db.modified_scene_nos())
