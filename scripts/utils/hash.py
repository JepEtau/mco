# -*- coding: utf-8 -*-
from hashlib import md5
import collections
import configparser
import os
from pprint import pprint



def create_hash_file(db, k_ep):
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



def get_hash_from_task(shot, task):
    __task = 'geometry' if task == 'final' else task
    for f in shot['filters']:
        if __task == f['task']:
            return f['hash']

    pprint(shot['filters'])
    sys.exit(print_red("Error: get_hash_from_step: [%s] not found" % (task)))
    return None


def get_hash_from_last_task(shot):
    return get_hash_from_task(shot, shot['last_task'])

