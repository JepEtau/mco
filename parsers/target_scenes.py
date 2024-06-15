import sys
from copy import deepcopy
from pprint import pprint

from .logger import logger
from .helpers import get_fps, nested_dict_set
from utils.p_print import *
from utils.time_conversions import ms_to_frame
from utils.mco_types import ChapterAudio, Scene, VideoChapter
from ._db import db
from ._types import key


def consolidate_target_scenes(k_ep: int | str, k_chapter: str):
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

    chapter_target: VideoChapter = db[k_ep]['video']['target'][k_chapter]

    # if k_chapter == 'episode':
    #     print(yellow("consolidate_target_scenes:start"))
    #     pprint(db['ep01']['video']['target'])

    k_ed_src = chapter_target['k_ed_src']
    chapter_src: VideoChapter = db[k_ep]['video'][k_ed_src][k_chapter]

    if chapter_src['count'] < 1:
        return

    # Verify that scenes are defined in src or target
    if (
        'scenes' not in chapter_target
        and 'scenes' not in chapter_src
    ):
        # Cannot consolidate because no scenes are defined
        sys.exit(f"error: consolidate_target_scenes: no scenes in {k_ep}:{k_chapter}")

    if k_ep==K_EP_DEBUG and k_chapter == K_CHAPTER_DEBUG:
        pprint(chapter_target)
        print(f"\ncreate_target_scenes: {k_ed_src}:{k_ep}:{k_chapter}")

    # List the scene no which are defined in target
    if 'scenes' in chapter_target.keys():
        target_scene_nos = ([s['no'] for s in chapter_target['scenes']])
    else:
        target_scene_nos = []
        chapter_target['scenes'] = []

    # Append scenes from src and sort
    for scene_src in chapter_src['scenes']:
        if scene_src['no'] not in target_scene_nos:
            chapter_target['scenes'].append(deepcopy(scene_src))
    chapter_target['scenes'] = sorted(chapter_target['scenes'], key=lambda s: s['no'])

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
    frame_count = 0
    for target_scene in chapter_target['scenes']:
        # TODO: 'dst' count may be erroneous... to validate

        if 'src' not in target_scene.keys() and 'dst' not in target_scene.keys():
            # Scene is copied from src
            target_scene.update({
                'src': {
                    'k_ed': k_ed_src,
                    'k_ep': k_ep,
                    'k_ch': k_chapter,
                    'no': target_scene['no'],
                    'start': target_scene['start'],
                    'count': target_scene['count'],
                    'replace': False,
                },
                'dst': {
                    'k_ed': k_ed_src,
                    'k_ep': k_ep,
                    'k_ch': k_chapter,
                    'count': target_scene['count'],
                },
                'k_ed': k_ed_src,
                'k_ep': k_ep,
                'k_ch': k_chapter,
            })

        elif 'src' in target_scene.keys():
            # Scene was defined in target section

            target_scene['src']['replace'] = True

            # Add the missing field in 'src' dict
            d = {
                'k_ed': k_ed_src,
                'k_ep': k_ep,
                'k_ch': k_chapter,
                'no': target_scene['no'],
            }
            for k, v in d.items():
                if k not in target_scene['src'].keys():
                    target_scene['src'][k] = v


            # Copy properties from src
            _k_ed_src = target_scene['src']['k_ed']
            _k_ep_src = target_scene['src']['k_ep']
            _k_chapter_src = target_scene['src']['k_ch']
            _scene_no_src = target_scene['src']['no']
            _scene_src: Scene = db[_k_ep_src]['video'][_k_ed_src][_k_chapter_src]['scenes'][_scene_no_src]
            for k in _scene_src.keys():
                if k not in target_scene.keys():
                    target_scene[k] = deepcopy(_scene_src[k])

            if 'segments' in target_scene['src'].keys():
                dst_count = 0
                for s in target_scene['src']['segments']:
                    dst_count += s['count']

            else:
                # Use the frame start/count from the original scene
                for k in ['start', 'count']:
                    if k not in target_scene['src'].keys():
                        target_scene['src'][k] = target_scene[k]

                dst_count = min(target_scene['count'], target_scene['src']['count'])
                if dst_count > target_scene['count']:
                    print(red(f"error: {k_ep}:{k_chapter}, not enough frames in src to generate scene no. {target_scene['no'],}"))
                    sys.exit()


            target_scene.update({
                'dst': {
                    'k_ed': k_ed_src,
                    'k_ep': k_ep,
                    'k_ch': k_chapter,
                    'count': dst_count,
                },

                'k_ed': _k_ed_src,
                'k_ep': _k_ep_src,
                'k_ch': _k_chapter_src,
            })
        else:
            print(red(f"{k_ep}:{k_chapter} Error: do not know what to do with: {target_scene}"))

        # Calculate frames count
        frame_count += target_scene['dst']['count']

    # Set frame count for this chapter
    chapter_target['count'] = frame_count


    if k_ep == K_EP_DEBUG and k_chapter == K_CHAPTER_DEBUG:
        print(green("-------------------- after ----------------------------\n"))
        print("After consolidation, db_video_target:")
        for k, v in chapter_target.items():
            if k != 'scenes':
                print(lightblue("\t%s" % (k), end='\t'))
                print(v)
        print(green("-------------------- after ----------------------------\n"))
        if 'scenes' in chapter_target.keys():
            print(lightblue("\tdb_video_target[scenes]"))
            for s in chapter_target['scenes']:
                print(lightcyan(f"\n{s['no']:03}"))
                pprint(s)
            pprint(chapter_target['scenes'][SCENE_NO])
        # print("   start: %d" % (db_video_target['start']))
        print("   count: %d" % (chapter_target['count']))
        print("\n")
        sys.exit()



