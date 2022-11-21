# -*- coding: utf-8 -*-
import sys
from parsers.parser_episodes import parse_episode

from utils.get_filters import filter_id_to_step
sys.path.append('../scripts')

import os
import os.path
from pprint import pprint
import gc
import re
from copy import deepcopy

from models.model_database import Model_database
from utils.common import (
    K_GENERIQUES,
    get_shot_from_frame_no_new,
    get_shot_no_from_frame_no,
    nested_dict_set,
)



def get_info_from_filename(filename):

    result = re.search(re.compile("(ep\d{2})_(\d{5,6})_(ep\d{2})__([\w_\d]+)__(\d{3})\.(\w{3})"), filename)
    if result is not None:
        # generique
        frame_no = int(result.group(2))
        k_ed = result.group(4)
        k_ep = result.group(3)
        filter_id = int(result.group(5))
        # print("%s:%s:%s: filter_id=%d" % (frame_k_ep, k_part, filename, filter_id))
    else:
        result = re.search(re.compile("(ep\d{2})_(\d{5,6})__([\w_\d]+)__(\d{3})\.(\w{3})"), filename)
        if result is not None:
            frame_no = int(result.group(2))
            k_ep = result.group(1)
            k_ed = result.group(3)
            filter_id = int(result.group(4))

    return k_ed, k_ep, frame_no, filter_id



