from collections import OrderedDict
import os
from pprint import pprint
import sys
from typing import Literal
from utils.p_print import *

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
    credit_chapter_keys,
    non_credit_chapter_keys,
)
from ._db import db




def parse_database(
    episode: str | int,
    lang: Literal['en', 'fr'] = 'fr',
    edition: str = ''
) -> dict[str, tuple[int]]:
    """Return nb of frames of video and audio tracks"""

    k_ep = f"ep{episode:02}" if isinstance(episode, int) else episode
    logger.debug(lightcyan(f"parse database", f"target: {k_ep}" if k_ep != "ep00" else ""))

    # Parse and merge dictionaries -> common configuration
    parse_common_configuration(language=lang)

    # Parse editions: folders, files and additional settings: dimension
    parse_editions()

    # Initialize dictionary for episodes per edition
    for k in db['editions']['available']:
        db_init_episodes(k_ed=k)
        # logger.debug(f"db_init_episodes: {db[k_ep]['video'].keys()}")

    for k in db['editions']['available']:
        parse_generiques(k_ed=k, verbose=False)
    # logger.debug("parse_generiques: ")
    # print("------------------------------------")
    # for k_chapter_g in credit_chapter_keys():
    #     print("--------------- %s ---------------------" % (k_chapter_g))
    #     pprint(db[k_chapter_g])
    # print("------------------------------------")
    # sys.exit()

    # Parse database file which contains common settings for all episodes
    parse_episodes_target()
    # if True:
    #     print("parse_episodes_target")
    #     print("-------------- %s ------------------" % (k_ep))
    #     pprint(db[k_ep]['video']['target'])
    #     print("------------------------------------")
    #     sys.exit()


    # Parse database file used for the target
    parse_credit_target()

    # Create a dict of dependencies for generiques
    dependencies: dict[str, list] = {}
    for k_chapter_g in credit_chapter_keys():
        dependencies_tmp = get_credits_dependencies(k_chapter_g=k_chapter_g)
        for k, v in dependencies_tmp.items():
            if k not in dependencies.keys():
                dependencies[k] = list()
            dependencies[k] = list(set(dependencies[k] + v))

    if k_ep != 'ep00':
        # Parse episode at first (required to generate dependencies)
        for k in db['editions']['available']:
            logger.debug(lightgrey(f"parse {k}:{k_ep}"))
            parse_episode(k_ed=k, k_ep=k_ep)

        # Get dependencies for this episode
        dependencies_tmp = get_episode_dependencies(k_ep)

    if False:
        print("parse_episode")
        print("------------------------------------")
        pprint(db[k_ep]['video'].keys())
        print("------------------------------------")
        sys.exit()

    # Add the reference
    if lang == 'fr':
        dependencies['k'].append('ep01')

    # Merge dependencies
    for k_ed, v in dependencies_tmp.items():
        if k_ed not in dependencies.keys():
            dependencies[k_ed] = list()
        dependencies[k_ed] = list(set(dependencies[k_ed] + v))

    print(lightcyan("dependencies: "), dependencies)
    if edition != '':
        if edition not in dependencies:
            dependencies[edition] = list()
        dependencies[edition].append(k_ep)

    # Parse episodes which are required (dependencies)
    pprint(dependencies)
    for k_ed_tmp, v in dependencies.items():
        for k_ep_tmp in v:
            if k_ep_tmp == k_ep:
                # Do not parse this episode another time
                continue
            logger.debug(lightgrey(f"parse dependency: {k_ed_tmp}:{k_ep_tmp}"))
            parse_episode(k_ed=k_ed_tmp, k_ep=k_ep_tmp)


    # Parse other config files for each dependency
    already_parsed = list()
    for k_ed_tmp, v in dependencies.items():
        for k_ep_tmp in dependencies[k_ed_tmp]:
            if k_ep_tmp not in already_parsed:
                parse_replace_configurations(k_ep_or_g=k_ep_tmp)
                # parse_stabilize_configurations(k_ep_or_g=k_ep_tmp)
                already_parsed.append(k_ep_tmp)



    # Génériques: debut/fin
    for k_chapter_g in ('g_debut', 'g_fin'):
        # Replaced frames
        parse_replace_configurations(k_ep_or_g=k_chapter_g)

        # Parameters used to stabilize
        # parse_stabilize_configurations(k_ep_or_g=k_chapter_g)

        # Create scenes used for the generation
        consolidate_target_scenes_g(k_ep='', k_chapter=k_chapter_g)

        # Consolidate by aligning the A/V tracks of generiques
        consolidate_av_tracks(k_ep='', k_chapter=k_chapter_g)
        # if k_chapter_g == 'g_fin':
        #     sys.exit()

    # Consolidate database for the episode ONLY
    if k_ep != 'ep00':
    # if k_ep not in ('ep00', 'ep99'):
        for chapter in non_credit_chapter_keys():
            consolidate_target_scenes(k_ep=k_ep, k_chapter=chapter)

        for k_chapter_g in ('g_asuivre', 'g_documentaire'):
            parse_replace_configurations(k_ep_or_g=k_chapter_g)
            # parse_stabilize_configurations(k_ep_or_g=k_chapter_g)
            parse_geometry_configurations(k_ep_or_g=k_chapter_g)
            consolidate_target_scenes_g(k_ep=k_ep, k_chapter=k_chapter_g)

    # Parse the geometry once all target scenes consolidated because
    # the geometry refers to the destination and not the source
    # bc of segment functionnality
    if k_ep != 'ep00':
        parse_geometry_configurations(k_ep_or_g=k_ep)
        for k_chapter_g in credit_chapter_keys():
            parse_geometry_configurations(k_ep_or_g=k_chapter_g)

    else:
        for k_chapter_g in ('g_debut', 'g_fin'):
            parse_geometry_configurations(k_ep_or_g=k_chapter_g)

    if k_ep != 'ep00':
        consolidate_av_sync(k_ep=k_ep)
        consolidate_av_tracks(k_ep=k_ep)

        stats = pprint_episode(k_ep=k_ep)
    else:
        stats = pprint_g_debut_fin()

    return stats


def parse_database_for_study(k_ed, k_ep, k_chapter):
    """
        database: global database
        k_ep: episode to generate
        k_ed: if specified, only source will be used (study mode)
    """

    print("Parse database for study")
    verbose = False

    parse_common_configuration()
    parse_editions()
    db_init_episodes(k_ed=k_ed)
    parse_generiques(k_ed=k_ed)
    parse_episode(k_ed=k_ed, k_ep=k_ep)
    parse_replace_configurations(k_ep_or_g=k_ep)
    parse_geometry_configurations(k_ep_or_g=k_ep)

    for k_p in ('g_debut', 'g_fin'):
        parse_replace_configurations(k_ep_or_g=k_p)
        parse_geometry_configurations(k_ep_or_g=k_p)


def get_dependencies(
    episode: int | str | None = None,
    chapter: str | None = None,
    track: Literal['audio', 'video', 'all'] = 'all'
) -> OrderedDict[str, list]:

    if episode is not None and episode != 0:
        return get_episode_dependencies(episode, track)
    else:
        return get_credits_dependencies(chapter, track)

