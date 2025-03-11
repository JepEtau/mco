from __future__ import annotations
from configparser import ConfigParser
from copy import deepcopy
from pprint import pprint
import re
import sys
from typing import Literal
from warnings import warn
from utils.p_print import *
from utils.mco_types import ChapterVideo, Scene
from scene.src_scene import SrcScenes
from ._db import db
from ._keys import (
    ep_key, all_chapter_keys, main_chapter_keys, ep_key, Chapter
)
from .effects import Effect, Effects



def scene_key(scene: Scene) -> str:
    if 'dst' in scene:
        k_ch: str = scene['dst']['k_ch']
        if k_ch in ("g_debut', 'g_fin"):
            return f"{k_ch}:{scene['no']:03}"
        return f"{scene['dst']['k_ep']}:{k_ch}:{scene['no']:03}"

    # This is a source scene
    return f"{scene['k_ed']}:{scene['k_ep']}:{scene['k_ch']}:{scene['no']:03}"


ScenePropertyName = Literal[
    "se_loop",
    "filters", "f",
    "decimate", "d",
    "decimate2", "d2",
]


def parse_scenes(
    k_ed: str,
    k_ep: str,
    k_ch: Chapter,
    config: ConfigParser,
    k_section: str,
) -> None:
    """Parse original scenes
    """
    in_scenes: list[Scene] = db[k_ep]['video'][k_ed][k_ch]['scenes']

    for k_option in config.options(k_section):
        value_str: str = config.get(k_section, k_option).replace(" ", "")

        # print(f"{k_section} -> {k_option}")
        scene_no = int(k_option)
        value_str = value_str.split("#")[0]
        scene_properties: list[str] = value_str.split(",")


        # scene may specify start or start:end
        if ':' in scene_properties[0]:
            start_end = scene_properties[0].split(":")
            # first field is the start and end of the scene
            start = int(start_end[0])
            if len(start_end) > 1:
                end = int(start_end[1])
            else:
                end = start
            count = end - start
            if k_ch == 'doc':
                count += 1
        else:
            start = int(scene_properties[0])
            count = 0

        # Append this scene to the list of scenes
        in_scenes.append({
            'k_ed': k_ed,
            'k_ep': k_ep,
            'k_ch': k_ch,
            'no': scene_no,
            'start': start,
            'count': count,
            'filters': None,
            'filters_id': 'default',
            'replace': dict(),
            'dsr': None
        })

        # This scene may contains other customized properties
        if len(scene_properties) > 1:
            for p in scene_properties:
                d = p.split("=")
                name: ScenePropertyName = d[0]
                # Custom filter
                if name in ("filters", "f"):
                    in_scenes[scene_no]['filters_id'] = d[1]

                elif name == "se_loop":
                    # Extend this scene by looping on 1st frame / last frame
                    start_end = d[1].split(":")
                    in_scenes[scene_no]['effects'] = Effects([
                        Effect(
                            name='se_loop',
                            extra_param=(
                                int(start_end[0]) if start_end[0] else 0,
                                int(start_end[1]) if start_end[1] else 0
                            )
                        )
                    ])

                elif name in ("decimate", "d"):
                    # cannot mix decimate and se_loop
                    in_scenes[scene_no]['effects'] = Effects([
                        Effect(
                            name='decimate',
                            extra_param=[int(d[1]) if len(d) > 1 else 5, 0]
                        )
                    ])

                elif name in ("decimate2", "d2"):
                    # cannot mix decimate and se_loop
                    in_scenes[scene_no]['effects'] = Effects([
                        Effect(
                            name='decimate_2',
                            extra_param=[int(d[1]) if len(d) > 1 else 5, 2]
                        )
                    ])



