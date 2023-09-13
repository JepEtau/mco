# -*- coding: utf-8 -*-
import sys
from pprint import pprint

from utils.common import FPS
from utils.nested_dict import nested_dict_set
from utils.pretty_print import *
from utils.time_conversions import (
    frames_to_ms,
    ms_to_frames,
)
from utils.types import Shot



def consolidate_av_tracks(db, k_ep, k_part:str='') -> None:
    if k_part in ['g_debut', 'g_fin']:
        __consolidate_av_tracks_g_debut_fin(db, k_ep, k_part_g=k_part)
        return

    print(red("consolidate_av_tracks:"), f"{k_ep}")
    K_EP_DEBUG, K_PART_DEBUG = [''] *2
    # K_EP_DEBUG = 'ep05'
    # K_PART_DEBUG = 'precedemment'
    try:
        db_video = db[k_ep]['video']['target']
        db_audio = db[k_ep]['audio']
    except:
        sys.exit(f"consolidate_av_tracks: error, audio or video does not exist in {k_ep}:common")

    if k_ep == K_EP_DEBUG:
        print(f"consolidate_av_tracks: {k_ep}, db_audio:")
        pprint(db_audio)

    # g_asuivre
    #---------------------------------------------------------------------------
    if db_video['asuivre']['count'] != 0:
        # Update the shot with the duration that is calculated in the audio structure
        k_part_g = 'g_asuivre'
        db_video[k_part_g]['count'] = db_audio[k_part_g]['count']
        last_shot = db_video[k_part_g]['shots'][-1]
        last_shot['effects'] = [
            'loop',
            last_shot['start'] + last_shot['count'] - 1,
            db_video[k_part_g]['count'] - last_shot['count']]
        if k_ep == K_EP_DEBUG:
            print(f"\ndb_video: %s:\n--------------------------------------" % (k_part_g))
            pprint(db_video[k_part_g])


    # g_documentaire
    #---------------------------------------------------------------------------
    # Update the shot with the duration that is calculated in the audio structure
    k_part_g = 'g_documentaire'

    last_shot = db_video[k_part_g]['shots'][-1]
    if db_audio[k_part_g]['count'] > db_video[k_part_g]['count']:
        # Use last frame
        loop_start = last_shot['start'] + last_shot['count'] - 1
        loop_count = db_audio[k_part_g]['count'] - db_video[k_part_g]['count']
        print(f"{k_part_g}: loop, last frame={loop_start}, {loop_count} frames")
        last_shot['effects'] = ['loop', loop_start, loop_count]

    elif db_video[k_part_g]['count'] > db_audio[k_part_g]['count']:
        # remove some frames
        print(f"{k_part_g}: remove {db_video[k_part_g]['count']- db_audio[k_part_g]['count']} frames")
        last_shot['count'] -= db_video[k_part_g]['count'] - db_audio[k_part_g]['count']
        last_shot['dst']['count'] = last_shot['count']

    db_video[k_part_g]['count'] = db_audio[k_part_g]['count']
    if k_ep == K_EP_DEBUG:
        print(f"\ndb_video: %s:\n--------------------------------------" % (k_part_g))
        pprint(db_video[k_part_g])


    # asuivre, documentaire
    #---------------------------------------------------------------------------
    for k_part in ['precedemment', 'episode', 'asuivre', 'documentaire']:
        if k_ep == K_EP_DEBUG and k_part == K_PART_DEBUG:
            print(f"\ndb_video: %s:\n--------------------------------------" % (k_part))
            pprint(db_video[k_part])

        # Calculate audio duration
        audio_duration = db_audio[k_part]['avsync'] + db_audio[k_part]['duration']

        if k_part == 'episode':
            # Add precedemment
            audio_duration = (db_audio['precedemment']['avsync']
                + db_audio['precedemment']['duration']
                + db_audio['episode']['duration'])

        # Round audio count to a multiple of 1000/FPS ms
        audio_count = ms_to_frames(audio_duration)
        audio_count_rounded = float(int((audio_duration * FPS / 1000) + 0.5))
        audio_count_float = (audio_duration * FPS / 1000)
        # print(f"%s:" % (k_part))
        # print(f"\taudio_count_rounded=%f" % (audio_count_rounded))
        # print(f"\taudio_count_float=%f" % (audio_count_float))
        if audio_count_float != audio_count_rounded:
            sys.exit(f"consolidate_av_tracks: correct or remove this (add an audio segment), {k_ep}:{k_part}")
            # Add silence to the latest segment
            s = db_audio[k_part]['segments'][-1]
            silence = int(((audio_count_rounded - audio_count_float) * 1000 / FPS) + 0.5)
            if 'segments' in s.keys():
                s['silence'] += silence
            else:
                s['silence'] = silence

            if k_part == 'episode':
                db_audio[k_part]['duration'] = int(audio_count_rounded * 1000 / FPS) - db_audio['precedemment']['duration']
            else:
                db_audio[k_part]['duration'] = int(audio_count_rounded * 1000 / FPS)
            audio_count = audio_count_rounded
            print ("%s.consolidate_av_tracks: %s:%s: add a silence to round the audio duration: %d" % (__name__, k_ep, k_part, silence))

        # Modify the real audio count to this new duration
        if k_part == 'episode':
            # this is a special case for episode: precedemment+episode
            # print(f"   rounded audio count episode+precedemment: %d" % (audio_count))

            # print(f"episode: consolidate_av_tracks:")
            # print(f"\tvideo avsync: {db_video['episode']['avsync']}")
            # print(f"\taudio avsync: {db_audio['episode']['avsync']}")

            db_audio['episode']['count'] = audio_count - db_audio['precedemment']['count']
            video_count = (db_video['precedemment']['avsync'] + db_video['precedemment']['count']
                + db_video['episode']['avsync'] + db_video['episode']['count'])


            # db_video[k_part]['count'] += db_video[k_part]['avsync']
        else:
            print_red(f"{k_part}")
            db_audio[k_part]['count'] = audio_count
            video_count = db_video[k_part]['count'] + db_video[k_part]['avsync']
            print(f"\taudio: {db_audio[k_part]['count']}")
            print(f"\tvideo: {video_count}")

        # Add loop_and_fade_in
        try:
            video_count += db_video[k_part]['shots'][0]['effects'][1]
        except:
            pass


        # Append added duration to audio track
        audio_count += ms_to_frames(db_audio[k_part]['avsync'])

        if k_part == 'precedemment':
            continue
        # video_count = db_video[k_part]['count']

        # print(f"info: %s:consolidate_av_tracks: %s:%s: video=%d, audio=%d" % (__name__, k_ep, k_part, video_count, audio_count))
        try:
            last_shot: Shot = db_video[k_part]['shots'][-1]
        except:
            continue

        if audio_count > video_count:
            # Frames shall be added: use the loop (and fadeout) effect for this
            print(f"{k_ep}:{k_part}: consolidate_av_tracks, ",
                  f"video({video_count}) < audio ({audio_count}): add video frames, ")

            frame_no = last_shot['start'] + last_shot['count'] - 1
            loop_count = audio_count - video_count
            if 'src' in last_shot.keys():
                if last_shot['src']['k_ep'] != k_ep:
                    frame_no = last_shot['src']['start'] + last_shot['src']['count'] - 1

                last_shot.update({
                    'effects': ['loop_and_fadeout', frame_no, loop_count, min(loop_count, 25)]
                })
                # last_shot['src']['count'] -= loop_count

            db_video[k_part]['count'] += loop_count

        elif audio_count < video_count:
            # Add silence to the audio track by adding a new segment
            print(f"{k_ep}:{k_part}: consolidate_av_tracks, ",
                  f"video({video_count}) > audio ({audio_count})")
            if True:
                print(yellow("warning: this has been patched (now, remove video frames) for documentaire, verify elsewhere"))
                last_shot:Shot = db_video[k_part]['shots'][-1]
                last_shot['count'] -= video_count - audio_count
                db_video[k_part]['count'] = db_audio[k_part]['count']
                last_shot['dst']['count'] = last_shot['count']
            else:
                video_duration = int(video_count * 1000 / FPS)
                audio_duration = db_audio[k_part]['duration']
                db_audio[k_part]['segments'].append({
                    'start': 0,
                    'end': 0,
                    'silence': video_duration - audio_duration,
                })
            db_audio[k_part]['count'] = db_video[k_part]['count']
            # print(f"-> added silence at the end")

        if k_ep == K_EP_DEBUG and k_part == K_PART_DEBUG:
            print(f"\ndb_video: {k_part}:\n--------------------------------------")
            pprint(db_video[k_part])


    # Add/modify effect of the first/last shot
    #---------------------------------------------------------------------------
    verbose = True
    for k_part in ['episode', 'asuivre', 'documentaire']:
        db_video_part = db_video[k_part]
        if db_video_part['count'] < 1:
            continue
        first_shot:Shot = db_video_part['shots'][0]
        last_shot:Shot = db_video_part['shots'][-1]

        if 'effects' in db_video_part.keys():
            if verbose:
                print_green(f"\teffects detected in {k_ep}:{k_part}")
                print(f"\t", db_video_part['effects'])

            if db_video_part['effects']['loop_and_fadein'] != 0:
                fadein_count = db_video_part['effects']['loop_and_fadein']
                if verbose:
                    print(f"consolidate_av_tracks: {k_ep}:{k_part}, patch the first shot -> fadein: add effects")
                    # pprint(db_video_part)
                # first_shot['src']['start'] += fadein_count
                # first_shot['src']['count'] -= fadein_count
                nested_dict_set(first_shot,
                    ['loop_and_fadein', fadein_count, fadein_count], 'effects')
                if verbose:
                    pprint(first_shot)
                    # sys.exit()

            if ('fadeout' in db_video_part['effects'].keys()
                and db_video_part['effects']['fadeout'] != 0):
                if verbose:
                    print(yellow(f"consolidate_av_tracks: {k_ep}:{k_part} modify fadeout effect in db_video!"))

                fadeout_count = db_video_part['effects']['fadeout']
                if 'effects' in last_shot.keys():
                    # Patch the fadeout/loop_and_fadeout duration
                    if last_shot['effects'][0] == 'fadeout':
                        if verbose:
                            print(f"consolidate_av_tracks: {k_ep}:{k_part}, patch the last shot -> fadeout: modify")
                        last_shot['effects'][2] = fadeout_count

                    elif last_shot['effects'][0] == 'loop_and_fadeout':
                        if verbose:
                            print(f"consolidate_av_tracks: {k_ep}:{k_part}, patch the last shot -> loop_and_fadeout: modify")
                            print(f"\t%d vs %d" % (last_shot['effects'][3], fadeout_count))
                            pprint(last_shot)

                        last_shot_count = (last_shot['count'] +  last_shot['effects'][2])
                        if fadeout_count > last_shot_count:
                            # Modify it because shot duration > fadeout duration
                            last_shot['effects'][3] = last_shot_count
                        else:
                            last_shot['effects'][3] = fadeout_count

                        if verbose:
                            # last_shot['effects'][2] = fadeout_count - last_shot['effects'][2]
                            print(f"->")
                            pprint(last_shot)

                else:
                    # Patch the last shot, add 'fadeout' effect
                    if verbose:
                        print(f"\tconsolidate_av_tracks: {k_ep}:{k_part}, patch the last shot -> fadeout: add effects")
                        pprint(db_video_part)
                    frame_no = last_shot['start'] + last_shot['count'] - 1
                    frame_loop_start = frame_no - fadeout_count + 1
                    nested_dict_set(last_shot,
                        ['fadeout', frame_loop_start, fadeout_count], 'effects')






