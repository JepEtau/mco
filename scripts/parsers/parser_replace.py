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

from utils.common import (
    get_src_shot_from_frame_no,
    nested_dict_set,
)
from utils.pretty_print import *

# n'utilise pas le no. de plan car en cas de modification de la
# liste des plans (ajout ou suppression), il pourrait y avoir des décalages
# le no. de plan est retrouvable par les parsers depuis le no. de trame
# et plus rapide encore lorsque la partie est spécifiée; lors de l'écriture automatique
# par l'éditeur, le no. de trame correspond à la 1ere trame du plan

def parse_replace_configurations(db, k_ep_or_g:str, k_ed_only=None):
    """ Parse configuration file
    It will returns the replaced frame for each frame. This is mainly edited in video
    editor
    """
    print_warning = False

    print_lightgreen("parse_replace_configurations: %s:%s" % (k_ed_only, k_ep_or_g))

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
    # print("\n%s.parse_replace_configurations" % (__name__))
    for k_section in config.sections():
        # print("\tk_section:%s" % (k_section))
        if '.' not in k_section:
            sys.exit("parse_replace_configurations: error, no edition,ep,part specified")
        k_ed, k_ep, k_part = k_section.split('.')
        if k_ed_only is not None and k_ed != k_ed_only:
            continue

        for frame_no_str in config.options(k_section):
            frame_no = int(frame_no_str)
            new_frame_no = int(config.get(k_section, frame_no_str).strip())

            # Get shot from frame no.
            # print_green("\tsearch %d in %s:%s:%s" % (frame_no, k_ed, k_ep, k_part))
            try:
                shot = get_src_shot_from_frame_no(db, frame_no, k_ed=k_ed, k_ep=k_ep, k_part=k_part)
            except:
                if not print_warning:
                    print("warning: parse_replace_configurations: shot not found for frame no. %d in %s:%s:%s" % (
                        frame_no, k_ed, k_ep, k_part))
                print_warning = True
                shot = None

            if shot is not None:
                try:
                    shot['replace'][frame_no] = new_frame_no
                except:
                    shot['replace'] = {frame_no: new_frame_no}
            # else:
                # sys.exit("error: parse_replace_configurations: shot not found for frame no. %d in %s:%s:%s" % (
                #     frame_no, k_ed, k_ep, k_part))

            # if k_ed=='s' and k_ep=='ep11' and k_part=='g_fin':
            #     pprint(shot['replace'])

def get_replaced_frames(db, k_ep, k_part) -> dict:
    """ Returns a dict of frames to replace
    """
    # print_lightgreen("%s.get_replaced_frames:  :%s:%s" % (__name__, k_ep, k_part))
    replace = dict()

    # Get the list of editions and episode that are used by this ep/part
    if k_part in ['g_debut', 'g_fin']:
        db_video = db[k_part]['video']
    else:
        db_video = db[k_ep]['video']['target'][k_part]

    # For each shot in the target, get the src shot
    for shot in db_video['shots']:
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

    # print("get_replaced_frames: %s:%s" % (k_ep, k_part))
    # pprint(replace)
    return replace
