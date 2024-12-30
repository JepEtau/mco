from argparse import ArgumentParser
from copy import deepcopy
import gc
import logging
from pprint import pprint
import signal
import sys
from typing import Literal

import numpy as np
from parsers import (
    TASK_NAMES,
    parse_database,
    logger,
    db,
    Chapter,
    all_chapter_keys,
    ep_key,
    ProcessingTask,
    TaskName,
    pprint_scene_mapping,
    get_fps,
)
from parsers._helpers import get_chapter_audio
from scene.consolidate import consolidate_scene
from utils.arg_parser import common_argument_parser
from utils.mco_types import (
    ChapterAudio,
    Effect,
    Scene,
    ChapterVideo,
)
from utils.p_print import *
from video.consolidate_scenes import get_chapter_video

StatsKeys = Literal[
    'audio',
    'video',
    'k_ed_src',
    'origin_video',
    'total_removed',
    'gaps',
    'se_loops'
]

def main():
    # Arguments
    parser = ArgumentParser(description="For doc consolidation")

    parser.add_argument(
        "--debug",
        action="store_true",
        required=False,
        help="debug"
    )

    parser.add_argument(
        "--en",
        action="store_true",
        required=False,
        help="English version"
    )

    arguments = parser.parse_args()

    if arguments.debug:
        logger.addHandler(logging.StreamHandler(sys.stdout))
        logger.setLevel("DEBUG")


    doc_stats: dict[str, dict[StatsKeys, int | str | list]] = {}
    k_ch = 'doc'
    # for ep_no in range(1, 40):
    for ep_no in range(4, 5):
        k_ep = ep_key(ep_no)
        parse_database(
            episode=k_ep,
            lang='fr',
            ignore_av_sync=True,
            avsync_stats=True
        )

        ch_audio: ChapterAudio = db[k_ep]['audio'][k_ch]
        ch_video: ChapterVideo = db[k_ep]['video']['target'][k_ch]

        pprint(ch_audio)

        k_ed: str = ch_video['default_src']['k_ed']
        if k_ed != 'k':
            raise ValueError(red(f"edition for {k_ep}:{k_ch} is erroneous: {k_ed}"))
        ch_src_video: ChapterVideo = db[k_ep]['video'][k_ed][k_ch]
        origin_video_count: int = (
            ch_src_video['scenes'][-1]['start']
            + ch_src_video['scenes'][-1]['count']
            - ch_src_video['scenes'][0]['start']
        )

        removed_frames = 0
        gaps: list[int] = [0]
        se_loops: int = 0
        for k in range(1, len(ch_src_video['scenes'])):
            scene: Scene = ch_src_video['scenes'][k]
            delta: int = (
                scene['start']
                - (ch_src_video['scenes'][k-1]['start'] + ch_src_video['scenes'][k-1]['count'])
            )
            removed_frames += delta
            gaps.append(delta)

            # pprint(scene)

            if 'effects' in scene and scene['effects'].has_effect('se_loop'):
                e: Effect = scene['effects'].get_effect('se_loop')
                se_loops += sum(e.extra_param)



        doc_stats[k_ep] = {
            'audio': int(ch_audio['duration'] * get_fps(db) / 1000),
            'video': ch_video['count'],
            'k_ed_src': ch_video['default_src']['k_ed'],
            'origin_video': origin_video_count,
            'total_removed': removed_frames,
            'gaps': gaps,
            'se_loops': se_loops,
        }
        if ch_audio['avsync'] != 0 or ch_video['avsync'] != 0:
            raise ValueError(red(f"Error: {k_ep}: avsync!=0 ({ch_audio['avsync']})"))

        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # Deactivated:
        # https://vscode.dev/github/JepEtau/mco_dev/blob/dev/parsers/target_av_tracks.py#L49-L50
        # https://vscode.dev/github/JepEtau/mco_dev/blob/dev/parsers/target_av_tracks.py#L124
        # https://vscode.dev/github/JepEtau/mco_dev/blob/dev/parsers/geometry.py#L211-L212


    for k_ep, stats in doc_stats.items():
        print(lightcyan(f"{k_ep}"))
        print(f"  {stats}")
        missing_framecount = stats['audio'] - stats['video']
        if missing_framecount:
            print(yellow(f"  missing {missing_framecount}"))
            print(f"  removed {stats['total_removed']}")
            if stats['audio'] > stats['origin_video']:
                print(yellow(
                    f"  missing {stats['audio'] - stats['origin_video']} frames in original video, verify audio"
                ))
        if stats['se_loops']:
            print(f"  Added {stats['se_loops']} frames")
        if missing_framecount > stats['se_loops']:
            print(red(f"  still missing {missing_framecount - stats['se_loops']}"))

            se_mapping: np.ndarray = np.zeros((len(stats['gaps']), 2), dtype=int)
            for i, n in enumerate(stats['gaps']):
                if not n:
                    continue
                se_mapping[i - 1][1] = min(n, int(n/2))
                se_mapping[i][0] = n - se_mapping[i - 1][1]

            # pprint(se_mapping)
            for i in range(len(stats['gaps'])):
                if se_mapping[i][0] != 0 or se_mapping[i][1] != 0:
                    print(f"{i:02} = , se_loop={se_mapping[i][0]}:{se_mapping[i][1]}")
                else:
                    print(f"{i:02} =")

        elif missing_framecount == stats['se_loops']:
            print(lightgreen(f"  {k_ep}: same frame count"))
        else:
            print(green(f"  {k_ep}: info: too many frames: {stats['se_loops'] - missing_framecount}"))

        print()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
