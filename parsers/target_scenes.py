from __future__ import annotations
import sys
from copy import deepcopy
from pprint import pprint
from warnings import warn

from .geometry import ChapterGeometry, parse_geometry_file

from .logger import logger
from .helpers import get_fps
from utils.p_print import *
from utils.time_conversions import ms_to_frame
from utils.mco_types import (
    ChapterAudio, RefScene, Scene, ChapterVideo,
)
from scene.src_scene import (
    SrcScenes
)
from ._db import db
from ._keys import Chapter, ep_key, scene_no_str
from .effects import Effect, Effects



def get_scene_no_from_frame_no(k_ed_ep_ch_no: list, frame_no: int) -> int:
    k_ed, k_ep, k_ch, _ = k_ed_ep_ch_no
    scenes: list[Scene] = db[k_ep]['video'][k_ed][k_ch]['scenes']
    for s in scenes:
        if s['start'] <= frame_no < s['start'] + s['count']:
            return s['no']
    raise ValueError(f"frame no. {frame_no} not found in {k_ed_ep_ch_no}")



def consolidate_target_scenes(k_ep: int | str, k_ch: Chapter) -> None:
    """This procedure is used to consolidate chapter of an 'episode': it uses the 'replace'
    field to generate a new list of scenes in the 'common' structure of the 'episode'. This list
    will be used for processing instead of the list defined in the edition.
    It is mainly used for 'asuivre' and 'precedemment' because these chapters use the scenes from the
    following or the previous 'episode'

    Note: this procedure has to be called only when the edition (to process)
    is defined before (i.e. db_video points to the choosen edition/episode/chapter)
    otherwise the target scenes will be overwritten by the other edition.

    Args:
        db_episode_src: the global db
        db_episode_dst: a single scene to consolidate
        k_chapter: chapter to consolidate (mainly 'asuivre' or 'precedemment')

    Returns:
        None

    """
    k_ep = ep_key(k_ep)
    K_EP_DEBUG, K_CHAPTER_DEBUG, SCENE_NO = ['', '', 0]
    # K_EP_DEBUG, K_CHAPTER_DEBUG, SCENE_NO = 'ep01', 'asuivre', 0

    if k_ep == 'ep99':
        return

    ch_video: ChapterVideo = db[k_ep]['video']['target'][k_ch]

    if k_ch in ('precedemment', 'asuivre'):
        print(yellow(f"consolidate_target_scenes: {k_ch}"))
        # pprint(db['ep01']['video']['target'][k_chapter])

    # Get the default source
    default_src = ch_video['default_src']
    k_ed_src, k_ep_src = default_src['k_ed'], default_src['k_ep']
    ch_video_src: ChapterVideo = db[k_ep]['video'][k_ed_src][k_ch]

    if ch_video_src['count'] < 1:
        if k_ch not in ('asuivre', 'precedemment'):
            print(yellow(f"{k_ed_src}:{k_ep}:{k_ch} is empty"))
            raise
        # return

    # Verify that scenes are defined in src or target
    if (
        'scenes' not in ch_video
        and 'scenes' not in ch_video_src
    ):
        # Cannot consolidate because no scenes are defined
        sys.exit(f"error: consolidate_target_scenes: no scenes in {k_ep}:{k_ch}")

    if k_ep==K_EP_DEBUG and k_ch == K_CHAPTER_DEBUG:
        pprint(ch_video)
        print(f"\ncreate_target_scenes: {k_ed_src}:{k_ep}:{k_ch}")

    # List the scene no which are defined in target
    if 'scenes' in ch_video.keys():
        target_scene_nos = (
            [s['no'] for s in ch_video['scenes']]
        )
    else:
        target_scene_nos = []
        ch_video['scenes'] = []

    # Find scene no if not specified in target scene list
    for scene in ch_video['scenes']:
        for src_scene in scene['src'].scenes():
            if src_scene['k_ed_ep_ch_no'][-1] == -1:
                scene_no = get_scene_no_from_frame_no(
                    src_scene['k_ed_ep_ch_no'],
                    frame_no=src_scene['start']
                )
                src_scene['k_ed_ep_ch_no'] = tuple(
                    list(src_scene['k_ed_ep_ch_no'])[:-1] + [scene_no]
                )

    # Append scenes from src and sort
    for scene_src in ch_video_src['scenes']:
        if (
            'scene_count' in ch_video
            and len(ch_video['scenes']) >= ch_video['scene_count']
        ):
            break
        if scene_src['no'] not in target_scene_nos:
            ch_video['scenes'].append(
                Scene(
                    no=scene_src['no'],
                    src=SrcScenes()
                )
            )
            ch_video['scenes'][-1]['src'].add_scene(
                k_ed=k_ed_src,
                k_ep=k_ep_src,
                k_ch=k_ch,
                no=scene_src['no'],
                start=scene_src['start'],
                count=scene_src['count'],
            )

    ch_video['scenes'] = sorted(ch_video['scenes'], key=lambda s: s['no'])
    if k_ep==K_EP_DEBUG and k_ch == K_CHAPTER_DEBUG:
        pprint(ch_video)

    # Consolidate each scene
    # TODO use audio source as ref
    k_ed_ref: str = 'f' if db[k_ep]['audio']['lang'] == 'en' else 'k'
    logger.debug(f"reference for {k_ep}:{k_ch}: {k_ed_ref}:{k_ep}:{k_ch}")
    ref_scenes: list[Scene] = db[k_ep]['video'][k_ed_ref][k_ch]['scenes']
    add_ref: bool = True
    if len(ref_scenes) != len(ch_video['scenes']):
        print(red(f"Target: {len(ch_video['scenes'])}, Reference ({k_ed_ref}): {len(ref_scenes)} scenes"))
        if k_ch != 'episode':
            add_ref = False
        if k_ch in ('precedemment', 'asuivre', 'reportage'):
            # pprint(ref_scenes)
            warn(f"{k_ch}: cannot add reference to every scenes")

    frame_count = 0
    for no, scene in enumerate(ch_video['scenes']):
        if len(scene['src']) == 0:
            in_scene: Scene = ch_video_src['scenes'][no]
            scene['src'].add_scene(
                k_ed=k_ed_src,
                k_ep=k_ep,
                k_ch=k_ch,
                no=in_scene['no'],
                start=in_scene['start'],
                count=in_scene['count'],
                effects=in_scene['effects']
            )

        scene['dst'] = {
            'k_ed': k_ed_src,
            'k_ep': k_ep,
            'k_ch': k_ch,
            'count': scene['src'].frame_count()
        }

        if add_ref and scene['no'] < len(ref_scenes):
            ref_scene = ref_scenes[scene['no']]
            scene['ref'] = RefScene(
                no=ref_scene['no'],
                start=ref_scene['start'],
                count=ref_scene['count'],
            )

        # Calculate frames count
        frame_count += scene['dst']['count']

    # Number of frames without effects
    ch_video['count'] = frame_count


    if k_ep == K_EP_DEBUG and k_ch == K_CHAPTER_DEBUG:
        print(green("-------------------- after ----------------------------\n"))
        print("After consolidation, db_video_target:")
        for k, v in ch_video.items():
            if k != 'scenes':
                print(lightcyan(f"\t{k}"), end='\t')
                print(v)
        print(green("-------------------- after ----------------------------\n"))
        if 'scenes' in ch_video.keys():
            print(lightcyan("\tdb_video_target[scenes]"))
            for s in ch_video['scenes']:
                print(lightcyan(f"\n{scene_no_str(s)}"))
                pprint(s)
            pprint(ch_video['scenes'][SCENE_NO])
        # print("   start: %d" % (db_video_target['start']))
        print(f"   count: {ch_video['count']}")
        print("\n")
        # sys.exit()



