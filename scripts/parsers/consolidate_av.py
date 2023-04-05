# -*- coding: utf-8 -*-
import sys

import re
from pprint import pprint

from utils.common import (
    FPS,
    K_ALL_PARTS,
    K_NON_GENERIQUE_PARTS,
    K_PARTS,
    pprint_audio,
    pprint_video,
    nested_dict_set,
)
from utils.time_conversions import (
    frames_to_ms,
    ms_to_frames,
)





def parser_consolidate_audio_video(db, k_ep):
    K_EP_DEBUG = ''

    db_common = db[k_ep]['common']

    if ('audio' not in db_common.keys()
    or 'video' not in db_common.keys()):
        return

    db_video = db_common['video']
    db_audio = db_common['audio']

    if k_ep == K_EP_DEBUG:
        print("<<<<<<<<<<<<<<<< parser_consolidate_audio_video ep=%s >>>>>>>>>>>>>>>>" % (k_ep))
        print(db_common.keys())
        print("<<<<<<<<<<<<<<<< VIDEO >>>>>>>>>>>>>>>>")
        pprint_video(db_video, ignore='shots', first_indent=4)
        print("<<<<<<<<<<<<<<<< AUDIO >>>>>>>>>>>>>>>>")
        pprint_audio(db_audio, first_indent=4)
        print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
        # sys.exit()

    # precedemment
    if 'precedemment' in db_audio.keys() and db_audio['precedemment']['duration'] != 0:
        avsync_ms = db_audio['precedemment']['start'] - frames_to_ms(db_video['precedemment']['start'])
        db_video['precedemment']['avsync'] = ms_to_frames(avsync_ms)
        db_audio['precedemment']['avsync'] = avsync_ms


    # episode
    if 'precedemment' in db_audio.keys() and db_audio['precedemment']['duration'] != 0:
        # Warning if avsync is specified in audio config, this will not work unless correct this
        audio_avsync_ms = (db_audio['episode']['start']
            - (db_audio['precedemment']['start'] + db_audio['precedemment']['duration']))
        db_audio['episode']['avsync'] = audio_avsync_ms

        video_avsync = (db_video['episode']['start']
            - (db_video['precedemment']['start'] + db_video['precedemment']['count']))
        db_video['episode']['avsync'] = video_avsync

        if db_video['episode']['start'] != db_video['episode']['shots'][0]['start']:
            sys.exit("parser_consolidate_audio_video: error: start of episode (%d) != start of 1st shot (%d)" % (
                db_video['episode']['start'], db_video['shots']['start']))
    else:
        avsync_ms = 0
        db_video['episode']['avsync'] = ms_to_frames(avsync_ms)
        db_audio['episode']['avsync'] = avsync_ms

    # g_asuivre
    k_part_g = 'g_asuivre'
    audio_count = ms_to_frames(db_audio[k_part_g]['duration'])
    db_video[k_part_g] = {
        'start': 0,
        'end': audio_count,
        'count': audio_count,
        'avsync': 0,
    }
    db_audio[k_part_g]['avsync'] = 0


    # asuivre
    if 'asuivre' in db_audio.keys() and db_audio['asuivre']['duration'] != 0:
        avsync_ms = db_audio['asuivre']['start'] - frames_to_ms(db_video['asuivre']['start'])
        db_video['asuivre']['avsync'] = ms_to_frames(avsync_ms)
        db_audio['asuivre']['avsync'] = avsync_ms

    # g_reportage
    k_part_g = 'g_reportage'
    audio_count = ms_to_frames(db_audio[k_part_g]['duration'])
    audio_start = ms_to_frames(db_audio[k_part_g]['start'])
    db_audio[k_part_g]['count'] = audio_count
    db_video[k_part_g] = {
        'start': audio_start,
        'end': audio_start + audio_count,
        'count': audio_count,
        'avsync': 0
    }

    # reportage: no a/v sync
    # avsync_ms = db_audio['reportage']['start'] - frames_to_ms(db_video['reportage']['start'])
    avsync_ms = 0
    db_video['reportage']['avsync'] = ms_to_frames(avsync_ms)
    db_audio['reportage']['avsync'] = avsync_ms


    # Update count
    for kp in K_PARTS:
        if kp == 'g_reportage':
            continue
        db_audio[kp]['count'] = ms_to_frames(db_audio[kp]['end'] - db_audio[kp]['start'])

    if k_ep == K_EP_DEBUG:
        print("--------------- Consolidated ----------------------- ")
        print("<<<<<<<<<<<<<<<< VIDEO (after consolidation) >>>>>>>>>>>>>>>>")
        pprint_video(db_video, ignore='shots', first_indent=4)
        print("<<<<<<<<<<<<<<<< AUDIO (after consolidation) >>>>>>>>>>>>>>>>")
        pprint_audio(db_audio, first_indent=4)
        # sys.exit()

