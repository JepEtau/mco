import re
import sys
from .helpers import get_fps
from ._keys import key



def parse_chapter_sections(
    db: dict[str, dict],
    episode: int | str,
    edition: str,
    config,
):
    k_section = 'chapters'
    db_video = db[key(episode)]['video'][edition]
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

            search_start_end = re.search(re.compile(r"(\d+):(\d+)"), property)
            if search_start_end is not None:
                start = int(search_start_end.group(1))
                end = int(search_start_end.group(2))
                continue

            search_fadein = re.search(re.compile(r"fadein=([0-9.]+)"), property)
            if search_fadein is not None:
                search_fadein = int(float(search_fadein.group(1)) * fps)
                continue

            search_fadeout = re.search(re.compile(r"fadeout=([0-9.]+)"), property)
            if search_fadeout is not None:
                chapter_fadeout = int(float(search_fadeout.group(1)) * fps)
                continue

        if start is None:
            sys.exit("Error: parse_chapter_sections: start and end values are required for %s in episode file" % (k_chapter))

        db_video[k_chapter].update({
            'effects': {
                'loop_and_fadein': chapter_fadein,
                'fadeout': chapter_fadeout,
            },
            'start': start,
            'end': end,
            'count': (end - start) if end > 0 else -1,
        })

