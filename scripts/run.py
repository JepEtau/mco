#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import configparser
from pprint import pprint
import signal

import cv2

from parsers.parser_database import parse_database
from parsers.parser_stitching import *
from parsers.parser_common import *
from parsers.parser_editions import *
from parsers.parser_episodes import *
from parsers.parser_generiques import *

from utils.common import K_ALL_PARTS
from utils.common import K_GENERIQUES
from utils.common import get_database_size
from utils.common import delete_items
from utils.common import get_tasklist
from utils.path import PATH_DATABASE_COMBINE

from audio.audio import extract_audio
from audio.audio import generate_audio

from video.video import generate_video
from video.concatenation import merge_audio_and_video_tracks
from video.concatenation import concatenate_all_clips
from video.concatenation import add_chapters
from images.extract_frames import extract_frames_for_study

g_database = dict()
g_database_combine = dict()
study_mode = True


def main():
    # if cv2.ocl.haveOpenCL():
    #     cv2.ocl.setUseOpenCL(True)

    # from scripts.frames_extract import frames_extract
    verbose = False
    # editions = ['k', 'a', 's', 's0']
    editions = ['k', 'a', 's']


    # Arguments
    #---------------------------------------------------------------------------
    parser = argparse.ArgumentParser(description="Main tool")
    parser.add_argument("--episode",
        type=int,
        default=0,
        required=False,
        help="Numéro d'épisode de 1 à 39. Ignoré pour la génération des génériques.")

    parser.add_argument("--edition",
        default='',
        required=False,
        choices=editions,
        help="Utilise uniquement cette edition")

    parser.add_argument("--part",
        default='',
        required=False,
        choices=K_ALL_PARTS,
        help="Partie à traiter")


    parser.add_argument("--shot_min",
        type=int,
        default=0,
        required=False,
        help="plans à processer: début. NON VERIFIE")

    parser.add_argument("--shot_max",
        type=int,
        default=999999,
        required=False,
        help="plans à processer: fin. NON VERIFIE")

    parser.add_argument("--shot",
        type=int,
        default=-1,
        required=False,
        help="numéro du plan à processer")


    parser.add_argument("--vfilter",
        default='',
        required=False,
        choices=[
            'deinterlace',
            'pre_upscale',
            'upscale',
            'denoise',
            'bgd',
            'stitching',
            'sharpen',
            'rgb',
            'geometry',
            'final',
        ],
        help="Applique les filtres video jusqu\'à celui spécifié ici (note: final=geometry")

    parser.add_argument("--afilter",
        default='',
        required=False,
        choices=[
            'extract',
            'final'
        ],
        help="Applique les filtres audio jusqu\'à celui spécifié ici")

    parser.add_argument("--study",
        action="store_true",
        help="Utilisé pour les études des trames, des filtres, etc.")

    parser.add_argument("--frames",
        action="store_true",
        help="Utilisé pour les études des trames, des filtres, etc.")

    parser.add_argument("--compare",
        action="store_true",
        help="debug: utilisé pour comparer les éditions (non fonctionnel)")

    parser.add_argument("--force",
        action="store_true",
        required=False,
        help="debug: force")

    parser.add_argument("--simulate",
        action="store_true",
        required=False,
        help="debug: do not générate a/v files, generate concatenation files only")

    parser.add_argument("--parse_only",
        action="store_true",
        required=False,
        help="debug: parse only the database")

    arguments = parser.parse_args()


    if arguments.compare:
        mode = 'compare'
    else:
        mode = 'normal'

    # Edition
    list_editions = ['']
    if arguments.edition == '' and arguments.compare:
        list_editions = editions
    elif arguments.edition == '':
        list_editions = [editions[0]]
    elif arguments.edition != '':
        list_editions = [arguments.edition]
    elif arguments.compare:
        list_editions = [arguments.edition]


    # Episode no.
    episode_no = arguments.episode
    k_episode = 'ep%02d' % (episode_no)

    if episode_no == 0 and arguments.part == '':
        sys.exit("Error: épisode ou partie non spécifiée")

    # Consolidate tasks: what will be done
    print("Edition(s): %s" % (', '.join(list_editions)))
    print("Episode: %d" % (episode_no))
    if arguments.part != '':
        print("Part: %s" % (arguments.part))
    print("Tasks:")
    print("\t- parse database")
    print("\t- consolidate generiques")

    video_filter = arguments.vfilter.replace('final', 'geometry')
    do_av_merge = False
    if (not arguments.study
    and arguments.afilter == ''
    and not arguments.frames):
        if (arguments.part in ['g_debut', 'g_fin']
        or arguments.part == ''):
            print("\t- force processing audio and video")
            arguments.afilter = 'final'
            if video_filter == '':
                video_filter = 'geometry'
            do_av_merge = True
        elif arguments.part != '':
            if video_filter == '':
                video_filter = 'geometry'
            do_av_merge = True

    if arguments.parse_only:
        # Parse database only
        # Parse database
        parse_database(g_database, editions, k_ep=k_episode, mode=mode, verbose=verbose)
        gc.collect()
        print("database: %0.1fkB" % (get_database_size(g_database)/1000.0))

        if arguments.part in K_GENERIQUES:
            print("\t\t- %s: " % (arguments.part))
            pprint(g_database[arguments.part])

        elif arguments.part != '':
            print("\t\t- precedemment, episode, g_asuivre, asuivre, g_reportage, reportage: ")
            pprint(g_database[k_episode])
        else:
            print("\t\t- all: ", end='')

        sys.exit()

    if arguments.afilter != '':
        print("\t- audio:")
        if arguments.part in K_GENERIQUES:
            print("\t\t- %s: " % (arguments.part), end='')
        elif arguments.part != '':
            print("\t\t- precedemment, episode, g_asuivre, asuivre, g_reportage, reportage: ", end='')
        else:
            print("\t\t- all: ", end='')

        if arguments.afilter == 'extract':
            print("extract only")
        elif arguments.afilter == 'final':
            print("final")

    if arguments.frames and video_filter == '':
        # Force to final if vfilter is not specified
        video_filter = 'geometry'

    if video_filter != '':
        if arguments.frames:
            print("\t- frames:")
        else:
            print("\t- video:")

        if arguments.part != '':
            print("\t\t- %s" % (arguments.part))
        else:
            print("\t\t- all parts")
        print("\t\t- last task=%s" % (video_filter))

    if do_av_merge:
        # Full generation of this episode
        print("\t- merge audio and video")

        if arguments.part == '':
            print("\t- merge all parts")
            print("\t- add chapters")


    if arguments.frames and arguments.part=='':
        sys.exit("Error: a part shall be one of the following: %s" % (", ".join(K_ALL_PARTS)))

    # Parse database
    parse_database(g_database, editions, k_ep=k_episode, mode=mode, verbose=verbose)
    gc.collect()
    print("database: %0.1fkB" % (get_database_size(g_database)/1000.0))
    print("processing, please wait...", flush=True)

    # Audio
    #-------------------------------------------------
    if arguments.afilter != '':
        if arguments.part in K_GENERIQUES:
            # Generiques
            k_part_g = arguments.part
            if arguments.afilter == 'extract':
                extract_audio(g_database, k_part_g, editions=list_editions, verbose=True, force=arguments.force)
            elif arguments.afilter == 'final':
                generate_audio(g_database, k_part_g, verbose=True, force=arguments.force)

        elif arguments.part != '':
            # precedemment, episode, g_asuivre, asuivre, g_reportage, reportage
            if arguments.afilter == 'extract':
                extract_audio(g_database, k_episode, editions=list_editions, verbose=True, force=arguments.force)
            elif arguments.afilter == 'final':
                generate_audio(g_database, k_episode, verbose=True, force=arguments.force)

        else:
            # All
            if arguments.afilter == 'extract':
                for k_part_g in ['g_debut', 'g_fin']:
                    extract_audio(g_database, k_part_g, editions=list_editions, force=arguments.force)
                extract_audio(g_database, k_episode, editions=list_editions, force=arguments.force)

            elif arguments.afilter == 'final':
                for k_part_g in ['g_debut', 'g_fin']:
                    generate_audio(g_database, k_part_g, force=arguments.force)
                v = True if arguments.force else False
                generate_audio(g_database, k_episode, verbose=v, force=arguments.force)



    # Video
    #-------------------------------------------------
    if video_filter in ['deinterlace', 'upscale', 'geometry']:
        # Video and frames

        # Get the list of tasks
        tasks = get_tasklist(final_task=video_filter)

        # Check if nnedi3_weights.bin exists
        if 'deinterlace' in tasks:
            nnedi_file = "./nnedi3_weights.bin"
            if not os.path.exists(nnedi_file):
                sys.exit("Error: file \"%s\" is missing, cannot continue" % (nnedi_file))


        if arguments.frames:
            # Extract frames
            extract_frames_for_study(
                g_database,
                editions=[arguments.edition],
                episode_no=episode_no,
                k_part=arguments.part,
                tasks=tasks,
                force=arguments.force,
                compare=arguments.compare)

        else:
            # Video

            # Shrink database
            for no in range(1, 40):
                k_ep_tmp = 'ep%02d' % (no)
                delete_items(g_database[k_ep_tmp], 'frames')
                continue

                # Cannot clean because we do not know the episodes for generiques
                if (episode_no - 1) <= no <= (episode_no + 1):
                    delete_items(g_database[k_ep_tmp], 'frames')
                    # print(d)
                    # del d['frames']
                    # d['frames'] = None
                else:
                    del g_database[k_ep_tmp]

            for k in K_GENERIQUES:
                if k in g_database.keys():
                    delete_items(g_database[k], 'frames')

            gc.collect()
            print("database: %0.1fkB" % (get_database_size(g_database)/1000.0))

            shot_min = arguments.shot_min
            shot_max = arguments.shot_max
            if arguments.shot != -1:
                shot_min = arguments.shot
                shot_max = arguments.shot + 1

            # Generate the video for the first edition only
            generate_video(
                g_database,
                episode_no=episode_no,
                k_part=arguments.part,
                tasks=tasks,
                edition=list_editions[0],
                force=arguments.force,
                simulation=arguments.simulate,
                shot_min=shot_min, shot_max=shot_max)

            if shot_min != 0 or shot_max != 999999:
                do_av_merge = False

    # Merge A/V streams
    #-------------------------------------------------
    if do_av_merge and not arguments.simulate:
        if arguments.part in ['g_debut', 'g_fin']:
            # I we process specified parts, merge video and audio tracks
            # is only possible for these generiques
            merge_audio_and_video_tracks(g_database, arguments.part, force=arguments.force)
        elif arguments.part == '':

            # Merge all video and audio tracks
            for k in ['g_debut', 'g_fin']:
                merge_audio_and_video_tracks(g_database, k_ep=k, force=arguments.force)

            # Merge video and audio stream from all parts (except g_debut and g_fin)
            merge_audio_and_video_tracks(g_database, k_ep=k_episode, force=arguments.force)

            # Concatenate all parts
            concatenate_all_clips(g_database, k_episode, force=arguments.force)

            # Add chapters to the video file
            if k_episode != 'ep00':
                add_chapters(g_database, k_episode)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
