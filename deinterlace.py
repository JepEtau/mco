import argparse
import gc
import logging
import os
from pprint import pprint
import signal
import sys
from parsers import (
    key,
    parse_database,
    logger,
    all_chapter_keys,
    get_dependencies,
)
from parsers.helpers import get_chapter_video_src
from processing.avs_qtgmc import QtgmcSettings, generate_avs_script, patch_avs_script
from processing.decoder import decoder_frame_prop
from utils.media import VideoInfo, extract_media_info, get_media_info
from utils.p_print import *
from utils.path_utils import absolute_path

g_database = dict()

def main():
    # Arguments
    parser = argparse.ArgumentParser(description="Deinterlace")
    parser.add_argument(
        "--episode",
        "-ep",
        type=int,
        default=0,
        required=False,
        help="from 1 to 39"
    )

    parser.add_argument(
        "--chapter",
        choices=all_chapter_keys(),
        default='',
        required=False,
        help="Chapter"
    )

    parser.add_argument(
        "--en",
        action="store_true",
        required=False,
        help="English version"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        required=False,
        help="debug"
    )

    parser.add_argument(
        "--edition",
        "-ed",
        choices=['f', 'k', 's'],
        default='',
        required=False,
        help="deinterlace video of this edition only"
    )

    arguments = parser.parse_args()

    if arguments.debug:
        logger.addHandler(logging.StreamHandler(sys.stdout))
        logger.setLevel("DEBUG")

    episode: int = arguments.episode
    chapter: str = arguments.chapter
    if episode == 0 and chapter == '':
        sys.exit("Error: at least an episode or a chapter shall be specified")

    if episode < 0 or episode > 39:
        sys.exit(red("Episode must be between 1 and 39"))

    if chapter in ('g_debut', 'g_fin'):
        episode = 0
    if episode != 0:
        print(f"Episode: {episode}")
    if chapter != '':
        print("Chapter: %s" % (chapter))
    print(f"Language: {'en' if arguments.en else 'fr'}")
    print("Tasks:")
    print("\t- parse database")

    # Parse database
    parse_database(
        g_database,
        episode=episode,
        lang='en' if arguments.en else 'fr'
    )
    gc.collect()

    db = g_database
    ep: str = key(episode)
    # Dependencies
    dependencies = get_dependencies(
        db=db,
        episode=ep,
        chapter=chapter,
        track='video'
    )
    # editions: list[str] = list([ed for ed, eps in dependencies.items() if ep in eps])
    editions: list[str] = list(dependencies.keys())

    # Get all range to deinterlace for each dependency
    in_videos: dict[str, dict[str, set]] = {}
    for ed in editions:
        for k_c in all_chapter_keys():
            inputs = get_chapter_video_src(db, ep, ed, k_c)['inputs']
            # in_videos[ed_ep_c] =
            fp: str = inputs['interlaced']['filepath']
            segment: tuple[int, int] = (inputs['progressive']['start'], inputs['progressive']['count'])
            if fp not in in_videos:
                in_videos[fp] = {
                    'ed_ep': (ed, ep),
                    'segments': set(),
                }
            in_videos[fp]['segments'].add(segment)

    pprint(in_videos)

    for in_video, value in in_videos.items():
        ed, ep = value['ed_ep']
        if arguments.edition != '' and ed != arguments.edition:
            continue

        # Input media
        in_media_path: str = absolute_path(in_video)
        try:
            in_media_info = extract_media_info(in_media_path)
        except:
            # debug:
            extract_media_info(in_media_path)
            pprint(get_media_info(in_media_path))
            sys.exit(f"[E] {in_media_path} is not a valid input media file")
        if arguments.debug:
            print(lightcyan("FFmpeg media info:"))
            pprint(get_media_info(in_media_path))
            print(lightcyan("to media info:"))
            pprint(in_media_info)
        in_video_info: VideoInfo = in_media_info['video']
        in_video_info['filepath'] = in_media_path

        pprint(in_video_info)

        # Get the output shape/dtype/channel order depending on the deinterlace algo
        d_shape, d_dtype, d_c_order, d_size = decoder_frame_prop(
            in_video_info,
            deint_algo='qtgmc',
        )
        print(cyan("Decoder:"))
        print(f"shape: {d_shape}")
        print(f"dtype: {d_dtype}")
        print(f"c_order: {d_c_order}")
        print(f"size: {d_size}")


        ep_db_dir: str = os.path.join(g_database['common']['directories']['config'], ep)
        # priorities: edition, episode, global
        deint_script: str = ''
        for script in (
            os.path.join(ep_db_dir, f"{ep}_{ed}_deint.avs"),
            os.path.join(ep_db_dir, f"{ep}_deint.avs"),
            os.path.join(g_database['common']['directories']['config'], f"deint.avs")
        ):
            print(script)
            if os.path.exists(script):
                deint_script = script
                break
        if deint_script != '':
            print(f"found a deinterlace script: {deint_script}")
        else:
            print(yellow("no script found"))

        # Is an avs script exist for this episode?
        #   use edition/episode no.

        # If not... Generate an avs script?
        # generate_avs_script(
        #     in_media_info["video"],
        #     in_video_info,
        #     QtgmcSettings()
        # )
        cache_dir: str = os.path.join(g_database['common']['directories']['cache'], ep)
        os.makedirs(cache_dir, exist_ok=True)
        trim_start, trim_count = list(value['segments'])[0]
        script_filepath: str = ""
        if deint_script != '':
            script_filepath = patch_avs_script(
                deint_script,
                in_video_info,
                trim_start,
                trim_count,
                cache_dir
            )
        print(script_filepath)

        break


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
