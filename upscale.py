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
)
from parsers.dsr import parse_dsr_file
from parsers.geometry import parse_geometry_file
from parsers.replace import parse_replace_file
from parsers.target_scenes import consolidate_target_scenes
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
        "-smin",
        type=int,
        default=-1,
        required=False,
        help="starting scene no. to process"
    )

    parser.add_argument(
        "--scene_max",
        "-smax",
        type=int,
        default=-1,
        required=False,
        help="last scene no. to process"
    )

    parser.add_argument(
        "-f",
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

    parser.add_argument(
        "--watermark",
        action="store_true",
        required=False,
        help="Watermark each scene with scene no."
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
    k_ch: Chapter = arguments.chapter

    parse_database(
        episode=episode,
        lang=arguments.lang,
    )
    gc.collect()

    # next_episode: str = ep_key(episode+1)
    # consolidate_target_scenes(k_ep=next_episode, k_ch='episode')
    # parse_geometry_file(k_ep_or_g=next_episode, k_ch='episode')
    # parse_replace_file(k_ep_or_g=next_episode, k_ch='episode')
    # parse_dsr_file(k_ep_or_g=next_episode)
    # pprint(db[next_episode]['video']['target']['episode']['scenes'])
    # sys.exit()

    scene_no: int | None = None
    scene_arg: str = arguments.scene
    if scene_arg.endswith('f'):
        raise NotImplementedError("scene_arg not yet implemented")
        scene_no = frame_to_scene_no(int(scene_arg[:-1]))
    elif scene_arg != '':
        scene_no: int = int(scene_arg)

    task: TaskName = 'upscale'

    upscale_scenes(
        episode=arguments.episode,
        single_chapter=k_ch,
        task_name=task,
        force=arguments.force,
        simulation=arguments.simulate,
        scene_no=scene_no,
        scene_min=arguments.scene_min,
        scene_max=arguments.scene_max,
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
