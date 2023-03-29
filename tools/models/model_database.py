# -*- coding: utf-8 -*-
import sys
sys.path.append('../scripts')

from copy import deepcopy
import gc
import os
import os.path

from pprint import pprint
from logger import log

from utils.path import PATH_DATABASE
from utils.common import (
    K_NON_GENERIQUE_PARTS,
    pprint_video,
)

from parsers.parser_common import parse_common_configuration
from parsers.parser_editions import parse_editions
from parsers.parser_generiques import (
    parse_generiques_target, parse_generiques,
    get_dependencies_for_generique,
)
from parsers.parser_episodes import (
    db_init_episodes,
    parse_get_dependencies_for_episodes,
    parse_episodes_target,
    parse_episode,
)
from parsers.parser_curves import (
    parse_curve_configurations,
)
from parsers.parser_replace import (
    parse_replace_configurations,
    get_replaced_frames,
)
from parsers.parser_geometry import parse_geometry_configurations
from parsers.parser_stabilize import parse_stabilize_configurations

from video.consolidate_av import (
    align_audio_video_durations,
    calculate_av_sync,
    align_audio_video_durations_g_debut_fin
)
from parsers.parser_shots import consolidate_target_shots, consolidate_target_shots_g

from models.model_geometry import Model_geometry
from models.model_curves import Model_curves
from models.model_replace import Model_replace
from models.model_stabilize import Model_stabilize



