# -*- coding: utf-8 -*-
import sys
import os
from pprint import pprint

from utils.hash import (
    FILENAME_TEMPLATE,
    STEP_INC,
    get_new_image_list,
    get_image_list,
)
from utils.path import get_output_path_from_shot
from utils.pretty_print import *


def get_frame_file_paths_until_effects(db, k_part, shot, suffix):
    k_ed = shot['k_ed']
    k_ep = shot['k_ep']
    k_part = shot['k_part']

    # Input folder
    current_output_folder = get_output_path_from_shot(db=db, shot=shot, task=shot['last_task'])
    print_yellow("get_frame_file_paths_until_effects: output folder: %s" % (current_output_folder))
        # pprint("last task: [%s]" % (shot['tasks'][-1]))
        # print("get_frame_file_paths_until_effects: input_folder=%s" % (input_folder))


    # Append images
    try:
        # Only a part of the src shot
        index_start = shot['src']['start'] - shot['start']
        index_end = index_start + shot['src']['count']
    except:
        # Full shot
        index_start = 0
        index_end = shot['count']

    step_no = shot['last_step']['step_no']
    hash = shot['last_step']['hash']

    if hash == '':
        # Last filter is null, use previous one
        # step_no -= STEP_INC
        previous_filter = shot['filters'][step_no-STEP_INC]
        hash = previous_filter['hash']
        if previous_filter['task'] == 'deinterlace':
            current_output_folder = get_output_path_from_shot(db=db, shot=shot, task=previous_filter['task'])
            image_list = get_image_list(shot=shot,
                folder=current_output_folder,
                step_no=step_no,
                hash=hash)
        else:
            image_list = get_image_list(shot=shot,
                folder=current_output_folder,
                step_no=STEP_REPLACE,
                hash=hash)
    else:
        if step_no == shot['last_step']['step_no_replace']:
            image_list = get_new_image_list(shot=shot,
                step_no=step_no,
                hash=shot['filters'][step_no - STEP_INC]['hash'])
        else:
            image_list = get_image_list(shot=shot,
                folder=current_output_folder,
                step_no=step_no,
                hash=hash)

    return image_list[index_start:index_end]



