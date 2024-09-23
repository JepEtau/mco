from __future__ import annotations

from pprint import pprint
import time
from PySide6.QtCore import (
    Signal,
)

from .db_helpers import consolidate_target
from ui.window_replace import ReplaceWindow

from .controller_common import CommonController
from .user_preferences import UserPreferences
from logger import log


from import_parsers import *
from utils.p_print import *
from parsers import (
    credit_chapter_keys,
    parse_database,
    key,
    db,
)


class ReplaceController(CommonController):
    signal_current_scene_modified = Signal(dict)
    signal_ready_to_play = Signal(dict)
    signal_reload_frame = Signal()
    signal_is_saved = Signal(str)

    signal_preview_options_consolidated = Signal(dict)
    signal_replace_list_refreshed = Signal(list)

    signal_scenelist = Signal(dict)


    def __init__(self):
        super().__init__()

        # Load saved preferences
        self.user_preferences: UserPreferences = UserPreferences(tool='replace')


        # Variables
        # self.model_database = Model_database()
        self.filepath = list()
        self.current_task = ''



    def set_view(self, view: ReplaceWindow):
        log.info("set view, connect signals")
        self.view = view

        self.view.widget_selection.signal_ep_p_changed[dict].connect(
            self.k_ep_p_changed
        )
        self.view.widget_selection.signal_selected_scene_changed[dict].connect(
            self.event_selected_scene_changed
        )
        # self.view.widget_selection.signal_selected_step_changed[str].connect(self.event_selected_step_changed)

        self.view.widget_replace.signal_save.connect(self.event_replace_save_requested)
        self.view.widget_replace.signal_replace_modified[dict].connect(self.event_frame_replaced)

        # self.view.signal_preview_options_changed[dict].connect(self.event_preview_options_changed)
        # self.view.signal_save_and_close.connect(self.event_save_and_close_requested)

        # Force refresh of preview options
        p = self.user_preferences.get_preferences()
        view.apply_user_preferences(p)

        self.parsed_episodes: list[str] = []
        k_ep = f"ep{
            (p['selection']['episode'])
            if p['selection']['episode'] != ''
            else ''
        }"
        self.current_selection = {
            'k_ep': '',
            'k_p': '',
            'scenes': None,
        }

        self.view.refresh_available_selection(
            self.get_available_episode_and_parts()
        )

        k_p: str = p['selection']['k_p']
        new_selection: dict[str, str] = {
            'k_ep': k_ep if k_ep not in ('', 'ep') else 'ep01',
            'k_p': k_p if k_p != '' else 'g_debut',
        }

        self.k_ep_p_changed(new_selection)



    def k_ep_p_changed(self, values:dict):
        """ Directory or step has been changed, update the database, list all images,
            list all scenes
        """
        print(lightcyan("----------------------- k_ep_p_changed -------------------------"))
        verbose = True
        if verbose:
            print(lightcyan("----------------------- k_ep_p_changed -------------------------"))
            pprint(values)
        k_ep_selected = values['k_ep']
        k_p_selected = values['k_p']

        if ((k_ep_selected == '' and k_p_selected == '')
            or (k_ep_selected != '' and k_p_selected == '')):
            log.info(f"no selected episode/part")
            return
        log.info(f"selection_changed: {k_ep_selected}:{k_p_selected}, {self.current_task}")

        if (
            k_ep_selected != self.current_selection['k_ep']
            and k_ep_selected not in self.parsed_episodes
        ):
            parse_database(
                episode=k_ep_selected,
                lang='fr'
            )
            consolidate_target(
                k_ep=k_ep_selected,
                task='lr'
            )

            self.parsed_episodes.append(k_ep_selected)


        # self.model_database.consolidate_database(
        #     k_ep=k_ep_selected,
        #     k_part=k_part_selected
        # )
        # NOTE replace: model contains the list of frames to replace

        # self.scenes is a pointer to the scenes for this episode/part
        # db = self.model_database.database()


        # Remove all frames
        self.frames.clear()

        # This will contains all scenes for this part
        self.scenes.clear()

        # Contains all path of frames for this part
        self.filepath.clear()

        # Get video db
        if k_p_selected in ('g_debut', 'g_fin'):
            db_video = db[k_p_selected]['video']
        else:
            db_video = db[k_ep_selected]['video']['target'][k_p_selected]

        if k_p_selected in credit_chapter_keys():
            k_ed_selected = ''
        else:
            k_ed_selected = db[k_ep_selected]['video']['target'][k_p_selected]['k_ed_src']


        # Create a dict to update the "browser" part of the editor widget
        self.current_selection = {
            'k_ed': k_ed_selected,
            'k_ep': k_ep_selected,
            'k_p': k_p_selected,
            'scenes': db_video['scenes'],
            'invalid': [],
        }

        # for f in self.frames[scene_no]:
        #     print("%s" % f['filepath'])


        # print("selected: %s:%s:%s" % (k_ed_selected, k_ep_selected, k_part_selected))
        self.signal_scenelist.emit(self.current_selection)






    def event_selected_scene_changed(self, selected: dict):
        log.info(f"select {len(selected['scenes'])} scenes, start:{selected['scenes'][0]}")
        verbose = True
        if verbose:
            print(lightgreen(f"selected scenes: {selected['k_ep']}:{selected['k_p']}, %s" % (
                ','.join(map(lambda x: str(x), selected['scenes'])))))

        log.info(f"selected scenes: {selected['k_ep']}:{selected['k_p']}, %s" % (
            ','.join(map(lambda x: str(x), selected['scenes']))))

        if len(selected['scenes']) == 0:
            return

        scene = self.current_scene()
        print("selected:", selected)

        # Create a list of frames for each selected scene
        frame_nos = []
        index = 0
        ticklist = [0]
        self.playlist_frames.clear()

        for scene_no in selected['scenes']:
            # mmmmh what??? should use self.scene
            frames = self.frames[scene_no]
            for index, frame in zip(range(len(frames)), frames):
                frame['index'] = index
                self.playlist_frames.append(frame)
                frame_nos.append(frame['frame_no'])

            ticklist.append(ticklist[-1] + len(self.frames[scene_no]))


        # Load images
        if verbose:
            print(lightgrey("\tload images:", end=' '))
            start_time = time.time()

        for scene_no in selected['scenes']:
            print(f"scene no. {scene_no}: load frames")

        if verbose:
            print(lightgrey(f"{time.time() - start_time:.1f}s"))


        # Update each frame
        for scene_no in selected['scenes']:
            scene = self.scenes[scene_no]

            # Replace
            self.refresh_replace_for_each_frame(scene=scene)

        if verbose and True:
            print(lightcyan("================================== scene ======================================="))
            pprint(self.scenes[0])
            print(lightcyan("-------------------------------------------------------------------------------"))


        self.playlist_properties.update({
            'frame_nos': frame_nos,
            'count': len(self.playlist_frames),
            'ticks': ticklist,
            'scenes': selected['scenes'],
        })

        # Set current to None to refresh widgets
        self.current_frame = None

        self.current_scene_no = selected['scenes'][0]
        scene = self.current_scene()
        scene_no = scene['no']


        # Replace
        self.refresh_replace_list()


        self.signal_preview_options_consolidated.emit(self.preview_options)
        log.info(f"selected scenes: scene is ready to play")
        self.signal_ready_to_play.emit(self.playlist_properties)





    # Replace frames
    #---------------------------------------------------------------------------
    def refresh_replace_list(self):
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

        self.signal_replace_list_refreshed.emit(list_replace)


    def refresh_replace_for_each_frame(self, scene):
        log.info(f"refresh replaced frame for each frame of scene {scene['no']}")
        for frame in self.frames[scene['no']]:
            frame['replaced_by']: self.model_database.get_replace_frame_no(scene=scene, frame_no=frame['frame_no'])



    def get_replace_frame_no_str(self, index) -> str:
        # print("get_replace_frame_no_str: %d" % (index))
        frame_no = self.playlist_frames[index]['frame_no']
        scene_no = self.playlist_frames[index]['scene_no']
        new_frame_no = self.model_database.get_replace_frame_no(scene_no, frame_no)
        # print("get_replace_frame_no: %d -> %d" % (frame_no, new_frame_no))
        if new_frame_no != -1:
            return str(new_frame_no)
        return ''


    def get_next_replaced_frame_index(self, index):
        # TODO: replace this: use the list_replace
        # print("find following replaced frame")

        # print("\tsearch in %d -> %d" % (frame_no + 1, self.playlist_properties['start'] + self.playlist_properties['count']))
        for i in range(index + 1, self.playlist_properties['count']):
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


    def event_frame_replaced(self, replace:dict):
        print(f"event_frame_replaced: {self.preview_options['replace']['allowed']}")
        action = replace['action']
        frame_no = replace['dst']
        log.info("replace %d" % (frame_no))
        print("scene no= %d" % (self.current_frame['scene_no']))
        # pprint(self.playlist_frames)
        scene = self.current_scene()
        scene_no = scene['no']
        index = frame_no - self.frames[scene_no][0]['frame_no']

        if action == 'replace':
            log.info(f"replace: scene no. {scene_no}, frame {frame_no} (index {index}) by {replace['src']}")

            # If the src frame is already replaced, use the src of this frame
            frame_no_src = self.model_database.get_replace_frame_no(scene, replace['src'])
            if frame_no_src == -1:
                frame_no_src = replace['src']

            self.model_database.set_replaced_frame(
                scene=scene,
                frame_no=frame_no,
                new_frame_no=frame_no_src)

        elif action == 'remove':
            log.info(f"remove: scene no. {scene_no}, frame {frame_no} (index {index})")
            self.model_database.remove_replaced_frame(scene=scene, frame_no=frame_no)


        self.current_frame['replaced_by'] = self.model_database.get_replace_frame_no(scene=scene, frame_no=frame_no)

        self.set_modification_status('replace', True)
        self.signal_scene_modified.emit({'scene_no': scene['no'], 'modifications': scene['modifications']})


        self.refresh_replace_list()
        self.signal_reload_frame.emit()


    def event_replace_discard_requested(self):
        log.info("discard modifications requested")
        self.model_database.discard_replace_modifications()
        self.refresh_replace_list()
        self.set_modification_status('replace', False)
        self.signal_reload_frame.emit()


    def event_replace_save_requested(self):
        self.model_database.save_replace_database()
        self.signal_is_saved.emit('replace')
        self.set_modification_status('replace', False)

