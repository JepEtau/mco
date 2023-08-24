# -*- coding: utf-8 -*-
import sys
from utils.common import pprint_video


def get_shot_from_frame_no(db, frame_no:int, k_ed, k_ep, k_part) -> dict:
    # print("get_shot_from_frame_no: %d in %s:%s:%s" % (frame_no, k_ed, k_ep, k_part))
    shots = db[k_ep]['video'][k_ed][k_part]['shots']
    for shot in shots:
        if shot is None:
            continue
        # print("%d in [%d; %d] ?" % (frame_no, shot['start'], shot['start'] + shot['count']))
        if shot['start'] <= frame_no < (shot['start'] + shot['count']):
            return shot

    # print("\nWarning: %s:get_shot_from_frame_no: not found, frame no. %d in %s:%s:%s continue" % (__name__, frame_no, k_ed, k_ep, k_part))
    # pprint_video(db[k_ep]['video'][k_ed][k_part], ignore='')
    # print("-----------------------------------------------")
    # # pprint(db[k_ep_ref]['video'][k_ed][k_part]['shots'])
    # sys.exit()

    return None
