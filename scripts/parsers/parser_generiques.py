# -*- coding: utf-8 -*-
import sys

import configparser
import os
import os.path
from pathlib import (
    Path,
    PosixPath,
)
import re

from pprint import pprint

from parsers.parser_av import parse_audio_generique
from parsers.parser_filters import (
    parse_filters_initialize,
    parser_filters_consolidate,
)
from parsers.parser_frames import parse_framelist
from parsers.parser_shots import parse_shotlist
from utils.common import K_GENERIQUES



#===========================================================================
#
#   Initialize configuration for all 'generiques'
#
#===========================================================================
def db_init_generiques(database, k_ed, verbose=False):
    db_common = database['common']

    for k_part_g in K_GENERIQUES:
        # Create structure for this generique
        # set the default episode no. to 1, it will be modified once
        # database files are parsed
        if k_part_g not in database.keys():
            database[k_part_g] = dict()

        database[k_part_g][k_ed] = {
            'k_ep': 'ep01',
            'video': {
                'shots': list(),
                'geometry': None
            },
            'audio': dict(),
            'filters': {'default': parse_filters_initialize(type='default')}
        }
        db_generique = database[k_part_g][k_ed]

        # Default input file
        k_ep_ref = db_generique['k_ep']
        if k_ep_ref not in database['editions'][k_ed]['inputs'].keys():
            sys.exit("Erreur: fichier manquant pour le générique %s: édition '%s', épisode %d" % (k_part_g, k_ed, int(k_ep_ref[-2:])))

        db_generique['path'] = {
            'input_audio': database['editions'][k_ed]['inputs'][k_ep_ref],
            'input_video': database['editions'][k_ed]['inputs'][k_ep_ref],

            # Cache
            'cache': os.path.join(db_common['directories']['cache'], "%s" % (k_part_g)),

            # Frames for study
            'frames': db_common['directories']['frames'],
        }



#===========================================================================
#
#   Parse the common episode file for all editions
#
#===========================================================================
def parse_generiques_common(database, verbose=False):

    for k_part_g in K_GENERIQUES:
        if k_part_g not in database.keys(): database[k_part_g] = dict()
        if 'common' not in database[k_part_g].keys():
            database[k_part_g]['common'] = {
                'video': {
                    'shots': list(),
                    'reference': {
                        'k_ed': None,
                        'k_ep': None
                    }
                },
                'audio': {
                    'reference': {
                        'k_ed': None,
                        'k_ep': None
                    },
                },
                'filters': {
                    'default': parse_filters_initialize(type='default')
                },
            }
        db_g_common = database[k_part_g]['common']

        # Open configuration file
        filepath = os.path.join(database['common']['directories']['config'], k_part_g, "%s_common.ini" % (k_part_g))
        if filepath.startswith("~/"):
            filepath = os.path.join(PosixPath(Path.home()), filepath[2:])
        if not os.path.exists(filepath):
            if verbose:
                print("Warning: %s.parse_generiques_common: missing file: %s, continue" % (__name__, filepath))
            continue

        # Cache
        db_g_common['path'] = {
            'cache': os.path.join(database['common']['directories']['cache'], k_part_g)
        }

        # Parse configuration
        config = configparser.ConfigParser()
        config.read(filepath)
        for k_section in config.sections():
            # Parse only supported sections:

            # Frames (used for studies)
            #----------------------------------------------------
            if k_section == 'frames':
                for k_option in config.options(k_section):
                    value_str = config.get(k_section, k_option)
                    value_str = value_str.replace(' ','')
                    # print("%s:%s=" % (k_section, k_option), value_str)

                    # Frames
                    if k_option == 'frames':
                        if 'frames' not in db_g_common.keys():
                            db_g_common['frames'] = list()
                        parse_framelist(db_g_common['frames'], value_str)

            # Video
            #----------------------------------------------------
            elif k_section == 'video':
                for k_option in config.options(k_section):
                    value_str = config.get(k_section, k_option)
                    value_str = value_str.replace(' ','')
                    # print("%s:%s=" % (k_section, k_option), value_str)

                    if k_option == 'reference_edition':
                        db_g_common['video']['reference']['k_ed'] = value_str

                    elif k_option == 'reference_episode':
                        db_g_common['video']['reference']['k_ep'] ='ep%02d' % (int(value_str))

                    elif k_option == 'shots':
                        parse_shotlist(db_g_common['video']['shots'], '', k_part_g, value_str)
                        for shot in db_g_common['video']['shots']:
                            # Force src as this is the common config file which
                            # specify the k_ed:k_ep to use
                            if 'src' in shot.keys():
                                shot['src']['use'] = True
                                shot['src']['count'] = shot['count']


            # Audio
            #----------------------------------------------------
            elif k_section == 'audio':
                parse_audio_generique(db_g_common['audio'], config)

            # Filters
            #----------------------------------------------------
            elif k_section.startswith("filters"):
                print("warning: parse_generiques_common: (%s) parse_and_update_filters_generique is deprecated, ignored" % (k_part_g))
                # parse_and_update_filters_generique(db_g_common, config, k_section)

        # Consolidate
        #----------------------------------------------------
        if 'frames' in db_g_common.keys():
            db_frames = db_g_common['frames']
            db_shots = db_g_common['video']['shots']

            for f in db_frames:
                # Use the reference episode if not specified in frame
                if f['k_ep'] == '':
                    f['k_ep'] = db_g_common['video']['reference']['k_ep']

                # find shot from frame no.
                for s in db_shots:
                    if s['start'] < f['ref'] < (s['start'] + s['count']):
                        # shot has been found
                        if s['filters'] != 'default' and 'filters' not in f.keys():
                            f['filters'] = s['filters']
                        elif f['filters'] != s['filters']:
                            print("warning: frame filter (%s) is different from shot filter (%s), overwrite it" %
                                (f['filters'], s['filters']))
                            # f['filters'] = s['filters']
                        break

