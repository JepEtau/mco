# -*- coding: utf-8 -*-
import sys
import configparser
import os
import os.path
from pathlib import (
    Path,
    PosixPath,
)
from pprint import pprint
import platform
from utils.nested_dict import nested_dict_set
from utils.pretty_print import *
from utils.process import get_process_cfg


def parse_common_configuration(db, config_path):
    verbose = False

    if verbose:
        print_lightcyan("Parse common configuration, file: ", end='')

    db['common'] = dict()
    db_common = db['common']

    # Get directories configuration file
    #=============================================================================
    filepath = os.path.normpath(os.path.abspath(os.path.join(config_path, "directories.ini")))
    if verbose:
        print(f"{filepath}")

    if filepath.startswith("~/"):
        filepath = os.path.join(PosixPath(Path.home()), filepath[2:])
    if not os.path.exists(filepath):
        sys.exit("Erreur: fichier de configuration manquant: %s" % (filepath))
    try:
        config_directories = configparser.ConfigParser()
        config_directories.read(filepath)

        for k_section in config_directories.sections():
            db_common[k_section] = dict()
            for _option in config_directories.options(k_section):
                value = config_directories.get(k_section, _option)
                db_common[k_section][_option] = value
    except:
        print("Erreur: parse_common_configuration: fichier de configuration non trouvé ou erroné: %s \n\n" % (filepath))
        sys.exit("Unexpected error:", sys.exc_info()[0])


    # Get common configuration file
    #=============================================================================
    filepath = os.path.join(config_path, "common.ini")
    if filepath.startswith("~/"):
        filepath = os.path.join(PosixPath(Path.home()), filepath[2:])
    if not os.path.exists(filepath):
        sys.exit("Erreur: fichier de configuration manquant: %s" % (filepath))
    try:
        config_general = configparser.ConfigParser()
        config_general.read(filepath)

        for k_section in config_general.sections():
            db_common[k_section] = {}
            for _option in config_general.options(k_section):
                value = config_general.get(k_section, _option)
                db_common[k_section][_option] = value
    except:
        print("Erreur: parse_common_configuration: fichier de configuration non trouvé ou erroné: %s \n\n" % (filepath))
        sys.exit("Unexpected error:", sys.exc_info()[0])



    # Clean settings
    #=============================================================================
    for k, v in db_common['settings'].items():
        for c in ['\"', '\r', '\n']:
            v = v.replace(c, '')
        db_common['settings'][k] = v


    # Directories
    #=============================================================================
    # Save relative directory as this is mandatory for ffmpeg
    db_common['directories']['config'] = config_path

    for d in ['config',
                '3rd_party',
                'inputs',
                'outputs',
                'cache',
                'cache_progressive',
                'cache_progressive_default',
                'cache_default',
                'frames',
                'frames_default',
                'hashes']:
        v = db_common['directories'][d]
        for c in ['\"', '\r', '\n']:
            v = v.replace(c, '')
        db_common['directories'][d] = os.path.normpath(os.path.abspath(v))


    for d in ['real_cugan', 'real_esrgan', 'esrgan', 'animesr', 'pytorch']:
        v = db_common['directories'][d]
        for c in ['\"', '\r', '\n']:
            v = v.replace(c, '')
        db_common['directories'][d] = os.path.normpath(os.path.abspath(os.path.join(
                        db_common['directories']['3rd_party'],
                        v)))
    # Clean
    for d, v in db_common['directories'].items():
        for c in ['\"', '\r', '\n']:
            v = v.replace(c, '')
        db_common['directories'][d] = v

    # Use default values
    for d in ['cache', 'cache_progressive', 'frames']:
        if not os.path.exists(db_common['directories'][d]):
            db_common['directories'][d] = db_common['directories']['%s_default' % (d)]
        try: del db_common['directories']['%s_default' % (d)]
        except: pass


    # Executables
    #=============================================================================
    if platform.system() == "Windows":
        # Windows
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
            except: pass

            db_common['tools'][tool] = os.path.abspath(os.path.normpath(os.path.join(
                            db_common['directories']['3rd_party'],
                            db_common['directories']['ffmpeg_win'],
                            db_common['tools'][tool])))

        tool = 'mkvmerge'
        if platform.system() == "Windows":
            db_common['tools']['mkvmerge'] = os.path.abspath(os.path.normpath(os.path.join(
                db_common['directories'][f"{tool}_win"], tool)))
        else:
            db_common['tools']['mkvmerge'] = tool

        for d in ['ffmpeg', 'ffmpeg_win',
                    'mkvmerge', 'mkvmerge_win']:
            try: del db_common['directories'][d]
            except: pass

    else:
        # Linux
        db_common['tools'] = {
            'ffmpeg': "ffmpeg",
            'mkvmerge': "mkvmerge",
            'ffprobe': "ffprobe"
        }

        for tool in ['ffmpeg', 'ffprobe']:
            try:
                v = db_common['directories'][d]
                for c in ['\"', '\r', '\n']:
                    v = v.replace(c, '')
            except: pass

            db_common['tools'][tool] = os.path.abspath(os.path.normpath(os.path.join(
                            db_common['directories']['3rd_party'],
                            db_common['directories']['ffmpeg'],
                            db_common['tools'][tool])))

        for d in ['ffmpeg', 'ffmpeg_win',
                    'mkvmerge', 'mkvmerge_win']:
            try: del db_common['directories'][d]
            except: pass


    db_common['tools']['nnedi3_weights'] = os.path.abspath(os.path.normpath(os.path.join(
                    db_common['directories']['3rd_party'],
                    db_common['directories']['nnedi3_weights'])))
    try: del db_common['directories']['nnedi3_weights']
    except: pass


    # Subprocess settings
    #===========================================================================
    db_common['process'] = get_process_cfg()


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


