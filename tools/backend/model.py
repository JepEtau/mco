# -*- coding: utf-8 -*-
import sys



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
from utils.pretty_print import *

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

from video.calculate_av_sync import calculate_av_sync
from video.consolidate_av_tracks import consolidate_av_tracks

from shot.consolidate_target_shots import (
    consolidate_target_shots,
    consolidate_target_shots_g,
)
from .model_geometry import *
from .model_curves import *
from .model_replace import *
from .model_database import *
from .model_stabilize import *

class Model(
    # Model_geometry,
    ReplaceModel,
    # Model_stabilize
):

    def __init__(self):
        super(Model, self).__init__()
        Model_geometry.__init__(self)
        Model_curves.__init__(self)
        ReplaceModel.__init__(self)
        Model_stabilize.__init__(self)

        # Variables
        self.global_database = None
        self.initial_database = dict()
        database_path = os.path.join(PATH_DATABASE)

        parse_common_configuration(self.initial_database, database_path)


        parse_editions(self.initial_database, database_path)

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



    def consolidate_database(self, k_ep, k_part):
        print_lightgreen("consolidate_database %s:%s" % (k_ep, k_part))
        if k_ep == '' and k_part == '':
            return

        del self.global_database
        self.global_database = deepcopy(self.initial_database)


        if k_ep.startswith('ep'):
            # Create a dict of dependencies for generiques
            dependencies = dict()
            for k_part_g in ['g_asuivre', 'g_documentaire']:
                dependencies_tmp = get_dependencies_for_generique(self.global_database, k_part_g=k_part_g)
                for k,v in dependencies_tmp.items():
                    if k not in dependencies.keys():
                        dependencies[k] = list()
                    dependencies[k] = list(set(dependencies[k] + v))


            # Parse episode at first (required to generate dependencies)
            for k_ed_tmp in self.k_editions:
                print_lightblue("  - parse %s:%s" % (k_ed_tmp, k_ep))
                parse_episode(self.global_database, k_ed=k_ed_tmp, k_ep=k_ep)

            # Get dependencies for this episode
            dependencies_tmp = parse_get_dependencies_for_episodes(self.global_database, k_ep=k_ep)

            # Merge dependencies
            for k,v in dependencies_tmp.items():
                if k not in dependencies.keys():
                    dependencies[k] = list()
                dependencies[k] = list(set(dependencies[k] + v))
            print_lightcyan("dependencies: ", end='')
            print(dependencies)

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
                    parse_replace_configurations(self.global_database, k_ep_or_g=k_ep_tmp)
                    parse_stabilize_configurations(self.global_database, k_ep_or_g=k_ep_tmp)
                    parse_curve_configurations(self.global_database, k_ep_or_g=k_ep_tmp)
                    parse_geometry_configurations(self.global_database, k_ep_or_g=k_ep_tmp)

            parse_stabilize_configurations(self.global_database, k_ep_or_g=k_ep)
            parse_curve_configurations(self.global_database, k_ep_or_g=k_ep)
            parse_replace_configurations(self.global_database, k_ep_or_g=k_ep)
            parse_geometry_configurations(self.global_database, k_ep_or_g=k_ep)

            # Consolidate database for the episode
            for k_p in K_NON_GENERIQUE_PARTS:
                consolidate_target_shots(self.global_database, k_ep=k_ep, k_part=k_p)

            for k_part_g in ['g_asuivre', 'g_documentaire']:
                parse_curve_configurations(self.global_database, k_ep_or_g=k_part_g)
                parse_replace_configurations(self.global_database, k_ep_or_g=k_part_g)
                parse_geometry_configurations(self.global_database, k_ep_or_g=k_part_g)
                # parse_stabilize_configurations(self.global_database, k_ep_or_g=k_part_g)
                consolidate_target_shots_g(self.global_database, k_ep=k_ep, k_part_g=k_part_g)

            calculate_av_sync(self.global_database, k_ep=k_ep)
            consolidate_av_tracks(self.global_database, k_ep=k_ep)

            # Consolidate each shot for the target
            # consolidate_target_shots(db=self.global_database, k_ep=k_ep, k_part=k_part)

            # Initialize db for edition
            if k_part != '':
                self.initialize_db_for_replace(db=self.global_database, k_ep=k_ep, k_part=k_part)
                self.initialize_db_for_geometry(self.global_database, k_ep=k_ep, k_part=k_part)
                self.initialize_db_for_stabilize(self.global_database, k_ep=k_ep, k_part=k_part)
                self.initialize_db_for_curves(db=self.global_database, k_ep=k_ep, k_part=k_part)

        else:
            k_part_g = k_part
            # Parse the episode used for this generique
            dependencies = get_dependencies_for_generique(self.global_database, k_part_g=k_part_g)
            print_lightcyan("dependencies: ", end='')
            print(dependencies)
            for k_ed_tmp, k_eps in dependencies.items():
                for k_ep_tmp in k_eps:
                    print_lightblue("  - parse %s:%s" % (k_ed_tmp, k_ep_tmp))
                    parse_episode(self.global_database, k_ed=k_ed_tmp, k_ep=k_ep_tmp)

            for k_ed_tmp, k_eps in dependencies.items():
                for k_ep_tmp in dependencies[k_ed_tmp]:
                    # Parse other config files for each dependency
                    parse_curve_configurations(self.global_database, k_ep_or_g=k_ep_tmp)
                    parse_replace_configurations(self.global_database, k_ep_or_g=k_ep_tmp)
                    # parse_geometry_configurations(self.global_database, k_ep_or_g=k_ep_tmp)
                    parse_stabilize_configurations(self.global_database, k_ep_or_g=k_ep_tmp)
                break

            # Parse config files
            parse_curve_configurations(self.global_database, k_ep_or_g=k_part_g)
            parse_replace_configurations(self.global_database, k_ep_or_g=k_part_g)
            parse_stabilize_configurations(self.global_database, k_ep_or_g=k_part_g)
            parse_geometry_configurations(self.global_database, k_ep_or_g=k_part_g)

            # Consolidate each shot for the target
            consolidate_target_shots_g(db=self.global_database, k_ep=k_ep, k_part_g=k_part_g)

            # Consolidate by aligning the A/V tracks of generiques
            consolidate_av_tracks(self.global_database, k_ep='', k_part=k_part_g)

            self.initialize_db_for_curves(db=self.global_database, k_ep='', k_part=k_part_g)
            self.initialize_db_for_replace(db=self.global_database, k_ep='', k_part=k_part_g)
            self.initialize_db_for_geometry(db=self.global_database, k_ep='', k_part=k_part_g)
            self.initialize_db_for_stabilize(db=self.global_database, k_ep='', k_part=k_part_g)

        gc.collect()


    def database(self):
        if self.global_database is None:
            return self.initial_database
        return self.global_database



    def is_db_modified(self, type:str=''):
        if type == 'curves':
            return bool(self.db_curves_library)
        elif type == 'shot_selection':
            return bool(self.db_curves_selection)
        elif type == 'replace':
            return bool(self.db_replaced_frames)
        elif type == 'geometry':
            return (bool(self.db_target_geometry)
            or bool(self.db_default_shot_geometry)
            or bool(self.db_shot_geometry))
        elif type == 'stabilize':
            return bool(self.db_stabilize)

        print_lightgreen('curves')
        pprint(self.db_curves_library)
        print_lightgreen('curves selection')
        pprint(self.db_curves_selection)
        print_lightgreen('replace')
        pprint(self.db_replaced_frames)
        print_lightgreen('geometry: target')
        pprint(self.db_target_geometry)
        print_lightgreen('geometry: default shot geometry')
        pprint(self.db_default_shot_geometry)
        print_lightgreen('geometry: shot geometry')
        pprint(self.db_shot_geometry)
        print_lightgreen('stabilize')
        pprint(self.db_stabilize)

        # is_default_geometry_modified = bool(self.db_default_shot_geometry)
        is_default_geometry_modified = False
        for _k_ed in self.db_default_shot_geometry.keys():
            for _k_ep in self.db_default_shot_geometry[_k_ed].keys():
                for _k_part in self.db_default_shot_geometry[_k_ed][_k_ep].keys():
                    crop = self.db_default_shot_geometry[_k_ed][_k_ep][_k_part]['crop']
                    for v in crop:
                        if v != 0:
                            is_default_geometry_modified = True
                            break


        if (bool(self.db_curves_library)
            or bool(self.db_curves_selection)
            or bool(self.db_replaced_frames)
            or bool(self.db_target_geometry)
            or is_default_geometry_modified
            or bool(self.db_shot_geometry)
            or bool(self.db_stabilize)):
            return True

        return False


    def get_modified_db(self) -> list:
        modified_db = list()

        if self.db_stabilize:
            modified_db.append('stabilize/deshake')

        if self.db_curves_library:
            modified_db.append('RGB curves')

        if self.db_curves_selection:
            modified_db.append('RGB curves selection')

        if self.db_replaced_frames:
            modified_db.append('frames to replace')

        if (self.db_target_geometry
            or self.db_default_shot_geometry
            or self.db_shot_geometry):
            modified_db.append('geometry')


        return modified_db


