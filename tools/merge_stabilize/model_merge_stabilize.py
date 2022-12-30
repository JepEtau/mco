# -*- coding: utf-8 -*-
import sys
sys.path.append('../scripts')

from functools import partial
import time

import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

import cv2
from skimage.filters import unsharp_mask
from skimage.util import img_as_ubyte
from skimage.util import img_as_float
import os
import gc
import numpy as np
import os.path

from copy import deepcopy
from multiprocessing import *


from pprint import pprint
from logger import log

from PySide6.QtCore import (
    Signal,
)
from PySide6.QtWidgets import QApplication


PATH_CACHE = "../cache"

from images.filtering import filter_bgd_curves

from common.preferences import Preferences
from models.model_database import Model_database
from models.model_common import Model_common

from parsers.parser_stitching import (
    STITCHING_SHOT_PARAMETERS_DEFAULT,
    STICTHING_FGD_PAD,
    write_bgd_curves_to_database,
)

from parsers.parser_stabilize import STABILIZATION_SHOT_PARAMETERS_KEYS

from utils.common import (
    get_database_size,
    get_frame_no_from_filepath,
    get_k_part_from_frame_no,
    get_shot_from_frame_no_new,
    get_shot_no_from_frame_no,
    K_GENERIQUES,
)
from utils.get_filters import FILTER_BASE_NO
from utils.get_framelist import get_framelist, get_single_framelist
from utils.consolidate_shots import consolidate_shot


SHOT_MIN = 25
SHOT_MAX = 25

# add padding to the ref frame for calculation of other frames
#   top, bottom, left, right
PAD_stabilize_REF = [80, 40, 20, 20]