class Model_framelist():

    def __init__(self, model_database:Model_database):
        super(Model_framelist, self).__init__()
        self.model_database = model_database

        self.frames = dict()
        self.k_eds = list()
        self.k_eps = list()
        self.k_parts = list()
        self.shotlist = dict()

        self.filter_by = {
            'k_ed': '',
            'k_ep': '',
            'k_part': '',
            'step': '',
            'filter_id': '',
            'shots': list()
        }
        self.available_filter_ids = list()


    def clear(self):
        self.k_eds.clear()
        self.k_eps.clear()
        self.k_parts.clear()
        self.frames.clear()


    def append(self, filename, k_ep, k_part):
        # Extract info from filename
        k_ed, k_ep_frame, frame_no, filter_id = get_info_from_filename(filename=filename)

        # Create a structure for a frame
        self.frames[filename] = {
            'filename': filename,
            'k_ed': k_ed,
            'k_ep': k_ep_frame if k_ep == '' else k_ep,
            'k_part': k_part,
            'k_step': filter_id_to_step(filter_id),
            'frame_no': frame_no,
            'filter_id': filter_id,
            # shot no. will be found after consolidation
            'shot_no': -1,
        }


    def get_editions(self) -> list:
        return self.k_eds

    def get_episodes(self) -> list:
        return self.k_eps

    def get_parts(self) -> list:
        return self.k_parts


    def get_frames(self):
        # Return all frames
        return self.frames



    def get_selected_frames(self, filters:dict) -> dict:
        # The list of frames shall be consolidated for some filtering
        selected_frames = dict()
        for k, f in self.frames.items():
            if filters['k_ed'] != '' and f['k_ed'] != filters['k_ed']:
                # print("edition is different")
                continue

            if filters['k_ep'] != '' and f['k_ep'] != filters['k_ep']:
                # print("episode is different")
                continue

            if filters['k_part'] != '' and f['k_part'] != filters['k_part']:
                # print("part is different")
                continue

            if filters['k_step'] != '' and f['k_step'] != filters['k_step']:
                # print("step is different")
                continue

            if len(filters['filter_ids']) > 0 and f['filter_id'] not in filters['filter_ids']:
                # print("filter_id is different")
                continue

            if len(filters['shot_nos']) > 0 and f['shot_no'] not in filters['shot_nos']:
                # print("shot_no")
                continue

            selected_frames[k] = f

        return selected_frames



    def consolidate(self):
        parsed_ed_ep = dict()
        self.shotlist.clear()
        for frame in self.frames.values():
            # Do not parse episode if already done
            if (frame['k_ed'] not in parsed_ed_ep.keys()
                or frame['k_ep'] not in parsed_ed_ep[frame['k_ed']]):
                # Parse episode
                print("parse episode: %s:%s" % (frame['k_ed'], frame['k_ep']))
                parse_episode(self.model_database.database(), k_ed=frame['k_ed'], k_ep=frame['k_ep'])
                try: parsed_ed_ep[frame['k_ed']].append(frame['k_ep'])
                except: parsed_ed_ep[frame['k_ed']] = [frame['k_ep']]

            try:
                shot = get_shot_from_frame_no_new(
                    self.model_database.database(),
                    frame['frame_no'], frame['k_ed'], frame['k_ep'], frame['k_part'])
                frame['shot_no'] = shot['no']

                nested_dict_set(self.shotlist, shot, shot['no'], frame['k_ed'])
            except:
                frame['shot_no'] = -1

            self.k_eds.append(frame['k_ed'])
            self.k_eps.append(frame['k_ep'])
            self.k_parts.append(frame['k_part'])

        self.k_eds = sorted(list(set(self.k_eds)))
        self.k_eps = sorted(list(set(self.k_eps)))
        self.k_parts = sorted(list(set(self.k_parts)))


    def get_shotlist(self):
        pprint(self.shotlist)
        return self.shotlist


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




    # def get_selected_frames(self, selection):
    #     # print("\n%s:get_filtered_imagelist:" % (__name__))
    #     # pprint(self.filter_by)
    #     # print("\n")

    #     images = list()
    #     self.available_filter_ids.clear()
    #     for k, f in self.frames.items():
    #         if (selection['k_ed'] != ''
    #             and f['k_ed'] != selection['k_ed']):
    #             # print("%s -> discard (edition %s)" % (f['filepath'], f['k_ed']))
    #             continue

    #         if (selection['step'] != ''
    #             and f['step'] != selection['step']):
    #             # print("%s -> discard (step %s)" % (f['filepath'], f['step']))
    #             continue

    #         if f['filter_id'] not in self.available_filter_ids:
    #             self.available_filter_ids.append(f['filter_id'])
    #         if (self.filter_by['filter_id'] != ''
    #             and f['filter_id'] != self.filter_by['filter_id']):
    #             # print("%s -> discard (filter_id %s)" % (f['filepath'], f['filter_id']))
    #             continue

    #         if (len(self.filter_by['shots']) > 0
    #             and f['shot_no'] not in self.filter_by['shots']):
    #             # print("%s -> discard (shot %d)" % (f['filepath'], f['shot_no']))
    #             continue

    #         # Add images
    #         # print("%s -> OK" % (f['filepath']))
    #         images.append(k)
    #     images.sort()
    #     return images


    def get_available_filter_ids(self):
        return self.available_filter_ids
        # filter_ids = list()
        # available_filter_ids = self.filter_ids()
        # for f_id in available_filter_ids:
        #     if filter_id_to_step(f_id) == self.filter_by['step']:
        #         filter_ids.append(f_id)
        # return filter_ids


    def __append(self, k_ep, k_part, filename):
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


    # def episode(self):
    #     return self.current_episode

    # def editions(self):
    #     edition_list = list()

    #     for k, f in self.frames.items():
    #         if f['k_ed'] not in edition_list:
    #             edition_list.append(f['k_ed'])
    #     edition_list.sort()
    #     return edition_list


    # def get_episode_dependencies(self):
    #     depencencies = list()
    #     for k, f in self.frames.items():
    #         if f['k_ep'] not in depencencies:
    #             depencencies.append(f['k_ep'])
    #     depencencies.sort()
    #     return depencencies


    # def filter_ids(self):
    #     filter_ids_list = list()
    #     for k, f in self.frames.items():
    #         if f['filter_id'] not in filter_ids_list:
    #             filter_ids_list.append(f['filter_id'])
    #         filter_ids_list.sort()
    #     return filter_ids_list


    # def set_new_filter_by(self, filter_by:dict):
    #     self.filter_by = deepcopy(filter_by)


    # def get_frame(self, image_name=''):
    #     if image_name == '':
    #         return None
    #     if image_name not in self.frames.keys():
    #         return None
    #     frame = self.frames[image_name]
    #     # todo: add other properties? shot_no, ref frame no.
    #     # or in append function?

    #     return frame



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
        db = self.model_database.database()
        if db is not None:
            if k_part in K_GENERIQUES:
                # Use the ed:ep defined as reference
                k_ed_ref = db[k_part]['target']['video']['src']['k_ed']
                k_ep_ref = db[k_part]['target']['video']['src']['k_ep']
            else:
                k_ed_ref = frame_k_ed
                k_ep_ref = frame_k_ep

            if 'shots' not in db[k_ep_ref][k_ed_ref][k_part]['video'].keys():
                # Parse and consolidate db if not alreday done
                self.model_database.consolidate_database(frame_k_ep, k_part,
                    do_parse_curves=False,
                    do_parse_replace=False,
                    do_parse_geometry=False)
            if 'shots' not in db[k_ep_ref][k_ed_ref][k_part]['video'].keys():
                # pprint(db[frame_k_ep][frame_k_ed][k_part])
                print("Error: shots for %s:%s:%s were not consolidated" % (k_ep_ref, k_ed_ref, k_part))
            # print("\tGet shot: %d in %s:%s:%s" % (frame_no, frame_k_ed, frame_k_ep, k_part))

            # Apply offset
            if 'offsets' in db[frame_k_ep][frame_k_ed][k_part]['video']:
                # print("Apply offset:")
                offsets = db[frame_k_ep][frame_k_ed][k_part]['video']['offsets']
                # print("edition=%s, episode_no!%d, offsets=" % (edition, episode_no), offsets)
                for offset in offsets:
                    if offset['start'] <= frame_no <= offset['end']:
                        frame_no = frame_no + offset['offset']
                        break
            # else:
            #     print("No offset:")


            shot = get_shot_from_frame_no_new(db, frame_no=frame_no, k_ed=frame_k_ed, k_ep=frame_k_ep, k_part=k_part)
            shot_no = shot['no']
            start = shot['start']
        else:
            print("%s.__append__: warning: database is empty" % (__name__))
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

