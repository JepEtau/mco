#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
from copy import deepcopy
import os
import os.path
from pathlib import Path
from pathlib import PosixPath
from pprint import pprint
import sys

from utils.common import get_k_part_from_frame_no
from utils.common import get_shot_from_frame_no_new

# n'utilise pas le no. de plan car en cas de modification de la
# liste des plans (ajout ou suppression), il pourrait y avoir des décalages
# le no. de plan est retrouvable par les parsers depuis le no. de trame
# et plus rapide encore lorsque la partie est spécifiée; lors de l'écriture automatique
# par l'éditeur, le no. de trame correspond à la 1ere trame du plan

def parse_replace_configurations(db, k_ep_or_g:str):
    """ Parse configuration file
    It will returns the replaced frame for each frame. This is mainly edited in video
    editor
    """
    # Open configuration file
    filepath = os.path.join(db['common']['directories']['config'], k_ep_or_g, "%s_replace.ini" % (k_ep_or_g))
    if filepath.startswith("~/"):
        filepath = os.path.join(PosixPath(Path.home()), filepath[2:])
    if not os.path.exists(filepath):
        # print("warning: %s does not exists" % (filepath))
        return

    # Parse the file
    config = configparser.ConfigParser()
    config.read(filepath)
    # print("%s.parse_replace_configurations" % (__name__))
    for k_section in config.sections():
        # print("\tk_section:%s" % (k_section))
        if '.' not in k_section:
            sys.exit("parse_replace_configurations: error, no edition,ep,part specified")
        k_ed, k_ep, k_part = k_section.split('.')

        for frame_no_str in config.options(k_section):
            frame_no = int(frame_no_str)
            new_frame_no = int(config.get(k_section, frame_no_str).strip())
            k_part = get_k_part_from_frame_no(db, k_ed, k_ep, frame_no)
            if k_part == '':
                # print("parse_replace_configurations: part not found for frame %d in %s:%s" % (frame_no, k_ed, k_ep))
                continue

            # print("\t%s:%s:%s frame no. %d replaced by %d" % (k_ed, k_ep, k_part, frame_no, new_frame_no))
            shot = get_shot_from_frame_no_new(db, frame_no=frame_no, k_ed=k_ed, k_ep=k_ep, k_part=k_part)
            if shot is None:
                sys.exit("parse_replace_configurations: error, shot not found for frame no. %d in %s:%s:%s" % (
                    frame_no, k_ed, k_ep, k_part))
            shot['replace'][frame_no] = new_frame_no
            # print("->")
            # pprint(shot)


def get_replaced_frames(db, k_ep, k_part) -> dict:
    """ Returns a dict of frames to replace
    """
    replace = dict()

    # Get the list of editions and episode that are used by this ep/part
    if k_part in ['g_debut', 'g_fin']:
        db_video = db[k_part]['common']['video']
    else:
        print("%s.get_replaced_frames: %s:%s" % (__name__, k_ep, k_part))
        k_ed_src = db[k_ep]['common']['video']['reference']['k_ed']
        k_ep_src = k_ep
        db_video = db[k_ep_src][k_ed_src][k_part]['video']
        print("%s.get_replaced_frames: src=%s:%s:%s" % (__name__, k_ed_src, k_ep_src, k_part))

    for shot in db_video['shots']:
        # print(shot)
        if ('src' not in shot.keys()
            or ('use' in shot['src'].keys()
            and not shot['src']['use'])):
            shot_src = shot
        else:
            if 'k_ed' in shot['src'].keys():
                k_ed_src = shot['src']['k_ed']
            k_ep_src = shot['src']['k_ep']
            k_part_src = get_k_part_from_frame_no(db, k_ed_src, k_ep_src, shot['src']['start'])
            shot_src = get_shot_from_frame_no_new(db, frame_no=shot['src']['start'], k_ed=k_ed_src, k_ep=k_ep_src, k_part=k_part_src)

        # pprint(shot_src)
        if len(shot_src['replace'].keys()) > 0:
            if k_ed_src not in replace.keys():
                replace[k_ed_src] = dict()
            if k_ep_src not in replace[k_ed_src].keys():
                replace[k_ed_src][k_ep_src] = dict()
            if k_part not in replace[k_ed_src][k_ep_src].keys():
                replace[k_ed_src][k_ep_src][k_part] = dict()

            replace[k_ed_src][k_ep_src][k_part].update(shot_src['replace'])


    return replace
