# -*- coding: utf-8 -*-
import sys
import numpy as np
from pprint import pprint

from parsers.parser_curves import parse_curves_file



def get_lut_from_curves(db, k_ep_or_g, k_curves:str):
    """ This function reads a curve file and
        returns the luts for each RGB channel. Returns None
        if there is a problem with the curve
    """
    # print("%s:get_lut_from_curves %s, %s" % (__name__, k_ep_or_g, k_curves))
    rgb_channels = parse_curves_file(db, k_ep_or_g, k_curves)
    if rgb_channels is None:
        return None

    return calculate_channel_lut(rgb_channels)



def calculate_channel_lut(rgb_channels, verbose=False):
    lut = dict()

    lut_master = np.clip(((255 * rgb_channels['m'].calculate(256, depth=1000) + 0.5) / 1000), 0, 255).astype('int')
    if verbose:
        print("--------------- calculate_channel_lut: master (%d) -------------------" % (len(lut_master)))
        pprint.pprint(lut_master)

    for k in ['r', 'g', 'b']:
        channel_lut = np.clip(((255 * rgb_channels[k].calculate(256, depth=1000) + 0.5) / 1000), 0, 255).astype('int')
        try:
            lut[k] = channel_lut[lut_master].astype('uint8')
        except:
            print("error")
            print("--------------- calculate_channel_lut: master (%d) -------------------" % (len(lut_m)))
            pprint.pprint(lut_master)

            print("--------------- calculate_channel_lut: %s (%d) -------------------" % (k, len(_lut)))
            pprint.pprint(channel_lut)

            # print("--------------- update_lookup_tables: lut[k] (%d) -------------------" % (len(lut[k])))
            # pprint.pprint(lut[k])
            sys.exit()

    if verbose:
        for k in ['r', 'g', 'b']:
            print("--------------- calculate_channel_lut: %s (%d) -------------------" % (k, len(lut[k])))
            pprint.pprint(lut[k])

    return lut
