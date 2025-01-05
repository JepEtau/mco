from argparse import ArgumentParser
import gc
import os
from pprint import pprint
import signal
import subprocess
import sys
import time

from nn_inference.toolbox.upscale_doc import consolidate_initial_doc_scenes
from parsers import (
    Chapter,
    db,
    ep_key,
    parse_database,
    parse_episode,
    ProcessingTask,
    VideoSettings,
)
from scene.consolidate_src import consolidate_src_scene
from utils.mco_types import (
    ChapterVideo,
    Scene,
)
from utils.mco_utils import ffmpeg_metadata
from utils.media import (
    extract_media_info_mco,
    vcodec_to_extension,
    VideoInfo,
)
from utils.path_utils import absolute_path
from utils.p_print import *
from utils.time_conversions import (
    FrameRate,
    frame_to_sexagesimal,
    s_to_sexagesimal,
)
from utils.tools import ffmpeg_exe



def main():
    # Arguments
    parser: ArgumentParser = ArgumentParser(
        description="Extract initial frames"
    )
    parser.add_argument(
        "--episode",
        "-ep",
        type=int,
        default=0,
        required=True,
        help="from 1 to 39"
    )

    parser.add_argument(
        "--edition",
        "-ed",
        choices=['f', 'k', 's', 'j', 's0'],
        default='',
        required=False,
        help="Use this edition"
    )

    parser.add_argument(
        "--force",
        action="store_true",
        required=False,
        help="Overwrite"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        required=False,
        help="debug"
    )

    arguments = parser.parse_args()


    episode: int = arguments.episode
    if episode == 0:
        sys.exit("Error: at least an episode shall be specified")

    if not (episode > 0 or episode <= 39 or episode == 99):
        sys.exit(red("Episode must be between 1 and 39"))

    k_ep = ep_key(episode)
    k_ch: Chapter = 'doc'
    print(f"Episode: {episode}")
    print(f"Chapter: {k_ch}")
    print("Tasks:")
    print("  - parse database")

    # Parse database
    parse_database(episode=episode, ignore_av_sync=True, avsync_stats=False)
    gc.collect()

    ch_video: ChapterVideo | None = None
    try:
        ch_video: ChapterVideo | None = db[k_ep]['video']['target'][k_ch]
    except:
        raise ValueError(f"no doc in {k_ep}")

    # Create a file per scene
    start_time: float = time.time()
    consolidate_initial_doc_scenes(
        ch_video,
        force=arguments.force,
        debug=arguments.debug
    )

    print(cyan("Elapsed time"), f"{s_to_sexagesimal(time.time() - start_time)}")


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
