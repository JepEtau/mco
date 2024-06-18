import os
from pprint import pprint

from parsers.helpers import get_fps

from processing.black_frame import generate_black_frame
from utils.mco_types import Scene, VideoChapter
# Audio, VideoPart
from utils.mco_utils import makedirs
from utils.p_print import *
from utils.logger import main_logger
# from utils.types import
from parsers import (
    db,
    Chapter,
    key,
    main_chapter_keys,
    all_chapter_keys,
    ProcessingTask,
)
from utils.time_conversions import ms_to_frame
from video.out_frame_list import (
    get_out_frame_list,
    get_out_frame_list_single,
)



def generate_concat_file(
    episode: str | int,
    chapter: Chapter,
    scene: Scene,
    previous_concat_fp: str = ''
):
    k_ep, k_ch = key(episode), chapter

    # print(
    #     lightgrey(f"\tcreate concatenation file: "),
    #     lightcyan(f"{k_ep}, {k_ch}, scene no. {scene['no']}")
    # )
    # Use a single concatenation file for
    #   - g_asuivre, g_documentaire
    if k_ch in ['g_asuivre', 'g_documentaire']:
        return generate_single_concat_file(
            episode=episode,
            chapter=chapter,
            scene=scene,
            previous_concat_fp=previous_concat_fp
        )

    # This function is used for the following chapters:
    #   - episode
    #   - documentaire

    # Get the list of frames for this scene
    img_fp: list[str] = get_out_frame_list(k_ep, k_ch, scene)

    black_image_filepath = os.path.join(db['common']['directories']['cache'], 'black.png')
    generate_black_frame(black_image_filepath, img_fp[0])

    # Folder for concatenation file
    makedirs(k_ep, k_ch, 'concat')

    # Open concatenation file
    k_ed = scene['k_ed']
    if previous_concat_fp == '' or len(img_fp) >= 5:
        # Use previous concatenation files because FFmpeg
        # cannot create a video file from less than 5 frames
        if k_ch in ('g_debut', 'g_fin'):
            concat_fp = os.path.join(
                db[k_ch]['cache_path'],
                "concat",
                f"{k_ch}_{scene['no']:03}__{k_ed}_{scene['k_ep']}.txt"
            )
        else:
            concat_fp = os.path.join(
                db[k_ep]['cache_path'],
                "concat",
                f"{k_ep}_{k_ch}_{scene['no']:03}__{k_ed}.txt"
            )

        # Save this filepath because it may be used for next scene
        previous_concat_fp = concat_fp
        concat_file = open(concat_fp, "w")

    else:
        print(orange(f"Use previous concatenation file: {previous_concat_fp}"))
        print(orange(f"{len(img_fp)}"))
        # print("-------------------------------------")
        # for k, v in db[k_ep]['video']['target'][k_ch].items():
        #     if k == 'scenes':
        #         continue
        #     print(f"{k}:")
        #     pprint(v)
        # sys.exit(print_red("Error or (TODO: deprecate) Use previous concatenation file: %s ?" % (previous_concatenation_filepath)))
        concat_file = open(previous_concat_fp, 'a')

    # print(f"{concatenation_filepath}")

    # Frame duration
    duration_str = "duration %.02f\n" % (1/get_fps(db))

    # Write into the concatenation file
    for p in img_fp:
        concat_file.write(f"file \'{p}\' \n")
        concat_file.write(duration_str)
    concat_file.close()

    return previous_concat_fp



def generate_single_concat_file(
    episode: int | str,
    chapter: Chapter,
    scene: Scene,
    previous_concat_fp: str = ''
):
    """This function is used for the following chs:
        - precedemment
        - g_asuivre
        - asuivre
        - g_documentaire
    """
    k_ep, k_ch = key(episode), chapter
    # print("%s.generate_single_concat_file" % (__name__))
    # pprint(scene)
    k: str = k_ep if k_ch not in ('g_debut', 'g_fin') else k_ch

    # Get the list of images
    img_fp: list[str] = get_out_frame_list_single(
        episode=episode, chapter=chapter, scene=scene
    )

    black_image_filepath = os.path.join(db['common']['directories']['cache'], 'black.png')
    generate_black_frame(black_image_filepath, img_fp[0])

    # Folder for concatenation file
    makedirs(k_ep, k_ch, 'concat')

    # Open concatenation file
    # hash = scene['last_step']['hash']
    k_ed = scene['k_ed']
    if previous_concat_fp == '':
        # Create a concatenation file
        if k_ch in ('g_debut', 'g_fin'):
            # Use the edition/episode defined as reference
            concat_fp: str = os.path.join(
                db[k]['cache_path'],
                "concat",
                f"{k}_video.txt"
            )

        else:
            concat_fp: str = os.path.join(
                db[k]['cache_path'],
                "concat",
                f"{k_ep}_{k_ch}_{0:03}__{k_ed}_{scene['src']['k_ep']}.txt"
            )
        previous_concat_fp = concat_fp
        concat_file = open(concat_fp, "w")

    else:
        # Use the previous concatenation file
        concat_file = open(previous_concat_fp, "a")

    # Frame duration
    duration_str = f"duration {1/get_fps(db):.02f}\n"

    # Write into the concatenation file
    for p in img_fp:
        concat_file.write(f"file \'{p}\' \n")
        concat_file.write(duration_str)
    concat_file.close()

    return previous_concat_fp



