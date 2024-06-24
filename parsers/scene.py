from configparser import ConfigParser
import re
import sys
from ._keys import all_chapter_keys, key
from utils.p_print import *
from utils.mco_types import Effect, Effects, Scene, SceneSrc, VideoChapter
from ._db import db
from ._keys import key



def parse_scenes(
    scenes: list[Scene],
    scenes_str: str
) -> None:
    """This procedure parse a string wich contains the list of scenes
        and update the structure of the db.
        Used for 'episodes' and 'documentaire'
    """
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
                    # Replace this scene by the source
                    if 'src' not in scenes[scene_no].keys():
                        scenes[scene_no]['src'] = dict()
                    scenes[scene_no]['src'].update({'use': True if d[1]=='y' else False})

                elif d[0] == 'effects':
                    effect = d[1].split(',')
                    if len(effect) < 4:
                        effect.extend([0] * 3)
                    name, ref, loop, fade = effect[:3]
                    scenes[scene_no]['effects'] = Effects([
                        Effect(name=name, frame_ref=ref, loop=loop, fade=fade)
                    ])



def parse_scenes_new(
    scenes: list[Scene],
    config,
    k_section: str,
) -> None:
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
    db_video: VideoChapter = db[k_ep]['video'][k_ed][k_chapter]

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
    db_scenes: list[dict],
    config: ConfigParser,
    k_section,
    language: str = 'fr'
) -> None:

    for k_option in config.options(k_section):
        value_str: str = config.get(k_section, k_option).replace(' ','')

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
                'src': SceneSrc(),
            })
            scene: Scene = db_scenes[-1]

            for p in scene_properties:
                try:
                    k, v = p.split('=')
                except:
                    # print(f'Error: target, section {k_section}, scene no. {scene_no}, unvalid property: [{p}]')
                    # sys.exit()
                    continue

                scene_src: SceneSrc = scene['src']
                if k == 'ed':
                    scene_src['k_ed'] = v

                elif k == 'ep':
                    scene_src['k_ep'] = key(int(v))

                elif k == 'chapter':
                    if v in all_chapter_keys():
                        scene_src['k_ch'] = v
                    else:
                        sys.exit(f"parse_target_scenelist: {v} is not recognized")

                elif k == 'scene':
                   scene_src['no'] = int(v)

                elif k == 'segments':
                    scene_src['segments'] = []
                    segments = v.replace(' ', '').split('\n')
                    for s in segments:
                        if (match := re.search(re.compile(r"(\d+):(\d+)"), s)):
                            scene_src['segments'].append({
                                'start': int(match.group(1)),
                                'count': int(match.group(2)),
                            })

                elif k in ['start', 'count']:
                    scene_src[k] = int(v)


            # # Debug
            # if k_section == 'scenes_episode.fr' and scene_no == 307:
            #     print(k_section)
            #     # pprint(scene_properties)
            #     pprint(scene)
            #     # sys.exit()


def get_scene_from_frame_no(
    db, frame_no: int, k_ed: str, k_ep: str, k_chapter: str
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
