# -*- coding: utf-8 -*-
import sys
import os
from pprint import pprint

from audio.utils import read_audio_file
from utils.common import (
    FPS,
    K_ALL_PARTS,
    K_GENERIQUES,
    K_PARTS,
)
from filters.ffmpeg_utils import (
    execute_simple_ffmpeg_command,
    execute_ffmpeg_command,
    get_video_duration,
)
from utils.get_frame_list import (
    get_frame_list,
    get_frame_list_single,
)
from utils.get_image_list import get_image_list
from utils.path import create_folder_for_concatenation
from utils.pretty_print import *
from utils.time_conversions import (
    ms_to_frames,
    current_datetime_str,
    frame2sexagesimal,
)



def create_concatenation_file(db, k_ep, k_part, shot, previous_concatenation_filepath=''):
    print_lightgreen(f"Create concatenation file: ", end='')
    print_lightcyan(f"{k_ep}, {k_part}, shot no. {shot['no']}: ", end='')
    # Use a single concatenation file for
    #   - g_asuivre, g_reportage
    if k_part in ['g_asuivre', 'g_reportage']:
        return create_single_concatenation_file(db,
            k_ep=k_ep, k_part=k_part, shot=shot,
            previous_concatenation_filepath=previous_concatenation_filepath)

    # This function is used for the following parts:
    #   - episode
    #   - reportage

    # Get the list of images
    images_filepath = get_frame_list(db=db,
        k_ep=k_ep, k_part=k_part, shot=shot)

    # Folder for concatenation file
    create_folder_for_concatenation(db, k_ep, k_part)

    # Open concatenation file
    k_ed = shot['k_ed']
    if (previous_concatenation_filepath == ''
        or len(images_filepath) >= 5):
        # Use previous concatenation files because FFmpeg
        # cannot create a video file from less than 5 frames
        if k_part in ['g_debut', 'g_fin']:
            concatenation_filepath = os.path.join(
                db[k_part]['cache_path'],
                "concatenation",
                f"{k_part}_{shot['no']:03}__{k_ed}_{shot['k_ep']}_.txt")
        else:
            concatenation_filepath = os.path.join(
                db[k_ep]['cache_path'],
                "concatenation",
                f"{k_ep}_{k_part}_{shot['no']:03}__{k_ed}_.txt")

        # Save this filepath because it may be used for next shot
        previous_concatenation_filepath = concatenation_filepath
        concatenation_file = open(concatenation_filepath, "w")

    else:
        sys.exit(print_red("(TODO: deprecate) Use previous concatenation file: %s" % (previous_concatenation_filepath)))
        concatenation_file = open(previous_concatenation_filepath, 'a')

    print(f"{concatenation_filepath}")

    # Frame duration
    duration_str = "duration %.02f\n" % (1/FPS)

    # Write into the concatenation file
    for p in images_filepath:
        concatenation_file.write("file \'%s\' \n" % (p))
        concatenation_file.write(duration_str)
    concatenation_file.close()

    return previous_concatenation_filepath



def create_single_concatenation_file(db, k_ep, k_part, shot, previous_concatenation_filepath=''):
    """This function is used for the following parts:
        - precedemment
        - g_asuivre
        - asuivre
        - g_reportage
    """
    # print("%s._create_concatenation_file" % (__name__))
    # pprint(shot)
    k_ep_or_g = k_ep if k_part not in ['g_debut', 'g_fin'] else k_part

    # Get the list of images
    images_filepath = get_frame_list_single(db,
        k_ep=k_ep, k_part=k_part, shot=shot)

    # Folder for concatenation file
    create_folder_for_concatenation(db, k_ep, k_part)

    # Open concatenation file
    # hash = shot['last_step']['hash']
    k_ed = shot['k_ed']
    if previous_concatenation_filepath == '':
        # Create a concatenation file

        if k_part in ['g_debut', 'g_fin']:
            # Use the edition/episode defined as reference
            concatenation_filepath = os.path.join(
                db[k_ep_or_g]['cache_path'], "concatenation",
                "%s_video.txt" % (k_ep_or_g))
        else:
            concatenation_filepath = os.path.join(db[k_ep_or_g]['cache_path'],
                "concatenation", "%s_%s_%03d__%s_%s_.txt" % (k_ep, k_part, 0, k_ed, shot['src']['k_ep']))
        previous_concatenation_filepath = concatenation_filepath
        concatenation_file = open(concatenation_filepath, "w")

    else:
        # Use the previous concatenation file
        concatenation_file = open(previous_concatenation_filepath, "a")

    # Frame duration
    duration_str = "duration %.02f\n" % (1/FPS)

    # Write into the concatenation file
    for p in images_filepath:
        concatenation_file.write("file \'%s\' \n" % (p))
        concatenation_file.write(duration_str)
    concatenation_file.close()

    return previous_concatenation_filepath


