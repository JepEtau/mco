#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pprint import pprint

from utils.common import K_GENERIQUES


def get_crop(db, frame_or_shot, k_part)-> list:
    k_ed = frame_or_shot['k_ed']
    k_ep = frame_or_shot['k_ep']

    if k_part in K_GENERIQUES:
        k_ed_src = db[k_part]['common']['video']['reference']['k_ed']
        # print("%s.get_crop: %s, %s->%s k_ep=%s" % (__name__, k_part, k_ed, k_ed_src, k_ep))
        return db[k_ep][k_ed_src][k_part]['video']['geometry']
    else:
        return db[k_ep][k_ed][k_part]['video']['geometry']
