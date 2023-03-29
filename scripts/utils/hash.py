# -*- coding: utf-8 -*-
import os
from hashlib import md5
import collections
import configparser
from pprint import pprint
from utils.pretty_print import *

FILENAME_TEMPLATE = "%s_%%05d__%s__%02d%s.png"
STEP_INC = 1
STEP_REPLACE = STEP_INC


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


def get_hash_for_replace(shot):
    replace_str = ""
    for k, v in shot['replace'].items():
        replace_str += "%s:%s," % (k, v)
    hash = calculate_hash(filter_str=replace_str)
    return hash


def is_hash_for_replace_valid(shot):
    hash = get_hash_for_replace(shot)
    replace_hash_filepath = os.path.join(shot['cache'], "replace_%s" % (hash))
    print_lightgrey("\t\t\tsearch replace_hash_filepath: %s" % (replace_hash_filepath))

    if os.path.exists(replace_hash_filepath):
        return True
    return False


def store_hash_for_replace(shot):
    for f in os.listdir(shot['cache']):
        if f.startswith("replace_"):
            os.remove(os.path.join(shot['cache'], f))

    hash = get_hash_for_replace(shot)
    replace_hash_filepath = os.path.join(shot['cache'], "replace_%s" % (hash))
    open(replace_hash_filepath, mode='w').close()

    print_lightgrey("\t\t\treplace_hash_filepath: %s" % (replace_hash_filepath))


def calculate_hash(filter_str):
    return md5(filter_str.encode('utf-8')).hexdigest()[:7]


def get_first_image_filepath(shot, folder, step_no, hash=''):
    if hash != '':
        suffix = "_%s" % (hash)
    else:
        suffix = ''
    filename_template = FILENAME_TEMPLATE % (shot['k_ep'], shot['k_ed'], step_no, suffix)
    if step_no == STEP_REPLACE:
        # First task after deinterlace, use replace dict
        print("\t\t\tget_first_image_filepath: use replace array")
        frame_start = 0
        new_frame_no = shot['replace'][frame_start]
    elif step_no == 0:
        # Deinterlace
        print("\t\t\tget_first_image_filepath: deinterlaced")
        new_frame_no = shot['start']
    else:
        new_frame_no = 0

    image_filepath = os.path.join(os.path.normpath(folder),
        filename_template % (new_frame_no))
    return image_filepath



def get_image_list(shot, folder, step_no, hash=''):
    if hash != '':
        suffix = "_%s" % (hash)
    else:
        suffix = ''
    filename_template = FILENAME_TEMPLATE % (shot['k_ep'], shot['k_ed'], step_no, suffix)

    image_list = list()

    replace = None
    if step_no == STEP_REPLACE:
        # First task after deinterlace, use replace dict
        print("\t\t\tget_image_list: use replace array")
        replace = shot['replace']
        frame_start = shot['start']
        filename_template = FILENAME_TEMPLATE % (shot['k_ep'], shot['k_ed'], 0, suffix)
    elif step_no == 0:
        # Deinterlace
        print("\t\t\tget_image_list: deinterlaced")
        frame_start = shot['start']
    else:
        frame_start = 0
    frame_count = shot['count']

    for no in range(frame_start, frame_start+frame_count):
        try:
            new_frame_no = replace[no]
        except:
            new_frame_no = no
        # print(new_frame_no)
        image_list.append(os.path.join(os.path.normpath(folder),
            filename_template % (new_frame_no)))

    return image_list
