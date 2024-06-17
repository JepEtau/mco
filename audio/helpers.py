import os
import numpy as np
import soundfile as sf
from scipy.io import wavfile
import subprocess
import time
from parsers import (
    db,
    logger,
    key,
    get_fps,
)
from utils.p_print import *


def read_audio(filepath: str) -> tuple[int, int, np.ndarray, float]:
    logger.debug(lightgreen(f"{__name__}: {filepath}"))

    sample_rate, audio_buffer = wavfile.read(filepath)
    audio_buffer_32b: np.ndarray
    audio_buffer: np.ndarray

    if len(audio_buffer.shape) == 1:
        # Mono, nb of bytes per samples should be checked,
        # assume it's always 16bit
        channels_count = 1
        audio_buffer_32b = np.array(audio_buffer, dtype=np.int32)
    else:
        # stereo, 24 bits
        channels_count = audio_buffer.shape[1]
        if audio_buffer.dtype == np.int16:
            audio_buffer_32b = audio_buffer.astype(np.int32) * 65536
        else:
            audio_buffer_32b = audio_buffer
    duration = audio_buffer_32b.shape[0] / sample_rate

    logger.debug(lightgrey(f"\tnb of channels: {channels_count}"))
    logger.debug(lightgrey(f"\tduration: {duration:.2f}s"))
    logger.debug(lightgrey(f"\tsample rate: {sample_rate}Hz"))

    return channels_count, sample_rate, audio_buffer_32b, duration



def write_audio(
    filepath: str,
    stereo_channels: np.ndarray,
    sample_rate = 48000
) -> None:
    logger.debug(lightgreen(f"{__name__}: {filepath} @ {sample_rate}Hz"))
    sf.write(
        file=filepath,
        data=stereo_channels,
        samplerate=sample_rate,
        subtype='PCM_24'
    )


def run_ffmpeg_command(command: list[str]) -> bool:
    start_time = time.time()
    sub_process = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    stdout: str = sub_process.stdout.decode('utf-8')
    stderr: str = sub_process.stderr.decode('utf-8')
    elapsed_time = time.time() - start_time
    logger.debug(lightgrey(f"\trun_ffmpeg_command executed in {elapsed_time:.02f}s"))
    if stdout:
        print(stdout)
    if stderr:
        print(stderr)
        return False
    return True



def get_output_filepath(
    episode: str | int | None = None,
    chapter: str | None = None,
) -> tuple[str, str]:
    k: str = ''
    if chapter in ('g_debut', 'g_fin') or episode is None:
        k = chapter
        logger.debug(lightgreen(f"{__name__}: {k}"))
    else:
        k = key(episode)
        logger.debug(lightgreen(f"{__name__}: {k}:{chapter}"))

    db_audio = db[k]['audio']

    # Working dir, maybe customized
    out_directory = os.path.join(db['common']['directories']['audio'])

    # Create the audio directory
    os.makedirs(out_directory, exist_ok=True)

    # Output filename
    suffix = f"_{db_audio['lang']}" if db_audio['lang'] != 'fr' else ''
    out_filename = f"{k}_audio{suffix}.{db['common']['settings']['audio_format']}"
    out_filepath = os.path.join(out_directory, out_filename)

    logger.debug(f"  {k}, {out_filepath}")
    return k, out_filepath



def get_audio_frame_count(episode: str, chapter: str) -> int:
    k, out_filepath = get_output_filepath(episode, chapter)
    fps = get_fps(db)

    print(lightgrey(f"  {k}: {out_filepath}"))

    channels_count, sample_rate, buffer, duration = read_audio(out_filepath)
    print(lightgrey(f"    channels: {channels_count}"))
    print(lightgrey(f"    sample rate: {sample_rate}Hz"))
    print(lightgrey(f"    buffer shape: {buffer.shape}"))
    print(lightgrey(f"    buffer dtype: {buffer.dtype}"))
    print(lightgrey(f"    duration: {duration}"))

    samples: float = buffer.shape[0]
    frame_count: int = int(fps * samples / float(sample_rate))
    print(f"  {frame_count} frames")

    return frame_count
