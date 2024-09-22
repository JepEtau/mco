
from pprint import pprint
from PySide6.QtCore import (
    Signal,
)

from ui.window_replace import ReplaceWindow

from .controller_common import CommonController
from .preferences import Preferences
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


    def __init__(self):
        super().__init__()

        # Load saved preferences
        self.preferences = Preferences(tool='replace')


        # Variables
        # self.model_database = Model_database()
        self.filepath = list()
        self.current_task = ''



    def set_view(self, view: ReplaceWindow):
        log.info("set view, connect signals")
        self.view = view

        # self.view.widget_selection.signal_selection_changed[dict].connect(self.selection_changed)
        # self.view.widget_selection.signal_selected_scene_changed[dict].connect(self.event_selected_scenes_changed)
        # self.view.widget_selection.signal_selected_step_changed[str].connect(self.event_selected_step_changed)

        self.view.widget_replace.signal_save.connect(self.event_replace_save_requested)
        self.view.widget_replace.signal_replace_modified[dict].connect(self.event_frame_replaced)

        # self.view.signal_preview_options_changed[dict].connect(self.event_preview_options_changed)
        # self.view.signal_save_and_close.connect(self.event_save_and_close_requested)

        # Force refresh of preview options
        p = self.preferences.get_preferences()
        k_ep = f"ep{
            (p['selection']['episode'])
            if p['selection']['episode'] != ''
            else ''
        }"

        self.current_selection = {
            'k_ep': '',
            'k_part': '',
            'scenes': None,
        }

        self.selection_changed({
            'k_ep': k_ep,
            'k_part': p['selection']['part'],
        })



    def selection_changed(self, values:dict):
        """ Directory or step has been changed, update the database, list all images,
            list all scenes
        """
        verbose = True
        if verbose:
            print(lightcyan("----------------------- selection_changed -------------------------"))
            pprint(values)
        k_ep_selected = values['k_ep']
        k_part_selected = values['k_part']

        self.current_task = values['k_step']

        if ((k_ep_selected == '' and k_part_selected == '')
            or (k_ep_selected != '' and k_part_selected == '')):
            log.info(f"no selected episode/part")
            return
        log.info(f"selection_changed: {k_ep_selected}:{k_part_selected}, {self.current_task}")

        if k_ep_selected != self.current_selection['k_ep']:
            parse_database(
                episode=k_ep_selected,
                lang='fr'
            )

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
        if k_part_selected in ('g_debut', 'g_fin'):
            db_video = db[k_part_selected]['video']
        else:
            db_video = db[k_ep_selected]['video']['target'][k_part_selected]

        if k_part_selected in credit_chapter_keys():
            k_ed_selected = ''
        else:
            k_ed_selected = db[k_ep_selected]['video']['target'][k_part_selected]['k_ed_src']


        # Walk through scenes
        scenes = db_video['scenes']
        log.info(f"consolidate all scenes: {k_ep_selected}:{k_part_selected}")
        for scene in scenes:
            self.consolidate_shot_for_video_editor(
                shot=scene,
            k_ep=k_ep_selected, k_part=k_part_selected
            )

        # Create a dict to update the "browser" part of the editor widget
        self.current_selection = {
            'k_ed': k_ed_selected,
            'k_ep': k_ep_selected,
            'k_part': k_part_selected,
            'scenes': self.scenes,
        }

        # for f in self.frames[shot_no]:
        #     print("%s" % f['filepath'])


        # print("selected: %s:%s:%s" % (k_ed_selected, k_ep_selected, k_part_selected))
        self.signal_scenes_modified.emit(self.current_selection)





