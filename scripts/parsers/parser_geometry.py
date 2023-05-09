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

from parsers.parser_generiques import get_dependencies_for_generique
from utils.common import (
    K_ALL_PARTS,
    K_GENERIQUES,
)
from shot.utils import get_shot_from_frame_no
from utils.nested_dict import nested_dict_set
from utils.pretty_print import *

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
    verbose = False
    K_ED_DEBUG = ''
    K_EP_DEBUG = ''
    K_PART_DEBUG = ''
    if verbose:
        print_lightgreen("parse_geometry_configurations: %s" % (k_ep_or_g))
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
        if verbose:
            print("\tparse_geometry_configurations: section:%s" % (k_section))
        if k_section in K_ALL_PARTS:
            # This section define the geometry of the target: i.e. width
            if k_ep_or_g in ['g_debut', 'g_fin']:
                nested_dict_set(db, {'target':dict()}, k_ep_or_g, 'video', 'geometry')
                target_geometry = db[k_ep_or_g]['video']['geometry']['target']
            else:
                nested_dict_set(db, {'target':dict()}, k_ep_or_g, 'video', 'target', k_section, 'geometry')
                target_geometry = db[k_ep_or_g]['video']['target'][k_section]['geometry']['target']

            properties = config.get(k_section, 'target').strip().replace(' ', '').split(',')
            for property in properties:
                property_array_str = property.split('=')
                property_name = property_array_str[0]

                if property_name == 'width':
                    target_geometry['w'] = int(property_array_str[1])

            # if k_section == 'asuivre':
            #     print("\t%s:%s" % (k_ep_or_g, k_section))
            #     pprint(db[k_ep_or_g]['video']['target'][k_section])
            #     # sys.exit()
            continue


        # if '.' not in k_section:
        #     sys.exit("__parse_curve_configurations: error, no edition,ep,part specified")
        k_ed, k_ep, k_part = k_section.split('.')
        if verbose:
            print_orange("\tk_ep_or_g=%s;\t%s:%s:%s" % (k_ep_or_g, k_ed, k_ep, k_part))
        for k_str in config.options(k_section):
            if verbose:
                print("\t\tk_str=%s" % (k_str))

            if k_str == 'default':
                # Default values for shots of this part
                properties = config.get(k_section, k_str)
                if verbose:
                    print("\t\tproperties:", properties)

                try:
                    nested_dict_set(db[k_ep]['video'],
                        get_geometry_from_properties(properties),
                        k_ed, k_part, 'geometry')
                except:
                    print_orange(f"warning: {k_ep}:{k_ed}:{k_part}: video does not exist")
                # if verbose:
                #     print("\t\tfinally:")
                #     pprint(db[k_ep]['video'][k_ed][k_part]['geometry'])
                #     sys.exit()

            else:
                # Custom values for a shot

                # if the key is the start/middle of a shot
                try: frame_no = int(k_str)
                except: continue

                # Get shot from shot
                try:
                    shot = get_shot_from_frame_no(db, frame_no, k_ed=k_ed, k_ep=k_ep, k_part=k_part)
                except:
                    # Shots not defined or unused
                    if verbose:
                        print_orange(f"\t\t\twarning: {k_ep}:{k_ed}:{k_part}: shot is not defined ({frame_no})")
                    continue

                if frame_no != shot['start']:
                    print_orange(f"warning: parse geometry configuration:", end=' ')
                    print(f"{frame_no} is not the start of {k_ed}:{k_ep}:{k_part}, no. {shot['no']:03}, {shot['start']}")


                properties = config.get(k_section, k_str)
                nested_dict_set(shot,
                    get_geometry_from_properties(properties),
                    'geometry', 'shot')

        # if k_section == 's.ep12.g_asuivre':
        #     pprint(db['g_asuivre'])
        #     pprint(db[k_ep]['video'][k_ed][k_part])
        #     print_cyan(db['ep01']['video']['target']['g_asuivre'])
        #     sys.exit()

        if k_ed==K_ED_DEBUG and k_ep==K_EP_DEBUG and k_part==K_PART_DEBUG:
            pprint(db[k_ep]['video'][k_ed][k_part])
            sys.exit()
    # if k_part==K_PART_DEBUG:
    #     pprint(db[k_ep_or_g]['target']['video'])
    #     sys.exit()


