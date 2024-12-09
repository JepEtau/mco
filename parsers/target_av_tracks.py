from __future__ import annotations
import sys
from pprint import pprint
import warnings


from parsers._keys import main_chapter_keys
from parsers.video_target import get_video_chapter_frame_count
from .helpers import get_fps, nested_dict_set
from .logger import logger
from utils.p_print import *
from utils.time_conversions import (
    FrameRate,
    frame_to_ms,
    ms_to_frame,
)
from utils.mco_types import ChapterAudio, Effect, Effects, Scene, ChapterVideo
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

    # !!!! FR language only

    # precedemment
    #---------------------------------------------------------------------------
    k_ch = 'precedemment'
    ch_audio: ChapterAudio = db_audio[k_ch]
    ch_video: ChapterVideo = db_video[k_ch]
    if ch_audio['duration']:
        audio_count = check_audio_duration_multiple_of_frames(ch_audio)
        ch_audio['count'] = audio_count
        video_count = ch_video['count']

        if video_count > audio_count:
            raise ValueError(red(f"{k_ep}:{k_ch} too many frames"))

        elif audio_count > video_count:
            add_loop_and_fadeout_effect(ch_video, ch_audio, k_ep, k_ch)

        else:
            consolidate_last_scene_effect(ch_video, k_ep, k_ch)


    # episode
    #---------------------------------------------------------------------------
    k_ch = 'episode'
    ch_audio: ChapterAudio = db_audio[k_ch]
    ch_video: ChapterVideo = db_video[k_ch]
    audio_count = check_audio_duration_multiple_of_frames(ch_audio)
    ch_audio['count'] = audio_count
    video_count = ch_video['count']

    k_ed_audio_src = db_audio['src']['k_ed']
    print(f"k_ed_audio_src: {k_ed_audio_src}")

    # First scene
    e_s0_vcount: int = ch_video['scenes'][0]['src'].frame_count()
    e_s0_acount: int = (
        db[k_ep]['video'][k_ed_audio_src]['episode']['scenes'][1]['start']
        - ms_to_frame(ch_audio['start'], fps)
    )
    print(f"Target: episode, 1st scene video count: {e_s0_vcount}, must be {e_s0_acount}")

    if e_s0_vcount > e_s0_acount:
        # Too many frames, add silence only for episode 1 (no precedemment)
        pprint(ch_audio)
        raise ValueError(f"{k_ep}:{k_ch} scene 0 is too long ({e_s0_vcount} > {e_s0_acount})")
        # TODO: cut and fadein

    elif e_s0_vcount < e_s0_acount:
        loop_count = e_s0_acount - e_s0_vcount
        # minimum between diff and 2.5s
        fade = min(loop_count, int(2.5 * fps))
        if 'effects' not in ch_video:
            print(red("TODO: add default effects in chapter"))
            raise
            ch_video['effects'] = Effects()
        ch_video['effects'].append(
            Effect(
                name='loop_and_fadein',
                loop=loop_count,
                fade=fade,
            )
        )
        video_count += loop_count
        logger.debug(f"Fade in and loop at the beginning of the episode: {loop_count}, fade={fade}")

    # Last scene
    if video_count > audio_count:
        raise ValueError(red(f"{k_ep}:{k_ch} too many frames"))

    elif audio_count > video_count:
        add_loop_and_fadeout_effect(ch_video, ch_audio, k_ep, k_ch)

    else:
        consolidate_last_scene_effect(ch_video, k_ep, k_ch)


    # g_asuivre
    #---------------------------------------------------------------------------
    if db_video['asuivre']['count']:
        k_ch = 'g_asuivre'
        ch_audio: ChapterAudio = db_audio[k_ch]
        ch_video: ChapterVideo = db_video[k_ch]

        ch_video['count'] = ch_audio['count']
        last_scene: Scene = ch_video['scenes'][-1]
        last_scene['effects'] = Effects([
            Effect(
                name='loop',
                frame_ref=last_scene['src'].last_frame_no(),
                loop=ch_video['count'] - last_scene['dst']['count']
            )
        ])
        if k_ep == K_EP_DEBUG:
            print(f"\ndb_video: %s:\n--------------------------------------" % (k_ch))
            pprint(ch_video)


    # asuivre
    #---------------------------------------------------------------------------
    k_ch = 'asuivre'
    ch_audio: ChapterAudio = db_audio[k_ch]
    ch_video: ChapterVideo = db_video[k_ch]
    audio_count = check_audio_duration_multiple_of_frames(ch_audio)
    ch_audio['count'] = audio_count

    if audio_count > video_count:
        add_loop_and_fadeout_effect(ch_video, ch_audio, k_ep, k_ch)

    elif video_count > audio_count:
        raise ValueError(red(f"{k_ep}:{k_ch} too many frames"))

    else:
        consolidate_last_scene_effect(ch_video, k_ep, k_ch)


    # g_documentaire
    #---------------------------------------------------------------------------
    k_ch = 'g_documentaire'
    ch_audio: ChapterAudio = db_audio[k_ch]
    ch_video: ChapterVideo = db_video[k_ch]

    ch_audio['count'] = ms_to_frame(ch_audio['duration'], fps)
    last_scene = ch_video['scenes'][-1]

    if ch_audio['count'] > ch_video['count']:
        # Use last frame to loop
        loop_start = last_scene['src'].last_frame_no()
        loop_count = ch_audio['count'] - ch_video['count']
        logger.debug(f"{k_ch}: loop, last frame={loop_start}, {loop_count} frames")
        last_scene['effects'] = Effects([
            Effect(
                name='loop',
                frame_ref=loop_start,
                loop=loop_count
            )
        ])

    elif ch_video['count'] > ch_audio['count']:
        # Remove some frames
        to_remove: int = ch_video['count'] - ch_audio['count']
        logger.debug(f"{k_ch}: remove {to_remove} frames")
        last_scene['src'].last_scene()['count'] -= to_remove
        last_scene['dst']['count'] = last_scene['src'].last_scene()['count']

    # audio frame count = video frame count
    ch_video['count'] = ch_audio['count']

    if k_ep == K_EP_DEBUG:
        logger.debug(f"\ndb_video: %s:\n--------------------------------------" % (k_ch))
        pprint(ch_video)



    # documentaire
    #---------------------------------------------------------------------------
    k_ch = 'documentaire'
    ch_audio: ChapterAudio = db_audio[k_ch]
    ch_video: ChapterVideo = db_video[k_ch]
    audio_count = check_audio_duration_multiple_of_frames(ch_audio)
    ch_audio['count'] = audio_count

    if audio_count > video_count:
        add_loop_and_fadeout_effect(ch_video, ch_audio, k_ep, k_ch)

    elif video_count > audio_count:
        # Remove frames
        # Patch Source frames: verify that the number of frames to extract is correct
        last_scene: Scene = ch_video['scenes'][-1]
        print(red("patch last scene:"), f"last scene frame count: {last_scene['src'].frame_count()}")
        to_remove: int = video_count - audio_count
        print(f"  to_remove: {to_remove}")
        last_scene['dst']['count'] -= to_remove
        last_scene['src'].last_scene()['count'] -= to_remove
        print(f"-> frame count: {last_scene['src'].frame_count()}")
        ch_video['count'] = ch_audio['count']
        raise ValueError(f"remove frames")

    if video_count == audio_count:
        consolidate_last_scene_effect(ch_video)





    for k_chapter in ['precedemment', 'episode', 'asuivre']:
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
            warnings.warn("%s.consolidate_av_tracks: %s:%s: add a silence to round the audio duration: %d" % (__name__, k_ep, k_chapter, silence))

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
        # try:
        #     effects: Effects = db_video[k_chapter]['scenes'][0]['effects']
        #     video_count += effects.primary_effect().loop
        # except:
        #     pass


        # Append added duration to audio track
        audio_count += ms_to_frame(db_audio[k_chapter]['avsync'], fps)


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

            frame_no = last_scene['src'].last_frame_no()
            loop_count = audio_count - video_count
            last_scene['effects'] = Effects([
                Effect(
                    name='loop_and_fadeout',
                    frame_ref=frame_no,
                    loop=loop_count,
                    fade=min(loop_count, 25)
                )
            ])

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
                last_scene['dst']['count'] -= video_count - audio_count
                db_video[k_chapter]['count'] = db_audio[k_chapter]['count']
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




    frame_rate: FrameRate = get_fps(db)
    for k_ch in main_chapter_keys():
        ch_video = db[k_ep]['video']['target'][k_ch]
        ch_audio = db[k_ep]['audio'][k_ch]

        if ch_audio['silence'] > 0:
            if 'silence' not in ch_video:
                ch_video['silence'] = 0

            ch_video['silence'] += int(
                ms_to_frame(ch_audio['silence'], frame_rate=frame_rate)
            )




