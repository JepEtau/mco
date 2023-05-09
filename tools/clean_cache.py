#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import multiprocessing
import re
import sys
sys.path.append('scripts')

from shot.consolidate_shot import consolidate_shot
from utils.hash import calculate_hash

from parsers.parser_database import parse_database
from utils.common import (
    K_ALL_PARTS,
    K_ALL_PARTS_ORDERED,
    K_GENERIQUES,
)

import argparse
import os
import signal

from pprint import pprint
from utils.pretty_print import *
import shutil
from multiprocessing import *
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor


TEMPLATE_IMG = "^ep\d{2}_\d{5}__[a-z0]*__\d{2}_([a-z0-9]{7}).*"

def main():
    db = dict()

    parser = argparse.ArgumentParser(description="Clean the cache directory")
    parser.add_argument("--episode",
        type=int,
        default=0,
        required=False,
        help="Numéro d'épisode de 1 à 39. Ignoré pour la génération des génériques.")

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


    parser.add_argument("--vfilter",
        default='',
        required=False,
        choices=['', 'edition'],
        help="Supprime les images utilisées pour l'édition")


    parser.add_argument("--verbose",
        action="store_true",
        required=False,
        help="verbose")


    arguments = parser.parse_args()

    episode_no = arguments.episode
    k_ep = 'ep%02d' % (episode_no)
    k_part = arguments.part
    verbose = arguments.verbose


    if episode_no == 0 and arguments.part == '':
        sys.exit("Error: épisode ou partie non spécifiée")

    parse_database(db, k_ep=k_ep)

    files = list()
    folders = list()

    k_parts = K_ALL_PARTS_ORDERED if k_part == '' else [k_part]
    for k_p in k_parts:
        hashes = list()
        hashes_str = ''

        if k_p in ['g_debut', 'g_fin']:
            db_video = db[k_p]['video']
        elif k_ep == 'ep00':
            sys.exit("Erreur: le numéro de l'épisode est manquant")
        else:
            db_video = db[k_ep]['video']['target'][k_p]


        if True:
            # Walk through target shots
            shots = db_video['shots']
            for shot in shots:

                # Use the final task
                shot['last_task'] = ''
                consolidate_shot(db, shot=shot)
                for f in shot['filters']:
                    if f['save'] and f['hash'] != '':
                        hashes.append(f['hash'])


                # Calculate hash for the video
                shot_hash = shot['last_step']['hash']
                shot_hash = shot['last_task'] if shot_hash == '' else shot_hash
                hashes_str += '%s:' % (shot_hash)


                # Remove images used for edition
                if arguments.vfilter != 'edition':
                    # so keep images if not in edition mode
                    shot['last_task'] = 'edition'
                    consolidate_shot(db, shot=shot)
                    for f in shot['filters']:
                        if f['save'] and f['hash'] != '':
                            hashes.append(f['hash'])

            # For video: not yet supported
            # hashes_str = hashes_str[:-1]
            # db_video['hash'] = calculate_hash(hashes_str)

            # All hashes have been listed
            hashes = list(set(hashes))
            print(hashes)

        # Get cache directory
        if k_p in['g_debut', 'g_fin']:
            cache_directory = os.path.join(db[k_part]['cache_path'])
        else:
            cache_directory = os.path.join(db[k_ep]['cache_path'], k_p)


        directories = sorted(os.listdir(cache_directory))
        for directory in directories:
            shot_path = os.path.join(cache_directory, directory)
            try:
                shot_no = int(directory)
            except:
                if directory == 'concatenation':
                    # Remove concatenation folder
                    folders.append(shot_path)
                elif os.path.isfile(shot_path):
                    files.append(step_path)
                else:
                    print_lightgrey(f"discard {shot_path}")
                continue


            if verbose:
                print(f"parse shot: {shot_path}")

            step_directories = sorted(os.listdir(shot_path))
            for step_directory in step_directories:
                step_path = os.path.join(shot_path, step_directory)
                if verbose:
                    print(f"\tparse step: {step_path}")

                if os.path.isfile(step_path):
                    files.append(step_path)
                    continue

                filepathes = sorted(os.listdir(step_path))
                for filepath in filepathes:
                    # Remove folders
                    absolute_filepath = os.path.join(step_path, filepath)
                    if os.path.isdir(absolute_filepath):
                        folders.append(absolute_filepath)
                        continue

                    properties = re.match(re.compile(TEMPLATE_IMG), filepath)
                    if properties is None:
                        # Not a valid image name
                        files.append(absolute_filepath)
                        continue

                    hash = properties.group(1)
                    if hash in hashes:
                        # is used
                        continue
                    files.append(absolute_filepath)
        # Stat
        # foldersize = 0
        # for f in folders:
        #     foldersize += shutil.disk_usage(f)[1]
        # foldersize = int(foldersize/ (1024 * 1024))

        filesize = 0
        for f in files:
            filesize += os.stat(f).st_size
        filesize = int(filesize/ (1024 * 1024))



        if verbose:
            print_lightgreen(f"folders to remove")
            pprint(folders)
            print_lightgreen(f"files to remove")
            pprint(files)
            print_lightcyan(f"- remove {folder_count} folder(s)")
            print_lightcyan(f"- remove {file_count} files: {filesize} MB")
            return


        cpu_count = int(multiprocessing.cpu_count() * (3/4))
        folder_count = len(folders)
        if folder_count > 0:
            print_lightcyan(f"- remove {folder_count} folder(s)")
            no = 0
            with ThreadPoolExecutor(max_workers=min(cpu_count, folder_count)) as executor:
                work_result = {executor.submit(remove_folder, folder): list for folder in folders}
                for future in concurrent.futures.as_completed(work_result):
                    success = future.result()
                    no += 1
                    print_yellow(f"{int((100.0 * no)/folder_count)}%%", flush=True, end='\r')
            print(f"          ", end='\r')
            print(f"\tdone")


        file_count = len(files)
        if file_count > 0:
            print_lightcyan(f"- remove {file_count} files: {filesize} MB")
            no = 0
            with ThreadPoolExecutor(max_workers=min(cpu_count, file_count)) as executor:
                work_result = {executor.submit(delete_file, file): list for file in files}
                for future in concurrent.futures.as_completed(work_result):
                    success = future.result()
                    no += 1
                    print_yellow(f"{int((100.0 * no)/file_count)}%%", flush=True, end='\r')
            print(f"          ", end='\r')
            print(f"\tdone")

        if file_count == 0 and folder_count == 0:
            print(f"Nothing to remove")


    # Remove empty directories
    remove_empty_folders(cache_directory)



def remove_empty_folders(folder_path):
    walk = list(os.walk(folder_path))
    for path, _, _ in walk[::-1]:
        if len(os.listdir(path)) == 0:
            shutil.rmtree(path)


def remove_folder(folder):
    # print(f"{folder}")
    try:
        shutil.rmtree(folder, ignore_errors=True)
    except:
        return False
    return True


def delete_file(filepath):
    # print(f"{filepath}")
    try:
        os.remove(filepath)
    except:
        return False
    return True

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()

