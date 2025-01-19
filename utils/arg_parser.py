from argparse import ArgumentParser
from parsers import (
    all_chapter_keys,
)

def common_argument_parser(
    description: str = '',
    add_language: bool = False,
) -> ArgumentParser:

    parser = ArgumentParser(description=description)
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

    if add_language:
        parser.add_argument(
            "--lang",
            choices=['en', 'fr'],
            required=False,
            default='fr',
            help="Choose language"
        )



    parser.add_argument(
        "--debug",
        action="store_true",
        required=False,
        help="debug"
    )



    parser.add_argument(
        "--compare",
        "-c",
        action="store_true",
        required=False,
        help="ignored except for upscale: append original scene no in the filename"
    )



    return parser
