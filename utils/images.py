from __future__ import annotations
from dataclasses import dataclass
import os
from pprint import pprint
import sys

from utils.mco_types import SrcScene
from .mco_utils import get_cache_path, get_dirname
from .p_print import *
from parsers import db

from typing import TYPE_CHECKING, Iterator
if TYPE_CHECKING:
    from utils.mco_types import Scene


IMG_FILENAME_TEMPLATE = "%s_%%05d__%s__%02d%s.png"



@dataclass
class Image:
    no: int
    in_fp: str
    out_fp: str

    # def __str__(self) -> str:
    #     return f"  Image(\n    no={self.no}\n    in={self.in_fp}\n    out={self.out_fp}\n  )"


class Images:
    def __init__(self, scene: Scene) -> None:
        self._images: list[Image]
        # directory: str = os.path.join(scene['cache'], dirname)
        self._scene = scene

        in_dirname, in_hashcode = get_dirname(scene, False)
        in_filename_template = IMG_FILENAME_TEMPLATE % (
            scene['k_ep'],
            scene['k_ed'],
            int(in_dirname[:2]),
            f"_{in_hashcode}" if in_hashcode != '' else ""
        )

        out_dirname, out_hashcode = get_dirname(scene, True)
        out_filename_template = IMG_FILENAME_TEMPLATE % (
            scene['k_ep'],
            scene['k_ed'],
            int(out_dirname[:2]),
            f"_{out_hashcode}" if out_hashcode != '' else ""
        )
        print(red(f"Images: {in_dirname} -> {out_dirname}"))

        _src_scene: SrcScene = (
            db[scene['src']['k_ep']]
            ['video']
            [scene['src']['k_ed']]
            [scene['src']['k_ch']]
            ['scenes']
            [scene['src']['no']]
        )

        frame_replace: dict[int, int] = {}
        if scene['task'].name != 'initial':
            frame_replace = _src_scene['replace']
        # if replace:
        #     imgs: list[str] = []
        #     for no in range(scene['start'], scene['start'] + scene['count']):
        #         out_no: int = frame_replace[no] if no in frame_replace else no
        #         imgs.append(os.path.join(directory, filename_template % (out_no)))
        #     return imgs
        in_base: str = scene['cache']
        out_base: str = scene['cache']
        if scene['k_ch'] in ('g_asuivre', 'g_documentaire'):
            in_base = get_cache_path(scene)
            in_dirname = get_dirname(scene)[0]
            if scene['task'].name == 'hr':
                out_base= get_cache_path(scene, out=True)
            else:
                out_base= get_cache_path(scene)
            out_dirname = get_dirname(scene, out=True)[0]

        if 'segments' in scene['src']:
            start = scene['src']['segments'][0]['start']
        else:
            start = scene['src']['start']

        count = scene['dst']['count']

        self._images = list([
            Image(
                no=no,
                in_fp=os.path.join(in_base, in_dirname, in_filename_template % (no)),
                out_fp=os.path.join(out_base, out_dirname, out_filename_template % (no))
            )

            for no in range(start, start + count)
            if no not in frame_replace
        ])

    def __len__(self) -> int:
        return len(self._images)


    def __str__(self) -> str:
        repr: str = f"\'images\': {self.__class__.__name__}=[\n"
        repr += ",\n".join([str(img) for img in self._images])
        repr += "\n]"
        return repr


    def images(self) -> list[Image]:
        return self._images


    def out_images(self) -> list[str]:
        return list([i.out_fp for i in self._images])


    def in_images(self) -> list[str]:
        return list([i.in_fp for i in self._images])


    def out_frames(self) -> list[str]:
        """Returns a list of filepath"""
        return self._scene['out_frames']

    #     scene = self._scene
    #     if scene['k_ch'] in ('g_asuivre', 'g_documentaire'):
    #         in_base = get_cache_path(scene)
    #         in_dirname = get_dirname(scene)[0]
    #         if scene['task'].name == 'hr':
    #             out_base= get_cache_path(scene, out=True)
    #         else:
    #             out_base= get_cache_path(scene)
    #         out_dirname = get_dirname(scene, out=True)[0]

    #     if scene['task'].name == 'hr':
    #         Image(
    #             no=no,
    #             in_fp=os.path.join(in_base, in_dirname, in_filename_template % (no)),
    #             out_fp=os.path.join(out_base, out_dirname, out_filename_template % (no))
    #         )

    #         for no in range(scene['start'], scene['start'] + scene['count'])
    #         if no not in frame_replace

