# -*- coding: utf-8 -*-
import sys

import configparser
import os
import os.path
from pathlib import (
    Path,
    PosixPath,
)
from pprint import pprint

from shot.utils import get_shot_from_frame_no
from utils.nested_dict import nested_dict_set
from utils.pretty_print import *


def parse_replace_configurations(db, k_ep_or_g:str):
    """ Parse configuration file
    It will returns the replaced frame for each frame. This is mainly edited in video
    editor
    """
    verbose = False

    if verbose:
        print_lightgreen("parse_replace_configurations: %s" % (k_ep_or_g))

    # Open configuration file
    filepath = os.path.join(db['common']['directories']['config'], k_ep_or_g, "%s_replace.ini" % (k_ep_or_g))
    if filepath.startswith("~/"):
        filepath = os.path.join(PosixPath(Path.home()), filepath[2:])
    if not os.path.exists(filepath):
        # print("warning: %s does not exist" % (filepath))
        return

    # Parse the file
    config = configparser.ConfigParser()
    config.read(filepath)
    for k_section in config.sections():
        if verbose:
            print_lightblue("\tk_section:%s" % (k_section))
        if '.' not in k_section:
            sys.exit("parse_replace_configurations: error, no edition,ep,part specified")
        k_ed, k_ep, k_part = k_section.split('.')

        for frame_no_str in config.options(k_section):
            frame_no = int(frame_no_str)
            new_frame_no = int(config.get(k_section, frame_no_str).strip())

            # Get shot from frame no.
            if verbose:
                print("\tsearch %d in %s:%s:%s" % (frame_no, k_ed, k_ep, k_part))

            try:
                shot = get_shot_from_frame_no(db, frame_no, k_ed=k_ed, k_ep=k_ep, k_part=k_part)
            except:
                if verbose:
                    print("warning: parse_replace_configurations: shot not found for frame no. %d in %s:%s:%s" % (
                        frame_no, k_ed, k_ep, k_part))
                shot = None

            if shot is not None:
                try:
                    shot['replace'][frame_no] = new_frame_no
                except:
                    shot['replace'] = {frame_no: new_frame_no}

                # TODO verify circular definition
                replace_list = list(shot['replace'].keys())
                for v in shot['replace'].values():
                    if v in replace_list:
                        sys.exit("error: circular reference: frame no. %d in %s:%s:%s" % (v, k_ed, k_ep, k_part))

        if verbose:
            if shot is not None:
                pprint(shot['replace'])
            sys.exit



def get_replaced_frames(db, k_ep, k_part) -> dict:
    """ Returns a dict of frames to replace
    """
    verbose = False
    if verbose:
        print_lightgreen(f"get_replaced_frames: {k_ep}:{k_part}")
    replace = dict()

    # Get the list of editions and episode that are used by this ep/part
    if k_part in ['g_debut', 'g_fin']:
        db_video = db[k_part]['video']
        if verbose:
            pprint(db_video)
            # pprint(db['ep11']['video']['s'])
    else:
        db_video = db[k_ep]['video']['target'][k_part]

    # For each shot in the target, get the src shot
    for shot in db_video['shots']:
        # TODO clean because src is also the same as the root k_ed/k_ep/k_part
        k_ed_src = shot['src']['k_ed']
        k_ep_src = shot['src']['k_ep']
        k_part_src = shot['src']['k_part']
        shot_no_src = shot['src']['no']
        shot_src = db[k_ep_src]['video'][k_ed_src][k_part_src]['shots'][shot_no_src]

        if 'replace' in shot_src.keys() and len(shot_src['replace'].keys()) > 0:
            try:
                replace[k_ed_src][k_ep_src][k_part].update(shot_src['replace'])
            except:
                nested_dict_set(replace, shot_src['replace'], k_ed_src, k_ep_src, k_part)

    if verbose:
        print("get_replaced_frames: %s:%s" % (k_ep, k_part))
        pprint(replace)
    return replace