def create_concatenation_file_video(db, k_ep, k_part, video_files:dict):
    """ This function creates a concatenation file which lists
        all video files to merge:
        - precedemment
        - episode
        - g_asuivre
        - asuivre
        - g_reportage
        - reportage

        Returns:
          Concatenation file path
    """
    verbose = False
    if verbose:
        print_lightcyan("create_concatenation_file_video %s:%s" % (k_ep, k_part))
        pprint(video_files)

    for k_ep_or_g in [k_ep, 'g_debut', 'g_fin']:

        if k_ep_or_g in ['g_debut', 'g_fin']:
            k_part = k_ep_or_g
            suffix = "%s" % (k_part)
        else:
            suffix = f"_{k_part}" if k_part != '' else ''
            suffix = f"{k_ep}{suffix}_video"
            k_part = ''

        # Folder used to store concatenation file
        create_folder_for_concatenation(db, k_ep, k_part)

        # Open concatenation file
        concatenation_filepath = os.path.join(
            db[k_ep_or_g]['cache_path'],
            "concatenation",
            f"{suffix}.txt")
        concatenation_file = open(concatenation_filepath, "w")
        if verbose:
            print_green("create_concatenation_file_video: %s" % (concatenation_filepath))

        if k_part in ['g_debut', 'g_fin']:
            for k_p in K_PARTS:
                for shot in video_files[k_p]:
                    p = shot['path'].replace('.txt', f"_{shot['hash']}_{shot['last_task']}.mkv")
                    p = p.replace('concatenation', 'video')
                    concatenation_file.write("file \'%s\' \n" % (p))
        else:
            for k_p in K_PARTS:
                try:
                    for filepath in video_files[k_p][k_p]:
                        p = filepath.replace('concatenation', 'video')
                        concatenation_file.write("file \'%s\' \n" % (p))
                except:
                    if k_p in K_GENERIQUES:
                        for shot in video_files[k_p]['shotlist']:
                            p = shot['path'].replace('.txt', f"_{shot['hash']}.mkv")
                            p = p.replace('concatenation', 'video')
                            concatenation_file.write("file \'%s\' \n" % (p))
        concatenation_file.close()
        return concatenation_filepath



def create_concatenation_file_silence(db, k_ep):
    # Create a concatenation file for silence
    files = dict()
    for k_p in K_PARTS:
        files[k_p] = list()
        # print("%s:%s" % (k_ep, k_p))
        if k_p not in db[k_ep]['audio'].keys():
            continue

        if ('silence' in db[k_ep]['audio'][k_p].keys()
                and db[k_ep]['audio'][k_p]['silence'] > 0):

            print_lightcyan(f"Create silence after {k_p}")

            # Convert silence duration in nb of frames
            # print(db[k_ep]['audio'][k_p]['silence'])
            silence_count = int(db[k_ep]['audio'][k_p]['silence'] * FPS / 1000)
            # print("silence = %d frames" % (silence_count))

            # Frame duration
            black_image_filepath = os.path.join(db['common']['directories']['cache'], 'black.png')
            duration_str = "duration %.02f\n" % (1/FPS)

            # Create the concatenation file for the silence
            create_folder_for_concatenation(db, k_ep, k_part=k_p)
            concatenation_filepath = os.path.join(db[k_ep]['cache_path'],
                "concatenation",
                "%s_%s__999_silence.txt" % (k_ep, k_p))
            concatenation_file = open(concatenation_filepath, "w")

            # Add frames to the files
            for i in range(silence_count):
                concatenation_file.write("file \'%s\' \n" % (black_image_filepath))
                concatenation_file.write(duration_str)

            files[k_p].append(concatenation_filepath)

            concatenation_file.close()

    return files



