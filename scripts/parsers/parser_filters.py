#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import sys
from pprint import pprint
from copy import deepcopy
import configparser

# ID used to identify filtering step
FILTERS_IDS = [
    'deinterlace',
    'pre_upscale',
    'denoise',
    'sharpen',
    'upscale'
]

# Filters that are handled by FFmpeg
FILTERS_FFMPEG = [
    'deinterlace',
    'pre_upscale',
    'upscale',
]

# Filters that are handled by openCV / sk_image -> todo: replace by 'python'
FILTERS_OPENCV = [
    'upscale',
    'denoise',
    'sharpen',
]


def parser_strip(valueStr):
    for c in ['\"', ' ', '\n', '\r']:
        valueStr = valueStr.replace(c, '')
    return valueStr


def parse_filters_initialize(type='common', verbose=False):
    # Returns an empty filter structure
    # i.e. 'None' or 'default' filter
    default_filters = dict()
    for k in ['ffmpeg', 'opencv', 'id']:
        default_filters[k] = dict()
    for k in FILTERS_IDS:
        default_filters['id'][k] = 0

    if type == 'common':
        for k in FILTERS_FFMPEG:
            default_filters['ffmpeg'][k] = None
        for k in FILTERS_OPENCV:
            default_filters['opencv'][k] = None
    else:
        for k in FILTERS_FFMPEG:
            default_filters['ffmpeg'][k] = 'default'
        for k in FILTERS_OPENCV:
            default_filters['opencv'][k] = 'default'

    return default_filters




#===========================================================================
#
#   Consolidate filters, i.e. replace 'default' by the default filter value
#
#===========================================================================
def parser_filters_consolidate(cfg_filters_common,
                                cfg_filters_edition,
                                cfg_filters_episode_common,
                                cfg_filters_episode,
                                label='unknown',
                                verbose=False):

    # if label == '[k:ep01]':
    #     verbose = True
    if verbose:
        print("\n___ %s: %s_______________________________" % (__name__, label))
        print("cfg_filters_common['filters']:")
        pprint(cfg_filters_common)
        print("\n-----------------------------------------\ncfg_filters_edition['filters']:")
        pprint(cfg_filters_edition)
        print("\n-----------------------------------------\ncfg_filters_episode_common['filters']:")
        pprint(cfg_filters_episode_common)
        print("\n-----------------------------------------\ncfg_filters_episode['filters']:")
        pprint(cfg_filters_episode)
        print("=========================================")


    for k_part, part in cfg_filters_episode.items():
        # if verbose:
        #     print("cfg_filters_episode[%s]" % (k_part))

        #     if part == 'default':
        #         print("This part is default, use the default from edition")

        for k_prog in ['ffmpeg', 'opencv']:

            for k_f, f in part[k_prog].items():
                if verbose:
                    print("\tcfg_filters_episode[%s][%s][%s] = %s" % (k_part, k_prog, k_f, f))
                if f == 'default':
                    # At first, if this filter id is not the default filter, try to consolidate
                    # with the default one of this part
                    if 'default' in cfg_filters_episode.keys() and k_part != 'default':
                        # print("cfg_filters_episode[%s][%s][%s] = %s" % (k_part, k_prog, k_f, f))
                        # print("\tTry to use the default filter:" )
                        f_tmp = cfg_filters_episode['default'][k_prog][k_f]
                        cfg_filters_episode[k_part][k_prog][k_f] = f_tmp
                        if f_tmp != 'default':
                            continue

                    # Then, get the parent filter until it is not a default filter
                    for parent in [cfg_filters_episode_common,
                                    cfg_filters_edition,
                                    cfg_filters_common]:
                        if k_part in parent.keys():
                            # use it
                            k_part_tmp = k_part
                        else:
                            # else, use the 'default' part
                            k_part_tmp = 'default'

                        if k_part_tmp not in parent.keys():
                            # print("%s: warning: %s does not exist" % (__name__, k_part_tmp))
                            continue

                        if (parent[k_part_tmp][k_prog][k_f] is not None
                            and parent[k_part_tmp][k_prog][k_f] != 'default'):
                            cfg_filters_episode[k_part][k_prog][k_f] = parent[k_part_tmp][k_prog][k_f]
                            if (k_f in FILTERS_IDS
                                and cfg_filters_episode[k_part][k_prog][k_f] is not None):
                                cfg_filters_episode[k_part]['id'][k_f] = parent[k_part_tmp]['id'][k_f]
                            break


    # Finaly, replace remaining 'default' by None
    for k_part, part in cfg_filters_episode.items():
        for k_prog in ['ffmpeg', 'opencv']:
            for k_f, f in part[k_prog].items():
                if f == 'default':
                    cfg_filters_episode[k_part][k_prog][k_f] = None

    if verbose:
        print("_________consolidated_________________")
        pprint(cfg_filters_episode)
        sys.exit()




