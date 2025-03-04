from configparser import ConfigParser
import os
import os.path
from pprint import pprint
import re

from utils.path_utils import absolute_path
from utils.p_print import *
from ._db import db
from .effects import (
    Effects,
    Effect,
)
from ._keys import (
    Chapter,
    credit_chapter_keys,
)
from .scenes import get_scene_from_frame_no

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from utils.mco_types import Scene
from scene.src_scene import SrcScene



def parse_loop_file(k_ep: str, k_ch: Chapter = "", verbose: bool = False) -> None:
    """ a loop is defined by frame no.
        number of loop excluding the frame ref no.
    """


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
                if verbose:
                    print(yellow(
                        f"[W] {os.path.basename(filepath)}: missing frame no."
                    ))
                    print(f"  {scene_no} -> {scene_no}_{f_no}")


            # Get scene_no from frame_no
            src_scene: Scene = get_scene_from_frame_no(
                f_no, k_ed=k_ed, k_ep=k_ep, k_ch=k_ch
            )
            if src_scene is None:
                # print(yellow(f"[W] parse_loop_file: scene not found for frame no. {f_no} in {k_ed}:{k_ep}:{k_ch}"))
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

                # no start, start from the begin of the scene
                # 040_08279 = :23:8302
                start = (
                    src_scene['start']
                    + (int(result.group(1)) if result.group(1) else 0)
                )

                # no start, no count -> full
                if not result.group(1) and not result.group(2):
                    # 143_18005 = ::
                    loop = src_scene['count']

                # from index to end of the scene
                elif result.group(1) and not result.group(2):
                    # 146_18125 = 36::18161
                    loop = src_scene['count'] - int(result.group(1))

                # +1 here because the second corresponds to the end frame INDEX
                elif not result.group(1) and result.group(2):
                    loop = int(result.group(2)) + 1

                # start and end specified
                elif result.group(1) and result.group(2):
                    # 52:78:5516
                    loop = int(result.group(2)) - int(result.group(1)) + 1

                # if not specified, use the frame in the middle
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





def get_loop_nframes(src_scene: SrcScene, f_no: int) -> int:
    """Returns the number of loops, frame ref included"""
    loop: int = 0

    in_scene: Scene = src_scene.in_scene
    if 'effects' not in in_scene:
        return loop

    e: Effect
    for e in in_scene['effects'].get_effects('replace_by_loop'):
        if f_no == e.f_ref:
            loop = e.loop
            # decrease loop if start of src is higher than start of loop
            if src_scene.start > e.start:
                loop -= src_scene.start - e.start
                raise ValueError(red("validate loop start < src start"))

            # decrease loop if end of src is lower than end of loop
            elif (e.start + e.loop)  > (src_scene.start + src_scene.count):
                loop -= (
                    (e.start + e.loop)
                    - (src_scene.start + src_scene.count)
                )
                print(lightcyan("-------------------------------"))
                pprint(e)
                pprint(src_scene)
                raise ValueError(red("validate loop (start+loop) is > end of source"))

    return loop
