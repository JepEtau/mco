# -*- coding: utf-8 -*-
import sys

import numpy as np
import os
from pprint import pprint

from utils.common import (
    K_AUDIO_PARTS,
    pprint_audio,
)
from utils.ffmpeg import ffmpeg_execute_command
from utils.path import create_audio_directory
from utils.time_conversions import (
    current_datetime_str,
    ms_to_frames,
    frames_to_ms,
)
from audio.utils import (
    read_audio_file,
    write_track_to_audio_file,
)


def extract_audio(db, k_ep_or_g:str, k_ed, force=False, verbose=False) -> str:
    # Returns the extracted filepath

    verbose = True
    print("%s.extract_audio: %s:%s" % (__name__, k_ed, k_ep_or_g))
    if k_ep_or_g in ['g_debut', 'g_fin']:
        k_ep = db[k_ep_or_g]['target']['audio']['src']['k_ep']
    else:
        k_ep = k_ep_or_g

    # if k_ed == '':
    #     use_default = True
    #     k_ed = db[k_ep_or_g]['target']['audio']['src']['k_ed']
    # else:
    #     use_default = False
    # k_ed = db[k_ep_or_g]['target']['audio']['src']['k_ed']


    if verbose:
        print("%s extract audio stream: %s:%s" % (current_datetime_str(), k_ed, k_ep))

    # Input audio file
    input_filepath = db[k_ep][k_ed]['path']['input_audio']
    if force or verbose:
        print("%s extract audio stream: %s:%s: %s" % (current_datetime_str(), k_ed, k_ep, input_filepath))

    if not os.path.exists(input_filepath):
        sys.exit("Erreur: le fichier d'entrée est manquant pour l'édition %s" % (k_ed))

    # Output audio file
    output_directory = os.path.join(db[k_ep]['target']['path']['cache'], "audio")
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    output_filename = "%s_%s_audio_extract.%s" % (k_ep, k_ed, db['common']['settings']['audio_format'])
    output_filepath = os.path.join(output_directory, output_filename)


    filename, extension = os.path.splitext(input_filepath)
    if extension == '.wav':
        # Already extracted
        print("\tuse file: %s" % (input_filepath))
        return input_filepath
    else:
        print("\tconvert file: %s -> %s" % (input_filepath, output_filepath))
        # Create complex filter
        filter_complex_str = ""
        filter_complex_str = filter_complex_str + "[outa]"
        # print("filter_complex_str = %s" % (filter_complex_str))

        print(input_filepath)

        # FFmpeg command
        command_ffmpeg = [db['common']['settings']['ffmpeg_exe']]
        command_ffmpeg.extend(db['common']['settings']['verbose'].split(' '))
        command_ffmpeg.extend(["-i", input_filepath,
                        # "-filter_complex", filter_complex_str,
                        # "-map", "[outa]",
                        "-sn", "-vn",
                        "-y", output_filepath
        ])
        std = ffmpeg_execute_command(command_ffmpeg, output_filepath, mode='', print_msg=False)
        return output_filepath