class Model_database(Model_geometry,
                    Model_curves,
                    Model_replace,
                    Model_stabilize,
                    object):

    def __init__(self):
        super(Model_database, self).__init__()
        Model_geometry.__init__(self)
        Model_curves.__init__(self)
        Model_replace.__init__(self)
        Model_stabilize.__init__(self)

        # Variables
        self.global_database = None
        self.initial_database = dict()

        parse_common_configuration(self.initial_database, PATH_DATABASE)

        # Discard replace to have the initial list of frames
        self.initial_database['common']['options']['discard_tasks'].append('replace')
        parse_editions(self.initial_database)

        self.k_editions = self.initial_database['editions']['available']
        for k_ed in self.k_editions:
            db_init_episodes(self.initial_database, k_ed=k_ed)

        # For each edition, parse the generique database
        for k_ed in self.k_editions:
            parse_generiques(self.initial_database, k_ed=k_ed)

        parse_episodes_target(self.initial_database)
        parse_generiques_target(self.initial_database)

        self.path_images =self.initial_database['common']['directories']['frames']


    def get_images_path(self):
        return self.path_images

    def get_cache_path(self):
        return self.initial_database['common']['directories']['cache']



    def consolidate_database(self, k_ep, k_part,
                                do_parse_curves:bool=True,
                                do_parse_replace:bool=True,
                                do_parse_geometry:bool=True,
                                do_parse_stabilize:bool=False):
        print("%s:consolidate_database %s:%s" % (__name__, k_ep, k_part))
        if k_ep == '' and k_part == '':
            return

        del self.global_database
        self.global_database = deepcopy(self.initial_database)


        if k_ep.startswith('ep'):
            # Create a dict of dependencies for generiques
            dependencies = dict()
            for k_part_g in ['g_asuivre', 'g_reportage']:
                dependencies_tmp = get_dependencies_for_generique(self.global_database, k_part_g=k_part_g)
                for k,v in dependencies_tmp.items():
                    if k not in dependencies.keys():
                        dependencies[k] = list()
                    dependencies[k] = list(set(dependencies[k] + v))


            # Parse episode at first (required to generate dependencies)
            for k_ed_tmp in self.k_editions:
                parse_episode(self.global_database, k_ed=k_ed_tmp, k_ep=k_ep)

            # Get dependencies for this episode
            dependencies_tmp = parse_get_dependencies_for_episodes(self.global_database, k_ep=k_ep)

            # Merge dependencies
            for k,v in dependencies_tmp.items():
                if k not in dependencies.keys():
                    dependencies[k] = list()
                dependencies[k] = list(set(dependencies[k] + v))

            # Parse episodes which are required (dependencies)
            for k_ed_tmp, v in dependencies.items():
                for k_ep_tmp in v:
                    if k_ep_tmp == k_ep:
                        # print("do not parse, already done: %s:%s" % (k_ed_tmp, k_ep_tmp))
                        continue
                    # print("parse dependency: %s:%s" % (k_ed_tmp, k_ep_tmp))
                    parse_episode(self.global_database, k_ed=k_ed_tmp, k_ep=k_ep_tmp)

            # Parse other config files for each dependency
            for k_ed_tmp, v in dependencies.items():
                for k_ep_tmp in dependencies[k_ed_tmp]:
                    if do_parse_stabilize:
                        parse_stabilize_configurations(self.global_database, k_ep_or_g=k_ep_tmp, parse_parameters=True)
                    if do_parse_curves:
                        parse_curve_configurations(self.global_database, k_ep_or_g=k_ep_tmp)
                    if do_parse_replace:
                        parse_replace_configurations(self.global_database, k_ep_or_g=k_ep_tmp, k_ed_only=k_ed_tmp)
                    if do_parse_geometry:
                        parse_geometry_configurations(self.global_database, k_ep_or_g=k_ep_tmp)

            if do_parse_stabilize:
                parse_stabilize_configurations(self.global_database, k_ep_or_g=k_ep, parse_parameters=True)
            if do_parse_curves:
                parse_curve_configurations(self.global_database, k_ep_or_g=k_ep)
            if do_parse_replace:
                parse_replace_configurations(self.global_database, k_ep_or_g=k_ep)
            if do_parse_geometry:
                parse_geometry_configurations(self.global_database, k_ep_or_g=k_ep)


            # Consolidate database for the episode
            for k_p in K_NON_GENERIQUE_PARTS:
                consolidate_target_shots(self.global_database, k_ep=k_ep, k_part=k_p)

            for k_part_g in ['g_asuivre', 'g_reportage']:
                if do_parse_curves:
                    parse_curve_configurations(self.global_database, k_ep_or_g=k_part_g)
                if do_parse_replace:
                    parse_replace_configurations(self.global_database, k_ep_or_g=k_part_g)
                if do_parse_geometry:
                    parse_geometry_configurations(self.global_database, k_ep_or_g=k_part_g)
                # if do_parse_stabilize:
                #     parse_stabilize_configurations(self.global_database, k_ep_or_g=k_part_g)
                consolidate_target_shots_g(self.global_database, k_ep=k_ep, k_part_g=k_part_g)

            calculate_av_sync(self.global_database, k_ep=k_ep)
            align_audio_video_durations(self.global_database, k_ep=k_ep)

            # Consolidate each shot for the target
            # consolidate_target_shots(db=self.global_database, k_ep=k_ep, k_part=k_part)


            if k_part != '':
                # Frames which are replaced
                if do_parse_replace:
                    self.db_replaced_frames_initial = get_replaced_frames(self.global_database, k_ep=k_ep, k_part=k_part)
                    self.db_replaced_frames = dict()

                # Geometry used at the end
                if do_parse_geometry:
                    self.initialize_db_for_geometry(self.global_database, k_ep=k_ep, k_part=k_part)

                # Stabilize
                if do_parse_stabilize:
                    self.initialize_db_for_stabilize(self.global_database, k_ep=k_ep, k_part=k_part)

                # RGB curves
                if do_parse_curves:
                    self.initialize_db_for_curves(db=self.global_database, k_ep=k_ep, k_part=k_part)

        else:
            k_part_g = k_part
            # Parse the episode used for this generique
            dependencies = get_dependencies_for_generique(self.global_database, k_part_g=k_part_g)

            for k_ed_tmp, k_eps in dependencies.items():
                for k_ep_tmp in k_eps:
                    parse_episode(self.global_database, k_ed=k_ed_tmp, k_ep=k_ep_tmp)

            for k_ed_tmp, k_eps in dependencies.items():
                for k_ep_tmp in dependencies[k_ed_tmp]:
                    # Parse other config files for each dependency
                    if do_parse_curves:
                        parse_curve_configurations(self.global_database, k_ep_or_g=k_ep_tmp)
                    if do_parse_replace:
                        parse_replace_configurations(self.global_database, k_ep_or_g=k_ep_tmp)
                    # if do_parse_geometry:
                    #     parse_geometry_configurations(self.global_database, k_ep_or_g=k_ep_tmp)
                    # if do_parse_stabilize:
                    #     parse_stabilize_configurations(self.global_database, k_ep_or_g=k_ep_tmp)
                break

            # Curves: this parser update the shots for each episode/part
            if do_parse_curves:
                parse_curve_configurations(self.global_database, k_ep_or_g=k_part_g)
                self.initialize_db_for_curves(db=self.global_database, k_ep='', k_part=k_part_g)

            # Consolidate each shot for the target
            consolidate_target_shots_g(db=self.global_database, k_ep=k_ep, k_part=k_part_g)

            # Consolidate by aligning the A/V tracks of generiques
            align_audio_video_durations_g_debut_fin(self.global_database, k_ep='', k_part_g=k_part_g)

            # Replaced frames
            if do_parse_replace:
                parse_replace_configurations(self.global_database, k_ep_or_g=k_part_g)
                self.db_replaced_frames_initial = get_replaced_frames(self.global_database, k_ep='', k_part=k_part_g)
                self.db_replaced_frames = dict()

            # geometry: crop and resize
            if do_parse_geometry:
                parse_geometry_configurations(self.global_database, k_ep_or_g=k_part_g)
                self.initialize_db_for_geometry(db=self.global_database, k_ep='', k_part=k_part_g)

            # if do_parse_stabilize:
            #     parse_stabilize_configurations(self.global_database, k_ep_or_g=k_part)
            #     self.initialize_db_for_stabilize(db=self.global_database, k_ep='', k_part=k_part)

        gc.collect()


    def database(self):
        if self.global_database is None:
            return self.initial_database
        return self.global_database



    def is_db_modified(self, type:str=''):
        if type == 'curves':
            return self.is_curves_db_modified
        elif type == 'shot_selection':
            return self.is_curves_selection_db_modified
        elif type == 'replace':
            return self.is_replace_db_modified
        elif type == 'geometry':
            return self.is_geometry_db_modified
        elif type == 'stabilize':
            return self.is_stabilize_db_modified


        return (self.is_curves_db_modified
            or self.is_curves_selection_db_modified
            or self.is_replace_db_modified
            or self.is_geometry_db_modified
            or self.is_stabilize_db_modified)


    def get_modified_db(self) -> list:
        modified_db = list()

        if self.is_stabilize_db_modified:
            modified_db.append('stabilize values')

        if self.is_curves_db_modified:
            modified_db.append('curves')

        if self.is_curves_selection_db_modified:
            modified_db.append('curves selection')

        if self.is_replace_db_modified:
            modified_db.append('frames to replace')

        if self.is_geometry_db_modified:
            modified_db.append('part or shot geometry')

        return modified_db


