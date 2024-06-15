import numpy as np
import os
import sys
from utils.p_print import *
from utils.path_utils import path_split
from utils.time_conversions import (
    ms_to_frame,
    frame_to_ms,
)
from parsers import (
    db,
    get_fps,
    key,
    logger,
    main_chapter_keys,
)
from .extract import extract_audio_track
from .helpers import (
    read_audio,
    write_audio,
    get_output_filepath,
)


def generate_audio_track(
    episode: str | int | None = None,
    chapter: str | None = None,
    force: bool = False,
) -> None:
    """Create an audio file for a specific episode. It will be merged
    with the video track of this episode (openening and end credits are excluded)
    """
    k, out_filepath = get_output_filepath(episode, chapter)

    fps = get_fps(db)
    db_audio = db[k]['audio']

    if os.path.exists(out_filepath) and not force:
        target_str: str = f"{k}:{chapter}" if episode is not None and chapter is not None else f"{k}"
        print(f"{target_str}: audio track already generated: {out_filepath}")
        return

    # Use a specific function
    if k in ('g_debut', 'g_fin'):
        _generate_audio_track_g(
            chapter=k,
            out_filepath=out_filepath,
            force=force,
        )
        return

    # Source
    k_ed, k_ep = db_audio['src']['k_ed'], key(episode)
    logger.debug(f"extract audio from {k_ed}:{k_ep}")

    # Extract audio file if needed
    input_filepath = extract_audio_track(
        episode=k_ep,
        edition=k_ed,
        force=force
    )

    print(f"{k}: generate audio track")

    # Read the input audio file
    channel_count, sample_rate, in_track, duration = read_audio(
        input_filepath,
    )
    sample_rate = int(sample_rate / 1000)

    logger.debug(f"{k_ep}: generate audio, settings:")
    logger.debug(f" sample rate: {sample_rate}")
    logger.debug(f" in_track: {in_track}")
    logger.debug(f" duration: {duration}")
    logger.debug(f" channels: {channel_count}")

    # Create output buffers
    out_left_channel = np.empty((0,0), dtype=np.int32)
    out_right_channel = np.empty((0,0), dtype=np.int32)
    if channel_count > 1:
        in_left_channel = in_track[:, 0]
        in_right_channel = in_track[:, 1]
    else:
        in_left_channel = in_track
    in_track_dtype = in_left_channel.dtype

    # Generate an output file
    ext = db['common']['settings']['audio_format']

    frame_count_prev: int = 0
    frame_count: int = 0
    samples_count: int = 0
    for k in main_chapter_keys():
        if db_audio[k]['duration'] == 0:
            continue

        logger.debug(f"  {k}:")
        # Add silence for A/V sync
        if db_audio[k]['avsync'] > 0:
            samples_count = int(db_audio[k]['avsync'] * sample_rate)
            logger.debug(f"\t  avsync: {samples_count} (({ms_to_frame(samples_count/sample_rate, fps):.1f}f")
            out_left_channel = np.append(out_left_channel, np.full(abs(samples_count), 0, dtype=in_track_dtype))
            if channel_count > 1:
                out_right_channel = np.append(out_right_channel, np.full(abs(samples_count), 0, dtype=in_track_dtype))

        # Concatenate segments
        for s in db_audio[k]['segments']:
            start = int(s['start'] * sample_rate)
            end = int(s['end'] * sample_rate)

            if 'k_ep' in s.keys():
                # Import this segment from another episode
                logger.debug("info: generate_audio_track: import from other episode")
                k_ep_src = s['k_ep']
                tmp_filepath: str = os.path.join(
                    path_split(out_filepath)[0],
                    f"{k_ep_src}_{k_ed}_audio.{ext}"
                )
                if not os.path.exists(tmp_filepath):
                    tmp_filepath = extract_audio_track(
                        episode=k_ep_src,
                        edition=k_ed,
                        force=force
                    )
                logger.debug(f" use file from another episode")
                logger.debug(f" sample rate: {sample_rate}")
                logger.debug(f" in_track: {in_track}")
                logger.debug(f" duration: {duration}")
                logger.debug(f" channels: {channel_count}")

                channel_count, sample_rate_src, in_track, duration = read_audio(tmp_filepath)
                if channel_count > 1:
                    in_left_channel_tmp = in_track[:, 0]
                    in_right_channel_tmp = in_track[:, 1]
                else:
                    in_left_channel_tmp = in_track

                sample_rate_src = int(sample_rate_src / 1000)
                start = int(s['start'] * sample_rate_src)
                end = int(s['end'] * sample_rate_src)
                logger.debug(
                    f"\t  [{start} ... {end}] ({end-start})"
                    + f"([{ms_to_frame(start/sample_rate_src, fps):.1}f "
                    + f"... {ms_to_frame(end/sample_rate_src, fps):.1}f] "
                    + f"({ms_to_frame((end-start)/sample_rate_src, fps):.1}f)"
                )
                out_left_channel = np.append(out_left_channel, in_left_channel_tmp[start:end])
                if channel_count > 1:
                    out_right_channel = np.append(out_right_channel, in_right_channel_tmp[start:end])

                continue
            else:
                tmp_left = np.array(in_left_channel[start:end])
                if channel_count > 1:
                    tmp_right = np.array(in_right_channel[start:end])


            if 'silence' in s:
                samples_count = frame_to_ms(ms_to_frame(int(s['silence'], fps), fps) * sample_rate)
                logger.debug("\t\tsilence: %d ms" % (samples_count / sample_rate))
                out_left_channel = np.append(out_left_channel, np.full(samples_count, 0, dtype=in_track_dtype))
                if channel_count > 1:
                    out_right_channel = np.append(out_right_channel, np.full(samples_count, 0, dtype=in_track_dtype))
            else:
                # Append segment
                logger.debug("\t\t[%d ... %d] (%d) ([(%.1ff) ... (%.1ff)] (%.1ff))" % (
                        start, end, end-start,
                        ms_to_frame(start/sample_rate, fps),
                        ms_to_frame(end/sample_rate, fps),
                        ms_to_frame((end-start)/sample_rate, fps)
                ))
                out_left_channel = np.append(
                    out_left_channel,
                    tmp_left.astype(in_track.dtype)
                )
                if channel_count > 1:
                    out_right_channel = np.append(
                        out_right_channel,
                        tmp_right.astype(in_track.dtype)
                    )

        # Apply fadeout at the end of this part
        if db_audio[k]['fadeout'] != 0:
            samples_count = int(db_audio[k]['fadeout'] * sample_rate)
            logger.debug("\t\tfadeout: alg:%s, %d (%.1ff)" % (
                db_audio[k]['fade_alg'],
                samples_count,
                ms_to_frame(samples_count/sample_rate, fps)
            ))
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
            logger.debug(f" out_len(L): {out_len}")
            logger.debug(f" out_len(R): {len(out_right_channel)}")
            out_left_channel[out_len - samples_count:] = out_left_channel[out_len - samples_count:] * fade_curve
            if channel_count > 1:
                out_right_channel[out_len - samples_count:] = out_right_channel[out_len - samples_count:] * fade_curve

        # Add a silence between 2 chapters
        if db_audio[k]['silence'] != 0:
            # round to a number a frame
            samples_count = int(frame_to_ms(
                ms_to_frame(int(db_audio[k]['silence']), fps) * sample_rate,
                fps
            ))
            # note, patch 'count' set only for debug
            # db_audio[k]['silence'] = ms_to_frame(samples_count/sample_rate)
            logger.debug("\t\tsilence: %d (%.1ff)" % (
                samples_count, ms_to_frame(samples_count/sample_rate, fps))
            )
            out_left_channel = np.append(
                out_left_channel,
                np.full(samples_count, 0, dtype=in_track_dtype)
            )
            if channel_count > 1:
                out_right_channel = np.append(
                    out_right_channel,
                    np.full(samples_count, 0, dtype=in_track_dtype)
                )

        frame_count = ms_to_frame(len(out_left_channel)/sample_rate, fps)
        logger.debug(
            f"\t  total: {frame_count - frame_count_prev} frames (count={frame_count}, count_prev={frame_count_prev})"
        )
        frame_count_prev = frame_count


    logger.debug(f" ->{out_filepath}")

    if channel_count > 1:
        out_track_stereo = np.ascontiguousarray(np.vstack((out_left_channel, out_right_channel)).transpose())
    else:
        # Create a stereo buffer (16bit)
        out_track_stereo = np.ascontiguousarray(
            np.vstack(
                (out_left_channel.astype(np.int16), out_left_channel.astype(np.int16))
            ).transpose()
        )

    write_audio(out_filepath, out_track_stereo, sample_rate=sample_rate*1000)



