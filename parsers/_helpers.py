import sys
from utils.mco_types import ChapterVideo
from utils.p_print import red
from ._db import db


def get_chapter_video(k_ep: str, k_ch: str) -> ChapterVideo | None:
    ch_video: ChapterVideo
    if k_ch in ('g_debut', 'g_fin'):
        ch_video = db[k_ch]['video']

    elif k_ep == 'ep00':
        sys.exit(red("Missing episode no."))

    else:
        print(k_ep, k_ch)
        ch_video = db[k_ep]['video']['target'][k_ch]

    # Do not generate clip for unused chapters
    if 'count' not in ch_video:
        return None

    if ch_video['count'] <= 0:
        return None

    return ch_video
