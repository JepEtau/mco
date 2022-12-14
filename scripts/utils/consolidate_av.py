# -*- coding: utf-8 -*-
import sys
from copy import deepcopy
from pprint import pprint

from utils.common import (
    FPS,
    pprint_audio,
    pprint_video
)
from utils.time_conversions import frames_to_ms, ms_to_frames



def align_audio_video_durations_g_debut_fin(db, k_ep, k_part_g):
    """This function compares the audio and video tracks of a generique
    It aligns these 2 durations by:
    - adding silences
    - adding frames (loop, loop and fadeout)
    """
    # print("%s.align_audio_video_durations_g_debut_fin: %s:%s" % (__name__, k_ep, k_part_g))

    if k_part_g not in ['g_debut', 'g_fin']:
        return

    # video and audio tracks
    db_video = db[k_part_g]['target']['video']
    db_audio = db[k_part_g]['target']['audio']

    shots = db_video['shots']

    if len(shots) == 1:
        if db_video['count'] != shots[0]['count']:
            sys.exit("%s.align_audio_video_durations_g_debut_fin : %s:%s todo: correct and remove this as this shall not occur: end" % (__name__, k_ep, k_part_g))

    # Get the duration in ms
    if k_part_g in db_audio.keys():
        audio_duration = db_audio[k_part_g]['duration']
        print("Warning: %s:align_audio_video_durations_g_debut_fin : correct this!!!" % (__name__))
    elif 'duration' in db_audio.keys():
        audio_duration = db_audio['duration']

    video_count = 0
    for s in shots:
        video_count += s['count']
    if db_video['count'] != video_count:
        sys.exit("%s.align_audio_video_durations_g_debut_fin : error: %s:%s consolidate has not been done before: why?" % (__name__, k_ep, k_part_g))


    # Use avsync for audio duration:
    if 'avsync' in db_audio.keys():
        audio_duration += db_audio['avsync']

    # Patch silence to a multiple of frames
    if 'silence' in db_audio.keys():
        silence_duration = db_audio['silence']
        silence_count_rounded = float(int((silence_duration * FPS / 1000) + 0.5))
        # silence_count_float = (silence_duration * FPS / 1000)
        # print("silence_count_rounded=%f" % (silence_count_rounded))
        # print("silence_count_float=%f" % (silence_count_float))
        db_audio['silence'] = int(silence_count_rounded * 1000 / FPS)


    audio_count = ms_to_frames(db_audio['duration'])
    # print("----------------- align_audio_video_durations_g_debut_fin: AUDIO ------------------")
    # pprint(db_audio)
    # sys.exit()

    # patch audio duration to a multiple of 1000/FPS ms
    audio_count_rounded = float(int((audio_duration * FPS / 1000) + 0.5))
    audio_count_float = (audio_duration * FPS / 1000)
    # print("audio_count_rounded=%f" % (audio_count_rounded))
    # print("audio_count_float=%f" % (audio_count_float))
    if audio_count_float != audio_count_rounded:
        # Add silence to the latest segment
        s = db_audio['segments'][-1]
        silence = int(((audio_count_rounded - audio_count_float) * 1000 / FPS) + 0.5)
        if 'segments' in s.keys():
            s['silence'] += silence
        else:
            s['silence'] = silence
        db_audio['duration'] = int(audio_count_rounded * 1000 / FPS)
        audio_count = audio_count_rounded
    db_audio['count'] = audio_count

    # print("\tk_part_g=%s" % (k_part_g))
    # print("\t- audio_count=%d" % (audio_count))
    # print("\t- video_count=%d" % (db_video['count']))

    if audio_count > video_count:
        # Frames shall be added: use the loop effect for this
        last_shot = shots[-1]
        frame_no = last_shot['start'] + last_shot['count'] - 1
        print("info: %s:align_audio_video_durations_g_debut_fin: add video frames, video(%d) < audio (%d)" % (__name__, video_count, audio_count))
        loop_count = int(audio_count - video_count)
        last_shot.update({'effects': ['loop_and_fadeout', frame_no, loop_count, min(loop_count, 25)]})
        db_video['count'] = db_audio['count']

    elif video_count > audio_count:
        # Add silence to the audio track by adding a new segment
        video_duration = int(video_count * 1000 / FPS)
        audio_duration = db_audio['duration']
        db_audio['segments'].append({
            'start': 0,
            'end': 0,
            'silence': video_duration - audio_duration,
        })
        db_audio['count'] = db_video['count']
        print("info: %s:align_audio_video_durations_g_debut_fin: video(%d) > audio (%d)" % (__name__, video_count, audio_count))


