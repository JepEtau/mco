from __future__ import annotations
import configparser
from dataclasses import dataclass, field
import os
from pprint import pprint
from PySide6.QtWidgets import QGraphicsEllipseItem
import re
from typing import Literal, TYPE_CHECKING, Self

from utils.p_print import *
from utils.path_utils import absolute_path
from ._db import db
from ._keys import all_chapter_keys
from .scenes import get_scene_from_frame_no
from .filters import parser_strip

if TYPE_CHECKING:
    from utils.mco_types import Scene


MaskShape = Literal['circle', 'ellipse', 'oblong']


@dataclass(slots=True)
class DsrRegion:
    shape: MaskShape
    # x, y, theta
    center: list[float | int, float | int]
    # w, h
    axes: list[float | int, float | int]
    # in radian
    angle: float
    # Used by editor
    item: QGraphicsEllipseItem | None = None

    def get(self, size: list[float, float] | None = None) -> Self:
        if size is None:
            return DsrRegion(self.shape, self.center, self.axes, self.angle)

        w, h = size
        return DsrRegion(
            self.shape,
            (int(self.center[0] * w + 0.5), int(self.center[1] * h + 0.5)),
            (int(self.axes[0] * h + 0.5), int(self.axes[1] * h + 0.5)),
            self.angle,
        )



@dataclass
class SceneDsr:
    _frames: dict[int, list[DsrRegion]] = field(default_factory=dict)
    _size: list[float, float] | None = None

    def get(
        self,
        frame_no: int | None = None
    ) -> list[DsrRegion] | dict[int, list[DsrRegion]] | None:
        """Returns a list of frame's patch"""
        if frame_no is None:
            return self.get_all()
        elif frame_no in self._frames:
            return list([p.get(self._size) for p in self._frames[frame_no]])
        return None


    def get_all(self) -> dict[int, list[DsrRegion]] | None:
        """Returns a list of region for each frame of the scene"""
        d: dict[int, list[DsrRegion]] = {}
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
            DsrRegion(
                shape=shape,
                center=coordinates,
                axes=size,
                angle=theta,
            )
        )


    def set_regions(self, frame_no: int, regions: list[DsrRegion]) -> None:
        self._frames[frame_no] = []
        print(lightcyan(f"set_regions: {len(regions)}"))
        for r in regions:
            self._frames[frame_no].append(
                DsrRegion(
                    shape=r.shape,
                    center=r.center,
                    axes=r.axes,
                    angle=r.angle,
                )
            )


    def set_frame_size(self, size: list[int, int] | tuple[int, int]) -> None:
        """Set the shape so that the get function returns absolute coordinates/size"""
        self._size = size



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
        rf"({'|'.join(list(MaskShape.__args__))})\s*=\s*(\d*\.?\d*),(\d*\.?\d*):(\d*\.?\d*),(\d*\.?\d*):(-?\d*\.?\d*)"
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

            if scene['dsr'] is None:
                scene['dsr'] = SceneDsr()
            scene_dsr: SceneDsr = scene['dsr']

            regions: list[str] = (
                config.get(k_section, frame_no_str).split('\n')
            )

            for region_str in regions:
                if verbose:
                    print(f"{frame_no} -> {region_str}")
                if not parser_strip(region_str):
                    continue

                if region := re.search(regex, region_str):
                    scene_dsr.add(
                        frame_no=frame_no,
                        shape=region.group(1),
                        coordinates=(float(region.group(2)), float(region.group(3))),
                        size=(float(region.group(4)), float(region.group(5))),
                        theta=float(region.group(6)),
                    )
                elif verbose:
                    print(yellow("failed:"), region_str)


        # if verbose:
        #     if scene is not None:
        #         scene['dsr'].set_frame_size((720, 576))
        #         pprint(scene['dsr'].get())
        #         pprint(scene)
        #     sys.exit()
