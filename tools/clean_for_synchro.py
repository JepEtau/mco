#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import multiprocessing
import re
import sys
from typing import (
    List
)

sys.path.append('scripts')

from shot.consolidate_shot import consolidate_shot
from processing_chain.hash import calculate_hash

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


TEMPLATE_IMG = "^ep\d{2}_\d{5}__[a-z0]*__\d{2}_([a-z0-9]{7}.*).png"

def main():
    db = dict()

    parser = argparse.ArgumentParser(description="Remove the images/video files")
    parser.add_argument("--episode",
        type=int,
        default=0,
        required=False,
        help="1 to 39")

    parser.add_argument("--vfilter",
        default='deinterlace',
        required=False,
        help="this filter only")

    parser.add_argument("--av_sync",
        action="store_true",
        default=True,
        required=False,
        help="remove files impacted by avsync")

    parser.add_argument("--fade",
        action="store_true",
        default=False,
        required=False,
        help="remove all files generated with fadein/fadeout")

    parser.add_argument("--verbose",
        action="store_true",
        default=False,
        required=False,
        help="verbose")

    arguments = parser.parse_args()

    episode_no = arguments.episode
    k_ep = f'ep{episode_no:02}'
    step = arguments.vfilter
    verbose = arguments.verbose
    av_sync = arguments.av_sync
    fade = arguments.fade
    if episode_no == 0:
        sys.exit("Error: épisode non spécifié")

    parse_database(db, k_ep=k_ep)

    files = list()
    folders = list()


    # Output video files
    output_dir = os.path.join(db['common']['directories']['outputs'])
    file_paths: List[str] = sorted(os.listdir(output_dir))
    for f in file_paths:
        if f.startswith(k_ep) and step in f and f.lower().endswith('.mkv'):
            files.append(os.path.join(output_dir, f))

    output_dir = os.path.join(db['common']['directories']['cache'], k_ep)
    file_paths: List[str] = sorted(os.listdir(output_dir))
    for f in file_paths:
        if f.startswith(k_ep) and step in f and f.lower().endswith('.mkv'):
            files.append(os.path.join(output_dir, f))

    output_dir = os.path.join(db['common']['directories']['cache'], k_ep, 'video')
    for lang in ['', '_en']:
        f = os.path.join(output_dir, f"{k_ep}_video{lang}.mkv")
        if os.path.exists(f):
            files.append(f)

    file_paths: List[str] = sorted(os.listdir(output_dir))
    for f in file_paths:

        if (match := re.match(re.compile("(ep\d{2})_([a-z]+)_[a-z0-9]+_([a-z]+)"), f)):
            # video of a part
            k_part = match.group(2)
            if (match.group(1) == k_ep and match.group(3) == step):
                if ((fade and k_part in ['precedemment', 'episode', 'asuivre', 'documentaire'])
                    or (av_sync and k_part in ['precedemment', 'episode'])):
                    files.append(os.path.join(output_dir, f))
            continue

        if (match := re.match(re.compile("(ep\d{2})_([a-z]+)_(\d{3})__[a-z]{1}__[a-z0-9]+_([a-z]+)"), f)):
            # find 1st and latest shot
            k_part = match.group(2)
            if (match.group(1) == k_ep and match.group(4) == step):
                shot_no = int(match.group(3))

                if shot_no == 0:
                    if k_part in ['precedemment', 'episode']:
                        files.append(os.path.join(output_dir, f))
                        continue

                if shot_no == db[k_ep]['video']['target'][k_part]['shots'][-1]['no']:
                    # Last shot
                    if ((av_sync and k_part in ['precedemment', 'episode'])
                        or (fade and k_part in ['precedemment', 'episode', 'asuivre', 'documentaire'])):
                        files.append(os.path.join(output_dir, f))
                continue

    filesize = 0
    for f in files:
        try: filesize += os.stat(f).st_size
        except: pass
    filesize = int(filesize/ (1024 * 1024))


    if verbose:
        print_lightgreen(f"folders to remove")
        pprint(folders)
        print_lightgreen(f"files to remove")
        pprint(files)
        print_lightcyan(f"- remove {len(folders)} folder(s)")
        print_lightcyan(f"- remove {len(files)} files: {filesize} MB")


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

