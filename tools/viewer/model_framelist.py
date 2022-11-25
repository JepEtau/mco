# -*- coding: utf-8 -*-

from copy import deepcopy
from pprint import pprint

from viewer.model_framelist_common import Model_framelist_common
from models.model_database import Model_database

class Model_framelist(Model_framelist_common):

    def __init__(self):
        super(Model_framelist, self).__init__()
        self.filter_by = {
            'editions': list(),
            'steps': list(),
            'filter_ids': list()
        }
        self.model_database = Model_database()
        db = self.model_database.database()
        self.path_images = db['common']['directories']['frames']


    def get_images_path(self):
        return self.path_images


    def consolidate_database(self, k_ep, k_part):
        self.model_database.consolidate_database(
            k_ep, k_part,
            do_parse_curves=False,
            do_parse_replace=False,
            do_parse_geometry=False,
            do_parse_stitching=False,
            apply_patch_for_study=True)


    def get_hide_struct(self):
        # Update the filter_by by removing
        # unused values
        new_filter_by = {
            'editions': list(),
            'steps': list(),
            'filter_ids': list()
        }
        # edition
        current_editions = self.editions()
        for e in self.filter_by['editions']:
            if e in current_editions:
                new_filter_by['editions'].append(e)

        # steps: static list
        new_filter_by['steps'] = self.filter_by['steps'].copy()

        # filter_ids
        current_filter_ids = self.filter_ids()
        for f in self.filter_by['filter_ids']:
            if f in current_filter_ids:
                new_filter_by['filter_ids'].append(f)

        return new_filter_by


    def get_filtered_imagelist(self):
        images = list()

        for k, f in self.frames.items():
            if f['k_ed'] in self.filter_by['editions']:
                continue
            if f['step'] in self.filter_by['steps']:
                continue
            if f['filter_id'] in self.filter_by['filter_ids']:
                continue

            # Add filtering
            images.append(k)

        images.sort()
        return images



    def append(self, k_ep, k_part, filename):
        self.__append__(k_ep, k_part, filename)
