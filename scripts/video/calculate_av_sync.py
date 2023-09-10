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


def calculate_av_sync(db, k_ep):
    verbose = True

    if ('audio' not in db[k_ep].keys()
        or 'video' not in db[k_ep].keys()):
        sys.exit("calculate_av_sync: error, audio or video does not exist in %s:common" % (__name__, k_ep))
        return
    db_video = db[k_ep]['video']['target']
    db_video_target = db[k_ep]['video']['target']
    db_audio = db[k_ep]['audio']

    if verbose:
        print_lightcyan(f"Calculate AV sync")


    # precedemment
    k_part = 'precedemment'
    db_audio['precedemment']['avsync'] = 0
    db_audio['episode']['avsync'] = 0
    db_video_target['precedemment']['avsync'] = 0
    db_video_target['episode']['avsync'] = 0

    if k_part in db_audio.keys() and db_audio[k_part]['duration'] != 0:
        # edition used as the src for the audio track

        k_ed_audio_src = db_audio['src']['k_ed']
        # if verbose:
        #     print_lightcyan(f"db_audio[{k_part}]:")
        #     pprint(db_audio[k_part])
        #     print_lightcyan(f"db_video {k_ed_src}:{k_part}:")
        #     pprint(db[k_ep]['video'][k_ed_src][k_part])
        #     print_lightcyan(f"db_video target:{k_part}:")
        #     pprint(db[k_ep]['video']['target'][k_part])

        # Compare video count from audio_src and target

        try:
            precedemment_video_count = (db[k_ep]['video'][k_ed_audio_src]['episode']['shots'][1]['start']
                            - db[k_ep]['video'][k_ed_audio_src]['precedemment']['shots'][1]['start'])
            precedemment_target_video_count = (db_video_target['episode']['shots'][1]['start']
                            - db_video_target['precedemment']['shots'][1]['start'])
        except:
            pprint(db[k_ep]['video'].keys())
            sys.exit(f"{k_ep}:{k_part}: video shots are not defined. They are required to calculate AV sync values.")
        if verbose:
            print_lightgrey(f"\tprecedemment to episode:")
            print_lightgrey(f"\t\tvideo count ({k_ed_audio_src}): {precedemment_video_count}")
            print_lightgrey(f"\t\tvideo count (target): {precedemment_target_video_count}")
        if precedemment_video_count != precedemment_target_video_count:
            print(yellow(f"\twarning: precedemment to episode: erroneous frame count between {k_ed_audio_src} and target"))


        # Ensure episode durations are the same
        episode_src_count = (db[k_ep]['video'][k_ed_audio_src]['episode']['shots'][-1]['start']
            - db[k_ep]['video'][k_ed_audio_src]['episode']['shots'][1]['start'])

        episode_target_count = 0
        for shot in db_video_target['episode']['shots'][1:-1]:
            episode_target_count += shot['dst']['count']

        avsync_episode = 0
        if episode_src_count != episode_target_count:
            # ep: 2, 13, 22
            print(red(f"\twarning: target vs source: erroneous frame count:"),
                    f"target: {episode_target_count}, src ({k_ed_audio_src}): {episode_src_count}")
            sys.exit()
            avsync_episode = episode_target_count - episode_src_count


        # synchronize episode, use the 2nd video shot

        # offset: target -> src (use audio track)
        # offset = src - target
        offset_src_to_target = (db_video_target['episode']['shots'][1]['start']
            - db[k_ep]['video'][k_ed_audio_src]['episode']['shots'][1]['start'])

        # audio start in target referentiel
        precedemment_audio_start = ms_to_frames(db_audio['precedemment']['start']) + offset_src_to_target

        # Precedemment: let's set the 1st frame of video aligned with the audio start
        db_video_target['precedemment']['avsync'] = 0

        # We moved the precedemment part, calculate new silence between precedemment and episode
        precedemment_video_count = db_video_target['precedemment']['count']
        episode_video_start = db_video_target['episode']['shots'][0]['start']
        video_silence = (episode_video_start
            - (precedemment_audio_start + precedemment_video_count))

        precedemment_audio_count = ms_to_frames(db_audio['precedemment']['duration'])

        print(f"k_ed_audio_src: {k_ed_audio_src}")
        print(f"\toffset: {offset_src_to_target}")
        print(f"\tprecedemment_audio_start: {precedemment_audio_start}")
        print(f"\tprecedemment_video_count: {precedemment_video_count}")

        print(f"\tprecedemment_video_count: {precedemment_video_count}")

        print(f"\tepisode_video_start: {episode_video_start}")
        print(f"\tprecedemment, audio_count: {precedemment_audio_count}")

        print(f"\tvideo_silence: {video_silence}")


        last_shot_precedemment:Shot = db_video_target['precedemment']['shots'][-1]
        first_shot_episode:Shot = db_video_target['episode']['shots'][0]
        print(f"\tlast_shot_precedemment: end: {last_shot_precedemment['start'] + last_shot_precedemment['dst']['count']}")
        print(f"\tfirst_shot_episode: start: {first_shot_episode['start']}")

        if video_silence < 0:
            # overlap
            print(p_lightgreen(f"precedemment to episode: remove {abs(video_silence)} frames"))
            video_silence = abs(video_silence)

            if precedemment_audio_count > precedemment_video_count:
                # Remove frames from episode
                # fr: ep no. 19
                # fadein to do
                # ep26 (99 frames)?????
                # validated (2023-08-28): 19
                print(f"\tepisode: remove {abs(video_silence)} frames")
                first_shot_episode['start'] += video_silence
                first_shot_episode['count'] -= video_silence
                first_shot_episode['dst']['count'] -= video_silence
                db_video_target['episode']['count'] -= video_silence
            else:
                # Remove frames from precedemment
                # fr: ep no. 14, 36
                # validated (2023-08-26): 14, 36
                # TODO: Improve: ep14, use fadeout
                # validated (2023-09-07): 3,
                print(f"\tprecedemment: remove {abs(video_silence)} frames")
                last_shot_precedemment['count'] -= video_silence
                last_shot_precedemment['dst']['count'] -= video_silence
                db_video_target['precedemment']['count'] -= video_silence

        elif video_silence > 0:
            # Add silence between precedemment and episode
            print(p_lightgreen(f"precedemment to episode: add video silence: {abs(video_silence)} frames"))

            if precedemment_audio_count > precedemment_video_count:
                # fr: ep no. 6, 7, 8, 9, 10, 11, 12, 13, 15, 16, 17, 18,
                #               20, 21, 22, 23, 24, 25, 26, 27, 28, 29,
                #               30, 31, 32, 34, 35, 37, 38, 39
                # validated (2023-09-07): 4, 5,
                print(f"\tprecedemment: loop and fadeout")
                av_diff = precedemment_audio_count - precedemment_video_count

                print(f"\tav_diff : {precedemment_audio_count - precedemment_video_count}")
                if av_diff <= video_silence:
                    print_purple("no need to revalidate")

                    # Add loop_and_fadeout to precedemment up to end of audio
                    loop_count = precedemment_audio_count - precedemment_video_count
                    loop_start = (last_shot_precedemment['start']
                        + last_shot_precedemment['count'] - 1)
                    last_shot_precedemment.update({
                        'effects': ['loop_and_fadeout', loop_start, loop_count, loop_count]})
                    db_video_target['precedemment']['count'] += loop_count

                    # If the amount of added frames were not enough
                    if loop_count < video_silence:
                        # Add silence at the beginning of the episode or fade_in
                        loop_count = video_silence - loop_count
                        nested_dict_set(db_video['episode'], loop_count, 'effects', 'loop_and_fadein')
                        db_video_target['episode']['count'] += loop_count
                else:
                    # Add loop_and_fadeout to precedemment up to end of audio
                    # fr: ep no. 6, 7, 8

                    loop_count = video_silence
                    loop_start = (last_shot_precedemment['start']
                        + last_shot_precedemment['count'] - 1)
                    last_shot_precedemment.update({
                        'effects': ['loop_and_fadeout', loop_start, loop_count, loop_count]})
                    db_video_target['precedemment']['count'] += loop_count

                    print_purple(f"loop_count: {loop_count}")

                    # # If the amount of added frames were not enough
                    # if loop_count < video_silence:
                    #     # Add silence at the beginning of the episode or fade_in
                    #     loop_count = video_silence - loop_count
                    #     nested_dict_set(db_video['episode'], loop_count, 'effects', 'loop_and_fadein')
                    #     db_video_target['episode']['count'] += loop_count


                    print_yellow("warning: silence is not enough")

                    # sys.exit()


            else:
                print(f"\tTODO: episode: loop and fadein")
                sys.exit()

        else:
            # No modifications
            # fr: ep no. 2
            # validated (2023-08-25): 02
            print(p_lightgreen(f"precedemment to episode: no modification"))


        if avsync_episode > 0:
            print(f"\tepisode: remove {abs(avsync_episode)} frames")
            # !!! ep13: ok to remove from 1st shot
            first_shot_episode['start'] += avsync_episode
            first_shot_episode['count'] -= avsync_episode
            first_shot_episode['dst']['count'] -= avsync_episode
            db_video_target['episode']['count'] -= avsync_episode
        elif avsync_episode < 0:
            sys.exit(f"TODO: avsync: {avsync_episode}, add frames/shots")
        # if db_video['episode']['start'] != db_video['episode']['shots'][0]['start']:
        #     sys.exit("calculate_av_sync: error: start of episode (%d) != start of 1st shot (%d)" % (
        #         db_video['episode']['start'], db_video[k_part]['shots'][0]['start']))

    else:
        # precedemment does not exist
        db_audio['precedemment']['avsync'] = 0
        db_video_target['precedemment'].update({
            'avsync': 0,
            'count': 0,
        })

        # episode
        k_part = 'episode'

        # Get the start frame no. from the src ed.
        k_ed_src = db_audio['src']['k_ed']
        video_start = db[k_ep]['video'][k_ed_src][k_part]['start']

        avsync_ms = db_audio[k_part]['start'] - frames_to_ms(video_start)
        # db_video[k_part].update({
        #     'avsync': ms_to_frames(abs(avsync_ms)) if avsync_ms < 0 else 0
        # })
        if avsync_ms > 0:
            db_video[k_part]['avsync'] = 0
            db_audio[k_part]['avsync'] = abs(avsync_ms)
        else:
            # missing video frames, use fade_in
            loop_count = ms_to_frames(abs(avsync_ms))
            nested_dict_set(db_video[k_part], loop_count, 'effects', 'loop_and_fadein')
            db_video[k_part]['count'] += loop_count

        print("calculate_av_sync:")
        print(f"\tavsync_ms: {avsync_ms}")

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
        db_video_target['g_asuivre'].update({
            'avsync': 0,
            'count': 0,
        })
        db_video_target[k_part].update({
            'avsync': 0,
            'count': 0,
        })

        db_audio['g_asuivre'].update({
            'avsync': 0,
            'count': 0,
        })
        db_audio[k_part].update({
            'avsync': 0,
            'count': 0,
        })

    # g_documentaire
    k_part_g = 'g_documentaire'
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

    # documentaire
    k_part = 'documentaire'
    db_video[k_part]['avsync'] = 0
    db_audio[k_part].update({
        'avsync': 0,
        # 'count': ms_to_frames(db_audio[k_part]['duration'])
    })

    # TODO remove the above modification of frames count once frame count is validate
    # Recalculte video count
    for k_part in K_PARTS_ORDERED:
        print(f"{k_part}")
        print(f"\tcurrent: {db_video[k_part]['count']}")

