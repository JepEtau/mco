# -*- coding: utf-8 -*-

from PySide6.QtCore import Signal
from PySide6.QtCore import QObject

from copy import deepcopy
import gc
import os
import os.path

from pprint import pprint
import configparser
from pathlib import Path
from pathlib import PosixPath
import sys
import re
import collections
from logger import log
from models.model_database import Model_database

# from curves_editor.curves_history import Curves_history

sys.path.append('../scripts')
from utils.common import K_GENERIQUES, get_shot_from_frame_no_new
from parsers.parser_curves import parse_curves_file
from parsers.parser_curves import write_curves_file

from images.curve import Curve



class Model_curves(object):
    signal_curvesSelectionChanged = Signal()
    signal_curvesResourcesChanged = Signal()

    def __init__(self, model_database:Model_database):
        super(Model_curves, self).__init__()

        self.model_database = model_database
        self.current_k_ep = ''
        self.shotlist = dict()



    def browse_curves_folder(self, k_ep_or_g=''):
        # Curves contained in the curves directory:
        #  filename, key but do not parse files (will be done dynamically)
        log.info("browse folder which contains curves: %s" % (k_ep_or_g))
        self.db_curves = dict()

        path_curves = self.model_database.get_curves_library_path()
        if not os.path.exists(path_curves):
            log.error("%s does not exist" % (path_curves))
            self.current_k_ep = ''
            return

        # Browse curves in the subdirectories
        if os.path.exists(os.path.join(path_curves, k_ep_or_g)):
            for f in os.listdir(os.path.join(path_curves, k_ep_or_g)):
                # print("\t%s" % (f))
                if f.endswith(".crv"):
                    # Create an element for each curve
                    k_curves = os.path.splitext(f)[0]
                    self.db_curves[k_curves] = {
                        'filepath': os.path.join(k_ep_or_g, f),
                        'k_curves': k_curves,
                        'channels': None,
                        'shots': []
                    }

        # Browse curves in the common directory
        for f in os.listdir(path_curves):
            if f.endswith(".crv"):
                # Create an element for each curve
                k_curves = os.path.splitext(f)[0]
                if k_curves in self.db_curves.keys():
                    # Do not add if already in base
                    continue
                self.db_curves[k_curves] = {
                    'filepath': f,
                    'k_curves': k_curves,
                    'channels': None,
                    'shots': []
                }

        self.current_k_ep = k_ep_or_g
        gc.collect()


    def initialize_shots_per_curves(self, shotlist):
        """ This function creates a list of shots for every curves
        It has to be called once the directory is changed.
        It contains all shots for each curves and not only for the shots that are listed in self.shotlist
        """
        self.shots_per_curves = dict()
        for k_no in shotlist.keys():
            for k_ed in shotlist[k_no]:
                for k_ep, k_curve in shotlist[k_no][k_ed].items():
                    if k_curve != '':
                        if k_curve not in self.shots_per_curves.keys():
                            self.shots_per_curves[k_curve] = list()
                        self.shots_per_curves[k_curve].append(k_no)
        # print("%s.initialize_shots_per_curves" % (__name__))
        # pprint(self.shots_per_curves)


    def names(self):
        return sorted(self.db_curves.keys())


    def set_curves_to_shot(self, shot_no, k_curves, k_ed, k_ep):
        """ Associate curves to the specified shot
        """
        log.info("curves for shot no. %d has been changed to %s" % (shot_no, k_curves))

        # Remove the shot no from the shots_per_curves list
        previous_k_curves = self.shotlist[shot_no][k_ed][k_ep]['k_curves']
        if previous_k_curves != '':
            self.shots_per_curves[previous_k_curves].remove(shot_no)

        # Append this shot to the list of shots for these curves
        self.shotlist[shot_no][k_ed][k_ep]['k_curves'] = k_curves

        if k_curves not in self.shots_per_curves.keys():
            self.shots_per_curves[k_curves] = list()
        self.shots_per_curves[k_curves].append(shot_no)

        # Order by shot no.
        self.shots_per_curves[k_curves] = sorted(self.shots_per_curves[k_curves])

        # Set a flag to indicate that this shot is modified
        self.mark_shot_as_modified(shot_no, k_ed, k_ep)


    def revert_modified_shot_using_k_curves(self, k_curves) -> bool:
        """Remove modification flag and returns True if the list is modified
        """
        is_modified = False
        for shot_no in self.shotlist.keys():
            for k_ed in self.shotlist[shot_no].keys():
                for k_ep in self.shotlist[shot_no][k_ed].keys():
                    item = self.shotlist[shot_no][k_ed][k_ep]
                    if item['k_curves'] == k_curves:
                        if item['is_modified']:
                            is_modified = True
                            item['is_modified'] = False
        return is_modified

    def mark_shot_as_modified(self, shot_no, k_ed, k_ep):
        # Set a flag to indicate that this shot is modified
        self.shotlist[shot_no][k_ed][k_ep]['is_modified'] = True


    def is_shot_modified(self, shot_no, k_ed, k_ep):
        return self.shotlist[shot_no][k_ed][k_ep]['is_modified']


    def get_modified_shots(self) -> list:
        modified_shots = list()
        for shot_no in self.shotlist.keys():
            is_modified = False
            for _k_ed in self.shotlist[shot_no].keys():
                for _k_ep in self.shotlist[shot_no][_k_ed].keys():
                    is_modified = is_modified or self.shotlist[shot_no][_k_ed][_k_ep]['is_modified']
            if is_modified:
                modified_shots.append(shot_no)
        return modified_shots


    def get_k_curves_from_shot_no(self, shot_no, k_ed, k_ep):
        return self.shotlist[shot_no][k_ed][k_ep]['k_curves']


    def get_initial_k_curves_from_shot_no(self, shot_no, k_ed, k_ep):
        initial_k_curves = self.shotlist[shot_no][k_ed][k_ep]['k_curves_initial']
        return initial_k_curves


    def get_curves_from_shot_no(self, shot_no, k_ed, k_ep):
        k_curve = self.shotlist[shot_no][k_ed][k_ep]['k_curves']
        log.info("(%s:%s) shot no. %d uses [%s]" % (k_ed, k_ep, shot_no, k_curve))
        if k_curve == '':
            return None
        return self.get_curves_from_name(k_curve=k_curve)


    def get_shots_from_k_curves(self, k_curves):
        """ Returns a list of shots that are using the same curves
        """
        if k_curves == '':
            return list()
        return self.shots_per_curves[k_curves]


    def get_curves_from_name(self, k_curve):
        """ Returns a dictionary which contains r,g,b,m channels
        """
        if k_curve == '':
            return None

        if self.db_curves[k_curve]['channels'] is None:
            # Parse the curve file if not already done
            log.info("parse curve file: %s" % (k_curve))
            channels = parse_curves_file(self.model_database.database(), self.current_k_ep, k_curve)
            self.db_curves[k_curve]['channels'] = channels

        return self.db_curves[k_curve]['channels']


    def backup_curves(self, k_curves, curves):
        log.info("model, append curves [%s]" % (k_curves))
        if k_curves in self.db_curves.keys():
            # print("%s.backup_curves: " % (__name__))
            # pprint(self.db_curves[k_curves], indent=8)
            self.db_curves[k_curves].update({
                'k_curves': k_curves,
                'channels': deepcopy(curves),
            })
            # print("-> ")
            # pprint(self.db_curves[k_curves], indent=8)

    def save_curves(self, curve_name, channels):
        log.info("model, save curves as [%s]" % (curve_name))
        # Do not copy the 'channels' as this will be done when reloading these curves
        # from the written files
        db = self.model_database.database()
        path_curves = db['common']['directories']['curves']
        if curve_name in self.db_curves.keys():
            # Overwrite
            self.db_curves[curve_name].update({
                'filepath': os.path.join(path_curves, self.current_k_ep, "%s.crv" % (curve_name)),
                'k_curves': curve_name,
                'channels': None,
            })
        else:
            self.db_curves[curve_name] = {
                'filepath': os.path.join(path_curves, self.current_k_ep, "%s.crv" % (curve_name)),
                'k_curves': curve_name,
                'channels': None,
                'shots': []
            }
        # Write the curves to a new curves file
        write_curves_file(
            filepath=self.db_curves[curve_name]['filepath'],
            channels=channels)

        gc.collect()


    def set_shotlist(self, shotlist:dict):
        self.shotlist = deepcopy(shotlist)
        for shot_no in self.shotlist.keys():
            for k_ed in shotlist[shot_no].keys():
                for k_ep, k_c in shotlist[shot_no][k_ed].items():
                    self.shotlist[shot_no][k_ed][k_ep] = {
                        'is_modified': False,
                        'k_curves': k_c,
                        'k_curves_initial': k_c,
                    }
        # print("%s.set_shotlist" % (__name__))
        # pprint(self.shotlist)
        # print("")


    def reset_shot_curve(self, shot_no, k_ed, k_ep):
        self.set_curves_to_shot(shot_no, self.shotlist[shot_no][k_ed][k_ep]['k_curves_initial'], k_ed, k_ep)
        self.shotlist[shot_no][k_ed][k_ep]['is_modified'] = False


    def reload_curves(self, k_curves):
        log.info("parse curve file: %s" % (k_curves))
        channels = parse_curves_file(PATH_CURVES, self.current_k_ep, k_curves)
        self.db_curves[k_curves]['channels'] = channels


    def get_all_todo_shots(self, k_ed, k_ep, k_part):
        db = self.model_database.database()
        shotlist = list()
        if k_part in K_GENERIQUES:
            db_video = db[k_part]['common']['video']

            # Append the shot no. if it has no or empty curve
            for shot in db_video['shots']:
                k_ed_src = shot['src']['k_ed']
                k_ep_src = shot['src']['k_ep']

                shot_src = db[k_ep_src][k_ed_src][k_part]['video']['shots'][shot['no']]
                if shot_src['curves'] is None:
                    shotlist.append(shot_src['no'])
                elif shot_src['curves']['k_curves'] == '':
                    shotlist.append(shot_src['no'])

        else:
            print("get_all_todo_shots: %s:%s:%s" % (k_ed, k_ep, k_part))
            db_video = db[k_ep][k_ed][k_part]['video']

            # Append the shot no. if it has no or empty curve
            for s in db_video['shots']:
                if s['curves'] is None:
                    shotlist.append(s['no'])
                elif s['curves']['k_curves'] == '':
                    shotlist.append(s['no'])

        return shotlist



    def save_curves_database(self, k_ep, k_part):
        log.info("save curves database")
        # print("\n%s.save_curves_database" % (__name__))
        db = self.model_database.database()

        # Open configuration file
        if k_part in K_GENERIQUES:
            filepath = os.path.join(db['common']['directories']['config'], k_part, "%s_curves.ini" % (k_part))
        else:
            filepath = os.path.join(db['common']['directories']['config'], k_ep, "%s_curves.ini" % (k_ep))
        if filepath.startswith("~/"):
            filepath = os.path.join(PosixPath(Path.home()), filepath[2:])

        # Parse the file
        if os.path.exists(filepath):
            config_curves = configparser.ConfigParser()
            config_curves.read(filepath)
        else:
            config_curves = configparser.ConfigParser({}, collections.OrderedDict)


        for shot_no in self.shotlist.keys():
            for _k_ed in self.shotlist[shot_no].keys():
                for _k_ep in self.shotlist[shot_no][_k_ed].keys():
                    shot = self.shotlist[shot_no][_k_ed][_k_ep]
                    # print("%s:%s:%s -> " % (_k_ed, k_part, shot_no), shot['is_modified'])

                    if shot['is_modified']:
                        k_section = '%s.%s.%s' % (_k_ed, _k_ep, k_part)
                        if not config_curves.has_section(k_section):
                            config_curves[k_section] = dict()

                        # Get shot from frame no.
                        shot_src = db[_k_ep][_k_ed][k_part]['video']['shots'][shot_no]
                        k_curves = shot['k_curves']
                        shot_start_str = str(shot_src['start'])
                        if k_curves == '' and config_curves.has_option(k_section, shot_start_str):
                            del config_curves[k_section][shot_start_str]
                        else:
                            config_curves.set(k_section, shot_start_str, k_curves)

                        # Update shotlist
                        shot['is_modified'] = False
                        shot['k_curves_initial'] = k_curves


        # Write to the database
        with open(filepath, 'w') as config_file:
            config_curves.write(config_file)

        self.is_curves_db_modified = False

