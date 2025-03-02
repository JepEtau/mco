from configparser import ConfigParser
import os
import os.path
from pathlib import (
    Path,
    PosixPath,
)
from pprint import pprint
from warnings import warn

from .scenes import get_scene_from_frame_no
from .helpers import nested_dict_set
from utils.p_print import *
from ._db import db
from ._keys import Chapter, ep_no

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from utils.mco_types import Scene


def replace_scene_bounds_(k_ep: str) -> None:
    print(yellow("replace_scene_bounds_"), k_ep)
    # edition 'j' only
    k_ed: str = 'j'
    k_chapter: Chapter = 'episode'
    if 'scenes' not in db[k_ep]['video'][k_ed][k_chapter]:
        print(red(f"no scenes for {k_ed}:{k_ep}:{k_chapter}"))
        return
    try:
        scenes: list[Scene] = db[k_ep]['video'][k_ed][k_chapter]['scenes']
    except:
        print(f"no scenes for {k_ed}:{k_ep}:{k_chapter}")
        raise

    for scene in scenes:
        sr = scene['replace']
        # first frame to be replaced by the following
        frame_no = scene['start']
        new_frame_no = frame_no + 1
        if frame_no in sr:
            print(yellow(f"{k_ep}:{scene['no']} (start) already in replace list {frame_no} <- {sr[frame_no]}"))
            if sr[frame_no] != new_frame_no:
                print(red("  different"))

        # Do not replace if already in src or used as the src
        if frame_no not in sr.keys() and frame_no not in sr.values():
            sr[frame_no] = new_frame_no

        elif new_frame_no in sr and sr[new_frame_no] == frame_no:
            print(darkgrey(f"[I] (start) {frame_no} is used as ref, ignore:"), sr)
            pass

        else:
            print("unknow error")
            # print(f"{scene['no']:03d} (first): won't replace {frame_no} because better than following")
            pprint(sr)
            raise

        # last frame to be replaced by the previous one
        frame_no = scene['start'] + scene['count'] - 1
        new_frame_no = frame_no - 1
        if frame_no in sr:
            print(yellow(f"{k_ep}:{scene['no']} (end) already in replace list {frame_no} <- {sr[frame_no]}"))
            if sr[frame_no] != new_frame_no:
                print(red("  different"))
        # Do not replace if used as the src
        if frame_no not in sr.keys() and frame_no not in sr.values():
            sr[frame_no] = new_frame_no

        elif new_frame_no in sr and sr[new_frame_no] == frame_no:
            print(darkgrey(f"[I] (end) {frame_no} is used as ref, ignore:"), sr)
            pass

        else:
            # Should never happen
            print("unknow error")
            # print(f"{scene['no']:03d} (last): won't replace {frame_no} because better than previous")
            pprint(sr)
            raise

        # Detect circular reference:
        #   consolidate if a frame is pointing to a frame already replaced
        consolidate = True
        t = 0
        while consolidate:
            t += 1
            consolidate: bool = False
            replace_list = list(scene['replace'].keys())
            for k, v in scene['replace'].items():
                if v in replace_list:
                    warn(yellow(f"replacing by a replaced frame. No. {frame_no} in {k_ed}:{k_ep}:{k_chapter}"))
                    scene['replace'][k] = scene['replace'][v]
                    consolidate = True
                    break
            if t > len(replace_list):
                raise(red(f" circular reference"))

        if scene['no'] == 5:
            print(lightcyan("scene no."), scene['no'])
            pprint(scene['replace'])


