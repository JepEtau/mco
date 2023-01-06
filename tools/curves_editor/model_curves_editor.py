# -*- coding: utf-8 -*-

import sys
sys.path.append('../scripts')

import gc
import os
import os.path
import time

from pprint import pprint
from logger import log
from copy import deepcopy
import cv2
import numpy as np

from PySide6.QtCore import(
    Signal,
)
from PySide6.QtWidgets import QApplication

from common.preferences import Preferences
from models.model_database import Model_database
from models.model_common import (
    Model_common,
)
from models.model_framelist import Model_framelist
from models.model_curves import Model_curves

from parsers.parser_generiques import parse_get_dependencies_for_generique
from utils.common import (
    K_ALL_PARTS,
    K_GENERIQUES,
)
from utils.get_filters import FILTER_BASE_NO
from images.filtering import filter_rgb



class Model_curves_editor(Model_common):
    signal_folders_parsed = Signal([dict])
    signal_current_shot_modified = Signal(dict)
    signal_reload_frame = Signal()
    signal_is_saved = Signal(str)

    signal_load_curves = Signal(dict)
    signal_curves_library_modified = Signal(dict)
    signal_shot_per_curves_modified = Signal(list)

    signal_framelist_modified = Signal(dict)

    # previous
    signal_selected_directory_changed = Signal(dict)
    signal_refresh_shotlist = Signal(list)
    signal_refresh_framelist = Signal(list)
    signal_refresh_modified_shots = Signal(list)
    signal_refresh_frame_properties = Signal(dict)
    signal_display_frame = Signal(dict)
    signal_refresh_curves_list = Signal(list)
    signal_refresh_curves_shot_list = Signal(list)
    signal_load_curves = Signal(dict)
    signal_folders_parsed = Signal(dict)


    WIDGET_LIST = [
        'curves',
        'selection'
    ]

    SELECTABLE_WIDGET_LIST = [
        'curves',
        'selection'
    ]


    def __init__(self):
        super(Model_curves_editor, self).__init__()

        # Load saved preferences
        self.preferences = Preferences(
            tool='curves_editor',
            widget_list=self.WIDGET_LIST)

        # Variables
        self.model_database = Model_database()
        self.filepath = list()

        self.current_selection = {
            'k_ed': '',
            'k_ep': '',
            'k_part': '',
            'k_step': '',
            'filter_ids': list(),
            'shot_nos': list(),
        }

        # Parse the frames directory to update the selection ui
        self.parse_frames_directory()

        # Variables: previous
        self.framelist = Model_framelist(self.model_database)
        self.model_curves = Model_curves()


    def set_view(self, view):
        self.view = view

        self.view.widget_selection.signal_selection_changed[dict].connect(self.selection_changed)
        self.view.widget_selection.signal_save_curves_selection_requested.connect(self.event_save_curves_selection_requested)
        self.view.widget_selection.signal_discard_curves_selection_requested.connect(self.event_discard_curves_selection_requested)
        self.view.widget_selection.signal_remove_curves_selection_requested.connect(self.event_remove_curves_selection_requested)

        self.view.widget_curves.widget_rgb_graph.signal_graph_modified[dict].connect(self.event_rgb_graph_modified)
        self.view.widget_curves.signal_save_rgb_curves_as[dict].connect(self.event_save_rgb_curves_as)
        self.view.widget_curves.widget_curves_selection.signal_curves_selection_changed[str].connect(self.event_curves_selection_changed)
        self.view.widget_curves.widget_curves_selection.signal_save_curves_selection_requested.connect(self.event_save_curves_selection_requested)
        self.view.widget_curves.widget_curves_selection.signal_discard_curves[str].connect(self.event_discard_rgb_curves_modifications)

        self.view.signal_preview_options_changed[dict].connect(self.event_preview_options_changed)
        self.view.signal_reload_directories_and_frames.connect(self.event_reload_directories_and_frames)
        self.view.signal_save_and_close.connect(self.event_save_and_close_requested)

        # Force refresh of preview options
        self.view.event_preview_options_changed('model')

        p = self.preferences.get_preferences()
        k_ep = 'ep%02d' % (p['selection']['episode']) if p['selection']['episode'] != '' else ''
        self.selection_changed({
                'k_ed': p['selection']['edition'],
                'k_ep': k_ep,
                'k_part': p['selection']['part'],
                'k_step': p['selection']['step'],
                'filter_ids': list(),
                'shots': list(),
            })



    def get_available_episode_and_parts(self) -> dict:
        log.info("get_available_episode_and_parts: removed")
        pass


    def parse_frames_directory(self):
        # Override the function
        k_eps_parts = dict()
        path_images = self.model_database.get_images_path()
        if os.path.exists(path_images):
            log.info("get available episode and parts")
            # Rather than walking through, try every possibilities
            # another option would be to select a folder, then the combobox
            # will be disabled
            for ep_no in range(1, 39):
                k_ep = 'ep%02d' % (ep_no)
                if os.path.exists(os.path.join(path_images, k_ep)):
                    k_eps_parts[k_ep] = list()
                    for k_part in K_ALL_PARTS:
                        if os.path.exists(os.path.join(path_images, k_ep, k_part)):
                            k_eps_parts[k_ep].append(k_part)

            k_eps_parts[' '] = list()
            for k_part_g in K_GENERIQUES:
                if os.path.exists(os.path.join(path_images, k_part_g)):
                    k_eps_parts[' '].append(k_part_g)

        # Create a dict to update combobox of the selectio widget
        db = self.model_database.database()
        self.available_selection = {
            'k_eds': sorted(db['editions']['available']),
            'k_eps_parts': k_eps_parts,
            'steps': list(k for k, v in sorted(FILTER_BASE_NO.items(), key=lambda item: item[1]))
        }


    def get_available_selection(self):
        return self.available_selection


    def get_step_labels(self):
        return self.step_labels


    def get_available_filter_ids(self):
        return self.framelist.get_available_filter_ids()


    def selection_changed(self, selection:dict, force=False):
        """ Selection has been changed, update the database, list all images,
            list all shots
        """
        print("----------------------- selection_changed -------------------------")
        pprint(self.current_selection)
        print("->")
        pprint(selection)

        do_send_signals = False
        k_ed = selection['k_ed']
        k_ep = selection['k_ep']
        k_part = selection['k_part']
        log.info("selection changed to %s:%s:%s" % (k_ed, k_ep, k_part))

        # Change edition if not supported
        db = self.model_database.database()
        if k_ed != '' and k_ed != ' ' and k_ed not in db['editions']['available']:
            print("Warning: saved selection is not in supported editions: k_ed: %s" % (k_ed))
            k_ed = db[k_ep]['target']['video'][k_part]['k_ed_src']
            print("\tchange to %s" % (k_ed))


        # Patch k_ep:k_part if no folder
        if len(self.available_selection['k_eps_parts'].keys()) == 0:
            log.info("No folders, cannot select anything")
        if k_ep == '' and k_part == '':
            log.info("Patch k_part or k_ep as none selected")
            try:
                k_part = self.available_selection['k_eps_parts'][' '][0]
            except:
                for k in self.available_selection['k_eps_parts'].keys():
                    if k != ' ':
                        k_ep = k
                        break
            log.info("patched to %s:%s:%s" % (k_ed, k_ep, k_part))

        # Changed directory
        if (k_ep != self.current_selection['k_ep']
            or k_part != self.current_selection['k_part']):
            pprint("initialize curves library")
            # Initialize db dor curves
            self.model_curves.initialize_curves_library(db=self.model_database.database(),
                k_ep=k_ep, k_part=k_part)


        k_eps = list()
        k_parts = list()
        if (k_ep != self.current_selection['k_ep']
            or k_part != self.current_selection['k_part']
            or force):
            print("reparse the folder")

            # The new selected ep/part is different, parse the folder
            # and create a new list of frames
            log.info("changed directory to %s:%s:%s" % (k_ed, k_ep, k_part))
            self.current_selection = deepcopy(selection)

            images_path = self.model_database.get_images_path()
            if k_part in K_GENERIQUES:
                images_path = os.path.join(images_path, k_part)
            else:
                images_path = os.path.join(images_path, k_ep, k_part)

            self.framelist.clear()
            self.framelist.set_available_editions(db['editions']['available'])
            try:
                for filename in os.listdir(images_path):
                    if filename.endswith(".png"):
                        self.framelist.append(images_path, filename, k_ep, k_part)
            except:
                print("error: the folder does not exist anymore")

            # Consolidate the list of frames
            self.framelist.consolidate(k_ep, k_part)

            # List of shots
            shotlist = self.framelist.get_filtered_shotlist(k_ed, k_ep)

            # List of curves
            curves_library = self.model_curves.get_library_curves(k_ed, k_ep)
            self.model_curves.initialize_db_for_curves(db=db, k_ep=k_ep, k_part=k_part)

            do_send_signals = True

        elif k_ed != self.current_selection['k_ed']:
            print("directory is the same, update only shotlist, curves db")
            # Consolidate the list of frames
            self.framelist.consolidate(k_ep, k_part)

            # List of shots
            shotlist = self.framelist.get_filtered_shotlist(k_ed, k_ep)

            # List of curves
            curves_library = self.model_curves.get_library_curves(k_ed, k_ep)

            do_send_signals = True


        self.current_selection = deepcopy(selection)

        # Get frames after applied the 'filter_by' structure
        self.frames = self.framelist.get_selected_frames(self.current_selection)

        if do_send_signals:
            self.signal_shotlist_modified.emit(shotlist)
            self.signal_curves_library_modified.emit(curves_library)

        # List of frames
        self.signal_framelist_modified.emit(self.frames)



    def event_reload_directories_and_frames(self):
        self.parse_frames_directory()
        self.signal_folders_parsed.emit(self.get_available_selection())
        self.selection_changed(self.current_selection, force=True)



    def event_curves_selection_changed(self, k_curves:str):
        log.info("select the new curves for this shot [%s]" % (k_curves))
        # current shot
        shot = self.framelist.get_shot_from_frame(self.current_frame)
        curves = self.model_curves.get_shot_curves_selection(db=self.model_database.database(),
            shot=shot)

        # Update the modifications structure to update the selection widget
        if k_curves != shot['modifications']['curves']['initial']:
            log.info("selected curves changed from %s to %s" % (shot['modifications']['curves']['initial'], k_curves))
            shot['modifications']['curves']['new'] = k_curves
            # Modify the selected curves in the db
            self.model_curves.set_curves_selection(db=self.model_database.database(),
                shot=shot, k_curves=k_curves)
        else:
            # Discard the current selected curves
            log.info("discard_curves_selection %s" % (shot['modifications']['curves']['new']))
            shot['modifications']['curves']['new'] = None
            self.model_curves.discard_curves_selection(db=self.model_database.database(),
                shot=shot)

        # Get the new selected curves
        curves = self.model_curves.get_shot_curves_selection(db=self.model_database.database(),
            shot=shot)

        # Refresh the list of shot for these curves
        shot_list = self.model_curves.get_shots_per_curves(k_curves)
        self.signal_shot_per_curves_modified.emit(shot_list)

        self.signal_current_shot_modified.emit(shot)
        self.signal_load_curves.emit(curves)
        self.signal_reload_frame.emit()



    def event_discard_curves_selection_requested(self):
        shot = self.framelist.get_shot_from_frame(self.current_frame)

        # Discard the current selected curves
        log.info("discard curves selection %s" % (shot['modifications']['curves']['new']))
        shot['modifications']['curves']['new'] = None
        self.model_curves.discard_curves_selection(db=self.model_database.database(),
            shot=shot)

        # Get the new selected curves
        curves = self.model_curves.get_shot_curves_selection(db=self.model_database.database(),
            shot=shot)

        self.signal_current_shot_modified.emit(shot)
        self.signal_load_curves.emit(curves)
        self.signal_reload_frame.emit()


    def event_remove_curves_selection_requested(self):
        shot = self.framelist.get_shot_from_frame(self.current_frame)

        # Discard the current selected curves
        log.info("remove curves selection requested %s" % (shot['modifications']['curves']['new']))
        shot['modifications']['curves']['new'] = ''
        self.model_curves.remove_curves_selection(db=self.model_database.database(),
            shot=shot)

        # Get the new selected curves
        curves = self.model_curves.remove_curves_selection(db=self.model_database.database(),
            shot=shot)

        self.signal_current_shot_modified.emit(shot)
        self.signal_load_curves.emit(curves)
        self.signal_reload_frame.emit()



    def get_curves_names(self, db, k_ep, k_part) -> dict:
        """ Returns a list of crops per shot for each edition
        TODO: remove this after havin reworked the curves editor
        """
        curves_names = dict()

        if k_part in K_GENERIQUES:
            dependencies = parse_get_dependencies_for_generique(db, k_part_g=k_part)
            if k_part == 'g_debut':
                # This is awful but necessary to study differences between editions
                dependencies.update({
                    'k': ['ep01'],
                    's': ['ep01', 'ep02'],
                })
        else:
            k_eds = db['editions']['available']
            dependencies = dict()
            for k_ed_tmp in k_eds:
                dependencies[k_ed_tmp] = [k_ep]

        for k_ed_tmp, k_eps in dependencies.items():
            for k_ep_tmp in k_eps:
                # print("\t%s:%s:%s" % (k_ed_tmp, k_ep_tmp, k_part))
                db_video = db[k_ep_tmp][k_ed_tmp][k_part]['video']
                for shot in db_video['shots']:
                    # print("\t--------------")
                    # print("\t%s:%s:%s" % (k_ed_tmp, k_ep_tmp, shot['no']))
                    # pprint(shot)

                    shot_no = shot['no']
                    if shot_no not in curves_names.keys():
                        curves_names[shot_no] = dict()
                    if k_ed_tmp not in curves_names[shot_no].keys():
                        curves_names[shot_no][k_ed_tmp] = dict()

                    # print("%s:%s:%s ->" % (k_ed, k_ep_tmp, shot['no']), shot['curves'])
                    if shot['curves'] is not None:
                        curves_names[shot_no][k_ed_tmp][k_ep_tmp] = shot['curves']['k_curves']
                    else:
                        curves_names[shot_no][k_ed_tmp][k_ep_tmp] = ''

        # print("%s.get_curves_names: %s:%s" % (__name__, k_ep_tmp, k_part))
        # pprint(curves_names)
        # sys.exit()
        return curves_names



    def event_rgb_graph_modified(self, rgb_channels):
        # log.info("RGB graph modified")
        shot = self.framelist.get_shot_from_frame(self.current_frame)
        self.model_curves.set_shot_rgb_channels(shot=shot, rgb_channels=rgb_channels)
        self.signal_reload_frame.emit()



    def event_discard_rgb_curves_modifications(self, k_curves:str):
        self.model_curves.discard_rgb_curves_modifications(k_curves)
        k_ed = self.current_frame['k_ed']
        k_ep = self.current_frame['k_ep']
        k_part = self.current_frame['k_part']

        # Get the initial curves
        curves = self.model_curves.get_curves(
            db=self.model_database.database(),
            k_ed=k_ed, k_ep=k_ep, k_curves=k_curves)

        # Send the list of curves
        self.signal_curves_library_modified.emit(self.model_curves.get_library_curves(k_ed, k_ep))

        # Reload curves
        self.signal_load_curves.emit(curves)
        self.signal_reload_frame.emit()



    def event_save_rgb_curves_as(self, curves):
        # Save the curves in the curves library
        log.info("save the rgb curves: %s -> %s" % (curves['k_curves_current'], curves['k_curves_new']))
        # if curves['k_curves_new'] == '':
        #     log.error("No name defined in the curves struct")
        #     return

        k_ed = self.current_frame['k_ed']
        k_ep = self.current_frame['k_ep']
        k_part = self.current_frame['k_part']
        self.model_curves.append_curves_to_database(db=self.model_database.database(),
            k_ed=k_ed, k_ep=k_ep, k_part=k_part, curves=curves)
        self.signal_curves_library_modified.emit(self.model_curves.get_library_curves(k_ed, k_ep))

        # Modify the current selection
        if curves['k_curves_new'] is not None:
            k_curves_new = curves['k_curves_new']
            self.event_curves_selection_changed(k_curves_new)



    def event_save_curves_selection_requested(self):
        log.info("save curves selection")
        # Save the curves selected for this shot
        print("event_save_curves_selection_requested")
        shot = self.framelist.get_shot_from_frame(self.current_frame)

        if shot['modifications']['curves']['new'] is None:
            print("\tnot modified")
            return

        # print("event_save_curves_selection_requested %s:%s:%s:%d" % (k_ed, k_ep, k_part, shot_no))
        self.model_curves.save_shot_curves_selection(db=self.model_database.database(),
            shot=shot)

        # Update the modifications structure to update the selection widget
        k_new_curves = shot['modifications']['curves']['new']
        shot['modifications']['curves'] = {
            'initial': k_new_curves,
            'new': None,
        }
        self.signal_current_shot_modified.emit(shot)
        self.signal_is_saved.emit('curves_selection')



    def event_save_and_close_requested(self):
        k_ep = self.current_selection['k_ep']
        k_part = self.current_selection['k_part']

        self.model_curves.save_curves_selection_database(
            self.shots,
            k_ed='',
            k_ep='',
            k_part=k_part,
            shot_no=-1)

        self.model_curves.save_all_curves(k_ep_or_g=k_part if k_part in K_GENERIQUES else k_ep)
        self.signal_close.emit()





    def get_frame_from_name(self, image_name=''):
        # log.info("image_name=%s" % (image_name))
        if image_name == 'reload':
            try:
                image_name = self.current_frame['filename']
            except:
                return None
        elif image_name == '':
            return None


        frame = self.framelist.get_frame(image_name)

        # Shot has changed: update UI with parameters for this shot (curves, crop, resize)
        if self.current_frame is None or frame['shot_no'] != self.current_frame['shot_no']:
            frame['reload_parameters'] = True
        else:
            frame['reload_parameters'] = False

        # current shot
        shot = self.framelist.get_shot_from_frame(frame)

        # Curves library
        if self.current_frame is None or frame['k_ed'] != self.current_frame['k_ed']:
            if self.current_frame is None:
                print("edition changed, reload curves library None->%s" % (frame['k_ed']))
                log.info("edition changed, reload curves library None->%s" % (frame['k_ed']))
            else:
                print("edition changed, reload curves library %s->%s" % (self.current_frame['k_ed'], frame['k_ed']))
                log.info("edition changed, reload curves library %s->%s" % (self.current_frame['k_ed'], frame['k_ed']))
            curves_library = self.model_curves.get_library_curves(frame['k_ed'], frame['k_ep'])
            self.signal_curves_library_modified.emit(curves_library)

        # Update curves and load it into the graph
        frame['curves'] = self.model_curves.get_shot_curves_selection(db=self.model_database.database(),
            shot=shot)
        # pprint(frame)

        # Load curves, force for each frame even if previous was using the same
        try:
            # log.info("load_curves frame curves")
            self.signal_load_curves.emit(frame['curves'])
            shot_list = self.model_curves.get_shots_per_curves(frame['curves']['k_curves'])
            self.signal_shot_per_curves_modified.emit(shot_list)
        except:
            log.info("no curves to load")
            self.signal_load_curves.emit(None)
            self.signal_shot_per_curves_modified.emit(None)


        # Purge image from the previous frame
        # this is necessary to limit the memory consumption
        self.purge_current_frame_cache()

        # Set current frame
        self.current_frame = frame

        # Generate the image for this frame
        options = self.preview_options
        if options is not None:
            index, img = generate_single_image(self.current_frame, preview_options=options)
            self.set_current_frame_cache(img=img)

        return self.current_frame







