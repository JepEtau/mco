import sys
import os
from pprint import pprint

IMG_FILENAME_TEMPLATE = "%s_%%05d__%s__%02d%s.png"

# from processing_chain.get_image_list import (
#     get_image_list_pre_replace,
#     get_new_image_list,
#     get_image_list,
# )
from utils.mco_types import Scene
from utils.mco_utils import get_out_dirname
from utils.p_print import *
from parsers import db


def get_frame_file_paths_until_effects(chapter: str, scene: Scene, suffix: str):
    k_ed = scene['k_ed']
    k_ep = scene['k_ep']
    chapter = scene['k_ch']

    # Input folder
    current_output_folder = get_out_dirname(scene=scene, task=scene['task'].name)

    # print(yellow("get_frame_file_paths_until_effects: output folder: %s" % (current_output_folder)))
        # pprint("last task: [%s]" % (scene['tasks'][-1]))
        # print("get_frame_file_paths_until_effects: input_folder=%s" % (input_folder))

    # Append images
    if 'segments' in scene['src'] and len(scene['src']['segments']) > 0:
        index_start = 0
        index_end = scene['dst']['count']
    else:
        index_start = max(0, scene['src']['start'] - scene['start'])
        index_end = index_start + scene['dst']['count']

    # step_no = scene['task']['step_no']
    hash = scene['task'].hash

    if hash == '':
        # Last filter is null, use previous one?
        return list()
        # step_no -= 1
        print(red("Error:last filter has a null hash value!"))
        pprint(scene['filters'])
        # sys.exit()
        previous_filter = scene['filters'][step_no-1]
        hash = previous_filter['hash']
        if previous_filter['task'] == 'deinterlace':
            current_output_folder = get_output_path_from_scene(db=db, scene=scene, task=previous_filter['task'])
            image_list = get_image_list(
                scene=scene,
                folder=current_output_folder,
                step_no=step_no,
                hash=hash)
        else:
            image_list = get_image_list(
                scene=scene,
                folder=current_output_folder,
                step_no=step_no-1,
                hash=hash)

    else:
        if scene['task'].name == 'deinterlace':
            image_list = get_image_list_pre_replace(
                scene=scene,
                folder=current_output_folder,
                step_no=step_no,
                hash=hash
            )

        elif step_no == scene['task']['step_edition']:
            image_list = get_new_image_list(
                scene=scene,
                step_no=step_no,
                hash=scene['filters'][step_no - 1]['hash']
            )

        else:
            image_list = get_image_list(
                scene=scene,
                folder=current_output_folder,
                step_no=step_no,
                hash=hash
            )

    # pprint(image_list)
    # print(lightcyan(f"{index_start} -> {index_end}"))
    return image_list[index_start:index_end]



