# -*- coding: utf-8 -*-
import sys
import os
from pprint import pprint

from audio.utils import read_single_track_audio_file
from utils.common import (
    FPS,
    K_PARTS,
)
from utils.ffmpeg import (
    get_duration,
    ffmpeg_execute_command,
)
from utils.get_framelist import (
    get_framelist,
    get_framelist_2,
)
from utils.path import create_folder_for_concatenation
from utils.time_conversions import (
    ms_to_frames,
    current_datetime_str,
    frame2sexagesimal,
)



def create_concatenation_file(db, k_ep, k_part, shot, previous_concatenation_filepath=''):
    if k_part in ['g_debut',
                    'precedemment',
                    'g_asuivre',
                    'asuivre',
                    'g_reportage',
                    'g_fin']:
        return create_concatenation_file_2(db,
                    k_ep=k_ep, k_part=k_part, shot=shot,
                    previous_concatenation_filepath=previous_concatenation_filepath)

    # This function is used for the following parts:
    #   - episode
    #   - reportage

    # Get the list of images
    images_filepath = get_framelist(db, k_ep, k_part, shot)

    # Open concatenation file
    create_folder_for_concatenation(db, k_ep)
    if len(images_filepath) >= 5 or previous_concatenation_filepath == '':
        k_ed = shot['k_ed']
        concatenation_filepath = os.path.join(db[k_ep]['common']['path']['cache'],
            "concatenation",
            "%s_%s__%s__%05d.txt" % (k_ep, k_part, k_ed, shot['start']))
        previous_concatenation_filepath = concatenation_filepath
        concatenation_file = open(concatenation_filepath, "w")
    else:
        print("\t\t\tuse previous concatenation file: %s" % (previous_concatenation_filepath))
        concatenation_file = open(previous_concatenation_filepath, 'a')

    # Frame duration
    duration_str = "duration %.02f\n" % (1/float(db['common']['fps']))

    # Write into the concatenation file
    for p in images_filepath:
        concatenation_file.write("file \'%s\' \n" % (p))
        concatenation_file.write(duration_str)
    concatenation_file.close()

    return previous_concatenation_filepath



def create_concatenation_file_2(db, k_ep, k_part, shot, previous_concatenation_filepath=''):
    # print("%s._create_concatenation_file" % (__name__))
    # pprint(shot)
    # This function is used for the following parts:
    #   - precedemment
    #   - asuivre
    #   - g_asuivre
    #   - g_reportage
    k_ep_or_g = k_ep if k_part not in ['g_debut', 'g_fin'] else k_part

    # Get the list of images
    images_filepath = get_framelist_2(db, k_ep=k_ep, k_part=k_part, shot=shot)

    # Open concatenation file
    create_folder_for_concatenation(db, k_ep_or_g)
    if previous_concatenation_filepath == '':
        # Create the concatenation file
        k_ed = shot['k_ed']
        if k_part in ['g_debut', 'g_fin']:
            # Use the edition/episode defined as reference
            k_ed_ref = db[k_part]['common']['video']['reference']['k_ed']
            k_ep_ref = db[k_part]['common']['video']['reference']['k_ep']
            concatenation_filepath = os.path.join(
                db[k_ep_or_g]['common']['path']['cache'],
                "concatenation",
                "%s_video.txt" % (k_ep_or_g))
        else:
            concatenation_filepath = os.path.join(db[k_ep_or_g]['common']['path']['cache'],
                "concatenation", "%s_%s__%s__%05d.txt" % (k_ep, k_part, k_ed, 0))
        previous_concatenation_filepath = concatenation_filepath
        concatenation_file = open(concatenation_filepath, "w")
    else:
        # Use the previous one
        concatenation_file = open(previous_concatenation_filepath, "a")

    # Frame duration
    duration_str = "duration %.02f\n" % (1/float(db['common']['fps']))

    # Write into the concatenation file
    for p in images_filepath:
        concatenation_file.write("file \'%s\' \n" % (p))
        concatenation_file.write(duration_str)
    concatenation_file.close()

    return previous_concatenation_filepath



def create_concatenation_file_video(db, edition, k_ep, video_files:dict):
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
    create_folder_for_concatenation(db, k_ep)
    concatenation_filepath = os.path.join(db[k_ep]['common']['path']['cache'],
        "concatenation",
        "%s_%s.txt" % (k_ep, edition))
    concatenation_file = open(concatenation_filepath, "w")
    for k in K_PARTS:
        for f in video_files[k]:
            p = f.replace('.txt', '.mkv')
            p = p.replace('concatenation', 'video')
            concatenation_file.write("file \'%s\' \n" % (p))
    concatenation_file.close()

    return concatenation_filepath



