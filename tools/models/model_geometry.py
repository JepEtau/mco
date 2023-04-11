# -*- coding: utf-8 -*-
import sys
sys.path.append('../scripts')

from copy import deepcopy
import os
import os.path
import configparser
from pathlib import Path
from pathlib import PosixPath
import collections


from pprint import pprint
from logger import log

from utils.nested_dict import (
    nested_dict_clean,
    nested_dict_set,
)
from utils.pretty_print import *
from parsers.parser_geometry import (
    get_initial_target_geometry,
    get_initial_default_shot_geometry,
    get_initial_shot_geometry,
)
from filters.utils import FINAL_FRAME_WIDTH

class Model_geometry():

    def __init__(self):
        # Use a single database to store the modified values
        # Thus, no history is possible with this implementation
        self.db_target_geometry_initial = dict()
        self.db_target_geometry = dict()

        self.db_default_shot_geometry_initial = dict()
        self.db_default_shot_geometry = dict()

        self.db_shot_geometry_initial = dict()
        self.db_shot_geometry = dict()

        self.is_geometry_db_modified = False


    def initialize_db_for_geometry(self, db, k_ep, k_part):
        # This function is used by the video editor
        # which uses the consolidated shots

        # Target geometry
        if k_part in ['g_asuivre', 'g_reportage']:
            self.db_target_geometry_initial = get_initial_target_geometry(self.global_database,
                k_ep=k_ep, k_part=k_part[2:])
        else:
            self.db_target_geometry_initial = get_initial_target_geometry(self.global_database,
                k_ep=k_ep, k_part=k_part)
        self.db_target_geometry = dict()

        # Default shot geometry
        self.db_default_shot_geometry_initial = get_initial_default_shot_geometry(self.global_database, k_ep=k_ep, k_part=k_part)
        self.db_default_shot_geometry = dict()

        # Shot geometry
        self.db_shot_geometry_initial = get_initial_shot_geometry(self.global_database, k_ep=k_ep, k_part=k_part)
        self.db_shot_geometry = dict()

        if False:
            self.is_geometry_db_modified = False
            print_cyan("db_target_geometry_initial:")
            pprint(self.db_target_geometry_initial)
            print_cyan("db_default_shot_geometry_initial:")
            pprint(self.db_default_shot_geometry_initial)
            print_cyan("db_shot_geometry_initial:")
            pprint(self.db_shot_geometry_initial)
            sys.exit()



    # Target
    #---------------------------------------------------------------------------
    def get_target_geometry(self, k_ep, k_part):
        k_ep_target = 'ep00' if k_part in ['g_debut', 'g_fin'] else k_ep
        try: return self.db_target_geometry[k_ep_target][k_part]
        except:
            try: return self.db_target_geometry_initial[k_ep_target][k_part]
            except: pass
        # print_orange("target geometry not found in db")
        return {'w': FINAL_FRAME_WIDTH}


    def set_target_geometry(self, k_ep, k_part, geometry):
        k_ep_target = 'ep00' if k_part in ['g_debut', 'g_fin'] else k_ep
        nested_dict_set(self.db_target_geometry, geometry, k_ep_target, k_part)
        self.is_geometry_db_modified = True


    def discard_target_geometry_modifications(self, k_ep, k_part):
        k_ep_target = 'ep00' if k_part in ['g_debut', 'g_fin'] else k_ep
        log.info("discard_target_geometry_modifications")
        try:
            del self.db_target_geometry[k_ep_target][k_part]
        except:
            pass
        nested_dict_clean(self.db_target_geometry)
        self.is_geometry_db_modified = False




    # Default shot
    #---------------------------------------------------------------------------
    def get_default_shot_geometry(self, shot):
        k_ed = shot['k_ed']
        k_ep = shot['k_ep']
        k_part = shot['k_part']
        try:
            return self.db_default_shot_geometry[k_ed][k_ep][k_part]
        except:
            try: return self.db_default_shot_geometry_initial[k_ed][k_ep][k_part]
            except: pass
        # print_orange("default shot geometry not found in db")
        return None

    def set_default_shot_geometry(self, shot, geometry):
        k_ed = shot['k_ed']
        k_ep = shot['k_ep']
        k_part = shot['k_part']
        nested_dict_set(self.db_default_shot_geometry, geometry, k_ed, k_ep, k_part)
        self.is_geometry_db_modified = True


    def remove_default_shot_geometry(self, shot):
        k_ed = shot['k_ed']
        k_ep = shot['k_ep']
        k_part = shot['k_part']
        nested_dict_set(self.db_default_shot_geometry, None, k_ed, k_ep, k_part)
        self.is_geometry_db_modified = True



    def discard_default_shot_geometry_modifications(self, shot):
        log.info("discard_shot_geometry_modifications")
        k_ed = shot['k_ed']
        k_ep = shot['k_ep']
        k_part = shot['k_part']
        try: del self.db_default_shot_geometry[k_ed][k_ep][k_part]
        except: pass

        nested_dict_clean(self.db_default_shot_geometry)
        self.is_geometry_db_modified = False





    # Shot (custom)
    #---------------------------------------------------------------------------
    def get_shot_geometry(self, shot:dict):
        k_ed = shot['k_ed']
        k_ep = shot['k_ep']
        k_part = shot['k_part']
        shot_start = shot['start']
        try:
            return self.db_shot_geometry[k_ed][k_ep][k_part][shot_start]
        except:
            try:
                return self.db_shot_geometry_initial[k_ed][k_ep][k_part][shot_start]
            except:
                pass
        # print_orange("shot geometry not found in db")
        return None

    def set_shot_geometry(self, shot:dict, geometry:dict):
        k_ed = shot['k_ed']
        k_ep = shot['k_ep']
        k_part = shot['k_part']
        shot_start = shot['start']
        nested_dict_set(self.db_shot_geometry, geometry, k_ed, k_ep, k_part, shot_start)
        self.is_geometry_db_modified = True


    def remove_shot_geometry(self, shot:dict):
        k_ed = shot['k_ed']
        k_ep = shot['k_ep']
        k_part = shot['k_part']
        shot_start = shot['start']
        nested_dict_set(self.db_shot_geometry, None, k_ed, k_ep, k_part, shot_start)
        self.is_geometry_db_modified = True


    def discard_shot_geometry_modifications(self, shot:dict):
        log.info("discard_shot_geometry_modifications")
        k_ed = shot['k_ed']
        k_ep = shot['k_ep']
        k_part = shot['k_part']
        shot_start = shot['start']
        try: del self.db_shot_geometry[k_ed][k_ep][k_part][shot_start]
        except: pass

        nested_dict_clean(self.db_shot_geometry)
        self.is_geometry_db_modified = False




    def save_geometry_database(self, k_ed, k_ep, k_part, shot):
        # Save all modifications
        verbose = False

        if not self.is_geometry_db_modified:
            return True

        log.info("save geometry database %s:%s" % (k_ep, k_part))
        if verbose:
            print_lightgreen("\nSave geometry database: %s:%s:%s\n---------------------------------------" % (k_ed, k_ep, k_part))
        db = self.global_database

        # Open configuration file
        if k_part in ['g_debut', 'g_fin']:
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


        # Target
        if verbose:
            print_lightgreen("Save target geometry")
        for k_ep_src, ep_values in self.db_target_geometry.items():
            for k_part_src, part_values in ep_values.items():
                k_section = '%s' % (k_part_src)

                if not config_geometry.has_section(k_section):
                    config_geometry[k_section] = dict()
                if verbose:
                    print("\tk_section = %s" % (k_section))

                # Update the values
                try:
                    value_array = list()
                    try:
                        width = part_values['w']
                        value_array.append("width=%s" % (width))
                        nested_dict_set(self.db_target_geometry_initial, deepcopy(part_values),
                            k_ep_src, k_part_src)
                    except: pass

                    config_geometry.set(k_section, 'target', ', '.join(value_array))
                except: pass
        nested_dict_clean(self.db_target_geometry_initial)
        self.db_target_geometry.clear()
        if verbose:
            print_lightcyan("\tnew initial target geometry:")
            pprint(self.db_target_geometry_initial)
            print_lightcyan("\tnew modified target geometry:")
            pprint(self.db_target_geometry)


        # Default shot_geometry
        if verbose:
            print_lightgreen("Save default shot geometry")
            print_lightcyan("\tdefault shot geometry:")
            pprint(self.db_default_shot_geometry)
        for k_ed_src, ed_values in self.db_default_shot_geometry.items():
            for k_ep_src, ep_values in ed_values.items():
                for k_part_src, shot_geometry in ep_values.items():

                    k_section = '%s.%s.%s' % (k_ed_src, k_ep_src, k_part_src)
                    if not config_geometry.has_section(k_section):
                        config_geometry[k_section] = dict()
                    # print("k_section = %s" % (k_section))

                    if shot_geometry is None:
                        # Remove from database
                        try: del self.db_default_shot_geometry_initial[k_ed_src][k_ep_src][k_part_src]
                        except: pass

                        # Remove fro config file
                        try: config_geometry.remove_option(k_section, k_part_src)
                        except: pass

                        continue

                    # Update the values
                    try:
                        value_array = list()
                        try:
                            crop = shot_geometry['crop']
                            value_array.append("crop=%s" % (':'.join(map(lambda x: "%d" % (x), crop))))
                            nested_dict_set(self.db_default_shot_geometry_initial, deepcopy(crop),
                                k_ed_src, k_ep_src, k_part_src, 'crop')
                        except: pass

                        try:
                            keep_ratio = shot_geometry['keep_ratio']
                            value_array.append("keep_ratio=%s" % ('true' if keep_ratio else 'false'))
                            nested_dict_set(self.db_default_shot_geometry_initial, deepcopy(keep_ratio),
                                k_ed_src, k_ep_src, k_part_src, 'keep_ratio')
                        except: pass

                        try:
                            fit_to_width= shot_geometry['fit_to_width']
                            value_array.append("fit_to_width=%s" % ('true' if fit_to_width else 'false'))
                            nested_dict_set(self.db_default_shot_geometry_initial, deepcopy(fit_to_width),
                                k_ed_src, k_ep_src, k_part_src, 'fit_to_width')
                        except: pass

                        config_geometry.set(k_section, 'default', ', '.join(value_array))
                    except:
                        pass
        nested_dict_clean(self.db_default_shot_geometry_initial)
        self.db_default_shot_geometry.clear()
        if verbose:
            print_lightcyan("\tnew initial default shot geometry:")
            pprint(self.db_default_shot_geometry_initial)
            print_lightcyan("\tnew modified default shot geometry:")
            pprint(self.db_default_shot_geometry)




        # shot_geometry
        if verbose:
            print_lightgreen("Save  geometry")
            print_lightcyan("\tshot geometry:")
            pprint(self.db_shot_geometry)
        for k_ed_src, ed_values in self.db_shot_geometry.items():
            for k_ep_src, ep_values in ed_values.items():
                for k_part_src, frame_nos in ep_values.items():
                    for frame_no, shot_geometry in frame_nos.items():

                        k_section = '%s.%s.%s' % (k_ed_src, k_ep_src, k_part_src)
                        if not config_geometry.has_section(k_section):
                            config_geometry[k_section] = dict()

                        if verbose:
                            print("k_section:%s, frame_no:%d" % (k_section, frame_no))

                        if shot_geometry is None:
                            # Remove from database
                            try: del self.db_shot_geometry_initial[k_ed_src][k_ep_src][k_part_src][frame_no]
                            except: pass

                            # Remove from config file
                            try: config_geometry.remove_option(k_section, str(frame_no))
                            except: pass

                            continue

                        # Update the values
                        try:
                            value_array = list()
                            try:
                                crop = shot_geometry['crop']
                                value_array.append("crop=%s" % (':'.join(map(lambda x: "%d" % (x), crop))))
                                nested_dict_set(self.db_shot_geometry_initial, deepcopy(crop),
                                    k_ed_src, k_ep_src, k_part_src, frame_no, 'crop')
                            except: pass

                            try:
                                keep_ratio = shot_geometry['keep_ratio']
                                value_array.append("keep_ratio=%s" % ('true' if keep_ratio else 'false'))
                                nested_dict_set(self.db_shot_geometry_initial, deepcopy(keep_ratio),
                                    k_ed_src, k_ep_src, k_part_src, frame_no, 'keep_ratio')
                            except: pass

                            try:
                                fit_to_width= shot_geometry['fit_to_width']
                                value_array.append("fit_to_width=%s" % ('true' if fit_to_width else 'false'))
                                nested_dict_set(self.db_shot_geometry_initial, deepcopy(fit_to_width),
                                    k_ed_src, k_ep_src, k_part_src, frame_no, 'fit_to_width')
                            except: pass

                            config_geometry.set(k_section, str(frame_no), ', '.join(value_array))
                        except:
                            pass
        self.db_shot_geometry.clear()
        nested_dict_clean(self.db_shot_geometry_initial)
        if verbose:
            print_lightcyan("\tnew initial shot geometry:")
            pprint(self.db_shot_geometry_initial)
            print_lightcyan("\tnew modified shot geometry:")
            pprint(self.db_shot_geometry)


        # Write to the config file
        with open(filepath, 'w') as config_file:
            config_geometry.write(config_file)

        # Clean the dictonaries
        self.db_default_shot_geometry.clear()
        self.db_shot_geometry.clear()

        self.is_geometry_db_modified = False
        return True



