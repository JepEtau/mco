# -*- coding: utf-8 -*-
import sys

import re
from pprint import pprint

from utils.common import (
    FPS,
    K_ALL_PARTS,
    K_NON_GENERIQUE_PARTS,
    K_PARTS,
    pprint_audio,
    pprint_video,
    nested_dict_set,
)
from utils.time_conversions import (
    frames_to_ms,
    ms_to_frames,
)


def parse_audio_section_generique(db_audio, config, verbose=False):
    k_section = 'audio'

    for k_option in config.options(k_section):
        value_str = config.get(k_section, k_option)
        value_str = value_str.replace(' ','')
        # print("%s, %s, %s => [%s]" % (k_section, part, k, value_str))

        # Source: edition and episode for the audio track
        if k_option == 'source':
            tmp = re.match(re.compile("([a-z_0-9]+):(ep[0-9]{2})"), value_str)
            if tmp is None:
                sys.exit("Error: wrong value for %s:%s [%s]" % (k_section, k_option, value_str))
            nested_dict_set(db_audio, {
                    'k_ed': tmp.group(1),
                    'k_ep': tmp.group(2),
                }, 'src')
            continue

        # Parse only supported sections
        if k_option not in ['g_debut', 'g_fin']:
            continue

        db_audio.update( {
            'segments': list()
        })
        duration = 0
        avsync = 0
        part_silence = 0
        segment_array = value_str.split()
        for segment_str in segment_array:
            properties = segment_str.split(',')

            # Start and end
            start_end = properties[0].split(':')
            if '.' in start_end[0]:
                start = int(1000 * float(start_end[0]))
            else:
                start = frames_to_ms(start_end[0])

            if '.' in start_end[1]:
                end = int(1000 * float(start_end[1]))
            else:
                end = frames_to_ms(start_end[1])

            # Duration
            d = end - start
            db_audio['segments'].append({
                'start': start,
                'end': end,
                'duration': d
            })
            duration += d

            # If other properties
            if len(properties) > 1:
                for i in range(1, len(properties)):

                    search_gain = re.search(re.compile("gain=([0-9.]+)"), properties[i])
                    if search_gain is not None:
                        gain = float(search_gain.group(1))
                        db_audio['segments'][-1]['gain'] = gain
                        continue

                    # The following will be considered as properties for the whole part
                    search_avsync = re.search(re.compile("avsync=([+-]?[0-9.]+)"), properties[i])
                    if search_avsync is not None:
                        avsync = int(1000 * float(search_avsync.group(1)))
                        continue

                    search_silence = re.search(re.compile("silence=([0-9.]+)"), properties[i])
                    if search_silence is not None:
                        part_silence = int(float(search_silence.group(1)) * 1000)
                        # frames_count += part_silence
                        continue

        # At this point, it is not possible to patch duration
        # and add silence (to the latest segment) to a multiple of frames
        # because we do not know the audio sample rate

        db_audio.update({
            'avsync': avsync,
            'silence': part_silence,
            'start': db_audio['segments'][0]['start'],
            'duration': duration,
            'end': db_audio['segments'][0]['start'] + d,
        })

    try:
        reference = db_audio['src']
    except:
        sys.exit("Error: missing source option in audio section for a generique")


