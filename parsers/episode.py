
from collections import OrderedDict
from configparser import ConfigParser
import os
import os.path
from pathlib import (
    Path,
    PosixPath,
)
import sys
from pprint import pprint
from typing import Literal

from utils.mco_types import ChapterVideo

from .logger import logger

from .audio import parse_audio_section
from .video_target import parse_video_target

from .filters import (
    parse_filters,
)
from .chapter import parse_chapter_sections
from .scene import (
    consolidate_parsed_scenes,
    parse_scenes,
    parse_scenes_new,
    parse_target_scenelist,
)
from ._keys import (
    all_chapter_keys,
    main_chapter_keys,
    non_credit_chapter_keys,
    key
)
from .helpers import nested_dict_set
from utils.p_print import *
from utils.path_utils import absolute_path
from ._db import db


#===========================================================================
#
#   Initialize configuration for all episodes
#
#===========================================================================
def db_init_episodes(k_ed, ep_min: int = 1, ep_max: int = 39, force: bool = True):
    inputs: dict = db['editions'][k_ed]['inputs']

    for i in range(ep_min, min(40, ep_max+1)):
        k_ep = key(i)

        if not force:
            # Do not create section if input file does not exist
            if k_ep not in inputs['video'] and k_ep not in inputs['audio']:
                # print("warning: input file for episode no. %d does not exist" % (i))
                continue

        # Create structure for this episode/edition

        # default sections:
        for k_chapter in all_chapter_keys():
            nested_dict_set(
                db,
                {
                    'replace': {},
                },
                k_ep, 'video', k_ed, k_chapter
            )

        # Set the video input file
        # nested_dict_set(db,
        #     db['editions'][k_ed]['inputs']['video'][k_ep],
        #     k_ep, 'video', k_ed, 'input')

        # Add path cache
        db[k_ep]['cache_path'] = os.path.normpath(
            os.path.join(db['common']['directories']['cache'], k_ep)
        )



#===========================================================================
#
#   Parse the common episode file for all editions
#
#===========================================================================
def parse_episodes_target(ep_min: int = 1, ep_max: int = 39):
    # ep_maxCount is the maximum nb of episodes: used for debug
    language = db['common']['settings']['language']

    for no in range(ep_min, min(40, ep_max+1)):
        k_ep = key(no)

        nested_dict_set(db, {}, k_ep, 'video', 'common')
        db_ep_common = db[k_ep]['video']['common']

        # Define a video target struct
        nested_dict_set(db, {}, k_ep, 'video', 'target')
        db_video_target = db[k_ep]['video']['target']

        # Audio target: there is no audio src, use the 'audio'
        # struct as the target
        nested_dict_set(db, {}, k_ep, 'audio')
        db_audio_target = db[k_ep]['audio']
        db_audio_target['lang'] = language


        # Open configuration file
        filepath: str = absolute_path(
            os.path.join(
                db['common']['directories']['config'],
                k_ep,
                f"{k_ep}_target.ini"
            )
        )
        if not os.path.exists(filepath):
            continue

        # Parse configuration
        # print("parse_episodes_target: filepath=%s" % (filepath))
        config = ConfigParser()
        config.read(filepath)
        for k_section in config.sections():

            # Audio
            #----------------------------------------------------
            if k_section.startswith('audio'):
                lang = 'fr'
                try:
                    _, lang = k_section.split('.')
                except:
                    print(yellow(f"{filepath}: audio section naming to be reworked, default=fr"))
                    pass

                if lang == db_audio_target['lang']:
                    parse_audio_section(db, k_ep, config, k_section)


            # Video
            #----------------------------------------------------
            elif k_section.startswith('video'):
                lang = 'fr'
                try:
                    _, lang = k_section.split('.')
                except:
                    pass

                if lang == db_audio_target['lang'] or k_section == 'video':
                    parse_video_target(
                        db,
                        episode=k_ep,
                        config=config,
                        k_section=k_section,
                    )


            # scenes
            #----------------------------------------------------
            elif k_section.startswith('scenes'):
                lang = 'fr'
                try:
                    k_section_chapter, lang = k_section.split('.')
                except:
                    k_section_chapter = k_section

                try:
                    _, k_chapter = k_section_chapter.split('_')
                except:
                    continue

                ch_video = db_video_target[k_chapter]
                ch_video.update({
                    'k_ep': k_ep,
                    'k_ch': k_chapter,
                    'scenes': []
                })

                if lang == db_audio_target['lang']:
                    parse_target_scenelist(
                        ch_video,
                        config,
                        k_section,
                        lang
                    )


