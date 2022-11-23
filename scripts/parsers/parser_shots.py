# -*- coding: utf-8 -*-
import sys
from pprint import pprint
from copy import deepcopy

from utils.common import K_GENERIQUES, pprint_video
from utils.time_conversions import ms_to_frames


def parse_shotlist(db_shots, k_ep, k_part, shotlist_str) -> None:
    """This procedure parse a string wich contains the list of shots
        and update the structure of the database.
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
            'dst': {
                'k_ep': k_ep,
                'k_part': k_part,
            },
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



def parse_shotlist_precedemment_asuivre(db_shots, k_ep, k_part, shotlist_str) -> None:
    """This procedure parse a string wich contains the list of shots
        and update the structure of the database.
        Used for 'précédemment' and 'à suivre'

    Args:
        db_shots: the structure where to store the shots
        shotlist_str: the string to parse

    Returns:
        None

    """
    shot_list = shotlist_str.split()

    for shot_no, shot in zip(range(len(shot_list)), shot_list):
        shot_properties = shot.split(',')
        db_shots.append({
            'no': shot_no,
            'start': int(shot_properties[0]),
            'count': 0,
            'dst': {
                'k_ep': k_ep,
                'k_part': k_part,
            },
            'filters': 'default',
            'curves': None,
            'replace': dict(),
        })
        if len(shot_properties) > 1:
            for p in shot_properties:
                d = p.split('=')
                if d[0] == 'src':
                    # The frames used in previous/next episode (i.e. source)
                    src_array = d[1].split(':')
                    db_shots[shot_no]['src'] = {
                        'k_ep': 'ep%02d' % (int(src_array[0])),
                        'start': int(src_array[1]),
                        'count': int(src_array[2]),
                    }

                elif d[0] == 'replace':
                    # Replace this shot by the source
                    db_shots[shot_no]['replace'] = True if d[1]=='y' else False

                elif d[0] == 'effects':
                    # maybe used when replace is not used
                    db_shots[shot_no]['effects'] = d[1].split(',')

    print("%s.parse_shotlist_precedemment_asuivre" % (__name__))
    pprint(db_shots)
    sys.exit()





def consolidate_shots_after_parse(db, k_ep, k_part, k_ed) -> None:
    """This procedure is used to consolidate the parsed shots
    It updates the total duration (in frames of the video for a part

    Args:
        db_video: the structure which contains the shots
                    and video properties

    Returns:
        None

    """
    K_PART_DEBUG = ''
    K_EP_DEBUG = ''
    SHOT_NO = 0

    if k_ed=='k' and k_ep==K_EP_DEBUG and k_part==K_PART_DEBUG:
        print("%s:consolidate_shots_after_parse: %s:%s:%s" % (__name__, k_ed, k_ep, k_part))
        pprint(db[k_ep][k_ed][k_part]['video']['shots'][SHOT_NO])
        print("")
        sys.exit()

    db_video = db[k_ep][k_ed][k_part]['video']

    # Create a single shot if no shot defined by the configuration file
    if 'shots' not in db_video.keys():
        # Create shot only if it the src (i.e. used for the target)
        if k_part in K_GENERIQUES:
            k_ed_src = db[k_part]['target']['video']['src']['k_ed']
            k_ep_src = db[k_part]['target']['video']['src']['k_ep']
        else:
            # pprint(db[k_ep]['target'])
            k_ed_src = db[k_ep]['target']['video']['src']['k_ed']
            k_ep_src = k_ep

        # print("SRC for %s:%s:%s is %s:%s:%s" % (k_ed, k_ep, k_part, k_ed_src, k_ep_src, k_part))
        if k_ed == k_ed_src and k_ep == k_ep_src:
            # print("\tDO create a shot for %s:%s:%s" % (k_ed, k_ep, k_part))

            # print("todo: %s:consolidate_shots_after_parse: verify generation of %s:%s:%s" % (__name__, k_ep, k_ed, k_part))
            # pprint(db_video)
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
        # else:
        #     print("\tdo not create a shot for %s:%s:%s" % (k_ed, k_ep, k_part))
        # print("consolidate_shots_after_parse: -->")
        # pprint(db_video['shots'])
        # print("")
        return


    # Update each shot durations
    shots = db_video['shots']
    frames_count = 0
    for i in range(0, len(shots)):
        # print(shots[i])
        if shots[i]['count'] == 0:
            if i + 1 >= len(shots):
                # Last shot: use the count field of the part
                shots[i]['count'] = db_video['start'] + db_video['count'] - shots[i]['start']
            else:
                shots[i]['count'] = shots[i+1]['start'] - shots[i]['start']

            # Update count in the src structure
            if 'src' in shots[i].keys():
                shots[i]['src']['count'] = shots[i]['count']

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
    if k_ed=='k' and k_ep==K_EP_DEBUG and k_part==K_PART_DEBUG:
        print("----->")
        pprint(db[k_ep][k_ed][k_part]['video']['shots'][SHOT_NO])
        print("")
        # sys.exit()



def create_target_shots(database, k_ep, k_part):
    """This procedure is used to consolidate part of an 'épisode': it uses the 'replace'
    field to generate a new list of shots in the 'common' structure of the 'épisode'. This list
    will be used for processing instead of the list defined in the edition.
    It is mainly used for 'asuivre' and 'precedemment' because these parts use the shots from the
    following or the previous 'épisode'

    Note: this procedure has to be called only when the edition (to process)
    is defined before (i.e. db_video points to the choosen edition/episode/part)
    otherwise the target shots will be overwritten by the other edition.

    Args:
        db_episode_src: the global database
        db_episode_dst: a single shot to consolidate
        k_part: part to consolidate (mainly 'asuivre' or 'precedemment')

    Returns:
        None

    """
    K_EP_DEBUG = ''
    K_PART_DEBUG = ''

    k_ed_src = database[k_ep]['target']['video']['src']['k_ed']
    # print("create_target_shots: %s:%s:%s" % (k_ed_src, k_ep, k_part))
    # pprint(database[k_ep])
    db_video_src = database[k_ep][k_ed_src][k_part]['video']
    db_video_dst = database[k_ep]['target']['video'][k_part]

    if k_ed_src=='k' and k_part == K_PART_DEBUG:
        print("\n%s.create_target_shots: consolidate %s:%s" % (__name__, k_ep, k_part))
        print(" start")
        print("\tvideo (src): %d\t(%d)" % (db_video_src['start'], db_video_src['count']))
        print("\tvideo (dst): %d\t(%d)" % (db_video_dst['start'], db_video_dst['count']))
    if k_ep == K_EP_DEBUG and k_part == K_PART_DEBUG:
        print("\n%s.create_target_shots: consolidate %s:%s" % (__name__, k_ep, k_part))
        print("------------------- before -----------------------------")
        print("db_video_src:")
        print("   start: %d" % (db_video_src['start']))
        print("   count: %d" % (db_video_src['count']))
        if 'shots' in db_video_src.keys():
            print("   db_video_src[shots]")
            for s in db_video_src['shots']:
                print("\t", s)
        print("\n")

        print("-------------------- before ----------------------------")
        print("db_video_dst:")
        print("   start: %d" % (db_video_dst['start']))
        print("   count: %d" % (db_video_dst['count']))
        if 'shots' in db_video_dst.keys():
            print("   db_video_dst[shots]")
            for s in db_video_dst['shots']:
                print("\t", s)
        print("\n")


    if ('shots' not in db_video_dst.keys()
        and 'shots' not in db_video_src.keys()):
        # Cannot consolidate because no shots are defined
        # print("\t\tinfo: %s.create_target_shots: no shots in src/dst %s:%s" % (__name__, k_ep, k_part))
        return

    if 'shots' not in db_video_dst.keys():
        # print("\n%s.create_target_shots: consolidate %s:%s, create DST shot" % (__name__, k_ep, k_part))
        # print("------------------------------------------------")
        db_video_dst['shots'] = deepcopy(db_video_src['shots'])
        for shot in  db_video_dst['shots']:
            # Remove uneccessary properties
            for p in ['filters',
                        'curves',
                        'replace']:
                if p in shot.keys():
                    del shot[p]
            if 'src' not in shot.keys() or not shot['src']['use']:
                shot['src'] = {
                    'k_ep': k_ep,
                    'k_ed': k_ed_src,
                    'start': shot['start'],
                    'count': shot['count'],
                    'use': True,
                }

    shots = db_video_dst['shots']

    # TODO: verify this
    database[k_ep]['target']['video']['src']['k_ep'] = k_ep

    # Calculate frames count
    if db_video_dst['start'] != db_video_src['start']:
        # The 1st shot is shorter in dst
        delta_frames_count = db_video_dst['start'] - db_video_src['start']

        # Patch the first src shot
        db_video_src['shots'][0]['start'] += delta_frames_count
        db_video_src['shots'][0]['count'] -= delta_frames_count

        # Patch the first dst shot
        db_video_dst['shots'][0]['start'] += delta_frames_count
        db_video_dst['shots'][0]['count'] -= delta_frames_count

        # Create a src structure for this shot if not already specified
        if 'src' not in shots[0].keys():
            shots[0]['src'] = {
                'k_ed': k_ed_src,
                'k_ep': k_ep,
                'use': True,
            }
        # Update the first shot (note: avsync is already calculated before)
        shots[0]['src'].update({
            'start': db_video_dst['start'],
            'count': db_video_src['shots'][0]['count'],
        })

    # Calculate real duration of the dst part
    frames_count = 0
    for shot in shots:
        if 'src' in shot.keys():
            shot['src']['k_ed'] = k_ed_src
            if 'use' in shot['src'].keys() and shot['src']['use']:
                # Use the src defined in configuration file
                shot['count'] = shot['src']['count']
            else:
                # Use the original shot
                shot['src'].update({
                    'start': shot['start'],
                    'count': shot['count'],
                    'k_ed': k_ed_src,
                    'k_ep': k_ep,
                    'use': True,
                })
        frames_count += shot['count']
    db_video_dst['count'] = frames_count


    if k_ed_src=='k' and k_ep == K_EP_DEBUG and k_part == K_PART_DEBUG:
        print("-------------------- after ----------------------------\n")
        print("After consolidation, db_video_src:")
        if 'shots' in db_video_src.keys():
            print("   db_video_src[shots]")
            for s in db_video_src['shots']:
                print("\t", s)
        print("   start: %d" % (db_video_src['start']))
        print("   count: %d" % (db_video_src['count']))
        print("\n")

        print("-------------------- after ----------------------------\n")
        print("After consolidation, db_video_dst:")
        if 'shots' in db_video_dst.keys():
            print("   db_video_dst[shots]")
            for s in db_video_dst['shots']:
                print("\t", s)
        print("   start: %d" % (db_video_dst['start']))
        print("   count: %d" % (db_video_dst['count']))
        print("\n")






def create_target_shots_g(db, k_ep, k_part_g) -> None:
    """This procedure is used
     to consolidate the parsed shots
    It updates the total duration (in frames of the video for a part

    Args:
        db_video: the structure which contains the shots
                    and video properties

    Returns:
        None

    """

    # Get the default source: edition:episode
    k_ed_src = db[k_part_g]['target']['video']['src']['k_ed']
    k_ep_src = db[k_part_g]['target']['video']['src']['k_ep']

    if k_part_g in ['g_debut', 'g_fin']:
        db_video_dst = db[k_part_g]['target']['video']
        db_video_dst.update({
            'avsync': 0,
        })

    elif k_part_g == 'g_asuivre':
        # Create the g_sauivre structure:
        #   this part was not yet defined because it depends on audio start/duration
        db_audio = db[k_ep]['target']['audio'][k_part_g]
        db_audio['avsync'] = 0
        db[k_ep]['target']['video'][k_part_g] = {
            'start': 0,
            'count': ms_to_frames(db_audio['duration']),
            'avsync': 0,
            'dst': {
                'k_ep': k_ep,
                'k_part': k_part_g,
            },
        }
        db_video_dst = db[k_ep]['target']['video'][k_part_g]

    elif k_part_g == 'g_reportage':
        # Create the g_reportage structure:
        #   this part was not yet defined because it depends on audio start/duration
        db_audio = db[k_ep]['target']['audio'][k_part_g]
        audio_count = ms_to_frames(db_audio['duration'])
        db_audio.update({
            'count': audio_count,
            'avsync': 0,
        })
        db[k_ep]['target']['video'][k_part_g] = {
            'start': ms_to_frames(db_audio['start']),
            'count': audio_count,
            'avsync': 0,
            'dst': {
                'k_ep': k_ep,
                'k_part': k_part_g,
            },
        }
        db_video_dst = db[k_ep]['target']['video'][k_part_g]


    if ('shots' not in db_video_dst.keys()
        or len(db_video_dst['shots']) == 0):
        frame_count = 0
        db_video_dst['shots'] = list()
        # if k_part_g == 'g_reportage':
        #     print("create_target_shots_g for %s:%s:%s" % (k_ed_src, k_ep, k_part_g))
        #     print("\tfrom %s:%s:%s" % (k_ep_src, k_ed_src, k_part_g))
        #     pprint(db[k_ep_src][k_ed_src][k_part_g]['video'])
        for shot_src in db[k_ep_src][k_ed_src][k_part_g]['video']['shots']:
            # Create a dst shot from src shot
            db_video_dst['shots'].append({
                'no': shot_src['no'],
                'start': shot_src['start'],
                'count': shot_src['count'],
                'dst': db[k_ep]['target']['video'][k_part_g]['dst'],
                'src': {
                    'k_ed': k_ed_src,
                    'k_ep': k_ep_src,
                    'start': shot_src['start'],
                    'count': shot_src['count'],
                    'use': True
                },
            })
            frame_count += shot_src['count']
        db_video_dst['count'] = frame_count
        # print("<<<<<<<<<<<<<<<< VIDEO %s:%s >>>>>>>>>>>>>>>>" % (k_ep, k_part_g))
        # pprint_video(db_video_dst, first_indent=4)
        return

    # Recalculate nb of frames for this part
    shots = db_video_dst['shots']
    frames_count = 0
    for i in range(0, len(shots)):
        if shots[i]['count'] == -1:
            if i + 1 >= len(shots):
                break
            shots[i]['count'] = shots[i+1]['start'] - shots[i]['start']
        if 'effects' in shots[i]:
            if shots[i]['effects'][0] == 'loop':
                frames_count += shots[i]['effects'][2]
                sys.exit("%s: add loop duration" % (__name__))
        frames_count += shots[i]['count']
    db_video_dst['count'] = frames_count

    if 'start' not in db_video_dst.keys():
        db_video_dst['start'] = db_video_dst['shots'][0]['start']

