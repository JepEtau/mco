from __future__ import annotations
from configparser import ConfigParser
from pprint import pprint
import re
import sys
from warnings import warn
from ._keys import all_chapter_keys, main_chapter_keys, ep_key, Chapter
from utils.p_print import *
from utils.mco_types import Effect, Effects, ChapterVideo, Scene
from scene.src_scene import SrcScene, SrcScenes
from ._db import db
from ._keys import ep_key



def scene_key(scene: Scene) -> str:
    if 'dst' in scene:
        k_ch: str = scene['dst']['k_ch']
        if k_ch in ('g_debut', 'g_fin'):
            return f"{k_ch}:{scene['no']:03}"
        return f"{scene['dst']['k_ep']}:{k_ch}:{scene['no']:03}"

    # This is a source scene
    return f"{scene['k_ed']}:{scene['k_ep']}:{scene['k_ch']}:{scene['no']:03}"


def parse_scenes(
    k_ed: str,
    k_ep: str,
    k_ch: str,
    scenes_str: str
) -> None:
    """This procedure parse a string wich contains the list of scenes
        and update the structure of the db.
        Used for 'episodes' and 'doc'
    """
    raise NotImplementedError(f"deprecated: {k_ed}:{k_ep}:{k_ch}")
    scenes: list[Scene] = db[k_ep]['video'][k_ed][k_ch]['scenes']
    for scene_no, scene in enumerate(scenes_str.split()):
        # print(scene)
        scene_properties = scene.split(',')

        # scene may specify start or start:end
        if ':' in scene_properties[0]:
            start_end = scene_properties[0].split(':')
            # first field is the start and end of the scene
            start = int(start_end[0])
            if len(start_end) > 1:
                end = int(start_end[1])
            else:
                end = start
            count = end - start
        else:
            start = int(scene_properties[0])
            count = 0

        # Append this scene to the list of scenes
        new_scene: Scene = {
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
        }
        scenes.append(new_scene)
        # print(scene_properties)
        # print(db_scenes[-1])

        # This scene may contains other customized properties
        scenes[scene_no]['src'] = SrcScene()
        src_scene: dict = scenes[scene_no]['src']
        if len(scene_properties) > 1:
            for p in scene_properties:
                d = p.split('=')
                if d[0] == 'filters':
                    # custom filter
                    scenes[scene_no]['filters_id'] = d[1]
                    raise ValueError(f"custom_filter: {scene_no}: {d}")

                elif d[0] == 'ed':
                    # edition that will be used to generate this scene
                    if 'src' not in scenes[scene_no].keys():
                        scenes[scene_no]['src'] = dict()
                    scenes[scene_no]['src'].update({'k_ed': d[1]})

                elif d[0] == 'ep' or d[0] == 'src':
                    # episode that will be used to generate this scene
                    if 'src' not in scenes[scene_no].keys():
                        scenes[scene_no]['src'] = dict()
                    src = d[1].split(':')
                    if len(src) == 3:
                        scenes[scene_no]['src'].update({
                            'k_ep': ep_key(int(src[0])),
                            'start': int(src[1]),
                            'count': int(src[2]),
                        })
                    elif len(src) == 2:
                        scenes[scene_no]['src'].update({
                            'k_ep': ep_key(int(src[0])),
                            'start': int(src[1]),
# 2022-11-13: replacement does not work: to verify
                            'count': -1
                        })
                    else:
                        scenes[scene_no]['src'].update({
                            'k_ep': ep_key(int(src[0])),
                            'start': start,
# 2022-11-13: replacement does not work: to verify
                            'count': -1
                        })

                elif d[0] == 'ch':
                    scenes[scene_no]['src'].update({'k_ch': d[1]})

                elif d[0] == 'replace':
                    raise ValueError(red("scene replace is deprecated"))

                elif d[0] == 'effects':
                    effect = d[1].split(',')
                    if len(effect) < 4:
                        effect.extend([0] * 3)
                    name, ref, loop, fade = effect[:3]
                    scenes[scene_no]['effects'] = Effects([
                        Effect(name=name, frame_ref=ref, loop=loop, fade=fade)
                    ])

    if k_ch == "asuivre":
        pprint(scenes)
        sys.exit()



