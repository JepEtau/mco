from __future__ import annotations
import sys
from typing import Any

import numpy as np
from import_parsers import *

from pprint import pprint
import time
from PySide6.QtCore import (
    Signal,
    Slot,
)

from nn_inference.toolbox.detect_inner_rect import detect_inner_rect
from tools.backend.geometry_database import GeometryDatabase

from ._types import (
    DetectInnerRectParams,
    GeometryAction,
    PlaylistProperties,
    Selection,
    TargetSceneGeometry,
)
from .frame_cache import FrameCache, Frame
from .common_controller import CommonController
from .user_preferences import UserPreferences
from logger import log
from ui.window_geometry import GeometryWindow
from utils.mco_types import Scene, SceneGeometry
from utils.p_print import *
from parsers import (
    db,
    TaskName
)


class GeometryController(CommonController):
    signal_preview_options_consolidated = Signal(dict)
    signal_replacements_refreshed = Signal()

    def __init__(self):
        super().__init__()

        # Load saved preferences
        self.user_preferences: UserPreferences = UserPreferences(tool='geometry')

        self.task_name: TaskName = 'hr'
        self.geometry_db = GeometryDatabase()
        self.frame_cache: FrameCache = FrameCache(replace_db=None)

        self.selection_geometry: dict[int, TargetSceneGeometry] = {}


    def set_view(self, view: GeometryWindow):
        super().set_view(view)

        # self.view.widget_geometry.signal_undo.connect(self.event_geometry_undo)
        # self.view.widget_geometry.signal_save.connect(self.event_geometry_save)
        # self.view.widget_geometry.signal_discard.connect(self.event_geometry_discard)
        self.view.widget_geometry.signal_geometry_modified.connect(self.event_geometry_modified)
        self.view.widget_geometry.signal_detect_inner_rect.connect(self.event_detect_inner_rect)


    def k_ep_p_changed(self, selection: Selection):
        super().k_ep_p_changed(selection)

        # Let's consolidate all geometry from all scenes
        log.info("Initialize geometry database")
        self.geometry_db.clear()
        self.geometry_db.initialize(self.selection())

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

        # Geometry
        self.selection_geometry.clear()
        for scene_no in selected['scenes']:
            scene: Scene = self.scenes[scene_no]
            self.selection_geometry.update(
                self.geometry_db.get_geometry(scene)
            )

        # self.signal_preview_options_consolidated.emit(self.preview_options)
        self.signal_ready_to_play.emit()


    def get_frame_at_index(self, index: int) -> tuple[Frame, Frame | None]:
        self.current_frame = self.playlist_frames[index]
        return self.current_frame, None


    def preview_modified(self, preview_settings: dict):
        self.preview_enabled = preview_settings['enabled']


    def get_scene_geometry(self, frame: Frame) -> TargetSceneGeometry:
        # print(lightcyan(f"get_scene_geometry: {frame.scene_key}, {frame.src_scene_key}"))
        return self.selection_geometry[frame.src_scene_key]


    @Slot(GeometryAction)
    def event_geometry_modified(self, modification: GeometryAction) -> None:
        scene_no: int = int(self.current_frame.scene_key.split(':')[-1])
        scene: Scene = self.scenes[scene_no]
        self.geometry_db.update_scene_geometry(scene, modification)
        self.selection_geometry.update(self.geometry_db.get_geometry(scene))
        self.signal_reload_frame.emit()


    @Slot(DetectInnerRectParams)
    def event_detect_inner_rect(self, params: DetectInnerRectParams) -> None:
        scene_no: int = int(self.current_frame.scene_key.split(':')[-1])
        scene: Scene = self.scenes[scene_no]
        self.geometry_db.update_scene_geometry(
            scene, GeometryAction(type='set', parameter='autocrop', value=params)
        )
        self.selection_geometry.update(self.geometry_db.get_geometry(scene))

        log.info("Start detecting inner rect")
        for f in self.frame_cache.get(scene=scene):
            # start a thread for detection
            coordinates, _ = detect_inner_rect(
                img=f.img,
                params=params
            )
            print(coordinates)

        log.info("Ended")
