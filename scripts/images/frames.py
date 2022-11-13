# -*- coding: utf-8 -*-
import sys
from datetime import timedelta
import copy
from pprint import pprint

from utils.common import K_GENERIQUES
from utils.path import get_output_frame_filepaths



def get_frames_for_study(database, edition:str, episode_no:int, k_part:str=''):
    print("%s.get_frames_for_study: episode no. %d, k_part=%s, edition=%s" % (__name__, episode_no, k_part, edition))

    # Returns a list of frames for an edition (recalculated with offset)
    if edition == '' or not episode_no<=39: return

    if k_part in K_GENERIQUES:
        # Generique
        if 'frames' not in database[k_part]['common'].keys():
            print("No frames defined in config file")
            return []
        list_of_frames = copy.deepcopy(database[k_part]['common']['frames'])

    else:
        # Episode
        k_episode = 'ep%02d' % (episode_no)
        db_ep_common = database[k_episode]['common']

        if 'frames' not in db_ep_common[k_part].keys():
            return []
        list_of_frames = copy.deepcopy(db_ep_common[k_part]['frames'])

    for f in list_of_frames:
        if f['k_ep'] == 0:
            f['k_ep'] = k_episode

        k_episode_tmp = f['k_ep']
        if k_episode_tmp not in database.keys():
            sys.exit("Error: %s: episode %d is not defined in the database" % (__name__, f['k_ep']))

        # Apply offset
        # print("k_episode_tmp=%s, edition=%s, k_part=%s" % (k_episode_tmp, edition, k_part))
        # pprint(database[k_episode_tmp][edition])
        # print("\n")
        if 'offsets' in database[k_episode_tmp][edition][k_part]['video']:
            # print("Apply offset:")
            offsets = database[k_episode_tmp][edition][k_part]['video']['offsets']
            # print("edition=%s, episode_no!%d, offsets=" % (edition, episode_no), offsets)
            for offset in offsets:
                if offset['start'] <= f['ref'] <= offset['end']:
                    f['no'] = f['ref'] + offset['offset']
                    break
            # if offsets:
            #     i = 0
            #     for ff in list_of_frames:
            #         if not (offsets[i]['start'] <= f['ref'] <= offsets[i]['end']):
            #             i += 1
            #
        else:
            print("No offset:")
            # print("edition=%s, episode_no!%d => no offset" % (edition, episode_no))
            f['no'] = f['ref']

    # 'no': the frame no. for this edition
    # 'ref': the frame no. defined in ep##_common
    return list_of_frames



def frame_no_to_timestamp(frame_no:int, fps=25.0):
    # Returns th frame no. converted to a timestamp (e.g. 1452.12s)
    timestamp_float = float(frame_no)/fps
    timestamp_int = int(timestamp_float)
    timestamp_ms = (100 * frame_no)/fps - (100 * timestamp_int)
    if timestamp_ms < 10:
        timestampStr = "%s.0%d" % (str(timedelta(seconds=timestamp_int)), timestamp_ms)
    else:
        timestampStr = "%s.%d" % (str(timedelta(seconds=timestamp_int)), timestamp_ms)
    return timestampStr


def frame_no_to_sexagesimal(frame_no:int, fps=25.0):
    timestamp_float = float(frame_no) / fps
    return timestamp_to_sexagesimal(timestamp_float)


def timestamp_to_sexagesimal(timestamp:float):
    # Timestamp (e.g. 1452.12s) to sexagesimal (HH:MM:SS.MS)
    ms = int((timestamp - int(timestamp)+0.0005) * 1000)
    timestamp_in_s = int(timestamp)
    timestamp_in_h = int(timestamp_in_s / 3600)
    hours = timestamp_in_h
    remaining_s = timestamp_in_s - (hours * 3600)
    minutes = int(remaining_s / 60)
    remaining_s = remaining_s - (minutes * 60)
    return "%02d:%02d:%02d.%03d" % (hours, minutes, remaining_s, ms)



def is_combination_possible(frames, db_combine):
    # For each frame no, verify whether combine could be done
    for f in frames['fgd']:
        if f['no'] not in db_combine.keys():
            print("Info: combination is not possible")
            return False
    print("Info: combination is possible")
    return True




def create_framelist_from_shot(db:dict, shot) -> list:
    """This function returns a list of all frames that shall be
    processed (extracted, sharpened, etc.) for this shot

    Args:
        db: global database
        shot: the shot that contains properties to generate the list

    Returns:
        list of frames

    """
    # print("%s.create_framelist_from_shot" % (__name__))
    frames_count = shot['count']
    framelist = list()
    # Create a list which contains properties for each frame
    for i in range(frames_count):
        f = {
            'shot_no': shot['no'],
            'no': shot['start'] + i,
            'ref': shot['ref'] + i,
            'filters': shot['filters'],
            'tasks': shot['tasks'].copy(),
            'layer': shot['layer'],
            'dimensions': shot['dimensions'].copy(),
            'geometry': None if 'geometry' not in shot.keys() else shot['geometry'],
            'curves': None if 'curves' not in shot.keys() else shot['curves'],
        }
        f['filepath'] = get_output_frame_filepaths(db, shot=shot, frame_no=f['ref'])
        framelist.append(f)

    return framelist



def patch_frames_for_stitching(frames, db_combine, do_combine=False):
    # print_combine_database(db_combine, k_ep=layers['bgd']['shot']['k_ep'])

    if do_combine:
        for f_fgd, f_bgd in zip(frames['fgd'], frames['bgd']):
            if f_fgd['no'] != f_bgd['ref']:
                sys.exit("error: frame no. differs between bgd and fgd")

            # Patch filepath/layer for foreground/background
            f_fgd['filepath']['bgd'] = f_bgd['filepath']['bgd']

            # Remove 'bgd' from tasks
            if 'bgd' in f_fgd['tasks']:
                f_fgd['tasks'].remove('bgd')

            # Remove tasks which should not be done for bacground image
            for t in ['stitching', 'sharpen', 'rgb', 'geometry']:
                if t in f_bgd['tasks']:
                    f_bgd['tasks'].remove(t)

            if f_bgd['layer'] == 'bgd':
                f_ref = f_bgd['ref']

                if f_ref in db_combine.keys():
                    # print("+++ %d :" % (f_ref), db_combine[f_ref])
                    # Add combine values to the fgd layer
                    f_fgd['stitching'] = {'geometry': db_combine[f_ref]['geometry'].copy()}

                    if 'bgd' in f_bgd['tasks']:
                        # Add rgb correction ('bgd') for background image if in tasks
                        bgd_curve = db_combine[f_ref]['curve']
                        if bgd_curve is not None:
                            f_bgd['stitching'] = {'curve': db_combine[f_ref]['curve']}
                    else:
                        # No curve defined: remove 'bgd' task
                        f_fgd['filepath']['bgd'] = f_bgd['filepath']['denoise']

                else:
                    # No combine/curve defined: remove 'bgd' task from bgd and combine from fgd
                    # print("no combine?")
                    for t in ['bgd', 'stitching']:
                        if t in f_bgd['tasks']:
                            f_bgd['tasks'].remove(t)
    else:
        for f_fgd in frames['fgd']:
            for t in ['bgd', 'stitching']:
                if t in f_fgd['tasks']:
                    f_fgd['tasks'].remove(t)
            f_fgd['filepath']['stitching'] = f_fgd['filepath']['denoise']


