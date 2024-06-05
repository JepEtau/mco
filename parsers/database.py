import os
from pprint import pprint
import sys
from typing import Literal
from utils.p_print import *
from utils.path_utils import absolute_path

from .av_sync import consolidate_av_sync
from .common import parse_common_configuration
from .credits import (
    parse_credit_target,
    parse_generiques,
    get_credits_dependencies,
)
from .edition import parse_editions
from .episode import (
    parse_episodes_target,
    get_episode_dependencies,
    db_init_episodes,
    parse_episode,
)
from .frames import (
    parse_frames_for_study,
    parse_frames_for_study_g,
)
from .p_print import pprint_episode, pprint_g_debut_fin
from .logger import logger
from .target_scenes import (
    consolidate_target_scenes,
    consolidate_target_scenes_g,
)
from .target_av_tracks import consolidate_av_tracks
from .geometry import parse_geometry_configurations
from .replace import parse_replace_configurations
# from .stabilize import parse_stabilize_configurations
from ._keys import (
    key,
    credit_chapter_keys,
    non_credit_chapter_keys,
)


__database_path__ = absolute_path(
    os.path.join(__file__, os.pardir, os.pardir, "db")
)


def parse_database(
    database,
    episode: str | int,
    lang: Literal['en', 'fr'] = 'fr'
) -> dict[str, tuple[int]]:
    """Return nb of frames of video and audio tracks"""

    k_ep = f"ep{episode:02}" if isinstance(episode, int) else episode
    logger.debug(lightcyan(f"parse database", f"target: {k_ep}" if k_ep != "ep00" else ""))

    # Parse and merge dictionaries -> common configuration
    parse_common_configuration(
        database,
        __database_path__,
        language=lang
    )


    # Parse editions: folders, files and additional settings: dimension
    parse_editions(database, db_dir=__database_path__, force=True)


    # Initialize dictionary for episodes per edition
    for k_ed_tmp in database['editions']['available']:
        db_init_episodes(database, k_ed=k_ed_tmp, force=True)
        # logger.debug(f"db_init_episodes: {database[k_ep]['video'].keys()}")


    for k_ed_tmp in database['editions']['available']:
        parse_generiques(database, k_ed=k_ed_tmp)
    # logger.debug("parse_generiques: ")
    # print("------------------------------------")
    # for k_chapter_g in credit_chapter_keys():
    #     print("--------------- %s ---------------------" % (k_chapter_g))
    #     pprint(database[k_chapter_g])
    # print("------------------------------------")
    # sys.exit()



    # Parse database file which contains common settings for all episodes
    parse_episodes_target(database)
    if False:
        print("parse_episodes_target")
        print("-------------- %s ------------------" % (k_ep))
        pprint(database[k_ep]['video'].keys())
        print("------------------------------------")
        sys.exit()


    # Parse database file used for the target
    parse_credit_target(database)

    # Create a dict of dependencies for generiques
    dependencies = dict()
    for k_chapter_g in credit_chapter_keys():
        dependencies_tmp = get_credits_dependencies(database, k_chapter_g=k_chapter_g)
        for k, v in dependencies_tmp.items():
            if k not in dependencies.keys():
                dependencies[k] = list()
            dependencies[k] = list(set(dependencies[k] + v))

    if k_ep != 'ep00':
        # Parse episode at first (required to generate dependencies)
        for k_ed_tmp in database['editions']['available']:
            logger.debug(lightgrey(f"parse {k_ed_tmp}:{k_ep}"))
            parse_episode(database, k_ed=k_ed_tmp, k_ep=k_ep)

        # Get dependencies for this episode
        dependencies_tmp = get_episode_dependencies(database, k_ep)

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

    # print(lightcyan("dependencies: "), end='')
    # print(dependencies)

    # Parse episodes which are required (dependencies)
    for k_ed_tmp, v in dependencies.items():
        for k_ep_tmp in v:
            if k_ep_tmp == k_ep:
                # Do not parse this episode another time
                continue
            logger.debug(lightgrey(f"parse dependency: {k_ed_tmp}:{k_ep_tmp}"))
            parse_episode(database, k_ed=k_ed_tmp, k_ep=k_ep_tmp)


    # Parse other config files for each dependency
    already_parsed = list()
    for k_ed_tmp, v in dependencies.items():
        for k_ep_tmp in dependencies[k_ed_tmp]:
            if k_ep_tmp not in already_parsed:
                parse_replace_configurations(database, k_ep_or_g=k_ep_tmp)
                # parse_stabilize_configurations(database, k_ep_or_g=k_ep_tmp)
                already_parsed.append(k_ep_tmp)


    # Parse the geometry for the target episode only
    # Otherwise it is overwritten by the following episodes
    if k_ep != 'ep00':
        parse_geometry_configurations(database, k_ep_or_g=k_ep)

    # Génériques: debut/fin
    for k_chapter_g in ['g_fin', 'g_debut']:
        # Replaced frames
        parse_replace_configurations(database, k_ep_or_g=k_chapter_g)

        # Parameters used to stabilize
        # parse_stabilize_configurations(database, k_ep_or_g=k_chapter_g)

        # Crop and resize
        parse_geometry_configurations(database, k_ep_or_g=k_chapter_g)

        # Create scenes used for the generation
        consolidate_target_scenes_g(database, k_ep='', k_chapter_c=k_chapter_g)

        # Consolidate by aligning the A/V tracks of generiques
        consolidate_av_tracks(database, k_ep='', k_chapter=k_chapter_g)
        # if k_chapter_g == 'g_fin':
        #     sys.exit()

    # Consolidate database for the episode ONLY
    if k_ep != 'ep00':
        for chapter in non_credit_chapter_keys():
            consolidate_target_scenes(database, k_ep=k_ep, k_chapter=chapter)

        for k_chapter_g in ['g_asuivre', 'g_documentaire']:
            parse_replace_configurations(database, k_ep_or_g=k_chapter_g)
            # parse_stabilize_configurations(database, k_ep_or_g=k_chapter_g)
            parse_geometry_configurations(database, k_ep_or_g=k_chapter_g)

            consolidate_target_scenes_g(database, k_ep=k_ep, k_chapter_c=k_chapter_g)

        consolidate_av_sync(database, k_ep=k_ep)
        consolidate_av_tracks(database, k_ep=k_ep)

        stats = pprint_episode(database, k_ep=k_ep)
    else:
        stats = pprint_g_debut_fin(database)

    return stats