def parse_replace_file(k_ep_or_g:str) -> None:
    """ Parse configuration file
    It will returns the replaced frame for each frame. This is mainly edited in video
    editor
    """
    verbose = False

    if verbose:
        print(lightgreen(f"parse_replace_file: {k_ep_or_g}"))


    # Open configuration file
    filepath: str = os.path.join(
        db['common']['directories']['config'],
        k_ep_or_g,
        f"{k_ep_or_g}_replace.ini"
    )
    if filepath.startswith("~/"):
        filepath = os.path.join(PosixPath(Path.home()), filepath[2:])
    if not os.path.exists(filepath):
        # print(f"warning: {filepath} does not exist, ignore")
        return

    # Parse the file
    config = ConfigParser()
    config.read(filepath)
    for k_section in config.sections():
        if verbose:
            print(blue(f"\tk_section:{k_section}"))
        if '.' not in k_section:
            raise ValueError("parse_replace_file: error, no edition,ep,chapter specified")
        k_ed, k_ep, k_chapter = k_section.split('.')

        for frame_no_str in config.options(k_section):
            frame_no = int(frame_no_str)
            new_frame_no = int(config.get(k_section, frame_no_str).strip())

            # Get scene from frame no.
            if verbose:
                print(f"\tsearch {frame_no} in {k_ed}:{k_ep}:{k_chapter} -> scene no.", end="")

            scene: Scene = get_scene_from_frame_no(
                frame_no, k_ed=k_ed, k_ep=k_ep, k_ch=k_chapter
            )
            if scene is None:
                continue

            if 'replace' not in scene:
                scene['replace'] = {}
            scene['replace'][frame_no] = new_frame_no

            # Detect circular reference:
            #   consolidate if a frame is pointing to a frame already replaced
            consolidate = True
            t = 0
            while consolidate:
                t += 1
                consolidate: bool = False
                replace_list = list(scene['replace'].keys())
                for k, v in scene['replace'].items():
                    if v in replace_list:
                        warn(yellow(f"replacing by a replaced frame. No. {frame_no} in {k_ed}:{k_ep}:{k_chapter}"))
                        scene['replace'][k] = scene['replace'][v]
                        consolidate = True
                        break
                if t > len(replace_list):
                    raise(red(f" circular reference"))

        if verbose:
            if k_ed == "j" and k_chapter == 'episode':
                scenes: list[Scene] = db[k_ep]['video'][k_ed][k_chapter]['scenes']
                for s in scenes:
                    pprint(s["replace"])

        if (
            not k_ep_or_g.startswith("g_")
            and k_ed == 'j'
            and ep_no(k_ep) < 40
        ):
            replace_scene_bounds_(k_ep=k_ep_or_g)



def get_replaced_frames(db, k_ep, k_chapter) -> dict:
    """ Returns a dict of frames to replace
    """
    verbose = False
    if verbose:
        print(lightgreen(f"get_replaced_frames: {k_ep}:{k_chapter}"))
    replace = dict()

    # Get the list of editions and episode that are used by this ep/chapter
    if k_chapter in ('g_debut', 'g_fin'):
        db_video = db[k_chapter]['video']
        if verbose:
            pprint(db_video)
            # pprint(db['ep11']['video']['s'])
    else:
        db_video = db[k_ep]['video']['target'][k_chapter]

    # For each scene in the target, get the src scene
    for scene in db_video['scenes']:
        # TODO clean because src is also the same as the root k_ed/k_ep/k_chapter
        src_scene = scene['src']

        k_ed_src = src_scene['k_ed']
        k_ep_src = src_scene['k_ep']
        k_chapter_src = src_scene['k_ch']
        scene_no_src = src_scene['no']
        scene_src = db[k_ep_src]['video'][k_ed_src][k_chapter_src]['scenes'][scene_no_src]

        if 'replace' in scene_src.keys() and len(scene_src['replace'].keys()) > 0:
            try:
                replace[k_ed_src][k_ep_src][k_chapter].update(scene_src['replace'])
            except:
                nested_dict_set(
                    replace, scene_src['replace'], k_ed_src, k_ep_src, k_chapter
                )

    if verbose:
        print("get_replaced_frames: %s:%s" % (k_ep, k_chapter))
        pprint(replace)
    return replace