#===========================================================================
#
#   Parse generiques configuration file
#
#===========================================================================
def parse_generiques(database, k_ed, verbose=False):

    for k_part_g in K_GENERIQUES:

        # k_ed = database[k_part_g]['common']['video']['reference']['k_ed']

        # Open database file
        filepath = os.path.join(database['common']['directories']['config'], k_part_g, "%s_%s.ini" % (k_part_g, k_ed))
        if filepath.startswith("~/"):
            filepath = os.path.join(PosixPath(Path.home()), filepath[2:])
        if not os.path.exists(filepath):
            if verbose:
                print("Warning: %s.parse_generiques: missing file: %s, continue" % (__name__, filepath))
            continue


        # Get config from edition
        db_generique = database[k_part_g][k_ed]

        config = configparser.ConfigParser()
        config.read(filepath)
        for k_section in config.sections():
            tmp = re.search(re.compile("([a-z]+)[_]*([a-z0-9]*)"), k_section)
            if tmp is None:
                print("erreur: [%s] n'est pas reconnu" % (k_section))
                sys.exit()
            else:
                k_mainSection = tmp.group(1)
                if len(tmp.groups()) > 1:
                    k_subSection = tmp.group(2)


            # Filters
            #----------------------------------------------------
            if k_section.startswith("filters"):
                print("warning: parse_generiques: (%s:%s) parse_and_update_filters_generique is deprecated, ignored" % (k_ed, k_part_g))
                # parse_and_update_filters_generique(db_generique, config, k_section, verbose=verbose)


            # Video
            #----------------------------------------------------
            elif k_section == 'video':
                # if k_part_g == 'g_asuivre' and edition=='s':
                if verbose:
                    print("---------------- %s, %s:video ----------------" % (k_ed, k_part_g))

                for k_option in config.options(k_section):
                    value_str = config.get(k_section, k_option)
                    value_str = value_str.replace(' ','')
                    # print("%s:%s=" % (k_section, k_option), value_str)

                    # Episode used as reference
                    if k_option == 'episode':
                        k_episode = 'ep%02d' % (int(value_str))
                        db_generique['video']['ep'] = k_episode
                        db_generique['path']['input_video'] = database['editions'][k_ed]['inputs'][k_episode]


            # Audio
            #----------------------------------------------------
            elif k_section == 'audio':
                if verbose:
                    print("---------------- %s, %s:audio ----------------" % (k_ed, k_part_g))

                for k_option in config.options(k_section):
                    value_str = config.get(k_section, k_option)
                    value_str = value_str.replace(' ','')

                    if k_option == k_part_g:
                        # calculate start and duration (in nb of frames)
                        properties = value_str.split(':')
                        db_generique['audio'].update({
                            'start': int(properties[0]),
                            'end': int(properties[1]),
                            'count': int(properties[1]) - int(properties[0])
                        })


        # Set dimensions:
        db_generique['dimensions'] = database['editions'][k_ed]['dimensions']

        # Consolidate filters
        # print("#### before consolidation: database[common][filters]")
        # pprint(database['common']['filters'])
        # print("#### before consolidation: database[g_asuivre][common][filters]")
        # pprint(database['g_asuivre']['common']['filters'])
        # print("#### before consolidation: database[g_asuivre][edition][filters]")
        # pprint(database[k_part_g]['common']['filters'])
        # print("###########################")

        # Consolidate
        #----------------------------------------------------

        parser_filters_consolidate(
            database['common']['filters'],
            database['editions'][k_ed]['filters'],
            database[k_part_g]['common']['filters'],
            database[k_part_g][k_ed]['filters'],
            label="[%s:%s]" % (k_ed, k_part_g),
            verbose=False)




def parse_get_dependencies_for_generique(db, k_part_g='') -> dict:
    """Return a dict of edition and episode which are required for
    this generique"""
    dependencies = dict()

    if k_part_g not in K_GENERIQUES:
        return dependencies

    db_video = db[k_part_g]['common']['video']

    # Common part
    if 'k_ep' in db_video['reference'].keys():
        k_ed_ref = db_video['reference']['k_ed']
        k_ep_ref = db_video['reference']['k_ep']
        if k_ed_ref not in dependencies.keys():
            dependencies[k_ed_ref] = list()
        dependencies[k_ed_ref].append(k_ep_ref)

    # Shots
    if 'shots' not in db_video.keys():
        sys.exit("parse_get_dependencies_for_generique: error, list of shots is missing")

    # print("parse_get_dependencies_for_generique: %s" % (k_part_g))
    # pprint(db_video['shots'])
    for s in db_video['shots']:
        if 'k_ed' not in s['src'].keys():
            s['src']['k_ed'] = db_video['reference']['k_ed']
        k_ed = s['src']['k_ed']
        if k_ed not in dependencies.keys():
            dependencies[k_ed] = list()
        dependencies[k_ed].append(s['src']['k_ep'])

    for k_ed in dependencies.keys():
        dependencies[k_ed] = list(set(dependencies[k_ed]))

    return dependencies