import re
import subprocess
import sys
import os
from pprint import pprint
from parsers import (
    db,
    key,
    get_fps,
    TaskName
)
from utils.logger import main_logger
from audio import get_audio_frame_count
from utils.mco_utils import makedirs, run_simple_command
from utils.p_print import *
from utils.path_utils import absolute_path
from utils.tools import ffprobe_exe, ffmpeg_exe


def get_video_duration(filename: str, integrity: bool = True) -> tuple[float, int]:
    fps = get_fps(db)

    command: list[str] = [ffprobe_exe, "-hide_banner"]
    if integrity:
        command.extend(["-count_frames"])
    command.extend(["-i", filename])

    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout: str = ''
    try:
        stdout = result.stdout.decode('utf-8')
    except:
        pass

    duration: int = 0
    frame_count: int = 0
    if integrity:
        if (result := re.search(re.compile(r"(File ended prematurely)"), stdout)):
            return 0.0, 0

    if (result := re.search(
        re.compile(r"Duration: ([0-9]{2}):([0-9]{2}):([0-9]{2}).([0-9]{2}),"),
        stdout
    )):
        duration = int(result[1]) * 60
        duration = (duration + int(result[2])) * 60
        duration = (duration + int(result[3])) * 100
        duration += int(result[4])
        frame_count = int(duration * fps / 100)

    return float(duration)/100.0, frame_count



def combine_av_tracks(
    episode: str,
    chapter: str = '',
    task: TaskName='lr',
    force: bool = False,
    simulation: bool = False
):
    k: str = ''
    if chapter in ('g_debut', 'g_fin') or episode is None:
        k = chapter
    else:
        k = key(episode)

    # Output filepath
    print(lightgreen(f"Merge audio and video tracks:"), lightcyan(f"{k}"))
    cache_path = db[k]['cache_path']

    language: str = db[k]['audio']['lang']
    language = '' if language == 'fr' else f"_{language}"
    suffix = '' if task == '' or task == 'final' else f"_{task}"

    audio_video_filepath: str = (
        os.path.join(cache_path, f"{k}{suffix}{language}.mkv")
        if k in ('g_debut', 'g_fin')
        else os.path.join(cache_path, f"{k}_av{suffix}{language}.mkv")
    )

    if os.path.exists(audio_video_filepath) and not force and not simulation:
        return

    # Get nb of frames from video stream
    if k in ('g_debut', 'g_fin'):
        video_filepath = os.path.join(
            cache_path,
            "video",
            f"{k}_video_{db[k]['video']['hash']}{suffix}{language}.mkv"
        )

    else:
        video_filepath = os.path.join(
            cache_path,
            "video",
            f"{k}_video{language}.mkv"
        )

    video_frames_count: int = 0
    try:
        _, video_frames_count = get_video_duration(video_filepath, integrity=False)
    except:
        pass

    # Get equivalent nb of frames from audio stream
    audio_filepath = os.path.join(
        db['common']['directories']['audio'],
        f"{k}_audio{language}.{db['common']['settings']['audio_format']}"
    )
    print(yellow(audio_filepath))
    audio_frames_count: int = 0
    try:
        frame_count = get_audio_frame_count(episode, chapter)
    except:
        k: str = f"episode {episode}" if chapter == '' else chapter
        raise RuntimeError(f"No valid audio for {k}")
    audio_frames_count = frame_count

    print(f"\tvideo: {video_filepath}: {video_frames_count}")
    print(f"\taudio: {audio_filepath}: {audio_frames_count}")
    print(f"\tAV file: {audio_video_filepath}")

    # Cannot continue if nb of frames differ
    if audio_frames_count != video_frames_count and not simulation:
        sys.exit(red(f"Error: cannot merge audio and video tracks: nb of frames differs"))

    # Merge Audio and Video tracks
    ffmpeg_command: list[str] = [
        ffmpeg_exe,
        *db['common']['settings']['verbose'],
        "-i", video_filepath,
        "-i", audio_filepath,
        "-c:v", "copy",
        "-c:a", "copy",
        "-y", audio_video_filepath
    ]

    return run_simple_command(ffmpeg_command)



def concatenate_all(
    episode: str,
    task: TaskName,
    simulation: bool = False
) -> None:
    k_ep: str = key(episode)
    print(lightgreen(f"Concatenate all A/V files:"), lightcyan(f"{k_ep}"))

    language = db[k_ep]['audio']['lang']
    lang_str = '' if language == 'fr' else f"_{language}"

    suffix = '' if task == '' or task == 'final' else f"_{task}"

    cache_directory = db[k_ep]['cache_path']
    output_filename = f"{k_ep}_no_chapters{suffix}{lang_str}.mkv"
    output_filepath = os.path.join(cache_directory, output_filename)
    main_logger.debug(f"A/V file (without chapters): {output_filepath}")

    # Create concat file
    makedirs(episode)
    concat_fp: str = absolute_path(
        os.path.join(
            cache_directory,
            "concat",
            f"{k_ep}.txt"
        )
    )
    concat_file = open(concat_fp, "w")

    p = os.path.join(db['g_debut']['cache_path'], f"g_debut{suffix}{lang_str}.mkv")
    concat_file.write(f"file \'{p}\' \n")

    p = os.path.join(cache_directory, f"{k_ep}_av{suffix}{lang_str}.mkv")
    concat_file.write(f"file \'{p}\' \n")

    p = os.path.join(db['g_fin']['cache_path'], f"g_fin{suffix}{lang_str}.mkv")
    concat_file.write(f"file \'{p}\' \n")

    concat_file.close()

    # Concatenate files
    ffmpeg_command: list[str] = [
        ffmpeg_exe,
        "-hide_banner",
        "-loglevel", "error",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_fp,
        "-c", "copy",
        "-y", output_filepath
    ]

    main_logger.debug(' '.join(ffmpeg_command))
    if not simulation:
        run_simple_command(ffmpeg_command)





