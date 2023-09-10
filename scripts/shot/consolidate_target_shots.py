# -*- coding: utf-8 -*-
import sys
from copy import deepcopy
from pprint import pprint

from utils.nested_dict import nested_dict_set
from utils.pretty_print import *
from utils.time_conversions import ms_to_frames
from utils.types import Shot, VideoPart


def consolidate_target_shots(db, k_ep, k_part):
    """This procedure is used to consolidate part of an 'épisode': it uses the 'replace'
    field to generate a new list of shots in the 'common' structure of the 'épisode'. This list
    will be used for processing instead of the list defined in the edition.
    It is mainly used for 'asuivre' and 'precedemment' because these parts use the shots from the
    following or the previous 'épisode'

    Note: this procedure has to be called only when the edition (to process)
    is defined before (i.e. db_video points to the choosen edition/episode/part)
    otherwise the target shots will be overwritten by the other edition.

    Args:
        db_episode_src: the global db
        db_episode_dst: a single shot to consolidate
        k_part: part to consolidate (mainly 'asuivre' or 'precedemment')

    Returns:
        None

    """
    K_EP_DEBUG, K_PART_DEBUG, SHOT_NO = ['', '', 0]
    # K_EP_DEBUG, K_PART_DEBUG, SHOT_NO = 'ep23', 'episode', 231

    db_video_target:VideoPart = db[k_ep]['video']['target'][k_part]

    # if k_part == 'episode':
    #     print_yellow("consolidate_target_shots:start")
    #     pprint(db['ep01']['video']['target'])

    k_ed_src = db_video_target['k_ed_src']
    db_video_src = db[k_ep]['video'][k_ed_src][k_part]

    # Verify that shots are defined in src or target
    if ('shots' not in db_video_target.keys()
        and 'shots' not in db_video_src.keys()):
        # Cannot consolidate because no shots are defined
        sys.exit(f"error: consolidate_target_shots: no shots in {k_ep}:{k_part}")

    if k_ep==K_EP_DEBUG and k_part == K_PART_DEBUG:
        pprint(db_video_target)
        print(f"\ncreate_target_shots: {k_ed_src}:{k_ep}:{k_part}")

    # List the shot no which are defined in target
    if 'shots' in db_video_target.keys():
        target_shot_nos = ([s['no'] for s in db_video_target['shots']])
    else:
        target_shot_nos = list()
        db_video_target['shots'] = list()

    # Append shots from src and sort
    for shot_src in db_video_src['shots']:
        if shot_src['no'] not in target_shot_nos:
            db_video_target['shots'].append(deepcopy(shot_src))
    db_video_target['shots'] = sorted(db_video_target['shots'], key=lambda s: s['no'])

    # Consolidate each shot
    # src:
    #   if defined in target:
    #       - define a ed/ep/part
    #       - define a different shot
    #       - define a different start/count of frames
    #   else:
    #       - use the values from the default src shot
    # dst:
    #       - define this ed/ep/part for this shot
    # k_ed/k_ep/k_part:
    #       - related to the shot defined by the src structure
    #
    frame_count = 0
    for shot in db_video_target['shots']:
        # TODO: 'dst' count may be erroneous... to validate
        if 'src' not in shot.keys() and 'dst' not in shot.keys():
            # Shot is copied from src
            shot.update({
                'src': {
                    'k_ed': k_ed_src,
                    'k_ep': k_ep,
                    'k_part': k_part,
                    'no': shot['no'],
                    'start': shot['start'],
                    'count': shot['count'],
                    'replace': False,
                },
                'dst': {
                    'k_ed': k_ed_src,
                    'k_ep': k_ep,
                    'k_part': k_part,
                    'count': shot['count'],
                },
                'k_ed': k_ed_src,
                'k_ep': k_ep,
                'k_part': k_part,
            })

        else:
            # Shot was defined in target section
            shot['src']['replace'] = True

            if 'k_ed' not in shot['src'].keys():
                shot['src']['k_ed'] = k_ed_src
            if 'k_ep' not in shot['src'].keys():
                shot['src']['k_ep'] = k_ep
            if 'k_part' not in shot['src'].keys():
                shot['src']['k_part'] = k_part
            if 'no' not in shot['src'].keys():
                shot['src']['no'] = shot['no']

            # Copy properties from src
            _k_ed_src = shot['src']['k_ed']
            _k_ep_src = shot['src']['k_ep']
            _k_part_src = shot['src']['k_part']
            _shot_no_src = shot['src']['no']
            _shot_src:Shot = db[_k_ep_src]['video'][_k_ed_src][_k_part_src]['shots'][_shot_no_src]
            for k in _shot_src.keys():
                if k not in shot.keys():
                    shot[k] = deepcopy(_shot_src[k])

            if 'count' not in shot['src'].keys():
                shot['src']['count'] = shot['count']
            if 'start' not in shot['src'].keys():
                shot['src']['start'] = shot['start']

            shot['count'] = min(shot['count'], shot['src']['count'])
            shot['start'] = max(shot['start'], shot['src']['start'])

            shot.update({
                'dst': {
                    'k_ed': k_ed_src,
                    'k_ep': k_ep,
                    'k_part': k_part,
                    'count': shot['count'],
                },
                'k_ed': _k_ed_src,
                'k_ep': _k_ep_src,
                'k_part': _k_part_src,
            })


        # Calculate frames count
        frame_count += shot['count']

    # Set frame count for this part
    db_video_target['count'] = frame_count


    # TODO:
    #   - add effects!
    #   - modify shot 0? avsync

    # if ('start' not in db_video_target.keys()
    #     or db_video_target['start'] is None) and 'shots' not in db_video_target.keys():
    #     # This was not specified in the target file, so use the one from the source
    #     print("info: create_target_shots: %s:%s is not declared in target, use the src %s" % (k_ep, k_part, k_ed_src))
    #     db_video_target.update({
    #         'start': db_video_src['start'],
    #         'end': db_video_src['end'],
    #         'count': db_video_src['count'],
    #         'effects': db_video_src['effects'],
    #     })
    #     if k_ep==K_EP_DEBUG and k_part == K_PART_DEBUG:
    #         sys.exit()

    # if k_ep==K_EP_DEBUG and k_part == K_PART_DEBUG:
    #     print("\n%s.create_target_shots: consolidate %s:%s" % (__name__, k_ep, k_part))
    #     print(" start")
    #     print("\tvideo (src): %d\t(%d)" % (db_video_src['start'], db_video_src['count']))
    #     # print("\tvideo (target): %d\t(%d)" % (db_video_target['start'], db_video_target['count']))



    # if k_ep == K_EP_DEBUG and k_part == K_PART_DEBUG:
    #     print("\n%s.create_target_shots: consolidate %s:%s" % (__name__, k_ep, k_part))
    #     print("------------------- before -----------------------------")
    #     print("db_video_src:")
    #     print("   start: %d" % (db_video_src['start']))
    #     print("   count: %d" % (db_video_src['count']))
    #     if 'shots' in db_video_src.keys():
    #         print("   db_video_src[shots]")
    #         for s in db_video_src['shots']:
    #             print("\t", s)
    #     print("\n")

    #     print("-------------------- before ----------------------------")
    #     print("db_video_target:")
    #     print("   start: %d" % (db_video_target['start']))
    #     print("   count: %d" % (db_video_target['count']))
    #     if 'shots' in db_video_target.keys():
    #         print("   db_video_target[shots]")
    #         for s in db_video_target['shots']:
    #             print("\t", s)
    #     print("\n")


    # if 'shots' not in db_video_target.keys():
    #     # print("\n%s.create_target_shots: consolidate %s:%s, create DST shot" % (__name__, k_ep, k_part))
    #     # print("------------------------------------------------")
    #     db_video_target['shots'] = deepcopy(db_video_src['shots'])
    #     for shot in  db_video_target['shots']:
    #         # Remove uneccessary properties
    #         for p in ['filters',
    #                     'curves',
    #                     'replace']:
    #             if p in shot.keys():
    #                 del shot[p]
    #         if 'src' not in shot.keys() or not shot['src']['use']:
    #             shot['src'] = {
    #                 'k_ep': k_ep,
    #                 'k_ed': k_ed_src,
    #                 'start': shot['start'],
    #                 'count': shot['count'],
    #                 'use': True,
    #             }


    # Calculate frames count
    # shots = db_video_target['shots']
    # if db_video_target['start'] != db_video_src['start']:
    #     # The 1st shot is shorter in dst
    #     delta_frames_count = db_video_target['start'] - db_video_src['start']

    #     # Patch the first src shot
    #     db_video_src['shots'][0]['start'] += delta_frames_count
    #     db_video_src['shots'][0]['count'] -= delta_frames_count

    #     # Patch the first dst shot
    #     db_video_target['shots'][0]['start'] += delta_frames_count
    #     db_video_target['shots'][0]['count'] -= delta_frames_count

    #     # Create a src structure for this shot if not already specified
    #     if 'src' not in shots[0].keys():
    #         shots[0]['src'] = {
    #             'k_ed': k_ed_src,
    #             'k_ep': k_ep,
    #             'use': True,
    #         }
    #     # Update the first shot (note: avsync is already calculated before)
    #     shots[0]['src'].update({
    #         'start': db_video_target['start'],
    #         'count': db_video_src['shots'][0]['count'],
    #     })

    # Calculate real duration of the dst part
    # frames_count = 0
    # for shot in shots:
    #     if 'src' in shot.keys():
    #         shot['src']['k_ed'] = k_ed_src
    #         if 'use' in shot['src'].keys() and shot['src']['use']:
    #             # Use the src defined in configuration file
    #             shot['count'] = shot['src']['count']
    #         else:
    #             # Use the original shot
    #             shot['src'].update({
    #                 'start': shot['start'],
    #                 'count': shot['count'],
    #                 'k_ed': k_ed_src,
    #                 'k_ep': k_ep,
    #                 'use': True,
    #             })
    #     frames_count += shot['count']
    # db_video_target['count'] = frames_count


    if k_ep == K_EP_DEBUG and k_part == K_PART_DEBUG:
        print_green("-------------------- after ----------------------------\n")
        print("After consolidation, db_video_target:")
        for k, v in db_video_target.items():
            if k != 'shots':
                print_lightblue("\t%s" % (k), end='\t')
                print(v)
        print_green("-------------------- after ----------------------------\n")
        if 'shots' in db_video_target.keys():
            print_lightblue("\tdb_video_target[shots]")
            # for s in db_video_target['shots']:
            #     print("\t", s)
            pprint(db_video_target['shots'][SHOT_NO])
        # print("   start: %d" % (db_video_target['start']))
        print("   count: %d" % (db_video_target['count']))
        print("\n")
        sys.exit()




