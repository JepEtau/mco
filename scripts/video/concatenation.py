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
    get_duration,
    execute_ffmpeg_command,
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

    # Use a single concatenation file for
    #   - g_asuivre, g_reoportage
    #   - precedemment
    #   - asuivre
    if k_part in ['g_asuivre', 'g_reportage', 'precedemment', 'asuivre']:
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
    hash = shot['last_step']['hash']
    k_ed = shot['k_ed']
    if (previous_concatenation_filepath == ''
        or len(images_filepath) >= 5):
        # Use previous concatenation files because FFmpeg
        # cannot create a video file from less than 5 frames
        if k_part in ['g_debut', 'g_fin']:
            concatenation_filepath = os.path.join(
                db[k_part]['cache_path'], "concatenation",
                "%s_%03d__%s_%s_.txt" % (k_part, shot['no'], k_ed, k_ep))
        else:
            concatenation_filepath = os.path.join(
                db[k_ep]['cache_path'], "concatenation",
                "%s_%s_%03d__%s_.txt" % (k_ep, k_part, shot['no'], k_ed))

        # Save this filepath because it may be used for next shot
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
    duration_str = "duration %.02f\n" % (1/float(db['common']['fps']))

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
    print_cyan("create_concatenation_file_video %s:%s" % (k_ep, k_part))
    pprint(video_files)

    for k_ep_or_g in [k_ep, 'g_debut', 'g_fin']:

        if k_ep_or_g in ['g_debut', 'g_fin']:
            k_part = k_ep_or_g
            suffix = "%s" % (k_part)
        else:
            suffix = "%s_%s" % (k_ep, k_part)
            k_part = ''

        # Folder used to store concatenation file
        create_folder_for_concatenation(db, k_ep, k_part)

        # Open concatenation file
        cache_directory = db[k_ep_or_g]['cache_path']
        concatenation_filepath = os.path.join(cache_directory,
            "concatenation", "%s.txt" % (suffix))
        concatenation_file = open(concatenation_filepath, "w")
        print_green("create_concatenation_file_video: %s" % (concatenation_filepath))

        if k_part in ['g_debut', 'g_fin']:
            for k_p in K_PARTS:
                for shot in video_files[k_p]:
                    filepath = shot['path']
                    hash = shot['hash']

                    p = filepath.replace('.txt', '_%s_%s.mkv' % (hash, shot['last_task']))
                    p = p.replace('concatenation', 'video')
                    concatenation_file.write("file \'%s\' \n" % (p))
        else:
            for k_p in K_PARTS:
                for shot in video_files[k_p]:
                    filepath = shot['path']
                    hash = shot['hash']

                    p = filepath.replace('.txt', '_%s.mkv' % (hash))
                    p = p.replace('concatenation', 'video')
                    concatenation_file.write("file \'%s\' \n" % (p))
        concatenation_file.close()
        sys.exit()
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

            print("%s create silence after %s" % (current_datetime_str(), k_p))

            # Convert silence duration in nb of frames
            # print(db[k_ep]['audio'][k_p]['silence'])
            silence_count = int(db[k_ep]['audio'][k_p]['silence'] * FPS / 1000)
            # print("silence = %d frames" % (silence_count))

            # Frame duration
            black_image_filepath = os.path.join(db['common']['directories']['cache'], 'black.png')
            duration_str = "duration %.02f\n" % (1/float(db['common']['fps']))

            # Create the concatenation file for the silence
            create_folder_for_concatenation(db, k_ep)
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
    input_filename = video_shot['path']
    shot_filepath = input_filename.replace("concatenation", "video")
    suffix = "_%s" % (video_shot['hash'])
    if video_shot['last_task'] != '':
        suffix += "_%s" % (video_shot['last_task'])
    shot_filepath = shot_filepath.replace('.txt', '%s.mkv' % (suffix))

    print("%s.combine_images_into_video: %s: %s -> %s" % (__name__, k_part, input_filename, shot_filepath))

    if not os.path.exists(shot_filepath) or force:
        print("%s concatenate images to %s" % (current_datetime_str(), shot_filepath))
        db_settings = db_common['settings']

        ffmpeg_command = [db_common['tools']['ffmpeg']]
        ffmpeg_command.extend(db_settings['verbose'].split(' '))
        ffmpeg_command.extend([
            "-r", str(FPS),
            "-f", "concat",
            "-safe", "0",
            "-i", input_filename,
            "-pix_fmt", db_settings['video_pixel_format']
        ])

        ffmpeg_command.extend(db_settings['video_quality'].split(' '))

        if 'reportage' in k_part:
            ffmpeg_command.extend(db_settings['video_film_tune'].split(' '))
        else:
            ffmpeg_command.extend(db_settings['video_tune'].split(' '))
        ffmpeg_command.extend(["-y", shot_filepath])

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



