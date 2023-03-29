# -*- coding: utf-8 -*-
import sys
import re
from pprint import pprint
from utils.common import nested_dict_set
from utils.pretty_print import *

# ID used to identify stage
FILTERS_IDS = [
    'deinterlace',
    'pre_upscale',
    'denoise',
    'sharpen',
    'upscale'
]


def parser_strip(valueStr):
    for c in ['\"', ' ', '\n', '\r']:
        valueStr = valueStr.replace(c, '')
    return valueStr


def __clean_filter(a_string):
    for c in ['\"', '\r', '\n', ' ']:
        a_string = a_string.replace(c, '')
    return a_string



def parse_filters(db_video, config, k_section, verbose=False):
    verbose = False
    if verbose:
        print_green("-------------------------------")
        print_green("|        parse_filters        |")
        print_green("| k_section=[%s]" % (k_section))
        if k_section.startswith('filters'):
            for k_option in config.options(k_section):
                print_lightcyan("%s=" % (k_option), end='')
                print_blue(config.get(k_section, k_option))
        print_green("-------------------------------")

    # Find part and subpart
    # k_section is filters_part[_subpart]
    tmp = re.search(re.compile("^filters_([a-z_]+)[.]*([0-9]*)$"), k_section)
    if tmp is None:
        print_red("parse_filters: error: [%s] is not a valid filter label" % (k_section))
        sys.exit()
    else:
        k_part = tmp.group(1)

    k_option = config.options(k_section)[0]
    if k_option != 'default' and not k_option.isdecimal():
        # Not allowed
        if verbose:
            print_yellow("\tDiscarded")
        return

    # Convert filter str to a list of dict
    steps_str = config.get(k_section, k_option)
    steps_str = __clean_filter(steps_str)
    step_list = steps_str.split(';')

    filters = list()
    for step_str in step_list:
        step_dict = {
            'save': False
        }
        if step_str.startswith('*'):
            step_str = step_str[1:]
            step_dict['save'] = True

        result = re.match(re.compile("^([a-z_]+):(.+)$"), step_str)
        if result is not None:
            step_dict['type'] = result.group(1)
            step_dict['str'] = result.group(2)
            filters.append(step_dict)
        else:
            # May use yes-pattern or no-pattern in the previous regex
            # but no time
            result = re.match(re.compile("^([a-z]+)$"), step_str)
            if result is not None:
                step_dict['type'] = result.group(1)
                step_dict['str'] = ''
                filters.append(step_dict)

    nested_dict_set(db_video, filters, k_part, 'filters', k_option)

    if verbose:
        print_yellow("______________ %s: %s ______________" % (__name__, k_section))
        pprint(db_video[k_part]['filters'])
        print_yellow("__________________________________________________________________\n")





