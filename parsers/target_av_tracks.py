from __future__ import annotations
from copy import deepcopy
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



def consolidate_av_tracks(k_ep, k_ch: str = '') -> None:
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
            # raise ValueError(red(f"{k_ep}:{k_ch} too many frames"))
            warnings.warn(red(f"{k_ep}:{k_ch} too many frames"))

        elif audio_count > video_count:
            add_loop_and_fadeout_effect(ch_video, ch_audio, k_ep, k_ch)

        else:
            consolidate_last_scene_effect(ch_video)


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

    print(lightcyan(f"----------------- Consolidate A/V tracks ------------------"))
    print(f"chapter: {k_ch}")
    print(f"  - audio_count: {ch_audio['count']}")
    print(f"  - audio_duration: {ch_audio['duration']}")
    print(f"  - video_count : {video_count}")
    print(f"  - video_count (rounded): {ch_video['count']}")

    # First scene
    e_s0_vcount: int = ch_video['scenes'][0]['src'].frame_count()
    e_s0_acount: int = (
        db[k_ep]['video'][k_ed_audio_src]['episode']['scenes'][1]['start']
        - ms_to_frame(ch_audio['start'], fps)
    )
    print(f"Target: episode, 1st scene video count: {e_s0_vcount}, must be {e_s0_acount}")

    if e_s0_vcount > e_s0_acount:
        warnings.warn(yellow(f"{k_ep}:{k_ch} scene 0 is too long ({e_s0_vcount} > {e_s0_acount})"))

        # Too many frames, add silence only for episode 1 (no precedemment)
        if db_video['precedemment']['count'] <= 0:
            print("add silence, use avsync")
            avsync: int = e_s0_vcount - e_s0_acount
            ch_audio['avsync'] = 1000. * avsync / fps
            pprint(ch_audio)
            ch_audio['count'] += avsync


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
                loop=loop_count - 1,
                fade=fade,
            )
        )
        video_count += loop_count
        logger.debug(f"Fade in and loop at the beginning of the episode: {loop_count}, fade={fade}")


    video_count = ch_video['count']
    audio_count = ch_audio['count']

    # Last scene
    print(lightblue(f"{k_ep}:{k_ch}"), f"audio count: before: {ch_audio['count']}")
    print(lightblue(f"{k_ep}:{k_ch}"), f"video count: before: {ch_video['count']}")
    if video_count > audio_count:
        # raise ValueError(red(f"{k_ep}:{k_ch} too many frames"))
        warnings.warn(red(f"{k_ep}:{k_ch} too many frames"))

    elif audio_count > video_count:
        add_loop_and_fadeout_effect(ch_video, ch_audio, k_ep, k_ch)

    else:
        consolidate_last_scene_effect(ch_video, k_ep, k_ch)
    print(lightblue(f"{k_ep}:{k_ch}"), f"audio count: after: {ch_audio['count']}")
    print(lightblue(f"{k_ep}:{k_ch}"), f"video count: after: {ch_video['count']}")


    # Report chapter effects (fadein) in first scene
    consolidate_first_scene_effect(ch_video=ch_video)

    print(f"  -> video_count: {ch_video['count']}")
    print(lightcyan(f"-----------------------------------------------------------"))

    consolidate_silence(ch_video, ch_audio)
    warnings.warn("Consolidate first scene with loop_and_fadein")



    # g_asuivre
    #---------------------------------------------------------------------------
    if db_video['asuivre']['count']:
        k_ch = 'g_asuivre'
        ch_audio: ChapterAudio = db_audio[k_ch]
        ch_video: ChapterVideo = db_video[k_ch]
        audio_count = check_audio_duration_multiple_of_frames(ch_audio)
        ch_audio['count'] = audio_count

        print(ch_video['count'])
        pprint(ch_audio)

        ch_video['count'] = ch_audio['count']
        last_scene: Scene = ch_video['scenes'][-1]
        last_scene['effects'] = Effects([
            Effect(
                name='loop',
                frame_ref=last_scene['src'].last_frame_no(),
                loop=ch_video['count'] - 1
            )
        ])
        last_scene['dst']['count'] = ch_video['count']
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
    video_count = ch_video['count']

    print(lightblue(f"{k_ep}:{k_ch}"), f"audio count: before: {ch_audio['count']}")
    print(lightblue(f"{k_ep}:{k_ch}"), f"video count: before: {ch_video['count']}")

    if audio_count > video_count:
        print("add_loop_and_fadeout_effect")
        add_loop_and_fadeout_effect(ch_video, ch_audio, k_ep, k_ch)

    elif video_count > audio_count:
        # raise ValueError(red(f"{k_ep}:{k_ch} too many frames: {video_count} > {audio_count}"))
        warnings.warn(red(f"{k_ep}:{k_ch} too many frames: {video_count} > {audio_count}"))

    else:
        print("consolidate_last_scene_effect")
        consolidate_last_scene_effect(ch_video)

    print(lightblue(f"{k_ep}:{k_ch}"), f"audio count: after: {ch_audio['count']}")
    print(lightblue(f"{k_ep}:{k_ch}"), f"video count: after: {ch_video['count']}")
    consolidate_silence(ch_video, ch_audio)


    # g_doc
    #---------------------------------------------------------------------------
    k_ch = 'g_doc'
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
        last_scene['dst']['count'] += loop_count

    elif ch_video['count'] > ch_audio['count']:
        # Remove some frames: patch src
        to_remove: int = ch_video['count'] - ch_audio['count']
        logger.debug(f"{k_ch}: remove {to_remove} frames")
        last_scene['src'].last_scene()['count'] -= to_remove
        last_scene['dst']['count'] = last_scene['src'].last_scene()['count']

    # audio frame count = video frame count
    ch_video['count'] = ch_audio['count']

    if k_ep == K_EP_DEBUG:
        logger.debug(f"\ndb_video: %s:\n--------------------------------------" % (k_ch))
        pprint(ch_video)



    # doc
    #---------------------------------------------------------------------------
    k_ch = 'doc'
    ch_audio: ChapterAudio = db_audio[k_ch]
    ch_video: ChapterVideo = db_video[k_ch]
    audio_count = check_audio_duration_multiple_of_frames(ch_audio)
    ch_audio['count'] = audio_count
    video_count = get_video_chapter_frame_count(k_ep, k_ch)

    print(lightblue(f"{k_ep}:{k_ch}"), f"audio count: before: {ch_audio['count']}")
    print(lightblue(f"{k_ep}:{k_ch}"), f"video count: before: {video_count}")

    if audio_count > video_count:
        add_loop_and_fadeout_effect(ch_video, ch_audio, k_ep, k_ch)
        raise

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

    consolidate_silence(ch_video, ch_audio)



