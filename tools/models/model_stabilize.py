# -*- coding: utf-8 -*-
import sys



import collections
from copy import deepcopy
import os
import os.path
import configparser
from pathlib import Path
from pathlib import PosixPath

from pprint import pprint
from logger import log

from utils.common import (
    K_GENERIQUES,
    get_k_part_from_frame_no,
)
from utils.nested_dict import nested_dict_clean, nested_dict_set
from utils.pretty_print import *

from shot.utils import get_shot_from_frame_no
from parsers.parser_stabilize import (
    get_initial_shot_stabilize_settings,
)


class Model_stabilize():

    def __init__(self):
        # Use a single database to store the modified values
        # Thus, no history is possible with this implementation
        self.db_stabilize_initial = dict()
        self.db_stabilize = dict()
        self.is_stabilize_db_modified = False


    def initialize_db_for_stabilize(self, db, k_ep, k_part):
        self.db_stabilize_initial = get_initial_shot_stabilize_settings(db, k_ep=k_ep, k_part=k_part)
        self.db_stabilize = dict()
        # print_lightcyan(f"initialize_db_for_stabilize")
        # pprint(self.db_stabilize_initial)
        # sys.exit()


    def get_shot_stabilize_settings(self, shot:dict) -> dict | None:
        k_ed = shot['k_ed']
        k_ep = shot['k_ep']
        k_part = shot['k_part']
        shot_start = shot['start']
        try:
            return self.db_stabilize[k_ed][k_ep][k_part][shot_start]
        except:
            pass
        try:
            return self.db_stabilize_initial[k_ed][k_ep][k_part][shot_start]
        except:
            return None
        return None

    def set_shot_stabilize_settings(self, shot:dict, settings):
        k_ed = shot['k_ed']
        k_ep = shot['k_ep']
        k_part = shot['k_part']
        shot_start = shot['start']
        nested_dict_set(self.db_stabilize, settings, k_ed, k_ep, k_part, shot_start)
        self.is_stabilize_db_modified = True



    def delete_shot_stabilize_settings(self, shot):
        k_ed = shot['k_ed']
        k_ep = shot['k_ep']
        k_part = shot['k_part']
        shot_start = shot['start']
        nested_dict_set(self.db_stabilize, None, k_ed, k_ep, k_part, shot_start)
        self.is_stabilize_db_modified = True


    def discard_shot_stabilize_settings(self, shot):
        log.info("discard_shot_stabilize_settings")
        k_ed = shot['k_ed']
        k_ep = shot['k_ep']
        k_part = shot['k_part']
        shot_start = shot['start']
        try: del self.db_stabilize[k_ed][k_ep][k_part][shot_start]
        except: pass
        nested_dict_clean(self.db_stabilize)
        if len(self.db_stabilize) == 0:
            self.is_stabilize_db_modified = False



    def save_shot_stabilize_settings(self, shot):
        verbose = False
        if not self.is_stabilize_db_modified:
            return True

        # log.info(f"save stabilize database {k_ep}:{k_part}")
        db = self.global_database
        k_ed = shot['k_ed']
        k_ep = shot['k_ep']
        k_part = shot['k_part']
        shot_start = shot['start']
        if verbose:
            print(f"save_shot_stabilize_settings: {k_ed}:{k_ep}:{k_part} shot no. {shot['no']}, start={shot_start}")

        # Get settings from db
        try: stabilize_settings = self.db_stabilize[k_ed][k_ep][k_part][shot_start]
        except:
            print("Warning: stabilize settings have not been modified")

        # Do not save if not valid
        if 'error' in stabilize_settings.keys() and stabilize_settings['error']:
            # Error in segment definition, do not save
            print_yellow("Warning: not valid, not saved")
            return

        # At least one segment
        if len(stabilize_settings['segments']) == 0:
            print_yellow("Warning: not segments, not saved")
            return

        # Open configuration file
        if k_part in ['g_debut', 'g_fin']:
            filepath = os.path.join(db['common']['directories']['config'], k_part, f"{k_part}_stabilize.ini")
        else:
            filepath = os.path.join(db['common']['directories']['config'], k_ep, f"{k_ep}_stabilize.ini")
        if filepath.startswith("~/"):
            filepath = os.path.join(PosixPath(Path.home()), filepath[2:])

        # Parse the file
        if os.path.exists(filepath):
            config_stabilize = configparser.ConfigParser(dict_type=collections.OrderedDict)
            config_stabilize.read(filepath)
        else:
            config_stabilize = configparser.ConfigParser({}, collections.OrderedDict)

        if verbose:
            print_lightgreen("save_stabilize_database")
            pprint(self.db_stabilize)

        # Get settings from db
        try: stabilize_settings = self.db_stabilize[k_ed][k_ep][k_part][shot_start]
        except:
            print("Warning: stabilize settings have not been modified")


        # Section, option
        k_section = f"{k_ed}.{k_ep}.{k_part}"
        k_option = f"{shot_start}_deshake"

        # Set or remove option
        if stabilize_settings is None:
            # Remove from config file
            try: config_stabilize.remove_option(k_section, k_option)
            except: pass
        else:
            # Convert dict into a str
            enable_str = "enable=%s;" % ('true' if stabilize_settings['enable'] else 'false')
            segments_str = ""
            for segment in stabilize_settings['segments']:
                mode_str = ""
                for k, v in segment['mode'].items():
                    mode_str += f"+{k}" if v else ''

                segments_str += f"\n{segment['stab']}"
                segments_str += f":start={segment['start']}"
                segments_str += f":end={segment['end']}"
                segments_str += f":from={segment['from']}"
                segments_str += f":ref={segment['ref']}"
                segments_str += f":static={'true' if segment['static'] else 'false'}"
                segments_str += f":enhance={segment['enhance']}"

                segments_str += f":mode={mode_str[1:]}"

                if len(segment['tracker']['regions']) > 0:
                    segments_str += f":"
                    segments_str += f"\ntracker={'enable' if segment['tracker']['enable'] else 'disable'},"
                    segments_str += f"{'inside' if segment['tracker']['inside'] else 'outside'}"
                    for region in segment['tracker']['regions']:
                        segments_str += f",\n\t"
                        for point in region:
                            segments_str += f"({point[0]}.{point[1]})"

                segments_str += ";"

            stabilize_settings_str = f"\"\"\"{enable_str}{segments_str}\n\"\"\""

            # Set the new option
            try:
                config_stabilize.set(k_section, k_option, stabilize_settings_str)
            except:
                config_stabilize[k_section] = dict()
                config_stabilize.set(k_section, k_option, stabilize_settings_str)

        # Write to the database
        with open(filepath, 'w') as config_file:
            config_stabilize.write(config_file)

        # Remove from initial if exists
        try:
            del self.db_stabilize_initial[k_ed][k_ep][k_part][shot_start]
        except:
            pass

        # Set the new curves selection in the initial database
        nested_dict_set(self.db_stabilize_initial, deepcopy(stabilize_settings),
            k_ed, k_ep, k_part, shot_start)

        # Remove from modified
        del self.db_stabilize[k_ed][k_ep][k_part][shot_start]

        # Clean the dictionary
        nested_dict_clean(self.db_stabilize)

        # Clear modification flag if dict is empty
        if len(self.db_stabilize.keys()) == 0:
            self.is_stabilize_db_modified = False
        else:
            print("all curves selection have not been saved")


