# -*- coding: utf-8 -*-

import sys
sys.path.append('../scripts')

import time
import os
import gc
import os.path
from pprint import pprint
from logger import log
from copy import deepcopy
import cv2
import numpy as np

from PySide6.QtCore import (
    QObject,
    Signal,
)

from common.preferences import Preferences
from models.model_database import Model_database
from models.model_common import Model_common

from images.filtering import filter_rgb

from utils.common import (
    K_GENERIQUES,
    K_NON_GENERIQUE_PARTS,
    get_frame_no_from_filepath,
    get_k_part_from_frame_no,
    get_shot_from_frame_no_new,
)
from utils.get_filters import FILTER_BASE_NO
from utils.get_framelist import get_framelist, get_framelist_2
from utils.consolidate import consolidate_shot

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

    WIDGET_LIST = [
        'controls',
        'replace',
        'geometry',
        'curves',
        'selection'
    ]

    SELECTABLE_WIDGET_LIST = [
        'curves',
        'replace',
        'geometry',
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
        for step in ['bgd', 'stitching']:
            self.step_labels.remove(step)



    def set_view(self, view):
        self.view = view

        self.view.widget_selection.signal_ep_or_part_selection_changed[dict].connect(self.ep_or_part_selection_changed)
        self.view.widget_selection.signal_selected_shots_changed[dict].connect(self.event_selected_shots_changed)

        self.view.widget_geometry.signal_save.connect(self.event_save_geometry_requested)
        self.view.widget_geometry.signal_discard.connect(self.event_geometry_discard_requested)
        self.view.widget_geometry.signal_geometry_modified[dict].connect(self.event_geometry_modified)

        self.view.widget_replace.signal_save.connect(self.event_save_replace_requested)
        self.view.widget_replace.signal_discard.connect(self.event_replace_discard_requested)
        self.view.widget_replace.signal_replace_modified[dict].connect(self.event_frame_replaced)

        self.view.widget_curves.widget_rgb_graph.signal_graph_modified[dict].connect(self.event_rgb_graph_modified)
        self.view.widget_curves.widget_curves_selection.signal_curves_selection_changed[str].connect(self.event_curves_selection_changed)
        self.view.widget_curves.signal_save_curves_as[dict].connect(self.event_save_curves_as)
        self.view.widget_curves.signal_save.connect(self.event_save_curves_selection_requested)
        self.view.widget_curves.widget_curves_selection.signal_discard_curves[str].connect(self.event_discard_curves)


        self.view.signal_preview_options_changed[dict].connect(self.event_preview_options_changed)
        self.view.signal_save_and_close.connect(self.event_save_and_close_requested)

        # Force refresh of previe options
        self.view.event_preview_options_changed()

        p = self.preferences.get_preferences()
        k_ep = 'ep%02d' % (p['selection']['episode']) if p['selection']['episode'] != '' else ''
        self.ep_or_part_selection_changed({
            'k_ep': k_ep,
            'k_part': p['selection']['part'],
            'k_step': p['selection']['step'],
        })



    def ep_or_part_selection_changed(self, values:dict):
        """ Directory or step has been changed, update the database, list all images,
            list all shots
        """
        # print("----------------------- ep_or_part_selection_changed -------------------------")
        # pprint(values)
        k_ep = values['k_ep']
        k_part = values['k_part']
        k_step = 'deinterlace' if values['k_step'] == '' else values['k_step']
        if (k_ep == '' and k_part == '') or (k_ep != '' and k_part == ''):
            return
        log.info("directory_changed: %s:%s" % (k_ep, k_part))

        self.model_database.consolidate_database(
            k_ep=k_ep,
            k_part=k_part,
            do_parse_replace=True,
            do_parse_geometry=True)

        # self.shots is a pointer to the shots for this episode/part
        db = self.model_database.database()

        p_missing_frame = os.path.join('icons', 'missing.png')

        # Remove all frames
        self.frames.clear()

        if k_part in ['g_debut', 'g_fin']:
            db_video = db[k_part]['common']['video']
        else:
            db_video = db[k_ep]['common']['video'][k_part]

        # will contains all shots for this part
        self.shots.clear()

        # Contains all path of frames for this part
        self.filepath.clear()

        shots = db_video['shots']
        for shot in shots:
            # Select the shot used for the generation
            if 'src' in shot.keys() and shot['src']['use']:
                k_ed_src = shot['src']['k_ed']
                k_ep_src = shot['src']['k_ep']
                k_part_src = get_k_part_from_frame_no(db, k_ed=k_ed_src, k_ep=k_ep_src, frame_no=shot['src']['start'])
                shot_src = deepcopy(get_shot_from_frame_no_new(db,
                    shot['src']['start'], k_ed=k_ed_src, k_ep=k_ep_src, k_part=k_part_src))

                if 'count' not in shot['src'].keys():
                    shot['src']['count'] = shot_src['count']
                if shot_src is None:
                    sys.exit("error: ep_or_part_selection_changed: shot src is None")
            else:
                k_ed_src = db[k_ep]['common']['video']['reference']['k_ed']
                k_ep_src = k_ep
                k_part_src = k_part
                shot_src = deepcopy(shot)

            print("\t\t%s: %s\t(%d)\t<- %s:%s:%s %d (%d)" % (
                "{:3d}".format(shot['no']),
                "{:5d}".format(shot['start']),
                shot['count'],
                k_ed_src,
                k_ep_src,
                k_part_src,
                shot_src['start'],
                shot_src['count']))

            shot_src.update({
                'k_ed': k_ed_src,
                'k_ep': k_ep_src,
                'k_part': k_part_src,
                'tasks': [values['k_step']],
            })
            if 'effects' in shot.keys():
                shot_src.update({'effects': shot['effects']})
            if 'dst' in shot.keys():
                shot_src['dst'] = shot['dst']
            if shot == shots[-1]:
                shot_src['last'] = True

            # Consolidation used fot the generation of frames for this shot
            consolidate_shot(db, shot=shot_src)

            # Patch the shot to create the concatenation file
            if 'src' in shot.keys() and shot['src']['use']:
                shot_properties_saved = ({'start': shot_src['start'], 'count': shot_src['count']})
                shot_src.update({
                    'start': shot['src']['start'],
                    'count': shot['src']['count']
                })
            shot_src['count'] = shot['count']

            if k_part in ['episode', 'reportage']:
                filepath_tmp = get_framelist(db, k_ep=k_ep, k_part=k_part, shot=shot_src)
            else:
                filepath_tmp = get_framelist_2(db, k_ep=k_ep, k_part=k_part, shot=shot_src)
            self.filepath.append(filepath_tmp)

            # Restore shot values
            if 'src' in shot.keys() and shot['src']['use']:
                shot_src.update(shot_properties_saved)

            # if 'src' in shot.keys() and shot['src']['use']:
            #     # restore src shot
            #     shot_src.update(shot_properties_saved)

            shot_no = shot['no']
            self.shots[shot_no] = shot_src
            current_shot = self.shots[shot_no]
            if 'src' in shot.keys():
                current_shot['src'] = shot['src']

            # patch count to include loop
            if ('effects' in current_shot.keys()
                and 'loop' in current_shot['effects'][0]):
                current_shot['count'] += current_shot['effects'][2]

            # Get curves for this shot
            curves = self.model_database.get_curves_selection(shot=current_shot)
            try: k_curves = curves['k_curves']
            except: k_curves =''
            if curves is None and current_shot['curves'] is not None:
                print("Error: curves [%s] is not found in the directory %s, correct this!" % (
                    current_shot['curves']['k_curves'],
                    self.model_database.get_curves_library_path()))
                current_shot['curves']['k_curves'] = "~" + current_shot['curves']['k_curves']

            # Update this shot for UI
            current_shot.update({
                # Uncomment if it simplifies following functions
                # 'k_ep_dst': k_ep,
                # 'k_part_dst': k_part,

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

            # Use the k_ed used for this shot: mandatory to get
            # the correct settings
            if k_part in K_GENERIQUES:
                k_ed_src = db[k_part]['common']['video']['reference']['k_ed']


            # Geometry for this shot:
            #   - part geometry
            #   - custom geometry: if g_asuivre/g_reportage, staabilize or stitched images
            shot_geometry = self.model_database.get_shot_geometry(
                k_ed=k_ed_src, k_ep=k_ep, shot=current_shot)

            # Create a list of frames for this shot
            self.frames[shot_no] = list()
            for p in filepath_tmp:
                frame_no = get_frame_no_from_filepath(p)

                if not os.path.exists(p):
                    image_filepath = p_missing_frame
                    current_shot['is_valid'] = False
                else:
                    image_filepath = p

                current_shot['frame_nos'].append(frame_no)
                self.frames[shot_no].append({
                    'k_ed': k_ed_src,
                    'k_ep': k_ep_src,
                    'k_part': k_part_src,
                    'shot_no': shot_no,
                    'frame_no': frame_no,

                    'filepath': image_filepath,
                    'replaced_by': self.model_database.get_replace_frame_no(shot=current_shot, frame_no=frame_no),
                    'curves': curves,
                    'geometry': shot_geometry,
                    'cache_fgd': None,
                    'cache': None,
                })

        # Create a dict to update the "browser" part of the editor widget
        if k_part in ['g_debut', 'g_fin']:
            k_ed = db[k_part]['common']['video']['reference']['k_ed']
        else:
            k_ed = db[k_ep]['common']['video']['reference']['k_ed']
        self.current_selection = {
            'k_ep': k_ep,
            'k_part': k_part,
            'k_step': k_step,
            'shots': self.shots,
            'reference': {
                'k_ed': k_ed,
                'k_ep': k_ep
            },
            'geometry': self.model_database.get_part_geometry(k_ed, k_part),
        }

        # Update selection with the part geometry
        if k_part in ['g_asuivre', 'g_reportage']:
            # Use the following part
            self.current_selection.update({
                'geometry': self.model_database.get_part_geometry(k_ed, k_part[2:]),
            })


        self.model_database.initialize_shots_per_curves(self.shots)
        self.signal_curves_library_modified.emit(self.model_database.get_library_curves())
        self.signal_shotlist_modified.emit(self.current_selection)



    def event_selected_shots_changed(self, selected_shots):
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
            'start': self.shots[selected_shots['shotlist'][0]]['start'],
            'frame_nos': frame_nos,
            'count': len(self.playlist_frames),
            'ticks': ticklist,
        })
        gc.collect()
        # pprint(self.framelist)

        self.refresh_replace_list()
        self.signal_ready_to_play.emit(self.playlist_properties)


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
        self.model_database.move_curves_selection_to_initial()

        self.event_save_geometry_requested()
        self.model_database.save_all_curves(k_ep_or_g=k_part if k_part in K_GENERIQUES else k_ep)
        self.signal_close.emit()



    def get_frame(self, frame_no):
        """ returns the replace frame unless there is no replacemed frame or
        the initial flag is set to True
        framelist contains all path for each frame of this playlist
        """
        # log.info("%s.get_frame: get_frame no. %d" % (__name__, frame_no))
        if not self.preview_options['replace']['is_enabled']:
            frame = self.playlist_frames[frame_no - self.playlist_properties['start']]
            # print("\tinitial")
            try: del frame['replaces']
            except: pass
        else:
            shot_no = self.get_shot_no_from_frame_no(frame_no)
            new_frame_no = self.model_database.get_replace_frame_no(self.shots[shot_no], frame_no)
            if new_frame_no == -1:
                frame = self.playlist_frames[frame_no - self.playlist_properties['start']]
                # print("\tnew_frame_no=-1")
                # print("\t%s" % (frame['filepath']))
                try: del frame['replaces']
                except: pass
            else:
                index = new_frame_no - self.playlist_properties['start']
                frame = self.playlist_frames[index]
                frame['replaces'] = frame_no

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
            # print("----> load RGB curves shot no. %d" % (frame['shot_no']) )
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
        # TODO: create a cache structure which manage the cache
        # and another thread to generate the next frames in background (when playing as a video)
        self.purge_current_frame_cache()

        # Set current frame
        self.current_frame = frame

        # Update geometry
        k_ed = self.current_selection['reference']['k_ed']
        frame['geometry'] = self.model_database.get_shot_geometry(k_ed=k_ed, k_ep=self.current_selection['k_ep'], shot=shot)
        pprint(frame['geometry'])


        # Generate the image for this frame
        options = self.preview_options
        if options is not None:
            index, img = generate_single_image(self.current_frame, preview_options=options)
            self.set_current_frame_cache(img=img)
        # else:
            # Cannot generate the image because no preview option is defined
            # The preview options will be updated by the window UI

        return self.current_frame


    def event_geometry_modified(self, modification:dict):
        """modification:
            - type
            - parameter
            - value
        """
        k_ed = self.current_selection['reference']['k_ed']
        k_ep = self.current_selection['k_ep']
        k_part = self.current_selection['k_part']
        shot_no = self.current_frame['shot_no']
        print("\nevent_geometry_modified for %s:%s:%s" % (k_ed, k_ep, k_part))
        pprint(modification)

        if (modification['type'] == 'part'
            or k_part in ['g_asuivre', 'g_reportage']):
            type = 'part'
            # Use a copy of parameters to not modify the initial values
            geometry = deepcopy(self.model_database.get_part_geometry(k_ed=k_ed, k_part=k_part))
        else:
            type = 'custom'
            geometry = deepcopy(self.model_database.get_custom_geometry(shot=self.shots[shot_no]))
        print("geometry")
        pprint(geometry)

        # Modify parameter
        value = modification['value']
        if 'crop' in modification['parameter']:
            c_t, c_b, c_l, c_r = geometry['crop']
            if modification['parameter'] == 'crop_top':
                geometry['crop'][0] = max(0, min(c_t + value, 400))

            elif modification['parameter'] == 'crop_bottom':
                geometry['crop'][1] = max(0, min(c_b + value, 400))

            elif modification['parameter'] == 'crop_left':
                geometry['crop'][2] = max(0, min(c_l + value, 400))

            elif modification['parameter'] == 'crop_right':
                geometry['crop'][3] = max(0, min(c_r + value, 400))

        if type == 'part':
            self.model_database.set_part_geometry(k_ed=k_ed, k_part=k_part, geometry=geometry)
        else:
            print("TODO: set custom geometry")
            self.model_database.set_custom_geometry(shot=self.shots[shot_no], geometry=geometry)

        # No need to flush cache as generation of a new image will be done (fast enough)

        self.signal_reload_frame.emit()


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


    def event_rgb_graph_modified(self, rgb_channels):
        shot_no = self.current_frame['shot_no']
        self.model_database.set_shot_rgb_channels(
            shot=self.shots[shot_no],
            rgb_channels=rgb_channels)
        self.signal_reload_frame.emit()


    def event_curves_selection_changed(self, k_curves:str):
        log.info("select the new curves for this shot [%s]" % (k_curves))
        shot_no = self.current_frame['shot_no']

        # Update the modifications structure to update the selection widget
        self.shots[shot_no]['modifications']['curves']['new'] = k_curves

        self.model_database.set_curves_selection(
            shot=self.shots[shot_no],
            k_curves=k_curves)
        curves = self.model_database.get_curves_selection(shot=self.shots[shot_no])

        # Refresh the list of shot for these curves
        shot_list = self.model_database.get_shots_per_curves(k_curves)
        self.signal_shot_per_curves_modified.emit(shot_list)

        self.signal_current_shot_modified.emit(self.shots[shot_no]['modifications'])
        self.signal_load_curves.emit(curves)
        self.signal_reload_frame.emit()


    def event_discard_curves(self, k_curves:str):
        self.model_database.discard_curves_modifications(k_curves)
        k_part = self.current_selection['k_part']
        k_ep = self.current_selection['k_ep']
        curves = self.model_database.get_curves(
            k_ep_or_g = k_part if k_part in K_GENERIQUES else k_ep,
            k_curves=k_curves)

        self.signal_curves_library_modified.emit(self.model_database.get_library_curves())
        self.signal_load_curves.emit(curves)
        self.signal_reload_frame.emit()


    def event_save_curves_as(self, curves):
        # Save the curves in the curves library
        if curves['k_curves'] == '':
            log.error("No name defined in the curves struct")
            return
        log.info("save curves as: %s" % (curves['k_curves']))
        k_part = self.current_selection['k_part']
        k_ep = self.current_selection['k_ep']
        self.model_database.save_curves_as(
            k_ep_or_g=k_part if k_part in K_GENERIQUES else k_ep,
            curves=curves)
        self.signal_curves_library_modified.emit(self.model_database.get_library_curves())


    def event_save_curves_selection_requested(self):
        # Save the curves selected for this shot
        k_ed = self.current_frame['k_ed']
        k_ep = self.current_frame['k_ep']
        k_part = self.current_frame['k_part']
        shot_no = self.current_frame['shot_no']
        print("event_save_curves_selection_requested %s:%s:%s:%d" % (k_ed, k_ep, k_part, shot_no))
        self.model_database.save_curves_selection_database(
            self.shots,
            k_ed=k_ed,
            k_ep=k_ep,
            k_part=k_part,
            shot_no=shot_no)
        self.model_database.move_curves_selection_to_initial()

        # Update the modifications structure to update the selection widget
        k_new_curves = self.shots[shot_no]['modifications']['curves']['new']
        self.shots[shot_no]['modifications']['curves'] = {
            'initial': k_new_curves,
            'new': None,
        }
        self.signal_current_shot_modified.emit(self.shots[shot_no]['modifications'])

        self.signal_is_saved.emit('curves_selection')


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
        frame_no = self.playlist_properties['start'] + index
        # print("\tsearch in %d -> %d" % (frame_no + 1, self.playlist_properties['start'] + self.playlist_properties['count']))
        for f_no in range(frame_no + 1, self.playlist_properties['start'] + self.playlist_properties['count']):
            shot_no = self.get_shot_no_from_frame_no(f_no)
            if self.model_database.get_replace_frame_no(shot_no, f_no) != -1:
                return f_no - self.playlist_properties['start']

        # print("\tsearch in %d -> %d" % (self.playlist_properties['start'], frame_no-1))
        for f_no in range(self.playlist_properties['start'], frame_no-1):
            shot_no = self.get_shot_no_from_frame_no(f_no)
            if self.model_database.get_replace_frame_no(shot_no, f_no) != -1:
                return f_no - self.playlist_properties['start']

        return -1


    def event_frame_replaced(self, replace:dict):
        action = replace['action']
        frame_no = replace['dst']
        shot_no = self.get_shot_no_from_frame_no(frame_no)
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
        self.model_database.move_replace_to_initial()
        self.signal_is_saved.emit('replace')



    def event_geometry_discard_requested(self):
        log.info("discard modifications requested")
        k_part = self.current_selection['k_part']
        db = self.model_database.database()
        if k_part in K_GENERIQUES:
            k_ed = db[k_part]['common']['video']['reference']['k_ed']
        else:
            k_ed =self.current_selection['k_ed']
        self.model_database.discard_part_geometry_modifications(k_ed=k_ed, k_part=k_part)
        self.signal_reload_frame.emit()


    def event_save_geometry_requested(self):
        k_part = self.current_selection['k_part']
        db = self.model_database.database()
        if k_part in K_GENERIQUES:
            k_ed = db[k_part]['common']['video']['reference']['k_ed']
            k_ep = db[k_part]['common']['video']['reference']['k_ep']
        else:
            k_ed =self.current_selection['k_ed']
            k_ep =self.current_selection['k_ep']
        self.model_database.save_geometry_database(k_ed=k_ed, k_ep=k_ep, k_part=k_part)
        self.model_database.move_part_geometry_to_initial()
        self.signal_is_saved.emit('geometry')



def get_dimensions_from_crop_values(width, height, crop):
    c_t, c_b, c_l, c_r = crop
    c_w = width - (c_l + c_r)
    c_h = height - (c_t + c_b)
    return [c_t, c_b, c_l, c_r, c_w, c_h]


def generate_single_image(frame:dict, preview_options:dict):
    print("generate_single_image")
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
    pprint(preview_options)

    # Calculate dimensions to crop the image
    c_t_p, c_b_p, c_l_p, c_r_p, c_w_p, c_h_p = get_dimensions_from_crop_values(h, w, frame['geometry']['part']['crop'])
    if ('custom' in frame['geometry'].keys()
        and frame['geometry']['custom'] is not None):
        # Use the customized geometry
        print("\t-> use the custom geometry")
        type = 'custom'
        c_t, c_b, c_l, c_r, c_w, c_h = get_dimensions_from_crop_values(h, w, frame['geometry']['custom']['crop'])
    else:
        # Use the part geometry
        print("\t-> use the part geometry")
        type = 'part'
        c_t, c_b, c_l, c_r, c_w, c_h = (c_t_p, c_b_p, c_l_p, c_r_p, c_w_p, c_h_p)
    w_final, h_final = (1440, 1080)

    # Preview options
    options = preview_options['geometry'][type]


    # Apply rgb curves
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

    # Part
    if options['crop_edition'] and not options['crop_preview']:
        # Add a rect
        # print("\t-> Use the original image")
        img = img_rgb

    elif options['crop_preview']:
        # Crop and no rect
        # print("\t-> Crop the image")
        img = np.ascontiguousarray(img_rgb[c_t:h-c_b, c_l:w-c_r], dtype=np.uint8)
        # print("\t-> cropped: ", img.shape)

    else:
        if options['resize_preview']:
            sys.exit("resize not possible because no crop")
        # Use original image
        # print("\t-> Use the original image")
        img = img_rgb


    img_resized = None
    if options['resize_preview']:
        # TODO: Modify in case of customized values
        # Only width will be used.

        # calculate new width and new height
        w_tmp = int((c_w * h_final) / float(c_h))

        # width and height of the resized cropped image for the part
        w_p_tmp = int((c_w_p * h_final) / float(c_h_p))

        if not options['crop_preview']:
            # Resize the orignal image and add rect
            w_tmp = int((w * h_final) / float(c_h))
            w_p_tmp = int((w * h_final) / float(c_h_p))
            h_tmp = int((h * h_final) / float(c_h))
            img_resized = cv2.resize(img, (w_tmp, h_tmp), interpolation=cv2.INTER_LANCZOS4)
            # print("\t-> resized original image: %dx%d, calculated:%dx%d" % (img_resized.shape[1], img_resized.shape[0], w_tmp, h_tmp ))
        else:
            # Resize the cropped image
            img_resized = cv2.resize(img, (w_tmp, h_final), interpolation=cv2.INTER_LANCZOS4)
            # print("\t-> resized cropped image: %dx%d, calculated:%dx%d" % (img_resized.shape[1], img_resized.shape[0], w_tmp, h_final ))

        # TODO: crop the resized image if custom resize and width != w_p_tmp
        if w_tmp != w_p_tmp:
            print("crop the customized image")


    if preview_options['geometry']['final_preview']:
        # Add padding to the cropped&resized image
        pad_left = int((w_final - w_tmp) / 2)
        pad_right = w_final - (w_tmp + pad_left)
        # print("\t-> pad=%d,%d" % (pad_left, pad_right))

        img_finalized = cv2.copyMakeBorder(img_resized, 0, 0, pad_left, pad_right,
            cv2.BORDER_CONSTANT, value=[0, 0, 0])

        # print("\t-> final: ", img_finalized.shape)
        # print("generate_single_image: %dms" % (int(1000 * (time.time() - now))))

        return (frame['index'], img_finalized)

    if img_resized is not None:
        # print("generate_single_image: %dms" % (int(1000 * (time.time() - now))))
        return (frame['index'], img_resized)
    else:
        # print("generate_single_image: %dms" % (int(1000 * (time.time() - now))))
        return (frame['index'], img)