def _consolidate_av_tracks_g_debut_end(db, k_ep, k_chapter_c):
    """This function compares the audio and video tracks of a generique
    It aligns these 2 durations by:
    - adding silences
    - adding frames (loop, loop and fadeout)
    """
    print(lightgreen(f"  _consolidate_av_tracks_g_debut_end: {k_chapter_c}"))
    fps = get_fps(db)
    if k_chapter_c not in ('g_debut', 'g_fin'):
        return

    # video and audio tracks
    db_video: ChapterVideo = db[k_chapter_c]['video']
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
    print(f"  audio duration: {audio_duration/1000:.03f}s")
    print(f"  audio count: {ms_to_frame(audio_duration, fps)}")

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


    print(lightcyan(f"----------------- Consolidate A/V tracks ------------------"))
    print(f"chapter: {k_chapter_c}")
    print(f"  - audio_count: {db_audio['count']}")
    print(f"  - audio_duration: {db_audio['duration']}")
    print(f"  - video_count : {video_count}")
    print(f"  - video_count (rounded): {db_video['count']}")
    # pprint(db_video)

    # Align audio and video duration
    scenes: list[Scene] = db_video['scenes']
    video_count = db_video['count']
    if audio_count > video_count:
        # Frames shall be added: use the loop effect for this
        last_scene: Scene = scenes[-1]
        frame_no = last_scene['src'].last_frame_no()
        print(f"  -> add video frames, video({video_count}) < audio ({audio_count})")
        loop_count = audio_count - video_count
        fade: int = min(loop_count, 25)
        if 'effects' not in last_scene:
            last_scene['effects'] = Effects()
        if (effect := last_scene['effects'].get_effect('fadeout')):
            # Transform the fadeout effect in loop_and_fadeout
            effect.name = 'loop_and_fadeout'
            effect.frame_ref = frame_no
            effect.loop = loop_count
            effect.fade = fade
        else:
            last_scene['effects'].append(
                Effect(
                    name='loop_and_fadeout',
                    frame_ref=frame_no,
                    loop=loop_count,
                    fade=fade,
                )
            )

        db_video['count'] += loop_count
        print(f"  -> video_count: {db_video['count']}")
        print(lightcyan(f"-----------------------------------------------------------"))
        return

    elif video_count > audio_count:
        # Add silence to the audio track by adding a new segment
        print(f"  -> add audio silence, video({video_count}) > audio ({audio_count})")
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
    print(f"  -> audio: {db_audio['count']}")

    if (effect := db_video['effects'].get_effect('fadeout')):
        last_scene: Scene = scenes[-1]
        frame_no = last_scene['src'].last_frame_no() - effect.fade
        if 'effect' not in last_scene:
            last_scene['effects'] = Effects()
        last_scene['effects'].append(
            Effect(
                name='fadeout',
                frame_ref=frame_no,
                loop=0,
                fade=effect.fade
            )
        )
    print(lightcyan(f"-----------------------------------------------------------"))

    # elif video_count == audio_count:
    #     print(f"info: consolidate_av_tracks: %s: video(%d) = audio (%d)" % (k_chapter_c, video_count, audio_count))