def consolidate_target_shots_g(db, k_ep, k_part_g) -> None:
    """This procedure is used
     to consolidate the parsed shots
    It updates the total duration (in frames of the video for a part

    Args:
        db_video: the structure which contains the shots
                    and video properties

    Returns:
        None

    """
    # print("consolidate_target_shots_g: %s:%s" % (k_ep, k_part_g))

    # Get the default source: edition:episode
    k_ed_src = db[k_part_g]['video']['src']['k_ed']
    k_ep_src = db[k_part_g]['video']['src']['k_ep']
    try:
        db_video_src = db[k_ep_src]['video'][k_ed_src][k_part_g]
    except:
        pprint(db[k_part_g])
        raise KeyError(f"Error: missing file from edition {k_ed_src}",
                       f"cannot use {k_ep_src}:{k_part_g}")

    if k_part_g in ['g_debut', 'g_fin']:
        db_video_target = db[k_part_g]['video']
        if 'avsync' in db_video_target.keys():
            print("############# consolidate_target_shots_g: avsync shall not be reset to 0: %d" % (db_video_target['avsync']))
            db_video_target.update({
                'avsync': 0,
            })
        else:
            db_video_target['avsync'] = 0

    elif k_part_g == 'g_asuivre':
        # Create the g_sauivre structure:
        #   this part was not yet defined because it depends on audio start/duration
        # print("create_target_shots_g;: %s:%s:%s" % ('', k_ep, k_part_g))
        try:
            db_audio = db[k_ep]['audio'][k_part_g]
        except:
            sys.exit(f"error: {k_ep}:{k_part_g}: audio is not defined or erroneous")
        db_audio['avsync'] = 0
        db[k_ep]['video']['target'][k_part_g] = {
            'start': 0,
            'count': ms_to_frames(db_audio['duration']),
            'avsync': 0,
            # 'dst': {
            #     'k_ep': k_ep,
            #     'k_part': k_part_g,
            # },
        }
        db_video_target = db[k_ep]['video']['target'][k_part_g]

    elif k_part_g == 'g_documentaire':
        # Create the g_documentaire structure:
        #   this part was not yet defined because it depends on audio start/duration
        db_audio = db[k_ep]['audio'][k_part_g]
        try:
            db_audio = db[k_ep]['audio'][k_part_g]
        except:
            sys.exit(f"error: {k_ep}:{k_part_g}: audio is not defined or erroneous")
        audio_count = ms_to_frames(db_audio['duration'])
        db_audio.update({
            'count': audio_count,
            'avsync': 0,
        })
        db[k_ep]['video']['target'][k_part_g] = {
            'start': ms_to_frames(db_audio['start']),
            'count': audio_count,
            'avsync': 0,
        }
        db_video_target = db[k_ep]['video']['target'][k_part_g]


    # Verify that shots are defined in src or target
    if ('shots' not in db_video_target.keys()
        and 'shots' not in db_video_src.keys()):
        # Cannot consolidate because no shots are defined
        sys.exit(print_red("error: %s.create_target_shots: no shots in src/dst %s:%s" % (__name__, k_ep, k_part_g)))


    # List the shot no which are defined in target
    if 'shots' in db_video_target.keys():
        target_shot_nos = ([s['no'] for s in db_video_target['shots']])
    else:
        target_shot_nos = list()
        db_video_target['shots'] = list()


    # Append shots from src and sort
    for shot_src in db_video_src['shots']:
        if shot_src['no'] not in target_shot_nos:
            db_video_target['shots'].append(deepcopy(shot_src))
    db_video_target['shots'] = sorted(db_video_target['shots'], key=lambda s: s['no'])


    frame_count = 0
    for shot in db_video_target['shots']:
        # TODO: 'dst' count may be erroneous... to validate
        if 'src' not in shot.keys():
            # Shot is copied from src
            shot.update({
                'src': {
                    'k_ed': k_ed_src,
                    'k_ep': k_ep_src,
                    'k_part': k_part_g,
                    'no': shot['no'],
                    'start': shot['start'],
                    'count': shot['count'],
                },
                'dst': {
                    'k_ed': k_ed_src,
                    'k_ep': k_ep,
                    'k_part': k_part_g,
                    'count': shot['count'],
                },
                'k_ed': k_ed_src,
                'k_ep': k_ep_src,
                'k_part': k_part_g,
            })

        else:
            # Shot was defined in target
            if 'k_ed' not in shot['src'].keys():
                shot['src']['k_ed'] = k_ed_src
            if 'k_ep' not in shot['src'].keys():
                shot['src']['k_ep'] = k_ep
            if 'k_part' not in shot['src'].keys():
                shot['src']['k_part'] = k_part_g
            if 'no' not in shot['src'].keys():
                shot['src']['no'] = shot['no']

            # Copy properties from src
            _k_ed_src = shot['src']['k_ed']
            _k_ep_src = shot['src']['k_ep']
            _k_part_src = shot['src']['k_part']
            _shot_no_src = shot['src']['no']
            _shot_src = db[_k_ep_src]['video'][_k_ed_src][_k_part_src]['shots'][_shot_no_src]
            for k in _shot_src.keys():
                if k not in shot.keys():
                    shot[k] = deepcopy(_shot_src[k])

            if 'count' not in shot['src'].keys():
                shot['src']['count'] = shot['count']
            if 'start' not in shot['src'].keys():
                shot['src']['start'] = shot['start']

            shot.update({
                'dst': {
                    'k_ed': k_ed_src,
                    'k_ep': k_ep,
                    'k_part': k_part_g,
                    'count': shot['count'],
                },
                'k_ed': _k_ed_src,
                'k_ep': _k_ep_src,
                'k_part': _k_part_src,
            })


        # Calculate frames count
        frame_count += shot['count']

    db_video_target['count'] = frame_count


    # Effects
    if k_part_g in ['g_debut', 'g_fin']:
        db_video_target = db[k_part_g]['video']
        if 'effects' in db_video_target.keys():
            last_shot = db_video_target['shots'][-1]

            if 'fadeout' in db_video_target['effects'].keys():
                fadeout_count = db_video_target['effects']['fadeout']
                frame_no = last_shot['src']['start'] + last_shot['src']['count'] - 1
                nested_dict_set(last_shot,
                    ['fadeout', frame_no - fadeout_count + 1, fadeout_count], 'effects')
