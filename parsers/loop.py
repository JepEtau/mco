from configparser import ConfigParser
import os
import os.path
from pprint import pprint
import re

from utils.mco_types import ChapterVideo
from utils.path_utils import absolute_path
from utils.p_print import *
from ._db import db
from .effects import (
    Effects,
    Effect,
    EffectName,
)
from ._helpers import get_chapter_video
from ._keys import (
    Chapter,
    credit_chapter_keys,
    ep_no,
)
from .scenes import get_scene_from_frame_no

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from utils.mco_types import Scene



def parse_loop_file(k_ep: str, k_ch: Chapter = "", verbose: bool = False) -> None:
    if verbose:
        print(darkgrey(f"[I] {k_ep}:{k_ch}: parse_loop_file"))

    # Open configuration file
    k_ep_or_g: str = k_ch if k_ch in credit_chapter_keys() else k_ep
    filepath = absolute_path(
            os.path.join(
            db['common']['directories']['config'],
            k_ep_or_g,
            f"{k_ep_or_g}_loop.ini"
        )
    )
    if not os.path.exists(filepath):
        if verbose:
            print(f"[I] Loop configuration not found: {filepath}")
        return

    # Parse the file
    config = ConfigParser()
    config.read(filepath)
    for k_section in config.sections():
        if '.' not in k_section:
            raise ValueError("parse_loop_file: error, no edition,ep,chapter specified")
        k_ed, k_ep, k_ch = k_section.split('.')

        for option in config.options(k_section):

            # Get src scene and start frame_no
            try:
                scene_no, f_no = map(int, option.split("_"))
            except:
                scene_no = int(option.split("_")[0])
                src_scene: Scene = db[k_ep]['video'][k_ed][k_ch]['scenes'][scene_no]
                f_no = src_scene['start']
                print(yellow(
                    f"[W] {os.path.basename(filepath)}: missing frame no."
                ))
                print(f"  {scene_no} -> {scene_no}_{f_no}")


            # Get scene_no from frame_no
            src_scene: Scene = get_scene_from_frame_no(
                f_no, k_ed=k_ed, k_ep=k_ep, k_ch=k_ch
            )
            if src_scene is None:
                print(yellow(f"[W] parse_loop_file: scene not found for frame no. {f_no} in {k_ed}:{k_ep}:{k_ch}"))
                continue

            # verify that scene no. didn't change
            if src_scene['start'] != f_no:
                print(yellow(f"[W] {k_ed}:{k_ep}:{k_ch}:{src_scene['no']}, wrong start f_no: {f_no}, must be {src_scene['start']}"))

            # Get loops
            loop_array: str = (
                config.get(k_section, option)
                .replace(" ", "")
                .replace("\n", "")
                .split(",")
            )
            for loop_str in loop_array:
                result = re.search(re.compile(r"(\d*):(\d*):(\d*)"), loop_str)
                start = (
                    src_scene['start']
                    + (int(result.group(1)) if result.group(1) else 0)
                )
                loop = (
                    int(result.group(2))
                    if result.group(2)
                    else src_scene['count'] - start
                )
                f_ref = (
                    int(result.group(3))
                    if result.group(3)
                    else (src_scene['start'] + (src_scene['count'] // 2))
                )

                if verbose:
                    print(darkgrey(
                        f"[I] {k_ed}:{k_ep}:{k_ch}:{src_scene['no']:03} "
                        + f"{result.groups()} -> {start}, {loop}, {f_ref}"
                    ))


                # Create a loop effect
                if 'effects' not in src_scene:
                    src_scene['effects'] = Effects()

                src_scene['effects'].append(
                    Effect(
                        name='replace_by_loop',
                        start=start,
                        f_ref=f_ref,
                        loop=loop,
                    )
                )

                if verbose:
                    print(darkgrey("[I] Added effect:"))
                    pprint(src_scene)
