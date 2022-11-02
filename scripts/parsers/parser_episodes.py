#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
from operator import itemgetter
from copy import deepcopy
import os
import os.path
from os import stat_result, system
from pathlib import Path
from pathlib import PosixPath
from pprint import pprint
import re
import sys

from parsers.parser_filters import *
from parsers.parser_av import *
from parsers.parser_shots import *
from parsers.parser_shots import consolidate_shots_after_parse
from utils.common import K_ALL_PARTS, K_NON_GENERIQUE_PARTS




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
        if k_ep not in database['editions'][k_ed]['inputs'].keys():
            # print("warning: input file for episode no. %d does not exist" % (i))
            continue

        # Create structure for this episode/edition
        if k_ep not in database.keys(): database[k_ep] = dict()
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
                },
                'audio': dict(),
            }

        # Default input file
        db_episode['path'] = {
            'input_audio': database['editions'][k_ed]['inputs'][k_ep],
            'input_video': database['editions'][k_ed]['inputs'][k_ep]
        }

        # Frames
        db_episode['path']['frames'] = db_common['directories']['frames']

        # Change relative path to absolute
        for key in db_episode['path'].keys():
            d = db_episode['path'][key]
            d = d.replace('\"', '')
            if d.startswith("~/"):
                d = os.path.join(PosixPath(Path.home()), d[2:])
            else:
                d = os.path.normpath(os.path.join(os.getcwd(), d)).strip('\n')
            db_episode['path'][key] = d



#===========================================================================
#
#   Parse the common episode file for all editions
#
#===========================================================================
def parse_episodes_common(db, ep_min=1, ep_max:int=39):
    # ep_maxCount is the maximum nb of episodes for debug purpose

    for i in range(ep_min, min(40, ep_max+1)):
        k_ep = 'ep%02d' % i
        if k_ep not in db.keys(): db[k_ep] = dict()
        if 'common' not in db[k_ep].keys(): db[k_ep]['common'] = dict()
        db_ep_common = db[k_ep]['common']

        # Cache
        db_ep_common['path'] = {
            'cache': os.path.join(db['common']['directories']['cache'], "%s" % (k_ep))
        }

        # Open configuration file
        filepath = os.path.join(db['common']['directories']['config'], k_ep, "%s_common.ini" % (k_ep))
        if filepath.startswith("~/"):
            filepath = os.path.join(PosixPath(Path.home()), filepath[2:])
        if not os.path.exists(filepath):
            # print("Info: fichier de configuration non défini: %s" % (filepath))
            # define a default filter
            db_ep_common['filters'] = {
                'default': parse_filters_initialize(type='default'),
            }
            continue

        # Parse configuration
        # print("parse_episodes_common: filepath=%s" % (filepath))
        config = configparser.ConfigParser()
        config.read(filepath)
        for k_section in config.sections():
            # Parse only supported sections:

            # Audio
            #----------------------------------------------------
            if k_section == 'audio':
                if 'audio' not in db_ep_common.keys():
                    db_ep_common['audio'] = dict()
                parse_audio(db_ep_common['audio'], config, verbose=False)

            # Video
            #----------------------------------------------------
            elif k_section == 'video':
                if 'video' not in db_ep_common.keys():
                    db_ep_common['video'] = dict()
                parse_video(db_ep_common['video'], config, verbose=False)


            # Frames (used for studies)
            #----------------------------------------------------
            # if k_section == 'frames':
            #     if 'frames' not in db_g_common.keys():
            #         db_g_common['frames'] = list()
            #     parse_framelist(db_ep_common['frames'], value_str)

            elif k_section == 'frames':
                for k_part in config.options(k_section):
                    value_str = config.get(k_section, k_part)
                    value_str = value_str.replace(' ','')

                    # if k_part not in cfg_episode.keys():
                    #     print("edition to use: %s" %(edition))
                    #     print("%s not in cfg_episode" % (k_part))
                    #     result = re.search("([a-z]+)_([a-z0-9]+)", k_part)
                    #     if result is not None:
                    #         print("found edition [%s]" % (result.group(2)))
                    #         if result.group(2) != edition:
                    #             print("info ignoring %s" % (k_part))
                    #             continue
                    #         else:
                    #             print("using edition %s" % (result.group(2)))
                    #             k_part = result.group(1)
                    if k_part not in db_ep_common.keys(): db_ep_common[k_part] = {}
                    db_ep_common[k_part]['frames'] = []
                    for fno in value_str.split('\n'):
                        match = None
                        match = re.match(re.compile("^([0-9]{1,2}):\s*([0-9]+)$"), fno)
                        if match is not None:
                            db_ep_common[k_part]['frames'].append({
                                'k_ep': int(match.group(1)),
                                'ref': int(match.group(2)),
                            })
                        else:
                            match = re.match(re.compile("^([0-9]+)$"), fno)
                            if match is not None:
                                match = re.match(r"([0-9]+)", fno)
                                if match:
                                    db_ep_common[k_part]['frames'].append({
                                        'k_ep': 0,
                                        'ref': int(match.group(1)),
                                    })

            # Filters
            #----------------------------------------------------
            elif k_section.startswith("filters"):
                parse_and_update_filters(db_ep_common, config, k_section, verbose=False)


            # Layers
            #----------------------------------------------------
            elif k_section == 'layers':
                for k_part in config.options(k_section):
                    if k_part not in K_NON_GENERIQUE_PARTS:
                        continue
                    value_str = config.get(k_section, k_part)
                    value_str = value_str.replace(' ','')
                    layers = value_str.split(',')

                    db_ep_common['video'][k_part]['layers'] = dict()
                    for layer in layers:
                        layer_edition = layer.split('=')
                        if layer_edition[0] not in ['bgd', 'fgd']:
                            continue
                        db_ep_common['video'][k_part]['layers'].update({
                            layer_edition[0]: layer_edition[1],
                            layer_edition[1]: layer_edition[0]
                        })


