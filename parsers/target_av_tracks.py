from __future__ import annotations
from copy import deepcopy
import sys
from pprint import pprint
import warnings


from parsers._keys import main_chapter_keys
from parsers.video_target import get_video_chapter_frame_count
from .helpers import get_frame_rate, nested_dict_set
from .logger import logger
from utils.p_print import *
from utils.time_conversions import (
    FrameRate,
    frame_to_ms,
    ms_to_frame,
)
from utils.mco_types import ChapterAudio, Scene, ChapterVideo
from ._db import db
from .effects import Effect, Effects



def consolidate_av_tracks(k_ep, k_ch: str = '', verbose: bool = False) -> None:
    fps = get_frame_rate()

    logger.debug(lightgreen(f"consolidate_av_tracks: {k_ep}"))
    if verbose:
        print(f"[I] consolidate_av_tracks: {k_ep}:{k_ch}")
    K_EP_DEBUG, K_CHAPTER_DEBUG = '', ''
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
            print(yellow(f"[W] {k_ep}:{k_ch} add loop and fadeout"))
            add_loop_and_fadeout_effect(ch_video, ch_audio, k_ep, k_ch)

        else:
            consolidate_last_scene_effect(ch_video, verbose=verbose)

    else:
        print(darkgrey(f"[I] No chapter: \'{k_ch}\'"))


    # episode
    #---------------------------------------------------------------------------
    k_ch = 'episode'
    # audio/video targets:
    ch_audio: ChapterAudio = db_audio[k_ch]
    ch_video: ChapterVideo = db_video[k_ch]

    audio_count = check_audio_duration_multiple_of_frames(ch_audio)
    ch_audio['count'] = audio_count
    video_count = ch_video['count']

    k_ed_audio_src = db_audio['src']['k_ed']

    print(lightcyan(f"----------------- Consolidate A/V tracks ------------------"))
    print(f"k_ed_audio_src: {k_ed_audio_src}")
    print(f"chapter: {k_ch}")
    print(f"  - audio_count: {ch_audio['count']}")
    print(f"  - audio_duration: {ch_audio['duration']}")
    print(f"  - video_count : {video_count}")
    print(f"  - video_count (rounded): {ch_video['count']}")


    #   episode: 1st scene
    #---------------------------------------------------------------------------
    print(lightblue(f"{k_ep}:{k_ch} First scene"))
    # First scenes
    #   Let's use the first 3 scenes because sometimes replaced by other edition
    #   and nb of frames might differ. e.g. episode 1
    e_s0_vcount: int = sum(
        [ch_video['scenes'][i]['src'].frame_count() for i in range(3)]
    )
    e_s0_acount: int = (
        db[k_ep]['video'][k_ed_audio_src]['episode']['scenes'][3]['start']
        - ms_to_frame(ch_audio['start'], fps)
    )
    print(f"Target: episode, 3 first scene video count: {e_s0_vcount}, must be {e_s0_acount}")

    if e_s0_vcount > e_s0_acount:
        print(yellow(f"[W] {k_ep}:{k_ch} first scenes are too long ({e_s0_vcount} > {e_s0_acount})"))
        to_remove: int = e_s0_vcount - e_s0_acount

        # Too many frames, add silence and fadein only for episode 1
        # (no precedemment)
        if db_video['precedemment']['count'] <= 0:
            avsync: int = to_remove // 2
            print(f"[I]  add silence, use avsync: {avsync}")
            ch_audio['avsync'] = 1000. * avsync / fps
            ch_audio['count'] += avsync
            to_remove -= avsync

        print(f"[I]  remove frames and fadein: {to_remove}")
        src_scene: Scene = ch_video['scenes'][0]['src'].primary_scene()
        src_scene.start += to_remove
        src_scene.count -= to_remove
        ch_video['count'] -= to_remove
        if 'effects' not in ch_video:
            ch_video['effects'] = Effects()
        ch_video['effects'].append(
            Effect(
                name='fadein',
                loop=to_remove - 1,
                fade=to_remove,
            )
        )

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

        warnings.warn(red(f"Fade in and loop at the beginning of the episode: {loop_count}, fade={fade}"))

    video_count = ch_video['count']
    audio_count = ch_audio['count']

    #   episode: last scene
    #---------------------------------------------------------------------------
    print(lightblue(f"{k_ep}:{k_ch} Last scene"))

    print(f" before")
    print(f"  - audio count: before: {ch_audio['count']}")
    print(f"  - video count: before: {ch_video['count']}")
    if video_count > audio_count:
        # raise ValueError(red(f"{k_ep}:{k_ch} too many frames"))
        warnings.warn(red(f"{k_ep}:{k_ch} too many frames"))

    elif audio_count > video_count:
        add_loop_and_fadeout_effect(ch_video, ch_audio, k_ep, k_ch)
        print(f"[I]  add loop and fadeout")

    else:
        consolidate_last_scene_effect(ch_video, verbose=verbose)
    print(f" after")
    print(f"  - audio count: after: {ch_audio['count']}")
    print(f"  - video count: after: {ch_video['count']}")


    # Report chapter effects (fadein) in first scene
    consolidate_first_scene_effect(ch_video=ch_video)

    print(f"  -> video_count: {ch_video['count']}")
    consolidate_silence(ch_video, ch_audio, verbose=verbose)
    print(lightcyan(f"-----------------------------------------------------------"))



    # g_asuivre
    #---------------------------------------------------------------------------
    if db_video['asuivre']['count']:
        print(lightblue(f"{k_ep}:{k_ch} g_asuivre"))
        k_ch = 'g_asuivre'
        ch_audio: ChapterAudio = db_audio[k_ch]
        ch_video: ChapterVideo = db_video[k_ch]
        audio_count = check_audio_duration_multiple_of_frames(ch_audio)
        ch_audio['count'] = audio_count
        ch_video['count'] = ch_audio['count']
        last_scene: Scene = ch_video['scenes'][-1]
        last_scene['effects'] = Effects([
            Effect(
                name='loop',
                f_ref=last_scene['src'].last_frame_no(),
                loop=ch_video['count'] - 1
            )
        ])
        last_scene['dst']['count'] = ch_video['count']
        print(f"  video count: {last_scene['dst']['count']}")
        if k_ep == K_EP_DEBUG:
            print(f"\ndb_video: %s:\n--------------------------------------" % (k_ch))
            pprint(ch_video)
    else:
        print(darkgrey(f"[I] No chapter: \'{k_ch}\'"))


    # asuivre
    #---------------------------------------------------------------------------
    k_ch = 'asuivre'
    ch_audio: ChapterAudio = db_audio[k_ch]
    ch_video: ChapterVideo = db_video[k_ch]
    audio_count = check_audio_duration_multiple_of_frames(ch_audio)
    ch_audio['count'] = audio_count
    video_count = ch_video['count']

    print(lightblue(f"{k_ep}:{k_ch}"))
    print(f" before")
    print(f"  - audio count: before: {ch_audio['count']}")
    print(f"  - video count: before: {ch_video['count']}")

    if audio_count > video_count:
        print("add_loop_and_fadeout_effect")
        add_loop_and_fadeout_effect(ch_video, ch_audio, k_ep, k_ch)

    elif video_count > audio_count:
        # raise ValueError(red(f"{k_ep}:{k_ch} too many frames: {video_count} > {audio_count}"))
        warnings.warn(red(f"{k_ep}:{k_ch} too many frames: {video_count} > {audio_count}"))

    else:
        print("consolidate_last_scene_effect")
        consolidate_last_scene_effect(ch_video, verbose=verbose)

    print(f" after")
    print(f" - audio count: after: {ch_audio['count']}")
    print(f" - video count: after: {ch_video['count']}")
    consolidate_silence(ch_video, ch_audio)
    print(lightcyan(f"-----------------------------------------------------------"))


    # g_doc
    #---------------------------------------------------------------------------
    k_ch = 'g_doc'
    ch_audio: ChapterAudio = db_audio[k_ch]
    ch_video: ChapterVideo = db_video[k_ch]

    ch_audio['count'] = ms_to_frame(ch_audio['duration'], fps)
    last_scene = ch_video['scenes'][-1]

    print(lightblue(f"{k_ep}:{k_ch}"))

    if ch_audio['count'] > ch_video['count']:
        # Use last frame to loop
        loop_start = last_scene['src'].last_frame_no()
        loop_count = ch_audio['count'] - ch_video['count']
        print(darkgrey(f"[I] Loop on last frame: {loop_count}"))
        logger.debug(f"{k_ch}: loop, last frame={loop_start}, {loop_count} frames")
        last_scene['effects'] = Effects([
            Effect(
                name='loop',
                f_ref=loop_start,
                loop=loop_count
            )
        ])
        last_scene['dst']['count'] += loop_count

    elif ch_video['count'] > ch_audio['count']:
        # Remove some frames: patch src
        to_remove: int = ch_video['count'] - ch_audio['count']
        print(darkgrey(f"[I] Remove some frames: {to_remove}"))
        logger.debug(f"{k_ch}: remove {to_remove} frames")
        last_scene['src'].last_scene().count -= to_remove
        last_scene['dst']['count'] = last_scene['src'].last_scene().count

    else:
        print(darkgrey(f"[I] Same duration: {ch_video['count']}f"))

    ch_video['count'] = ch_audio['count']


    # doc
    #---------------------------------------------------------------------------
    k_ch = 'doc'
    ch_audio: ChapterAudio = db_audio[k_ch]
    ch_video: ChapterVideo = db_video[k_ch]
    audio_count = check_audio_duration_multiple_of_frames(ch_audio)
    ch_audio['count'] = audio_count
    video_count = get_video_chapter_frame_count(k_ep, k_ch)

    print(lightblue(f"{k_ep}:{k_ch}"))
    print(f" before")
    print(f"  - audio count: before: {ch_audio['count']}")
    print(f"  - video count: before: {ch_video['count']}")

    if audio_count > video_count:
        add_loop_and_fadeout_effect(ch_video, ch_audio, k_ep, k_ch)
        raise ValueError("must not loop and fadeout")

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
        consolidate_last_scene_effect(ch_video, verbose=verbose)


    print(f" after")
    print(f" - audio count: after: {ch_audio['count']}")
    print(f" - video count: after: {ch_video['count']}")

    consolidate_silence(ch_video, ch_audio, verbose=verbose)
    print(lightcyan(f"-----------------------------------------------------------"))





