from __future__ import annotations
import sys
from pprint import pprint
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
from utils.mco_types import Effect, Effects, Scene
from ._db import db



def consolidate_av_sync(k_ep):
    episode = db[k_ep]
    fps = get_fps(db)
    logger.debug(lightgreen(f"consolidate_av_sync"))


    if ('audio' not in episode or 'video' not in episode):
        sys.exit("calculate_av_sync: error, audio or video does not exist in %s:common" % (__name__, k_ep))
        return
    db_video = episode['video']['target']
    video_track = episode['video']['target']
    audio_track: dict = episode['audio']




    # precedemment
    k_chapter = 'precedemment'
    audio_track['precedemment']['avsync'] = 0
    audio_track['episode']['avsync'] = 0
    video_track['precedemment']['avsync'] = 0
    video_track['episode']['avsync'] = 0

    if k_chapter in audio_track and audio_track[k_chapter]['duration'] != 0:
        # edition used as the src for the audio track

        k_ed_audio_src = audio_track['src']['k_ed']
        # if verbose:
        #     print(lightcyan(f"db_audio[{k_chapter}]:"))
        #     pprint(db_audio[k_chapter])
        #     print(lightcyan(f"db_video {k_ed_src}:{k_chapter}:"))
        #     pprint(episode['video'][k_ed_src][k_chapter])
        #     print(lightcyan(f"db_video target:{k_chapter}:"))
        #     pprint(episode['video']['target'][k_chapter])

        # Compare video count from audio_src and target

        try:
            precedemment_video_count = (episode['video'][k_ed_audio_src]['episode']['scenes'][1]['start']
                            - episode['video'][k_ed_audio_src]['precedemment']['scenes'][1]['start'])
            precedemment_target_video_count = (video_track['episode']['scenes'][1]['start']
                            - video_track['precedemment']['scenes'][1]['start'])
        except:
            pprint(episode['video'].keys())
            sys.exit(f"{k_ep}:{k_chapter}: video scenes are not defined. They are required to calculate AV sync values.")
        logger.debug(lightgrey(f"\tprecedemment to episode:"))
        logger.debug(lightgrey(f"\t\tvideo count ({k_ed_audio_src}): {precedemment_video_count}"))
        logger.debug(lightgrey(f"\t\tvideo count (target): {precedemment_target_video_count}"))
        if precedemment_video_count != precedemment_target_video_count:
            logger.info(yellow(f"[W] precedemment to episode: erroneous frame count between {k_ed_audio_src} and target"))


        # Ensure episode durations are the same
        episode_src_count = (episode['video'][k_ed_audio_src]['episode']['scenes'][-1]['start']
            - episode['video'][k_ed_audio_src]['episode']['scenes'][1]['start'])

        episode_target_count = 0
        for scene in video_track['episode']['scenes'][1:-1]:
            episode_target_count += scene['dst']['count']

        avsync_episode = 0
        if episode_src_count != episode_target_count:
            # ep: 2, 13, 22
            print(red(f"\twarning: target vs source: erroneous frame count:"),
                    f"target: {episode_target_count}, src ({k_ed_audio_src}): {episode_src_count}")
            # sys.exit()
            avsync_episode = episode_target_count - episode_src_count


        # synchronize episode, use the 2nd video scene

        # offset: target -> src (use audio track)
        # offset = src - target
        offset_src_to_target = (video_track['episode']['scenes'][1]['start']
            - episode['video'][k_ed_audio_src]['episode']['scenes'][1]['start'])

        # audio start in target referentiel
        precedemment_audio_start = ms_to_frame(audio_track['precedemment']['start'], fps) + offset_src_to_target

        # Precedemment: let's set the 1st frame of video aligned with the audio start
        video_track['precedemment']['avsync'] = 0

        # We moved the precedemment part, calculate new silence between precedemment and episode
        precedemment_video_count = video_track['precedemment']['count']
        episode_video_start = video_track['episode']['scenes'][0]['start']
        video_silence = (episode_video_start
            - (precedemment_audio_start + precedemment_video_count))

        precedemment_audio_count = ms_to_frame(audio_track['precedemment']['duration'], fps)

        logger.debug(f"k_ed_audio_src: {k_ed_audio_src}")
        logger.debug(f"\toffset: {offset_src_to_target}")
        logger.debug(f"\tprecedemment_audio_start: {precedemment_audio_start}")
        logger.debug(f"\tprecedemment_video_count: {precedemment_video_count}")
        logger.debug(f"\tepisode_video_start: {episode_video_start}")
        logger.debug(f"\tprecedemment, audio_count: {precedemment_audio_count}")
        logger.debug(f"\tvideo_silence: {video_silence}")

        last_scene_precedemment: Scene = video_track['precedemment']['scenes'][-1]
        first_scene_episode: Scene = video_track['episode']['scenes'][0]
        logger.debug(f"\tlast_scene_precedemment: end: {last_scene_precedemment['start'] + last_scene_precedemment['dst']['count']}")
        logger.debug(f"\tfirst_scene_episode: start: {first_scene_episode['start']}")

        if video_silence < 0:
            # overlap
            logger.debug(lightgreen(f"precedemment to episode: remove {abs(video_silence)} frames"))
            video_silence = abs(video_silence)

            if precedemment_audio_count > precedemment_video_count:
                # Remove frames from episode
                # fr: ep no. 19
                # fadein to do
                # ep26 (99 frames)?????
                # validated (2023-08-28): 19
                logger.debug(f"\tepisode: remove {abs(video_silence)} frames")
                first_scene_episode['start'] += video_silence
                first_scene_episode['count'] -= video_silence
                first_scene_episode['dst']['count'] -= video_silence
                video_track['episode']['count'] -= video_silence
            else:
                # Remove frames from precedemment
                # fr: ep no. 14, 36
                # validated (2023-08-26): 14, 36
                # TODO: Improve: ep14, use fadeout
                # validated (2023-09-07): 3,
                logger.debug(f"\tprecedemment: remove {abs(video_silence)} frames")
                last_scene_precedemment['count'] -= video_silence
                last_scene_precedemment['dst']['count'] -= video_silence
                video_track['precedemment']['count'] -= video_silence

        elif video_silence > 0:
            # Add silence between precedemment and episode
            logger.debug(lightgreen(f"precedemment to episode: add video silence: {abs(video_silence)} frames"))

            if precedemment_audio_count > precedemment_video_count:
                # fr: ep no. 6, 7, 8, 9, 10, 11, 12, 13, 15, 16, 17, 18,
                #               20, 21, 22, 23, 24, 25, 26, 27, 28, 29,
                #               30, 31, 32, 34, 35, 37, 38, 39
                # validated (2023-09-07): 4, 5,
                logger.debug(f"\tprecedemment: loop and fadeout")
                av_diff = precedemment_audio_count - precedemment_video_count

                logger.debug(f"\tav_diff : {precedemment_audio_count - precedemment_video_count}")
                if av_diff <= video_silence:
                    logger.debug(purple("no need to revalidate"))

                    # Add loop_and_fadeout to precedemment up to end of audio
                    loop_count = precedemment_audio_count - precedemment_video_count
                    loop_start = (
                        last_scene_precedemment['start']
                        + last_scene_precedemment['count'] - 1
                    )
                    last_scene_precedemment['effects'] = Effects([
                        Effect(
                            name='loop_and_fadeout',
                            frame_ref=loop_start,
                            loop=loop_count,
                            fade=loop_count
                        )
                    ])
                    video_track['precedemment']['count'] += loop_count

                    # If the amount of added frames were not enough
                    if loop_count < video_silence:
                        # Add silence at the beginning of the episode or fade_in
                        loop_count = video_silence - loop_count
                        db_video['episode']['effects'] = Effects([
                            Effect(
                                name='loop_and_fadein',
                                loop=loop_count,
                                fade=0,
                            )
                        ])
                        video_track['episode']['count'] += loop_count
                        logger.debug(f"\tAdd silence at the beginning of the episode: {loop_count}")
                else:
                    # Add loop_and_fadeout to precedemment up to end of audio
                    # fr: ep no. 6, 7, 8

                    loop_count = video_silence
                    loop_start = (
                        last_scene_precedemment['start']
                        + last_scene_precedemment['count'] - 1
                    )
                    last_scene_precedemment['effects'] = Effects([
                        Effect(
                            name='loop_and_fadeout',
                            frame_ref=loop_start,
                            loop=loop_count,
                            fade=loop_count
                        )
                    ])
                    video_track['precedemment']['count'] += loop_count

                    logger.debug(purple(f"loop_count: {loop_count}"))

                    # # If the amount of added frames were not enough
                    # if loop_count < video_silence:
                    #     # Add silence at the beginning of the episode or fade_in
                    #     loop_count = video_silence - loop_count
                    #     nested_dict_set(db_video['episode'], loop_count, 'effects', 'loop_and_fadein')
                    #     db_video_target['episode']['count'] += loop_count


                    logger.debug(yellow("warning: silence is not enough"))

                    # sys.exit()


            else:
                logger.debug(f"\tTODO: episode: loop and fadein")
                sys.exit()

        else:
            # No modifications
            # fr: ep no. 2
            # validated (2023-08-25): 02
            logger.debug(lightgreen(f"precedemment to episode: no modification"))


        if avsync_episode > 0:
            logger.debug(f"\tepisode: remove {abs(avsync_episode)} frames")
            # !!! ep13: ok to remove from 1st scene
            first_scene_episode['start'] += avsync_episode
            first_scene_episode['count'] -= avsync_episode
            first_scene_episode['dst']['count'] -= avsync_episode
            video_track['episode']['count'] -= avsync_episode
        elif avsync_episode < 0:
            sys.exit(f"TODO: avsync: {avsync_episode}, add frames/scenes")
        # if db_video['episode']['start'] != db_video['episode']['scenes'][0]['start']:
        #     sys.exit("calculate_av_sync: error: start of episode (%d) != start of 1st scene (%d)" % (
        #         db_video['episode']['start'], db_video[k_chapter]['scenes'][0]['start']))

    else:
        # precedemment does not exist
        audio_track['precedemment']['avsync'] = 0
        video_track['precedemment'].update({
            'avsync': 0,
            'count': 0,
        })

        # episode
        k_chapter = 'episode'

        # Get the start frame no. from the src ed.
        k_ed_src = audio_track['src']['k_ed']
        video_start = episode['video'][k_ed_src][k_chapter]['start']

        avsync_ms = audio_track[k_chapter]['start'] - frame_to_ms(video_start, fps)
        # db_video[k_chapter].update({
        #     'avsync': ms_to_frame(abs(avsync_ms), fps) if avsync_ms < 0 else 0
        # })
        if avsync_ms > 0:
            db_video[k_chapter]['avsync'] = 0
            audio_track[k_chapter]['avsync'] = abs(avsync_ms)
        else:
            # missing video frames, use fade_in
            loop_count = ms_to_frame(abs(avsync_ms), fps)
            nested_dict_set(db_video[k_chapter], loop_count, 'effects', 'loop_and_fadein')
            db_video[k_chapter]['count'] += loop_count

        logger.debug(lightgrey(f"\tcalculate_av_sync: avsync_ms: {avsync_ms}"))

    k_chapter = 'asuivre'
    if k_chapter in audio_track and audio_track[k_chapter]['duration'] != 0:
        # g_asuivre
        k_chapter_g = 'g_asuivre'
        audio_count = ms_to_frame(audio_track[k_chapter_g]['duration'], fps)
        db_video[k_chapter_g].update({
            'start': 0,
            # 'count': audio_count,
            'avsync': 0,
        })

        audio_track[k_chapter_g].update({
            'avsync': 0,
            'count': ms_to_frame(audio_track[k_chapter_g]['end'] - audio_track[k_chapter_g]['start'], fps)
        })

        # asuivre
        db_video[k_chapter]['avsync'] = 0
        audio_count = ms_to_frame(audio_track[k_chapter]['duration'], fps)
        audio_track[k_chapter].update({
            'avsync': 0,
            'count': audio_count
        })
    else:
        video_track['g_asuivre'].update({
            'avsync': 0,
            'count': 0,
        })
        video_track[k_chapter].update({
            'avsync': 0,
            'count': 0,
        })

        audio_track['g_asuivre'].update({
            'avsync': 0,
            'count': 0,
        })
        audio_track[k_chapter].update({
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
    db_video[k_chapter_g].update({
        'start': 0,
        # 'count': audio_count,
        'avsync': 0
    })

    # documentaire
    k_chapter = 'documentaire'
    db_video[k_chapter]['avsync'] = 0
    audio_track[k_chapter].update({
        'avsync': 0,
        # 'count': ms_to_frame(db_audio[k_chapter]['duration'], fps)
    })

    # TODO remove the above modification of frames count once frame count is validate
    # Recalculte video count
    for k_chapter in main_chapter_keys():
        logger.debug(f"\t{k_chapter}: count={db_video[k_chapter]['count']}")

