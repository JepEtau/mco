# -*- coding: utf-8 -*-
import os
from hashlib import md5
import collections
import configparser
from pprint import pprint
from utils.pretty_print import *

FILENAME_TEMPLATE = "%s_%%05d__%s__%02d%s.png"
STEP_INC = 1


def create_log(db, k_ep):
    if not os.path.exists(db['common']['directories']['hashes']):
        os.makedirs(db['common']['directories']['hashes'])

    hash_log_file = os.path.join(db['common']['directories']['hashes'],
        "%s_hash.ini" % (k_ep))

    if os.path.exists(hash_log_file):
        config_filter_hash = configparser.ConfigParser(dict_type=collections.OrderedDict)
        config_filter_hash.read(hash_log_file)
    else:
        config_filter_hash = configparser.ConfigParser(dict(), collections.OrderedDict)

    k_section = 'md5'
    if not config_filter_hash.has_section(k_section):
        config_filter_hash[k_section] = dict()

    with open(hash_log_file, 'w') as config_file:
        config_filter_hash.write(config_file)

    return hash_log_file



def log_filter(filter_str, hash_log_file):
    """Add the filter to the db and returns the short hash code"""
    hash = calculate_hash(filter_str=filter_str)

    config_filter_hash = configparser.ConfigParser(dict_type=collections.OrderedDict)
    config_filter_hash.read(hash_log_file)

    k_section = 'md5'
    if not config_filter_hash.has_option(k_section, hash):
        config_filter_hash.set(k_section, hash, "\"%s\"" % (filter_str))
        with open(hash_log_file, 'w') as config_file:
            config_filter_hash.write(config_file)
    return hash


def calculate_hash_for_replace(shot):
    replace_str = ""
    for k, v in shot['replace'].items():
        replace_str += "%s:%s," % (k, v)
    hash = calculate_hash(filter_str=replace_str)
    return hash


def calculate_hash(filter_str):
    return md5(filter_str.encode('utf-8')).hexdigest()[:7]


def get_first_image_filepath(shot, folder, step_no, hash=''):

    suffix = "_%s" % (hash) if hash != '' else ''
    filename_template = FILENAME_TEMPLATE % (shot['k_ep'], shot['k_ed'], step_no, suffix)

    if step_no == 0:
        # Deinterlace
        print("\t\t\tget_first_image_filepath: deinterlaced")
        new_frame_no = shot['start']
    else:
        new_frame_no = 0

    image_filepath = os.path.join(os.path.normpath(folder),
        filename_template % (new_frame_no))
    return image_filepath


def get_new_image_list(shot, step_no, hash=''):
    # if step_no != shot['last_step']['step_no_replace'])
    #     sys.exit()
    print_orange("get_new_image_list: use replace list, step=%d" % (step_no))

    # Template to name the files
    suffix = "_%s" % (hash) if hash != '' else ''
    filename_template = FILENAME_TEMPLATE % (shot['k_ep'], shot['k_ed'], step_no, suffix)
    folder = os.path.join(shot['cache'], "%02d" %  (step_no-STEP_INC))

    # Start frame no.
    # Generate the list
    replace = shot['replace']
    image_list = list()
    if step_no == 0:
        # Deinterlace: use frame no to facilitate the debug
        for no in range(shot['start'], shot['start'] + shot['count']):
            try:
                new_frame_no = replace[no]
                print_purple("\t%d -> %d" % (no, new_frame_no))
            except:
                new_frame_no = no
                print_green("\t%d -> %d" % (no, new_frame_no))

            image_list.append(os.path.join(os.path.normpath(folder),
                filename_template % (new_frame_no)))
    else:
        for no in range(shot['count']):
            try:
                new_frame_no = replace[shot['start'] + no] - shot['start']
                print_purple("\t%d <- %d" % (no, new_frame_no))
            except:
                new_frame_no = no
                print_green("\t%d <- %d" % (no, new_frame_no))

            image_list.append(os.path.join(os.path.normpath(folder),
                filename_template % (new_frame_no)))

    return image_list


def get_image_list(shot, folder, step_no, hash=''):
    try:
        if step_no == shot['last_step']['step_no_replace']:
            return get_new_image_list(shot=shot, step_no=step_no, hash=hash)
    except:
        print_orange("get_image_list: continue, step=%d" % (step_no))

    # Template to name the files
    suffix = "_%s" % (hash) if hash != '' else ''
    filename_template = FILENAME_TEMPLATE % (shot['k_ep'], shot['k_ed'], step_no, suffix)

    # Start frame no.: deinterlace: use frame no to facilitate the debug
    frame_start = shot['start'] if step_no == 0 else 0

    # Generate the list
    image_list = list()
    for no in range(frame_start, frame_start+shot['count']):
        image_list.append(os.path.join(os.path.normpath(folder),
            filename_template % (no)))

    return image_list
