# -*- coding: utf-8 -*-
import sys

import re
from pprint import pprint

from utils.common import (
    FPS,
    K_PARTS,
)

def parse_parts_section(db_episode, config, k_ep, verbose=False):
    k_section = 'parts'

    for k_option in config.options(k_section):
        value_str = config.get(k_section, k_option)
        value_str = value_str.replace(' ','')
        # print("%s, %s => [%s]" % (k_section, k_option, value_str))

        # Parse only supported sections
        if k_option not in K_PARTS:
            continue
        k_part = k_option

        part_fadein = 0
        part_fadeout = 0
        start = None
        end = -1

        # Walk through values
        properties = value_str.split(',')
        # print("\t%s:%s, properties:," % (k_ep, k_part), properties)
        for property in properties:

            search_start_end = re.search(re.compile("(\d+):(\d+)"), property)
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

        if start is None:
            sys.exit("Error: parse_parts_section: start and end values are required for %s:%s in episode file" % (k_ep, k_part))

        db_episode.update({
            k_part: {
                'video': {
                    'effects': {
                        'fadein': part_fadein,
                        'fadeout': part_fadeout,
                    },
                    'start': start,
                    'end': end,
                    'count': (end - start) if end > 0 else -1,
                }
            }
        })

