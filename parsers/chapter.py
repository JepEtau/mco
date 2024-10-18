from __future__ import annotations
import re
import sys

from utils.mco_types import Effect, Effects
from .helpers import get_fps
from ._keys import ep_key



def parse_chapter_sections(
    db: dict[str, dict],
    episode: int | str,
    edition: str,
    config,
):
    k_section = 'chapters'
    db_video = db[ep_key(episode)]['video'][edition]
    fps: float = get_fps(db)

    for k_chapter in config.options(k_section):
        value_str = config.get(k_section, k_chapter)
        value_str = value_str.replace(' ','')
        # print("%s, %s => [%s]" % (k_section, k_chapter, value_str))

        chapter_fadein = 0
        chapter_fadeout = 0
        start = None
        end = -1

        # Walk through values
        properties = value_str.split(',')
        # print("\t%s:%s, properties:," % (k_ep, k_chapter), properties)
        for property in properties:

            if (search_start_end := re.search(re.compile(r"(\d+):(\d+)"), property)):
                start = int(search_start_end.group(1))
                end = int(search_start_end.group(2))

            elif (search_fadein := re.search(re.compile(r"fadein=([\d.]+)"), property)):
                chapter_fadein = int(float(search_fadein.group(1)) * fps)

            elif (search_fadeout := re.search(re.compile(r"fadeout=([\d.]+)"), property)):
                chapter_fadeout = int(float(search_fadeout.group(1)) * fps)

        if start is None:
            sys.exit("Error: parse_chapter_sections: start and end values are required for %s in episode file" % (k_chapter))

        db_video[k_chapter].update({
            'start': start,
            'end': end,
            'count': (end - start) if end > 0 else -1,
        })
        db_video[k_chapter]['effects'] = Effects(
            effects=[
                # Effect(name='loop_and_fadein', fade=chapter_fadein),
                Effect(name='fadein', fade=chapter_fadein),
                Effect(name='fadeout', fade=chapter_fadeout)
            ]
        )
