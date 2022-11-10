#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from email.mime import audio
import sys
from pprint import pprint

from parsers.parser_common import parse_common_configuration
from parsers.parser_editions import parse_editions
from parsers.parser_episodes import (
    parse_episodes_common,
    parse_get_dependencies_for_episodes,
    db_init_episodes,
    parse_episode,
)
from parsers.parser_generiques import (
    db_init_generiques,
    parse_generiques_common,
    parse_generiques,
    parse_get_dependencies_for_generique,
)
from parsers.parser_shots import (
    create_dst_shots,
    create_dst_shots_g,
)

from parsers.parser_curves import parse_curve_configurations
from parsers.parser_replace import parse_replace_configurations
from parsers.parser_geometry import parse_geometry_configurations
from parsers.parser_stitching import parse_stitching_configurations


from utils.common import K_GENERIQUES, K_NON_GENERIQUE_PARTS, K_PARTS, pprint_video
from utils.consolidate import align_audio_video_durations
from utils.consolidate import align_audio_video_durations_g_debut_fin
from utils.consolidate import determine_av_sync
from utils.path import PATH_DATABASE
from utils.time_conversions import ms_to_frames




def parse_database(database, editions, k_ep, mode='', verbose=False):

    # Parse and merge dictionaries -> common configuration
    database['common'] = parse_common_configuration(PATH_DATABASE, verbose=verbose)
    if False:
        print("parse_common_configuration")
        print("------------------------------------")
        pprint(database)
        print("------------------------------------")


    # Parse editions: folders, files and additional settings: dimension
    database['editions'] = parse_editions(database, verbose=verbose)
    if False:
        print("parse_editions")
        print("------------------------------------")
        pprint(database)
        print("------------------------------------")
        sys.exit()


    # Parse database file which contains common settings for all episodes
    parse_episodes_common(database)
    if False:
        print("parse_episodes_common")
        print("------------------------------------")
        pprint(database)
        print("------------------------------------")
        sys.exit()

    # Initialize dictionary for episodes per edition
    cfg_episodes = dict()
    for k_ed in editions:
        db_init_episodes(database, k_ed=k_ed)
    if False:
        print("db_init_episodes")
        print("------------------------------------")
        pprint(database)
        print("------------------------------------")
        sys.exit()


    # Initialize dictionary for generiques
    for k_ed in editions:
        db_init_generiques(database, k_ed=k_ed, verbose=verbose)


    # Parse database file which contains common settings for generiques
    parse_generiques_common(database, verbose=verbose)
    for k_ed in editions:
        parse_generiques(database, k_ed=k_ed, verbose=verbose)


    # Define the default edition
    database['editions']['default'] = editions[0]


    # Create a dict of dependencies for generiques
    dependencies = dict()
    for k_part_g in K_GENERIQUES:
        dependencies_tmp = parse_get_dependencies_for_generique(database, k_part_g=k_part_g)
        for k,v in dependencies_tmp.items():
            if k not in dependencies.keys():
                dependencies[k] = list()
            dependencies[k] = list(set(dependencies[k] + v))


    if k_ep != 'ep00':
        # Parse episode at first (required to generate dependencies)
        for k_ed_tmp in editions:
            parse_episode(database, k_ed=k_ed_tmp, k_ep=k_ep)

        # Get dependencies for this episode
        dependencies_tmp = parse_get_dependencies_for_episodes(database, k_ep)


    # Merge dependencies
    for k,v in dependencies_tmp.items():
        if k not in dependencies.keys():
            dependencies[k] = list()
        dependencies[k] = list(set(dependencies[k] + v))

    # Parse episodes which are required (dependencies)
    # pprint(dependencies)
    for k_ed_tmp, v in dependencies.items():
        for k_ep_tmp in v:
            if k_ep_tmp == k_ep:
                continue
            parse_episode(database, k_ed=k_ed_tmp, k_ep=k_ep_tmp, verbose=verbose)

    # Parse other config files for each dependency
    for k_ed_tmp, v in dependencies.items():
        for k_ep_tmp in dependencies[k_ed_tmp]:
            # Parse config file used to stabilize/stitch
            parse_stitching_configurations(database, k_ep_or_g=k_ep_tmp)

            parse_curve_configurations(database, k_ep_or_g=k_ep_tmp)
            parse_replace_configurations(database, k_ep_or_g=k_ep_tmp)
        break

    # Parse the geometry for the target episode only
    # Otherwise it is overwritten by the following episodes
    if k_ep != 'ep00':
        parse_geometry_configurations(database, k_ep_or_g=k_ep)

    # Génériques: debut/fin
    for k_part_g in ['g_debut', 'g_fin']:
        # Curves: this parser update the shots for each episode/part
        parse_curve_configurations(database, k_ep_or_g=k_part_g)

        # TODO: reenable this ?
        # # Parse config file used to stabilize/stitch
        # parse_stitching_configurations(database, k_ep_or_g=k_part_g)

        # Replaced frames
        parse_replace_configurations(database, k_ep_or_g=k_part_g)

        # Crop and resize
        parse_geometry_configurations(database, k_ep_or_g=k_part_g)

        # Create shots used for the generation
        create_dst_shots_g(database, k_ep='', k_part_g=k_part_g)

        # Consolidate by aligning the A/V tracks of generiques
        align_audio_video_durations_g_debut_fin(database, k_ep='', k_part_g=k_part_g)



    # Consolidate database for the episode ONLY
    if k_ep != 'ep00':
        for k_p in K_NON_GENERIQUE_PARTS:
            create_dst_shots(database, k_ep=k_ep, k_part=k_p)

        for k_part_g in ['g_asuivre', 'g_reportage']:
            parse_curve_configurations(database, k_ep_or_g=k_part_g)
            parse_replace_configurations(database, k_ep_or_g=k_part_g)
            parse_geometry_configurations(database, k_ep_or_g=k_part_g)

            create_dst_shots_g(database, k_ep=k_ep, k_part_g=k_part_g)

        determine_av_sync(database, k_ep=k_ep)
        align_audio_video_durations(database, k_ep=k_ep)

        pprint_episode(database, k_ep=k_ep)
    else:
        pprint_g_debut_fin(database)


    # pprint_video(database[k_ep]['common']['video'])



