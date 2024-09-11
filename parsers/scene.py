from __future__ import annotations
from configparser import ConfigParser
from pprint import pprint
import re
import sys
from ._keys import all_chapter_keys, key
from utils.p_print import *
from utils.mco_types import Effect, Effects, ChapterVideo, Scene
from scene.src_scene import SrcScenes
from ._db import db
from ._keys import key



def parse_scenes(
    k_ed: str,
    k_ep: str,
    k_ch: str,
    scenes_str: str
) -> None:
    """This procedure parse a string wich contains the list of scenes
        and update the structure of the db.
        Used for 'episodes' and 'documentaire'
    """
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
            'curves': None,
            'replace': dict(),
        }
        scenes.append(new_scene)
        # print(scene_properties)
        # print(db_scenes[-1])

        # This scene may contains other customized properties
        if len(scene_properties) > 1:
            for p in scene_properties:
                d = p.split('=')
                if d[0] == 'filters':
                    # custom filter
                    scenes[scene_no]['filters_id'] = d[1]

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
                            'k_ep': key(int(src[0])),
                            'start': int(src[1]),
                            'count': int(src[2]),
                        })
                    elif len(src) == 2:
                        scenes[scene_no]['src'].update({
                            'k_ep': key(int(src[0])),
                            'start': int(src[1]),
# 2022-11-13: replacement does not work: to verify
                            'count': -1
                        })
                    else:
                        scenes[scene_no]['src'].update({
                            'k_ep': key(int(src[0])),
                            'start': start,
# 2022-11-13: replacement does not work: to verify
                            'count': -1
                        })

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



def parse_scenes_new(
    k_ed: str,
    k_ep: str,
    k_ch: str,
    config,
    k_section: str,
) -> None:
    scenes: list[Scene] = db[k_ep]['video'][k_ed][k_ch]['scenes']
    for k_option in config.options(k_section):
        value_str: str = config.get(k_section, k_option).replace(' ','')

        scene_no = int(k_option)
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
        })
        # print(scene_properties)
        # print(db_scenes[-1])

        # This scene may contains other customized properties
        if len(scene_properties) > 1:
            for p in scene_properties:
                d = p.split('=')
                # Custom filter
                if d[0] == 'filters':
                    scenes[scene_no]['filters_id'] = d[1]



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
    db_video_target: ChapterVideo,
    config: ConfigParser,
    k_section,
    language: str = 'fr'
) -> None:

    db_scenes: list[Scene] = db_video_target['scenes']

    for k_option in config.options(k_section):
        value_str: str = (
            config.get(k_section, k_option)
            .replace(' ','')
            .replace('\n','')
        )

        if k_option == 'max':
            db_video_target['scene_count'] = int(value_str) + 1
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

        scene_properties: list[str] = value_str.split(',')

        # Parse properties
        if len(scene_properties) > 0:

            # Append this scene to the list of scenes
            db_scenes.append({
                'no': scene_no,
                'src': SrcScenes(),
            })
            scene: Scene = db_scenes[-1]

            k_ed: str = db_video_target['k_ed_src']
            k_ep: str = db_video_target['k_ep']
            k_ch: str = db_video_target['k_ch']

            current_scene_no: int = -1
            segment_start: int = -1
            segment_count: int = -1
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
                    k_ep = key(int(v))

                elif k == 'chapter':
                    if v in all_chapter_keys():
                        k_ch = v
                    else:
                        sys.exit(f"parse_target_scenelist: {v} is not recognized")

                elif k == 'scene':
                   if current_scene_no != -1:
                       scene['src'].add_scene(
                           k_ed=k_ed,
                           k_ep=k_ep,
                           k_ch=k_ch,
                           no=current_scene_no,
                           start=segment_start,
                           count=segment_count,
                       )
                   current_scene_no = int(v)
                   segment_start = -1
                   segment_count = -1

                elif k == 'segment':
                    if (match := re.search(re.compile(r"(\d+):(\d+)"), v)):
                        segment_start = int(match.group(1))
                        segment_count = int(match.group(2))


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
                        name: str = match.group(1)
                        frame_ref: int = 0
                        # use fade for blend out
                        fade: int = int(match.group(2))
                        effects.append(
                            Effect(
                                name=name,
                                frame_ref=frame_ref,
                                fade=fade,
                            )
                        )
                    elif (
                        v.startswith('title')
                        and (match := re.search(re.compile(
                                r"([a-z_]+):(-?\d+):([\d+[.]*\d*):([\d+[.]*\d*)"
                            ), v))
                    ):
                        # blend with last image from previous scene
                        if effects is None:
                            effects = Effects()
                        name: str = match.group(1)
                        loop: int = int(match.group(2))
                        start_zoom_factor = float(match.group(3))
                        end_zoom_factor = float(match.group(4))
                        effects.append(
                            Effect(
                                name=name,
                                frame_ref=frame_ref,
                                loop=loop,
                                fade=fade,
                                zoom_factor=start_zoom_factor,
                                extra_param=end_zoom_factor,
                            )
                        )
                    else:
                        print("failed")
                    # if k_ch == 'g_debut':
                    #     pprint(effects)
                    #     # sys.exit()

            scene['src'].add_scene(
                k_ed=k_ed,
                k_ep=k_ep,
                k_ch=k_ch,
                no=current_scene_no if current_scene_no != -1 else scene_no,
                start=segment_start,
                count=segment_count,
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

    return None