def consolidate_target_scenes_g(k_ep: int | str, k_ch: str) -> None:
    """Generate the list of scenes which will be used for this credit
    (opening, precedemment, asuivre, end)
    The total duration (in frames) is updated
    """
    k_ep: str = ep_key(k_ep)
    fps = get_fps(db)
    logger.debug(lightgreen(f"consolidate_target_scenes_g: {k_ep}:{k_ch}"))

    # Get the default source
    default_src = db[k_ch]['video']['default_src']
    k_ed_src, k_ep_src = default_src['k_ed'], default_src['k_ep']
    try:
        ch_video_src: ChapterVideo = db[k_ep_src]['video'][k_ed_src][k_ch]
    except:
        pprint(db[k_ch])
        raise KeyError(f"Error: missing file from edition {k_ed_src}",
                       f"cannot use {k_ep_src}:{k_ch}")

    ch_video: ChapterVideo
    if k_ch in ('g_debut', 'g_fin'):
        ch_video = db[k_ch]['video']

    elif k_ch == 'g_asuivre':
        # Create a structure:
        #   this chapter was not yet defined because it depends on audio start/duration
        # print("create_target_scenes_g;: %s:%s:%s" % ('', k_ep, k_chapter_g))
        try:
            ch_audio = db[k_ep]['audio'][k_ch]
        except:
            sys.exit(f"error: {k_ep}:{k_ch}: audio is not defined or erroneous")

        db[k_ep]['video']['target'][k_ch] = ChapterVideo(
            start=0,
            count=ms_to_frame(ch_audio['duration'], fps),
            scenes=[],
            # effects: Effects
            # geometry: ChapterGeometry
            avsync=0,
            silence=0,
            # task: ProcessingTask
            # inputs: Inputs
            # default_src: VideoSrc
        )
        ch_video = db[k_ep]['video']['target'][k_ch]
        pprint(ch_video)

    elif k_ch == 'g_doc':
        # Create the g_doc structure:
        #   this chapter was not yet defined because it depends on audio start/duration
        ch_audio: ChapterAudio = db[k_ep]['audio'][k_ch]
        ch_audio['count'] = ms_to_frame(ch_audio['duration'], fps)

        db[k_ep]['video']['target'][k_ch] = ChapterVideo(
            start=ms_to_frame(ch_audio['start'], fps),
            count=ch_audio['count'],
            scenes=[],
            # effects: Effects
            # geometry: ChapterGeometry
            avsync=0,
            silence=0,
            # task: ProcessingTask
            # inputs: Inputs
            # default_src: VideoSrc
        )
        ch_video = db[k_ep]['video']['target'][k_ch]

    # List the scene no which are defined in target
    target_scene_nos = ([s['no'] for s in ch_video['scenes']])

    # Append scenes from src and sort
    scene_count: int = (
        ch_video['scene_count']
        if 'scene_count' in ch_video
        else len(ch_video_src['scenes'])
    )
    for no in range(scene_count):
        if no in target_scene_nos:
            continue
        print(f"add {no}")
        scene_src: Scene = ch_video_src['scenes'][no]
        ch_video['scenes'].append(
            Scene(
                no=scene_src['no'],
                src=SrcScenes()
            )
        )
        ch_video['scenes'][-1]['src'].add_scene(
            k_ed=k_ed_src,
            k_ep=k_ep_src,
            k_ch=k_ch,
            no=scene_src['no'],
            start=scene_src['start'],
            count=scene_src['count'],
        )
    # if k_ch == 'g_fin':
    #     pprint(ch_video['scenes'])
    #     raise
    ch_video['scenes'] = sorted(ch_video['scenes'], key=lambda s: s['no'])

    k_ed_ref: str = 'f' if db[k_ch]['audio']['lang'] == 'en' else 'k'
    k_ep_ref: str = 'ep01' if k_ch in ('g_debut', 'g_fin') else k_ep

    # k_ed_ref: str = 's' if k_ch == 'g_fin' else k_ed_ref
    # k_ep_ref: str = 'ep11' if k_ch == 'g_fin' else k_ep_ref

    logger.debug(f"reference for {k_ch}: {k_ed_ref}:{k_ep_ref}:{k_ch}")
    ref_scenes: list[Scene] = (
        db[k_ep_ref]['video'][k_ed_ref][k_ch]['scenes']
    )
    add_ref: bool = True
    if len(ref_scenes) != len(ch_video['scenes']):
        print(f"reference: {k_ed_src}:{k_ep_ref}:{k_ch}")
        print(red(f"Target: {len(ch_video['scenes'])}, Reference ({k_ed_ref}): {len(ref_scenes)} scenes"))
        add_ref = False

    # Calculate frames to generate for each scene
    frame_count: int = 0
    for scene in ch_video['scenes']:
        dst_frame = scene['src'].frame_count(exclude_loop=False)
        scene['dst'] = {
            'k_ep': k_ep,
            'k_ch': k_ch,
            # 'k_ed': k_ed_ref,
            'count': dst_frame,
        }
        frame_count += dst_frame

        if add_ref:
            ref_scene = ref_scenes[scene['no']]
            scene['ref'] = RefScene(
                no=ref_scene['no'],
                start=ref_scene['start'],
                count=ref_scene['count'],
            )


    # Number of frames without effects
    ch_video['count'] = frame_count


    if k_ch in ('g_asuivre', 'g_doc'):
        parse_geometry_file(k_ep_or_g=k_ep, k_ch=k_ch)
        # print("____")
        # pprint(db[k_ep]['video']['target'][k_ch[2:]]['geometry'])
        # raise

        # width: int = db[k_ep]['video']['target'][k_ch[2:]]['geometry'].width
        # for scene in ch_video['scenes']:
        #     if 'geometry' in scene:
        #         scene['geometry'].chapter.width = width
        #         ch_video['geometry'] = ChapterGeometry(width=width)
        #     else:
        #         print(f"target: {k_ep}:{k_ch}")
        #         pprint(scene)
        #         raise ValueError(f"no width defined in {k_ep}:{k_ch[2:]}")

            # if k_ch == 'g_doc':
            #     # pprint(scene['src'].primary_scene()['scene'])
            #     pprint(scene['geometry'])
            #     raise