def create_concatenation_file_silence(db, k_ed, k_ep):
    # Create a concatenation file for silence
    files = dict()
    for k_p in K_PARTS:
        files[k_p] = list()
        # print("%s:%s:%s" % (k_ed, k_ep, k_p))
        if k_p not in db[k_ep]['common']['audio'].keys():
            continue

        if ('silence' in db[k_ep]['common']['audio'][k_p].keys()
                and db[k_ep]['common']['audio'][k_p]['silence'] > 0):

            print("%s create silence after %s" % (current_datetime_str(), k_p))

            # Convert silence duration in nb of frames
            # print(db[k_ep]['common']['audio'][k_p]['silence'])
            silence_count = int(db[k_ep]['common']['audio'][k_p]['silence'] * FPS / 1000)
            # print("silence = %d frames" % (silence_count))

            # Frame duration
            black_image_filepath = os.path.join(db['common']['directories']['cache'],
                'black.%s' % (db['common']['settings']['frame_format']))
            duration_str = "duration %.02f\n" % (1/float(db['common']['fps']))

            # Create the concatenation file for the silence
            create_folder_for_concatenation(db, k_ep)
            concatenation_filepath = os.path.join(db[k_ep]['common']['path']['cache'],
                "concatenation",
                "%s_%s__%s__999_silence.txt" % (k_ep, k_p, k_ed))
            concatenation_file = open(concatenation_filepath, "w")

            # Add frames to the files
            for i in range(silence_count):
                concatenation_file.write("file \'%s\' \n" % (black_image_filepath))
                concatenation_file.write(duration_str)

            files[k_p].append(concatenation_filepath)

            concatenation_file.close()

    return files



def combine_images_into_video(db_settings, k_part, input_filename, force=False, simulation:bool=False):
    shot_filepath = input_filename.replace("concatenation", "video")
    shot_filepath = shot_filepath.replace('.txt', '.mkv')

    # print("%s.combine_images_into_video: %s: %s -> %s" % (__name__, k_part, files, shot_filepath))

    if not os.path.exists(shot_filepath) or force:
        print("%s concatenate images to %s" % (current_datetime_str(), shot_filepath))

        filter_complexStr = "[0]setsar=1[outv]"
        command_ffmpeg = [['ffmpeg_exe']]
        command_ffmpeg.extend(db_settings['verbose'].split(' '))

        # rework this with settings from database
        command_ffmpeg.extend([
            "-r", str(FPS),
            "-f", "concat",
            "-safe", "0",
            "-i", input_filename,
            "-filter_complex", filter_complexStr, "-map", "[outv]",
            "-pix_fmt", db_settings['video_pixel_format']])
        command_ffmpeg.extend(db_settings['video_quality'].split(' '))
        if 'reportage' in k_part:
            command_ffmpeg.extend(db_settings['video_film_tune'].split(' '))
        else:
            command_ffmpeg.extend(db_settings['video_tune'].split(' '))
        command_ffmpeg.extend(["-y", shot_filepath])

        if simulation:
            return

        std = ffmpeg_execute_command(command_ffmpeg, filename=shot_filepath)
        if len(std) > 0:
            print("returned:")
            print(std)
            print("--------------------")
            if "Impossible to open" in std:
                if os.path.exists(shot_filepath):
                    os.remove(shot_filepath)
                sys.exit("error: cannot create %s" % (shot_filepath))



