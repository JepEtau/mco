# -*- coding: utf-8 -*-
import sys

import configparser
import os
import os.path
import numpy as np
from pathlib import Path
from pathlib import PosixPath
from pprint import pprint
import re

from utils.common import (
    K_GENERIQUES,
    get_k_part_from_frame_no,
    get_shot_from_frame_no_new,
    nested_dict_set,
)
from images.curve import Curve

# n'utilise pas le no. de plan car en cas de modification de la
# liste des plans (ajout ou suppression), il pourrait y avoir des décalages
# le no. de plan est retrouvable par les parsers depuis le no. de trame
# et plus rapide encore lorsque la partie est spécifiée; lors de l'écriture automatique
# par l'éditeur, le no. de trame correspond à la 1ere trame du plan
#
# frame_no,<curve>


def parse_curve_configurations(db, k_ep_or_g:str):
    """ Parse configuration file
    It will returns the shots no. for each curve. This is mainly edited in curves
    editor
    """

    # Open configuration file
    filepath = os.path.join(db['common']['directories']['config'], k_ep_or_g, "%s_curves.ini" % (k_ep_or_g))
    if filepath.startswith("~/"):
        filepath = os.path.join(PosixPath(Path.home()), filepath[2:])
    if not os.path.exists(filepath):
        # print("warning: %s:__parse_curve_configurations: %s, %s is missing" % (__name__, k_ep_or_g, filepath))
        return

    # Parse the file
    config = configparser.ConfigParser()
    config.read(filepath)
    for k_section in config.sections():
        # print("\tsection:%s" % (k_section))
        if '.' not in k_section:
            sys.exit("__parse_curve_configurations: error, no edition,ep,part specified")
        k_ed, k_ep, k_part = k_section.split('.')

        for frame_no_str in config.options(k_section):
            frame_no = int(frame_no_str)
            value_str = config.get(k_section, frame_no_str)
            k_curve = value_str.strip()
            if k_curve == '':
                continue

            # Get shot from frame no.
            shot = get_shot_from_frame_no_new(db, frame_no, k_ed=k_ed, k_ep=k_ep, k_part=k_part)

            # Append curves struct to the shot
            shot['curves'] = {
                'k_curves': k_curve,
                'lut':None,
            }
            # print("%s:%s:%s: shot no. %s -> %s" % (k_ed, k_ep, k_part, shot['no'], shot['curves']['k_curves']))


def parse_curves_file(db, k_ep_or_g, k_curves:str) -> dict:
    """ This function reads a curve file and
        returns a curve object for each channel
        returns None if there is a problem with the curve file
    """
    # print("%s.parse_curves_file: %s, %s" % (__name__, k_ep_or_g, k_curves))
    library_path = db['common']['directories']['curves']
    filepath = os.path.join(library_path, k_ep_or_g, "%s.crv" % (k_curves))
    try:
        curves_file = open(filepath, 'r')
    except:
        print("Error: %s.parse_curves_file: %s, fichier manquant ou erroné: %s" % (__name__, k_ep_or_g, filepath))
        raise
    try:
        rgb_channels = {
            'r': Curve(),
            'g': Curve(),
            'b': Curve(),
            'm': Curve()
        }
        for line in curves_file.readlines():
            match = re.match("([r|g|b|m])=(.*)", line)
            k_channel = match.group(1)
            groups = match.group(2).split(';')
            rgb_channels[k_channel].remove_all_points()
            for group in groups:
                xy = group.split(':')
                rgb_channels[k_channel].add_point(np.float64(xy[0]),np.float64(xy[1]))
        curves_file.close()
    except:
        sys.exit("Error: cannot load curve file: %s" % (filepath))
        return None

    return rgb_channels



def write_curves_file(filepath, channels):
    """ This function writes a curve file
    """
    # filepath = os.path.join(path, k_ep_or_g, "%s.crv" % (curve_name))
    # if filepath.startswith("~/"):
    #     filepath = os.path.join(PosixPath(Path.home()), filepath[2:])

    # Write file
    try:
        curve_file = open(filepath, 'w')
    except:
        os.makedirs(os.path.dirname(filepath))
        curve_file = open(filepath, 'w')

    # pprint.pprint(curves)
    for k in ['m', 'r', 'g', 'b']:
        valueStr = "%s=" % (k)
        for p in channels[k].points():
            valueStr += "%.06f:%.06f;" % (p.x(), p.y())
        valueStr = valueStr[:-1]
        curve_file.write(valueStr + '\n')
    curve_file.close()



