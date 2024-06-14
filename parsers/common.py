
from configparser import ConfigParser
import os
import os.path
from pathlib import (
    Path,
    PosixPath,
)
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
    db_common = db['common']
    db_path = absolute_path(database_path)
    external_dir = absolute_path(os.path.join(__file__, os.pardir, os.pardir, "external"))

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
    db_common['directories']['config'] = database_path
    for d in (
        'config',
        'inputs',
        'outputs',
        'cache',
        'cache_progressive',
        'cache_progressive_default',
        'cache_default',
        'frames',
        'frames_default',
        'hashes',
        'audio',
        'audio_default',
    ):
        v: str = db_common['directories'][d]
        for c in ['\"', '\r', '\n']:
            v = v.replace(c, '')
        db_common['directories'][d] = absolute_path(v)


    # Clean
    for d, v in db_common['directories'].items():
        for c in ['\"', '\r', '\n']:
            v = v.replace(c, '')
        db_common['directories'][d] = absolute_path(v)

    # Use default values
    for d in ['cache', 'cache_progressive', 'frames', 'audio']:
        if not os.path.exists(db_common['directories'][d]):
            db_common['directories'][d] = absolute_path(
                db_common['directories'][f"{d}_default"]
            )
        try:
            del db_common['directories'][f"{d}_default"]
        except:
            pass


    # Executables
    #=============================================================================
    if sys.platform == "win32":
        db_common['tools'] = {
            'ffmpeg': "ffmpeg.exe",
            'mkvmerge': "mkvmerge.exe",
            'ffprobe': "ffprobe.exe"
        }

        for tool in ['ffmpeg', 'ffprobe']:
            try:
                v = db_common['directories'][d]
                for c in ['\"', '\r', '\n']:
                    v = v.replace(c, '')
            except:
                pass


        tool = 'mkvmerge'
        if sys.platform == "win32":
            db_common['tools']['mkvmerge'] = absolute_path(
                os.path.join(db_common['directories'][f"{tool}_win"], tool)
            )
        else:
            db_common['tools']['mkvmerge'] = tool


    else:
        # Linux
        db_common['tools'] = {
            'ffmpeg': "ffmpeg",
            'mkvmerge': "mkvmerge",
            'ffprobe': "ffprobe"
        }

        for d in ['ffmpeg', 'ffmpeg_win',
                    'mkvmerge', 'mkvmerge_win']:
            try:
                del db_common['directories'][d]
            except:
                pass



    # Subprocess settings
    #===========================================================================
    # db_common['process'] = get_process_cfg()


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


