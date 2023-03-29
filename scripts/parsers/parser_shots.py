# -*- coding: utf-8 -*-
import sys
from copy import deepcopy
from pprint import pprint

from utils.common import (
    FPS,
    K_ALL_PARTS,
    K_GENERIQUES,
    nested_dict_set,
    pprint_video,
)
from utils.pretty_print import *
from utils.time_conversions import ms_to_frames


def parse_shotlist(db_shots, k_ep, k_part, shotlist_str) -> None:
    """This procedure parse a string wich contains the list of shots
        and update the structure of the db.
        Used for 'épisodes' and 'reportage'

    Args:
        db_shots: the structure where to store the shots
        shotlist_str: the string to parse

    Returns:
        None

    """
    shot_list = shotlist_str.split()

    for shot_no, shot in zip(range(len(shot_list)), shot_list):
        # print(shot)
        shot_properties = shot.split(',')

        # Shot may specify start or start:end
        if ':' in shot_properties[0]:
            start_end = shot_properties[0].split(':')
            # first field is the start and end of the shot
            start = int(start_end[0])
            if len(start_end) > 1:
                end = int(start_end[1])
            else:
                end = start
            count = end - start
        else:
            start = int(shot_properties[0])
            count = 0

        # Append this shot to the list of shots
        db_shots.append({
            'no': shot_no,
            'start': start,
            'count': count,
            'filters': 'default',
            'curves': None,
            'replace': dict(),
        })
        # print(shot_properties)
        # print(db_shots[-1])

        # This shot may contains other customized properties
        if len(shot_properties) > 1:
            for p in shot_properties:
                d = p.split('=')
                if d[0] == 'filter':
                    # custom filter
                    db_shots[shot_no]['filters'] = d[1]

                elif d[0] == 'ed':
                    # edition that will be used to generate this shot
                    if 'src' not in db_shots[shot_no].keys():
                        db_shots[shot_no]['src'] = dict()
                    db_shots[shot_no]['src'].update({'k_ed': d[1]})

                elif d[0] == 'ep' or d[0] == 'src':
                    # episode that will be used to generate this shot
                    if 'src' not in db_shots[shot_no].keys():
                        db_shots[shot_no]['src'] = dict()
                    src = d[1].split(':')
                    if len(src) == 3:
                        db_shots[shot_no]['src'].update({
                            'k_ep': 'ep%02d' % (int(src[0])),
                            'start': int(src[1]),
                            'count': int(src[2]),
                        })
                    elif len(src) == 2:
                        db_shots[shot_no]['src'].update({
                            'k_ep': 'ep%02d' % (int(src[0])),
                            'start': int(src[1]),
# 2022-11-13: replacement does not work: to verify
                            'count': -1
                        })
                    else:
                        db_shots[shot_no]['src'].update({
                            'k_ep': 'ep%02d' % (int(src[0])),
                            'start': start,
# 2022-11-13: replacement does not work: to verify
                            'count': -1
                        })

                elif d[0] == 'replace':
                    # Replace this shot by the source
                    if 'src' not in db_shots[shot_no].keys():
                        db_shots[shot_no]['src'] = dict()
                    db_shots[shot_no]['src'].update({'use': True if d[1]=='y' else False})

                elif d[0] == 'effects':
                    db_shots[shot_no]['effects'] = d[1].split(',')



def consolidate_parsed_shots(db, k_ed, k_ep, k_part) -> None:
    """This procedure is used to consolidate the parsed shots
    It updates the total duration (in frames of the video for a part
    Args:
        db_video: the structure which contains the shots
                    and video properties
    Returns:
        None

    """
    db_video = db[k_ep]['video'][k_ed][k_part]

    # Create a single shot if no shot defined by the configuration file
    if 'shots' not in db_video.keys():
        if 'count' not in db_video.keys() or db_video['count'] == 0:
            return
        db_video['shots'] = [{
            'no': 0,
            'start': db_video['start'],
            'filters': 'default',
            'count': db_video['count'],
            'curves': None,
            'replace': dict(),
            'dst':{
                'k_ep': k_ep,
                'k_part': k_part,
            }
        }]
        return

    # Update each shot durations
    shots = db_video['shots']
    frames_count = 0
    for i in range(0, len(shots)):
        # print(shots[i])
        if shots[i] is None:
            continue

        if shots[i]['count'] == 0:
            if i + 1 >= len(shots):
                # Last shot: use the count field of the part
                shots[i]['count'] = db_video['start'] + db_video['count'] - shots[i]['start']
            else:
                shots[i]['count'] = shots[i+1]['start'] - shots[i]['start']

        if 'effects' in shots[i]:
            if shots[i]['effects'][0] == 'loop':
                frames_count += shots[i]['effects'][2]
                sys.exit("%s: add loop duration" % (__name__))

        if shots[i]['count'] <= 0 and i < len(shots)-1:
            print("Error: %s:%s:%s: shot start=%d, shot length (%d) < 0 " % (k_ed, k_ep, k_part, shots[i]['start'], shots[i]['count']))
            # pprint(shots)
            sys.exit()

        frames_count += shots[i]['count']

    # The new part duration is the sum of all shots duration
    # db_video['count'] = frames_count




