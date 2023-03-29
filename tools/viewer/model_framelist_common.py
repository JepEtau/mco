# -*- coding: utf-8 -*-
import sys
sys.path.append('../scripts')

import os
import os.path
from pprint import pprint
import gc
import re
from copy import deepcopy

from filters.utils import filter_id_to_step
from utils.common import (
    K_GENERIQUES,
    get_shot_from_frame_no_new,
)


class Model_framelist_common(object):

    def __init__(self):
        super(Model_framelist_common, self).__init__()
        self.frames = dict()
        self.current_episode = ''
        self.current_part = ''


    def clear(self):
        # delete all frames
        self.frames.clear()
        gc.collect()


    def episode(self):
        return self.current_episode

    def editions(self):
        edition_list = list()

        for k, f in self.frames.items():
            if f['k_ed'] not in edition_list:
                edition_list.append(f['k_ed'])
        edition_list.sort()
        return edition_list


    def get_episode_dependencies(self):
        depencencies = list()
        for k, f in self.frames.items():
            if f['k_ep'] not in depencencies:
                depencencies.append(f['k_ep'])
        depencencies.sort()
        return depencencies


    def filter_ids(self):
        filter_ids_list = list()
        for k, f in self.frames.items():
            if f['filter_id'] not in filter_ids_list:
                filter_ids_list.append(f['filter_id'])
            filter_ids_list.sort()
        return filter_ids_list


    def print(self):
        pprint(self.frames)


    def set_new_filter_by(self, filter_by:dict):
        self.filter_by = deepcopy(filter_by)


    def get_frame(self, image_name=''):
        if image_name == '':
            return None
        if image_name not in self.frames.keys():
            return None
        frame = self.frames[image_name]
        # todo: add other properties? shot_no, ref frame no.
        # or in append function?

        return frame



    def __append__(self, k_ep, k_part, filename):
        # Get details from filename
        if k_part in K_GENERIQUES:
            result = re.search(re.compile("(ep\d{2})_(\d{5,6})_(ep\d{2})__([\w_\d]+)__(\d{3})\.(\w{3})"), filename)
            if result:
                frame_no = int(result.group(2))
                frame_k_ep = result.group(3)
                frame_k_ed = result.group(4)
                filter_id = int(result.group(5))
                # print("%s:%s:%s: filter_id=%d" % (frame_k_ep, k_part, filename, filter_id))
            else:
                return
            filepath = os.path.join(self.get_images_path(), k_part, filename)
        else:
            result = re.search(re.compile("(ep\d{2})_(\d{5,6})__([\w_\d]+)__(\d{3})\.(\w{3})"), filename)
            if result:
                frame_k_ep = result.group(1)
                frame_no = int(result.group(2))
                frame_k_ed = result.group(3)
                filter_id = int(result.group(4))
            else:
                return
            filepath = os.path.join(self.get_images_path(), frame_k_ep, k_part, filename)

        # Get shot from frame_no.
        # try:
        #     db = self.model_database.database()
        #     if db is not None:
        #         if k_part in K_GENERIQUES:
        #             # Use the ed:ep defined as reference
        #             k_ed_src = db[k_part]['target']['video']['src']['k_ed']
        #             k_ep_src = db[k_part]['target']['video']['src']['k_ep']
        #         else:
        #             k_ed_src = frame_k_ed
        #             k_ep_src = frame_k_ep

        #         if 'shots' not in db[k_ep_src][k_ed_src][k_part]['video'].keys():
        #             # Parse and consolidate db if not alreday done
        #             self.model_database.consolidate_database(frame_k_ep, k_part,
        #                 do_parse_curves=False,
        #                 do_parse_replace=False,
        #                 do_parse_geometry=False)
        #         if 'shots' not in db[k_ep_src][k_ed_src][k_part]['video'].keys():
        #             # pprint(db[frame_k_ep][frame_k_ed][k_part])
        #             print("Error: shots for %s:%s:%s were not consolidated" % (k_ep_src, k_ed_src, k_part))
        #         # print("\tGet shot: %d in %s:%s:%s" % (frame_no, frame_k_ed, frame_k_ep, k_part))

        #         # Apply offset
        #         if 'offsets' in db[frame_k_ep][frame_k_ed][k_part]['video']:
        #             # print("Apply offset:")
        #             offsets = db[frame_k_ep][frame_k_ed][k_part]['video']['offsets']
        #             # print("edition=%s, episode_no!%d, offsets=" % (edition, episode_no), offsets)
        #             for offset in offsets:
        #                 if offset['start'] <= frame_no <= offset['end']:
        #                     frame_no = frame_no + offset['offset']
        #                     break
        #         # else:
        #         #     print("No offset:")


        #         shot = get_shot_from_frame_no_new(db, frame_no=frame_no, k_ed=frame_k_ed, k_ep=frame_k_ep, k_part=k_part)
        #         shot_no = shot['no']
        #         start = shot['start']
        #     else:
        #         print("%s.__append__: warning: database is empty" % (__name__))
        #         shot_no = 0
        #         start = 0
        # except:
        #     shot_no = 0
        #     start = 0
        shot_no = 0
        start = 0

        self.frames[filename] = {
            'k_ep': frame_k_ep,
            'k_part': k_part,
            'k_ed': frame_k_ed,
            'no': frame_no,
            'filter_id': filter_id,
            'step': filter_id_to_step(filter_id),
            'filepath': os.path.abspath(filepath),
            'shot_no': shot_no,
            'start': start
        }

        # print("file: %s" % (filename))
        # pprint(self.frames[filename])
        # print("__________")

