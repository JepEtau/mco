# -*- coding: utf-8 -*-

import sys
sys.path.append('../scripts')

from copy import deepcopy

from pprint import pprint
from logger import log

from parsers.parser_stitching import (
    parse_stitching_curves_database
)


from utils.get_curves import (
    calculate_channel_lut_for_stitching,
)



class Model_stitching_curves():

    def __init__(self):
        # super(self).__init__(self)

        # The db contains curves for each shot no.
        # Warning: the bgd edition is fixed. If needed, this can be modified to
        # be similar to the curves class but it not required at this moment

        self.db_stitching_shots_curves_initial = dict()
        self.db_stitching_shots_curves = dict()
        self.is_stitching_curves_db_modified = False


    def parse_stitching_curves_database(self, k_ep):
        # Create 2 db, one for the initial, the second for modified curves
        self.db_stitching_curves_initial = parse_stitching_curves_database(
            self.global_database, k_ep=k_ep)
        self.db_stitching_curves = dict()


    def get_stitching_curves_names(self) -> dict:
        names = list(self.db_stitching_curves_initial.keys())
        names += list(self.db_stitching_curves.keys())
        names_sorted = sorted(list(dict.fromkeys(names)))
        return {
            'all':names_sorted,
            'modified': self.db_stitching_curves.keys()
        }


    def discard_stitching_curves_modifications(self, k_curves):
        try:
            del self.db_stitching_curves[k_curves]
        except:
            print("Error: discard_curves_modifications: failed")
            pass


    def get_stitching_curves(self, k_curves):
        # Return a dict of k_curves and (Curve, lut) for each channel
        try:
            curves = self.db_stitching_curves[k_curves]
        except:
            try: curves = self.db_stitching_curves_initial[k_curves]
            except: return None

        if curves['lut'] is None:
            curves['lut'] = calculate_channel_lut_for_stitching(curves['channels'])
        return curves



    def modify_stitching_curves(self, curves:dict):
        k_curves = curves['k_curves']
        if k_curves != '':
            self.db_stitching_curves[k_curves] = deepcopy(curves)
            self.is_stitching_curves_db_modified = True


    def select_shot_stitching_curves(self, shot_no, k_curves):
        if shot_no not in self.db_stitching_shots_curves.keys():
            self.db_stitching_shots_curves[shot_no] = dict()

        log.info("select_shot_stitching_curves: shot_no. %d, k_curves=%s" % (shot_no, k_curves))
        self.db_stitching_shots_curves[shot_no] = self.get_stitching_curves(k_curves)


    def set_shot_stitching_curves_as_initial(self, shot_no):
        # Move from modified to initial db
        if shot_no in self.db_stitching_shots_curves.keys():
            self.db_stitching_shots_curves_initial[shot_no] = deepcopy(self.db_stitching_shots_curves[shot_no])
            del self.db_stitching_shots_curves[shot_no]


    def reset_shot_stitching_curves_selection(self, shot_no):
        if shot_no in self.db_stitching_shots_curves.keys():
            del self.db_stitching_shots_curves[shot_no]


    def get_shot_stitching_curves(self, shot_no):
        print("get_shot_stitching_curves for shot_no: %d" % (shot_no))
        try: shot = self.db_stitching_shots_curves[shot_no]
        except:
            try: shot = self.db_stitching_shots_curves_initial[shot_no]
            except:
                print("\t-> None")
                return None

        if shot is None:
            print("\t-> removed from initial")
            return None

        k_curves = shot['k_curves']
        if k_curves != '':
            # Get the curve from the global database
            print("\t-> %s (get_stitching_curves)" % (k_curves))
            return self.get_stitching_curves(k_curves)

        points = shot['points']
        if points is not None:
            print("\t-> %s" % (k_curves))
            return {
                'k_curves': k_curves,
                'points': points,
                'lut': shot['lut'],
            }
        print("\t-> None")
        return None

    def get_modified_shot_stitching_curves(self):
        return self.db_stitching_shots_curves

    def set_shot_stitching_curves(self, shot_no, curves_dict):
        # curves_dict:
        #     'k_curves' : curve name
        #     'points': dict of Curves objects for each r,g,b channel
        # if k_curve == '', this means that the curve jas not yet been "saved as"
        if shot_no not in self.db_stitching_shots_curves.keys():
            self.db_stitching_shots_curves[shot_no] = dict()

        # if 'curves' not in self.db_stitching_shots_curves[shot_no].keys():
        #     # Create a new curve for this shot
        #     self.db_stitching_shots_curves[shot_no] = deepcopy(STITCHING_CURVES_DEFAULT)

        print("set_shot_stitching_curves")
        # pprint(curves_dict)

        self.db_stitching_shots_curves[shot_no] = {
            'k_curves': curves_dict['k_curves'],
            'points': curves_dict['points'],
            'lut': curves_dict['lut']
        }
        self.is_stitching_db_modified = True

        if curves_dict['k_curves'] != '':
            self.modify_stitching_curves(curves_dict)
        else:
            print("no selected curves")


    def remove_shot_stitching_curves(self, shot_no):
        # Remove the curves of this shot
        print("remove_shot_stitching_curves: %d" % (shot_no))
        print(self.db_stitching_shots_curves_initial.keys())
        print("---")
        print(self.db_stitching_shots_curves.keys())
        print("")
        if shot_no in self.db_stitching_shots_curves.keys():
            if shot_no in self.db_stitching_shots_curves_initial.keys():
                # Force to none to overwrite the initial curves
                # del self.db_stitching_shots_curves[shot_no]
                # self.db_stitching_shots_curves[shot_no] = {'k_curves': ''}
                self.db_stitching_shots_curves[shot_no] = None
                log.info("Force to none to overwrite the initial curves")
            else:
                del self.db_stitching_shots_curves[shot_no]
        elif shot_no in self.db_stitching_shots_curves_initial.keys():
                # Force to none to overwrite the initial curves
                self.db_stitching_shots_curves[shot_no] = None
                log.info("Force to none to overwrite the initial curves")

