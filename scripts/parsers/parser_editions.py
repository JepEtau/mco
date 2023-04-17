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
import re

from parsers.parser_filters import parse_filters
from utils.nested_dict import nested_dict_set
from utils.pretty_print import *



#===========================================================================
#
#   Parse common configuration file
#
#===========================================================================
def parser_edition_common(db_common, filename, verbose=False):

    # Get specific 'common configuration file' and merge it
    #=============================================================================
    if filename.startswith("~/"):
        filename = os.path.join(PosixPath(Path.home()), filename[2:])
    if not os.path.exists(filename):
        sys.exit("Erreur: fichier de configuration manquant: %s" % (filename))
    try:
        config_general = configparser.ConfigParser()
        config_general.read(filename)
        for k_section in config_general.sections():
            if k_section not in db_common.keys():
                db_common[k_section] = {}
            for _option in config_general.options(k_section):
                value = config_general.get(k_section, _option)
                db_common[k_section][_option] = value
    except:
        print("parser_edition_common: Erreur: fichier de configuration non trouvé ou erroné: %s \n\n" % (filename))
        sys.exit("Unexpected error:", sys.exc_info()[0])



#===========================================================================
#
#   Get editions from folder
#
#===========================================================================
def parse_editions(database, cfg_foldername, verbose=False):
    db_common = database['common']
    verbose = False

    mkv_foldername = db_common['directories']['inputs']
    database['editions'] = dict()
    db_editions = database['editions']
    available_editions = list()

    # Get directory path
    if mkv_foldername.startswith("~/"):
        mkv_foldername = os.path.join(PosixPath(Path.home()), mkv_foldername)
    if not os.path.isdir(mkv_foldername):
        sys.exit(print_red("Error: parse_editions: mkv folder %s is not a valid folder" % (mkv_foldername)))


    # List directories and files
    #   append it to the global dictionary
    for folder in os.listdir(mkv_foldername):
        # list of folders in mkv files
        f_edition = os.path.join(mkv_foldername, folder)

        if os.path.isdir(f_edition):
            # Edition found
            if verbose:
                print("found folder(edition)=%s" % (folder))
            db_editions[folder] = {
                'inputs': {
                    'video': dict(),
                    'audio': dict(),
                }
            }

            inputs = db_editions[folder]['inputs']

            # List episodes and their input files for each edition
            for filename in os.listdir(f_edition):
                if verbose:
                    print("filename= %s" % (filename))
                filepath = os.path.join(db_common['directories']['inputs'], folder, filename)
                if os.path.isfile(filepath):
                    if verbose:
                        print("search ep no. from %s" % (filename))
                    tmp = None
                    tmp = re.search(re.compile("^([a-z_a-z0-9]+)_ep([0-9]{2})(?:-([0-9]{2}))?"), filename)
                    if tmp is not None:
                        if tmp.group(1) == folder:
                            # single episode or first episode in this file
                            ep_no = int(tmp.group(2))
                            k_ep = 'ep%02d' % (ep_no)
                            if filename.endswith(".mkv"):
                                # Video with or w/out audio
                                inputs['video'][k_ep] = filepath
                                if k_ep not in inputs['audio'].keys():
                                    # use this file by default as the audio src
                                    inputs['audio'][k_ep] = filepath

                                if tmp.group(3) is not None:
                                    # multiple episode in this file
                                    for i in range(ep_no+1, int(tmp.group(3))+1):
                                        k_ep = 'ep%02d' % (i)
                                        inputs['video'][k_ep] = filepath
                                        if k_ep not in inputs['audio'].keys():
                                            # use this file by default as the audio src
                                            inputs['audio'][k_ep] = filepath

                            elif filename.endswith(".wav"):
                                # Audio
                                inputs['audio']['ep%02d' % (ep_no)] = filepath
                                if tmp.group(3) is not None:
                                    # multiple episode in this file
                                    for i in range(ep_no+1, int(tmp.group(3))+1):
                                        inputs['audio']['ep%02d' % (i)] = filepath
                        else:
                            print("Error: prefix differs from edition %s vs %s" % (tmp.group(1), folder))

            # Add to the list of available editions
            available_editions.append(folder)

    if verbose:
        pprint(db_editions)


    # Get directory path
    if cfg_foldername.startswith("~/"):
        cfg_foldername = os.path.join(PosixPath(Path.home()), cfg_foldername)
    if not os.path.isdir(cfg_foldername):
        sys.exit(print_red("Error: parse_editions: config %s is not a valid folder" % (cfg_foldername)))

    # Get common file for each edition
    for k_ed in available_editions.copy():
        edition_common_filename = os.path.join(cfg_foldername, "common_%s.ini" % (k_ed))
        if not os.path.isfile(edition_common_filename):
            # print("warning: %s: remove edition [%s]" % (__name__, k_ed))
            # No config file found for this edition, remove it from the available
            del db_editions[k_ed]
            available_editions.remove(k_ed)
            continue
        else:
            if verbose:
                print("consolidate edition [%s]" % (k_ed))

            # Parse comon ini file for each edition
            config = configparser.ConfigParser()
            config.read(edition_common_filename)
            for k_section in config.sections():
                if k_section.startswith("filters"):
                    parse_filters(db_editions[k_ed], config, k_section)
                    continue

                if k_section == 'dimensions':
                    for k_option in config.options(k_section):
                        value_str = config.get(k_section, k_option)
                        k_tmp, k_step_tmp = k_option.split('_')
                        nested_dict_set(db_editions[k_ed], int(value_str), 'dimensions', k_step_tmp, k_tmp[0])
                    continue

    # Consolidate editions
    db_editions['available']  = list()
    for k_ed in available_editions:
        edition = db_editions[k_ed]

        if len(edition['inputs']['video']) == 0 and len(edition['inputs']['audio']) == 0:
            del db_editions[k_ed]
            print("warning: %s: remove edition [%s]" % (__name__, k_ed))
            continue

        # Consolidate dimensions
        if 'dimensions' in edition.keys():
            # Custom dimensions used for this edition
            # Merge manually, update do not update sub-dict
            for k in db_common['dimensions']:
                if k not in edition['dimensions'].keys():
                    edition['dimensions'][k] = db_common['dimensions'][k]
                else:
                    for kk in db_common['dimensions'][k].keys():
                        if kk not in edition['dimensions'][k]:
                            edition['dimensions'][k][kk] = db_common['dimensions'][k][kk]
        else:
            # Create a simple link (do not copy)
            edition['dimensions'] = db_common['dimensions']

        db_editions['available'] .append(k_ed)


    # Set the edition used as the ereference for the calculation of the frame no.
    db_editions['k_ed_ref'] = database['common']['reference']['edition']