def consolidate_av_tracks_g_debut_fin(k_ch: str, verbose: bool = False) -> None:
    """This function compares the audio and video tracks of a generique
    It aligns these 2 durations by:
    - adding silences
    - adding frames (loop, loop and fadeout)
    """
    if verbose:
        print(darkgrey(f"[I] consolidate_av_tracks_g_debut_fin: {k_ch}"))
        print(f"  language: {db[k_ch]['audio']['lang']}")
    frame_rate = get_frame_rate()
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
    else:
        pprint(ch_audio)
        raise

    if verbose:
        print(f"  audio duration (silence included): {audio_duration/1000:.03f}s")
    initial_audio_count = ms_to_frame(audio_duration, frame_rate)
    if verbose:
        print(f"  audio count: {initial_audio_count}")

    # Align audio track to a multiple of seconds
    rounded_audio_duration = 1000 * int(1 + float(audio_duration)/1000)
    audio_count = ms_to_frame(rounded_audio_duration, frame_rate)
    if verbose:
        print(f"rounded audio count: {audio_count}")
    if frame_to_ms(audio_count, frame_rate) != audio_duration:
        ch_audio['segments'].append({
            'start': 0,
            'end': 0,
            'silence': frame_to_ms(audio_count, frame_rate) - audio_duration
        })

    # Update audio duration and nb of frames
    ch_audio['count'] = audio_count
    ch_audio['duration'] = frame_to_ms(audio_count, frame_rate)


    if verbose:
        print(lightcyan(f"----------------- Consolidate A/V tracks ------------------"))
        print(f"chapter: {k_ch}")
        print(f"  - audio_count: {ch_audio['count']}")
        print(f"  - audio_duration: {ch_audio['duration']}")
        print(f"  - video_count : {video_count}")
        print(f"  - video_count (rounded): {ch_video['count']}")
    # pprint(db_video)

    # Align audio and video duration
    scenes: list[Scene] = ch_video['scenes']
    ch_video['silence'] = ms_to_frame(ch_audio['silence'], frame_rate)
    ch_video['silence'] += (audio_count - initial_audio_count)

    video_and_silence_count = ch_video['count'] + ch_video['silence']

    if verbose:
        print(f"  video + silence: {video_and_silence_count} vs audio_count: {audio_count}")
    # raise

    # The following consildation are done for g_debut/g_fin
    # because g_reporatge/g_asuivre video count uses audio count
    if audio_count > video_and_silence_count:
        # Frames shall be added: use the loop effect for this
        last_scene: Scene = scenes[-1]
        frame_no = last_scene['src'].last_frame_no()
        if verbose:
            print(f"  -> add video frames, video({video_and_silence_count}) < audio ({audio_count})")
        loop_count = audio_count - video_and_silence_count

        fade: int = 25
        if (effect := ch_video['effects'].get_effect('fadeout')):
            fade = effect.fade

        if 'effects' not in last_scene:
            last_scene['effects'] = Effects()

        # Transform the fadeout effect in loop_and_fadeout
        if effect := last_scene['effects'].get_effect('fadeout'):
            warnings.warn(red("consolidate_av_tracks_g_debut_fin - verify this"))
            effect.name = 'loop_and_fadeout'
            effect.f_ref = frame_no
            effect.loop = loop_count
            effect.fade = fade

        else:
            last_scene['effects'].append(
                Effect(
                    name='loop_and_fadeout',
                    f_ref=frame_no,
                    loop=loop_count,
                    fade=fade,
                )
            )

        last_scene['dst']['count'] += loop_count
        ch_video['count'] += loop_count
        if verbose:
            print(f"  -> video_count: {ch_video['count']}")
            print(lightcyan(f"-----------------------------------------------------------"))


    elif video_and_silence_count > audio_count:
        # Add silence to the audio track by adding a new segment
        raise
        print(f"  -> add audio silence, video({video_and_silence_count}) > audio ({audio_count})")
        video_duration = frame_to_ms(video_and_silence_count, frame_rate)
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
                    f_ref=frame_no,
                    loop=0,
                    fade=effect.fade
                )
            )
        print(lightcyan(f"-----------------------------------------------------------"))


    elif video_count == audio_count:
        if verbose:
            print(f"  - audio = video = {audio_count}")
        consolidate_last_scene_effect(ch_video=ch_video)


    # Report chapter effects (fadein) in first scene, there is no loop in generiques
    consolidate_first_scene_effect(ch_video=ch_video)


    if 'silence' in ch_audio and ch_audio['silence']:
        ch_video['silence'] = ch_audio['count'] - ch_video['count']
        if verbose:
            print(f"add silence: {ch_video['silence']}")
        # raise