def calculate_av_sync(db, k_ep):
    K_EP_DEBUG = ''
    db_target = db[k_ep]['target']

    if ('audio' not in db_target.keys()
        or 'video' not in db_target.keys()):
        sys.exit("%s.calculate_av_sync: error, audio or video does not exist in %s:common" % (__name__, k_ep))
        return
    db_video = db_target['video']
    db_audio = db_target['audio']

    # precedemment
    k_part = 'precedemment'
    if k_part in db_audio.keys() and db_audio[k_part]['duration'] != 0:
        # precedemment
        avsync_ms = frames_to_ms(db_video[k_part]['start']) - db_audio[k_part]['start']
        db_video[k_part]['avsync'] = ms_to_frames(avsync_ms) if avsync_ms > 0 else 0
        db_audio[k_part].update({
            'avsync': avsync_ms if avsync_ms < 0 else 0,
            'count': ms_to_frames(db_audio[k_part]['end'] - db_audio[k_part]['start']),
        })

        # episode
        k_part = 'episode'
        audio_avsync_ms = (db_audio[k_part]['start']
            - (db_audio['precedemment']['start'] + db_audio['precedemment']['duration']))
        db_audio[k_part].update({
            'avsync': audio_avsync_ms,
            'count': ms_to_frames(db_audio[k_part]['end'] - db_audio[k_part]['start'])
        })

        video_avsync = (db_video[k_part]['start']
                        - (db_video['precedemment']['start'] + db_video['precedemment']['count']))
        db_video[k_part]['avsync'] = video_avsync

        if db_video['episode']['start'] != db_video['episode']['shots'][0]['start']:
            sys.exit("calculate_av_sync: error: start of episode (%d) != start of 1st shot (%d)" % (
                db_video['episode']['start'], db_video[k_part]['shots'][0]['start']))
    else:
        # precedemment does not exist
        db_target['audio']['precedemment'].update({
            'avsync': 0,
            'count': 0,
        })
        db_target['video']['precedemment'].update({
            'avsync': 0,
            'count': 0,
        })

        # episode
        k_part = 'episode'
        avsync_ms = db_audio[k_part]['start'] - frames_to_ms(db_video[k_part]['start'])
        db_video[k_part].update({
            'avsync': ms_to_frames(avsync_ms) if avsync_ms < 0 else 0
        })
        db_audio[k_part].update({
            'avsync': avsync_ms if avsync_ms > 0 else 0,
        })


    k_part = 'asuivre'
    if k_part in db_audio.keys() and db_audio[k_part]['duration'] != 0:
        # g_asuivre
        k_part_g = 'g_asuivre'
        audio_count = ms_to_frames(db_audio[k_part_g]['duration'])
        db_video[k_part_g].update({
            'start': 0,
            # 'count': audio_count,
            'avsync': 0,
        })

        db_audio[k_part_g].update({
            'avsync': 0,
            'count': ms_to_frames(db_audio[k_part_g]['end'] - db_audio[k_part_g]['start'])
        })

        # asuivre
        db_video[k_part]['avsync'] = 0
        audio_count = ms_to_frames(db_audio[k_part]['duration'])
        db_audio[k_part].update({
            'avsync': 0,
            'count': audio_count
        })
    else:
        db_video[k_part]['count'] = 0
        db_audio[k_part]['count'] = 0


    # g_reportage
    k_part_g = 'g_reportage'
    audio_count = ms_to_frames(db_audio[k_part_g]['duration'])
    db_audio[k_part_g].update({
        'count': audio_count,
        'avsync': 0
    })
    db_video[k_part_g].update({
        'start': 0,
        # 'count': audio_count,
        'avsync': 0
    })

    # reportage
    k_part = 'reportage'
    db_video[k_part]['avsync'] = 0
    db_audio[k_part].update({
        'avsync': 0,
        # 'count': ms_to_frames(db_audio[k_part]['duration'])
    })

    if k_ep == K_EP_DEBUG:
        print("<<<<<<<<<<<<<<<< calculate_av_sync ep=%s >>>>>>>>>>>>>>>>" % (k_ep))
        print(db_target.keys())
        print("<<<<<<<<<<<<<<<< VIDEO >>>>>>>>>>>>>>>>")
        pprint_video(db_video, ignore='shots', first_indent=4)
        print("<<<<<<<<<<<<<<<< AUDIO >>>>>>>>>>>>>>>>")
        pprint_audio(db_audio, first_indent=4)
        print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")



