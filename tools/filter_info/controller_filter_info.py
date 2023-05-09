# -*- coding: utf-8 -*-
import sys
sys.path.append("scripts")

import collections
import configparser
import re
import os.path
from pathlib import Path
from pprint import pprint

from PySide6.QtCore import (
    QObject,
    Signal,
)

from filter_info.preferences import Preferences
from utils.pretty_print import *

TEMPLATE_SHOT_EPISODE = "^(ep\d{2})_([a-z_]+)_(\d{3})__([a-z0]*)__([a-z0-9]{7}).*"
TEMPLATE_SHOT_G_DEBUT_FIN = "^(g_[a-z]+)_(\d{3})__([a-z0]*)_(ep\d{2})__([a-z0-9]{7}).*"
TEMPLATE_SHOT_G = "^(ep\d{2})_(g_[a-z]+)_(\d{3})__([a-z0]*)_(ep\d{2})__([a-z0-9]{7}).*"
TEMPLATE_IMG = "^(ep\d{2})_(\d{5})__([a-z0]*)__(\d{2})_([a-z0-9]{7}).*"


class Controller_filter_info(QObject):
    signal_refresh_filters = Signal(dict)


    def __init__(self):
        super(Controller_filter_info, self).__init__()
        self.view = None

        # Load saved preferences
        self.preferences = Preferences()

        # Variables

    def load_file(self, filepath):
        if filepath is not None:
            self.event_new_file(filepath=filepath)


    def exit(self):
        # print("%s:exit" % (__name__))
        pass

    def exit(self):
        # print("%s:exit" % (__name__))
        p = self.view.get_preferences()
        self.preferences.save(p)
        # print("model: exit")


    def get_preferences(self):
        p = self.preferences.get_preferences()
        return p


    def save_preferences(self, preferences:dict):
        preferences = self.view.get_preferences()
        self.preferences.save(preferences)


    def set_view(self, view):
        self.view = view


    def event_new_file(self, filepath=''):
        print("dropped %s" % (filepath))

        # Is file or folder
        if os.path.isdir(filepath):
            return

        filepath = Path(filepath)
        extension = filepath.suffix

        # Extension
        if extension not in ['.mkv', '.png']:
            return

        # Filename
        filename = filepath.stem

        # File properties
        file_properties = {'hash': None}

        if extension == '.mkv':
            properties = re.match(re.compile(TEMPLATE_SHOT_EPISODE), filename)
            if properties is not None:
                file_properties = {
                    'k_ed': properties.group(4),
                    'k_ep': properties.group(1),
                    'k_part': properties.group(2),
                    'shot_no': int(properties.group(3)),
                    'hash': properties.group(5),
                }

            if file_properties['hash'] is None:
                properties = re.match(re.compile(TEMPLATE_SHOT_G_DEBUT_FIN), filename)
                if properties is not None:
                    file_properties = {
                        'k_ed': properties.group(3),
                        'k_ep': properties.group(4),
                        'k_part': properties.group(1),
                        'shot_no': int(properties.group(2)),
                        'hash': properties.group(5),
                    }

            if file_properties['hash'] is None:
                properties = re.match(re.compile(TEMPLATE_SHOT_G), filename)
                if properties is not None:
                    file_properties = {
                        'k_ed': properties.group(5),
                        'k_ep': properties.group(5),
                        'k_part': properties.group(2),
                        'shot_no': int(properties.group(3)),
                        'hash': properties.group(6),
                    }

            if file_properties['hash'] is None:
                print_orange(f"Cannot extract properties from {filename}: pattern")


        elif extension == '.png':
            properties = re.match(re.compile(TEMPLATE_IMG), filename)
            if properties is not None:
                file_properties = {
                    'k_ed': properties.group(3),
                    'k_ep': properties.group(1),
                    'k_part': filepath.parent.parent.name,
                    'shot_no': int(filepath.parent.name),
                    'frame_no': properties.group(2),
                    'step_no': properties.group(4),
                    'hash': properties.group(5),
                }
            if file_properties['hash'] is None:
                print_orange("Cannot extract properties from [%s]" % (filename))

        # Use a short filepath
        file_properties.update({
            'filename': filepath.name,
            'folder': "%s/%s/" % (
                filepath.parent.parent.name,
                filepath.parent.name)
        })

        # Get filters from hash
        file_properties['filters'] = self.get_filters_from_hash(file_properties)

        self.signal_refresh_filters.emit(file_properties)



    def get_filters_from_hash(self, file_properties):
        if file_properties['hash'] is None:
            return None

        # log file
        filepath_hashes = os.path.normpath(os.path.join(
            "hashes",
            "%s_hash.ini" % (file_properties['k_ep'])
        ))
        print_green("hashes: %s" % (filepath_hashes))

        # Read log file
        if os.path.exists(filepath_hashes):
            config_hashes = configparser.ConfigParser(dict_type=collections.OrderedDict)
            config_hashes.read(filepath_hashes)
        else:
            print_orange("Error: log file not found: %s" % (filepath_hashes))

        filters = list()

        hash = file_properties['hash']
        do_break = False
        i = 0
        while i < 99 and not do_break:
            i += 1
            # Max 99 filters
            value_str = config_hashes.get('md5', hash)
            print("key=%s, value_str=[%s]" % (hash, value_str))
            output_hash = hash

            is_found = False
            properties = re.match(re.compile("^\"([a-z0-9]{7}),([^\"]+)\"$"), value_str)
            if properties is not None:
                hash = properties.group(1)
                filter_str = properties.group(2)
                is_found = True

            if not is_found:
                properties = re.match(re.compile("^\"([a-z0-9]{7})_[^,]+,([^\"]+)\"$"), value_str)
                if properties is not None:
                    hash = properties.group(1)
                    filter_str = properties.group(2)
                    is_found = True

            if not is_found:
                properties = re.match(re.compile("^\"([^\"]+)\"$"), value_str)
                if properties is not None:
                    filter_str = properties.group(1)
                    do_break = True
                    is_found = True

            if not is_found:
                print_yellow("error: [%s]" % (value_str))

            filters.insert(0, {
                'filter_str': filter_str,
                'hash': output_hash
            })


        # Avisynth
        filter_str = filters[0]['filter_str']
        filter_str = filter_str.replace(';', ';\n')
        filters[0]['filter_str'] = filter_str

        # Other filters
        for no in range(1, len(filters)):
            filter_str = filters[no]['filter_str']
            filter_str = filter_str.replace(',', ',\n                ')
            filters[no]['filter_str'] = filter_str

        return filters