class Model_merge_stabilize(Model_common):
    signal_current_shot_modified = Signal(dict)
    signal_ready_to_play = Signal(dict)
    signal_reload_frame = Signal()
    signal_is_modified = Signal(dict)
    signal_cache_is_ready = Signal()
    signal_refresh_image = Signal()

    signal_load_bgd_curves = Signal(dict)
    signal_bgd_curves_library_modified = Signal(dict)

    signal_stitching_calculated = Signal()
    signal_stabilize_calculated = Signal()

    signal_is_saved = Signal(str)

    WIDGET_LIST = [
        'controls',
        'bgd_curves',
        'stitching',
        'stabilize',
        'geometry',
        'selection'
    ]

    SELECTABLE_WIDGET_LIST = [
        'bgd_curves',
        'stitching',
        'stabilize',
        'geometry'
    ]

    def __init__(self):
        super(Model_merge_stabilize, self).__init__()
        self.view = None

        # Load saved preferences
        self.preferences = Preferences(
            tool='merge_stabilize',
            widget_list=self.WIDGET_LIST)

        # Variables
        self.model_database = Model_database()

        self.shots_fgd = dict()
        self.frames_fgd = dict()

        self.filepath_fgd = list()
        self.filepath_bgd = list()

        for step in ['deinterlace', 'pre_upscale', 'upscale', 'stitching', 'sharpen', 'rgb', 'geometry']:
            self.step_labels.remove(step)


    def set_view(self, view):
        self.view = view

        self.view.widget_selection.signal_selection_changed[dict].connect(self.selection_changed)
        self.view.widget_selection.signal_selected_shots_changed[dict].connect(self.event_selected_shots_changed)

        self.view.signal_generate_cache[list].connect(self.event_prepare_frames_for_preview)

        self.view.widget_stitching.signal_calculation_requested[dict].connect(self.event_stitching_do_calculate)

        self.view.widget_bgd_curves.widget_hist_curves.signal_curves_modified[dict].connect(self.event_bgd_curves_modified)

        # self.view.widget_bgd_curves.signal_curves_modified[dict].connect(self.event_bgd_curves_modified)
        self.view.widget_bgd_curves.signal_save_curves_as[dict].connect(self.event_save_bgd_curves_as)
        self.view.widget_bgd_curves.signal_discard.connect(self.event_discard_bgd_curves_modifications)

        self.view.widget_bgd_curves.signal_remove_selection.connect(self.event_remove_bgd_curves_selection)
        self.view.widget_bgd_curves.signal_selection_changed[str].connect(self.event_bgd_curves_selected)
        self.view.widget_bgd_curves.signal_reset_selection.connect(self.event_reset_bgd_curves_selection)
        self.view.widget_bgd_curves.signal_save_selection.connect(partial(self.event_save_modifications, 'bgd_curves'))

        self.view.widget_stabilize.signal_calculation_requested[dict].connect(self.event_stabilize_do_calculate)
        self.view.widget_stabilize.signal_enabled_modified[bool].connect(self.event_stabilize_set_enabled)
        self.view.widget_stabilize.signal_save.connect(partial(self.event_save_modifications, 'stabilize'))

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
            'shot_min': 0,
            'shot_max': 999999,
        })



    def selection_changed(self, values:dict):
        """ Directory or step has been changed, update the database, list all images,
            list all shots
        """
        print("----------------------- selection_changed -------------------------")
        pprint(values)
        k_ep_selected = values['k_ep']
        k_part_selected = values['k_part']
        k_step = 'deinterlace' if values['k_step'] == '' else values['k_step']
        if ((k_ep_selected == '' and k_part_selected in K_GENERIQUES)
            or (k_ep_selected != '' and k_part_selected != 'episode')):
            return
        log.info("directory_changed: %s:%s" % (k_ep_selected, k_part_selected))

        shot_min = 0 if 'shot_min' not in values.keys() else values['shot_min']
        shot_max = 999999 if 'shot_max' not in values.keys() else values['shot_max']
        # shot_min = SHOT_MIN
        # shot_max = SHOT_MAX

        self.model_database.consolidate_database(
            k_ep=k_ep_selected,
            k_part=k_part_selected,
            do_parse_curves=True,
            do_parse_replace=False,
            do_parse_geometry=False,
            do_parse_stitching=True)

        # self.shots is a pointer to the shots for this episode/part
        db = self.model_database.database()

        # Remove all frames
        self.frames.clear()

        # will contains all shots for this part
        self.shots_fgd.clear()

        # Contains all path of frames for this part
        self.filepath_fgd.clear()
        self.filepath_bgd.clear()

        # Get video db
        db_video = db[k_ep_selected]['target']['video'][k_part_selected]

        # Walk through shots
        shots = db_video['shots']
        for shot_fgd in shots:
            if not (shot_min <= shot_fgd['no'] <= shot_max):
                print("discard shot no. %d" % (shot_fgd['no']))
                continue

            # For debug only
            print("\t\t%s: %s\t(%d)\t<- %s:%s:%s   %d (%d)" % (
                "{:3d}".format(shot_fgd['no']),
                "{:5d}".format(shot_fgd['start']),
                shot_fgd['dst']['count'],
                shot_fgd['k_ed'],
                shot_fgd['k_ep'],
                shot_fgd['k_part'],
                shot_fgd['start'],
                shot_fgd['count']),
                flush=True)

            # Consolidate shot
            shot_fgd['tasks'] = [values['k_step']]
            consolidate_shot(db, shot=shot_fgd)

            shot_no = shot_fgd['no']
            self.shots_fgd[shot_no] = shot_fgd

            # print("---------------------")
            # pprint(self.filepath_fgd)
            # print("---------------------")
            # pprint(self.filepath_bgd)
            # print("---------------------")
            # sys.exit()

            shot_fgd.update({
                'is_valid': True,

                # Frame no. ... for what?
                'frame_nos': list(),

                # Structure to display the modifications in the selection widget
                'modifications': {
                    # 'curves' : {
                    #     'initial': k_curves,
                    #     'new': None,
                    # },
                },
            })

        # Create a dict to update the "browser" part of the editor widget
        if k_part_selected in K_GENERIQUES:
            k_ed_selected = db[k_part_selected]['target']['video']['src']['k_ed']
            print("Error: cannot select %s:%s:%s" % (k_ed_selected, k_ep_selected, k_part_selected))
            return
        else:
            k_ed_selected = db[k_ep_selected]['target']['video']['src']['k_ed']
        self.current_selection = {
            'k_ed': k_ed_selected,
            'k_ep': k_ep_selected,
            'k_part': k_part_selected,
            'k_step': k_step,
            'shots': self.shots_fgd,
            'geometry': None,
        }

        # Use the selected ed:ep:part
        # self.current_selection.update({
        #     'geometry': self.model_database.get_part_geometry(
        #         k_ed=k_ed_selected,
        #         k_ep=k_ep_selected,
        #         k_part=k_part_selected),
        # })


        # self.model_database.initialize_shots_per_curves(self.shots)
        # self.signal_curves_library_modified.emit(self.model_database.get_library_curves())
        # reenable this
        # self.signal_bgd_curves_library_modified.emit(self.model_database.get_bgd_curves_names())
        self.signal_shotlist_modified.emit(self.current_selection)



    def event_selected_shots_changed(self, selected_shots):
        print("event_selected_shots_changed")
        if len(selected_shots['shotlist']) == 0:
            return

        k_ep_selected = self.current_selection['k_ep']
        k_part_selected = self.current_selection['k_part']
        p_missing_frame = os.path.join('icons', 'missing.png')

        # for shot_no in self.shots_fgd.keys():
        #     if shot_no not in selected_shots['shotlist']:
        #         del self.shots_fgd
        db = self.model_database.database()

        for shot_no in selected_shots['shotlist']:
            # self.shots_fgd[shot_no] = shot_fgd
            shot_fgd = self.shots_fgd[shot_no]

            # For debug only
            print("\t\t%s: %s\t(%d)\t<- %s:%s:%s   %d (%d)" % (
                "{:3d}".format(shot_fgd['no']),
                "{:5d}".format(shot_fgd['start']),
                shot_fgd['dst']['count'],
                shot_fgd['k_ed'],
                shot_fgd['k_ep'],
                shot_fgd['k_part'],
                shot_fgd['start'],
                shot_fgd['count']),
                flush=True)

            # Copy shot and consolidate it
            shot_bgd = dict()
            for k, v in shot_fgd.items():
                if k not in ['stabilization', 'filters']:
                    shot_bgd.update({k: v})
                else:
                    shot_bgd.update({k: None})
            shot_bgd.update({
                'filters': 'default',
                'layer': 'bgd',
                'tasks': [self.current_selection['k_step']],
            })
            consolidate_shot(db, shot=shot_bgd)
            # pprint(shot_bgd)
            # print("")
            # sys.exit("event_selected_shots_changed")

            # Get a list of path for each frame  for this shot: episode only!
            if k_part_selected == 'episode':
                filepath_fgd_tmp = get_framelist(db, k_ep=k_ep_selected, k_part=k_part_selected, shot=shot_fgd)
                filepath_bgd_tmp = get_framelist(db, k_ep=k_ep_selected, k_part=k_part_selected, shot=shot_bgd)
            else:
                print("error: cannot select %s:%s" % (k_ep_selected, k_part_selected))
                return
            self.filepath_fgd += filepath_fgd_tmp
            self.filepath_bgd += filepath_bgd_tmp

            # if 'stitching' in shot_src.keys():
            #     k_curves = shot_src['stitching']['curves']['k_curves']
            #     # if k_curves != ''
            #     shot_src['stitching']['curves'] = self.model_database.get_shot_bgd_curves(shot_no)
            #     del shot_src['stitching']['frames']
            #     shot_src['stitching']['geometry'] = self.model_database.get_shot_stitching_fgd_crop(shot_no)

            # Get values for this shot
            bgd_curves = self.model_database.get_shot_bgd_curves_selection(db=db, shot=shot_bgd)
            stitching_fgd_crop = self.model_database.get_fgd_crop(shot=shot_fgd)
            # st_geometry = self.model_database.get_shot_st_geometry(shot_no)
            # part_geometry = self.model_database.get_part_geometry(k_ed_src, k_part)
            st_geometry = None
            shot_geometry = None

            self.frames_fgd[shot_no] = list()
            for p_fgd, p_bgd in zip(self.filepath_fgd, self.filepath_bgd):
                frame_no = get_frame_no_from_filepath(p_fgd)
                # print("process frame: %d" % (frame_no), flush=True)

                # image_bgd_filepath = p.replace(
                #     "__%s__" % (shot_src['layers']['fgd']),
                #     "__%s__" % (shot_src['layers']['bgd']))

                # shot_src['layer'] = 'bgd'
                # consolidate_shot(db, shot=shot_src)
                # filter_id = get_filter_id(db, shot, shot['tasks'][-1])
                # print(filter_id)

                if not os.path.exists(p_fgd):
                    fgd_image_filepath = p_missing_frame
                    shot_fgd['is_valid'] = False
                else:
                    fgd_image_filepath = p_fgd

                if not os.path.exists(p_bgd):
                    print("missing file: %s" % (p_bgd))
                    bgd_image_filepath = p_missing_frame
                    shot_bgd['is_valid'] = False
                else:
                    bgd_image_filepath = p_bgd

                shot_fgd['frame_nos'].append(frame_no)
                self.frames_fgd[shot_no].append({
                    'dst': shot_fgd['dst'],
                    'src': shot_fgd['src'],
                    'k_ed': shot_fgd['k_ed'],
                    'k_ep': shot_fgd['k_ep'],
                    'k_part': shot_fgd['k_part'],
                    'shot_no': shot_no,
                    'frame_no': frame_no,

                    'filepath': fgd_image_filepath,
                    'filepath_bgd': bgd_image_filepath,
                    # 'dimensions': shot['dimensions'],
                    # 'replaced_by': self.model_database.get_replace_frame_no(shot=shot_fgd, frame_no=frame_no),
                    # 'curves': shot_fgd['curves'],
                    'geometry': shot_geometry,
                    'stitching': {
                        'parameters': self.model_database.get_frame_stitching_parameters(shot_no, frame_no),
                        'm': self.model_database.get_image_stitching_matrix(shot_fgd, frame_no),
                        'fgd_crop': stitching_fgd_crop,
                        'curves': bgd_curves,
                    },
                    'stabilize': {
                        'delta_interval': self.model_database.get_shot_stabilize_parameters(shot_no, frame_no)['delta_interval'],
                        'dx_dy': self.model_database.get_frame_stabilize(shot_no, frame_no),
                    },
                    'st_geometry': st_geometry,
                    'cache': None,
                    'cache_fgd': None,
                    'cache_bgd': None,
                    'cache_bgd_tmp': None,
                })
                # pprint(self.frames_fgd[shot_no])
                # sys.exit("event_selected_shots_changed")

        now = time.time()
        frame_nos = list()

        ticklist = [0]
        self.playlist_frames.clear()
        index = 0
        for shot_no in selected_shots['shotlist']:
            shot = self.frames_fgd[shot_no]
            for frame in shot:
                frame['index'] = index
                index += 1
                self.playlist_frames.append(frame)
                frame_nos.append(frame['frame_no'])
            ticklist.append(ticklist[-1] + len(self.frames_fgd[shot_no]))

        # Opend fgd images
        with ThreadPoolExecutor(max_workers=8) as executor:
            future_load_image = {executor.submit(load_image, frame, False): frame for frame in self.playlist_frames}
            for future in concurrent.futures.as_completed(future_load_image):
                # frame_no, img = future_load_image[future]
                index, img = future.result()
                self.playlist_frames[index]['cache_fgd'] = img

        # Opend bgd images
        with ThreadPoolExecutor(max_workers=8) as executor:
            future_load_image = {executor.submit(load_image, frame, True): frame for frame in self.playlist_frames}
            for future in concurrent.futures.as_completed(future_load_image):
                # frame_no, img = future_load_image[future]
                index, img = future.result()
                self.playlist_frames[index]['cache_bgd'] = img


        # Calculate initial image
        if self.get_preview_options() == 'stitching':
            playlist = [self.playlist_frames[0]]

            if False:
                # Calculate Stiching values for each frame
                now = time.time()
                with ThreadPoolExecutor(max_workers=4) as executor:
                    future_stitching_image = {
                        executor.submit(calculate_stitching_values, frame): frame for frame in playlist
                    }
                    for future in concurrent.futures.as_completed(future_stitching_image):
                        # frame_no, img = future_stitching_image[future]
                        index, m = future.result()
                        frame = self.playlist_frames[index]
                        self.model_database.set_frame_stitching_transformation(
                            shot_no=frame['shot_no'],
                            frame_no=frame['frame_no'],
                            transformation=m)

                        frame['stitching']['m'] = self.model_database.get_frame_stitching_transformation(frame['shot_no'], frame['frame_no'])
                        # pprint(frame['stitching'])

                self.model_database.set_shot_stitching_parameters(frame['shot_no'], {'is_enabled': True})
                print("calculate_stitching_values: %.3f" % (time.time() - now))

        self.playlist_properties.update({
            'start': self.shots_fgd[selected_shots['shotlist'][0]]['start'],
            'frame_nos': frame_nos,
            'count': len(self.playlist_frames),
            'ticks': ticklist,
        })

        print("event_selected_shots_changed: %f ms" % ((time.time() - now) * 1000))
        gc.collect()

        self.signal_ready_to_play.emit(self.playlist_properties)


    def get_modified_db(self):
        return self.model_database.get_modified_db()


    def event_save_and_close_requested(self):
        k_ep = self.current_selection['k_ep']
        k_part = self.current_selection['k_part']

        # TODO: save all parameters from widgets

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
            try: del frame['replace']
            except: pass
        else:
            shot_no = self.get_shot_no_from_frame_no(frame_no)
            new_frame_no = self.model_database.get_replace_frame_no(self.shots_fgd[shot_no], frame_no)
            if new_frame_no == -1:
                frame = self.playlist_frames[frame_no - self.playlist_properties['start']]
                # print("\tnew_frame_no=-1")
                # print("\t%s" % (frame['filepath']))
                try: del frame['replace']
                except: pass
            else:
                index = new_frame_no - self.playlist_properties['start']
                frame = self.playlist_frames[index]
                frame['replace'] = frame_no

        # Shot has changed: update UI with parameters for this shot (curves, crop, resize)
        if self.current_frame is None or frame['shot_no'] != self.current_frame['shot_no']:
            frame['reload_parameters'] = True
        else:
            frame['reload_parameters'] = False

        # current shot
        shot = self.shots_fgd[frame['shot_no']]

        # Stitching

        # bgd curves
        frame['stitching']['curves'] = self.model_database.get_shot_bgd_curves_selection(
            db=self.model_database.database(), shot=shot)
        if self.current_frame is None or frame['shot_no'] != self.current_frame['shot_no']:
            try:
                self.signal_load_bgd_curves.emit(frame['curves'])
            except:
                self.signal_load_bgd_curves.emit(None)
        elif self.current_frame is None:
            self.signal_load_bgd_curves.emit(None)


        # Purge image from the previous frame
        # this is necessary to limit the memory consumption
        # TODO: create a cache structure which manage the cache
        # and another thread to generate the next frames in background (when playing as a video)
        self.purge_current_frame_cache()

        # Set current frame
        self.current_frame = frame

        # Stabilization

        # Update curves
        # frame['curves'] = self.model_database.get_shot_curves_selection(
        #     db=self.model_database.database(), shot=shot)


        # Purge image from the previous frame
        # self.purge_current_frame_cache()


        # Update geometry
        if False:
            # TODO: reenable this or use the video editor?
            if frame['k_part'] in ['g_debut', 'g_fin']:
                frame['geometry'] = self.model_database.get_shot_geometry(
                    k_ed=frame['k_ed'],
                    k_ep=frame['k_ep'],
                    k_part=frame['k_part'],
                    shot=shot)
            else:
                frame['geometry'] = self.model_database.get_shot_geometry(
                    k_ed=self.current_frame['k_ed'],
                    k_ep=self.current_frame['k_ep'],
                    k_part=self.current_frame['k_part'],
                    shot=shot)

        # Generate the image for this frame
        options = self.preview_options
        if options is not None:
            index, img = generate_single_image(self.current_frame, preview_options=options)
            self.set_current_frame_cache(img=img)
        # else:
            # Cannot generate the image because no preview option is defined
            # The preview options will be updated by the window UI

        return self.current_frame





    def get_current_shot_parameters(self, k_details_list:list):
        if self.current_frame is None:
            return None

        shot_no = self.current_frame['shot_no']
        shot_dict = dict()
        if 'stitching' in k_details_list:
            shot_dict.update({
                'stitching': {
                    'fgd_crop': self.model_database.get_shot_stitching_fgd_crop(shot_no=shot_no),
                    'curves': None,
                    'parameters':self.model_database.get_shot_stitching_parameters(shot_no=shot_no),
                }
            })

            bgd_curves = self.model_database.get_shot_bgd_curves(shot_no=shot_no)
            if bgd_curves is not None:
                shot_dict['stitching'].update({
                    'curves': {
                        'k_curves': bgd_curves['k_curves'],
                        'points': bgd_curves['points'],
                    },
                })

        if 'stabilize' in k_details_list:
            shot_dict.update({
                'stabilize': {
                    'parameters': self.model_database.get_shot_stabilize_parameters(shot_no=shot_no),
                    'shot_start': self.shots_fgd[shot_no]['start'],
                    'shot_count': self.shots_fgd[shot_no]['count'],
                }
            })

        return shot_dict


    def event_geometry_modified(self, modification:dict):
        """modification:
            - side
            - value
        """
        k_ed = self.current_selection['reference']['k_ed']
        k_part = self.current_selection['k_part']

        coordinates = self.model_database.get_crop_coordinates(k_ed=k_ed, k_part=k_part)
        db = self.model_database.database()
        if coordinates is None:
            coordinates = [0, 0,
                db['common']['dimensions']['upscale']['w'],
                db['common']['dimensions']['upscale']['h']]

        value = modification['value']
        if modification['side'] == 'top':
            coordinates[1] += value
            if value < 0:
                coordinates[1] = max(0, coordinates[1])
            else:
                coordinates[1] = min(coordinates[1], int(db['common']['dimensions']['upscale']['h']/2))
        elif modification['side'] == 'bottom':
            coordinates[3] += value
            if value < 0:
                coordinates[3] = max(coordinates[3], int(db['common']['dimensions']['upscale']['h']/2))
            else:
                coordinates[3] = min(coordinates[3], db['common']['dimensions']['upscale']['h'])

        if modification['side'] == 'left':
            coordinates[0] += value
            if value < 0:
                coordinates[0] = max(0, coordinates[0])
            else:
                coordinates[0] = min(coordinates[0], int(db['common']['dimensions']['upscale']['w']/2))

        elif modification['side'] == 'right':
            coordinates[2] += value
            if value < 0:
                coordinates[2] = max(coordinates[2], int(db['common']['dimensions']['upscale']['w']/2))
            else:
                coordinates[2] = min(coordinates[2], db['common']['dimensions']['upscale']['w'])
        self.model_database.set_crop_coordinates(k_ed, k_part, coordinates)

        # Update frames
        for k_shot_no in self.frames.keys():
            for f in self.frames_fgd[k_shot_no]:
                f['geometry'] = coordinates

        self.signal_is_modified.emit({'status': True, 'shot_no': None, 'crop': coordinates})
        self.signal_reload_frame.emit()


    def event_geometry_discard_requested(self):
        log.info("TODO")
        print("TODO")


    def event_save_geometry_requested(self):
        log.info("TODO")
        print("TODO")



    def event_save_modifications(self, k_settings=''):
        """k_settings:
            - stabilization
            - all
        """
        k_ep = self.current_selection['k_ep']
        k_part = self.current_selection['k_part']

        if k_settings == 'stabilize':
            log.info("save stabilization changes")
            shot_no = self.current_frame['shot_no']
            shot = self.get_shot(shot_no=shot_no)
            is_saved = self.model_database.save_stabilize_database(k_ep=k_ep, k_part=k_part,
                shots={shot_no: shot})
            if is_saved:
                self.signal_is_saved.emit([k_settings])

        elif k_settings == 'bgd_curves':
            log.info("save stitching curves changes")
            shot_no = self.current_frame['shot_no']
            shot = self.get_shot(shot_no=shot_no)

            # Save the selected curves selection
            save_shot_bgd_curves(db=self.model_database.database(), k_ep=k_ep, k_part=k_part,
                shots={shot_no: shot},
                bgd_curves=self.model_database.get_modified_shot_bgd_curves())

            # Set as initial and remove from modified: to avoid parsing the stitching file
            self.model_database.set_shot_bgd_curves_as_initial(shot_no)

            self.signal_is_saved.emit([k_settings])

        elif k_settings == 'all':
            log.info("TODO: save all?")


    def event_bgd_curves_modified(self, rgb_channels):
        shot_no = self.current_frame['shot_no']
        print("-> event_bgd_curves_modified, shot no. %d" % (shot_no))
        self.model_database.set_shot_bgd_channels(
            shot=self.shots_fgd[shot_no],
            rgb_channels=rgb_channels)
        self.signal_reload_frame.emit()


    def event_bgd_curves_selection_changed(self, k_curves:str):
        print("event_curves_selection_changed: todo")


    def event_save_shot_bgd_curves(self):
        print("todo: event_save_shot_bgd_curves")


    def event_bgd_curves_selected(self, k_curves):
        log.info("select k_curves: %s" % (k_curves))
        shot_no = self.current_frame['shot_no']

        # for f in self.frames_fgd[shot_no]:
        #     print(f['stitching'])

        self.model_database.select_shot_bgd_curves(shot_no=shot_no, k_curves=k_curves)

        # Update each frames of the shot
        shot_curves = self.model_database.get_shot_bgd_curves(shot_no)
        for f in self.frames_fgd[shot_no]:
            if ('cache' in f.keys()
                and f['cache'] is not None):
                del f['cache']
                f['cache'] = None
            f['stitching']['curves'] = shot_curves

        # for f in self.frames_fgd[shot_no]:
        #     print(f['stitching']['curves']['k_curves'])

        self.signal_load_bgd_curves.emit(shot_curves)
        self.signal_refresh_image.emit()


    def event_discard_bgd_curves_modifications(self, k_curves=''):
        self.model_database.discard_bgd_curves_modifications(k_curves)
        k_part = self.current_selection['k_part']
        k_ep = self.current_selection['k_ep']

        # Get the initial curves
        curves = self.model_database.get_bgd_curves(self.model_database.database(),
            k_ep_or_g = k_part if k_part in K_GENERIQUES else k_ep,
            k_curves=k_curves)

        # Send the list of curves
        self.signal_bgd_curves_library_modified.emit(self.model_database.get_bgd_library_curves())

        # Reload curves
        self.signal_load_bgd_curves.emit(curves)
        self.signal_reload_frame.emit()


        # Remove modifications of the selected curves
        log.info("discard modifications %s" % (k_curves))

        self.model_database.discard_bgd_curves_modifications(k_curves)

        # Update the curves list
        self.signal_bgd_curves_library_modified.emit(
            self.model_database.get_bgd_curves_names())

        # Get shot_curves for this shot
        shot_no = self.current_frame['shot_no']
        shot_curves = self.model_database.get_shot_bgd_curves(shot_no)
        self.signal_load_bgd_curves.emit(shot_curves)

        self.signal_refresh_image.emit()


    def event_remove_bgd_curves_selection(self):
        log.info("remove cruves for this shot")
        shot_no = self.current_frame['shot_no']
        self.model_database.remove_shot_bgd_curves(shot_no=shot_no)

        # Update each frames of the shot
        for f in self.frames_fgd[shot_no]:
            if ('cache' in f.keys()
                and f['cache'] is not None):
                del f['cache']
                f['cache'] = None
            f['stitching']['curves'] = None

        self.signal_load_bgd_curves.emit(None)
        self.signal_refresh_image.emit()



    def reset_to_initial_bgd_curves(self):
        print("TODO: reset to initial stitching curves")
        # 2 cases:


    def event_reset_bgd_curves_selection(self):
        log.info("reset selection to initial")
        shot_no = self.current_frame['shot_no']
        self.model_database.reset_shot_bgd_curves_selection(shot_no=shot_no)

        # Get shot_curves for this shot
        shot_curves = self.model_database.get_shot_bgd_curves(shot_no)

        # Reset this curve if modified
        self.model_database.discard_bgd_curves_modifications(k_curves=shot_curves['k_curves'])
        shot_curves = self.model_database.get_shot_bgd_curves(shot_no)

        # Update each frames of the shot
        for f in self.frames_fgd[shot_no]:
            if ('cache' in f.keys()
                and f['cache'] is not None):
                del f['cache']
                f['cache'] = None
            f['stitching']['curves'] = shot_curves

        # Update the curves list
        self.signal_bgd_curves_library_modified.emit(
            self.model_database.get_bgd_curves_names())
        self.signal_load_bgd_curves.emit(shot_curves)
        self.signal_refresh_image.emit()


    def event_save_bgd_curves_as(self, curves:dict):
        log.info("save stitching curves as %s" % (curves['k_curves']))
        k_ep = self.current_selection['k_ep']
        shot_no = self.current_frame['shot_no']

        # Write the new curves to the file
        write_bgd_curves_to_database(db=self.model_database.database(), k_ep=k_ep, curves=curves)

        # Discard the current modified curves and reparse the database
        current_curves = self.model_database.get_shot_bgd_curves(shot_no=shot_no)
        self.model_database.discard_bgd_curves_modifications(current_curves['k_curves'])
        self.model_database.reload_bgd_curves_databse(k_ep=k_ep)

        # Update the curves list
        self.signal_bgd_curves_library_modified.emit(
            self.model_database.get_bgd_curves_names())

        # Set the new curves as selected
        self.model_database.select_shot_bgd_curves(shot_no=shot_no, k_curves=curves['k_curves'])
        shot_curves = self.model_database.get_shot_bgd_curves(shot_no)

        self.signal_load_bgd_curves.emit(shot_curves)
        self.signal_refresh_image.emit()


    def event_stitching_do_calculate(self, parameters):
        do_recalculate = False

        frame_no = self.current_frame['frame_no']
        shot_no = self.get_shot_no_from_frame_no(frame_no=frame_no)

        current_parameters = self.model_database.get_frame_stitching_parameters(shot_no=shot_no, frame_no=frame_no)
        pprint(current_parameters)
        pprint(parameters)
        # current_parameters = self.model_database.get_shot_stitching_parameters(shot_no)

        for k in STITCHING_SHOT_PARAMETERS_DEFAULT:
            # Do not verify these parameters
            if k in ['is_default', 'is_ready']:
                continue
            # set flag if at least one parameter differs
            if parameters[k] != current_parameters[k]:
                do_recalculate = True
                break

        if do_recalculate:
            print("Recalculate")
            parameters['is_processed'] = False
            if current_parameters['is_shot'] and not parameters['is_shot']:
                # Remove the customized parameters as it changed from 'frame' to 'shot
                self.model_database.remove_frame_stitching_parameters(shot_no, frame_no)
            self.model_database.set_frame_stitching_parameters(shot_no, frame_no, parameters)
            # self.calculate_stitching_values(shot_no=shot_no)
        else:
            print("no need to recalculate")

        self.signal_stitching_calculated.emit()
        self.signal_refresh_image.emit()




    def reset_and_get_initial_shot_stabilize_parameters(self):
        shot_no = self.current_frame['shot_no']
        self.model_database.reset_shot_stabilize_parameters(shot_no=shot_no)

        # Flush cache
        parameters = self.model_database.get_shot_stabilize_parameters(shot_no=shot_no)
        for f in self.frames_fgd[shot_no]:
            frame_no = f['frame_no']
            # print("flush cache: %d: %d" % (f['shot_no'], f['frame_no']))
            if ('cache' in f.keys()
                and f['cache'] is not None):
                del f['cache']
                f['cache'] = None

            f['stabilize'] = {
                'delta_interval': self.model_database.get_shot_stabilize_parameters(shot_no, frame_no)['delta_interval'],
                'dx_dy': self.model_database.get_frame_stabilize(shot_no, frame_no)
            }

        self.signal_refresh_image.emit()
        return parameters


    def event_stabilize_set_enabled(self, is_enabled):
        # Update parameters for this shot
        shot_no = self.current_frame['shot_no']
        parameters = deepcopy(self.model_database.get_shot_stabilize_parameters(shot_no=shot_no))
        for p in parameters:
            p['is_processed'] = False
            p['is_enabled'] = False
        self.model_database.set_shot_stabilize_parameters(shot_no=shot_no, shot_parameters=parameters)

        # Flush cache
        for f in self.frames_fgd[shot_no]:
            # print("flush cache: %d: %d" % (f['shot_no'], f['frame_no']))
            if ('cache' in f.keys()
                and f['cache'] is not None):
                del f['cache']
                f['cache'] = None

            f['stabilize'] = {
                'delta_interval': [0,0,0,0],
                'dx_dy': None
            }

        # Delete stabilization values from frames
        self.model_database.flush_frames_stabilize(shot_no=shot_no)
        self.signal_refresh_image.emit()


    def event_stabilize_do_calculate(self, parameters):
        do_recalculate = False

        shot_no = self.get_shot_no_from_frame_no(frame_no=parameters[0]['start'])
        current_parameters = self.model_database.get_shot_stabilize_parameters(shot_no)
        if len(current_parameters) != len(parameters):
            print("nb of segments differ")
            do_recalculate = True
        else:
            for i in range(len(current_parameters)):
                for k in STABILIZATION_SHOT_PARAMETERS_KEYS:
                    if parameters[i][k] != current_parameters[i][k]:
                        do_recalculate = True
                        break

        if do_recalculate:
            print("Recalculate")
            for p in parameters:
                p['is_processed'] = False
            self.model_database.set_shot_stabilize_parameters(shot_no, parameters)
            self.calculate_stabilize_values(shot_no=shot_no)
        else:
            print("no need to recalculate")

        self.signal_stabilize_calculated.emit()
        self.signal_refresh_image.emit()


    def calculate_stabilize_values(self, shot_no):
        """ Calculate translation values for stabilization.
        This function will calculate these parameters for the shot associated to this frame no.
        """
        print("calculate_stabilize_values: shot_no=%d" % (shot_no))

        shot = self.get_shot(shot_no)
        framelist = self.frames_fgd[shot_no]

        # Reset all stabilization value
        print("reset from %d to %d" % (shot['start'], shot['start']+shot['count'] - 1))
        for i in range(0, shot['count']-1):
            self.model_database.set_frame_stabilize(shot_no, frame_no=shot['start']+i, transformation=None)

        # 1st segment, TODO: add for multiples segments if needed
        parameters = self.model_database.get_shot_stabilize_parameters(shot_no)[0]

        # todo: calculate for multiple segments
        start = parameters['start']
        end = parameters['end']
        ref =  parameters['ref']

        frame_index_ref = ref - shot['start']
        # filepath = framelist[frame_index_ref]['filepath']
        img_ref_gray = cv2.cvtColor(framelist[frame_index_ref]['cache_fgd'], cv2.COLOR_RGB2GRAY)
        img_ref = cv2.copyMakeBorder(img_ref_gray,
            top=PAD_stabilize_REF[0],
            bottom=PAD_stabilize_REF[1],
            left=PAD_stabilize_REF[2],
            right=PAD_stabilize_REF[3],
            borderType=cv2.BORDER_CONSTANT, value=[0, 0, 0])

        # Detect feature points
        points_ref = cv2.goodFeaturesToTrack(img_ref,
            maxCorners=parameters['max_corners'],
            qualityLevel=parameters['quality_level'],
            minDistance=parameters['min_distance'],
            blockSize=parameters['block_size'])
            # useHarrisDetector=True, k=0.04)

        # For debug, save an image
        # corners = np.int0(points_ref)
        # for i in corners:
        #     x,y = i.ravel()
        #     cv2.circle(img_ref,(x,y),3,255,-1)
        # cv2.imwrite("reference.png", img_ref)
        # sys.exit()


        delta_x_list = [0]
        delta_y_list = [0]
        print("calculate from %d to %d" % (start, end))
        for f_no in range(start, end):
            f_index = f_no - shot['start']

            if ('cache' in framelist[f_index].keys()
                and framelist[f_index]['cache'] is not None):
                del framelist[f_index]['cache']
                framelist[f_index]['cache'] = None

            if f_no == ref:
                transformation = [0.0, 0.0]
                self.model_database.set_frame_stabilize(shot_no, f_no, transformation=transformation)
                delta_x_list.append(0)
                delta_y_list.append(0)
                continue

            # filepath = framelist[f_index]['filepath']
            img_src_gray = cv2.cvtColor(framelist[f_index]['cache_fgd'], cv2.COLOR_RGB2GRAY)
            img_src = cv2.copyMakeBorder(img_src_gray,
                PAD_stabilize_REF[0],
                PAD_stabilize_REF[1],
                PAD_stabilize_REF[2],
                PAD_stabilize_REF[3],
                cv2.BORDER_CONSTANT, value=[0, 0, 0])

            # Calculate optical flow (i.e. track feature points)
            points, status, err = cv2.calcOpticalFlowPyrLK(
                img_ref,
                img_src,
                points_ref, None)

            transformation_matrix, _ = cv2.estimateAffinePartial2D(points, points_ref)
            transformation = [
                np.round(np.float32(transformation_matrix[0][2]), decimals=6), # dx
                np.round(np.float32(transformation_matrix[1][2]), decimals=6)  # dy
            ]
            delta_x_list.append(transformation[0])
            delta_y_list.append(transformation[1])

            self.model_database.set_frame_stabilize(shot_no, f_no, transformation=transformation)

        # Set min/max delta for this shot
        if min(delta_x_list) < 0:
            dx_min = round(min(delta_x_list) - .5)
        else:
            dx_min = round(min(delta_x_list) + .5)
        dx_max = round(max(delta_x_list) + .5)

        if min(delta_y_list) < 0:
            dy_min = round(min(delta_y_list) - .5)
        else:
            dy_min = round(min(delta_y_list) + .5)
        dy_max = round(max(delta_y_list) + .5)

        # Update the parameters for this shot and set it to enabled
        self.model_database.set_shot_stabilize_parameters(shot_no, {
            'is_enabled': True,
            'delta_interval': [dx_min, dx_max, dy_min, dy_max],
            'is_ready': True,
        })

        # Update dx_dy for each frame
        for f_no in range(shot['start'], shot['start'] + shot['count']):
            f_index = f_no - shot['start']
            framelist[f_index]['stabilize']['dx_dy'] = self.model_database.get_frame_stabilize(shot_no, f_no)





    def event_prepare_frames_for_preview(self, preview_options_frame_index):
        print("prepare cache:", preview_options_frame_index)
        index = preview_options_frame_index[1]

        do_compute_stabilize_values = False
        if do_compute_stabilize_values:
            self.calculate_stabilize_values(self.playlist_frames, index)
            if True:
                # Save for debug
                k_ep = self.current_selection['k_ep']
                k_part = self.current_selection['k_part']
                print("save stabilization database %s:%s" % (k_ep, k_part))
                self.model_database.save_stabilize_database(k_ep=k_ep, k_part=k_part, shots=self.shots)

        # playlist = [self.playlist_frames[0]]
        playlist = self.playlist_frames

        do_compute_stitching_values = False
        if do_compute_stitching_values:
            # Calculate Stiching values for each frame
            now = time.time()
            with ThreadPoolExecutor(max_workers=4) as executor:
                future_stitching_image = {
                    executor.submit(calculate_stitching_values, frame): frame for frame in playlist
                }
                for future in concurrent.futures.as_completed(future_stitching_image):
                    # frame_no, img = future_stitching_image[future]
                    index, m = future.result()
                    frame = self.playlist_frames[index]
                    self.model_database.set_frame_stitching_transformation(
                        shot_no=frame['shot_no'],
                        frame_no=frame['frame_no'],
                        transformation=m)
                    frame['stitching']['m'] = self.model_database.get_frame_stitching_transformation(frame['shot_no'], frame['frame_no'])

            self.model_database.set_shot_stitching_parameters(frame['shot_no'], {'is_enabled': True})
            print("calculate_stitching_values: %.3f" % (time.time() - now))

            # if True:
            #     # Save for debug
            #     k_ep = self.current_selection['k_ep']
            #     k_part = self.current_selection['k_part']
            #     self.model_database.save_stitching_database(k_ep=k_ep, k_part=k_part, shots=self.shots)


        if False:
            curves = self.view.widget_bgd_curves.get_curve_luts()
            now = time.time()
            with ThreadPoolExecutor(max_workers=8) as executor:
                future_load_image = {executor.submit(process_single_frame, frame, self.get_preview_options(), curves): frame for frame in playlist}
                for future in concurrent.futures.as_completed(future_load_image):
                    # frame_no, img = future_load_image[future]
                    index, img, hist = future.result()
                    self.playlist_frames[index]['cache'] = img
            print("process_single_frame: %.3f" % (time.time() - now))

        print("send signal")
        self.signal_cache_is_ready.emit()