def get_framelist(db, k_ep, k_part, shot) -> list:
    """This function returns a list of images which is used
    to create concatenation files or by tools for video editing
    It is used for the following parts:
      - episode
      - reportage
      - g_debut, g_fin
    """
    image_list = list()

    k_ed = shot['k_ed']
    k_ep_src = shot['k_ep']
    # Target video
    if k_part in ['g_debut', 'g_fin']:
        db_video = db[k_part]['video']
    else:
        db_video = db[k_ep]['video']['target'][k_part]

    k_part_src = shot['k_part']
    if 'start' in shot['dst']:
        print_lightgreen("use the dst start and count for the concatenation file")
        start = shot['dst']['start']
        end = start + shot['dst']['count']
    else:
        start = shot['start']
        end = start + shot['count']

    # Get hash to set the suffix
    hash = shot['last_step']['hash']
    step_no = shot['last_step']['step_no']
    if hash == '':
        # Last filter is null, use previous hash
        previous_filter = shot['filters'][step_no - STEP_INC]
        hash = previous_filter['hash']
    suffix = "_%s" % (hash)

    # A/V sync for the first shot
    try:
        if shot['no'] == 0:

            black_image_filepath = os.path.join(db['common']['directories']['cache'], 'black.png')
            if db_video['avsync'] > 0:
                # Add black images to the first shot for A/V sync
                # print("avsync: add frames for k_part=%s, avsync=%d" % (k_part, db_video['avsync']))
                for i in range(db_video['avsync']):
                    image_list.append(black_image_filepath)
    except:
        sys.exit(print_red("\t\t\tinfo: discard a/v, target does not exist"))


    # Add files for effects
    if 'effects' in shot.keys():
        effect = shot['effects'][0]
        print_lightgreen("get_framelist_single: effect=%s" % (effect))

        if effect == 'loop_and_fadeout':
            # Initialize values for loop/fadeout
            loop_start = shot['effects'][1]
            loop_count = shot['effects'][2]
            fadeout_count = shot['effects'][3]
            print_lightgreen("\t%s: loop start=%d, count=%d / fadeout start=?, count=%d" % (
                effect, loop_start, loop_count, fadeout_count))

            # Append images until start of loop_and_fadeout
            image_list += get_frame_file_paths_until_effects(db,
                k_part=k_part, shot=shot, suffix=suffix)


            input_folder = get_output_path_from_shot(db, shot, task=shot['last_task'])
            if loop_count < fadeout_count:
                # Looping is < fading out: replace the frames before the loop
                # by the generated ones
                del image_list[loop_count - fadeout_count:]
            elif loop_count > fadeout_count:
                # Looping is > fading out: append the differences to the image list
                filename_template = FILENAME_TEMPLATE % (k_ep_src, k_ed, step_no, suffix)
                if shot['last_task'] == 'deinterlace':
                    filepath = os.path.join(input_folder, filename_template % (loop_start))
                else:
                    filepath = os.path.join(input_folder, filename_template % (loop_start - shot['start']))
                for i in range(loop_count - fadeout_count):
                    # print("\t\t\t+ loop: %s" % (p))
                    image_list.append(filepath)

            # Output folder
            k_ep_dst = shot['dst']['k_ep']
            k_part_dst = shot['dst']['k_part']
            if k_part_dst in ['g_debut', 'g_fin']:
                output_folder = os.path.join(db[k_part_dst]['cache_path'])
            else:
                output_folder = os.path.join(db[k_ep_dst]['cache_path'], k_part_dst)
            output_folder = os.path.join(output_folder,
                '%03d' % (shot['no']),
                '%02d' % (step_no))

            # Append images to the list
            shot_src_start = shot['start']
            shot_src_count = shot['count']
            filename_template = FILENAME_TEMPLATE % (k_ep_src, k_ed, step_no, suffix)
            if shot['last_task'] != 'deinterlace':
                shot_src_start = 0

            for f_no in range(shot_src_start + shot_src_count,
                                shot_src_start + shot_src_count + fadeout_count):
                filepath = os.path.join(output_folder, filename_template % (f_no))
                image_list.append(filepath)
                # print("\t\t\t+ fadeout: %s" % (p))


        elif effect == 'fadeout':
            # print("\n%s.get_framelist (%s:%s)" % (__name__, k_ep, k_part))
            # pprint(shot)
            # fadeout_start = shot['effects'][1]
            fadeout_count = shot['effects'][2]
            # print("\t\tfadeout: fadeout %d->%d (%d)" % (
            #     fadeout_start, fadeout_start+fadeout_count, fadeout_count))
            print_lightgreen("\t%s: fadeout start=?, count=%d" % (
                effect, fadeout_count))


            # Append images until start of fadeout
            image_list += get_frame_file_paths_until_effects(db,
                k_part=k_part, shot=shot, suffix=suffix)
            image_list = image_list[:-1 *fadeout_count]

            # Output folder
            k_ep_dst = shot['dst']['k_ep']
            k_part_dst = shot['dst']['k_part']
            if k_part_dst in ['g_debut', 'g_fin']:
                output_folder = os.path.join(db[k_part_dst]['cache_path'])
            else:
                output_folder = os.path.join(db[k_ep_dst]['cache_path'], k_part_dst)
            output_folder = os.path.join(output_folder,
                '%03d' % (shot['no']),
                '%02d' % (step_no))

            # Append images to the list
            shot_src_start = shot['start']
            shot_src_count = shot['count']
            filename_template = FILENAME_TEMPLATE % (k_ep_src, k_ed, step_no, suffix)
            if shot['last_task'] != 'deinterlace':
                shot_src_start = 0

            for f_no in range(shot_src_start + shot_src_count,
                                shot_src_start + shot_src_count + fadeout_count):
                filepath = os.path.join(output_folder, filename_template % (f_no))
                image_list.append(filepath)

                # print("\t\t\t+ fadeout: %s" % (p))

    else:
        image_list += get_frame_file_paths_until_effects(db,
            k_part=k_part, shot=shot, suffix=suffix)

    if k_part in ['g_debut', 'g_fin']:
    # Append silence to these parts
        if ('silence' in db_video.keys()
            and shot['no'] == (len(db_video['shots']) - 1)):
            # Add black frames to the files
            black_image_filepath = os.path.join(db['common']['directories']['cache'], 'black.png')
            for i in range(db_video['silence']):
                image_list.append(black_image_filepath)

    return image_list