def consolidate_in_scenes(k_ed: str, k_ep: str, k_ch: Chapter) -> None:
    """This procedure is used to consolidate the parsed scenes
    It updates the total duration (in frames of the video for a chapter
    """
    in_ch_video: ChapterVideo = db[k_ep]['video'][k_ed][k_ch]

    # Create a single scene if no scene defined by the configuration file
    if 'scenes' not in in_ch_video:
        if 'count' not in in_ch_video or in_ch_video['count'] == 0:
            return
        in_ch_video['scenes'] = [
            Scene(
                no=0,
                start=in_ch_video['start'],
                filters_id='default',
                filters=None,
                count=in_ch_video['count'],
                replace={},
                dst={'k_ep': k_ep, 'k_ch': k_ch}
            )
        ]
        return

    # Update each scene durations
    scenes: list[Scene] = in_ch_video['scenes']
    ch_frame_count: int = 0
    for i, scene in enumerate(scenes):
        if scene is None:
            continue

        if scene['count'] == 0:
            if i + 1 >= len(scenes):
                # Last scene: use the count field of the chapter
                scene['count'] = in_ch_video['start'] + in_ch_video['count'] - scene['start']
            else:
                scene['count'] = scenes[i+1]['start'] - scene['start']

        if 'effects' in scene:
            effects: Effects = scene['effects']
            if e := effects.get_effect("loop"):
                ch_frame_count += e.loop
                sys.exit("%s: add loop duration" % (__name__))

            if e := effects.get_effect("decimate"):
                # raise ValueError("decimate")
                print(f"decimate: {k_ed}:{k_ep}:{k_ch}:{scene['no']}")
                # factor: int = e.extra_param[0]
                e.extra_param[1] = scene['count']
                # scene['count'] = int(scene['count'] * (factor - 1 ) / factor + 0.5)
                # pprint(scene)
                # raise

            elif e := effects.get_effect("decimate_2"):
                raise ValueError("decimate2")
            #     factor: int = e.extra_param[0]
            #     # e.extra_param[1] = scene['count']
            #     scene['count'] =  int((scene['count'] * (factor - 1 ) / factor + 0.5) / e.extra_param[1])

        if scene['count'] <= 0 and i < len(scenes) - 1:
            raise ValueError(red(f"Error: {k_ed}:{k_ep}:{k_ch}: scene no. {scene['no']:03d}, length (scene['count']) < 0"))

        ch_frame_count += scene['count']

    in_ch_video['count'] = ch_frame_count



