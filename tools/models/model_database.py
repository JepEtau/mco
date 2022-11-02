#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

from utils.get_curves import calculate_channel_lut, get_lut_from_curves
sys.path.append('../scripts')
from copy import deepcopy
import gc
import os
import os.path
import configparser
from pathlib import Path
from pathlib import PosixPath
import collections
import numpy as np


from pprint import pprint
from logger import log

from PySide6.QtCore import(
    QObject,
    Signal,
)


from utils.path import PATH_DATABASE
from utils.common import K_GENERIQUES, K_NON_GENERIQUE_PARTS, get_k_part_from_frame_no, get_shot_from_frame_no_new, nested_dict_clean, nested_dict_set, pprint_video

from parsers.parser_common import parse_common_configuration
from parsers.parser_database import pprint_episode

from parsers.parser_editions import parse_editions
from parsers.parser_editions import get_available_editions

from parsers.parser_generiques import db_init_generiques
from parsers.parser_generiques import parse_generiques_common, parse_generiques
from parsers.parser_generiques import parse_get_dependencies_for_generique

from parsers.parser_episodes import db_init_episodes, parse_get_dependencies_for_episodes
from parsers.parser_episodes import parse_episodes_common, parse_episode

from parsers.parser_shots import create_dst_shots, create_dst_shots_g

from utils.consolidate import align_audio_video_durations, determine_av_sync
from utils.consolidate import align_audio_video_durations_g_debut_fin

from parsers.parser_stabilize import STABILIZATION_SHOT_PARAMETERS_DEFAULT
from parsers.parser_stabilize import parse_stabilize_configurations
from parsers.parser_stabilize import get_shots_stabilize_parameters, get_frames_stabilize


from parsers.parser_stitching import STITCHING_SHOT_PARAMETERS_DEFAULT
from parsers.parser_stitching import get_frames_stitching_parameters
from parsers.parser_stitching import get_frames_stitching_transformation
from parsers.parser_stitching import get_shot_stitching_curves
from parsers.parser_stitching import get_shots_stitching_fgd_crop
from parsers.parser_stitching import parse_stitching_configurations
from parsers.parser_stitching import get_shots_stitching_parameters
from parsers.parser_stitching import STITCHING_CURVES_DEFAULT, parse_stitching_curves_database

from parsers.parser_curves import (
    get_curves_selection,
    parse_curve_configurations,
    parse_curves_file,
    parse_curves_folder,
    write_curves_file
)

from parsers.parser_replace import parse_replace_configurations
from parsers.parser_replace import get_replaced_frames

from parsers.parser_geometry import parse_geometry_configurations
from parsers.parser_geometry import get_part_geometry
from parsers.parser_geometry import get_shots_st_geometry

from images.curve import Curve, calculate_lut_for_bgd



