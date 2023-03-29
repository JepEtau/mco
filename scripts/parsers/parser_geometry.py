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
    K_GENERIQUES,
    get_src_shot_from_frame_no,
    nested_dict_set,
)
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
    K_ED_DEBUG = 'f'
    K_EP_DEBUG = ''
    K_PART_DEBUG = 'episode'
    print_green("\nparse_geometry_configurations: %s" % (k_ep_or_g))
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
        print_lightcyan("\tparse_geometry_configurations: section:%s" % (k_section))
        if '.' not in k_section:
            sys.exit("__parse_curve_configurations: error, no edition,ep,part specified")
        k_ed, k_ep, k_part = k_section.split('.')

        print("\t%s:%s:%s" % (k_ed, k_ep, k_part))
        for k_str in config.options(k_section):
            print("\tk_str=%s" % (k_str))

            if k_str == 'part':
                # Global settings for this part
                # if k_ep_or_g in ['g_debut', 'g_fin']:
                #     if k_ep_or_g != k_part:
                #         raise Exception("error: %s <> %s" % (k_ep_or_g, k_part))
                #     db[k_ep]['video'][k_ed][k_ep_or_g]['geometry'] = {
                #         'crop': [0, 0, 0, 0]
                #     }
                #     part_geometry = db[k_ep]['video'][k_ed][k_ep_or_g]['geometry']
                # else:
                #     # TODO: clean because same as generique... ???
                #     db[k_ep]['video'][k_ed][k_part]['geometry'] = {
                #         'crop': [0, 0, 0, 0]
                #     }

                nested_dict_set(db, dict(), k_ep, 'video', k_ed, k_part, 'geometry')
                part_geometry = db[k_ep]['video'][k_ed][k_part]['geometry']
                properties = config.get(k_section, k_str).strip().replace(' ', '').split(',')
                for property in properties:
                    property_array_str = property.split('=')
                    property_name = property_array_str[0]

                    if property_name == 'keep_ratio':
                        part_geometry[property_name] = True if property_array_str[1] == 'true' else False

                    elif property_name == 'fit_to_part':
                        print("part: found fit_to_part in %s:%s:%s:\t" % (k_ed, k_ep, k_part))
                        nested_dict_set(part_geometry,
                            True if property_array_str[1] == 'true' else False,
                            'resize',
                            property_name)

                    elif property_name in ['resize', 'crop']:
                        # crop: x0, y0, x1, y1
                        # resize: w,h
                        values = property_array_str[1].split(':')
                        part_geometry[property_name] = list(map(lambda x: int(x), values))
                continue

            # if the key is the start of a shot
            try: shot_start = int(k_str)
            except: continue

            # Get shot from shot
            try:
                shot = get_src_shot_from_frame_no(db, shot_start, k_ed=k_ed, k_ep=k_ep, k_part=k_part)
            except:
                # Shots not defined or unused
                print_orange("\tShot not defined: shot_start %d, %s:%s:%s" % (shot_start, k_ed, k_ep, k_part))
                continue

            if shot_start != shot['start']:
                print_red("key [%d] is not the start of the shot no. %d" % (shot_start, shot['no']))
                continue

            properties = config.get(k_section, k_str).strip().replace(' ', '').split(',')
            for property in properties:
                property_array_str = property.split('=')
                property_name = property_array_str[0]

                if property_name == 'keep_ratio':
                    value = True if property_array_str[1] == 'true' else False
                    nested_dict_set(shot, value, 'geometry', 'shot', property_name)

                elif property_name == 'fit_to_part':
                    print("shot: found fit_to_part in %s:%s:%s:\t" % (k_ed, k_ep, k_part))
                    value = True if property_array_str[1] == 'true' else False,
                    nested_dict_set(shot, value, 'geometry', 'shot', 'resize', property_name)

                elif property_name in ['resize', 'crop']:
                    # crop: x0, y0, x1, y1
                    # resize: w,h
                    values = list(map(lambda x: int(x), property_array_str[1].split(':')))
                    nested_dict_set(shot,  values, 'geometry', 'shot', property_name)

        if k_ed==K_ED_DEBUG and k_ep==K_EP_DEBUG and k_part==K_PART_DEBUG:
            pprint(db[k_ep]['video'][k_ed][k_part])
            sys.exit()

def get_initial_part_geometry(db, k_ep, k_part) -> dict:
    """ Returns a list of crops/resize per part for each edition
    """
    # print("get_initial_part_geometry for %s:%s" % (k_ep, k_part))
    part_geometry = dict()

    if k_part in K_GENERIQUES:
        # Get the list of editions and episode that are used by this generique
        dependencies = get_dependencies_for_generique(db, k_part_g=k_part)

        # For each dependency, get the list of geometry
        for k_ed in dependencies.keys():
            for k_ep_tmp in dependencies[k_ed]:
                db_video = db[k_ep_tmp]['video'][k_ed][k_part]
                # print("get_part_geometry: %s:%s:%s" % (k_ed,k_ep_src,k_part))
                # pprint(db[k_ep_src][k_ed][k_part])
                try:
                    nested_dict_set(part_geometry,
                        db_video['geometry'].copy(),
                        k_ed, k_ep_tmp, k_part)
                except:
                    pass
    else:
        # Get All geometry for all editions ofr this ep/part
        for k_ed in db['editions']['available']:
            if k_ed not in db[k_ep].keys():
                continue
            db_video = db[k_ep]['video'][k_ed][k_part]
            try:
                nested_dict_set(part_geometry,
                    db_video['geometry'].copy(),
                    k_ed, k_ep, k_part)
            except:
                pass

    return part_geometry




def get_initial_shot_geometry(db, k_ep, k_part) -> dict:
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
                    # print("get_part_geometry: %s:%s:%s" % (k_ed,k_ep_src,k_part))
                    # pprint(db[k_ep_src][k_ed][k_part])
                    try:
                        nested_dict_set(shot_geometry,
                            shot['geometry'].copy(),
                            k_ed, k_ep_tmp, k_part, shot['start'])
                    except:
                        pass
    else:
        # Get All geometry for all editions ofr this ep/part
        for k_ed in db['editions']['available']:
            if k_ed not in db[k_ep]['video'].keys():
                continue

            db_video = db[k_ep]['video'][k_ed][k_part]
            if 'shots' not in db_video.keys():
                continue

            for shot in db_video['shots']:
                try:
                    nested_dict_set(shot_geometry,
                        shot['geometry'].copy(),
                        k_ed, k_ep_tmp, k_part, shot['start'])
                except:
                    pass


    return shot_geometry




