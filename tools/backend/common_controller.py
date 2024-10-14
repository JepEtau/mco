from __future__ import annotations
from pprint import pprint
from PySide6.QtCore import (
    QObject,
    Signal,
    Slot,
)
from abc import ABC, abstractmethod, ABCMeta
from ui.window_common import CommonWindow
from ._types import PlaylistProperties, Selection
from .frame_cache import Frame
from .db_helpers import consolidate_target
from .user_preferences import UserPreferences
from logger import log
from utils.p_print import *
from parsers import (
    parse_database,
    all_chapter_keys,
    key,
    db,
    TaskName
)

class QMeta(ABCMeta, type(QObject)):
    def __new__(mcls, name, bases, namespace, **kwargs):
        cls = ABCMeta.__new__(mcls, name, bases, namespace, **kwargs)
        return cls


class CommonController(QObject, metaclass=QMeta):
    signal_current_scene_modified = Signal(dict)
    signal_ready_to_play = Signal()
    signal_reload_frame = Signal()
    signal_is_saved = Signal(str)
    signal_close = Signal()
    signal_selection_modified = Signal()
    signal_modified_scenes = Signal(list)
    signal_error = Signal(str)


    def __init__(self):
        super().__init__()
        self.view = None

        self.task_name: TaskName = 'lr'

        self.user_preferences: UserPreferences = None
        self.parsed_episodes: list[str] = []
        self._playlist_properties: PlaylistProperties = PlaylistProperties()
        self.playlist_frames: list[Frame] = []

        self.current_selection: Selection = None
        self.current_scene_no: int = 0
        self.current_frame: Frame | None = None

        self.preview_enabled: bool = True
        self.preview_options = None


    def exit(self):
        # print("%s:exit" % (__name__))
        p = self.view.get_user_preferences()
        self.user_preferences.save(p)
        try:
            log.handlers[0].close()
        except:
            pass
        # print("model: exit")


    # def apply_user_preferences(self, user_preferences:dict):
    #     try:
    #         s = user_preferences['window_main']
    #         self.setGeometry(s['geometry'][0],
    #             s['geometry'][1],
    #             s['geometry'][2],
    #             s['geometry'][3])
    #     except:
    #         pass
    #     self.setGeometry(100,100,2000,800)


    def get_user_preferences(self):
        p = self.user_preferences.get_preferences()
        return p


    def save_preferences(self, preferences:dict):
        preferences = self.view.get_user_preferences()
        self.user_preferences.save(preferences)


    def get_available_episode_and_parts(self) -> dict[str, list]:
        episode_and_parts: dict[str, list] = {}
        for no in range(1, 40):
            k_ep = key(no)
            # if os.path.exists(os.path.join(path_cache, k_ep)):
            episode_and_parts[k_ep] = list(all_chapter_keys())

        episode_and_parts['ep01'].remove('precedemment')
        episode_and_parts['ep39'].remove('g_asuivre')
        episode_and_parts['ep39'].remove('asuivre')

        return episode_and_parts


    def set_view(self, view: type[CommonWindow]):
        log.info("set view, connect signals")
        self.view = view

        self.view.widget_selection.signal_ep_p_changed[Selection].connect(
            self.k_ep_p_changed
        )
        self.view.widget_selection.signal_selected_scene_changed[dict].connect(
            self.event_selected_scene_changed
        )
        # self.view.widget_selection.signal_selected_step_changed[str].connect(self.event_selected_step_changed)

        # self.view.signal_save_and_close.connect(self.event_save_and_close_requested)

        self.view.signal_preview_modified[dict].connect(self.preview_modified)

        # Force refresh of preview options
        p = self.user_preferences.get_preferences()
        view.apply_user_preferences(p)
        pprint(p)


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
                lang='fr',
            )
            consolidate_target(
                k_ep=selection.k_ep,
                task=self.task_name
            )
            self.parsed_episodes.append(selection.k_ep)

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


    @abstractmethod
    def event_selected_scene_changed(self, selected: dict) -> None: ...


    def selection(self) -> Selection:
        # Return current selection and scene list
        return self.current_selection


    def playlist_properties(self) -> PlaylistProperties:
        return self._playlist_properties


    def current_scene(self):
        try:
            return self.scenes[self.current_scene_no]
        except:
            print(orange("\tget current scene: current scene is None"))
            log.warning("get current scene: current scene is None")
            pass
        # self.scenes[self.current_frame['scene_no']]
        return None


    def get_index_from_frame_no(self, frame_no):
        return self._playlist_properties.frame_nos.index(frame_no)


    def get_frame_at_index(self, index: int) -> tuple[Frame, Frame | None]:
        return self.playlist_frames[index], None
