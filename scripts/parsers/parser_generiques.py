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

from parsers.parser_audio import parse_audio_section_generique
from parsers.parser_shots import parse_target_shotlist
from parsers.video_target import parse_video_section_g
from utils.common import (
    FPS,
    K_GENERIQUES
)
from utils.nested_dict import nested_dict_set
from utils.pretty_print import *



#===========================================================================
#
#   Parse the common episode file for all editions
#
#===========================================================================
def parse_generiques_target(db, language:str='fr'):
    verbose = False

    for k_part_g in K_GENERIQUES:

        # Open configuration file
        filepath = os.path.join(db['common']['directories']['config'], k_part_g, "%s_target.ini" % (k_part_g))
        if filepath.startswith("~/"):
            filepath = os.path.join(PosixPath(Path.home()), filepath[2:])
        if not os.path.exists(filepath):
            if verbose:
                print("Warning: %s.parse_generiques_target: missing file: %s, continue" % (__name__, filepath))
            continue

        # Initialize structure for this generique
        db[k_part_g] = {
            'video': {
                'shots': list()
            },
            'audio': dict(),
            'cache_path': os.path.join(db['common']['directories']['cache'], k_part_g),
        }

        db_video_target = db[k_part_g]['video']
        db_audio_target = db[k_part_g]['audio']
        db_audio_target['lang'] = language

        # Parse configuration
        config = configparser.ConfigParser()
        config.read(filepath)
        for k_section in config.sections():

            # Audio
            #----------------------------------------------------
            if k_section.startswith('audio'):
                lang = 'fr'
                try:
                    _, lang = k_section.split('.')
                except:
                    print_yellow(f"{filepath}: audio section naming to be reworked, default=fr")

                if lang == db_audio_target['lang']:
                    parse_audio_section_generique(db[k_part_g]['audio'],
                        config, k_section)


            # Video
            #----------------------------------------------------
            elif k_section.startswith('video'):
                lang = 'fr'
                try:
                    _, lang = k_section.split('.')
                except:
                    pass

                if lang == db_audio_target['lang'] or k_section == 'video':
                    parse_video_section_g(db_video_target, config, k_section)


            # Shots
            #----------------------------------------------------
            elif k_section == 'shots':
                nested_dict_set(db_video_target, list(), 'shots')
                parse_target_shotlist(db_video_target['shots'],
                    config, k_section, verbose=False)


        # Source must be defined before consolidating
        try:
            k_ed_src = db[k_part_g]['video']['src']['k_ed']
            k_ep_src = db[k_part_g]['video']['src']['k_ep']
        except:
            pprint(db[k_part_g])
            sys.exit(f"Error: {k_part_g}: k_ed:k_ep must be defined, missing \'source\' option")




#===========================================================================
#
#   Parse generiques configuration file
#
#===========================================================================
def parse_generiques(db, k_ed, verbose=False):

    for k_part_g in K_GENERIQUES:
        # Open db file
        filepath = os.path.join(db['common']['directories']['config'], k_part_g, "%s_%s.ini" % (k_part_g, k_ed))
        if filepath.startswith("~/"):
            filepath = os.path.join(PosixPath(Path.home()), filepath[2:])
        if not os.path.exists(filepath):
            if verbose:
                print("Warning: %s.parse_generiques: missing file: %s, continue" % (__name__, filepath))
            continue


        # Get config from edition
        db_generique = db[k_part_g][k_ed]

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

            # Video
            #----------------------------------------------------
            if k_section == 'video':
                # if k_part_g == 'g_asuivre' and edition=='s':
                if False:
                    print_cyan("---------------- %s, %s:video ----------------" % (k_ed, k_part_g))

                for k_option in config.options(k_section):
                    value_str = config.get(k_section, k_option)
                    value_str = value_str.replace(' ','')
                    # print("%s:%s=" % (k_section, k_option), value_str)

                    # Episode used as reference
                    if k_option == 'episode':
                        sys.exit("parse_generiques: to remove?")
                        k_episode = 'ep%02d' % (int(value_str))
                        db_generique['video']['ep'] = k_episode
                        db_generique['video']['input'] = db['editions'][k_ed]['inputs'][k_episode]


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
        db_generique['dimensions'] = db['editions'][k_ed]['dimensions']




def get_dependencies_for_generique(db, k_part_g='') -> dict:
    """Return a dict of edition and episode which are required for
    this generique"""
    dependencies = dict()

    if k_part_g not in K_GENERIQUES:
        return dependencies

    # Audio
    try:
        db_audio = db[k_part_g]['audio']
        k_ed_src = db_audio['src']['k_ed']
        k_ep_src = db_audio['src']['k_ep']
        if k_ed_src not in dependencies.keys():
            dependencies[k_ed_src] = list()
        dependencies[k_ed_src].append(k_ep_src)
    except:
        pass

    # Video
    db_video = db[k_part_g]['video']

    # Common part contains the source
    if 'k_ep' in db_video['src'].keys():
        k_ed_src = db_video['src']['k_ed']
        k_ep_src = db_video['src']['k_ep']
        if k_ed_src not in dependencies.keys():
            dependencies[k_ed_src] = list()
        dependencies[k_ed_src].append(k_ep_src)

    # Shots
    if 'shots' not in db_video.keys():
        sys.exit("get_dependencies_for_generique: error, list of shots is missing")

    # print("get_dependencies_for_generique: %s" % (k_part_g))
    # pprint(db_video['shots'])
    for s in db_video['shots']:
        if 'k_ed' not in s['src'].keys():
            s['src']['k_ed'] = db_video['src']['k_ed']
        k_ed = s['src']['k_ed']
        if k_ed not in dependencies.keys():
            dependencies[k_ed] = list()
        dependencies[k_ed].append(s['src']['k_ep'])

    for k_ed in dependencies.keys():
        dependencies[k_ed] = list(set(dependencies[k_ed]))

    return dependencies