def generate_single_image(frame:dict, preview_options:dict):
    # log.info("generate single image")
    # print("\ngenerate_single_image:")
    # pprint(preview_options)
    now = time.time()
    img = None

    frame['cache_initial'] = cv2.imread(frame['filepath'], cv2.IMREAD_COLOR)
    # try:
    #     if frame['cache_initial'] is None:
    #         # The original has not yet been loaded
    #         frame['cache_initial'] = cv2.imread(frame['filepath'], cv2.IMREAD_COLOR)
    # except:
    #     frame['cache_initial'] = None

    img_original = frame['cache_initial']
    h, w, c = img_original.shape
    # print("\t-> initial: ", frame['cache_initial'].shape)

    # Upscale images to fit images to screen
    do_resize_image_to_screen = preview_options['selection']['is_fit_image_to_screen']
    if do_resize_image_to_screen:
        screens = QApplication.screens()
        h_resized = screens[0].size().height()
        w_resized = int((w * h_resized) / h)
        img_resized = cv2.resize(img_original,
                    (w_resized, h_resized),
                    interpolation=cv2.INTER_LANCZOS4)
    else:
        h_resized = h
        w_resized = w
        img_resized = img_original

    # Apply rgb curves
    if preview_options['curves']['is_enabled'] and frame['curves'] is not None:
        try:
            img_rgb = filter_rgb(frame, img_resized)
        except:
            print("Error: cannot apply RGB curves")
            img_rgb = img_resized

        if preview_options['curves']['split']:
            # Merge 2 images to split the screen
            x = preview_options['curves']['split_x']
            if do_resize_image_to_screen:
                x = int((x * h_resized) / h)
            img_rgb[0:h_resized,x:w_resized,] = img_resized[0:h_resized,x:w_resized,]
        return (frame['frame_no'], img_rgb)
    else:
        return (frame['frame_no'], img_resized)

