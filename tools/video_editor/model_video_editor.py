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

from PySide6.QtCore import (
    Signal,
)

from common.preferences import Preferences
from models.model_database import Model_database
from models.model_common import (
    Model_common,
)

from utils.common import (
    K_GENERIQUES,
    get_dimensions_from_crop_values,
)
from utils.get_frame_list import get_frame_list, get_frame_list_single
from video.consolidate_shot import consolidate_shot
from filters.filters import calculate_geometry_parameters, filter_rgb
from utils.pretty_print import *


class Model_video_editor(Model_common):
    signal_current_shot_modified = Signal(dict)
    signal_ready_to_play = Signal(dict)
    signal_is_modified = Signal(dict)
    signal_reload_frame = Signal()
    signal_is_saved = Signal(str)
    signal_replace_list_refreshed = Signal(dict)

    signal_load_curves = Signal(dict)
    signal_curves_library_modified = Signal(dict)
    signal_shot_per_curves_modified = Signal(list)

    signal_stabilize_parameters_loaded = Signal(dict)

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
        super(Model_video_editor, self).__init__()

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

        self.view.widget_replace.signal_save.connect(self.event_save_replace_requested)
        self.view.widget_replace.signal_discard.connect(self.event_replace_discard_requested)
        self.view.widget_replace.signal_replace_modified[dict].connect(self.event_frame_replaced)

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
        k_ep = 'ep%02d' % (p['selection']['episode']) if p['selection']['episode'] != '' else ''
        self.selection_changed({
            'k_ep': k_ep,
            'k_part': p['selection']['part'],
            'k_step': p['selection']['step'],
        })



    def selection_changed(self, values:dict):
        """ Directory or step has been changed, update the database, list all images,
            list all shots
        """
        # print("----------------------- selection_changed -------------------------")
        # pprint(values)
        k_ep_selected = values['k_ep']
        k_part_selected = values['k_part']
        task = 'deinterlace' if values['k_step'] == '' else values['k_step']
        if ((k_ep_selected == '' and k_part_selected == '')
            or (k_ep_selected != '' and k_part_selected == '')):
            return
        log.info("directory_changed: %s:%s" % (k_ep_selected, k_part_selected))

        self.model_database.consolidate_database(
            k_ep=k_ep_selected,
            k_part=k_part_selected,
            do_parse_replace=True,
            do_parse_geometry=True)
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


        # Get the part geometry
        # print("selection_changed: update geometry: %s" % (k_part_selected))
        if k_part_selected in ['g_debut', 'g_fin']:
            # Use the k_ed:k_ep defined as the source for this geometry
            part_geometry = self.model_database.get_part_geometry(
                    k_ed=db[k_part_selected]['video']['src']['k_ed'],
                    k_ep=db[k_part_selected]['video']['src']['k_ep'],
                    k_part=k_part_selected)
        elif k_part_selected in ['g_asuivre', 'g_reportage']:
            # Use the following part to get the geometry for this part
            part_geometry = self.model_database.get_part_geometry(
                    k_ed=db[k_ep_selected]['video']['target'][k_part_selected[2:]]['k_ed_src'],
                    k_ep=k_ep_selected,
                    k_part=k_part_selected[2:])
        else:
            # Use the selected ed:ep:part
            part_geometry = self.model_database.get_part_geometry(
                    k_ed=k_ed_selected,
                    k_ep=k_ep_selected,
                    k_part=k_part_selected)


        # Walk through shots
        shots = db_video['shots']
        for shot in shots:
            # For debug only
            print("\t\t%s: %s\t(%d)\t<- %s:%s:%s   %d (%d)" % (
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

            if True:
                print_lightcyan("================================== SHOT =======================================")
                pprint(shot)
                print_lightcyan("===============================================================================")


            # Geometry for this shot
            if k_part_selected in ['g_asuivre', 'g_reportage']:
                # Use the 'part' for these special cases
                k_ed_tmp = db[k_part_selected]['video']['src']['k_ed']
                shot_geometry = self.model_database.get_part_geometry(
                    k_ed=k_ed_tmp,
                    k_ep=k_ep_selected,
                    k_part=k_part_selected)
            else:
                shot_geometry = self.model_database.get_shot_geometry(shot=shot)

            # Create a list of frames for this shot
            self.frames[shot_no] = list()
            for p, i in zip(filepath_tmp, range(len(filepath_tmp))):

                if task in ['deinterlace', 'pre_replace']:
                    # Use the frame no. from video to simplify frame replacement
                    frame_no = shot['src']['start'] + i
                else:
                    frame_no = i
                    # frame_no = get_frame_no_from_filepath(p)

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
                        'part': part_geometry,
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

        self.refresh_replace_list()
        self.signal_ready_to_play.emit(self.playlist_properties)


    def event_save_and_close_requested(self):
        k_ep = self.current_selection['k_ep']
        k_part = self.current_selection['k_part']

        self.event_save_replace_requested()

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
        curves = self.model_database.get_shot_curves_selection(db=self.model_database.database(),
            shot=shot)

        # Update the modifications structure to update the selection widget
        if k_curves != self.shots[shot_no]['modifications']['curves']['initial']:
            log.info("selection has changed")
            self.shots[shot_no]['modifications']['curves']['new'] = k_curves
            # Modify the selected curves in the db
            self.model_database.set_curves_selection(db=self.model_database.database(),
                shot=shot,
                k_curves=k_curves)
        else:
            # Discard the current selected curves
            self.shots[shot_no]['modifications']['curves']['new'] = None
            self.model_database.discard_curves_selection(db=self.model_database.database(),
                shot=shot)

        # Get the new selected curves
        curves = self.model_database.get_shot_curves_selection(db=self.model_database.database(),
            shot=shot)

        # Refresh the list of shot for these curves
        shot_list = self.model_database.get_shots_per_curves(k_curves)
        self.signal_shot_per_curves_modified.emit(shot_list)

        self.signal_current_shot_modified.emit(shot['modifications'])
        self.signal_load_curves.emit(curves)
        self.signal_reload_frame.emit()


    def event_discard_rgb_curves_modifications(self, k_curves:str):
        k_ed = self.current_frame['k_ed']
        k_ep = self.current_frame['k_ep']
        self.model_database.discard_rgb_curves_modifications(k_curves, k_ed, k_ep)

        # Get the initial curves
        curves = self.model_database.get_curves(self.model_database.database(),
            k_ed=k_ed, k_ep=k_ep, k_curves=k_curves)

        # Send the list of curves
        self.signal_curves_library_modified.emit(self.model_database.get_library_curves(k_ed, k_ep))

        # Reload curves
        self.signal_load_curves.emit(curves)
        self.signal_reload_frame.emit()


    def event_save_rgb_curves_as(self, curves):
        # Save the curves in the curves library
        log.info("save the curves: %s -> %s" % (curves['k_curves_current'], curves['k_curves_new']))
        # if curves['k_curves_new'] == '':
        #     log.error("No name defined in the curves struct")
        #     return

        k_part = self.current_frame['k_part']
        k_ed = self.current_frame['k_ed']
        k_ep = self.current_frame['k_ep']
        self.model_database.append_curves_to_database(
            db=self.model_database.database(),
            k_ed=k_ed,
            k_ep=k_ep,
            k_part=k_part,
            curves=curves)
        self.signal_curves_library_modified.emit(self.model_database.get_library_curves(k_ed, k_ep))

        # Modify the current selection
        if curves['k_curves_new'] is not None:
            k_curves_new = curves['k_curves_new']
            self.event_curves_selection_changed(k_curves_new)


    def event_save_curves_selection_requested(self):
        log.info("save curves selection")
        # Save the curves selected for this shot
        shot_no = self.current_frame['shot_no']
        shot = self.shots[shot_no]

        if shot['modifications']['curves']['new'] is None:
            return

        # print("event_save_curves_selection_requested %s:%s:%s:%d" % (k_ed, k_ep, k_part, shot_no))
        self.model_database.save_shot_curves_selection(db=self.model_database.database(),
            shot=shot)

        # Update the modifications structure to update the selection widget
        k_new_curves = shot['modifications']['curves']['new']
        shot['modifications']['curves'] = {
            'initial': k_new_curves,
            'new': None,
        }
        self.signal_current_shot_modified.emit(shot['modifications'])
        self.signal_is_saved.emit('curves_selection')


    def is_replace_allowed(self):
        shot = self.get_current_shot()
        if shot is None:
            return False
        return self.model_database.is_replace_allowed(shot=shot)


    def refresh_replace_list(self):
        # List of frames to replace
        log.info("refresh list")
        list_replace = list()
        for frame in self.playlist_frames:
            frame_no = self.model_database.get_replace_frame_no(
                    shot=self.shots[frame['shot_no']],
                    frame_no=frame['frame_no'])
            if frame_no != -1:
                list_replace.append({
                    'shot_no': frame['shot_no'],
                    'src': frame_no,
                    'dst': frame['frame_no'],
                })
        self.signal_replace_list_refreshed.emit(list_replace)


    def get_replace_frame_no_str(self, index) -> str:
        # print("get_replace_frame_no_str: %d" % (index))
        frame_no = self.playlist_frames[index]['frame_no']
        shot_no = self.playlist_frames[index]['shot_no']
        new_frame_no = self.model_database.get_replace_frame_no(shot_no, frame_no)
        # print("get_replace_frame_no: %d -> %d" % (frame_no, new_frame_no))
        if new_frame_no != -1:
            return str(new_frame_no)
        return ''


    def get_next_replaced_frame_index(self, index):
        # TODO: replace this: use the list_replace
        # print("find following replaced frame")

        # print("\tsearch in %d -> %d" % (frame_no + 1, self.playlist_properties['start'] + self.playlist_properties['count']))
        for i in range(index + 1, self.playlist_properties['count']):
            shot_no = self.get_shot_no_from_index(i)
            shot = self.shots[shot_no]
            frame_no = shot['start'] + i
            if self.model_database.get_replace_frame_no(shot, frame_no) != -1:
                return i

        # print("\tsearch in %d -> %d" % (self.playlist_properties['start'], frame_no-1))
        for i in range(0, index-1):
            shot_no = self.get_shot_no_from_index(i)
            shot = self.shots[shot_no]
            frame_no = shot['start'] + i
            if self.model_database.get_replace_frame_no(shot_no, frame_no) != -1:
                return i
        return -1


    def event_frame_replaced(self, replace:dict):
        action = replace['action']
        frame_no = replace['dst']
        log.info("replace %d" % (frame_no))
        print("shot no= %d" % (self.current_frame['shot_no']))
        # pprint(self.playlist_frames)
        shot_no = self.current_frame['shot_no']
        shot_src = self.shots[shot_no]
        index = frame_no - self.frames[shot_no][0]['frame_no']



        if action == 'replace':
            log.info("replace: shot_no=%d, frame_no=%d (index=%d) by %d" % (shot_no, frame_no, index, replace['src']))
            self.model_database.set_replaced_frame(
                shot=shot_src,
                frame_no=frame_no,
                new_frame_no=replace['src'])
            # update the frame as it is required to refresh the list of the widget_replace
            # print("index: %d" % )
            # self.frames[shot_no][index]['replaced_by'] = self.model_database.get_replace_frame_no(shot_src, frame_no)

        elif action == 'remove':
            log.info("remove: shot_no=%d, frame_no=%d (index=%d)" % (shot_no, frame_no, index))
            self.model_database.remove_replaced_frame(shot=shot_src, frame_no=frame_no)

            # update the frame as it is required to refresh the list of the widget_replace
            # self.frames[shot_no][index]['replaced_by'] = self.model_database.get_replace_frame_no(shot_src, frame_no)

        self.refresh_replace_list()
        self.signal_reload_frame.emit()


    def event_replace_discard_requested(self):
        log.info("discard modifications requested")
        self.model_database.discard_replace_modifications()
        self.refresh_replace_list()
        self.signal_reload_frame.emit()


    def event_save_replace_requested(self):
        self.model_database.save_replace_database()
        self.signal_is_saved.emit('replace')



    def event_geometry_modified(self, modification:dict):
        """modification:
            - type
            - parameter
            - value
        """
        k_ed = self.current_frame['k_ed']
        k_ep = self.current_frame['k_ep']
        k_part = self.current_frame['k_part']
        shot_no = self.current_frame['shot_no']
        shot = self.shots[shot_no]
        # print("\nevent_geometry_modified for %s:%s:%s as %s" % (k_ed, k_ep, k_part, modification['type']))
        # pprint(modification)
        # print("\tshot: %s:%s:%s" % (shot['k_ed'], shot['k_ep'], shot['k_part']))

        if modification['type'] == 'part':
            type = 'part'
            # Use a copy of parameters to not modify the initial values
            k_ed_src = k_ed
            k_ep_src = k_ep
            geometry = deepcopy(self.model_database.get_part_geometry(k_ed=k_ed_src, k_ep=k_ep_src, k_part=k_part))

        elif k_part in ['g_asuivre', 'g_reportage']:
            type = 'part'
            # Use a copy of parameters to not modify the initial values
            db = self.model_database.database()
            k_ed_src = db[k_part]['target']['video']['src']['k_ed']
            k_ep_src = db[k_part]['target']['video']['src']['k_ep']
            geometry = deepcopy(self.model_database.get_part_geometry(k_ed=k_ed_src, k_ep=k_ep_src, k_part=k_part))

        else:
            type = 'shot'
            geometry = deepcopy(self.model_database.get_shot_geometry(shot=shot))


        # Modify parameter
        value = modification['value']
        if 'crop' in modification['parameter']:
            if geometry is not None:
                c_t, c_b, c_l, c_r = geometry['crop']
            else:
                geometry = {'crop':  [0, 0, 0, 0]}
                c_t, c_b, c_l, c_r = geometry['crop']

            if modification['parameter'] == 'crop_top':
                geometry['crop'][0] = max(0, min(c_t + value, 400))

            elif modification['parameter'] == 'crop_bottom':
                geometry['crop'][1] = max(0, min(c_b - value, 400))

            elif modification['parameter'] == 'crop_left':
                geometry['crop'][2] = max(0, min(c_l + value, 400))

            elif modification['parameter'] == 'crop_right':
                geometry['crop'][3] = max(0, min(c_r + value, 400))

        elif modification['parameter'] == 'fit_to_part':
            try:
                geometry['resize']['fit_to_part'] =  value
            except:
                geometry.update({'resize': {'fit_to_part': value}})

            if k_part in ['g_asuivre', 'g_reportage']:
                self.model_database.set_part_geometry(k_ed=k_ed_src, k_ep=k_ep_src, k_part=k_part, geometry=geometry)
            else:
                self.model_database.set_shot_geometry(shot=shot, geometry=geometry)

        elif modification['parameter'] == 'ratio':
            try:
                geometry['ratio'] =  value
            except:
                geometry.update({'ratio': value})


        elif modification['parameter'] == 'remove':
            # remove the shot geometry, use the part geometry
            self.model_database.remove_shot_geometry(shot=shot)

        elif modification['parameter'] == 'copy':
            # copy the part geometry into the shot geometry
            self.model_database.set_shot_geometry(
                shot=shot,
                geometry=deepcopy(self.model_database.get_part_geometry(k_ed=k_ed, k_ep=k_ep, k_part=k_part)))

        if 'crop' in modification['parameter']:
            # Add resize? maybe later...
            if type == 'part':
                self.model_database.set_part_geometry(k_ed=k_ed_src, k_ep=k_ep_src, k_part=k_part, geometry=geometry)
            elif type == 'shot':
                self.model_database.set_shot_geometry(shot=shot, geometry=geometry)


        self.signal_reload_frame.emit()


    def event_geometry_discard_requested(self):
        log.info("discard modifications requested")
        k_part = self.current_selection['k_part']
        db = self.model_database.database()
        if k_part in K_GENERIQUES:
            k_ed = db[k_part]['target']['video']['src']['k_ed']
        else:
            k_ed =self.current_selection['k_ed']
        k_ep = self.current_frame['k_ep']
        self.model_database.discard_part_geometry_modifications(k_ed=k_ed, k_ep=k_ep, k_part=k_part)
        self.signal_reload_frame.emit()


    def event_save_geometry_requested(self):
        k_part = self.current_selection['k_part']
        db = self.model_database.database()
        if k_part in ['g_debut', 'g_fin']:
            k_ed = self.current_frame['k_ed']
            k_ep = self.current_frame['k_ep']
        else:
            k_ep = self.current_selection['k_ep']
            k_ed = self.current_frame['k_ed']
        # pprint(self.current_selection)
        shot = self.shots[self.current_frame['shot_no']]

        self.model_database.save_geometry_database(k_ed=k_ed, k_ep=k_ep, k_part=k_part, shot=shot)
        self.signal_is_saved.emit('geometry')

    def get_current_shot(self):
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
        if not self.preview_options['replace']['is_enabled']:

            try: del frame['replace']
            except: pass
        else:
            print_green("get replace frame: index=%d" % (index))
            frame_no = frame['frame_no']
            shot_no = frame['shot_no']
            shot = self.shots[shot_no]
            print_green("\tshot no. %d, frame no. %d" % (shot_no, frame_no))
            new_frame_no = self.model_database.get_replace_frame_no(self.shots[shot_no], frame_no)
            if new_frame_no == -1:
                frame = self.playlist_frames[index]
                try: del frame['replace']
                except: pass
            else:
                frame = self.playlist_frames[index + (new_frame_no - frame_no)]
                frame['replace'] = frame_no

        # Shot has changed: update UI with parameters for this shot (curves, crop, resize)
        if self.current_frame is None or frame['shot_no'] != self.current_frame['shot_no']:
            frame['reload_parameters'] = True
        else:
            frame['reload_parameters'] = False

        # Current shot
        is_shot_changed = False
        shot = self.shots[frame['shot_no']]

        # if shot is different
        if self.current_frame is None or frame['shot_no'] != self.current_frame['shot_no']:
            is_shot_changed = True

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
        if shot['k_part'] in ['g_asuivre', 'g_reportage']:
            frame['geometry'].update({
                # Do not modify the part geometry
                # The shot geometry uses the 'part' stored in the  k_ep config file
                'shot': self.model_database.get_part_geometry(k_ed=shot['k_ed'], k_ep=shot['k_ep'], k_part=shot['k_part']),

                # Used when the width of the cropped img  for the shot < width of the cropped img of the part
                # is updated by the generate function
                'error': False,
            })
        else:
            frame['geometry'].update({
                'part': self.model_database.get_part_geometry(k_ed=shot['k_ed'], k_ep=shot['k_ep'], k_part=shot['k_part']),
                'shot': self.model_database.get_shot_geometry(shot=shot),

                # Used when the width of the cropped img  for the shot < width of the cropped img of the part
                # is updated by the generate function
                'error': False,
            })


        # Purge image from the previous frame
        # this is necessary to limit the memory consumption
        # TODO: create a cache structure which manage the cache
        # and another thread to generate the next frames in background (when playing as a video)
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

            geometry = calculate_geometry_parameters(shot=shot, img=frame['cache_initial'])
            pprint(geometry)

            index, img = generate_single_image(self.current_frame, geometry, preview_options=options)
            self.set_current_frame_cache(img=img)
        # print("\t%dms" % (int(1000 * (time.time() - now))))
        # else:
            # Cannot generate the image because no preview option is defined
            # The preview options will be updated by the window UI
        if is_shot_changed:
            self.signal_shot_changed.emit()

        return self.current_frame




def generate_single_image(frame:dict, geometry, preview_options:dict):
    log.info("generate single image")

    verbose = False
    if verbose:
        print("\ngenerate_single_image:")
        pprint(preview_options)
        print("\t-> %s:%s:%s" % (frame['k_ed'], frame['k_ep'], frame['k_part']))

    img_original = frame['cache_initial']
    h, w, c = img_original.shape
    # print("\t-> initial: ", frame['cache_initial'].shape)
    if verbose:
        pprint(frame['geometry'])
    # Calculate dimensions to crop the image
    try:
        c_t_p, c_b_p, c_l_p, c_r_p, c_w_p, c_h_p = get_dimensions_from_crop_values(w, h, frame['geometry']['part']['crop'])
    except:
        c_t_p, c_b_p, c_l_p, c_r_p, c_w_p, c_h_p = [0, 0, 0, 0, w, h]
    if frame['geometry']['shot'] is not None:
        # Use the customized geometry
        type = 'shot'
        c_t, c_b, c_l, c_r, c_w, c_h = get_dimensions_from_crop_values(w, h, frame['geometry']['shot']['crop'])
    else:
        # Use the part geometry
        type = 'part'
        try:
            c_t, c_b, c_l, c_r, c_w, c_h = get_dimensions_from_crop_values(w, h, frame['geometry']['part']['crop'])
        except:
            c_t, c_b, c_l, c_r, c_w, c_h = [0, 0, 0, 0, w, h]
    if verbose:
        print("\t-> use the %s geometry %d:%d:%d:%d  %dx%d" % (type, c_t, c_b, c_l, c_r, c_w, c_h))

    # Final width and height
    w_final = geometry['final']['w']
    h_final = geometry['final']['h']

    # Preview options
    options = preview_options['geometry'][type]
    # print("\t -> cropped: %dx%d" % (c_w, c_h))

    # Apply rgb curves
    #------------------------------------
    if preview_options['curves']['is_enabled'] and frame['curves'] is not None:
        try:
            img_rgb = filter_rgb(frame, img_original)
        except:
            print("Cannot apply RGB curves")
            img_rgb = img_original

        if preview_options['curves']['split']:
            # Merge 2 images to split the screen
            x = preview_options['curves']['split_x']
            if options['resize_preview']:
                w_tmp = int((c_w * h_final) / float(c_h))
                pad_left = int((w_final - w_tmp) / 2)
                x = max(0, int((x-pad_left) / (h_final / float(c_h))) + c_l)
            img_rgb[0:h,x:w,] = img_original[0:h,x:w,]
    else:
        img_rgb = img_original

    # Crop the image
    #------------------------------------
    if options['crop_edition'] and not options['crop_preview']:
        # Add a rect
        if verbose:
            print("\t-> Use the original image")
        img_cropped = img_rgb

    elif options['crop_preview']:
        # Crop and no rect
        if verbose:
            print("\t-> Crop the image, ", end='')
        c_t, c_b, c_l, c_r = geometry['crop']
        img_cropped = np.ascontiguousarray(img_rgb[
            c_t : geometry['initial']['h'] - c_b,
            c_l : geometry['initial']['w'] - c_r], dtype=np.uint8)
        if verbose:
            print("cropped: ", img_cropped.shape)

    else:
        if options['resize_preview']:
            pprint(frame['geometry'])
            print("Error: generate_single_image: resize not possible because no crop for type [%s]" % (type))
        # Use original image
        # print("\t-> Use the original image")
        img_cropped = img_rgb


    # Resize the image
    #------------------------------------
    img_resized_final = None
    img_resized = None
    if options['resize_preview']:
        # Calculate new width and new height
        w_p_tmp = int((c_w_p * h_final) / float(c_h_p))
        w_tmp = int((c_w * h_final) / float(c_h))

        # width and height of the resized cropped image for the part

        if options['crop_preview']:
            # Resize the cropped image
            try:
                do_fit_to_part = frame['geometry']['shot']['resize']['fit_to_part']
                if do_fit_to_part is not None and do_fit_to_part:
                    if verbose:
                        print("\tfit to part: w_tmp=%d -> w_p_tmp=%d" % (w_tmp, w_p_tmp))
                    w_tmp = w_p_tmp
            except:
                print("\tDO NOT fit to part: w_tmp=%d -> w_p_tmp=%d" % (w_tmp, w_p_tmp))
                pass

            img_resized = cv2.resize(src=img_cropped,
                dsize=(geometry['resize']['w'], geometry['resize']['h']),
                interpolation=cv2.INTER_LANCZOS4)

            if verbose:
                print("\t-> resized cropped image: %dx%d, calculated:%dx%d" % (img_resized.shape[1], img_resized.shape[0], w_tmp, h_final ))
        else:
            # Resize the original image and add rect
            w_p_tmp = int((w * h_final) / float(c_h_p))
            w_tmp = int((w * h_final) / float(c_h))
            h_tmp = int((h * h_final) / float(c_h))
            img_resized = cv2.resize(img_cropped, (w_tmp, h_tmp), interpolation=cv2.INTER_LANCZOS4)
            if verbose:
                print("\t-> resized original image: %dx%d, calculated:%dx%d" % (img_resized.shape[1], img_resized.shape[0], w_tmp, h_tmp ))

        if w_tmp != w_p_tmp:
            if verbose:
                print("\tw_p_tmp != w_tmp: %d vs %d" % (w_tmp, w_p_tmp))
            if options['crop_preview']:
                if verbose:
                    print("\t!!!! crop the customized image: w_tmp=%d vs w_p_tmp=%d" % (w_tmp, w_p_tmp))
                if w_tmp > w_p_tmp:
                    # Crop the image
                    # Calculate the position of the left crop of the part after resizing
                    c_l_p_resized = int(((c_l_p) * h_final) / float(c_h_p))
                    c_l_resized = int(((c_l) * h_final) / float(c_h))
                    if verbose:
                        print("\tcrop the image: c_l_p_resized=%d, c_l_resized=%d" % (c_l_p_resized, c_l_resized))
                    x0 = c_l_resized - c_l_p_resized
                    x1 = w_p_tmp + x0
                    if verbose:
                        print("\tcrop the image: x0=%d, x1=%d, (w_tmp + x0)=%d" % (x0, x1, w_tmp+x0))
                    if x1 > w_tmp:
                        # Crop is too big on the left
                        if verbose:
                            print("\tcrop is too big on the left")
                        x0 = w_tmp - w_p_tmp
                        x1 = w_tmp
                        # print("\tcrop the image: c_l_p_resized=%d, c_l_resized=%d, x0=%d, x1=%d -> new resized width=%d" % (c_l_p_resized, c_l_resized, x0, x1, x1 - x0))
                    img_resized_final = np.ascontiguousarray(img_resized[0:h_final,  x0:x1,])
                elif w_p_tmp > w_tmp:
                    if verbose:
                        print("\terror: shot_width is < part_width: w_tmp=%d,  w_p_tmp=%d" % (w_tmp, w_p_tmp))
                    try:
                        do_fit_to_part = frame['geometry']['shot']['resize']['fit_to_part']
                        if do_fit_to_part is not None and do_fit_to_part:
                            if verbose:
                                print("\tfit to part: w_tmp=%d -> w_p_tmp=%d" % (w_tmp, w_p_tmp))
                            img_resized_final = cv2.resize(img_cropped, (w_p_tmp, h_tmp), interpolation=cv2.INTER_LANCZOS4)
                        else:
                            do_fit_to_part = False
                    except:
                        do_fit_to_part = False
                        pass

                    if not do_fit_to_part:
                        frame['geometry']['error'] = True
                        pad_left = int((w_p_tmp - w_tmp)/2)
                        pad_right = w_p_tmp - w_tmp - pad_left
                        img_resized_final = np.ascontiguousarray(cv2.copyMakeBorder(img_resized, 0, 0, pad_left, pad_right,
                            cv2.BORDER_CONSTANT, value=[255, 255, 255]))
                    # if verbose:
                        # print("\t-> width (resized vs part): w_tmp=%d, w_p_tmp=%d" % (img_resized_final.shape[1], w_p_tmp))
            else:
                if verbose:
                    print("\tcrop_preview is disabled")
        else:
            img_resized_final = img_resized
    else:
        img_resized_final = img_cropped


    if preview_options['geometry']['final_preview']:
        if verbose:
            print("\tshow the final image: add padding")
        # Add padding to the cropped&resized image
        pad_left = int(((w_final - w_p_tmp) / 2) + 0.5)
        pad_right = w_final - (w_p_tmp + pad_left)
        # print("\t-> pad=%d,%d" % (pad_left, pad_right))

        img_finalized = cv2.copyMakeBorder(img_resized_final, 0, 0, pad_left, pad_right,
            cv2.BORDER_CONSTANT, value=[0, 0, 0])

        # print("\t-> final: ", img_finalized.shape)
        # print("generate_single_image: %dms" % (int(1000 * (time.time() - now))))
        return (frame['index'], img_finalized)


    if img_resized is not None:
        # print("generate_single_image: %dms" % (int(1000 * (time.time() - now))))
        return (frame['index'], img_resized)
    else:
        # print("generate_single_image: %dms" % (int(1000 * (time.time() - now))))
        if img_resized_final.shape[0] == 576:
            img_resized_final_2 = cv2.resize(img_cropped, (img_resized_final.shape[1] * 2, img_resized_final.shape[0]*2), interpolation=cv2.INTER_LANCZOS4)
        else:
            img_resized_final_2 = img_resized_final
        return (frame['index'], img_resized_final_2)