# def generate_single_image(frame:dict, preview_options:dict):
#     # Foreground image (shall be denoised)
#     image_fgd = frame['cache_fgd']
#     if image_fgd is None:
#         # return (frame['index'], cv2.imread(frame['filepath'], cv2.IMREAD_COLOR))
#         sys.exit("cache is not ready")

#     return image_fgd


def generate_single_image(frame:dict, preview_options:dict):
    print("generate_single_image", flush=True)
    # pprint(frame)

    # pprint(preview_options)

    # Foreground image
    img_fgd = frame['cache_fgd']
    height_fgd, width_fgd, c = img_fgd.shape
    print("\timg_fgd: %dx%d" % (width_fgd, height_fgd), flush=True)

    # Modify the bgd image (stitching)
    if preview_options['stitching']['is_enabled']:
        print("\tapply stitching on background image", flush=True)
        if frame['cache_bgd_tmp'] is None:
            # Apply the stitching parameters if preview is enabled
            img_bgd = frame['cache_bgd']

            if frame['stitching']['m'] is not None:
                # Use the matrix to modify the background image
                frame['cache_bgd_tmp'] = cv2.warpPerspective(
                    img_bgd,
                    frame['stitching']['m'],
                    (width_fgd+STICTHING_FGD_PAD[2]+STICTHING_FGD_PAD[3], height_fgd+STICTHING_FGD_PAD[0]+STICTHING_FGD_PAD[1]),
                    cv2.INTER_LANCZOS4,
                    borderMode=cv2.BORDER_CONSTANT, borderValue=(128,128,128))
                img_bgd_tmp = frame['cache_bgd_tmp']
            else:
                # Cannot modify the background
                img_bgd_tmp = cv2.copyMakeBorder(img_bgd,
                    top=STICTHING_FGD_PAD[0], bottom=STICTHING_FGD_PAD[1],
                    left=STICTHING_FGD_PAD[2], right=STICTHING_FGD_PAD[3],
                    borderType=cv2.BORDER_CONSTANT, value=(0,0,0))
        else:
            # Already modified
            img_bgd_tmp = frame['cache_bgd_tmp']
    else:
        img_bgd_tmp = frame['cache_bgd']



    if preview_options['bgd_curves']['is_enabled']:
        print("\tapply rgb curves on bgd image", flush=True)
        # Apply curves on background image
        if img_bgd_tmp is not None:
            # Apply RGB curves to get a similar histogram between bgd and fgd
            try:
                img_bgd = filter_bgd_curves(frame, img_bgd_tmp)
                # return (frame['index'], img_bgd)
            except:
                print("\tCannot apply RGB curves on background image")
                img_bgd = img_bgd_tmp
        else:
            print("\tbgd tmp image is None")
            img_bgd = img_bgd_tmp
    else:
        # Do not apply bgd curves
        img_bgd = img_bgd_tmp
    # print("EROOOOOOR")

    # Crop used for stitching
    # pprint(frame['stitching'])
    crop_top, crop_bottom, crop_left, crop_right = frame['stitching']['fgd_crop']
    y0 = crop_top
    y1 = height_fgd - crop_bottom
    x0 = crop_left
    x1 = width_fgd - crop_right
    pad_h_t = STICTHING_FGD_PAD[0]
    pad_w_l = STICTHING_FGD_PAD[2]


    # extract ROI used for stitching
    print("\tfgd ROI: x:%d->%d, y:%d->%d" % (x0, x1, y0, y1), flush=True)
    print("\tbgd ROI: x:%d->%d, y:%d->%d" % (x0 + pad_w_l, x1 + pad_w_l, y0 + pad_h_t, y1 + pad_h_t), flush=True)
    img_fgd_roi = np.ascontiguousarray(img_fgd[y0:y1, x0:x1], dtype=np.uint8)
    img_bgd_roi = np.ascontiguousarray(img_bgd[
        y0 + pad_h_t : y1 + pad_h_t,
        x0 + pad_w_l : x1 + pad_w_l], dtype=np.uint8)

    histogram = None
    if preview_options['bgd_curves']['is_enabled']:
        # Calculate histogram for the current channel only (optimization)
        print("\tcalculate histogram", flush=True)
        selected_channel = preview_options['bgd_curves']['selected_channel']
        do_calculate_histograms = True
        if do_calculate_histograms:
            if selected_channel == 'r':
                hist_roi_target = cv2.calcHist([img_fgd_roi], [2], None, [256], ranges=[0, 256])
                hist_roi_modified = cv2.calcHist([img_bgd_roi], [2], None, [256], ranges=[0, 256])
            elif selected_channel == 'g':
                hist_roi_target = cv2.calcHist([img_fgd_roi], [1], None, [256], ranges=[0, 256])
                hist_roi_modified = cv2.calcHist([img_bgd_roi], [1], None, [256], ranges=[0, 256])
            elif selected_channel == 'b':
                hist_roi_target = cv2.calcHist([img_fgd_roi], [0], None, [256], ranges=[0, 256])
                hist_roi_modified = cv2.calcHist([img_bgd_roi], [0], None, [256], ranges=[0, 256])

            if selected_channel is not None:
                histogram = {
                    selected_channel: {
                        'target': hist_roi_target,
                        'modified': hist_roi_modified,
                    }
                }
    frame['histogram'] = histogram

    if preview_options['stitching']['is_enabled']:
        # Merge images
        do_blend = True
        if do_blend:
            # Blend a common part
            img_blended = cv2.addWeighted(src1=img_bgd_roi, alpha=0.5, src2=img_fgd_roi, beta=0.5, gamma=0)
            img_bgd[y0+pad_h_t:y1+pad_h_t, x0+pad_w_l:x1+pad_w_l] = img_blended

            blend_width = 2
            img_bgd[y0+pad_h_t+blend_width:y1+pad_h_t-blend_width, x0+pad_w_l+blend_width:x1+pad_w_l-blend_width] = img_fgd[y0+blend_width:y1-blend_width, x0+blend_width:x1-blend_width]
        else:
            # Replace sub-part
            img_bgd[y0+pad_h_t:y1+pad_h_t, x0+pad_w_l:x1+pad_w_l] = img_fgd_roi

    frame['cache'] = img_bgd


    return (frame['index'], img_bgd)

