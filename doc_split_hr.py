from argparse import ArgumentParser
import gc
import logging
import os
from pprint import pprint
import signal
import subprocess
import sys
import time
from typing import TYPE_CHECKING, Any

from parsers import (
    Chapter,
    db,
    ep_key,
    parse_database,
    parse_episode,
    ProcessingTask,
    TaskName,
    VideoSettings,
)
from parsers._helpers import get_chapter_video
from parsers.p_print import pprint_scene_mapping
if TYPE_CHECKING:
    from scene.src_scene import SrcScene
from scene.consolidate import consolidate_scene
from scene.consolidate_src import consolidate_src_scene
from utils.logger import main_logger as main_logger
from utils.mco_types import (
    ChapterVideo,
    Scene,
    Inputs,
)
from utils.mco_utils import (
    calculate_frame_count,
    ffmpeg_metadata,
    scene_id_str,
    str_to_video_codec,
)
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
        "--scene",
        "-s",
        type=int,
        default=-1,
        required=False,
        help="scene no. to process. Integer or frame value (e.g. 2450f)"
    )

    parser.add_argument(
        "--watermark",
        action="store_true",
        required=False,
        help="Watermark each scene with scene no."
    )

    parser.add_argument(
        "--debug",
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

    arguments = parser.parse_args()

    if arguments.debug:
        main_logger.addHandler(logging.StreamHandler(sys.stdout))
        main_logger.setLevel("DEBUG")

    episode: int = arguments.episode
    if episode == 0:
        sys.exit("Error: at least an episode shall be specified")

    if not (episode > 0 or episode <= 39 or episode == 99):
        sys.exit(red("Episode must be between 1 and 39"))

    k_ep = ep_key(episode)
    k_ch: Chapter = 'doc'
    scene_no: int = arguments.scene
    debug: bool = arguments.debug
    print(f"Episode: {episode}")
    print(f"Chapter: {k_ch}")
    print("Tasks:")
    print("  - parse database")


    # Parse database
    parse_database(episode=episode)
    gc.collect()


    task_name: TaskName = 'hr'
    vsettings: VideoSettings = db['common']['video_format'][task_name]


    # Output directory
    out_cache_dir: str = os.path.join(
        db['common']['directories']['cache_doc'], k_ep, "hr"
    )
    os.makedirs(out_cache_dir, exist_ok=True)


    # Get chapter video
    ch_video: ChapterVideo | None = get_chapter_video(k_ep, k_ch)
    if ch_video is None:
        raise ValueError(f"No {k_ch} for {k_ep}")
    ch_video['task'] = ProcessingTask(name=task_name)


    # Walk through target scenes
    scenes: list[Scene] = ch_video['scenes']
    for scene in scenes:
        if scene_no != -1 and scene['no'] != scene_no:
            continue
        pprint_scene_mapping(scene)

        # Consolidate this scene
        consolidate_scene(
            scene=scene,
            task_name=task_name,
            watermark=arguments.watermark
        )
        scene_id: str = scene_id_str(scene)


        if debug:
            print(lightcyan(f"======================= split doc: {scene_id} ============================="))
            pprint(scene)
            print(lightcyan("==============================================================================="))

        to_produce: int = calculate_frame_count(scene)

        if len(scene['src'].scenes()) > 1:
            raise NotImplementedError(f"Multiple src scenes not implemented yet")


        # Get src scene and first frame no of the extracted video
        src_scene: SrcScene = scene['src'].primary_scene()
        k_ed_src, k_ep_src, k_ch_src = src_scene['k_ed_ep_ch_no'][:3]
        progressive_start: int = (
            db[k_ep_src]['video'][k_ed_src][k_ch_src]['start']
        )


        # Input upscaled video filename
        in_cache_dir: str = os.path.join(
            db['common']['directories']['cache_doc'], k_ep
        )
        in_video_fp: str = os.path.join(
            in_cache_dir,
            f"{k_ep_src}_{k_ch_src}_{k_ed_src}_{task_name}{vcodec_to_extension[vsettings.codec]}"
        )
        in_video_info: VideoInfo = extract_media_info_mco(in_video_fp)['video']
        fps: FrameRate = in_video_info['frame_rate_r']


        # Seek
        seek_start: int = src_scene['start'] - progressive_start
        seek_count: int = src_scene['count']


        # Output filepath
        out_video_fp: str = os.path.join(
            out_cache_dir,
            f"{k_ep}_{k_ch}_{scene['no']:03}_{task_name}{vcodec_to_extension[vsettings.codec]}"
        )

        if debug:
            print(f"extract: {in_video_fp}, {seek_start}({seek_count}) -> {out_video_fp}")


        # Add padding
        in_h, in_w = in_video_info['shape'][:2]
        if task_name == 'hr':
            pad: int = vsettings.pad
            filters: list[str] = [
                f"pad={in_w + 2 * pad}:{in_h + 2 * pad}:{pad}:{pad}:black"
            ]

        filter_complex: str = ','.join(filters)
        for c in (' ', '\n', '\r', '\t'):
            filter_complex = filter_complex.replace(c, '')

        ffmpeg_filter: list[str] = [
            "-filter_complex",
            f"[0:v]{filter_complex}[outv]",
            "-map", "[outv]"
        ]

        # Reset metadata
        scene["task"].video_settings.metadata = {}
        metadata: list[str] = ffmpeg_metadata(scene)

        ffmpeg_command: list[str] = [
            ffmpeg_exe,
            "-hide_banner",
            "-loglevel", "warning",
            "-stats",
            "-ss", frame_to_sexagesimal(seek_start, fps),
            "-i", in_video_fp,
            "-t", frame_to_sexagesimal(seek_count, fps),
            *ffmpeg_filter,
            "-vcodec", str_to_video_codec[vsettings.codec].value,
            "-pix_fmt", vsettings.pix_fmt,
            *vsettings.codec_options,
            *metadata,
            out_video_fp, "-y"
        ]


        # Discard if already exists
        if (
            os.path.exists(out_video_fp)
            and os.path.getmtime(in_video_fp) < os.path.getmtime(out_video_fp)
        ):
            out_video_info = extract_media_info_mco(out_video_fp)['video']
            if (
                out_video_info['frame_count'] == seek_count
            ):
                if not arguments.force:
                    print(lightgreen(f"Already extracted:"), out_video_fp)
                    return
                else:
                    print(lightcyan("Force extraction"))


        print(lightcyan("FFmpeg command"), ' '.join(ffmpeg_command))
        start_time: float = time.time()
        ffmpeg_subprocess: subprocess.Popen = subprocess.Popen(
            ffmpeg_command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        os.set_blocking(ffmpeg_subprocess.stdout.fileno(), False)
        while ffmpeg_subprocess.poll() is None:
            line = ffmpeg_subprocess.stdout.readline().decode('utf-8')
            if line:
                print(line.strip(), end='\r', file=sys.stdout)

        stdout, stderr = ffmpeg_subprocess.communicate()
        if stderr is not None:
            for line in stderr.decode('utf-8').split('\n'):
                print(line)
        if stdout is not None:
            for line in stdout.decode('utf-8').split('\n'):
                print(line)

        print(cyan("Extracted in"), f"{s_to_sexagesimal(time.time() - start_time)}")
        print()



if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