def parse_database_for_study(db, k_ed, k_ep, k_chapter):
    """
        database: global database
        k_ep: episode to generate
        k_ed: if specified, only source will be used (study mode)
    """

    print("Parse database for study")
    verbose = False

    parse_common_configuration(db, __database_path__)
    parse_editions(db, db_dir=__database_path__)
    db_init_episodes(db, k_ed=k_ed)
    parse_generiques(db, k_ed=k_ed)
    parse_episode(db, k_ed=k_ed, k_ep=k_ep)
    parse_replace_configurations(db, k_ep_or_g=k_ep)
    parse_geometry_configurations(db, k_ep_or_g=k_ep)

    for k_p in ['g_debut', 'g_fin']:
        parse_replace_configurations(db, k_ep_or_g=k_p)
        parse_geometry_configurations(db, k_ep_or_g=k_p)

    if k_chapter in credit_chapter_keys():
        parse_frames_for_study_g(db, k_chapter_g=k_chapter)

    parse_frames_for_study(db, k_ep=k_ep)



def get_dependencies(
    db: dict,
    episode: int | str | None = None,
    chapter: str | None = None,
    track: Literal['audio', 'video', 'all'] = 'all'
) -> dict[str, list]:

    if episode is not None and episode != 0:
        return get_episode_dependencies(db, episode, track)
    else:
        return get_credits_dependencies(db, chapter, track)

