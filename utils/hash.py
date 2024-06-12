import sys
from hashlib import md5
import collections
import configparser
import os
from pprint import pprint


def create_hash_file(db, ep: str) -> str:
    hashes_dir: str = db['common']['directories']['hashes']
    os.makedirs(hashes_dir, exist_ok=True)

    hash_log_file: str = os.path.join(hashes_dir, f"{ep}_hash.ini")

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


def store_filter(filter_str: str, hash_log_file: str) -> str:
    """Add the filter to the db and returns the short hash code"""
    hash = hash(filter_str=filter)

    config_filter_hash = configparser.ConfigParser(dict_type=collections.OrderedDict)
    config_filter_hash.read(hash_log_file)

    k_section = 'md5'
    if not config_filter_hash.has_option(k_section, hash):
        config_filter_hash.set(k_section, hash, f"\"{filter_str}\"")
        with open(hash_log_file, 'w') as config_file:
            config_filter_hash.write(config_file)
    return hash



def calc_hash(line_str: str) -> str:
    return md5(line_str.encode('utf-8')).hexdigest()[:7]


def store_hash_filter(hash: str, filter_str: str, hash_log_file: str) -> str:
    """Add the filter to the db and returns the short hash code"""
    config_filter_hash = configparser.ConfigParser(dict_type=collections.OrderedDict)
    config_filter_hash.read(hash_log_file)

    k_section = 'md5'
    if not config_filter_hash.has_option(k_section, hash):
        config_filter_hash.set(k_section, hash, "\"%s\"" % (filter_str))
        with open(hash_log_file, 'w') as config_file:
            config_filter_hash.write(config_file)
    return hash