def align_audio_video_durations(db, k_ep):
    K_EP_DEBUG = ''
    db_target = db[k_ep]['target']

    if ('audio' not in db_target.keys()
        or 'video' not in db_target.keys()):
        sys.exit("%s.align_audio_video_durations: error, audio or video does not exist in %s:common" % (__name__, k_ep))
        return
    db_video = db_target['video']
    db_audio = db_target['audio']

    if k_ep == K_EP_DEBUG:
        print("%s.align_audio_video_durations: %s:common" % (__name__, k_ep))
        pprint(db_audio)

    # g_asuivre
    #---------------------------------------------------------------------------
    # Update the shot with the duration that is calculated in the audio structure
    k_part_g = 'g_asuivre'
    last_shot = db_video[k_part_g]['shots'][-1]
    last_shot['effects'] = [
        'loop',
        last_shot['start'] + last_shot['count'] - 1,
        db_audio[k_part_g]['count'] - 1]


    # g_reportage
    #---------------------------------------------------------------------------
    # Update the shot with the duration that is calculated in the audio structure
    k_part_g = 'g_reportage'
    last_shot = db_video[k_part_g]['shots'][-1]
    if db_audio[k_part_g]['count'] > db_video[k_part_g]['count']:
        # loop on last frame
        loop_start = last_shot['start'] + last_shot['count'] - 1
        loop_count = db_audio[k_part_g]['count'] - db_video[k_part_g]['count']
        # print("%s: loop on last frame (%d): %d frames" % (k_part_g, loop_start, loop_count))
        last_shot['effects'] = ['loop', loop_start, loop_count]
    elif db_video[k_part_g]['count'] > db_audio[k_part_g]['count']:
        # remove some frames
        # print("%s: remove %d frames" % (k_part_g, db_video[k_part_g]['count'] - db_audio[k_part_g]['count']))
        last_shot['count'] -= db_video[k_part_g]['count'] - db_audio[k_part_g]['count']
    db_video[k_part_g]['count'] = db_audio[k_part_g]['count']


    # precedemment+episode, asuivre, reportage
    #---------------------------------------------------------------------------
    for k_part in ['episode', 'asuivre', 'reportage']:
        # Calculate audio duration
        audio_duration = db_audio[k_part]['avsync'] + db_audio[k_part]['duration']

        if k_part == 'episode':
            # Add precedemment
            audio_duration += (db_audio['precedemment']['avsync'] + db_audio['precedemment']['duration'])

        # Round audio count to a multiple of 1000/FPS ms
        audio_count = ms_to_frames(audio_duration)
        audio_count_rounded = float(int((audio_duration * FPS / 1000) + 0.5))
        audio_count_float = (audio_duration * FPS / 1000)
        # print("%s:" % (k_part))
        # print("\taudio_count_rounded=%f" % (audio_count_rounded))
        # print("\taudio_count_float=%f" % (audio_count_float))
        if audio_count_float != audio_count_rounded:
            sys.exit("%s.align_audio_video_durations: correct or remove this (add an audio segment), %s:%" % (k_ep, k_part))
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
            print ("%s.align_audio_video_durations: %s:%s: add a silence to round the audio duration: %d" % (__name__, k_ep, k_part, silence))

        # Modify the real audio count to this new duration
        if k_part == 'episode':
            # this is a special case for episode: precedemment+episode
            # print("   rounded audio count episode+precedemment: %d" % (audio_count))
            db_audio[k_part]['count'] = audio_count - ms_to_frames(db_audio['precedemment']['duration'])
            video_count = (db_video['precedemment']['count'] + db_video['precedemment']['avsync']
                            + db_video[k_part]['count'] + db_video[k_part]['avsync'])
        else:
            db_audio[k_part]['count'] = audio_count
            video_count = db_video[k_part]['count'] + db_video[k_part]['avsync']

        # print("info: %s:align_audio_video_durations: %s:%s: video=%d, audio=%d" % (__name__, k_ep, k_part, video_count, audio_count))
        last_shot = db_video[k_part]['shots'][-1]

        if audio_count > video_count:
            # Frames shall be added: use the loop (and fadeout) effect for this
            # print("info: %s:align_audio_video_durations: %s:%s: add video frames, video(%d) < audio (%d)" % (__name__, k_ep, k_part, video_count, audio_count))

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
            # print("info: %s:align_audio_video_durations:  %s:%s: add audio, video(%d) > audio (%d)" % (__name__, k_ep, k_part, video_count, audio_count))

            video_duration = int(video_count * 1000 / FPS)
            audio_duration = db_audio[k_part]['duration']
            db_audio[k_part]['segments'].append({
                'start': 0,
                'end': 0,
                'silence': video_duration - audio_duration,
            })
            db_audio[k_part]['count'] = db_video[k_part]['count']
            # print("-> added silence at the end")


    # Add/modify effect of the last shot
    #---------------------------------------------------------------------------
    for k_part in ['episode', 'asuivre', 'reportage']:
        db_video_part = db_video[k_part]
        last_shot = db_video_part['shots'][-1]

        if 'effects' in db_video_part.keys():
            # print("effects detected in %s:%s" % (k_ep, k_part))
            # pprint(db_video_part['effects'])

            if db_video_part['effects']['fadein'] != 0:
                sys.exit("%s.align_audio_video_durations: Error: TODO: %s:%s fadein effect in db_video!!!!" % (__name__, k_ep, k_part))

            if db_video_part['effects']['fadeout'] != 0:
                # print("%s.align_audio_video_durations: %s:%s modify fadeout effect in db_video!" % (__name__, k_ep, k_part))

                fadeout_count = db_video_part['effects']['fadeout']
                if 'effects' in last_shot.keys():
                    # Patch the fadeout/loop_and_fadeout duration
                    if last_shot['effects'][0] == 'fadeout':
                        # print("%s.align_audio_video_durations: %s:%s, patch the last shot -> fadeout: modify" % (__name__, k_ep, k_part))
                        last_shot['effects'][2] = fadeout_count

                    elif last_shot['effects'][0] == 'loop_and_fadeout':
                        # print("%s.align_audio_video_durations: %s:%s, patch the last shot -> loop_and_fadeout: modify" % (__name__, k_ep, k_part))
                        # print("\t%d vs %d" % (last_shot['effects'][3], fadeout_count))
                        # pprint(last_shot)
                        if fadeout_count < last_shot['count']:
                            # Modify it because shot duration > fadeout duration
                            last_shot['effects'][3] = fadeout_count
                        # last_shot['effects'][2] = fadeout_count - last_shot['effects'][2]
                        # print("->")
                        # pprint(last_shot)

                else:
                    # Patch the last shot, add 'fadeout' effect
                    # print("\n%s.align_audio_video_durations: %s:%s, patch the last shot -> fadeout: add effects" % (__name__, k_ep, k_part))
                    if 'src' in last_shot.keys() and last_shot['src']['use']:
                        frame_no = last_shot['src']['start'] + last_shot['src']['count'] - 1
                        last_shot['src']['count'] -= fadeout_count
                    else:
                        frame_no = last_shot['start'] + last_shot['count'] - 1

                    last_shot.update({
                        'effects': ['fadeout', frame_no-fadeout_count, fadeout_count],
                    })

    return