def generate_audio(db, k_ep:str, force=False, verbose=False):
    """Create an audio file for a specified episode. This will be merged
    with video of this episode (generiques are excluded)
    db_audio contains properties to process and create the audio file

    Args:
        db: the global database
        k_ep: episode

    Returns:
        None

    """
    if k_ep in ['g_debut', 'g_fin']:
        _generate_audio_generique(db, k_part_g=k_ep, force=force, verbose=verbose)
        return

    if verbose:
        print("%s.generate_audio: %s" % (__name__, k_ep))

    db_audio = db[k_ep]['target']['audio']
    # extract audio from edition
    k_ed = db_audio['src']['k_ed']

    # Create the audio directory
    create_audio_directory(db, k_ep)

    # Output audio file
    output_directory = os.path.join(db[k_ep]['target']['path']['cache'], "audio")
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    output_filename = "%s_audio.%s" % (k_ep, db['common']['settings']['audio_format'])
    output_filepath = os.path.join(output_directory, output_filename)
    if os.path.exists(output_filepath) and not force:
        print("%s generate audio: %s, already exists, skip" % (current_datetime_str(), k_ep))
        return

    print("%s generate audio: %s" % (current_datetime_str(), k_ep))

    input_directory = os.path.join(db[k_ep]['target']['path']['cache'], "audio")
    tmp_filename = "%s_%s_audio_extract.%s" % (k_ep, k_ed, db['common']['settings']['audio_format'])
    tmp_filepath = os.path.join(input_directory, tmp_filename)
    if not os.path.exists(tmp_filepath):
        tmp_filepath = extract_audio(db, k_ep, k_ed, force=force, verbose=verbose)
    channels_count, sample_rate, in_track, duration = read_audio_file(tmp_filepath, True)
    sample_rate = int(sample_rate / 1000)

    if channels_count != 1:
        sys.exit("error: generate_audio: only mono is supported for %s" % (k_ep))

    # Generate an output buffer
    out_left_channel = np.empty((0,0), dtype=np.int32)
    in_left_channel = in_track
    in_track_dtype = in_left_channel.dtype

    # Generate an output file
    out_left_channel = np.empty((0,0), dtype=in_track_dtype)
    frames_count_prev = 0
    for k in K_AUDIO_PARTS:
        if db_audio[k]['duration'] == 0:
            continue

        if verbose:
            print("\t%s:" % (k))
        # Add silence for A/V sync
        if db_audio[k]['avsync'] > 0:
            samples_count = int(db_audio[k]['avsync'] * sample_rate)
            if verbose:
                print("\t\tavsync: %d ((%.1ff))" % (samples_count, ms_to_frames(samples_count/sample_rate)))
            out_left_channel = np.append(out_left_channel, np.full(abs(samples_count), 0, dtype=in_track_dtype))

        # Concatenate segments
        for s in db_audio[k]['segments']:
            if 'k_ep' in s.keys():
                # Import this segment from another episode
                print("info: generate_audio: import from other episode")
                k_ep_src = s['k_ep']
                input_directory = os.path.join(db[k_ep_src]['target']['path']['cache'], "audio")
                tmp_filename = "%s_%s_audio_extract.%s" % (k_ep_src, k_ed, db['common']['settings']['audio_format'])
                tmp_filepath = os.path.join(input_directory, tmp_filename)
                if not os.path.exists(tmp_filepath):
                    tmp_filepath = extract_audio(db, k_ep_src, k_ed, force=force, verbose=verbose)

                channels_count, sample_rate_src, in_left_channel_tmp, duration = read_audio_file(tmp_filepath)
                sample_rate_src = int(sample_rate_src / 1000)
                start = int(s['start'] * sample_rate_src)
                end = int(s['end'] * sample_rate_src)
                if verbose:
                    print("\t\t[%d ... %d] (%d) ([(%.1ff) ... (%.1ff)] (%.1ff))" % (start, end, end-start,
                        ms_to_frames(start/sample_rate_src), ms_to_frames(end/sample_rate_src), ms_to_frames((end-start)/sample_rate_src)))
                out_left_channel = np.append(out_left_channel, in_left_channel_tmp[start:end])
                continue

            if 'silence' in s.keys():
                samples_count = frames_to_ms(ms_to_frames(int(s['silence'])) * sample_rate)
                if verbose:
                    print("\t\tsilence: %d ms" % (samples_count / sample_rate))
                out_left_channel = np.append(out_left_channel, np.full(samples_count, 0, dtype=in_track_dtype))
            else:
                start = int(s['start'] * sample_rate)
                end = int(s['end'] * sample_rate)
                if verbose:
                    print("\t\t[%d ... %d] (%d) ([(%.1ff) ... (%.1ff)] (%.1ff))" % (start, end, end-start,
                        ms_to_frames(start/sample_rate), ms_to_frames(end/sample_rate), ms_to_frames((end-start)/sample_rate)))
                out_left_channel = np.append(out_left_channel, in_left_channel[start:end])

        # Apply fadeout at the end of this part
        if db_audio[k]['fadeout'] != 0:
            samples_count = int(db_audio[k]['fadeout'] * sample_rate)
            if verbose:
                print("\t\tfadeout: alg:%s, %d (%.1ff)" % (db_audio[k]['fade_alg'], samples_count, ms_to_frames(samples_count/sample_rate)))
            # https://www.hackaudio.com/digital-signal-processing/combining-signals/fade-inout/
            # https://github.com/spatialaudio/selected-topics-in-audio-signal-processing-exercises/blob/master/tools.py
            fade_curve = np.arange(samples_count) / samples_count

            if db_audio[k]['fade_alg'] == 'sin':
                fade_curve = 1 - np.sin(fade_curve * np.pi / 2)
            elif db_audio[k]['fade_alg'] == 'cos':
                fade_curve = 1 - ((1 - np.cos(fade_curve * np.pi)) / 2)
            else:
                # logarithmic
                fade_curve = np.power(0.1, fade_curve * 5)

            out_len = len(out_left_channel)
            out_left_channel[out_len - samples_count:] = out_left_channel[out_len - samples_count:] * fade_curve



        # Add a silence between 2 parts
        if db_audio[k]['silence'] != 0:
            # round to a number a frame
            samples_count = frames_to_ms(ms_to_frames(int(db_audio[k]['silence'])) * sample_rate)
            # note, patch 'count' filed only for debug
            # db_audio[k]['silence'] = ms_to_frames(samples_count/sample_rate)
            if verbose:
                print("\t\tsilence: %d (%.1ff)" % (samples_count, ms_to_frames(samples_count/sample_rate)))
            out_left_channel = np.append(out_left_channel, np.full(samples_count, 0, dtype=in_track_dtype))

        frames_count = ms_to_frames(len(out_left_channel)/sample_rate)
        if verbose:
            print("\t\ttotal: %d frames (frames_count=%d, frames_count_prev=%d)" % (frames_count - frames_count_prev, frames_count, frames_count_prev))
        frames_count_prev = frames_count


    if verbose:
        print("\t->%s" % (output_filepath))

    # Create a stereo buffer (16bit)
    out_track_stereo = np.ascontiguousarray(
        np.vstack((out_left_channel.astype(np.int16),
        out_left_channel.astype(np.int16))).transpose())

    write_track_to_audio_file(output_filepath, out_track_stereo, sample_rate=sample_rate*1000)




