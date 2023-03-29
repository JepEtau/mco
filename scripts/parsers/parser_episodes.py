# -*- coding: utf-8 -*-
import configparser
import os
import os.path
from pathlib import (
    Path,
    PosixPath,
)
import re
import sys

from pprint import pprint

from parsers.parser_audio import parse_audio_section
from parsers.parser_video import parse_video_section

from parsers.parser_filters import (
    parse_filters,
)
from parsers.parser_parts import parse_part_sections
from parsers.parser_shots import (
    consolidate_parsed_shots,
    parse_shotlist,
    parse_target_shotlist,
)
from utils.common import (
    K_ALL_PARTS,
    K_PARTS,
    nested_dict_set,
)
from utils.pretty_print import *



#===========================================================================
#
#   Initialize configuration for all episodes
#
#===========================================================================
def db_init_episodes(db, k_ed, ep_min:int=1, ep_max:int=39):
    # ep_maxCount is the maximum nb of episodes for debug purpose
    db_common = db['common']

    for i in range(ep_min, min(40, ep_max+1)):
        k_ep = 'ep%02d' % i

        # Do not create section if input file does not exist
        if (k_ep not in db['editions'][k_ed]['inputs']['video'].keys()
            and k_ep not in db['editions'][k_ed]['inputs']['audio'].keys()):
            # print("warning: input file for episode no. %d does not exist" % (i))
            continue

        # Create structure for this episode/edition

        # default sections:
        for k_part in K_ALL_PARTS:
            nested_dict_set(db, {
                    'replace': dict(),
                }, k_ep, 'video', k_ed, k_part)

        # Set the video input file
        # nested_dict_set(db,
        #     db['editions'][k_ed]['inputs']['video'][k_ep],
        #     k_ep, 'video', k_ed, 'input')

        # Add path cache
        db[k_ep]['cache_path'] = os.path.normpath(
            os.path.join(db['common']['directories']['cache'], "%s" % (k_ep)))



#===========================================================================
#
#   Parse the common episode file for all editions
#
#===========================================================================
def parse_episodes_target(db, ep_min=1, ep_max:int=39, study_mode=False):
    # ep_maxCount is the maximum nb of episodes: used for debug

    for i in range(ep_min, min(40, ep_max+1)):
        k_ep = 'ep%02d' % i
        nested_dict_set(db, dict(), k_ep, 'video', 'common')
        db_ep_common = db[k_ep]['video']['common']

        nested_dict_set(db, dict(), k_ep, 'video', 'target')
        db_ep_target = db[k_ep]['video']['target']


        # Open configuration file
        filepath = os.path.join(db['common']['directories']['config'], k_ep, "%s_target.ini" % (k_ep))
        if filepath.startswith("~/"):
            filepath = os.path.join(PosixPath(Path.home()), filepath[2:])
        if not os.path.exists(filepath):
            continue

        # Parse configuration
        # print("parse_episodes_target: filepath=%s" % (filepath))
        config = configparser.ConfigParser()
        config.read(filepath)
        for k_section in config.sections():

            # Audio
            #----------------------------------------------------
            if k_section == 'audio':
                nested_dict_set(db, dict(), k_ep, 'audio')
                parse_audio_section(db[k_ep]['audio'], config, verbose=False)

            # Video
            #----------------------------------------------------
            elif k_section == 'video':
                db_ep_target['k_ed_ref'] = db['common']['reference']['edition']
                parse_video_section(db_ep_target, config, k_ep, verbose=False)

            # Shots
            #----------------------------------------------------
            elif k_section.startswith('shots_'):
                k_part = k_section[len('shots_'):]
                nested_dict_set(db_ep_target, list(), k_part, 'shots')
                parse_target_shotlist(db_ep_target[k_part]['shots'],
                    config, k_section, verbose=False)


