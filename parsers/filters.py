from configparser import ConfigParser
import sys
import re
from pprint import pprint
from .helpers import nested_dict_set
from utils.p_print import *

# ID used to identify stage
FILTERS_IDS = [
    'deinterlace',
    'pre_upscale',
    'denoise',
    'sharpen',
    'upscale'
]


def parser_strip(data: str) -> str:
    for c in ['\"', ' ', '\n', '\r']:
        data = data.replace(c, '')
    return data


def __clean_filter(data: str) -> str:
    for c in ['\"', '\r', '\n', ' ']:
        data = data.replace(c, '')
    return data



def parse_filters(db_video, config: ConfigParser, k_section: str):
    verbose = False
    if verbose:
        print(lightcyan("Parse_filters: "))
        print(green(f"\tsection: {k_section}"))
        if k_section.startswith('filters'):
            for k_option in config.options(k_section):
                print(
                    green(f"\t{k_option} = "),
                    lightgrey(config.get(k_section, k_option))
                )

    # Find chapter and subchapter
    # k_section is filters_chapter[_subchapter]
    tmp = re.search(re.compile(r"^filters_([a-z_]+)[.]*([0-9]*)$"), k_section)
    if tmp is None:
        print(red("parse_filters: error: [%s] is not a valid filter label" % (k_section)))
        sys.exit()
    else:
        k_chapter = tmp.group(1)

    for k_option in config.options(k_section):
        if k_option != 'default' and not k_option.isdecimal():
            # Not allowed
            if verbose:
                print(yellow("\tDiscarded"))
            print(red(f"\tError: filter {k_section}/{k_option}"))
            return

        if verbose:
            print(green(f"\tparse filter {k_section}/{k_option}"))
        # Convert filter str to a list of dict
        steps_str = config.get(k_section, k_option)
        steps_str = __clean_filter(steps_str)
        step_list: list[str] = steps_str.split(';')

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
                result = re.match(re.compile(r"id:([a-z0-9_-]+),(.+)$"), step_str)
                if result is not None:
                    step_dict['id'] = result.group(1)
                    step_str = result.group(2)
                else:
                    sys.exit(red(f"Error parsing filters: [{step_str}]"))

            result = re.match(re.compile(r"^([a-z_]+):(.+)$"), step_str)
            if result is not None:
                step_dict['type'] = result.group(1)
                step_dict['str'] = result.group(2)
                filters.append(step_dict)
            else:
                # May use yes-pattern or no-pattern in the previous regex
                # but no time
                result = re.match(re.compile(r"^([a-z]+)$"), step_str)
                if result is not None:
                    step_dict['type'] = result.group(1)
                    step_dict['str'] = ''
                    filters.append(step_dict)

        nested_dict_set(db_video, filters, k_chapter, 'filters', k_option)

        if verbose and k_option == '999':
            # used to debug complex processing chains
            pprint(filters)
            sys.exit()

    if verbose:
        print(green(f"\tfinally: section {k_section}"))
        pprint(db_video[k_chapter]['filters'])