def __consolidate_av_tracks_g_debut_fin(db, k_ep, k_part_g):
    """This function compares the audio and video tracks of a generique
    It aligns these 2 durations by:
    - adding silences
    - adding frames (loop, loop and fadeout)
    """
    if k_part_g not in ['g_debut', 'g_fin']:
        return

    # video and audio tracks
    db_video = db[k_part_g]['video']
    db_audio = db[k_part_g]['audio']

    # Verify that the nb of frames corresponds to the part duration
    shots = db_video['shots']
    if len(shots) == 1:
        if db_video['count'] != shots[0]['count']:
            sys.exit("consolidate_av_tracks : %s:%s todo: correct and remove this as this shall not occur: end" % (__name__, k_ep, k_part_g))

    # Get nb of frames for the video track
    video_count = 0
    for s in shots:
        video_count += s['count']
    if db_video['count'] != video_count:
        sys.exit("consolidate_av_tracks : error: %s:%s consolidate has not been done before: why?" % (__name__, k_ep, k_part_g))

    # Align video track to a multiple of seconds
    db_video['count'] = int(FPS * int(1 + db_video['count'] / FPS))
    if video_count != db_video['count']:
        db_video['silence'] = db_video['count'] - video_count


    # Get the duration in ms
    audio_duration = db_audio['duration']
    if 'avsync' in db_audio.keys():
        audio_duration += db_audio['avsync']
    if 'silence' in db_audio.keys():
        audio_duration += db_audio['silence']
    # print(f"audio duration: %.03fs" % (audio_duration/1000))
    # print(f"audio count: %d" % (ms_to_frames(audio_duration)))

    # Align audio track to a multiple of seconds
    rounded_audio_duration = 1000 * int(1 + float(audio_duration)/1000)
    audio_count = ms_to_frames(rounded_audio_duration)
    # print(f"rounded audio count: %d" % (audio_count))
    if frames_to_ms(audio_count) != audio_duration:
        db_audio['segments'].append({
            'start': 0,
            'end': 0,
            'silence': frames_to_ms(audio_count) - audio_duration
        })

    # Update audio duration and nb of frames
    db_audio['count'] = audio_count
    db_audio['duration'] = frames_to_ms(audio_count)


    # print(f"----------------- consolidate_av_tracks: AUDIO ------------------")
    # print(f"\tk_part_g=%s" % (k_part_g))
    # print(f"\t- audio_count=%d" % (db_audio['count']))
    # print(f"\t- audio_duration=%d" % (db_audio['duration']))
    # print(f"\t- video_count=%d" % (db_video['count']))

    # Align audio and video duration
    video_count = db_video['count']
    if audio_count > video_count:
        # Frames shall be added: use the loop effect for this
        last_shot = shots[-1]
        frame_no = last_shot['start'] + last_shot['count'] - 1
        # print(f"info: consolidate_av_tracks: %s: add video frames, video(%d) < audio (%d)" % (k_part_g, video_count, audio_count))
        loop_count = audio_count - video_count
        last_shot.update({'effects': ['loop_and_fadeout', frame_no, loop_count, min(loop_count, 25)]})
        db_video['count'] += loop_count

    elif video_count > audio_count:
        # Add silence to the audio track by adding a new segment
        # print(f"info: consolidate_av_tracks: %s: video(%d) > audio (%d)" % (k_part_g, video_count, audio_count))
        video_duration = frames_to_ms(video_count)
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
    #     print(f"info: consolidate_av_tracks: %s: video(%d) = audio (%d)" % (k_part_g, video_count, audio_count))



