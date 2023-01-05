# -*- coding: utf-8 -*-
import sys

import configparser
from copy import deepcopy
import os
import os.path
from pathlib import (
    Path,
    PosixPath,
)
import re

from pprint import pprint

from parsers.parser_av import (
    parse_audio_section,
    parse_video_section,
)
from parsers.parser_filters import (
    parse_and_update_filters,
    parse_filters_initialize,
    parser_filters_consolidate,
)
from parsers.parser_frames import parse_framelist
from parsers.parser_parts import parse_parts_section
from parsers.parser_shots import (
    consolidate_shots_after_parse,
    parse_shotlist,
)
from utils.common import (
    K_ALL_PARTS,
    K_PARTS,
    nested_dict_set,
    nested_dict_get,
)




#===========================================================================
#
#   Initialize configuration for all episodes
#
#===========================================================================
def db_init_episodes(database, k_ed, ep_min:int=1, ep_max:int=39):
    # ep_maxCount is the maximum nb of episodes for debug purpose
    db_common = database['common']

    for i in range(ep_min, min(40, ep_max+1)):
        k_ep = 'ep%02d' % i

        # Do not create section if input file does not exist
        if (k_ep not in database['editions'][k_ed]['inputs']['video'].keys()
            and k_ep not in database['editions'][k_ed]['inputs']['audio'].keys()):
            # print("warning: input file for episode no. %d does not exist" % (i))
            continue

        # Create structure for this episode/edition
        if k_ep not in database.keys():
            database[k_ep] = dict()
        database[k_ep][k_ed] = {
            'filters': dict(),
        }
        db_episode = database[k_ep][k_ed]

        # default sections:
        # audio section is set to None to simplify later parsing
        for k_part in K_ALL_PARTS:
            db_episode[k_part] = {
                'video': {
                    'geometry': None,
                    'replace': dict(),
                    'input': database['editions'][k_ed]['inputs']['video'][k_ep],
                },
                'audio': {
                    'input': database['editions'][k_ed]['inputs']['audio'][k_ep],
                },
            }

        # # Frames
        # nested_dict_set(db_episode, db_common['directories']['frames'], 'path', 'frames')

        # # Change relative path to absolute
        # for key in db_episode['path'].keys():
        #     d = db_episode['path'][key]
        #     d = d.replace('\"', '')
        #     if d.startswith("~/"):
        #         d = os.path.join(PosixPath(Path.home()), d[2:])
        #     else:
        #         d = os.path.normpath(os.path.join(os.getcwd(), d)).strip('\n')
        #     db_episode['path'][key] = d


#===========================================================================
#
#   Parse the common episode file for all editions
#
#===========================================================================
def parse_episodes_target(db, ep_min=1, ep_max:int=39, study_mode=False):
    # ep_maxCount is the maximum nb of episodes: used for debug

    for i in range(ep_min, min(40, ep_max+1)):
        k_ep = 'ep%02d' % i
        nested_dict_set(db, dict(), k_ep, 'common')
        db_ep_common = db[k_ep]['common']

        nested_dict_set(db, dict(), k_ep, 'target')
        db_ep_target = db[k_ep]['target']


        # Open configuration file
        filepath = os.path.join(db['common']['directories']['config'], k_ep, "%s_target.ini" % (k_ep))
        if filepath.startswith("~/"):
            filepath = os.path.join(PosixPath(Path.home()), filepath[2:])
        if not os.path.exists(filepath):
            # print("Info: fichier de configuration non défini: %s" % (filepath))
            # define a default filter
            db_ep_common.update({
                'filters': {
                    'default': parse_filters_initialize(type='default'),
                },
            })
            continue

        # Parse configuration
        # print("parse_episodes_target: filepath=%s" % (filepath))
        config = configparser.ConfigParser()
        config.read(filepath)
        for k_section in config.sections():
            # Parse only supported sections:

            # Audio
            #----------------------------------------------------
            if k_section == 'audio':
                nested_dict_set(db_ep_target, dict(), 'audio')
                parse_audio_section(db_ep_target['audio'], config, verbose=False)

            # Video
            #----------------------------------------------------
            elif k_section == 'video':
                nested_dict_set(db_ep_target, dict(), 'video')
                db_ep_target['video']['k_ed_ref'] = db['common']['reference']['edition']
                parse_video_section(db_ep_target['video'], config, k_ep, verbose=False)

            # Frames (used for studies)
            #----------------------------------------------------
            elif k_section == 'frames' and study_mode:
                # Parse this section only when in study mode (--frames)
                db_ep_common.update({
                    'frames': {
                        'path_output': os.path.join(db['common']['directories']['frames'], "%s" % (k_ep)),
                    },
                })

                for k_part in config.options(k_section):
                    value_str = config.get(k_section, k_part)
                    value_str = value_str.replace(' ','')

                    db_ep_common['frames'][k_part] = list()
                    parse_framelist(db_ep_common['frames'][k_part], value_str)

            # Filters
            #----------------------------------------------------
            elif k_section.startswith("filters"):
                parse_and_update_filters(db_ep_common, config, k_section, verbose=False)


        # Add path cache to the target structure
        db_ep_target.update({
            'path_cache': os.path.join(db['common']['directories']['cache'], "%s" % (k_ep)),
        })





