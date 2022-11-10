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

from utils.get_curves import calculate_channel_lut
from utils.common import (
    K_GENERIQUES,
    nested_dict_set,
)
from parsers.parser_curves import (
    parse_curves_file,
    write_curves_file,
)


class Model_curves():

    def __init__(self):
        # Use a single database to store the modified values
        # Thus, no history is possible with this implementation
        self.shots_per_curves = dict()

        self.is_curves_db_modified = False
        self.is_curves_selection_db_modified = False



    # RGB curves
    def get_curves_selection(self, shot):
        # Get the curves associated to this shot
        k_ed = shot['k_ed']
        k_ep = shot['k_ep']
        k_part = shot['k_part']
        shot_no = shot['no']
        # print("db_curves_selection_initial")
        # pprint(self.db_curves_selection_initial)
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


