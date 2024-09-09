import sys
from copy import deepcopy
from pprint import pprint

from .logger import logger
from .helpers import get_fps
from utils.p_print import *
from utils.time_conversions import ms_to_frame
from utils.mco_types import (
    ChapterAudio, Effect, Effects, RefScene, Scene, ChapterVideo,
)
from scene.src_scene import (
    SrcScenes
)
from ._db import db
from ._types import key


def consolidate_target_scenes(k_ep: int | str, k_chapter: str) -> None:
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
    k_ep = key(k_ep)
    K_EP_DEBUG, K_CHAPTER_DEBUG, SCENE_NO = ['', '', 0]
    # K_EP_DEBUG, K_CHAPTER_DEBUG, SCENE_NO = 'ep01', 'episode', 0

    if k_ep == 'ep99':
        return

    target_chapter: ChapterVideo = db[k_ep]['video']['target'][k_chapter]

    # if k_chapter == 'episode':
    #     print(yellow("consolidate_target_scenes:start"))
    #     pprint(db['ep01']['video']['target'])

    k_ed_src = target_chapter['k_ed_src']
    chapter_src: ChapterVideo = db[k_ep]['video'][k_ed_src][k_chapter]

    if chapter_src['count'] < 1:
        return

    # Verify that scenes are defined in src or target
    if (
        'scenes' not in target_chapter
        and 'scenes' not in chapter_src
    ):
        # Cannot consolidate because no scenes are defined
        sys.exit(f"error: consolidate_target_scenes: no scenes in {k_ep}:{k_chapter}")

    if k_ep==K_EP_DEBUG and k_chapter == K_CHAPTER_DEBUG:
        pprint(target_chapter)
        print(f"\ncreate_target_scenes: {k_ed_src}:{k_ep}:{k_chapter}")

    # List the scene no which are defined in target
    if 'scenes' in target_chapter.keys():
        target_scene_nos = ([s['no'] for s in target_chapter['scenes']])
    else:
        target_scene_nos = []
        target_chapter['scenes'] = []

    # Append scenes from src and sort
    for scene_src in chapter_src['scenes']:
        if scene_src['no'] not in target_scene_nos:
            target_chapter['scenes'].append(
                Scene(
                    no=scene_src['no'],
                    src=SrcScenes()
                )
            )
    target_chapter['scenes'] = sorted(target_chapter['scenes'], key=lambda s: s['no'])
    if k_ep==K_EP_DEBUG and k_chapter == K_CHAPTER_DEBUG:
        pprint(target_chapter)

    # Consolidate each scene
    # src:
    #   if defined in target:
    #       - define a ed/ep/chapter
    #       - define a different scene
    #       - define a different start/count of frames
    #   else:
    #       - use the values from the default src scene
    # dst:
    #       - define this ed/ep/chapter for this scene
    # k_ed/k_ep/k_chapter:
    #       - related to the scene defined by the src structure
    #
    k_ed_ref: str = 'f' if db[k_ep]['audio']['lang'] == 'en' else 'k'

    if k_ep == 'ep01' and k_chapter in ('episode'):
        print(red("REWORK ep01 db"))
        k_ed_ref = 'f'

    ref_scenes: list[Scene] = db[k_ep]['video'][k_ed_ref][k_chapter]['scenes']
    add_ref: bool = True
    if len(ref_scenes) != len(target_chapter['scenes']):
        print(f"reference: {k_ed_src}:{k_ep}:{k_chapter}")
        print(red(f"Target: {len(target_chapter['scenes'])}, Reference: {len(ref_scenes)} scenes"))
        add_ref = False
        if k_chapter in ('episode'):
            pprint(ref_scenes)
            raise ValueError

    frame_count = 0
    for no, target_scene in enumerate(target_chapter['scenes']):
        if len(target_scene['src']) == 0:
            in_scene: Scene = chapter_src['scenes'][no]
            target_scene['src'].add_scene(
                k_ed=k_ed_src,
                k_ep=k_ep,
                k_ch=k_chapter,
                no=in_scene['no'],
                start=in_scene['start'],
                count=in_scene['count'],
            )

        target_scene['dst'] = {
            'k_ed': k_ed_src,
            'k_ep': k_ep,
            'k_ch': k_chapter,
            'count': target_scene['src'].frame_count()
        }

        if add_ref:
            target_scene['ref'] = RefScene(
                no=ref_scenes[no]['no'],
                start=ref_scenes[no]['start'],
                count=ref_scenes[no]['count'],
            )

        # Calculate frames count
        frame_count += target_scene['dst']['count']

    # Number of frames without effects
    target_chapter['count'] = frame_count


    if k_ep == K_EP_DEBUG and k_chapter == K_CHAPTER_DEBUG:
        print(green("-------------------- after ----------------------------\n"))
        print("After consolidation, db_video_target:")
        for k, v in target_chapter.items():
            if k != 'scenes':
                print(lightcyan(f"\t{k}"), end='\t')
                print(v)
        print(green("-------------------- after ----------------------------\n"))
        if 'scenes' in target_chapter.keys():
            print(lightcyan("\tdb_video_target[scenes]"))
            for s in target_chapter['scenes']:
                print(lightcyan(f"\n{s['no']:03}"))
                pprint(s)
            pprint(target_chapter['scenes'][SCENE_NO])
        # print("   start: %d" % (db_video_target['start']))
        print("   count: %d" % (target_chapter['count']))
        print("\n")
        # sys.exit()



