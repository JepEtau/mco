# -*- coding: utf-8 -*-
import sys
import configparser
import os
import os.path
from pathlib import (
    Path,
    PosixPath,
)
import re

from pprint import pprint

from parsers.parser_generiques import parse_get_dependencies_for_generique
from utils.common import (
    K_GENERIQUES,
    get_k_part_from_frame_no,
    get_shot_from_frame_no_new,
    nested_dict_set,
)

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
    # print("\nparse_geometry_configurations: %s" % (k_ep_or_g))
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

        # print("%s:%s:%s:\t" % (k_ed, k_ep, k_part))

        for k_str in config.options(k_section):

            if k_str == 'geometry':
                # Global settings for this part
                if k_ep_or_g in ['g_debut', 'g_fin']:
                    if k_ep_or_g != k_part:
                        raise Exception("error: %s <> %s" % (k_ep_or_g, k_part))
                    db[k_ep][k_ed][k_ep_or_g]['video']['geometry'] = {'crop': [0, 0, 0, 0]}
                    part_geometry = db[k_ep][k_ed][k_ep_or_g]['video']['geometry']
                else:
                    db[k_ep][k_ed][k_part]['video']['geometry'] = {'crop': [0, 0, 0, 0]}
                    part_geometry = db[k_ep][k_ed][k_part]['video']['geometry']

                properties = config.get(k_section, k_str).strip().replace(' ', '').split(',')
                for property in properties:
                    property_array_str = property.split('=')
                    property_name = property_array_str[0]

                    if property_name == 'keep_ratio':
                        part_geometry[property_name] = True if property_array_str[1] == 'true' else False

                    elif property_name in ['resize', 'crop']:
                        # crop: x0, y0, x1, y1
                        # resize: w,h
                        values = property_array_str[1].split(':')
                        part_geometry[property_name] = list(map(lambda x: int(x), values))

            elif k_str.endswith('_geometry'):
                sys.exit("TODO: custom geometry for shots has to be implemented")
                # Frame no. = int(k_str[:-1 * len('_geometry')])
                # Get shot no from frame no
                # Get properties for this shot



def get_part_geometry_list(db, k_ep, k_part) -> dict:
    """ Returns a list of crops/resize per part for each edition
    """
    # print("get_part_geometry_list for %s:%s" % (k_ep, k_part))
    part_geometry = dict()

    if k_part in ['g_debut', 'g_fin']:
        # Get the list of editions and episode that are used by this generique
        dependencies = parse_get_dependencies_for_generique(db, k_part_g=k_part)

        # For each dependency, get the list of geometry
        for k_ed in dependencies.keys():
            for k_ep_tmp in dependencies[k_ed]:
                db_video = db[k_ep_tmp][k_ed][k_part]['video']
                # print("get_part_geometry: %s:%s:%s" % (k_ed,k_ep_src,k_part))
                # pprint(db[k_ep_src][k_ed][k_part])
                try: geometry = db_video['geometry'].copy()
                except: geometry = {'crop': [0, 0, 0, 0]}
                nested_dict_set(part_geometry, geometry, k_ed, k_ep_tmp, k_part)

    elif k_part in ['g_asuivre', 'g_reportage']:
        # Get the geometry in he ed/ep used to generate this generique
        k_ed_ref = db[k_part]['target']['video']['src']['k_ed']
        k_ep_ref = db[k_part]['target']['video']['src']['k_ep']
        db_video = db[k_ep_ref][k_ed_ref][k_part]['video']
        try: geometry = db_video['geometry'].copy()
        except: geometry = {'crop': [0, 0, 0, 0]}
        nested_dict_set(part_geometry, geometry, k_ed_ref, k_ep_ref, k_part)

    else:
        # Get All geometry for all editions ofr this ep/part
        for k_ed in db['editions']['available']:
            db_video = db[k_ep][k_ed][k_part]['video']
            try: geometry = db_video['geometry'].copy()
            except: geometry = {'crop': [0, 0, 0, 0]}
            nested_dict_set(part_geometry, geometry, k_ed, k_ep, k_part)

    # pprint(part_geometry)
    # if k_part == 'g_asuivre':
    #     sys.exit()
    return part_geometry




def get_shots_st_geometry(db, k_ep, k_part) -> dict:
    """ Returns a dict of crop/resize for each shot of this k_ep:k_part
    """
    st_geometry = dict()

    # Get the list of editions and episode that are used by this ep/part
    if k_part in ['g_debut', 'g_fin']:
        db_video = db[k_part]['target']['video']
    else:
        print("%s.get_shots_st_geometry: %s:%s" % (__name__, k_ep, k_part))
        k_ed_src = db[k_ep]['target']['video']['src']['k_ed']
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

