# -*- coding: utf-8 -*-
import sys
sys.path.append('../scripts')

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
    get_shot_from_frame_no_new,
    pprint_video,
)
from parsers.parser_stabilize import (
    STABILIZE_SHOT_PARAMETERS_DEFAULT,
    get_shots_stabilize_parameters,
    get_frames_stabilize,
)
#!!! This does not work, but still in the project for later use


class Model_stabilize():

    def __init__(self):
        # Use a single database to store the modified values
        # Thus, no history is possible with this implementation
        # self.db_stabilize_frames_initial = dict()
        self.db_stabilize_frames = dict()
        self.db_stabilize_shots_parameters = dict()
        self.is_stabilize_db_modified = False

    def initialize_db_for_stabilize(self, db, k_ep, k_part):
        self.db_stabilize_shots_parameters_initial = get_shots_stabilize_parameters(self.global_database, k_ep=k_ep, k_part=k_part)
        self.db_stabilize_shots_parameters = dict()

        self.db_stabilize_frames_initial = get_frames_stabilize(self.global_database, k_ep=k_ep, k_part=k_part)
        self.db_stabilize_frames = dict()



    # Stabilize parameters
    def get_shot_stabilize_parameters(self, shot_no, frame_no=-1, initial=False):
        """ Return the parameters used for the stabilize
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
            # print("Error, no stabilize defined for this shot")
            return deepcopy(STABILIZE_SHOT_PARAMETERS_DEFAULT)

        if frame_no == -1:
            return parameters

        # A shot may contains multiple shots; this dict contains a list of segments
        for segment in parameters:
            if segment['start'] <= frame_no < segment['end']:
                return segment
        # print("segment not found for %d" % (frame_no))
        return deepcopy(STABILIZE_SHOT_PARAMETERS_DEFAULT)


    def set_shot_stabilize_parameters(self, shot_no, shot_parameters):
        if type(shot_parameters) is dict:
            self.db_stabilize_shots_parameters[shot_no][0].update(shot_parameters)
        else:
            self.db_stabilize_shots_parameters[shot_no] = deepcopy(shot_parameters)
        self.is_stabilize_db_modified = True


    def reset_shot_stabilize_parameters(self, shot_no):
        print("reset shot stabilize parameters")
        if shot_no in self.db_stabilize_shots_parameters.keys():
            del self.db_stabilize_shots_parameters[shot_no]
        self.flush_frames_stabilize(shot_no)



    # Stabilize values for each frame
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





    def save_stabilize_database(self, k_ep, k_part, shots):
        print("save_stabilize_database")
        if not self.is_stabilize_db_modified:
            return True

        log.info("save stabilize database %s:%s" % (k_ep, k_part))
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
                    sys.exit("Error: save_stabilize_database: shot_src is None")
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
                        print("Error: calculations have not been done, discard")
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


