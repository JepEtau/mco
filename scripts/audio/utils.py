# -*- coding: utf-8 -*-
import numpy as np
import soundfile as sf
from scipy.io import wavfile
from pprint import pprint

from utils.time_conversions import current_datetime_str


def read_audio_file(filepath, verbose=False) -> tuple[int, int, np.ndarray, float]:
    # print("read_audio_file: %s" % (filepath))
    sample_rate, audio_buffer = wavfile.read(filepath)
    if len(audio_buffer.shape) == 1:
        # Mono, nb of bytes per samples shoulf be checked,
        # but it is always 16bit
        channels_count = 1
        audio_buffer_32b = np.array(audio_buffer, dtype=np.int32)
    else:
        # Stéréo, 24 bits
        channels_count = audio_buffer.shape[1]
        if audio_buffer.dtype == np.int16:
            audio_buffer_32b = audio_buffer.astype(np.int32) * 65536
        else:
            audio_buffer_32b = audio_buffer
    duration = audio_buffer_32b.shape[0] / sample_rate

    if verbose:
        print("%s read audio file" % (current_datetime_str()))
        print("\tnb of channels: %d" % (channels_count))
        print("\tduration: %.2fs" % (duration))
        print("\tsample rate: %dHz" % (sample_rate))

    return channels_count, sample_rate, audio_buffer_32b, duration


def write_track_to_audio_file(filepath, stereo_channels:np.ndarray, sample_rate=48000) -> None:
    # print("write_track_to_audio_file: %sHz" % (sample_rate))
    sf.write(
        file=filepath,
        data=stereo_channels,
        samplerate=sample_rate,
        subtype='PCM_24')

