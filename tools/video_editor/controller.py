# -*- coding: utf-8 -*-
import sys

from utils.nested_dict import nested_dict_set
sys.path.append('../scripts')

from copy import deepcopy
import cv2
import gc
import os
import os.path
import time
import multiprocessing
from multiprocessing import *
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

from pprint import pprint
from logger import log
from utils.pretty_print import *

from PySide6.QtCore import (
    Signal,
)

from common.preferences import Preferences
from models.model_database import Model_database

from common.controller_common import Controller_common
from video_editor.controller_rgb import Controller_rgb
from video_editor.controller_replace import Controller_replace
from video_editor.controller_geometry import Controller_geometry
from shot.consolidate_shot import consolidate_shot

from filters.deshake import (
    consolidate_stabilize_segments,
    deshake,
    verify_stabilize_segments
)
from filters.deshakers import STABILIZE_BORDER_HIGH_RES
from filters.filters import calculate_geometry_parameters
from filters.utils import (
    is_stabilize_task_enabled
)
from utils.common import K_GENERIQUES
from utils.get_frame_list import (
    get_frame_list,
    get_frame_list_single
)
from video_editor.generate_image import generate_image


class Controller_video_editor(Controller_common,
                                Controller_rgb,
                                Controller_replace,
                                Controller_geometry):
    signal_current_shot_modified = Signal(dict)
    signal_ready_to_play = Signal(dict)
    signal_is_modified = Signal(dict)
    signal_reload_frame = Signal()
    signal_is_saved = Signal(str)

    signal_stabilize_settings_refreshed = Signal(dict)
    signal_stabilization_done = Signal()

    signal_preview_options_consolidated = Signal(dict)



    WIDGET_LIST = [
        'controls',
        'replace',
        'geometry',
        'curves',
        'stabilize',
        'selection',
    ]

    SELECTABLE_WIDGET_LIST = [
        'curves',
        'replace',
        'geometry',
        'stabilize',
    ]

    def __init__(self):
        super(Controller_video_editor, self).__init__()
        Controller_rgb.__init__(self)
        Controller_replace.__init__(self)
        Controller_geometry.__init__(self)

        # Load saved preferences
        self.preferences = Preferences(
            tool='video_editor',
            widget_list=self.WIDGET_LIST)

        # Variables
        self.model_database = Model_database()
        self.filepath = list()
        self.current_task = ''

    def set_view(self, view):
        self.view = view

        self.view.widget_selection.signal_selection_changed[dict].connect(self.selection_changed)
        self.view.widget_selection.signal_selected_shots_changed[dict].connect(self.event_selected_shots_changed)

        self.view.widget_geometry.signal_save.connect(self.event_save_geometry_requested)
        self.view.widget_geometry.signal_discard.connect(self.event_geometry_discard_requested)
        self.view.widget_geometry.signal_geometry_modified[dict].connect(self.event_geometry_modified)

        self.view.widget_replace.signal_save.connect(self.event_replace_save_requested)
        self.view.widget_replace.signal_discard.connect(self.event_replace_discard_requested)
        self.view.widget_replace.signal_replace_modified[dict].connect(self.event_frame_replaced)

        self.view.widget_curves.widget_rgb_graph.signal_graph_modified[dict].connect(self.event_rgb_graph_modified)
        self.view.widget_curves.widget_curves_selection.signal_curves_selection_changed[str].connect(self.event_curves_selection_changed)
        self.view.widget_curves.signal_save_rgb_curves_as[dict].connect(self.event_save_rgb_curves_as)
        self.view.widget_curves.widget_curves_selection.signal_save_curves_selection_requested.connect(self.event_save_curves_selection_requested)
        self.view.widget_curves.widget_curves_selection.signal_discard_curves[str].connect(self.event_discard_rgb_curves_modifications)

        self.view.widget_stabilize.signal_settings_modified[dict].connect(self.event_stabilize_modified)
        self.view.widget_stabilize.signal_save.connect(self.event_stabilize_save_requested)
        self.view.widget_stabilize.signal_stabilization_requested.connect(self.event_stabilization_requested)


        self.view.signal_preview_options_changed[dict].connect(self.event_preview_options_changed)
        self.view.signal_save_and_close.connect(self.event_save_and_close_requested)

        # Force refresh of preview options
        p = self.preferences.get_preferences()
        k_ep = 'ep%02d' % (p['selection']['episode']) if p['selection']['episode'] != '' else ''
        self.selection_changed({
            'k_ep': k_ep,
            'k_part': p['selection']['part'],
            'k_step': p['selection']['step'],
        })


    # Select a new episode/part
    #---------------------------------------------------------------------------

    def selection_changed(self, values:dict):
        """ Directory or step has been changed, update the database, list all images,
            list all shots
        """
        print_lightcyan("----------------------- selection_changed -------------------------")
        pprint(values)
        k_ep_selected = values['k_ep']
        k_part_selected = values['k_part']
        task = 'deinterlace' if values['k_step'] == '' else values['k_step']

        self.current_task = values['k_step']

        if ((k_ep_selected == '' and k_part_selected == '')
            or (k_ep_selected != '' and k_part_selected == '')):
            log.info(f"no selected episode/part")
            return
        log.info(f"directory_changed: {k_ep_selected}:{k_part_selected}, {self.current_task}")

        self.model_database.consolidate_database(
            k_ep=k_ep_selected,
            k_part=k_part_selected)
        # NOTE replace: model contains the list of frames to replace

        # self.shots is a pointer to the shots for this episode/part
        db = self.model_database.database()

        p_missing_frame = os.path.join('icons', 'missing.png')

        # Remove all frames
        self.frames.clear()

        # This will contains all shots for this part
        self.shots.clear()

        # Contains all path of frames for this part
        self.filepath.clear()

        # Get video db
        if k_part_selected in ['g_debut', 'g_fin']:
            db_video = db[k_part_selected]['video']
        else:
            db_video = db[k_ep_selected]['video']['target'][k_part_selected]

        if k_part_selected in K_GENERIQUES:
            k_ed_selected = ''
        else:
            k_ed_selected = db[k_ep_selected]['video']['target'][k_part_selected]['k_ed_src']


        # Walk through shots
        shots = db_video['shots']
        for shot in shots:
            # For debug only
            print_lightgreen("\t\t%s: %s\t(%d)\t<- %s:%s:%s   %d (%d)" % (
                "{:3d}".format(shot['no']),
                "{:5d}".format(shot['start']),
                shot['dst']['count'],
                shot['k_ed'],
                shot['k_ep'],
                shot['k_part'],
                shot['start'],
                shot['count']),
                flush=True)

            # Consolidate shot
            shot['last_task'] = task
            consolidate_shot(db, shot=shot, edition_mode=True)
            # NOTE replace: if last task is 'edition', the hashes
            # are different from the final generation

            # Get a list of path for each frame  for this shot
            if k_part_selected in ['g_asuivre', 'g_reportage']:
                filepath_tmp = get_frame_list_single(db, k_ep=k_ep_selected, k_part=k_part_selected, shot=shot)
            else:
                filepath_tmp = get_frame_list(db, k_ep=k_ep_selected, k_part=k_part_selected, shot=shot)
            self.filepath.append(filepath_tmp)

            shot_no = shot['no']
            self.shots[shot_no] = shot

            # Get curves for this shot
            curves = self.model_database.get_shot_curves_selection(db=db, shot=shot)
            try:
                k_curves = curves['k_curves']
            except:
                k_curves =''
            if curves is None and shot['curves'] is not None:
                print("Error: curves [%s] is not found in curves library, correct this!" % (shot['curves']['k_curves']))
                pprint(curves)
                print("-----")
                pprint(shot)
                sys.exit()
                shot['curves']['k_curves'] = '~' + shot['curves']['k_curves']


            # Update this shot for UI:
            # to do: put in a 'ui' structure
            shot.update({
                'is_valid': True,

                # Frame no. ... for what?
                'frame_nos': list(),

                # Structure to display the modifications in the selection widget
                'modifications': {
                    'curves' : {
                        'initial': k_curves,
                        'new': None,
                    },
                },
            })


            # Get the target geometry
            target_geometry = None
            default_shot_geometry = None
            shot_geometry = None
            if k_part_selected in ['g_debut', 'g_fin']:
                # Use the k_ed:k_ep defined as the source for this geometry
                target_geometry = self.model_database.get_target_geometry(
                        k_ep='ep00',
                        k_part=k_part_selected)
            elif k_part_selected in ['g_asuivre', 'g_reportage']:
                # Use the following part to get the geometry for this part
                target_geometry = self.model_database.get_target_geometry(
                        k_ep=k_ep_selected,
                        k_part=k_part_selected[2:])
            else:
                # Use the selected ed:ep:part
                target_geometry = self.model_database.get_target_geometry(
                        k_ep=k_ep_selected,
                        k_part=k_part_selected)

            # Get shot and default geometry
            default_shot_geometry = self.model_database.get_default_shot_geometry(shot=shot)
            shot_geometry = self.model_database.get_shot_geometry(shot=shot)
            if shot_geometry is None and default_shot_geometry is None:
                if shot['k_part'] in ['g_asuivre', 'g_reportage']:
                    print_yellow("\t\t\tNo shot geometry defined, create a shot geometry")
                    # Not geometry define, create a new one
                    self.model_database.set_shot_geometry(shot=shot, geometry={
                        'crop': [0] * 4,
                        'keep_ratio': True,
                        'fit_to_width': False})
                    shot_geometry = self.model_database.get_shot_geometry(shot=shot)
                elif is_stabilize_task_enabled(shot):
                    # Not geometry define, create a new one
                    print_yellow("\t\t\tNo shot geometry defined, stabilize filter detected, associate a shot geometry")
                    self.model_database.set_shot_geometry(shot=shot, geometry={
                        'crop': [STABILIZE_BORDER_HIGH_RES] * 4,
                        'keep_ratio': True,
                        'fit_to_width': False})
                    shot_geometry = self.model_database.get_shot_geometry(shot=shot)
                else:
                    print_yellow("\t\t\tNo shot geometry defined, associate a default shot geometry")
                    self.model_database.set_default_shot_geometry(shot=shot, geometry={
                        'crop': [0] * 4,
                        'keep_ratio': True,
                        'fit_to_width': False})
                    default_shot_geometry = self.model_database.get_default_shot_geometry(shot=shot)

            if False:
            # if shot['no'] == 0:
                print_lightcyan("================================== SHOT =======================================")
                pprint(shot)
                print_lightcyan("===============================================================================")
                print_lightcyan("target_geometry:")
                pprint(target_geometry)
                print_lightcyan("default_shot_geometry:")
                pprint(default_shot_geometry)
                print_lightcyan("shot_geometry:")
                pprint(shot_geometry)
                # sys.exit()
                pprint(filepath_tmp)

            # Create a list of frames for this shot
            self.frames[shot_no] = list()
            for p, i in zip(filepath_tmp, range(len(filepath_tmp))):

                if task in ['deinterlace', 'edition']:
                    # Use the frame no. from video to simplify frame replacement
                    frame_no = shot['src']['start'] + i
                else:
                    frame_no = i

                if not os.path.exists(p):
                    image_filepath = p_missing_frame
                    shot['is_valid'] = False
                else:
                    image_filepath = p

                self.frames[shot_no].append({
                    'dst': shot['dst'],
                    'src': shot['src'],
                    'k_ed': shot['k_ed'],
                    'k_ep': shot['k_ep'],
                    'k_part': shot['k_part'],
                    'shot_no': shot_no,
                    'frame_no': frame_no,

                    'filepath': image_filepath,
                    # 'replaced_by': self.model_database.get_replace_frame_no(shot=shot, frame_no=frame_no),
                    'curves': curves,
                    'geometry': None,
                    # 'geometry': {
                    #     'target': target_geometry,
                    #     'default': default_shot_geometry,
                    #     'shot': shot_geometry,
                    #     'dimensions': shot['geometry']['dimensions'],
                    # },
                    'cache_initial': None,
                    'cache': None,
                    'cache_deshake': None,
                })
            # for f in self.frames[shot_no]:
            #     print(f['frame_no'])
            # sys.exit()

        # Create a dict to update the "browser" part of the editor widget

        self.current_selection = {
            'k_ed': k_ed_selected,
            'k_ep': k_ep_selected,
            'k_part': k_part_selected,
            'k_step': task,
            'shots': self.shots,
        }

        # for f in self.frames[shot_no]:
        #     print("%s" % f['filepath'])


        self.model_database.initialize_shots_per_curves(self.shots)
        # print("selected: %s:%s:%s" % (k_ed_selected, k_ep_selected, k_part_selected))
        if k_part_selected in K_GENERIQUES:
            curves_library = self.model_database.get_library_curves(
                self.shots[0]['k_ed'], self.shots[0]['k_ep'])
        else:
            curves_library = self.model_database.get_library_curves(k_ed_selected, k_ep_selected)
        self.signal_curves_library_modified.emit(curves_library)
        self.signal_shotlist_modified.emit(self.current_selection)


    def event_selected_shots_changed(self, selected_shots:dict):
        print_lightgreen(f"selected shots: {selected_shots['k_ep']}:{selected_shots['k_part']}, %s, step: {selected_shots['k_step']}" % (
            ','.join(map(lambda x: str(x), selected_shots['shotlist']))))


        log.info(f"selected shots: {selected_shots['k_ep']}:{selected_shots['k_part']}, %s, {selected_shots['k_step']}" % (
            ','.join(map(lambda x: str(x), selected_shots['shotlist']))))

        if len(selected_shots['shotlist']) == 0:
            return

        try:
            shot = self.current_shot()
            previous_shot_id = f"{shot['k_ed']}:{shot['k_ep']}:{shot['k_part']}:{shot['no']}"
        except:
            previous_shot_id = ""

        # Create a list of frames for each selected shot
        frame_nos = list()
        index = 0
        ticklist = [0]
        self.playlist_frames.clear()
        for shot_no in selected_shots['shotlist']:
            # mmmmh what??? should use self.shot
            shot = self.frames[shot_no]
            for frame in shot:
                frame['index'] = index
                index += 1
                self.playlist_frames.append(frame)
                frame_nos.append(frame['frame_no'])
            ticklist.append(ticklist[-1] + len(self.frames[shot_no]))

        gc.collect()

        # Load images
        print_lightgrey("\tload images")
        start_time = time.time()
        cpu_count = 12
        # image_filepathes = [f['filepath'] for f in self.frames[shot_no]]
        for shot_no in selected_shots['shotlist']:
            worklist = list()
            for i, f in zip(range(len(self.frames[shot_no])), self.frames[shot_no]):
                if f['cache_initial'] is None:
                    worklist.append([i, f['filepath']])
            if len(self.frames[shot_no]) > 0:
                with ThreadPoolExecutor(max_workers=min(cpu_count, len(self.frames[shot_no]))) as executor:
                    work_result = {executor.submit(load_image, i, f): list for (i, f) in worklist}
                    for future in concurrent.futures.as_completed(work_result):
                        no, img = future.result()
                        self.frames[shot_no][no]['cache_initial'] = img
            print_green("%.02fs" % (time.time() - start_time))


        # Update each frame
        for shot_no in selected_shots['shotlist']:
            shot = self.shots[shot_no]

            # Update each frame with deshake status flag
            self.refresh_stabilize_flag_for_each_frame(shot=shot)

            # Geometry: must be done AFTER having set stabilize flag
            self.refresh_geometry_for_each_frame(shot=shot)

            # Replace
            self.refresh_replace_for_each_frame(shot=shot)



        self.playlist_properties.update({
            # 'start': self.shots[selected_shots['shotlist'][0]]['start'],
            'frame_nos': frame_nos,
            'count': len(self.playlist_frames),
            'ticks': ticklist,
        })

        # Set current to None to refresh widgets
        self.current_frame = None

        self.current_shot_no = selected_shots['shotlist'][0]
        shot = self.current_shot()
        shot_no = shot['no']

        # Update stabilize widget
        stabilize_settings = self.model_database.get_shot_stabilize_settings(shot=shot)

        # Replace
        self.refresh_replace_list()

        # Curves: update the curves db
        if shot['k_part'] in ['g_debut', 'g_fin']:
            curves_library = self.model_database.get_library_curves(shot['k_ed'], shot['k_ep'])
            self.signal_curves_library_modified.emit(curves_library)


        new_shot_id = f"{shot['k_ed']}:{shot['k_ep']}:{shot['k_part']}:{shot['no']}"

        # Get preview options
        self.preview_options = self.view.get_preview_options()
        self.consolidate_preview_options()

        if previous_shot_id != new_shot_id:
            # Stabilize current shot
            if (stabilize_settings is not None
                and stabilize_settings['enable']
                and self.preview_options['stabilize']['enabled']):
                self.stabilize(shot=self.current_shot())

                # Refresh UI
                self.signal_stabilization_done.emit()

            # Consolidate preview
            self.signal_preview_options_consolidated.emit(self.preview_options)

        self.signal_stabilize_settings_refreshed.emit(stabilize_settings)

        log.info(f"selected shots: shot is ready to play")
        self.signal_ready_to_play.emit(self.playlist_properties)



    def event_save_and_close_requested(self):
        k_ep = self.current_selection['k_ep']
        k_part = self.current_selection['k_part']


        self.signal_close.emit()


    def get_modified_db(self):
        return self.model_database.get_modified_db()


    def current_shot(self):
        try:
            return self.shots[self.current_shot_no]
        except:
            print_orange("no shot selected, cannot return current shot")
            log.warning("no shot selected, cannot return current shot")
            pass
        # self.shots[self.current_frame['shot_no']]

        return None

    def get_current_frame_no(self):
        return self.current_frame['frame_no']

    def get_index_from_frame_no(self, frame_no):
        # log.info(f"get index for frame no. {frame_no}")
        return self.playlist_properties['frame_nos'].index(frame_no)

    def get_frame_at_index(self, index):
        """ returns the replace frame unless there is no replacemed frame or
        the initial flag is set to True
        framelist contains all path for each frame of this playlist
        """
        # log.info(f"get_frame: get_frame at index {index}")
        # print_lightgreen("playlist: nb of frames: %d" % (len(self.playlist_frames)))
        if len(self.playlist_frames) == 0:
            return None

        try:
            shot = self.current_shot()
            previous_shot_id = f"{shot['k_ed']}:{shot['k_ep']}:{shot['k_part']}:{shot['no']}"
        except:
            previous_shot_id = ""
        if self.current_frame is None:
            previous_shot_id = ""

        frame = self.playlist_frames[index]
        frame_no = frame['frame_no']
        shot_no = frame['shot_no']

        # Select shot:
        shot = self.shots[shot_no]

        # Replace: remove key if disabled
        if not self.preview_options['replace']['enabled']:
            try: del frame['replace']
            except: pass
        else:
            # TODO clean this
            # print_green("\tshot no. %d, frame no. %d" % (shot_no, frame_no))
            new_frame_no = self.model_database.get_replace_frame_no(shot, frame_no)
            if new_frame_no == -1:
                frame = self.playlist_frames[index]
                try: del frame['replace']
                except: pass
            else:
                frame = self.playlist_frames[index + (new_frame_no - frame_no)]
                frame['replace'] = frame_no


        # If shot is different: todo: is reload_parameters required?
        new_shot_id = f"{shot['k_ed']}:{shot['k_ep']}:{shot['k_part']}:{shot['no']}"
        if previous_shot_id != new_shot_id:
            is_shot_changed = True
            frame['reload_parameters'] = True
        else:
            is_shot_changed = False
            frame['reload_parameters'] = False


        # Update curves and load it into the graph
        frame['curves'] = self.model_database.get_shot_curves_selection(
            db=self.model_database.database(), shot=shot)
        if is_shot_changed:
            # Shot is different, refresh the curve database in the curves widget
            if shot['k_part'] in ['g_debut', 'g_fin']:
                curves_library = self.model_database.get_library_curves(shot['k_ed'], shot['k_ep'])
                self.signal_curves_library_modified.emit(curves_library)

            try:
                self.signal_load_curves.emit(frame['curves'])
                shot_list = self.model_database.get_shots_per_curves(frame['curves']['k_curves'])
                self.signal_shot_per_curves_modified.emit(shot_list)
            except:
                self.signal_load_curves.emit(None)
                self.signal_shot_per_curves_modified.emit(None)


        # Remove this
        # elif self.current_frame is None:
        #     self.signal_load_curves.emit(None)

        # Get geometry: already done each time a modification is done
        # Stabilize settings: already loaded

        # Purge image from the previous frame
        self.purge_current_frame_cache()

        # Set current frame
        self.current_frame = frame
        self.current_shot_no = frame['shot_no']

        # Generate the image for this frame
        # now = time.time()
        options = self.preview_options
        if options is not None:
            try:
                if frame['cache_initial'] is None:
                    # The original has not yet been loaded
                    frame['cache_initial'] = cv2.imread(frame['filepath'], cv2.IMREAD_COLOR)
            except:
                frame['cache_initial'] = None
                return None

            index, img = generate_image(self.current_frame, preview_options=options)
            self.set_current_frame_cache(img=img)
        # print("\t%dms" % (int(1000 * (time.time() - now))))


        return self.current_frame




    def event_preview_options_changed(self, preview_options):
        log.info("preview options changed")
        self.preview_options = preview_options
        self.consolidate_preview_options()
        self.signal_preview_options_consolidated.emit(self.preview_options)
        self.signal_reload_frame.emit()



    def consolidate_preview_options(self):
        # Modify preview settings because some widget have to be disabled
        verbose = False
        log.info("consolidate options")
        options = self.preview_options

        if verbose:
            print(f"Consolidate preview options, task: {self.current_task}")
            print_lightcyan("\npreview mode changed:")
            pprint( self.preview_options)

        options['replace']['allowed'] = True
        if self.current_task == 'edition':
            options['geometry']['allowed'] = True
            options['stabilize']['allowed'] = True
        else:
            options['geometry']['allowed'] = False
            options['stabilize']['allowed'] = False

        if self.current_task not in ['edition']:
            # Stabilize is disable if not in edition mode
            options['stabilize']['enabled'] = False

        if not options['replace']['enabled']:
            # Cannot stabilize if replace not active (use replace to stabilize)
            options['stabilize']['enabled'] = False

        if options['stabilize']['enabled']:
            # Force replace if stabilize
            options['replace']['enabled'] = True

        if not options['geometry']['allowed']:
            # If geometry is disabled, disable all preview
            tmp = options['geometry']['shot']['is_default']
            for k0 in options['geometry'].keys():
                try:
                    for k1 in options['geometry'][k0].keys():
                        options['geometry'][k0][k1] = False
                except:
                        options['geometry'][k0] = False

            options['geometry']['shot']['is_default'] = tmp

        self.preview_options = options

        if verbose:
            print_lightgreen("\tconsolidated:")
            pprint(self.preview_options)



    # Deshake/stabilize
    #---------------------------------------------------------------------------
    def event_stabilize_modified(self, settings):
        # print_lightcyan("event_stabilize_modified")
        # pprint(settings)
        shot = self.current_shot()

        # Consolidate segments
        settings['segments'] = consolidate_stabilize_segments(segments=settings['segments'])

        # Validate settings and reorder segments
        settings['error'] = not verify_stabilize_segments(
            shot=shot, segments=settings['segments'])

        # Get current settings
        current_settings = self.model_database.get_shot_stabilize_settings(shot=shot)

        # Set new settings
        self.model_database.set_shot_stabilize_settings(shot=shot, settings=deepcopy(settings))

        # Return consolidated segments
        new_settings = deepcopy(self.model_database.get_shot_stabilize_settings(shot=shot))
        if (current_settings is None
            and settings['enable']
            and len(settings['segments']) == 0):
            # Not already defined, define a new one
            new_settings['error'] = False
            new_settings['segments'] = [{
                'alg': 'cv2_deshaker',
                'start': shot['start'],
                'end':  shot['start'] + shot['count'] - 1,
                'ref': 'middle',
                'mode': {
                    'vertical': True,
                    'horizontal': True,
                    'rotation': False,
                }
            }]

        if not new_settings['error']:
            # Flush images
            for f in self.frames[shot['no']]:
                f['cache_deshake'] = None

        if new_settings['enable'] != current_settings['enable']:
            # Geometry has to be consolidated if change enabled/disable
            self.refresh_geometry_for_each_frame(shot=shot)


        self.signal_stabilize_settings_refreshed.emit(new_settings)


    def refresh_stabilize_flag_for_each_frame(self, shot):
        shot_stabilize = self.model_database.get_shot_stabilize_settings(shot=shot)
        for frame in self.frames[shot['no']]:
            try:
                nested_dict_set(frame, shot_stabilize['enable'], 'stabilize', 'enable')
            except:
                nested_dict_set(frame, False, 'stabilize', 'enable')


    def event_stabilize_discard_requested(self):
        log.info("discard modifications requested")
        shot = self.current_shot()
        self.model_database.discard_shot_stabilize_settings(
            k_ep=shot['k_ep'], k_part=shot['k_part'])
        self.signal_reload_frame.emit()


    def event_stabilize_save_requested(self):
        # Save current shot only
        shot = self.current_shot()
        self.model_database.save_shot_stabilize_settings(shot)
        self.signal_is_saved.emit('stabilize')



    def stabilize(self, shot):
        print_lightgreen("\tStabilization requested")
        log.info("\tStabilization requested")
        shot_no = shot['no']

        # Get stabilization parameters
        settings = self.model_database.get_shot_stabilize_settings(shot=shot)
        try:
            is_valid = verify_stabilize_segments(shot=shot, segments=settings['segments'])
        except:
            is_valid = False
        if not is_valid:
            print_red("Segments are not valid")
            return

        # Get all images
        print_lightgrey("\tload images")
        start_time = time.time()
        cpu_count = 12
        # image_filepathes = [f['filepath'] for f in self.frames[shot_no]]

        worklist = list()
        for i, frame in zip(range(len(self.frames[shot_no])), self.frames[shot_no]):
            if frame['cache_initial'] is None:
                worklist.append([i, frame['filepath']])

        with ThreadPoolExecutor(max_workers=min(cpu_count, len(self.frames[shot_no]))) as executor:
            work_result = {executor.submit(load_image, i, f): list for (i, f) in worklist}
            for future in concurrent.futures.as_completed(work_result):
                no, img = future.result()
                self.frames[shot_no][no]['cache_initial'] = img

        print_green("%.02fs" % (time.time() - start_time))

        # Create a list of images
        frames = self.frames[shot_no]
        images = list()
        image_list = list()
        for frame in frames:
            frame_no = frame['frame_no']
            new_frame_no = self.model_database.get_replace_frame_no(shot=shot, frame_no=frame_no)
            if new_frame_no != -1:
                print(f"{frame_no} replaced by {new_frame_no}")
                frame_index = new_frame_no - shot['start']
            else:
                frame_index = frame_no - shot['start']

            images.append(frames[frame_index]['cache_initial'])
            image_list.append(frames[frame_index]['filepath'])

        print_lightgrey("\tdeshake")

        # Patch shot deshake with the modified values
        shot['deshake'] = settings

        pprint(shot)

        # Deshake
        hash, output_images = deshake(
            shot=shot,
            images=images,
            image_list=image_list,
            add_border=True,
            step_no=shot['last_step']['step_no'],
            input_hash=shot['filters'][shot['last_step']['step_no'] - 1],
            get_hash=False,
            do_force=False)

        print_lightgrey("\tended")
        for f, img in zip(self.frames[shot_no], output_images):
            f['cache_deshake'] = img

        # Refresh all frames of this shot: ste the stabilize 'enable' flag
        self.refresh_stabilize_flag_for_each_frame(shot)

        # Geometry has to be consolidated if change enabled/disable
        self.refresh_geometry_for_each_frame(shot=shot)



    def event_stabilization_requested(self):
        # Stabilize current shot
        self.stabilize(shot=self.current_shot())

        # Consolidate preview
        self.preview_options['stabilize']['enabled'] = True
        self.consolidate_preview_options()

        # Refresh UI
        self.signal_preview_options_consolidated.emit(self.preview_options)
        self.signal_reload_frame.emit()
        self.signal_stabilization_done.emit()


def load_image(i, f):
    return i, cv2.imread(f, cv2.IMREAD_COLOR)