def check_audio_duration_multiple_of_frames(ch_audio: ChapterAudio) -> int:
    fps = get_frame_rate()
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

    # Reuse part's fade if already defined in config files
    ch_fade: int = 0
    if ch_video['effects'].has_effect('fadeout'):
        ch_fade = ch_video['effects'].get_effect('fadeout').fade

    last_scene['effects'] = Effects([
        Effect(
            name='loop_and_fadeout',
            f_ref=last_scene['src'].last_frame_no(),
            loop=loop_count,
            fade=max(ch_fade, min(loop_count, 25))
        )
    ])
    last_scene['dst']['count'] += loop_count
    ch_video['count'] += loop_count



def consolidate_last_scene_effect(
    ch_video: ChapterVideo,
    verbose: bool = False,
) -> None:
    # Get fadeout from chapter and put it in last scene
    if ch_effect := ch_video['effects'].get_effect('fadeout'):
        last_scene: Scene = ch_video['scenes'][-1]
        last_scene['effects'] = Effects([
            Effect(
                name='fadeout',
                f_ref=last_scene['dst']['count'] - ch_effect.fade,
                fade=ch_effect.fade
            )
        ])
        if verbose:
            print(darkgrey(f"[I] add fadeout effect: {ch_effect.fade}"))



def consolidate_first_scene_effect(ch_video: ChapterVideo) -> None:
    if ch_effect := ch_video['effects'].get_effect('fadein'):
        first_scene: Scene = ch_video['scenes'][0]
        if 'effects' not in first_scene:
            first_scene['effects'] = Effects()
        effect = deepcopy(ch_effect)
        effect.f_ref = first_scene['src'].first_frame_no()
        first_scene['effects'].append(effect)

    elif ch_effect := ch_video['effects'].get_effect('loop_and_fadein'):
        first_scene: Scene = ch_video['scenes'][0]
        if 'effects' not in first_scene:
            first_scene['effects'] = Effects()
        effect = deepcopy(ch_effect)
        effect.f_ref = first_scene['src'].first_frame_no()
        first_scene['effects'].append(effect)



def consolidate_silence(
    ch_video: ChapterVideo,
    ch_audio: ChapterVideo,
    verbose: bool = False
) -> None:
    if 'silence' in ch_audio and ch_audio['silence']:
        ch_video['silence'] = ms_to_frame(
            ch_audio['silence'], frame_rate=get_frame_rate()
        )
        if verbose:
            print(darkgrey(f"[I] add silence: {ch_video['silence']}"))
