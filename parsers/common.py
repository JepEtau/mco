from __future__ import annotations
from configparser import ConfigParser
import os
import os.path
from pprint import pprint
import sys
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

    config_directories = ConfigParser()
    config_directories.read(filepath)

    # Get directories
    for k_section in config_directories.sections():
        db_common[k_section] = dict()
        for _option in config_directories.options(k_section):
            value = config_directories.get(k_section, _option)
            db_common[k_section][_option] = value

    # Get common configuration file
    filepath = absolute_path(os.path.join(db_path, "common.ini"))
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
        'cache_doc',
        'cache_doc_default',
        'hashes',
        'audio',
        'audio_default',
    ):
        v: str = directories[d]
        for c in ['\"', '\r', '\n']:
            v = v.replace(c, '')
        directories[d] = v

    directories['images'] = os.path.join(directories['inputs'], "img")

    root_path: str = absolute_path(
        os.path.join(__file__, os.pardir, os.pardir)
    )

    # Clean
    for d, v in directories.items():
        for c in ['\"', '\r', '\n']:
            v = v.replace(c, '')
        directories[d] = absolute_path(os.path.join(root_path, v))

    # Use default values
    for d in (
        'cache',
        'cache_progressive',
        'audio',
        'inputs',
        'outputs',
    ):
        if not os.path.exists(directories[d]) or sys.platform == 'linux':
            directories[d] = absolute_path(os.path.join(directories[f"{d}_default"]))
        try:
            del directories[f"{d}_default"]
        except:
            pass

    if sys.platform == 'linux':
        d: str = 'cache_doc'
        if not os.path.exists(directories[d]):
            directories[d] = absolute_path(os.path.join(directories[f"{d}_default"]))
        try:
            del directories[f"{d}_default"]
        except:
            pass

    for k in (
        'audio',
        'cache',
        'cache_doc',
        'cache_progressive',
    ):
        os.makedirs(directories[k], exist_ok=True)


    # Others
    #===========================================================================

    # Discard editions
    try:
        editions_to_discard = list(db_common['editions']['discard'].replace(' ', '').split(','))
    except:
        editions_to_discard = list()
        pass
    nested_dict_set(
        db_common,
        keys=('editions', 'discard'),
        o=editions_to_discard,
    )
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


