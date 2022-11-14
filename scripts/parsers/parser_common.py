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
import subprocess

from parsers.parser_filters import parse_and_update_filters


DATABASE_PATH = "../database"

#===========================================================================
#
#   Parse common configuration file
#
#===========================================================================
def parse_common_configuration(config_path, verbose=False):

    db_common = dict()

    # Get directories configuration file
    #=============================================================================
    filepath = os.path.join(config_path, "directories.ini")
    if filepath.startswith("~/"):
        filepath = os.path.join(PosixPath(Path.home()), filepath[2:])
    if not os.path.exists(filepath):
        sys.exit("Erreur: fichier de configuration manquant: %s" % (filepath))
    try:
        config_directories = configparser.ConfigParser()
        config_directories.read(filepath)

        for k_section in config_directories.sections():
            db_common[k_section] = {}
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


    # Options
    #=============================================================================
    for key in db_common['options'].keys():
        value_str = db_common['options'][key]
        db_common['options'][key] = list(value_str.replace(' ', '').split(','))

    # Create empty list if not defined (avoid too many if/except)
    for o in ['deinterlace_add_tasks',
                'upscale_add_tasks',
                'discard_tasks']:
        if o not in db_common['options'].keys():
            db_common['options'][o] = list()



    # Directories
    #=============================================================================
    # Save relative directory as this is mandatory for ffmpeg
    db_common['directories']['config'] = config_path

    for key in db_common['directories'].keys():
        d = db_common['directories'][key]
        d = d.replace('\"', '')
        if d.startswith("~/"):
            d = os.path.join(PosixPath(Path.home()), d[2:])
        elif d.startswith("../"):
            d = os.path.normpath(os.path.join(os.getcwd(), d))
        db_common['directories'][key] = d


    # Executables
    #=============================================================================
    db_common['settings']['ffmpeg_exe'] = "ffmpeg"
    db_common['settings']['mkvmerge_exe'] = "mkvmerge"
    db_common['settings']['ffprobe_exe'] = "ffprobe"
    if sys.platform == 'win32':
        command = os.path.join(os.path.normpath(db_common['directories']['ffmpeg_win32']), "ffmpeg.exe")
        db_common['settings']['ffmpeg_exe'] = command
        if not os.path.exists(command):
            print("erreur: executable %s non trouvé" % (command))
            sys.exit()

        command = os.path.join(db_common['directories']['ffmpeg_win32'], "ffprobe.exe")
        db_common['settings']['ffprobe_exe'] = command
        if not os.path.exists(command):
            print("erreur: executable %s non trouvé" % (command))
            sys.exit()

        command = os.path.join(db_common['directories']['mkvmerge_win32'], "mkvmerge.exe")
        db_common['settings']['mkvmerge_exe'] = command
        if not os.path.exists(command):
            print("erreur: executable %s non trouvé" % (command))
            sys.exit()
    elif 'ffmpeg' in db_common['directories'].keys():
        command = os.path.join(db_common['directories']['ffmpeg'], "ffmpeg")
        db_common['settings']['ffmpeg_exe'] = command
        if not os.path.exists(command):
            print("erreur: executable %s non trouvé" % (command))
            sys.exit()

        command = os.path.join(db_common['directories']['ffmpeg'], "ffprobe")
        db_common['settings']['ffprobe_exe'] = command
        if not os.path.exists(command):
            print("erreur: executable %s non trouvé" % (command))
            sys.exit()

    for key in db_common['settings'].keys():
        for c in ['\"', '\r', '\n']:
            db_common['settings'][key] = db_common['settings'][key].replace(c, '')


    # Subprocess settings
    #===========================================================================
    if hasattr(subprocess, 'STARTUPINFO'):
        startupInfo = subprocess.STARTUPINFO()
        startupInfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupInfo.dwFlags |= subprocess.STARTF_USESTDHANDLES
        osEnvironment = os.environ
    else:
        startupInfo = None
        osEnvironment = None

    db_common['process'] = {
        'startupInfo': startupInfo,
        'osEnvironment': osEnvironment,
    }

    # Dimensions
    #===========================================================================
    db_common['dimensions'] = {
        'initial': {
            'w': int(db_common['dimensions']['width_initial']),
            'h': int(db_common['dimensions']['height_initial'])
        },
        'upscale': {
            'w': int(db_common['dimensions']['width_upscale']),
            'h': int(db_common['dimensions']['height_upscale'])
        },
        'final': {
            'w': int(db_common['dimensions']['width_final']),
            'h': int(db_common['dimensions']['height_final'])
        }
    }



    # Filters
    #===========================================================================
    # Parse default common filters for all editions/parts
    if verbose:
        print("%s: parse the default filter" % (__name__))
    parse_and_update_filters(db_common, config_general, k_section='common', verbose=verbose)

    # Other common settings
    #===========================================================================
    db_common['fps'] = 25.0


    # # Dimensions
    # #===========================================================================
    # for k in db_common['dimensions'].keys():
    #     db_common['dimensions'][k] = int(db_common['dimensions'][k])

    return db_common


