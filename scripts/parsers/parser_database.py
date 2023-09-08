# -*- coding: utf-8 -*-
import sys

from pprint import pprint
from utils.pretty_print import *

from parsers.parser_common import parse_common_configuration
from parsers.parser_editions import parse_editions
from parsers.parser_episodes import (
    parse_episodes_target,
    parse_get_dependencies_for_episodes,
    db_init_episodes,
    parse_episode,
)
from parsers.parser_frames import (
    parse_frames_for_study,
    parse_frames_for_study_g,
)
from parsers.parser_generiques import (
    parse_generiques_target,
    parse_generiques,
    get_dependencies_for_generique,
)
from shot.consolidate_target_shots import (
    consolidate_target_shots,
    consolidate_target_shots_g,
)
from parsers.parser_curves import parse_curve_configurations
from parsers.parser_geometry import parse_geometry_configurations
from parsers.parser_replace import parse_replace_configurations
from parsers.parser_stabilize import parse_stabilize_configurations
from utils.common import (
    K_GENERIQUES,
    K_NON_GENERIQUE_PARTS,
)
from video.calculate_av_sync import calculate_av_sync
from video.consolidate_av_tracks import consolidate_av_tracks

from utils.path import PATH_DATABASE



def parse_database(database, k_ep, lang:str=''):
    """
        database: global database
        k_ep: episode to generate
        k_ed: if specified, only source will be used (study mode)
    """
    if k_ep == 'ep00':
        print_lightcyan(f"parse database")
    else:
        print_lightcyan(f"parse database, target: {k_ep}")


    # Parse and merge dictionaries -> common configuration
    parse_common_configuration(database, PATH_DATABASE, language=lang)


    # Parse editions: folders, files and additional settings: dimension
    parse_editions(database, cfg_foldername=PATH_DATABASE, force=True)

    # Initialize dictionary for episodes per edition
    for k_ed_tmp in database['editions']['available']:
        db_init_episodes(database, k_ed=k_ed_tmp, force=True)
    if False:
        print("db_init_episodes")
        print("------------------------------------")
        pprint(database[k_ep]['video'].keys())
        print("------------------------------------")
        sys.exit()


    for k_ed_tmp in database['editions']['available']:
        parse_generiques(database, k_ed=k_ed_tmp)
    if False:
        print("parse_generiques")
        print("------------------------------------")
        for k_part_g in K_GENERIQUES:
            print("--------------- %s ---------------------" % (k_part_g))
            pprint(database[k_part_g])
        print("------------------------------------")
        sys.exit()



    # Parse database file which contains common settings for all episodes
    parse_episodes_target(database)
    if False:
        print("parse_episodes_target")
        print("-------------- %s ------------------" % (k_ep))
        pprint(database[k_ep]['video'].keys())
        print("------------------------------------")
        sys.exit()


    # Parse database file used for the target
    parse_generiques_target(database)

    # Create a dict of dependencies for generiques
    dependencies = dict()
    for k_part_g in K_GENERIQUES:
        dependencies_tmp = get_dependencies_for_generique(database, k_part_g=k_part_g)
        for k, v in dependencies_tmp.items():
            if k not in dependencies.keys():
                dependencies[k] = list()
            dependencies[k] = list(set(dependencies[k] + v))

    if k_ep != 'ep00':
        # Parse episode at first (required to generate dependencies)
        for k_ed_tmp in database['editions']['available']:
            print_lightgrey("  - parse %s:%s" % (k_ed_tmp, k_ep))
            parse_episode(database, k_ed=k_ed_tmp, k_ep=k_ep)

        # Get dependencies for this episode
        dependencies_tmp = parse_get_dependencies_for_episodes(database, k_ep)

    if False:
        print("parse_episode")
        print("------------------------------------")
        pprint(database[k_ep]['video'].keys())
        print("------------------------------------")
        sys.exit()

    # Merge dependencies
    for k, v in dependencies_tmp.items():
        if k not in dependencies.keys():
            dependencies[k] = list()
        dependencies[k] = list(set(dependencies[k] + v))

    # print_lightcyan("dependencies: ", end='')
    # print(dependencies)

    # Parse episodes which are required (dependencies)
    for k_ed_tmp, v in dependencies.items():
        for k_ep_tmp in v:
            if k_ep_tmp == k_ep:
                # Do not parse this episode another time
                continue
            print_lightgrey(f"  - parse dependency: {k_ed_tmp}:{k_ep_tmp}")
            parse_episode(database, k_ed=k_ed_tmp, k_ep=k_ep_tmp)


    # Parse other config files for each dependency
    already_parsed = list()
    for k_ed_tmp, v in dependencies.items():
        for k_ep_tmp in dependencies[k_ed_tmp]:
            if k_ep_tmp not in already_parsed:
                parse_replace_configurations(database, k_ep_or_g=k_ep_tmp)
                parse_stabilize_configurations(database, k_ep_or_g=k_ep_tmp)
                parse_curve_configurations(database, k_ep_or_g=k_ep_tmp)
                already_parsed.append(k_ep_tmp)


    # Parse the geometry for the target episode only
    # Otherwise it is overwritten by the following episodes
    if k_ep != 'ep00':
        parse_geometry_configurations(database, k_ep_or_g=k_ep)

    # Génériques: debut/fin
    for k_part_g in ['g_fin', 'g_debut']:
        # Replaced frames
        parse_replace_configurations(database, k_ep_or_g=k_part_g)

        # Parameters used to stabilize
        parse_stabilize_configurations(database, k_ep_or_g=k_part_g)

        # Curves: this parser update the shots for each episode/part
        parse_curve_configurations(database, k_ep_or_g=k_part_g)

        # Crop and resize
        parse_geometry_configurations(database, k_ep_or_g=k_part_g)

        # Create shots used for the generation
        consolidate_target_shots_g(database, k_ep='', k_part_g=k_part_g)

        # Consolidate by aligning the A/V tracks of generiques
        consolidate_av_tracks(database, k_ep='', k_part=k_part_g)
        # if k_part_g == 'g_fin':
        #     sys.exit()

    # Consolidate database for the episode ONLY
    if k_ep != 'ep00':
        for k_p in K_NON_GENERIQUE_PARTS:
            consolidate_target_shots(database, k_ep=k_ep, k_part=k_p)

        for k_part_g in ['g_asuivre', 'g_documentaire']:
            parse_replace_configurations(database, k_ep_or_g=k_part_g)
            parse_stabilize_configurations(database, k_ep_or_g=k_part_g)
            parse_curve_configurations(database, k_ep_or_g=k_part_g)
            parse_geometry_configurations(database, k_ep_or_g=k_part_g)

            consolidate_target_shots_g(database, k_ep=k_ep, k_part_g=k_part_g)

        calculate_av_sync(database, k_ep=k_ep)
        consolidate_av_tracks(database, k_ep=k_ep)

        pprint_episode(database, k_ep=k_ep)
    else:
        pprint_g_debut_fin(database)



def parse_database_for_study(db, k_ed, k_ep, k_part):
    """
        database: global database
        k_ep: episode to generate
        k_ed: if specified, only source will be used (study mode)
    """

    print("Parse database for study")
    verbose = False

    parse_common_configuration(db, PATH_DATABASE)
    parse_editions(db, cfg_foldername=PATH_DATABASE)
    db_init_episodes(db, k_ed=k_ed)
    parse_generiques(db, k_ed=k_ed)
    parse_episode(db, k_ed=k_ed, k_ep=k_ep)
    parse_replace_configurations(db, k_ep_or_g=k_ep)
    parse_curve_configurations(db, k_ep_or_g=k_ep)
    parse_geometry_configurations(db, k_ep_or_g=k_ep)

    for k_p in ['g_debut', 'g_fin']:
        parse_replace_configurations(db, k_ep_or_g=k_p)
        parse_curve_configurations(db, k_ep_or_g=k_p)
        parse_geometry_configurations(db, k_ep_or_g=k_p)

    if k_part in K_GENERIQUES:
        parse_frames_for_study_g(db, k_part_g=k_part)

    parse_frames_for_study(db, k_ep=k_ep)


