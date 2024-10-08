
from copy import deepcopy
import re
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

from utils.mco_types import ChapterGeometry, ChapterVideo, SceneGeometry, Scene
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

def parse_geometry_configurations(k_ep_or_g: str):
    """ Parse configuration file which list the crop coordinates for each scene.
    TODO: it uses the first frame of a scene to identify the scene rather the index, so that
    a modification of scenes will not break anything
    """
    verbose = False
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
        if section not in all_chapter_keys():
            continue
        if verbose:
            print(f"\tparse_geometry_configurations: chapter: {section}")

        # Get db target video
        db_video: ChapterVideo
        if k_ep_or_g in ('g_debut', 'g_fin'):
            db_video = db[k_ep_or_g]['video']
        else:
            db_video = db[k_ep_or_g]['video']['target'][section]

        # for each option
        for k_str in config.options(section):
            if verbose:
                print(f"\t\tk_str=[{k_str}]")

            if k_str == 'width':
                db_video['geometry'] = ChapterGeometry(int(config.get(section, 'width')))

            if result := re.search(re.compile(r"(\d{3})_([afkjs])_(ep\d{2})_([a-z_]+)_(\d{3})"), k_str):
                scene_no: int = int(result.group(1))
                k_ed_src: str = result.group(2)
                k_ep_src: str = result.group(3)
                k_ch_src: str = result.group(4)
                scene_no_src: int = int(result.group(5))
                scene: Scene = db_video['scenes'][scene_no]
                src_scene: Scene = scene['src'].primary_scene()['scene']
                if (
                    src_scene['k_ed'] != k_ed_src
                    or src_scene['k_ep'] != k_ep_src
                    or src_scene['k_ch'] != k_ch_src
                    or src_scene['no'] != scene_no_src
                ):
                    if verbose:
                        print(yellow(f"not the primary scene: [{k_str}]"))
                    continue

                properties = config.get(section, k_str)
                scene['geometry'] = get_geometry_from_properties(properties)

        for scene in db_video['scenes']:
            if 'geometry' not in scene:
                scene['geometry'] = SceneGeometry(use_default=True)

        if 'geometry' not in db_video:
            db_video['geometry'] = ChapterGeometry()

        # # if '.' not in k_section:
        # #     sys.exit("__parse_curve_configurations: error, no edition,ep,chapter specified")
        # k_ed, k_ep, k_chapter = section.split('.')
        # if verbose:
        #     print(orange(f"\tk_ep_or_g={k_ep_or_g};\t{k_ed}:{k_ep}:{k_chapter}"))
        # for k_str in config.options(section):
        #     if verbose:
        #         print(f"\t\tk_str={k_str}")

        #     if k_str == 'default':
        #         # Default values for scenes of this chapter
        #         properties = config.get(section, k_str)
        #         if verbose:
        #             print("\t\tproperties:", properties)

        #         try:
        #             nested_dict_set(
        #                 db[k_ep]['video'],
        #                 get_geometry_from_properties(properties),
        #                 k_ed, k_chapter, 'geometry'
        #             )
        #         except:
        #             print(orange(f"warning: {k_ep}:{k_ed}:{k_chapter}: video does not exist"))
        #         # if verbose:
        #         #     print("\t\tfinally:")
        #         #     pprint(db[k_ep]['video'][k_ed][k_chapter]['geometry'])
        #         #     sys.exit()

        #     else:
        #         # Custom values for a scene

        #         # if the key is the start/middle of a scene
        #         try:
        #             frame_no = int(k_str)
        #         except:
        #             continue

        #         # Get scene from scene
        #         try:
        #             src_scene = get_scene_from_frame_no(frame_no, k_ed=k_ed, k_ep=k_ep, k_chapter=k_chapter)
        #         except:
        #             # scenes not defined or unused
        #             if verbose:
        #                 logger.debug(
        #                     orange(f"parse_geometry_configurations: ")
        #                     + darkgrey(f"{k_ep}:{k_ed}:{k_chapter}: scene not found for frame no. {frame_no}")
        #                 )
        #             continue

        #         if src_scene is not None and  frame_no != src_scene['start']:
        #             logger.debug(
        #                 orange(f"parse_geometry_configurations: ")
        #                  + f"{frame_no} is not the start of {k_ed}:{k_ep}:{k_chapter}, no. {src_scene['no']:03}, {src_scene['start']}"
        #             )
        #         elif src_scene is None:
        #             logger.debug(
        #                 orange(f"parse_geometry_configurations: ")
        #                  + darkgrey(f"{k_ep}:{k_ed}:{k_chapter}: scene not found for frame no. {frame_no}")
        #             )
        #             continue


        # if k_section == 's.ep12.g_asuivre':
        #     pprint(db['g_asuivre'])
        #     pprint(db[k_ep]['video'][k_ed][k_chapter])
        #     print(cyan(db['ep01']['video']['target']['g_asuivre'])
        #     sys.exit()

        # if k_ed==K_ED_DEBUG and k_ep==K_EP_DEBUG and k_chapter==K_chapter_DEBUG:
        #     pprint(db[k_ep]['video'][k_ed][k_chapter])
        #     sys.exit()
    # if k_chapter==K_chapter_DEBUG:
    #     pprint(db[k_ep_or_g]['target']['video'])
    if verbose and k_ep_or_g == 'g_debut':
        pprint(db_video)
        sys.exit()


def get_geometry_from_properties(properties_str: str) -> SceneGeometry:
    geometry: SceneGeometry = SceneGeometry()

    properties = properties_str.strip().replace(' ', '').split(',')
    for property in properties:
        property_array_str: list[str] = property.split('=')
        property_name = property_array_str[0]
        value: str = property_array_str[1]

        if property_name == 'keep_ratio':
            geometry.keep_ratio = bool(value == 'true')
            geometry.defined = True

        elif property_name == 'fit_to_width':
            geometry.fit_to_width = bool(value == 'true')
            geometry.defined = True

        elif property_name == 'crop':
            # crop: x0, y0, x1, y1
            geometry.crop = list(map(int, value.split(':')))
            geometry.defined = True

        # Inner rect detection
        elif property_name == 'detection_params':
            # threshold_min, morph_kernel_radius, erode_kernel_radius, erode_iterations
            values = value.split(':')
            geometry.detection_params.threshold_min = int(values[0])
            geometry.detection_params.morph_kernel_radius = int(values[1])
            geometry.detection_params.erode_kernel_radius = int(values[2])
            geometry.detection_params.erode_iterations = int(values[3])

        elif property_name == 'autocrop':
            # crop: x0, y0, x1, y1
            geometry.autocrop = list(map(int, value.split(':')))

        elif property_name == 'use_autocrop':
            geometry.use_autocrop = bool(value == 'true')

        elif property_name == 'default':
            # Use a global default crop value
            geometry.use_default = bool(value == 'true')

        elif property_name == 'custom_detection_params':
            geometry.custom_detection_params = bool(value == 'true')

    return geometry





