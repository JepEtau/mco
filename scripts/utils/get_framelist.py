#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from pprint import pprint

from utils.common import get_shot_from_frame_no_new
from utils.get_filters import get_filter_id
from utils.path import get_output_path_from_shot
from utils.time_conversions import ms_to_frames


def _get_frames_until_effects(db, k_part, shot, suffix, count=0):
    k_part_src = shot['k_part']
    k_ep_src = shot['k_ep']
    k_ed = shot['k_ed']

    shot_start = shot['start']
    shot_count = shot['count'] if count == 0 else count

    # Replace images
    if 'replace' not in db['common']['options']['discard_tasks']:
        frames_to_replace = db[k_ep_src][k_ed][k_part_src]['video']['replace']
    else:
        # defined in discarded tasks
        frames_to_replace = dict()

    # Input folder
    if k_part in ['g_debut', 'g_fin']:
        input_folder = os.path.join(
            db[k_part]['common']['path']['cache'],
            '%05d' % (shot_start))
    else:
        pprint("last task: [%s]" % (shot['tasks'][-1]))
        input_folder = get_output_path_from_shot(db=db, shot=shot, task=shot['tasks'][-1])
        print("_get_frames_until_effects: input_folder=%s" % (input_folder))


    # Append images
    images = list()
    try:
        start = shot['dst']['start']
        end = start + shot['dst']['count']
    except:
        start = shot_start
        end = shot_start + shot_count

    for f_no in range(start, end):
        if f_no in frames_to_replace:
            filename = "%s_%05d%s" % (k_ep_src, frames_to_replace[f_no], suffix)
        else:
            filename = "%s_%05d%s" % (k_ep_src, f_no, suffix)
        p = os.path.join(input_folder, filename)
        images.append(p)

    return images



def get_framelist(db, k_ep, k_part, shot) -> list:
    """This function returns a list of images which is used
    to create concatenation files or by tools for video editing
    It is used for the following parts:
      - episode
      - reportage
    """
    images = list()

    k_part_src = shot['k_part']
    k_ep_src = shot['k_ep']
    k_ed = shot['k_ed']
    start = shot['start']
    end = start + shot['count']

    extension = db['common']['settings']['frame_format']
    # Get the filter id
    filter_id = get_filter_id(db, shot, shot['tasks'][-1])
    suffix = "__%s__%03d.%s" % (k_ed, filter_id, extension)


    # A/V sync for the first shot
    if shot['no'] == 0:
        db_video = db[k_ep]['common']['video'][k_part]

        black_image_filepath = os.path.join(db['common']['directories']['cache'], 'black.%s' % (extension))
        if db_video['avsync'] > 0:
            # Add black images to the first shot for A/V sync
            for i in range(db_video['avsync']):
                images.append(black_image_filepath)



    # Patch the last frame no. when a fadeout effect is used
    if 'effects' in shot.keys():

        if shot['effects'][0] == 'loop_and_fadeout':
            # print("\n%s.get_framelist (%s:%s)" % (__name__, k_ep, k_part))
            # pprint(shot)

            # Initialize values for loop/fadeout
            loop_start = shot['effects'][1]
            loop_count = shot['effects'][2]

            fadeout_count = shot['effects'][3]
            fadeout_start = shot['start'] + shot['count'] - fadeout_count

            # Append images until start of loop_and_fadeout
            if fadeout_count <= loop_count:
                shot_count = shot['count']
            else:
                shot_count = shot['count'] - (fadeout_count - loop_count)

            # Patch the dst structure to get the toatal images UNTIL effect
            if 'start' in shot['dst']:
                shot['dst']['count'] -= (fadeout_count - loop_count)
            else:
                shot['dst'].update({
                    'count': shot_count,
                    'start': shot['start'],
                })

            images += _get_frames_until_effects(db, k_part=k_part, shot=shot, suffix=suffix)
            # print("\t\t\t+ ... %s" % (images[-1]))

            if loop_count > fadeout_count:
                p = images[-1]
                for i in range(loop_count - fadeout_count):
                    # print("\t\t\t+ fadeout: %s" % (p))
                    images.append(p)

            k_part_src = shot['k_part']
            k_ep_src = shot['k_ep']
            k_ed = shot['k_ed']
            frame_no = min(loop_start, fadeout_start)
            shot_src = get_shot_from_frame_no_new(db, frame_no, k_ed, k_ep_src, k_part_src)

            if 'dst' in shot.keys():
                print("--> detected dst for the loop_and_fadeout effect -->")
                pprint(shot)
                print("")
                k_part_src = shot['k_part']
                k_ep_src = shot['dst']['k_ep']

            input_folder = os.path.join(db[k_ep_src]['common']['path']['cache'], k_part, '%05d' % (shot_src['start']))
            for f_no in range(shot_src['start'] + shot_src['count'],
                                shot_src['start'] + shot_src['count'] + fadeout_count):
            # for f_no in range(end, end + fadeout_count):
                filename = "%s_%05d%s" % (shot['k_ep'], f_no, suffix)
                p = os.path.join(input_folder, filename)
                images.append(p)
                # print("\t\t\t+ fadeout: %s" % (p))


        elif shot['effects'][0] == 'fadeout':
            # print("\n%s.get_framelist (%s:%s)" % (__name__, k_ep, k_part))
            # pprint(shot)
            frame_no = shot['effects'][1]
            fadeout_start = end
            fadeout_count = shot['effects'][2]
            # print("\t\tfadeout: fadeout %d->%d (%d)" % (
            #     fadeout_start, fadeout_start+fadeout_count, fadeout_count))

            # Patch the dst structure to get the toatal images UNTIL effect
            if 'start' in shot['dst']:
                shot['dst']['count'] -= fadeout_count
            else:
                shot['dst'].update({
                    'count': shot['start'] - fadeout_count,
                    'start': shot['start'],
                })

            # Append images until start of fadeout
            images += _get_frames_until_effects(db, k_part=k_part, shot=shot, suffix=suffix)

            print("nb of images = %d" % (len (images)))


            # Fadeout
            k_part_src = shot['k_part']
            k_ep_src = shot['k_ep']
            k_ed = shot['k_ed']

            shot_src = get_shot_from_frame_no_new(db, frame_no, k_ed, k_ep_src, k_part_src)
            input_folder = os.path.join(db[k_ep_src]['common']['path']['cache'],
                k_part, '%05d' % (shot_src['start']))

            for f_no in range(fadeout_start, fadeout_start+fadeout_count):
                filename = "%s_%05d%s" % (k_ep_src, f_no, suffix)
                p = os.path.join(input_folder, filename)
                images.append(p)
                # print("\t\t\t+ fadeout: %s" % (p))

    else:
        images += _get_frames_until_effects(db, k_part=k_part, shot=shot, suffix=suffix)


    return images



