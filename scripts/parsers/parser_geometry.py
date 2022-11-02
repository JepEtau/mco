#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
from operator import itemgetter
from copy import deepcopy
import os
import os.path
from os import stat_result, system
from pathlib import Path
from pathlib import PosixPath
from pprint import pprint
import re
import sys
from parsers.parser_generiques import parse_get_dependencies_for_generique
from time import sleep
from utils.common import get_k_part_from_frame_no, get_shot_from_frame_no_new
from utils.common import K_GENERIQUES

# n'utilise pas le no. de plan car en cas de modification de la
# liste des plans (ajout ou suppression), il pourrait y avoir des décalages
# le no. de plan est retrouvable par les parsers depuis le no. de trame
# et plus rapide encore lorsque la partie est spécifiée; lors de l'écriture automatique
# par l'éditeur, le no. de trame correspond à la 1ere trame du plan

def parse_geometry_configurations(db, k_ep_or_g:str):
    """ Parse configuration file which list the crop coordinates for each shot.
    TODO: it uses the first frame of a shot to identify the shot rather the index, so that
    a modification of shots will not break anything
    """

    # Open configuration file
    filepath = os.path.join(db['common']['directories']['config'], k_ep_or_g, "%s_geometry.ini" % (k_ep_or_g))
    if filepath.startswith("~/"):
        filepath = os.path.join(PosixPath(Path.home()), filepath[2:])
    if not os.path.exists(filepath):
        return

    # Parse the file
    config = configparser.ConfigParser()
    config.read(filepath)
    for k_section in config.sections():
        # print("\tsection:%s" % (k_section))
        if '.' not in k_section:
            sys.exit("__parse_curve_configurations: error, no edition,ep,part specified")
        k_ed, k_ep, k_part = k_section.split('.')

        # print("%s:%s:%s:\t" % (k_ed, k_ep, k_part), end='')
        db[k_ep][k_ed][k_part]['video']['geometry'] = {
            'crop': [0,0,0,0],
            'resize': [0,0],
            'keep_ratio': True,
        }
        for k_str in config.options(k_section):
            if k_str == 'crop':
                coordinates = config.get(k_section, k_str).strip().split(':')
                # x0, y0, x1, y1
                db[k_ep][k_ed][k_part]['video']['geometry']['crop'] = list(map(lambda x: int(x), coordinates))


def get_part_geometry(db, k_ep, k_part) -> dict:
    """ Returns a list of crops/resize per part for each edition
    """
    part_geometry = dict()

    # Get the list of editions and episode that are used by this ep/part
    if k_part in K_GENERIQUES:
        dependencies = parse_get_dependencies_for_generique(db, k_part_g=k_part)
        k_ep_src = db[k_part]['common']['video']['reference']['k_ep']
        k_ed = db[k_part]['common']['video']['reference']['k_ed']
    else:
        dependencies = db['editions']
        k_ep_src = k_ep

    # for each dependency, get the list of crop
    part_geometry = dict()
    for k_ed in dependencies.keys():
        if k_ed == 'layers':
            continue
        db_video = db[k_ep_src][k_ed][k_part]['video']
        # print("get_part_geometry: %s:%s:%s" % (k_ed,k_ep_src,k_part))
        # pprint(db[k_ep_src][k_ed][k_part])
        if k_ed not in part_geometry.keys():
            part_geometry[k_ed] = dict()
        if db_video['geometry'] is not None:
            part_geometry[k_ed][k_part] = db_video['geometry'].copy()

    return part_geometry





def get_shots_st_geometry(db, k_ep, k_part) -> dict:
    """ Returns a dict of crop/resize for each shot of this k_ep:k_part
    """
    st_geometry = dict()

    # Get the list of editions and episode that are used by this ep/part
    if k_part in ['g_debut', 'g_fin']:
        db_video = db[k_part]['common']['video']
    else:
        print("%s.get_shots_st_geometry: %s:%s" % (__name__, k_ep, k_part))
        k_ed_src = db[k_ep]['common']['video']['reference']['k_ed']
        k_ep_src = k_ep
        db_video = db[k_ep_src][k_ed_src][k_part]['video']
        print("%s.get_shots_st_geometry: src=%s:%s:%s" % (__name__, k_ed_src, k_ep_src, k_part))

    for shot in db_video['shots']:
        # print(shot)
        if ('src' not in shot.keys()
            or ('use' in shot['src'].keys()
            and not shot['src']['use'])):
            shot_src = shot
        else:
            if 'k_ed' in shot['src'].keys():
                k_ed_src = shot['src']['k_ed']
            k_ep_src = shot['src']['k_ep']
            k_part_src = get_k_part_from_frame_no(db, k_ed_src, k_ep_src, shot['src']['start'])
            shot_src = get_shot_from_frame_no_new(db, frame_no=shot['src']['start'], k_ed=k_ed_src, k_ep=k_ep_src, k_part=k_part_src)

        # Append to the dict if fgd_geometry is defined
        if 'st_geometry' not in shot_src.keys():
            continue

        if shot_src['st_geometry'] is not None:
            st_geometry[shot['no']] = shot_src['st_geometry']

    return st_geometry

