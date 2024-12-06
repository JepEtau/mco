from __future__ import annotations
import sys
from pprint import pprint

from scene.src_scene import SrcScene, SrcScenes
from .logger import logger
from ._keys import (
    main_chapter_keys,
)
from .audio import get_fps
from .helpers import nested_dict_set
from utils.p_print import *
from utils.time_conversions import (
    frame_to_ms,
    ms_to_frame,
)
from utils.mco_types import ChapterVideo, Effect, Effects, Scene
from ._db import db



def consolidate_av_sync(k_ep: str):
    episode = db[k_ep]
    fps = get_fps(db)
    logger.debug(lightgreen(f"consolidate_av_sync"))

    if ('audio' not in episode or 'video' not in episode):
        sys.exit("calculate_av_sync: error, audio or video does not exist in %s:common" % (__name__, k_ep))
        return
    db_target_video = episode['video']['target']
    tvideo_track = episode['video']['target']
    audio_track: dict = episode['audio']

    p_target_video: ChapterVideo = episode['video']['target']['precedemment']
    pprint(p_target_video)

    # precedemment
    k_ch = 'precedemment'
    # no avsync for precedemment
    audio_track['precedemment']['avsync'] = 0

    # initialize avsync of episode to 0to 0
    audio_track['episode']['avsync'] = 0
    p_target_video['avsync'] = 0
    tvideo_track['episode']['avsync'] = 0

    if k_ch in audio_track and audio_track[k_ch]['duration'] != 0:
        # edition used as the src for the audio track

        # get edition used for the track: k for fr, f for en
        k_ed_audio_src = audio_track['src']['k_ed']

        print(red("AVsync\n-------------------"))
        logger.debug(f"k_ed_audio_src: {k_ed_audio_src}")
        p_video_count = p_target_video['count']
        p_audio_count = ms_to_frame(audio_track['precedemment']['duration'], fps)

        print(f"Target: precedemment video count: {p_video_count}")
        print(f"Target: precedemment audio count: {p_audio_count}")
        if p_video_count > p_audio_count:
            raise ValueError(f"Precedemment is too long ({p_video_count} > {p_audio_count})")
        elif p_video_count < p_audio_count:
            raise NotImplementedError("Add loop and fadeout")


        e_vchapter: ChapterVideo = db_target_video['episode']
        e_s0_vcount: int = e_vchapter['scenes'][0]['src'].frame_count()
        e_s0_acount: int = (
            episode['video'][k_ed_audio_src]['episode']['scenes'][1]['start']
            - ms_to_frame(audio_track['episode']['start'], fps)
        )
        print(f"Target: episode, 1st scene video count: {e_s0_vcount}")
        print(f"Target: episode, 1st scene audio count: {e_s0_acount}")


        if e_s0_vcount > e_s0_acount:
            raise ValueError(f"episode, scene 0 is too long ({e_s0_vcount} > {e_s0_acount})")
            # TODO: cut and fadein
        elif e_s0_vcount < e_s0_acount:

            loop_count = e_s0_acount - e_s0_vcount
            # minimum between diff and 1.5s
            fade = min(loop_count, int(2 * fps))
            if 'effects' not in e_vchapter:
                print(red("TODO: add default effects in chapter"))
                e_vchapter['effects'] = Effects()
            e_vchapter['effects'].append(
                Effect(
                    name='loop_and_fadein',
                    loop=loop_count,
                    fade=fade,
                )
            )
            tvideo_track['episode']['count'] += loop_count
            logger.debug(f"Fade in and loop at the beginning of the episode: {loop_count}, fade={fade}")


        # # Compare video count from audio_src and target

        # # TODO: we cans use scene['ref'] which has the start specified
        # print(red("AVsync to be verified with fadeout+loop\n-------------------"))
        # # _calculate_precedemment_target_vcount(k_ep, k_ch)
        # print(yellow(p_target_video['count']))
        # print(yellow(p_target_video['scenes'][0]['src'].frame_count()))
        # p_vcount: int = p_target_video['count'] - p_target_video['scenes'][0]['src'].frame_count()
        # p_s1_ref: int = episode['video'][k_ed_audio_src]['precedemment']['scenes'][1]

        # e_vchapter: ChapterVideo = db_target_video['episode']
        # e_s0_vcount: int = e_vchapter['scenes'][0]['src'].frame_count()
        # e_s1_ref: int = episode['video'][k_ed_audio_src]['episode']['scenes'][1]
        # e_slast_ref: int = episode['video'][k_ed_audio_src]['episode']['scenes'][-1]

        # # p_ref_vcount is the audio duration between p_s1 and e_s1 "reference"
        # # p_target_vcount is the video duration between p_s1 and e_s1 "target" w/out adding silences
        # print(f"audio source: {k_ed_audio_src}")
        # p_target_vcount: int = 0
        # try:
        #     p_ref_vcount = e_s1_ref['start'] - p_s1_ref['start']
        #     p_target_vcount = p_vcount + e_s0_vcount
        # except:
        #     pprint(episode['video'].keys())
        #     pprint(episode['video']['target'].keys())
        #     pprint(episode['video']['target']['precedemment'])
        #     raise ValueError(f"{k_ep}:{k_ch}: video scenes are not defined. They are required to calculate AV sync values.")
        # print(f"Src video count: {p_ref_vcount}")

        # logger.debug(lightgrey(f"AVsync: precedemment to episode (use the 2nd scene):"))
        # logger.debug(lightgrey(f"  video count ({k_ed_audio_src}): {p_ref_vcount}"))
        # logger.debug(lightgrey(f"  video count (target): {p_target_vcount}"))
        # if p_ref_vcount != p_target_vcount:
        #     print(yellow(f"[W] precedemment to episode: erroneous frame count between audio ref ({k_ed_audio_src}) and target:"))
        #     print(yellow(f"  {p_ref_vcount}, {p_target_vcount}"))


        # # Verifications before consolidating AVsync
        # episode_src_count = e_slast_ref['start'] - e_s1_ref['start']
        # episode_target_count = 0
        # for scene in tvideo_track['episode']['scenes'][1:-1]:
        #     episode_target_count += scene['dst']['count']

        # avsync_episode = 0
        # if episode_src_count != episode_target_count:
        #     # ep: 2, 13, 22
        #     print(red(f"\twarning: target vs source: erroneous frame count:"),
        #             f"target: {episode_target_count}, src ({k_ed_audio_src}): {episode_src_count}")
        #     # sys.exit()
        #     avsync_episode = episode_target_count - episode_src_count


        # # Now synchronize all

        # # offset used to change referentiel: target -> src
        # # offset = src - target
        # e_tscenes: list[Scene] = tvideo_track['episode']['scenes']
        # offset_src_to_target = e_tscenes[1]['src'].first_frame_no() - e_s1_ref['start']

        # # audio start in target referentiel
        # precedemment_audio_start = (
        #     ms_to_frame(audio_track['precedemment']['start'], fps)
        #     + offset_src_to_target
        # )

        # # Precedemment: let's set the 1st frame of video aligned with the audio start
        # p_target_video['avsync'] = 0

        # # We moved the precedemment part, calculate new silence between precedemment and episode
        # p_ref_vcount = tvideo_track['precedemment']['count']
        # video_silence = (
        #     e_tscenes[0]['src'].first_frame_no()
        #     - (precedemment_audio_start + p_ref_vcount)
        # )

        # p_audio_count = ms_to_frame(audio_track['precedemment']['duration'], fps)

        # logger.debug(f"\tsrc to target offset: {offset_src_to_target}")
        # logger.debug(f"\tprecedemment_audio_start: {precedemment_audio_start}")
        # logger.debug(f"\tprecedemment_video_count: {p_ref_vcount}")
        # logger.debug(f"\tepisode_video_start: {e_tscenes[0]['src'].first_frame_no()}")
        # logger.debug(f"\tprecedemment, audio_count: {p_audio_count}")
        # logger.debug(f"\tvideo_silence: {video_silence}")

        # p_last_scene: Scene = p_target_video['scenes'][-1]
        # first_scene_episode: Scene = tvideo_track['episode']['scenes'][0]
        # logger.debug(f"\tlast_scene_precedemment: end: {p_last_scene['src'].first_frame_no() + p_last_scene['dst']['count']}")
        # logger.debug(f"\tfirst_scene_episode: start: {first_scene_episode['src'].first_frame_no()}")

        # # !!! Overlapped scenes
        # if video_silence < 0:
        #     # overlap
        #     logger.debug(lightgreen(f"precedemment to episode: remove {abs(video_silence)} frames"))
        #     video_silence = abs(video_silence)

        #     if p_audio_count > p_ref_vcount:
        #         # Remove frames from episode
        #         # fr: ep no. 19
        #         # fadein to do
        #         # ep26 (99 frames)?????
        #         # validated (2023-08-28): 19
        #         logger.debug(f"\tepisode: remove {abs(video_silence)} frames")
        #         first_scene_episode['start'] += video_silence
        #         first_scene_episode['count'] -= video_silence
        #         first_scene_episode['dst']['count'] -= video_silence
        #         tvideo_track['episode']['count'] -= video_silence
        #     else:
        #         # Remove frames from precedemment
        #         # fr: ep no. 14, 36
        #         # validated (2023-08-26): 14, 36
        #         # TODO: Improve: ep14, use fadeout
        #         # validated (2023-09-07): 3,
        #         logger.debug(f"\tprecedemment: remove {abs(video_silence)} frames")
        #         p_last_scene['count'] -= video_silence
        #         p_last_scene['dst']['count'] -= video_silence
        #         tvideo_track['precedemment']['count'] -= video_silence

        # # Add video silence between precedemment and episode
        # elif video_silence > 0:
        #     logger.debug(lightgreen(f"precedemment to episode: add video silence: {abs(video_silence)} frames"))

        #     if p_audio_count > p_ref_vcount:
        #         # fr: ep no. 6, 7, 8, 9, 10, 11, 12, 13, 15, 16, 17, 18,
        #         #               20, 21, 22, 23, 24, 25, 26, 27, 28, 29,
        #         #               30, 31, 32, 34, 35, 37, 38, 39
        #         # validated (2023-09-07): 4, 5,
        #         logger.debug(f"\tprecedemment: loop and fadeout")
        #         av_diff = p_audio_count - p_ref_vcount

        #         logger.debug(f"\tav_diff : {p_audio_count - p_ref_vcount}")
        #         # Add loop_and_fadeout to precedemment up to end of audio
        #         if av_diff <= video_silence:
        #             logger.debug(purple("no need to revalidate"))

        #             loop_count = p_audio_count - p_ref_vcount
        #             loop_start = (
        #                 p_last_scene['src'].first_frame_no()
        #                 + p_last_scene['dst']['count'] - 1
        #             )
        #             p_last_scene['effects'] = Effects([
        #                 Effect(
        #                     name='loop_and_fadeout',
        #                     frame_ref=loop_start,
        #                     loop=loop_count,
        #                     fade=loop_count
        #                 )
        #             ])
        #             p_target_video['count'] += loop_count

        #             # If the amount of added frames were not enough
        #             # Add silence at the beginning of the episode or fade_in
        #             if loop_count < video_silence:
        #                 loop_count = video_silence - loop_count
        #                 db_target_video['episode']['effects'] = Effects([
        #                     Effect(
        #                         name='loop_and_fadein',
        #                         loop=loop_count,
        #                         fade=0,
        #                     )
        #                 ])
        #                 tvideo_track['episode']['count'] += loop_count
        #                 logger.debug(f"\tAdd silence at the beginning of the episode: {loop_count}")

        #         else:
        #             # Add loop_and_fadeout to precedemment up to end of audio
        #             # fr: ep no. 6, 7, 8

        #             loop_count = video_silence
        #             loop_start = (
        #                 p_last_scene['start']
        #                 + p_last_scene['count'] - 1
        #             )
        #             p_last_scene['effects'] = Effects([
        #                 Effect(
        #                     name='loop_and_fadeout',
        #                     frame_ref=loop_start,
        #                     loop=loop_count,
        #                     fade=loop_count
        #                 )
        #             ])
        #             p_target_video['count'] += loop_count

        #             logger.debug(purple(f"loop_count: {loop_count}"))

        #             # # If the amount of added frames were not enough
        #             # if loop_count < video_silence:
        #             #     # Add silence at the beginning of the episode or fade_in
        #             #     loop_count = video_silence - loop_count
        #             #     nested_dict_set(db_video['episode'], loop_count, 'effects', 'loop_and_fadein')
        #             #     db_video_target['episode']['count'] += loop_count


        #             logger.debug(yellow("warning: silence is not enough"))

        #             # sys.exit()


        #     else:
        #         logger.debug(f"\tTODO: episode: loop and fadein")
        #         sys.exit()

        # # No need to add/remove video silences
        # else:
        #     # No modifications
        #     # fr: ep no. 2
        #     # validated (2023-08-25): 02
        #     logger.debug(lightgreen(f"precedemment to episode: no modification"))


        # if avsync_episode > 0:
        #     logger.debug(f"\tepisode: remove {abs(avsync_episode)} frames")
        #     # !!! ep13: ok to remove from 1st scene
        #     first_scene_episode['start'] += avsync_episode
        #     first_scene_episode['count'] -= avsync_episode
        #     first_scene_episode['dst']['count'] -= avsync_episode
        #     tvideo_track['episode']['count'] -= avsync_episode
        # elif avsync_episode < 0:
        #     sys.exit(f"TODO: avsync: {avsync_episode}, add frames/scenes")
        # # if db_video['episode']['start'] != db_video['episode']['scenes'][0]['start']:
        # #     sys.exit("calculate_av_sync: error: start of episode (%d) != start of 1st scene (%d)" % (
        # #         db_video['episode']['start'], db_video[k_chapter]['scenes'][0]['start']))

    else:
        # precedemment does not exist
        tvideo_track['precedemment'].update({
            'avsync': 0,
            'count': 0,
        })

        # episode
        k_ch = 'episode'

        # Get the start frame no. from the src ed.
        k_ed_src = audio_track['src']['k_ed']
        video_start = episode['video'][k_ed_src][k_ch]['start']

        avsync_ms = audio_track[k_ch]['start'] - frame_to_ms(video_start, fps)
        # db_video[k_chapter].update({
        #     'avsync': ms_to_frame(abs(avsync_ms), fps) if avsync_ms < 0 else 0
        # })
        if avsync_ms > 0:
            db_target_video[k_ch]['avsync'] = 0
            audio_track[k_ch]['avsync'] = abs(avsync_ms)
        else:
            # missing video frames, use fade_in
            loop_count = ms_to_frame(abs(avsync_ms), fps)
            nested_dict_set(db_target_video[k_ch], loop_count, 'effects', 'loop_and_fadein')
            db_target_video[k_ch]['count'] += loop_count

        logger.debug(lightgrey(f"\tcalculate_av_sync: avsync_ms: {avsync_ms}"))

    k_ch = 'asuivre'
    if k_ch in audio_track and audio_track[k_ch]['duration'] != 0:
        # g_asuivre
        k_chapter_g = 'g_asuivre'
        audio_count = ms_to_frame(audio_track[k_chapter_g]['duration'], fps)
        db_target_video[k_chapter_g].update({
            'start': 0,
            # 'count': audio_count,
            'avsync': 0,
        })

        audio_track[k_chapter_g].update({
            'avsync': 0,
            'count': ms_to_frame(audio_track[k_chapter_g]['end'] - audio_track[k_chapter_g]['start'], fps)
        })

        # asuivre
        db_target_video[k_ch]['avsync'] = 0
        audio_count = ms_to_frame(audio_track[k_ch]['duration'], fps)
        audio_track[k_ch].update({
            'avsync': 0,
            'count': audio_count
        })
    else:
        tvideo_track['g_asuivre'].update({
            'avsync': 0,
            'count': 0,
        })
        tvideo_track[k_ch].update({
            'avsync': 0,
            'count': 0,
        })

        audio_track['g_asuivre'].update({
            'avsync': 0,
            'count': 0,
        })
        audio_track[k_ch].update({
            'avsync': 0,
            'count': 0,
        })

    # g_documentaire
    k_chapter_g = 'g_documentaire'
    audio_count = ms_to_frame(audio_track[k_chapter_g]['duration'], fps)
    audio_track[k_chapter_g].update({
        'count': audio_count,
        'avsync': 0
    })
    db_target_video[k_chapter_g].update({
        'start': 0,
        # 'count': audio_count,
        'avsync': 0
    })

    # documentaire
    k_ch = 'documentaire'
    db_target_video[k_ch]['avsync'] = 0
    audio_track[k_ch].update({
        'avsync': 0,
        # 'count': ms_to_frame(db_audio[k_chapter]['duration'], fps)
    })

    # TODO remove the above modification of frames count once frame count is validate
    # Recalculte video count
    for k_ch in main_chapter_keys():
        logger.debug(f"\t{k_ch}: count={db_target_video[k_ch]['count']}")