def pprint_g_debut_fin(db):

    if False:
        # print last shot of every part
        for k_part_g in ['g_debut', 'g_fin']:
            print("%s" % (k_part_g))
            db_video = db[k_part_g]['common']['video']
            if db_video['count'] == 0:
                continue
            print("  ", db_video['shots'][-1])

    print("\n        ", end='')
    print("audio".rjust(18), end='')
    print("avsync(A)".rjust(16), end='')
    print("video".rjust(14), end='')
    print("1st shot".rjust(17), end='')
    print("frames".rjust(10), end='')
    print("loop".rjust(12), end='')
    print("avsync(V)".rjust(15), end='')
    print("total(V)".rjust(12), end='')
    print("total(A)".rjust(12), end='')
    print("")
    for k_part_g in ['g_debut', 'g_fin']:
        episode_audio_count = 0
        episode_video_count = 0
        db_video = db[k_part_g]['common']['video']
        db_audio = db[k_part_g]['common']['audio']
        frames_count = 0

        if db_video['count'] == 0:
            print("%s" % (k_part_g.ljust(16)), end='')
            print("\t(0)")
            continue

        first_shot = db_video['shots'][0]

        for shot in db_video['shots']:
            frames_count += shot['count']
        last_shot = db_video['shots'][-1]

        loop_count = 0
        if 'effects' in last_shot:
            if 'loop' in last_shot['effects'][0]:
                loop_count = last_shot['effects'][2]
        total_frames_count = frames_count + loop_count

        total_frames_count += db_video['avsync']

        audio_duration = 0
        audio_duration +=  db_audio['avsync']
        for segment in db_audio['segments']:
            if 'duration' in segment.keys():
                audio_duration += segment['duration']
            if 'silence' in segment.keys():
                audio_duration += segment['silence']

        print("%s" % (k_part_g.ljust(12)), end='')

        # audio
        start_str = "%d" % ms_to_frames(db_audio['start'])
        count_str = "(%d)" % ms_to_frames(db_audio['duration'])
        print("%s%s" % (start_str.rjust(10), count_str.rjust(8)), end='')

        # avsync audio
        tmp_str = "%d" % ms_to_frames(db_audio['avsync'])
        print("%s" % (tmp_str.rjust(8)), end='')

        # video
        start_str = "%d" % db_video['start']
        count_str = "(%d)" % db_video['count']
        print("%s%s" % (start_str.rjust(12), count_str.rjust(8)), end='')

        # start of 1st shot
        start_str = "%d" % first_shot['start']
        print("%s" % (start_str.rjust(12)), end='')

        # frames count (sum of shots only)
        tmp_str = "%d" % frames_count
        print("%s" % (tmp_str.rjust(12)), end='')

        # loop
        tmp_str = "%d" % loop_count
        print("%s" % (tmp_str.rjust(12)), end='')

        # avsync
        tmp_str = "%d" % db_video['avsync']
        print("%s" % (tmp_str.rjust(12)), end='')

        # total frames count
        tmp_str = "%d" % total_frames_count
        print("%s" % (tmp_str.rjust(12)), end='')

        # total audio count
        tmp_str = "%d" % ms_to_frames(audio_duration)
        print("%s" % (tmp_str.rjust(12)), end='')

        print("")

        episode_audio_count += ms_to_frames(audio_duration)
        episode_video_count += total_frames_count

        # print(">>> db_audio")
        # pprint(db_audio)
        # print("-------------------")
        # print(">>> db[%s]" % (k_ep))
        # pprint(db[k_ep])

        silence_count = ms_to_frames(db[k_part_g]['common']['audio']['silence'])
        episode_audio_count += silence_count
        episode_video_count += silence_count

        print("audio (count): %d" % (episode_audio_count))
        print("video (count): %d" % (episode_video_count))
        print("")



