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
from parsers.parser_geometry import get_part_geometry_list
from parsers.parser_geometry import get_shots_st_geometry


class Model_geometry():

    def __init__(self):
        self.is_geometry_db_modified = False


    # Final geometry for each part
    def get_part_geometry(self, k_ed, k_ep, k_part):
        # pprint(self.db_part_geometry_initial)
        try:
            return self.db_part_geometry[k_ed][k_part]
        except:
            try:
                return self.db_part_geometry_initial[k_ed][k_part]
            except:
                pass
        print("get_part_geometry: %s:%s:%s" % (k_ed, k_ep, k_part))
        print("-> not found")
        return {'crop': [0, 0, 0, 0]}


    def set_part_geometry(self, k_ed, k_ep, k_part, geometry):
        # db_modified = self.db_part_geometry
        # if k_ed not in db_modified.keys():
        #     db_modified[k_ed] = dict()
        # if k_part not in db_modified[k_ed].keys():
        #     db_modified[k_ed][k_part] = dict()
        # db_modified[k_ed][k_part] = geometry
        print("set_part_geometry: %s:%s:%s" % (k_ed, k_ep, k_part))
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


    def get_shot_geometry(self, k_ed, k_ep, k_part, shot):
        print("get shot geometry for %s:%s:%s" % (k_ed, k_ep, k_part))
        print("\t%s:%s:%s" % (shot['k_ed'], shot['k_ep'], shot['k_part']))
        db = self.global_database
        if k_part in ['g_asuivre', 'g_reportage']:
            # Consider this part geometry as a customized one.
            # So that this part will have teh same dimension as the following part
            shot_geometry = {
                'part': self.get_part_geometry(
                            k_ed=k_ed,
                            k_ep=k_ep,
                            k_part=k_part[2:]),
                'custom': self.get_part_geometry(
                            k_ed=db[k_part]['common']['video']['reference']['k_ed'],
                            k_ep=db[k_part]['common']['video']['reference']['k_ep'],
                            k_part=k_part),
            }
        else:
            shot_geometry = {
                'part': self.get_part_geometry(k_ed=k_ed, k_ep=k_ep, k_part=k_part),
                'custom': self.get_custom_geometry(shot=shot),
            }

        # print("shot_geometry")
        # pprint(shot_geometry)
        # sys.exit()
        return shot_geometry



    def save_geometry_database(self, k_ed, k_ep, k_part):
        if not self.is_geometry_db_modified:
            return True

        log.info("save geometry database %s:%s" % (k_ep, k_part))
        print("\n\nsave_geometry_database: %s:%s:%s\n---------------------------------------" % (k_ed, k_ep, k_part))
        pprint(self.db_part_geometry)
        db = self.global_database

        # Open configuration file
        if k_part in ['g_debut', 'g_fin']:
            filepath = os.path.join(db['common']['directories']['config'], k_part, "%s_geometry.ini" % (k_part))
        else:
            filepath = os.path.join(db['common']['directories']['config'], k_ep, "%s_geometry.ini" % (k_ep))
        if filepath.startswith("~/"):
            filepath = os.path.join(PosixPath(Path.home()), filepath[2:])

        print("file: %s" % (filepath))

        # Parse the file
        if os.path.exists(filepath):
            config_geometry = configparser.ConfigParser(dict_type=collections.OrderedDict)
            config_geometry.read(filepath)
        else:
            config_geometry = configparser.ConfigParser({}, collections.OrderedDict)

        if k_part in ['g_asuivre', 'g_reportage']:
            k_ed_src = db[k_part]['common']['video']['reference']['k_ed']
            k_ep_src = db[k_part]['common']['video']['reference']['k_ep']
        else:
            k_ed_src = k_ed
            k_ep_src = k_ep

        # Update the config file, select section
        k_section = '%s.%s.%s' % (k_ed_src, k_ep_src, k_part)
        print("k_section = %s" % (k_section))

        if not config_geometry.has_section(k_section):
            config_geometry[k_section] = dict()

        # Update the values
        try:
            value_array = []
            try: value_array.append("crop=%s" % (':'.join(map(lambda x: "%d" % (x), self.db_part_geometry[k_ed_src][k_part]['crop']))))
            except: pass

            try: value_array.append("resize=%s" % (':'.join(map(lambda x: "%d" % (x), self.db_part_geometry[k_ed_src][k_part]['resize']))))
            except: pass

            try: value_array.append("keep_ration=%s" % ('true' if self.db_part_geometry[k_ed_src][k_part]['resize'] else 'false'))
            except: pass

            config_geometry.set(k_section, 'geometry', ', '.join(value_array))
        except: pass

        # TODO: Add values coming from custom geometry

        # Write to the database
        with open(filepath, 'w') as config_file:
            config_geometry.write(config_file)

        self.is_geometry_db_modified = False
        return True