#     now = time.time()
#     img = None
#     print_time = False

#     if print_time:
#         now = time.time()
#         print("process_single_frame")


#     # Foreground image (shall be denoised)
#     image_fgd = frame['cache_fgd']
#     if image_fgd is None:
#         # return (frame['index'], cv2.imread(frame['filepath'], cv2.IMREAD_COLOR))
#         sys.exit("cache is not ready")


#     if preview_options['stitching']['roi_edition']:
#         # ROI for stitching: use the original foreground image
#         return (frame['index'], image_fgd)


#     if preview_options['stitching']['is_enabled']:
#         if frame['cache_bgd'] is not None:
#             img_bgd = frame['cache_bgd']
#         else:
#             filepath_bgd = frame['filepath_bgd']
#             img_bgd = cv2.imread(filepath_bgd, cv2.IMREAD_COLOR)

#         # fgd dimensions
#         height_fgd, width_fgd, c = image_fgd.shape

#         if preview_options['bgd_curves']['is_enabled']:
#             # Apply RGB curves to get a similar histogram between bgd and fgd
#             lut = frame['stitching']['curves']['lut']
#             b, g, r = cv2.split(img_bgd_modified)

#             shape = r.shape
#             img_bgd_r = lut['r'][r.flatten()].reshape(shape).astype(np.uint8)

