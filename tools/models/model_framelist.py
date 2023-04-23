# -*- coding: utf-8 -*-
import sys
sys.path.append('../scripts')
import os
import os.path
from pprint import pprint
import gc
import re

from parsers.parser_curves import parse_curve_configurations
from parsers.parser_episodes import (
    parse_episode,
    parse_get_dependencies_for_episodes
)
from parsers.parser_generiques import get_dependencies_for_generique

from models.model_database import Model_database
from utils.common import K_GENERIQUES
from utils.nested_dict import nested_dict_set


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
        self.available_editions = list()


    def clear(self):
        self.k_eds.clear()
        self.k_eps.clear()
        self.k_parts.clear()
        self.frames.clear()



    def set_available_editions(self, available_editions:list):
        self.available_editions = available_editions


    def append(self, filepath, filename, k_ep, k_part):
        # Extract info from filename
        k_ed_frame, k_ep_frame, frame_no, filter_id = get_info_from_filename(filename=filename)

        if k_ed_frame not in self.available_editions:
            return

        # Create a structure for a frame
        self.frames[filename] = {
            'filepath': os.path.join(filepath, filename),
            'filename': filename,
            'k_ed': k_ed_frame,
            'k_ep': k_ep_frame if k_ep == '' else k_ep,
            'k_part': k_part,
            'frame_no': frame_no,
            'filter_id': filter_id,
            # shot no. will be found after consolidation
            'shot_no': -1,

            'cache': None,
            'cache_initial': None,
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
        # sys.exit()
        selected_frames = dict()
        filter_k_step = filters['k_step'].replace(' ', '')
        for k, f in self.frames.items():
            if filters['k_ed'] != '' and f['k_ed'] != filters['k_ed']:
                # print("edition is different: %s" % (f['k_ed']))
                continue

            if filters['k_ep'] != '' and f['k_ep'] != filters['k_ep']:
                # print("episode is different: %s" % (f['k_ep']))
                continue

            if filters['k_part'] != '' and f['k_part'] != filters['k_part']:
                # print("part is different: %s" % (f['k_part']))
                continue

            if filter_k_step != '' and f['k_step'] != filters['k_step']:
                # print("step is different: %s vs [%s]" % (f['k_step'], filters['k_step']))
                continue

            if len(filters['filter_ids']) > 0 and f['filter_id'] not in filters['filter_ids']:
                # print("filter_id is different: %s" % (f['filter_id']))
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
            dependencies = get_dependencies_for_generique(db, k_part_g=k_part)
            for k_ed_tmp, k_eps in dependencies.items():
                for k_ep_tmp in k_eps:
                    # print("parse_episode for generiques: k_ed=%s, k_ep=%s" % (k_ed_tmp, k_ep_tmp))
                    parse_episode(db, k_ed=k_ed_tmp, k_ep=k_ep_tmp)
        else:
            # print("parse dependencies for k_ep=%s" % (k_ep))
            dependencies = parse_get_dependencies_for_episodes(db, k_ep)
            for k_ed_tmp, k_eps in dependencies.items():
                for k_ep_tmp in k_eps:
                    # print("parse_episode: k_ed=%s, k_ep=%s" % (k_ed_tmp, k_ep_tmp))
                    parse_episode(db, k_ed=k_ed_tmp, k_ep=k_ep_tmp)

        # For each frame, parse the episode if not already done
        for frame in self.frames.values():
            # print("%s:%s" % (frame['k_ed'], frame['k_ep']))
            k_ed_tmp = frame['k_ed']
            k_ep_tmp = frame['k_ep']
            if k_ed_tmp in parsed_ed_ep.keys() and k_ep_tmp in parsed_ed_ep[k_ed_tmp]:
                continue
            if k_ed_tmp in dependencies.keys() and k_ep_tmp in dependencies[k_ed_tmp]:
                continue

            # Parse episode
            # print("parse episode: %s:%s" % (k_ed_tmp, k_ep_tmp))
            parse_episode(db, k_ed=k_ed_tmp, k_ep=k_ep_tmp)

            # Add to parsed dict
            try:
                parsed_ed_ep[k_ed_tmp].append(k_ep_tmp)
            except:
                parsed_ed_ep[k_ed_tmp] = [k_ep_tmp]

        # print("%s:%s -> " % (frame['k_ep'], frame['k_ed']))

        # Parse the config files used get the selected curves for each shot
        parse_curve_configurations(db, k_ep_or_g=k_part if k_part in K_GENERIQUES else k_ep)

        for frame in self.frames.values():
            if frame['k_ed'] not in db['editions']['available']:
                # print("info: consolidate: discard frame %s as the edition %s is not available" % (frame['filename'], frame['k_ed']))
                continue

            # print("get video src for %s:%s" % (frame['k_ed'], frame['k_ep']))
            db_video_src = db[frame['k_ep']][frame['k_ed']][k_part]['video']

            # Apply offset to the frame no if needed
            frame_no = frame['frame_no']

            # Find shot no in k_ed_src:k_ep_src
            try:
                shots = db_video_src['shots']
                is_found = False
                for shot in shots:
                    if shot['start'] <= frame_no < (shot['start'] + shot['count']):
                        is_found = True
                        break
                if not is_found:
                    # print("shot not found for frame no %d in %s:%s:%s (%s)" % (frame_no, frame['k_ed'], frame['k_ep'], frame['k_part'], frame['filename']))
                    continue
                frame['shot_no'] = shot['no']
            except:
                continue

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

            # Add this shot to the shotlist
            try:
                # print("Shot already in db: %s:%s:%s:%d" % (frame['k_ed'], frame['k_ep'], frame['k_part'], shot['no']))
                shot_tmp = self.shotlist[frame['k_ed']][frame['k_ep']][shot['no']]
            except:
                # print("Add shot: %s:%s:%s:%d" % (frame['k_ed'], frame['k_ep'], frame['k_part'], shot['no']))
                nested_dict_set(self.shotlist, shot, frame['k_ed'], frame['k_ep'], shot['no'])
            # pprint(self.shotlist)
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

    # def get_shotlist(self):
    #     return self.shotlist

    def get_filtered_shotlist(self, k_ed, k_ep):
        # print("get_filtered_shotlist: %s:%s" % (k_ed, k_ep))
        # Reorganize shot list
        shotlist_tmp = dict()
        if k_ed == '' or k_ed == ' ':
            shotlist_tmp = dict()
            for k_ed_tmp in self.shotlist.keys():
                    for k_ep_tmp in self.shotlist[k_ed_tmp].keys():
                        for shot_no in self.shotlist[k_ed_tmp][k_ep_tmp].keys():
                            shot = self.shotlist[k_ed_tmp][k_ep_tmp][shot_no]
                            if shot_no not in shotlist_tmp.keys():
                                shotlist_tmp[shot_no] = [shot]
                            else:
                                shotlist_tmp[shot_no].append(shot)

        else:
            for k_ed_tmp in self.shotlist.keys():
                    for k_ep_tmp in self.shotlist[k_ed_tmp].keys():
                        if k_ed_tmp == k_ed and k_ep_tmp == k_ep:
                            for shot_no in self.shotlist[k_ed_tmp][k_ep_tmp].keys():
                                shot = self.shotlist[k_ed_tmp][k_ep_tmp][shot_no]
                                if shot_no not in shotlist_tmp.keys():
                                    shotlist_tmp[shot_no] = [shot]
                                else:
                                    shotlist_tmp[shot_no].append(shot)

        shotlist_ordered = dict()
        shot_nos = sorted(list(shotlist_tmp.keys()))
        no = 0
        for shot_no in shot_nos:
            shots = shotlist_tmp[shot_no]
            for shot in shots:
                shotlist_ordered[no] = shot
                no += 1

        return shotlist_ordered


    def get_shot_from_frame(self, frame):
        try:
            shot = self.shotlist[frame['k_ed']][frame['k_ep']][frame['shot_no']]
        except:
            # print("shot no found for frame:")
            # pprint(frame)
            return None
        return shot



    def get_available_filter_ids(self):
        return self.available_filter_ids