def get_geometry_from_properties(properties_str):
    geometry_dict = {
        'keep_ratio': True,
        'fit_to_width': False,
        'crop': [0] * 4
    }
    properties = properties_str.strip().replace(' ', '').split(',')
    for property in properties:
        property_array_str = property.split('=')
        property_name = property_array_str[0]

        if property_name == 'keep_ratio':
            geometry_dict[property_name] = True if property_array_str[1] == 'true' else False

        elif property_name == 'fit_to_width':
            geometry_dict['fit_to_width'] = True if property_array_str[1] == 'true' else False

        elif property_name == 'crop':
            # crop: x0, y0, x1, y1
            values = property_array_str[1].split(':')
            geometry_dict[property_name] = list(map(lambda x: int(x), values))

    return geometry_dict



def get_initial_target_geometry(db, k_ep, k_part) -> dict:
    # print("get_initial_target_geometry for %s:%s" % (k_ep, k_part))
    target_geometry = dict()

    if k_part in ['g_debut', 'g_fin']:
        db_video = db[k_part]['video']
        k_ep_target = 'ep00'
    elif k_part in ['g_asuivre', 'g_reportage']:
        db_video = db[k_ep]['video']['target'][k_part[2:]]
        k_ep_target = k_ep
    else:
        db_video = db[k_ep]['video']['target'][k_part]
        k_ep_target = k_ep

    try:
        nested_dict_set(target_geometry, db_video['geometry']['target'].copy(), k_ep_target, k_part)
    except:
        pass

    return target_geometry



def get_initial_default_shot_geometry(db, k_ep, k_part) -> dict:
    """ Returns a list of crops/resize per part for each edition
    """
    verbose = True
    if verbose:
        print_lightgreen("get_initial_default_shot_geometry for %s:%s" % (k_ep, k_part))
    default_shot_geometry = dict()

    if k_part in ['g_debut', 'g_fin']:
        # Get the list of editions and episode that are used by this generique
        dependencies = get_dependencies_for_generique(db, k_part_g=k_part)

        # For each dependency, get the list of geometry
        for k_ed in dependencies.keys():
            for k_ep_tmp in dependencies[k_ed]:
                db_video = db[k_ep_tmp]['video'][k_ed][k_part]
                if verbose:
                    print(f"get_initial_default_shot_geometry for {k_part}: {k_ed}:{k_ep_tmp}:{k_part}")
                # pprint(db[k_ep_src][k_ed][k_part])
                try:
                    nested_dict_set(default_shot_geometry,
                        db_video['geometry'].copy(),
                        k_ed, k_ep_tmp, k_part)
                except:
                    pass
    else:
        # Get All geometry for all editions ofr this ep/part
        if verbose:
            print("\t", db['editions']['available'])
        for k_ed in db['editions']['available']:
            if k_ed not in db[k_ep]['video'].keys():
                continue
            db_video = db[k_ep]['video'][k_ed][k_part]
            try:
                nested_dict_set(default_shot_geometry,
                    db_video['geometry'].copy(),
                    k_ed, k_ep, k_part)
            except:
                pass

    if verbose:
        pprint(default_shot_geometry)
        # sys.exit()
    return default_shot_geometry



def get_initial_shot_geometry(db, k_ep, k_part) -> dict:
    verbose = False

    if verbose:
        print_lightcyan(f"get_initial_shot_geometry: {k_ep}:{k_part}")

    shot_geometry = dict()
    if k_part in ['g_debut', 'g_fin']:
        # Get the list of editions and episode that are used by this generique
        dependencies = get_dependencies_for_generique(db, k_part_g=k_part)

        # For each dependency, get the list of geometry
        for k_ed in dependencies.keys():
            for k_ep_tmp in dependencies[k_ed]:
                db_video = db[k_ep_tmp]['video'][k_ed][k_part]
                if 'shots' not in db_video.keys():
                    continue

                for shot in db_video['shots']:
                    # print("get_initial_shot_geometry: %s:%s:%s" % (k_ed,k_ep_src,k_part))
                    # pprint(db[k_ep_src][k_ed][k_part])
                    try:
                        nested_dict_set(shot_geometry,
                            shot['geometry']['shot'].copy(),
                            k_ed, k_ep_tmp, k_part, shot['start'])
                    except:
                        pass
    else:
        # Get All geometry for all editions ofr this ep/part
        if verbose:
            print_lightgrey(f"\t- available editions: {db['editions']['available']}")

        for k_ed in db['editions']['available']:
            if k_ed not in db[k_ep]['video'].keys():
                continue

            if verbose:
                print_lightgrey(f"\t- parts: {list(db[k_ep]['video'][k_ed].keys())}")
            db_video = db[k_ep]['video'][k_ed][k_part]
            if 'shots' not in db_video.keys():
                continue

            for shot in db_video['shots']:
                try:
                    nested_dict_set(shot_geometry,
                        shot['geometry']['shot'].copy(),
                        k_ed, k_ep, k_part, shot['start'])
                except:
                    pass

    return shot_geometry




