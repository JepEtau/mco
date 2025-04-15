from dataclasses import dataclass
import os
from pprint import pprint
import random
import re
import signal
import sys
from argparse import ArgumentParser
import logging
from pprint import pprint
import signal
import sys
import time

from utils.mco_utils import calculate_scene_frame_count, scene_id_str
DVR_PLUGIN_LOADED = False
from pydvr import (
    DVR,
    DVRItem,
    DVRProject,
    DVRTimeline,
    Render,
    app_already_started,
    Pages,
)

try:
    from pydvr import (
        DVR,
        DVRItem,
        DVRProject,
        DVRTimeline,
        Render,
        app_already_started,
        Pages,
    )
    DVR_PLUGIN_LOADED = True
except:
    pass

from parsers import (
    Chapter,
    ep_key,
    parse_database,
    get_chapter_video,
    ProcessingTask,
    pprint_scene_mapping,
)
from utils.media import (
    extract_media_info_mco,
    VideoCodec,
    str_to_video_codec,
    VideoInfo,
)
from scene.consolidate import consolidate_scene
from utils.mco_types import Scene, ChapterVideo
from utils.arg_parser import common_argument_parser
from utils.logger import main_logger
from utils.p_print import *
from video.consolidate_scenes import consolidate_scenes


dvr = None

