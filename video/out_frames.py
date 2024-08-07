from __future__ import annotations
import sys
import os
from pprint import pprint
from processing.black_frame import generate_black_frame
from scene.filters import do_watermark
from utils.images import IMG_FILENAME_TEMPLATE, Images
from utils.mco_types import Effect, Scene
from utils.mco_utils import get_cache_path, get_dirname, get_out_directory
from utils.p_print import *
from utils.logger import main_logger
from parsers import (
    db,
    key,
    task_to_dirname,
)



def get_out_frame_paths_until_effects(scene: Scene) -> list[str]:

    out_dir: str = get_out_directory(scene)
    print(yellow(f"get_out_frame_paths_until_effects: out_directory: {out_dir}"))

    # if isinstance(scene['in_frames'], Images):
    #     return scene['in_frames'].out_images()


    # print(yellow(f"get_frame_file_paths_until_effects: output folder:"), f"{current_output_folder}")
    # sys.exit()
    # Append images
    if 'segments' in scene['src'] and len(scene['src']['segments']) > 0:
        pprint(scene['src'])
        index_start = scene['src']['segments'][0]['start']
        index_end = index_start + scene['dst']['count']
    else:
        # index_start = max(0, scene['src']['start'] - scene['start'])
        index_start = scene['src']['start']
        index_end = index_start + scene['dst']['count']

    # step_no = scene['task']['step_no']
    hash = scene['task'].hashcode

    if hash == '':
        # Last filter is null, use previous one?
        # return list()
        # step_no -= 1
        print(red(f"Error: {scene['task'].name} has a null hash value!"))
        pprint(scene['filters'])
        sys.exit()
        previous_filter = scene['filters'][step_no-1]
        hash = previous_filter['hash']
        if previous_filter['task'] == 'deinterlace':
            out_dir = get_output_path_from_scene(db=db, scene=scene, task=previous_filter['task'])
            image_list = get_image_list(
                scene=scene,
                folder=out_dir,
                step_no=step_no,
                hash=hash)
        else:
            image_list = get_image_list(
                scene=scene,
                folder=out_dir,
                step_no=step_no-1,
                hash=hash)

    dirname, hashcode = get_dirname(scene, out=True)
    directory: str = os.path.join(scene['cache'], dirname)
    print(yellow(f"get_out_frame_paths_until_effects {scene['task'].name} -> {dirname}"))
    filename_template = IMG_FILENAME_TEMPLATE % (
        scene['k_ep'],
        scene['k_ed'],
        int(dirname[:2]),
        f"_{hashcode}" if hashcode != '' else ""
    )

    image_list: list[str] = []
    if scene['task'].name == 'initial':
        image_list: list[str] = list([
            os.path.join(directory, filename_template % (index_start + no))
            for no in range(scene['src']['count'])
        ])

    else:
        frame_replace = scene['replace']
        for no in range(index_start, index_end):
            out_no: int = frame_replace[no] if no in frame_replace else no
            image_list.append(os.path.join(directory, filename_template % (out_no)))

    # pprint(image_list)
    # print(len(image_list))
    # sys.exit()
    # return image_list[index_start:index_end]
    return image_list


