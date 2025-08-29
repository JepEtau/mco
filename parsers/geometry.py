from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass, field
import re
import sys
import configparser
import os
import os.path
from pprint import pprint
from typing import Any

from scene.src_scene import SrcScene
from utils.p_print import *
from utils.mco_types import ChapterVideo, Scene
from utils.path_utils import absolute_path

from ._keys import all_chapter_keys
from .logger import logger
from ._db import db
from .hash import calc_hash

from processing.resize_to_4_3 import (
    ConvertTo43Params,
    TransformationValues,
    calculate_transformation_values,
)

FINAL_HEIGHT: int = 1080
FINAL_WIDTH: int = int(FINAL_HEIGHT * 4 / 3)


@dataclass
class ChapterGeometry:
    width: int = 1440


@dataclass(slots=True)
class DetectInnerRectParams:
    threshold_min: int = 10
    morph_kernel: int = 3
    erode_kernel: int = 5
    erode_iterations: int = 1
    do_add_borders: bool = True




@dataclass
class SceneGeometry:
    keep_ratio: bool = True
    fit_to_width: bool = False
    crop: list[int, int, int, int] = field(default_factory=list)
    use_default: bool = False
    chapter: ChapterGeometry = field(default_factory=ChapterGeometry)
    detection_params: DetectInnerRectParams = field(
        default_factory=DetectInnerRectParams
    )
    custom_detection_params: bool = False
    use_autocrop: bool = False
    autocrop: list[int, int, int, int] = field(default_factory=list)

    def __post_init__(self):
        # top, bottom, left, right
        self.crop = [0, 0, 0, 0]
        self.autocrop = [0, 0, 0, 0]
        self._defined: bool = False
        self._in_size: tuple[int, int] | None = None
        self.transformation: TransformationValues | None = None


    @property
    def defined(self) -> bool:
        return self._defined


    @defined.setter
    def defined(self, defined) -> None:
        self._defined = defined


    def get_crop(self) -> list[int, int, int, int]:
        """ top, bottom, left, right
        """
        crop_values: list[int, int, int, int] = (
            self.autocrop
            if self.use_autocrop
            else self.crop
        )
        return crop_values


    def max_width(self) -> int:
        # Maximum width this scene can have. Width of the resized crop rectangle
        c_t, c_b, c_l, c_r = self.get_crop()
        c_h, c_w = self._in_size[0] - (c_t + c_b), self._in_size[1] - (c_l + c_r)
        return int(c_w * FINAL_HEIGHT / c_h)


    def set_in_size(self, in_size: tuple[int, int]) -> None:
        """(h, w)
        """
        self._in_size = in_size


    def calculate_transformation(self, ch_width: int | None = None) -> TransformationValues | None :
        to_43_params: ConvertTo43Params = ConvertTo43Params(
            crop=self.get_crop(),
            keep_ratio=self.keep_ratio,
            fit_to_width=self.fit_to_width,
            final_height=FINAL_HEIGHT,
            scene_width=self.chapter.width if ch_width is None else ch_width,
        )

        if self._in_size is None:
            raise ValueError(red("missing input size"))

        self.transformation = None
        try:
            self.transformation = calculate_transformation_values(
                in_w=self._in_size[1],
                in_h=self._in_size[0],
                out_w=FINAL_WIDTH,
                params=to_43_params,
                verbose=False
            )
        except:
            pass

        return self.transformation


    def is_erroneous(self):
        return bool(
            self.transformation is None
            or self.transformation.err_borders is not None
        )


    def hash(self) -> str:
        params: str = f"{self.keep_ratio};{self.fit_to_width}"
        if self.use_autocrop:
            params += ";ac," + ','.join(list(
                map(str, (
                    self.detection_params.do_add_borders,
                    self.detection_params.morph_kernel,
                    self.detection_params.erode_kernel,
                    self.detection_params.erode_iterations,
                    self.detection_params.do_add_borders,
                ))
            ))
        else:
            params += f";{','.join(list(map(str, self.crop)))}"
        params += f";{self.chapter.width}"
        return calc_hash(params)



# n'utilise pas le no. de plan car en cas de modification de la
# liste des plans (ajout ou suppression), il pourrait y avoir des décalages
# le no. de plan est retrouvable par les parsers depuis le no. de trame
# et plus rapide encore lorsque la partie est spécifiée; lors de l'écriture automatique
# par l'éditeur, le no. de trame correspond à la 1ere trame du plan