def combine_images_into_video(db_common, k_part, video_shot, force=False, simulation:bool=False):
    verbose = False

    input_filename = video_shot['path']
    shot_filepath = input_filename.replace("concatenation", "video")
    suffix = "_%s" % (video_shot['hash'])
    if video_shot['last_task'] != '':
        suffix += "_%s" % (video_shot['last_task'])
    shot_filepath = shot_filepath.replace('.txt', '%s.mkv' % (suffix))

    print_lightgreen(f"Combine images into video: ", end='')
    print_lightcyan(f"{k_part}: ", end='')
    print(f"{shot_filepath}")

    if not os.path.exists(shot_filepath) or force:
        db_settings = db_common['settings']

        ffmpeg_command = [db_common['tools']['ffmpeg']]
        ffmpeg_command.extend(db_settings['verbose'].split(' '))
        ffmpeg_command.extend([
            "-r", str(FPS),
            "-f", "concat",
            "-safe", "0",
            "-i", input_filename,
            "-pix_fmt", db_settings['video_pixel_format'],
            "-colorspace:v", "bt709",
            "-color_primaries:v", "bt709",
            "-color_trc:v", "bt709",
            "-color_range:v", "tv"
        ])

        ffmpeg_command.extend(db_settings['video_quality'].split(' '))

        if 'reportage' in k_part:
            ffmpeg_command.extend(db_settings['video_film_tune'].split(' '))
        else:
            ffmpeg_command.extend(db_settings['video_tune'].split(' '))
        ffmpeg_command.extend(["-y", shot_filepath])

        if verbose:
            print_green(ffmpeg_command)
        if simulation:
            return

        success = execute_simple_ffmpeg_command(ffmpeg_command=ffmpeg_command)
        if not success:
            print_red("error: failed to generate %s" % (shot_filepath))
            try:
                os.remove(shot_filepath)
            except:
                pass

    return None



def merge_audio_and_video_tracks(db, k_ep_or_g, last_task, force:bool=False, simulation:bool=False):
    # Output filepath
    print_lightgreen(f"Merge audio and video tracks: {k_ep_or_g}")
    if k_ep_or_g in ['g_debut', 'g_fin']:
        cache_path = db[k_ep_or_g]['cache_path']
        audio_video_filepath = os.path.join(cache_path, "%s.mkv" % (k_ep_or_g))
    else:
        cache_path = db[k_ep_or_g]['cache_path']
        audio_video_filepath = os.path.join(cache_path, "%s_av.mkv" % (k_ep_or_g))

    if os.path.exists(audio_video_filepath) and not force and not simulation:
        return

    suffix = '' if last_task == '' or last_task == 'final' else f"_{last_task}"

    # Get nb of frames from video stream
    if k_ep_or_g in ['g_debut', 'g_fin']:
        video_filepath = os.path.join(cache_path, "video",
            f"{k_ep_or_g}_video_{db[k_ep_or_g]['video']['hash']}{suffix}.mkv")
    else:
        video_filepath = os.path.join(cache_path, "video", f"{k_ep_or_g}_video.mkv")

    try:
        video_frames_count = get_video_duration(db['common'], video_filepath, integrity=False)[1]
    except:
        video_frames_count = 0

    # Get equivalent nb of frames from audio stream
    audio_filepath = os.path.join(cache_path, "audio", "%s_audio.%s" % (k_ep_or_g, db['common']['settings']['audio_format']))
    try:
        channels_count, sample_rate, in_track, duration = read_audio_file(audio_filepath)
    except:
        duration = 0
    audio_frames_count = int(duration*FPS)

    print(f"\tvideo: {video_filepath}: {video_frames_count}")
    print(f"\taudio: {audio_filepath}: {audio_frames_count}")
    print(f"\tAV file: {audio_video_filepath}")

    # Cannot continue if nb of frames differ
    if audio_frames_count != video_frames_count and not simulation:
        sys.exit(print_red(f"Error: cannot merge audio and video tracks: nb of frames differs"))

    # Merge Audio and Video tracks
    ffmpeg_command = [db['common']['tools']['ffmpeg']]
    ffmpeg_command.extend(db['common']['settings']['verbose'].split(' '))
    ffmpeg_command.extend([
        "-i", video_filepath,
        "-i", audio_filepath,
        "-c:v", "copy",
        "-c:a", "copy",
        "-shortest",
        "-y", audio_video_filepath
    ])
    if simulation:
        print_lightgrey(' '.join(ffmpeg_command))
    else:
        std = execute_ffmpeg_command(db, command=ffmpeg_command, filename=audio_video_filepath)
        if len(std) > 0:
            print(std)



