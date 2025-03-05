import gc
import logging
from pprint import pprint
import signal
import sys
from parsers import (
    TASK_NAMES,
    parse_database,
    logger,
    db,
    Chapter,
    all_chapter_keys,
    ep_key,
    ProcessingTask,
    TaskName,
    pprint_scene_mapping,
    get_frame_rate,
)
from parsers._helpers import get_chapter_audio
from scene.consolidate import consolidate_scene
from scene.src_scene import SrcScenes
from utils.arg_parser import common_argument_parser
from utils.mco_types import (
    ChapterAudio,
    Scene,
    ChapterVideo,
)
from utils.p_print import *
from video.consolidate_scenes import get_chapter_video


def main():
    # Arguments
    parser = common_argument_parser(
        description="Parse the database",
        add_language=True,
    )

    parser.add_argument(
        "--stats",
        choices=['scene'],
        default='',
        required=False,
        help="debug"
    )

    parser.add_argument(
        "--task",
        "-t",
        choices=TASK_NAMES,
        default='lr',
        required=False,
        help="task name"
    )

    arguments = parser.parse_args()

    if arguments.debug:
        logger.addHandler(logging.StreamHandler(sys.stdout))
        logger.setLevel("DEBUG")

    episode: int = arguments.episode
    chapter: str = arguments.chapter
    if episode == 0 and chapter == '':
        sys.exit("Error: at least an episode or a chapter shall be specified")

    if episode < 0 or episode > 39:
        sys.exit(red("Episode must be between 1 and 39"))

    if chapter in ('g_debut', 'g_fin'):
        episode = 0
    if episode != 0:
        print(f"Episode: {episode}")
    if chapter != '':
        print("Chapter: %s" % (chapter))
    print(f"Language: {arguments.lang}")
    print("Tasks:")
    print("\t- parse database")

    # Parse database
    dependencies = parse_database(episode=episode, lang=arguments.lang)
    gc.collect()

    print(lightcyan("dependencies:"))
    pprint(dependencies)
    # For inspection
    # db_ep: dict = g_database['ep01']
    # print(db_ep.keys())
    # print(db_ep['cache_path'])
    # pprint(db_ep['audio'])

    # print(db.keys())
    # pprint(db['common'])
    k_ep = ep_key(episode)
    task_name: TaskName = arguments.task


    chapters: list[Chapter] = all_chapter_keys() if arguments.chapter == '' else [arguments.chapter]
    for k_ch in chapters:
        print(lightcyan(f"episode: {k_ep}, chapter: {k_ch}"))
        ch_video: ChapterVideo = get_chapter_video(k_ep, k_ch)
        ch_audio: ChapterAudio = get_chapter_audio(k_ep, k_ch)
        if ch_audio is None:
            continue
        if ch_video is None:
            continue
        ch_video['task'] = ProcessingTask(name=task_name)

        # Walk through target scenes
        scenes: list[Scene] = ch_video['scenes']
        target_count = 0
        ref_count: int = 0
        for scene in scenes:
            pprint_scene_mapping(scene)

            if 'ref' in scene:
                ref_count += scene['ref']['count']
            target_count += scene['dst']['count']

        if 'ref' not in scene:
            ref_count = 0
            k_ep_or_g = 'ep01' if k_ch in ('g_debut', 'g_fin') else k_ep
            _k_ed = (
                'k'
                if db[k_ep_or_g]['audio']['lang'] == 'fr'
                else 'f'
            )
            print(f"  reference: {_k_ed}:{k_ep}:{k_ch} ({k_ep_or_g})")
            if _k_ed in db[k_ep_or_g]['video']:
                for s in db[k_ep_or_g]['video'][_k_ed][k_ch]['scenes']:
                    ref_count += s['count']
            else:
                print("Ignore reference as it has not been parsed")

        if 'effects' in scenes[0]:
            print(lightcyan("first scene effect:"))
            pprint(scenes[0]['effects'])

        if ch_audio['avsync']:
            print(lightcyan("first scene AVsync:"), ch_audio['avsync'])

        if 'effects' in scenes[-1]:
            print(lightcyan("last scene effect:"))
            pprint(scenes[-1]['effects'])

        if k_ch in ('g_debut', 'g_fin'):
            if ch_video['silence']:
                target_count += ch_video['silence']
        if ch_video['silence']:
            print(lightcyan("video silence:"), ch_video['silence'])

        print(f"  Reference: {ref_count}")
        print(f"  Audio: {ch_audio['count']}")
        print(f"  Target: {target_count}")

        # pprint(ch_video)
        scene_no: int = arguments.scene
        if scene_no != -1:
            print(lightcyan(f"Scene no. {scene_no}"), f"count={scene['dst']['count']}")
            ch_video: ChapterVideo | None = get_chapter_video(k_ep, k_ch)
            if ch_video is None:
                continue

            consolidate_scene(scenes[scene_no], task_name=task_name)

            pprint(ch_video.keys())
            pprint(scenes[scene_no])


        if False:
            if k_ch == 'episode':
                for scene in scenes:
                    src_scenes: SrcScenes = scene['src'].scenes()
                    if len(src_scenes) > 1:
                        print(f"{scene['no']:03} -> ", end= "")
                        for s in src_scenes:
                            _k_ed, _k_ep, _k_ch, _no = s['k_ed_ep_ch_no']
                            print(f"{_no}, ", end ="")

                        print()
                    else:
                        s = src_scenes[0]
                        _k_ed, _k_ep, _k_ch, _no = s['k_ed_ep_ch_no']
                        if _k_ed == 'j':
                            print(f"{scene['no']:03} -> {_k_ed}:{_no: 3}")
                        else:
                            print(f"{scene['no']:03} -> {_k_ed}")


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
