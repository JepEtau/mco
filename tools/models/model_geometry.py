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

from utils.common import (
    nested_dict_set,
)
from parsers.parser_geometry import (
    get_initial_part_geometry,
    get_initial_shot_geometry,
)


class Model_geometry():

    def __init__(self):
        # Use a single database to store the modified values
        # Thus, no history is possible with this implementation
        self.db_part_geometry_initial = dict()
        self.db_part_geometry = dict()

        self.db_shot_geometry_initial = dict()
        self.db_shot_geometry = dict()

        self.is_geometry_db_modified = False


    def initialize_db_for_geometry(self, db, k_ep, k_part):
        print("Model_geometry:initialize_db_for_geometry: get initial geometry")
        # This function is used by the video editor
        # which uses the consolidated shots
        self.db_part_geometry_initial = get_initial_part_geometry(self.global_database, k_ep='', k_part=k_part)
        self.db_part_geometry = dict()
        pprint(self.db_part_geometry_initial)

        self.db_shot_geometry_initial = get_initial_shot_geometry(self.global_database, k_ep='', k_part=k_part)
        self.db_shot_geometry = dict()

        pprint(self.db_shot_geometry_initial)



    # Final geometry for each part
    def get_part_geometry(self, k_ed, k_ep, k_part):
        # pprint(self.db_part_geometry_initial)
        try:
            return self.db_part_geometry[k_ed][k_ep][k_part]
        except:
            try:
                return self.db_part_geometry_initial[k_ed][k_ep][k_part]
            except:
                pass
        # print("get_part_geometry: %s:%s:%s" % (k_ed, k_ep, k_part))
        # print("-> not found")
        return {'crop': [0, 0, 0, 0]}


    def set_part_geometry(self, k_ed, k_ep, k_part, geometry):
        # print("set_part_geometry: %s:%s:%s" % (k_ed, k_ep, k_part))
        nested_dict_set(self.db_part_geometry, geometry, k_ed, k_ep, k_part)
        self.is_geometry_db_modified = True


    def discard_part_geometry_modifications(self, k_ed, k_ep, k_part):
        log.info("discard_part_geometry_modifications")
        try:
            del self.db_part_geometry[k_ed][k_ep][k_part]
        except:
            pass

        if len(self.db_part_geometry[k_ed][k_ep].keys()) == 0:
            del self.db_part_geometry[k_ed][k_ep]
        if len(self.db_part_geometry[k_ed].keys()) == 0:
            del self.db_part_geometry[k_ed]
        self.is_geometry_db_modified = False



    def get_shot_geometry(self, shot):
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
        return {'crop': [0, 0, 0, 0]}

    def set_shot_geometry(self, shot, geometry):
        k_ed = shot['k_ed']
        k_ep = shot['k_ep']
        k_part = shot['k_part']
        shot_start = shot['start']
        nested_dict_set(self.db_part_geometry, geometry, k_ed, k_ep, k_part, shot_start)
        self.is_geometry_db_modified = True


    def discard_shot_geometry_modifications(self, shot):
        log.info("discard_shot_geometry_modifications")
        k_ed = shot['k_ed']
        k_ep = shot['k_ep']
        k_part = shot['k_part']
        shot_start = shot['start']
        try:
            del self.db_shot_geometry[k_ed][k_ep][k_part][shot_start]
        except:
            pass

        if len(self.db_shot_geometry[k_ed][k_ep][k_part].keys()) == 0:
            del self.db_shot_geometry[k_ed][k_ep][k_part]
        if len(self.db_shot_geometry[k_ed][k_ep].keys()) == 0:
            del self.db_shot_geometry[k_ed][k_ep]
        if len(self.db_shot_geometry[k_ed].keys()) == 0:
            del self.db_shot_geometry[k_ed]
        self.is_geometry_db_modified = False



    # def get_shot_geometry(self, k_ed, k_ep, k_part, shot):
    #     # print("get shot geometry for %s:%s:%s" % (k_ed, k_ep, k_part), end='')
    #     # print("\t<- shot: %s:%s:%s" % (shot['k_ed'], shot['k_ep'], shot['k_part']))
    #     db = self.global_database
    #     if k_part in ['g_asuivre', 'g_reportage']:
    #         # Consider this part geometry as a customized one.
    #         # So that this part will have teh same dimension as the following part
    #         shot_geometry = {
    #             'part': self.get_part_geometry(
    #                         k_ed=k_ed,
    #                         k_ep=k_ep,
    #                         k_part=k_part[2:]),
    #             'shot': self.get_part_geometry(
    #                         k_ed=db[k_part]['target']['video']['src']['k_ed'],
    #                         k_ep=db[k_part]['target']['video']['src']['k_ep'],
    #                         k_part=k_part),
    #         }

    #     elif k_part in ['g_debut', 'g_fin']:
    #         # In this case, the custom geometry is the part of the dependency
    #         # print("* k_part=%s" % (k_part))
    #         k_ed_target = db[k_part]['target']['video']['src']['k_ed']
    #         k_ep_target = db[k_part]['target']['video']['src']['k_ep']
    #         shot_geometry = {
    #             'part': self.get_part_geometry(
    #                         k_ed=k_ed_target, k_ep=k_ep_target, k_part=k_part),
    #             'shot': None
    #         }
    #         if shot['k_ed'] != k_ed_target or shot['k_ep'] != k_ep_target:
    #             # Use the geometry for this part and use it as a custom
    #             # print("\t   shot k_ed:k_ep is <> ref k_ed:k_ep, use %s:%s:%s" % (
    #             #     shot['k_ed'], shot['k_ep'], shot['k_part']))
    #             shot_geometry.update({
    #                 'shot': self.get_part_geometry(
    #                             k_ed=shot['k_ed'], k_ep=shot['k_ep'], k_part=shot['k_part']),
    #             })
    #     else:
    #         shot_geometry = {
    #             'part': self.get_part_geometry(k_ed=k_ed, k_ep=k_ep, k_part=k_part),
    #             'shot': self.get_shot_geometry(shot=shot),
    #         }

    #     # print("\tshot_geometry:", shot_geometry)
    #     return shot_geometry





    def save_geometry_database(self, k_ed, k_ep, k_part, shot):
        # Save all modifications

        if not self.is_geometry_db_modified:
            return True

        log.info("save geometry database %s:%s" % (k_ep, k_part))
        # print("\n\nsave_geometry_database: %s:%s:%s\n---------------------------------------" % (k_ed, k_ep, k_part))
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

        # Update the config: geometry of a part
        for k_ed_src, ed_values in self.db_part_geometry.items():
            for k_ep_src, ep_values in ed_values.items():
                for k_part_src, part_values in ep_values.items():

                    k_section = '%s.%s.%s' % (k_ed_src, k_ep_src, k_part_src)
                    if not config_geometry.has_section(k_section):
                        config_geometry[k_section] = dict()
                    # print("k_section = %s" % (k_section))

                    # Update the values
                    try:
                        value_array = list()
                        try:
                            geometry_crop = part_values['crop']
                            value_array.append("crop=%s" % (':'.join(map(lambda x: "%d" % (x), geometry_crop))))
                            nested_dict_set(self.db_part_geometry_initial, deepcopy(geometry_crop),
                                k_ed_src, k_ep_src, k_part_src, 'crop')
                        except: pass

                        try:
                            geometry_resize = part_values['resize']
                            value_array.append("resize=%s" % (':'.join(map(lambda x: "%d" % (x), geometry_resize))))
                            nested_dict_set(self.db_part_geometry_initial, deepcopy(geometry_resize),
                                k_ed_src, k_ep_src, k_part_src, 'resize')
                        except: pass

                        try:
                            geometry_ratio = part_values['ratio']
                            value_array.append("keep_ratio=%s" % ('true' if geometry_ratio else 'false'))
                            nested_dict_set(self.db_part_geometry_initial, deepcopy(geometry_ratio),
                                k_ed_src, k_ep_src, k_part_src, 'ratio')
                        except: pass

                        config_geometry.set(k_section, 'part', ', '.join(value_array))
                    except: pass


        # Update the config: geometry of each shot
        for k_ed_src, ed_values in self.db_shot_geometry.items():
            for k_ep_src, ep_values in ed_values.items():
                for k_part_src, part_values in ep_values.items():
                    for shot_start, shot_values in part_values.items():

                        k_section = '%s.%s.%s' % (k_ed_src, k_ep_src, k_part_src)
                        if not config_geometry.has_section(k_section):
                            config_geometry[k_section] = dict()
                        # print("k_section = %s" % (k_section))

                        # Update the values
                        try:
                            value_array = list()
                            try:
                                geometry_crop = shot_values['crop']
                                value_array.append("crop=%s" % (':'.join(map(lambda x: "%d" % (x), geometry_crop))))
                                nested_dict_set(self.db_part_geometry_initial, deepcopy(geometry_crop),
                                    k_ed_src, k_ep_src, k_part_src, shot_start, 'crop')
                            except: pass

                            try:
                                geometry_resize = shot_values['resize']
                                value_array.append("resize=%s" % (':'.join(map(lambda x: "%d" % (x), geometry_resize))))
                                nested_dict_set(self.db_part_geometry_initial, deepcopy(geometry_resize),
                                    k_ed_src, k_ep_src, k_part_src, shot_start, 'resize')
                            except: pass

                            try:
                                geometry_ratio = shot_values['ratio']
                                value_array.append("keep_ratio=%s" % ('true' if geometry_ratio else 'false'))
                                nested_dict_set(self.db_part_geometry_initial, deepcopy(geometry_ratio),
                                    k_ed_src, k_ep_src, k_part_src, shot_start, 'ratio')
                            except: pass

                            config_geometry.set(k_section, str(shot_start), ', '.join(value_array))
                        except: pass


        # Write to the config file
        with open(filepath, 'w') as config_file:
            config_geometry.write(config_file)

        # Clean the dictonaries
        self.db_part_geometry.clear()
        self.db_shot_geometry.clear()

        self.is_geometry_db_modified = False
        return True





    # def save_shot_geometry(self, k_ed, k_ep, k_part, shot):
    #     if not self.is_geometry_db_modified:
    #         return True

    #     log.info("save save_shot_geometry database %s:%s" % (k_ep, k_part))
    #     print("\n\save_shot_geometry: %s:%s:%s\n---------------------------------------" % (k_ed, k_ep, k_part))
    #     pprint(self.db_part_geometry)
    #     db = self.global_database

    #     # Open configuration file
    #     if k_part in ['g_debut', 'g_fin']:
    #         filepath = os.path.join(db['common']['directories']['config'], k_part, "%s_geometry.ini" % (k_part))
    #     else:
    #         filepath = os.path.join(db['common']['directories']['config'], k_ep, "%s_geometry.ini" % (k_ep))
    #     if filepath.startswith("~/"):
    #         filepath = os.path.join(PosixPath(Path.home()), filepath[2:])

    #     print("file: %s" % (filepath))

    #     # Parse the file
    #     if os.path.exists(filepath):
    #         config_geometry = configparser.ConfigParser(dict_type=collections.OrderedDict)
    #         config_geometry.read(filepath)
    #     else:
    #         config_geometry = configparser.ConfigParser({}, collections.OrderedDict)

    #     if k_part in ['g_debut', 'g_fin']:
    #         k_ed_src = shot['k_ed']
    #         k_ep_src = shot['k_ep']
    #     elif k_part in ['g_asuivre', 'g_reportage']:
    #         k_ed_src = db[k_part]['target']['video']['src']['k_ed']
    #         k_ep_src = db[k_part]['target']['video']['src']['k_ep']
    #     else:
    #         k_ed_src = k_ed
    #         k_ep_src = k_ep

    #     # Update the config file, select section
    #     k_section = '%s.%s.%s' % (k_ed_src, k_ep_src, k_part)
    #     print("k_section = %s" % (k_section))

    #     if not config_geometry.has_section(k_section):
    #         config_geometry[k_section] = dict()

    #     # Update the values
    #     try:
    #         value_array = list()
    #         try:
    #             geometry_crop = self.db_part_geometry[k_ed_src][k_ep_src][k_part]['crop']
    #             value_array.append("crop=%s" % (':'.join(map(lambda x: "%d" % (x), geometry_crop))))
    #             nested_dict_set(self.db_part_geometry, deepcopy(geometry_crop),
    #                 k_ed_src, k_ep_src, k_part, 'crop')

    #             # del self.db_part_geometry[k_ed_src][k_ep_src][k_part]['crop']
    #         except: pass

    #         try:
    #             geometry_resize = self.db_part_geometry[k_ed_src][k_ep_src][k_part]['resize']
    #             value_array.append("resize=%s" % (':'.join(map(lambda x: "%d" % (x), geometry_resize))))
    #             nested_dict_set(self.db_part_geometry, deepcopy(geometry_resize),
    #                 k_ed_src, k_ep_src, k_part, 'resize')
    #             # del self.db_part_geometry[k_ed_src][k_ep_src][k_part]['resize']
    #         except: pass

    #         try:
    #             geometry_ratio = self.db_part_geometry[k_ed_src][k_ep_src][k_part]['ratio']
    #             value_array.append("keep_ratio=%s" % ('true' if geometry_ratio else 'false'))
    #             nested_dict_set(self.db_part_geometry, deepcopy(geometry_ratio),
    #                 k_ed_src, k_ep_src, k_part, 'ratio')
    #         except: pass

    #         try:
    #             del self.db_part_geometry[k_ed_src][k_ep_src][k_part]
    #         except:
    #             pass

    #         config_geometry.set(k_section, 'geometry', ', '.join(value_array))
    #     except: pass


    #     # Write to the database
    #     with open(filepath, 'w') as config_file:
    #         config_geometry.write(config_file)

    #     # Clean the dictonary
    #     # Clean the database and consider as not modified only if all keys have been saved
    #     # TODO: replace by a nested dict
    #     k_ed_keys = list(self.db_part_geometry.keys())
    #     for k_ed_tmp in k_ed_keys:
    #         k_ep_keys = list(self.db_part_geometry[k_ed_tmp].keys())
    #         for k_ep_tmp in k_ep_keys:
    #             k_parts_keys = list(self.db_part_geometry[k_ed_tmp][k_ep_tmp].keys())
    #             for k_part_tmp in k_parts_keys:
    #                 if len(self.db_part_geometry[k_ed_tmp][k_ep_tmp][k_part_tmp].keys()) == 0:
    #                     del self.db_part_geometry[k_ed_tmp][k_ep_tmp][k_part_tmp]

    #             if len(self.db_part_geometry[k_ed_tmp][k_ep_tmp].keys()) == 0:
    #                 del self.db_part_geometry[k_ed_tmp][k_ep_tmp]

    #         if len(self.db_part_geometry[k_ed_tmp].keys()) == 0:
    #             del self.db_part_geometry[k_ed_tmp]

    #     if len(self.db_part_geometry.keys()) == 0:
    #         self.is_geometry_db_modified = False
    #     else:
    #         print("all geometry have not been saved: ")
    #         pprint(self.db_part_geometry)

    #     return True