def consolidate_target_scenes_g(k_ep: int | str, k_chapter_c: str) -> None:
    """Generate the list of scenes which will be used for this credit
    (opening, precedemment, asuivre, end)
    The total duration (in frames) is updated
    """
    k_ep: str = key(k_ep)
    fps = get_fps(db)
    logger.debug(lightgreen(f"consolidate_target_scenes_g: {k_ep}:{k_chapter_c}"))

    # Get the default source
    src_video = db[k_chapter_c]['video']['src']
    k_ed_src, k_ep_src = src_video['k_ed'], src_video['k_ep']
    try:
        db_video_src = db[k_ep_src]['video'][k_ed_src][k_chapter_c]
    except:
        pprint(db[k_chapter_c])
        raise KeyError(f"Error: missing file from edition {k_ed_src}",
                       f"cannot use {k_ep_src}:{k_chapter_c}")

    if k_chapter_c in ('g_debut', 'g_fin'):
        db_video_target: VideoChapter = db[k_chapter_c]['video']
        if 'avsync' in db_video_target.keys():
            print("############# consolidate_target_scenes_g: avsync shall not be reset to 0: %d" % (db_video_target['avsync']))
            db_video_target.update({
                'avsync': 0,
            })
        else:
            db_video_target['avsync'] = 0

    elif k_chapter_c == 'g_asuivre':
        # Create a structure:
        #   this chapter was not yet defined because it depends on audio start/duration
        # print("create_target_scenes_g;: %s:%s:%s" % ('', k_ep, k_chapter_g))
        try:
            db_audio = db[k_ep]['audio'][k_chapter_c]
        except:
            sys.exit(f"error: {k_ep}:{k_chapter_c}: audio is not defined or erroneous")
        db_audio['avsync'] = 0
        db[k_ep]['video']['target'][k_chapter_c] = {
            'start': 0,
            'count': ms_to_frame(db_audio['duration'], fps),
            'avsync': 0,
            # 'dst': {
            #     'k_ep': k_ep,
            #     'k_ch': k_chapter_g,
            # },
        }
        db_video_target = db[k_ep]['video']['target'][k_chapter_c]

    elif k_chapter_c == 'g_documentaire':
        # Create the g_documentaire structure:
        #   this chapter was not yet defined because it depends on audio start/duration
        db_audio: ChapterAudio = db[k_ep]['audio'][k_chapter_c]
        try:
            db_audio = db[k_ep]['audio'][k_chapter_c]
        except:
            sys.exit(f"error: {k_ep}:{k_chapter_c}: audio is not defined or erroneous")
        audio_count = ms_to_frame(db_audio['duration'], fps)
        db_audio.update({
            'count': audio_count,
            'avsync': 0,
        })
        db[k_ep]['video']['target'][k_chapter_c] = {
            'start': ms_to_frame(db_audio['start'], fps),
            'count': audio_count,
            'avsync': 0,
        }
        db_video_target = db[k_ep]['video']['target'][k_chapter_c]


    # Verify that scenes are defined in src or target
    if (
        'scenes' not in db_video_target.keys()
        and 'scenes' not in db_video_src.keys()
    ):
        sys.exit(red("error: %s.create_target_scenes: no scenes in src/dst %s:%s" % (__name__, k_ep, k_chapter_c)))


    # List the scene no which are defined in target
    if 'scenes' in db_video_target.keys():
        target_scene_nos = ([s['no'] for s in db_video_target['scenes']])
    else:
        target_scene_nos = []
        db_video_target['scenes'] = []


    # Append scenes from src and sort
    for scene_src in db_video_src['scenes']:
        if scene_src['no'] not in target_scene_nos:
            db_video_target['scenes'].append(deepcopy(scene_src))
    db_video_target['scenes'] = sorted(db_video_target['scenes'], key=lambda s: s['no'])


    frame_count = 0
    for scene in db_video_target['scenes']:
        # TODO: 'dst' count may be erroneous... to validate
        if 'src' not in scene.keys():
            # Scene is copied from src
            scene.update({
                'src': {
                    'k_ed': k_ed_src,
                    'k_ep': k_ep_src,
                    'k_ch': k_chapter_c,
                    'no': scene['no'],
                    'start': scene['start'],
                    'count': scene['count'],
                },
                'dst': {
                    'k_ed': k_ed_src,
                    'k_ep': k_ep,
                    'k_ch': k_chapter_c,
                    'count': scene['count'],
                },
                'k_ed': k_ed_src,
                'k_ep': k_ep_src,
                'k_ch': k_chapter_c,
            })

        else:
            # Scene was defined in target
            if 'k_ed' not in scene['src'].keys():
                scene['src']['k_ed'] = k_ed_src
            if 'k_ep' not in scene['src'].keys():
                scene['src']['k_ep'] = k_ep
            if 'k_ch' not in scene['src'].keys():
                scene['src']['k_ch'] = k_chapter_c
            if 'no' not in scene['src'].keys():
                scene['src']['no'] = scene['no']

            # Copy properties from src
            _k_ed_src = scene['src']['k_ed']
            _k_ep_src = scene['src']['k_ep']
            _k_chapter_src = scene['src']['k_ch']
            _scene_no_src = scene['src']['no']
            _scene_src = db[_k_ep_src]['video'][_k_ed_src][_k_chapter_src]['scenes'][_scene_no_src]
            for k in _scene_src.keys():
                if k not in scene.keys():
                    scene[k] = deepcopy(_scene_src[k])

            if 'count' not in scene['src'].keys():
                scene['src']['count'] = scene['count']
            if 'start' not in scene['src'].keys():
                scene['src']['start'] = scene['start']

            scene.update({
                'dst': {
                    'k_ed': k_ed_src,
                    'k_ep': k_ep,
                    'k_ch': k_chapter_c,
                    'count': scene['count'],
                },
                'k_ed': _k_ed_src,
                'k_ep': _k_ep_src,
                'k_ch': _k_chapter_src,
            })


        # Calculate frames count
        frame_count += scene['count']

    db_video_target['count'] = frame_count


    # Effects
    if k_chapter_c in ('g_debut', 'g_fin'):
        db_video_target = db[k_chapter_c]['video']
        if 'effects' in db_video_target.keys():
            last_scene = db_video_target['scenes'][-1]

            if 'fadeout' in db_video_target['effects'].keys():
                fadeout_count = db_video_target['effects']['fadeout']
                frame_no = last_scene['src']['start'] + last_scene['src']['count'] - 1
                nested_dict_set(last_scene,
                    ['fadeout', frame_no - fadeout_count + 1, fadeout_count], 'effects')
