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
from parsers.parser_video_target import parse_video_target_section

from parsers.parser_filters import (
    parse_filters,
)
from parsers.parser_parts import parse_part_sections
from parsers.parser_shots import (
    consolidate_parsed_shots,
    parse_shotlist,
    parse_shotlist_new,
    parse_target_shotlist,
)
from utils.common import (
    K_ALL_PARTS,
    K_PARTS,
)
from utils.nested_dict import nested_dict_set
from utils.pretty_print import *



#===========================================================================
#
#   Initialize configuration for all episodes
#
#===========================================================================
def db_init_episodes(db, k_ed, ep_min:int=1, ep_max:int=39, force:bool=False):
    # ep_maxCount is the maximum nb of episodes for debug purpose
    db_common = db['common']

    for i in range(ep_min, min(40, ep_max+1)):
        k_ep = f'ep{i:02d}'

        if not force:
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
def parse_episodes_target(db, ep_min=1, ep_max:int=39):
    # ep_maxCount is the maximum nb of episodes: used for debug
    language = db['common']['settings']['language']

    for no in range(ep_min, min(40, ep_max+1)):
        k_ep = f'ep{no:02d}'

        nested_dict_set(db, dict(), k_ep, 'video', 'common')
        db_ep_common = db[k_ep]['video']['common']

        # Define a video target struct
        nested_dict_set(db, dict(), k_ep, 'video', 'target')
        db_video_target = db[k_ep]['video']['target']

        # Audio target: there is no audio src, use the 'audio'
        # struct as the target
        nested_dict_set(db, dict(), k_ep, 'audio')
        db_audio_target = db[k_ep]['audio']
        db_audio_target['lang'] = language


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
            if k_section.startswith('audio'):
                lang = 'fr'
                try:
                    _, lang = k_section.split('.')
                except:
                    print_yellow(f"{filepath}: audio section naming to be reworked, default=fr")
                    pass

                if lang == db_audio_target['lang']:
                    parse_audio_section(db_audio_target, config, k_section)


            # Video
            #----------------------------------------------------
            elif k_section.startswith('video'):
                lang = 'fr'
                try:
                    _, lang = k_section.split('.')
                except:
                    pass

                if lang == db_audio_target['lang'] or k_section == 'video':
                    parse_video_target_section(db_video_target, config, k_section, k_ep)


            # Shots
            #----------------------------------------------------
            elif k_section.startswith('shots'):
                lang = 'fr'
                try:
                    k_section_part, lang = k_section.split('.')
                except:
                    k_section_part = k_section

                try:
                    _, k_part = k_section_part.split('_')
                except:
                    continue

                nested_dict_set(db_video_target, list(), k_part, 'shots')
                if lang == db_audio_target['lang']:
                    parse_target_shotlist(db_video_target[k_part]['shots'],
                        config, k_section, lang)