def consolidate_target_scenes_g(k_ep: int | str, k_chapter: str) -> None:
    """Generate the list of scenes which will be used for this credit
    (opening, precedemment, asuivre, end)
    The total duration (in frames) is updated
    """
    k_ep: str = key(k_ep)
    fps = get_fps(db)
    logger.debug(lightgreen(f"consolidate_target_scenes_g: {k_ep}:{k_chapter}"))

    # Get the default source
    src_video = db[k_chapter]['video']['src']
    k_ed_src, k_ep_src = src_video['k_ed'], src_video['k_ep']
    try:
        chapter_src: ChapterVideo = db[k_ep_src]['video'][k_ed_src][k_chapter]
    except:
        pprint(db[k_chapter])
        raise KeyError(f"Error: missing file from edition {k_ed_src}",
                       f"cannot use {k_ep_src}:{k_chapter}")


    if k_chapter in ('g_debut', 'g_fin'):
        target_chapter: ChapterVideo = db[k_chapter]['video']
        if 'avsync' in target_chapter.keys():
            print("############# consolidate_target_scenes_g: avsync shall not be reset to 0: %d" % (target_chapter['avsync']))
            target_chapter.update({
                'avsync': 0,
            })
        else:
            target_chapter['avsync'] = 0

    elif k_chapter == 'g_asuivre':
        # Create a structure:
        #   this chapter was not yet defined because it depends on audio start/duration
        # print("create_target_scenes_g;: %s:%s:%s" % ('', k_ep, k_chapter_g))
        try:
            db_audio = db[k_ep]['audio'][k_chapter]
        except:
            sys.exit(f"error: {k_ep}:{k_chapter}: audio is not defined or erroneous")
        db_audio['avsync'] = 0
        db[k_ep]['video']['target'][k_chapter] = {
            'start': 0,
            'count': ms_to_frame(db_audio['duration'], fps),
            'avsync': 0,
            # 'dst': {
            #     'k_ep': k_ep,
            #     'k_ch': k_chapter_g,
            # },
        }
        target_chapter = db[k_ep]['video']['target'][k_chapter]

    elif k_chapter == 'g_documentaire':
        # Create the g_documentaire structure:
        #   this chapter was not yet defined because it depends on audio start/duration
        db_audio: ChapterAudio = db[k_ep]['audio'][k_chapter]
        try:
            db_audio = db[k_ep]['audio'][k_chapter]
        except:
            sys.exit(f"error: {k_ep}:{k_chapter}: audio is not defined or erroneous")
        audio_count = ms_to_frame(db_audio['duration'], fps)
        db_audio.update({
            'count': audio_count,
            'avsync': 0,
        })
        db[k_ep]['video']['target'][k_chapter] = {
            'start': ms_to_frame(db_audio['start'], fps),
            'count': audio_count,
            'avsync': 0,
        }
        target_chapter = db[k_ep]['video']['target'][k_chapter]


    # Verify that scenes are defined in src or target
    if (
        'scenes' not in target_chapter.keys()
        and 'scenes' not in chapter_src.keys()
    ):
        sys.exit(red("error: %s.create_target_scenes: no scenes in src/dst %s:%s" % (__name__, k_ep, k_chapter)))


    # List the scene no which are defined in target
    if 'scenes' in target_chapter.keys():
        target_scene_nos = ([s['no'] for s in target_chapter['scenes']])
    else:
        target_scene_nos = []
        target_chapter['scenes'] = []


    # Append scenes from src and sort
    for scene_src in chapter_src['scenes']:
        if scene_src['no'] not in target_scene_nos:
            target_chapter['scenes'].append(
                Scene(
                    no=scene_src['no'],
                    src=SrcScenes()
                )
            )
    target_chapter['scenes'] = sorted(target_chapter['scenes'], key=lambda s: s['no'])


    k_ed_ref: str = 'f' if db[k_chapter]['audio']['lang'] == 'en' else 'k'
    # k_ed_src, k_ep_src = src_video['k_ed'], src_video['k_ep']

    print(red(f"target scenes, reference: {k_ed_src}:{k_ep_src}:{k_chapter}"))
    # sys.exit()
    ref_scenes: list[Scene] = db[k_ep_src]['video'][k_ed_src][k_chapter]['scenes']
    add_ref: bool = True
    if len(ref_scenes) != len(target_chapter['scenes']):
        print(f"reference: {k_ed_src}:{k_ep}:{k_chapter}")
        print(red(f"Target: {len(target_chapter['scenes'])}, Reference: {len(ref_scenes)} scenes"))
        add_ref = False

    frame_count: int = 0
    for no, target_scene in enumerate(target_chapter['scenes']):
        # TODO: 'dst' count may be erroneous... to validate
        if len(target_scene['src']) == 0:
            in_scene: Scene = chapter_src['scenes'][no]
            target_scene['src'].add_scene(
                k_ed=k_ed_src,
                k_ep=k_ep_src,
                k_ch=k_chapter,
                no=in_scene['no'],
                start=in_scene['start'],
                count=in_scene['count'],
            )

        target_scene['dst'] = {
            'k_ed': k_ed_src,
            'k_ep': k_ep,
            'k_ch': k_chapter,
            'count': target_scene['src'].frame_count()
        }

        if add_ref:
            target_scene['ref'] = RefScene(
                no=ref_scenes[no]['no'],
                start=ref_scenes[no]['start'],
                count=ref_scenes[no]['count'],
            )

        frame_count += target_scene['dst']['count']

    # Number of frames without effects
    target_chapter['count'] = frame_count

    # Effects
    if k_chapter in ('g_debut', 'g_fin'):
        target_chapter: ChapterVideo = db[k_chapter]['video']
        if 'effects' in target_chapter:
            last_scene = target_chapter['scenes'][-1]

            effect: Effect = target_chapter['effects'].primary_effect()
            if 'fadeout' in effect.name:
                fadeout_count: int = effect.fade
                frame_no = last_scene['src'].last_frame_no()
                last_scene['effects'] = Effects([
                    Effect(
                        name='fadeout',
                        frame_ref=frame_no - fadeout_count + 1,
                        fade=fadeout_count
                    )
                ])

