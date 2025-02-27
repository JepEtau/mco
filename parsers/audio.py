from __future__ import annotations
from configparser import ConfigParser
from pprint import pprint
import re
import sys
from ._keys import (
    ep_key,
    main_chapter_keys
)
from .helpers import(
    nested_dict_set,
    get_frame_rate,
)
from ._db import db
from utils.time_conversions import frame_to_ms
from utils.p_print import *
from utils.mco_types import AudioSrc, ChapterAudio

# TODO: refactoring, what are the differences between generique and other chapters ?

def parse_audio_g(
    ch_audio: ChapterAudio,
    config: ConfigParser,
    k_section: str,
) -> None:
    # This function update the audio section
    fps = get_frame_rate()

    for k_option in config.options(k_section):
        value_str = config.get(k_section, k_option).replace(' ','')

        # Source: edition and episode for the audio track
        if k_option == 'source':
            tmp = re.search(re.compile(r"([a-z_0-9]+):(ep[0-9]{2})"), value_str)
            if tmp is None:
                sys.exit(red(f"Error: wrong value for {k_section}:{k_option} [{value_str}]"))
            ch_audio['src'] = AudioSrc(k_ed=tmp.group(1), k_ep=tmp.group(2))
            continue

        # Parse only supported sections
        if k_option not in ('g_debut', 'g_fin'):
            continue

        ch_audio['segments'] = []
        duration = 0
        avsync = 0
        chapter_silence = 0
        segment_array = value_str.split()
        for segment_str in segment_array:
            properties = segment_str.split(',')

            # Start and end
            start_end = properties[0].split(':')
            if '.' in start_end[0]:
                start = int(1000 * float(start_end[0]))
            else:
                start = frame_to_ms(start_end[0], fps)

            if '.' in start_end[1]:
                end = int(1000 * float(start_end[1]))
            else:
                end = frame_to_ms(start_end[1], fps)

            # Duration
            d = end - start
            ch_audio['segments'].append({
                'start': start,
                'end': end,
                'duration': d
            })
            duration += d

            # If other properties
            if len(properties) > 1:
                for i in range(1, len(properties)):

                    search_gain = re.search(re.compile(r"gain=([0-9.]+)"), properties[i])
                    if search_gain is not None:
                        gain = float(search_gain.group(1))
                        ch_audio['segments'][-1]['gain'] = gain
                        continue

                    # The following will be considered as properties for the whole chapter
                    search_avsync = re.search(re.compile(r"avsync=([+-]?[0-9.]+)"), properties[i])
                    if search_avsync is not None:
                        avsync = int(1000 * float(search_avsync.group(1)))
                        continue

                    search_silence = re.search(re.compile(r"silence=([0-9.]+)"), properties[i])
                    if search_silence is not None:
                        chapter_silence = int(float(search_silence.group(1)) * 1000)
                        # frames_count += chapter_silence
                        continue

        # At this point, it is not possible to patch duration
        # and add silence (to the latest segment) to a multiple of frames
        # because we do not know the audio sample rate

        ch_audio.update({
            'avsync': avsync,
            'silence': chapter_silence,
            'start': ch_audio['segments'][0]['start'],
            'duration': duration,
            'end': ch_audio['segments'][0]['start'] + d,
        })

    try:
        reference = ch_audio['src']
    except:
        raise ValueError("Error: missing source option in audio section for a generique")



def parse_audio_section(
    db: dict,
    episode: str | int,
    config: ConfigParser,
    k_section: str,
) -> None:
    k_ep = ep_key(episode)
    db_audio = db[k_ep]['audio']
    fps: float = get_frame_rate()

    for k_option in config.options(k_section):
        value_str = config.get(k_section, k_option).replace(' ','')

        if k_option == 'source':
            nested_dict_set(db_audio, keys=('src', 'k_ed'), o=value_str)
            # print("detected source: %s" % (value_str))
            continue

        # Parse only supported sections
        if k_option not in main_chapter_keys():
            continue

        k_ch = k_option
        db_audio[k_option] = {
            'segments': list()
        }

        chapter_fadein = 0
        chapter_fadeout = 0
        chapter_fadeout_alg = ''
        chapter_silence = 0
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
                start = frame_to_ms(start_end[0], fps)

            if '.' in start_end[1]:
                end = int(1000 * float(start_end[1]))
            else:
                end = frame_to_ms(start_end[1], fps)

            # Duration
            d = end - start
            db_audio[k_ch]['segments'].append({
                'start': start,
                'end': end,
                'duration': d
            })
            duration += d

            # If other properties
            if len(properties) > 1:
                for i in range(1, len(properties)):
                    search_fadein = re.search(re.compile(r"fadein=([0-9.]+)"), properties[i])
                    if search_fadein is not None:
                        search_fadein = int(float(search_fadein.group(1)) * 1000)
                        continue

                    search_fadeout = re.search(re.compile(r"fadeout=([0-9.]+):?([a-z]*)"), properties[i])
                    if search_fadeout is not None:
                        chapter_fadeout = int(float(search_fadeout.group(1)) * 1000)
                        chapter_fadeout_alg = search_fadeout.group(2)
                        continue

                    search_silence = re.search(re.compile(r"silence=([0-9.]+)"), properties[i])
                    if search_silence is not None:
                        chapter_silence = int(float(search_silence.group(1)) * 1000)
                        # chapter_silence = int(float(search_silence.group(1)) * fps)
                        # frames_count += chapter_silence
                        continue

                    search_k_ep_src = re.search(re.compile(r"src=([0-9]{1,2})"), properties[i])
                    if search_k_ep_src is not None:
                        k_ep_src = int(search_k_ep_src.group(1))
                        db_audio[k_ch]['segments'][-1]['k_ep'] = 'ep%02d' % (k_ep_src)
                        continue
            else:
                k_ep_src = -1


        db_audio[k_ch].update({
            'fadein': chapter_fadein,
            'fadeout': chapter_fadeout,
            'fade_alg': chapter_fadeout_alg,
            'silence': chapter_silence,
            'start': db_audio[k_ch]['segments'][0]['start'],
            'duration': duration,
            'end': db_audio[k_ch]['segments'][0]['start'] + d,
            'avsync': 0
        })

