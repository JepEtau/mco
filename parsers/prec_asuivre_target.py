from __future__ import annotations
from configparser import ConfigParser
import os
from pprint import pprint
import re
import sys
from utils.p_print import red
from utils.path_utils import absolute_path
from ._db import db
from ._keys import Chapter, all_chapter_keys, ep_key, main_chapter_keys
from scene.src_scene import SrcScenes, SrcScene, Scene


def get_dst_scene_nos(
    k_ep_dst: str,
    k_ch_dst: Chapter,
    k_ep: str,
    k_ch: Chapter,
    verbose: bool = False
) -> list[int]:
    scene_list: list[str] = []

    if verbose:
        print(f"destination: {k_ep_dst}:{k_ch_dst}")
        print(f"source: {k_ep}:{k_ch}")

    src_ed_ep_ch_nos: list[int] = []
    # Parse asuivre/precedemment traget section
    #   get the src ed/ep/ch/scene_no for each scene
    db_scenes: list[Scene] = parse_target_chapter(k_ep=k_ep_dst, k_ch=k_ch_dst)
    for scene in db_scenes:
        for src_scene in scene['src'].scenes():
            src_ed_ep_ch_nos.append(src_scene['k_ed_ep_ch_no'])
    if verbose:
        print(f"  source scene list for {k_ep_dst}:{k_ch_dst}:")
        pprint(src_ed_ep_ch_nos)

    # For each source scene, search the destination scene
    for src_ed_ep_ch_no in src_ed_ep_ch_nos:
        if src_ed_ep_ch_no[1] != src_ed_ep_ch_nos[0][1]:
            raise ValueError(f"episode no is different for scene no.{src_ed_ep_ch_no[3]}")

        scene: Scene
        for scene in db[k_ep]['video']['target'][k_ch]['scenes']:
            if scene['src'].primary_scene().k_ed_ep_ch_no == src_ed_ep_ch_no:
                scene_list.append(scene['no'])
                break

    return scene_list



def get_ed_to_src_scene(
    k_ep: str,
    k_ch: Chapter,
) -> dict:
    db_target_scenes: list[Scene] = parse_target_chapter(k_ep=k_ep, k_ch=k_ch)
    ed_to_target_map: dict = {}

    # Use primary scene_no
    for scene in db_target_scenes:
        in_scene: Scene = scene['src'].primary_scene().in_scene
        in_scene_no = in_scene['no']
        in_ed = in_scene['k_ed']
        if in_ed not in ed_to_target_map:
            ed_to_target_map[in_ed] = {}
        ed_to_target_map[in_ed][in_scene_no] = scene['no']

    pprint(ed_to_target_map)

    return ed_to_target_map



def parse_target_chapter(k_ep: str, k_ch: Chapter) -> list[SrcScene]:
    # Open configuration file
    filepath: str = absolute_path(
        os.path.join(
            db['common']['directories']['config'],
            k_ep,
            f"{k_ep}.ini"
        )
    )

    config = ConfigParser()
    config.read(filepath)

    db_scenes: list[Scene] = []

    k_section = f"scenes_{k_ch}"
    for k_option in config.options(k_section):
        value_str: str = (
            config.get(k_section, k_option)
            .replace(' ','')
            .replace('\n','')
        )

        try:
            scene_no = int(k_option)
        except:
            try:
                scene_no, _ = k_option.split('_')
                scene_no = int(scene_no)
            except:
                sys.exit(f"erroneous option {k_option} in section [{k_section}]")


        value_str = value_str.split("#")[0]
        scene_properties: list[str] = value_str.split(',')

        # Parse properties
        if len(scene_properties) > 0:
            db_scenes.append({
                'no': scene_no,
                'src': SrcScenes(),
            })
            scene: Scene = db_scenes[-1]
            current_scene_no: int | None = None
            segment_start: int = -1
            segment_count: int = -1

            _k_ep: str = k_ep
            k_ed: str = 'j'
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
                elif k in ('scene', 's'):
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

            scene['src'].add_scene(
                k_ed=k_ed,
                k_ep=_k_ep,
                k_ch=k_ch,
                no=current_scene_no if current_scene_no is not None else scene_no,
                start=segment_start,
                count=segment_count,
            )

            # todo: use the one defined in video section
            k_ed = 'j'

    return db_scenes
