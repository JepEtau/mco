# -*- coding: utf-8 -*-
import sys
sys.path.append('../scripts')

from copy import deepcopy
import gc
import os
import os.path
import configparser
from pathlib import Path
from pathlib import PosixPath
import collections
import numpy as np

from pprint import pprint
from logger import log

from utils.path import PATH_DATABASE
from utils.common import (
    K_GENERIQUES,
    K_NON_GENERIQUE_PARTS,
    get_k_part_from_frame_no,
    get_shot_from_frame_no_new,
    pprint_video,
    recursive_update,
)

from models.model_stitching import Model_stitching
from models.model_bgd_curves import Model_bgd_curves
from models.model_geometry import Model_geometry
from models.model_curves import Model_curves
from models.model_replace import Model_replace

from parsers.parser_common import parse_common_configuration
from parsers.parser_database import pprint_episode

from parsers.parser_editions import parse_editions

from parsers.parser_generiques import (
    db_init_generiques,
    parse_generiques_common, parse_generiques,
    parse_get_dependencies_for_generique,
)

from parsers.parser_episodes import (
    db_init_episodes,
    parse_get_dependencies_for_episodes,
    parse_episodes_common,
    parse_episode,
)

from parsers.parser_shots import create_target_shots, create_target_shots_g

from utils.consolidate_av import (
    align_audio_video_durations,
    calculate_av_sync,
    align_audio_video_durations_g_debut_fin
)
from utils.consolidate_shots import consolidate_target_shots

from parsers.parser_stabilize import (
    STABILIZATION_SHOT_PARAMETERS_DEFAULT,
    parse_stabilize_configurations,
    get_shots_stabilize_parameters,
    get_frames_stabilize,
)


from parsers.parser_stitching import (
    STITCHING_SHOT_PARAMETERS_DEFAULT,
    get_frames_stitching_parameters,
    get_frames_stitching_transformation,
    parse_stitching_configurations,
    get_shots_stitching_parameters,
)

from parsers.parser_curves import (
    parse_curve_configurations,
)

from parsers.parser_replace import parse_replace_configurations
from parsers.parser_replace import get_replaced_frames

from parsers.parser_geometry import parse_geometry_configurations
from parsers.parser_geometry import get_initial_part_geometry
from parsers.parser_geometry import get_shots_st_geometry




