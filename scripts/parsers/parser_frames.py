# -*- coding: utf-8 -*-
import configparser
import os
from pathlib import Path, PosixPath
import re
from pprint import pprint
from copy import deepcopy

from utils.nested_dict import nested_dict_set



def parse_frames_for_study(db, k_ep):
    # Parse the ini file which contains the listf of frames
    # used in study mode

    nested_dict_set(db, dict(), k_ep, 'video', 'frames')
    db_frames = db[k_ep]['video']['frames']

    # Open configuration file
    filepath = os.path.join(db['common']['directories']['config'], k_ep, "%s_frames.ini" % (k_ep))
    if filepath.startswith("~/"):
        filepath = os.path.join(PosixPath(Path.home()), filepath[2:])
    if not os.path.exists(filepath):
        return

    # Parse configuration file
    config = configparser.ConfigParser()
    config.read(filepath)
    for k_section in config.sections():
        # Parse only supported sections

        if k_section == 'frames':
            # Parse this section only when in study mode (--frames)
            db_frames['path_output'] =  os.path.join(db['common']['directories']['frames'], "%s" % (k_ep)),

            for k_part in config.options(k_section):
                value_str = config.get(k_section, k_part)
                value_str = value_str.replace(' ','')

                db_frames[k_part] = list()
                parse_framelist(db_frames[k_part], value_str)



def parse_frames_for_study_g(db, k_part_g):
    # Parse the ini file which contains the listf of frames
    # used in study mode

    nested_dict_set(db, dict(), k_part_g, 'video', 'frames')
    db_frames = db[k_part_g]['video']['frames']

    # Open configuration file
    filepath = os.path.join(db['common']['directories']['config'], k_part_g, "%s_frames.ini" % (k_part_g))
    if filepath.startswith("~/"):
        filepath = os.path.join(PosixPath(Path.home()), filepath[2:])
    if not os.path.exists(filepath):
        return

    # Parse configuration file
    config = configparser.ConfigParser()
    config.read(filepath)
    for k_section in config.sections():
        # Parse only supported sections

        if k_section == 'frames':
            # Parse this section only when in study mode (--frames)
            db_frames['path_output'] =  os.path.join(db['common']['directories']['frames'], "%s" % (k_part_g)),

            for k_part in config.options(k_section):
                value_str = config.get(k_section, k_part)
                value_str = value_str.replace(' ','')

                db_frames[k_part] = list()
                parse_framelist(db_frames[k_part], value_str)




def parse_framelist(db_frames, framelist_str):
    framelist = framelist_str.split()

    for frame_no, frame in zip(range(len(framelist)), framelist):
        # print(shot)
        frame_properties = frame.split(',')
        f_tmp = {
            'no': int(frame_properties[0])
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
                elif d[0] == 'ed':
                    # custom edition
                    f_tmp['k_ed'] = d[1]
        try:
            if f_tmp['k_ep'] == '*':
                for i in range(1,40):
                    f_tmp['k_ep'] = 'ep%02d' % (i)
                    db_frames.append(deepcopy(f_tmp))
            else:
                db_frames.append(f_tmp)
        except:
            db_frames.append(f_tmp)

