
from configparser import ConfigParser
import sys
import os
import os.path
from pathlib import (
    Path,
    PosixPath,
)
from pprint import pprint
import re
from utils.p_print import *
from utils.path_utils import absolute_path
from ._types import Database
from ._keys import key
from .logger import logger
from ._db import db, database_path


#===========================================================================
#
#   Parse common configuration file
#
#===========================================================================
def parser_edition_common(db_common: dict, filename: str, verbose=False):

    db_common = db['common']

    filename = absolute_path(filename)
    if not os.path.exists(filename):
        sys.exit(f"[E] fichier de configuration manquant: {filename}")
    try:
        config_general = ConfigParser()
        config_general.read(filename)
        for k_section in config_general.sections():
            if k_section not in db_common.keys():
                db_common[k_section] = {}
            for _option in config_general.options(k_section):
                value = config_general.get(k_section, _option)
                db_common[k_section][_option] = value
    except:
        print("parser_edition_common: [E] fichier de configuration non trouvé ou erroné: %s \n\n" % (filename))
        sys.exit("Unexpected error:", sys.exc_info()[0])



#===========================================================================
#
#   Get editions from folder
#
#===========================================================================
def parse_editions(verbose=False):
    db_common = db['common']
    verbose = False

    logger.debug(lightgreen(f"parse editions:"))

    inputs_dir = db_common['directories']['inputs']
    if 'editions' not in db:
        db['editions'] = dict()
    db_editions = db['editions']
    available_editions = list()

    # Get directory path
    if not os.path.isdir(inputs_dir):
        sys.exit(red(f"Error: parse_editions: mkv folder {inputs_dir} is not a valid folder"))


    # List directories and files
    #   append it to the global dictionary
    for folder in os.listdir(inputs_dir):
        # list of folders in mkv files
        f_edition: str = os.path.join(inputs_dir, folder)
        if verbose:
            print(lightgrey(f"\t{folder}"))

        if os.path.isdir(f_edition):
            # Edition found
            if verbose:
                print(f"found folder(edition)=%s" % (folder))
            db_editions[folder] = {
                'inputs': {
                    'video': dict(),
                    'audio': dict(),
                }
            }

            inputs = db_editions[folder]['inputs']

            # List episodes and their input files for each edition
            for filename in os.listdir(f_edition):
                logger.debug(f"\tfilename= {filename}" % ())
                filepath = os.path.join(inputs_dir, folder, filename)
                if os.path.isfile(filepath):
                    if verbose:
                        print("\tsearch ep no. from %s" % (filename))
                    if (tmp := re.search(
                        re.compile(r"^([a-z_a-z0-9]+)_ep([0-9]{2})(?:-([0-9]{2}))?"),
                        filename)
                    ):
                        if tmp.group(1) == folder:
                            # single episode or first episode in this file
                            ep_no = int(tmp.group(2))
                            k_ep = key(ep_no)
                            # Video with or w/out audio
                            if filename.endswith(".mkv"):
                                inputs['video'][k_ep] = filepath
                                if k_ep not in inputs['audio']:
                                    # use this file by default as the audio src
                                    inputs['audio'][k_ep] = filepath

                                if tmp.group(3) is not None:
                                    # multiple episode in this file
                                    for i in range(ep_no+1, int(tmp.group(3))+1):
                                        k_ep = key(i)
                                        inputs['video'][k_ep] = filepath
                                        if k_ep not in inputs['audio']:
                                            # use this file by default as the audio src
                                            inputs['audio'][k_ep] = filepath
                            # Audio
                            elif filename.endswith(".wav"):
                                inputs['audio'][k_ep] = filepath
                                if tmp.group(3) is not None:
                                    # multiple episode in this file
                                    for i in range(ep_no+1, int(tmp.group(3))+1):
                                        inputs['audio']['ep%02d' % (i)] = filepath
                        else:
                            print("Error: prefix differs from edition %s vs %s" % (tmp.group(1), folder))

            # Add to the list of available editions
            available_editions.append(folder)

    if verbose:
        print(lightgreen("Editions:"))
        pprint(db_editions)


    # Get directory path
    if not os.path.isdir(database_path):
        sys.exit(red(f"Error: parse_editions: {database_path} is not a valid directory"))


    if verbose:
        print(lightgreen("Available editions:"), available_editions)
        print(lightgreen("Discard editions:"), db_common['editions']['discard'])


    # Remove editions that should not be parsed
    for k_ed in db_common['editions']['discard']:
        try:
            available_editions.remove(k_ed)
            del db_editions[k_ed]
        except:
            pass

    if verbose:
        print(lightgreen("Editions:"))
        pprint(db_editions.keys())

    # Consolidate editions
    db_editions['available']  = list()
    for k_ed in available_editions:
        edition = db_editions[k_ed]

        if len(edition['inputs']['video']) == 0 and len(edition['inputs']['audio']) == 0:
            del db_editions[k_ed]
            # print(f"warning: {__name__}: remove edition {k_ed}")
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

        db_editions['available'].append(k_ed)

