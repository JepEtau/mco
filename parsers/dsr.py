from __future__ import annotations
import configparser
from dataclasses import dataclass, field
from hashlib import md5
import json
import os
from pprint import pprint
from PySide6.QtWidgets import QGraphicsEllipseItem
import re
from typing import Literal, TYPE_CHECKING, Self

from .hash import calc_hash
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
    # When a patch is for multiple frames
    start: int = -1
    end: int = -1
    # Used by editor
    item: QGraphicsEllipseItem | None = None

    def get(self, size: list[float, float] | None = None) -> Self:
        if size is None:
            return DsrRegion(
                self.shape, self.center, self.axes, self.angle, self.start, self.end,
            )

        w, h = size
        return DsrRegion(
            self.shape,
            (int(self.center[0] * w + 0.5), int(self.center[1] * h + 0.5)),
            (int(self.axes[0] * w + 0.5), int(self.axes[1] * h + 0.5)),
            self.angle,
            self.start,
            self.end,
        )

    def hash(self):
        dsr_str = ":".join([
            self.shape,
            ",".join(map(str, self.center)),
            ",".join(map(str, self.axes)),
            f"{self.angle}",
        ])
        return md5(dsr_str.encode('utf-8')).hexdigest()[:7]



@dataclass
class SceneDsr:
    _frames: dict[int, list[DsrRegion]] = field(default_factory=dict)
    _size: list[float, float] | None = None

    def get(
        self,
        frame_no: int | None = None
    ) -> list[DsrRegion] | dict[int, list[DsrRegion]] | None:
        """Returns a list of frame's patch
        if frame_no is None, returns all patches
        """
        patches: list = []
        if frame_no is None:
            patches = self.get_all()

        elif frame_no in self._frames:
            patches = list([p.get(self._size) for p in self._frames[frame_no]])

        # frames sharing the same patch
        if -1 in self._frames.keys():
            for p in self._frames[-1]:
                if p.start <= frame_no <= p.end:
                    patches.append(p)

        return patches if patches else None


    def has_patches(self) -> bool:
        return bool(len(self._frames.keys()) > 0)


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
        theta: float,
        start: int = -1,
        end: int = -1,
    ) -> None:
        if not frame_no in self._frames:
            self._frames[frame_no] = []

        self._frames[frame_no].append(
            DsrRegion(
                shape=shape,
                center=coordinates,
                axes=size,
                angle=theta,
                start=start,
                end=end,
            )
        )


    def set_regions(
        self,
        frame_no: int,
        regions: list[DsrRegion],
        start: int = -1,
        end: int = -1,
    ) -> None:
        self._frames[frame_no] = []
        print(lightcyan(f"set_regions: count={len(regions)}"))

        # Remove deleted shared patches
        if -1 in self._frames.keys():
            # This frame has shared patches
            print("shared patches:")
            pprint(self._frames[-1])
            to_remove: list[int] = []
            for i, p in enumerate(self._frames[-1]):
                if p.start <= frame_no <= p.end:
                    # this frame should contain this shared patch
                    # if not, it has been removed
                    found: bool = False
                    for r in regions:
                        if r == p:
                            print(yellow(f"found"))
                            found = True
                            # remove the patch from the frame patches
                            # because it is contained in the shared patches
                            regions.remove(r)
                            break
                    if not found:
                        # this shared patch has been removed
                        to_remove.append(i)

            if to_remove:
                print(f"remove items: {to_remove}")
                for i in sorted(to_remove, reverse=True):
                    del self._frames[-1][i]

        print(blue("new regions to set:"))
        print(regions)
        for r in regions:
            _f_no = frame_no

            # shared patch
            if r.start != -1 and r.end != -1:
                _f_no = -1
                if -1 not in self._frames.keys():
                    self._frames[_f_no] = []

            # Append to frame dsr list or shared list
            self._frames[_f_no].append(
                DsrRegion(
                    shape=r.shape,
                    center=r.center,
                    axes=r.axes,
                    angle=r.angle,
                    start=r.start,
                    end=r.end,
                )
            )


    def set_frame_size(self, size: list[int, int] | tuple[int, int]) -> None:
        """Set the shape so that the get function returns absolute coordinates/size"""
        self._size = size


    def hash(self) -> str:
        regions_str_list: list[str] = []
        for frame_no, dsr_regions in self._frames.items():
            regions_str_list.append(":".join(d.hash() for d in dsr_regions))
        regions_str = ";".join(regions_str_list)
        return calc_hash(regions_str)