class Model_database(Model_bgd_curves,
                    Model_geometry,
                    Model_curves,
                    Model_replace,
                    Model_stitching,
                    object):

    def __init__(self):
        super(Model_database, self).__init__()
        Model_bgd_curves.__init__(self)
        Model_stitching.__init__(self)
        Model_geometry.__init__(self)
        Model_curves.__init__(self)
        Model_replace.__init__(self)

        # Variables
        self.global_database = None
        self.initial_database = dict()

        self.frame_parameters = dict()

        self.db_stabilize_frames = dict()
        self.db_stabilize_shots_parameters = dict()
        self.is_stabilize_db_modified = False

        self.initial_database['common'] = parse_common_configuration(PATH_DATABASE)

        # Discard replace to have the initial list of frames
        self.initial_database['common']['options']['discard_tasks'].append('replace')

        k_ed_ref = self.initial_database['common']['reference']['edition']

        self.initial_database['editions'] = parse_editions(self.initial_database,
            k_ed_fgd='k', k_ed_ref=k_ed_ref)
        parse_episodes_common(self.initial_database)

        self.k_editions = self.initial_database['editions']['available']
        for k_ed in self.k_editions:
            db_init_episodes(self.initial_database, k_ed=k_ed)

            # Initialize dictionary for generiques
            db_init_generiques(self.initial_database, k_ed=k_ed)

        # Parse database file which contains common settings for generiques
        parse_generiques_common(self.initial_database)
        # For each edition, parse the generique database
        for k_ed in self.k_editions:
            parse_generiques(self.initial_database, k_ed=k_ed)

        self.path_images =self.initial_database['common']['directories']['frames']


        # Here, we have the initial database
    def get_images_path(self):
        return self.path_images


    def get_cache_path(self):
        return self.initial_database['common']['directories']['cache']


    def get_curves_library_path(self):
        return self.initial_database['common']['directories']['curves']


    def consolidate_database(self, k_ep, k_part,
                                do_parse_curves:bool=True,
                                do_parse_replace:bool=True,
                                do_parse_geometry:bool=True,
                                do_parse_stitching:bool=False):
        # print("%s:consolidate_database %s:%s" % (__name__, k_ep, k_part))
        if k_ep == '' and k_part == '':
            return

        del self.global_database
        self.global_database = deepcopy(self.initial_database)


        if k_ep.startswith('ep'):
            # Create a dict of dependencies for generiques
            dependencies = dict()
            for k_part_g in ['g_asuivre', 'g_reportage']:
                dependencies_tmp = parse_get_dependencies_for_generique(self.global_database, k_part_g=k_part_g)
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
                print(k_ed_tmp)
                for k_ep_tmp in dependencies[k_ed_tmp]:
                    print(k_ep_tmp)
                    if do_parse_stitching:
                        parse_stitching_configurations(self.global_database, k_ep_or_g=k_ep_tmp, parse_parameters=True)
                    parse_stabilize_configurations(self.global_database, k_ep_or_g=k_ep_tmp, parse_parameters=True)

                    if do_parse_curves:
                        parse_curve_configurations(self.global_database, k_ep_or_g=k_ep_tmp)

                    if do_parse_replace:
                        parse_replace_configurations(self.global_database, k_ep_or_g=k_ep_tmp, k_ed_only=k_ed_tmp)
                    if do_parse_geometry:
                        parse_geometry_configurations(self.global_database, k_ep_or_g=k_ep_tmp)

            if do_parse_stitching:
                parse_stitching_configurations(self.global_database, k_ep_or_g=k_ep, parse_parameters=True)
            parse_stabilize_configurations(self.global_database, k_ep_or_g=k_ep, parse_parameters=True)
            if do_parse_curves:
                parse_curve_configurations(self.global_database, k_ep_or_g=k_ep)
            if do_parse_replace:
                parse_replace_configurations(self.global_database, k_ep_or_g=k_ep)
            if do_parse_geometry:
                parse_geometry_configurations(self.global_database, k_ep_or_g=k_ep)


            # Consolidate database for the episode
            for k_p in K_NON_GENERIQUE_PARTS:
                create_target_shots(self.global_database, k_ep=k_ep, k_part=k_p)

            for k_part_g in ['g_asuivre', 'g_reportage']:
                if do_parse_curves:
                    parse_curve_configurations(self.global_database, k_ep_or_g=k_part_g)
                if do_parse_replace:
                    parse_replace_configurations(self.global_database, k_ep_or_g=k_part_g)
                if do_parse_geometry:
                    parse_geometry_configurations(self.global_database, k_ep_or_g=k_part_g)

                # Create shots used for the generation
                create_target_shots_g(self.global_database, k_ep=k_ep, k_part_g=k_part_g)

            calculate_av_sync(self.global_database, k_ep=k_ep)
            align_audio_video_durations(self.global_database, k_ep=k_ep)

            # Consolidate each shot for the target
            consolidate_target_shots(
                db=self.global_database,
                k_ed='',
                k_ep=k_ep,
                k_part=k_part,
            )


            if k_part != '':
                # Frames which are replaced
                if do_parse_replace:
                    self.db_replaced_frames_initial = get_replaced_frames(self.global_database, k_ep=k_ep, k_part=k_part)
                    self.db_replaced_frames = dict()

                # Geometry used at the end
                if do_parse_geometry:
                    if k_part in ['g_asuivre', 'g_reportage']:
                        self.db_part_geometry_initial = get_initial_part_geometry(self.global_database, k_ep=k_ep, k_part=k_part[2:])
                        recursive_update(self.db_part_geometry_initial, get_initial_part_geometry(self.global_database, k_ep=k_ep, k_part=k_part))
                    else:
                        self.db_part_geometry_initial = get_initial_part_geometry(self.global_database, k_ep=k_ep, k_part=k_part)
                    self.db_part_geometry = dict()

                # Image stitching
                if do_parse_stitching:
                    # Parameters
                    self.db_stitching_shots_parameters_initial = get_shots_stitching_parameters(self.global_database, k_ep=k_ep, k_part=k_part)
                    self.db_stitching_shots_parameters = dict()
                    self.db_stitching_frames_parameters_initial = get_frames_stitching_parameters(self.global_database, k_ep=k_ep, k_part=k_part)
                    self.db_stitching_frames_parameters = dict()

                    # Values: transformation matrix
                    self.initialize_db_for_transformation(db=self.global_database, k_ep=k_ep, k_part=k_part)

                    # !!!!! TODO: this won't work when replacing shots from another episode:
                    # use a duplicated curves file parameters?
                    # concatenate libraries for up to 3 episodes?
                    # better solution would be to parse dynamicaly the folders. i.e. load and save the curves
                    # from the other directory if the src episode is not the same.
                    self.initialize_db_for_bgd_curves(db=self.global_database, k_ep=k_ep, k_part=k_part)
                    self.initialize_db_for_fgd_crop(db=self.global_database, k_ep=k_ep, k_part=k_part)

                # Stabilization
                self.db_stabilize_shots_parameters_initial = get_shots_stabilize_parameters(self.global_database, k_ep=k_ep, k_part=k_part)
                self.db_stabilize_shots_parameters = dict()

                self.db_stabilize_frames_initial = get_frames_stabilize(self.global_database, k_ep=k_ep, k_part=k_part)
                self.db_stabilize_frames = dict()

                self.db_st_geometry_initial = get_shots_st_geometry(self.global_database, k_ep=k_ep, k_part=k_part)
                self.db_st_geometry = dict()

                # RGB curves
                if do_parse_curves:
                    self.initialize_db_for_curves(db=self.global_database, k_ep=k_ep, k_part=k_part)

        else:
            # Parse the episode used for this generique
            dependencies = parse_get_dependencies_for_generique(self.global_database, k_part_g=k_part)

            for k_ed_tmp, k_eps in dependencies.items():
                for k_ep_tmp in k_eps:
                    # print("\tparse_episode: k_ed=%s, k_ep=%s" % (k_ed_tmp, k_ep_tmp))
                    parse_episode(self.global_database, k_ed=k_ed_tmp, k_ep=k_ep_tmp)

            for k_ed_tmp, k_eps in dependencies.items():
                for k_ep_tmp in dependencies[k_ed_tmp]:
                    # Parse other config files for each dependency
                    # print("\tparse_***_configurations: k_ed=%s, k_ep=%s" % (k_ed_tmp, k_ep_tmp))
                    # if do_parse_stitching:
                    #     parse_stitching_configurations(self.global_database, k_ep_or_g=k_ep_tmp)
                    if do_parse_curves:
                        parse_curve_configurations(self.global_database, k_ep_or_g=k_ep_tmp)
                    if do_parse_replace:
                        parse_replace_configurations(self.global_database, k_ep_or_g=k_ep_tmp)
                    # if do_parse_geometry:
                    #     parse_geometry_configurations(self.global_database, k_ep_or_g=k_ep_tmp)
                break

            # # Stabilization and stitching
            # if do_parse_stitching:
            #     parse_stitching_configurations(self.global_database, k_ep_or_g=k_part)

            # Curves: this parser update the shots for each episode/part
            if do_parse_curves:
                parse_curve_configurations(self.global_database, k_ep_or_g=k_part)

            # Replaced frames
            if do_parse_replace:
                parse_replace_configurations(self.global_database, k_ep_or_g=k_part)

            # Crop
            if do_parse_geometry:
                parse_geometry_configurations(self.global_database, k_ep_or_g=k_part)

            # Create shots used for the generation
            create_target_shots_g(self.global_database, k_ep='', k_part_g=k_part)

            # Consolidate by aligning the A/V tracks of generiques
            align_audio_video_durations_g_debut_fin(self.global_database, k_ep='', k_part_g=k_part)

            # Consolidate each shot for the target
            consolidate_target_shots(
                db=self.global_database,
                k_ed='',
                k_ep=k_ep,
                k_part=k_part,
            )

            # Curves
            if do_parse_curves:
                self.initialize_db_for_curves(db=self.global_database, k_ep=k_ep, k_part=k_part)

            if do_parse_geometry:
                self.db_part_geometry_initial = get_initial_part_geometry(self.global_database, k_ep='', k_part=k_part)
                self.db_part_geometry = dict()

            if do_parse_replace:
                self.db_replaced_frames_initial = get_replaced_frames(self.global_database, k_ep='', k_part=k_part)
                self.db_replaced_frames = dict()


        gc.collect()


    def database(self):
        if self.global_database is None:
            return self.initial_database
        return self.global_database




    # TODO: no, this is is for final geometry, rework this!!!
    # Use this geometry values to replace the final one, used after stitching/stabilization
    def get_shot_stitching_crop(self, shot_no):
        if shot_no in self.db_stitching_shots_parameters.keys():
            if 'crop' in self.db_stitching_shots_parameters[shot_no].keys():
                return self.db_stitching_shots_parameters[shot_no]['geometry']
        # print("returned default for shot no. %d" % (shot_no))
        return [0, 0, 0, 0]



    # Parameters for shot stitching
    def get_shot_stitching_parameters(self, shot_no):
        """Returns the parameters for this shot
        """
        for db_parameters in [self.db_stitching_shots_parameters,
                                self.db_stitching_shots_parameters_initial]:
            if shot_no in db_parameters.keys():
                if db_parameters[shot_no]['is_enabled']:
                    return db_parameters[shot_no]
        return deepcopy(STITCHING_SHOT_PARAMETERS_DEFAULT)


    def set_shot_stitching_parameters(self, shot_no, parameters):
        """Set new parameters for this shot
        """
        if shot_no not in self.db_stitching_shots_parameters.keys():
            self.db_stitching_shots_parameters[shot_no] = deepcopy(STITCHING_SHOT_PARAMETERS_DEFAULT)
        self.db_stitching_shots_parameters[shot_no].update(parameters)
        self.is_stitching_db_modified = True


    def remove_shot_stitching_parameters(self, shot_no):
        """Remove the parameters for this shot
        """
        if shot_no not in self.db_stitching_shots_parameters_initial.keys():
            # Set a flag to remove this parameters (use is_enabled flag)
            if shot_no not in self.db_stitching_shots_parameters.keys():
                self.db_stitching_shots_parameters[shot_no] = deepcopy(self.db_stitching_shots_parameters_initial[shot_no])
            self.db_stitching_shots_parameters[shot_no]['is_enabled'] = False
        else:
            # Not defined in initial db, remove from modified
            if shot_no in self.db_stitching_shots_parameters.keys():
                del self.db_stitching_shots_parameters[shot_no]

        # Remove all customized parameters for each frame in this shot
        self.remove_all_frames_stitching_parameters()
        self.is_stitching_db_modified = True


    def remove_single_frame_stitching_parameters(self, shot_no, frame_no):
        if (shot_no in self.db_stitching_shots_parameters_initial.keys()
            and frame_no in self.db_stitching_shots_parameters_initial[shot_no].keys()):
            # Set a flag to remove this parameters (use is_enabled flag)
            if shot_no not in self.db_stitching_frames_parameters.keys():
                self.db_stitching_frames_parameters[shot_no] = dict()
            if frame_no not in self.db_stitching_frames_parameters[shot_no].keys():
                self.db_stitching_frames_parameters[shot_no][frame_no] = deepcopy(self.db_stitching_shots_parameters_initial[shot_no][frame_no])
            self.db_stitching_shots_parameters[shot_no][frame_no]['is_enabled'] = False
        else:
            # Not in initial, remove from modified
            if (shot_no in self.db_stitching_frames_parameters.keys()
                and frame_no in self.db_stitching_frames_parameters[shot_no].keys()):
                del self.db_stitching_frames_parameters[shot_no][frame_no]
        self.is_stitching_db_modified = True


    def remove_all_frames_stitching_parameters(self, shot_no):
        """Remove the parameters for all frames
        """
        if shot_no not in self.db_stitching_frames_parameters_initial.keys():
            # Set a flag to remove this parameters (use is_enabled flag)
            if shot_no not in self.db_stitching_frames_parameters.keys():
                self.db_stitching_frames_parameters[shot_no] = dict()

            for f_no, f_values in self.db_stitching_frames_parameters_initial.items():
                if f_no not in self.db_stitching_frames_parameters[shot_no].keys():
                    self.db_stitching_frames_parameters[shot_no][f_no] = deepcopy(f_values)
                self.db_stitching_frames_parameters[shot_no][f_no]['is_enabled'] = False
        else:
            # Not defined in initial db, remove from modified
            if shot_no in self.db_stitching_frames_parameters.keys():
                del self.db_stitching_frames_parameters[shot_no]
        self.is_stitching_db_modified = True


    # Stitching parameters used for each frame (overwrite the one from shot)
    def get_frame_stitching_parameters(self, shot_no, frame_no):
        """ Return the parameters used for the stitching: the parameters
        might be different for each frame, thus get parameters from frame is defined
        otherwise, returns the parameters for the shot
        """
        if shot_no in self.db_stitching_frames_parameters.keys():
            if frame_no in self.db_stitching_frames_parameters[shot_no].keys():
                return self.db_stitching_frames_parameters[shot_no][frame_no]

        if shot_no in self.db_stitching_frames_parameters_initial.keys():
            if frame_no in self.db_stitching_frames_parameters_initial[shot_no].keys():
                return self.db_stitching_frames_parameters_initial[shot_no][frame_no]

        return self.get_shot_stitching_parameters(shot_no=shot_no)


    def set_frame_stitching_parameters(self, shot_no, frame_no, parameters):
        """Set new parameters for this shot
        """
        if shot_no not in self.db_stitching_frames_parameters.keys():
            self.db_stitching_frames_parameters[shot_no] = dict()
        self.db_stitching_frames_parameters[shot_no][frame_no] = deepcopy(STITCHING_SHOT_PARAMETERS_DEFAULT)
        self.db_stitching_frames_parameters[shot_no][frame_no].update(parameters)
        self.is_stitching_db_modified = True


    def set_stitching_parameters(self, shot_no, frame_no, parameters):
        if parameters['is_shot']:
            # These parameters are the new ones for the shot
            self.set_shot_stitching_parameters(shot_no=shot_no, parameters=parameters)
        else:
            self.set_frame_stitching_parameters(shot_no=shot_no, frame_no=frame_no, parameters=parameters)
        self.is_stitching_db_modified = True




    # Stabilization parameters
    def get_shot_stabilize_parameters(self, shot_no, frame_no=-1, initial=False):
        """ Return the parameters used for the stabilization
        """
        # print("get_shot_stabilize_parameters: shot no. %d, frame no. %d" % (shot_no, frame_no))
        # pprint(self.db_stabilize_shots_parameters)

        if shot_no in self.db_stabilize_shots_parameters.keys() and not initial:
            # print("found in modified")
            parameters = self.db_stabilize_shots_parameters[shot_no]
        elif shot_no in self.db_stabilize_shots_parameters_initial.keys():
            # print("found in initial")
            parameters = self.db_stabilize_shots_parameters_initial[shot_no]
        else:
            # print("Error, no stabilization defined for this shot")
            return deepcopy(STABILIZATION_SHOT_PARAMETERS_DEFAULT)

        if frame_no == -1:
            return parameters

        # A shot may contains multiple shots; this dict contains a list of segments
        for segment in parameters:
            if segment['start'] <= frame_no < segment['end']:
                return segment
        # print("segment not found for %d" % (frame_no))
        return deepcopy(STABILIZATION_SHOT_PARAMETERS_DEFAULT)


    def set_shot_stabilize_parameters(self, shot_no, shot_parameters):
        if type(shot_parameters) is dict:
            self.db_stabilize_shots_parameters[shot_no][0].update(shot_parameters)
        else:
            self.db_stabilize_shots_parameters[shot_no] = deepcopy(shot_parameters)
        self.is_stabilize_db_modified = True


    def reset_shot_stabilize_parameters(self, shot_no):
        print("reset shot stabilization parameters")
        if shot_no in self.db_stabilize_shots_parameters.keys():
            del self.db_stabilize_shots_parameters[shot_no]
        self.flush_frames_stabilize(shot_no)



    # Stabilization values for each frame
    def get_frame_stabilize(self, shot_no, frame_no):
        for db_tmp in [self.db_stabilize_frames,
                        self.db_stabilize_frames_initial]:
            if shot_no in db_tmp.keys() and frame_no in db_tmp[shot_no].keys():
                return db_tmp[shot_no][frame_no]
        return None


    def set_frame_stabilize(self, shot_no, frame_no, transformation):
        db_modified = self.db_stabilize_frames
        if shot_no not in db_modified.keys():
            db_modified[shot_no] = dict()
        db_modified[shot_no][frame_no] = transformation
        self.is_stabilize_db_modified = True


    def flush_frames_stabilize(self, shot_no):
        print("flush_frames_stabilize")
        db_modified = self.db_stabilize_frames
        if shot_no in db_modified.keys():
            del db_modified[shot_no]




    # Crop to apply after stabilization/image stitching
    def get_shot_st_geometry(self, shot_no):
        for db_tmp in [self.db_st_geometry,
                        self.db_st_geometry_initial]:
            if shot_no in db_tmp.keys():
                return db_tmp[shot_no]
        return [0, 0, 0, 0]

    def set_shot_st_geometry(self, shot_no, geometry):
        self.db_st_geometryp[shot_no] = geometry
        self.is_geometry_db_modified = True

    def discard_shot_st_geometry(self, shot_no):
        if shot_no in self.db_st_geometry.keys():
            del self.db_st_geometry[shot_no]
        self.is_geometry_db_modified = True





    def is_db_modified(self, type:str=''):
        if type == 'curves':
            return self.is_curves_db_modified
        elif type == 'shot_selection':
            return self.is_curves_selection_db_modified
        elif type == 'replace':
            return self.is_replace_db_modified
        elif type == 'geometry':
            return self.is_geometry_db_modified
        elif type == 'stitching':
            return self.is_stabilize_db_modified
        elif type == 'stabilization':
            return self.is_stitching_db_modified
        elif type == 'bgd_curves':
            return self.is_bgd_curves_db_modified


        return (self.is_curves_db_modified
            or self.is_curves_selection_db_modified
            or self.is_replace_db_modified
            or self.is_geometry_db_modified
            or self.is_stabilize_db_modified
            or self.is_stitching_db_modified
            or self.is_bgd_curves_db_modified)


    def get_modified_db(self) -> list:
        modified_db = list()

        if self.is_curves_db_modified:
            modified_db.append('curves')

        if self.is_curves_selection_db_modified:
            modified_db.append('curves selection')

        if self.is_replace_db_modified:
            modified_db.append('frames to replace')

        if self.is_geometry_db_modified:
            modified_db.append('part or shot geometry')

        if self.is_stabilize_db_modified:
            modified_db.append('stabilization values')

        if self.is_stitching_db_modified:
            modified_db.append('stitching values')

        if self.is_bgd_curves_db_modified:
            modified_db.append('curves before stitching')

        return modified_db




    def save_stabilize_database(self, k_ep, k_part, shots):
        print("save_stabilize_database")
        if not self.is_stabilize_db_modified:
            return True

        log.info("save stabilization database %s:%s" % (k_ep, k_part))
        db = self.global_database

        for shot_no, shot in shots.items():
            # print("***********************************************")
            # pprint(shot)

            # Select the shot used for the generation
            if 'src' in shot.keys() and shot['src']['use']:
                k_ed_src = shot['src']['k_ed']
                k_ep_src = shot['src']['k_ep']
                k_part_src = get_k_part_from_frame_no(db, k_ed=k_ed_src, k_ep=k_ep_src, frame_no=shot['src']['start'])
                shot_src = get_shot_from_frame_no_new(db,
                    shot['src']['start'], k_ed=k_ed_src, k_ep=k_ep_src, k_part=k_part_src)
                if 'count' not in shot['src'].keys():
                    shot['src']['count'] = shot_src['count']
                if shot_src is None:
                    sys.exit("Error: save_stabilize_database: shot_src is None")
            else:
                k_ed_src = db[k_ep]['common']['video']['reference']['k_ed']
                k_ep_src = k_ep
                k_part_src = k_part
                shot_src = shot


            # Use the config file
            if k_part in K_GENERIQUES:
                k_ed_src = db[k_part]['common']['video']['reference']['k_ed']
                k_part_src = k_part


            # Add parameters
            if shot_no not in self.db_stabilize_shots_parameters.keys():
                log.info("This shot has not been modified, discard save")
                print(("This shot has not been modified, discard save"))
                self.is_stabilize_db_modified = False
                return True


            # Open configuration file
            if k_part in K_GENERIQUES:
                filepath = os.path.join(db['common']['directories']['config'], k_part_src, "%s_stabilize.ini" % (k_part))
            else:
                filepath = os.path.join(db['common']['directories']['config'], k_ep_src, "%s_stabilize.ini" % (k_ep))
            if filepath.startswith("~/"):
                filepath = os.path.join(PosixPath(Path.home()), filepath[2:])


            # Parse the file
            if os.path.exists(filepath):
                config_stabilize = configparser.ConfigParser(dict_type=collections.OrderedDict)
                config_stabilize.read(filepath)
            else:
                config_stabilize = configparser.ConfigParser({}, collections.OrderedDict)

            # pprint(self.db_stabilize_frames)

            # Update the config file
            k_section = '%s.%s.%s' % (k_ed_src, k_ep_src, k_part_src)

            # Create a section if it does not exist
            if not config_stabilize.has_section(k_section):
                config_stabilize[k_section] = dict()


            parameters = self.db_stabilize_shots_parameters[shot_no]
            key_str = "%d_parameters" % (shot['start'])

            if parameters is None:
                print("cannot add parameters")
                pprint(parameters)
                # No parameters or default for this shot
                key_str = "%d_parameters" % (shot['start'])
                if config_stabilize.has_option(k_section, key_str):
                    del config_stabilize[k_section, key_str]

                for f_no in range(shot['start'], shot['start'] + shot['count']):
                    if config_stabilize.has_option(k_section, str(f_no)):
                        del config_stabilize[k_section, str(f_no)]
            else:
                # Parameters are specified,
                parameters_str = ""
                for p in parameters:
                    if p['is_enabled'] and p['is_processed']:
                        # Calculation has already been done
                        parameters_str += "\nsegment=%d:%d:%d, ref_points=%d:%.2f:%d:%d, delta_interval=%s" % (
                            p['start'],
                            p['end'],
                            p['ref'],
                            p['max_corners'],
                            p['quality_level'],
                            p['min_distance'],
                            p['block_size'],
                            ':'.join(map(lambda x: "%d" % (x), p['delta_interval']))
                        )
                    else:
                        print("Error: calculations have not been done, discard")
                        self.is_stabilize_db_modified = False
                        return False
                config_stabilize.set(k_section, key_str, parameters_str)

            # Add dx, dy for each frame
            for f_no in range(shot['start'], shot['start'] + shot['count']):
                dx_dy_array = self.get_frame_stabilize(shot_no, frame_no=f_no)
                if dx_dy_array is not None:
                    transformation_str = "%f:%f" % (dx_dy_array[0], dx_dy_array[1])
                    config_stabilize.set(k_section, str(f_no), transformation_str)
                else:
                    if config_stabilize.has_option(k_section, str(f_no)):
                        config_stabilize.remove_option(k_section, str(f_no))

            if False:
                # Remove unused sections and sort
                for k_section in config_stabilize.sections():
                    if len(config_stabilize[k_section]) == 0:
                        config_stabilize.remove_section(k_section)

            # Sort the section
            config_stabilize[k_section] = collections.OrderedDict(sorted(config_stabilize[k_section].items(), key=lambda x: x[0]))


            # Write to the database
            with open(filepath, 'w') as config_file:
                config_stabilize.write(config_file)

        self.is_stabilize_db_modified = False
        return True







    def event_save_database(self, curves:dict):
        log.info("global mode: save bgd curve as %s for image %s" % (curves['k_curves'], curves['image_name']))

        k_curves = curves['k_curves']
        # Save curves
        if curves['points'] is not None and k_curves != '':
            self.model_curves.save_bgd_curves(k_curves, curves['points'])

        # Modify shot: use the frame to find the shot no.
        frame = self.framelist.get_frame(curves['image_name'])

        # Save the database, use the frame struct to save the
        # correspondant edition/episode/part
        self.model_curves.save_curves_database(k_ep=frame['k_ep'], k_part=frame['k_part'])
        frame['k_curves_initial'] = k_curves

        # Send a list of modified shots
        self.signal_refresh_modified_shots.emit(self.model_curves.get_modified_shots())

        self.signal_refresh_frame_properties.emit(frame)