def generate_silence_concat_file(episode: int | str) -> dict:
    k_ep = key(episode)
    files: dict[str, list] = {}
    fps = get_fps(db)

    for k_ch in main_chapter_keys():
        files[k_ch] = []
        if k_ch not in db[k_ep]['audio']:
            continue

        db_audio = db[k_ep]['audio'][k_ch]
        if 'silence' in db_audio and db_audio['silence'] > 0:
            main_logger.debug(lightgrey(f"\t- {k_ch}"))

            task: ProcessingTask = db[k_ep]['video']['target'][k_ch]['task']

            # Convert silence duration in nb of frames
            silence_count = ms_to_frame(db_audio['silence'], fps)
            # print("silence = %d frames" % (silence_count))

            # Duration
            black_image_filepath = os.path.join(
                db['common']['directories']['cache'],
                'black.png'
            )
            duration_str = f"duration {1/fps:.02f}\n"

            # Create the concatenation file for the silence
            makedirs(k_ep, k_ch, 'concat')
            concat_fp = os.path.join(
                db[k_ep]['cache_path'],
                "concat",
                f"{k_ep}_{k_ch}_silence.txt"
            )
            concat_file = open(concat_fp, "w")

            # Add frames to the files
            for _ in range(silence_count):
                concat_file.write(f"file \'{black_image_filepath}\' \n")
                concat_file.write(duration_str)

            files[k_ch].append(concat_fp)
            concat_file.close()

    return files



def generate_video_concat_file(
    episode: int | str,
    chapter: str,
):
    """ This function creates a concatenation file which lists
        all video files to merge:
        - precedemment
        - episode
        - g_asuivre
        - asuivre
        - g_documentaire
        - documentaire

        Returns:
          Concatenation file path
    """
    k_ep, k_ch = key(episode), chapter
    verbose: bool = False
    main_logger.debug(f"create_video_concat_file {k_ep}:{k_ch}")

    # Assume language is same for k_ep and start/end/to_follow/documentary credits
    if k_ch in ('g_debut', 'g_fin'):
        language = db[k_ch]['audio']['lang']
    else:
        language = db[k_ep]['audio']['lang']
    lang_str = '' if language == 'fr' else f"_{language}"

    for k_ep_or_g in [k_ep, 'g_debut', 'g_fin']:
        if k_ep_or_g is None:
            continue

        if k_ep_or_g in ('g_debut', 'g_fin'):
            k_ch = k_ep_or_g
            suffix = f"{k_ch}"
        else:
            suffix = f"_{k_ch}" if k_ch != '' else ''
            suffix = f"{k_ep}{suffix}_video"
            k_ep_or_g = k_ep
            # k_ch = ''

        # Folder used to store concatenation file
        makedirs(k_ep, k_ch, 'concat')

        # Open concatenation file
        concat_fp = os.path.join(
            db[k_ep_or_g]['cache_path'],
            "concat",
            f"{suffix}{lang_str}.txt")
        concat_file = open(concat_fp, "w")
        if verbose:
            print(green(f"create_video_concat_file: {concat_fp}"))

        if k_ep_or_g in ('g_debut', 'g_fin'):
            video: VideoChapter = db[k]['video']
            pprint(video)
            concat_file.write(f"file \'{video['task'].video_file}\' \n")
            audio = db[k_ep]['audio'][k]
            if 'silence' in audio and audio['silence'] > 0:
                silence_fp: str = os.path.join(
                    db[k_ep]['cache_path'],
                    "video",
                    f"{k_ep}_{k}_silence.mkv"
                )
                concat_file.write(f"file \'{silence_fp}\' \n")

            import sys
            sys.exit()
            for k in main_chapter_keys():
                for scene in video_files[k]:
                    p = scene['path'].replace('.txt', f"_{scene['hash']}_{scene['last_task']}{lang_str}.mkv")
                    p = p.replace('concat', 'video')
                    concat_file.write(f"file \'{p}\' \n")
        else:
            # if k in ('g_debut', 'g_fin'):


            for k in main_chapter_keys():
                video: VideoChapter = db[k_ep]['video']['target'][k]
                if video['count'] == 0:
                    continue

                if len(video['scenes']) > 1:
                    concat_file.write(f"file \'{video['task'].video_file}\' \n")
                else:
                    concat_file.write(f"file \'{video['scenes'][0]['task'].video_file}\' \n")

                audio = db[k_ep]['audio'][k]
                if 'silence' in audio and audio['silence'] > 0:
                    silence_fp: str = os.path.join(
                        db[k_ep]['cache_path'],
                        "video",
                        f"{k_ep}_{k}_silence_{video['task'].name}.mkv"
                    )
                    concat_file.write(f"file \'{silence_fp}\' \n")

        concat_file.close()
        return concat_fp

