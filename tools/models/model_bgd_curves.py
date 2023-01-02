# -*- coding: utf-8 -*-

import sys
sys.path.append('../scripts')

from copy import deepcopy

from pprint import pprint
from logger import log

from parsers.parser_stitching import (
    parse_bgd_curves_database,
    get_bgd_curves_selection,
)


from utils.get_curves import (
    calculate_channel_lut_for_stitching,
)
from utils.common import (
    K_GENERIQUES,
    nested_dict_get,
    nested_dict_set,
)


class Model_bgd_curves():

    def __init__(self):
        # super(self).__init__(self)

        # The db contains curves for each shot no.
        # Warning: the bgd edition is fixed. If needed, this can be modified to
        # be similar to the curves class but it not required at this moment

        # self.db_stitching_shots_curves_initial = dict()
        # self.db_stitching_shots_curves = dict()

        self.is_bgd_curves_db_modified = False
        self.is_bgd_curves_selection_db_modified = False


    def initialize_db_for_bgd_curves(self, db, k_ep, k_part):
        # This function is used by the video editor
        # which uses the consolidated shots
        self.initialize_bgd_curves_library(db=db, k_ep=k_ep, k_part=k_part)
        # pprint(self.db_bgd_curves_library_initial)
        if k_ep.startswith('ep'):
            # if k_part in ['g_asuivre', 'g_reportage']:
            #     k_ep_ref = db[k_part]['target']['video']['src']['k_ep']
            #     self.db_bgd_curves_selection_initial = get_initial_curves_selection(db, k_ep=k_ep_ref, k_part=k_part)
            # else:
            self.db_bgd_curves_selection_initial = get_bgd_curves_selection(db, k_ep=k_ep, k_part=k_part)
        else:
            self.db_bgd_curves_selection_initial = get_bgd_curves_selection(db, k_ep=k_ep, k_part=k_part)
        self.db_bgd_curves_selection = dict()


    def initialize_bgd_curves_selection(self, shotlist, k_part=''):
        # This function is used by the curves editor
        # which does not use the consolidate and target shots (only src)
        log.info("initialize bgd curves selection for each shot")
        # shotlist = self.framelist.get_shotlist()
        if k_part == '':
            k_part = self.current_selection['k_part']

        self.db_bgd_curves_selection_initial = dict()
        for k_ed in shotlist.keys():
                for k_ep in shotlist[k_ed].keys():
                    for shot_no in shotlist[k_ed][k_ep].keys():
                        shot = shotlist[k_ed][k_ep][shot_no]
                        if shot['stitching']['curves'] is not None:
                            nested_dict_set(self.db_bgd_curves_selection_initial, shot['stitching']['curves'],
                                k_ed, k_ep, k_part, shot['start'])
        self.db_bgd_curves_selection = dict()


    def initialize_bgd_curves_library(self, db, k_ep, k_part):
        if k_part in K_GENERIQUES:
            print("initialize_bgd_curves_library: not supported for k_part=%s" % (k_part))
        else:
            self.db_bgd_curves_library_initial = parse_bgd_curves_database(db=db, k_ep=k_ep)
        self.db_bgd_curves_library = dict()



    # RGB curves
    def get_shot_bgd_curves_selection(self, db, shot) -> dict:
        # Get the curves associated to this shot
        k_ed = shot['k_ed']
        k_ep = shot['k_ep']
        k_part = shot['k_part']
        shot_start = shot['start']
        # print("model: self.db_bgd_curves_selection_initial %s:%s:%s:%s" % (k_ed, k_ep, k_part, shot_start))
        try: shot_bgd_curves = self.db_bgd_curves_selection[k_ed][k_ep][k_part][shot_start]
        except:
            try: shot_bgd_curves = self.db_bgd_curves_selection_initial[k_ed][k_ep][k_part][shot_start]
            except: return None

        if 'k_curves' not in shot_bgd_curves.keys() or shot_bgd_curves['k_curves'] == '':
            # This shot uses new RGB curves which are not yet been saved in the library
            return shot_bgd_curves

        # Get the curves from the library
        k_ep_or_g = k_part if k_part in K_GENERIQUES else k_ep
        curves = self.get_bgd_curves(db, k_ep_or_g, shot_bgd_curves['k_curves'])
        return curves



    def set_shot_bgd_channels(self, shot, rgb_channels):
        k_ed = shot['k_ed']
        k_ep = shot['k_ep']
        k_part = shot['k_part']
        shot_start = shot['start']
        # Get the curves frome the db_chot_curves. it points to the curves
        # stored in the db_bgd_curves_library
        print("set_shot_bgd_channels: %s:%s:%s:%d" % (k_ed, k_ep, k_part, shot_start))
        try:
            shot_bgd_curves = self.db_bgd_curves_selection[k_ed][k_ep][k_part][shot_start]
        except:
            try:
                shot_bgd_curves = self.db_bgd_curves_selection_initial[k_ed][k_ep][k_part][shot_start]
            except:
                print("these curves does not exist: create an empty one in the db_shot")
                curves = ({
                    'k_curves': '',
                    'channels': deepcopy(rgb_channels),
                    'lut': calculate_channel_lut_for_stitching(rgb_channels),
                    'is_modified': True,
                })
                nested_dict_set(self.db_bgd_curves_selection, curves, k_ed, k_ep, k_part, shot_start)
                self.is_bgd_curves_db_modified = True
                return

        if shot_bgd_curves['k_curves'] == '':
            # Curves is not yet saved in library
            self.db_bgd_curves_selection[k_ed][k_ep][k_part][shot_start].update({
                'channels': deepcopy(rgb_channels),
                'lut': calculate_channel_lut_for_stitching(rgb_channels),
                'is_modified': True,
            })
            self.is_bgd_curves_db_modified = True
            return

        # Modify the curves in the library
        print("these curves exists: modify [%s]" % (shot_bgd_curves['k_curves']))
        is_modified = self.set_bgd_curves(k_curves=shot_bgd_curves['k_curves'], rgb_channels=rgb_channels)
        if not is_modified:
            # No curves found for this k_curves, create a new one in the shot
            print("add it to the modified db")
            bgd_curves = ({
                'k_curves': '',
                'channels': deepcopy(rgb_channels),
                'lut': calculate_channel_lut_for_stitching(rgb_channels),
                'is_modified': True,
            })
            nested_dict_set(self.db_bgd_curves_selection, bgd_curves, k_ed, k_ep, k_part, shot_start)

        self.is_bgd_curves_db_modified = True



    def set_bgd_curves_selection(self, db, shot:dict, k_curves:str):
        k_ed = shot['k_ed']
        k_ep = shot['k_ep']
        k_part = shot['k_part']
        shot_start = shot['start']

        # Get the curves from the library
        k_ep_or_g = k_part if k_part in K_GENERIQUES else k_ep
        curves = self.get_bgd_curves(db, k_ep_or_g, k_curves)

        # Set the modified shot curves
        nested_dict_set(self.db_bgd_curves_selection, curves, k_ed, k_ep, k_part, shot_start)

        self.is_bgd_curves_selection_db_modified = True



    def discard_bgd_curves_selection(self, db, shot:dict):
        k_ed = shot['k_ed']
        k_ep = shot['k_ep']
        k_part = shot['k_part']
        shot_start = shot['start']
        shot_no = shot['no']
        log.info("discard_bgd_curves_selection %s:%s:%s:%s" % (k_ed, k_ep, k_part, shot_start))

        # Access directly to the modified, because the get_curves_selection function
        # may return the curves from the initial db
        # If there is a problem, this will have to be corrected
        try:
            k_curves_current = self.db_bgd_curves_selection[k_ed][k_ep][k_part][shot_start]
        except:
            print("Error: %s:%s:%s:%s: current curves are not found in the db_bgd_curves_selection (modified db)" % (k_ed, k_ep, k_part, shot_start))
            # pprint(self.db_bgd_curves_selection)
            # raise Exception()
            pass
        del self.db_bgd_curves_selection[k_ed][k_ep][k_part][shot_start]



    def remove_bgd_curves_selection(self, db, shot:dict):
        k_ed = shot['k_ed']
        k_ep = shot['k_ep']
        k_part = shot['k_part']
        shot_start = shot['start']

        # Set the modified shot curves
        nested_dict_set(self.db_bgd_curves_selection, {'k_curves': ''}, k_ed, k_ep, k_part, shot_start)

        self.is_bgd_curves_selection_db_modified = True


    # RGB curves library
    def get_library_bgd_curves(self):
        bgd_curves_library = dict()
        for k in self.db_bgd_curves_library_initial.keys():
            if k in self.db_bgd_curves_library.keys():
                # These curves are modified or deleted
                if not 'deleted' in self.db_bgd_curves_library[k].keys():
                    # These curves are modified
                    bgd_curves_library[k] = True
            else:
                bgd_curves_library[k] = False
        return bgd_curves_library



    def get_bgd_curves(self, db, k_ep_or_g:str, k_curves:str):
        # Find these curves in the libraries
        try: bgd_curves = self.db_bgd_curves_library[k_curves]
        except:
            try: bgd_curves = self.db_bgd_curves_library_initial[k_curves]
            except: bgd_curves = None

        # If not found, add these curves to the library as it may be not in the same k_ep
        if bgd_curves is None:
            # Create a curve structure
            self.db_bgd_curves_library_initial[k_curves] = {
                    'k_curves': k_curves,
                    'channels': None,
                    'lut': None,
                    'shots': []
            }
            bgd_curves = self.db_bgd_curves_library_initial[k_curves]

        # Parse the file if not already done
        if bgd_curves['channels'] is None:
            print("error: get_bgd_curves: channels for [%s] is not found in the library" % (k_curves))

        if bgd_curves['channels'] is None:
            # The curves file has not been found
            log.warning("The curves have not been found")
            bgd_curves = None
        else:
            if bgd_curves['lut'] is None:
                bgd_curves['lut'] = calculate_channel_lut_for_stitching(bgd_curves['channels'])
        return bgd_curves



    def set_bgd_curves(self, k_curves:str, rgb_channels):
        print("set_bgd_curves")
        try:
            bgd_curves = self.db_bgd_curves_library[k_curves]
        except:
            try:
                print("set_curves: copy from initial to modified")
                self.db_bgd_curves_library[k_curves] = deepcopy(self.db_bgd_curves_library_initial[k_curves])
                bgd_curves = self.db_bgd_curves_library[k_curves]
            except:
                print("[%s] does not exists neither in library not in initial library" % (k_curves))
                return False

        bgd_curves.update({
            'channels': deepcopy(rgb_channels),
            'lut': calculate_channel_lut_for_stitching(rgb_channels),
            'is_modified': True,
        })
        self.is_bgd_curves_db_modified = True
        return True



    def discard_bgd_curves_modifications(self, k_curves):
        print("WARNING: discard RGB curves modification")
        try:
            del self.db_bgd_curves_library[k_curves]
        except:
            print("Error: discard_curves_modifications: failed")
            pass



    def save_all_curves(self, k_ep_or_g):
        print("TODO: save_all_curves")
        # for bgd_curves in self.db_curves_library.values():
        #     self.save_curves_as(k_ep_or_g=k_ep_or_g, curves=curves)


    def save_bgd_curves_as(self, db, k_ep_or_g, curves):
        print("TODO: save_rgb_bgd_curves_as")




    def save_shot_bgd_curves_selection(self, db, shot):
        if not self.is_bgd_curves_selection_db_modified:
            return True
        print("TODO: save_shot_bgd_curves_selection")









