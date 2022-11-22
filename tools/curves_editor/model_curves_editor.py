# -*- coding: utf-8 -*-

import sys

from parsers.parser_curves import parse_curves_folder
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
    nested_dict_set,
    recursive_update,
)
from utils.get_filters import FILTER_BASE_NO
from images.filtering import filter_rgb

from utils.get_curves import calculate_channel_lut
from parsers.parser_curves import (
    get_curves_selection,
    parse_curves_file,
    parse_curves_folder,
    write_curves_file,
)



class Model_curves_editor(Model_common):
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
        for step in ['bgd', 'stitching']:
            self.step_labels.remove(step)

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

        # Previous
        # self.view.widget_curves_editor.signal_directory_changed[dict].connect(self.event_directory_changed)
        # self.view.widget_curves_editor.signal_filter_by_changed[dict].connect(self.update_filter_by)
        # self.view.widget_curves_editor.signal_select_image[str].connect(self.select_frame)

        # self.framelist.set_new_filter_by(p['selected'])

        # self.view.widget_curves_editor.signal_set_shot_curves[dict].connect(self.event_select_curves)
        # self.view.widget_curves_editor.signal_reset_shot_curves[str].connect(self.event_reset_curves)
        # self.view.widget_curves_editor.signal_reset_curves[str].connect(self.event_reload_curves)

        # self.view.widget_curves_editor.signal_save_curves[dict].connect(self.event_save_curves_as)
        # self.view.widget_curves_editor.signal_save_database[dict].connect(self.event_save_database)

        # New:
        self.view.widget_selection.signal_selection_changed[dict].connect(self.selection_changed)
        # self.view.widget_selection.signal_selected_shots_changed[dict].connect(self.event_selected_shots_changed)

        self.view.widget_curves.widget_rgb_graph.signal_graph_modified[dict].connect(self.event_rgb_graph_modified)
        self.view.widget_curves.widget_curves_selection.signal_curves_selection_changed[str].connect(self.event_curves_selection_changed)
        self.view.widget_curves.signal_save_rgb_curves_as[dict].connect(self.event_save_rgb_curves_as)
        self.view.widget_curves.widget_curves_selection.signal_save_curves_selection_requested.connect(self.event_save_curves_selection_requested)
        self.view.widget_curves.widget_curves_selection.signal_discard_curves[str].connect(self.event_discard_rgb_curves_modifications)

        self.view.signal_preview_options_changed[dict].connect(self.event_preview_options_changed)
        self.view.signal_save_and_close.connect(self.event_save_and_close_requested)


        # Force refresh of preview options
        self.view.event_preview_options_changed('model')

        p = self.preferences.get_preferences()
        pprint(p)
        k_ep = 'ep%02d' % (p['selection']['episode']) if p['selection']['episode'] != '' else ''
        self.selection_changed({
                'k_ed': p['selection']['edition'],
                'k_ep': k_ep,
                'k_part': p['selection']['part'],
                'k_step': p['selection']['step'],
                'filter_ids': list(),
                'shot_nos': list(),
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


    def selection_changed(self, selection:dict):
        """ Selection has been changed, update the database, list all images,
            list all shots
        """
        # print("----------------------- selection_changed -------------------------")
        # pprint(selection)

        k_ed =  selection['k_ed']
        k_ep =  selection['k_ep']
        k_part =  selection['k_part']
        log.info("selection changed to %s:%s:%s" % (k_ed, k_ep, k_part))
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

        k_eps = list()
        k_parts = list()
        if (k_ed != self.current_selection['k_ed']
            or k_ep != self.current_selection['k_ep']
            or k_part != self.current_selection['k_part']):
            # The new selected ep/part is different, parse the folder
            # and create a new list of frames
            log.info("changed directory")
            self.current_selection = deepcopy(selection)

            images_path = self.model_database.get_images_path()
            if k_part in K_GENERIQUES:
                images_path = os.path.join(images_path, k_part)
            else:
                images_path = os.path.join(images_path, k_ep, k_part)
            print("image path: %s" % (images_path))
            log.info("image path: %s" % (images_path))

            self.framelist.clear()
            # try:
            for filename in os.listdir(images_path):
                if filename.endswith(".png"):
                    self.framelist.append(images_path, filename, k_ep, k_part)
            # except:
            #     print("error: the folder does not exist anymore")

            # Initialize db dor curves
            self.model_curves.initialize_curves_library(db=self.model_database.database(),
                k_ep=k_ep, k_part=k_part)

            # Consolidate the list of frames
            self.framelist.consolidate()
            # pprint(self.framelist.get_frames())

            # List of shots
            shotlist = self.framelist.get_shotlist()

            # Initialize the curves selection
            self.model_curves.initialize_curves_selection(shotlist=shotlist, k_part=k_part)


            # Reorganize shot list
            shotlist_tmp = dict()
            for k_ed in shotlist.keys():
                    for k_ep in shotlist[k_ed].keys():
                        for shot_no in shotlist[k_ed][k_ep].keys():
                            shot = shotlist[k_ed][k_ep][shot_no]

                            if shot_no not in shotlist_tmp.keys():
                                shotlist_tmp[shot_no] = [shot]
                            else:
                                shotlist_tmp[shot_no].append(shot)

            shotlist_ordered = dict()
            shot_nos = sorted(list(shotlist_tmp.keys()))
            no = 0
            for shot_no in shot_nos:
                shots = shotlist_tmp[shot_no]
                for shot in shots:
                    shotlist_ordered[no] = shot
                    no += 1

            self.signal_curves_library_modified.emit(self.model_curves.get_library_curves())

            # pprint(shotlist_ordered)
            self.signal_shotlist_modified.emit(shotlist_ordered)

        else:
            self.current_selection = deepcopy(selection)


        # Get frames after applied the 'filter_by' structure
        self.frames = self.framelist.get_selected_frames(self.current_selection)
        # print("selected frames:")
        # pprint(self.frames)

        # List of frames
        self.signal_framelist_modified.emit(self.frames)







    def event_curves_selection_changed(self, k_curves:str):
        log.info("select the new curves for this shot [%s]" % (k_curves))
        # current shot
        shot = self.framelist.get_shot_from_frame(self.current_frame)
        curves = self.model_curves.get_curves_selection(db=self.model_database.database(),
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
        curves = self.model_curves.get_curves_selection(db=self.model_database.database(),
            shot=shot)

        # Refresh the list of shot for these curves
        shot_list = self.model_curves.get_shots_per_curves(k_curves)
        self.signal_shot_per_curves_modified.emit(shot_list)

        self.signal_current_shot_modified.emit(shot)
        self.signal_load_curves.emit(curves)
        self.signal_reload_frame.emit()





    def event_select_curves(self, curves_dict:dict):
        """ A curve has been selected for a shot
        """
        # print("%s.event_select_curves" % (__name__))
        # pprint(curves_dict)
        curve_name = curves_dict['k_curves']
        frame = self.framelist.get_frame(curves_dict['image_name'])

        # Get RGB curves (parse the file if not already done)
        rgb_curves = self.model_curves.get_curves_from_name(curve_name)

        # Modifiy the curve of the selected shot
        shot_no = self.framelist.get_shot_no_from_image_name(curves_dict['image_name'])
        self.model_curves.set_curves_to_shot(shot_no, curve_name, k_ed=frame['k_ed'], k_ep=frame['k_ep'])

        frame['k_curves'] = curve_name

        # Get new list of shots that are using the same k_curves
        shot_list_for_k_curve = self.model_curves.get_shots_from_k_curves(curve_name)

        # Refresh the list of shats that are using the same curves and apply new rgb curves
        self.signal_refresh_curves_shot_list.emit(shot_list_for_k_curve)
        self.signal_load_curves.emit(rgb_curves)

        # Inform the "browser" that this shot is modified
        self.signal_refresh_modified_shots.emit(self.model_curves.get_modified_shots())


    def event_reset_curves(self, image_name):
        """ Set the curve for this shot to initial
        """
        log.info("reset %s to initial curves" % (image_name))
        # Get shot no. and reset to initial curves
        frame = self.framelist.get_frame(image_name)
        shot_no = self.framelist.get_shot_no_from_image_name(image_name)
        self.model_curves.reset_shot_curve(shot_no, k_ed=frame['k_ed'], k_ep=frame['k_ep'])

        # Send a list of modified shots
        print("event_reset_curves")
        print(self.model_curves.get_modified_shots())
        self.signal_refresh_modified_shots.emit(self.model_curves.get_modified_shots())

        # Reload image with initial curves
        self.select_frame(image_name)


    def event_reload_curves(self, k_curves):
        log.info("reset %s to initial" % (k_curves))
        self.model_curves.reload_curves(k_curves)
        rgb_curves = self.model_curves.get_curves_from_name(k_curves)
        do_reload_shots = self.model_curves.revert_modified_shot_using_k_curves(k_curves)

        self.signal_load_curves.emit(rgb_curves)
        if do_reload_shots:
            self.signal_refresh_modified_shots.emit(self.model_curves.get_modified_shots())



    def event_mark_shot_as_modified(self, image_name):
        # Inform the "browser" that this shot is modified
        shot_no = self.framelist.get_shot_no_from_image_name(image_name)
        frame = self.framelist.get_frame(image_name)
        frame_k_ed = frame['k_ed']
        frame_k_ep = frame['k_ep']
        self.model_curves.mark_shot_as_modified(shot_no, k_ed=frame_k_ed, k_ep=frame_k_ep)
        self.signal_refresh_modified_shots.emit(self.model_curves.get_modified_shots())


    def event_backup_curves(self, curves_dict:dict):
        log.info("backup [%s] curves" % (curves_dict['k_curves']))
        k_curves = curves_dict['k_curves']
        self.model_curves.backup_curves(k_curves, curves_dict['channels'])


    def event_save_curves_as(self, curves_dict:dict):
        log.info("global mode: save curve as %s for image %s" % (curves_dict['k_curves'], curves_dict['image_name']))

        k_curves = curves_dict['k_curves']
        # Save curves
        if curves_dict['channels'] is not None:
            self.model_curves.save_curves(k_curves, curves_dict['channels'])

        # Modify shot: use the frame to find the shot no.
        frame = self.framelist.get_frame(curves_dict['image_name'])
        frame['k_curves'] = k_curves

        # Save the database, use the frame struct to save the
        # correspondant edition/episode/part
        # pprint(frame)
        # self.model_curves.save_database(frame)
        # self.signal_refresh_modified_shots.emit(self.model_curves.get_modified_shots())

        # RGB curves: parse the file if not already done
        rgb_curves = self.model_curves.get_curves_from_name(k_curves)

        # Modifiy current shot curve
        # shot_no = self.framelist.get_shot_no_from_image_name(curves['image_name'])
        self.model_curves.set_curves_to_shot(frame['shot_no'], k_curves, k_ed=frame['k_ed'], k_ep=frame['k_ep'])

        # Refresh list of curves
        self.signal_refresh_curves_list.emit(self.model_curves.names())
        # self.select_frame(curves['image_name'])
        self.signal_display_frame.emit(frame)


    def event_save_database(self, curves:dict):
        log.info("global mode: save curve as %s for image %s" % (curves['k_curves'], curves['image_name']))

        k_curves = curves['k_curves']
        # Save curves
        if curves['channels'] is not None and k_curves != '':
            self.model_curves.save_curves(k_curves, curves['channels'])

        # Modify shot: use the frame to find the shot no.
        frame = self.framelist.get_frame(curves['image_name'])

        # Save the database, use the frame struct to save the
        # correspondant edition/episode/part
        self.model_curves.save_curves_database(k_ep=frame['k_ep'], k_part=frame['k_part'])
        frame['k_curves_initial'] = k_curves

        # Send a list of modified shots
        self.signal_refresh_modified_shots.emit(self.model_curves.get_modified_shots())

        self.signal_refresh_frame_properties.emit(frame)


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
        shot = self.framelist.get_shot_from_frame(self.current_frame)
        self.model_curves.set_shot_rgb_channels(shot=shot, rgb_channels=rgb_channels)
        self.signal_reload_frame.emit()


    def event_discard_rgb_curves_modifications(self, k_curves:str):
        self.model_curves.discard_rgb_curves_modifications(k_curves)
        k_part = self.current_selection['k_part']
        k_ep = self.current_selection['k_ep']

        # Get the initial curves
        curves = self.model_curves.get_curves(
            k_ep_or_g = k_part if k_part in K_GENERIQUES else k_ep,
            k_curves=k_curves)

        # Send the list of curves
        self.signal_curves_library_modified.emit(self.model_curves.get_library_curves())

        # Reload curves
        self.signal_load_curves.emit(curves)
        self.signal_reload_frame.emit()


    def event_save_rgb_curves_as(self, curves):
        # Save the curves in the curves library
        log.info("save the rgb curves: %s -> %s" % (curves['k_curves_current'], curves['k_curves_new']))
        print("\nsave the rgb curves: %s -> %s" % (curves['k_curves_current'], curves['k_curves_new']))
        # if curves['k_curves_new'] == '':
        #     log.error("No name defined in the curves struct")
        #     return

        k_part = self.current_frame['k_part']
        k_ep = self.current_frame['k_ep']
        self.model_curves.save_rgb_curves_as(
            db=self.model_database.database(),
            k_ep_or_g=k_part if k_part in K_GENERIQUES else k_ep,
            curves=curves)
        self.signal_curves_library_modified.emit(self.model_curves.get_library_curves())

        # Modify the current selection
        if curves['k_curves_new'] is not None:
            k_curves_new = curves['k_curves_new']
            self.event_curves_selection_changed(k_curves_new)


    def event_save_curves_selection_requested(self):
        log.info("save curves selection")
        # Save the curves selected for this shot
        shot = self.framelist.get_shot_from_frame(self.current_frame)

        if shot['modifications']['curves']['new'] is None:
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

        # Update curves and load it into the graph
        frame['curves'] = self.model_curves.get_curves_selection(db=self.model_database.database(),
            shot=shot)
        if self.current_frame is None or frame['shot_no'] != self.current_frame['shot_no']:
            try:
                self.signal_load_curves.emit(frame['curves'])
                shot_list = self.model_curves.get_shots_per_curves(frame['curves']['k_curves'])
                self.signal_shot_per_curves_modified.emit(shot_list)
            except:
                self.signal_load_curves.emit(None)
                self.signal_shot_per_curves_modified.emit(None)
        elif self.current_frame is None:
            self.signal_load_curves.emit(None)


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

    try:
        if frame['cache_fgd'] is None:
            # The original has not yet been loaded
            frame['cache_fgd'] = cv2.imread(frame['filepath'], cv2.IMREAD_COLOR)
    except:
        frame['cache_fgd'] = None

    img_original = frame['cache_fgd']
    h, w, c = img_original.shape
    # print("\t-> initial: ", frame['cache_fgd'].shape)

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
            print("Cannot apply RGB curves")
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

