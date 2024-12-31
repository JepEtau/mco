from __future__ import annotations
from configparser import ConfigParser
from pprint import pprint
import re
import sys
from warnings import warn

from utils.mco_types import ChapterVideo, Effect, Effects, Scene, VideoSrc
from ._keys import (
    ep_key,
    all_chapter_keys,
    non_credit_chapter_keys,
    main_chapter_keys,
    Chapter,
)
from .helpers import (
    get_fps,
    nested_dict_set,
)
from .logger import logger
from utils.p_print import *
from ._db import db
from .geometry import ChapterGeometry


def get_video_chapter_frame_count(k_ep: str, k_ch: Chapter) -> int:
    video_count: str = 0

    if k_ch in ('g_debut', 'g_fin'):
        db_video = db[k_ch]['video']
        scenes: list[Scene] = db_video['scenes']
        if len(scenes) == 1:
            if db_video['count'] != scenes[0]['count']:
                sys.exit(red(f"consolidate_av_tracks : {k_ep}:{k_ch} todo: correct and remove this as this shall not occur: end"))

        for s in scenes:
            video_count += s['dst']['count']
        if db_video['count'] != video_count:
            sys.exit(red(f"consolidate_av_tracks : error: {k_ep}:{k_ch} consolidate has not been done before: why?"))
        return video_count

    elif k_ch == 'doc':
        print(k_ep)
        print(k_ch)
        ch_video = db[k_ep]['video']['target'][k_ch]
        scenes: list[Scene] = ch_video['scenes']
        for s in scenes:
            print(s['src'].frame_count())
            # print(s['dst']['count'])
            # print(s['src'].primary_scene()['effects'])
            # print()
            video_count += s['src'].frame_count()

        # for s in scenes:
        #     primary_src_scene = s['src'].primary_scene()['scene']
        #     if 'effects' in primary_src_scene:
        #         e: Effect = primary_src_scene['effects'].get_effect('se_loop')
        #         if e is not None:
        #             video_count += sum(e.extra_param)

        #     # print(s['src'].frame_count())
        #     # print(s['dst']['count'])
        #     print(['effects'])
        #     print()

        # pprint(db[k_ep]['video']['target'][k_ch])
        return video_count

    raise NotImplementedError(":".join((k_ep, k_ch)))



def create_ch_target_video(k_ep: str, k_ch: str) -> None:

    # ChapterVideo
    ch_video: ChapterVideo = ChapterVideo(
        start=0,
        end=0,
        count=-1,
        scenes=[],
        effects=Effects(),
        geometry=ChapterGeometry(),
        avsync=0,
        silence=0,
        # Do not define this yet
        task=None,
        inputs=None,
        default_src=VideoSrc(k_ed='', k_ep=k_ep)
    )

    if k_ch in ('g_debut', 'g_fin'):
        if k_ch in db:
            raise ValueError(f"{k_ep}:{k_ch} target video already exists")
        nested_dict_set(db, keys=(k_ch, 'video', 'target'), o=ch_video)

    else:
        if k_ch in db[k_ep]['video']['target']:
            raise ValueError(f"{k_ep}:{k_ch} target video already exists")
        db[k_ep]['video']['target'][k_ch] = ch_video




def parse_video_target(
    db,
    k_ep: str,
    config: ConfigParser,
    k_section,
) -> None:
    db_video = db[k_ep]['video']['target']
    fps: float = get_fps(db)

    logger.debug(lightgreen(f"parse_video_target: {k_ep}"))
    k_ed_src: str = ''

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
        k_ch = k_option
        create_ch_target_video(k_ep=k_ep, k_ch=k_ch)
        # pprint(db_video[k_ch])
        effects: Effects = db_video[k_ch]['effects']
        k_ch_ed_src = ''
        start = 0
        end = -1

        # Walk through values
        properties = value_str.split(',')
        # logger.debug(f"\t{k_ep}:{k_chapter}, properties: ", properties)
        for property in properties:

            if search_start_end := re.search(re.compile(r"(\d+):(-?\d+)"), property):
                start = int(search_start_end.group(1))
                end = int(search_start_end.group(2))

            elif search_fadein := re.search(re.compile(r"fadein=([0-9.]+)"), property):
                chapter_fadein = int(float(search_fadein.group(1)) * fps)
                effects.append(Effect(name='fadein', fade=chapter_fadein))

            if search_fadeout := re.search(re.compile(r"fadeout=([0-9.]+)"), property):
                chapter_fadeout = int(float(search_fadeout.group(1)) * fps)
                effects.append(Effect(name='fadeout', fade=chapter_fadeout))

            if search_k_ed_src := re.search(re.compile(r"ed=([a-z]+[0-9]*)"), property):
                k_ch_ed_src = search_k_ed_src.group(1)

        ch_video: ChapterVideo = db_video[k_ch]
        ch_video.update({
            'start': start,
            'end': end,
            'count': (end - start) if end > 0 else -1,
            'default_src': VideoSrc(
                k_ed=k_ch_ed_src if k_ch_ed_src else k_ed_src,
                k_ep=k_ep
            ),
        })


    if k_ed_src is None:
        raise ValueError(f"error: parse_video_target_section: missing key \'source\' in target file {k_ep}.ini")


    for k_ch in non_credit_chapter_keys():
        if k_ch not in db_video:
            # warn(yellow(f"{k_ep}:{k_ch} is not defined in target video"))
            # The target will use the chapter defined in the src edition
            create_ch_target_video(k_ep, k_ch)

        if not db_video[k_ch]['default_src']['k_ed']:
            db_video[k_ch]['default_src']['k_ed'] = k_ed_src



def parse_video_target_g(
    ch_video: ChapterVideo,
    config: ConfigParser,
    k_section: str,
    k_ch: str,
) -> None:
    fps: float = get_fps(db)
    k_ep: str = "ep99"

    for k_option in config.options(k_section):
        value_str = config.get(k_section, k_option)
        value_str = value_str.replace(' ','')
        logger.debug(f"{k_section}:{k_option}={value_str}")

        if k_option == 'source':
            tmp = re.search(re.compile(r"([a-z_0-9]+):(ep[0-9]{2})"), value_str)
            if tmp is None:
                sys.exit(f"Error: wrong value for {k_section}:{k_option} [{value_str}]")
            ch_video['default_src'] = VideoSrc(k_ed=tmp.group(1), k_ep=tmp.group(2))
            continue

        start = None
        end = -1

        # Walk through values
        properties = value_str.split(',')

        effects: Effects = ch_video['effects']
        for property in properties:
            if search_start_end := re.search(re.compile(r"(\d+):(-?\d+)"), property):
                start = int(search_start_end.group(1))
                end = int(search_start_end.group(2))

            elif result := re.search(re.compile(r"fadeout=([0-9.]+)"), property):
                chapter_fadeout = int(float(result.group(1)) * fps)
                effects.append(Effect(name='fadeout', fade=chapter_fadeout))

            elif result := re.search(re.compile(r"fadein=([0-9.]+)"), property):
                chapter_fadein = int(float(result.group(1)) * fps)
                effects.append(Effect(name='fadein', fade=chapter_fadein))


        ch_video.update({
            'effects': effects,
            'start': start,
            'end': end,
            'count': (end - start) if end > 0 else -1,
            'k_ep': k_ep,
            'k_ch': k_ch,
        })
