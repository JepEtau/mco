#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
sys.path.append('../scripts')

import gc
import os
import os.path
from pprint import pprint
from logger import log

from PySide6.QtCore import(
    QObject,
    Signal,
)
from PySide6.QtWidgets import QApplication

from curves_editor.preferences import Preferences
from curves_editor.model_framelist import Model_framelist
from curves_editor.model_curves import Model_curves

from models.model_database import Model_database

from parsers.parser_curves import get_curves_names
from utils.common import K_ALL_PARTS
from utils.common import K_GENERIQUES
from utils.common import recursive_update
from utils.get_filters import FILTER_BASE_NO


class Model_curves_editor(QObject):
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



    def __init__(self):
        super(Model_curves_editor, self).__init__()
        self.view = None

        # Load saved preferences
        self.preferences = Preferences()

        # Variables
        self.step_labels = [k for k, v in sorted(FILTER_BASE_NO.items(), key=lambda item: item[1])]
        self.model_database = Model_database()
        self.framelist = Model_framelist(self.model_database)
        self.model_curves = Model_curves(self.model_database)
        self.model_curves.browse_curves_folder()

        self.shotlist_no = list()


    def exit(self):
        # print("\t%s: save and exit" % (__name__))
        p = self.view.get_preferences()
        self.preferences.save(p)
        try:
            log.handlers[0].close()
        except:
            pass
        # print("\t\tdone")

    def set_view(self, view):
        self.view = view

        self.view.widget_curves_editor.signal_directory_changed[dict].connect(self.event_directory_changed)
        self.view.widget_curves_editor.signal_filter_by_changed[dict].connect(self.update_filter_by)
        self.view.widget_curves_editor.signal_select_image[str].connect(self.select_frame)

        p = self.preferences.get_preferences()
        k_ep = 'ep%02d' % (p['tools']['episode']) if p['tools']['episode'] != '' else ''
        self.framelist.set_new_filter_by(p['selected'])

        self.view.widget_curves_editor.signal_set_shot_curves[dict].connect(self.event_select_curves)
        self.view.widget_curves_editor.signal_reset_shot_curves[str].connect(self.event_reset_curves)
        self.view.widget_curves_editor.signal_reset_curves[str].connect(self.event_reload_curves)

        self.view.widget_curves_editor.signal_backup_curves[dict].connect(self.event_backup_curves)
        self.view.widget_curves_editor.signal_save_curves[dict].connect(self.event_save_curves_as)
        self.view.widget_curves_editor.signal_mark_shot_as_modified[str].connect(self.event_mark_shot_as_modified)
        self.view.widget_curves_editor.signal_save_database[dict].connect(self.event_save_database)

        self.view.signal_reload_folder.connect(self.event_reload_folders)

        self.event_reload_folders()
        # self.event_directory_changed({'k_ep': k_ep, 'k_part': p['tools']['part']})

    def get_preferences(self):
        p = self.preferences.get_preferences()
        return p



    def save_preferences(self, preferences:dict):
        preferences = self.ui.get_preferences()
        self.preferences.save(preferences)


    def event_reload_folders(self):
        episode_and_parts = self.get_available_episode_and_parts()
        self.signal_folders_parsed.emit(episode_and_parts)



    def get_available_episode_and_parts(self) -> dict:
        episode_and_parts = dict()
        path_images = self.framelist.get_images_path()
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

        return episode_and_parts



    def event_directory_changed(self, values:dict):
        """ Directory has been changed, update the database, list all images,
            list all shots
        """
        k_ep = values['k_ep']
        k_part = values['k_part']
        log.info("directory_changed: %s:%s" % (k_ep, k_part))
        # pprint(values)
        if k_ep == '' and k_part == '':
            return

        # Parse remaining elements not already parsed
        if k_part in ['g_debut', 'g_fin']:
            k_eps = ['']
        else:
            k_eps = [k_ep]

        shotlist = dict()
        for k_ep_tmp in k_eps:
            # print(">>>>>>>>>>>>>>>>>>>>>>>> %s:%s <<<<<<<<<<<<<<<<<<<<" % (k_ep_tmp, k_part))
            self.model_database.consolidate_database(k_ep=k_ep_tmp, k_part=k_part,
                do_parse_curves=True,
                do_parse_replace=False,
                do_parse_geometry=False)

            # List of shots and curves in shotlist
            shotlist_tmp = get_curves_names(self.model_database.database(), k_ep=k_ep_tmp, k_part=k_part)
            recursive_update(out_dict=shotlist, in_dict=shotlist_tmp)
        # print("---------------------------------------------------------")
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
                            self.framelist.append(k_ep, k_part, f)
            else:
                if os.path.exists(os.path.join(path_images, k_ep)):
                    path = os.path.join(path_images, k_ep, k_part)
                    if os.path.exists(path):
                        for f in os.listdir(path):
                            if f.endswith(".png"):
                                self.framelist.append(k_ep, k_part, f)
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
        gc.collect()
        self.signal_refresh_curves_list.emit(self.model_curves.names())
        self.signal_selected_directory_changed.emit(selected)



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


    def select_frame(self, image_name=''):
        frame = self.framelist.get_frame(image_name)
        if frame is None or image_name == '':
            log.info("select frame but frame not found, image_name:%s" % (image_name))
            self.signal_load_curves.emit(None)
            self.signal_refresh_curves_shot_list.emit([])
            self.signal_display_frame.emit(None)
            return

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