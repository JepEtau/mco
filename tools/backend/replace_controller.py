from __future__ import annotations
from import_parsers import *

from pprint import pprint
import time
from PySide6.QtCore import (
    Signal,
    Slot,
)

from ._types import PlaylistProperties, ReplaceAction, Selection
from .replace_database import ReplaceDatabase
from .frame_cache import FrameCache, Frame
from .db_helpers import consolidate_target
from .controller_common import CommonController
from .user_preferences import UserPreferences
from logger import log
from ui.window_replace import ReplaceWindow

from utils.mco_types import Scene
from utils.p_print import *
from parsers import (
    parse_database,
    key,
    db,
)


class ReplaceController(CommonController):
    signal_current_scene_modified = Signal(dict)
    signal_ready_to_play = Signal()
    signal_reload_frame = Signal()
    signal_is_saved = Signal(str)

    signal_preview_options_consolidated = Signal(dict)
    signal_replacements_refreshed = Signal()

    signal_selection_modified = Signal()
    signal_error = Signal(str)

    signal_modified_scenes = Signal(list)


    def __init__(self):
        super().__init__()

        # Load saved preferences
        self.user_preferences: UserPreferences = UserPreferences(tool='replace')


        # Variables
        # self.model_database = Model_database()
        self.filepath = list()
        self.current_task = ''
        self.replace_db = ReplaceDatabase()
        self.frame_cache: FrameCache = FrameCache(self.replace_db)
        self.playlist_frames: list[Frame] = []
        self.replacements: dict[int, dict[int, int]] = {}
        self.preview_enabled: bool = True
        self.current_frame: Frame | None = None



    def set_view(self, view: ReplaceWindow):
        log.info("set view, connect signals")
        self.view = view

        self.view.widget_selection.signal_ep_p_changed[Selection].connect(
            self.k_ep_p_changed
        )
        self.view.widget_selection.signal_selected_scene_changed[dict].connect(
            self.event_selected_scene_changed
        )
        # self.view.widget_selection.signal_selected_step_changed[str].connect(self.event_selected_step_changed)

        self.view.widget_replace.signal_replace_modified[ReplaceAction].connect(self.event_frame_replaced)
        self.view.widget_replace.signal_replace_removed.connect(
            self.event_replace_removed
        )
        self.view.widget_replace.signal_undo.connect(self.event_replace_undo)
        self.view.widget_replace.signal_save.connect(self.event_replace_save)
        self.view.widget_replace.signal_discard.connect(self.event_replace_discard)


        # self.view.signal_save_and_close.connect(self.event_save_and_close_requested)

        self.view.signal_preview_modified[dict].connect(self.preview_modified)

        # Force refresh of preview options
        p = self.user_preferences.get_preferences()
        view.apply_user_preferences(p)
        pprint(p)

        self.parsed_episodes: list[str] = []


        self.view.refresh_available_selection(
            self.get_available_episode_and_parts()
        )

        self.current_selection = Selection(
            k_ep='', k_ch=''
        )
        k_ep = key(p['selection']['episode'])
        k_ch: str = p['selection']['k_ch']
        new_selection: Selection = Selection(
            k_ep=k_ep if k_ep not in ('', 'ep') else 'ep01',
            k_ch=k_ch if k_ch != '' else 'g_debut',
        )

        self.k_ep_p_changed(new_selection)



    def k_ep_p_changed(self, selection: Selection):
        """ Directory or step has been changed, update the database, list all images,
            list all scenes
        """
        print(lightcyan("----------------------- k_ep_p_changed -------------------------"))
        verbose = True
        if verbose:
            print(lightcyan("----------------------- k_ep_p_changed -------------------------"))
            pprint(selection)

        if ((selection.k_ep == '' and selection.k_ch == '')
            or (selection.k_ep != '' and selection.k_ch == '')):
            log.info(f"no selected episode/part")
            return
        log.info(f"selection_changed: {selection.k_ep}:{selection.k_ch}, {selection.task}")

        if (
            selection.k_ep != self.current_selection.k_ep
            and selection.k_ep not in self.parsed_episodes
        ):
            parse_database(
                episode=selection.k_ep,
                lang='fr'
            )
            consolidate_target(
                k_ep=selection.k_ep,
                task='lr'
            )

            self.parsed_episodes.append(selection.k_ep)

        # Remove all frames
        self.frames.clear()

        # Get video db
        if selection.k_ch in ('g_debut', 'g_fin'):
            db_video = db[selection.k_ch]['video']
        else:
            db_video = db[selection.k_ep]['video']['target'][selection.k_ch]

        self.scenes = db_video['scenes']

        # Create a dict to update the "browser" part of the editor widget
        self.current_selection = Selection(
            k_ep=selection.k_ep,
            k_ch=selection.k_ch,
            task='lr',
            scenes=self.scenes,
        )
        self.signal_selection_modified.emit()
        self.signal_modified_scenes.emit(self.replace_db.modified_scene_nos())


    def selection(self) -> Selection:
        # Return current selection and scene list
        return self.current_selection



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
        index = 0
        ticklist = [0]
        # self.playlist_frames.clear()

        self.playlist_frames.clear()
        # Load images
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


        # Replace
        self.replacements.clear()
        for scene_no in selected['scenes']:
            scene: Scene = self.scenes[scene_no]
            self.replacements.update(
                self.replace_db.get_replacements(scene)
            )

        self.signal_replacements_refreshed.emit()
        # self.signal_preview_options_consolidated.emit(self.preview_options)
        self.signal_ready_to_play.emit()


    def playlist_properties(self) -> PlaylistProperties:
        return self._playlist_properties


    def playlist_replacements(self) -> dict[int, dict[int, int]]:
        return self.replacements


    def get_index_from_frame_no(self, frame_no):
        return self._playlist_properties.frame_nos.index(frame_no)


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


    def preview_modified(self, preview_settings: dict):
        self.preview_enabled = preview_settings['enabled']



    def is_frame_used_for_replace(self, frame: Frame) -> bool:
        scene_no = int(frame.scene_key.split(':')[-1])
        return bool(frame.no in list(self.replacements[scene_no].values()))


    @Slot(ReplaceAction)
    def event_frame_replaced(self, replace: ReplaceAction):
        print(yellow("event_frame_replaced"))
        pprint(replace)

        scene_no: int = int(replace.current.scene_key.split(':')[-1])
        # if isinstance(replace.by, Frame):
        log.info(f"replace: {replace.current.no} <- {replace.by.no}")
        by: int = (
            replace.by.by
            if replace.by.by != replace.current.no
            else replace.by.no
        )
        log.info(f"replace (consolidated): {replace.current.no} <- {by}")

        scene: Scene = self.scenes[scene_no]
        self.replace_db.add(
            scene,
            replace.current.src_scene_key,
            replace.current.no,
            by
        )
        replace.current.by = replace.by.no

        print(self.replace_db.modified_scene_nos())
        del self.replacements[scene_no]
        self.replacements.update(self.replace_db.get_replacements(scene))
        self.signal_replacements_refreshed.emit()
        self.signal_reload_frame.emit()
        print(f"modified_scenes: {self.replace_db.modified_scene_nos()}")
        self.signal_modified_scenes.emit(self.replace_db.modified_scene_nos())


    @Slot(dict)
    def event_replace_removed(self, remove_dict: dict[str, list[int]]) -> None:
        removed_frame_no: list[int] = []
        for scene_no, frame_nos in remove_dict.items():
            removed_frame_no.extend(frame_nos)
            scene_no = int(scene_no)
            scene: Scene = self.scenes[scene_no]
            self.replace_db.remove_multiple(scene, frame_nos)
            del self.replacements[scene_no]
            self.replacements.update(self.replace_db.get_replacements(scene))

        for f in self.playlist_frames:
            if f.no in removed_frame_no:
                f.by = f.no
                removed_frame_no.remove(f.by)

        print(self.replace_db.modified_scene_nos())
        self.signal_replacements_refreshed.emit()
        self.signal_reload_frame.emit()
        print(f"modified_scenes: {self.replace_db.modified_scene_nos()}")
        self.signal_modified_scenes.emit(self.replace_db.modified_scene_nos())


    @Slot()
    def event_replace_undo(self):
        log.info("undo signal received")
        self.replace_db.undo()
        self.replacements.clear()
        for scene_no in self.playlist_properties().scenes:
            scene: Scene = self.scenes[scene_no]
            self.replacements.update(
                self.replace_db.get_replacements(scene)
            )
        self.signal_replacements_refreshed.emit()
        self.signal_reload_frame.emit()
        self.signal_modified_scenes.emit(self.replace_db.modified_scene_nos())


    @Slot()
    def event_replace_save(self):
        print(f"selected scenes: {self.playlist_properties().scenes}")
        print(self.replace_db.modified_scene_nos())
        for scene_no in self.playlist_properties().scenes:
            print(f"save no.{scene_no}")
            scene: Scene = self.current_selection.scenes[scene_no]
            self.replace_db.save(scene)

        self.signal_is_saved.emit('replace')
        print(f"modified_scenes: {self.replace_db.modified_scene_nos()}")
        self.signal_modified_scenes.emit(self.replace_db.modified_scene_nos())



    def event_replace_discard(self):
        log.info("discard modifications requested")
        self.replacements.clear()
        for scene_no in self.playlist_properties().scenes:
            scene: Scene = self.scenes[scene_no]
            self.replace_db.discard(scene)
            self.replacements.update(
                self.replace_db.get_replacements(scene)
            )
        self.signal_replacements_refreshed.emit()
        self.signal_reload_frame.emit()
        print(f"modified_scenes: {self.replace_db.modified_scene_nos()}")
        self.signal_modified_scenes.emit(self.replace_db.modified_scene_nos())





    # Replace frames
    #---------------------------------------------------------------------------
    def refresh_replace_widget(self):
        verbose = False
        # List of frames to replace
        log.info("refresh list")
        if verbose:
            print(lightcyan("Refresh replace list"))
            pprint(self.model_database.db_replaced_frames_initial)


        list_replace = list()

        for frame in self.playlist_frames:
            scene = self.scenes[frame['scene_no']]
            frame_no = self.model_database.get_replace_frame_no(
                scene=scene, frame_no=frame['frame_no'])
            if frame_no != -1:
                list_replace.append({
                    'scene_no': frame['scene_no'],
                    'src': frame_no,
                    'dst': frame['frame_no'],
                })
        if verbose:
            print(f"send signal to refresh replace list widget:")
            pprint(list_replace)

        self.signal_replacements_refreshed.emit(list_replace)



    def get_next_replaced_frame_index(self, index):
        # TODO: replace this: use the list_replace
        # print("find following replaced frame")

        # print("\tsearch in %d -> %d" % (frame_no + 1, self.playlist_properties['start'] + self.playlist_properties['count']))
        for i in range(index + 1, self._playlist_properties['count']):
            scene_no = self.get_scene_no_from_index(i)
            scene = self.scenes[scene_no]
            frame_no = scene['start'] + i
            if self.model_database.get_replace_frame_no(scene, frame_no) != -1:
                return i

        # print("\tsearch in %d -> %d" % (self.playlist_properties['start'], frame_no-1))
        for i in range(0, index-1):
            scene_no = self.get_scene_no_from_index(i)
            scene = self.scenes[scene_no]
            frame_no = scene['start'] + i
            if self.model_database.get_replace_frame_no(scene_no, frame_no) != -1:
                return i
        return -1





