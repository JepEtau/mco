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
    K_GENERIQUES,
    nested_dict_set,
)

from parsers.parser_geometry import parse_geometry_configurations
from parsers.parser_geometry import get_part_geometry
from parsers.parser_geometry import get_shots_st_geometry


class Model_geometry():

    def __init__(self):
        self.is_geometry_db_modified = False


    # Final geometry for each part
    def get_part_geometry(self, k_ed, k_part):
        # print("get_part_geometry: %s:%s" % (k_ed, k_part))
        # pprint(self.db_part_geometry_initial)
        for db_tmp in [self.db_part_geometry,
                        self.db_part_geometry_initial]:
            if k_ed in db_tmp.keys() and k_part in db_tmp[k_ed].keys():
                return db_tmp[k_ed][k_part]

        return {'crop': [0, 0, 0, 0]}


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


    def get_custom_geometry(self, shot):
        print("return the geometry for this shot")
        # TODO: return the geometry for this shot
        return None


    def set_custom_geometry(self, shot, geometry):
        print("set the customized geometry for this shot")
        # TODO: set the geometry for this shot


    def get_shot_geometry(self, k_ed, k_ep, shot):
        k_part = shot['k_part']
        print("get shot geometry for %s:%s:%s" % (k_ed, k_ep, k_part))

        # Geometry
        db = self.global_database
        if k_part in ['g_asuivre', 'g_reportage']:
            # Consider this part geometry as a customized one.
            # So that this part will have teh same dimension as the following part
            shot_geometry = {
                'part': self.get_part_geometry(
                            k_ed=db[k_ep]['common']['video']['reference']['k_ed'],
                            k_part=k_part[2:]),
                'custom': self.get_part_geometry(k_ed=k_ed, k_part=k_part),
            }
        else:
            shot_geometry = {
                'part': self.get_part_geometry(k_ed=k_ed, k_part=k_part),
                'custom': self.get_custom_geometry(shot=shot),
            }

        # print("shot_geometry")
        # pprint(shot_geometry)
        # sys.exit()
        return shot_geometry



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

