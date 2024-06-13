import os
import sys
from parsers import (
    db,
    key,
    logger,
)
from utils.p_print import *
from utils.path_utils import get_extension
from .helpers import run_ffmpeg_command
from utils.tools import ffmpeg_exe

def extract_audio_track(
    episode: int | str| None = None,
    chapter: str | None = None,
    edition: str = '',
    force: bool = False
) -> str:
    print("Extracting audio from input files")
    k_ep: str = key(episode)

    if chapter in ['g_debut', 'g_fin']:
        k_src = db[chapter]['audio']['src']['k_ep']
        k_ed = db[chapter]['audio']['src']['k_ed']
    else:
        k_src = k_ep
        k_ed = db[k_src]['audio']['src']['k_ed'] if edition == '' else edition

    logger.debug(lightgreen(f"{__name__}: {k_ed}:{k_src}:{chapter}"))

    # Input audio file
    try:
        in_filepath = db['editions'][k_ed]['inputs']['audio'][k_src]
    except:
        sys.exit(red(f"Missing file: edition {k_ed}, episode {k_src}"))
    if force:
        logger.debug(f"Extract audio stream: {k_ed}:{k_src} from {in_filepath}")

    if not os.path.exists(in_filepath):
        sys.exit(f"Error: audio: input file is missing, edition: {k_ed}")

    # Output audio file
    out_directory: str = os.path.join(db['common']['directories']['cache'], 'audio')
    os.makedirs(out_directory, exist_ok=True)

    out_filename: str = f"{k_src}_{k_ed}_audio.{db['common']['settings']['audio_format']}"
    out_filepath = os.path.join(out_directory, out_filename)

    if os.path.exists(out_filepath):
        logger.debug("\talready extracted")
        return out_filepath

    extension = get_extension(in_filepath)
    if extension == '.wav' and os.path.exists(in_filepath):
        logger.debug(f"\tuse file: {in_filepath}")
        return in_filepath

    else:
        logger.debug(f"\t{in_filepath} -> {out_filepath}")

        # FFmpeg command
        ffmpeg_command = [ffmpeg_exe]
        ffmpeg_command.extend(db['common']['settings']['verbose'].split(' '))
        ffmpeg_command.extend([
            "-i", in_filepath,
            "-sn",
            "-vn"
        ])

        # AWFULL but necessary to keep 24bit audio for the 'b' edition
        # TODO: do a ffprobe before ?
        if "b_ep" in in_filepath:
            ffmpeg_command.extend(["-c:a", "copy"])

        ffmpeg_command.extend(["-y", out_filepath])

        run_ffmpeg_command(ffmpeg_command)

        return out_filepath

