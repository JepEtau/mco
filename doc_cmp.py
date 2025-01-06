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
        "-tpz",
        action="store_true",
        required=False,
        help="Overwrite"
    )

    parser.add_argument(
        "-s",
        type=int,
        default=0,
        required=True,
        help="scene no."
    )

    arguments = parser.parse_args()


    episode: int = arguments.episode
    if episode == 0:
        sys.exit("Error: at least an episode shall be specified")

    if not (episode > 0 or episode <= 39 or episode == 99):
        sys.exit(red("Episode must be between 1 and 39"))

    k_ep: str = ep_key(episode)

    if sys.platform == "linux":
        hr_path = f"/media/adg/A2G/mco.doc/{k_ep}/hr"
    else:
        raise NotImplementedError("only linux")

    scene_no: str = f"{arguments.s:02}"
    op: str = f"{k_ep}_doc_{scene_no}__k_hr.mxf"
    dvr: str = f"{k_ep}_doc_{scene_no}__k_hr_dvr.mxf"
    tpz: str = f"{k_ep}_doc_{scene_no}__k_hr_tpz.mxf"

    ext_files: list[str] = []

    op_fp = absolute_path(os.path.join(hr_path, op))
    ext_files.append(f"--external-file={absolute_path(os.path.join(hr_path, dvr))}")

    # Add tpz
    tpz_fp: str = absolute_path(os.path.join(hr_path, tpz))
    vid3 = ""
    if arguments.tpz and os.path.exists(tpz_fp):
        ext_files.append(f"--external-file={tpz_fp}")
        vid3 = "[vid3]"

    print(lightcyan(f"input1:"), op_fp)
    for i, fp in enumerate(ext_files):
        print(lightcyan(f"input{i+2}:"), fp)

    comp_command: list[str] = [
        "mpv",
        f"--lavfi-complex=[vid1][vid2]{vid3}hstack=inputs={len(ext_files) + 1}[vo]",
        f"{op_fp}",
        *ext_files
    ]

    print(purple(f"MPV command:"), " ".join(comp_command))
    subprocess.call(comp_command)




if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