def main():
    # Arguments
    parser: ArgumentParser = common_argument_parser(
        description="Generate episode (final)",
        add_language=True,
    )

    parser.add_argument(
        "--project",
        "-p",
        type=str,
        default="ep01_python",
        required=False,
        help="project name"
    )

    arguments = parser.parse_args()

    if arguments.debug:
        main_logger.addHandler(logging.StreamHandler(sys.stdout))
        main_logger.setLevel("DEBUG")

    k_ep: str = ep_key(arguments.episode)
    k_ch: Chapter = 'episode'
    debug: bool = arguments.debug
    scene_no: int = arguments.scene


    project_name = "ep01_episode"
    db_name = "mco"

    if DVR_PLUGIN_LOADED:
        global dvr
        dvr = DVR()
        print(lightcyan(f"DaVinci Resolve version:"), dvr.version())
        # Load project
        if dvr.current_database_name() != db_name:
            dvr.set_current_database(name=db_name)
        print(lightcyan(f"Database:"), dvr.current_database_name())
        project: DVRProject = None
        if dvr.current_project_name() != project_name:
            project = dvr.load_project(project_name)
        else:
            project = dvr.current_project()
        print(lightcyan(f"Project loaded:"), project.name)

        pprint(project.get_settings())

        timeline: DVRTimeline = project.get_timeline()
        print(lightcyan(f"Timeline:"), timeline.name)
        timeline.set_as_current()
        pprint(timeline.get_settings())

        dvr.select_page(name="edit")
        if False:
            print(lightcyan(f"Input media clips:"))
            item: DVRItem
            count = timeline.video_item_count()
            random.seed(time.time())
            for no in range(1, 5):
                dvr_index = random.randint(1, count)
                item: DVRItem = timeline.select_item(dvr_index)
                pprint(item.get_properties())
                item.cropping.crop = (0, 0, 0, 0)
                print(f"item no. {dvr_index}:\n  {item.media_clip.filename}, start frame {item.start_frame}\n")

        in_filepaths: list[str] = list(
            [item.media_clip.filepath for item in timeline.video_track_items()]
        )
        print(len(in_filepaths))
        scene_nos: list[int] = []
        for f in sorted(in_filepaths):
            result = re.search(re.compile(r"ep01_episode_(\d{3})__.*"), f)
            no = int(result.group(1))
            if no in scene_nos:
                print(red(f"scene no. {no} already in list of scenes"))
            else:
                scene_nos.append(no)


        if False:
            print("---------------------------------")
            dvr.select_page("deliver")
            print(project.render.get_render_mode())
            print("---------------------------------")
            pprint(project.render.get_render_jobs())
            print("---------------------------------")
            pprint(project.render.get_presets())
            print("---------------------------------")
            pprint(project.dvr_project.GetRenderFormats())
            # pprint(project.dvr_project.GetRenderFormats())

            # %{Source Name}_cg


        print("done")
        if not app_already_started():
            print(yellow("TODO: close it"))
            dvr.quit()
    else:
        raise ValueError(red("Cannot use DaVinci Resolve API"))


    # Parse databse and consolidate
    parse_database(episode=k_ep)
    task = 'cg'

    ch_video: ChapterVideo | None = get_chapter_video(k_ep, k_ch)
    if ch_video is None:
        raise ValueError(red(f"failed to load {k_ch}"))

    ch_video['task'] = ProcessingTask(name=task)
    if debug:
        print(f"\n<<<<<<<<<<<<<<<<<<<<< {k_ch} >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

    # Scenes to process: dict[in_fp: out_fp]
    video_to_update_fp: dict[str, str] = {}

    # Walk through target scenes
    scenes: list[Scene] = ch_video['scenes']

    if timeline.video_item_count() != len(scenes):
        raise ValueError(red(f"missing scenes timeline: {timeline.video_item_count()}, must be {len(scenes)}"))

    for scene in scenes:
        if scene_no != -1 and scene['no'] != scene_no:
            continue
        pprint_scene_mapping(scene)
        consolidate_scene(scene, task_name=task)
        scene_id: str = scene_id_str(scene)

        if debug:
            print(lightcyan(f"======================= generate_{task}_scenes: {scene_id} ============================="))
            pprint(scene)
            print(lightcyan("==============================================================================="))

        in_video_fp: str = scene['task'].in_video_file
        out_video_fp: str = scene['task'].video_file

        do_append: bool = False
        if not os.path.exists(in_video_fp):
            raise ValueError(red(f"Missing input file: {in_video_fp}"))
        if (
            not os.path.exists(out_video_fp)
            or os.path.getmtime(in_video_fp) > os.path.getmtime(out_video_fp)
        ):
            do_append = True

        else:
            dst_frame_count: int = calculate_scene_frame_count(scene)
            in_video_info: VideoInfo | None =  None
            try:
                in_video_info = extract_media_info_mco(in_video_fp)['video']
                print(f"  input video file: {out_video_info['frame_count']} frames")
                if in_video_info['frame_count'] != dst_frame_count:
                    raise ValueError(f"Error: {scene_id}, input file has wrong number of frames")
            except:
                raise ValueError(f"Error: {scene_id}, not valid input file")

            print(yellow(f"Scene to generate: {dst_frame_count} frames"))
            out_video_info: VideoInfo | None =  None
            try:
                out_video_info = extract_media_info_mco(out_video_fp)['video']
                print(f"  output video file: {out_video_info['frame_count']} frames")
                if out_video_info['frame_count'] != dst_frame_count:
                    do_append = True
            except:
                do_append = True

        if do_append:
            video_to_update_fp[in_video_fp] = out_video_fp

    # Stabilize
    dvr.select_page("edit")
    for item in timeline.video_track_items():
        in_video_fp: str = item.media_clip.filepath

        # If this clip has to be rendered, stabilize it first
        if in_video_fp in video_to_update_fp:
            timeline.select_item(item)
            print(lightcyan(f"stabilize item:"), item.name)
            if not item.stabilize():
                print(red(f"  failed to stabilize item: {item.name}"))



    render: Render = project.render
            # out_video_fp: str = video_to_update_fp[in_video_fp]

    # # Define a render job
    # render.load_preset('mco_cg')





def signal_handler(signum, frame):
    # Close if it has been started from this script
    if not app_already_started():
        print(yellow("TODO: close it"))
        dvr.quit()
    sys.exit()

if __name__ == "__main__":
    # signal.signal(signal.SIGINT, signal.SIG_DFL)
    signal.signal(signal.SIGINT, signal_handler)
    main()