def merge_audio_and_video_tracks(db, k_ep_or_g, force=False):
    # Output filepath
    print("merge_audio_and_video_tracks: %s" % (k_ep_or_g))
    if k_ep_or_g in ['g_debut', 'g_fin']:
        cache_path = db[k_ep_or_g]['cache_path']
        audio_video_filepath = os.path.join(cache_path, "%s.mkv" % (k_ep_or_g))
    else:
        cache_path = db[k_ep_or_g]['cache_path']
        audio_video_filepath = os.path.join(cache_path, "%s_av.mkv" % (k_ep_or_g))

    if os.path.exists(audio_video_filepath) and not force:
        return

    # Get nb of frames from video stream
    if k_ep_or_g in ['g_debut', 'g_fin']:
        video_filepath = os.path.join(cache_path, "video", "%s_video_%s.mkv" % (
            k_ep_or_g, db[k_ep_or_g]['video']['hash']))
    else:
        # TODO k_part is missing...
        video_filepath = os.path.join(cache_path, "video", "%s_video_%s.mkv" % (
            k_ep_or_g, db[k_ep_or_g]['target']['video'][k_part]['hash']))

    video_frames_count = int(get_duration(db, video_filepath, integrity=False) * FPS)

    # Get equivalent nb of frames from audio stream
    audio_filepath = os.path.join(cache_path, "audio", "%s_audio.%s" % (k_ep_or_g, db['common']['settings']['audio_format']))
    channels_count, sample_rate, in_track, duration = read_audio_file(audio_filepath)
    audio_frames_count = int(duration*FPS)

    print("%s %s: merge audio and video: %s" % (current_datetime_str(), k_ep_or_g, audio_video_filepath))
    print("\t\tvideo: %s: %d" % (video_filepath, video_frames_count))
    print("\t\taudio: %s: %d" % (audio_filepath, audio_frames_count))

    # Cannot continue if nb of frames differ
    if audio_frames_count != video_frames_count:
        sys.exit("Error: %s.merge_audio_and_video_tracks: nb of frames differs" % (__name__))

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
    std = execute_ffmpeg_command(db, command=ffmpeg_command, filename=audio_video_filepath)
    if len(std) > 0:
        print(std)



def concatenate_shots(db, k_ep:str, k_part:str, video_files:dict, force:bool=False):
    print_cyan("concatenate_shots %s:%s" % (k_ep, k_part))
    # pprint(video_files)
    if k_part in ['g_debut', 'g_fin']:
        suffix = "%s_video" % (k_part)
        k_ep_or_g = k_part
    else:
        suffix = "%s_%s" % (k_ep, k_part)
        k_ep_or_g = k_ep

    # Folder used to store concatenation file
    create_folder_for_concatenation(db, k_ep, k_part)

    # Open concatenation file
    cache_directory = db[k_ep_or_g]['cache_path']
    concatenation_filepath = os.path.join(cache_directory,
        "concatenation", "%s_%s.txt" % (suffix, video_files['hash']))
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
        p = filepath.replace('.txt', '_%s.mkv' % (hash))
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
    std = execute_ffmpeg_command(db, command=ffmpeg_command, filename=output_filepath)
    print(std)



def concatenate_all_clips(db, k_ep:str, force=False) -> None:
    cache_directory = db[k_ep]['cache_path']
    output_filename = "%s_full.mkv" % (k_ep)
    output_filepath = os.path.join(cache_directory, output_filename)

    if os.path.exists(output_filepath) and not force:
        return

    # Create concatenation file
    create_folder_for_concatenation(db, k_ep)
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
    std = execute_ffmpeg_command(db, command=ffmpeg_command, filename=output_filename)
    if len(std) > 0:
        print(std)



def add_chapters(db, k_ep:str) -> str:
    cache_directory = db[k_ep]['cache_path']

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
    std = execute_ffmpeg_command(db, command=command_mkvmerge, filename=final_filepath)
    if len(std) > 0:
        print(std)
