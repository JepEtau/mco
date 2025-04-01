from argparse import ArgumentParser
from copy import deepcopy
import gc
import logging
from pprint import pprint
import signal
import sys
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
    get_frame_rate,
)
from parsers._helpers import get_chapter_audio
from scene.consolidate import consolidate_scene
from utils.arg_parser import common_argument_parser
from utils.mco_types import (
    ChapterAudio,
    Scene,
    ChapterVideo,
)
from utils.p_print import *
from video.consolidate_scenes import get_chapter_video


def main():
    # Arguments
    parser = ArgumentParser(description="returns audio durations for each chapter of each episode")

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


    prec: dict[str, dict[Chapter, str | int]] = {}
    asuivre: dict[str, dict[Chapter, str | int]] = {}
    g_doc: dict[str, dict[Chapter, str | int]] = {}
    for ep_no in range(1, 40):
        k_ep = ep_key(ep_no)
        parse_database(
            episode=k_ep,
            lang='fr',
            avsync_stats=True
        )

        # prec
        ch_audio: ChapterAudio = db[k_ep]['audio']['prec']
        if 'count' in ch_audio and ch_audio['count'] != 0:
            prec[k_ep] = {
                'avsync': ch_audio['avsync'],
                'count': int(ch_audio['duration'] * get_frame_rate() / 1000),
            }
            if ch_audio['count'] != prec[k_ep]['count']:
                raise ValueError(red(f"Error: {k_ep}: {ch_audio['count']} vs {prec[k_ep]['count']}"))

            if ch_audio['avsync'] != 0:
                raise ValueError(red(f"Error: {k_ep}: avsync!=0 ({ch_audio['avsync']})"))

        # A suivre
        ch_audio: ChapterAudio = db[k_ep]['audio']['asuivre']
        if 'count' in ch_audio and ch_audio['count'] != 0:
            asuivre[k_ep] = {
                'avsync': ch_audio['avsync'],
                'count': int(ch_audio['duration'] * get_frame_rate() / 1000),
            }
            if ch_audio['count'] != asuivre[k_ep]['count']:
                raise ValueError(red(f"Error: {k_ep}: {ch_audio['count']} vs {prec[k_ep]['count']}"))

            if ch_audio['avsync'] != 0:
                raise ValueError(red(f"Error: {k_ep}: avsync!=0 ({ch_audio['avsync']})"))


        # A suivre
        ch_audio: ChapterAudio = db[k_ep]['audio']['g_doc']
        if 'count' in ch_audio and ch_audio['count'] != 0:
            g_doc[k_ep] = {
                'avsync': ch_audio['avsync'],
                'count': int(ch_audio['duration'] * get_frame_rate() / 1000),
            }


        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # Deactivated:
        # https://vscode.dev/github/JepEtau/mco_dev/blob/dev/parsers/target_av_tracks.py#L49-L50
        # https://vscode.dev/github/JepEtau/mco_dev/blob/dev/parsers/target_av_tracks.py#L124
        # https://vscode.dev/github/JepEtau/mco_dev/blob/dev/parsers/geometry.py#L211-L212


    print(lightcyan("prec"))
    for k, v in prec.items():
        print(f"{k}\t{v['count']}")

    print(lightcyan("\nasuivre"))
    for k, v in asuivre.items():
        print(f"{k}\t{v['count']}")


    print(lightcyan("\ng_doc"))
    for k, v in g_doc.items():
        print(f"{k}\t{v['count']}")
    g_doc_max = max(list([v['count'] for v in g_doc.values()]))
    print(f"-> {g_doc_max}")

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
