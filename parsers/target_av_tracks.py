import sys
from pprint import pprint

from parsers.video_target import get_video_chapter_frame_count
from .helpers import get_fps, nested_dict_set
from .logger import logger
from utils.p_print import *
from utils.time_conversions import (
    frame_to_ms,
    ms_to_frame,
)
from utils.mco_types import Effect, Effects, Scene, VideoChapter
from ._db import db



def consolidate_av_tracks(k_ep, k_chapter: str = '') -> None:
    if k_chapter in ('g_debut', 'g_fin'):
        _consolidate_av_tracks_g_debut_end(db, k_ep, k_chapter_c=k_chapter)
        return

    fps = get_fps(db)

    logger.debug(lightgreen(f"consolidate_av_tracks: {k_ep}"))
    K_EP_DEBUG, K_CHAPTER_DEBUG = [''] *2
    # K_EP_DEBUG = 'ep05'
    # K_CHAPTER_DEBUG = 'precedemment'
    try:
        db_video = db[k_ep]['video']['target']
        db_audio = db[k_ep]['audio']
    except:
        sys.exit(f"consolidate_av_tracks: error, audio or video does not exist in {k_ep}:common")


    # g_asuivre
    #---------------------------------------------------------------------------
    if db_video['asuivre']['count'] != 0:
        # Update the scene with the duration that is calculated in the audio structure
        k_chapter_c = 'g_asuivre'
        db_video[k_chapter_c]['count'] = db_audio[k_chapter_c]['count']
        last_scene: Scene = db_video[k_chapter_c]['scenes'][-1]
        last_scene['effects'] = Effects([
            Effect(
                name='loop',
                frame_ref=last_scene['start'] + last_scene['count'] - 1,
                loop=db_video[k_chapter_c]['count'] - last_scene['count']
            )
        ])
        if k_ep == K_EP_DEBUG:
            print(f"\ndb_video: %s:\n--------------------------------------" % (k_chapter_c))
            pprint(db_video[k_chapter_c])


    # g_documentaire
    #---------------------------------------------------------------------------
    # Update the scene with the duration that is calculated in the audio structure
    k_chapter_c = 'g_documentaire'

    last_scene = db_video[k_chapter_c]['scenes'][-1]
    if db_audio[k_chapter_c]['count'] > db_video[k_chapter_c]['count']:
        # Use last frame
        loop_start = last_scene['start'] + last_scene['count'] - 1
        loop_count = db_audio[k_chapter_c]['count'] - db_video[k_chapter_c]['count']
        logger.debug(f"{k_chapter_c}: loop, last frame={loop_start}, {loop_count} frames")
        last_scene['effects'] = Effects([
            Effect(
                name='loop',
                frame_ref=loop_start,
                loop=loop_count
            )
        ])

    elif db_video[k_chapter_c]['count'] > db_audio[k_chapter_c]['count']:
        # remove some frames
        logger.debug(f"{k_chapter_c}: remove {db_video[k_chapter_c]['count']- db_audio[k_chapter_c]['count']} frames")
        last_scene['count'] -= db_video[k_chapter_c]['count'] - db_audio[k_chapter_c]['count']
        last_scene['dst']['count'] = last_scene['count']

    db_video[k_chapter_c]['count'] = db_audio[k_chapter_c]['count']
    if k_ep == K_EP_DEBUG:
        logger.debug(f"\ndb_video: %s:\n--------------------------------------" % (k_chapter_c))
        pprint(db_video[k_chapter_c])


    # asuivre, documentaire
    #---------------------------------------------------------------------------
    for k_chapter in ['precedemment', 'episode', 'asuivre', 'documentaire']:
        if k_ep == K_EP_DEBUG and k_chapter == K_CHAPTER_DEBUG:
            logger.debug(f"\ndb_video: %s:\n--------------------------------------" % (k_chapter))
            pprint(db_video[k_chapter])

        # Calculate audio duration
        audio_duration = db_audio[k_chapter]['avsync'] + db_audio[k_chapter]['duration']

        if k_chapter == 'episode':
            # Add precedemment
            audio_duration = (
                db_audio['precedemment']['avsync']
                + db_audio['precedemment']['duration']
                + db_audio['episode']['duration']
            )

        # Round audio count to a multiple of 1000/fps ms
        audio_count = ms_to_frame(audio_duration, fps)
        audio_count_rounded = float(int((audio_duration * fps / 1000) + 0.5))
        audio_count_float = (audio_duration * fps / 1000)
        # print(f"%s:" % (k_chapter))
        # print(f"\taudio_count_rounded=%f" % (audio_count_rounded))
        # print(f"\taudio_count_float=%f" % (audio_count_float))
        if audio_count_float != audio_count_rounded:
            sys.exit(f"consolidate_av_tracks: correct or remove this (add an audio segment), {k_ep}:{k_chapter}")
            # Add silence to the latest segment
            s = db_audio[k_chapter]['segments'][-1]
            silence = int(((audio_count_rounded - audio_count_float) * 1000 / fps) + 0.5)
            if 'segments' in s.keys():
                s['silence'] += silence
            else:
                s['silence'] = silence

            if k_chapter == 'episode':
                db_audio[k_chapter]['duration'] = int(audio_count_rounded * 1000 / fps) - db_audio['precedemment']['duration']
            else:
                db_audio[k_chapter]['duration'] = int(audio_count_rounded * 1000 / fps)
            audio_count = audio_count_rounded
            print ("%s.consolidate_av_tracks: %s:%s: add a silence to round the audio duration: %d" % (__name__, k_ep, k_chapter, silence))

        # Modify the real audio count to this new duration
        if k_chapter == 'episode':
            # this is a special case for episode: precedemment+episode
            # print(f"   rounded audio count episode+precedemment: %d" % (audio_count))

            # print(f"episode: consolidate_av_tracks:")
            # print(f"\tvideo avsync: {db_video['episode']['avsync']}")
            # print(f"\taudio avsync: {db_audio['episode']['avsync']}")

            db_audio['episode']['count'] = audio_count - db_audio['precedemment']['count']
            video_count: int = (
                db_video['precedemment']['avsync']
                + db_video['precedemment']['count']
                + db_video['episode']['avsync'] + db_video['episode']['count']
            )


            # db_video[k_chapter]['count'] += db_video[k_chapter]['avsync']
        else:
            logger.debug(lightcyan(f"{k_chapter}"))
            db_audio[k_chapter]['count'] = audio_count
            video_count = db_video[k_chapter]['count'] + db_video[k_chapter]['avsync']
            logger.debug(f"\taudio: {db_audio[k_chapter]['count']}")
            logger.debug(f"\tvideo: {video_count}")

        # Add loop_and_fade_in
        try:
            effects: Effects = db_video[k_chapter]['scenes'][0]['effects']
            video_count += effects.primary_effect().loop
        except:
            pass


        # Append added duration to audio track
        audio_count += ms_to_frame(db_audio[k_chapter]['avsync'], fps)

        if k_chapter == 'precedemment':
            continue
        # video_count = db_video[k_chapter]['count']

        # logger.debug(f"info: %s:consolidate_av_tracks: %s:%s: video=%d, audio=%d" % (__name__, k_ep, k_chapter, video_count, audio_count))
        try:
            last_scene: Scene = db_video[k_chapter]['scenes'][-1]
        except:
            continue

        if audio_count > video_count:
            # Frames shall be added: use the loop (and fadeout) effect for this
            logger.debug(
                lightgrey(f"\t{k_ep}:{k_chapter}: ")
                + f"video({video_count}) < audio ({audio_count}): add video frames, "
            )

            frame_no = last_scene['start'] + last_scene['count'] - 1
            loop_count = audio_count - video_count
            if 'src' in last_scene.keys():
                if last_scene['src']['k_ep'] != k_ep:
                    frame_no = last_scene['src']['start'] + last_scene['src']['count'] - 1

                last_scene['effects'] = Effects([
                    Effect(
                        name='loop_and_fadeout',
                        frame_ref=frame_no,
                        loop=loop_count,
                        fade=min(loop_count, 25)
                    )
                ])
                # last_scene['src']['count'] -= loop_count

            db_video[k_chapter]['count'] += loop_count

        elif audio_count < video_count:
            # Add silence to the audio track by adding a new segment
            logger.debug(
                lightgrey(f"{k_ep}:{k_chapter}: ")
                +  f"video({video_count}) > audio ({audio_count})"
            )
            if True:
                logger.debug(yellow("warning: this has been patched (now, remove video frames) for documentaire, verify elsewhere"))
                last_scene:Scene = db_video[k_chapter]['scenes'][-1]
                last_scene['count'] -= video_count - audio_count
                db_video[k_chapter]['count'] = db_audio[k_chapter]['count']
                last_scene['dst']['count'] = last_scene['count']
            else:
                video_duration = int(video_count * 1000 / fps)
                audio_duration = db_audio[k_chapter]['duration']
                db_audio[k_chapter]['segments'].append({
                    'start': 0,
                    'end': 0,
                    'silence': video_duration - audio_duration,
                })
            db_audio[k_chapter]['count'] = db_video[k_chapter]['count']
            # print(f"-> added silence at the end")

        if k_ep == K_EP_DEBUG and k_chapter == K_CHAPTER_DEBUG:
            logger.debug(f"\ndb_video: {k_chapter}:\n--------------------------------------")
            pprint(db_video[k_chapter])


    # Add/modify effect of the first/last scene
    #---------------------------------------------------------------------------
    for k_chapter in ['episode', 'asuivre', 'documentaire']:
        video: VideoChapter = db_video[k_chapter]
        if video['count'] < 1:
            continue
        first_scene: Scene = video['scenes'][0]
        last_scene: Scene = video['scenes'][-1]

        if 'effects' in video:
            logger.debug(green(f"Effects detected in {k_ep}:{k_chapter}"))
            print("====================================================")
            pprint(video['effects'])
            for effect in video['effects']:
            # effect: Effect = video['effects'].primary_effect()

                if effect.name == 'loop_and_fadein':
                    raise RuntimeError("TODO to be corrected asap")
                    fadein_count = video['effects'].primary_effect()
                    logger.debug(f"\t{k_ep}:{k_chapter}, patch the first scene -> fadein: add effects")
                    # pprint(video)
                    # first_scene['src']['start'] += fadein_count
                    # first_scene['src']['count'] -= fadein_count

                    first_scene['effects'] = Effects([
                        Effect(
                            name='loop_and_fadein',
                            frame_ref=0,
                            loop=fadein_count,
                            fade=fadein_count
                        )
                    ])
                    # logger.debug(first_scene)
                    # sys.exit()

                if 'fadeout' in effect.name and effect.fade > 0:
                    logger.debug(yellow(f"\t{k_ep}:{k_chapter} modify fadeout effect in db_video!"))

                    fadeout_count = effect.fade
                    if 'effects' in last_scene:
                        effect: Effect = last_scene['effects'].primary_effect()
                        # Patch the fadeout/loop_and_fadeout duration
                        if effect.name == 'fadeout':
                            logger.debug(f"\t{k_ep}:{k_chapter}, patch the last scene -> fadeout: modify")
                            effect.fade = fadeout_count

                        elif effect.name == 'loop_and_fadeout':
                            logger.debug(f"\t{k_ep}:{k_chapter}, patch the last scene -> loop_and_fadeout: modify")
                            logger.debug(f"\t%d vs %d" % (effect.fade, fadeout_count))
                            # pprint(last_scene)

                            last_scene_count = (last_scene['count'] + effect.loop)
                            if fadeout_count > last_scene_count:
                                # Modify it because scene duration > fadeout duration
                                effect.fade = last_scene_count
                            else:
                                effect.fade = fadeout_count

                            # logger.debug(f"-> {last_scene}")

                    else:
                        # Patch the last scene, add 'fadeout' effect
                        logger.debug(f"\tconsolidate_av_tracks: {k_ep}:{k_chapter}, patch the last scene -> fadeout: add effects")
                        # pprint(video)
                        frame_no = last_scene['start'] + last_scene['count'] - 1
                        frame_loop_start = frame_no - fadeout_count + 1
                        last_scene['effects'] = Effects([
                            Effect(
                                name='fadeout',
                                frame_ref=frame_loop_start,
                                fade=fadeout_count
                            )
                        ])