def concatenate_shots(db, k_ep:str, k_part:str, video_files:dict,
                      force:bool=False, simulation:bool=False):
    verbose=False
    print_lightcyan(f"Concatenate shots: {k_ep}:{k_part}")
    if verbose:
        pprint(video_files)

    if k_part in ['g_debut', 'g_fin']:
        suffix = "%s_video" % (k_part)
        k_ep_or_g = k_part
    else:
        suffix = "%s_%s" % (k_ep, k_part)
        k_ep_or_g = k_ep

    # Folder used to store concatenation file
    create_folder_for_concatenation(db, k_ep, k_part)


    # Last task is the suffix
    last_task = video_files['shotlist'][0]['last_task']
    last_task_str = '' if last_task == '' else f"_{last_task}"

    # Open concatenation file
    cache_directory = db[k_ep_or_g]['cache_path']
    concatenation_filepath = os.path.join(cache_directory,
        "concatenation", f"{suffix}_{video_files['hash']}{last_task_str}.txt")
    concatenation_file = open(concatenation_filepath, "w")

    # Output video file
    output_filepath = concatenation_filepath.replace('concatenation', 'video')
    output_filepath = output_filepath.replace('.txt', '.mkv')
    if os.path.exists(output_filepath) and not force:
        return

    # Create concatenation file
    concatenation_file = open(concatenation_filepath, "w")
    for shot in video_files['shotlist']:
        filepath = shot['path']
        hash = shot['hash']
        p = filepath.replace('.txt', f"_{hash}{last_task_str}.mkv")
        p = p.replace('concatenation', 'video')
        concatenation_file.write("file \'%s\' \n" % (p))
    concatenation_file.close()

    # Patch the list of files
    video_files[k_part] = [concatenation_filepath]

    print("%s %s: concatenate shots into a single clip: %s" % (current_datetime_str(), k_part, output_filepath))
    # Concatenate shots into a single video
    ffmpeg_command = [db['common']['tools']['ffmpeg']]
    ffmpeg_command.extend(db['common']['settings']['verbose'].split(' '))
    ffmpeg_command.extend([
        "-f", "concat",
        "-safe", "0",
        "-i", concatenation_filepath,
        "-c", "copy",
        "-y", output_filepath
    ])
    if simulation:
        print_lightgrey(' '.join(ffmpeg_command))
    else:
        std = execute_ffmpeg_command(db, command=ffmpeg_command, filename=output_filepath)
        print(std)



def concatenate_all_clips(db, k_ep:str, force=False, simulation:bool=False) -> None:
    print_lightgreen(f"Concatenation all A/V clips: {k_ep}")

    cache_directory = db[k_ep]['cache_path']
    output_filename = f"{k_ep}_no_chapters.mkv"
    output_filepath = os.path.join(cache_directory, output_filename)
    print(f"\tA/V file (no chapters): {output_filepath}")

    if os.path.exists(output_filepath) and not force:
        return

    # Create concatenation file
    create_folder_for_concatenation(db, k_ep=k_ep, k_part='')
    concatenation_filepath = os.path.join(cache_directory, "concatenation", "%s.txt" % (k_ep))
    concatenation_filepath = os.path.normpath(os.path.join(os.getcwd(), concatenation_filepath))
    concatenation_file = open(concatenation_filepath, "w")

    p = os.path.join(db['g_debut']['cache_path'], "g_debut.mkv")
    concatenation_file.write("file \'%s\' \n" % (p))

    p = os.path.join(cache_directory, "%s_av.mkv" % (k_ep))
    concatenation_file.write("file \'%s\' \n" % (p))

    p = os.path.join(db['g_fin']['cache_path'], "g_fin.mkv")
    concatenation_file.write("file \'%s\' \n" % (p))

    concatenation_file.close()

    # Concatenate files
    ffmpeg_command = [db['common']['tools']['ffmpeg']]
    ffmpeg_command.extend(db['common']['settings']['verbose'].split(' '))
    ffmpeg_command.extend([
        "-f", "concat",
        "-safe", "0",
        "-i", concatenation_filepath,
        "-c", "copy",
        "-y", output_filepath
    ])
    if simulation:
        print_lightgrey(' '.join(ffmpeg_command))
    else:
        std = execute_ffmpeg_command(db, command=ffmpeg_command, filename=output_filename)
        if len(std) > 0:
            print(std)



