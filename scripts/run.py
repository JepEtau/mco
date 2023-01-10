#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
import argparse
import gc
from pprint import pprint
import signal

from audio.audio import (
    extract_audio,
    generate_audio,
)
from images.extract_frames import extract_frames_for_study
from parsers.parser_database import parse_database
from utils.common import (
    K_ALL_PARTS,
    K_GENERIQUES,
    get_database_size,
)
from utils.consolidate_shots import consolidate_target_shots
from utils.tasks import get_tasklist
from video.concatenation import (
    merge_audio_and_video_tracks,
    concatenate_all_clips,
    add_chapters,
)
from video.video import generate_video


g_database = dict()
study_mode = True

def main():
    # if cv2.ocl.haveOpenCL():
    #     cv2.ocl.setUseOpenCL(True)

    # from scripts.frames_extract import frames_extract
    verbose = False
    editions = ['s0', 's', 'k', 'a', 'f']


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
        help="Utilise cette edition")

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

    parser.add_argument("--regenerate",
        action="store_true",
        required=False,
        help="regenerate video")


    arguments = parser.parse_args()

    # Edition
    k_ed = arguments.edition

    # Episode no.
    episode_no = arguments.episode
    k_episode = 'ep%02d' % (episode_no)

    if episode_no == 0 and arguments.part == '':
        sys.exit("Error: épisode ou partie non spécifiée")

    # Consolidate tasks: what will be done
    print("Edition: %s" % (k_ed))
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
        parse_database(g_database, k_ep=k_episode, verbose=verbose, study_mode=arguments.frames)
        gc.collect()
        print("database: %0.1fkB" % (get_database_size(g_database)/1000.0))

        if arguments.part in K_GENERIQUES:
            print("\t\t- %s: " % (arguments.part))
            pprint(g_database[arguments.part])
            print("-----------------------------")
            pprint(g_database['ep01']['k']['g_debut'])

        elif arguments.part != '':
            print("\t\t- precedemment, episode, g_asuivre, asuivre, g_reportage, reportage: ")
            pprint(g_database[k_episode])
        else:
            print("\t\t- all: ", end='')
        print()
        # pprint(g_database)
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
    if k_episode == 'ep00' and arguments.frames:
        # for frame study
        k_episode = 'ep01'

    parse_database(g_database, k_ep=k_episode, verbose=verbose, study_mode=arguments.frames)
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
                extract_audio(g_database, k_ep_or_g=k_part_g, k_ed=k_ed, verbose=True, force=arguments.force)
            elif arguments.afilter == 'final':
                generate_audio(g_database, k_part_g, verbose=True, force=arguments.force|arguments.regenerate)

        elif arguments.part != '':
            # precedemment, episode, g_asuivre, asuivre, g_reportage, reportage
            if arguments.afilter == 'extract':
                extract_audio(g_database, k_ep_or_g=k_episode, k_ed=k_ed, verbose=True, force=arguments.force)
            elif arguments.afilter == 'final':
                generate_audio(g_database, k_ep=k_episode, verbose=True, force=arguments.force|arguments.regenerate)

        else:
            # All
            if arguments.afilter == 'extract':
                for k_part_g in ['g_debut', 'g_fin']:
                    extract_audio(g_database, k_ep_or_g=k_part_g, k_ed=k_ed, force=arguments.force)
                extract_audio(g_database, k_ep_or_g=k_episode, k_ed=k_ed, force=arguments.force)

            elif arguments.afilter == 'final':
                for k_part_g in ['g_debut', 'g_fin']:
                    generate_audio(g_database, k_part_g, force=arguments.force)
                v = True if arguments.force else False
                generate_audio(g_database, k_ep=k_episode, verbose=v, force=arguments.force|arguments.regenerate)



    # Video
    #-------------------------------------------------

    # Get the list of tasks
    tasks = get_tasklist(db=g_database, final_task=video_filter)

    if len(tasks) > 0:
        # Check if nnedi3_weights.bin exists
        if 'deinterlace' in tasks:
            nnedi_file = "./nnedi3_weights.bin"
            if not os.path.exists(nnedi_file):
                sys.exit("Error: file \"%s\" is missing, cannot continue" % (nnedi_file))

        # Consolidate each shot for the target
        consolidate_target_shots(
            db=g_database,
            k_ep=k_episode,
            k_part=arguments.part,
        )

        # Specified shot min. and max
        shot_min = arguments.shot_min
        shot_max = arguments.shot_max
        if arguments.shot != -1:
            shot_min = arguments.shot
            shot_max = arguments.shot + 1

        if arguments.frames:
            # Extract frames
            extract_frames_for_study(
                db=g_database,
                k_ed=k_ed,
                k_ep=k_episode,
                k_part=arguments.part,
                tasks=tasks,
                force=arguments.force,
                shot_min=shot_min, shot_max=shot_max)
            return

        # elif video_filter in ['deinterlace', 'upscale', 'geometry']:
        else:
            # Generate the video
            generate_video(
                db=g_database,
                k_ep=k_episode,
                k_part=arguments.part,
                tasks=tasks,
                force=arguments.force,
                simulation=arguments.simulate,
                shot_min=shot_min, shot_max=shot_max,
                do_regenerate=arguments.regenerate)

            if shot_min != 0 or shot_max != 999999:
                do_av_merge = False

        if (not arguments.frames
            and video_filter in ['deinterlace', 'denoise', 'upscale', 'geometry', 'sharpen']):
            do_av_merge = True
        else:
            do_av_merge = True


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
                    merge_audio_and_video_tracks(g_database, k_ep=k, force=arguments.force|arguments.regenerate)

                # Merge video and audio stream from all parts (except g_debut and g_fin)
                merge_audio_and_video_tracks(g_database, k_ep=k_episode, force=arguments.force|arguments.regenerate)

                # Concatenate all parts
                concatenate_all_clips(g_database, k_episode, force=arguments.force|arguments.regenerate)

                # Add chapters to the video file
                if k_episode != 'ep00':
                    add_chapters(g_database, k_episode)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
