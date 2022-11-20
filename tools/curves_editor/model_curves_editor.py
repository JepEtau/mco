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
from curves_editor.model_curves import Model_curves

from parsers.parser_generiques import parse_get_dependencies_for_generique
from utils.common import (
    K_ALL_PARTS,
    K_GENERIQUES,
    recursive_update,
)
from utils.get_filters import FILTER_BASE_NO
from images.filtering import filter_rgb


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
    signal_shotlist_modified = Signal(dict)


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


        # Variables: previous
        self.framelist = Model_framelist(self.model_database)
        self.model_curves = Model_curves(self.model_database)
        self.model_curves.browse_curves_folder()
        self.shotlist_no = list()




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

        # self.view.widget_curves_editor.signal_backup_curves[dict].connect(self.event_backup_curves)
        # self.view.widget_curves_editor.signal_save_curves[dict].connect(self.event_save_curves_as)
        # self.view.widget_curves_editor.signal_mark_shot_as_modified[str].connect(self.event_mark_shot_as_modified)
        # self.view.widget_curves_editor.signal_save_database[dict].connect(self.event_save_database)

        # New:
        self.view.widget_selection.signal_selection_changed[dict].connect(self.selection_changed)
        # self.view.widget_selection.signal_selected_shots_changed[dict].connect(self.event_selected_shots_changed)


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
        # Override the function
        episode_and_parts = dict()
        path_images = self.model_database.get_images_path()
        if os.path.exists(path_images):
            log.info("get available episode and parts")
            # Rather than walking through, try every possibilities
            # another option would be to select a folder, then the combobox
            # will be disabled

            for ep_no in range(1, 39):
                k_ep = 'ep%02d' % (ep_no)
                if os.path.exists(os.path.join(path_images, k_ep)):
                    episode_and_parts[k_ep] = list()

                    for k_part in K_ALL_PARTS:
                        if os.path.exists(os.path.join(path_images, k_ep, k_part)):
                            episode_and_parts[k_ep].append(k_part)

            episode_and_parts[' '] = list()
            for k_part_g in K_GENERIQUES:
                if os.path.exists(os.path.join(path_images, k_part_g)):
                    episode_and_parts[' '].append(k_part_g)

        print("get_available_episode_and_parts")
        pprint(episode_and_parts)

        return episode_and_parts


    def selection_changed(self, selection:dict):
        """ Selection has been changed, update the database, list all images,
            list all shots
        """
        print("selection_changed")
        print("from")
        pprint(self.current_selection)
        print("----------------------- selection_changed -------------------------")
        pprint(selection)

        k_ed =  selection['k_ed']
        k_ep =  selection['k_ep']
        k_part =  selection['k_part']

        if (k_ed != self.current_selection['k_ed']
            or k_ep != self.current_selection['k_ep']
            or k_part != self.current_selection['k_part']):
            # The new selected ep/part is different, parse the folder
            # and create a new list of frames

            images_path = self.model_database.get_images_path()
            if k_part in K_GENERIQUES:
                images_path = os.path.join(images_path, k_part)
            else:
                images_path = os.path.join(images_path, k_ep, k_part)
            print("image path: %s" % (images_path))

            self.framelist.clear()
            # try:
            for filename in os.listdir(images_path):
                if filename.endswith(".png"):
                    self.framelist.append(filename, k_ep, k_part)
            # except:
            #     print("error: the folder does not exist anymore")

        # Consolidate the list of frames
        self.framelist.consolidate()

        pprint(self.framelist.get_frames())

        # Get frames which corresponds to the 'filter_by' structure
        self.frames = self.framelist.get_selected_frames(selection)
        print("selected frames:")
        pprint(self.frames)

        self.current_selection = deepcopy(selection)
        self.signal_framelist_modified.emit(self.frames)

        # self.model_database.initialize_shots_per_curves(self.shots)
        # self.signal_curves_library_modified.emit(self.model_database.get_library_curves())
        # self.signal_shotlist_modified.emit(self.current_selection)








    def event_directory_changed(self, values:dict):
        """ Directory has been changed, update the database, list all images,
            list all shots
        """
        k_ep = values['k_ep']
        k_part = values['k_part']
        log.info("directory_changed: %s:%s" % (k_ep, k_part))
        pprint("directory_changed: %s:%s" % (k_ep, k_part))
        pprint(values)
        if k_ep == '' and k_part == '':
            return

        # Parse remaining elements not already parsed
        if k_part in ['g_debut', 'g_fin']:
            k_eps = ['']
        else:
            k_eps = [k_ep]

        shotlist = dict()
        for k_ep_tmp in k_eps:
            print(">>>>>>>>>>>>>>>>>>>>>>>> %s:%s <<<<<<<<<<<<<<<<<<<<" % (k_ep_tmp, k_part))
            self.model_database.consolidate_database(k_ep=k_ep_tmp, k_part=k_part,
                do_parse_curves=True,
                do_parse_replace=False,
                do_parse_geometry=False,
                apply_patch_for_study=True)

            # List of shots and curves in shotlist
            shotlist_tmp = self.get_curves_names(self.model_database.database(), k_ep=k_ep_tmp, k_part=k_part)
            recursive_update(out_dict=shotlist, in_dict=shotlist_tmp)
        print("---------------------------------------------------------")
        # pprint(shotlist)
        # sys.exit()


        if k_part in K_GENERIQUES:
            self.model_curves.browse_curves_folder(k_ep_or_g=k_part)
        else:
            self.model_curves.browse_curves_folder(k_ep_or_g=k_ep)

        # Create a list of frames from the directory
        self.framelist.clear()
        path_images = self.framelist.get_images_path()
        if os.path.exists(path_images):
            if k_part in K_GENERIQUES:
                path = os.path.join(path_images, k_part)
                if os.path.exists(path):
                    for f in os.listdir(path):
                        if f.endswith(".png"):
                            self.frames.append(f)
            else:
                if os.path.exists(os.path.join(path_images, k_ep)):
                    path = os.path.join(path_images, k_ep, k_part)
                    if os.path.exists(path):
                        for f in os.listdir(path):
                            if f.endswith(".png"):
                                self.frames.append(f)
                # else:
                #   cannot parse this folder, refresh and set all to default values ?
            # else:
            #   cannot parse this folder, refresh and set all to default values ?
        # pprint(self.framelist.print())

        # Get episodes that shall be parsed
        # k_eps = self.framelist.get_episode_dependencies()
        # print(k_eps)

        self.model_curves.initialize_shots_per_curves(shotlist)
        self.model_curves.set_shotlist(shotlist)
        self.shotlist_no = list(shotlist.keys())

        # Create a dict to update the "browser" part of the editor widget
        selected = {
            'k_ep': k_ep,
            'k_part': k_part,
            'editions': self.framelist.editions(),
            'filter_ids': self.framelist.get_available_filter_ids(),
            'shotnames': list(shotlist.keys()),
            'selected': self.framelist.get_selected_struct(),
        }

        print("%s:directory_changed: %s:%s" % (__name__, k_ep, k_part))
        # pprint(new_widget_values)
        # print("-")
        # sys.exit()
        # self.signal_selected_directory_changed.emit(selected)

        self.model_database.initialize_shots_per_curves(self.shots)
        self.signal_curves_library_modified.emit(self.model_database.get_library_curves())
        self.signal_shotlist_modified.emit(self.current_selection)


    # def event_reload_folders(self):
    #     episode_and_parts = self.get_available_episode_and_parts()
    #     self.signal_folders_parsed.emit(episode_and_parts)



    def update_filter_by(self, filter_by):
        k_ep = filter_by['k_ep']
        k_part = filter_by['k_part']
        k_ed = filter_by['k_ed']
        log.info("update filter_by in model and send the new list to the browser %s:%s:%s" % (k_ed, k_ep, k_part))

        if filter_by['todo']:
            log.info("select todo list")
            # Show all shots which have no associated curves
            # if k_ed == '':
            #     print("Error: cannot show shots for an unspecified edition")
            #     return

            shotlist = self.model_curves.get_all_todo_shots(k_ed, k_ep, k_part)
            self.signal_refresh_shotlist.emit(shotlist)

        elif len(filter_by['shots']) == 0:
            # Refresh the shot list
            # print("update_filter_by, shot list, count=%d -> no shot selected" % (len(filter_by['shots'])))
            # self.signal_refresh_shotlist.emit(self.framelist.shot_names())
            self.signal_refresh_shotlist.emit(self.shotlist_no)

        # print("set the new filter")
        # pprint(filter_by)
        # Update filter_by in framelist
        self.framelist.set_new_filter_by(filter_by)

        # Get the list of images
        filtered_imagelist = self.framelist.get_filtered_imagelist()
        self.signal_refresh_framelist.emit(filtered_imagelist)



    def get_step_labels(self):
        return self.step_labels


    def get_available_filter_ids(self):
        return self.framelist.get_available_filter_ids()


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



    # Imported from video_editor!
    #-----------------------------------------------------
    def event_rgb_graph_modified(self, rgb_channels):
        shot_no = self.current_frame['shot_no']
        self.model_database.set_shot_rgb_channels(
            shot=self.shots[shot_no],
            rgb_channels=rgb_channels)
        self.signal_reload_frame.emit()


    def event_curves_selection_changed(self, k_curves:str):
        log.info("select the new curves for this shot [%s]" % (k_curves))
        shot_no = self.current_frame['shot_no']
        shot = self.shots[shot_no]
        curves = self.model_database.get_curves_selection(shot=shot)

        # Update the modifications structure to update the selection widget
        if k_curves != self.shots[shot_no]['modifications']['curves']['initial']:
            log.info("selection has changed")
            self.shots[shot_no]['modifications']['curves']['new'] = k_curves
            # Modify the selected curves in the db
            self.model_database.set_curves_selection(
                shot=shot,
                k_curves=k_curves)
        else:
            # Discard the current selected curves
            self.shots[shot_no]['modifications']['curves']['new'] = None
            self.model_database.discard_curves_selection(shot=shot)

        # Get the new selected curves
        curves = self.model_database.get_curves_selection(shot=shot)

        # Refresh the list of shot for these curves
        shot_list = self.model_database.get_shots_per_curves(k_curves)
        self.signal_shot_per_curves_modified.emit(shot_list)

        self.signal_current_shot_modified.emit(shot['modifications'])
        self.signal_load_curves.emit(curves)
        self.signal_reload_frame.emit()


    def event_discard_rgb_curves_modifications(self, k_curves:str):
        self.model_database.discard_rgb_curves_modifications(k_curves)
        k_part = self.current_selection['k_part']
        k_ep = self.current_selection['k_ep']

        # Get the initial curves
        curves = self.model_database.get_curves(
            k_ep_or_g = k_part if k_part in K_GENERIQUES else k_ep,
            k_curves=k_curves)

        # Send the list of curves
        self.signal_curves_library_modified.emit(self.model_database.get_library_curves())

        # Reload curves
        self.signal_load_curves.emit(curves)
        self.signal_reload_frame.emit()


    def event_save_curves_as(self, curves):
        # Save the curves in the curves library
        log.info("save the curves: %s -> %s" % (curves['k_curves_current'], curves['k_curves_new']))
        # if curves['k_curves_new'] == '':
        #     log.error("No name defined in the curves struct")
        #     return

        k_part = self.current_frame['k_part']
        k_ep = self.current_frame['k_ep']
        self.model_database.save_rgb_curves_as(
            k_ep_or_g=k_part if k_part in K_GENERIQUES else k_ep,
            curves=curves)
        self.signal_curves_library_modified.emit(self.model_database.get_library_curves())

        # Modify the current selection
        if curves['k_curves_new'] is not None:
            k_curves_new = curves['k_curves_new']
            self.event_curves_selection_changed(k_curves_new)


    def event_save_curves_selection_requested(self):
        # Save the curves selected for this shot
        shot_no = self.current_frame['shot_no']
        # print("event_save_curves_selection_requested %s:%s:%s:%d" % (k_ed, k_ep, k_part, shot_no))
        self.model_database.save_shot_curves_selection(self.shots[shot_no])

        # Update the modifications structure to update the selection widget
        k_new_curves = self.shots[shot_no]['modifications']['curves']['new']
        self.shots[shot_no]['modifications']['curves'] = {
            'initial': k_new_curves,
            'new': None,
        }
        self.signal_current_shot_modified.emit(self.shots[shot_no]['modifications'])
        self.signal_is_saved.emit('curves_selection')




    def event_save_and_close_requested(self):
        k_ep = self.current_selection['k_ep']
        k_part = self.current_selection['k_part']

        self.event_save_replace_requested()

        self.model_database.save_curves_selection_database(
            self.shots,
            k_ed='',
            k_ep='',
            k_part=k_part,
            shot_no=-1)

        self.event_save_geometry_requested()
        self.model_database.save_all_curves(k_ep_or_g=k_part if k_part in K_GENERIQUES else k_ep)
        self.signal_close.emit()


    def select_image(self, image_name=''):
        frame = self.framelist.get_frame(image_name)

        # Shot has changed: update UI with parameters for this shot (curves, crop, resize)
        if self.current_frame is None or frame['shot_no'] != self.current_frame['shot_no']:
            frame['reload_parameters'] = True
        else:
            frame['reload_parameters'] = False

        # current shot
        shot = self.shots[frame['shot_no']]

        # Update curves and load it into the graph
        frame['curves'] = self.model_database.get_curves_selection(shot=shot)
        if self.current_frame is None or frame['shot_no'] != self.current_frame['shot_no']:
            try:
                self.signal_load_curves.emit(frame['curves'])
                shot_list = self.model_database.get_shots_per_curves(frame['curves']['k_curves'])
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

        if False:
            # previous
            frame_k_ed = frame['k_ed']
            frame_k_ep = frame['k_ep']

            # log.info("select frame: %s (shot:%d)" % (image_name, frame['shot_no']))
            if not self.model_curves.is_shot_modified(frame['shot_no'], k_ed=frame_k_ed, k_ep=frame_k_ep):
                curves = self.model_curves.get_curves_from_shot_no(frame['shot_no'], k_ed=frame_k_ed, k_ep=frame_k_ep)

            # Get new list of shots that are using the same k_curve
            frame['k_curves'] = self.model_curves.get_k_curves_from_shot_no(frame['shot_no'], k_ed=frame_k_ed, k_ep=frame_k_ep)
            frame['k_curves_initial'] = self.model_curves.get_initial_k_curves_from_shot_no(frame['shot_no'], k_ed=frame_k_ed, k_ep=frame_k_ep)
            shot_list_for_k_curve = self.model_curves.get_shots_from_k_curves(frame['k_curves'])

            # Load rgb curves, refresh shot list for this k_curve and display the selected image
            if not self.model_curves.is_shot_modified(frame['shot_no'], k_ed=frame_k_ed, k_ep=frame_k_ep):
                self.signal_load_curves.emit(curves)
            self.signal_refresh_curves_shot_list.emit(shot_list_for_k_curve)
            self.signal_display_frame.emit(frame)


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
        return (frame['index'], img_rgb)
    else:
        return (frame['index'], img_resized)