def consolidate_av_tracks_g_debut_fin(k_ch: str) -> None:
    """This function compares the audio and video tracks of a generique
    It aligns these 2 durations by:
    - adding silences
    - adding frames (loop, loop and fadeout)
    """
    print(lightgreen(f"  _consolidate_av_tracks_g_debut_end: {k_ch}"))
    print(f"  language: {db[k_ch]['audio']['lang']}")
    fps = get_fps(db)
    if k_ch not in ('g_debut', 'g_fin'):
        return

    # video and audio tracks
    ch_video: ChapterVideo = db[k_ch]['video']
    ch_audio: ChapterAudio = db[k_ch]['audio']

    # Get nb of frames for the video track
    video_count: int = get_video_chapter_frame_count(k_ep='', k_ch=k_ch)

    # # Align video track to a multiple of seconds
    # ch_video['count'] = int(fps * int(1 + ch_video['count'] / fps))
    # if video_count != ch_video['count']:
    #     ch_video['silence'] = ch_video['count'] - video_count

    # Get the duration in ms
    audio_duration = ch_audio['duration']
    if 'avsync' in ch_audio:
        audio_duration += ch_audio['avsync']

    # Add silence because audio track is generated with this
    if 'silence' in ch_audio:
        audio_duration += ch_audio['silence']

    print(f"  audio duration (silence included): {audio_duration/1000:.03f}s")
    initial_audio_count = ms_to_frame(audio_duration, fps)
    print(f"  audio count: {initial_audio_count}")

    # Align audio track to a multiple of seconds
    rounded_audio_duration = 1000 * int(1 + float(audio_duration)/1000)
    audio_count = ms_to_frame(rounded_audio_duration, fps)
    print(f"rounded audio count: {audio_count}")
    if frame_to_ms(audio_count, fps) != audio_duration:
        ch_audio['segments'].append({
            'start': 0,
            'end': 0,
            'silence': frame_to_ms(audio_count, fps) - audio_duration
        })

    # Update audio duration and nb of frames
    ch_audio['count'] = audio_count
    ch_audio['duration'] = frame_to_ms(audio_count, fps)


    print(lightcyan(f"----------------- Consolidate A/V tracks ------------------"))
    print(f"chapter: {k_ch}")
    print(f"  - audio_count: {ch_audio['count']}")
    print(f"  - audio_duration: {ch_audio['duration']}")
    print(f"  - video_count : {video_count}")
    print(f"  - video_count (rounded): {ch_video['count']}")
    # pprint(db_video)

    # Align audio and video duration
    scenes: list[Scene] = ch_video['scenes']
    ch_video['silence'] = ms_to_frame(ch_audio['silence'], fps)
    ch_video['silence'] += (audio_count - initial_audio_count)

    video_count_silence = ch_video['count'] + ch_video['silence']

    print(f"  video_count_silence: {video_count_silence} vs audio_count: {audio_count}")
    # raise

    # The following consildation are done for g_debut/g_fin
    # because g_reporatge/g_asuivre video count uses audio count
    if audio_count > video_count_silence:
        # Frames shall be added: use the loop effect for this
        last_scene: Scene = scenes[-1]
        frame_no = last_scene['src'].last_frame_no()
        print(f"  -> add video frames, video({video_count_silence}) < audio ({audio_count})")
        loop_count = audio_count - video_count_silence

        fade: int = 25
        if (effect := ch_video['effects'].get_effect('fadeout')):
            fade = effect.fade

        if 'effects' not in last_scene:
            last_scene['effects'] = Effects()

        # Transform the fadeout effect in loop_and_fadeout
        if effect := last_scene['effects'].get_effect('fadeout'):
            warnings.warn(red("consolidate_av_tracks_g_debut_fin - verify this"))
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

        last_scene['dst']['count'] += loop_count
        ch_video['count'] += loop_count
        print(f"  -> video_count: {ch_video['count']}")
        print(lightcyan(f"-----------------------------------------------------------"))


    elif video_count_silence > audio_count:
        # Add silence to the audio track by adding a new segment
        raise
        print(f"  -> add audio silence, video({video_count_silence}) > audio ({audio_count})")
        video_duration = frame_to_ms(video_count_silence, fps)
        audio_duration = ch_audio['duration']
        silence_duration = video_duration - audio_duration
        ch_audio['segments'].append({
            'start': 0,
            'end': 0,
            'silence': silence_duration,
        })
        ch_audio['count'] = ch_video['count']
        ch_audio['duration'] += silence_duration

        print(f"  -> audio: {ch_audio['count']}")

        if (effect := ch_video['effects'].get_effect('fadeout')):
            raise NotImplementedError("fadeout for g_debut/g_fin")
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


    elif video_count == audio_count:
        consolidate_last_scene_effect(ch_video=ch_video)


    # Report chapter effects (fadein) in first scene, there is no loop in generiques
    consolidate_first_scene_effect(ch_video=ch_video)


    if 'silence' in ch_audio and ch_audio['silence']:
        ch_video['silence'] = ch_audio['count'] - ch_video['count']
        print(f"add silence: {ch_video['silence']}")
        # raise


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
        # if ch_fade > loop_count:
        #     raise ValueError(f"ch fade ({ch_fade}) is > loop {loop_count}")
    last_scene['effects'] = Effects([
        Effect(
            name='loop_and_fadeout',
            frame_ref=last_scene['src'].last_frame_no(),
            loop=loop_count,
            fade=max(ch_fade, min(loop_count, 25))
        )
    ])
    last_scene['dst']['count'] += loop_count
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



def consolidate_first_scene_effect(ch_video: ChapterVideo) -> None:
    if ch_effect := ch_video['effects'].get_effect('fadein'):
        first_scene: Scene = ch_video['scenes'][0]
        if 'effects' not in first_scene:
            first_scene['effects'] = Effects()
        effect = deepcopy(ch_effect)
        effect.frame_ref = first_scene['src'].first_frame_no()
        first_scene['effects'].append(effect)

    elif ch_effect := ch_video['effects'].get_effect('loop_and_fadein'):
        first_scene: Scene = ch_video['scenes'][0]
        if 'effects' not in first_scene:
            first_scene['effects'] = Effects()
        effect = deepcopy(ch_effect)
        effect.frame_ref = first_scene['src'].first_frame_no()
        first_scene['effects'].append(effect)



def consolidate_silence(ch_video: ChapterVideo, ch_audio: ChapterVideo) -> None:
    if 'silence' in ch_audio and ch_audio['silence']:
        ch_video['silence'] = ms_to_frame(
            ch_audio['silence'], frame_rate=get_fps(db)
        )
        print(f"add silence: {ch_video['silence']}")