def get_framelist_2(db, k_ep, k_part, shot) -> list:
    """This function returns a list of images which is used
    to create concatenation files or by tools for video editing
    It is used for the following parts:
        - g_debut
        - precedemment
        - g_asuivre
        - asuivre
        - g_reportage
        - g_fin
    """
    images = list()

    k_ep_src = shot['k_ep']
    k_ed = shot['k_ed']

    extension = db['common']['settings']['frame_format']

    print("%s:get_framelist_2: use %s for %s:%s" % (__name__, k_ep_src, k_ep, k_part))
    k_part_src = shot['k_part']
    if 'start' in shot['dst']:
        print("use the dst start and count for the concatenation file")
        start = shot['dst']['start']
        end = start + shot['dst']['count']
    else:
        start = shot['start']
        end = start + shot['count']


    # Get the filter id
    try:
        filter_id = get_filter_id(db, shot, shot['tasks'][-1])
    except:
        print("warning: filter for shot (start: %d) is not found for last task [%s]" % (shot['start'], shot['tasks'][-1]))
        filter_id = 999
    suffix = "__%s__%03d.%s" % (k_ed, filter_id, extension)

    # A/V sync for the first shot
    if shot['no'] == 0:
        if k_part in ['g_debut', 'g_fin']:
            db_video = db[k_part]['common']['video']
        else:
            db_video = db[k_ep]['common']['video'][k_part]

        if db_video['avsync'] != 0 and k_part != 'precedemment':
            sys.exit("get_framelist_2: avsync not supported for %d:%d" % (k_ep, k_part))

        black_image_filepath = os.path.join(db['common']['directories']['cache'], 'black.%s' % (extension))
        if db_video['avsync'] > 0:
            # Add black images to the first shot for A/V sync
            for i in range(abs(db_video['avsync'])):
                images.append(black_image_filepath)


    # Add files for effects
    if 'effects' in shot.keys():

        if shot['effects'][0] == 'loop':
            frame_no = shot['effects'][1]
            loop_count = shot['effects'][2]
            # print("\t\tloop: loop %d times on %d" % (loop_count, frame_no))

            input_folder = get_output_path_from_shot(db=db, shot=shot, task=shot['tasks'][-1])

            # Add the frames before the loop
            for f_no in range(start, end):
                filename = "%s_%05d%s" % (k_ep_src, f_no, suffix)
                p = os.path.join(input_folder, filename)
                images.append(p)

            # Add the loop
            prefix = "%s_" % (k_ep_src)
            filename = "%s%05d%s" % (prefix, frame_no, suffix)
            for i in range(loop_count):
                p = os.path.join(input_folder, filename)
                images.append(p)

        elif shot['effects'][0] == 'loop_and_fadeout':
            # print("\n%s.get_framelist (%s:%s)" % (__name__, k_ep, k_part))
            # pprint(shot)

            # Initialize values for loop/fadeout
            loop_start = shot['effects'][1]
            loop_count = shot['effects'][2]

            fadeout_count = shot['effects'][3]
            fadeout_start = shot['start'] + shot['count'] - fadeout_count

            # Append images until start of loop_and_fadeout
            if fadeout_count <= loop_count:
                shot_count = shot['count']
            else:
                shot_count = shot['count'] - (fadeout_count - loop_count)
            images += _get_frames_until_effects(db, k_part=k_part, shot=shot, suffix=suffix,
                count=shot_count)
            # print("\t\t\t+ ... %s" % (images[-1]))

            if loop_count > fadeout_count:
                p = images[-1]
                for i in range(loop_count - fadeout_count):
                    # print("\t\t\t+ fadeout: %s" % (p))
                    images.append(p)


            k_part_src = shot['k_part']
            k_ep_src = shot['k_ep']
            k_ed = shot['k_ed']
            frame_no = min(loop_start, fadeout_start)
            shot_src = get_shot_from_frame_no_new(db, frame_no, k_ed, k_ep_src, k_part_src)

            if 'dst' in shot.keys():
                print("--> detected dst for the loop_and_fadeout effect")
                k_part_src = shot['k_part']
                k_ep_src = shot['dst']['k_ep']

            # Input folder
            if k_part in ['g_debut', 'g_fin']:
                input_folder = os.path.join(db[k_part]['common']['path']['cache'])
            else:
                input_folder = os.path.join(db[k_ep_src]['common']['path']['cache'], k_part)
            input_folder = os.path.join(input_folder, '%05d' % (shot_src['start']))

            # Append images to the list
            for f_no in range(shot_src['start'] + shot_src['count'],
                                shot_src['start'] + shot_src['count'] + fadeout_count):
                filename = "%s_%05d%s" % (shot['k_ep'], f_no, suffix)
                p = os.path.join(input_folder, filename)
                images.append(p)
                # print("\t\t\t+ fadeout: %s" % (p))

        elif shot['effects'][0] == 'fadeout':
            # print("\n%s.get_framelist_2 (%s:%s)" % (__name__, k_ep, k_part))
            # pprint(shot)
            frame_no = shot['effects'][1]
            fadeout_start = end
            fadeout_count = shot['effects'][2]
            # print("\t\tfadeout: fadeout %d->%d (%d)" % (fadeout_start, fadeout_start+fadeout_count, fadeout_count))


            # Patch the dst structure to get the toatal images UNTIL effect
            if 'start' in shot['dst']:
                shot['dst']['count'] -= fadeout_count
            else:
                shot['dst'].update({
                    'count': shot['start'] - fadeout_count,
                    'start': shot['start'],
                })

            # Append images until start of fadeout
            images += _get_frames_until_effects(db,
                k_part=k_part, shot=shot, suffix=suffix)


            # Add the frames generated by the fadeout effect
            # k_ep_dst = k_ep
            # k_part_dst = k_part
            if 'dst' in shot.keys():
                print("--> detected dst for the fadeout effect")
                pprint(shot)
                print("")
                sys.exit()
                # Use dst folder
                k_ep_dst = shot['dst']['k_ep']
                k_part_dst = shot['dst']['k_part']

                frame_no = shot['start'] + shot['count']
                shot_src = get_shot_from_frame_no_new(db, shot['start'], k_ed, k_ep_src, k_part_src)
                input_folder = os.path.join(db[k_ep_dst]['common']['path']['cache'], k_part_dst, '%05d' % (shot_src['start']))
                for f_no in range(shot_src['start'] + shot_src['count'],
                                    shot_src['start'] + shot_src['count'] + fadeout_count):
                    filename = "%s_%05d%s" % (k_ep_src, f_no, suffix)
                    p = os.path.join(input_folder, filename)
                    images.append(p)
                    # print("\t\t\t+ fadeout: %s" % (p))

            else:
                # Use src folder
                k_ed = shot['k_ed']
                k_ep_src = shot['k_ep']
                k_part_src = shot['k_part']

                shot_src = get_shot_from_frame_no_new(db, frame_no, k_ed, k_ep_src, k_part_src)
                input_folder = os.path.join(db[k_ep_src]['common']['path']['cache'], k_part, '%05d' % (shot_src['start']))
                for f_no in range(fadeout_start, fadeout_start+fadeout_count):
                    filename = "%s_%05d%s" % (k_ep_src, f_no, suffix)
                    p = os.path.join(input_folder, filename)
                    images.append(p)
                    # print("\t\t\t+ fadeout: %s" % (p))

    else:
        images += _get_frames_until_effects(db,
            k_part=k_part, shot=shot, suffix=suffix)



    # Append silence to this part
    if k_part in ['g_debut', 'g_fin'] and 'last' in shot.keys():
        if 'silence' in db[k_part]['common']['audio'].keys():
            # Add black frames to the files
            black_image_filepath = os.path.join(db['common']['directories']['cache'],
                'black.%s' % (db['common']['settings']['frame_format']))
            silence_count = ms_to_frames(db[k_part]['common']['audio']['silence'])
            # print("add black images: %d" % (silence_count))
            for i in range(silence_count):
                images.append(black_image_filepath)

    return images