def _consolidate_av_tracks_g_debut_end(db, k_ep, k_chapter_c):
    """This function compares the audio and video tracks of a generique
    It aligns these 2 durations by:
    - adding silences
    - adding frames (loop, loop and fadeout)
    """
    logger.debug(lightgreen(f"consolidate_av_tracks_g_debut_end: {k_chapter_c}"))
    fps = get_fps(db)
    if k_chapter_c not in ('g_debut', 'g_fin'):
        return

    # video and audio tracks
    db_video = db[k_chapter_c]['video']
    db_audio = db[k_chapter_c]['audio']

    # Get nb of frames for the video track
    video_count: int = get_video_chapter_frame_count(k_ep=k_ep, k_ch=k_chapter_c)

    # Align video track to a multiple of seconds
    db_video['count'] = int(fps * int(1 + db_video['count'] / fps))
    if video_count != db_video['count']:
        db_video['silence'] = db_video['count'] - video_count

    # Get the duration in ms
    audio_duration = db_audio['duration']
    if 'avsync' in db_audio:
        audio_duration += db_audio['avsync']
    if 'silence' in db_audio:
        audio_duration += db_audio['silence']
    print(f"audio duration: {audio_duration/1000:.03f}s")
    print(f"audio count: {ms_to_frame(audio_duration, fps)}")

    # Align audio track to a multiple of seconds
    rounded_audio_duration = 1000 * int(1 + float(audio_duration)/1000)
    audio_count = ms_to_frame(rounded_audio_duration, fps)
    # print(f"rounded audio count: %d" % (audio_count))
    if frame_to_ms(audio_count, fps) != audio_duration:
        db_audio['segments'].append({
            'start': 0,
            'end': 0,
            'silence': frame_to_ms(audio_count, fps) - audio_duration
        })

    # Update audio duration and nb of frames
    db_audio['count'] = audio_count
    db_audio['duration'] = frame_to_ms(audio_count, fps)


    print(f"----------------- Consolidate A/V tracks ------------------")
    print(f"chapter: {k_chapter_c}")
    print(f"  - audio_count: {db_audio['count']}")
    print(f"  - audio_duration: {db_audio['duration']}")
    print(f"  - video_count : {video_count}")
    print(f"  - video_count (rounded): {db_video['count']}")

    # Align audio and video duration
    scenes: list[Scene] = db_video['scenes']
    video_count = db_video['count']
    if audio_count > video_count:
        # Frames shall be added: use the loop effect for this
        last_scene: Scene = scenes[-1]
        frame_no = last_scene['start'] + last_scene['count'] - 1
        print(f"[I] consolidate_av_tracks: {k_chapter_c}: add video frames, video({video_count}) < audio ({audio_count})")
        loop_count = audio_count - video_count
        last_scene['effects'] = Effects([
            Effect(
                name='loop_and_fadeout',
                frame_ref=frame_no,
                loop=loop_count,
                fade=min(loop_count, 25)
            )
        ])
        db_video['count'] += loop_count

    elif video_count > audio_count:
        # Add silence to the audio track by adding a new segment
        print(f"[I] consolidate_av_tracks: {k_chapter_c}: add audio silence, video({video_count}) > audio ({audio_count})")
        video_duration = frame_to_ms(video_count, fps)
        audio_duration = db_audio['duration']
        silence_duration = video_duration - audio_duration
        db_audio['segments'].append({
            'start': 0,
            'end': 0,
            'silence': silence_duration,
        })
        db_audio['count'] = db_video['count']
        db_audio['duration'] += silence_duration

    # elif video_count == audio_count:
    #     print(f"info: consolidate_av_tracks: %s: video(%d) = audio (%d)" % (k_chapter_c, video_count, audio_count))