#===========================================================================
#
#   Parse a single episode configuration file
#
#===========================================================================
def parse_episode(database, k_ed, k_ep, verbose=False):

    # pprint(database['common']['directories']['config'])

    # Open configuration file
    filepath = os.path.join(database['common']['directories']['config'], k_ep, "%s_%s.ini" % (k_ep, k_ed))
    if filepath.startswith("~/"):
        filepath = os.path.join(PosixPath(Path.home()), filepath[2:])
    # if not os.path.exists(filepath):
        # print("Warning: episode %02d, fichier de configuration manquant: %s" % (episode_no, filepath))
        # sys.exit()

    # If the input video file has not been found, do not parse the config file
    if k_ed not in database[k_ep].keys():
        print("Erreur: parse_episode: fichier %s ou fichier video manquant pour %s:%s" % (filepath, k_ed, k_ep))
        sys.exit()

    # Get config from edition
    db_episode = database[k_ep][k_ed]


    # Parse configuration
    config = configparser.ConfigParser()
    config.read(filepath)
    for k_section in config.sections():
        # if verbose: print("\tsection=%s" % (k_section))

        # Filters
        #----------------------------------------------------
        if k_section.startswith("filters"):
            parse_and_update_filters(db_episode, config, k_section, verbose=verbose)

        # Parts: frame start and (end+1)
        #----------------------------------------------------
        elif k_section == 'parts':
            parse_parts_section(db_episode, config, k_ep, verbose=False)

        # Parts: shots and other properties
        #----------------------------------------------------
        elif k_section in K_ALL_PARTS:
            k_part = k_section
            for k_option in config.options(k_section):
                value_str = config.get(k_section, k_option)
                value_str = value_str.replace(' ','')

                # Shots
                if k_option == 'shots':
                    if k_section in ['episode',
                                    'reportage',
                                    'g_debut',
                                    'g_fin',
                                    'g_asuivre',
                                    'g_reportage']:
                        # if 'shots' not in db_episode[k_part]['video'].keys():
                        db_episode[k_part]['video'].update({'shots': list()})
                        parse_shotlist(db_episode[k_part]['video']['shots'], k_ep, k_part, value_str)

                    elif k_section in ['precedemment', 'asuivre']:
                        # Precedemment and asuivre are different as some shots
                        # may be replaced
                        # if 'shots' not in db_episode[k_part]['video'].keys():
                        db_episode[k_part]['video'].update({'shots': list()})
                        parse_shotlist(db_episode[k_part]['video']['shots'], k_ep, k_part, value_str)
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

                db_episode[k_part]['video'].update({
                    'offsets': offsets,
                })
                # print("offsets, %s, part %s: " % (k_ep, k_part), offsets)
                # pprint(offsets)
                # print("TODO: reorder offsets")

    # Copy frames dict from common if not specified in configuration file
    # for k in database[k_ep]['common'].keys():
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
    db_episode['dimensions'] = database['editions'][k_ed]['dimensions']


    # Consolidate filters
    # if k_ep == 'ep17':
    #     print("------------ consolidate filters ------------")
    #     print("#### before consolidation: database[%s][%s]['g_reportage'][filters]" % (k_ed, k_ep))
    #     pprint(database['common']['filters'])
    #     print("#### before consolidation: database[common][filters]")
    #     pprint(database['common']['filters'])
    #     print("#### before consolidation: database[%s][common][filters]" % (k_ep))
    #     pprint(database[k_ep]['common']['filters'])
    #     print("#### before consolidation: database[%s][%s][filters]" % (k_ed, k_ep))
    #     pprint(database[k_ep][k_ed]['filters'])
    #     print("###########################")
    #     sys.exit()

    # Create a default filter for each part if not specified
    for k_part in K_PARTS:
        if k_part not in database[k_ep][k_ed]['filters'].keys():
            database[k_ep][k_ed]['filters'][k_part] = parse_filters_initialize(type='default')

        if 'filters' not in db_episode[k_part]['video'].keys():
            nested_dict_set(db_episode, 'default', k_part, 'video', 'filters')

    # Create a default filter for this episode if not specified
    if 'filters' not in database[k_ep]['common'].keys():
        database[k_ep]['common']['filters'] = dict()

    # Merge filters to create consistent filters for each episode/part
    parser_filters_consolidate(
        database['common']['filters'],
        database['editions'][k_ed]['filters'],
        database[k_ep]['common']['filters'],
        database[k_ep][k_ed]['filters'],
        label="[%s:%s]" % (k_ed, k_ep),
        verbose=verbose)


    # Calculate durations for each parts based on shots duration
    for k_p in K_ALL_PARTS:
        consolidate_shots_after_parse(db=database, k_ep=k_ep, k_part=k_p, k_ed=k_ed)


    return True


def parse_get_dependencies_for_episodes(db, k_ep) -> dict:
    """Return a dict of edition and episode which are required for
    this episode

    """
    dependencies = dict()

    # Edition used as the default one
    try: k_ed_src = db[k_ep]['target']['video']['src']['k_ed']
    except: k_ed_src = db['editions']['k_ed_ref']

    # Common part
    for k_part in K_PARTS:
        if k_part not in db[k_ep]['target']['video'].keys():
            continue

        db_video = db[k_ep]['target']['video'][k_part]
        if 'shots' in db_video.keys():
            shots = db_video['shots']
            for shot in shots:
                # print(shot)
                if 'src' in shot.keys() and 'k_ep' in shot['src'].keys():
                    if 'k_ed' in shot['src']:
                        k_ed_dep = shot['src']['k_ed']
                    else:
                        k_ed_dep = k_ed_src

                    if k_ed_dep not in dependencies.keys():
                        dependencies[k_ed_dep] = list()
                    dependencies[k_ed_dep].append(shot['src']['k_ep'])

    # Edition used as the default source
    for k_part in K_PARTS:
        if k_part not in db[k_ep][k_ed_src].keys():
            continue

        db_video = db[k_ep][k_ed_src][k_part]['video']
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