#             shape = g.shape
#             img_bgd_g = lut['g'][g.flatten()].reshape(shape).astype(np.uint8)

#             shape = b.shape
#             img_bgd_b = lut['b'][b.flatten()].reshape(shape).astype(np.uint8)

#             img_bgd_bgr = cv2.merge((img_bgd_b, img_bgd_g, img_bgd_r))
#         else:
#             # Do not apply stitching curves
#             img_bgd_bgr = image_fgd



#         if frame['stitching']['m'] is not None:
#             # Use the matrix to modify the background image
#             img_bgd_modified = cv2.warpPerspective(
#                 img_bgd,
#                 frame['stitching']['m'],
#                 (width_fgd+STICTHING_FGD_PAD[2]+STICTHING_FGD_PAD[3], height_fgd+STICTHING_FGD_PAD[0]+STICTHING_FGD_PAD[1]),
#                 cv2.INTER_LANCZOS4,
#                 borderMode=cv2.BORDER_CONSTANT, borderValue=(128,128,128))
#         else:
#             # Cannot modify the background
#             img_bgd_modified = cv2.copyMakeBorder(img_bgd,
#                 top=STICTHING_FGD_PAD[0], bottom=STICTHING_FGD_PAD[1],
#                 left=STICTHING_FGD_PAD[2], right=STICTHING_FGD_PAD[3],
#                 borderType=cv2.BORDER_CONSTANT, value=(0,0,0))