#===========================================================================
#
#   Parse filters from a configuration file
#
#===========================================================================
def parse_and_update_filters_generique(db:dict, config, k_section, verbose=False):

    # if k_section.startswith('filters_g_reportage'):
    #     verbose = True

    if verbose:
        print("-------------------------------")
        print("|        parse_filters        |")
        print("| k_section=[%s]" % (k_section))
        if k_section.startswith('filters'):
            print("")
            for k_option in config.options(k_section):
                print("%s=" % (k_option), config.get(k_section, k_option))
        print("-------------------------------")

    # Define a filters structure if not already exist in this database
    if 'filters' not in db.keys():
        db['filters'] = dict()

    # Get filter ID: default or used by a shot/frame
    # filter_id = 'default'
    # tmp = re.search(re.compile("^filters_([a-z_]+)(?:.?([0-9]*))$"), k_section)
    # if tmp is not None:
    #     k_part = tmp.group(1)
    #     if tmp.group(2) != '':
    #         filter_id = tmp.group(2)
    # else:
    #     sys.exit("Error: cannot parse filter section [%s]" % (k_section))


    filter_id = 'default'
    if k_section == 'common':
        # This is the common filter used if no one is defined:
        # Overwrite k_section for common
        k_section = 'filters'
        db['filters'] = {filter_id: parse_filters_initialize(type='common')}
    elif k_section == 'filters':
        db['filters'][filter_id] = parse_filters_initialize(type='default')
    else:
        # Find part and filter used for a shot/frame
        tmp = re.search(re.compile("^filters_([a-z_]+)(?:.?([0-9]*))$"), k_section)
        if tmp is not None:
            if tmp.group(2) != '':
                filter_id = tmp.group(2)
        db['filters'][filter_id] = parse_filters_initialize(type='default')


    # Modify filters handled by FFMPEG
    for k in FILTERS_FFMPEG:
        if k+'_ffmpeg' in config.options(k_section):
            valueStr = parser_strip(config.get(k_section, k+'_ffmpeg'))
            if valueStr != "":
                # Overwrite by the defined filter defined in the config file
                db['filters'][filter_id]['ffmpeg'][k] = valueStr
            else:
                # Do not use the parent filter, i.e. no Filter shall be used
                db['filters'][filter_id]['ffmpeg'][k] = None


    # Modify filters handled by openCV
    for k in FILTERS_OPENCV:
        # if k_part == 'default' and k_subpart == "":
        #     programs['opencv'][k] = None
        # else:
        #     programs['opencv'][k] = 'default'

        if k in config.options(k_section):
            valueStr = parser_strip(config.get(k_section, k))
            if valueStr != "":
                # Overwrite by the defined filter defined in the config file
                subfilters = valueStr.split(',')
                db['filters'][filter_id]['opencv'][k] = []
                for s in subfilters:
                    db['filters'][filter_id]['opencv'][k].append(s)
            else:
                # Do not use the parent filter, i.e. no Filter shall be used
                db['filters'][filter_id]['opencv'][k] = None


    # Assign ID
    for f in FILTERS_IDS:
        k_id = 'id_%s' % (f)
        if k_id in config.options(k_section):
            db['filters'][filter_id]['id'][f] = int(config.get(k_section, k_id))
        else:
            db['filters'][filter_id]['id'][f] = 0

    if verbose:
        print("______________ %s: %s ______________" % (__name__, k_section))
        pprint(db['filters'])
        # if k_section.startswith('filters_g_reportage'):
        #     sys.exit()






