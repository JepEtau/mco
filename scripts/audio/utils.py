# -*- coding: utf-8 -*-
import sys

import numpy as np
import wave

from pprint import pprint


def read_audio_file(filepath, verbose=False):
    print("read_audio_file: %s" % (filepath))
    audio_track = wave.open(filepath, mode='rb')
    (channels_count, sampwidth, sample_rate, nframes, comptype, compname) = audio_track.getparams()
    audio_buffer = audio_track.readframes(nframes)
    audio_track.close()

    if verbose:
        print("\tnb of channels: %d" % (channels_count))
        print("\tduration: %.2fs" % (nframes/sample_rate))
        print("\tsample rate: %dHz" % (sample_rate))
        print("\tsample width: %dbit" % (sampwidth * 8))

    if sampwidth != 2 or channels_count != 1:
        sys.exit("error: wav format not supported")
    in_track = np.frombuffer(audio_buffer, dtype=np.int16)

    return channels_count, sample_rate, in_track, float(nframes)/sample_rate


def write_track_to_audio_file(filepath, stereo_channels, sample_rate=48000) -> None:
    print("write_track_to_audio_file: %sHz" % (sample_rate))
    out_file = wave.open(filepath, mode='wb')
    # out_file.setnchannels(1)
    # Changed to stereo
    out_file.setnchannels(2)
    out_file.setsampwidth(2)
    out_file.setframerate(sample_rate)
    out_file.writeframes(stereo_channels)
    # out_file.write(stereo_channels)
    out_file.close()