class Model_database(object):

    def __init__(self):
        super(Model_database, self).__init__()

        # Variables
        self.global_database = None
        self.initial_database = dict()
        self.is_parsed_dict = dict()
        self.shots_per_curves = dict()

        self.frame_parameters = dict()

        self.db_stabilize_frames = dict()
        self.db_stabilize_shots_parameters = dict()

        self.db_stitching_shots_parameters = dict()
        self.db_stitching_frames = dict()

        self.crop_coordinates = dict()

        self.replaced_frames = dict()

        self.is_curves_db_modified = False
        self.is_curves_selection_db_modified = False
        self.is_replace_db_modified = False
        self.is_stabilize_db_modified = False
        self.is_stitching_db_modified = False
        self.is_stitching_curves_db_modified = False
        self.is_geometry_db_modified = False



        self.initial_database['common'] = parse_common_configuration(PATH_DATABASE)
        self.initial_database['editions'] = parse_editions(self.initial_database)
        parse_episodes_common(self.initial_database)

        self.k_editions = get_available_editions(self.initial_database)
        for k_ed in self.k_editions:
            db_init_episodes(self.initial_database, k_ed=k_ed)

            # Initialize dictionary for generiques
            db_init_generiques(self.initial_database, k_ed=k_ed)

        # Parse database file which contains common settings for generiques
        parse_generiques_common(self.initial_database)
        # For each edition, parse the generique database
        for k_ed in self.k_editions:
            parse_generiques(self.initial_database, k_ed=k_ed)

        self.path_images =self.initial_database['common']['directories']['frames']


        # Here, we have the initial database
    def get_images_path(self):
        return self.path_images

    def get_cache_path(self):
        return self.initial_database['common']['directories']['cache']

    def get_curves_library_path(self):
        return self.initial_database['common']['directories']['curves']

    def consolidate_database(self, k_ep, k_part,
                                do_parse_curves:bool=True,
                                do_parse_replace:bool=True,
                                do_parse_geometry:bool=True,
                                do_parse_stitching:bool=False):
        print("%s:consolidate_database %s:%s" % (__name__, k_ep, k_part))

        if k_ep == '' and k_part == '':
            return

        del self.global_database
        self.global_database = deepcopy(self.initial_database)


        if k_ep.startswith('ep'):
            # Create a dict of dependencies for generiques
            dependencies = dict()
            for k_part_g in ['g_asuivre', 'g_reportage']:
                dependencies_tmp = parse_get_dependencies_for_generique(self.global_database, k_part_g=k_part_g)
                for k,v in dependencies_tmp.items():
                    if k not in dependencies.keys():
                        dependencies[k] = list()
                    dependencies[k] = list(set(dependencies[k] + v))


            # Parse episode at first (required to generate dependencies)
            for k_ed_tmp in self.k_editions:
                parse_episode(self.global_database, k_ed=k_ed_tmp, k_ep=k_ep)

            # Get dependencies for this episode
            dependencies_tmp = parse_get_dependencies_for_episodes(self.global_database, k_ep=k_ep)

            # Merge dependencies
            for k,v in dependencies_tmp.items():
                if k not in dependencies.keys():
                    dependencies[k] = list()
                dependencies[k] = list(set(dependencies[k] + v))

            # Parse episodes which are required (dependencies)
            for k_ed_tmp, v in dependencies.items():
                for k_ep_tmp in v:
                    if k_ep_tmp == k_ep:
                        # print("do not parse, already done: %s:%s" % (k_ed_tmp, k_ep_tmp))
                        continue
                    # print("parse dependency: %s:%s" % (k_ed_tmp, k_ep_tmp))
                    parse_episode(self.global_database, k_ed=k_ed_tmp, k_ep=k_ep_tmp)

            # Parse other config files for each dependency
            for k_ed_tmp, v in dependencies.items():
                for k_ep_tmp in dependencies[k_ed_tmp]:
                    if do_parse_stitching:
                        parse_stitching_configurations(self.global_database, k_ep_or_g=k_ep_tmp, parse_parameters=True)
                    parse_stabilize_configurations(self.global_database, k_ep_or_g=k_ep_tmp, parse_parameters=True)

                    if do_parse_curves:
                        parse_curve_configurations(self.global_database, k_ep_or_g=k_ep_tmp)

                    if do_parse_replace:
                        parse_replace_configurations(self.global_database, k_ep_or_g=k_ep_tmp)
                    if do_parse_geometry:
                        parse_geometry_configurations(self.global_database, k_ep_or_g=k_ep_tmp)

            if do_parse_stitching:
                parse_stitching_configurations(self.global_database, k_ep_or_g=k_ep, parse_parameters=True)
            parse_stabilize_configurations(self.global_database, k_ep_or_g=k_ep, parse_parameters=True)
            if do_parse_curves:
                parse_curve_configurations(self.global_database, k_ep_or_g=k_ep)
            if do_parse_replace:
                parse_replace_configurations(self.global_database, k_ep_or_g=k_ep)
            if do_parse_geometry:
                parse_geometry_configurations(self.global_database, k_ep_or_g=k_ep)


            # Consolidate database for the episode
            for k_p in K_NON_GENERIQUE_PARTS:
                create_dst_shots(self.global_database, k_ep=k_ep, k_part=k_p)

            for k_part_g in ['g_asuivre', 'g_reportage']:
                if do_parse_curves:
                    parse_curve_configurations(self.global_database, k_ep_or_g=k_part_g)
                if do_parse_replace:
                    parse_replace_configurations(self.global_database, k_ep_or_g=k_part_g)
                if do_parse_geometry:
                    parse_geometry_configurations(self.global_database, k_ep_or_g=k_part_g)

                # Create shots used for the generatio
                create_dst_shots_g(self.global_database, k_ep=k_ep, k_part_g=k_part_g)

            determine_av_sync(self.global_database, k_ep=k_ep)
            align_audio_video_durations(self.global_database, k_ep=k_ep)

            if k_part != '':
                if do_parse_replace:
                    self.db_replaced_frames_initial = get_replaced_frames(self.global_database, k_ep=k_ep, k_part=k_part)
                    self.db_replaced_frames = dict()

                if do_parse_geometry:
                    self.db_part_geometry_initial = get_part_geometry(self.global_database, k_ep=k_ep, k_part=k_part)
                    self.db_part_geometry = dict()

                if do_parse_stitching:
                    self.db_stitching_shots_parameters_initial = get_shots_stitching_parameters(self.global_database, k_ep=k_ep, k_part=k_part)
                    self.db_stitching_shots_parameters = dict()
                    self.db_stitching_frames_parameters_initial = get_frames_stitching_parameters(self.global_database, k_ep=k_ep, k_part=k_part)
                    self.db_stitching_frames_parameters = dict()

                    self.db_stitching_frames_initial = get_frames_stitching_transformation(self.global_database, k_ep=k_ep, k_part=k_part)
                    self.db_stitching_frames = dict()

                    self.parse_stitching_curves_database(k_ep=k_ep)
                    self.db_stitching_shots_curves_initial = get_shot_stitching_curves(self.global_database, k_ep=k_ep, k_part=k_part)
                    self.db_stitching_shots_curves = dict()

                    self.db_stitching_shots_fgd_crop_initial = get_shots_stitching_fgd_crop(self.global_database, k_ep=k_ep, k_part=k_part)
                    self.db_stitching_shots_fgd_crop = dict()

                self.db_stabilize_shots_parameters_initial = get_shots_stabilize_parameters(self.global_database, k_ep=k_ep, k_part=k_part)
                self.db_stabilize_shots_parameters = dict()

                self.db_stabilize_frames_initial = get_frames_stabilize(self.global_database, k_ep=k_ep, k_part=k_part)
                self.db_stabilize_frames = dict()

                self.db_st_geometry_initial = get_shots_st_geometry(self.global_database, k_ep=k_ep, k_part=k_part)
                self.db_st_geometry = dict()

                if do_parse_curves:
                    self.db_curves_library_initial = parse_curves_folder(db=self.global_database, k_ep_or_g=k_ep)
                    self.db_curves_library = dict()
                    self.db_curves_selection_initial = get_curves_selection(self.global_database, k_ep=k_ep, k_part=k_part)
                    self.db_curves_selection = dict()
                # print("<<<<<<<<<<<<<<<<< %s:%s: shot stabilization parameters >>>>>>>>>>>>>>>>>>>>" % (k_ep, k_part))
                # for k_shot_no, parameters in self.db_stabilize_shots_parameters.items():
                #     for parameter in parameters:
                #         if parameter['is_enabled']:
                #             print("%d:" % (k_shot_no), end='')
                #             pprint(parameter)
                # pprint(self.db_stabilize_shots_parameters)

                # self.shots_stitching = get_shots_stitching(self.global_database, k_ep=k_ep, k_part=k_part)
                # self.db_stitching_frames = get_stitching_frames(self.global_database, k_ep=k_ep, k_part=k_part)
                # self.shots_stitching_settings = get_shots_stitching_settings(self.global_database, k_ep=k_ep, k_part=k_part)

                # print("<<<<<<<<<<<<<<<<< %s:%s: shot stitching parameters >>>>>>>>>>>>>>>>>>>>" % (k_ep, k_part))
                # for k_shot_no, parameters in self.db_stitching_shots_parameters.items():
                #     if parameters['parameters']['is_enabled']:
                #         print("%d:" % (k_shot_no), end='')
                #         pprint(parameters)

            # print("<<<<<<<<<<<<<<<<< %s:%s: frame stabilization >>>>>>>>>>>>>>>>>>>>" % (k_ep, k_part))
            # pprint(self.db_stabilize_frames)

            # print("<<<<<<<<<<<<<<<<< %s:%s: frame stitching >>>>>>>>>>>>>>>>>>>>" % (k_ep, k_part))
            # pprint(self.db_stitching_frames)

            # print("<<<<<<<<<<<<<<<<< %s:%s: shots stitching settings >>>>>>>>>>>>>>>>>>>>" % (k_ep, k_part))
            # pprint(self.shots_stitching_settings)
            # print("<<<<<<<<<<<<<<<<< %s:%s: shots stitching >>>>>>>>>>>>>>>>>>>>" % (k_ep, k_part))
            # pprint(self.shots_stitching)
            # print("<<<<<<<<<<<<<<<<< %s:%s: frames stitching >>>>>>>>>>>>>>>>>>>>" % (k_ep, k_part))
            # pprint(self.db_stitching_frames)
            # print("<<<<<<<<<<<<<<<<< %s:%s: replaced frames >>>>>>>>>>>>>>>>>>>>" % (k_ep, k_part))
            # pprint(self.replaced_frames)
            # sys.exit()

        else:
            # Parse the episode used for this generique
            dependencies = parse_get_dependencies_for_generique(self.global_database, k_part_g=k_part)
            for k_ed_tmp, k_eps in dependencies.items():
                for k_ep_tmp in k_eps:
                    # print("\tparse_episode: k_ed=%s, k_ep=%s" % (k_ed_tmp, k_ep_tmp))
                    parse_episode(self.global_database, k_ed=k_ed_tmp, k_ep=k_ep_tmp)

            for k_ed_tmp, k_eps in dependencies.items():
                for k_ep_tmp in dependencies[k_ed_tmp]:
                    # Parse other config files for each dependency
                    # print("\tparse_***_configurations: k_ed=%s, k_ep=%s" % (k_ed_tmp, k_ep_tmp))
                    if do_parse_stitching:
                        parse_stitching_configurations(self.global_database, k_ep_or_g=k_ep_tmp)
                    if do_parse_curves:
                        parse_curve_configurations(self.global_database, k_ep_or_g=k_ep_tmp)
                    if do_parse_replace:
                        parse_replace_configurations(self.global_database, k_ep_or_g=k_ep_tmp)
                    if do_parse_geometry:
                        parse_geometry_configurations(self.global_database, k_ep_or_g=k_ep_tmp)
                break

            # Stabilization and stitching
            if do_parse_stitching:
                parse_stitching_configurations(self.global_database, k_ep_or_g=k_part)

            # Curves: this parser update the shots for each episode/part
            # print("\tparse_curve_configurations: k_part_g=%s" % (k_part))
            if do_parse_curves:
                parse_curve_configurations(self.global_database, k_ep_or_g=k_part)

            # Replaced frames
            if do_parse_replace:
                # print("\tparse_replace_configurations: k_part_g=%s" % (k_part))
                parse_replace_configurations(self.global_database, k_ep_or_g=k_part)
                self.db_replaced_frames_initial = get_replaced_frames(self.global_database, k_ep='', k_part=k_part)
                self.db_replaced_frames = dict()

            # Crop
            if do_parse_geometry:
                # print("\tparse_geometry_configurations: k_part_g=%s" % (k_part))
                parse_geometry_configurations(self.global_database, k_ep_or_g=k_part)
                self.db_part_geometry_initial = get_part_geometry(self.global_database, k_ep='', k_part=k_part)
                self.db_part_geometry = dict()

            # Curves
            if do_parse_curves:
                self.db_curves_selection_initial = get_curves_selection(self.global_database, k_ep=k_ep, k_part=k_part)
                self.db_curves_selection = dict()
                self.db_curves_library_initial = parse_curves_folder(db=self.global_database, k_ep_or_g=k_part)
                self.db_curves_library = dict()

            # Create shots used for the generation
            # print("\tcreate_dst_shots_g: k_part_g=%s" % (k_part))
            create_dst_shots_g(self.global_database, k_ep='', k_part_g=k_part)

            # Consolidate by aligning the A/V tracks of generiques
            # print("\talign_audio_video_durations_g_debut_fin: k_part_g=%s" % (k_part))
            align_audio_video_durations_g_debut_fin(self.global_database, k_ep='', k_part_g=k_part)

            # print("\t%s:%s, replaced frames" % (k_ep, k_part))
            # pprint(self.replaced_frames)


        # print("\tended")
        # if k_ep == 'ep01':
            # pprint(self.global_database[k_ep]['k'])
            # pprint_video(self.global_database[k_ep]['k']['episode'])
            # pprint_episode(self.global_database, k_ep)
            # sys.exit()
        gc.collect()

    def database(self):
        if self.global_database is None:
            return self.initial_database
        return self.global_database



    # RGB curves
    def get_curves_selection(self, shot):
        # Get the curves associated to this shot
        k_ed = shot['k_ed']
        k_ep = shot['k_ep']
        k_part = shot['k_part']
        shot_no = shot['no']
        try: shot_curves = self.db_curves_selection[k_ed][k_ep][k_part][shot_no]
        except:
            try: shot_curves = self.db_curves_selection_initial[k_ed][k_ep][k_part][shot_no]
            except: return None

        if 'k_curves' not in shot_curves.keys() or shot_curves['k_curves'] == '':
            # This shot uses new RGB curves which are not yet been saved in the library
            return shot_curves

        # Get the curves from the library
        k_ep_or_g = k_part if k_part in K_GENERIQUES else k_ep
        curves = self.get_curves(k_ep_or_g, shot_curves['k_curves'])
        return curves


    def set_shot_rgb_channels(self, shot, rgb_channels):
        k_ed = shot['k_ed']
        k_ep = shot['k_ep']
        k_part = shot['k_part']
        shot_no = shot['no']
        # Get the curves frome the db_chot_curves. it points to the curves
        # stored in the db_curves_library
        try:
            shot_curves = self.db_curves_selection[k_ed][k_ep][k_part][shot_no]
        except:
            try:
                shot_curves = self.db_curves_selection_initial[k_ed][k_ep][k_part][shot_no]
            except:
                print("these curves does not exist: create an empty one in the db_shot")
                curves = ({
                    'k_curves': '',
                    'channels': deepcopy(rgb_channels),
                    'lut': calculate_channel_lut(rgb_channels),
                    'is_modified': True,
                })
                nested_dict_set(self.db_curves_selection, curves, k_ed, k_ep, k_part, shot_no)
                self.is_curves_db_modified = True
                return

        if shot_curves['k_curves'] == '':
            # Curves is not yet saved in library
            self.db_curves_selection[k_ed][k_ep][k_part][shot_no].update({
                'channels': deepcopy(rgb_channels),
                'lut': calculate_channel_lut(rgb_channels),
                'is_modified': True,
            })
            self.is_curves_db_modified = True
            return

        # Modify the curves in the library
        is_modified = self.set_curves(k_curves=shot_curves['k_curves'], rgb_channels=rgb_channels)
        if not is_modified:
            # No curves found for this k_curves, create a new one in the shot
            curves = ({
                'k_curves': '',
                'channels': deepcopy(rgb_channels),
                'lut': calculate_channel_lut(rgb_channels),
                'is_modified': True,
            })
            nested_dict_set(self.db_curves_selection, curves, k_ed, k_ep, k_part, shot_no)

        self.is_curves_db_modified = True



    def set_curves_selection(self, shot:dict, k_curves:str):
        k_ed = shot['k_ed']
        k_ep = shot['k_ep']
        k_part = shot['k_part']
        shot_no = shot['no']

        # Get the curves from the library
        k_ep_or_g = k_part if k_part in K_GENERIQUES else k_ep
        curves = self.get_curves(k_ep_or_g, k_curves)

        # Set the modified shot curves
        nested_dict_set(self.db_curves_selection, curves, k_ed, k_ep, k_part, shot_no)

        # Refresh the list of shots for each curves
        for shotlist in self.shots_per_curves.values():
            try:
                shotlist.remove(shot_no)
                break
            except: pass
        try: self.shots_per_curves[k_curves].append(shot_no)
        except: self.shots_per_curves[k_curves] = [shot_no]

        self.is_curves_selection_db_modified = True


    def move_curves_selection_to_initial(self):
        for k_ed in self.db_curves_selection.keys():
            for k_ep in self.db_curves_selection[k_ed].keys():
                for k_part in self.db_curves_selection[k_ed][k_ep].keys():
                    for shot_no, shot_curves in self.db_curves_selection[k_ed][k_ep][k_part].items():
                        if shot_curves['k_curves'] != '':
                            nested_dict_set(self.db_curves_selection_initial,
                                deepcopy(shot_curves), k_ed, k_ep, k_part, shot_no)
                        else:
                            print("error: curves are not saved for shot no. %d" % (shot_no))
        self.db_curves_selection.clear()
        self.is_curves_selection_db_modified = False


    # List the shots which use the  same curves
    def initialize_shots_per_curves(self, shots):
        self.shots_per_curves = dict()
        for shot_no, shot in shots.items():
            try:
                k_curves = shot['curves']['k_curves']
                try: self.shots_per_curves[k_curves].append(shot_no)
                except: self.shots_per_curves[k_curves] = [shot_no]
            except:
                pass

    def get_shots_per_curves(self, k_curves):
        try:
            return list(sorted(self.shots_per_curves[k_curves]))
        except:
            return None


    # RGB curves library
    def get_library_curves(self):
        curves_library = dict()
        for k in self.db_curves_library_initial.keys():
            if k in self.db_curves_library.keys():
                # These curves are modified or deleted
                if not 'deleted' in self.db_curves_library[k].keys():
                    # These curves are modified
                    curves_library[k] = True
            else:
                curves_library[k] = False
        return curves_library


    def get_curves(self, k_ep_or_g:str, k_curves:str):
        try:
            curves = self.db_curves_library[k_curves]
            log.info("[%s] is found in the modified db" % (k_curves))
        except:
            try:
                curves = self.db_curves_library_initial[k_curves]
                # log.info("[%s] is found in the initial db" % (k_curves))
            except:
                return None
        if curves['channels'] is None:
            # print("parse %s.crv file" % (k_curves))
            curves['channels'] = parse_curves_file(
                db=self.global_database,
                k_ep_or_g=k_ep_or_g,
                k_curves=k_curves)
        if curves['channels'] is None:
            # The curves file has not been found
            log.warning("The curves have not been found")
            curves = None
        else:
            if curves['lut'] is None:
                curves['lut'] = calculate_channel_lut(curves['channels'])
        return curves


    def set_curves(self, k_curves:str, rgb_channels):
        try:
            curves = self.db_curves_library[k_curves]
        except:
            try:
                print("set_curves: copy from initial to modified")
                self.db_curves_library[k_curves] = deepcopy(self.db_curves_library_initial[k_curves])
                curves = self.db_curves_library[k_curves]
            except:
                print("[%s] does not exists neither in library not in initial library" % (k_curves))
                return False

        curves.update({
            'channels': deepcopy(rgb_channels),
            'lut': calculate_channel_lut(rgb_channels),
            'is_modified': True,
        })
        self.is_curves_db_modified = True
        return True


    def discard_curves_modifications(self, k_curves):
        try:
            del self.db_curves_library[k_curves]
        except:
            print("Error: discard_curves_modifications: failed")
            pass


    def save_all_curves(self, k_ep_or_g):
        for curves in self.db_curves_library.values():
            self.save_curves_as(k_ep_or_g=k_ep_or_g, curves=curves)


    def save_curves_as(self, k_ep_or_g, curves):
        k_curves = curves['k_curves']
        try:
            # Remove from modified db
            del self.db_curves_library[k_curves]
            log.info("removed [%s] from modified db" % (k_curves))
        except:
            # These curves were not modified
            pass

        # Append these curves in the initial db
        try:
            # overwrite curves
            filepath = filepath = os.path.join(
                self.global_database['common']['directories']['curves'],
                self.db_curves_library_initial[k_curves]['filepath'])
        except:
            # new curves
            log.error("filepath is not specified for [%s]" % (k_curves))
            filepath = os.path.join(
                self.global_database['common']['directories']['curves'],
                k_ep_or_g,
                "%s.crv" % (k_curves))

        log.info("write curves file as [%s]" % (filepath))
        pprint(curves)
        write_curves_file(filepath=filepath, channels=curves['channels'])

        self.db_curves_library_initial[k_curves] = {
            'k_curves': k_curves,
            'filepath': filepath,
            'channels': deepcopy(curves['channels']),
            'lut': None,
            'shots': []
        }

        # Consider as not modified
        # self.db_curves_library_initial[k_curves]['is_modified'] = False

        # Write or overwrite the curves files

        # if k_curves in self.db_curves_library_initial.keys():
        #     # These curves where already defined in the initial db
        #     log.info("mark [%s] as modified" % (k_curves))
        #     self.db_curves_library[k_curves]['is_modified'] = True
        # else:
        #     log.info("mark [%s] is a new one" % (k_curves))
        #     self.db_curves_library[k_curves]['is_modified'] = False



    # Replaced frames
    def get_replace_frame_no(self, shot:dict, frame_no:int):
        """ Return the new frame no. if replaced. Returns -1 otherwise
        """
        k_ed = shot['k_ed']
        k_ep = shot['k_ep']
        k_part = shot['k_part']
        try: return self.db_replaced_frames[k_ed][k_ep][k_part][frame_no]
        except: pass
        try: return self.db_replaced_frames_initial[k_ed][k_ep][k_part][frame_no]
        except: return -1

    def set_replaced_frame(self, shot, frame_no, new_frame_no):
        k_ed = shot['k_ed']
        k_ep = shot['k_ep']
        k_part = shot['k_part']
        nested_dict_set(self.db_replaced_frames, new_frame_no, k_ed, k_ep, k_part, frame_no)
        self.is_replace_db_modified = True


    def remove_replaced_frame(self, shot, frame_no):
        db_modified = self.db_replaced_frames
        k_ed = shot['k_ed']
        k_ep = shot['k_ep']
        k_part = shot['k_part']
        try:
            if frame_no in self.db_replaced_frames_initial[k_ed][k_ep][k_part].keys():
                nested_dict_set(self.db_replaced_frames, -1, k_ed,k_ep, k_part, frame_no)
                self.is_replace_db_modified = True
                return
        except:
            pass
        try: del db_modified[k_ed][k_ep][k_part][frame_no]
        except:
            print("Error: cannot remove from modified: %s:%s:%s:%d" % (k_ed, k_ep, k_part, frame_no))
            pprint(self.db_replaced_frames)
            sys.exit()
        self.is_replace_db_modified= True
        return


    def discard_replace_modifications(self):
        log.info("discard_replace_modifications")
        self.db_replaced_frames.clear()
        self.is_replace_db_modified = False


    def move_replace_to_initial(self):
        # Move modifications from modified to initial: faster than parsing the config file
        # but not secure. TODO: reparse the config file?
        for k_ed in self.db_replaced_frames.keys():
            for k_ep in self.db_replaced_frames[k_ed].keys():
                for k_part in self.db_replaced_frames[k_ed][k_ep].keys():
                    for frame_no in self.db_replaced_frames[k_ed][k_ep][k_part]:
                        v = self.db_replaced_frames[k_ed][k_ep][k_part][frame_no]
                        if v == -1:
                            del self.db_replaced_frames_initial[k_ed][k_ep][k_part][frame_no]
                        else:
                            nested_dict_set(self.db_replaced_frames_initial,
                                v, k_ed, k_ep, k_part, frame_no)
        self.db_replaced_frames.clear()
        self.is_replace_db_modified = False


    # Final geometry for each part
    def get_part_geometry(self, k_ed, k_part):
        for db_tmp in [self.db_part_geometry,
                        self.db_part_geometry_initial]:
            if k_ed in db_tmp.keys() and k_part in db_tmp[k_ed].keys():
                return db_tmp[k_ed][k_part]
        return None

    def set_part_geometry(self, k_ed, k_part, geometry):
        # db_modified = self.db_part_geometry
        # if k_ed not in db_modified.keys():
        #     db_modified[k_ed] = dict()
        # if k_part not in db_modified[k_ed].keys():
        #     db_modified[k_ed][k_part] = dict()
        # db_modified[k_ed][k_part] = geometry
        nested_dict_set(self.db_part_geometry, geometry, k_ed, k_part)
        self.is_geometry_db_modified = True

    def discard_part_geometry_modifications(self, k_ed, k_part):
        log.info("discard_part_geometry_modifications")
        db_modified = self.db_part_geometry
        try: del db_modified[k_ed][k_part]
        except: pass
        if len(db_modified[k_ed].keys()) == 0:
            del db_modified[k_ed]
        self.is_geometry_db_modified = False

    def move_part_geometry_to_initial(self):
        # Move modifications from modified to initial
        self.db_part_geometry_initial.update(deepcopy(self.db_part_geometry))
        self.db_part_geometry.clear()




    # TODO: no, this is is for final geometry, rework this!!!
    # Use this geometry values to replace the final one, used after stitching/stabilization
    def get_shot_stitching_crop(self, shot_no):
        if shot_no in self.db_stitching_shots_parameters.keys():
            if 'crop' in self.db_stitching_shots_parameters[shot_no].keys():
                return self.db_stitching_shots_parameters[shot_no]['geometry']
        # print("returned default for shot no. %d" % (shot_no))
        return [0, 0, 0, 0]


    # Transformation for each frame
    def get_frame_stitching_transformation(self, shot_no, frame_no):
        for db_tmp in [self.db_stitching_frames,
                            self.db_stitching_frames_initial]:
            if shot_no in db_tmp.keys():
                if frame_no in db_tmp[shot_no].keys():
                    return db_tmp[shot_no][frame_no]
        return None

    def set_frame_stitching_transformation(self, shot_no, frame_no, transformation):
        db_modified = self.db_stitching_frames
        if shot_no not in db_modified.keys():
            db_modified[shot_no] = dict()
        db_modified[shot_no][frame_no] = transformation
        self.is_stabilize_db_modified = True


    def flush_frame_stitching_transformation(self, shot_no):
        print("flush_frame_stitching_transformation")
        db_modified = self.db_stitching_frames
        if shot_no in db_modified.keys():
            del db_modified[shot_no]



    # Parameters for shot stitching
    def get_shot_stitching_parameters(self, shot_no):
        """Returns the parameters for this shot
        """
        for db_parameters in [self.db_stitching_shots_parameters,
                                self.db_stitching_shots_parameters_initial]:
            if shot_no in db_parameters.keys():
                if db_parameters[shot_no]['is_enabled']:
                    return db_parameters[shot_no]
        return deepcopy(STITCHING_SHOT_PARAMETERS_DEFAULT)


    def set_shot_stitching_parameters(self, shot_no, parameters):
        """Set new parameters for this shot
        """
        if shot_no not in self.db_stitching_shots_parameters.keys():
            self.db_stitching_shots_parameters[shot_no] = deepcopy(STITCHING_SHOT_PARAMETERS_DEFAULT)
        self.db_stitching_shots_parameters[shot_no].update(parameters)
        self.is_stitching_db_modified = True


    def remove_shot_stitching_parameters(self, shot_no):
        """Remove the parameters for this shot
        """
        if shot_no not in self.db_stitching_shots_parameters_initial.keys():
            # Set a flag to remove this parameters (use is_enabled flag)
            if shot_no not in self.db_stitching_shots_parameters.keys():
                self.db_stitching_shots_parameters[shot_no] = deepcopy(self.db_stitching_shots_parameters_initial[shot_no])
            self.db_stitching_shots_parameters[shot_no]['is_enabled'] = False
        else:
            # Not defined in initial db, remove from modified
            if shot_no in self.db_stitching_shots_parameters.keys():
                del self.db_stitching_shots_parameters[shot_no]

        # Remove all customized parameters for each frame in this shot
        self.remove_all_frames_stitching_parameters()
        self.is_stitching_db_modified = True


    def remove_single_frame_stitching_parameters(self, shot_no, frame_no):
        if (shot_no in self.db_stitching_shots_parameters_initial.keys()
            and frame_no in self.db_stitching_shots_parameters_initial[shot_no].keys()):
            # Set a flag to remove this parameters (use is_enabled flag)
            if shot_no not in self.db_stitching_frames_parameters.keys():
                self.db_stitching_frames_parameters[shot_no] = dict()
            if frame_no not in self.db_stitching_frames_parameters[shot_no].keys():
                self.db_stitching_frames_parameters[shot_no][frame_no] = deepcopy(self.db_stitching_shots_parameters_initial[shot_no][frame_no])
            self.db_stitching_shots_parameters[shot_no][frame_no]['is_enabled'] = False
        else:
            # Not in initial, remove from modified
            if (shot_no in self.db_stitching_frames_parameters.keys()
                and frame_no in self.db_stitching_frames_parameters[shot_no].keys()):
                del self.db_stitching_frames_parameters[shot_no][frame_no]
        self.is_stitching_db_modified = True


    def remove_all_frames_stitching_parameters(self, shot_no):
        """Remove the parameters for all frames
        """
        if shot_no not in self.db_stitching_frames_parameters_initial.keys():
            # Set a flag to remove this parameters (use is_enabled flag)
            if shot_no not in self.db_stitching_frames_parameters.keys():
                self.db_stitching_frames_parameters[shot_no] = dict()

            for f_no, f_values in self.db_stitching_frames_parameters_initial.items():
                if f_no not in self.db_stitching_frames_parameters[shot_no].keys():
                    self.db_stitching_frames_parameters[shot_no][f_no] = deepcopy(f_values)
                self.db_stitching_frames_parameters[shot_no][f_no]['is_enabled'] = False
        else:
            # Not defined in initial db, remove from modified
            if shot_no in self.db_stitching_frames_parameters.keys():
                del self.db_stitching_frames_parameters[shot_no]
        self.is_stitching_db_modified = True


    # Stitching parameters used for each frame (overwrite the one from shot)
    def get_frame_stitching_parameters(self, shot_no, frame_no):
        """ Return the parameters used for the stitching: the parameters
        might be different for each frame, thus get parameters from frame is defined
        otherwise, returns the parameters for the shot
        """
        if shot_no in self.db_stitching_frames_parameters.keys():
            if frame_no in self.db_stitching_frames_parameters[shot_no].keys():
                return self.db_stitching_frames_parameters[shot_no][frame_no]

        if shot_no in self.db_stitching_frames_parameters_initial.keys():
            if frame_no in self.db_stitching_frames_parameters_initial[shot_no].keys():
                return self.db_stitching_frames_parameters_initial[shot_no][frame_no]

        return self.get_shot_stitching_parameters(shot_no=shot_no)


    def set_frame_stitching_parameters(self, shot_no, frame_no, parameters):
        """Set new parameters for this shot
        """
        if shot_no not in self.db_stitching_frames_parameters.keys():
            self.db_stitching_frames_parameters[shot_no] = dict()
        self.db_stitching_frames_parameters[shot_no][frame_no] = deepcopy(STITCHING_SHOT_PARAMETERS_DEFAULT)
        self.db_stitching_frames_parameters[shot_no][frame_no].update(parameters)
        self.is_stitching_db_modified = True


    def set_stitching_parameters(self, shot_no, frame_no, parameters):
        if parameters['is_shot']:
            # These parameters are the new ones for the shot
            self.set_shot_stitching_parameters(shot_no=shot_no, parameters=parameters)
        else:
            self.set_frame_stitching_parameters(shot_no=shot_no, frame_no=frame_no, parameters=parameters)
        self.is_stitching_db_modified = True



    # Crop to apply to the fgd image before merging fgd and bgd images
    def get_shot_stitching_fgd_crop(self, shot_no):
        for db_tmp in [self.db_stitching_shots_fgd_crop,
                        self.db_stitching_shots_fgd_crop_initial]:
            if shot_no in db_tmp.keys():
                return db_tmp[shot_no]
        return [0, 0, 0, 0]

    def set_shot_stitching_fgd_crop(self, shot_no, coordinates):
        self.db_stitching_shots_fgd_crop[shot_no] = coordinates
        self.is_stitching_db_modified = True

    def discard_shot_stitching_fgd_crop_modifications(self, shot_no):
        if shot_no in self.db_stitching_shots_fgd_crop.keys():
            del self.db_stitching_shots_fgd_crop[shot_no]
        self.is_stitching_db_modified = True




    # Stabilization parameters
    def get_shot_stabilize_parameters(self, shot_no, frame_no=-1, initial=False):
        """ Return the parameters used for the stabilization
        """
        # print("get_shot_stabilize_parameters: shot no. %d, frame no. %d" % (shot_no, frame_no))
        # pprint(self.db_stabilize_shots_parameters)

        if shot_no in self.db_stabilize_shots_parameters.keys() and not initial:
            # print("found in modified")
            parameters = self.db_stabilize_shots_parameters[shot_no]
        elif shot_no in self.db_stabilize_shots_parameters_initial.keys():
            # print("found in initial")
            parameters = self.db_stabilize_shots_parameters_initial[shot_no]
        else:
            # print("Error, no stabilization defined for this shot")
            return deepcopy(STABILIZATION_SHOT_PARAMETERS_DEFAULT)

        if frame_no == -1:
            return parameters

        # A shot may contains multiple shots; this dict contains a list of segments
        for segment in parameters:
            if segment['start'] <= frame_no < segment['end']:
                return segment
        # print("segment not found for %d" % (frame_no))
        return deepcopy(STABILIZATION_SHOT_PARAMETERS_DEFAULT)


    def set_shot_stabilize_parameters(self, shot_no, shot_parameters):
        if type(shot_parameters) is dict:
            self.db_stabilize_shots_parameters[shot_no][0].update(shot_parameters)
        else:
            self.db_stabilize_shots_parameters[shot_no] = deepcopy(shot_parameters)
        self.is_stabilize_db_modified = True


    def reset_shot_stabilize_parameters(self, shot_no):
        print("reset shot stabilization parameters")
        if shot_no in self.db_stabilize_shots_parameters.keys():
            del self.db_stabilize_shots_parameters[shot_no]
        self.flush_frames_stabilize(shot_no)



    # Stabilization values for each frame
    def get_frame_stabilize(self, shot_no, frame_no):
        for db_tmp in [self.db_stabilize_frames,
                        self.db_stabilize_frames_initial]:
            if shot_no in db_tmp.keys() and frame_no in db_tmp[shot_no].keys():
                return db_tmp[shot_no][frame_no]
        return None


    def set_frame_stabilize(self, shot_no, frame_no, transformation):
        db_modified = self.db_stabilize_frames
        if shot_no not in db_modified.keys():
            db_modified[shot_no] = dict()
        db_modified[shot_no][frame_no] = transformation
        self.is_stabilize_db_modified = True


    def flush_frames_stabilize(self, shot_no):
        print("flush_frames_stabilize")
        db_modified = self.db_stabilize_frames
        if shot_no in db_modified.keys():
            del db_modified[shot_no]




    # Crop to apply after stabilization/image stitching
    def get_shot_st_geometry(self, shot_no):
        for db_tmp in [self.db_st_geometry,
                        self.db_st_geometry_initial]:
            if shot_no in db_tmp.keys():
                return db_tmp[shot_no]
        return [0, 0, 0, 0]

    def set_shot_st_geometry(self, shot_no, geometry):
        self.db_st_geometryp[shot_no] = geometry
        self.is_geometry_db_modified = True

    def discard_shot_st_geometry(self, shot_no):
        if shot_no in self.db_st_geometry.keys():
            del self.db_st_geometry[shot_no]
        self.is_geometry_db_modified = True



    # Curve to apply to bgd before merging bgd and fgd images
    #---------------------------------------------------------------------------
    def parse_stitching_curves_database(self, k_ep):
        # Create 2 db, one for the initial, the second for modified curves
        self.db_stitching_curves_initial = parse_stitching_curves_database(
            self.global_database, k_ep=k_ep)
        self.db_stitching_curves = dict()


    def reload_stitching_curves_databse(self, k_ep):
        # Reload the database but keep the modified ones
        self.db_stitching_curves_initial = parse_stitching_curves_database(
            self.global_database, k_ep=k_ep)


    def get_stitching_curves_names(self) -> dict:
        names = list(self.db_stitching_curves_initial.keys())
        names += list(self.db_stitching_curves.keys())
        names_sorted = sorted(list(dict.fromkeys(names)))
        return {'all':names_sorted, 'modified': self.db_stitching_curves.keys()}


    def discard_stitching_curves_modifications(self, k_curves):
        if k_curves in self.db_stitching_curves.keys():
            log.info("remove the stitching curves from modified db [%s]" % k_curves)
            del self.db_stitching_curves[k_curves]
        else:
            log.info("[%s] has not been modified, cannot remove it" % k_curves)


    def get_stitching_curves(self, k_curves):
        # Return a dict of k_curves and (Curve, lut) for each channel
        if (k_curves not in self.db_stitching_curves_initial.keys()
            and k_curves not in self.db_stitching_curves.keys()):
            print("get_stitching_curves: [%s] is not in modified/initial db" % (k_curves))
            return STITCHING_CURVES_DEFAULT

        if k_curves in self.db_stitching_curves.keys():
            print("get_stitching_curves: %s: modified" % (k_curves))
            curves = self.db_stitching_curves[k_curves]

        elif k_curves in self.db_stitching_curves_initial.keys():
            print("get_stitching_curves: %s: initial" % (k_curves))
            curves = self.db_stitching_curves_initial[k_curves]

        if curves['lut'] is None:
            # Calculate lut from channels
            curves['lut'] = dict()
            for k_c in ['r', 'g', 'b']:
                curve = Curve()
                curve.remove_all_points()
                for p in curves['points'][k_c]:
                    curve.add_point(p[0], p[1])
                curves['lut'][k_c] = calculate_lut_for_bgd(curve=curve)
        return curves


    def modify_stitching_curves(self, curves:dict):
        k_curves = curves['k_curves']
        if k_curves != '':
            self.db_stitching_curves[k_curves] = deepcopy(curves)
            self.is_stitching_curves_db_modified = True


    def select_shot_stitching_curves(self, shot_no, k_curves):
        if shot_no not in self.db_stitching_shots_curves.keys():
            self.db_stitching_shots_curves[shot_no] = dict()

        log.info("select_shot_stitching_curves: shot_no. %d, k_curves=%s" % (shot_no, k_curves))
        self.db_stitching_shots_curves[shot_no] = self.get_stitching_curves(k_curves)


    def set_shot_stitching_curves_as_initial(self, shot_no):
        # Move from modified to initial db
        if shot_no in self.db_stitching_shots_curves.keys():
            self.db_stitching_shots_curves_initial[shot_no] = deepcopy(self.db_stitching_shots_curves[shot_no])
            del self.db_stitching_shots_curves[shot_no]


    def reset_shot_stitching_curves_selection(self, shot_no):
        if shot_no in self.db_stitching_shots_curves.keys():
            del self.db_stitching_shots_curves[shot_no]


    def get_shot_stitching_curves(self, shot_no):
        print("get_shot_stitching_curves for shot_no: %d" % (shot_no))
        if shot_no in self.db_stitching_shots_curves.keys():
            shot = self.db_stitching_shots_curves[shot_no]
        elif shot_no in self.db_stitching_shots_curves_initial.keys():
            shot = self.db_stitching_shots_curves_initial[shot_no]
        else:
            print("\t-> None")
            return None

        if shot is None:
            print("\t-> removed from initial")
            return None

        k_curves = shot['k_curves']
        if k_curves != '':
            # Get the curve from the global database
            print("\t-> %s (get_stitching_curves)" % (k_curves))
            return self.get_stitching_curves(k_curves)

        points = shot['points']
        if points is not None:
            print("\t-> %s" % (k_curves))
            return {
                'k_curves': k_curves,
                'points': points,
                'lut': shot['lut'],
            }
        print("\t-> None")
        return None

    def get_modified_shot_stitching_curves(self):
        return self.db_stitching_shots_curves

    def set_shot_stitching_curves(self, shot_no, curves_dict):
        # curves_dict:
        #     'k_curves' : curve name
        #     'points': dict of Curves objects for each r,g,b channel
        # if k_curve == '', this means that the curve jas not yet been "saved as"
        if shot_no not in self.db_stitching_shots_curves.keys():
            self.db_stitching_shots_curves[shot_no] = dict()

        # if 'curves' not in self.db_stitching_shots_curves[shot_no].keys():
        #     # Create a new curve for this shot
        #     self.db_stitching_shots_curves[shot_no] = deepcopy(STITCHING_CURVES_DEFAULT)

        print("set_shot_stitching_curves")
        # pprint(curves_dict)

        self.db_stitching_shots_curves[shot_no] = {
            'k_curves': curves_dict['k_curves'],
            'points': curves_dict['points'],
            'lut': curves_dict['lut']
        }
        self.is_stitching_db_modified = True

        if curves_dict['k_curves'] != '':
            self.modify_stitching_curves(curves_dict)
        else:
            print("no selected curves")


    def remove_shot_stitching_curves(self, shot_no):
        # Remove the curves of this shot
        print("remove_shot_stitching_curves: %d" % (shot_no))
        print(self.db_stitching_shots_curves_initial.keys())
        print("---")
        print(self.db_stitching_shots_curves.keys())
        print("")
        if shot_no in self.db_stitching_shots_curves.keys():
            if shot_no in self.db_stitching_shots_curves_initial.keys():
                # Force to none to overwrite the initial curves
                # del self.db_stitching_shots_curves[shot_no]
                # self.db_stitching_shots_curves[shot_no] = {'k_curves': ''}
                self.db_stitching_shots_curves[shot_no] = None
                log.info("Force to none to overwrite the initial curves")
            else:
                del self.db_stitching_shots_curves[shot_no]
        elif shot_no in self.db_stitching_shots_curves_initial.keys():
                # Force to none to overwrite the initial curves
                self.db_stitching_shots_curves[shot_no] = None
                log.info("Force to none to overwrite the initial curves")


    def is_db_modified(self, type:str=''):
        if type == 'curves':
            return self.is_curves_db_modified
        elif type == 'shot_selection':
            return self.is_curves_selection_db_modified
        elif type == 'replace':
            return self.is_replace_db_modified
        elif type == 'geometry':
            return self.is_geometry_db_modified
        elif type == 'stitching':
            return self.is_stabilize_db_modified
        elif type == 'stabilization':
            return self.is_stitching_db_modified
        elif type == 'stitching_curves':
            return self.is_stitching_curves_db_modified


        return (self.is_curves_db_modified
            or self.is_curves_selection_db_modified
            or self.is_replace_db_modified
            or self.is_geometry_db_modified
            or self.is_stabilize_db_modified
            or self.is_stitching_db_modified
            or self.is_stitching_curves_db_modified)



    def save_curves_selection_database(self, shots, k_ed, k_ep, k_part, shot_no=-1):
        if not self.is_curves_selection_db_modified:
            return True
        log.info("save shot curves database")

        db = self.global_database

        # Open configuration file
        if k_part in K_GENERIQUES:
            filepath = os.path.join(db['common']['directories']['config'], k_part, "%s_curves.ini" % (k_part))
        else:
            filepath = os.path.join(db['common']['directories']['config'], k_ep, "%s_curves.ini" % (k_ep))
        if filepath.startswith("~/"):
            filepath = os.path.join(PosixPath(Path.home()), filepath[2:])

        print("save_curves_selection_database: %s" % (filepath))

        # Parse the file
        if os.path.exists(filepath):
            config_curves = configparser.ConfigParser()
            config_curves.read(filepath)
        else:
            config_curves = configparser.ConfigParser({}, collections.OrderedDict)


        if shot_no == -1:
            # Save all shots:
            for k_ed_tmp in self.db_curves_selection.keys():
                for k_ep_tmp in self.db_curves_selection[k_ed_tmp].keys():
                    for k_part_tmp in self.db_curves_selection[k_ed_tmp][k_ep_tmp].keys():
                        for shot_no, shot in self.db_curves_selection[k_ed_tmp][k_ep_tmp][k_part_tmp].items():
                            if 'k_curves' not in shot.keys() or shot['k_curves'] == '':
                                # These curves are not saved in the database (=error)
                                # we consider that the curves selection cannot be removed
                                # TODO
                                print("error: these curves have not been saved")
                                continue

                            k_section = '%s.%s.%s' % (k_ed_tmp, k_ep_tmp, k_part_tmp)
                            shot_start_str = str(shots[shot_no]['start'])
                            try:
                                config_curves.set(k_section, shot_start_str, shot['k_curves'])
                            except:
                                config_curves[k_section] = dict()
                                config_curves.set(k_section, shot_start_str, shot['k_curves'])
                            shot['k_curves'] = -1
        else:
            shot = self.db_curves_selection[k_ed][k_ep][k_part][shot_no]
            if 'k_curves' not in shot.keys() or shot['k_curves'] == '':
                # These curves are not saved in the database (=error)
                # we consider that the curves selection cannot be removed
                # TODO
                print("error: these curves have not been saved")

            k_section = '%s.%s.%s' % (k_ed, k_ep, k_part)
            shot_start_str = str(shots[shot_no]['start'])
            try:
                config_curves.set(k_section, shot_start_str, shot['k_curves'])
            except:
                config_curves[k_section] = dict()
                config_curves.set(k_section, shot_start_str, shot['k_curves'])
            del self.db_curves_selection[k_ed][k_ep][k_part][shot_no]


        # Write to the database
        with open(filepath, 'w') as config_file:
            config_curves.write(config_file)

        # Clean the database and consider as not modified only if all keys have been saved
        # TODO: replace by a nested dict
        k_ed_keys = list(self.db_curves_selection.keys())
        for k_ed_tmp in k_ed_keys:
            k_ep_keys = list(self.db_curves_selection[k_ed_tmp].keys())
            for k_ep_tmp in k_ep_keys:
                k_parts_keys = list(self.db_curves_selection[k_ed_tmp][k_ep_tmp].keys())
                for k_part_tmp in k_parts_keys:
                    k_shot_nos = list(self.db_curves_selection[k_ed_tmp][k_ep_tmp][k_part_tmp].keys())
                    for shot_no in k_shot_nos:
                        shot = self.db_curves_selection[k_ed_tmp][k_ep_tmp][k_part_tmp][shot_no]
                        if shot['k_curves'] == -1:
                            del self.db_curves_selection[k_ed_tmp][k_ep_tmp][k_part_tmp][shot_no]

                    if len(self.db_curves_selection[k_ed_tmp][k_ep_tmp][k_part_tmp].keys()) == 0:
                        del self.db_curves_selection[k_ed_tmp][k_ep_tmp][k_part_tmp]

                if len(self.db_curves_selection[k_ed_tmp][k_ep_tmp].keys()) == 0:
                    del self.db_curves_selection[k_ed_tmp][k_ep_tmp]

            if len(self.db_curves_selection[k_ed_tmp].keys()) == 0:
                del self.db_curves_selection[k_ed_tmp]

        if len(self.db_curves_selection.keys()) == 0:
            self.is_curves_selection_db_modified = False
        else:
            print("all selection have not been saved: ")
            pprint(self.db_curves_selection)

        return True



    def save_geometry_database(self, k_ep, k_part):
        if not self.is_geometry_db_modified:
            return True

        log.info("Save part_geometry")
        db = self.global_database

        # Open configuration file
        if k_part in K_GENERIQUES:
            filepath = os.path.join(db['common']['directories']['config'], k_part, "%s_geometry.ini" % (k_part))
        else:
            filepath = os.path.join(db['common']['directories']['config'], k_ep, "%s_geometry.ini" % (k_ep))
        if filepath.startswith("~/"):
            filepath = os.path.join(PosixPath(Path.home()), filepath[2:])

        # Parse the file
        if os.path.exists(filepath):
            config_geometry_coordinates = configparser.ConfigParser()
            config_geometry_coordinates.read(filepath)
        else:
            config_geometry_coordinates = configparser.ConfigParser({}, collections.OrderedDict)
            # config_geometry_coordinates[k_part] = {}

        if k_part in K_GENERIQUES:
            k_ed_src = db[k_part]['common']['video']['reference']['k_ed']
            k_ep_src = db[k_part]['common']['video']['reference']['k_ep']
            # print(k_ed_src)
            # print(k_ep_src)
            # print(k_part)
            coordinates = self.get_crop_coordinates(k_ed_src, k_part)
            k_section = '%s.%s.%s' % (k_ed_src, k_ep_src, k_part)
        else:
            k_ed_src = db[k_ep]['common']['video']['reference']['k_ed']
            coordinates = self.get_crop_coordinates(k_ed_src, k_part)
            k_section = '%s.%s.%s' % (k_ed_src, k_ep, k_part)

        # Set the coordinates
        if not config_geometry_coordinates.has_section(k_section):
            config_geometry_coordinates[k_section] = dict()
        config_geometry_coordinates.set(k_section, 'crop', ','.join([str(i) for i in coordinates]))

        # Remove unused sections and sort
        for k_section in config_geometry_coordinates.sections():
            if len(config_geometry_coordinates[k_section]) == 0:
                config_geometry_coordinates.remove_section(k_section)

            # Sort the section
            config_geometry_coordinates[k_section] = collections.OrderedDict(sorted(config_geometry_coordinates[k_section].items(), key=lambda x: x[0]))


        # Write to the database
        with open(filepath, 'w') as config_file:
            config_geometry_coordinates.write(config_file)

        self.is_geometry_db_modified = False
        return True



    def save_replace_database(self, k_ep, k_part, shots):
        if not self.is_replace_db_modified:
            return True

        log.info("save replace database %s:%s" % (k_ep, k_part))
        db = self.global_database

        for k_shot_no, shot in shots.items():
            # print("***********************************************")
            # pprint(shot)

            # Select the shot used for the generation
            if 'src' in shot.keys() and shot['src']['use']:
                k_ed_src = shot['src']['k_ed']
                k_ep_src = shot['src']['k_ep']
                k_part_src = get_k_part_from_frame_no(db, k_ed=k_ed_src, k_ep=k_ep_src, frame_no=shot['src']['start'])
                shot_src = get_shot_from_frame_no_new(db,
                    shot['src']['start'], k_ed=k_ed_src, k_ep=k_ep_src, k_part=k_part_src)
                if 'count' not in shot['src'].keys():
                    shot['src']['count'] = shot_src['count']
                if shot_src is None:
                    sys.exit()
            else:
                k_ed_src = db[k_ep]['common']['video']['reference']['k_ed']
                k_ep_src = k_ep
                k_part_src = k_part
                shot_src = shot


            # Use the config file
            if k_part in K_GENERIQUES:
                k_ed_src = db[k_part]['common']['video']['reference']['k_ed']
                k_part_src = k_part


            # Open configuration file
            if k_part in K_GENERIQUES:
                filepath = os.path.join(db['common']['directories']['config'], k_part_src, "%s_replace.ini" % (k_part))
            else:
                filepath = os.path.join(db['common']['directories']['config'], k_ep_src, "%s_replace.ini" % (k_ep))
            if filepath.startswith("~/"):
                filepath = os.path.join(PosixPath(Path.home()), filepath[2:])


            # Parse the file
            if os.path.exists(filepath):
                config_replace = configparser.ConfigParser(dict_type=collections.OrderedDict)
                config_replace.read(filepath)
            else:
                config_replace = configparser.ConfigParser({}, collections.OrderedDict)


            # Update the config file
            k_section = '%s.%s.%s' % (k_ed_src, k_ep_src, k_part_src)

            if not config_replace.has_section(k_section):
                config_replace[k_section] = dict()

            for f_no, f_no_new in self.replaced_frames[k_shot_no].items():
                f_no_str = str(f_no)
                if f_no_new == -1 and config_replace.has_option(k_section, f_no_str):
                    del config_replace[k_section][f_no_str]
                else:
                    config_replace.set(k_section, f_no_str, str(f_no_new))

            # Remove unused sections and sort
            for k_section in config_replace.sections():
                if len(config_replace[k_section]) == 0:
                    config_replace.remove_section(k_section)

                # Sort the section
                config_replace[k_section] = collections.OrderedDict(sorted(config_replace[k_section].items(), key=lambda x: x[0]))


            # Write to the database
            with open(filepath, 'w') as config_file:
                config_replace.write(config_file)

        self.is_replace_db_modified = False
        return True



    def save_stabilize_database(self, k_ep, k_part, shots):
        print("save_stabilize_database")
        if not self.is_stabilize_db_modified:
            return True

        log.info("save stabilization database %s:%s" % (k_ep, k_part))
        db = self.global_database

        for shot_no, shot in shots.items():
            # print("***********************************************")
            # pprint(shot)

            # Select the shot used for the generation
            if 'src' in shot.keys() and shot['src']['use']:
                k_ed_src = shot['src']['k_ed']
                k_ep_src = shot['src']['k_ep']
                k_part_src = get_k_part_from_frame_no(db, k_ed=k_ed_src, k_ep=k_ep_src, frame_no=shot['src']['start'])
                shot_src = get_shot_from_frame_no_new(db,
                    shot['src']['start'], k_ed=k_ed_src, k_ep=k_ep_src, k_part=k_part_src)
                if 'count' not in shot['src'].keys():
                    shot['src']['count'] = shot_src['count']
                if shot_src is None:
                    sys.exit()
            else:
                k_ed_src = db[k_ep]['common']['video']['reference']['k_ed']
                k_ep_src = k_ep
                k_part_src = k_part
                shot_src = shot


            # Use the config file
            if k_part in K_GENERIQUES:
                k_ed_src = db[k_part]['common']['video']['reference']['k_ed']
                k_part_src = k_part


            # Add parameters
            if shot_no not in self.db_stabilize_shots_parameters.keys():
                log.info("This shot has not been modified, discard save")
                print(("This shot has not been modified, discard save"))
                self.is_stabilize_db_modified = False
                return True


            # Open configuration file
            if k_part in K_GENERIQUES:
                filepath = os.path.join(db['common']['directories']['config'], k_part_src, "%s_stabilize.ini" % (k_part))
            else:
                filepath = os.path.join(db['common']['directories']['config'], k_ep_src, "%s_stabilize.ini" % (k_ep))
            if filepath.startswith("~/"):
                filepath = os.path.join(PosixPath(Path.home()), filepath[2:])


            # Parse the file
            if os.path.exists(filepath):
                config_stabilize = configparser.ConfigParser(dict_type=collections.OrderedDict)
                config_stabilize.read(filepath)
            else:
                config_stabilize = configparser.ConfigParser({}, collections.OrderedDict)

            # pprint(self.db_stabilize_frames)

            # Update the config file
            k_section = '%s.%s.%s' % (k_ed_src, k_ep_src, k_part_src)

            # Create a section if it does not exist
            if not config_stabilize.has_section(k_section):
                config_stabilize[k_section] = dict()


            parameters = self.db_stabilize_shots_parameters[shot_no]
            key_str = "%d_parameters" % (shot['start'])

            if parameters is None:
                print("cannot add parameters")
                pprint(parameters)
                # No parameters or default for this shot
                key_str = "%d_parameters" % (shot['start'])
                if config_stabilize.has_option(k_section, key_str):
                    del config_stabilize[k_section, key_str]

                for f_no in range(shot['start'], shot['start'] + shot['count']):
                    if config_stabilize.has_option(k_section, str(f_no)):
                        del config_stabilize[k_section, str(f_no)]
            else:
                # Parameters are specified,
                parameters_str = ""
                for p in parameters:
                    if p['is_enabled'] and p['is_processed']:
                        # Calculation has already been done
                        parameters_str += "\nsegment=%d:%d:%d, ref_points=%d:%.2f:%d:%d, delta_interval=%s" % (
                            p['start'],
                            p['end'],
                            p['ref'],
                            p['max_corners'],
                            p['quality_level'],
                            p['min_distance'],
                            p['block_size'],
                            ':'.join(map(lambda x: "%d" % (x), p['delta_interval']))
                        )
                    else:
                        print("error: calculations have not been done, discard")
                        self.is_stabilize_db_modified = False
                        return False
                config_stabilize.set(k_section, key_str, parameters_str)

            # Add dx, dy for each frame
            for f_no in range(shot['start'], shot['start'] + shot['count']):
                dx_dy_array = self.get_frame_stabilize(shot_no, frame_no=f_no)
                if dx_dy_array is not None:
                    transformation_str = "%f:%f" % (dx_dy_array[0], dx_dy_array[1])
                    config_stabilize.set(k_section, str(f_no), transformation_str)
                else:
                    if config_stabilize.has_option(k_section, str(f_no)):
                        config_stabilize.remove_option(k_section, str(f_no))

            if False:
                # Remove unused sections and sort
                for k_section in config_stabilize.sections():
                    if len(config_stabilize[k_section]) == 0:
                        config_stabilize.remove_section(k_section)

            # Sort the section
            config_stabilize[k_section] = collections.OrderedDict(sorted(config_stabilize[k_section].items(), key=lambda x: x[0]))


            # Write to the database
            with open(filepath, 'w') as config_file:
                config_stabilize.write(config_file)

        self.is_stabilize_db_modified = False
        return True



    def save_replace_database(self):
        if not self.is_replace_db_modified:
            return True

        log.info("save replace database")
        db = self.global_database

        for k_ed in self.db_replaced_frames.keys():
            for k_ep in self.db_replaced_frames[k_ed].keys():
                for k_part in self.db_replaced_frames[k_ed][k_ep].keys():
                    db_replace_frames_modified = self.db_replaced_frames[k_ed][k_ep][k_part]

                    if k_part in K_GENERIQUES:
                        # Open configuration file
                        if k_part in K_GENERIQUES:
                            filepath = os.path.join(db['common']['directories']['config'], k_part, "%s_replace.ini" % (k_part))
                        else:
                            filepath = os.path.join(db['common']['directories']['config'], k_ep, "%s_replace.ini" % (k_ep))
                        if filepath.startswith("~/"):
                            filepath = os.path.join(PosixPath(Path.home()), filepath[2:])

                    # Parse the file
                    if os.path.exists(filepath):
                        config_replace = configparser.ConfigParser(dict_type=collections.OrderedDict)
                        config_replace.read(filepath)
                    else:
                        config_replace = configparser.ConfigParser({}, collections.OrderedDict)

                    # Update the config file, select section
                    k_section = '%s.%s.%s' % (k_ed, k_ep, k_part)

                    if not config_replace.has_section(k_section):
                        config_replace[k_section] = dict()

                    # Update the values
                    for frame_no, new_frame_no in db_replace_frames_modified.items():
                        if new_frame_no == -1:
                            # Remove from the config file
                            if config_replace.has_option(k_section, str(frame_no)):
                                config_replace.remove_option(k_section, str(frame_no))
                        else:
                            # Set the new value
                            config_replace.set(k_section, str(frame_no), str(new_frame_no))

                    # Write to the database
                    with open(filepath, 'w') as config_file:
                        config_replace.write(config_file)

        self.is_replace_db_modified = False
        return True



    def save_stitching_database(self, k_ep, k_part, shots):
        if not self.is_stitching_db_modified:
            return True

        log.info("save stitching database %s:%s" % (k_ep, k_part))
        db = self.global_database

        for k_shot_no, shot in shots.items():
            # print("***********************************************")
            # pprint(shot)

            # Select the shot used for the generation
            if 'src' in shot.keys() and shot['src']['use']:
                k_ed_src = shot['src']['k_ed']
                k_ep_src = shot['src']['k_ep']
                k_part_src = get_k_part_from_frame_no(db, k_ed=k_ed_src, k_ep=k_ep_src, frame_no=shot['src']['start'])
                shot_src = get_shot_from_frame_no_new(db,
                    shot['src']['start'], k_ed=k_ed_src, k_ep=k_ep_src, k_part=k_part_src)
                if 'count' not in shot['src'].keys():
                    shot['src']['count'] = shot_src['count']
                if shot_src is None:
                    sys.exit()
            else:
                k_ed_src = db[k_ep]['common']['video']['reference']['k_ed']
                k_ep_src = k_ep
                k_part_src = k_part
                shot_src = shot


            # Use the config file
            if k_part in K_GENERIQUES:
                k_ed_src = db[k_part]['common']['video']['reference']['k_ed']
                k_part_src = k_part


            # Open configuration file
            if k_part in K_GENERIQUES:
                filepath = os.path.join(db['common']['directories']['config'], k_part_src, "%s_stitching.ini" % (k_part))
            else:
                filepath = os.path.join(db['common']['directories']['config'], k_ep_src, "%s_stitching.ini" % (k_ep))
            if filepath.startswith("~/"):
                filepath = os.path.join(PosixPath(Path.home()), filepath[2:])


            # Parse the file
            if os.path.exists(filepath):
                config_stitching = configparser.ConfigParser(dict_type=collections.OrderedDict)
                config_stitching.read(filepath)
            else:
                config_stitching = configparser.ConfigParser({}, collections.OrderedDict)

            # Update the config file
            k_section = '%s.%s.%s' % (k_ed_src, k_ep_src, k_part_src)

            if not config_stitching.has_section(k_section):
                config_stitching[k_section] = dict()

            # Add parameters
            parameters = self.get_shot_stitching_parameters(k_shot_no)
            key_str = "%d_parameters" % (shot['start'])
            if parameters is None:
                print("cannot add parameters")
                pprint(parameters)
                # No parameters or default for this shot
                key_str = "%d_parameters" % (shot['start'])
                if config_stitching.has_option(k_section, key_str):
                    del config_stitching[k_section, key_str]

                for f_no in range(shot['start'], shot['start'] + shot['count']):
                    if config_stitching.has_option(k_section, str(f_no)):
                        del config_stitching[k_section, str(f_no)]
            else:
                # Parameters are specified
                value_str = "en=%s, roi=%s, sharpen=%s:%s, extractor=%s, matching=%s, method=%s, reproj_threshold=%d, knn_ratio=%.02f" % (
                    'true' if parameters['is_enabled'] else 'false',
                    ':'.join(map(lambda x: "%d" % (x), parameters['roi'])),
                    np.format_float_positional(parameters['sharpen'][0]),
                    np.format_float_positional(parameters['sharpen'][1]),
                    parameters['extractor'],
                    parameters['matching'],
                    parameters['method'],
                    parameters['reproj_threshold'],
                    parameters['knn_ratio'])
                config_stitching.set(k_section, key_str, value_str)


            # Add crop areas applied on fgd image
            crop_values = self.get_shot_stitching_crop(k_shot_no)
            key_str = "%d_crop" % (shot['start'])
            value_str = "fgd=%s, shot=%s" % (
                ':'.join(map(lambda x: "%d" % (x), crop_values['fgd'])),
                ':'.join(map(lambda x: "%d" % (x), crop_values['shot'])))
            config_stitching.set(k_section, key_str, value_str)


            # Add m for each frame
            for f_no in range(shot['start'], shot['start'] + shot['count']):
                m = self.get_frame_stitching_transformation(k_shot_no, frame_no=f_no)
                if m is not None:
                    matrix_str = "m=" + np.array2string(m.reshape(9), separator=',')[1:-1]
                    matrix_str = matrix_str.replace('\t', '').replace('\n', '').replace(' ', '')
                    config_stitching.set(k_section, str(f_no), matrix_str)

            if False:
                # Remove unused sections and sort
                for k_section in config_stitching.sections():
                    if len(config_stitching[k_section]) == 0:
                        config_stitching.remove_section(k_section)

                    # Sort the section
                    config_stitching[k_section] = collections.OrderedDict(sorted(config_stitching[k_section].items(), key=lambda x: x[0]))


            # Write to the database
            with open(filepath, 'w') as config_file:
                config_stitching.write(config_file)

        self.is_stitching_db_modified = False
        return True



    def save_geometry_database(self, k_ed, k_ep, k_part):
        if not self.is_geometry_db_modified:
            return True

        log.info("save geometry database %s:%s" % (k_ep, k_part))
        db = self.global_database

        if k_part in K_GENERIQUES:
            # Open configuration file
            if k_part in K_GENERIQUES:
                filepath = os.path.join(db['common']['directories']['config'], k_part, "%s_geometry.ini" % (k_part))
            else:
                filepath = os.path.join(db['common']['directories']['config'], k_ep, "%s_geometry.ini" % (k_ep))
            if filepath.startswith("~/"):
                filepath = os.path.join(PosixPath(Path.home()), filepath[2:])


        # Parse the file
        if os.path.exists(filepath):
            config_geometry = configparser.ConfigParser(dict_type=collections.OrderedDict)
            config_geometry.read(filepath)
        else:
            config_geometry = configparser.ConfigParser({}, collections.OrderedDict)

        # Update the config file, select section
        k_section = '%s.%s.%s' % (k_ed, k_ep, k_part)

        if not config_geometry.has_section(k_section):
            config_geometry[k_section] = dict()

        # Update the values
        if (k_ed in self.db_part_geometry.keys()
        and k_part in self.db_part_geometry[k_ed].keys()):
            config_geometry.set(k_section, 'crop',
                ':'.join(map(lambda x: "%d" % (x), self.db_part_geometry[k_ed][k_part]['crop'])))

        # TODO: Add resize of shots
        # TODO: Add values coming from st geometry

        # Write to the database
        with open(filepath, 'w') as config_file:
            config_geometry.write(config_file)

        self.is_geometry_db_modified = False
        return True


    def event_save_database(self, curves:dict):
        log.info("global mode: save bgd curve as %s for image %s" % (curves['k_curves'], curves['image_name']))

        k_curves = curves['k_curves']
        # Save curves
        if curves['points'] is not None and k_curves != '':
            self.model_curves.save_stitching_curves(k_curves, curves['points'])

        # Modify shot: use the frame to find the shot no.
        frame = self.framelist.get_frame(curves['image_name'])

        # Save the database, use the frame struct to save the
        # correspondant edition/episode/part
        self.model_curves.save_curves_database(k_ep=frame['k_ep'], k_part=frame['k_part'])
        frame['k_curves_initial'] = k_curves

        # Send a list of modified shots
        self.signal_refresh_modified_shots.emit(self.model_curves.get_modified_shots())

        self.signal_refresh_frame_properties.emit(frame)