# def consolidate_target_shots_after_parse(db, k_ep, k_part, k_ed) -> None:
#     """This procedure is used to consolidate the parsed shots
#     It updates the total duration (in frames of the video for a part

#     Args:
#         db_video: the structure which contains the shots
#                     and video properties

#     Returns:
#         None

#     """
#     K_PART_DEBUG = ''
#     K_EP_DEBUG = ''
#     SHOT_NO = 1

#     if k_ed=='k' and k_ep==K_EP_DEBUG and k_part==K_PART_DEBUG:
#         print("%s:consolidate_parsed_shots: %s:%s:%s" % (__name__, k_ed, k_ep, k_part))
#         pprint(db[k_ep]['video'][k_ed][k_part]['shots'][SHOT_NO])
#         print("")
#         # sys.exit()

#     db_video = db[k_ep]['video'][k_ed][k_part]

#     # Create a single shot if no shot defined by the configuration file
#     if 'shots' not in db_video.keys():
#         # Create shot only if it the src (i.e. used for the target)
#         if k_part in K_GENERIQUES:
#             k_ed_src = db[k_part]['video']['src']['k_ed']
#             k_ep_src = db[k_part]['video']['src']['k_ep']
#         else:
#             k_ed_src = db[k_ep]['video']['target'][k_part]['k_ed_src']
#             k_ep_src = k_ep

#         # print("SRC for %s:%s:%s is %s:%s:%s" % (k_ed, k_ep, k_part, k_ed_src, k_ep_src, k_part))
#         if k_ed == k_ed_src and k_ep == k_ep_src:
#             # print("\tDO create a shot for %s:%s:%s" % (k_ed, k_ep, k_part))

#             # print("todo: %s:consolidate_parsed_shots: verify generation of %s:%s:%s" % (__name__, k_ep, k_ed, k_part))
#             # pprint(db_video)
#             if 'count' not in db_video.keys() or db_video['count'] == 0:
#                 return
#             db_video['shots'] = [{
#                 'no': 0,
#                 'start': db_video['start'],
#                 'filters': 'default',
#                 'count': db_video['count'],
#                 'curves': None,
#                 'replace': dict(),
#                 'dst':{
#                     'k_ep': k_ep,
#                     'k_part': k_part,
#                 }
#             }]
#         # else:
#         #     print("\tdo not create a shot for %s:%s:%s" % (k_ed, k_ep, k_part))
#         # print("consolidate_parsed_shots: -->")
#         # pprint(db_video['shots'])
#         # print("")
#         return


#     # Update each shot durations
#     shots = db_video['shots']
#     frames_count = 0
#     for i in range(0, len(shots)):
#         # print(shots[i])
#         if shots[i] is None:
#             continue

#         if shots[i]['count'] == 0:
#             if i + 1 >= len(shots):
#                 # Last shot: use the count field of the part
#                 shots[i]['count'] = db_video['start'] + db_video['count'] - shots[i]['start']
#             else:
#                 shots[i]['count'] = shots[i+1]['start'] - shots[i]['start']

#             # Update count in the src structure
#             if ('src' in shots[i].keys()
#                 and shots[i]['dst']['k_part'] not in ['precedemment', 'asuivre']):
#                 # 2022-12-02: do not modify the frame count if the dst is replaced
#                 #   which is the case of these parts
#                 # TODO: verify when replacing episode by 'precedemment' or 'asuivre'
#                 shots[i]['src']['count'] = shots[i]['count']

