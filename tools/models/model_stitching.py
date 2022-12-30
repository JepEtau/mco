# -*- coding: utf-8 -*-

import sys
sys.path.append('../scripts')

from copy import deepcopy
import os
import os.path

from pprint import pprint
from logger import log

from parsers.parser_stitching import (
    get_initial_fgd_crop,
    get_initial_matrix,
)

from utils.common import (
    K_GENERIQUES,
    nested_dict_get,
    nested_dict_set,
)


class Model_stitching():

    def __init__(self):
        self.db_stitching_shots_parameters = dict()
        self.db_stitching_frames = dict()
        self.is_stitching_db_modified = False


    # Crop foreground image
    #===========================================================================
    def initialize_db_for_fgd_crop(self, db, k_ep, k_part):
        # Get a dict of defined crop coordinates
        self.db_stitching_fgd_crop_initial = get_initial_fgd_crop(db, k_ep=k_ep, k_part=k_part)
        self.db_stitching_fgd_crop = dict()
        # pprint(self.db_stitching_fgd_crop_initial)
        # sys.exit("initialize_db_for_fgd_crop")


    def get_fgd_crop(self, shot):
        # Crop to apply to the fgd image before merging fgd and bgd images
        # pprint(shot)
        # pprint(self.db_stitching_fgd_crop_initial)
        # sys.exit("get_fgd_crop")
        k_ed = shot['k_ed']
        k_ep = shot['k_ep']
        k_part = shot['k_part']
        shot_start = shot['start']
        try:
            return self.db_stitching_fgd_crop[k_ed][k_ep][k_part][shot_start]
        except:
            try:
                return self.db_stitching_fgd_crop_initial[k_ed][k_ep][k_part][shot_start]
            except:
                pass
        return [0, 0, 0, 0]


    def set_fgd_crop(self, shot, geometry):
        k_ed = shot['k_ed']
        k_ep = shot['k_ep']
        k_part = shot['k_part']
        shot_start = shot['start']
        nested_dict_set(self.db_stitching_fgd_crop, geometry,
            k_ed, k_ep, k_part, shot_start)
        self.is_stitching_db_modified = True


    def discard_fgd_crop_modifications(self, shot):
        k_ed = shot['k_ed']
        k_ep = shot['k_ep']
        k_part = shot['k_part']
        shot_start = shot['start']
        try:
            del self.db_stitching_fgd_crop[k_ed][k_ep][k_part][shot_start]
        except:
            pass
        self.is_stitching_db_modified = True


    def move_fgd_crop_to_initial(self):
        # Move modifications from modified to initial
        self.db_stitching_fgd_crop_initial.update(deepcopy(self.db_stitching_fgd_crop))
        self.db_stitching_fgd_crop.clear()





    # Transformation matrix used to modify the background image
    #===========================================================================
    def initialize_db_for_transformation(self, db, k_ep, k_part):
        self.db_stitching_matrix_initial = get_initial_matrix(db, k_ep=k_ep, k_part=k_part)
        self.db_stitching_matrix = dict()


    def get_image_stitching_matrix(self, shot, frame_no):
        k_ed = shot['k_ed']
        k_ep = shot['k_ep']
        k_part = shot['k_part']
        shot_start = shot['start']
        try:
            return self.db_stitching_matrix[k_ed][k_ep][k_part][shot_start][frame_no]
        except:
            try:
                return self.db_stitching_matrix_initial[k_ed][k_ep][k_part][shot_start][frame_no]
            except:
                pass
        return None


    def set_image_stitching_matrix(self, shot, frame_no, matrix):
        k_ed = shot['k_ed']
        k_ep = shot['k_ep']
        k_part = shot['k_part']
        shot_start = shot['start']
        nested_dict_set(self.db_stitching_matrix, matrix,
            k_ed, k_ep, k_part, shot_start, frame_no)
        self.is_stitching_db_modified = True


    def discard_image_stitching_matrix_modifications(self, shot, frame_no):
        k_ed = shot['k_ed']
        k_ep = shot['k_ep']
        k_part = shot['k_part']
        shot_start = shot['start']
        try:
            del self.db_stitching_matrix[k_ed][k_ep][k_part][shot_start][frame_no]
        except:
            pass
        self.is_stitching_db_modified = True


    def discard_shot_image_stitching_matrix_modifications(self, shot):
        k_ed = shot['k_ed']
        k_ep = shot['k_ep']
        k_part = shot['k_part']
        shot_start = shot['start']
        try:
            del self.db_stitching_matrix[k_ed][k_ep][k_part][shot_start]
        except:
            pass
        self.is_stitching_db_modified = True


    def move_image_stitching_matrix_to_initial(self):
        # Move modifications from modified to initial
        self.db_stitching_matrix_initial.update(deepcopy(self.db_stitching_matrix))
        self.db_stitching_matrix.clear()





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
                m = self.get_image_stitching_transformation(k_shot_no, frame_no=f_no)
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