def _generate_audio_generique(db, k_part_g, force=False, verbose=False):
    """Create the audio file for the 'generique'

    Args:
        db: the global database
        k_part_g: keyword for 'generique'

    Returns:
        None

    """
    if k_part_g not in ['g_debut', 'g_fin']:
        sys.exit("Error: %s.generate_audio_generique: do not use this function for part %s" % (__name__,  k_part_g))

    k_ed = db[k_part_g]['target']['audio']['src']['k_ed']
    k_ep = db[k_part_g]['target']['audio']['src']['k_ep']

    # Output audio file
    output_directory = os.path.join(db[k_part_g]['target']['path']['cache'], "audio")
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    output_filename = "%s_audio.%s" % (k_part_g, db['common']['settings']['audio_format'])
    output_filepath = os.path.join(output_directory, output_filename)
    if os.path.exists(output_filepath) and not force:
        print("%s generate audio: %s, already exists, skip" % (current_datetime_str(), k_part_g))
        return

    print("%s generate audio: %s from %s" % (current_datetime_str(), k_part_g, k_ep))

    # Extract audio file if needed
    tmp_filename = "%s_%s_audio_extract.%s" % (k_ep, k_ed, db['common']['settings']['audio_format'])
    tmp_filepath = os.path.join(db[k_ep]['target']['path']['cache'], "audio", tmp_filename)
    if not os.path.exists(tmp_filepath) or force:
        tmp_filepath = extract_audio(db, k_ep, k_ed, force=force, verbose=verbose)

    channels_count, sample_rate, in_track, duration = read_audio_file(tmp_filepath, verbose=True)
    sample_rate = int(sample_rate / 1000)

    db_audio = db[k_part_g]['target']['audio']

    # Generate an output buffer
    out_left_channel = np.empty((0,0), dtype=np.int32)
    if channels_count == 2:
        in_left_channel = in_track[:, 0]
        in_right_channel = in_track[:, 1]
        out_right_channel = np.empty((0,0), dtype=np.int32)
    else:
        in_left_channel = in_track
    in_track_dtype = in_left_channel.dtype


    # Add the audio for this part
    if 'start' in db[k_part_g]['target']['audio'].keys():
        # Use the 'start' and 'end' properties from the common section
        # print("Use the common timestamps")
        start = int(db_audio['start'] * sample_rate)
        end = int(db_audio['end'] * sample_rate)
    else:
        # Use the 'start' and 'end' properties from the edition section
        # because no changes are defined in common section
        # print("Use the src timestamps")
        start = int(db[k_part_g][k_ed]['audio']['start'] * sample_rate)
        end = int(db[k_part_g][k_ed]['audio']['end'] * sample_rate)

    # Add silence for A/V sync
    if db_audio['avsync'] > 0:
        samples_count = int(db_audio['avsync'] * sample_rate)
        if verbose:
            print("\t\tavsync: (%d)" % (samples_count))
        out_left_channel = np.append(out_left_channel, np.full(abs(samples_count), 0, dtype=in_track_dtype))
        if channels_count == 2:
            out_right_channel = np.append(out_right_channel, np.full(abs(samples_count), 0, dtype=in_track_dtype))

    # Concatenate segments
    for s in db_audio['segments']:
        start = int(s['start'] * sample_rate)
        end = int(s['end'] * sample_rate)
        tmp_left = np.array(in_left_channel[start:end])
        if channels_count == 2:
            tmp_right = np.array(in_right_channel[start:end])

        if 'gain' in s.keys():
            # Apply gain
            gain = 10**(s['gain']/10.0)
            tmp_left = gain * np.array(tmp_left)
            if channels_count == 2:
                tmp_right = gain * np.array(tmp_right)
            if verbose:
                print("\t\t[%d ... %d], gain=%.1fdB (%.02f)\t(%d)" % (start, end, s['gain'], gain, end-start))
        else:
            # No effect
            if verbose:
                if (end-start) > 0:
                        print("\t\t[%d ... %d]\t(%d)" % (start, end, end-start))

        # Append segment
        if (end-start) > 0:
            out_left_channel = np.append(out_left_channel, tmp_left.astype(in_track.dtype))
            if channels_count == 2:
                out_right_channel = np.append(out_right_channel, tmp_right.astype(in_track.dtype))

        if 'silence' in s.keys():
            # append silence
            samples_count = int(s['silence'] * sample_rate)
            if verbose:
                print("\t\tsilence: (%d)" % (samples_count))
            out_left_channel = np.append(out_left_channel, np.full(samples_count, 0, dtype=in_track_dtype))
            if channels_count == 2:
                out_right_channel = np.append(out_right_channel, np.full(samples_count, 0, dtype=in_track_dtype))


    # Add a silence between 2 parts. This shall be defined in the common section
    if ('silence' in db_audio.keys()
    and db_audio['silence'] != 0):
        samples_count = int(db_audio['silence'] * sample_rate)
        if verbose:
            print("\t\tsilence: (%d)" % (samples_count))
        out_left_channel = np.append(out_left_channel, np.full(samples_count, 0, dtype=in_track_dtype))
        if channels_count == 2:
            out_right_channel = np.append(out_right_channel, np.full(samples_count, 0, dtype=in_track_dtype))

    if verbose:
        print("\t->%s" % (output_filepath))

    # Create a stereo buffer (16bit)
    if channels_count == 2:
        out_track_stereo = np.ascontiguousarray(np.vstack((out_left_channel, out_right_channel)).transpose())
    else:
        out_track_stereo = np.ascontiguousarray(
            np.vstack((out_left_channel.astype(np.int16),
            out_left_channel.astype(np.int16))).transpose())

    # Save audio file as wav
    write_track_to_audio_file(output_filepath, out_track_stereo, sample_rate=sample_rate*1000)