#-----------------------------------------------------------------------------------
#----------------------------- previous --------------------------------------------
#-----------------------------------------------------------------------------------













    # def get_bgd_curves_names(self) -> dict:
    #     names = list(self.db_bgd_curves_initial.keys())
    #     names += list(self.db_bgd_curves.keys())
    #     names_sorted = sorted(list(dict.fromkeys(names)))
    #     return {
    #         'all':names_sorted,
    #         'modified': self.db_bgd_curves.keys()
    #     }


    # def discard_bgd_curves_modifications(self, k_curves):
    #     try:
    #         del self.db_bgd_curves[k_curves]
    #     except:
    #         print("Error: discard_curves_modifications: failed")
    #         pass


    # def get_bgd_curves(self, k_curves):
    #     # Return a dict of k_curves and (Curve, lut) for each channel
    #     try:
    #         curves = self.db_bgd_curves[k_curves]
    #     except:
    #         try: curves = self.db_bgd_curves_initial[k_curves]
    #         except: return None

    #     if curves['lut'] is None:
    #         curves['lut'] = calculate_channel_lut_for_stitching(curves['channels'])
    #     return curves



    # def modify_bgd_curves(self, curves:dict):
    #     k_curves = curves['k_curves']
    #     if k_curves != '':
    #         self.db_bgd_curves[k_curves] = deepcopy(curves)
    #         self.is_bgd_curves_db_modified = True


    # def select_shot_bgd_curves(self, shot_no, k_curves):
    #     if shot_no not in self.db_stitching_shots_curves.keys():
    #         self.db_stitching_shots_curves[shot_no] = dict()

    #     log.info("select_shot_bgd_curves: shot_no. %d, k_curves=%s" % (shot_no, k_curves))
    #     self.db_stitching_shots_curves[shot_no] = self.get_bgd_curves(k_curves)


    # def set_shot_bgd_curves_as_initial(self, shot_no):
    #     # Move from modified to initial db
    #     if shot_no in self.db_stitching_shots_curves.keys():
    #         self.db_stitching_shots_curves_initial[shot_no] = deepcopy(self.db_stitching_shots_curves[shot_no])
    #         del self.db_stitching_shots_curves[shot_no]


    # def reset_shot_bgd_curves_selection(self, shot_no):
    #     if shot_no in self.db_stitching_shots_curves.keys():
    #         del self.db_stitching_shots_curves[shot_no]


    # def get_shot_bgd_curves(self, db, shot) -> dict:
    #     # Get the curves associated to this shot
    #     k_ed = shot['k_ed']
    #     k_ep = shot['k_ep']
    #     k_part = shot['k_part']
    #     shot_start = shot['start']

    #     # print("model: self.db_bgd_curves_selection_initial %s:%s:%s:%s" % (k_ed, k_ep, k_part, shot_start))
    #     try: shot_bgd_curves = self.db_bgd_curves_selection[k_ed][k_ep][k_part][shot_start]
    #     except:
    #         try: shot_bgd_curves = self.db_bgd_curves_selection_initial[k_ed][k_ep][k_part][shot_start]
    #         except: return None

    #     print("get_shot_bgd_curves for shot_no: %d" % (shot_no))
    #     try: shot = self.db_stitching_shots_curves[shot_no]
    #     except:
    #         try: shot = self.db_stitching_shots_curves_initial[shot_no]
    #         except:
    #             print("\t-> None")
    #             return None

    #     if shot is None:
    #         print("\t-> removed from initial")
    #         return None

    #     k_curves = shot['k_curves']
    #     if k_curves != '':
    #         # Get the curve from the global database
    #         print("\t-> %s (get_bgd_curves)" % (k_curves))
    #         return self.get_bgd_curves(k_curves)

    #     points = shot['points']
    #     if points is not None:
    #         print("\t-> %s" % (k_curves))
    #         return {
    #             'k_curves': k_curves,
    #             'points': points,
    #             'lut': shot['lut'],
    #         }
    #     print("\t-> None")
    #     return None

    # def get_modified_shot_bgd_curves(self):
    #     return self.db_stitching_shots_curves

    # def set_shot_bgd_curves(self, shot_no, curves_dict):
    #     # curves_dict:
    #     #     'k_curves' : curve name
    #     #     'points': dict of Curves objects for each r,g,b channel
    #     # if k_curve == '', this means that the curve jas not yet been "saved as"
    #     if shot_no not in self.db_stitching_shots_curves.keys():
    #         self.db_stitching_shots_curves[shot_no] = dict()

    #     # if 'curves' not in self.db_stitching_shots_curves[shot_no].keys():
    #     #     # Create a new curve for this shot
    #     #     self.db_stitching_shots_curves[shot_no] = deepcopy(bgd_CURVES_DEFAULT)

    #     print("set_shot_bgd_curves")
    #     # pprint(curves_dict)

    #     self.db_stitching_shots_curves[shot_no] = {
    #         'k_curves': curves_dict['k_curves'],
    #         'points': curves_dict['points'],
    #         'lut': curves_dict['lut']
    #     }
    #     self.is_stitching_db_modified = True

    #     if curves_dict['k_curves'] != '':
    #         self.modify_bgd_curves(curves_dict)
    #     else:
    #         print("no selected curves")


    # def remove_shot_bgd_curves(self, shot_no):
    #     # Remove the curves of this shot
    #     print("remove_shot_bgd_curves: %d" % (shot_no))
    #     print(self.db_stitching_shots_curves_initial.keys())
    #     print("---")
    #     print(self.db_stitching_shots_curves.keys())
    #     print("")
    #     if shot_no in self.db_stitching_shots_curves.keys():
    #         if shot_no in self.db_stitching_shots_curves_initial.keys():
    #             # Force to none to overwrite the initial curves
    #             # del self.db_stitching_shots_curves[shot_no]
    #             # self.db_stitching_shots_curves[shot_no] = {'k_curves': ''}
    #             self.db_stitching_shots_curves[shot_no] = None
    #             log.info("Force to none to overwrite the initial curves")
    #         else:
    #             del self.db_stitching_shots_curves[shot_no]
    #     elif shot_no in self.db_stitching_shots_curves_initial.keys():
    #             # Force to none to overwrite the initial curves
    #             self.db_stitching_shots_curves[shot_no] = None
    #             log.info("Force to none to overwrite the initial curves")

