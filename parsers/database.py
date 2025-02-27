from __future__ import annotations
from collections import OrderedDict
import os
from pprint import pprint
import sys
from typing import Any, Literal
from utils.mco_types import ChapterVideo
from utils.p_print import *

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
from .logger import logger
from .loop import parse_loop_file
from .target_scenes import (
    consolidate_target_scenes,
    consolidate_target_scenes_g,

)
from .target_av_tracks import (
    consolidate_av_tracks,
    consolidate_av_tracks_g_debut_fin,
)
from .geometry import parse_geometry_file
from .replace import parse_replace_file
from .dsr import parse_dsr_file
from .stabilize import parse_stabilize_file
from ._keys import (
    credit_chapter_keys,
    non_credit_chapter_keys,
    ep_key,
)
from ._db import db
from .p_print import pprint_episode, pprint_g_debut_fin
from .vsettings import parse_video_settings


def parse_database(
    episode: str | int,
    lang: Literal['en', 'fr'] = 'fr',
    edition: str = '',
    ignore_av_sync: bool = False,
    avsync_stats: bool = False
) -> dict[str, tuple[int]]:
    """Parse the database for a specified episode
        - ignore avsync when called by a tool or for stats before aligning AV channels
        - avsync_stats: to consolidate AV sync only -> ignore geometry, ....
    """


    k_ep = f"ep{episode:02}" if isinstance(episode, int) else episode
    logger.debug(lightcyan(f"parse database", f"target: {k_ep}" if k_ep != "ep00" else ""))

    # Parse and merge dictionaries -> common configuration
    parse_common_configuration(language=lang)
    parse_video_settings(verbose=False)

    # Parse editions: folders, files and additional settings: dimension
    parse_editions()

    # Initialize dictionary for episodes per edition
    for k in db['editions']['available']:
        db_init_episodes(k_ed=k)

    for k in db['editions']['available']:
        parse_generiques(k_ed=k, verbose=False)

    # Parse targets
    parse_episodes_target()
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
        if 'k' not in dependencies:
            dependencies['k'] = []
        dependencies['k'].append('ep01')

    # Merge dependencies
    for k_ed, v in dependencies_tmp.items():
        if k_ed not in dependencies.keys():
            dependencies[k_ed] = list()
        dependencies[k_ed] = list(set(dependencies[k_ed] + v))

    logger.debug(lightcyan("dependencies: "), dependencies)
    if edition != '':
        if edition not in dependencies:
            dependencies[edition] = list()
        dependencies[edition].append(k_ep)

    # Parse episodes which are required (dependencies)
    logger.debug(dependencies)
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
                parse_replace_file(k_ep_or_g=k_ep_tmp)
                parse_loop_file(k_ep=k_ep_tmp, verbose=True)
                parse_dsr_file(k_ep_or_g=k_ep_tmp)
                # parse_stabilize_configurations(k_ep_or_g=k_ep_tmp)
                already_parsed.append(k_ep_tmp)

    if edition != '':
        return None

    # Génériques: debut/fin
    for k_chapter_g in ('g_debut', 'g_fin'):
        # Replaced frames
        # parse_replace_file(k_ep_or_g=k_chapter_g)

        # Parameters used to stabilize
        # parse_stabilize_configurations(k_ep=k_ep, k_ch=k_chapter_g)

        # Create scenes used for the generation
        consolidate_target_scenes_g(k_ep='', k_ch=k_chapter_g)

        # Consolidate by aligning the A/V tracks of generiques
        consolidate_av_tracks_g_debut_fin(k_ch=k_chapter_g)


    # Consolidate database for the episode ONLY
    if k_ep != 'ep00':
    # if k_ep not in ('ep00', 'ep99'):
        for chapter in non_credit_chapter_keys():
            consolidate_target_scenes(k_ep=k_ep, k_ch=chapter)
        print(f"database, parse stabilization: {k_ep}")
        parse_stabilize_file(k_ep=k_ep)

        for k_chapter_g in ('g_asuivre', 'g_doc'):
            parse_replace_file(k_ep_or_g=k_chapter_g)
            parse_dsr_file(k_ep_or_g=k_chapter_g)
            # parse_stabilize_configurations(k_ep_or_g=k_chapter_g)
            # consolidate_target_scenes_g(k_ep=k_ep, k_ch=k_chapter_g)
            # parse_geometry_file(k_ep_or_g=k_chapter_g)

    for k_chapter_g in ('g_debut', 'g_fin'):
        parse_stabilize_file(k_ep=k_ep, k_ch=k_chapter_g)

    # Parse the geometry once all target scenes consolidated because
    # the geometry refers to the destination and not the source
    # bc of segment functionnality
    if k_ep != 'ep00':
        if not avsync_stats:
            parse_geometry_file(k_ep_or_g=k_ep)
        for k_chapter_g in credit_chapter_keys():

            if k_chapter_g in ('g_doc', 'g_asuivre'):
                consolidate_target_scenes_g(k_ep=k_ep, k_ch=k_chapter_g)
            else:
                parse_geometry_file(k_ep_or_g=k_chapter_g)
    else:
        for k_chapter_g in ('g_debut', 'g_fin'):
            parse_geometry_file(k_ep_or_g=k_chapter_g)


    if ignore_av_sync:
        return None

    stats: dict[str, Any] | None = None
    if k_ep != 'ep00':
        consolidate_av_tracks(k_ep=k_ep)

        stats = pprint_episode(k_ep=k_ep)
    else:
        stats = pprint_g_debut_fin()

    return stats, dependencies



def get_dependencies(
    episode: int | str | None = None,
    chapter: str | None = None,
    track: Literal['audio', 'video', 'all'] = 'all'
) -> OrderedDict[str, list]:

    if episode is not None and episode != 0:
        return get_episode_dependencies(episode, track)
    else:
        return get_credits_dependencies(chapter, track)