def get_curves_selection(db, k_ep, k_part) -> dict:
    # Create a dictionary of curves selection for each shot
    # It uses the shot_src so that this will work when replacing shots
    # from another episode/part
    shot_curves = dict()

    print("%s.get_curves_selection: src=?:%s:%s" % (__name__, k_ep, k_part))

    # Get the list of editions and episode that are used by this ep/part
    if k_part in ['g_debut', 'g_fin']:
        db_video = db[k_part]['common']['video']
    elif k_part in ['g_asuivre', 'g_reportage']:
        k_ed_src = db[k_part]['common']['video']['reference']['k_ed']
        k_ep_src = k_ep
        print("\t-> %s:%s:%s" % (k_ed_src, k_ep_src, k_part))
        db_video = db[k_ep_src][k_ed_src][k_part]['video']
    else:
        print("%s.get_curves_selection: %s:%s" % (__name__, k_ep, k_part))
        k_ed_src = db[k_ep]['common']['video']['reference']['k_ed']
        k_ep_src = k_ep
        db_video = db[k_ep_src][k_ed_src][k_part]['video']
        # print("%s.get_curves_selection: src=%s:%s:%s" % (__name__, k_ed_src, k_ep_src, k_part))

    for shot in db_video['shots']:
        if ('src' not in shot.keys()
            or ('use' in shot['src'].keys()
            and not shot['src']['use'])):
            shot_src = shot
            k_part_src = k_part
        else:
            if 'k_ed' in shot['src'].keys():
                k_ed_src = shot['src']['k_ed']
            k_ep_src = shot['src']['k_ep']
            k_part_src = get_k_part_from_frame_no(db,
                k_ed_src,
                k_ep_src,
                shot['src']['start'])
            shot_src = get_shot_from_frame_no_new(db,
                frame_no=shot['src']['start'],
                k_ed=k_ed_src,
                k_ep=k_ep_src,
                k_part=k_part_src)

        # Append to the dict if stitching curves are defined
        if 'curves' not in shot_src.keys():
            continue

        if shot_src['curves'] is not None:
            nested_dict_set(shot_curves, shot_src['curves'], k_ed_src, k_ep_src, k_part_src, shot['no'])

    return shot_curves



def parse_curves_folder(db, k_ep_or_g):
    # Curves contained in the curves directory:
    #  filename, key but do not parse files (will be done dynamically)
    # TODO: it lists all curves for a folder but this function has to be modified
    #       to also list the curves from another episode (dependancies)
    print("browse folder which contains curves: %s" % (k_ep_or_g))
    db_curves = dict()

    path = os.path.join(db['common']['directories']['curves'])
    if not os.path.exists(path):
        print("%s does not exist" % (path))
        return db_curves

    # Browse curves in the subdirectories
    if os.path.exists(os.path.join(path, k_ep_or_g)):
        for f in os.listdir(os.path.join(path, k_ep_or_g)):
            print("\t%s" % (f))
            if f.endswith(".crv"):
                # Create an element for each curve
                k_curves = os.path.splitext(f)[0]
                db_curves[k_curves] = {
                    'k_curves': k_curves,
                    'filepath': os.path.join(k_ep_or_g, f),
                    'channels': None,
                    'lut': None,
                    'shots': []
                }

    # Browse curves in the common directory
    # NO!
    # for f in os.listdir(path):
    #     if f.endswith(".crv"):
    #         # Create an element for each curve
    #         k_curves = os.path.splitext(f)[0]
    #         if k_curves in db_curves.keys():
    #             # Do not add if already in base
    #             continue
    #         db_curves[k_curves] = {
    #             'k_curves': k_curves,
    #             'filepath': f,
    #             'channels': None,
    #             'lut': None,
    #             'shots': []
    #         }


    # for each shot, get the src episode
    # and get the curves from the other folder.

    return db_curves
