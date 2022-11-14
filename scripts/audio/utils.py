# -*- coding: utf-8 -*-
import sys

import numpy as np
import wave

from pprint import pprint


def read_single_track_audio_file(filepath, verbose=False):
    audio_track = wave.open(filepath, mode='rb')
    (nchannels, sampwidth, sample_rate, nframes, comptype, compname) = audio_track.getparams()
    audio_buffer = audio_track.readframes(nframes)
    audio_track.close()

    if verbose:
        print("\tnb of channels: %d" % (nchannels))
        print("\tduration: %.2fs" % (nframes/sample_rate))
        print("\tsample rate: %dHz" % (sample_rate))
        print("\tsample width: %dbit" % (sampwidth * 8))

    if sampwidth != 2 or nchannels != 1:
        sys.exit("error: wav format not supported")
    in_track = np.frombuffer(audio_buffer, dtype=np.int16)

    return sample_rate, in_track, float(nframes)/sample_rate


def write_single_track_audio_file(filepath, out, sample_rate=48000) -> None:
    out_file = wave.open(filepath, mode='wb')
    out_file.setnchannels(1)
    out_file.setsampwidth(2)
    out_file.setframerate(sample_rate)
    out_file.writeframes(out)
    out_file.close()