def check_audio_duration_multiple_of_frames(ch_audio: ChapterAudio) -> int:
    fps = get_fps(db)
    audio_duration: float = ch_audio['duration']
    audio_count = ms_to_frame(audio_duration, fps)
    audio_count_rounded = float(int((audio_duration * fps / 1000) + 0.5))
    audio_count_float = (audio_duration * fps / 1000)
    if audio_count_float != audio_count_rounded:
        raise ValueError(f"consolidate_av_tracks: correct or remove this (add an audio segment), {k_ep}:{k_ch}")
        # Add silence to the latest segment
        s = ch_audio['segments'][-1]
        silence = int(((audio_count_rounded - audio_count_float) * 1000 / fps) + 0.5)
        if 'segments' in s.keys():
            s['silence'] += silence
        else:
            s['silence'] = silence

        ch_audio['duration'] = int(audio_count_rounded * 1000 / fps)
        audio_count = audio_count_rounded
        warnings.warn(f"consolidate_av_tracks: {k_ep}:{k_ch}: add a silence to round the audio duration: {silence}")
    return audio_count


def add_loop_and_fadeout_effect(
    ch_video: ChapterVideo,
    ch_audio: ChapterAudio,
    k_ep: str, k_ch: str
):
    # Frames shall be added: use the loop (and fadeout) effect for this
    video_count = ch_video['count']
    audio_count = ch_audio['count']
    logger.debug(
        lightgrey(f"\t{k_ep}:{k_ch}: ")
        + f"video({video_count}) < audio ({audio_count}): add video frames, "
    )
    last_scene: Scene = ch_video['scenes'][-1]
    loop_count: int = audio_count - video_count
    ch_fade: int = 0
    if ch_video['effects'].has_effect('fadeout'):
        ch_fade = ch_video['effects'].get_effect('fadeout').fade
        if ch_fade > audio_count - video_count:
            raise ValueError(f"ch fade ({ch_fade}) is > loop {loop_count}")
    last_scene['effects'] = Effects([
        Effect(
            name='loop_and_fadeout',
            frame_ref=last_scene['src'].last_frame_no(),
            loop=loop_count,
            fade=max(ch_fade, min(loop_count, 25))
        )
    ])
    ch_video['count'] += loop_count



def consolidate_last_scene_effect(ch_video: ChapterVideo) -> None:
    # Get fadeout from chapter and put it in last scene
    if ch_effect := ch_video['effects'].get_effect('fadeout'):
        last_scene: Scene = ch_video['scenes'][-1]
        last_scene['effects'] = Effects([
            Effect(
                name='fadeout',
                frame_ref=last_scene['dst']['count'] - ch_effect.fade,
                fade=ch_effect.fade
            )
        ])
