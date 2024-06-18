import os
from parsers import (
    db,
    key,
    TaskName,
    get_fps
)
from utils.mco_utils import run_simple_command
from utils.path_utils import absolute_path
from utils.time_conversions import frame_to_sexagesimal, ms_to_frame
from utils.p_print import *
from utils.tools import mkvmerge_exe
from utils.logger import main_logger


CHAPTER_NAMES: dict[str, tuple[str]] = {
    'en': [
        "Opening credits",
        "Previously",
        "Episode",
        "To follow",
        "Documentary",
        "End credits",
    ],
    'fr': [
        "Générique de début",
        "Précédemment",
        "Episode",
        "A suivre",
        "Documentaire",
        "Générique de fin",
    ],
}

def add_chapters(
    episode: str,
    task: TaskName,
    simulation:bool=False
) -> None:
    k_ep: str = key(episode)
    fps = get_fps(db)

    # Add chapters to the video file
    language = db[k_ep]['audio']['lang']
    lang_str = '' if language == 'fr' or task=='final' else f"_{language}"

    suffix = '' if task == '' or task == 'final' else f"_{task}"

    cache_directory: str = db[k_ep]['cache_path']
    input_filename = f"{k_ep}_no_chapters{suffix}{lang_str}.mkv"
    input_filepath = os.path.join(cache_directory, input_filename)

    output_directory = db['common']['directories']['outputs']
    os.makedirs(output_directory, exist_ok=True)
    final_filename = f"{k_ep}{suffix}{lang_str}.mkv"
    final_filepath = os.path.join(output_directory, final_filename)

    print(lightgreen(f"Add chapters:"), lightcyan(f"{k_ep}"))
    print(f"\tFinal file: {final_filepath}")

    # Create file for chapters
    chapters_filepath = absolute_path(
        os.path.join(
            cache_directory,
            "concat",
            f"{k_ep}_chapters{lang_str}.txt"
        )
    )
    chapters_file = open(chapters_filepath, "w")

    index: str = 0
    count: str = 0

    chapters_file.write(f"CHAPTER0{index}=00:00:00.000\n")
    chapters_file.write(f"CHAPTER0{index}NAME={CHAPTER_NAMES[language][0]}\n")
    count += db['g_debut']['audio']['count']

    chapter = 'precedemment'
    if db[k_ep]['audio'][chapter]['count'] > 0:
        index += 1
        chapters_file.write(f"CHAPTER0{index}={frame_to_sexagesimal(count, fps)}0\n")
        chapters_file.write(f"CHAPTER0{index}NAME={CHAPTER_NAMES[language][1]}\n")

        video_count = db[k_ep]['video']['target'][chapter]['avsync']
        video_count += db[k_ep]['video']['target'][chapter]['count']
        # video_count += ms_to_frame(db['g_debut']['audio'][chapter]['silence'], fps)
        count += video_count

    chapter = 'episode'
    # print(f"{chapter}: {count}")
    index += 1
    chapters_file.write(f"CHAPTER0{index}={frame_to_sexagesimal(count, fps)}0\n")
    chapters_file.write(f"CHAPTER0{index}NAME={CHAPTER_NAMES[language][2]}\n")
    video_count = db[k_ep]['video']['target'][chapter]['avsync']
    video_count += db[k_ep]['video']['target'][chapter]['count']
    video_count += ms_to_frame(db[k_ep]['audio'][chapter]['silence'], fps)
    count += video_count

    chapter = 'asuivre'
    # print(f"{chapter}: {count}")
    if db[k_ep]['audio'][chapter]['count'] > 0:
        index += 1
        chapters_file.write(f"CHAPTER0{index}={frame_to_sexagesimal(count, fps)}0\n")
        chapters_file.write(f"CHAPTER0{index}NAME={CHAPTER_NAMES[language][3]}\n")

        audio_duration = db[k_ep]['audio']['g_'+chapter]['avsync']
        audio_duration += db[k_ep]['audio']['g_'+chapter]['duration']
        audio_duration += db[k_ep]['audio'][chapter]['duration']
        audio_duration += db[k_ep]['audio'][chapter]['silence']
        count += ms_to_frame(audio_duration, fps)

    chapter = 'documentaire'
    # print(f"{chapter}: {count}")
    index += 1
    chapters_file.write(f"CHAPTER0{index}={frame_to_sexagesimal(count, fps)}0\n")
    chapters_file.write(f"CHAPTER0{index}NAME={CHAPTER_NAMES[language][4]}\n")

    audio_duration = db[k_ep]['audio']['g_'+chapter]['avsync']
    audio_duration += db[k_ep]['audio']['g_'+chapter]['duration']
    audio_duration += db[k_ep]['audio'][chapter]['duration']
    audio_duration += db[k_ep]['audio'][chapter]['silence']
    count += ms_to_frame(audio_duration, fps)

    index += 1
    chapter = 'g_fin'
    # print(f"{chapter}: {count}")
    chapters_file.write(f"CHAPTER0{index}={frame_to_sexagesimal(count, fps)}0\n")
    chapters_file.write(f"CHAPTER0{index}NAME={CHAPTER_NAMES[language][5]}\n")

    chapters_file.close()

    mkvmerge_command: list[str] = [
        mkvmerge_exe,
        '--quiet',
        '--chapters', chapters_filepath,
        '--output', final_filepath,
        input_filepath
    ]

    main_logger.debug(' '.join(mkvmerge_command))
    if not simulation:
        run_simple_command(mkvmerge_command)