#===========================================================================
#
#   Parse filters from a configuration file
#
#===========================================================================
def parse_and_update_filters(db:dict, config, k_section, verbose=False):

    if verbose:
        print("\n-------------------------------")
        print("|        parse_filters        |")
        print("| k_section=[%s]" % (k_section))
        if k_section.startswith('filters'):
            print("")
            for k_option in config.options(k_section):
                print("\t%s=" % (k_option), config.get(k_section, k_option))
        print("-------------------------------")

    # Define a filters structure if not already exist in this database
    if 'filters' not in db.keys():
        db['filters'] = dict()


    filter_id = 'default'
    if k_section == 'common':
        # This is the common filter used if no one is defined:
        k_part = 'default'
        filter_id = 'default'
        # Overwrite k_section for common
        k_section = 'filters'
        db['filters'] = {filter_id: parse_filters_initialize(type='common')}
    elif k_section == 'filters':
        k_part = 'default'
        filter_id = 'default'
        db['filters'][filter_id] = parse_filters_initialize(type='default')
    else:
        # Find part and subpart
        # k_section is filters_part[_subpart]
        tmp = re.search(re.compile("^filters_([a-z_]+)[.]*([0-9]*)$"), k_section)
        if tmp is None:
            print("parse_and_update_filters: error: [%s] is not a valid filter label" % (k_section))
            sys.exit()
        else:
            k_part = tmp.group(1)
            if tmp.group(2) != '':
                filter_id = "%s.%s" % (k_part, tmp.group(2))
            else:
                filter_id = k_part
            if filter_id not in db['filters'].keys():
                db['filters'][filter_id] = parse_filters_initialize(type='default')



    # Modify filters handled by FFMPEG
    for k in FILTERS_FFMPEG:
        if k+'_ffmpeg' in config.options(k_section):
            valueStr = parser_strip(config.get(k_section, k+'_ffmpeg'))
            if valueStr != "":
                # Overwrite by the defined filter defined in the config file
                db['filters'][filter_id]['ffmpeg'][k] = valueStr
            else:
                # Do not use the parent filter, i.e. no Filter shall be used
                db['filters'][filter_id]['ffmpeg'][k] = None



    # Modify filters handled by openCV
    for k in FILTERS_OPENCV:
        # if k_part == 'default' and k_subpart == "":
        #     programs['opencv'][k] = None
        # else:
        #     programs['opencv'][k] = 'default'

        if k in config.options(k_section):
            valueStr = parser_strip(config.get(k_section, k))
            if valueStr != "":
                # Overwrite by the defined filter defined in the config file
                subfilters = valueStr.split(',')
                db['filters'][filter_id]['opencv'][k] = []
                for s in subfilters:
                    db['filters'][filter_id]['opencv'][k].append(s)
            else:
                # Do not use the parent filter, i.e. no Filter shall be used
                db['filters'][filter_id]['opencv'][k] = None


    # Assign ID
    for f in FILTERS_IDS:
        k_id = 'id_%s' % (f)
        if k_id in config.options(k_section):
            db['filters'][filter_id]['id'][f] = int(config.get(k_section, k_id))
        else:
            db['filters'][filter_id]['id'][f] = 0

    if verbose:
        print("______________ %s: %s: %s ______________" % (__name__, k_section, filter_id))
        pprint(db['filters'])
        print("__________________________________________________________________\n")






#===========================================================================
#
#   Parse filters from a configuration file
#
#===========================================================================
def parse_and_update_filters_previous(db:dict, config, k_section, verbose=False):

    verbose =True

    if verbose:
        print("-------------------------------")
        print("|        parse_filters        |")
        print("| k_section=[%s]" % (k_section))
        print("")
        print(config)
        print("-------------------------------")

    # Define a filters structure if not already exist in this database
    if 'filters' not in db.keys():
        db['filters'] = dict()


    if k_section == 'common':
        # This is the common filter used if no one is defined:
        k_part = 'default'
        k_section_tmp = 'default'
        # Overwrite k_section for common
        k_section = 'filters'
        db['filters'] = {k_section_tmp: parse_filters_initialize(type='common')}
    elif k_section == 'filters':
        k_part = 'default'
        k_section_tmp = 'default'
        db['filters'][k_section_tmp] = parse_filters_initialize(type='default')
    else:
        # Find part and subpart
        # k_section is filters_part[_subpart]
        tmp = re.search(re.compile("^filters_([a-z_]+)[_]*([0-9]*)$"), k_section)
        if tmp is None:
            print("parse_and_update_filters_previous: error: [%s] is not a valid filter label" % (k_section))
            sys.exit()
        else:
            k_part = tmp.group(1)
            if len(tmp.groups()) == 3:
                k_section_tmp = "%s_%s" % (k_part, tmp.group(2))
            else:
                k_section_tmp = k_part
            db['filters'][k_section_tmp] = parse_filters_initialize(type='default')



    # Modify filters handled by FFMPEG
    for k in FILTERS_FFMPEG:
        if k+'_ffmpeg' in config.options(k_section):
            valueStr = parser_strip(config.get(k_section, k+'_ffmpeg'))
            if valueStr != "":
                # Overwrite by the defined filter defined in the config file
                db['filters'][k_section_tmp]['ffmpeg'][k] = valueStr
            else:
                # Do not use the parent filter, i.e. no Filter shall be used
                db['filters'][k_section_tmp]['ffmpeg'][k] = None



    # Modify filters handled by openCV
    for k in FILTERS_OPENCV:
        # if k_part == 'default' and k_subpart == "":
        #     programs['opencv'][k] = None
        # else:
        #     programs['opencv'][k] = 'default'

        if k in config.options(k_section):
            valueStr = parser_strip(config.get(k_section, k))
            if valueStr != "":
                # Overwrite by the defined filter defined in the config file
                subfilters = valueStr.split(',')
                db['filters'][k_section_tmp]['opencv'][k] = []
                for s in subfilters:
                    db['filters'][k_section_tmp]['opencv'][k].append(s)
            else:
                # Do not use the parent filter, i.e. no Filter shall be used
                db['filters'][k_section_tmp]['opencv'][k] = None


    # Assign ID
    for f in FILTERS_IDS:
        k_id = 'id_%s' % (f)
        if k_id in config.options(k_section):
            db['filters'][k_section_tmp]['id'][f] = int(config.get(k_section, k_id))
        else:
            db['filters'][k_section_tmp]['id'][f] = 0

    if verbose:
        print("______________ %s: %s: %s ______________" % (__name__, k_section, k_section_tmp))
        pprint(db['filters'])
        if k_section.startswith('filters_g_reportage'):
            sys.exit()


