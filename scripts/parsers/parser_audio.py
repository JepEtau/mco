# -*- coding: utf-8 -*-
from configparser import ConfigParser
from pprint import pprint
import re
import sys

from utils.common import K_PARTS
from utils.nested_dict import nested_dict_set
from utils.time_conversions import frames_to_ms
from utils.types import Audio


# TODO: refactoring, what are the differences between generique and other parts ?

def parse_audio_section_generique(db_audio:Audio, config:ConfigParser, k_section) -> None:
    # This function modifies the db_audio variable

    for k_option in config.options(k_section):
        value_str = config.get(k_section, k_option).replace(' ','')

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

        db_audio['segments'] = list()
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



def parse_audio_section(db_audio, config:ConfigParser, k_section) -> None:
    # This function modifies the db_audio variable

    for k_option in config.options(k_section):
        value_str = config.get(k_section, k_option).replace(' ','')

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

