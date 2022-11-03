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

from PySide6.QtCore import (
    Signal,
)

from common.preferences import Preferences
from models.model_database import Model_database
from models.model_common import Model_common

from images.filtering import filter_rgb

from utils.common import (
    K_GENERIQUES,
    get_frame_no_from_filepath,
    get_k_part_from_frame_no,
    get_shot_from_frame_no_new,
)
from utils.get_filters import FILTER_BASE_NO
from utils.get_framelist import get_framelist, get_framelist_2
from utils.consolidate import consolidate_shot

class Model_filters_editor(Model_common):
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
        'selection'
    ]

    SELECTABLE_WIDGET_LIST = [
        'selection'
    ]

    def __init__(self):
        super(Model_filters_editor, self).__init__()

        # Load saved preferences
        self.preferences = Preferences(
            tool='filters_editor',
            widget_list=self.WIDGET_LIST)

        # Variables
        self.model_database = Model_database()

        self.filepath = list()

        self.list_replace = list()

        for step in ['bgd', 'stitching']:
            self.step_labels.remove(step)



    def set_view(self, view):
        self.view = view

        self.view.widget_selection.signal_ep_or_part_selection_changed[dict].connect(self.ep_or_part_selection_changed)
        self.view.widget_selection.signal_selected_shots_changed[dict].connect(self.event_selected_shots_changed)

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
            do_parse_curves=False,
            do_parse_replace=False,
            do_parse_geometry=True,
            do_parse_stitching=False,
            apply_patch_for_study=True)

        # self.shots is a pointer to the shots for this episode/part
        db = self.model_database.database()

        p_missing_frame = os.path.join('img', 'missing.png')

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
                'is_valid': True,

                # Frame no. ... for what?
                'frames_no': list(),

                # Structure to display the modifications in the selection widget
                'modifications': {
                },
            })

            if k_part in K_GENERIQUES:
                k_ed_src = db[k_part]['common']['video']['reference']['k_ed']

            # Create a list of frames for this shot
            self.frames[shot_no] = list()
            for p in filepath_tmp:
                frame_no = get_frame_no_from_filepath(p)

                if not os.path.exists(p):
                    image_filepath = p_missing_frame
                    current_shot['is_valid'] = False
                else:
                    image_filepath = p

                current_shot['frames_no'].append(frame_no)
                self.frames[shot_no].append({
                    'k_ed': k_ed_src,
                    'k_ep': k_ep_src,
                    'k_part': k_part_src,
                    'shot_no': shot_no,
                    'frame_no': frame_no,

                    'filepath': image_filepath,
                    'geometry': self.model_database.get_part_geometry(k_ed_src, k_part),
                    'cache': None,
                })


        # Create a dict to update the "browser" part of the editor widget
        if k_part in K_GENERIQUES:
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

        self.signal_ready_to_play.emit(self.playlist_properties)


    def event_save_and_close_requested(self):
        k_ep = self.current_selection['k_ep']
        k_part = self.current_selection['k_part']
        self.signal_close.emit()



    def get_frame(self, frame_no):
        """ returns the replace frame unless there is no replacemed frame or
        the initial flag is set to True
        framelist contains all path for each frame of this playlist
        """
        # log.info("%s.get_frame: get_frame no. %d" % (__name__, frame_no))
        index = frame_no - self.playlist_properties['start']
        frame = self.playlist_frames[index]

        # Shot has changed: update UI with parameters for this shot (curves, crop, resize)
        if self.current_frame is None or frame['shot_no'] != self.current_frame['shot_no']:
            frame['reload_parameters'] = True
        else:
            frame['reload_parameters'] = False

        # Purge image from the previous frame
        # this is necessary to limit the memory consumption
        # TODO: create a cache structure which manage the cache
        # and another thread to generate the next frames in background (when playing as a video)
        self.purge_current_frame_cache()

        # Set current frame
        self.current_frame = frame

        # Update geometry
        k_ed = self.current_selection['reference']['k_ed']
        k_part = self.current_selection['k_part']
        frame['geometry'] = self.model_database.get_part_geometry(k_ed=k_ed, k_part=k_part)

        # Generate the image for this frame
        options = self.preview_options
        if options is not None:
            index, img = generate_single_image(self.current_frame, preview_options=options)
            self.set_current_frame_cache(img=img)
        # else:
            # Cannot generate the image because no preview option is defined
            # The preview options will be updated by the window UI

        return self.current_frame




def generate_single_image(frame:dict, preview_options:dict):
    # print("generate_single_image")

    now = time.time()
    img = None

    try:
        if frame['cache'] is None:
            # The original has not yet been loaded
            frame['cache'] = cv2.imread(frame['filepath'], cv2.IMREAD_COLOR)
    except:
        frame['cache'] = None

    img_original = frame['cache']
    h, w, c = img_original.shape

    return (frame['index'], img_original)

