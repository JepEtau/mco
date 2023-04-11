# -*- coding: utf-8 -*-
import sys

import re
from pprint import pprint

from utils.common import (
    FPS,
    K_ALL_PARTS,
    K_NON_GENERIQUE_PARTS,
    K_PARTS,
)



def parse_video_section(db_video, config, k_ep, verbose=False):

    k_section = 'video'

    k_ed_ref = None
    k_ed_src = None
    for k_option in config.options(k_section):
        value_str = config.get(k_section, k_option)
        value_str = value_str.replace(' ','')
        # print("%s, %s => [%s]" % (k_section, k_option, value_str))

        if k_option == 'source':
            k_ed_src = value_str
            continue

        if k_option == 'ed_ref':
            k_ed_ref = value_str
            continue

        # Parse only supported sections
        if k_option not in K_PARTS:
            continue
        k_part = k_option

        part_fadein = 0
        part_fadeout = 0
        k_part_ed_src = None
        start = None
        end = -1

        # Walk through values
        properties = value_str.split(',')
        # print("\t%s:%s, properties:," % (k_ep, k_part), properties)
        for property in properties:

            search_start_end = re.search(re.compile("(\d+):(-?\d+)"), property)
            if search_start_end is not None:
                start = int(search_start_end.group(1))
                end = int(search_start_end.group(2))
                continue

            search_fadein = re.search(re.compile("fadein=([0-9.]+)"), property)
            if search_fadein is not None:
                search_fadein = int(float(search_fadein.group(1)) * FPS)
                continue

            search_fadeout = re.search(re.compile("fadeout=([0-9.]+)"), property)
            if search_fadeout is not None:
                part_fadeout = int(float(search_fadeout.group(1)) * FPS)
                continue

            search_k_ed_src = re.search(re.compile("ed=([a-z]+[0-9]*)"), property)
            if search_k_ed_src is not None:
                k_part_ed_src = search_k_ed_src.group(1)
                # sys.exit("found %s for %s:%s" % (k_part_ed_src, k_ep, k_part))
                continue

        # if start is None:
        #     sys.exit("Error: parse_video_section: start and end values are required for %s:%s in target file" % (k_ep, k_part))

        db_video[k_part] = {
            'effects': {
                'fadein': part_fadein,
                'fadeout': part_fadeout,
            },
            'start': start,
            'end': end,
            'count': (end - start) if end > 0 else -1,
            'k_ed_src': k_part_ed_src,
        }

    if k_ed_src is None:
        sys.exit("error: parse_video_section: missing key \'source\' in target file %s_target.ini" % (k_ep))

    for k_part in K_NON_GENERIQUE_PARTS:
        try:
            if db_video[k_part]['k_ed_src'] is None:
                db_video[k_part]['k_ed_src'] = k_ed_src
        except:
            pass


    for k_part in K_ALL_PARTS:
        if k_part not in db_video.keys():
            # The target will use the part defined in the src edition
            db_video[k_part] = {
                'k_ed_src': k_ed_src,
            }


    for k_part in K_NON_GENERIQUE_PARTS:
        if db_video[k_part]['k_ed_src'] is None:
            sys.exit("Errror: parse_video_section: edition shall be defined for %s:%s" % (k_ep, k_part))

    # Set the edition used as the reference for the frames no.
    db_video['k_ed_ref'] = k_ed_ref


    if k_part == 'g_fin':
        pprint(db_video[k_part])
        sys.exit()


