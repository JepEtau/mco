from __future__ import annotations
from configparser import ConfigParser
import sys
import re
from pprint import pprint
from .helpers import nested_dict_set
from utils.p_print import *
from ._types import Filter, TASK_NAMES, TaskName

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


def clean_ffmpeg_filter(data: str) -> str:
    for c in ['\"', '\r', '\n', ' ']:
        data = data.replace(c, '')
    return data



def parse_filters(db_video, config: ConfigParser, k_section: str):
    """Only parse filters, no verifications.
    This is done when consolidating the scene
    """
    verbose = True
    if verbose:
        print(lightcyan(f"Parse_filters:"))
        print(green(f"  section: {k_section}"))
        if k_section.startswith('filters'):
            for k_option in config.options(k_section):
                print(
                    green(f"\t{k_option} = "),
                    lightgrey(config.get(k_section, k_option))
                )

    # Find chapter and subchapter
    # k_section is filters_chapter[_subchapter]
    if (tmp := re.search(re.compile(r"^filters_([a-z_]+)[.]*([0-9]*)$"), k_section)):
        k_chapter = tmp.group(1)
    else:
        print(red("parse_filters: error: [%s] is not a valid filter label" % (k_section)))
        sys.exit()

    for k_option in config.options(k_section):
        # if k_option != 'default' and not k_option.isdecimal():
        #     # Not allowed
        #     if verbose:
        #         print(yellow("\tDiscarded"))
        #     print(red(f"\tError: filter {k_section}/{k_option}"))
        #     return

        if verbose:
            print(green(f"\tparse filter {k_section}:{k_option}"))
        # Convert filter str to a list of dict
        filters_str: str = config.get(k_section, k_option)
        filters: list[str] = (
            clean_ffmpeg_filter(filters_str).split(';')
        )
        filters = list([f for f in filters if f != ''])
        pprint(filters)
        scene_filters: dict[TaskName, Filter] = {}
        for f in filters:

            task_filter: Filter | None = None
            if (result := re.search(re.compile(r"^([a-z_]+):(.+)$"), f)):
                # if result.group(1) not in TASK_NAMES:
                #     raise ValueError(f"{result.group(1)} is not a valid task")
                task_filter = Filter(
                    task_name=result.group(1),
                    sequence=result.group(2)
                )

            elif (result := re.search(re.compile(r"^([a-z]+)$"), f)):
                # May use yes-pattern or no-pattern in the previous regex
                # if result.group(1) not in TASK_NAMES:
                #     raise ValueError(f"{result.group(1)} is not a valid task")
                task_filter = Filter(
                    task_name=result.group(1),
                    sequence=''
                )

            else:
                pprint(filters)
                raise ValueError("Unrecognized filter")

            if task_filter.task_name not in TASK_NAMES:
                print(red(f"[W] {task_filter.task_name} is not a valid task name"))
                continue

            if task_filter.task_name is not None:
                scene_filters[task_filter.task_name] = task_filter
            else:
                print(f"TODO: rework filter: {k_section}")

        nested_dict_set(db_video, scene_filters, k_chapter, 'filters', k_option)

        if verbose and k_option == '999':
            # used to debug complex processing chains
            pprint(scene_filters)
            sys.exit()

    if verbose:
        print(green(f"\tfinally: section {k_section}"))
        pprint(db_video[k_chapter]['filters'])
        # if len(db_video[k_chapter]['filters']['default']) > 0:
        #     sys.exit()



