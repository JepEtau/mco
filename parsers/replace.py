from configparser import ConfigParser
import os
import os.path
from pathlib import (
    Path,
    PosixPath,
)
from pprint import pprint
import sys

from .scene import get_scene_from_frame_no
from .helpers import nested_dict_set
from utils.p_print import *


def parse_replace_configurations(db, k_ep_or_g:str):
    """ Parse configuration file
    It will returns the replaced frame for each frame. This is mainly edited in video
    editor
    """
    verbose = False

    if verbose:
        print(lightgreen("parse_replace_configurations: %s" % (k_ep_or_g)))

    # Open configuration file
    filepath = os.path.join(db['common']['directories']['config'], k_ep_or_g, "%s_replace.ini" % (k_ep_or_g))
    if filepath.startswith("~/"):
        filepath = os.path.join(PosixPath(Path.home()), filepath[2:])
    if not os.path.exists(filepath):
        # print("warning: %s does not exist" % (filepath))
        return

    # Parse the file
    config = ConfigParser()
    config.read(filepath)
    for k_section in config.sections():
        if verbose:
            print(lightblue("\tk_section:%s" % (k_section)))
        if '.' not in k_section:
            sys.exit("parse_replace_configurations: error, no edition,ep,chapter specified")
        k_ed, k_ep, k_chapter = k_section.split('.')

        for frame_no_str in config.options(k_section):
            frame_no = int(frame_no_str)
            new_frame_no = int(config.get(k_section, frame_no_str).strip())

            # Get scene from frame no.
            if verbose:
                print("\tsearch %d in %s:%s:%s" % (frame_no, k_ed, k_ep, k_chapter))

            try:
                scene = get_scene_from_frame_no(db, frame_no, k_ed=k_ed, k_ep=k_ep, k_chapter=k_chapter)
            except:
                if verbose:
                    print("warning: parse_replace_configurations: scene not found for frame no. %d in %s:%s:%s" % (
                        frame_no, k_ed, k_ep, k_chapter))
                scene = None

            if scene is not None:
                try:
                    scene['replace'][frame_no] = new_frame_no
                except:
                    scene['replace'] = {frame_no: new_frame_no}

                # TODO verify circular definition
                replace_list = list(scene['replace'].keys())
                for v in scene['replace'].values():
                    if v in replace_list:
                        sys.exit("error: circular reference: frame no. %d in %s:%s:%s" % (v, k_ed, k_ep, k_chapter))

        if verbose:
            if scene is not None:
                pprint(scene['replace'])
            sys.exit



def get_replaced_frames(db, k_ep, k_chapter) -> dict:
    """ Returns a dict of frames to replace
    """
    verbose = False
    if verbose:
        print(lightgreen(f"get_replaced_frames: {k_ep}:{k_chapter}"))
    replace = dict()

    # Get the list of editions and episode that are used by this ep/chapter
    if k_chapter in ['g_debut', 'g_fin']:
        db_video = db[k_chapter]['video']
        if verbose:
            pprint(db_video)
            # pprint(db['ep11']['video']['s'])
    else:
        db_video = db[k_ep]['video']['target'][k_chapter]

    # For each scene in the target, get the src scene
    for scene in db_video['scenes']:
        # TODO clean because src is also the same as the root k_ed/k_ep/k_chapter
        k_ed_src = scene['src']['k_ed']
        k_ep_src = scene['src']['k_ep']
        k_chapter_src = scene['src']['k_chapter']
        scene_no_src = scene['src']['no']
        scene_src = db[k_ep_src]['video'][k_ed_src][k_chapter_src]['scenes'][scene_no_src]

        if 'replace' in scene_src.keys() and len(scene_src['replace'].keys()) > 0:
            try:
                replace[k_ed_src][k_ep_src][k_chapter].update(scene_src['replace'])
            except:
                nested_dict_set(replace, scene_src['replace'], k_ed_src, k_ep_src, k_chapter)

    if verbose:
        print("get_replaced_frames: %s:%s" % (k_ep, k_chapter))
        pprint(replace)
    return replace
