# -*- coding: utf-8 -*-
import sys
import os
from pprint import pprint

from processing_chain.get_image_list import (
    FILENAME_TEMPLATE,
    STEP_INC,
    get_image_list_pre_replace,
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
    # print_yellow("get_frame_file_paths_until_effects: output folder: %s" % (current_output_folder))
        # pprint("last task: [%s]" % (shot['tasks'][-1]))
        # print("get_frame_file_paths_until_effects: input_folder=%s" % (input_folder))


    # Append images
    if 'segments' in shot['src'].keys() and len(shot['src']['segments']) > 0:
        index_start = 0
        index_end = shot['dst']['count']
    else:
        index_start = max(0, shot['src']['start'] - shot['start'])
        index_end = index_start + shot['dst']['count']

    step_no = shot['last_step']['step_no']
    hash = shot['last_step']['hash']

    if hash == '':
        # Last filter is null, use previous one?
        return list()
        # step_no -= STEP_INC
        print_red("Error:last filter has a null hash value!")
        pprint(shot['filters'])
        # sys.exit()
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
                step_no=step_no-STEP_INC,
                hash=hash)

    else:
        if shot['last_task'] == 'edition':
            image_list = get_image_list_pre_replace(shot=shot,
                folder=current_output_folder,
                step_no=step_no,
                hash=hash)
        elif step_no == shot['last_step']['step_edition']:
            image_list = get_new_image_list(shot=shot,
                step_no=step_no,
                hash=shot['filters'][step_no - STEP_INC]['hash'])
        else:
            image_list = get_image_list(shot=shot,
                folder=current_output_folder,
                step_no=step_no,
                hash=hash)

    # pprint(image_list)
    # print(lightcyan(f"{index_start} -> {index_end}"))
    return image_list[index_start:index_end]