#         if 'effects' in shots[i]:
#             if shots[i]['effects'][0] == 'loop':
#                 frames_count += shots[i]['effects'][2]
#                 sys.exit("%s: add loop duration" % (__name__))

#         if shots[i]['count'] <= 0 and i < len(shots)-1:
#             print("Error: %s:%s:%s: shot start=%d, shot length (%d) < 0 " % (k_ed, k_ep, k_part, shots[i]['start'], shots[i]['count']))
#             # pprint(shots)
#             sys.exit()

#         frames_count += shots[i]['count']

#     # The new part duration is the sum of all shots duration
#     # db_video['count'] = frames_count
#     if k_ed=='k' and k_ep==K_EP_DEBUG and k_part==K_PART_DEBUG:
#         print("----->")
#         pprint(db[k_ep][k_ed][k_part]['video']['shots'][SHOT_NO])
#         print("")
#         sys.exit()


def parse_target_shotlist(db_shots, config, k_section, verbose=False) -> None:
    for k_option in config.options(k_section):
        value_str = config.get(k_section, k_option)
        value_str = value_str.replace(' ','')

        shot_no = int(k_option)
        shot_properties = value_str.split(',')

        # Parse properties
        if len(shot_properties) > 1:
            # Append this shot to the list of shots
            db_shots.append({
                'no': shot_no,
                'src': dict()
            })
            shot = db_shots[-1]

            for p in shot_properties:
                d = p.split('=')

                if d[0] == 'ed':
                    shot['src']['k_ed'] = d[1]

                elif d[0] == 'ep':
                    shot['src']['k_ep'] = "ep%02d" % (int(d[1]))

                elif d[0] == 'part':
                    if d[1] in K_ALL_PARTS:
                        shot['src']['k_part'] = d[1]
                    else:
                        sys.exit("parse_target_shotlist: %s is not recognized" % (d[1]))
                elif d[0] == 'shot':
                    shot['src']['no'] = int(d[1])

                elif d[0] == 'segment':
                    start_end = d[1].split(':')
                    shot['src']['start'] = int(start_end[0])
                    shot['src']['count'] = int(start_end[1]) - shot['src']['start']



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
    K_EP_DEBUG = ''
    K_PART_DEBUG = 'episode'

    db_video_target = db[k_ep]['video']['target'][k_part]
    k_ed_src = db_video_target['k_ed_src']
    db_video_src = db[k_ep]['video'][k_ed_src][k_part]

    # Verify that shots are defined in src or target
    if ('shots' not in db_video_target.keys()
        and 'shots' not in db_video_src.keys()):
        # Cannot consolidate because no shots are defined
        sys.exit("error: %s.create_target_shots: no shots in src/dst %s:%s" % (__name__, k_ep, k_part))

    if k_ep==K_EP_DEBUG and k_part == K_PART_DEBUG:
        pprint(db_video_target)
        print("\ncreate_target_shots: %s:%s:%s" % (k_ed_src, k_ep, k_part))

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
        if 'src' not in shot.keys():
            # Shot is copied from src
            shot.update({
                'src': {
                    'k_ed': k_ed_src,
                    'k_ep': k_ep,
                    'k_part': k_part,
                    'no': shot['no'],
                    'start': shot['start'],
                    'count': shot['count'],
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
            # Shot was defined in target
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
            for s in db_video_target['shots']:
                print("\t", s)
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
    db_video_src = db[k_ep_src]['video'][k_ed_src][k_part_g]

    if k_part_g in ['g_debut', 'g_fin']:
        print("############# consolidate_target_shots_g: avsync shall not be reset to 0")
        db_video_target = db[k_part_g]['video']
        db_video_target.update({
            'avsync': 0,
        })

    elif k_part_g == 'g_asuivre':
        # Create the g_sauivre structure:
        #   this part was not yet defined because it depends on audio start/duration
        # print("create_target_shots_g;: %s:%s:%s" % ('', k_ep, k_part_g))
        db_audio = db[k_ep]['audio'][k_part_g]
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

    elif k_part_g == 'g_reportage':
        # Create the g_reportage structure:
        #   this part was not yet defined because it depends on audio start/duration
        db_audio = db[k_ep]['audio'][k_part_g]
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
        sys.exit(print_red("error: %s.create_target_shots: no shots in src/dst %s:%s" % (__name__, k_ep, k_part)))


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
