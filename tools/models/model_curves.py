# -*- coding: utf-8 -*-
import sys


from copy import deepcopy
import os
import os.path
import configparser
from pathlib import Path
from pathlib import PosixPath
import collections


from pprint import pprint
from logger import log

from utils.get_curves import calculate_channel_lut
from utils.common import (
    K_GENERIQUES,
)
from utils.nested_dict import nested_dict_clean, nested_dict_set
from parsers.parser_curves import (
    parse_curves_database,
    get_initial_curves_selection,
)


class Model_curves():

    def __init__(self):
        # Use a single database to store the modified values
        # Thus, no history is possible with this implementation
        self.shots_per_curves = dict()
        self.is_curves_db_modified = False
        self.is_curves_selection_db_modified = False


    def initialize_db_for_curves(self, db, k_ep, k_part):
        # print("Model_curves:initialize_db_for_curves: get initial curves selection")
        # This function is used by the video editor
        # which uses the consolidated shots
        self.initialize_curves_library(db=db, k_ep=k_ep, k_part=k_part)
        self.db_curves_selection_initial = get_initial_curves_selection(db, k_ep=k_ep, k_part=k_part)
        self.db_curves_selection = dict()


    def initialize_curves_library(self, db, k_ep, k_part):
        k_ep_or_g = k_part if k_part in K_GENERIQUES else k_ep
        self.db_curves_library_initial = parse_curves_database(db=db, k_ep_or_g=k_ep_or_g)
        self.db_curves_library = dict()
        # pprint(self.db_curves_library_initial)


    # RGB curves
    def get_shot_curves_selection(self, db, shot) -> dict:
        # Get the curves associated to this shot
        k_ed = shot['k_ed']
        k_ep = shot['k_ep']
        k_part = shot['k_part']
        shot_start = shot['start']
        # print("model: self.db_curves_selection_initial %s:%s:%s:%s" % (k_ed, k_ep, k_part, shot_start))
        try:
            shot_curves = self.db_curves_selection[k_ed][k_ep][k_part][shot_start]
        except:
            try:
                shot_curves = self.db_curves_selection_initial[k_ed][k_ep][k_part][shot_start]
            except:
                return None

        if 'k_curves' not in shot_curves.keys() or shot_curves['k_curves'] == '':
            # This shot uses new RGB curves which are not yet been saved in the library
            return shot_curves

        # Get the curves from the library
        curves = self.get_curves(db, k_ed, k_ep, shot_curves['k_curves'])
        return curves


    def set_shot_rgb_channels(self, shot, rgb_channels):
        k_ed = shot['k_ed']
        k_ep = shot['k_ep']
        k_part = shot['k_part']
        shot_start = shot['start']
        # Get the curves frome the db_chot_curves. it points to the curves
        # stored in the db_curves_library
        try:
            shot_curves = self.db_curves_selection[k_ed][k_ep][k_part][shot_start]
        except:
            try:
                shot_curves = self.db_curves_selection_initial[k_ed][k_ep][k_part][shot_start]
            except:
                curves = ({
                    'k_curves': '',
                    'channels': deepcopy(rgb_channels),
                    'lut': calculate_channel_lut(rgb_channels),
                    'is_modified': True,
                })
                nested_dict_set(self.db_curves_selection, curves, k_ed, k_ep, k_part, shot_start)
                self.is_curves_db_modified = True
                return

        if shot_curves['k_curves'] == '':
            # Curves is not yet saved in library
            self.db_curves_selection[k_ed][k_ep][k_part][shot_start].update({
                'channels': deepcopy(rgb_channels),
                'lut': calculate_channel_lut(rgb_channels),
                'is_modified': True,
            })
            self.is_curves_db_modified = True
            return

        # Modify the curves in the library
        is_modified = self.set_curves(k_ed, k_ep, k_curves=shot_curves['k_curves'], rgb_channels=rgb_channels)
        if not is_modified:
            # No curves found for this k_curves, create a new one in the shot
            curves = ({
                'k_curves': '',
                'channels': deepcopy(rgb_channels),
                'lut': calculate_channel_lut(rgb_channels),
                'is_modified': True,
            })
            nested_dict_set(self.db_curves_selection, curves, k_ed, k_ep, k_part, shot_start)

        self.is_curves_db_modified = True



    def set_curves_selection(self, db, shot:dict, k_curves:str):
        k_ed = shot['k_ed']
        k_ep = shot['k_ep']
        k_part = shot['k_part']
        shot_start = shot['start']
        shot_no = shot['no']

        # Get the curves from the library
        curves = self.get_curves(db, k_ed, k_ep, k_curves)

        # Set the modified shot curves
        nested_dict_set(self.db_curves_selection, curves, k_ed, k_ep, k_part, shot_start)

        # Refresh the list of shots for each curves
        for shotlist in self.shots_per_curves.values():
            try:
                shotlist.remove(shot_no)
                break
            except: pass

        try:
            if shot_no not in self.shots_per_curves[k_curves]:
                self.shots_per_curves[k_curves].append(shot_no)
        except:
            self.shots_per_curves[k_curves] = [shot_no]

        self.is_curves_selection_db_modified = True



    def discard_curves_selection(self, db, shot:dict):
        k_ed = shot['k_ed']
        k_ep = shot['k_ep']
        k_part = shot['k_part']
        shot_start = shot['start']
        shot_no = shot['no']
        log.info("discard_curves_selection %s:%s:%s:%s" % (k_ed, k_ep, k_part, shot_start))

        # Access directly to the modified, because the get_curves_selection function
        # may return the curves from the initial db
        # If there is a problem, this will have to be corrected
        try:
            k_curves_current = self.db_curves_selection[k_ed][k_ep][k_part][shot_start]
        except:
            print("Error: %s:%s:%s:%s: current curves are not found in the db_curves_selection (modified db)" % (k_ed, k_ep, k_part, shot_start))
            # pprint(self.db_curves_selection)
            # raise Exception()
            pass
        del self.db_curves_selection[k_ed][k_ep][k_part][shot_start]
        curves = self.get_shot_curves_selection(db=db, shot=shot)
        try:
            k_curves_initial = curves['k_curves']
            try: self.shots_per_curves[k_curves_initial].append(shot_no)
            except: self.shots_per_curves[k_curves_initial] = [shot_no]
        except:
            # No initial curves
            pass

        # Refresh the list of shots for each curves
        try: self.shots_per_curves[k_curves_current].remove(shot_no)
        except: pass



    def remove_curves_selection(self, db, shot:dict):
        k_ed = shot['k_ed']
        k_ep = shot['k_ep']
        k_part = shot['k_part']
        shot_start = shot['start']
        shot_no = shot['no']

        # Get the curves from the library
        k_ep_or_g = k_part if k_part in K_GENERIQUES else k_ep

        # Set the modified shot curves
        nested_dict_set(self.db_curves_selection, {'k_curves': ''}, k_ed, k_ep, k_part, shot_start)

        # Refresh the list of shots for each curves
        for shotlist in self.shots_per_curves.values():
            try:
                shotlist.remove(shot_no)
                break
            except: pass

        self.is_curves_selection_db_modified = True




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
    def get_library_curves(self, k_ed, k_ep) -> list:
        curves_library = dict()
        # Get k_curves from initial db
        try:
            k_curves_list = list(self.db_curves_library_initial[k_ed][k_ep].keys())
            curves_library = {k_curves:False for k_curves in k_curves_list}
        except:
            pass

        # Get k_curves from modified db
        try:
            for k_curves, curves in self.db_curves_library[k_ed][k_ep].items():
                if not 'deleted' in curves:
                    # These curves are modified
                    curves_library[k_curves] = True
        except:
            pass

        return curves_library



    def get_curves(self, db, k_ed:str, k_ep:str, k_curves:str):
        # Find these curves in the curves library
        try:
            curves = self.db_curves_library[k_ed][k_ep][k_curves]
        except:
            try:
                curves = self.db_curves_library_initial[k_ed][k_ep][k_curves]
            except:
                curves = None

        # If not found, add these curves to the library
        if curves is None:
            print("get_curves: add to the library")
            # Create a curve structure
            nested_dict_set(self.db_curves_library_initial, {
                'k_curves': k_curves,
                'channels': None,
                'lut': None,
                'shots': []
            }, k_ed, k_ep, k_curves)
            curves = self.db_curves_library_initial[k_ed][k_ep][k_curves]

        if curves['lut'] is None:
            curves['lut'] = calculate_channel_lut(curves['channels'])

        return curves



    def set_curves(self, k_ed, k_ep, k_curves:str, rgb_channels):
        try:
            curves = self.db_curves_library[k_ed][k_ep][k_curves]
        except:
            try:
                nested_dict_set(self.db_curves_library,
                    deepcopy(self.db_curves_library_initial[k_ed][k_ep][k_curves]),
                    k_ed, k_ep, k_curves)
                curves = self.db_curves_library[k_ed][k_ep][k_curves]
            except:
                # print("[%s] does not exists neither in library not in initial library" % (k_curves))
                return False

        curves.update({
            'channels': deepcopy(rgb_channels),
            'lut': calculate_channel_lut(rgb_channels),
            'is_modified': True,
        })
        self.is_curves_db_modified = True
        return True



    def discard_rgb_curves_modifications(self, k_curves, k_ed, k_ep):
        print("WARNING: discard RGB curves modification")
        try:
            del self.db_curves_library[k_ed][k_ep][k_curves]
        except:
            print("Error: discard_curves_modifications: failed")
            pass



    # def save_all_curves(self, k_ep_or_g):
    #     for curves in self.db_curves_library.values():
    #         self.save_curves_as(k_ep_or_g=k_ep_or_g, curves=curves)



    def append_curves_to_database(self, db, k_ed, k_ep, k_part, curves):
        k_curves_current = curves['k_curves_current']
        log.info("Try removing [%s] from modified db" % (k_curves_current))
        try:
            # Remove from modified db
            del self.db_curves_library[k_ed][k_ep][k_curves_current]
        except:
            # These curves were not modified
            pass

        # Append these curves in the initial db
        k_curves = k_curves_current if curves['k_curves_new'] is None else curves['k_curves_new']
        log.info("Append %s to the db" % (k_curves))

        # Open configuration file
        if k_part in K_GENERIQUES:
            filepath = os.path.join(db['common']['directories']['config'], k_part, "%s_curves_db.ini" % (k_part))
        else:
            filepath = os.path.join(db['common']['directories']['config'], k_ep, "%s_curves_db.ini" % (k_ep))

        if filepath.startswith("~/"):
            filepath = os.path.join(PosixPath(Path.home()), filepath[2:])

        # Parse the file
        if os.path.exists(filepath):
            config_curves_db = configparser.ConfigParser()
            config_curves_db.read(filepath)
        else:
            config_curves_db = configparser.ConfigParser({}, collections.OrderedDict)

        # Section name
        if k_part in K_GENERIQUES:
            k_section = '%s.%s.%s' % (k_ed, k_ep, k_curves)
        else:
            k_section = '%s.%s' % (k_ed, k_curves)

        # Write RGBM points
        for k_channel in ['m', 'r', 'g', 'b']:
            value_str = ""
            for p in curves['channels'][k_channel].points():
                value_str += "%.06f:%.06f," % (p.x(), p.y())
            value_str = value_str[:-1]
            try:
                config_curves_db.set(k_section, k_channel, value_str)
            except:
                config_curves_db[k_section] = dict()
                config_curves_db.set(k_section, k_channel, value_str)

        # Write to the database
        with open(filepath, 'w') as config_file:
            config_curves_db.write(config_file)


        # Add it to the initial library
        nested_dict_set(self.db_curves_library_initial, {
            'k_curves': k_curves,
            'channels': deepcopy(curves['channels']),
            'lut': None,
            'shots': []
        }, k_ed, k_ep, k_curves)



    def save_shot_curves_selection(self, db, shot):
        if not self.is_curves_selection_db_modified:
            return True

        k_ed = shot['k_ed']
        k_ep = shot['k_ep']
        k_part = shot['k_part']
        shot_start = shot['start']

        log.info(f"save shot curves selection: {k_ed}:{k_ep}:{k_part}")
        print(f"save shot curves selection: {k_ed}:{k_ep}:{k_part} shot no. {shot['no']}, start={shot_start}")

        # Open configuration file
        if k_part in K_GENERIQUES:
            filepath = os.path.join(db['common']['directories']['config'], k_part, "%s_curves.ini" % (k_part))
        else:
            filepath = os.path.join(db['common']['directories']['config'], k_ep, "%s_curves.ini" % (k_ep))
        if filepath.startswith("~/"):
            filepath = os.path.join(PosixPath(Path.home()), filepath[2:])
        # print("save_curves_selection_database: %s" % (filepath))

        # Parse the file
        if os.path.exists(filepath):
            config_curves_selection = configparser.ConfigParser()
            config_curves_selection.read(filepath)
        else:
            config_curves_selection = configparser.ConfigParser({}, collections.OrderedDict)

        # Get shot
        try: shot_curves = self.db_curves_selection[k_ed][k_ep][k_part][shot_start]
        except:
            print("Warning: the selection has not been modified")
        if shot_curves['k_curves'] == '':
            # These curves are not saved in the database (=error)
            # we consider that the curves selection cannot be removed
            print("Error: the RGB curves have not been saved")

        k_section = '%s.%s.%s' % (k_ed, k_ep, k_part)
        try:
            config_curves_selection.set(k_section, str(shot_start), shot_curves['k_curves'])
        except:
            config_curves_selection[k_section] = dict()
            config_curves_selection.set(k_section, str(shot_start), shot_curves['k_curves'])

        # Write to the database
        with open(filepath, 'w') as config_file:
            config_curves_selection.write(config_file)

        # Remove from initial if exists
        try:
            del self.db_curves_selection_initial[k_ed][k_ep][k_part][shot_start]
        except:
            pass

        # Set the new curves selection in the initial database
        nested_dict_set(self.db_curves_selection_initial, {
                'k_curves': shot_curves['k_curves'],
                'lut': None
            }, k_ed, k_ep, k_part, shot_start)

        # Remove from modified
        del self.db_curves_selection[k_ed][k_ep][k_part][shot_start]

        # Clean the dictionary
        nested_dict_clean(self.db_curves_selection)
        # TODO: replace by a nested dict
        # k_ed_keys = list(self.db_curves_selection.keys())
        # for k_ed_tmp in k_ed_keys:
        #     k_ep_keys = list(self.db_curves_selection[k_ed_tmp].keys())
        #     for k_ep_tmp in k_ep_keys:
        #         k_parts_keys = list(self.db_curves_selection[k_ed_tmp][k_ep_tmp].keys())
        #         for k_part_tmp in k_parts_keys:
        #             if len(self.db_curves_selection[k_ed_tmp][k_ep_tmp][k_part_tmp].keys()) == 0:
        #                 del self.db_curves_selection[k_ed_tmp][k_ep_tmp][k_part_tmp]

        #         if len(self.db_curves_selection[k_ed_tmp][k_ep_tmp].keys()) == 0:
        #             del self.db_curves_selection[k_ed_tmp][k_ep_tmp]

        #     if len(self.db_curves_selection[k_ed_tmp].keys()) == 0:
        #         del self.db_curves_selection[k_ed_tmp]

        # Clear modification flag if dict is empty
        if len(self.db_curves_selection.keys()) == 0:
            self.is_curves_selection_db_modified = False
        else:
            print("all curves selection have not been saved")


        return True


