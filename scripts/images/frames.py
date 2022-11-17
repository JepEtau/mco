# -*- coding: utf-8 -*-
import sys
from datetime import timedelta
import copy
from pprint import pprint

from utils.common import K_GENERIQUES
from utils.consolidate_shots import consolidate_shot
from utils.get_curves import get_lut_from_curves
from utils.get_filters import get_filters_from_shot
from utils.path import get_output_frame_filepaths, get_output_frame_filepaths_for_study






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






def create_framelist_for_study(db, k_ed, k_ep, k_part, tasks, force:bool=False):
    # This is an awfull function which should be reworked but no time to spend for this
    print("%s.create_framelist_for_study: %s:%s:%s" % (__name__, k_ed, k_ep, k_part))


    # Returns a list of frames for an edition (calculated with offset)
    if k_part in ['g_debut', 'g_fin']:
        try: frame_list = db[k_part]['common']['frames']
        except: return
        k_ed_ref = db[k_part]['target']['video']['src']['k_ed']
        k_ep_ref = db[k_part]['target']['video']['src']['k_ep']
    if k_part in ['g_asuivre', 'g_reportage']:
        try: frame_list = db[k_part]['common']['frames']
        except: return
        k_ed_ref = db[k_part]['target']['video']['src']['k_ed']
        k_ep_ref = db[k_part]['target']['video']['src']['k_ep']
        print("\tUse %s:%s as reference" % (k_ed_ref, k_ep_ref))
    else:
        try: frame_list = db[k_ep]['common'][k_part]['frames']
        except: return
        k_ep_ref = k_ep
        k_ed_ref = db['common']['reference']['k_ed']

    # k_ed
    if k_ed == '':
        k_ed_src = k_ed_ref
    else:
        # Use the one defined in command line
        k_ed_src = k_ed

    # k_ep
    # if k_part in ['g_debut', 'g_fin']:
    #     if k_ep != '':
    #         print("use %s as src" % (k_ep))
    #         k_ep_src = k_ep
    # else:
    #     if k_ep != '':
    #         # Use the one defined in command line
    #         print("use %s as src" % (k_ep))
    #         k_ep_src = k_ep
        # else:
        #     print("use %s as src" % (k_ep))


    for frame in frame_list:
        # print(frame)

        do_append_geometry = False
        if k_ed != '':
            # k_ed force by command line
            # print("k_ed forced to [%s]" % (k_ed))
            k_ed_src = k_ed
        elif 'k_ed' in frame.keys():
            # k_ed specified in the frame (i.e. in the config file)
            # print("k_ed in config file")
            k_ed_src = frame['k_ed']
        else:
            # k_ed not provided, so use the one specified in the shots (target)
            # print("find k_ed in edition")

            # Find shot no in k_ed_ref:k_ep_ref
            frame_ref = frame['ref']
            shots = db[k_ep_ref][k_ed_ref][k_part]['video']['shots']
            is_found = False
            for shot in shots:
                if (frame_ref >= shot['start']
                and frame_ref < (shot['start'] + shot['count'])):
                    is_found = True
                    break
            if not is_found:
                print("shot not found for frame %d in reference: %s:%s:%s" % (frame_ref, k_ed_ref, k_ep, k_part))
                continue

            # Get the shot no.
            shot_no = shot['no']

            # Get the target shot
            if k_part in ['g_debut', 'g_fin']:
                shot = db[k_part]['target']['video']['shots'][shot_no]
            else:
                shot = db[k_ep]['target']['video'][k_part]['shots'][shot_no]
            k_ed_src = shot['src']['k_ed']
            k_ep_src = shot['src']['k_ep']

            # This shot is the target, geometry is possible
            do_append_geometry = True

        # We can find the frame_no by using the specified edition
        frame['k_ed'] = k_ed_src

        # Determine k_ep
        if 'k_ep' in frame.keys():
            # Use the episode specified by the target
            print("use the k_ep [%s] specified in the common.ini" % (frame['k_ep']))
            k_ep_src = frame['k_ep']
        elif k_ep_src == 'ep00':
            print("use k_ep_ref [%s] as src to generate the frame" % (k_ep_ref))
            k_ep_src = k_ep_ref
        else:
            print("use k_ep [%s] as src to generate the frame" % (k_ep))
            k_ep_src = k_ep


        # Get frame no from frame ref
        if k_ed_src != k_ed_ref or k_ep_src != k_ep_ref:
            print("convert frame_ref into frame_no, ref = %s:%s" % (k_ed_ref, k_ep_ref))
            if 'offsets' in db[k_ep_src][k_ed_src][k_part]['video']:
                offsets = db[k_ep_src][k_ed_src][k_part]['video']['offsets']
                # print("%s:%s:%s, offsets=" % (k_ed_src, k_ep, k_part), offsets)
                for offset in offsets:
                    if offset['start'] <= frame['ref'] <= offset['end']:
                        frame['no'] = frame['ref'] + offset['offset']
                        break
            else:
                # print("No offset:")
                frame['no'] = frame['ref']
        else:
            # print("no need to convert")
            frame['no'] = frame['ref']

        # set k_ep, k_part
        frame['k_part'] = k_part
        frame['k_ep'] = k_ep_src

        # Get shot of this frame
        k_ed_f = frame['k_ed']
        k_ep_f = frame['k_ep']
        frame_no = frame['no']
        shots = db[k_ep_f][k_ed_f][k_part]['video']['shots']
        is_found = False
        for shot in shots:
            if shot['start'] <= frame_no < (shot['start'] + shot['count']):
                is_found = True
                break
        if not is_found:
            print("Error: shot not found for %s in %s:%s:%s" % (frame_no, k_ed_f, k_ep_f, k_part))


        # Update the frames with the data found in this shot
        if 'filters' not in frame.keys() or frame['filters'] == 'default':
            # Use the filters defined in shot
            frame['filters'] = shot['filters']
        # else:
            # This frame is specifying others filters

        frame.update({
            'curves': shot['curves'],
            'tasks': tasks.copy(),
            'input': db['editions'][k_ed_f]['inputs'][k_ep_f],
            'dimensions': db['editions'][k_ed_f]['dimensions'],

            # Stitching is not yet supported
            'layer': 'bgd',

            # geometry: consolidated below only if k_ep:k_ed
            # are the ones defined in the target shot
            'geometry': None,
        })

        # Consolidate filters
        frame['filters'] = get_filters_from_shot(db, frame)

        # Consolidate curves
        if frame['curves'] is not None:
            k_ep_or_g = k_part if k_part in K_GENERIQUES else k_ep
            shot['curves']['lut'] = get_lut_from_curves(db,
                                        k_ep_or_g,
                                        frame['curves']['k_curves'])

        # Output file paths, patch this frame to use the function
        frame['start'] = frame['ref']
        frame['filepath'] = get_output_frame_filepaths_for_study(db, frame=frame)

        # Remove unused tasks
        if 'bgd' in frame['tasks']:
            frame['tasks'].remove('bgd')

        # Remove stitching
        for t in ['stitching', 'stabilize']:
            if t not in frame.keys():
                try: frame['tasks'].remove(t)
                except: pass

        # Geometry: try
        if not do_append_geometry:
            continue

        if k_part in ['g_debut', 'g_fin']:
            k_ep_src = db[k_part]['target']['video']['src']['k_ep']
            k_ed_src = db[k_part]['target']['video']['src']['k_ed']
            frame['geometry'] = {
                'part': db[k_ep_src][k_ed_src][k_part]['video']['geometry'],
            }
            # Add a different geometry because it is not the same k_ed:k_ep
            if k_ed_f != k_ed_src or k_ep_f != k_ep_src:
                frame['geometry'].update({
                    'custom': db[k_ep_f][k_ed_f][k_part]['video']['geometry'],
                })
        elif k_part in ['g_asuivre', 'g_reportage']:
            print("create_framelist_for_study: verify geometry for %s" % (k_part))
            k_ep_src = frame['k_ep']
            k_ed_src = frame['k_ed']
            print("get geometry from part %s:%s:%s" % (k_ed, k_ep, k_part[2:]))
            frame['geometry'] = {
                'part':  db[k_ep][k_ed_f][k_part[2:]]['video']['geometry'],
                'custom': db[k_ep][k_ed_f][k_part]['video']['geometry'],
            }
        # else:
            # TODO once the shot geometry will be implemented or use the part
            # refer to consolidate_shot function

    return frame_list