def pprint_episode(db, k_ep):

    if False:
        # print last shot of every part
        for k_p in K_PARTS:
            print("%s" % (k_p))
            db_video = db[k_ep]['common']['video'][k_p]
            if db_video['count'] == 0:
                continue
            print("  ", db_video['shots'][-1])

    print("\n            ", end='')
    print("    audio".rjust(20), end='')
    print("sync(A)".rjust(14), end='')
    print("video".rjust(14), end='')
    print("1st shot".rjust(16), end='')
    print("frames".rjust(11), end='')
    print("loop".rjust(12), end='')
    print("sync(V)".rjust(14), end='')
    print("total(V)".rjust(11), end='')
    print("total(A)".rjust(12), end='')
    print("")
    episode_audio_count = 0
    episode_video_count = 0
    for k_p in K_PARTS:
        db_video = db[k_ep]['common']['video'][k_p]
        db_audio = db[k_ep]['common']['audio'][k_p]
        frames_count = 0
        print("    %s" % (k_p.ljust(12)), end='')

        if db_video['count'] == 0:
            print("%s%s" % ("0".rjust(10), "(0)".rjust(8)))
            continue

        first_shot = db_video['shots'][0]

        for shot in db_video['shots']:
            frames_count += shot['count']
        last_shot = db_video['shots'][-1]

        loop_count = 0
        if 'effects' in last_shot:
            if 'loop' in last_shot['effects'][0]:
                loop_count = last_shot['effects'][2]
        total_frames_count = frames_count + loop_count

        total_frames_count += db_video['avsync']

        audio_duration = 0
        audio_duration +=  db_audio['avsync']
        for segment in db_audio['segments']:
            if 'duration' in segment.keys():
                audio_duration += segment['duration']
            if 'silence' in segment.keys():
                audio_duration += segment['silence']

        # audio
        start_str = "%d" % ms_to_frames(db_audio['start'])
        count_str = "(%d)" % ms_to_frames(db_audio['duration'])
        print("%s%s" % (start_str.rjust(10), count_str.rjust(8)), end='')

        # avsync audio
        tmp_str = "%d" % ms_to_frames(db_audio['avsync'])
        print("%s" % (tmp_str.rjust(8)), end='')

        # video
        start_str = "%d" % db_video['start']
        count_str = "(%d)" % db_video['count']
        print("%s%s" % (start_str.rjust(12), count_str.rjust(8)), end='')

        # start of 1st shot
        start_str = "%d" % first_shot['start']
        print("%s" % (start_str.rjust(12)), end='')

        # frames count (sum of shots only)
        tmp_str = "%d" % frames_count
        print("%s" % (tmp_str.rjust(12)), end='')

        # loop
        tmp_str = "%d" % loop_count
        print("%s" % (tmp_str.rjust(12)), end='')

        # avsync
        tmp_str = "%d" % db_video['avsync']
        print("%s" % (tmp_str.rjust(12)), end='')

        # total frames count
        tmp_str = "%d" % total_frames_count
        print("%s" % (tmp_str.rjust(12)), end='')

        # total audio count
        tmp_str = "%d" % ms_to_frames(audio_duration)
        print("%s" % (tmp_str.rjust(12)), end='')

        print("")

        episode_audio_count += ms_to_frames(audio_duration)
        episode_video_count += total_frames_count

        # print(">>> db_audio")
        # pprint(db_audio)
        # print("-------------------")
        # print(">>> db[%s]" % (k_ep))
        # pprint(db[k_ep])

    for k_p in ['episode', 'asuivre', 'reportage']:
        silence_count = ms_to_frames(db[k_ep]['common']['audio'][k_p]['silence'])
        episode_audio_count += silence_count
        episode_video_count += silence_count

    print("")
    print("    audio (total count): %d" % (episode_audio_count))
    print("    video (total count): %d" % (episode_video_count))
    print("")
