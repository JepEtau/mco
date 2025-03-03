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



def parse_filters(
    db_video,
    config: ConfigParser,
    k_section: str,
    verbose: bool = False
):
    """Only parse filters, no verifications.
    This is done when consolidating the scene
    """
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
        print(red(f"parse_filters: error: [{k_section}] is not a valid filter label"))
        sys.exit()

    for k_option in config.options(k_section):
        if verbose:
            print(darkgrey(f"  parse filter [{k_section}]{k_option}"))

        # Convert filter str to a list of dict
        filters_str: str = config.get(k_section, k_option)

        if filters_str in config.options(k_section):
            if verbose:
                print(darkgrey(f"    alias to {filters_str}"))
            filters_str: str = config.get(k_section, filters_str)

        filters: list[str] = (
            clean_ffmpeg_filter(filters_str).split(';')
        )
        filters = list([f for f in filters if f != ''])
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

            elif (result := re.search(re.compile(r"^([a-z_]+)$"), f)):
                # May use yes-pattern or no-pattern in the previous regex
                # if result.group(1) not in TASK_NAMES:
                #     raise ValueError(f"{result.group(1)} is not a valid task")
                task_filter = Filter(
                    task_name=result.group(1),
                    sequence=''
                )

            else:
                # pprint(db_video)
                raise ValueError(f"Unrecognized filter: {f} (k_chapter: {k_chapter})")


            if task_filter.task_name not in TASK_NAMES:
                print(red(f"[W] {task_filter.task_name} is not a valid task name"))
                continue

            if task_filter.task_name is not None:
                scene_filters[task_filter.task_name] = task_filter
            else:
                print(f"TODO: rework filter: {k_section}")

        nested_dict_set(
            db_video,
            keys=(k_chapter, 'filters', k_option),
            o=scene_filters
        )

        if verbose and k_option == '999':
            # used to debug complex processing chains
            pprint(scene_filters)
            sys.exit()

    if verbose:
        print(green(f"\tfinally: section {k_section}"))
        pprint(db_video[k_chapter]['filters'])
        # if len(db_video[k_chapter]['filters']['default']) > 0:
        #     sys.exit()



