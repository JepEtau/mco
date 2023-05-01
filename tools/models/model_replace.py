# -*- coding: utf-8 -*-
import sys


import os
import os.path
import configparser
from pathlib import Path
from pathlib import PosixPath
import collections

from pprint import pprint
from logger import log

from utils.common import K_GENERIQUES
from utils.nested_dict import nested_dict_set
from utils.pretty_print import *
from parsers.parser_replace import (
    get_replaced_frames,
)

class Model_replace():

    def __init__(self):
        self.db_replaced_frames_initial = dict()
        # Use a single database to store the modified values
        # Thus, no history is possible with this implementation
        self.db_replaced_frames = dict()
        self.is_replace_db_modified = False


    def initialize_db_for_replace(self, db, k_ep, k_part):
        print(f"Model_replace: get initial geometry: {k_ep}:{k_part}")
        # This function is used by the video editor
        # which uses the consolidated shots
        self.db_replaced_frames_initial = get_replaced_frames(db, k_ep=k_ep, k_part=k_part)
        self.db_replaced_frames = dict()


    # Replaced frames
    def get_replace_frame_no(self, shot:dict, frame_no:int):
        """ Return the new frame no. if replaced. Returns -1 otherwise
        """
        k_ed = shot['k_ed']
        k_ep = shot['k_ep']
        k_part = shot['k_part']
        # print_lightgreen("get_replace_frame_no %s:%s:%s:%d" % (k_ed, k_ep, k_part, frame_no))
        try:
            return self.db_replaced_frames[k_ed][k_ep][k_part][frame_no]
        except:
            pass
        try:
            return self.db_replaced_frames_initial[k_ed][k_ep][k_part][frame_no]
        except:
            return -1


    def set_replaced_frame(self, shot, frame_no, new_frame_no):
        k_ed = shot['k_ed']
        k_ep = shot['k_ep']
        k_part = shot['k_part']
        try:
            if new_frame_no in self.db_replaced_frames[k_ed][k_ep][k_part].keys():
                print_red("error: replace: circular reference. TODO: block this")
                return
        except: pass

        try:
            if new_frame_no in self.db_replaced_frames_initial[k_ed][k_ep][k_part].keys():
                print_red("error: replace: circular reference. TODO: block this")
                return
        except: pass
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



    def save_replace_database(self):
        if not self.is_replace_db_modified:
            return True

        log.info("save replace database")
        db = self.global_database

        for k_ed, ed_values in self.db_replaced_frames.items():
            for k_ep, ep_values in ed_values.items():
                for k_part, part_values in ep_values.items():

                    # Open configuration file
                    if k_part in K_GENERIQUES:
                        # Write into a single file in the generique directory
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
                    for frame_no, new_frame_no in part_values.items():
                        if new_frame_no == -1:
                            # Remove from the config file
                            if config_replace.has_option(k_section, str(frame_no)):
                                config_replace.remove_option(k_section, str(frame_no))
                            try: del self.db_replaced_frames_initial[k_ed][k_ep][k_part][frame_no]
                            except: pass
                        else:
                            # Set the new value
                            config_replace.set(k_section, str(frame_no), str(new_frame_no))
                            nested_dict_set(self.db_replaced_frames_initial,
                                new_frame_no, k_ed, k_ep, k_part, frame_no)


                    # Write to the database
                    with open(filepath, 'w') as config_file:
                        config_replace.write(config_file)

        self.db_replaced_frames.clear()
        self.is_replace_db_modified = False
        return True