#===========================================================================
#
#   Parse a single episode configuration file
#
#===========================================================================
def parse_episode(k_ed: str, k_ep: str | int):
    verbose = False
    k_ep: str = key(k_ep)

    logger.debug(lightgreen(f"parse_episode: {k_ed}:{k_ep}"))

    # Open configuration file
    filepath = absolute_path(os.path.join(
        db['common']['directories']['config'],
        k_ep,
        f"{k_ep}_{k_ed}.ini"
    ))

    # If the input video file has not been found, do not parse the config file
    if k_ed not in db[k_ep]['video']:
        logger.debug(orange(f"\twarning: {k_ed}:{k_ep}: ignore missing file: {filepath}"))
        return

    # Video db for this edition
    db_video = db[k_ep]['video'][k_ed]


    # Create default dict for inputs
    input_filepath =  ''
    try:
        input_filepath = db['editions'][k_ed]['inputs']['video'][k_ep]
    except:
        pass
    for k_chapter in all_chapter_keys():
        nested_dict_set(db_video, {
            'interlaced': {
                'filepath': input_filepath,
            },
            'progressive': {
                'enable': False,
                'start': 0,
                'count': -1,
            }
        }, k_chapter, 'inputs')


    # Parse configuration
    config = ConfigParser()
    config.read(filepath)
    for k_section in config.sections():
        logger.debug(lightgrey("\tsection: %s" % (k_section)))

        # De-interlace
        #----------------------------------------------------
        if k_section == 'deinterlace':
            for k_option in config.options(k_section):
                value_str = config.get(k_section, k_option)
                value_str = value_str.replace(' ','')
                logger.debug("\t\t%s=%s" % (k_option, value_str))

                if k_option == 'ffv1' and value_str in ['yes', 'true']:
                    # Use ffv1 generated by avisynth (progressive video)
                    for k_chapter in all_chapter_keys():
                        db_video[k_chapter]['inputs']['progressive']['enable'] = True
                elif k_option == 'range':
                    (start, end) = list(map(lambda x: int(x), value_str.split(':')))
                    for k_chapter in all_chapter_keys():
                        db_video[k_chapter]['inputs']['progressive']['start'] = start
                        db_video[k_chapter]['inputs']['progressive']['count'] = end - start if end != -1 else end

        # Filters
        #----------------------------------------------------
        elif k_section.startswith("filters"):
            parse_filters(db_video, config, k_section)

        # chapters: frame start and (end+1)
        #----------------------------------------------------
        elif k_section == 'chapters':
            parse_chapter_sections(
                db,
                episode=k_ep,
                edition=k_ed,
                config=config,
            )

        # chapters: scenes and other properties (previous format)
        #----------------------------------------------------
        elif k_section in all_chapter_keys():
            k_chapter = k_section
            for k_option in config.options(k_section):
                value_str = config.get(k_section, k_option)
                value_str = value_str.replace(' ','')

                # scenes
                db_video_chapter = db_video[k_chapter]
                db_video_chapter['scenes'] = []
                if k_option == 'scenes':
                    if k_section in ['episode',
                                    'documentaire',
                                    'g_debut',
                                    'g_fin',
                                    'g_asuivre',
                                    'g_documentaire']:
                        parse_scenes(db_video_chapter['scenes'], value_str)

                    elif k_section in ['precedemment', 'asuivre']:
                        # precedemment and asuivre are different as some scenes
                        # may be replaced
                        # TODO rework as the function/parameteres are the same!
                        parse_scenes(db_video_chapter['scenes'], value_str)


        # chapters: scenes (new format)
        #----------------------------------------------------
        elif k_section.startswith('scenes_'):
            k_chapter = k_section[len('scenes_'):]
            if k_chapter not in all_chapter_keys():
                continue
            db_video[k_chapter]['scenes'] = []
            parse_scenes_new(db_video[k_chapter]['scenes'], config, k_section)


    # Set dimensions
    #  TODO is this really needed?
    nested_dict_set(db[k_ep]['video'], db['editions'][k_ed]['dimensions'], 'dimensions')


    # Calculate durations for each chapters based on scenes duration
    for k_p in all_chapter_keys():
        consolidate_parsed_scenes(k_ed=k_ed, k_ep=k_ep, k_chapter=k_p)

    # Consolidate inputs dict
    for k_chapter in all_chapter_keys():
        try:
            if db_video[k_chapter]['count'] == -1:
                continue
        except:
            continue

        chapter_video: dict = db_video[k_chapter]

        # Skip if progressive shall not be used
        input_progressive = db_video[k_chapter]['inputs']['progressive']
        if not input_progressive['enable']:
            continue

        # Force disable if this chapter is not in progressive file
        chapter_end = chapter_video['start'] + chapter_video['count']
        progressive_end = input_progressive['start'] + input_progressive['count']
        if chapter_video['start'] < input_progressive['start']:
            input_progressive['enable'] = False
        elif (input_progressive['count'] != -1 and progressive_end < chapter_end):
            input_progressive['enable'] = False

    if verbose:
        if k_ed == 'f' and k_ep == 'ep01':
            pprint(db_video)
            sys.exit()



