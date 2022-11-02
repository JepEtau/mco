#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from pprint import pprint
from copy import deepcopy


def parse_framelist(db_frames, framelist_str):
    framelist = framelist_str.split()

    for frame_no, frame in zip(range(len(framelist)), framelist):
        # print(shot)
        frame_properties = frame.split(',')
        f_tmp = {
            'ref': int(frame_properties[0]),
            'filters': 'default',
            'k_ep': ''
        }
        if len(frame_properties) > 1:
            for f in frame_properties:
                d = f.split('=')
                if d[0] == 'filters':
                    # custom filter
                    f_tmp['filters'] = d[1]
                elif d[0] == 'ep':
                    # custom episode
                    if d[1] == '*':
                        f_tmp['k_ep'] = d[1]
                    else:
                        f_tmp['k_ep'] = 'ep%02d' % (int(d[1]))

        if f_tmp['k_ep'] == '*':
            for i in range(1,40):
                f_tmp['k_ep'] = 'ep%02d' % (i)
                db_frames.append(deepcopy(f_tmp))
        else:
            db_frames.append(f_tmp)

