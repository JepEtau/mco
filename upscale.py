from argparse import ArgumentParser
import gc
import logging
from pprint import pprint
import signal
import sys
from parsers import (
    Chapter,
    db,
    ep_key,
    parse_database,
    TaskName,
    parse_prec_asuivre_scenes,
)
from utils.arg_parser import common_argument_parser
from utils.logger import main_logger as main_logger
from utils.p_print import *
from video.upscale_scenes import upscale_scenes
try:
    import winsound
except ImportError:
    pass


def main():
    # Arguments
    parser: ArgumentParser = common_argument_parser('Upscale scenes', add_language=True)
    parser.add_argument(
        "--edition",
        "-ed",
        choices=('j', 'f', 'k', 's', 's0'),
        default='',
        required=False,
        help="Filter by edition"
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
    print(f"Language: {arguments.lang}")
    print("Tasks:")
    print("\t- parse database")

    # Parse database
    # if arguments.edition != '':
    #     episode = arguments.episode
    k_ch_dst: Chapter = arguments.chapter
    ep_no_dst: int = arguments.episode
    k_ep_dst: str = ep_key(arguments.episode)

    k_ch: Chapter = k_ch_dst
    k_ep: str = k_ep_dst

    # Parse following/previous chapter
    if k_ch_dst in ('precedemment', 'asuivre'):
        k_ep = ep_key(ep_no_dst + (1 if k_ch_dst == 'asuivre' else -1))
        k_ch = 'episode'

    parse_database(episode=k_ep, lang=arguments.lang)
    gc.collect()

    # Parse target list for these chapters
    scene_list: list[int] = []
    if k_ch_dst in ('precedemment', 'asuivre'):
        scene_list = parse_prec_asuivre_scenes(k_ep=k_ep_dst, k_ch=k_ch_dst)

    # next_episode: str = ep_key(episode+1)
    # consolidate_target_scenes(k_ep=next_episode, k_ch='episode')
    # parse_geometry_file(k_ep_or_g=next_episode, k_ch='episode')
    # parse_replace_file(k_ep_or_g=next_episode, k_ch='episode')
    # parse_dsr_file(k_ep_or_g=next_episode)
    # pprint(db[next_episode]['video']['target']['episode']['scenes'])
    # sys.exit()

    scene_no: int = arguments.scene

    task: TaskName = 'upscale'

    upscale_scenes(
        episode=k_ep,
        single_chapter=k_ch,
        task_name=task,
        force=arguments.force,
        simulation=arguments.simulate,
        scene_no=scene_no,
        scene_min=arguments.scene_min,
        scene_max=arguments.scene_max,
        scene_list=scene_list,
        watermark=arguments.watermark,
        edition=arguments.edition,
        debug=arguments.debug,
        compare=arguments.compare,
    )

    if sys.platform == "win32":
        winsound.Beep(frequency=440, duration=200)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