def get_episode_dependencies(
    episode: int | str,
    track: Literal['audio', 'video', 'all'] = 'all'
) -> OrderedDict[str, list]:
    """Return a dict of edition and episode which are required for
    this episode

    """
    k_ep: str = key(episode)
    dependencies: OrderedDict[str, set] = OrderedDict()
    target_video: dict = db[k_ep]['video']['target']

    # Common chapter
    for chapter in main_chapter_keys():
        if chapter not in target_video:
            continue

        chapter_video: ChapterVideo = target_video[chapter]
        if 'scenes' in chapter_video:
            for scene in chapter_video['scenes']:
                for k_ed, k_eps in scene['src'].get_dependencies().items():
                    if k_ed not in dependencies:
                        dependencies[k_ed] = set()
                    for k_ep in k_eps:
                        dependencies[k_ed].add(k_ep)

    # Edition used as the default source
    for chapter in non_credit_chapter_keys():
        k_ed_src = target_video[chapter]['k_ed_src']

        if track in ('video', 'all'):
            try:
                chapter_video = db[k_ep]['video'][k_ed_src][chapter]
            except:
                sys.exit(red(f"error: {k_ed_src}:{k_ep}:{chapter}: missing input file"))
            if 'scenes' in chapter_video.keys():
                scenes = chapter_video['scenes']
                for scene in scenes:
                    if 'src' in scene.keys() and 'k_ep' in scene['src']:
                        k_ed_dep = (
                            scene['src']['k_ed']
                            if 'k_ed' in scene['src']
                            else k_ed_src
                        )
                        if k_ed_dep not in dependencies:
                            dependencies[k_ed_dep] = set()
                        dependencies[k_ed_dep].add(scene['src']['k_ep'])

        if track in ('audio', 'all'):
            k_ed_dep = db[k_ep]['audio']['src']['k_ed']
            try:
                db_audio = db[k_ep]['audio'][chapter]
            except:
                sys.exit(red(f"error: {k_ed_src}:{k_ep}:{chapter}: missing input file"))

            for segment in db_audio['segments']:
                if 'k_ep' in segment and segment['k_ep'] != k_ep:
                    if k_ed_dep not in dependencies.keys():
                        dependencies[k_ed_dep] = []
                    dependencies[k_ed_dep].add(segment['k_ep'])

    for k_ed in dependencies.keys():
        dependencies[k_ed] = list(dependencies[k_ed])

    return dependencies

