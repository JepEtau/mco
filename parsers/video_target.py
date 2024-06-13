
from configparser import ConfigParser
import re
import sys
from ._keys import (
    key,
    all_chapter_keys,
    non_credit_chapter_keys,
    main_chapter_keys,
)
from .helpers import (
    get_fps,
    nested_dict_set,
)
from .logger import logger
from utils.p_print import *



def parse_video_target(
    db,
    episode: int | str,
    config: ConfigParser,
    k_section,
) -> None:
    k_ep: str = key(episode)
    db_video = db[k_ep]['video']['target']
    fps: float = get_fps(db)

    logger.debug(lightgreen(f"parse_video_target: {k_ep}"))

    k_ed_src = None
    for k_option in config.options(k_section):
        value_str = config.get(k_section, k_option)
        value_str = value_str.replace(' ','')
        logger.debug(lightgrey(f"   {k_option} => [{value_str}]"))

        if k_option == 'source':
            k_ed_src = value_str
            continue

        # Parse only supported sections
        if k_option not in main_chapter_keys():
            continue
        k_chapter = k_option

        chapter_fadein = 0
        chapter_fadeout = 0
        k_chapter_ed_src = None
        start = None
        end = -1

        # Walk through values
        properties = value_str.split(',')
        # logger.debug(f"\t{k_ep}:{k_chapter}, properties: ", properties)
        for property in properties:

            search_start_end = re.search(re.compile(r"(\d+):(-?\d+)"), property)
            if search_start_end is not None:
                start = int(search_start_end.group(1))
                end = int(search_start_end.group(2))
                continue

            search_fadein = re.search(re.compile(r"fadein=([0-9.]+)"), property)
            if search_fadein is not None:
                chapter_fadein = int(float(search_fadein.group(1)) * fps)
                continue

            search_fadeout = re.search(re.compile(r"fadeout=([0-9.]+)"), property)
            if search_fadeout is not None:
                chapter_fadeout = int(float(search_fadeout.group(1)) * fps)
                continue

            search_k_ed_src = re.search(re.compile(r"ed=([a-z]+[0-9]*)"), property)
            if search_k_ed_src is not None:
                k_chapter_ed_src = search_k_ed_src.group(1)
                # sys.exit("found %s for %s:%s" % (k_chapter_ed_src, k_ep, k_chapter))
                continue

        # if start is None:
        #     sys.exit("Error: parse_video_target_section: start and end values are required for %s:%s in target file" % (k_ep, k_chapter))

        nested_dict_set(db_video, dict(), k_chapter)
        db_video[k_chapter].update({
            'effects': {
                'fadein': chapter_fadein,
                'fadeout': chapter_fadeout,
                'loop_and_fadein': 0,
            },
            'start': start,
            'end': end,
            'count': (end - start) if end > 0 else -1,
            'k_ed_src': k_chapter_ed_src,
        })
        if chapter_fadein != 0:
            logger.debug(lightcyan(f"fadein != 0: {k_chapter}"))
            logger.debug(db_video[k_chapter])
            # sys.exit()

    if k_ed_src is None:
        sys.exit("error: parse_video_target_section: missing key \'source\' in target file %s_target.ini" % (k_ep))

    for k_chapter in non_credit_chapter_keys():
        try:
            if db_video[k_chapter]['k_ed_src'] is None:
                db_video[k_chapter]['k_ed_src'] = k_ed_src
        except:
            pass


    for k_chapter in all_chapter_keys():
        if k_chapter not in db_video.keys():
            # The target will use the chapter defined in the src edition
            db_video[k_chapter] = {
                'k_ed_src': k_ed_src,
            }


    for k_chapter in non_credit_chapter_keys():
        if db_video[k_chapter]['k_ed_src'] is None:
            sys.exit("Errror: parse_video_target_section: edition shall be defined for %s:%s" % (k_ep, k_chapter))



def parse_video_target_g(
    db,
    chapter: str,
    config: ConfigParser,
    k_section,
) -> None:
    db_video: dict = db[chapter]['video']
    fps: float = get_fps(db)

    for k_option in config.options(k_section):
        value_str = config.get(k_section, k_option)
        value_str = value_str.replace(' ','')
        # logger.debug("%s:%s=" % (k_section, k_option), value_str)

        if k_option == 'source':
            tmp = re.match(re.compile(r"([a-z_0-9]+):(ep[0-9]{2})"), value_str)
            if tmp is None:
                sys.exit("Error: wrong value for %s:%s [%s]" % (k_section, k_option, value_str))
            db_video['src'] = {
                'k_ed': tmp.group(1),
                'k_ep': tmp.group(2),
            }
            continue

        # Walk through values
        properties = value_str.split(',')

        chapter_fadeout = 0
        for property in properties:
            search_fadeout = re.search(re.compile(r"fadeout=([0-9.]+)"), property)
            if search_fadeout is not None:
                chapter_fadeout = int(float(search_fadeout.group(1)) * fps)

                db_video['effects'] = {
                    'fadeout': chapter_fadeout,
                }
