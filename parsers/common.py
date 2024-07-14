
from configparser import ConfigParser
import os
import os.path
from pathlib import (
    Path,
    PosixPath,
)
from pprint import pprint
import sys

from ._types import TASK_NAMES, VideoSettings
from .helpers import (
    nested_dict_set,
)
from utils.p_print import *
from utils.path_utils import absolute_path
from ._db import (
    db,
    database_path,
)



def parse_common_configuration(language:str=''):
    verbose = False

    if verbose:
        print(lightcyan("Parse common configuration, file: "), end='')

    db['common'] = dict()
    db_common: dict[str, str | list[str]] = db['common']
    db_path = absolute_path(database_path)

    # Get configuration file's directories
    filepath = os.path.join(db_path, "directories.ini")
    if verbose:
        print(f"{filepath}")
    if not os.path.exists(filepath):
        sys.exit(f"Error: missing file: {filepath}")
    try:
        config_directories = ConfigParser()
        config_directories.read(filepath)

        for k_section in config_directories.sections():
            db_common[k_section] = dict()
            for _option in config_directories.options(k_section):
                value = config_directories.get(k_section, _option)
                db_common[k_section][_option] = value
    except:
        print("[E] parse_common_configuration: fichier de configuration non trouvé ou erroné: %s \n\n" % (filepath))
        sys.exit("Unexpected error:", sys.exc_info()[0])


    # Get common configuration file
    filepath = os.path.join(db_path, "common.ini")
    if filepath.startswith("~/"):
        filepath = os.path.join(PosixPath(Path.home()), filepath[2:])
    if not os.path.exists(filepath):
        sys.exit("[E] fichier de configuration manquant: %s" % (filepath))
    try:
        config_general = ConfigParser()
        config_general.read(filepath)

        for k_section in config_general.sections():
            if k_section.startswith('video_format'):
                continue

            db_common[k_section] = {}
            for _option in config_general.options(k_section):
                value = config_general.get(k_section, _option)
                db_common[k_section][_option] = value
    except:
        print("[E] parse_common_configuration: fichier de configuration non trouvé ou erroné: %s \n\n" % (filepath))
        sys.exit("Unexpected error:", sys.exc_info()[0])


    # Clean settings
    for k, v in db_common['settings'].items():
        for c in ['\"', '\'','\r', '\n']:
            v = v.replace(c, '')
        db_common['settings'][k] = v

    db_common['settings']['verbose'] = db_common['settings']['verbose'].split(' ')

    # Directories
    directories: dict[str, str] = db_common['directories']
    directories['config'] = database_path
    for d in (
        'config',
        'inputs',
        'outputs',
        'cache',
        'cache_progressive',
        'cache_progressive_default',
        'cache_default',
        'hashes',
        'audio',
        'audio_default',
    ):
        v: str = directories[d]
        for c in ['\"', '\r', '\n']:
            v = v.replace(c, '')
        directories[d] = absolute_path(v)


    # Clean
    for d, v in directories.items():
        for c in ['\"', '\r', '\n']:
            v = v.replace(c, '')
        directories[d] = absolute_path(v)

    # Use default values
    for d in ('cache', 'cache_progressive', 'audio'):
        if not os.path.exists(directories[d]):
            directories[d] = absolute_path(directories[f"{d}_default"])
        try:
            del directories[f"{d}_default"]
        except:
            pass


    # Others
    #===========================================================================

    # Discard editions
    try:
        editions_to_discard = list(db_common['editions']['discard'].replace(' ', '').split(','))
    except:
        editions_to_discard = list()
        pass
    nested_dict_set(db_common, editions_to_discard, 'editions', 'discard')

    if verbose:
        pprint(db)
        sys.exit()


    # Language
    #===========================================================================
    # lower priority: common.ini
    if 'language' not in db_common['settings'].keys():
        db_common['settings']['language'] = 'fr'

    # middle priority: 'en' file stored in database folder
    if os.path.exists(os.path.normpath(os.path.abspath(os.path.join(database_path, 'en')))):
        db_common['settings']['language'] = 'en'

    # highest priority: argument
    if language != '':
        db_common['settings']['language'] = language


    # Video formats
    db_common['video_format'] = {}
    for task in TASK_NAMES:
        section: str = f"video_format_{task}"
        if section not in config_general.sections():
            continue

        vformat = config_general[section]
        options: str = vformat['codec_options'].replace('\"', '')
        db_common['video_format'][task] = VideoSettings(
            codec=vformat['codec'],
            codec_options=options.split(' ') if options else [],
            pix_fmt=vformat['pix_fmt'],
            frame_rate=db_common['settings']['fps'],
        )
