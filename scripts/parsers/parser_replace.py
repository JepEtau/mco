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
    get_k_part_from_frame_no,
    get_or_create_src_shot,
    get_shot_from_frame_no_new,
    nested_dict_set,
)

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
    # print("\n%s.parse_replace_configurations" % (__name__))
    for k_section in config.sections():
        # print("\tk_section:%s" % (k_section))
        if '.' not in k_section:
            sys.exit("parse_replace_configurations: error, no edition,ep,part specified")
        k_ed, k_ep, k_part = k_section.split('.')

        for frame_no_str in config.options(k_section):
            frame_no = int(frame_no_str)
            new_frame_no = int(config.get(k_section, frame_no_str).strip())

            # Get shot from frame no.
            print("parse_replace_configurations, find %d in %s:%s:%s" % (frame_no, k_ed, k_ep, k_part))
            # shot = get_shot_from_frame_no_new(db, frame_no, k_ed=k_ed, k_ep=k_ep, k_part=k_part)
            # replaced bya function which creates the src shot if not defined in the config file
            shot = get_or_create_src_shot(db, frame_no, k_ed=k_ed, k_ep=k_ep, k_part=k_part)

            if shot is None:
                sys.exit("parse_replace_configurations: error, shot not found for frame no. %d in %s:%s:%s" % (
                    frame_no, k_ed, k_ep, k_part))
            try:
                shot['replace'][frame_no] = new_frame_no
            except:
                shot['replace'] = {frame_no: new_frame_no}



def get_replaced_frames(db, k_ep, k_part) -> dict:
    """ Returns a dict of frames to replace
    """
    replace = dict()

    # Get the list of editions and episode that are used by this ep/part
    if k_part in ['g_debut', 'g_fin']:
        db_video = db[k_part]['target']['video']
    else:
        k_ed_src = db[k_ep]['target']['video']['src']['k_ed']
        k_ep_src = k_ep
        db_video = db[k_ep_src][k_ed_src][k_part]['video']
        # print("%s.get_replaced_frames: src=%s:%s:%s" % (__name__, k_ed_src, k_ep_src, k_part))

    for shot in db_video['shots']:
        if 'src' in shot.keys() and 'use' in shot['src'] and shot['src']['use']:
            # Use the src shot because this one is replaced
            if 'k_ed' in shot['src'].keys():
                k_ed_src = shot['src']['k_ed']
            k_ep_src = shot['src']['k_ep']
            k_part_src = get_k_part_from_frame_no(db, k_ed_src, k_ep_src, shot['src']['start'])
            shot_src = get_shot_from_frame_no_new(db, frame_no=shot['src']['start'], k_ed=k_ed_src, k_ep=k_ep_src, k_part=k_part_src)
        else:
            shot_src = shot

        if len(shot_src['replace'].keys()) > 0:
            try:
                replace[k_ed_src][k_ep_src][k_part].update(shot_src['replace'])
            except:
                nested_dict_set(replace, shot_src['replace'], k_ed_src, k_ep_src, k_part)


    # print("get_replaced_frames: %s:%s" % (k_ep, k_part))
    # pprint(replace)
    return replace