def parse_target_scenelist(
    ch_video: ChapterVideo,
    config: ConfigParser,
    k_section: str,
    k_ep: str,
    k_ch: str,
    language: str = 'fr'
) -> None:
    # This is valable for all EXCEPT doc which uses the declared src scene

    db_scenes: list[Scene] = ch_video['scenes']

    for k_option in config.options(k_section):
        value_str: str = (
            config.get(k_section, k_option)
            .replace(" ","")
            .replace("\n","")
        )

        if k_option == 'count':
            ch_video['scene_count'] = int(value_str)
            continue

        lang = language
        try:
            scene_no = int(k_option)
        except:
            try:
                scene_no, lang = k_option.split("_")
                scene_no = int(scene_no)
                if lang != language:
                    continue
            except:
                sys.exit(f"erroneous option {k_option} in section [{k_section}]")

        value_str = value_str.split("#")[0]
        scene_properties: list[str] = value_str.split(",")

        k_ed: str = ch_video['default_src']['k_ed']

        # Parse properties
        if len(scene_properties) > 0:

            # Append this scene to the list of scenes
            append: bool = True
            for i, s in enumerate(db_scenes):
                if s['no'] == scene_no:
                    if k_section.endswith(language):
                        warn(yellow(f"{scene_no} is already defined, it will be replaced"))
                        if 'overwritten_scenes' not in ch_video:
                            ch_video['overwritten_scenes'] = {}
                        ch_video['overwritten_scenes'][scene_no] = deepcopy(db_scenes[i])
                        del db_scenes[i]
                    else:
                        append = False
                    break
            if not append:
                continue

            db_scenes.append({
                'no': scene_no,
                'src': SrcScenes(),
            })
            scene: Scene = db_scenes[-1]

            current_scene_no: int | None = None
            segment_start: int = -1
            segment_count: int = -1
            effects: Effects | None = None
            _k_ep: str = k_ep
            for p in scene_properties:
                try:
                    k, v = p.split("=")
                except:
                    # print(f'Error: target, section {k_section}, scene no. {scene_no}, unvalid property: [{p}]")
                    # sys.exit()
                    continue

                if k == 'ed':
                    k_ed = v

                elif k == 'ep':
                    k_ep = ep_key(int(v))

                elif k == 'ch':
                    if v in all_chapter_keys():
                        k_ch = v
                    else:
                        sys.exit(f"parse_target_scenelist: {v} is not recognized")

                elif k == 'src':
                    if current_scene_no is not None:
                        scene['src'].add_scene(
                            k_ed=k_ed,
                            k_ep=k_ep,
                            k_ch=k_ch,
                            no=current_scene_no,
                            start=segment_start,
                            count=segment_count,
                        )
                    segment_start = -1
                    segment_count = -1
                    current_scene_no = None

                    if ed_ep_ch_scene := re.search(re.compile(r"([a-z]{1})?:*(\d{1,2}):([a-z_]+)?:*(\d+)?"), v):
                        if ed_ep_ch_scene.group(1) is not None:
                            k_ed = ed_ep_ch_scene.group(1)
                        _k_ep = ep_key(int(ed_ep_ch_scene.group(2)))
                        k_ch = ed_ep_ch_scene.group(3)
                        if k_ch not in main_chapter_keys():
                            raise ValueError(f"not valid chapter: {k_ch}")

                        if ed_ep_ch_scene.group(4) is not None:
                            scene_no = int(ed_ep_ch_scene.group(4))
                            current_scene_no = scene_no
                        else:
                            # Find scene no from frame no
                            current_scene_no = -1
                    else:
                        raise ValueError(v)

                # Src scene
                elif k in ("scene', 's"):
                    if current_scene_no is not None:
                       scene['src'].add_scene(
                           k_ed=k_ed,
                           k_ep=_k_ep,
                           k_ch=k_ch,
                           no=current_scene_no,
                           start=segment_start,
                           count=segment_count,
                       )
                    current_scene_no = int(v)
                    segment_start = -1
                    segment_count = -1

                elif k in ("segment", "sg"):
                    start_count = v.split(":")
                    if start_count[0] == '':
                        segment_start = -1
                    else:
                        segment_start = int(start_count[0])

                    if start_count[1] == '':
                        segment_count = -1
                    else:
                        segment_count = int(start_count[1])

                elif k == 'effect':
                    print(f"effect: {v}")
                    # name, frame_ref, count, param
                    if (match := re.search(re.compile(
                        r"([a-z_]+):(-?\d+):(\d+):([\d+[.]*\d*)"
                    ), v)):
                        if effects is None:
                            effects = Effects()
                        name: str = match.group(1)
                        frame_ref: int = int(match.group(2))
                        loop: int = 0
                        fade: int = 0
                        zoom_factor: int = 0
                        if 'loop' in name or 'zoom' in name:
                            loop = int(match.group(3))
                        if 'fade' in name:
                            fade = int(match.group(4))
                        if 'zoom' in name:
                            zoom_factor = float(match.group(4))

                        effects.append(
                            Effect(
                                name=name,
                                f_ref=frame_ref,
                                loop=loop,
                                fade=fade,
                                zoom_factor=zoom_factor
                            )
                        )
                        pprint(effects)
                    elif (
                        v.startswith("blend")
                        and (match := re.search(re.compile(r"([a-z_]+):(-?\d+)"), v))
                    ):
                        # blend with last image from previous scene
                        if effects is None:
                            effects = Effects()
                        frame_ref: int = 0
                        effects.append(
                            Effect(
                                name=match.group(1),
                                f_ref=frame_ref,
                                # use fade for blend out
                                fade=int(match.group(2)),
                            )
                        )
                    elif (
                        v.startswith("title")
                        and (match := re.search(re.compile(
                                r"([a-z_.]+):(-?\d+):([\d+[.]*\d*):([\d+[.]*\d*)"
                            ), v))
                    ):
                        # title=<frame_count>:<zoom_start>:<zoom_end>
                        if effects is None:
                            effects = Effects()
                        start_zoom_factor = float(match.group(3))
                        end_zoom_factor = float(match.group(4))
                        effects.append(
                            Effect(
                                name=match.group(1),
                                f_ref=frame_ref,
                                loop=int(match.group(2)),
                                fade=0,
                                zoom_factor=start_zoom_factor,
                                extra_param=end_zoom_factor,
                            )
                        )

                    elif (
                        v.startswith("overlay")
                        and (match := re.search(re.compile(r"([a-z_]+):(\d+):([a-z_\d]+.png):(\d+):(\d+)"), v))
                    ):
                        # overlay=<x_position>:<filename>:<start_frame_no>:<frame_count>
                        if 'effects' not in scene or scene['effects'] is None:
                            scene['effects'] = Effects()
                        scene['effects'].append(
                            Effect(
                                name=match.group(1),
                                f_ref=int(match.group(4)),
                                loop=int(match.group(5)),
                                extra_param=(int(match.group(2)), match.group(3)),
                            )
                        )

                    else:
                        print("failed")
                    # if k_ch == 'g_debut':
                    #     pprint(effects)
                    #     # sys.exit()

            scene['src'].add_scene(
                k_ed=k_ed if k_ed != '' else ch_video['default_src']['k_ed'],
                k_ep=_k_ep if _k_ep != '' else ch_video['default_src']['k_ep'],
                k_ch=k_ch,
                no=current_scene_no if current_scene_no is not None else scene_no,
                start=segment_start,
                count=segment_count,
                effects=effects
            )
            if k_ep == 'ep03' and k_ch =='episode' and scene['no'] == 189:
                pprint(scene)
                # raise


def get_scene_from_frame_no(
    frame_no: int,
    k_ed: str,
    k_ep: str,
    k_ch: str
) -> Scene | None:
    if 'scenes'not in db[k_ep]['video'][k_ed][k_ch]:
        return None

    scenes: list[Scene] = db[k_ep]['video'][k_ed][k_ch]['scenes']
    for scene in scenes:
        if scene is None:
            continue
        # print("%d in [%d; %d] ?" % (frame_no, scene['start'], scene['start'] + scene['count']))
        if scene['start'] <= frame_no < (scene['start'] + scene['count']):
            return scene

    # raise ValueError
    return None
