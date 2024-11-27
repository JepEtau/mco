from __future__ import annotations
import configparser
from dataclasses import dataclass, field
import os
from pprint import pprint
import re
import sys
from typing import Literal, TYPE_CHECKING, Self

import numpy as np

from utils.p_print import *
from utils.path_utils import absolute_path
from ._db import db
from ._keys import all_chapter_keys
from .logger import logger
from .scenes import get_scene_from_frame_no
from .filters import parser_strip

if TYPE_CHECKING:
    from utils.mco_types import Scene


MaskShape = Literal['circle', 'ellipse', 'oblong']


@dataclass(slots=True)
class DsrMask:
    shape: MaskShape
    # x, y, theta
    center: np.ndarray[float | int, float | int]
    # w, h
    axes: np.ndarray[float | int, float | int]
    # in radian
    angle: float

    def get(self, size: np.ndarray[float, float]) -> Self:
        return DsrMask(
            self.shape,
            np.round(self.center * size).astype(int),
            np.round(self.axes * size).astype(int),
            self.angle,
        )



@dataclass
class FrameDsr:
    _frames: dict[int, list[DsrMask]] = field(default_factory=dict)
    _size: np.ndarray[float, float] = None

    def get(
        self,
        frame_no: int | None = None
    ) -> list[DsrMask] | dict[int, list[DsrMask]] | None:
        """Returns a list of frame's patch"""
        if frame_no is None:
            return self.get_all()
        elif frame_no in self._frames:
            return list([p.get(self._size) for p in self._frames[frame_no]])
        return None


    def get_all(self) -> dict[int, list[DsrMask]] | None:
        """Returns a list of frame's patch"""
        d: dict[int, list[DsrMask]] = {}
        for frame_no, l in self._frames.items():
            d.update({frame_no: list([p.get(self._size) for p in l])})
        return d


    def add(
        self,
        frame_no: int,
        shape: MaskShape,
        coordinates: list[float, float] | tuple[float, float],
        size: list[float, float] | tuple[float, float],
        theta: float
    ) -> None:
        if not frame_no in self._frames:
            self._frames[frame_no] = []

        self._frames[frame_no].append(
            DsrMask(
                shape=shape,
                center=np.array(coordinates, np.float32),
                axes=np.array(size, np.float32),
                angle=theta,
            )
        )


    def set_frame_size(self, size: list[int, int] | tuple[int, int]) -> None:
        """Set the shape so that the get function returns absolute coordinates/size"""
        self._size = np.array(size, dtype=np.float32)




def parse_dsr_file(k_ep_or_g: str):
    verbose = True
    if verbose:
        print(lightgreen(f"parse_dsr_file: {k_ep_or_g}"))

    # Open configuration file
    filepath = absolute_path(
            os.path.join(
            db['common']['directories']['config'],
            k_ep_or_g,
            f"{k_ep_or_g}_dsr.ini"
        )
    )
    if not os.path.exists(filepath):
        return

    print(f"{'|'.join(list(MaskShape.__args__))}")
    # shape:x:y:w:h:theta
    regex: re.Pattern = re.compile(
        rf"({'|'.join(list(MaskShape.__args__))})=(\d*\.?\d*):(\d*\.?\d*):(\d*\.?\d*):(\d*\.?\d*):(-?\d*\.?\d*)"
    )

    config = configparser.ConfigParser()
    config.read(filepath)
    for k_section in config.sections():
        k_ed, k_ep, k_chapter = k_section.split('.')
        if k_chapter not in all_chapter_keys():
            continue
        if verbose:
            print(f"parse_dsr_file: chapter: {k_chapter}")


        for frame_no_str in config.options(k_section):
            frame_no = int(frame_no_str)

            # Get scene from frame no.
            if verbose:
                print(f"\tsearch {frame_no} in {k_ed}:{k_ep}:{k_chapter}")

            try:
                scene: Scene = get_scene_from_frame_no(
                    frame_no, k_ed=k_ed, k_ep=k_ep, k_chapter=k_chapter
                )
            except:
                if verbose:
                    print(f"warning: parse_replace_configurations: scene not found for frame no. {frame_no} in {k_ed}:{k_ep}:{k_chapter}")
                continue

            if 'dsr' not in scene:
                scene['dsr'] = FrameDsr()
            scene_dsr: FrameDsr = scene['dsr']

            patches: list[str] = parser_strip(
                config.get(k_section, frame_no_str)
            ).split(',')

            for patch_str in patches:
                if verbose:
                    print(f"{frame_no} -> {patch_str}")
                if not patch_str:
                    continue

                if patch := re.search(regex, patch_str):
                    scene_dsr.add(
                        frame_no=frame_no,
                        shape=patch.group(1),
                        coordinates=(float(patch.group(2)), float(patch.group(3))),
                        size=(float(patch.group(4)), float(patch.group(5))),
                        theta=float(patch.group(6)),
                    )

            # scene['dsr'][frame_no] =

        if verbose:
            if scene is not None:
                scene['dsr'].set_frame_size((720, 576))
                pprint(scene['dsr'].get())
                pprint(scene)
            # sys.exit()