def get_frame_list(k_ep: str, k_ch: str, scene: Scene) -> list[str]:
    """This function returns a list of images which is used
    to create concatenation files or by tools for video editing
    It is used for the following parts:
      - episode
      - documentaire
      - g_debut, g_fin
    """
    image_list: list[str] = []

    k_ed = scene['k_ed']
    k_ep_src = scene['k_ep']
    # Target video
    if k_ch in ['g_debut', 'g_fin']:
        db_video = db[k_ch]['video']
    else:
        db_video = db[k_ep]['video']['target'][k_ch]

    # Get hash to set the suffix
    hash: str = scene['task'].hash
    # step_no = scene['task']['step_no']
    # if hash == '':
    #     # Last filter is null, use previous hash
    #     previous_filter = scene['filters'][step_no - 1]
    #     hash = previous_filter['hash']
    suffix: str = f"_{hash}"

    # A/V sync for the first scene
    try:
        if scene['no'] == 0:
            black_image_filepath = os.path.join(
                db['common']['directories']['cache'],
                'black.png'
            )
            if db_video['avsync'] > 0:
                # Add black images to the first scene for A/V sync
                # print("avsync: add frames for k_part=%s, avsync=%d" % (k_part, db_video['avsync']))
                for _ in range(db_video['avsync']):
                    image_list.append(black_image_filepath)
    except:
        print(orange("\t\t\tinfo: discard a/v, target does not exist"))


    # Add files for effects
    if 'effects' in scene.keys() and scene['task'].name != 'edition':
        effect = scene['effects'][0]
        print(green(f"\tget frame list: effect={effect}"))

        if effect == 'loop_and_fadeout':
            # Initialize values for loop/fadeout
            loop_start = scene['effects'][1]
            loop_count = scene['effects'][2]
            fadeout_count = scene['effects'][3]
            print(lightgrey(
                f"\tloop start={loop_start}, count={loop_count} / fadeout start=?, count={fadeout_count}"
            ))

            # Append images until start of loop_and_fadeout
            image_list += get_frame_file_paths_until_effects(
                chapter=k_ch, scene=scene, suffix=suffix
            )

            input_folder = get_output_path_from_scene(db, scene, task=scene['task'].name)
            if loop_count < fadeout_count:
                # Looping is < fading out: replace the frames before the loop
                # by the generated ones
                del image_list[loop_count - fadeout_count:]
            elif loop_count > fadeout_count:
                # Looping is > fading out: append the differences to the image list
                filename_template = IMG_FILENAME_TEMPLATE % (k_ep_src, k_ed, step_no, suffix)
                if scene['task'].name == 'deinterlace':
                    filepath = os.path.join(input_folder, filename_template % (loop_start))
                else:
                    filepath = os.path.join(input_folder, filename_template % (loop_start - scene['start']))
                for i in range(loop_count - fadeout_count):
                    # print("\t\t\t+ loop: %s" % (p))
                    image_list.append(filepath)

            # Output folder
            k_ep_dst: str = scene['dst']['k_ep']
            k_ch_dst: str = scene['dst']['k_ch']
            if k_ch_dst in ['g_debut', 'g_fin']:
                output_folder: str = os.path.join(db[k_ch_dst]['cache_path'])
            else:
                output_folder: str = os.path.join(db[k_ep_dst]['cache_path'], k_ch_dst)
            output_folder = os.path.join(
                output_folder, f"{scene['no']:03}", f"{step_no:02}"
            )

            # Append images to the list
            scene_src_start, scene_src_count = scene['start'], scene['count']
            filename_template = IMG_FILENAME_TEMPLATE % (k_ep_src, k_ed, step_no, suffix)
            if scene['task'].name != 'deinterlace':
                scene_src_start = 0

            for f_no in range(
                scene_src_start + scene_src_count,
                scene_src_start + scene_src_count + fadeout_count
            ):
                filepath = os.path.join(output_folder, filename_template % (f_no))
                image_list.append(filepath)
                # print("\t\t\t+ fadeout: %s" % (p))

        elif effect == 'fadeout':
            # print("\n%s.get_frame_list (%s:%s)" % (__name__, k_ep, k_part))
            # pprint(scene)
            # fadeout_start = scene['effects'][1]
            fadeout_count = scene['effects'][2]
            # print("\t\tfadeout: fadeout %d->%d (%d)" % (
            #     fadeout_start, fadeout_start+fadeout_count, fadeout_count))
            print(lightgrey(f"\tfadeout start=?, count={fadeout_count}"))


            # Append images until start of fadeout
            image_list += get_frame_file_paths_until_effects(db,
                chapter=k_ch, scene=scene, suffix=suffix)
            image_list = image_list[:-1 *fadeout_count]

            # Output folder
            k_ep_dst = scene['dst']['k_ep']
            k_ch_dst = scene['dst']['k_ch']
            if k_ch_dst in ['g_debut', 'g_fin']:
                output_folder = os.path.join(db[k_ch_dst]['cache_path'])
            else:
                output_folder = os.path.join(db[k_ep_dst]['cache_path'], k_ch_dst)
            output_folder = os.path.join(output_folder, f"{scene['no']:03}", f"{step_no:02}")

            # Append images to the list
            scene_src_start = scene['src']['start']
            scene_src_count = scene['src']['count']
            filename_template = IMG_FILENAME_TEMPLATE % (k_ep_src, k_ed, step_no, suffix)
            if scene['task'].name not in ('deinterlace'):
                scene_src_start = 0

            for f_no in range(scene_src_start + scene_src_count,
                                scene_src_start + scene_src_count + fadeout_count):
                filepath = os.path.join(output_folder, filename_template % (f_no))
                image_list.append(filepath)

                # print("\t\t\t+ fadeout: %s" % (p))

        elif effect == 'loop_and_fadein':
            # fadein_start = scene['effects'][1]
            fadein_count = scene['effects'][2]
            print(lightgrey(f"\tloop and fade in start={scene['start']}, count={fadein_count}"))

            # Output folder
            k_ep_dst = scene['dst']['k_ep']
            k_ch_dst = scene['dst']['k_ch']
            if k_ch_dst in ['g_debut', 'g_fin']:
                output_folder = os.path.join(db[k_ch_dst]['cache_path'])
            else:
                output_folder = os.path.join(db[k_ep_dst]['cache_path'], k_ch_dst)
            output_folder = os.path.join(output_folder, f"{scene['no']:03}", f"{step_no:02}")

            # Fade in
            scene_src_start = scene['start']
            scene_src_count = scene['count']
            filename_template = IMG_FILENAME_TEMPLATE % (k_ep_src, k_ed, step_no, suffix)
            if scene['task'].name not in ('deinterlace'):
                scene_src_start = 0

            image_list = list()
            for f_no in range(scene_src_start + scene_src_count,
                                scene_src_start + scene_src_count + fadein_count):
                image_list.append(os.path.join(output_folder, filename_template % (f_no)))

            # List of images and remove the 1st 'fadein_count' images
            image_list += get_frame_file_paths_until_effects(db,
                chapter=k_ch, scene=scene, suffix=suffix)

    else:
        image_list += get_frame_file_paths_until_effects(
            chapter=k_ch, scene=scene, suffix=suffix
        )

    if k_ch in ['g_debut', 'g_fin', 'precedemment']:
        # Append silence to these parts
        if 'silence' in db_video and scene['no'] == (len(db_video['scenes']) - 1):
            black_image_filepath = os.path.join(
                db['common']['directories']['cache'], 'black.png'
            )
            for _ in range(db_video['silence']):
                image_list.append(black_image_filepath)

    return image_list