def parse_dsr_file(k_ep_or_g: str, verbose: bool = False):
    if verbose:
        print(lightgrey(f"parse_dsr_file: {k_ep_or_g}"))

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

    if verbose:
        print(f"  {'|'.join(list(MaskShape.__args__))}")
    # shape:x:y:w:h:theta
    regex: re.Pattern = re.compile(
        rf"({'|'.join(list(MaskShape.__args__))})\s*=\s*(\d*\.?\d*),(\d*\.?\d*):(\d*\.?\d*),(\d*\.?\d*):(-?\d*\.?\d*)"
    )
    # shape:x:y:w:h:theta:start:end
    regex_multiple: re.Pattern = re.compile(
        rf"({'|'.join(list(MaskShape.__args__))})\s*=\s*(\d*\.?\d*),(\d*\.?\d*):(\d*\.?\d*),(\d*\.?\d*):(-?\d*\.?\d*):(\d+):(\d+)"
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
            if "_" in frame_no_str:
                # Patch for a multiple frames
                _frame_no_str, _ = frame_no_str.split("_")
                frame_no = int(_frame_no_str)

                # frame_no is the first frame of the cene,
                # Get scene from frame no.
                if verbose:
                    print(f"\tsearch {frame_no} in {k_ed}:{k_ep}:{k_chapter}")

                scene: Scene = get_scene_from_frame_no(
                    frame_no, k_ed=k_ed, k_ep=k_ep, k_ch=k_chapter
                )
                if scene is None:
                    continue
                if scene['dsr'] is None:
                    scene['dsr'] = SceneDsr()
                scene_dsr: SceneDsr = scene['dsr']

                # Get all patches
                patches: list[str] = (
                    config.get(k_section, frame_no_str).split('\n')
                )

                for patch_str in patches:
                    if not parser_strip(patch_str):
                        continue

                    if region := re.search(regex_multiple, patch_str):
                        # use frame_no as -1 to indicates that i's a patch to add
                        # to multiple frames
                        scene_dsr.add(
                            frame_no=-1,
                            shape=region.group(1),
                            coordinates=(float(region.group(2)), float(region.group(3))),
                            size=(float(region.group(4)), float(region.group(5))),
                            theta=float(region.group(6)),
                            start=int(region.group(7)),
                            end=int(region.group(8)),
                        )
                print(red("detected muliple frames sharing the same shape"))
                pprint(scene_dsr.get_all())

            else:
                # Patch for a single frame
                frame_no = int(frame_no_str)

                # Get scene from frame no.
                if verbose:
                    print(f"\tsearch {frame_no} in {k_ed}:{k_ep}:{k_chapter}")

                scene: Scene = get_scene_from_frame_no(
                    frame_no, k_ed=k_ed, k_ep=k_ep, k_ch=k_chapter
                )
                if scene is None:
                    continue

                if scene['dsr'] is None:
                    scene['dsr'] = SceneDsr()
                scene_dsr: SceneDsr = scene['dsr']

                patches: list[str] = (
                    config.get(k_section, frame_no_str).split('\n')
                )

                for patch_str in patches:
                    if verbose:
                        print(f"{frame_no} -> {patch_str}")
                    if not parser_strip(patch_str):
                        continue

                    if region := re.search(regex, patch_str):
                        scene_dsr.add(
                            frame_no=frame_no,
                            shape=region.group(1),
                            coordinates=(float(region.group(2)), float(region.group(3))),
                            size=(float(region.group(4)), float(region.group(5))),
                            theta=float(region.group(6)),
                        )
                    elif verbose:
                        print(yellow("failed:"), patch_str)


        # if verbose:
        #     if scene is not None:
        #         scene['dsr'].set_frame_size((720, 576))
        #         pprint(scene['dsr'].get())
        #         pprint(scene)
        #     sys.exit()