def _generate_audio_track_g(
    chapter: str,
    out_filepath: str,
    force: bool = False
) -> None:
    """Create the audio file for the 'generique'

    Args:
        db: the global database
        k_part_g: keyword for 'generique'

    Returns:
        None

    """
    if chapter not in ('g_debut', 'g_fin'):
        sys.exit(red(f"Error: {__name__}: do not use this function for chapter {chapter}"))

    logger.debug(lightgreen(f"{__name__}: {chapter}"))

    # Source
    db_audio: dict = db[chapter]['audio']
    k_ed: str = db_audio['src']['k_ed']
    k_ep: str = db_audio['src']['k_ep']

    # Read audio file, extract audio file if needed
    in_filepath: str = extract_audio_track(
        episode=k_ep,
        chapter=chapter,
        edition=k_ed,
        force=force
    )
    print(f"{chapter}: generate audio track")

    channel_count, sample_rate, in_track, duration = read_audio(in_filepath)
    sample_rate = int(sample_rate / 1000)

    logger.debug(f"extracted, generate:")
    logger.debug(f"\tsample rate: {sample_rate}")
    logger.debug(f"\tin_track: {in_track.shape}")
    logger.debug(f"\tduration: {duration}")
    logger.debug(f"\tchannels: {channel_count}")

    # Generate an output buffer
    out_left_channel: np.ndarray = np.empty((0,0), dtype=np.int32)
    if channel_count > 1:
        in_left_channel: np.ndarray = in_track[:, 0]
        in_right_channel: np.ndarray = in_track[:, 1]
        out_right_channel: np.ndarray = np.empty((0,0), dtype=np.int32)

    else:
        in_left_channel: np.ndarray = in_track
    in_track_dtype = in_left_channel.dtype

    # Add the audio for this part
    start = int(db[chapter]['audio']['start'] * sample_rate)
    end = int(db[chapter]['audio']['end'] * sample_rate)

    # Add silence for A/V sync
    if db_audio['avsync'] > 0:
        samples_count = int(db_audio['avsync'] * sample_rate)
        logger.debug(f"\t  avsync: ({samples_count})")
        out_left_channel = np.append(
            out_left_channel,
            np.full(abs(samples_count), 0, dtype=in_track_dtype)
        )
        if channel_count > 1:
            out_right_channel = np.append(
            out_right_channel,
            np.full(abs(samples_count), 0, dtype=in_track_dtype)
        )

    # Concatenate segments
    for s in db_audio['segments']:
        start: int = int(s['start'] * sample_rate)
        end: int = int(s['end'] * sample_rate)

        tmp_left: np.ndarray = np.array(in_left_channel[start:end])
        if channel_count > 1:
            tmp_right: np.ndarray = np.array(in_right_channel[start:end])

        # Apply gain
        if 'gain' in s.keys():
            gain = 10**(s['gain']/10.0)
            tmp_left = gain * np.array(tmp_left)
            if channel_count > 1:
                tmp_right = gain * np.array(tmp_right)
            logger.debug(f"\t\t[{start}... {end}], gain={s['gain']:.1f}dB ({gain:.02f})   ({end-start}")

        # No effect
        elif end - start > 0:
            logger.debug(f"\t\t[{start} ... {end}]   ({end-start})")

        # Append segment
        if (end-start) > 0:
            out_left_channel = np.append(out_left_channel, tmp_left.astype(in_track.dtype))
            if channel_count > 1:
                out_right_channel = np.append(out_right_channel, tmp_right.astype(in_track.dtype))

        # Append silence
        if 'silence' in s:
            samples_count = int(s['silence'] * sample_rate)
            logger.debug("\t\tsilence: (%d)" % (samples_count))
            out_left_channel = np.append(
                out_left_channel,
                np.full(samples_count, 0, dtype=in_track_dtype)
            )
            if channel_count > 1:
                out_right_channel = np.append(
                    out_right_channel, np.full(samples_count, 0, dtype=in_track_dtype)
                )

    # Add a silence between 2 chapters. This shall be defined in the common section
    if 'silence' in db_audio and db_audio['silence'] != 0:
        samples_count = int(db_audio['silence'] * sample_rate)
        logger.debug(f"\tsilence: ({samples_count})")
        out_left_channel = np.append(out_left_channel, np.full(samples_count, 0, dtype=in_track_dtype))
        if channel_count > 1:
            out_right_channel = np.append(out_right_channel, np.full(samples_count, 0, dtype=in_track_dtype))

    logger.debug(f"\t->{out_filepath}")

    # Create a stereo buffer (16bit)
    if channel_count > 1:
        out_track_stereo = np.ascontiguousarray(np.vstack((out_left_channel, out_right_channel)).transpose())
    else:
        out_track_stereo = np.ascontiguousarray(
            np.vstack((out_left_channel.astype(np.int16),
            out_left_channel.astype(np.int16))).transpose())

    # Save audio file as wav
    logger.debug(f"output audio track: {type(out_track_stereo)}, shape: {out_track_stereo.shape}")
    write_audio(out_filepath, out_track_stereo, sample_rate=sample_rate*1000)