def get_frame_list_single(k_ep: str, chapter: str, scene: Scene) -> list:
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

    k_ed = scene['k_ed']
    k_ep_src = scene['k_ep']
    if chapter in ['g_debut', 'g_fin']:
        db_video = db[chapter]['video']
        print(yellow("CLEEEEEEEEEAAAAAAAAAAAAAAAAANNNNNNNNNNN"))
    else:
        db_video = db[k_ep]['video']['target'][chapter]

    # print("%s:get_frame_list_single: use %s for %s:%s" % (__name__, k_ep_src, k_ep, k_part))
    # pprint(scene)
    if 'start' in scene['dst']:
        # print("use the dst start and count for the concatenation file")
        start = scene['dst']['start']
        end = start + scene['dst']['count']
    else:
        start = scene['start']
        end = start + scene['count']

    # Get hash to set the suffix
    hash: str = scene['task']['hash']
    step_no = scene['task']['step_no']
    if hash == '':
        # Last filter is null, use previous hash
        previous_filter = scene['filters'][step_no - 1]
        hash = previous_filter['hash']
    suffix: str = f"_{hash}"

    # A/V sync for the first scene
    try:
        if scene['no'] == 0:
            if db_video['avsync'] != 0 and chapter != 'precedemment':
                sys.exit(print(red("get_frame_list_single: avsync not supported for %s:%s" % (k_ep, chapter))))

            black_image_filepath = os.path.join(db['common']['directories']['cache'], 'black.png')
            if db_video['avsync'] > 0:
                # print("avsync: add frames for k_part=%s, avsync=%d" % (k_part, db_video['avsync']))
                # Add black images to the first scene for A/V sync
                for i in range(abs(db_video['avsync'])):
                    image_list.append(black_image_filepath)
    except:
        sys.exit(print(red("\t\t\tinfo: discard a/v, target does not exist")))


    # Add files for effects
    if 'effects' in scene.keys():
        effect = scene['effects'][0]
        print(green(f"\tget frame list (single): effect={effect}"))

        if effect == 'loop':
            frame_no = scene['effects'][1]
            loop_count = scene['effects'][2]
            print(lightgrey(f"\tloop {loop_count} times on {frame_no}"))

            input_folder = get_out_dirname(scene, task=scene['task'].name)

            # Append the frames before the loop
            filename_template = IMG_FILENAME_TEMPLATE % (k_ep_src, k_ed, step_no, suffix)
            if scene['task'].name not in ('deinterlace'):
                end -= start
                start = 0
            print(orange("start=%d, end=%d" % (start, end)))
            for f_no in range(start, end):
                filepath = os.path.join(input_folder, filename_template % (f_no))
                image_list.append(filepath)

            # Loop
            filename_template = IMG_FILENAME_TEMPLATE % (k_ep_src, k_ed, step_no, suffix)
            if scene['task'].name in ('deinterlace'):
                filepath = os.path.join(input_folder, filename_template % (frame_no))
            else:
                filepath = os.path.join(input_folder, filename_template % (frame_no - scene['start']))
            # print(orange("start=%d, end=%d" % (start, end)))

            for i in range(loop_count):
                image_list.append(filepath)

        elif effect == 'loop_and_fadeout':
            # Initialize values for loop/fadeout
            loop_start = scene['effects'][1]
            loop_count = scene['effects'][2]
            fadeout_count = scene['effects'][3]
            print(lightgrey(
                f"\tstart={loop_start}, count={loop_count} / fadeout start=?, count={fadeout_count}"
            ))

            # Append images until start of loop_and_fadeout
            image_list += get_frame_file_paths_until_effects(
                chapter=chapter, scene=scene, suffix=suffix
            )


            input_folder = get_out_dirname(scene, task=scene['task'].name)
            if loop_count < fadeout_count:
                # Looping is < fading out: replace the frames before the loop
                # by the generated ones
                del image_list[loop_count - fadeout_count:]

            elif loop_count > fadeout_count:
                # Looping is > fading out: append the differences to the image list
                filename_template = IMG_FILENAME_TEMPLATE % (k_ep_src, k_ed, step_no, suffix)
                if scene['task'].name == 'deinterlace':
                    filepath = os.path.join(input_folder, filename_template % (loop_start))
                else:
                    filepath = os.path.join(input_folder, filename_template % (loop_start - scene['start']))
                for _ in range(loop_count - fadeout_count):
                    # print("\t\t\t+ loop: %s" % (p))
                    image_list.append(filepath)

            # Output folder
            k_ep_dst = scene['dst']['k_ep']
            k_ch_dst = scene['dst']['k_ch']
            if k_ch_dst in ['g_debut', 'g_fin']:
                output_folder = os.path.join(db[k_ch_dst]['cache_path'])
            else:
                output_folder = os.path.join(db[k_ep_dst]['cache_path'], k_ch_dst)
            output_folder = os.path.join(
                output_folder,
                f"{scene['no']:03}",
                f"{step_no:02d}"
            )

            # Append images to the list
            scene_src_start, scene_src_count = scene['src']['start'], scene['src']['count']
            filename_template = IMG_FILENAME_TEMPLATE % (k_ep_src, k_ed, step_no, suffix)
            if scene['task'].name != 'deinterlace':
                scene_src_start = 0

            for f_no in range(
                scene_src_start + scene_src_count,
                scene_src_start + scene_src_count + fadeout_count
            ):
                image_list.append(
                    os.path.join(output_folder, filename_template % (f_no))
                )
                # print("\t\t\t+ fadeout: %s" % (p))


        elif effect == 'fadeout':
            sys.exit(print(red("error: get_frame_list_single: effect=%s has to be verified" % (effect))))
            # print("\n%s.get_frame_list (%s:%s)" % (__name__, k_ep, k_part))
            # pprint(scene)
            fadeout_start = scene['effects'][1]
            fadeout_count = scene['effects'][2]
            # print("\t\tfadeout: fadeout %d->%d (%d)" % (
            #     fadeout_start, fadeout_start+fadeout_count, fadeout_count))
            print(lightgreen("\t%s: fadeout start=%s, count=%d" % (
                effect, fadeout_start, fadeout_count)))


            # Append images until start of fadeout
            image_list += get_frame_file_paths_until_effects(db,
                chapter=chapter, scene=scene, suffix=suffix)
            image_list = image_list[:-1 *fadeout_count]

            # Output folder
            k_ep_dst = scene['dst']['k_ep']
            k_ch_dst = scene['dst']['k_ch']
            if k_ch_dst in ['g_debut', 'g_fin']:
                output_folder = os.path.join(db[k_ch_dst]['cache_path'])
            else:
                output_folder = os.path.join(db[k_ep_dst]['cache_path'], k_ch_dst)
            output_folder = os.path.join(output_folder,
                '%03d' % (scene['no']),
                '%02d' % (step_no))

            # Append images to the list
            scene_src_start = scene['start']
            scene_src_count = scene['count']
            filename_template = IMG_FILENAME_TEMPLATE % (k_ep_src, k_ed, step_no, suffix)
            if scene['task'].name != 'deinterlace':
                scene_src_start = 0

            for f_no in range(scene_src_start + scene_src_count,
                                scene_src_start + scene_src_count + fadeout_count):
                filepath = os.path.join(output_folder, filename_template % (f_no))
                image_list.append(filepath)

    else:
        image_list += get_frame_file_paths_until_effects(
            chapter=chapter, scene=scene, suffix=suffix
        )

    # Append silence to this part
    if 'silence' in db_video and scene['no'] == (len(db_video['scenes']) - 1):
        # Add black frames to the files
        black_image_filepath = os.path.join(
            db['common']['directories']['cache'],
            'black.png'
        )
        for _ in range(db_video['silence']):
            image_list.append(black_image_filepath)

    return image_list