#         if preview_options['stitching']['crop_edition']:
#             # Crop the foreground image
#             image_fgd_cropped = image_fgd[y0:y1, x0:x1]
#             image_fgd_with_borders = cv2.copyMakeBorder(image_fgd_cropped,
#                 top=pad_h_t, bottom=STICTHING_FGD_PAD[1],
#                 left=pad_w_l, right=STICTHING_FGD_PAD[3],
#                 borderType=cv2.BORDER_CONSTANT, value=(255,128,128))




#             # crop used for stitching
#             crop_top, crop_bottom, crop_left, crop_right = frame['stitching']['geometry']['fgd']
#             y0 = crop_top
#             y1 = height_fgd - crop_bottom
#             x0 = crop_left
#             x1 = width_fgd - crop_right
#             pad_h_t = STICTHING_FGD_PAD[0]
#             pad_w_l = STICTHING_FGD_PAD[2]




#             return (frame['index'], image_fgd_with_borders, None)



#     # Apply stabilization if enabled before other modifications

#     #   1.1. Add padding to the initial image, even if no stabilization
#     width_stabilized = width_fgd + pad_w_l + pad_w_r
#     height_stabilized = height_fgd + pad_h_t + pad_h_b
#     image_fgd_with_borders = cv2.copyMakeBorder(image_fgd,
#         pad_h_t, pad_h_b,
#         pad_w_l, pad_w_r,
#         cv2.BORDER_CONSTANT,
#         value=[0, 0, 0])

