
from copy import deepcopy
import sys
import configparser
import os
import os.path
from pathlib import (
    Path,
    PosixPath,
)
from pprint import pprint
from typing import Any

from utils.mco_types import ChapterGeometry, SceneGeometry
from utils.path_utils import absolute_path

from .credits import get_credits_dependencies
from ._keys import all_chapter_keys
from .logger import logger
from .scene import get_scene_from_frame_no
from .helpers import nested_dict_set
from utils.p_print import *
from ._db import db

# n'utilise pas le no. de plan car en cas de modification de la
# liste des plans (ajout ou suppression), il pourrait y avoir des décalages
# le no. de plan est retrouvable par les parsers depuis le no. de trame
# et plus rapide encore lorsque la partie est spécifiée; lors de l'écriture automatique
# par l'éditeur, le no. de trame correspond à la 1ere trame du plan

def parse_geometry_configurations(k_ep_or_g:str):
    """ Parse configuration file which list the crop coordinates for each scene.
    TODO: it uses the first frame of a scene to identify the scene rather the index, so that
    a modification of scenes will not break anything
    """
    verbose = True
    K_ED_DEBUG = ''
    K_EP_DEBUG = ''
    K_chapter_DEBUG = ''
    if verbose:
        print(lightgreen(f"parse_geometry_configurations: {k_ep_or_g}"))

    # Open configuration file
    filepath = absolute_path(
            os.path.join(
            db['common']['directories']['config'],
            k_ep_or_g,
            f"{k_ep_or_g}_geometry.ini"
        )
    )
    if not os.path.exists(filepath):
        return

    # Parse the file
    config = configparser.ConfigParser()
    config.read(filepath)
    for section in config.sections():
        if verbose:
            print(f"\tparse_geometry_configurations: chapter: {section}")
        if section in all_chapter_keys():
            width: int = -1
            properties = config.get(section, 'target').strip().replace(' ', '').split(',')
            for property in properties:
                property_array_str = property.split('=')
                property_name = property_array_str[0]

                if property_name == 'width':
                    width = int(property_array_str[1])

            # This section define the geometry of the chapter: i.e. width
            if k_ep_or_g in ('g_debut', 'g_fin'):
                db[k_ep_or_g]['video']['geometry'] = ChapterGeometry(width)

            else:
                db[k_ep_or_g]['video']['target'][section]['geometry'] = ChapterGeometry(width)

            continue

        # if '.' not in k_section:
        #     sys.exit("__parse_curve_configurations: error, no edition,ep,chapter specified")
        k_ed, k_ep, k_chapter = section.split('.')
        if verbose:
            print(orange(f"\tk_ep_or_g={k_ep_or_g};\t{k_ed}:{k_ep}:{k_chapter}"))
        for k_str in config.options(section):
            if verbose:
                print(f"\t\tk_str={k_str}")

            if k_str == 'default':
                # Default values for scenes of this chapter
                properties = config.get(section, k_str)
                if verbose:
                    print("\t\tproperties:", properties)

                try:
                    nested_dict_set(
                        db[k_ep]['video'],
                        get_geometry_from_properties(properties),
                        k_ed, k_chapter, 'geometry'
                    )
                except:
                    print(orange(f"warning: {k_ep}:{k_ed}:{k_chapter}: video does not exist"))
                # if verbose:
                #     print("\t\tfinally:")
                #     pprint(db[k_ep]['video'][k_ed][k_chapter]['geometry'])
                #     sys.exit()

            else:
                # Custom values for a scene

                # if the key is the start/middle of a scene
                try:
                    frame_no = int(k_str)
                except:
                    continue

                # Get scene from scene
                try:
                    scene = get_scene_from_frame_no(frame_no, k_ed=k_ed, k_ep=k_ep, k_chapter=k_chapter)
                except:
                    # scenes not defined or unused
                    if verbose:
                        logger.debug(
                            orange(f"parse_geometry_configurations: ")
                            + darkgrey(f"{k_ep}:{k_ed}:{k_chapter}: scene not found for frame no. {frame_no}")
                        )
                    continue

                if scene is not None and  frame_no != scene['start']:
                    logger.debug(
                        orange(f"parse_geometry_configurations: ")
                         + f"{frame_no} is not the start of {k_ed}:{k_ep}:{k_chapter}, no. {scene['no']:03}, {scene['start']}"
                    )
                elif scene is None:
                    logger.debug(
                        orange(f"parse_geometry_configurations: ")
                         + darkgrey(f"{k_ep}:{k_ed}:{k_chapter}: scene not found for frame no. {frame_no}")
                    )
                    continue

                properties = config.get(section, k_str)
                scene['geometry'] = get_geometry_from_properties(properties)

        # if k_section == 's.ep12.g_asuivre':
        #     pprint(db['g_asuivre'])
        #     pprint(db[k_ep]['video'][k_ed][k_chapter])
        #     print(cyan(db['ep01']['video']['target']['g_asuivre'])
        #     sys.exit()

        if k_ed==K_ED_DEBUG and k_ep==K_EP_DEBUG and k_chapter==K_chapter_DEBUG:
            pprint(db[k_ep]['video'][k_ed][k_chapter])
            sys.exit()
    # if k_chapter==K_chapter_DEBUG:
    #     pprint(db[k_ep_or_g]['target']['video'])
    #     sys.exit()


