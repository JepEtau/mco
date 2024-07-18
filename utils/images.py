from __future__ import annotations
from dataclasses import dataclass
import os
from .mco_utils import get_dirname
from .p_print import *

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

        frame_replace: dict[int, int] = {}
        if scene['task'].name != 'initial':
            frame_replace = scene['replace']
        # if replace:
        #     imgs: list[str] = []
        #     for no in range(scene['start'], scene['start'] + scene['count']):
        #         out_no: int = frame_replace[no] if no in frame_replace else no
        #         imgs.append(os.path.join(directory, filename_template % (out_no)))
        #     return imgs
        self._images = list([
            Image(
                no=no,
                in_fp=os.path.join(scene['cache'], in_dirname, in_filename_template % (no)),
                out_fp=os.path.join(scene['cache'], out_dirname, out_filename_template % (no))
            )

            for no in range(scene['start'], scene['start'] + scene['count'])
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

