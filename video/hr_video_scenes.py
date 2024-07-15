from collections import deque
import math
import sys
import os
import subprocess
import time
from pprint import pprint

import numpy as np


from parsers._types import VideoSettings
from processing.upscale import UpscalePipeline
from nn_inference.resource_mgr import Frame
from scene.consolidate import consolidate_scene
from utils.images import Image
from utils.mco_types import Scene, VideoChapter
from utils.media import extract_media_info, str_to_video_codec
from utils.p_print import *
from utils.mco_utils import makedirs
from utils.pxl_fmt import PIXEL_FORMAT
from utils.time_conversions import FrameRate
from utils.tools import ffmpeg_exe
from parsers import (
    db,
    Chapter,
    all_chapter_keys,
    key,
    TaskName,
    ProcessingTask,
)
from .concat_frames import (
    set_video_filename,
)


def generate_hr_scenes(
    episode: str,
    single_chapter: Chapter = '',
    task: TaskName = '',
    force: bool = False,
    simulation: bool = False,
    scene_no: int | None = None,
    scene_min: int = -1,
    scene_max: int = -1,
    watermark: bool = False,
    edition: str | None = None,
    debug: bool = False
):

    k_ep = key(episode)
    k_ed = edition

    # Create the video directory for this episode or chapter
    makedirs(k_ep, single_chapter, 'video')

    # Create the scen vclip chapter by chapter
    chapters: Chapter = all_chapter_keys() if single_chapter == '' else [single_chapter]
    in_frame_count: int = 0

    start_time_full = time.time()
    for chapter in chapters:

        # k_ep_src is the default episode source used to generate a chapter
        k_ep_src: str = ''
        video: VideoChapter
        if chapter in ('g_debut', 'g_fin'):
            video = db[chapter]['video']
            k_ep_src: str = k_ep if task == 'initial' else video['src']['k_ep']

        elif k_ep is None or k_ep == 'ep00':
            sys.exit(red("Missing episode no."))

        else:
            # Use the source video clip if edition is specified
            # Used for study
            video = (
                db[k_ep]['video']['target'][chapter]
                if k_ed == ''
                else db[k_ep]['video'][k_ed][chapter]
            )
            k_ep_src = k_ep

        # Do not generate clip for unused chapters
        if video['count'] <= 0:
            continue

        if debug:
            print(lightcyan(chapter))

        video['task'] = ProcessingTask(name=task)

        # Walk through target scenes
        scenes: list[Scene] = video['scenes']
        for scene in scenes:
            if scene_no is not None and scene['no'] != scene_no:
                continue
            if scene_min != -1 and scene_max != -1:
                if scene['no'] < scene_min or scene['no'] > scene_max:
                    continue

            # Patch the for study mode
            if k_ed != '':
                scene.update({
                    'dst': {
                        'count': scene['count'],
                        'k_ed': k_ed,
                        'k_ep': k_ep,
                        'k_ch': chapter,
                    },
                    'src': {
                        'k_ed': k_ed,
                        'k_ep': k_ep_src,
                        'k_ch': chapter,
                    },
                    'k_ed': k_ed,
                    'k_ep': k_ep_src,
                    'k_ch': chapter,
                })

            if debug:
                print(
                    lightgreen(f"\t{scene['no']}: {scene['start']}"),
                    f"\t({scene['dst']['count']})\t<- {scene['k_ed']}:{scene['k_ep']}:{scene['k_ch']}",
                    f"   {scene['start']} ({scene['count']})"
                )

            # Set the last task
            scene['task'] = ProcessingTask(name=task)

            # Generate frames for this scene
            consolidate_scene(scene=scene)
            set_video_filename(scene)

    print(f"Total time: {time.time() - start_time_full:.03f}s")

    scenes_to_process: list[Scene] = []
    for chapter in chapters:
        k_ep_src: str = ''
        video: VideoChapter
        if chapter in ('g_debut', 'g_fin'):
            video = db[chapter]['video']
            k_ep_src: str = k_ep if task == 'initial' else video['src']['k_ep']
        else:
            video = (
                db[k_ep]['video']['target'][chapter]
                if k_ed == ''
                else db[k_ep]['video'][k_ed][chapter]
            )
            k_ep_src = k_ep

        if video['count'] <= 0:
            continue

        # Walk through target scenes
        scenes: list[Scene] = video['scenes']
        for scene in scenes:
            if scene_no is not None and scene['no'] != scene_no:
                continue
            if scene_min != -1 and scene_max != -1:
                if scene['no'] < scene_min or scene['no'] > scene_max:
                    continue

            print(lightcyan("================================== Scene ======================================="))
            pprint(scene)
            print(lightcyan("==============================================================================="))
            if os.path.exists(scene['task'].video_file) and not force:
                continue

            scenes_to_process.append(scene)

    print(f"Total number of scenes to upscale: {len(scenes_to_process)}")

    scene: Scene = scenes_to_process[0]

    # Input
    in_fp: str = scene['task'].in_video_file
    video_info = extract_media_info(in_fp)['video']
    pix_fmt: str = video_info['pix_fmt']
    pipe_bpp: int = PIXEL_FORMAT[pix_fmt]['pipe_bpp']
    print(f"pipe_bpp: {pipe_bpp}")
    nbytes = math.prod(video_info['shape'][:2]) * pipe_bpp / 8
    frame_count: int = video_info['frame_count']
    if int(nbytes) != nbytes:
        raise ValueError(f"[E] Number of bytes is not a multiple of 8: {nbytes} bytes ({pix_fmt})")
    in_frame_nbytes: int = int(nbytes)
    print(f"Input frame, {frame_count} frames, nbytes = {in_frame_nbytes}")

    pipe_pixfmt = pix_fmt

    reader_command: list[str] = [
        ffmpeg_exe,
        "-hide_banner",
        "-loglevel", "warning",
        "-nostats",
        "-i", in_fp,
        "-f", "image2pipe",
        "-pix_fmt", pipe_pixfmt,
        "-vcodec", "rawvideo",
        "-"
    ]
    if debug:
        print(lightgreen(f"[V]FFmpeg reader command:"), ' '.join(reader_command))

    # Open subprocess
    reader_subproces: subprocess.Popen = None
    try:
        reader_subproces = subprocess.Popen(
            reader_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=10**9
        )
    except Exception as e:
        raise ValueError(red(f"[E][R] Unexpected error: {type(e)}", flush=True))

    # Output settings
    out_fp: str = scene['task'].video_file
    frame_rate: FrameRate = video_info['frame_rate_r']
    fps: str = ''
    if isinstance(frame_rate, tuple | list):
        if frame_rate[1] == 1:
            fps = str(frame_rate[0])
        else:
            fps = '/'.join(map(str, frame_rate))
    else:
        fps = f"{frame_rate}"

    vsettings: VideoSettings = scene['task'].video_settings
    if vsettings.codec not in str_to_video_codec:
        sys.exit(red(f"{vsettings.codec} is not supported"))
    h, w = video_info['shape'][:2]

    # Output
    in_fp: str = ""
    writer_command: list[str] = [
        ffmpeg_exe,
        "-hide_banner",
        "-loglevel", "warning",
        "-nostats",

        "-f", "rawvideo",
        '-pixel_format', pipe_pixfmt,
        '-video_size', f"{w}x{h}",
        "-r", fps,

        "-i", "pipe:0",

        "-vcodec", str_to_video_codec[vsettings.codec].value,
        "-pix_fmt", vsettings.pix_fmt,
        *vsettings.codec_options
    ]

    # Add metadata
    writer_command.extend(["-movflags", "use_metadata_tags"])
    if len(vsettings.metadata.keys()):
        for k, bpp in vsettings.metadata.items():
            writer_command.extend(["-metadata:s:v:0", f"{k}={bpp}"])

    # Output filename
    writer_command.extend([out_fp, "-y"])

    if debug:
        print(purple(f"[V] FFmpeg writer command:"), ' '.join(writer_command))

    # Open subprocess
    writer_subproces: subprocess.Popen = None
    if True:
        try:
            writer_subproces = subprocess.Popen(
                writer_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except Exception as e:
            raise ValueError(red(f"[E][W] Unexpected error: {type(e)}"))

    in_frame: np.ndarray
    # try:
    total_size = 0
    for no in range(
        scene['src']['start'],
        scene['src']['start'] + scene['src']['count']
    ):
        # Get input frame
        in_frame = reader_subproces.stdout.read(in_frame_nbytes)
        if len(in_frame) < in_frame_nbytes:
            raise ValueError(red(f"[E][R] Unexpected error: frame size < {in_frame_nbytes}"))

        # print(f"{no}: {len(in_frame)}")
        # print(f"{no}", end='\r')
        # in_frame = reader_subproces.stdout.read()
        # total_size += len(in_frame)
        # print(f"{no}: {len(in_frame)}")

        # Write
        writer_subproces.stdin.write(in_frame)

    print(total_size)
    # except Exception as e:
    #     print(e)

    if writer_subproces is not None:
        stderr_bytes: bytes | None = None
        try:
            # Arbitrary timeout value
            _, stderr = writer_subproces.communicate(timeout=10)
        except:
            writer_subproces.kill()
            pass
        if stderr_bytes is not None:
            stderr = stderr_bytes.decode('utf-8)')
            # TODO: parse the output file
            pprint(stderr)
    print("done")
