import argparse
import gc
import logging
import os
from pprint import pprint
import signal
import subprocess
import sys
import time
from typing import OrderedDict
from parsers import (
    db,
    logger as parse_logger,
    key,
    parse_database,
    all_chapter_keys,
    get_dependencies,
)
from processing.deint import (
    calc_deint_hash,
    deint_command,
    get_template_script,
    qtgmc_deint_command,
    g_deint_algorithms,
    get_qtgmc_args,
    generate_avs_script
)
from processing.decoder import decoder_frame_prop
from utils.mco_types import Inputs
from utils.media import VideoInfo, extract_media_info, get_media_info
from utils.p_print import *
from utils.path_utils import absolute_path, path_split
from utils.logger import main_logger
from utils.time_conversions import s_to_sexagesimal


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
        choices=['f', 'k', 's', 'j'],
        default='',
        required=False,
        help="deinterlace video of this edition only"
    )

    # Deinterlace
    parser.add_argument(
        "--deint",
        choices=g_deint_algorithms,
        default='qtgmc',
        required=False,
        help="""Deinterlace algorithm.
QTGMC uses an Avisynth+ script and can be runned under Windows only.
Others are FFmpeg deinterlacers. Refer to https://ffmpeg.org/documentation.html
use deint_params to customize settings
note for nnedi: it is not needed to specify the path
\n"""
    )
    parser.add_argument(
        "--deint_params",
        type=str,
        default='',
        required=False,
        help="""Parameters passed to the FFmpeg command for deinterlacing
Refer to https://ffmpeg.org/documentation.html
Default value for NNEDI deinterlacer is \"nsize=s8x6:nns=n128:qual=slow:etype=s:pscrn=new3\".
\n"""
    )

    parser.add_argument(
        "--check_duration",
        action="store_true",
        required=False,
        help="Ignore check before deinterlacing"
    )

    arguments = parser.parse_args()

    if arguments.debug:
        parse_logger.addHandler(logging.StreamHandler(sys.stdout))
        parse_logger.setLevel("WARNING")

        main_logger.addHandler(logging.StreamHandler(sys.stdout))
        main_logger.setLevel("DEBUG")

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
        episode=episode,
        lang='en' if arguments.en else 'fr'
    )
    gc.collect()

    ep: str = key(episode)
    # Dependencies
    dependencies = get_dependencies(
        episode=ep,
        chapter=chapter,
        track='video'
    )

    main_edition: str = db['ep01']['video']['target']['episode']['k_ed_src']
    editions: list[str] = []
    [
        editions.append(ed)
        for ed in [main_edition] + list(dependencies.keys())
        if ed not in editions
    ]

    if arguments.debug:
        print(cyan("Dependencies"))
        pprint(dependencies)
        pprint(editions)

    # Get all range to deinterlace for each dependency
    in_videos: OrderedDict[str, dict[str, set]] = OrderedDict()
    for k_ed in editions:
        if k_ed not in dependencies:
            continue

        if arguments.edition != '' and k_ed != arguments.edition:
            continue

        for k_ep in dependencies[k_ed]:
            for k_c in all_chapter_keys():
                input: Inputs = db[k_ep]['video'][k_ed][k_c]['inputs']
                fp: str = input['interlaced']['filepath']

                segment: tuple[int, int] = (
                    input['progressive']['start'],
                    input['progressive']['count']
                )

                if fp not in in_videos:
                    in_videos[fp] = {
                        'ed_ep': (k_ed, k_ep),
                        'segments': set(),
                    }
                in_videos[fp]['segments'].add(segment)

    if arguments.debug:
        print(cyan("Dependencies"))
        pprint(in_videos)

    for in_video, value in in_videos.items():
        ed, ep = value['ed_ep']
        # if arguments.edition != '' and ed != arguments.edition:
        #     continue

        # Input media
        in_media_path: str = absolute_path(in_video)
        if in_media_path is None or in_media_path == '':
            raise FileExistsError(red(f"Missing input file: edition: {ed}, episode: {ep}"))
        print(cyan(f"Input:"), f"{in_media_path}")
        try:
            in_media_info = extract_media_info(in_media_path)
        except:
            # debug:
            extract_media_info(in_media_path)
            sys.exit(f"[E] {in_media_path} is not a valid input media file")
        if arguments.debug:
            print(lightcyan("FFmpeg media info:"))
            pprint(get_media_info(in_media_path))
            print(lightcyan("to media info:"))
            pprint(in_media_info)
        in_video_info: VideoInfo = in_media_info['video']
        in_video_info['filepath'] = in_media_path

        if not in_video_info['is_interlaced']:
            print(yellow(f"\t{in_media_path} is already progressive"))
            # continue

        # Get the output shape/dtype/channel order depending on the deinterlace algo
        d_shape, d_dtype, d_c_order, d_size = decoder_frame_prop(
            in_video_info,
            deint_algo=arguments.deint,
        )
        if arguments.debug:
            print(cyan("Decoder:"))
            print(f"\tshape: {d_shape}")
            print(f"\tdtype: {d_dtype}")
            print(f"\tc_order: {d_c_order}")
            print(f"\tsize: {d_size}")

        db_directories: dict[str, str] = db['common']['directories']


        # QTGMC or FFmpeg
        trim_start, trim_count = list(value['segments'])[0]
        main_logger.debug(f"trim: start: {trim_start}, count: {trim_count}")
        if arguments.deint == 'qtgmc':

            # Get AviSynth+ template
            template_script: str = get_template_script(ep, ed)
            print(cyan(f"Avisynth+ script template:"), f"{template_script}")

            # Create a script from this template
            cache_dir: str = os.path.join(db_directories['cache'], ep)
            os.makedirs(cache_dir, exist_ok=True)

            if template_script != '':
                # Extract QTGMC arguments to create a hashcode
                # and to add to the output video metadata
                qtgmc_args: OrderedDict[str, str] = get_qtgmc_args(template_script)
                hashcode, filter_str = calc_deint_hash(qtgmc_args)
                script_filepath: str = os.path.join(
                    db_directories['cache_progressive'],
                    f"{path_split(in_media_path)[1]}_{hashcode}.avs"
                )
                if script_filepath == template_script:
                    raise ValueError("Overwriting the original script is not allowed")

                generate_avs_script(
                    template_script,
                    script_filepath,
                    in_video_info=in_video_info,
                    trim_start=trim_start,
                    trim_count=trim_count,
                )
            print(cyan(f"Avisynth+ script:"), f"{script_filepath}")

            # Create the FFmpeg command
            out_filepath: str = os.path.join(
                db_directories['cache_progressive'],
                f"{path_split(in_media_path)[1]}_{hashcode}.mkv"
            )
            ffmpeg_command: str = qtgmc_deint_command(
                in_video_info=in_video_info,
                script=script_filepath,
                qtgmc_args=qtgmc_args,
                out_filepath=out_filepath
            )

        else:
            deint_algo: str = arguments.deint
            deint_params: str = arguments.deint_params
            if deint_algo == 'nnedi' and deint_params == '':
                deint_params: str = "nsize=s8x6:nns=n128:qual=slow:etype=s:pscrn=new3"
            hashcode, filter_str = calc_deint_hash({
                'algo': deint_algo,
                'params': deint_params
            })

            # Other deinterlacers
            out_filepath: str = os.path.join(
                db_directories['cache_progressive'],
                f"{path_split(in_media_path)[1]}_{deint_algo}_{hashcode}.mkv"
            )

            ffmpeg_command: str = deint_command(
                in_video_info=in_video_info,
                algo=deint_algo,
                params=deint_params,
                trim_start=trim_start,
                trim_count=trim_count,
                out_filepath=out_filepath
            )

        print(cyan(f"Output:"), f"{out_filepath}")
        if os.path.exists(out_filepath):
            out_video_info = extract_media_info(out_filepath)['video']
            _trim_count: int = (
                trim_count
                if trim_count != -1
                else in_video_info['frame_count'] - trim_start
            )
            main_logger.debug(
                f"{out_filepath} already exists "
                + f"asked: {_trim_count} vs "
                + f"current video: {out_video_info['frame_count']}"
            )

            if out_video_info['frame_count'] == _trim_count or not arguments.check_duration:
                print()
                continue
        else:
           main_logger.debug(f"{out_filepath} does not exist")

        frame_count: int = (
            in_video_info['frame_count'] - trim_start
            if trim_count == -1
            else trim_count
        )
        print(cyan(f"Number of frames:"), f"{frame_count}")

        if arguments.debug:
            print(f"{hashcode} -> {filter_str}")
            print(' '.join(ffmpeg_command))

        os.makedirs(db_directories['cache_progressive'], exist_ok=True)
        start_time: float = time.time()
        sub_process = subprocess.Popen(
            ffmpeg_command,
            stdin=subprocess.PIPE,
            stdout=sys.stdout,
            stderr=subprocess.STDOUT,
        )

        stdout, stderr = sub_process.communicate()
        if arguments.debug:
            if stderr is not None:
                for line in stderr.decode('utf-8').split('\n'):
                    print(line)
            if stdout is not None:
                for line in stdout.decode('utf-8').split('\n'):
                    print(line)

        print(cyan("Elapsed time"), f"{s_to_sexagesimal(time.time() - start_time)}")

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