#===========================================================================
#
#   Parse a single episode configuration file
#
#===========================================================================
def parse_episode(db, k_ed, k_ep, verbose=False):
    # pprint(db['common']['directories']['config'])

    # Open configuration file
    filepath = os.path.join(db['common']['directories']['config'], k_ep, "%s_%s.ini" % (k_ep, k_ed))
    if filepath.startswith("~/"):
        filepath = os.path.join(PosixPath(Path.home()), filepath[2:])
    # if not os.path.exists(filepath):
        # print("Warning: episode %02d, fichier de configuration manquant: %s" % (episode_no, filepath))
        # sys.exit()

    # If the input video file has not been found, do not parse the config file
    if k_ed not in db[k_ep]['video'].keys():
        # print("Warning: parse_episode: fichier %s ou fichier video manquant pour %s:%s" % (filepath, k_ed, k_ep))
        return
        # sys.exit()

    # Get config from edition
    db_episode = db[k_ep]


    # Parse configuration
    config = configparser.ConfigParser()
    config.read(filepath)
    for k_section in config.sections():
        if verbose: print("\tsection=%s" % (k_section))

        # Filters
        #----------------------------------------------------
        if k_section.startswith("filters"):
            parse_filters(db_episode['video'][k_ed], config, k_section, verbose=verbose)

        # Parts: frame start and (end+1)
        #----------------------------------------------------
        elif k_section == 'parts':
            parse_part_sections(db_episode['video'][k_ed], config, verbose=False)

        # Parts: shots and other properties
        #----------------------------------------------------
        elif k_section in K_ALL_PARTS:
            k_part = k_section
            for k_option in config.options(k_section):
                value_str = config.get(k_section, k_option)
                value_str = value_str.replace(' ','')

                # Shots
                db_video_part = db_episode['video'][k_ed][k_part]
                if k_option == 'shots':
                    if k_section in ['episode',
                                    'reportage',
                                    'g_debut',
                                    'g_fin',
                                    'g_asuivre',
                                    'g_reportage']:
                        # if 'shots' not in db_episode[k_part]['video'].keys():
                        db_video_part.update({'shots': list()})
                        parse_shotlist(db_video_part['shots'],
                            k_ep, k_part, value_str)

                    elif k_section in ['precedemment', 'asuivre']:
                        # Precedemment and asuivre are different as some shots
                        # may be replaced
                        # if 'shots' not in db_episode[k_part]['video'].keys():
                        db_video_part.update({'shots': list()})
                        parse_shotlist(db_video_part['shots'], k_ep, k_part, value_str)
                        # if k_ep == 'ep01' and k_part == 'asuivre':
                        #     pprint(db_episode[k_part]['video']['shots'])
                        #     sys.exit()

        # Offsets
        #----------------------------------------------------
        if k_section == 'offsets':

            for k_part in config.options(k_section):
                if verbose:
                    print("\t\t%s" % (k_part))

                # Parse list of offsets
                value_str = config.get(k_section, k_part)
                offsets = []
                for offset in value_str.split('\n'):
                    diffStr = offset.replace(' ','')
                    tmp = None
                    tmp = re.match(re.compile("^(\d+):(-?\d+)$"), diffStr)
                    if tmp is not None:
                        frameStart = int(tmp.group(1))
                        offset = int(tmp.group(2)) - frameStart
                        if offsets:
                            offsets[len(offsets)-1]['end'] = frameStart - 1
                        offsets.append({'start': frameStart, 'offset': offset, 'end': 99999999})
                        # print("\t\t\tframeStart=%d, offset=%d" % (frameStart, offset))

                db_episode['video'][k_ed][k_part].update({
                    'offsets': offsets,
                })
                # print("offsets, %s, part %s: " % (k_ep, k_part), offsets)
                # pprint(offsets)
                # print("TODO: reorder offsets")

    # Copy frames dict from common if not specified in configuration file
    # for k in db[k_ep]['common'].keys():
    #     # todo: improve this if other sections are listed in common episode file
    #     if k == 'filters':
    #         continue

    #     if k not in db_episode.keys():
    #         db_episode[k] = {}
    #         # Deactivate this to simplify the structure
    #         if False:
    #             if 'frames' not in cfg_ep[k].keys():
    #                 cfg_ep[k]['frames'] = deepcopy(cfg_ep_common[k]['frames'])
    #                 for frame in cfg_ep[k]['frames']:
    #                     frame['no'] = frame['ref']


    # Set dimensions:
    nested_dict_set(db_episode,
        db['editions'][k_ed]['dimensions'],
        'video', 'dimensions')

    # Consolidate filters
    # if k_ep == 'ep17':
    #     print("------------ consolidate filters ------------")
    #     print("#### before consolidation: db[%s][%s]['g_reportage'][filters]" % (k_ed, k_ep))
    #     pprint(db['common']['filters'])
    #     print("#### before consolidation: db[common][filters]")
    #     pprint(db['common']['filters'])
    #     print("#### before consolidation: db[%s][common][filters]" % (k_ep))
    #     pprint(db[k_ep]['common']['filters'])
    #     print("#### before consolidation: db[%s][%s][filters]" % (k_ed, k_ep))
    #     pprint(db[k_ep][k_ed]['filters'])
    #     print("###########################")
    #     sys.exit()

    # Create a default filter for each part if not specified
    # db_video = db_episode['video']
    # for k_part in K_ALL_PARTS:
    #     if k_part not in db_video[k_ed]['filters'].keys():
    #         # For each part, define the default filters
    #         db_video[k_ed]['filters'][k_part] = 'default'

    #     if 'filters' not in db_video[k_ed][k_part].keys():
    #         nested_dict_set(db_video, 'default', k_ed, k_part, 'filters')


    # Calculate durations for each parts based on shots duration
    for k_p in K_ALL_PARTS:
        consolidate_parsed_shots(db=db, k_ed=k_ed, k_ep=k_ep, k_part=k_p)