def get_framelist_single(db, k_ep, k_part, shot) -> list:
    """This function returns a list of images which is used
    to create concatenation files or by tools for video editing
    It is used for the following parts:
        - precedemment
        - g_asuivre
        - asuivre
        - g_reportage
    """
    image_list = list()

    k_ed = shot['k_ed']
    k_ep_src = shot['k_ep']
    if k_part in ['g_debut', 'g_fin']:
        db_video = db[k_part]['video']
    else:
        db_video = db[k_ep]['video']['target'][k_part]

    # print("%s:get_framelist_single: use %s for %s:%s" % (__name__, k_ep_src, k_ep, k_part))
    # pprint(shot)
    k_part_src = shot['k_part']
    if 'start' in shot['dst']:
        # print("use the dst start and count for the concatenation file")
        start = shot['dst']['start']
        end = start + shot['dst']['count']
    else:
        start = shot['start']
        end = start + shot['count']

    # Get hash to set the suffix
    hash = shot['last_step']['hash']
    step_no = shot['last_step']['step_no']
    if hash == '':
        # Last filter is null, use previous hash
        previous_filter = shot['filters'][step_no - STEP_INC]
        hash = previous_filter['hash']
    suffix = "_%s" % (hash)

    # A/V sync for the first shot
    try:
        if shot['no'] == 0:
            if db_video['avsync'] != 0 and k_part != 'precedemment':
                sys.exit(print_red("get_framelist_single: avsync not supported for %s:%s" % (k_ep, k_part)))

            black_image_filepath = os.path.join(db['common']['directories']['cache'], 'black.png')
            if db_video['avsync'] > 0:
                # print("avsync: add frames for k_part=%s, avsync=%d" % (k_part, db_video['avsync']))
                # Add black images to the first shot for A/V sync
                for i in range(abs(db_video['avsync'])):
                    image_list.append(black_image_filepath)
    except:
        sys.exit(print_red("\t\t\tinfo: discard a/v, target does not exist"))


    # Add files for effects
    if 'effects' in shot.keys():
        effect = shot['effects'][0]
        print_lightgreen("get_framelist_single: effect=%s" % (effect))

        if effect == 'loop':
            frame_no = shot['effects'][1]
            loop_count = shot['effects'][2]
            print_lightgreen("\tloop: loop %d times on %d" % (loop_count, frame_no))

            input_folder = get_output_path_from_shot(db=db,
                shot=shot, task=shot['last_task'])

            # Append the frames before the loop
            filename_template = FILENAME_TEMPLATE % (k_ep_src, k_ed, step_no, suffix)
            if shot['last_task'] != 'deinterlace':
                end -= start
                start = 0
            print_orange("start=%d, end=%d" % (start, end))
            for f_no in range(start, end):
                filepath = os.path.join(input_folder, filename_template % (f_no))
                image_list.append(filepath)

            # Loop
            filename_template = FILENAME_TEMPLATE % (k_ep_src, k_ed, step_no, suffix)
            if shot['last_task'] == 'deinterlace':
                filepath = os.path.join(input_folder, filename_template % (frame_no))
            else:
                filepath = os.path.join(input_folder, filename_template % (frame_no - shot['start']))
            # print_orange("start=%d, end=%d" % (start, end))

            for i in range(loop_count):
                image_list.append(filepath)

        elif effect == 'loop_and_fadeout':
            # Initialize values for loop/fadeout
            loop_start = shot['effects'][1]
            loop_count = shot['effects'][2]
            fadeout_count = shot['effects'][3]
            print_lightgreen("\t%s: loop start=%d, count=%d / fadeout start=?, count=%d" % (
                effect, loop_start, loop_count, fadeout_count))

            # Append images until start of loop_and_fadeout
            image_list += get_frame_file_paths_until_effects(db,
                k_part=k_part, shot=shot, suffix=suffix)


            input_folder = get_output_path_from_shot(db, shot, task=shot['last_task'])
            if loop_count < fadeout_count:
                # Looping is < fading out: replace the frames before the loop
                # by the generated ones
                del image_list[loop_count - fadeout_count:]
            elif loop_count > fadeout_count:
                # Looping is > fading out: append the differences to the image list
                filename_template = FILENAME_TEMPLATE % (k_ep_src, k_ed, step_no, suffix)
                if shot['last_task'] == 'deinterlace':
                    filepath = os.path.join(input_folder, filename_template % (loop_start))
                else:
                    filepath = os.path.join(input_folder, filename_template % (loop_start - shot['start']))
                for i in range(loop_count - fadeout_count):
                    # print("\t\t\t+ loop: %s" % (p))
                    image_list.append(filepath)

            # Output folder
            k_ep_dst = shot['dst']['k_ep']
            k_part_dst = shot['dst']['k_part']
            if k_part_dst in ['g_debut', 'g_fin']:
                output_folder = os.path.join(db[k_part_dst]['cache_path'])
            else:
                output_folder = os.path.join(db[k_ep_dst]['cache_path'], k_part_dst)
            output_folder = os.path.join(output_folder,
                '%03d' % (shot['no']),
                '%02d' % (step_no))

            # Append images to the list
            shot_src_start = shot['start']
            shot_src_count = shot['count']
            filename_template = FILENAME_TEMPLATE % (k_ep_src, k_ed, step_no, suffix)
            if shot['last_task'] != 'deinterlace':
                shot_src_start = 0

            for f_no in range(shot_src_start + shot_src_count,
                                shot_src_start + shot_src_count + fadeout_count):
                filepath = os.path.join(output_folder, filename_template % (f_no))
                image_list.append(filepath)
                # print("\t\t\t+ fadeout: %s" % (p))


        elif effect == 'fadeout':
            sys.exit(print_red("error: get_framelist_single: effect=%s has to be verified" % (effect)))
            # print("\n%s.get_framelist (%s:%s)" % (__name__, k_ep, k_part))
            # pprint(shot)
            fadeout_start = shot['effects'][1]
            fadeout_count = shot['effects'][2]
            # print("\t\tfadeout: fadeout %d->%d (%d)" % (
            #     fadeout_start, fadeout_start+fadeout_count, fadeout_count))
            print_lightgreen("\t%s: fadeout start=%s, count=%d" % (
                effect, fadeout_start, fadeout_count))


            # Append images until start of fadeout
            image_list += get_frame_file_paths_until_effects(db,
                k_part=k_part, shot=shot, suffix=suffix)
            image_list = image_list[:-1 *fadeout_count]

            # Output folder
            k_ep_dst = shot['dst']['k_ep']
            k_part_dst = shot['dst']['k_part']
            if k_part_dst in ['g_debut', 'g_fin']:
                output_folder = os.path.join(db[k_part_dst]['cache_path'])
            else:
                output_folder = os.path.join(db[k_ep_dst]['cache_path'], k_part_dst)
            output_folder = os.path.join(output_folder,
                '%03d' % (shot['no']),
                '%02d' % (step_no))

            # Append images to the list
            shot_src_start = shot['start']
            shot_src_count = shot['count']
            filename_template = FILENAME_TEMPLATE % (k_ep_src, k_ed, step_no, suffix)
            if shot['last_task'] != 'deinterlace':
                shot_src_start = 0

            for f_no in range(shot_src_start + shot_src_count,
                                shot_src_start + shot_src_count + fadeout_count):
                filepath = os.path.join(output_folder, filename_template % (f_no))
                image_list.append(filepath)

    else:
        image_list += get_frame_file_paths_until_effects(db,
            k_part=k_part, shot=shot, suffix=suffix)

    # Append silence to this part
    if ('silence' in db_video.keys()
        and shot['no'] == (len(db_video['shots']) - 1)):
        # Add black frames to the files
        black_image_filepath = os.path.join(db['common']['directories']['cache'], 'black.png')
        for i in range(db_video['silence']):
            image_list.append(black_image_filepath)

    return image_list


