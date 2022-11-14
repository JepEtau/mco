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

from parsers.parser_filters import parse_and_update_filters



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
def parse_editions(database, k_ed_fgd='k', k_ed_ref='k', cfg_foldername="../database", verbose=False):
    db_common = database['common']

    mkv_foldername = db_common['directories']['input']
    db_editions = dict()
    available_editions = list()

    # Get directory path
    if mkv_foldername.startswith("~/"):
        mkv_foldername = os.path.join(PosixPath(Path.home()), mkv_foldername)
    if not os.path.isdir(mkv_foldername):
        sys.exit("Error: %s is not a valid folder" % (mkv_foldername))


    # List directories and files
    #   append it to the global dictionary
    for folder in os.listdir(mkv_foldername):
        # list of folders in mkv files
        f_edition = os.path.join(mkv_foldername, folder)

        if os.path.isdir(f_edition):
            # Edition found
            if verbose:
                print("found folder(edition)=%s" % (folder))
            db_editions[folder] = {'inputs': {}}

            inputs = db_editions[folder]['inputs']

            # List episodes and their input files for each edition
            for filename in os.listdir(f_edition):
                if verbose:
                    print("filename= %s" % (filename))
                filepath = os.path.join(db_common['directories']['input'], folder, filename)
                if os.path.isfile(filepath) and filename.endswith(".mkv"):
                    if verbose: print("search ep no. from %s" % (filename))
                    tmp = None
                    tmp = re.search(re.compile("^([a-z_a-z0-9]+)_ep([0-9]{2})(?:-([0-9]{2}))?"), filename)
                    if tmp is not None:
                        if tmp.group(1) == folder:
                            # single episode or first episode in this file
                            epNo = int(tmp.group(2))
                            inputs['ep%02d' % (epNo)] = filepath
                            if tmp.group(3) is not None:
                                # multiple episode in this file
                                for i in range(epNo+1, int(tmp.group(3))+1):
                                    inputs['ep%02d' % (i)] = filepath
                        else:
                            print("Error: prefix differs from edition %s vs %s" % (tmp.group(1), folder))
                    else:
                        sys.exit("Error: %s is not a valid filename" % (filename))

            # Add to the list of available editions
            available_editions.append(folder)

    if verbose:
        pprint(db_editions)


    # Get directory path
    if cfg_foldername.startswith("~/"):
        cfg_foldername = os.path.join(PosixPath(Path.home()), cfg_foldername)
    if not os.path.isdir(cfg_foldername):
        sys.exit("Error: %s is not a valid folder" % (cfg_foldername))

    # Get common file for each edition
    for k_ed in available_editions:
        edition_common_filename = os.path.join(cfg_foldername, "common_%s.ini" % (k_ed))
        if not os.path.isfile(edition_common_filename):
            # print("warning: %s: remove edition [%s]" % (__name__, k_ed))
            # No config file found for this edition, remove it from the available
            del db_editions[k_ed]
            available_editions.remove(k_ed)
            continue
        else:
            if verbose: print("consolidate edition [%s]" % (k_ed))

            # Parse comon ini file for each edition
            config = configparser.ConfigParser()
            config.read(edition_common_filename)
            for k_section in config.sections():
                if k_section.startswith("filters"):
                    parse_and_update_filters(db_editions[k_ed], config, k_section, verbose)
                    continue

                if k_section == 'dimensions':
                    # Only 'width_initial' is supported
                    for k_option in config.options(k_section):
                        value_str = config.get(k_section, k_option)
                        if k_option == 'width_initial':
                            db_editions[k_ed][k_section] = {'initial': {'w': int(value_str)}}
                    continue


    # Consolidate editions
    for k_ed in available_editions:
        edition = db_editions[k_ed]
        # Create filters structure if not exist
        if 'filters' not in edition.keys():
           edition['filters'] = dict()

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

    # Available editions
    db_editions['available'] = available_editions

    # Set the target (i.e. the edition used as foreground)
    db_editions['fgd'] = k_ed_fgd

    # Set the edition used as the ereference for the calculation of the frame no.
    db_editions['k_ed_ref'] = k_ed_ref

    return db_editions

