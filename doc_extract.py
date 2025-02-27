from argparse import ArgumentParser
import gc
import os
from pprint import pprint
import signal
import subprocess
import sys
import time

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
    parse_database(episode=episode, edition=arguments.edition)
    gc.collect()

    # Extract full chapter
    k_ed_ref: str = (
        arguments.edition
        if arguments.edition != ''
        else db[k_ep]['video']['target'][k_ch]['default_src']['k_ed']
    )
    print(f"  - edition: {k_ed_ref}")

    k_ed = k_ed_ref
    if k_ed_ref != db[k_ep]['video']['target'][k_ch]['default_src']['k_ed']:
        parse_episode(k_ed=k_ed_ref, k_ep=k_ep)
    else:
        k_ed = db[k_ep]['video']['target'][k_ch]['default_src']['k_ed']

    ch_video: ChapterVideo | None = None
    try:
        ch_video: ChapterVideo | None = db[k_ep]['video'][k_ed][k_ch]
    except:
        raise ValueError(f"no doc in {k_ed}:{k_ep}")

    # Consolidate a src scene to use task settings
    scene: Scene = ch_video['scenes'][0]
    scene['task'] = ProcessingTask(name='initial')
    consolidate_src_scene(scene=scene)

    # Input
    in_video_path: str = absolute_path(scene['inputs'].progressive().filepath)
    vsettings: VideoSettings = db['vsettings']['initial']

    # Output video filename
    cache_path: str = os.path.join(
        db['common']['directories']['cache_doc'],
        'progressive'
    )
    os.makedirs(cache_path, exist_ok=True)
    out_filepath: str = os.path.join(
        cache_path,
        f"{k_ep}_{k_ch}_{k_ed}_{scene['task'].hash}{vcodec_to_extension[vsettings.codec]}"
    )

    # Create folders for HR
    hr_directory: str = os.path.join(
        db['common']['directories']['cache_doc'], k_ep
    )
    os.makedirs(hr_directory, exist_ok=True)

    # Extract input video info
    in_video_info: VideoInfo = extract_media_info_mco(in_video_path)['video']
    fps: FrameRate = in_video_info['frame_rate_r']

    # Seek
    seek_start: int = ch_video['start']
    seek_count: int = ch_video['count']

    # Overwrite metadata
    _scene = {
        'task': ProcessingTask(
            name='initial',
            video_settings=db['vsettings']['initial']
        )
    }
    _scene['task'].video_settings.metadata = {
        'hash': scene['task'].hash,
        'start': seek_start,
        'count': seek_count,
    }
    metadata: list[str] = ffmpeg_metadata(_scene)

    # Check if existing output file is up to date
    is_up_to_date: bool = False
    if os.path.exists(out_filepath):
        is_up_to_date = True
        out_video_info = extract_media_info_mco(out_filepath)['video']
        for k, v in scene['task'].video_settings.metadata.items():
            if (k not in out_video_info['metadata']
                or out_video_info['metadata'][k] != v
            ):
                is_up_to_date = False
                break
        is_up_to_date = (
            is_up_to_date
            and out_video_info['frame_count'] == seek_count
        )

    if is_up_to_date:
        print(lightgreen(f"Already extracted:"), out_filepath)
        if not arguments.force:
            return
        else:
            print(lightcyan("Force extraction"))

    # FFmpg command
    ffmpeg_command: list[str] = [
        ffmpeg_exe,
        "-hide_banner",
        "-loglevel", "warning",
        "-stats",
        "-ss", frame_to_sexagesimal(seek_start, fps),
        "-i", in_video_path,
        "-t", frame_to_sexagesimal(seek_count, fps),
        "-c:v", "copy",
        "-an",
        "-sn",
        "-map_chapters", "-1",
        *metadata,
        "-y", out_filepath
    ]

    print(lightcyan("FFmpeg command"), ' '.join(ffmpeg_command))
    start_time: float = time.time()
    sub_process = subprocess.Popen(
        ffmpeg_command,
        stdin=subprocess.PIPE,
        stdout=sys.stdout,
        stderr=subprocess.STDOUT,
    )

    stdout, stderr = sub_process.communicate()
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
