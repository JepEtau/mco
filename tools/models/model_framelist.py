# -*- coding: utf-8 -*-
import sys
from parsers.parser_curves import parse_curve_configurations
from parsers.parser_episodes import parse_episode, parse_get_dependencies_for_episodes
from parsers.parser_generiques import parse_get_dependencies_for_generique

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
    nested_dict_get,
    pprint_video,
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


    def append(self, filepath, filename, k_ep, k_part):
        # Extract info from filename
        k_ed, k_ep_frame, frame_no, filter_id = get_info_from_filename(filename=filename)

        # Create a structure for a frame
        self.frames[filename] = {
            'filepath': os.path.join(filepath, filename),
            'filename': filename,
            'k_ed': k_ed,
            'k_ep': k_ep_frame if k_ep == '' else k_ep,
            'k_part': k_part,
            'k_step': filter_id_to_step(filter_id),
            'frame_no': frame_no,
            'filter_id': filter_id,
            # shot no. will be found after consolidation
            'shot_no': -1,

            'cache_fgd': None,
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

    def get_frame(self, image_name):
        return self.frames[image_name]

    def get_selected_frames(self, filters:dict) -> dict:
        # The list of frames shall be consolidated for some filtering
        # print("get_selected_frames")
        # pprint(filters)
        # print("IN:")
        # pprint(self.frames)
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

            if len(filters['shots']) > 0:
                do_append = False
                for shot_str in filters['shots']:
                    k_ed, k_ep, shot_no = shot_str.split('.')
                    if (f['shot_no'] == int(shot_no)
                        and f['k_ed'] == k_ed
                        and f['k_ep'] == k_ep):
                        do_append = True
                        break
                if not do_append:
                    continue

            selected_frames[k] = f

        return selected_frames



    def consolidate(self, k_ep, k_part):
        parsed_ed_ep = dict()
        self.shotlist.clear()
        db = self.model_database.database()

        if k_part in K_GENERIQUES:
            dependencies = parse_get_dependencies_for_generique(db, k_part_g=k_part)
            for k_ed_tmp, k_eps in dependencies.items():
                for k_ep_tmp in k_eps:
                    print("parse_episode: k_ed=%s, k_ep=%s" % (k_ed_tmp, k_ep_tmp))
                    parse_episode(db, k_ed=k_ed_tmp, k_ep=k_ep_tmp)
        else:
            print("parse dependencies for k_ep=%s" % (k_ep))
            dependencies = parse_get_dependencies_for_episodes(db, k_ep)
            for k_ed_tmp, k_eps in dependencies.items():
                for k_ep_tmp in k_eps:
                    print("parse_episode: k_ed=%s, k_ep=%s" % (k_ed_tmp, k_ep_tmp))
                    parse_episode(db, k_ed=k_ed_tmp, k_ep=k_ep_tmp)

        for frame in self.frames.values():
            if (frame['k_ed'] not in parsed_ed_ep.keys()
                or frame['k_ep'] not in parsed_ed_ep[frame['k_ed']]
                or frame['k_ed'] not in dependencies.keys()
                or frame['k_ep'] not in dependencies[frame['k_ed']]):

                # Parse episode
                # print("parse episode: %s:%s" % (frame['k_ed'], frame['k_ep']))
                parse_episode(db, k_ed=frame['k_ed'], k_ep=frame['k_ep'])

                # Add to parsed dict
                try: parsed_ed_ep[frame['k_ed']].append(frame['k_ep'])
                except: parsed_ed_ep[frame['k_ed']] = [frame['k_ep']]
        # print("%s:%s -> " % (frame['k_ep'], frame['k_ed']))


        # Parse the config files used get the selected curves for each shot
        parse_curve_configurations(db, k_ep_or_g=k_part if k_part in K_GENERIQUES else k_ep)

        for frame in self.frames.values():
            # try:
            shot = self.__get_shot_from_frame(db, frame)

            # Consolidate this shot
            if 'curves' not in shot.keys():
                shot['curves'] = None

            shot.update({
                'k_ed': frame['k_ed'],
                'k_ep': frame['k_ep'],
                'k_part': frame['k_part'],
                'modifications': {
                    'curves': {
                        'initial': None if shot['curves'] is None else shot['curves']['k_curves'],
                        'new': None,
                    },
                },
            })
            frame['shot_no'] = shot['no']

            try:
                shot_tmp = self.shotlist[frame['k_ed']][frame['k_ep']][shot['no']]
            except:
                nested_dict_set(self.shotlist, shot, frame['k_ed'], frame['k_ep'], shot['no'])
            # except:
            #     print("error: cannot find shot no. for frame %s in %s:%s:%s" % (frame['frame_no'], frame['k_ed'], frame['k_ep'], frame['k_part']))
            #     frame['shot_no'] = -1
            # print("\n SHOT used for curves editor ->")
            # pprint(shot)
            # print("------------------------------------------------------------\n")


            self.k_eds.append(frame['k_ed'])
            self.k_eps.append(frame['k_ep'])
            self.k_parts.append(frame['k_part'])

        # print("------------------ SHOTLIST ----------------------")
        # pprint(self.shotlist)
        # sys.exit()

        self.k_eds = sorted(list(set(self.k_eds)))
        self.k_eps = sorted(list(set(self.k_eps)))
        self.k_parts = sorted(list(set(self.k_parts)))



    def get_shotlist(self):
        # pprint(self.shotlist)
        return self.shotlist



    def get_shot_from_frame(self, frame):
        try:
            shot = self.shotlist[frame['k_ed']][frame['k_ep']][frame['shot_no']]
        except:
            print("shot no found for frame:")
            pprint(frame)
            return None
        return shot



    def get_available_filter_ids(self):
        return self.available_filter_ids
        # filter_ids = list()
        # available_filter_ids = self.filter_ids()
        # for f_id in available_filter_ids:
        #     if filter_id_to_step(f_id) == self.filter_by['step']:
        #         filter_ids.append(f_id)
        # return filter_ids



    def __get_shot_from_frame(self, db, frame) -> dict:
        frame_no = frame['frame_no']
        k_ed = frame['k_ed']
        k_ep = frame['k_ep']
        k_part = frame['k_part']
        # print("find %d in %s:%s:%s" % (frame_no, k_ed, k_ep, k_part))

        if 'shots' in db[k_ep][k_ed][k_part]['video'].keys():
            shots = db[k_ep][k_ed][k_part]['video']['shots']
            for shot in shots:
                if shot is None:
                    continue
                # print("%d in [%d; %d] ?" % (frame_no, shot['start'], shot['start'] + shot['count']))
                if shot['start'] <= frame_no < (shot['start'] + shot['count']):
                    # print("\t-> %d found in k_ed:k_ep %s:%s, shot no. %d" % (frame_no, k_ed, k_ep, shot['no']))
                    return shot


        # This part has no shot (because none defined in the config file)

        # Get the k_ed_src:k_ep src defined in TARGET
        if k_part in K_GENERIQUES:
            # TODO: replace this but the edition set as reference once the shots
            # are defined in g_fin, g_asuivre for edition k
            k_ed_src = db[k_part]['target']['video']['src']['k_ed']
            k_ep_src = db[k_part]['target']['video']['src']['k_ep']
            # print("\tuse %s:%s as src" % (k_ed_src, k_ep_src))
        else:
            try: k_ed_src = db[k_ep]['target']['video']['src']['k_ed']
            except: k_ed_src = db['editions']['k_ed_ref']

            # This is differnt from 'get_or_create_src_shot':
            # do not use the 'global' src
            k_ep_src = k_ep


        # Get the SRC shot defined in TARGET
        is_found = False
        shots = db[k_ep_src][k_ed_src][k_part]['video']['shots']
        for shot in shots:
            # print("%d in [%d; %d] ?" % (frame_no, shot['start'], shot['start'] + shot['count']))
            if shot['start'] <= frame_no < (shot['start'] + shot['count']):
                # print("\t-> %d found in k_ed_src:k_ep_src %s:%s at shot no. %d" % (frame_no, k_ed_src, k_ep_src, shot['no']))
                is_found = True
                break
        if not is_found:
            print("Error: shot no found in SRC but SHOULD BE: %d in %s:%s:%s" % (frame_no, k_ed_src, k_ep_src, k_part))
            pprint(db[k_ep_src][k_ed_src][k_part]['video'])
            sys.exit()

        # Create a list of shots
        db_video = db[k_ep][k_ed][k_part]['video']
        if 'shots' not in db_video.keys() or len(db_video['shots']) == 0:
            # print("create the list of shots")
            shot_count = len(shots)
            db_video['shots'] =  [None] * shot_count

        # Create a shot (~copy) with the minimal of data
        print("\t-> create shot no. %d in %s:%s:%s video" % (shot['no'],k_ep, k_ed, k_part))
        db_video['shots'][shot['no']] = {
            'start': shot['start'],
            'count': shot['count'],
            'no': shot['no'],
        }
        shot = db_video['shots'][shot['no']]
        return shot



        print("\nError: %s:get_shot_from_frame_no_new: not found, frame no. %d in %s:%s:%s, cannot continue" %
            (__name__, frame_no, k_ed, k_ep, k_part))
        # pprint_video(db[k_ep_ref][k_ed_ref][k_part]['video'], ignore='')
        pprint(db[k_ep_ref][k_ed_ref][k_part]['video']['shots'])
        print("-----------------------------------------------")
        pprint(db[k_ep][k_ed][k_part]['video']['shots'])
        sys.exit()