def get_geometry_from_properties(properties_str: str) -> SceneGeometry:
    geometry: SceneGeometry = SceneGeometry()

    properties = properties_str.strip().replace(' ', '').split(',')
    for property in properties:
        property_array_str: list[str] = property.split('=')
        property_name = property_array_str[0]

        if property_name == 'keep_ratio':
            geometry.keep_ratio = bool(property_array_str[1] == 'true')
            geometry.defined = True

        elif property_name == 'fit_to_width':
            geometry.fit_to_width = bool(property_array_str[1] == 'true')
            geometry.defined = True

        elif property_name == 'crop':
            # crop: x0, y0, x1, y1
            values = property_array_str[1].split(':')
            geometry.crop = tuple([map(lambda x: int(x), values)])
            geometry.defined = True




    return geometry



def get_initial_default_scene_geometry(k_ep: str, k_chapter: str) -> dict:
    """ Returns a list of crops/resize per chapter for each edition
    """
    verbose = True
    if verbose:
        print(lightgreen("get_initial_default_scene_geometry for %s:%s" % (k_ep, k_chapter)))
    default_scene_geometry = dict()

    if k_chapter in ('g_debut', 'g_fin'):
        # Get the list of editions and episode that are used by this generique
        dependencies = get_credits_dependencies(db, k_chapter_g=k_chapter)

        # For each dependency, get the list of geometry
        for k_ed in dependencies.keys():
            for k_ep_tmp in dependencies[k_ed]:
                db_video = db[k_ep_tmp]['video'][k_ed][k_chapter]
                if verbose:
                    print(f"get_initial_default_scene_geometry for {k_chapter}: {k_ed}:{k_ep_tmp}:{k_chapter}")
                # pprint(db[k_ep_src][k_ed][k_chapter])
                raise ValueError("here!!!")
                try:
                    nested_dict_set(
                        default_scene_geometry,
                        deepcopy(db_video['geometry']),
                        k_ed, k_ep_tmp, k_chapter
                    )

                except:
                    pass
    else:
        # Get All geometry for all editions ofr this ep/chapter
        if verbose:
            print("\t", db['editions']['available'])
        raise ValueError("here!!!")
        for k_ed in db['editions']['available']:
            if k_ed not in db[k_ep]['video'].keys():
                continue
            db_video = db[k_ep]['video'][k_ed][k_chapter]
            try:
                nested_dict_set(default_scene_geometry,
                    db_video['geometry'].copy(),
                    k_ed, k_ep, k_chapter)
            except:
                pass

    if verbose:
        pprint(default_scene_geometry)
        # sys.exit()
    return default_scene_geometry



def get_initial_scene_geometry(k_ep, k_chapter) -> dict:
    verbose = False

    if verbose:
        print(lightcyan(f"get_initial_scene_geometry: {k_ep}:{k_chapter}"))

    scene_geometry = dict()
    if k_chapter in ('g_debut', 'g_fin'):
        # Get the list of editions and episode that are used by this generique
        dependencies = get_credits_dependencies(db, k_chapter_g=k_chapter)

        # For each dependency, get the list of geometry
        for k_ed in dependencies.keys():
            for k_ep_tmp in dependencies[k_ed]:
                db_video = db[k_ep_tmp]['video'][k_ed][k_chapter]
                if 'scenes' not in db_video.keys():
                    continue

                for scene in db_video['scenes']:
                    # print("get_initial_scene_geometry: %s:%s:%s" % (k_ed,k_ep_src,k_chapter))
                    # pprint(db[k_ep_src][k_ed][k_chapter])
                    try:
                        geometry: SceneGeometry = scene['geometry']
                        nested_dict_set(
                            scene_geometry,
                            geometry.scene,
                            k_ed, k_ep_tmp, k_chapter, scene['start']
                        )
                    except:
                        pass
    else:
        # Get All geometry for all editions of this ep/chapter
        if verbose:
            print(lightgrey(f"\t- available editions: {db['editions']['available']}"))

        for k_ed in db['editions']['available']:
            if k_ed not in db[k_ep]['video'].keys():
                continue

            if verbose:
                print(lightgrey(f"\t- chapters: {list(db[k_ep]['video'][k_ed].keys())}"))
            db_video = db[k_ep]['video'][k_ed][k_chapter]
            if 'scenes' not in db_video.keys():
                continue

            for scene in db_video['scenes']:
                try:
                    geometry: SceneGeometry = scene['geometry']
                    nested_dict_set(
                        scene_geometry,
                        geometry.scene,
                        k_ed, k_ep, k_chapter, scene['start']
                    )
                except:
                    pass

    return scene_geometry




