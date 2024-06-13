import argparse
import gc
import logging
from pprint import pprint
import signal
import sys
from audio import (
    extract_audio_track,
    generate_audio_track,
    get_audio_frame_count,
)
from parsers import (
    db,
    key,
    logger,
    parse_database,
)
from parsers import all_chapter_keys, credit_chapter_keys
from utils.p_print import *


def main():
    editions = ['s0', 's', 'k', 'a', 'f', 'b', 'c']


    # Arguments
    parser = argparse.ArgumentParser(description="Parse the database")
    parser.add_argument(
        "--episode",
        "-ep",
        type=int,
        default=0,
        required=False,
        help="from 1 to 39"
    )

    parser.add_argument(
        "--chapter",
        "-c",
        choices=all_chapter_keys(),
        default='',
        required=False,
        help="Chapter"
    )

    parser.add_argument(
        "--process",
        "-p",
        choices=['extract', 'generate'],
        default='generate',
        required=False,
        help="Extract or generate the audio track"
    )

    parser.add_argument(
        "--en",
        action="store_true",
        required=False,
        help="English version"
    )

    parser.add_argument(
        "--edition",
        "-ed",
        choices=editions,
        default='',
        required=False,
        help="Edition: use to extract audio stream only"
    )

    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        required=False,
        help="Force. Overwrite previous files"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        required=False,
        help="debug"
    )

    parser.add_argument(
        "--stats",
        action="store_true",
        required=False,
        help="Statistics"
    )

    arguments = parser.parse_args()

    if arguments.debug:
        logger.addHandler(logging.StreamHandler(sys.stdout))
        logger.setLevel("DEBUG")

    episode: int = arguments.episode
    chapter: str = arguments.chapter
    if episode == 0 and chapter == '':
        sys.exit("Error: at least an episode or a chapter shall be specified")

    if episode < 0 or episode > 39:
        sys.exit(red("Episode must be between 1 and 39"))

    if chapter in ('g_debut', 'g_fin'):
        episode = 0
    if episode != 0:
        print(f"Episode: {episode}")
    if chapter != '':
        print("Chapter: %s" % (chapter))
    print(f"Language: {'en' if arguments.en else 'fr'}")
    print("Tasks:")
    print("\t- parse database")

    process: str = arguments.process
    print("\t- audio: ", end='')
    if chapter in credit_chapter_keys():
        print(f"\n\t\t{chapter}: ")
    elif chapter != '':
        print("episode: ", end='')
    else:
        print("all: ", end='')

    if process == 'extract':
        print("extract")
    elif process == 'generate':
        print("extract, generate")

    stats = parse_database(episode=episode, lang='en' if arguments.en else 'fr')
    gc.collect()

    # Process
    edition = arguments.edition
    if chapter in credit_chapter_keys():
        if process == 'extract':
            extract_audio_track(
                db,
                chapter=chapter,
                edition=edition,
                force=arguments.force
            )

        elif process == 'generate' and chapter in ('g_debut', 'g_fin'):
            if edition != db[chapter]['audio']['src']['k_ed']:
                print(orange(
                    f"[I] use edition: \'{db[chapter]['audio']['src']['k_ed']}\'")
                )
            generate_audio_track(
                db,
                chapter=chapter,
                force=arguments.force
            )

    elif chapter != '':
        # precedemment, episode, g_asuivre, asuivre, g_documentaire, documentaire
        if process == 'extract':
            extract_audio_track(
                episode=episode,
                chapter=chapter,
                edition=edition,
                force=arguments.force
            )

        elif process == 'generate':
            generate_audio_track(
                episode=episode,
                force=arguments.force
            )

    else:
        # All
        if process == 'extract':
            for _chapter in ['g_debut', 'g_fin']:
                extract_audio_track(
                    edition=edition,
                    force=arguments.force
                )

            extract_audio_track(
                episode=episode,
                chapter=_chapter,
                edition=edition,
                force=arguments.force
            )

        elif process == 'generate':
            for _chapter in ['g_debut', 'g_fin']:
                generate_audio_track(
                    episode=_chapter,
                    force=arguments.force
                )

            generate_audio_track(
                episode=episode,
                force=arguments.force
            )

    # Verify generated audio file
    if arguments.stats:
        _episode = key(episode) if episode != 0 and chapter not in ('g_debut', 'g_fin') else None
        _chapter = chapter if _episode is not None else chapter
        print(f"\nVerify generated audio file: {_episode}:{_chapter}")
        frame_count = get_audio_frame_count(
            episode=_episode,
            chapter=_chapter,
        )
        if _episode is not None:
            video_count, audio_count = stats[_episode]
        else:
            video_count, audio_count = stats[_chapter]

        if audio_count != frame_count or audio_count != video_count:
            print(red("Error: audio file is not valid. It will be impossible to merge audio and video tracks"))
        else:
            print(lightgreen("Audio file is valid"))


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
