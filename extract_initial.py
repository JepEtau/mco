import argparse
import gc
import logging
from pprint import pprint
import signal
import sys
from parsers import (
    parse_database,
    logger,
    all_chapter_keys,
    db
)
from utils.arg_parser import common_argument_parser
from utils.logger import main_logger as main_logger
from utils.p_print import *
from video.extract_scenes import extract_scenes
from video.video_track import generate_video_track



def main():
    # Arguments
    parser: argparse.ArgumentParser = common_argument_parser(
        description="Extract initial frames",
        add_language=False,
    )

    parser.add_argument(
        "--edition",
        "-ed",
        choices=['f', 'k', 's', 'j'],
        default='',
        required=True,
        help="Use this edition as source rather than the one selected in database"
    )

    parser.add_argument(
        "--scene",
        "-s",
        type=str,
        default='',
        required=False,
        help="scene no. to process. Integer or frame value (e.g. 2450f)"
    )

    parser.add_argument(
        "--scene_min",
        type=int,
        default=-1,
        required=False,
        help="starting scene no. to process"
    )

    parser.add_argument(
        "--scene_max",
        type=int,
        default=-1,
        required=False,
        help="last scene no. to process"
    )

    parser.add_argument(
        "--watermark",
        action="store_true",
        required=False,
        help="Watermark each scene with scene no."
    )

    parser.add_argument(
        "--stats",
        action="store_true",
        required=False,
        help="debug"
    )

    parser.add_argument(
        "--force",
        action="store_true",
        required=False,
        help="Overwrite"
    )

    parser.add_argument(
        "--simulate",
        action="store_true",
        required=False,
        help="Simulate the process"
    )


    arguments = parser.parse_args()

    if arguments.debug:
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
    print("Tasks:")
    print("\t- parse database")

    # Parse database
    parse_database(episode=episode, edition=arguments.edition)
    gc.collect()

    if arguments.edition == '':
        raise ValueError(f"Edition must be specified")

    # For inspection
    # db_ep: dict = g_database['ep01']
    # print(db_ep.keys())
    # print(db_ep['cache_path'])
    # pprint(db_ep['audio'])

    # print(g_database.keys())
    # pprint(g_database['common'])

    #
    scene_no: int | None = None
    scene_arg: str = arguments.scene
    if scene_arg.endswith('f'):
        raise NotImplementedError("scene_arg not yet implemented")
        scene_no = frame_to_scene_no(int(scene_arg[:-1]))
    elif scene_arg != '':
        scene_no: int = int(scene_arg)

    extract_scenes(
        episode=arguments.episode,
        single_chapter=arguments.chapter,
        task='initial',
        force=arguments.force,
        simulation=arguments.simulate,
        scene_no=scene_no,
        scene_min=arguments.scene_min,
        scene_max=arguments.scene_max,
        watermark=arguments.watermark,
        edition=arguments.edition,
        debug=arguments.debug
    )



if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