def parse_get_dependencies_for_episodes(db, k_ep) -> dict:
    """Return a dict of edition and episode which are required for
    this episode

    """
    dependencies = dict()

    # Common part
    for k_part in K_PARTS:
        if k_part not in db[k_ep]['video']['target'].keys():
            continue

        db_video = db[k_ep]['video']['target'][k_part]
        if 'shots' in db_video.keys():
            shots = db_video['shots']
            for shot in shots:
                # print(shot)
                if 'src' in shot.keys() and 'k_ep' in shot['src'].keys():
                    if 'k_ed' in shot['src']:
                        k_ed_dep = shot['src']['k_ed']
                    else:
                        k_ed_dep = db_video['k_ed_src']

                    if k_ed_dep not in dependencies.keys():
                        dependencies[k_ed_dep] = list()
                    dependencies[k_ed_dep].append(shot['src']['k_ep'])


    # Edition used as the default source
    for k_part in K_PARTS:
        k_ed_src = db[k_ep]['video']['target'][k_part]['k_ed_src']
        if k_part not in db[k_ep]['video'][k_ed_src].keys():
            continue

        db_video = db[k_ep]['video'][k_ed_src][k_part]
        if 'shots' in db_video.keys():
            shots = db_video['shots']
            for shot in shots:
                if 'src' in shot.keys() and 'k_ep' in shot['src'].keys():
                    # print(shot)
                    if 'k_ed' in shot['src']:
                        k_ed_dep = shot['src']['k_ed']
                    else:
                        k_ed_dep = k_ed_src

                    if k_ed_dep not in dependencies.keys():
                        dependencies[k_ed_dep] = list()
                    dependencies[k_ed_dep].append(shot['src']['k_ep'])

    for k_ed in dependencies.keys():
        dependencies[k_ed] = list(set(dependencies[k_ed]))

    return dependencies