def merge_audio_and_video_tracks(db, k_ep, force=False):
    # Output filepath
    # print("%s.merge_audio_and_video_tracks: %s" % (__name__, k_ep))
    suffix = "" if k_ep in ['g_debut', 'g_fin'] else "_audio_video"
    audio_video_filepath = os.path.join(
        db[k_ep]['common']['path']['cache'],
        "%s%s.mkv" % (k_ep, suffix))
    if os.path.exists(audio_video_filepath) and not force:
        return

    # Get nb of frames from video stream
    video_filepath = os.path.join(db[k_ep]['common']['path']['cache'], "video", "%s_video.mkv" % (k_ep))
    video_frames_count = int(get_duration(db, video_filepath, integrity=False) * FPS)

    # Get equivalent nb of frames from audio stream
    audio_filepath = os.path.join(db[k_ep]['common']['path']['cache'], "audio", "%s_audio.%s" % (k_ep, db['common']['settings']['audio_format']))
    sample_rate, in_track, duration = read_single_track_audio_file(audio_filepath)
    audio_frames_count = int(duration*FPS)

    print("%s %s: merge audio and video: %s" % (current_datetime_str(), k_ep, audio_video_filepath))
    print("\t\tvideo: %s: %d" % (video_filepath, video_frames_count))
    print("\t\taudio: %s: %d" % (audio_filepath, audio_frames_count))

    # Cannot continue if nb of frames differ
    if audio_frames_count != video_frames_count:
        sys.exit("Error: %s.merge_audio_and_video_tracks: nb of frames differs" % (__name__))

    # Merge Audio and Video tracks
    command_ffmpeg = [db['common']['settings']['ffmpeg_exe']]
    command_ffmpeg.extend(db['common']['settings']['verbose'].split(' '))
    command_ffmpeg.extend([
        "-i", video_filepath,
        "-i", audio_filepath,
        "-c:v", "copy",
        "-c:a", "copy",
        "-shortest",
        "-y", audio_video_filepath])
    std = ffmpeg_execute_command(command_ffmpeg, filename=audio_video_filepath)
    if len(std) > 0:
        print(std)



def concatenate_shots(db, k_ed:str, k_ep:str, k_part:str, video_files:dict, force:bool=False):
    cache_directory = db[k_ep]['common']['path']['cache']

    # Concatenation file
    create_folder_for_concatenation(db, k_ep)
    concatenation_filepath = os.path.join(cache_directory,
        "concatenation",
        "%s_%s__%s.txt" % (k_ep, k_part, k_ed))

    # Output video file
    output_filepath = concatenation_filepath.replace('concatenation', 'video')
    output_filepath = output_filepath.replace('.txt', '.mkv')
    if os.path.exists(output_filepath) and not force:
        return

    # Create concatenation file
    concatenation_file = open(concatenation_filepath, "w")
    for f in video_files[k_part]:
        p = f.replace('.txt', '.mkv')
        p = p.replace('concatenation', 'video')
        concatenation_file.write("file \'%s\' \n" % (p))
    concatenation_file.close()

    # Patch the list of files
    video_files[k_part] = [concatenation_filepath]

    print("%s %s: concatenate shots into a single clip: %s" % (current_datetime_str(), k_part, output_filepath))
    # Concatenate shots into a single video
    command_ffmpeg = [db['common']['settings']['ffmpeg_exe']]
    command_ffmpeg.extend(db['common']['settings']['verbose'].split(' '))
    command_ffmpeg.extend([
                    "-f", "concat",
                    "-safe", "0",
                    "-i", concatenation_filepath,
                    "-c", "copy",
                    "-y", output_filepath])
    std = ffmpeg_execute_command(command=command_ffmpeg, filename=output_filepath)
    print(std)



def concatenate_all_clips(db, k_ep:str, force=False) -> None:

    cache_directory = db[k_ep]['common']['path']['cache']
    output_filename = "%s_full.mkv" % (k_ep)
    output_filepath = os.path.join(cache_directory, output_filename)

    if os.path.exists(output_filepath) and not force:
        return

    # Create concatenation file
    create_folder_for_concatenation(db, k_ep)
    concatenation_filepath = os.path.join(cache_directory, "concatenation", "%s.txt" % (k_ep))
    concatenation_filepath = os.path.normpath(os.path.join(os.getcwd(), concatenation_filepath))
    concatenation_file = open(concatenation_filepath, "w")

    p = os.path.join(db['g_debut']['common']['path']['cache'], "g_debut.mkv")
    concatenation_file.write("file \'%s\' \n" % (p))

    p = os.path.join(cache_directory, "%s_audio_video.mkv" % (k_ep))
    concatenation_file.write("file \'%s\' \n" % (p))

    p = os.path.join(db['g_fin']['common']['path']['cache'], "g_fin.mkv")
    concatenation_file.write("file \'%s\' \n" % (p))

    concatenation_file.close()


    # Concatenate files
    command_ffmpeg = [db['common']['settings']['ffmpeg_exe']]
    command_ffmpeg.extend(db['common']['settings']['verbose'].split(' '))
    command_ffmpeg.extend([
                    "-f", "concat",
                    "-safe", "0",
                    "-i", concatenation_filepath,
                    "-c", "copy",
                    "-y", output_filepath])
    std = ffmpeg_execute_command(command=command_ffmpeg, filename=output_filename)
    # print(std)



