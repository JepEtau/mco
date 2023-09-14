# -*- coding: utf-8 -*-
import re
import sys
from pprint import pprint

from utils.common import (
    K_ALL_PARTS,
    pprint_video,
)
from utils.nested_dict import nested_dict_set
from utils.pretty_print import *
from utils.types import Shot


def parse_shotlist(db_shots:list[Shot], k_ep, k_part, shotlist_str) -> None:
    """This procedure parse a string wich contains the list of shots
        and update the structure of the db.
        Used for 'épisodes' and 'documentaire'

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
        new_shot: Shot = {
            'no': shot_no,
            'start': start,
            'count': count,
            'filters': None,
            'filters_id': 'default',
            'curves': None,
            'replace': dict(),
        }
        db_shots.append(new_shot)
        # print(shot_properties)
        # print(db_shots[-1])

        # This shot may contains other customized properties
        if len(shot_properties) > 1:
            for p in shot_properties:
                d = p.split('=')
                if d[0] == 'filters':
                    # custom filter
                    db_shots[shot_no]['filters_id'] = d[1]

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




def parse_shotlist_new(db_shots, config, k_section, verbose=False) -> None:
    for k_option in config.options(k_section):
        value_str = config.get(k_section, k_option).replace(' ','')

        shot_no = int(k_option)
        shot_properties = value_str.split(',')


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
            'filters': None,
            'filters_id': 'default',
            'curves': None,
            'replace': dict(),
        })
        # print(shot_properties)
        # print(db_shots[-1])

        # This shot may contains other customized properties
        if len(shot_properties) > 1:
            for p in shot_properties:
                d = p.split('=')
                if d[0] == 'filters':
                    # custom filter
                    db_shots[shot_no]['filters_id'] = d[1]



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
        db_video['shots'] = [Shot(
            no = 0,
            start = db_video['start'],
            filters_id = 'default',
            filters = None,
            count = db_video['count'],
            curves = None,
            replace = dict(),
            dst = dict(
                k_ep = k_ep,
                k_part = k_part
            )
        )]

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
            sys.exit(red(f"Error: {k_ed}:{k_ep}:{k_part}: shot no. {shots[i]['no']:03d}, length (shots[i]['count']) < 0"))

        frames_count += shots[i]['count']

    # The new part duration is the sum of all shots duration
    # db_video['count'] = frames_count



def parse_target_shotlist(db_shots, config, k_section, language:str='fr') -> None:

    for k_option in config.options(k_section):
        value_str = config.get(k_section, k_option).replace(' ','')

        lang = language
        try:
            shot_no = int(k_option)
        except:
            try:
                shot_no, lang = k_option.split('_')
                shot_no = int(shot_no)
                if lang != language:
                    continue
            except:
                sys.exit(f"erroneous option {k_option} in section [{k_section}]")

        shot_properties = value_str.split(',')

        # Parse properties
        if len(shot_properties) > 0:

            # Append this shot to the list of shots
            db_shots.append({
                'no': shot_no,
                'src': dict(),
            })
            shot = db_shots[-1]

            for p in shot_properties:
                try:
                    k, v = p.split('=')
                except:
                    print(f'Error: target, section {k_section}, shot no.{shot_no}, unvalid property: [{p}]')
                    # sys.exit()
                    continue

                if k == 'ed':
                    shot['src']['k_ed'] = v

                elif k == 'ep':
                    shot['src']['k_ep'] = f"ep{int(v):02}"

                elif k == 'part':
                    if v in K_ALL_PARTS:
                        shot['src']['k_part'] = v
                    else:
                        sys.exit(f"parse_target_shotlist: {v} is not recognized")

                elif k == 'shot':
                    shot['src']['no'] = int(v)

                elif k == 'segments':
                    shot['src']['segments'] = list()
                    segments = v.replace(' ', '').split('\n')
                    for s in segments:
                        if (match := re.match(re.compile("(\d+):(\d+)"), s)):
                            shot['src']['segments'].append({
                                'start': int(match.group(1)),
                                'count': int(match.group(2)),
                            })

                elif k in ['start', 'count']:
                    shot['src'][k] = int(v)


            # Debug episode29
            if k_section == 'shots_episode.fr' and shot_no == 307:
                print(k_section)
                # pprint(shot_properties)
                pprint(shot)
                # sys.exit()