#===========================================================================
#
#   Parse a single episode configuration file
#
#===========================================================================
def parse_episode(database, k_ed, k_ep, verbose=False):

    # Open configuration file
    filepath = os.path.join(database['common']['directories']['config'], k_ep, "%s_%s.ini" % (k_ep, k_ed))
    if filepath.startswith("~/"):
        filepath = os.path.join(PosixPath(Path.home()), filepath[2:])
    # if not os.path.exists(filepath):
        # print("Warning: episode %02d, fichier de configuration manquant: %s" % (episode_no, filepath))
        # sys.exit()

    # If the input video file has not been found, do not parse the config file
    if k_ed not in database[k_ep].keys():
        sys.exit("Erreur: fichier manquant, édition '%s', épisode %d" % (k_ed, int(k_ep[-2:])))

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
            for k_part in config.options(k_section):
                valuesStr = config.get(k_section, k_part)
                valuesStr = valuesStr.replace(' ','')
                # print("[%s] -> %s, %s => [%s]" % (k_section, section, valuesStr))
                values = re.search(re.compile("^(\d+):(\d+)$"), valuesStr)

                if k_part in K_ALL_PARTS:
                    frames_count = int(values.group(2)) - int(values.group(1))
                    db_episode[k_part]['video'].update({
                        'start': int(values.group(1)),
                        'end': int(values.group(2)),
                        'count': frames_count,
                    })

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
                        db_episode[k_part]['video']['shots'] = list()
                        parse_shotlist(db_episode[k_part]['video']['shots'], value_str)

                    elif k_section in ['precedemment', 'asuivre']:
                        # Precedemment and asuivre are different as some shots
                        # may be replaced
                        # if 'shots' not in db_episode[k_part]['video'].keys():
                        db_episode[k_part]['video']['shots'] = list()
                        parse_shotlist(db_episode[k_part]['video']['shots'], value_str)
                        # if k_ep == 'ep01' and k_part == 'asuivre':
                        #     pprint(db_episode[k_part]['video']['shots'])
                        #     sys.exit()

        # Frames
        #----------------------------------------------------
        if k_section == 'frames':

            for k in config.options(k_section):
                tmp = None
                tmp = re.match("^offsets_(\w+)", k)
                if tmp is not None:
                    k_part = tmp.group(1)
                    if verbose: print("\t\t%s" % (k_part))

                    # Parse list of offsets
                    value_str = config.get(k_section, k)
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

                    db_episode[k_part]['video']['offsets'] = offsets
                    # print("offsets, ep %d, part %s: " % (episode_no, k_part), offsets)
                    # pprint(offsets)
                    # print("TODO: reorder offsets")


                    # Deactivate this to simplify the structure
                    if False:
                        # Now, copy from common and apply offsets
                        db_episode[k_part]['frames'] = deepcopy(cfg_ep_common[k_part]['frames'])
                        for i in range(len(offsets)):
                            offset = offsets[i][1]
                            for frame in db_episode[k_part]['frames']:
                                if frame['ref'] > offsets[i][0]:
                                    frame['no'] = frame['ref'] + offset
                else:
                    # Deactivate this to simplify the structure
                    if False:
                        db_episode[k_part]['frames'] = deepcopy(cfg_ep_common[k_part]['frames'])
                        for frame in db_episode[k_part]['frames']:
                            frame['no'] = frame['ref']


    # Copy frames dict from common if not specified in configuration file
    for k in database[k_ep]['common'].keys():
        # todo: improve this if other sections are listed in common episode file
        if k == 'filters':
            continue

        if k not in db_episode.keys():
            db_episode[k] = {}
            # Deactivate this to simplify the structure
            if False:
                if 'frames' not in cfg_ep[k].keys():
                    cfg_ep[k]['frames'] = deepcopy(cfg_ep_common[k]['frames'])
                    for frame in cfg_ep[k]['frames']:
                        frame['no'] = frame['ref']


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
            db_episode[k_part]['video']['filters'] = 'default'

    # Create a default filter for this episode if not specified
    if 'filters' not in  database[k_ep]['common'].keys():
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