def get_frame_list(db, k_ep, k_part, shot) -> list:
    """This function returns a list of images which is used
    to create concatenation files or by tools for video editing
    It is used for the following parts:
      - episode
      - documentaire
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
            black_image_filepath = os.path.join(
                db['common']['directories']['cache'], 'black.png')
            if db_video['avsync'] > 0:
                # Add black images to the first shot for A/V sync
                # print("avsync: add frames for k_part=%s, avsync=%d" % (k_part, db_video['avsync']))
                for i in range(db_video['avsync']):
                    image_list.append(black_image_filepath)
    except:
        print_orange("\t\t\tinfo: discard a/v, target does not exist")


    # Add files for effects
    if 'effects' in shot.keys() and shot['last_task'] != 'edition':
        effect = shot['effects'][0]
        print_green(f"\tget frame list: effect={effect}")

        if effect == 'loop_and_fadeout':
            # Initialize values for loop/fadeout
            loop_start = shot['effects'][1]
            loop_count = shot['effects'][2]
            fadeout_count = shot['effects'][3]
            print_lightgrey(f"\tloop start={loop_start}, count={loop_count} / fadeout start=?, count={fadeout_count}")

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
            # print("\n%s.get_frame_list (%s:%s)" % (__name__, k_ep, k_part))
            # pprint(shot)
            # fadeout_start = shot['effects'][1]
            fadeout_count = shot['effects'][2]
            # print("\t\tfadeout: fadeout %d->%d (%d)" % (
            #     fadeout_start, fadeout_start+fadeout_count, fadeout_count))
            print_lightgrey(f"\tfadeout start=?, count={fadeout_count}")


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
            output_folder = os.path.join(output_folder, f"{shot['no']:03}", f"{step_no:02}")

            # Append images to the list
            shot_src_start = shot['src']['start']
            shot_src_count = shot['src']['count']
            filename_template = FILENAME_TEMPLATE % (k_ep_src, k_ed, step_no, suffix)
            if shot['last_task'] not in ['deinterlace', 'edition']:
                shot_src_start = 0

            for f_no in range(shot_src_start + shot_src_count,
                                shot_src_start + shot_src_count + fadeout_count):
                filepath = os.path.join(output_folder, filename_template % (f_no))
                image_list.append(filepath)

                # print("\t\t\t+ fadeout: %s" % (p))

        elif effect == 'loop_and_fadein':
            # fadein_start = shot['effects'][1]
            fadein_count = shot['effects'][2]
            print_lightgrey(f"\tloop and fade in start={shot['start']}, count={fadein_count}")

            # Output folder
            k_ep_dst = shot['dst']['k_ep']
            k_part_dst = shot['dst']['k_part']
            if k_part_dst in ['g_debut', 'g_fin']:
                output_folder = os.path.join(db[k_part_dst]['cache_path'])
            else:
                output_folder = os.path.join(db[k_ep_dst]['cache_path'], k_part_dst)
            output_folder = os.path.join(output_folder, f"{shot['no']:03}", f"{step_no:02}")

            # Fade in
            shot_src_start = shot['start']
            shot_src_count = shot['count']
            filename_template = FILENAME_TEMPLATE % (k_ep_src, k_ed, step_no, suffix)
            if shot['last_task'] not in ['deinterlace', 'edition']:
                shot_src_start = 0

            image_list = list()
            for f_no in range(shot_src_start + shot_src_count,
                                shot_src_start + shot_src_count + fadein_count):
                image_list.append(os.path.join(output_folder, filename_template % (f_no)))

            # List of images and remove the 1st 'fadein_count' images
            image_list += get_frame_file_paths_until_effects(db,
                k_part=k_part, shot=shot, suffix=suffix)

    else:
        image_list += get_frame_file_paths_until_effects(db,
            k_part=k_part, shot=shot, suffix=suffix)

    if k_part in ['g_debut', 'g_fin', 'precedemment']:
        # Append silence to these parts
        if ('silence' in db_video.keys()
            and shot['no'] == (len(db_video['shots']) - 1)):
            # Add black frames to the files
            black_image_filepath = os.path.join(db['common']['directories']['cache'], 'black.png')
            for i in range(db_video['silence']):
                image_list.append(black_image_filepath)

    return image_list



def get_frame_list_single(db, k_ep, k_part, shot) -> list:
    """This function returns a list of images which is used
    to create concatenation files or by tools for video editing
    It is used for the following parts:
        - precedemment
        - g_asuivre
        - asuivre
        - g_documentaire
    """
    verbose = False
    image_list = list()

    k_ed = shot['k_ed']
    k_ep_src = shot['k_ep']
    if k_part in ['g_debut', 'g_fin']:
        db_video = db[k_part]['video']
        print_yellow("CLEEEEEEEEEEEEEEEEEEEEEEEEEEEEAAAAAAAAAAAAAAAAAAAAAAAAAAANNNNNNNNNNNNNNNNNNNNNNNNNN")
    else:
        db_video = db[k_ep]['video']['target'][k_part]

    # print("%s:get_frame_list_single: use %s for %s:%s" % (__name__, k_ep_src, k_ep, k_part))
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
                sys.exit(print_red("get_frame_list_single: avsync not supported for %s:%s" % (k_ep, k_part)))

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
        print_green(f"\tget frame list (single): effect={effect}")

        if effect == 'loop':
            frame_no = shot['effects'][1]
            loop_count = shot['effects'][2]
            print_lightgrey(f"\tloop {loop_count} times on {frame_no}")

            input_folder = get_output_path_from_shot(db=db,
                shot=shot, task=shot['last_task'])

            # Append the frames before the loop
            filename_template = FILENAME_TEMPLATE % (k_ep_src, k_ed, step_no, suffix)
            if shot['last_task'] not in ['deinterlace', 'edition']:
                end -= start
                start = 0
            print_orange("start=%d, end=%d" % (start, end))
            for f_no in range(start, end):
                filepath = os.path.join(input_folder, filename_template % (f_no))
                image_list.append(filepath)

            # Loop
            filename_template = FILENAME_TEMPLATE % (k_ep_src, k_ed, step_no, suffix)
            if shot['last_task'] in ['deinterlace', 'edition']:
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
            print_lightgrey("\tstart=%d, count=%d / fadeout start=?, count=%d" % (
                loop_start, loop_count, fadeout_count))

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
            shot_src_start = shot['src']['start']
            shot_src_count = shot['src']['count']
            filename_template = FILENAME_TEMPLATE % (k_ep_src, k_ed, step_no, suffix)
            if shot['last_task'] not in ['deinterlace', 'edition']:
                shot_src_start = 0

            for f_no in range(shot_src_start + shot_src_count,
                                shot_src_start + shot_src_count + fadeout_count):
                filepath = os.path.join(output_folder, filename_template % (f_no))
                image_list.append(filepath)
                # print("\t\t\t+ fadeout: %s" % (p))


        elif effect == 'fadeout':
            sys.exit(print_red("error: get_frame_list_single: effect=%s has to be verified" % (effect)))
            # print("\n%s.get_frame_list (%s:%s)" % (__name__, k_ep, k_part))
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


