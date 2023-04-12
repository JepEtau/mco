# -*- coding: utf-8 -*-
import sys
sys.path.append('../scripts')

import cv2
import gc
import os
import os.path
import time

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

from filters.filters import calculate_geometry_parameters
from filters.utils import (
    STABILIZE_BORDER,
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



    # Send a signal to inform that the shot changed
    signal_shot_changed = Signal()

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



        self.view.signal_preview_options_changed[dict].connect(self.event_preview_options_changed)
        self.view.signal_save_and_close.connect(self.event_save_and_close_requested)

        # Force refresh of preview options
        self.view.event_preview_options_changed('model')

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

        if ((k_ep_selected == '' and k_part_selected == '')
            or (k_ep_selected != '' and k_part_selected == '')):
            log.info(f"no selected episode/part")
            return
        log.info(f"directory_changed: {k_ep_selected}:{k_part_selected}")

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
            consolidate_shot(db, shot=shot)
            # NOTE replace: if last task is 'pre_replace', the hashes
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
                        'crop': [STABILIZE_BORDER] * 4,
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

                if task in ['deinterlace', 'pre_replace']:
                    # Use the frame no. from video to simplify frame replacement
                    frame_no = shot['src']['start'] + i
                else:
                    frame_no = i

                if not os.path.exists(p):
                    image_filepath = p_missing_frame
                    shot['is_valid'] = False
                else:
                    image_filepath = p

                shot['frame_nos'].append(frame_no)
                self.frames[shot_no].append({
                    'dst': shot['dst'],
                    'src': shot['src'],
                    'k_ed': shot['k_ed'],
                    'k_ep': shot['k_ep'],
                    'k_part': shot['k_part'],
                    'shot_no': shot_no,
                    'frame_no': frame_no,

                    'filepath': image_filepath,
                    'replaced_by': self.model_database.get_replace_frame_no(shot=shot, frame_no=frame_no),
                    'curves': curves,
                    'geometry': {
                        'target': target_geometry,
                        'default': default_shot_geometry,
                        'shot': shot_geometry,
                        'dimensions': shot['geometry']['dimensions'],
                    },
                    'cache_initial': None,
                    'cache': None,
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
        log.info("selected shots changed %s:%s, %s, %s" % (
            selected_shots['k_ep'],
            selected_shots['k_part'],
            ','.join(map(lambda x: str(x), selected_shots['shotlist'])),
            selected_shots['k_step']))

        if len(selected_shots['shotlist']) == 0:
            return

        frame_nos = list()
        index = 0
        ticklist = [0]
        self.playlist_frames.clear()
        for shot_no in selected_shots['shotlist']:
            shot = self.frames[shot_no]
            for frame in shot:
                frame['index'] = index
                index += 1
                self.playlist_frames.append(frame)
                frame_nos.append(frame['frame_no'])
            ticklist.append(ticklist[-1] + len(self.frames[shot_no]))


        self.playlist_properties.update({
            # 'start': self.shots[selected_shots['shotlist'][0]]['start'],
            'frame_nos': frame_nos,
            'count': len(self.playlist_frames),
            'ticks': ticklist,
        })

        # Flush internal variables
        self.current_frame = None


        gc.collect()
        # pprint(self.framelist)

        shot_no = selected_shots['shotlist'][0]
        shot = self.shots[shot_no]

        # Replace
        self.refresh_replace_list()

        # Curves: update the curves db
        if shot['k_part'] in ['g_debut', 'g_fin']:
            curves_library = self.model_database.get_library_curves(shot['k_ed'], shot['k_ep'])
            self.signal_curves_library_modified.emit(curves_library)


        if False:
            print_lightcyan("================================== SHOT =======================================")
            pprint(shot)
            print_lightcyan("===============================================================================")
        self.signal_ready_to_play.emit(self.playlist_properties)


    def event_save_and_close_requested(self):
        k_ep = self.current_selection['k_ep']
        k_part = self.current_selection['k_part']

        self.event_replace_save_requested()

        print("TODO: Save the shot curves selection")
        # self.model_database.save_shot_curves_selection(
        #     self.shots,
        #     k_ed='',
        #     k_ep='',
        #     k_part=k_part,
        #     shot_no=-1)

        self.event_save_geometry_requested()
        self.model_database.save_all_curves(k_ep_or_g=k_part if k_part in K_GENERIQUES else k_ep)
        self.signal_close.emit()


    def get_modified_db(self):
        return self.model_database.get_modified_db()


    def current_shot(self):
        try: return self.shots[self.current_frame['shot_no']]
        except: pass
        return None




    def get_frame_from_index(self, index):
        """ returns the replace frame unless there is no replacemed frame or
        the initial flag is set to True
        framelist contains all path for each frame of this playlist
        """
        # log.info("get_frame: get_frame from index. %d" % (index))
        # print_lightgreen("playlist: nb of frames: %d" % (len(self.playlist_frames)))
        if len(self.playlist_frames) == 0:
            return None

        frame = self.playlist_frames[index]
        frame_no = frame['frame_no']
        shot_no = frame['shot_no']
        # new shot:
        shot = self.shots[shot_no]

        if not self.preview_options['replace']['is_enabled']:

            try: del frame['replace']
            except: pass
        else:

            # print_green("\tshot no. %d, frame no. %d" % (shot_no, frame_no))
            new_frame_no = self.model_database.get_replace_frame_no(shot, frame_no)
            if new_frame_no == -1:
                frame = self.playlist_frames[index]
                try: del frame['replace']
                except: pass
            else:
                frame = self.playlist_frames[index + (new_frame_no - frame_no)]
                frame['replace'] = frame_no

        # If shot is different
        if self.current_frame is None or frame['shot_no'] != self.current_frame['shot_no']:
            is_shot_changed = True
            frame['reload_parameters'] = True
        else:
            is_shot_changed = False
            frame['reload_parameters'] = False

        # Update curves and load it into the graph
        frame['curves'] = self.model_database.get_shot_curves_selection(
            db=self.model_database.database(), shot=shot)
        if is_shot_changed:
            try:
                self.signal_load_curves.emit(frame['curves'])
                shot_list = self.model_database.get_shots_per_curves(frame['curves']['k_curves'])
                self.signal_shot_per_curves_modified.emit(shot_list)
            except:
                self.signal_load_curves.emit(None)
                self.signal_shot_per_curves_modified.emit(None)
        elif self.current_frame is None:
            self.signal_load_curves.emit(None)

        # Load current geometry
        k_part_src = shot['dst']['k_part'][2:] if shot['dst']['k_part'] in ['g_asuivre', 'g_reportage'] else shot['dst']['k_part']
        target_geometry = self.model_database.get_target_geometry(k_ep=shot['dst']['k_ep'], k_part=k_part_src)
        frame['geometry'].update({
            'target': target_geometry,
            'default': self.model_database.get_default_shot_geometry(shot=shot),
            'shot': self.model_database.get_shot_geometry(shot=shot),

            # Used when the width of the cropped img  for the shot < width of the cropped img of the part
            # is updated by the generate function
            'error': False,
        })
        # print_yellow("db_target_geometry_initial")
        # pprint(self.model_database.db_target_geometry_initial)
        # print_yellow("db_target_geometry")
        # pprint(self.model_database.db_target_geometry)
        # pprint(frame['geometry'])

        # Load new stabilize settings
        if is_shot_changed:
            settings = self.model_database.get_shot_stabilize_settings(shot=shot)
            self.signal_stabilize_settings_refreshed.emit(settings)

        # Purge image from the previous frame
        self.purge_current_frame_cache()

        # Set current frame
        self.current_frame = frame

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

            if target_geometry['w'] == -1:
                print_lightcyan("calculate target geometry %s:%s" % (frame['k_ep'], frame['k_part']))
                # Calculate width
                geometry = calculate_geometry_parameters(shot=frame, img=frame['cache_initial'])
                target_geometry['w'] = geometry['resize']['w']
                self.model_database.set_target_geometry(
                    k_ep=frame['k_ep'], k_part=frame['k_part'],
                    geometry=target_geometry)

            frame['geometry_values'] = calculate_geometry_parameters(shot=frame, img=frame['cache_initial'])
            frame['geometry']['error'] = True if frame['geometry_values']['pad_error'] is not None else False

            index, img = generate_image(self.current_frame, preview_options=options)
            self.set_current_frame_cache(img=img)
        # print("\t%dms" % (int(1000 * (time.time() - now))))
        # else:
            # Cannot generate the image because no preview option is defined
            # The preview options will be updated by the window UI



        if is_shot_changed:
            self.signal_shot_changed.emit()

        return self.current_frame







    # Deshake/stabilize
    #---------------------------------------------------------------------------
    def is_stabilize_allowed(self) -> bool:
        shot = self.current_shot()
        if shot is None:
            return False
        is_allowed = self.model_database.is_stabilize_allowed(shot=shot)
        return is_allowed


    def event_stabilize_modified(self, settings):
        print_lightcyan("event_stabilize_modified")
        pprint(settings)
        shot = self.current_shot()

        # Validate settings and reorder segments

        # Set new settings
        self.model_database.set_shot_stabilize_settings(shot=shot, settings=settings)

        new_settings = self.model_database.get_shot_stabilize_settings(shot=shot)
        self.signal_stabilize_settings_refreshed.emit(new_settings)


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


