from argparse import ArgumentParser
from parsers import (
    all_chapter_keys,
    TASK_NAMES,
)


def common_argument_parser(
    description: str = '',
    add_language: bool = False,
) -> ArgumentParser:

    parser = ArgumentParser(description=description)
    parser.add_argument(
        "--edition",
        "-ed",
        choices=('j', 'f', 'k', 's', 's0'),
        default='',
        required=False,
        help="Filter by edition"
    )

    parser.add_argument(
        "--episode",
        "-ep",
        type=int,
        default=0,
        required=False,
        help="from 1 to 39"
    )

    parser.add_argument(
        "--chapter",
        "-ch",
        choices=all_chapter_keys(),
        default='',
        required=False,
        help="Chapter"
    )

    parser.add_argument(
        "-smin",
        "--scene_min",
        type=int,
        default=-1,
        required=False,
        help="starting scene no. to process"
    )

    parser.add_argument(
        "-smax",
        "--scene_max",
        type=int,
        default=-1,
        required=False,
        help="last scene no. to process"
    )

    parser.add_argument(
        "--scene",
        "-s",
        type=int,
        default=-1,
        required=False,
        help="scene no. to process"
    )

    parser.add_argument(
        "--task",
        "-t",
        choices=TASK_NAMES,
        default='lr',
        required=False,
        help="task name"
    )

    parser.add_argument(
        "--watermark",
        "-w",
        action="store_true",
        required=False,
        help="Watermark each scene with scene no."
    )

    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        required=False,
        help="Overwrite"
    )

    parser.add_argument(
        "-sim",
        "--simulate",
        action="store_true",
        required=False,
        help="Do not generate files"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        required=False,
        help="debug"
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        required=False,
        help="verbose"
    )

    parser.add_argument(
        "--compare",
        "-c",
        action="store_true",
        required=False,
        help="UPSCALE only: append original scene no in the filename"
    )


    if add_language:
        parser.add_argument(
            "--lang",
            choices=['en', 'fr'],
            required=False,
            default='fr',
            help="Choose language"
        )


    return parser
