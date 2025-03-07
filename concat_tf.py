from argparse import ArgumentParser
import gc
import logging
from pprint import pprint
import signal
import sys
from parsers import (
    ep_key,
    parse_database,
    TaskName,
    Chapter,
    get_chapter_video,
)
from utils.arg_parser import common_argument_parser
from utils.logger import main_logger as main_logger
from utils.mco_types import ChapterVideo
from utils.p_print import *
from video.upscale_scenes import upscale_scenes
from video.concat_scenes import concat_scenes



def main():
    # Arguments
    parser: ArgumentParser = common_argument_parser(
        description="Generate Low Resolution video",
        add_language=True,
    )

    arguments = parser.parse_args()

    if arguments.debug:
        main_logger.addHandler(logging.StreamHandler(sys.stdout))
        main_logger.setLevel("DEBUG")

    ep_no: int = arguments.episode
    chapter: str = arguments.chapter
    if ep_no == 0:
        sys.exit("Error: episode no. must be specified")

    if ep_no < 0 or ep_no > 39:
        sys.exit(red("Episode must be between 1 and 39"))

    if chapter in ('g_debut', 'g_fin'):
        ep_no = 0
    if ep_no != 0:
        print(f"Episode: {ep_no}")
    if chapter != '':
        print(f"Chapter: {chapter}")
    print(f"Language: {arguments.lang}")
    print("Tasks:")
    print("\t- parse database")

    # Parse database
    parse_database(episode=ep_no, lang=arguments.lang)
    gc.collect()

    k_ep = ep_key(arguments.episode)
    k_ch: Chapter = arguments.chapter
    task: TaskName = 'tf'

    if k_ch != 'episode':
        print(red("Force to \'episode\'"))
        k_ch = 'episode'

    upscale_scenes(
        episode=k_ep,
        single_chapter=k_ch,
        task_name=task,
        force=arguments.force,
        simulation=True,
        # scene_no=arguments.scene_no,
        # scene_min=arguments.scene_min,
        # scene_max=arguments.scene_max,
        # scene_list=scene_list,
        watermark=False,
        # edition=arguments.edition,
        debug=arguments.debug
    )


    ch_video: ChapterVideo | None = get_chapter_video(k_ep, k_ch)
    pprint(ch_video['task'])
    pprint(ch_video['count'])
    concat_scenes(
        episode=k_ep,
        chapter=k_ch,
        ch_video=ch_video,
        force=arguments.force,
        simulation=False
    )



if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
