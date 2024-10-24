from __future__ import annotations
from copy import deepcopy
from pprint import pprint
import sys
from utils.p_print import *
from parsers import (
    db,
    scene_key,
)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from utils.mco_types import Scene, ChapterVideo
    from parsers import (
        Filter,
        VideoSettings,
    )

def get_ffmpeg_pad_color_filter(scene: Scene) -> str:
    vsettings: VideoSettings = scene['task'].video_settings
    color_params: str = "setparams=colorspace=bt709:color_primaries=bt709:color_trc=bt709"
    # color_conv: str = "scale=in_color_matrix=bt601:out_color_matrix=bt709:flags=full_chroma_int+accurate_rnd"

    if vsettings.pad != 0:
        pad: int = vsettings.pad
        pad_filter: str = f"pad=w=iw+{2*pad}:h={2*pad}+ih:x={pad}:y={pad}:color=black"
        return f"{pad_filter}"

    else:
        return ""


def do_watermark(scene: Scene) -> bool:
    return bool('watermark' in scene['filters'][scene['task'].name].sequence)



def get_filters(scene: Scene) -> list[Filter]:
    debug: bool = False
    s_key: str = scene_key(scene)
    k_ed, k_ep, k_ch = scene['k_ed'], scene['k_ep'], scene['k_ch']
    chapter_video: ChapterVideo = db[k_ep]['video'][k_ed][k_ch]

    if debug:
        print(lightgreen(f"get filters from scene: {s_key}, start: {scene['start']}"))
        pprint(scene)

    if scene['filters_id'] == 'default':
        if debug:
            print(lightgrey(f"\tdefault filter"))
            # pprint(chapter_video['filters'])

        # This scene uses default filters. Use the one defined in the part
        if (
            'filters' not in chapter_video
            and scene['task'].name != 'initial'
        ):
            sys.exit(print(red(f"Error: {s_key}: no available filters")))

        try:
            filters = chapter_video['filters']['default']
        except:
            if scene['task'].name == 'initial':
                return {}
            else:
                print(red(f"Error: default filter is not defined but required by {s_key}"))
                pprint(scene)
                sys.exit()

    elif isinstance(scene['filters_id'], str):
        if debug:
            print(yellow(f"custom filter: {scene['filters']}"))

        filters = deepcopy(chapter_video['filters']['default'])

        # This scene uses a custom filter defined in the 'filters' struct in this part
        try:
            filters.update(chapter_video['filters'][scene['filters_id']])
        except:
            print(red(f"\tdefined filters: {list(chapter_video['filters'].keys())}"))
            print(orange(f"\tfallback: using default"))
            raise ValueError(red(f"Error: {s_key}, filter {scene['filters']} not found"))
            filters = chapter_video['filters']['default']
    else:
        # This scene may default filters, but to be validated
        print(red(f"Error: no filters defined for {s_key}"))
        sys.exit()

    if debug:
        pprint(filters)
        raise NotImplementedError(f"it was filters for scene: {':'.join((k_ed, k_ep, k_ch))}")
    return filters

