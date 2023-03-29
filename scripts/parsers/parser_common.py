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

from parsers.parser_filters import parse_filters
from utils.process import get_process_cfg

DATABASE_PATH = "../database"

#===========================================================================
#
#   Parse common configuration file
#
#===========================================================================
def parse_common_configuration(db, config_path, verbose=False):
    db['common'] = dict()
    db_common = db['common']

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

    if 'deinterlace_fast' in db_common['options'].keys():
        db_common['options']['deinterlace_fast'] = True if db_common['options']['deinterlace_fast'][0] == 'y' else False
    else:
        db_common['options']['deinterlace_fast'] = False


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
                'output',
                'cache',
                'cache_default',
                'frames',
                'frames_default',
                'hashes']:
        v = db_common['directories'][d]
        for c in ['\"', '\r', '\n']:
            v = v.replace(c, '')
        db_common['directories'][d] = os.path.normpath(os.path.abspath(v))


    for d in ['real_cugan', 'real_esrgan', 'esrgan']:
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
    for d in ['cache', 'frames']:
        if not os.path.exists(db_common['directories'][d]):
            db_common['directories'][d] = db_common['directories']['%s_default' % (d)]
        try: del db_common['directories']['%s_default' % (d)]
        except: pass


    # Executables
    #=============================================================================
    if sys.platform == 'win32':
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
        db_common['tools']['mkvmerge'] = os.path.abspath(os.path.normpath(os.path.join(
                        db_common['directories']['3rd_party'],
                        db_common['directories']['%s_win' % (tool)],
                        db_common['tools'][tool])))


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

    # Dimensions
    #===========================================================================
    db_common['dimensions'] = {
        'initial': {
            'w': int(db_common['dimensions']['width_initial']),
            'h': int(db_common['dimensions']['height_initial'])
        },
        'deinterlace': {
            'w': int(db_common['dimensions']['width_deinterlace']),
            'h': int(db_common['dimensions']['height_deinterlace'])
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




    # Other common settings
    #===========================================================================
    db_common['fps'] = 25.0


    # # Dimensions
    # #===========================================================================
    # for k in db_common['dimensions'].keys():
    #     db_common['dimensions'][k] = int(db_common['dimensions'][k])