def parse_get_dependencies_for_episodes(db, k_ep) -> dict:
    """Return a dict of edition and episode which are required for
    this episode

    """
    dependencies = dict()

    k_ed_ref = db[k_ep]['common']['video']['reference']['k_ed']
    k_ed = k_ed_ref
    # print("use k_ed_ref=%s" % (k_ed_ref))

    # Common part
    for k_p in K_PARTS:
        if k_p not in db[k_ep]['common']['video'].keys():
            continue

        db_video = db[k_ep]['common']['video'][k_p]
        if 'shots' in db_video.keys():
            shots = db_video['shots']
            for shot in shots:
                # print(shot)
                if 'src' in shot.keys() and 'k_ep' in shot['src'].keys():
                    if 'k_ed' in shot['src']:
                        k_ed_dep = shot['src']['k_ed']
                    else:
                        k_ed_dep = k_ed_ref

                    if k_ed_dep not in dependencies.keys():
                        dependencies[k_ed_dep] = list()
                    dependencies[k_ed_dep].append(shot['src']['k_ep'])

    # Edition used as the reference
    for k_p in K_PARTS:
        if k_p not in db[k_ep][k_ed].keys():
            continue

        db_video = db[k_ep][k_ed][k_p]['video']
        if 'shots' in db_video.keys():
            shots = db_video['shots']
            for shot in shots:
                if 'src' in shot.keys() and 'k_ep' in shot['src'].keys():
                    # print(shot)
                    if 'k_ed' in shot['src']:
                        k_ed_dep = shot['src']['k_ed']
                    else:
                        k_ed_dep = k_ed_ref

                    if k_ed_dep not in dependencies.keys():
                        dependencies[k_ed_dep] = list()
                    dependencies[k_ed_dep].append(shot['src']['k_ep'])

    for k_ed in dependencies.keys():
        dependencies[k_ed] = list(set(dependencies[k_ed]))

    return dependencies