def parse_audio_section(db_audio, config, verbose=False):
    k_section = 'audio'


    for k_option in config.options(k_section):
        value_str = config.get(k_section, k_option)
        value_str = value_str.replace(' ','')
        # print("%s, %s, %s => [%s]" % (k_section, part, k, value_str))

        if k_option == 'source':
            nested_dict_set(db_audio, value_str, 'src', 'k_ed')
            # print("detected source: %s" % (value_str))
            continue

        # Parse only supported sections
        if k_option not in K_PARTS:
            continue

        k_part = k_option
        db_audio[k_option] = {
            'segments': list()
        }

        part_fadein = 0
        part_fadeout = 0
        part_fadeout_alg = ''
        part_silence = 0
        duration = 0
        segment_array = value_str.split()
        for segment_str in segment_array:
            properties = segment_str.replace(' ', '').split(',')
            # print(properties)

            # Start and end
            start_end = properties[0].split(':')
            if '.' in start_end[0]:
                start = int(1000 * float(start_end[0]))
            else:
                start = frames_to_ms(start_end[0])

            if '.' in start_end[1]:
                end = int(1000 * float(start_end[1]))
            else:
                end = frames_to_ms(start_end[1])

            # Duration
            d = end - start
            db_audio[k_part]['segments'].append({
                'start': start,
                'end': end,
                'duration': d
            })
            duration += d

            # If other properties
            if len(properties) > 1:
                for i in range(1, len(properties)):
                    search_fadein = re.search(re.compile("fadein=([0-9.]+)"), properties[i])
                    if search_fadein is not None:
                        search_fadein = int(float(search_fadein.group(1)) * 1000)
                        continue

                    search_fadeout = re.search(re.compile("fadeout=([0-9.]+):?([a-z]*)"), properties[i])
                    if search_fadeout is not None:
                        part_fadeout = int(float(search_fadeout.group(1)) * 1000)
                        part_fadeout_alg = search_fadeout.group(2)
                        continue

                    search_silence = re.search(re.compile("silence=([0-9.]+)"), properties[i])
                    if search_silence is not None:
                        part_silence = int(float(search_silence.group(1)) * 1000)
                        # part_silence = int(float(search_silence.group(1)) * FPS)
                        # frames_count += part_silence
                        continue

                    search_k_ep_src = re.search(re.compile("src=([0-9]{1,2})"), properties[i])
                    if search_k_ep_src is not None:
                        k_ep_src = int(search_k_ep_src.group(1))
                        db_audio[k_part]['segments'][-1]['k_ep'] = 'ep%02d' % (k_ep_src)
                        continue
            else:
                k_ep_src = -1


        db_audio[k_part].update({
            'fadein': part_fadein,
            'fadeout': part_fadeout,
            'fade_alg': part_fadeout_alg,
            'silence': part_silence,
            'start': db_audio[k_part]['segments'][0]['start'],
            'duration': duration,
            'end': db_audio[k_part]['segments'][0]['start'] + d,
            'avsync': 0
        })

    # if db_audio['src']['k_ed'] == 's':
    #     print("detected another source")



def parse_video_section(db_video, config, k_ep, verbose=False):
    k_section = 'video'

    k_ed_ref = None
    k_ed_src = None
    for k_option in config.options(k_section):
        value_str = config.get(k_section, k_option)
        value_str = value_str.replace(' ','')
        # print("%s, %s => [%s]" % (k_section, k_option, value_str))

        if k_option == 'source':
            k_ed_src = value_str
            continue

        if k_option == 'ed_ref':
            k_ed_ref = value_str
            continue

        # Parse only supported sections
        if k_option not in K_PARTS:
            continue
        k_part = k_option

        part_fadein = 0
        part_fadeout = 0
        k_part_ed_src = None
        start = None
        end = -1

        # Walk through values
        properties = value_str.split(',')
        # print("\t%s:%s, properties:," % (k_ep, k_part), properties)
        for property in properties:

            search_start_end = re.search(re.compile("(\d+):(-?\d+)"), property)
            if search_start_end is not None:
                start = int(search_start_end.group(1))
                end = int(search_start_end.group(2))
                continue

            search_fadein = re.search(re.compile("fadein=([0-9.]+)"), property)
            if search_fadein is not None:
                search_fadein = int(float(search_fadein.group(1)) * FPS)
                continue

            search_fadeout = re.search(re.compile("fadeout=([0-9.]+)"), property)
            if search_fadeout is not None:
                part_fadeout = int(float(search_fadeout.group(1)) * FPS)
                continue

            search_k_ed_src = re.search(re.compile("ed=([a-z]+[0-9]*)"), property)
            if search_k_ed_src is not None:
                k_part_ed_src = search_k_ed_src.group(1)
                # sys.exit("found %s for %s:%s" % (k_part_ed_src, k_ep, k_part))
                continue

        # if start is None:
        #     sys.exit("Error: parse_video_section: start and end values are required for %s:%s in target file" % (k_ep, k_part))

        db_video[k_part] = {
            'effects': {
                'fadein': part_fadein,
                'fadeout': part_fadeout,
            },
            'start': start,
            'end': end,
            'count': (end - start) if end > 0 else -1,
            'k_ed_src': k_part_ed_src,
        }

    if k_ed_src is None:
        sys.exit("error: parse_video_section: missing key \'source\' in target file %s_target.ini" % (k_ep))

    for k_part in K_NON_GENERIQUE_PARTS:
        try:
            if db_video[k_part]['k_ed_src'] is None:
                db_video[k_part]['k_ed_src'] = k_ed_src
        except:
            pass


    for k_part in K_ALL_PARTS:
        if k_part not in db_video.keys():
            # The target will use the part defined in the src edition
            db_video[k_part] = {
                'k_ed_src': k_ed_src,
            }


    for k_part in K_NON_GENERIQUE_PARTS:
        if db_video[k_part]['k_ed_src'] is None:
            sys.exit("Errror: parse_video_section: edition shall be defined for %s:%s" % (k_ep, k_part))

    # Set the edition used as the reference for the frames no.
    db_video['k_ed_ref'] = k_ed_ref




