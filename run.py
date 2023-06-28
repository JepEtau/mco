#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.append('scripts')

import argparse
import gc
import signal

from pprint import pprint
from utils.pretty_print import *

from audio.extract_audio_track import extract_audio_track
from audio.generate_audio_track import generate_audio_track
from img_toolbox.utils import FILTER_TAGS

from parsers.parser_database import (
    parse_database,
    parse_database_for_study
)
from utils.common import (
    K_ALL_PARTS,
    K_GENERIQUES,
)
from utils.frames import copy_frames_for_study
from utils.stats import display_stats

from video.combine_av_tracks import combine_av_tracks
from video.concatenate_all import concatenate_all
from video.add_chapters import add_chapters
from video.generate_video_track import generate_video_track


g_database = dict()
study_mode = True

def main():
    # if cv2.ocl.haveOpenCL():
    #     cv2.ocl.setUseOpenCL(True)

    # from scripts.frames_extract import frames_extract
    verbose = False
    editions = ['s0', 's', 'k', 'a', 'f', 'b', 'c']


    # Arguments
    #---------------------------------------------------------------------------
    parser = argparse.ArgumentParser(description="Main tool")
    parser.add_argument("--episode",
        type=int,
        default=0,
        required=False,
        help="Numéro d'épisode de 1 à 39. Ignoré pour la génération des génériques.")

    parser.add_argument("--lang",
        default='',
        required=False,
        choices=['fr', 'en'],
        help="Language and video edition")

    parser.add_argument("--part",
        default='',
        required=False,
        choices=K_ALL_PARTS,
        help="Partie à générer")

    parser.add_argument("--shot",
        type=int,
        default=-1,
        required=False,
        help="debug: numéro du plan à générer")

    parser.add_argument("--shot_min",
        type=int,
        default=0,
        required=False,
        help="debug: plans à générer: début.")

    parser.add_argument("--shot_max",
        type=int,
        default=999999,
        required=False,
        help="debug: plans à générer: fin.")

    parser.add_argument("--vfilter",
        default=FILTER_TAGS[-1],
        required=False,
        choices=FILTER_TAGS,
        help="debug: applique les filtres video jusqu\'à celui spécifié ici (note: final=geometry)")

    parser.add_argument("--afilter",
        default='',
        required=False,
        choices=[
            'extract',
            'final'
        ],
        help="debug: applique les filtres audio jusqu\'à celui spécifié ici")

    parser.add_argument("--frames",
        action="store_true",
        help="debug: sera utilisé pour comparer des trames, des filtres, etc. Nécessite les arguments --edition, --episode et --part)")

    parser.add_argument("--edition",
        default='',
        required=False,
        choices=editions,
        help="debug: utilise cette edition")

    parser.add_argument("--force",
        action="store_true",
        required=False,
        help="debug: force. NON VERIFIE")

    parser.add_argument("--simulate",
        action="store_true",
        required=False,
        help="debug: génère les fichiers de concatenation uniquement")

    parser.add_argument("--parse_only",
        action="store_true",
        required=False,
        help="debug: analyse les fichiers de configuration")

    parser.add_argument("--stats",
        action="store_true",
        required=False,
        help="debug: affiche les avancées/stats")


    parser.add_argument("--regenerate",
        action="store_true",
        required=False,
        help="debug: regénère les fichier vidéo. NON VERIFIE")


    parser.add_argument("--watermark",
        action="store_true",
        required=False,
        help="debug: ajoute le numéro du plan sur chaque trame")

    arguments = parser.parse_args()

    # Edition
    k_ed = arguments.edition

    # Episode no.
    episode_no = arguments.episode
    k_episode = 'ep%02d' % (episode_no)

    if episode_no == 0 and arguments.part == '':
        sys.exit("Error: épisode ou partie non spécifiée")

    # Consolidate tasks: what will be done
    if k_ed != '':
        print("Edition: %s (study mode)" % (k_ed))
    print("Episode: %d" % (episode_no))
    if arguments.part != '':
        print("Part: %s" % (arguments.part))
    print(f"Language: {arguments.lang if arguments.lang != '' else 'auto'}")
    print("Tasks:")
    print("\t- parse database")
    print("\t- consolidate generiques")

    video_filter = arguments.vfilter.replace('final', 'geometry')
    do_av_merge = False
    if not arguments.frames and arguments.afilter == '':
        if (arguments.part in ['g_debut', 'g_fin']
        or arguments.part == ''):

            print("\t- force processing audio and video")
            afilter = 'final'
            if video_filter == '':
                video_filter = 'geometry'
            do_av_merge = True

        elif arguments.part != '':
            if video_filter == '':
                video_filter = 'geometry'
            do_av_merge = True

    if arguments.parse_only:
        # Parse database
        parse_database(g_database, k_ep=k_episode, lang=arguments.lang)
        gc.collect()
        print(p_lightcyan(f"Language: {g_database['common']['settings']['language']}"))

        if arguments.part in K_GENERIQUES:
            print("\t\t- %s: " % (arguments.part))
            pprint(g_database[arguments.part])
            print("-----------------------------")
            # pprint(g_database['ep01']['k']['g_debut'])

        elif arguments.part != '':
            print("\t\t- precedemment, episode, g_asuivre, asuivre, g_documentaire, documentaire: ")

            # debugging purpose, modify this
            # pprint(g_database[k_episode]['video']['f'].keys())
            # pprint(g_database[k_episode]['video']['f'][arguments.part]['filters'])
            # pprint(g_database[k_episode]['video']['f'][arguments.part])
            print(p_lightcyan(f"--------------------------- target -------------------------------"))
            pprint(g_database[k_episode]['video']['target'][arguments.part])
        print()

        # pprint(g_database[k_episode]['audio'])
        # pprint(g_database[k_episode]['video']['target'])
        sys.exit()

    afilter = 'final'
    print("\t- audio: ", end='')
    if arguments.afilter != '' and arguments.shot == -1:
        afilter = arguments.afilter
        if arguments.part in K_GENERIQUES:
            print("\n\t\t- %s: " % (arguments.part), end='')
        elif arguments.part != '':
            print("\n\t\t- precedemment, episode, g_asuivre, asuivre, g_documentaire, documentaire: ", end='')
        else:
            print("\n\t\t- all: ", end='')

    if afilter == 'extract':
        print("extract only")
    elif afilter == 'final':
        print("final")
    else:
        print("not processed")

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


    # Parse database
    #-------------------------------------------------
    if arguments.frames:
        if k_ed == '' or k_episode == 'ep00' or arguments.part == '':
            sys.exit(print_red("Erreur: l'édition, l'épisode et la partie doivent être spécifiés"))

        parse_database_for_study(g_database, k_ed=k_ed, k_ep=k_episode, k_part=arguments.part)
    else:
        parse_database(g_database, k_ep=k_episode, lang=arguments.lang)

    gc.collect()


    # Collect statistics
    #-------------------------------------------------
    if arguments.stats:
        display_stats(
            db=g_database,
            k_ep=k_episode,
            k_part=arguments.part)
        return

    # Audio
    #-------------------------------------------------
    if arguments.shot == -1 and not arguments.simulate:
        if afilter != '':
            if arguments.part in K_GENERIQUES:
                # Generiques
                k_part_g = arguments.part
                if afilter == 'extract':
                    extract_audio_track(g_database, k_ep=k_part_g, k_ed=k_ed, force=arguments.force)
                elif afilter == 'final':
                    if k_ed != g_database[k_part_g]['audio']['src']['k_ed']:
                        print_orange(f"Warning: audio: discard specified edition, use final edition: {g_database[k_part_g]['audio']['src']['k_ed']}")
                    generate_audio_track(g_database,
                        k_ep_or_g=k_part_g,
                        verbose=True,
                        force=arguments.force|arguments.regenerate)

            elif arguments.part != '':
                # precedemment, episode, g_asuivre, asuivre, g_documentaire, documentaire
                if afilter == 'extract':
                    extract_audio_track(g_database, k_ep=k_episode, k_ed=k_ed, force=arguments.force)
                elif afilter == 'final':
                    generate_audio_track(g_database,
                        k_ep_or_g=k_episode,
                        verbose=True,
                        force=arguments.force|arguments.regenerate)

            else:
                # All
                if afilter == 'extract':
                    for k_part_g in ['g_debut', 'g_fin']:
                        extract_audio_track(g_database, k_ep=k_part_g, k_ed=k_ed, force=arguments.force)
                    extract_audio_track(g_database, k_ep=k_episode, k_ed=k_ed, force=arguments.force)

                elif afilter == 'final':
                    for k_part_g in ['g_debut', 'g_fin']:
                        if k_ed != g_database[k_part_g]['audio']['src']['k_ed']:
                            print_orange(f"Warning: audio: discard specified edition, use final edition: {g_database[k_part_g]['audio']['src']['k_ed']}")
                        generate_audio_track(g_database,
                            k_ep_or_g=k_part_g,
                            force=arguments.force)

                    generate_audio_track(g_database,
                        k_ep_or_g=k_episode,
                        verbose=True if arguments.force else False,
                        force=arguments.force|arguments.regenerate)

        if arguments.afilter != '':
            return

    # Video
    #-------------------------------------------------

    # Get the list of tasks
    if video_filter == 'geometry':
        video_filter = 'final'

    # Specified shot min. and max
    shot_min = arguments.shot_min
    shot_max = arguments.shot_max
    if arguments.shot != -1:
        shot_min = arguments.shot
        shot_max = arguments.shot + 1

    if arguments.frames:
        # Extract frames
        copy_frames_for_study(db=g_database,
            k_ed=k_ed,
            k_ep=k_episode,
            k_part=arguments.part,
            last_task=video_filter)
    else:
        # Generate the video
        generate_video_track(
            db=g_database,
            k_ed=k_ed,
            k_ep=k_episode,
            k_part=arguments.part,
            last_task=video_filter,
            force=arguments.force,
            simulation=arguments.simulate,
            shot_min=shot_min, shot_max=shot_max,
            do_regenerate=arguments.regenerate,
            watermark=arguments.watermark)

        if shot_min != 0 or shot_max != 999999:
            do_av_merge = False

    # if video_filter in ['deinterlace', 'upscale', 'sharpen', 'geometry', 'final']:
    #     # TODO: allow all video
        do_av_merge = True
    # else:
    #     do_av_merge = False


    # Merge A/V streams
    #-------------------------------------------------
    if k_ed == '':
        # Create final video only if edition is not specified
        if do_av_merge:
            if arguments.part in ['g_debut', 'g_fin'] and arguments.shot == -1:
                # Part is specified, merge audio and video files
                combine_av_tracks(g_database,
                    k_ep_or_g=arguments.part,
                    last_task=video_filter,
                    force=arguments.force,
                    simulation=arguments.simulate)

            elif arguments.part == '':
                # Merge all video and audio tracks
                for k in ['g_debut', 'g_fin']:
                    combine_av_tracks(g_database,
                        k_ep_or_g=k,
                        last_task=video_filter,
                        force=arguments.force|arguments.regenerate,
                        simulation=arguments.simulate)

                # Merge video and audio stream from all parts (except g_debut and g_fin)
                combine_av_tracks(g_database,
                    k_ep_or_g=k_episode,
                    last_task=video_filter,
                    force=arguments.force|arguments.regenerate,
                    simulation=arguments.simulate)

                # Concatenate all parts
                concatenate_all(g_database,
                    k_ep=k_episode,
                    last_task=video_filter,
                    force=arguments.force|arguments.regenerate,
                    simulation=arguments.simulate)

                # Add chapters to the video file and write into output folder
                if k_episode != 'ep00':
                    add_chapters(g_database,
                        k_ep=k_episode,
                        last_task=video_filter,
                        simulation=arguments.simulate)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