def add_chapters(db, k_ep:str, simulation:bool=False) -> None:
    # Merge chapters to the video file

    cache_directory = db[k_ep]['cache_path']
    input_filename = f"{k_ep}_no_chapters.mkv" % ()
    input_filepath = os.path.join(cache_directory, input_filename)

    output_directory = db['common']['directories']['outputs']
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    final_filename = "%s.mkv" % (k_ep)
    final_filepath = os.path.join(output_directory, final_filename)

    print_lightgreen(f"Add chapters: {k_ep}")
    print(f"\tFinal file: {final_filepath}")

    # Create file for chapters
    chapters_filepath = os.path.join(cache_directory, "concatenation", "%s_chapters.txt" % (k_ep))
    chapters_filepath = os.path.normpath(os.path.join(os.getcwd(), chapters_filepath))
    chapters_file = open(chapters_filepath, "w")

    index = 0
    count = 0

    chapters_file.write("CHAPTER0%d=00:00:00.000\n" % (index))
    chapters_file.write("CHAPTER0%dNAME=Générique de début\n" % (index))
    count += db['g_debut']['audio']['count']
    count += ms_to_frames(db['g_debut']['audio']['silence'])

    k_part = 'precedemment'
    if db[k_ep]['audio'][k_part]['count'] > 0:
        index += 1
        chapters_file.write("CHAPTER0%d=%s0\n" % (index, frame2sexagesimal(count)))
        chapters_file.write("CHAPTER0%dNAME=Précédemment\n" % (index))

        video_count = db[k_ep]['video']['target'][k_part]['avsync']
        video_count += db[k_ep]['video']['target'][k_part]['count']
        # video_count += ms_to_frames(db['g_debut']['audio'][k_part]['silence'])
        count += video_count


    k_part = 'episode'
    # print("%s: %d" % (k_part, count))
    index += 1
    chapters_file.write("CHAPTER0%d=%s0\n" % (index, frame2sexagesimal(count)))
    chapters_file.write("CHAPTER0%dNAME=Episode\n" % (index))
    video_count = db[k_ep]['video']['target'][k_part]['avsync']
    video_count += db[k_ep]['video']['target'][k_part]['count']
    video_count += ms_to_frames(db[k_ep]['audio'][k_part]['silence'])
    count += video_count


    k_part = 'asuivre'
    # print("%s: %d" % (k_part, count))
    if db[k_ep]['audio'][k_part]['count'] > 0:
        index += 1
        chapters_file.write("CHAPTER0%d=%s0\n" % (index, frame2sexagesimal(count)))
        chapters_file.write("CHAPTER0%dNAME=A suivre\n" % (index))

        audio_duration = db[k_ep]['audio']['g_'+k_part]['avsync']
        audio_duration += db[k_ep]['audio']['g_'+k_part]['duration']
        audio_duration += db[k_ep]['audio'][k_part]['duration']
        audio_duration += db[k_ep]['audio'][k_part]['silence']
        count += ms_to_frames(audio_duration)

    k_part = 'reportage'
    # print("%s: %d" % (k_part, count))
    index += 1
    chapters_file.write("CHAPTER0%d=%s0\n" % (index, frame2sexagesimal(count)))
    chapters_file.write("CHAPTER0%dNAME=Reportage\n" % (index))

    audio_duration = db[k_ep]['audio']['g_'+k_part]['avsync']
    audio_duration += db[k_ep]['audio']['g_'+k_part]['duration']
    audio_duration += db[k_ep]['audio'][k_part]['duration']
    audio_duration += db[k_ep]['audio'][k_part]['silence']
    count += ms_to_frames(audio_duration)

    index += 1
    k_part = 'g_fin'
    # print("%s: %d" % (k_part, count))
    chapters_file.write("CHAPTER0%d=%s0\n" % (index, frame2sexagesimal(count)))
    chapters_file.write("CHAPTER0%dNAME=Générique de fin\n" %(index))

    chapters_file.close()


    mkvmerge_command = [db['common']['tools']['mkvmerge']]
    mkvmerge_command.extend([
                    "--chapters", chapters_filepath,
                    "-o", final_filepath,
                    input_filepath])
    if simulation:
        print_lightgrey(' '.join(mkvmerge_command))
    else:
        std = execute_ffmpeg_command(db, command=mkvmerge_command, filename=final_filepath)
        if len(std) > 0:
            print(std)