def parser_consolidate_audio_video(db, k_ep):
    K_EP_DEBUG = ''

    db_common = db[k_ep]['common']

    if ('audio' not in db_common.keys()
    or 'video' not in db_common.keys()):
        return

    db_video = db_common['video']
    db_audio = db_common['audio']

    if k_ep == K_EP_DEBUG:
        print("<<<<<<<<<<<<<<<< parser_consolidate_audio_video ep=%s >>>>>>>>>>>>>>>>" % (k_ep))
        print(db_common.keys())
        print("<<<<<<<<<<<<<<<< VIDEO >>>>>>>>>>>>>>>>")
        pprint_video(db_video, ignore='shots', first_indent=4)
        print("<<<<<<<<<<<<<<<< AUDIO >>>>>>>>>>>>>>>>")
        pprint_audio(db_audio, first_indent=4)
        print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
        # sys.exit()

    # precedemment
    if 'precedemment' in db_audio.keys() and db_audio['precedemment']['duration'] != 0:
        avsync_ms = db_audio['precedemment']['start'] - frames_to_ms(db_video['precedemment']['start'])
        db_video['precedemment']['avsync'] = ms_to_frames(avsync_ms)
        db_audio['precedemment']['avsync'] = avsync_ms


    # episode
    if 'precedemment' in db_audio.keys() and db_audio['precedemment']['duration'] != 0:
        # Warning if avsync is specified in audio config, this will not work unless correct this
        audio_avsync_ms = (db_audio['episode']['start']
            - (db_audio['precedemment']['start'] + db_audio['precedemment']['duration']))
        db_audio['episode']['avsync'] = audio_avsync_ms

        video_avsync = (db_video['episode']['start']
            - (db_video['precedemment']['start'] + db_video['precedemment']['count']))
        db_video['episode']['avsync'] = video_avsync

        if db_video['episode']['start'] != db_video['episode']['shots'][0]['start']:
            sys.exit("parser_consolidate_audio_video: error: start of episode (%d) != start of 1st shot (%d)" % (
                db_video['episode']['start'], db_video['shots']['start']))
    else:
        avsync_ms = 0
        db_video['episode']['avsync'] = ms_to_frames(avsync_ms)
        db_audio['episode']['avsync'] = avsync_ms

    # g_asuivre
    k_part_g = 'g_asuivre'
    audio_count = ms_to_frames(db_audio[k_part_g]['duration'])
    db_video[k_part_g] = {
        'start': 0,
        'end': audio_count,
        'count': audio_count,
        'avsync': 0,
    }
    db_audio[k_part_g]['avsync'] = 0


    # asuivre
    if 'asuivre' in db_audio.keys() and db_audio['asuivre']['duration'] != 0:
        avsync_ms = db_audio['asuivre']['start'] - frames_to_ms(db_video['asuivre']['start'])
        db_video['asuivre']['avsync'] = ms_to_frames(avsync_ms)
        db_audio['asuivre']['avsync'] = avsync_ms

    # g_reportage
    k_part_g = 'g_reportage'
    audio_count = ms_to_frames(db_audio[k_part_g]['duration'])
    audio_start = ms_to_frames(db_audio[k_part_g]['start'])
    db_audio[k_part_g]['count'] = audio_count
    db_video[k_part_g] = {
        'start': audio_start,
        'end': audio_start + audio_count,
        'count': audio_count,
        'avsync': 0
    }

    # reportage: no a/v sync
    # avsync_ms = db_audio['reportage']['start'] - frames_to_ms(db_video['reportage']['start'])
    avsync_ms = 0
    db_video['reportage']['avsync'] = ms_to_frames(avsync_ms)
    db_audio['reportage']['avsync'] = avsync_ms


    # Update count
    for kp in K_PARTS:
        if kp == 'g_reportage':
            continue
        db_audio[kp]['count'] = ms_to_frames(db_audio[kp]['end'] - db_audio[kp]['start'])

    if k_ep == K_EP_DEBUG:
        print("--------------- Consolidated ----------------------- ")
        print("<<<<<<<<<<<<<<<< VIDEO (after consolidation) >>>>>>>>>>>>>>>>")
        pprint_video(db_video, ignore='shots', first_indent=4)
        print("<<<<<<<<<<<<<<<< AUDIO (after consolidation) >>>>>>>>>>>>>>>>")
        pprint_audio(db_audio, first_indent=4)
        # sys.exit()