#===========================================================================
#
#   Parse a single episode configuration file
#
#===========================================================================
def parse_episode(db, k_ed, k_ep):
    verbose = False

    if verbose:
        print_lightgreen("parse_episode: %s:%s" % (k_ed, k_ep))

    # Open configuration file
    filepath = os.path.join(db['common']['directories']['config'], k_ep, "%s_%s.ini" % (k_ep, k_ed))
    if filepath.startswith("~/"):
        filepath = os.path.join(PosixPath(Path.home()), filepath[2:])

    # If the input video file has not been found, do not parse the config file
    if k_ed not in db[k_ep]['video'].keys():
        if verbose:
            print_orange("\twarning: %s:%s: missing file %s, ignoring" % (k_ed, k_ep, filepath))
        return

    # Video db for this edition
    db_video = db[k_ep]['video'][k_ed]


    # Create default dict for inputs
    input_filepath =  ''
    try:
        input_filepath = db['editions'][k_ed]['inputs']['video'][k_ep]
    except:
        pass
    for k_part in K_ALL_PARTS:
        nested_dict_set(db_video, {
            'interlaced': {
                'filepath': input_filepath,
            },
            'progressive': {
                'enable': False,
                'start': 0,
                'count': -1,
            }
        }, k_part, 'inputs')


    # Parse configuration
    config = configparser.ConfigParser()
    config.read(filepath)
    for k_section in config.sections():
        if verbose:
            print_lightgrey("\tsection: %s" % (k_section))

        # De-interlace
        #----------------------------------------------------
        if k_section == 'deinterlace':
            for k_option in config.options(k_section):
                value_str = config.get(k_section, k_option)
                value_str = value_str.replace(' ','')
                if verbose:
                    print("\t\t%s=%s" % (k_option, value_str))

                if k_option == 'ffv1' and value_str in ['yes', 'true']:
                    # Use ffv1 generated by avisynth (progressive video)
                    for k_part in K_ALL_PARTS:
                        db_video[k_part]['inputs']['progressive']['enable'] = True
                elif k_option == 'range':
                    (start, end) = list(map(lambda x: int(x), value_str.split(':')))
                    for k_part in K_ALL_PARTS:
                        db_video[k_part]['inputs']['progressive']['start'] = start
                        db_video[k_part]['inputs']['progressive']['count'] = end - start if end != -1 else end

        # Filters
        #----------------------------------------------------
        elif k_section.startswith("filters"):
            parse_filters(db_video, config, k_section)

        # Parts: frame start and (end+1)
        #----------------------------------------------------
        elif k_section == 'parts':
            parse_part_sections(db_video, config, verbose=False)

        # Parts: shots and other properties (previous format)
        #----------------------------------------------------
        elif k_section in K_ALL_PARTS:
            k_part = k_section
            for k_option in config.options(k_section):
                value_str = config.get(k_section, k_option)
                value_str = value_str.replace(' ','')

                # Shots
                db_video_part = db_video[k_part]
                db_video_part['shots'] = list()
                if k_option == 'shots':
                    if k_section in ['episode',
                                    'documentaire',
                                    'g_debut',
                                    'g_fin',
                                    'g_asuivre',
                                    'g_documentaire']:
                        parse_shotlist(db_video_part['shots'],
                            k_ep, k_part, value_str)

                    elif k_section in ['precedemment', 'asuivre']:
                        # Precedemment and asuivre are different as some shots
                        # may be replaced
                        # TODO rework as the function/parameteres are the same!
                        parse_shotlist(db_video_part['shots'],
                            k_ep, k_part, value_str)


        # Parts: shots (new format)
        #----------------------------------------------------
        elif k_section.startswith('shots_'):
            k_part = k_section[len('shots_'):]
            if k_part not in K_ALL_PARTS:
                continue
            nested_dict_set(db_video, list(), k_part, 'shots')
            parse_shotlist_new(db_video[k_part]['shots'],
                config, k_section, verbose=False)


    # Set dimensions
    #  TODO is this really needed?
    nested_dict_set(db[k_ep]['video'], db['editions'][k_ed]['dimensions'], 'dimensions')


    # Calculate durations for each parts based on shots duration
    for k_p in K_ALL_PARTS:
        consolidate_parsed_shots(db=db, k_ed=k_ed, k_ep=k_ep, k_part=k_p)

    # Consolidate inputs dict
    for k_part in K_ALL_PARTS:
        try:
            if db_video[k_part]['count'] == -1:
                continue
        except:
            continue

        # Skip if progressive shall not be used
        input_progressive = db_video[k_part]['inputs']['progressive']
        if not input_progressive['enable']:
            continue

        # Force disable if this part is not in progressive file
        part_end = db_video[k_part]['start'] + db_video[k_part]['count']
        progressive_end = input_progressive['start'] + input_progressive['count']
        if db_video[k_part]['start'] < input_progressive['start']:
            input_progressive['enable'] = False
        elif (input_progressive['count'] != -1 and progressive_end < part_end):
            input_progressive['enable'] = False

    if verbose:
        if k_ed == 'f' and k_ep == 'ep01':
            pprint(db_video)
            sys.exit()


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

        try:
            db_video = db[k_ep]['video'][k_ed_src][k_part]
        except:
            sys.exit(red(f"error: {k_ed_src}:{k_ep}: it seems that the input file is missing"))
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

        k_ed_dep = db[k_ep]['audio']['src']['k_ed']
        try:
            db_audio = db[k_ep]['audio'][k_part]
        except:
            sys.exit(red(f"error: {k_ed_src}:{k_ep}: it seems that the input file is missing"))

        for segment in db_audio['segments']:
            if 'k_ep' in segment.keys() and segment['k_ep'] != k_ep:
                if k_ed_dep not in dependencies.keys():
                    dependencies[k_ed_dep] = list()
                dependencies[k_ed_dep].append(segment['k_ep'])

    for k_ed in dependencies.keys():
        dependencies[k_ed] = list(set(dependencies[k_ed]))

    return dependencies