#     if preview_options['stabilize']['is_enabled']:
#         height_fgd, width_fgd, c = image_fgd.shape

#         # 1. Generate the translated image, add padding
#         pad_w_l = 40
#         pad_w_r = 20
#         pad_h_t = 80
#         pad_h_b = 40


#         if frame['stabilize']['dx_dy'] is not None:
#             #   1.2. Generate a stabilized image
#             if False:
#                 # Slower and interpolate pixels
#                 transformation_matrix = np.float32([
#                     [1, 0, 0],
#                     [0, 1, frame['stabilize']['dx_dy'][1]]
#                 ])
#                 img_stabilized = cv2.warpAffine(
#                     image_fgd_with_borders,
#                     transformation_matrix,
#                     (width_stabilized, height_stabilized),
#                     flags=cv2.INTER_LANCZOS4,
#                     borderMode=cv2.BORDER_CONSTANT,
#                     borderValue=(0,0,0))
#             else:
#                 # Faster and do not interpolate pixels
#                 if frame['stabilize']['dx_dy'][1] >= 1:
#                     # Add padding
#                     dy = abs(int(frame['stabilize']['dx_dy'][1]))
#                     img_fgd_cropped = image_fgd_with_borders[
#                         0:height_stabilized - dy,
#                         0:width_stabilized
#                     ]
#                     img_stabilized = cv2.copyMakeBorder(img_fgd_cropped,
#                         top=dy, bottom=0,
#                         left=0, right=0,
#                         borderType=cv2.BORDER_CONSTANT,
#                         value=[0, 0, 0])

#                 elif frame['stabilize']['dx_dy'][1] <= -1:
#                     dy = abs(int(frame['stabilize']['dx_dy'][1]))
#                     # Remove
#                     img_fgd_cropped = image_fgd_with_borders[
#                         dy:height_stabilized,
#                         0:width_stabilized
#                     ]
#                     img_stabilized = cv2.copyMakeBorder(img_fgd_cropped,
#                         top = 0, bottom=dy,
#                         left=0, right=0,
#                         borderType=cv2.BORDER_CONSTANT,
#                         value=[0, 0, 0])
#                 else:
#                     img_stabilized = image_fgd_with_borders


#         if preview_options['curves']['is_enabled']:
#             sys.exit("TODO: generate_single_image: apply curves!!!")



#     if preview_options == 'stitching':

#         # print("process_single_frame: stitching")




#         # Apply stitching
#         do_stitching = True
#         if do_stitching:
#             img_bgd_modified = cv2.warpPerspective(
#                 img_bgd,
#                 frame['stitching']['m'],
#                 (width_fgd+STICTHING_FGD_PAD[2]+STICTHING_FGD_PAD[3], height_fgd+STICTHING_FGD_PAD[0]+STICTHING_FGD_PAD[1]),
#                 cv2.INTER_LANCZOS4,
#                 borderMode=cv2.BORDER_CONSTANT, borderValue=(128,128,128))
#         else:
#             # no stitching
#             img_bgd_modified = cv2.copyMakeBorder(img_bgd,
#                 top=STICTHING_FGD_PAD[0], bottom=STICTHING_FGD_PAD[1],
#                 left=STICTHING_FGD_PAD[2], right=STICTHING_FGD_PAD[3],
#                 borderType=cv2.BORDER_CONSTANT, value=(0,0,0))
#         if print_time:
#             print("\tstitching: %.1f" % (1000* (time.time() - now)))
#             now = time.time()


