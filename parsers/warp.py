from configparser import ConfigParser
import os
import os.path
from pathlib import (
    Path,
    PosixPath,
)
from pprint import pprint
from warnings import warn

from utils.path_utils import absolute_path

from .scenes import get_scene_from_frame_no
from .helpers import nested_dict_set
from utils.p_print import *
from ._db import db
from ._keys import Chapter, ep_no

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from utils.mco_types import Scene



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
            # new_frame_no = int(config.get(k_section, frame_no_str).strip())

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
            scene['warp'][frame_no] = ...

        # if verbose:
        #     if not k_ep_or_g.startswith("g_") and k_ed == "j" and k_chapter == 'episode':
        #         scenes: list[Scene] = db[k_ep]['video'][k_ed][k_chapter]['scenes']
        #         for s in scenes:
        #             pprint(s["replace"])


