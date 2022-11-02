#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from pprint import pprint

from utils.common import K_ALL_PARTS
from utils.common import get_k_part_from_frame_no
from utils.common import get_shot_from_frame_no_new
from video.concatenation import combine_images_into_video
from video.concatenation import concatenate_shots
from video.concatenation import create_concatenation_file
from video.concatenation import create_concatenation_file_silence
from video.concatenation import create_concatenation_file_video
from utils.ffmpeg import ffmpeg_execute_command

# from utils.concatenation import *
from utils.path import create_video_directory
from utils.time_conversions import current_datetime_str

from video.effects import *
from video.shots import *


def generate_video(db, episode_no:int, tasks:list, cpu_count=0, edition='', k_part:str='', force:bool=False, simulation:bool=False, shot_min:int=0, shot_max:int=999999):
    k_ep = 'ep%02d' % (episode_no)

    # Create the video directory
    create_video_directory(db, k_ep)

    # Generate a black frame for silences
    if not simulation:
        create_black_frame(db, tasks[-1])

    # List video files for each
    video_files = dict()
    for k in K_ALL_PARTS:
        video_files[k] = list()

    # print("Generate video: %s, %s, tasks=%s" % (edition, k_ep, ', '.join(tasks)))

    # Process part(s)
    k_parts = K_ALL_PARTS if k_part == '' else [k_part]
    for k_p in k_parts:

        if k_p in ['g_debut', 'g_fin']:
            db_video = db[k_p]['common']['video']
            k_episode = db[k_p]['common']['video']['reference']['k_ep']
            create_video_directory(db, k_p)
        else:
            db_video = db[k_ep]['common']['video'][k_p]
            k_episode = k_ep

        if db_video['count'] == 0:
            continue

        if 'shots' not in db_video.keys():
            # print("\t\tnot shot defined in %s, ignoring" % (k_p))
            continue
        print("%s %s: extract and process images" % (current_datetime_str(), k_p))

        previous_concatenation_filepath = ''

        # Walk through shots
        shots = db_video['shots']
        for shot in shots:
            if not (shot_min <= shot['no'] < shot_max):
                continue

            # Select the shot used for the generation
            # print("\n++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            # print("target:")
            # pprint(shot)
            # sys.exit()
            if 'src' in shot.keys() and shot['src']['use']:
                k_ed_src = shot['src']['k_ed']
                k_ep_src = shot['src']['k_ep']
                k_part_src = get_k_part_from_frame_no(db, k_ed=k_ed_src, k_ep=k_ep_src, frame_no=shot['src']['start'])
                # pprint(shot)
                # print("\nfind %d  in %s:%s:%s" % (shot['src']['start'], k_ed_src, k_ep_src, k_part_src))
                shot_src = deepcopy(get_shot_from_frame_no_new(db,
                    shot['src']['start'], k_ed=k_ed_src, k_ep=k_ep_src, k_part=k_part_src))

                if 'count' not in shot['src'].keys():
                    shot['src']['count'] = shot_src['count']
                if ((shot['src']['start'] + shot['src']['count']) > (shot_src['start'] + shot_src['count'])
                    and 'effects' not in shot.keys()):
                    print("error: cannot generate shot as the source has not enough frames src: start=%d" % (shot['src']['start']))
                    print("target:")
                    pprint(shot)
                # print("source:")
                # pprint(shot_src)
                # print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n")
                # sys.exit()
            else:
                k_ed_src = db[k_episode]['common']['video']['reference']['k_ed']
                k_ep_src = k_episode
                k_part_src = k_p
                shot_src = deepcopy(shot)

            print("\t\t%s: %s\t(%d)\t<- %s:%s:%s %d (%d)" % (
                "{:3d}".format(shot['no']),
                "{:5d}".format(shot['start']),
                shot['count'],
                k_ed_src,
                k_ep_src,
                k_part_src,
                shot_src['start'],
                shot_src['count']),
                flush=True)

            if (k_part_src in db[k_ep_src]['common']['video'].keys()
                and 'layers' in db[k_ep_src]['common']['video'][k_part_src].keys()):
                # print("Layer specified", db[k_ep_src]['common']['video'][k_part_src]['layers'])
                shot_src.update({
                    'layers': db[k_ep_src]['common']['video'][k_part_src]['layers']
                })

            shot_src.update({
                'k_ed': k_ed_src,
                'k_ep': k_ep_src,
                'k_part': k_part_src,
                'tasks': tasks.copy(),
            })
            if 'effects' in shot.keys():
                shot_src.update({'effects': shot['effects']})
            if 'dst' in shot.keys():
                shot_src['dst'] = shot['dst']
            if shot == shots[-1]:
                shot_src['last'] = True

            # Generate frames for this shot
            if not simulation:
                process_shot(db,
                    shot=shot_src,
                    db_combine={},
                    cpu_count=cpu_count)
            else:
                consolidate_shot(db, shot=shot_src)

            # Patch the shot to create the concatenation file
            if 'src' in shot.keys() and shot['src']['use']:
                shot_properties_saved = ({'start': shot_src['start'], 'count': shot_src['count']})
                shot_src.update({
                    'start': shot['src']['start'],
                    'count': shot['src']['count']
                })
            shot_src['count'] = shot['count']

            # Create concatenation file
            tmp = create_concatenation_file(db,
                k_ep=k_episode, k_part=k_p, shot=shot_src,
                previous_concatenation_filepath=previous_concatenation_filepath)
            if tmp != previous_concatenation_filepath and tmp != '':
                # Add the filepath to the the concatenation video file
                video_files[k_p].append(tmp)
            previous_concatenation_filepath = tmp

            # Restore shot values
            if 'src' in shot.keys() and shot['src']['use']:
                shot_src.update(shot_properties_saved)


    # Combine images to mkv
    for kp, files in video_files.items():
        if k_part != '' and kp != k_part or simulation:
            # Do not combine when a single part has to be processed
            continue

        for f in files:
            combine_images_into_video(db, k_part=kp, files=f, force=force, simulation=simulation)

    if k_part in ['g_debut', 'g_fin']:
        return

    # Concatenate shots in a single clip
    for k_p, filepaths in video_files.items():
        if len(filepaths) > 1 and not simulation:
            concatenate_shots(db, k_ed=edition, k_ep=k_ep, k_part=k_p, video_files=video_files, force=force)


    # Create concatenation files and video files for silences
    if k_part == '' and not simulation:
        # Only if a full generation is asked
        video_files_tmp = create_concatenation_file_silence(db, k_ed=edition, k_ep=k_ep)
        for k_p, filepaths in video_files_tmp.items():
            video_files[k_p] += filepaths
            for f in filepaths:
                # print("%s: %s" % (k_p, f))
                combine_images_into_video(db, k_part=k_p, files=f, force=force, simulation=simulation)


    # Concatenate video clips from all parts
    if k_part == '' and not simulation:
        # Generate a concatenation file that contains all video files except g_debut and g_fin
        concatenation_filepath = create_concatenation_file_video(db, edition, k_ep, video_files)

        # Concatenate video clips
        episode_video_filepath = os.path.join(db[k_ep]['common']['path']['cache'],
            "video", "%s_video.mkv" % (k_ep))
        if not os.path.exists(episode_video_filepath) or force:
            print("%s concatenate video clips to %s" % (current_datetime_str(), episode_video_filepath))
            command_ffmpeg = [db['common']['settings']['ffmpeg_exe']]
            command_ffmpeg.extend(db['common']['settings']['verbose'].split(' '))
            command_ffmpeg.extend([
                "-f", "concat",
                "-safe", "0",
                "-i", concatenation_filepath,
                "-c", "copy",
                "-y", episode_video_filepath
            ])
            std = ffmpeg_execute_command(command_ffmpeg, filename=episode_video_filepath)
            if len(std) > 0:
                print(std)