def get_out_frame_paths(
    episode: int | str,
    chapter: str,
    scene: Scene
) -> list[str]:
    """This function returns a list of images which is used
    to create concatenation files or by tools for video editing
    It is used for the following chapters:
      - episode
      - documentaire
      - g_debut, g_fin
    """
    k_ep, k_ch = key(episode), chapter
    imgs: list[str] = []

    k_ed = scene['k_ed']
    k_ep_src = scene['k_ep']
    # Target video
    if k_ch in ('g_debut', 'g_fin'):
        db_video = db[k_ch]['video']
    else:
        db_video = db[k_ep]['video']['target'][k_ch]

    # Get hash to set the suffix
    hash: str = scene['task'].hashcode
    dirname: str = task_to_dirname[scene['task'].name]
    task_no: int = int(dirname[:2])
    suffix: str = f"_{hash}"

    # A/V sync for the first scene
    try:
        if scene['no'] == 0:
            if db_video['avsync'] != 0 and chapter != 'precedemment':
                sys.exit(print(red("get_out_frame_list_single: avsync not supported for %s:%s" % (k_ep, chapter))))

            if db_video['avsync'] > 0:
                # Add black images to the first scene for A/V sync
                # print("avsync: add frames for k_ch=%s, avsync=%d" % (k_ch, db_video['avsync']))
                black_image_filepath = os.path.join(
                    db['common']['directories']['cache'],
                    'black.png'
                )
                for _ in range(db_video['avsync']):
                    imgs.append(black_image_filepath)
    except:
        print(orange("\t\t\tinfo: discard a/v, target does not exist"))

    # Add files for effects
    if 'effects' in scene and scene['task'].name != 'initial':
        effect = scene['effects'].primary_effect()
        main_logger.debug(green(f"\tget frame list: effect={effect}"))

        if effect.name == 'loop':
            # Used by g_asuivre, g_documentaire
            frame_no = effect.frame_ref
            loop_count = effect.loop
            main_logger.debug(lightgrey(f"\tloop {loop_count} times on {frame_no}"))

            # All frames until loop effect
            imgs = get_out_frame_paths_until_effects(scene)

            # Loop
            out_dir: str = os.path.join(
                scene['cache'],
                get_dirname(scene, out=True)[0]
            )

            filename_template = IMG_FILENAME_TEMPLATE % (k_ep_src, k_ed, task_no, suffix)
            filepath = os.path.join(out_dir, filename_template % (frame_no))
            imgs.extend(list([filepath] * loop_count))

        elif effect.name == 'loop_and_fadeout':
            # Initialize values for loop/fadeout
            loop_start = effect.frame_ref
            loop_count = effect.loop
            fadeout_count = effect.fade
            main_logger.debug(
                lightgrey(f"\tloop start={loop_start}, ")
                + lightgrey(f"count={loop_count} / fadeout start={loop_start}, ")
                + lightgrey(f"count={fadeout_count}")
            )

            # Append images until start of loop_and_fadeout
            imgs += get_out_frame_paths_until_effects(scene)

            input_dir = get_out_directory(scene)
            if loop_count < fadeout_count:
                # Looping is < fading out: replace the frames before the loop
                # by the generated ones
                del imgs[loop_count - fadeout_count:]

            elif loop_count > fadeout_count:
                # Looping is > fading out: append the differences to the image list
                filename_template = IMG_FILENAME_TEMPLATE % (
                    k_ep_src, k_ed, task_no, suffix
                )
                if scene['task'].name == 'lr' and not do_watermark(scene):
                    filepath = os.path.join(
                        os.path.join(
                            get_cache_path(scene),
                            task_to_dirname['initial']),
                            filename_template % (loop_start)
                    )
                else:
                    filepath = os.path.join(input_dir, filename_template % (loop_start))

                for _ in range(loop_count - fadeout_count):
                    print(f"\t\t\t+ loop: {filepath}")
                    imgs.append(filepath)

            # Output directory
            k_ep_dst: str = scene['dst']['k_ep']
            k_ch_dst: str = scene['dst']['k_ch']
            if k_ch_dst in ('g_debut', 'g_fin'):
                out_dir: str = os.path.join(db[k_ch_dst]['cache_path'])
            else:
                out_dir: str = os.path.join(db[k_ep_dst]['cache_path'], k_ch_dst)
            out_dir = os.path.join(out_dir, f"{scene['no']:03}", dirname)

            # Append images to the list
            scene_src_start, scene_src_count = scene['start'], scene['count']
            filename_template = IMG_FILENAME_TEMPLATE % (
                k_ep_src, k_ed, task_no, suffix
            )
            # if scene['task'].name != 'deinterlace':
            #     scene_src_start = 0

            for i in range(fadeout_count):
                filepath = os.path.join(
                    out_dir,
                    filename_template % (scene_src_start + scene_src_count + i)
                )
                imgs.append(filepath)

        elif effect.name == 'fadeout':
            # print("\n%s.get_out_frame_list (%s:%s)" % (__name__, k_ep, k_ch))
            # pprint(scene)
            fadeout_count = effect.fade
            # print("\t\tfadeout: fadeout %d->%d (%d)" % (
            #     fadeout_start, fadeout_start+fadeout_count, fadeout_count))
            main_logger.debug(lightgrey(f"\tfadeout start=?, count={fadeout_count}"))

            # Append images until start of fadeout
            imgs += get_out_frame_paths_until_effects(scene)
            imgs = imgs[:-1 *fadeout_count]

            # Output folder
            k_ep_dst = scene['dst']['k_ep']
            k_ch_dst = scene['dst']['k_ch']
            if k_ch_dst in ('g_debut', 'g_fin'):
                out_dir = os.path.join(db[k_ch_dst]['cache_path'])
            else:
                out_dir = os.path.join(db[k_ep_dst]['cache_path'], k_ch_dst)
            out_dir = os.path.join(
                out_dir,
                f"{scene['no']:03}",
                dirname
            )

            # Append images to the list
            scene_src_start = scene['src']['start']
            scene_src_count = scene['src']['count']
            filename_template = IMG_FILENAME_TEMPLATE % (
                k_ep_src, k_ed, task_no, suffix
            )
            for f_no in range(
                scene_src_start + scene_src_count,
                scene_src_start + scene_src_count + fadeout_count
            ):
                filepath = os.path.join(out_dir, filename_template % (f_no))
                imgs.append(filepath)

                # print("\t\t\t+ fadeout: %s" % (p))

        elif effect.name == 'loop_and_fadein':
            fadein_count = effect.fade
            main_logger.debug(lightgrey(f"\tloop and fade in start={scene['start']}, count={fadein_count}"))
            print(yellow(f"TODO: verify loop_and_fadein"))
            raise
            # Output folder
            k_ep_dst = scene['dst']['k_ep']
            k_ch_dst = scene['dst']['k_ch']
            if k_ch_dst in ('g_debut', 'g_fin'):
                out_dir = os.path.join(db[k_ch_dst]['cache_path'])
            else:
                out_dir = os.path.join(db[k_ep_dst]['cache_path'], k_ch_dst)
            out_dir = os.path.join(
                out_dir,
                f"{scene['no']:03}",
                dirname
            )

            # Fade in
            scene_src_start = scene['start']
            scene_src_count = scene['count']
            filename_template = IMG_FILENAME_TEMPLATE % (
                k_ep_src, k_ed, task_no, suffix
            )
            if scene['task'].name not in ('deinterlace'):
                scene_src_start = 0

            imgs = list()
            for f_no in range(scene_src_start + scene_src_count,
                                scene_src_start + scene_src_count + fadein_count):
                imgs.append(
                    os.path.join(out_dir, filename_template % (f_no))
                )

            # List of images and remove the 1st 'fadein_count' images
            imgs += get_out_frame_paths_until_effects(scene)

    else:
        imgs += get_out_frame_paths_until_effects(scene)

    if k_ch in ('g_debut', 'g_fin', 'precedemment'):
        # Append silence to these parts
        if 'silence' in db_video and scene['no'] == len(db_video['scenes']) - 1:
            black_image_filepath = os.path.join(
                db['common']['directories']['cache'],
                'black.png'
            )
            for _ in range(db_video['silence']):
                imgs.append(black_image_filepath)
            generate_black_frame(black_image_filepath, imgs[0])

    return imgs



