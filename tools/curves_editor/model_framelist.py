# -*- coding: utf-8 -*-
import sys
sys.path.append('../scripts')

import os
import os.path
from pprint import pprint
import gc
import re
from copy import deepcopy

from models.model_framelist_common import Model_framelist_common
from models.model_database import Model_database
from utils.common import (
    get_shot_from_frame_no_new,
    get_shot_no_from_frame_no,
    get_shot_from_frame_no,
)


class Model_framelist(Model_framelist_common):

    def __init__(self, model_database:Model_database):
        super(Model_framelist, self).__init__()
        self.filter_by = {
            'k_ed': '',
            'step': '',
            'filter_id': '',
            'shots': list()
        }
        self.available_filter_ids = list()
        self.model_database = model_database
        self.frames = dict()


    def get_shot_no_from_image_name(self, image_name):
        return self.frames[image_name]['shot_no']

    def get_images_path(self):
        return self.model_database.get_images_path()

    def shot_list(self):
        print("%s.shot_list" % (__name__))
        db = self.model_database.database()
        shots = dict()
        for k, frame in self.frames.items():
            if frame['shot_no'] not in shots.keys():
                k_ed = frame['k_ed']
                k_ep = frame['k_ep']
                k_part = frame['k_part']
                frame_no = frame['no']

                shot = get_shot_from_frame_no_new(db, frame_no, k_ed=k_ed, k_ep=k_ep, k_part=k_part)
                if False:
                    # Get shot from frame_no.
                    if k_part in K_GENERIQUES:
                        # print("%s.shot_list: k_ed=%s, k_ep=%s, k_part=%s" % (__name__, k_ed, k_ep, k_part))
                        # print(self.database[k_part].keys())
                        k_ed_ref = db[k_part]['common']['video']['reference']['k_ed']
                        shot = get_shot_from_frame_no(db[k_part][k_ed_ref], frame_no, k_part)
                    else:
                        shot = get_shot_from_frame_no(db[k_ep][k_ed], frame_no, k_part)

                    if shot is None:
                        print("%s.shot_list: k_ed=%s, k_ep=%s, k_part=%s" % (__name__, k_ed, k_ep, k_part))
                        pprint(shot)
                        sys.exit()
                        break

                # Add shot and associated curves to this structure
                if k_ed not in shots.keys():
                    shots[k_ed] = dict()
                if shot['curves'] is not None:
                    shots[k_ed][frame['shot_no']] = shot['curves']['k_curves']
                else:
                    shots[k_ed][frame['shot_no']] = ''
        pprint(shots)
        print("")
        return shots



    def shot_names(self):
        names = list()
        for k, f in self.frames.items():
            if f['shot_no'] not in names:
                names.append(f['shot_no'])
        names.sort()
        return names


    def get_selected_struct(self):
        # print("%s:get_selected_struct:" % (__name__))
        # pprint(self.filter_by)
        # Update the filter_by by removing
        # unused values
        new_filter_by = {
            'k_ed': '',
            'step': self.filter_by['step'],
            'filter_id': '',
            'shots': list()
        }
        # edition
        if self.filter_by['k_ed'] in self.editions():
            new_filter_by['k_ed'] = self.filter_by['k_ed']

        # filter_id
        if self.filter_by['filter_id'] in self.filter_ids():
            new_filter_by['filter_id'] = self.filter_by['filter_id']

        # current_filter_ids = self.filter_ids()
        # for f in self.filter_by['filter_ids']:
        #     if f in current_filter_ids:
        #         new_filter_by['filter_ids'].append(f)

        # shots
        current_shots = self.shot_names()
        for f in self.filter_by['shots']:
            if f in current_shots:
                new_filter_by['shots'].append(f)
        # print("->")
        # pprint(new_filter_by)
        # sys.exit()
        return new_filter_by



    def get_filtered_imagelist(self):
        # print("\n%s:get_filtered_imagelist:" % (__name__))
        # pprint(self.filter_by)
        # print("\n")

        images = list()
        self.available_filter_ids.clear()
        for k, f in self.frames.items():
            if (self.filter_by['k_ed'] != ''
                and f['k_ed'] != self.filter_by['k_ed']):
                # print("%s -> discard (edition %s)" % (f['filepath'], f['k_ed']))
                continue

            if (self.filter_by['step'] != ''
                and f['step'] != self.filter_by['step']):
                # print("%s -> discard (step %s)" % (f['filepath'], f['step']))
                continue

            if f['filter_id'] not in self.available_filter_ids:
                self.available_filter_ids.append(f['filter_id'])
            if (self.filter_by['filter_id'] != ''
                and f['filter_id'] != self.filter_by['filter_id']):
                # print("%s -> discard (filter_id %s)" % (f['filepath'], f['filter_id']))
                continue

            if (len(self.filter_by['shots']) > 0
                and f['shot_no'] not in self.filter_by['shots']):
                # print("%s -> discard (shot %d)" % (f['filepath'], f['shot_no']))
                continue

            # Add images
            # print("%s -> OK" % (f['filepath']))
            images.append(k)
        images.sort()
        return images


    def get_available_filter_ids(self):
        return self.available_filter_ids
        # filter_ids = list()
        # available_filter_ids = self.filter_ids()
        # for f_id in available_filter_ids:
        #     if filter_id_to_step(f_id) == self.filter_by['step']:
        #         filter_ids.append(f_id)
        # return filter_ids


    def append(self, k_ep, k_part, filename):
        # pprint(self.model_database.database())
        self.__append__(k_ep, k_part, filename)
        # self.frames[filename].update({})

        if False:

            if k_part in K_GENERIQUES:
                frame_no = self.frames[filename]['no']
                edition = db[k_part]['common']['video']['reference']['k_ed']
                db_video = db[k_part][edition]['video']

                k_ed_src

                shot = get_shot_from_frame_no_new(db, frame_no, k_ed=k_ed_src, k_ep=k_ep_src, k_part=k_part)

                db[k_ep][k_ed][k_part]['video']['shots']

                shot_no = get_shot_no_from_frame_no(db_video, frame_no, k_part)
                self.frames[filename].update({
                    'shot_no': shot_no,
                })
            else:
                edition = self.frames[filename]['k_ed']
                frame_no = self.frames[filename]['no']
                # print("%s: %s:%s:%s, %d" % (filename, edition, k_ep, k_part, frame_no))
                db_video = db[k_ep][edition][k_part]['video']
                # pprint(db[k_ep])
                # sys.exit()
                shot_no = get_shot_no_from_frame_no(db_video, frame_no, k_part)

                self.frames[filename].update({
                    'shot_no': shot_no,
                })

                # print("%s -> shot %d" % (filename, self.frames[filename]['shot_no']))

