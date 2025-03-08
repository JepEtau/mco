from argparse import ArgumentParser
import gc
import logging
from pprint import pprint
import signal
import sys
from parsers import (
    parse_database,
    all_chapter_keys,
    Chapter,
    ep_key,
    get_ed_to_src_scene,
    get_chapter_video,
)
from parsers.episode import parse_episode
from utils.arg_parser import common_argument_parser
from utils.logger import main_logger as main_logger
from utils.mco_types import ChapterVideo, Scene
from utils.p_print import *
from video.extract_scenes import extract_scenes



def main():
    # Arguments
    parser: ArgumentParser = common_argument_parser(
        description="Generate LQ scenes for experiments"
    )

    parser.add_argument(
        "--stats",
        action="store_true",
        required=False,
        help="debug"
    )

    arguments = parser.parse_args()

    if arguments.debug:
        main_logger.addHandler(logging.StreamHandler(sys.stdout))
        main_logger.setLevel("DEBUG")

    episode: int = arguments.episode
    k_ch: Chapter = arguments.chapter
    if episode == 0 and k_ch == '':
        sys.exit("Error: at least an episode or a chapter shall be specified")

    if not (episode > 0 or episode <= 39 or episode == 99):
        sys.exit(red("Episode must be between 1 and 39"))

    elif episode != 0 and k_ch == '':
        k_ch = 'episode'

    if k_ch in ('g_debut', 'g_fin'):
        episode = 0

    if episode != 0:
        print(f"Episode: {episode}")

    if k_ch != '':
        print("Chapter: %s" % (k_ch))

    k_ep: str = ep_key(episode)
    k_ed: str = arguments.edition
    scene_no: int = arguments.scene

    # Parse database, consolidate target but no need to consolidate avsync
    parse_database(episode=k_ep, edition='', ignore_av_sync=True)
    gc.collect()

    parse_episode(k_ed=k_ed, k_ep=k_ep)
    extract_scenes(
        episode=k_ep,
        single_chapter=k_ch,
        task_name='lr',
        force=arguments.force,
        simulation=arguments.simulate,
        scene_no=scene_no,
        scene_min=arguments.scene_min,
        scene_max=arguments.scene_max,
        watermark=False,
        edition=k_ed,
        debug=arguments.debug,
        compare=True,
    )


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