def add_chapters(db, k_ep:str) -> str:
    cache_directory = db[k_ep]['common']['path']['cache']

    # Create file for chapters
    chapters_filepath = os.path.join(cache_directory, "concatenation", "%s_chapters.txt" % (k_ep))
    chapters_filepath = os.path.normpath(os.path.join(os.getcwd(), chapters_filepath))
    chapters_file = open(chapters_filepath, "w")

    index = 0
    count = 0

    chapters_file.write("CHAPTER0%d=00:00:00.000\n" % (index))
    chapters_file.write("CHAPTER0%dNAME=Générique de début\n" % (index))
    count += db['g_debut']['common']['audio']['count']
    count += ms_to_frames(db['g_debut']['common']['audio']['silence'])

    k_part = 'precedemment'
    if db[k_ep]['common']['audio'][k_part]['count'] > 0:
        index += 1
        chapters_file.write("CHAPTER0%d=%s0\n" % (index, frame2sexagesimal(count)))
        chapters_file.write("CHAPTER0%dNAME=Précédemment\n" % (index))

        video_count = db[k_ep]['common']['video'][k_part]['avsync']
        video_count += db[k_ep]['common']['video'][k_part]['count']
        # video_count += ms_to_frames(db['g_debut']['common']['audio'][k_part]['silence'])
        count += video_count


    k_part = 'episode'
    # print("%s: %d" % (k_part, count))
    index += 1
    chapters_file.write("CHAPTER0%d=%s0\n" % (index, frame2sexagesimal(count)))
    chapters_file.write("CHAPTER0%dNAME=Episode\n" % (index))
    video_count = db[k_ep]['common']['video'][k_part]['avsync']
    video_count += db[k_ep]['common']['video'][k_part]['count']
    video_count += ms_to_frames(db[k_ep]['common']['audio'][k_part]['silence'])
    count += video_count


    k_part = 'asuivre'
    # print("%s: %d" % (k_part, count))
    if db[k_ep]['common']['audio'][k_part]['count'] > 0:
        index += 1
        chapters_file.write("CHAPTER0%d=%s0\n" % (index, frame2sexagesimal(count)))
        chapters_file.write("CHAPTER0%dNAME=A suivre\n" % (index))

        audio_duration = db[k_ep]['common']['audio']['g_'+k_part]['avsync']
        audio_duration += db[k_ep]['common']['audio']['g_'+k_part]['duration']
        audio_duration += db[k_ep]['common']['audio'][k_part]['duration']
        audio_duration += db[k_ep]['common']['audio'][k_part]['silence']
        count += ms_to_frames(audio_duration)

    k_part = 'reportage'
    # print("%s: %d" % (k_part, count))
    index += 1
    chapters_file.write("CHAPTER0%d=%s0\n" % (index, frame2sexagesimal(count)))
    chapters_file.write("CHAPTER0%dNAME=Reportage\n" % (index))

    audio_duration = db[k_ep]['common']['audio']['g_'+k_part]['avsync']
    audio_duration += db[k_ep]['common']['audio']['g_'+k_part]['duration']
    audio_duration += db[k_ep]['common']['audio'][k_part]['duration']
    audio_duration += db[k_ep]['common']['audio'][k_part]['silence']
    count += ms_to_frames(audio_duration)

    index += 1
    k_part = 'g_fin'
    # print("%s: %d" % (k_part, count))
    chapters_file.write("CHAPTER0%d=%s0\n" % (index, frame2sexagesimal(count)))
    chapters_file.write("CHAPTER0%dNAME=Générique de fin\n" %(index))

    chapters_file.close()

    # Merge chapters to the video file
    input_filename = "%s_full.mkv" % (k_ep)
    input_filepath = os.path.join(cache_directory, input_filename)

    final_filename = "%s.mkv" % (k_ep)
    final_filepath = os.path.join(cache_directory, final_filename)

    command_mkvmerge = [db['common']['settings']['mkvmerge_exe']]
    command_mkvmerge.extend([
                    "--chapters", chapters_filepath,
                    "-o", final_filepath,
                    input_filepath])
    print("%s Append chapters: %s" % (current_datetime_str(), final_filepath))
    std = ffmpeg_execute_command(command=command_mkvmerge, filename=final_filepath)
    # print(std)
