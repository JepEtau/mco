import sys
from utils.mco_types import ChapterVideo, ChapterAudio
from utils.p_print import *
from ._db import db


def get_chapter_video(k_ep: str, k_ch: str) -> ChapterVideo | None:
    """Returns the target video object"""
    ch_video: ChapterVideo
    if k_ch in ('g_debut', 'g_fin'):
        ch_video = db[k_ch]['video']

    elif k_ep == 'ep00':
        sys.exit(red("Missing episode no."))

    else:
        ch_video = db[k_ep]['video']['target'][k_ch]

    # Do not generate clip for unused chapters
    if 'count' not in ch_video:
        print(yellow(f"warning: no \'count\' in {k_ep}:{k_ch} -> no scenes"))
        return None

    if ch_video['count'] <= 0:
        return None

    return ch_video



def get_chapter_audio(k_ep: str, k_ch: str) -> ChapterAudio | None:
    """Returns the target audio object"""
    ch_audio: ChapterAudio
    if k_ch in ('g_debut', 'g_fin'):
        ch_audio = db[k_ch]['audio']

    elif k_ep == 'ep00':
        sys.exit(red("Missing episode no."))

    else:
        ch_audio = db[k_ep]['audio'][k_ch]

    # Do not generate clip for unused chapters
    if 'count' not in ch_audio:
        print(yellow(f"warning: no \'count\' in {k_ep}:{k_ch} -> no audio segment"))
        return None

    if ch_audio['count'] <= 0:
        return None

    return ch_audio