def parse_geometry_file(k_ep_or_g: str, k_ch: str = '') -> None:
    """ Parse configuration file which list the crop coordinates for each scene.
    TODO: it uses the first frame of a scene to identify the scene rather the index, so that
    a modification of scenes will not break anything
    """
    verbose = True
    if verbose:
        print(lightgreen(f"parse_geometry_file: {k_ep_or_g}"))

    # Open configuration file
    if k_ch in ('g_asuivre', 'g_doc'):
        # raise ValueError(f"k_ep_or_g: {k_ep_or_g}, k_ch: {k_ch}")
        ch_video = db[k_ep_or_g]['video']['target'][k_ch]
        _k_ed, _k_ep, _k_ch, _ = ch_video['scenes'][0]['src'].primary_scene()['k_ed_ep_ch_no']
        filepath = absolute_path(
                os.path.join(
                db['common']['directories']['config'],
                _k_ep,
                f"{_k_ep}_geometry.ini"
            )
        )
    else:
        filepath = absolute_path(
                os.path.join(
                db['common']['directories']['config'],
                k_ep_or_g,
                f"{k_ep_or_g}_geometry.ini"
            )
        )

    if not os.path.exists(filepath):
        return


    # Parse the geometry file
    config = configparser.ConfigParser()
    config.read(filepath)
    for section in config.sections():
        if section not in all_chapter_keys():
            continue
        if verbose:
            print(f"parse_geometry_file: chapter: {section}")

        # Get db target video
        ch_video: ChapterVideo
        if k_ep_or_g in ('g_debut', 'g_fin'):
            ch_video = db[k_ep_or_g]['video']
        else:
            if section not in db[k_ep_or_g]['video']['target']:
                db[k_ep_or_g]['video']['target'][section] = {'scenes': []}
            ch_video = db[k_ep_or_g]['video']['target'][section]

        # for each option
        for k_str in config.options(section):
            if verbose:
                print(f"\t\tk_str=[{k_str}]")

            if k_str == 'width' and section in all_chapter_keys():
                ch_video['geometry'] = ChapterGeometry(
                    int(config.get(section, 'width'))
                )

            if result := re.search(re.compile(r"(\d{3})_([afkjs])_(ep\d{2})_([a-z_]+)_(\d{3})"), k_str):
                scene_no: int = int(result.group(1))
                k_ed_src: str = result.group(2)
                k_ep_src: str = result.group(3)
                k_ch_src: str = result.group(4)
                scene_no_src: int = int(result.group(5))

                src_ch_video = db[k_ep_src]['video'][k_ed_src][k_ch_src]
                try:
                    src_scene: SrcScene = src_ch_video['scenes'][scene_no_src]
                except:
                    # 2025-08-29
                    #   disable this to avoid too many messages when using dsr/replace tool

                    # print(red(f"exception: parse_geometry_file: {k_ep_or_g}:{section}:{scene_no}"))
                    # print(red(f"    src scene: {k_ep_src}:{k_ed_src}:{k_ch_src}:{scene_no_src}"))
                    pass
                # try:
                #     scene: Scene = ch_video['scenes'][scene_no]
                # except Exception as e:
                #     print(red(f"exception: parse_geometry_file: {k_ep_or_g}:{section}:{scene_no}"))
                #     pass
                # src_scene: Scene = scene['src'].primary_scene().in_scene
                # if (
                #     src_scene['k_ed'] != k_ed_src
                #     or src_scene['k_ep'] != k_ep_src
                #     or src_scene['k_ch'] != k_ch_src
                #     or src_scene['no'] != scene_no_src
                # ):
                #     if verbose:
                #         print(yellow(f"not the primary scene: [{k_str}]"))
                #         print(f"{src_scene['k_ed']} vs {k_ed_src}")
                #         print(f"{src_scene['k_ep']} vs {k_ep_src}")
                #         print(f"{src_scene['k_ch']} vs {k_ch_src}")
                #         print(f"{src_scene['no']} vs {scene_no_src}")
                #         pprint(scene)
                #         raise
                #     continue

                properties = config.get(section, k_str)
                try:
                    src_scene['geometry'] = get_geometry_from_properties(properties)
                except:
                    # 2025-08-29 disable info to avoid too many messages
                    # print(red(f"failed getting geometry or assign to src scene: {scene_no_src}"))
                    pass

        for scene in ch_video['scenes']:
            if 'geometry' not in scene:
                scene['geometry'] = SceneGeometry(use_default=True)

        if 'geometry' not in ch_video:
            ch_video['geometry'] = ChapterGeometry()

    if verbose and k_ep_or_g == 'g_doc':
        pprint(ch_video)
        raise


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
            crop = list(map(int, value.split(':')))
            geometry.crop = list([max(0, v) for v in crop])
            geometry.defined = True

        # Inner rect detection
        elif property_name == 'detection_params':
            # threshold_min, morph_kernel_radius, erode_kernel_radius, erode_iterations
            if value != "default":
                values = value.split(':')
                geometry.detection_params.threshold_min = int(values[0])
                geometry.detection_params.morph_kernel = int(values[1])
                geometry.detection_params.erode_kernel = int(values[2])
                geometry.detection_params.erode_iterations = int(values[3])
            # else:
            #     print(yellow(f"use default detection params"))

        elif property_name == 'autocrop':
            # crop: x0, y0, x1, y1
            geometry.autocrop = list(map(int, value.split(':')))

        elif property_name == 'use_autocrop':
            geometry.use_autocrop = bool(value == 'true')

        elif property_name == 'default':
            # Use a global default crop value
            geometry.use_default = bool(value == 'true')

        elif property_name == 'detection_params':
            geometry.custom_detection_params = not bool(value == 'default')

    return geometry