def parse_scenes_new(
    k_ed: str,
    k_ep: str,
    k_ch: Chapter,
    config,
    k_section: str,
) -> None:
    scenes: list[Scene] = db[k_ep]['video'][k_ed][k_ch]['scenes']
    k_ed_ep_ch: str = f"{k_ed}:{k_ep}:{k_ch}"
    # print(f"Parse scene list: {k_ed_ep_ch}")

    for k_option in config.options(k_section):
        value_str: str = config.get(k_section, k_option).replace(' ','')

        # print(f"{k_section} -> {k_option}")
        scene_no = int(k_option)
        value_str = value_str.split("#")[0]
        scene_properties: list[str] = value_str.split(',')


        # scene may specify start or start:end
        if ':' in scene_properties[0]:
            start_end = scene_properties[0].split(':')
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
        scenes.append({
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
        # print(scene_properties)
        # print(db_scenes[-1])

        # This scene may contains other customized properties
        if len(scene_properties) > 1:
            for p in scene_properties:
                d = p.split('=')
                k: str = d[0]
                # Custom filter
                if k == 'filters':
                    scenes[scene_no]['filters_id'] = d[1]

                elif k == 'se_loop':
                    # Extend this scene by looping on 1st frame / last frame
                    start_end = d[1].split(':')
                    scenes[scene_no]['effects'] = Effects([
                        Effect(
                            name='se_loop',
                            extra_param=(
                                int(start_end[0]) if start_end[0] else 0,
                                int(start_end[1]) if start_end[1] else 0
                            )
                        )
                    ])


    # if k_ch == "asuivre" and k_ed not in ("s", "f", "k"):
    #     pprint(scenes)
    #     raise ValueError(red(f"{k_ed_ep_ch}"))



def consolidate_parsed_scenes(k_ed, k_ep, k_chapter) -> None:
    """This procedure is used to consolidate the parsed scenes
    It updates the total duration (in frames of the video for a chapter
    """
    db_video: ChapterVideo = db[k_ep]['video'][k_ed][k_chapter]

    # Create a single scene if no scene defined by the configuration file
    if 'scenes' not in db_video:
        if 'count' not in db_video or db_video['count'] == 0:
            return
        db_video['scenes'] = [
            Scene(
                no = 0,
                start = db_video['start'],
                filters_id = 'default',
                filters = None,
                count = db_video['count'],
                replace = dict(),
                dst = dict(
                    k_ep = k_ep,
                    k_chapter = k_chapter
                )
            )
        ]

        return

    # Update each scene durations
    scenes: list[Scene] = db_video['scenes']
    frames_count: int = 0
    for i, scene in enumerate(scenes):
        if scene is None:
            continue

        if scene['count'] == 0:
            if i + 1 >= len(scenes):
                # Last scene: use the count field of the chapter
                scene['count'] = db_video['start'] + db_video['count'] - scene['start']
            else:
                scene['count'] = scenes[i+1]['start'] - scene['start']

        if 'effects' in scene:
            effect: Effect = scene['effects'].primary_effect()
            if effect.name == 'loop':
                frames_count += effect.loop
                sys.exit("%s: add loop duration" % (__name__))

        if scene['count'] <= 0 and i < len(scenes) - 1:
            sys.exit(red(f"Error: {k_ed}:{k_ep}:{k_chapter}: scene no. {scene['no']:03d}, length (scene['count']) < 0"))

        frames_count += scene['count']



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
            .replace(' ','')
            .replace('\n','')
        )

        if k_option == 'count':
            ch_video['scene_count'] = int(value_str)
            continue

        lang = language
        try:
            scene_no = int(k_option)
        except:
            try:
                scene_no, lang = k_option.split('_')
                scene_no = int(scene_no)
                if lang != language:
                    continue
            except:
                sys.exit(f"erroneous option {k_option} in section [{k_section}]")

        value_str = value_str.split("#")[0]
        scene_properties: list[str] = value_str.split(',')

        k_ed: str = ch_video['default_src']['k_ed']

        # Parse properties
        if len(scene_properties) > 0:

            # Append this scene to the list of scenes
            append: bool = True
            for i, s in enumerate(db_scenes):
                if s['no'] == scene_no:
                    if k_section.endswith(language):
                        warn(yellow(f"{scene_no} is already defined, it will be replaced"))
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
            backward: bool = False
            effects: Effects | None = None
            for p in scene_properties:
                try:
                    k, v = p.split('=')
                except:
                    # print(f'Error: target, section {k_section}, scene no. {scene_no}, unvalid property: [{p}]')
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
                            backward=backward
                        )
                    segment_start = -1
                    segment_count = -1
                    current_scene_no = None
                    backward = False

                    if ed_ep_ch_scene := re.search(re.compile(r"([a-z]{1})?:*(\d{1,2}):([a-z_]+)?:*(\d+)?"), v):
                        if ed_ep_ch_scene.group(1) is not None:
                            k_ed = ed_ep_ch_scene.group(1)
                        k_ep = ep_key(int(ed_ep_ch_scene.group(2)))
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
                elif k in ('scene', 's'):
                    if current_scene_no is not None:
                       scene['src'].add_scene(
                           k_ed=k_ed,
                           k_ep=k_ep,
                           k_ch=k_ch,
                           no=current_scene_no,
                           start=segment_start,
                           count=segment_count,
                           backward=backward
                       )
                    current_scene_no = int(v)
                    segment_start = -1
                    segment_count = -1
                    backward = False

                elif k == 'backward':
                    if v.lower() == "true":
                        backward = True

                elif k in ('segment', 'sg'):
                    start_count = v.split(':')
                    if start_count[0] == '':
                        segment_start = -1
                    else:
                        segment_start = int(start_count[0])

                    if start_count[1] == '':
                        segment_count = -1
                    else:
                        segment_count = int(start_count[1])

                elif k == 'effect':
                    # print(f"effect: {v}")
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
                                frame_ref=frame_ref,
                                loop=loop,
                                fade=fade,
                                zoom_factor=zoom_factor
                            )
                        )
                    elif (
                        v.startswith('blend')
                        and (match := re.search(re.compile(r"([a-z_]+):(-?\d+)"), v))
                    ):
                        # blend with last image from previous scene
                        if effects is None:
                            effects = Effects()
                        frame_ref: int = 0
                        effects.append(
                            Effect(
                                name=match.group(1),
                                frame_ref=frame_ref,
                                # use fade for blend out
                                fade=int(match.group(2)),
                            )
                        )
                    elif (
                        v.startswith('title')
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
                                frame_ref=frame_ref,
                                loop=int(match.group(2)),
                                fade=0,
                                zoom_factor=start_zoom_factor,
                                extra_param=end_zoom_factor,
                            )
                        )

                    elif (
                        v.startswith('overlay')
                        and (match := re.search(re.compile(r"([a-z_]+):(\d+):([a-z_\d]+.png):(\d+):(\d+)"), v))
                    ):
                        # overlay=<x_position>:<filename>:<start_frame_no>:<frame_count>
                        if 'effects' not in scene or scene['effects'] is None:
                            scene['effects'] = Effects()
                        scene['effects'].append(
                            Effect(
                                name=match.group(1),
                                frame_ref=int(match.group(4)),
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
                k_ep=k_ep if k_ep != '' else ch_video['default_src']['k_ep'],
                k_ch=k_ch,
                no=current_scene_no if current_scene_no is not None else scene_no,
                start=segment_start,
                count=segment_count,
                backward=backward,
                effects=effects
            )


def get_scene_from_frame_no(
    frame_no: int,
    k_ed: str,
    k_ep: str,
    k_chapter: str
) -> Scene | None:
    # print("get_scene_from_frame_no: %d in %s:%s:%s" % (frame_no, k_ed, k_ep, k_chapter))
    scenes: list[Scene] = db[k_ep]['video'][k_ed][k_chapter]['scenes']
    for scene in scenes:
        if scene is None:
            continue
        # print("%d in [%d; %d] ?" % (frame_no, scene['start'], scene['start'] + scene['count']))
        if scene['start'] <= frame_no < (scene['start'] + scene['count']):
            return scene

    # print("\nWarning: %s:get_scene_from_frame_no: not found, frame no. %d in %s:%s:%s continue" % (__name__, frame_no, k_ed, k_ep, k_chapter))
    # pprint_video(db[k_ep]['video'][k_ed][k_chapter], ignore='')
    # print("-----------------------------------------------")
    # # pprint(db[k_ep_ref]['video'][k_ed][k_chapter]['scenes'])
    # sys.exit()

    raise ValueError
    return None
