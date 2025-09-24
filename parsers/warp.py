from configparser import ConfigParser
from dataclasses import dataclass, field
import os
import os.path
from pathlib import (
    Path,
    PosixPath,
)
from pprint import pprint
from warnings import warn

from .hash import calc_hash
from utils.path_utils import absolute_path

from .scenes import get_scene_from_frame_no
from .helpers import nested_dict_set
from utils.p_print import *
from ._db import db
from ._keys import Chapter, ep_no

from typing import TYPE_CHECKING, Literal
if TYPE_CHECKING:
    from utils.mco_types import Scene



@dataclass
class Warp:
    enabled: bool = False
    matcher: Literal['knn', 'bf'] = 'knn'
    knn_ratio: float = .7
    max_distance_ratio: float = .2
    ref_frame: Literal['previous', 'next'] = 'next'

    def __str__(self) -> str:
        return ", ".join(
            [
                f"enabled={'true' if self.enabled else 'false'}",
                f"matcher={self.matcher}",
                f"knn_ratio={self.knn_ratio:.02f}",
                f"max_distance_ratio={self.max_distance_ratio:.02f}",
                f"ref_frame={self.ref_frame}"
            ]
        )

# @dataclass
# class SceneWarp:
#     _frames: dict[int, Warp] = field(default_factory=dict)
#     _size: list[float, float] | None = None

#     def get(
#         self,
#         frame_no: int | None = None
#     ) -> dict[int, Warp] | None:
#         """Returns a frame's warp params
#         if frame_no is None, returns all warps
#         """
#         warps: list = []
#         if frame_no is None:
#             warps = self.get_all()

#         elif frame_no in self._frames:
#             warps = list([p.get(self._size) for p in self._frames.])

#         return warps if warps else None


#     def has_patches(self) -> bool:
#         return bool(len(self._frames.keys()) > 0)


#     def get_all(self) -> dict[int, list[Warp]] | None:
#         """Returns a list of warp parameters for each frame of the scene"""
#         d: dict[int, list[Warp]] = {}
#         for frame_no, l in self._frames.items():
#             d.update({frame_no: list([p.get(self._size) for p in l])})
#         return d


#     def add(self, frame_no, warp: Warp) -> None:
#         if not frame_no in self._frames:
#             self._frames[frame_no] = warp


#     def set_frame_size(self, size: list[int, int] | tuple[int, int]) -> None:
#         """Set the shape so that the get function returns absolute coordinates/size"""
#         self._size = size


#     def hash(self) -> str:
#         warp_str_list: list[str] = []
#         for frame_no, warp in self._frames.items():
#             parmas_str = ":".join(d.hash() for d in warp)
#             warp_str_list.append(f"{frame_no}={parmas_str}")
#         warp_list_str = ";".join(warp_str_list)
#         return calc_hash(warp_list_str)




def parse_warp_file(k_ep_or_g:str) -> None:
    """ Parse configuration file
    """
    verbose = False

    if verbose:
        print(lightgreen(f"parse_warp_file: {k_ep_or_g}"))


    # Open configuration file
    filepath: str = absolute_path(
            os.path.join(
            db['common']['directories']['config'],
            k_ep_or_g,
            f"{k_ep_or_g}_warp.ini"
        )
    )

    # Parse the file
    config = ConfigParser()
    config.read(filepath)
    for k_section in config.sections():
        if verbose:
            print(blue(f"\tk_section:{k_section}"))
        if '.' not in k_section:
            raise ValueError("parse_warp_file: error, no edition,ep,chapter specified")
        k_ed, k_ep, k_chapter = k_section.split('.')

        for frame_no_str in config.options(k_section):
            frame_no = int(frame_no_str)
            warp = value_to_warp_params(config.get(k_section, frame_no_str).strip())

            # Get scene from frame no.
            if verbose and False:
                print(f"\tsearch {frame_no} in {k_ed}:{k_ep}:{k_chapter} -> scene no.", end="")

            scene: Scene = get_scene_from_frame_no(
                frame_no, k_ed=k_ed, k_ep=k_ep, k_ch=k_chapter
            )
            if scene is None:
                continue

            if 'warp' not in scene:
                scene['warp'] = {}
            scene['warp'][frame_no] = warp
            print(warp)



def value_to_warp_params(properties_str: str) -> Warp:
    warp: Warp = Warp()

    properties = properties_str.strip().replace(' ', '').split(',')
    for property in properties:
        property_array_str: list[str] = property.split('=')
        property_name = property_array_str[0]
        value: str = property_array_str[1]

        if property_name == 'enabled':
            warp.enabled = bool(value == 'true')

        elif property_name == 'matcher':
            warp.matcher = value

        elif property_name == 'knn_ratio':
            warp.knn_ratio = float(value)

        elif property_name == 'max_distance_ratio':
            warp.max_distance_ratio = float(value)

        elif property_name == 'ref_frame':
            warp.ref_frame = value

    return warp



