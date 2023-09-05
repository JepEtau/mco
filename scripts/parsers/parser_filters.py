# -*- coding: utf-8 -*-
import sys
import re
from pprint import pprint
from utils.nested_dict import nested_dict_set
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



def parse_filters(db_video, config, k_section):
    verbose = False
    if verbose:
        print_lightcyan("Parse_filters: ")
        print_green(f"\tsection: {k_section}")
        if k_section.startswith('filters'):
            for k_option in config.options(k_section):
                print_green(f"\t{k_option} = ", end='')
                print_lightgrey(config.get(k_section, k_option))

    # Find part and subpart
    # k_section is filters_part[_subpart]
    tmp = re.search(re.compile("^filters_([a-z_]+)[.]*([0-9]*)$"), k_section)
    if tmp is None:
        print_red("parse_filters: error: [%s] is not a valid filter label" % (k_section))
        sys.exit()
    else:
        k_part = tmp.group(1)

    for k_option in config.options(k_section):
        if k_option != 'default' and not k_option.isdecimal():
            # Not allowed
            if verbose:
                print_yellow("\tDiscarded")
            print_red(f"\tError: filter {k_section}/{k_option}")
            return

        if verbose:
            print_green(f"\tparse filter {k_section}/{k_option}")
        # Convert filter str to a list of dict
        steps_str = config.get(k_section, k_option)
        steps_str = __clean_filter(steps_str)
        step_list = steps_str.split(';')

        filters = list()
        for step_str in step_list:
            step_dict = {
                'save': False,
                'id': None,
            }

            # Save images after this filter
            if step_str.startswith('*'):
                step_str = step_str[1:]
                step_dict['save'] = True

            # Get the node id
            if step_str.startswith('id:'):
                result = re.match(re.compile("id:([a-z0-9_-]+),(.+)$"), step_str)
                if result is not None:
                    step_dict['id'] = result.group(1)
                    step_str = result.group(2)
                else:
                    sys.exit(p_red(f"Error parsing filters: [{step_str}]"))

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

        if verbose and k_option == '999':
            # used to debug complex processing chains
            pprint(filters)
            sys.exit()

    if verbose:
        print_green(f"\tfinally: section {k_section}")
        pprint(db_video[k_part]['filters'])