#             img_bgd_bgr = img_bgd_modified
#         if print_time:
#             print("\tRGB curves on fgd: %.1f" % (1000* (time.time() - now)))
#             now = time.time()

#         # extract ROI for stitching
#         img_fgd_roi = image_fgd[y0:y1, x0:x1]
#         img_bgd_roi = img_bgd_bgr[y0+pad_h_t:y1+pad_h_t, x0+pad_w_l:x1+pad_w_l]


#         # Calculate histogram for the current channel only (optimization)
#         histogram = None
#         do_calculate_histograms = True
#         if do_calculate_histograms:
#             if current_channel == 'r':
#                 hist_roi_target = cv2.calcHist([img_fgd_roi], [2], None, [256], ranges=[0, 256])
#                 hist_roi_modified = cv2.calcHist([img_bgd_roi], [2], None, [256], ranges=[0, 256])
#             elif current_channel == 'g':
#                 hist_roi_target = cv2.calcHist([img_fgd_roi], [1], None, [256], ranges=[0, 256])
#                 hist_roi_modified = cv2.calcHist([img_bgd_roi], [1], None, [256], ranges=[0, 256])
#             elif current_channel == 'b':
#                 hist_roi_target = cv2.calcHist([img_fgd_roi], [0], None, [256], ranges=[0, 256])
#                 hist_roi_modified = cv2.calcHist([img_bgd_roi], [0], None, [256], ranges=[0, 256])

#             if current_channel is not None:
#                 histogram = {
#                     current_channel: {
#                         'target': hist_roi_target,
#                         'modified': hist_roi_modified,
#                     }
#                 }
#         if print_time:
#             print("\tcalculate hist: %.1f" % (1000* (time.time() - now)))
#             now = time.time()

#         # Merge images
#         do_blend = True
#         if do_blend:
#             # Blend a common part
#             img_blended = cv2.addWeighted(src1=img_bgd_roi, alpha=0.5, src2=img_fgd_roi, beta=0.5, gamma=0)
#             img_bgd_bgr[y0+pad_h_t:y1+pad_h_t, x0+pad_w_l:x1+pad_w_l] = img_blended
#             blend_width = 2
#             img_bgd_bgr[y0+pad_h_t+blend_width:y1+pad_h_t-blend_width, x0+pad_w_l+blend_width:x1+pad_w_l-blend_width] = image_fgd[y0+blend_width:y1-blend_width, x0+blend_width:x1-blend_width]
#             img_bgd_new = img_bgd_bgr
#         else:
#             # Replace sub-part
#             img_bgd_bgr[y0+pad_h_t:y1+pad_h_t, x0+pad_w_l:x1+pad_w_l] = img_fgd_roi
#             img_bgd_new = img_bgd_bgr
#         if print_time:
#             print("\tmerge images: %.1f" % (1000* (time.time() - now)))
#             now = time.time()

#         # Stabilize
#         img_bgd_stabilized = stabilize_image(frame, img_bgd_new)
#         if print_time:
#             print("\tstabilize: %.1f" % (1000* (time.time() - now)))
#             now = time.time()

#         # Crop the image
#         # !!! Warning: this is not the final crop wich is define in the shot
#         frame['stitching']['geometry']['shot'] = [30,5,10,10]
#         crop_top, crop_bottom, crop_left, crop_right = frame['stitching']['geometry']['shot']
#         img_bgd_stabilized_cropped = np.ascontiguousarray(img_bgd_stabilized[
#             crop_top : img_bgd_stabilized.shape[0] - crop_bottom,
#             crop_left: img_bgd_stabilized.shape[1] - crop_right
#         ])

#         if print_time:
#             print("\tcrop: %.1f" % (1000* (time.time() - now)))
#             now = time.time()

#         return (frame['index'], img_bgd_stabilized_cropped, histogram)



#     if preview_options in ['stabilize', 'fgd_cropped']:


#         if do_stabilize:

#         else:
#             img_stabilized = image_fgd_with_borders

#         # cv2.imwrite("test.png", img_stabilized)
#         if preview_options == 'stabilize':
#             if print_time:
#                 print("process_single_frame: stabilized: %.2f" % (1000*(time.time() - now)))
#             return (frame['index'], img_stabilized, None)

#     if preview_options == 'fgd_cropped':
#         # fgd_crop_list = frame['shot_stitching']['fgd_crop']
#         # fgd_crop_x0 = fgd_crop_list[0]
#         # fgd_crop_y0 = fgd_crop_list[1]
#         # fgd_crop_w = width_fgd - (fgd_crop_list[2] + fgd_crop_x0)
#         # fgd_crop_h = height_fgd - (fgd_crop_list[3] + fgd_crop_y0)

#         # depends on each shot (defined by user -> use UI for this)
#         crop_left = 25
#         crop_right = 20
#         crop_top = 15
#         crop_bottom = 10

#         dy_max = frame['stabilize']['parameters']['delta_interval'][3]

#         # Position and dimension for foreground ROI and cropped
#         # with dx stabilization:
#         # x0 = pad_w_l + dx_max + crop_left
#         # x1 = width_fgd + pad_w_l + dx_max - crop_right

#         # w/out dx stabilization:
#         x0 = pad_w_l + crop_left
#         x1 = width_fgd + pad_w_l - crop_right

#         dy = 0
#         if frame['stabilize']['dx_dy'] is not None:
#             dy = frame['stabilize']['dx_dy'][1]
#             if abs(dy) < dy_max:
#                 dy = int(dy_max)
#             #     print("use dy rather than dy_min")
#             #     y0 = pad_h_t + int(dy) + crop_top
#             #     y1 = height_fgd + pad_h_t + int(dy) - crop_bottom
#             # else:
#             #     y0 = pad_h_t + int(dy_max) + crop_top
#             #     y1 = height_fgd + pad_h_t + int(dy_max) - crop_bottom

#         # else:
#             # print("no stabilization for %d" % (frame_no))
#         y0 = pad_h_t + int(dy) + crop_top
#         y1 = pad_h_t + height_fgd + int(dy) - crop_top - crop_bottom

#         # print("dimensions: (x0, x1)(y0, y1) = (%d;%d)(%d;%d)" % (x0, x1, y0, y1))

#         img_fgd_cropped = img_stabilized[
#             y0:y1,
#             x0:x1
#         ]

#         #   2.2. Add padding to the stabilized, cropped image
#         img_fgd_4_combine = cv2.copyMakeBorder(img_fgd_cropped,
#             top=y0, bottom=height_stabilized - y1,
#             left=x0, right=width_stabilized - x1,
#             borderType=cv2.BORDER_CONSTANT,
#             value=[0, 0, 0])

#         # cv2.imwrite("test2.png", img_fgd_4_combine)
#         # img_fgd_4_combine = np.ascontiguousarray(img_fgd_4_combine, dtype=np.uint8)
#         # print(img_fgd_4_combine.flags['C_CONTIGUOUS'])

#         # print(1000*(time.time() - now))
#         return (frame['index'], img_fgd_4_combine, hist)


#     # elif preview_options == 'stitching':
#     #     image_bgd = cv2.imread(frame['filepath_bgd'], cv2.IMREAD_COLOR)

#     if preview_options == 'stabilize':
#         img = img_stabilized

#     return (frame['index'], img)


def load_image(frame, is_bgd=False):
    if is_bgd:
        filepath = frame['filepath_bgd']
    else:
        filepath = frame['filepath']
    img = cv2.imread(filepath, cv2.IMREAD_COLOR)
    return (frame['index'], img)