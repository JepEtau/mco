from __future__ import annotations
from configparser import ConfigParser
from dataclasses import dataclass, field
import os
from pprint import pprint
from utils.p_print import *
from utils.path_utils import absolute_path
from ._db import (
    db,
    database_path,
)
from ._types import TASK_NAMES



@dataclass
class ColorSettings:
    colorspace: str = 'bt709'
    color_primaries: str = 'bt709'
    color_trc: str = 'bt709'
    color_range: str = 'limited'



@dataclass
class VideoSettings:
    codec: str
    codec_options: list[str]
    pix_fmt: str
    pad: int = 0
    frame_rate: int = 0
    size: tuple[int, int] | None = None
    metadata: dict[str, str] = field(default_factory=dict)




def parse_video_settings(verbose: bool = False) -> None:
    if verbose:
        print(darkgrey("[I] parse_video_settings"))

    # Get configuration file's directories
    vsettings_fp = absolute_path(
        os.path.join(database_path, "video_settings.ini")
    )

    # Video settings
    db['vsettings'] = {}
    dbvs: dict = db['vsettings']

    # Parse the file
    config = ConfigParser()
    config.read(vsettings_fp)

    # common
    k_section: str = 'common'
    dbvs[k_section] = {}
    for option in config.options(k_section):
        v = config.get(k_section, option)
        try:
            dbvs[k_section][option] = int(v)
        except:
            dbvs[k_section][option] = v

    # For each task...
    for task in TASK_NAMES:
        if task not in config.sections():
            continue

        vsettings = config[task]

        # output video size
        size = vsettings.get('size', None)
        if size is not None:
            size = tuple(map(int, size.split("x")))

        # codec options
        options: str = (
            vsettings
            .get('codec_options', '')
            .replace('\"', '')
            .replace('\n', ' ')
            .replace('  ', ' ')
            .strip()
        )

        # add to the database
        dbvs[task] = VideoSettings(
            size=size,
            frame_rate=dbvs['common']['frame_rate'],
            codec=vsettings.get('codec', ''),
            codec_options=options.split(' ') if options else [],
            pix_fmt=vsettings.get('pix_fmt', ''),
            pad=int(vsettings.get('pad', '0')),
        )

    if verbose:
        pprint(db['vsettings'])