def get_out_frame_list_single(
    episode: int | str,
    chapter: str,
    scene: Scene
) -> list[str]:
    """This function returns a list of images which is used
    to create concatenation files or by tools for video editing
    It is used for the following parts:
        - precedemment
        - g_asuivre
        - asuivre
        - g_documentaire
    """
    verbose = False
    k_ep = key(episode)
    image_list: list[str] = []

    k_ed = scene['k_ed']
    k_ep_src = scene['k_ep']
    if chapter in ('g_debut', 'g_fin'):
        db_video = db[chapter]['video']
        print(yellow("CLEEEEEEEEEAAAAAAAAAAAAAAAAANNNNNNNNNNN"))
    else:
        db_video = db[k_ep]['video']['target'][chapter]

    # print("%s:get_out_frame_list_single: use %s for %s:%s" % (__name__, k_ep_src, k_ep, k_ch))
    # pprint(scene)
    # if 'start' in scene['dst']:
    #     # print("use the dst start and count for the concatenation file")
    #     start = scene['dst']['start']
    #     end = start + scene['dst']['count']
    # else:
    #     start = scene['start']
    #     end = start + scene['count']

    # Get hash to set the suffix
    hash: str = scene['task'].hashcode
    dirname: str = task_to_dirname[scene['task'].name]
    task_no: int = int(dirname[:2])
    if hash == '':
        # # Last filter is null, use previous hash
        # previous_filter = scene['filters'][step_no - 1]
        # hash = previous_filter['hash']
        raise ValueError("Error, get_out_frame_list_single, hash=null")
    suffix: str = f"_{hash}"

    # A/V sync for the first scene
    try:
        if scene['no'] == 0:
            if db_video['avsync'] != 0 and chapter != 'precedemment':
                sys.exit(print(red("get_out_frame_list_single: avsync not supported for %s:%s" % (k_ep, chapter))))

            black_image_filepath = os.path.join(db['common']['directories']['cache'], 'black.png')
            if db_video['avsync'] > 0:
                # print("avsync: add frames for k_ch=%s, avsync=%d" % (k_ch, db_video['avsync']))
                # Add black images to the first scene for A/V sync
                for i in range(abs(db_video['avsync'])):
                    image_list.append(black_image_filepath)
    except:
        # sys.exit(
        main_logger.debug(red("get_out_frame_list_single: discard a/v, target does not exist"))
        # )


    # Add files for effects
    if 'effects' in scene and scene['task'].name != 'initial':
        effect: Effect = scene['effects'].primary_effect()
        main_logger.debug(green(f"\tget frame list (single): effect={effect}"))

        if effect.name == 'loop':
            # Used by g_asuivre, g_documentaire
            frame_no = effect.frame_ref
            loop_count = effect.loop
            main_logger.debug(lightgrey(f"\tloop {loop_count} times on {frame_no}"))

            # All frames until loop effect
            image_list = get_out_frame_paths_until_effects(scene)

            # Loop
            out_dir: str = os.path.join(
                scene['cache'],
                get_dirname(scene, out=True)[0]
            )

            filename_template = IMG_FILENAME_TEMPLATE % (k_ep_src, k_ed, task_no, suffix)
            filepath = os.path.join(out_dir, filename_template % (frame_no))
            image_list.extend(list([filepath] * loop_count))

        elif effect == 'loop_and_fadeout':
            # Initialize values for loop/fadeout
            loop_start = effect.frame_ref
            loop_count = effect.loop
            fadeout_count = effect.fade
            main_logger.debug(lightgrey(
                f"\tstart={loop_start}, count={loop_count} / fadeout start=?, count={fadeout_count}"
            ))

            # Append images until start of loop_and_fadeout
            image_list += get_out_frame_paths_until_effects(scene)

            in_dir: str = get_out_directory(scene)
            if loop_count < fadeout_count:
                # Looping is < fading out: replace the frames before the loop
                # by the generated ones
                del image_list[loop_count - fadeout_count:]

            elif loop_count > fadeout_count:
                # Looping is > fading out: append the differences to the image list
                filename_template = IMG_FILENAME_TEMPLATE % (k_ep_src, k_ed, task_no, suffix)
                # if scene['task'].name == 'deinterlace':
                filepath = os.path.join(in_dir, filename_template % (loop_start))
                # else:
                #     filepath = os.path.join(input_folder, filename_template % (loop_start - scene['start']))
                for _ in range(loop_count - fadeout_count):
                    # print("\t\t\t+ loop: %s" % (p))
                    image_list.append(filepath)

            # Output folder
            k_ep_dst = scene['dst']['k_ep']
            k_ch_dst = scene['dst']['k_ch']
            if k_ch_dst in ('g_debut', 'g_fin'):
                output_folder = os.path.join(db[k_ch_dst]['cache_path'])
            else:
                output_folder = os.path.join(db[k_ep_dst]['cache_path'], k_ch_dst)
            output_folder = os.path.join(
                output_folder,
                f"{scene['no']:03}",
                dirname
            )

            # Append images to the list
            scene_src_start: int = scene['src']['start']
            scene_src_count: int = scene['src']['count'] - (fadeout_count - loop_count)
            filename_template = IMG_FILENAME_TEMPLATE % (k_ep_src, k_ed, task_no, suffix)
            # if scene['task'].name != 'deinterlace':
            #     scene_src_start = 0

            for f_no in range(
                scene_src_start + scene_src_count,
                scene_src_start + scene_src_count + fadeout_count
            ):
                image_list.append(
                    os.path.join(output_folder, filename_template % (f_no))
                )
                print(f"\t\t\t+ fadeout: {f_no}")

        elif effect.name == 'fadeout':
            sys.exit(print(red("error: get_out_frame_list_single: effect=%s has to be verified" % (effect))))
            # print("\n%s.get_out_frame_list (%s:%s)" % (__name__, k_ep, k_ch))
            # pprint(scene)
            fadeout_start = effect.frame_ref
            fadeout_count = effect.fade
            # print("\t\tfadeout: fadeout %d->%d (%d)" % (
            #     fadeout_start, fadeout_start+fadeout_count, fadeout_count))
            main_logger.debug(lightgreen("\t%s: fadeout start=%s, count=%d" % (
                effect, fadeout_start, fadeout_count)))


            # Append images until start of fadeout
            image_list += get_out_frame_paths_until_effects(scene)
            image_list = image_list[:-1 *fadeout_count]

            # Output folder
            k_ep_dst = scene['dst']['k_ep']
            k_ch_dst = scene['dst']['k_ch']
            if k_ch_dst in ('g_debut', 'g_fin'):
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
        image_list += get_out_frame_paths_until_effects(scene)

    # Append silence to this part
    if 'silence' in db_video and scene['no'] == (len(db_video['scenes']) - 1):
        # Add black frames to the files
        black_image_filepath = os.path.join(
            db['common']['directories']['cache'],
            'black.png'
        )
        for _ in range(db_video['silence']):
            image_list.append(black_image_filepath)
        generate_black_frame(black_image_filepath, image_list[0])

    return image_list


