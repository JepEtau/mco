from __future__ import annotations
from copy import deepcopy
from enum import Enum
import math
import re
import subprocess
from typing import IO, Literal
import sys
import os
from pprint import pprint
import time

import numpy as np

from scene.consolidate import consolidate_scene
from scene.filters import clean_fcomplex, get_ffmpeg_pad_filter
from scene.src_scene import SrcScene
from utils.mco_types import ChapterVideo, Effect, Scene
from utils.mco_utils import ffmpeg_metadata
from utils.media import (
    extract_media_info_mco,
    vcodec_to_extension,
    str_to_video_codec,
    VideoInfo,
)
from utils.p_print import *
from utils.path_utils import absolute_path, path_split
from utils.pxl_fmt import PIXEL_FORMAT
from utils.time_conversions import (
    FrameRate,
    frame_to_s,
    frame_to_sexagesimal,
    s_to_sexagesimal,
)
from utils.tools import ffmpeg_exe
from parsers import (
    clean_ffmpeg_filter,
    db,
    VideoSettings,
    ProcessingTask,
    TaskName,
    pprint_scene_mapping,
    scene_no_str,
)

if sys.platform == 'win32':
    import winreg

    def get_topaz_directory(type: Literal["install", "models"]) -> str | None:
        directory = None
        key_name = r'InstallDir' if type == 'install' else r'ModelDir'
        access_registry = winreg.ConnectRegistry(None,winreg.HKEY_LOCAL_MACHINE)
        try:
            access_key = winreg.OpenKey(access_registry,r"SOFTWARE\Topaz Labs LLC\Topaz Video AI")
            directory = winreg.QueryValueEx(access_key, key_name)[0]
            if access_key:
                winreg.CloseKey(access_key)
        except:
            pass
        return directory



    TOPAZ_INSTALL_DIR = get_topaz_directory('install')
    TOPAZ_MODEL_DIR = get_topaz_directory('models')
is_topaz_env_set: bool = False



def set_topaz_environment() -> None:
    global is_topaz_env_set

    if sys.platform != 'win32':
        is_topaz_env_set = True
        return

    if not is_topaz_env_set:
        print("set Topaz environment")
        os.environ['PATH'] = f"{TOPAZ_INSTALL_DIR};{TOPAZ_MODEL_DIR};" + os.environ['PATH']
        os.environ['TVAI_MODEL_DATA_DIR'] = TOPAZ_MODEL_DIR
        os.environ['TVAI_MODEL_DIR'] = TOPAZ_MODEL_DIR
        print(os.environ['TVAI_MODEL_DATA_DIR'])
        print(os.environ['TVAI_MODEL_DIR'])
        is_topaz_env_set = True


def _get_consolidated_progressive_fp(ch_video: ChapterVideo) -> str:
    scenes: list[Scene] = ch_video['scenes']
    first_scene: Scene = scenes[0]

    vsettings: VideoSettings = db['common']['video_format']['initial']

    # Output video filename
    k_ed, k_ep, k_ch, _ = first_scene['src'].primary_scene()['k_ed_ep_ch_no']
    cache_path: str = os.path.join(
        db['common']['directories']['cache_doc'],
        'progressive'
    )
    os.makedirs(cache_path, exist_ok=True)
    out_video_fp: str = os.path.join(
        cache_path,
        f"{k_ep}_{k_ch}_{k_ed}_{first_scene['task'].hash}{vcodec_to_extension[vsettings.codec]}"
    )
    return out_video_fp



def upscale_doc_scene(
    scene: Scene,
    seek_start: int,
    seek_count: int,
    debug: bool = False,
    force: bool = False,
) -> None:

    in_video_fp: str = scene['task'].in_video_file
    out_video_fp: str = scene['task'].video_file
    task_name = scene['task'].name

    os.makedirs(path_split(out_video_fp)[0], exist_ok=True)
    # print(
    #     lightcyan(f"scene {scene['no']:02}:"),
    #     f"{in_video_fp}, {seek_start} ({seek_count}) -> {out_video_fp}"
    # )

    in_video_info: VideoInfo = extract_media_info_mco(in_video_fp)['video']
    fps: FrameRate = in_video_info['frame_rate_r']

    # Reset metadata
    scene["task"].video_settings.metadata = {}

    # Discard if already exists
    upscaled: bool = False
    if (
        os.path.exists(out_video_fp)
        and os.path.getmtime(in_video_fp) < os.path.getmtime(out_video_fp)
    ):
        try:
            out_video_info = extract_media_info_mco(out_video_fp)['video']
            if (
                out_video_info['frame_count'] == seek_count
            ):
                if not force:
                    print(lightgreen(f"Already upscaled:"), out_video_fp)
                    upscaled = True

                else:
                    print(lightcyan("Force extraction"))
        except:
            pass

    if not upscaled:
        in_h, in_w = in_video_info['shape'][:2]
        out_h, out_w = 2 * in_h, 2 * in_w

        prenoise: float = 1
        grain: float = 0.01
        gsize: int = 1

        doc_filter: str = scene['filters'][task_name].sequence.split(",")[-1]
        params: re.Match
        if params := re.search(re.compile(r"mco_doc=(\d):(\d):(\d)"), doc_filter):
            prenoise = int(params.group(1)) / 100.
            grain = float(params.group(2)) / 100.
            gsize = int(params.group(3))

        filter_complex: str = f"""
            tvai_up=model=prob-4
                :scale=0:w={out_w}:h={out_h}
                :preblur=0
                :noise=0
                :details=0
                :halo=0
                :blur=0
                :compression=0
                :estimate=8
                :prenoise={prenoise:.2f}
                :blend=0.2
                :grain={grain:.2f}:gsize={gsize}
                :device=0:vram=1:instances=1,
            scale=w={out_w}:h={out_h}:flags=lanczos:threads=0
        """

        # # Add padding
        # in_h, in_w = in_video_info['shape'][:2]
        vsettings: VideoSettings = db['common']['video_format'][task_name]
        # if task_name == 'hr' and scene['dst']['k_ch'] != 'g_doc':
        #     pad: int = vsettings.pad
        #     filter_complex += (
        #         f",pad={out_w + 2 * pad}:{out_h + 2 * pad}:{pad}:{pad}:black"
        #     )

        ffmpeg_filter: list[str] = [
            "-filter_complex",
            f"[0:v]{clean_ffmpeg_filter(filter_complex)}[outv]",
            "-map", "[outv]"
        ]

        seek_start_args: list[str] = []
        if seek_start != 0:
            seek_start_args = ["-ss", frame_to_sexagesimal(seek_start, fps)]
        seek_count_args: list[str] = []
        if seek_count != 0:
            seek_count_args = ["-t", frame_to_sexagesimal(seek_count, fps)]

        ffmpeg_command: list[str] = [
            "ffmpeg",
            "-hide_banner",
            *seek_start_args,
            "-i", in_video_fp,
            *seek_count_args,
            "-sws_flags", "spline+accurate_rnd+full_chroma_int",
            *ffmpeg_filter,

            "-pix_fmt", vsettings.pix_fmt,
            "-vcodec", str_to_video_codec[vsettings.codec].value,
            *vsettings.codec_options,
            # *metadata,
            "-an",
            "-sn",
            "-map_metadata", "-1",

            "-movflags", "frag_keyframe+empty_moov+delay_moov+use_metadata_tags+write_colr",
            "-bf", "0",
            "-y", out_video_fp
        ]

        print(lightcyan("FFmpeg command:"), ' '.join(ffmpeg_command))
        print()
        if sys.platform == 'win32':
            start_time: float = time.time()
            ffmpeg_subprocess: subprocess.Popen = subprocess.Popen(
                ffmpeg_command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=TOPAZ_INSTALL_DIR,
            )
            os.set_blocking(ffmpeg_subprocess.stdout.fileno(), False)
            while ffmpeg_subprocess.poll() is None:
                line = ffmpeg_subprocess.stdout.readline().decode('utf-8')
                if line:
                    print(line.strip(), end='\r', file=sys.stdout)

            stdout, stderr = ffmpeg_subprocess.communicate()
            if stderr is not None:
                for line in stderr.decode('utf-8').split('\n'):
                    print(line)
            if stdout is not None:
                for line in stdout.decode('utf-8').split('\n'):
                    print(line)

            print(f"Extracted in {(time.time() - start_time)}")
            print()



def upscale_doc_chapter(
    ch_video: ChapterVideo,
    debug: bool = False,
    force: bool = False,
) -> None:
    print(lightcyan("Upscale doc chapter"))
    set_topaz_environment()

    # Consolidate scenes as not done before
    scenes: list[Scene] = ch_video['scenes']
    for scene in scenes:
        pprint_scene_mapping(scene)
        scene['task'] = ProcessingTask(name=ch_video['task'].name)
        consolidate_scene(scene=scene)

    # Create a virtual scene to upscale the whole chapter
    # Use the first scene for that
    virtual_scene: Scene = deepcopy(ch_video['scenes'][0])
    last_scene = ch_video['scenes'][-1]
    ch_count: int = (
        last_scene['src'].last_frame_no()
        - virtual_scene['src'].first_frame_no()
        + 1
    )
    virtual_scene['dst']['count'] = ch_count
    virtual_scene['geometry'] = None
    if 'ref' not in virtual_scene:
        virtual_scene['ref'] = {}
    virtual_scene['ref']['count'] = virtual_scene['dst']['count']
    virtual_scene['src'].primary_scene()['count'] = ch_count
    # virtual_scene['task'].video_file = absolute_path(
    #     os.path.join(
    #         cache_path,
    #         f"ed_{scene['k_ed']}",
    #         f"{basename}{suffix}{ext}"
    #     )
    # )


    # Upscale this cirtual scene
    src_scene = virtual_scene['src'].primary_scene()
    task_name: TaskName = scene['task'].name

    # Input video file
    in_video_fp: str = src_scene['scene']['task'].in_video_file
    if not os.path.exists(in_video_fp):
        raise ValueError(f"missing {in_video_fp}")
    virtual_scene['task'].in_video_file = in_video_fp

    # Seek
    ch_seek_start: int = (
        src_scene['start']
        - src_scene['scene']['inputs'].progressive().start
    )
    ch_seek_count: int = ch_count

    # vsettings: VideoSettings = scene['task'].video_settings
    vsettings: VideoSettings = db['common']['video_format'][task_name]
    k_ed, k_ep, k_ch = src_scene['k_ed_ep_ch_no'][:3]

    # Output filepath
    basename = f"{k_ep}_{k_ch}__{k_ed}"
    suffix = f"_{task_name}"
    ext: str = vcodec_to_extension[vsettings.codec]
    out_ch_video_fp = absolute_path(
        os.path.join(
            virtual_scene['cache'],
            task_name,
            f"{basename}{suffix}{ext}"
        )
    )
    virtual_scene['task'].video_file = out_ch_video_fp

    # Upscale this chapter
    upscale_doc_scene(
        scene=virtual_scene,
        seek_start=ch_seek_start,
        seek_count=ch_seek_count,
        debug=debug,
        force=force,
    )

    # Create a folder for color grading
    os.makedirs(
        os.path.abspath(
            os.path.join(path_split(out_ch_video_fp)[0], os.pardir, 'cg')
        ),
        exist_ok=True
    )

    # Split upscaled video into scenes
    in_video_info: VideoInfo = extract_media_info_mco(out_ch_video_fp)['video']
    for scene in scenes:
        # Only one src scene per scene
        src_scene = scene['src'].primary_scene()['scene']

        # Input and output filepath
        in_video_fp = out_ch_video_fp
        out_video_fp = scene['task'].video_file

        # Seek
        seek_start: int = src_scene['start'] - ch_seek_start
        seek_count: int = src_scene['count']

        # Discard if already exists
        if (
            os.path.exists(out_video_fp)
            and os.path.getmtime(in_video_fp) < os.path.getmtime(out_video_fp)
        ):
            out_video_info = extract_media_info_mco(out_video_fp)['video']
            if (
                out_video_info['frame_count'] == seek_count
            ):
                if not force:
                    print(lightgreen(f"Already extracted:"), out_video_fp)
                    continue
                else:
                    print(lightcyan("Force extraction"))

        # Split
        os.makedirs(path_split(out_video_fp)[0], exist_ok=True)
        print(
            lightcyan(f"scene {scene['no']:02}:"),
            f"{in_video_fp}, {seek_start} ({seek_count}) -> {out_video_fp}"
        )

        fps: FrameRate = in_video_info['frame_rate_r']
        ffmpeg_command: list[str] = [
            ffmpeg_exe,
            "-hide_banner",
            "-loglevel", "warning",
            "-stats",
            "-ss", frame_to_sexagesimal(seek_start, fps),
            "-i", in_video_fp,
            "-t", frame_to_sexagesimal(seek_count, fps),
            "-vcodec", "copy",
            "-an",
            "-sn",
            "-map_metadata", "-1",
            out_video_fp, "-y"
        ]
        print()
        if debug:
            print(lightcyan("FFmpeg command:"), ' '.join(ffmpeg_command))
        start_time: float = time.time()
        ffmpeg_subprocess: subprocess.Popen = subprocess.Popen(
            ffmpeg_command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        os.set_blocking(ffmpeg_subprocess.stdout.fileno(), False)
        while ffmpeg_subprocess.poll() is None:
            line = ffmpeg_subprocess.stdout.readline().decode('utf-8')
            if line:
                print(line.strip(), end='\r', file=sys.stdout)

        stdout, stderr = ffmpeg_subprocess.communicate()
        if stderr is not None:
            for line in stderr.decode('utf-8').split('\n'):
                print(line)
        if stdout is not None:
            for line in stdout.decode('utf-8').split('\n'):
                print(line)

        print(cyan("Extracted in"), f"{s_to_sexagesimal(time.time() - start_time)}")
        print()

        # For debug
        if not sys.platform == 'win32':
            fp: str = out_video_fp.replace("_hr", "_hr_cg").replace("/hr", "/cg")
            if os.path.exists(fp) and os.path.islink(fp):
                os.unlink(fp)
            if not os.path.exists(out_video_fp):
                raise FileNotFoundError(red(f"{out_video_fp}"))
            os.symlink(out_video_fp, fp)



def upscale_doc_scenes(
    scenes: list[Scene],
    debug: bool = False,
    force: bool = False,
) -> None:
    print(lightcyan("Upscale doc scenes"))
    set_topaz_environment()

    # Output video filename
    # _, k_ep, k_ch, _ = scenes[0]['src'].primary_scene()['k_ed_ep_ch_no']
    # ch_video: ChapterVideo = db[k_ep]['video']['target'][k_ch]
    # in_video_fp: str = _get_consolidated_progressive_fp(ch_video)

    # scene_seek_start: int = 0
    # scene_seek_count: int = 0
    for scene in scenes:
        consolidate_scene(scene=scene, task_name='hr')

        # Consider a single src scene is used
        src_scene = scene['src'].primary_scene()['scene']
        task_name: TaskName = scene['task'].name

        # Input video file
        # scene['task'].in_video_file = in_video_fp
        # print(scene['task'].in_video_file)
        # continue
        in_video_fp: str = scene['task'].in_video_file
        if not os.path.exists(in_video_fp):
            pprint(scene['task'])
            raise FileNotFoundError(red(f"missing file: {in_video_fp}"))
            in_video_fp = src_scene['task'].fallback_in_video_files[task_name]
            src_scene['task'].in_video_file = in_video_fp

        # Disabled it because we use the consolidated initial scene from now
        # # Seek
        # scene_seek_start += scene_seek_count
        # scene_seek_count: int = src_scene['count']

        # # Add se loop
        # if (
        #     'effects' in src_scene
        #     and src_scene['effects'].has_effect('se_loop')
        # ):
        #     e: Effect = src_scene['effects'].get_effect('se_loop')
        #     scene_seek_count += sum(e.extra_param)

        scene_seek_start: int = 0
        scene_seek_count = 0

        print(
            lightcyan(f"Scene no. {scene['no']}:"),
            f"{in_video_fp}: {scene_seek_start} ({scene_seek_count})"
        )

        # Patch out name to be able to choose the best upscaled
        if scene['dst']['k_ch'] == 'doc':
            scene['task'].video_file = scene['task'].video_file.replace('_hr.', '_hr_tpz.')

        # For g_doc, used fallback because we used intermediary file
        if scene['dst']['k_ch'] in ('g_doc',):
            scene_seek_start = 0
            scene_seek_count = src_scene['count']
            scene['task'].video_file = scene['task'].fallback_in_video_files['hr']
            src_scene = scene

        upscale_doc_scene(
            scene,
            seek_start=scene_seek_start,
            seek_count=scene_seek_count,
            debug=debug,
            force=force,
        )



def consolidate_initial_doc(
    ch_video: ChapterVideo,
    debug: bool = False,
    force: bool = False,
) -> None:
    scenes: list[Scene] = ch_video['scenes']
    first_scene: Scene = scenes[0]

    # Input video file
    in_video_fp: str = first_scene['src'].primary_scene()['scene']['task'].in_video_file
    vsettings: VideoSettings = db['common']['video_format']['initial']

    # Output video filename
    out_video_fp: str = _get_consolidated_progressive_fp(ch_video)
    print(lightcyan(f"files:"), f"{in_video_fp} -> {out_video_fp}")

    # Calculate number of frames
    frame_count: int = 0
    for scene in scenes:
        src_scene: SrcScene = scene['src'].primary_scene()['scene']
        frame_count += src_scene['count']
        if (
            'effects' in src_scene
            and src_scene['effects'].has_effect('se_loop')
        ):
            e: Effect = src_scene['effects'].get_effect('se_loop')
            frame_count += sum(e.extra_param)
    print(lightcyan(f"consolidated framecount:"), f"{frame_count}")

    # Ignore if already exists
    if os.path.exists(out_video_fp):
        try:
            out_video_info: VideoInfo = extract_media_info_mco(out_video_fp)['video']
            if out_video_info['frame_count'] == frame_count:
                print(lightgreen("Already extracted"))
                return
        except:
            pass

    # Input video scenes
    in_video_info: VideoInfo = extract_media_info_mco(in_video_fp)['video']
    in_pipe_shape = in_video_info['shape']
    in_h, in_w = in_pipe_shape[:2]
    in_pipe_dtype = np.uint8
    in_pipe_pixfmt = in_video_info['pix_fmt']
    # in_pipe_nbytes: int = (
    #     in_h * in_w * PIXEL_FORMAT[in_pipe_pixfmt]['pipe_bpp']
    # ) // 8
    in_pipe_nbytes: int = in_h * in_w * 4

    # Output video
    out_pipe_dtype: np.dtype = in_pipe_dtype
    out_pipe_pixfmt: str = in_pipe_pixfmt

    if debug or True:
        print(lightcyan(f"Input:"))
        print(f"  video file: {in_video_fp}")
        print(f"  frame_count: {in_video_info['frame_count']}")
        print(f"  dimensions: {in_w}x{in_h}")
        print(f"  pipe dtype: {in_pipe_dtype}")
        print(f"  pipe pixfmt: {in_pipe_pixfmt}")
        print(f"  pipe nbytes: {in_pipe_nbytes}")
        pprint(PIXEL_FORMAT[in_pipe_pixfmt])

        print(lightcyan(f"Output:"))
        print(f"  video file: {out_video_fp}")
        print(f"  pixfmt: {in_pipe_pixfmt}")
        print(f"  pipe dtype: {out_pipe_dtype}")
        print(f"  pipe pixfmt: {out_pipe_pixfmt}")


    # Encoder
    encoder_command: list[str] = [
        ffmpeg_exe,
        "-hide_banner",
        "-loglevel", "error",
        "-nostats",

        "-f", "rawvideo",
        '-pixel_format', vsettings.pix_fmt,
        '-video_size', f"{in_w}x{in_h}",
        "-r", str(vsettings.frame_rate),

        "-i", "pipe:0",

        "-vcodec", str_to_video_codec[vsettings.codec].value,
        *vsettings.codec_options,
        "-pix_fmt", vsettings.pix_fmt,
        "-color_range", "limited",

        "-y",
        out_video_fp
    ]
    if debug:
        print(purple(f"[V][E] command: "), " ".join(encoder_command))
    os.makedirs(path_split(out_video_fp)[0], exist_ok=True)
    e_subprocess: subprocess.Popen = None
    try:
        e_subprocess = subprocess.Popen(
            encoder_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    except Exception as e:
        print(f"[E] Unexpected error: {type(e)}", flush=True)
    e_stream: IO = e_subprocess.stdin
    os.set_blocking(e_subprocess.stdout.fileno(), False)


    # For each src scene, add start/end loop
    src_seek_start: int = 0
    src_seek_count: int = 0
    for scene in scenes:
        # Seek
        src_scene: SrcScene = scene['src'].primary_scene()['scene']
        src_seek_start = src_scene['start']
        src_seek_count: int = src_scene['count']

        src_seek_start_args = (
            ["-ss", f"{frame_to_sexagesimal(src_seek_start, frame_rate=in_video_info['frame_rate_r'])}"]
            if src_seek_start and src_seek_count
            else []
        )
        src_seek_count_args = (
            ["-t", f"{frame_to_s(src_seek_count, frame_rate=in_video_info['frame_rate_r'])}"]
            if src_seek_count
            else []
        )

        d_command: list[str] = [
            ffmpeg_exe,
            "-hide_banner",
            "-loglevel", "warning",
            "-nostats",
            *src_seek_start_args,
            "-i", in_video_fp,
            *src_seek_count_args,

            "-f", "image2pipe",
            "-pix_fmt", in_pipe_pixfmt,
            "-vcodec", "rawvideo",
            "-"
        ]
        d_subprocess: subprocess.Popen = None
        try:
            d_subprocess = subprocess.Popen(
                d_command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
        except Exception as e:
            print(red(f"[D][W] Unexpected error: {type(e)}"))
            return False
        print(lightcyan(f"Src scene no. {src_scene['no']}"))
        if debug:
            print(purple(f"  Decoder command:"), ' '.join(d_command))

        # SE loop
        start_loop: int = 0
        end_loop: int = 0
        if 'effects' in src_scene and src_scene['effects'].has_effect('se_loop'):
            e: Effect = src_scene['effects'].get_effect('se_loop')
            start_loop, end_loop = e.extra_param

        d_stream: IO = d_subprocess.stdout
        i: int = 0
        while i < src_seek_count:
            in_buffer = np.frombuffer(d_stream.read(in_pipe_nbytes), dtype=np.uint8)
            if i == 0 and start_loop:
                [e_stream.write(in_buffer) for _ in range(start_loop)]
                start_loop = 0

            if i == (src_seek_count - 1) and end_loop:
                [e_stream.write(in_buffer) for _ in range(end_loop)]
                end_loop = 0

            i += 1
            e_stream.write(in_buffer)

            # line = e_subprocess.stdout.readline().decode('utf-8')
            # if line:
            #     print(line.strip(), end='\r', file=sys.stdout)

        # if scene['no'] == 2:
        #     break

    stdout_bytes: bytes | None = None
    stdout_bytes, _ = e_subprocess.communicate(timeout=20)
    if stdout_bytes is not None:
        stdout = stdout_bytes.decode('utf-8)')
        # TODO: parse the output file
        if stdout != '':
            print(f"stdout:")
            pprint(stdout)






def consolidate_initial_doc_scenes(
    ch_video: ChapterVideo,
    debug: bool = False,
    force: bool = False,
) -> None:
    scenes: list[Scene] = ch_video['scenes']
    # first_scene: Scene = scenes[0]

    for scene in scenes:
        consolidate_scene(scene=scene, task_name='hr')

        primary_src_scene: SrcScene = scene['src'].primary_scene()
        src_scene: Scene = primary_src_scene['scene']

        # Input video file
        in_video_fp: str = src_scene['inputs'].progressive().filepath
        vsettings: VideoSettings = db['common']['video_format']['hr']

        # Output video filename
        k_ed, k_ep, k_ch, _ = primary_src_scene['k_ed_ep_ch_no']
        cache_path: str = os.path.join(
            db['common']['directories']['cache_doc'],
            k_ep,
            'initial'
        )
        os.makedirs(cache_path, exist_ok=True)

        out_video_fp: str = os.path.join(
            cache_path,
            f"{k_ep}_{k_ch}_{scene_no_str(scene)}__{k_ed}{vcodec_to_extension[vsettings.codec]}"
        )

        print(lightcyan(f"files:"), f"{in_video_fp} -> {out_video_fp}")

        # Modify the in video filepath to be used by the tpz upscale function
        scene['task'].in_video_file = out_video_fp

        # Calculate number of frames
        frame_count: int = src_scene['count']
        if (
            'effects' in src_scene
            and src_scene['effects'].has_effect('se_loop')
        ):
            e: Effect = src_scene['effects'].get_effect('se_loop')
            frame_count += sum(e.extra_param)
        print(lightcyan(f"consolidated framecount:"), f"{frame_count}")

        # Ignore if already exists
        if os.path.exists(out_video_fp):
            try:
                out_video_info: VideoInfo = extract_media_info_mco(out_video_fp)['video']
                if out_video_info['frame_count'] == frame_count:
                    print(lightgreen("Already extracted"), out_video_fp)
                    if not force:
                        continue
                    else:
                        print(lightcyan("Force extraction"))
            except:
                pass

        # Input video scenes
        in_video_info: VideoInfo = extract_media_info_mco(in_video_fp)['video']
        in_pipe_shape = in_video_info['shape']
        in_h, in_w = in_pipe_shape[:2]
        in_pipe_dtype = np.uint8
        in_pipe_pixfmt = in_video_info['pix_fmt']
        # in_pipe_nbytes: int = (
        #     in_h * in_w * PIXEL_FORMAT[in_pipe_pixfmt]['pipe_bpp']
        # ) // 8
        in_pipe_nbytes: int = in_h * in_w * 4

        # Output video
        out_pipe_dtype: np.dtype = in_pipe_dtype
        out_pipe_pixfmt: str = in_pipe_pixfmt

        if debug or True:
            print(lightcyan(f"Input:"))
            print(f"  video file: {in_video_fp}")
            print(f"  frame_count: {in_video_info['frame_count']}")
            print(f"  dimensions: {in_w}x{in_h}")
            print(f"  pipe dtype: {in_pipe_dtype}")
            print(f"  pipe pixfmt: {in_pipe_pixfmt}")
            print(f"  pipe nbytes: {in_pipe_nbytes}")
            pprint(PIXEL_FORMAT[in_pipe_pixfmt])

            print(lightcyan(f"Output:"))
            print(f"  video file: {out_video_fp}")
            print(f"  pixfmt: {in_pipe_pixfmt}")
            print(f"  pipe dtype: {out_pipe_dtype}")
            print(f"  pipe pixfmt: {out_pipe_pixfmt}")


        # Encoder

        # FFmpeg filters
        filter_complex: list[str] = []
        pad: int = vsettings.pad
        fcomplex_str: str = f"pad=w=iw+{pad}:h={pad}+ih:x={pad//2}:y={pad//2}:color=black"
        filter_complex = [
            "-filter_complex", f"[0:v]{fcomplex_str}[outv]",
            "-map", "[outv]"
        ]
        print(purple(f"[V][E] fcomplex_str:"), fcomplex_str)

        encoder_command: list[str] = [
            ffmpeg_exe,
            "-hide_banner",
            "-loglevel", "error",
            "-nostats",

            "-f", "rawvideo",
            '-pixel_format', vsettings.pix_fmt,
            '-video_size', f"{in_w}x{in_h}",
            "-r", str(vsettings.frame_rate),

            "-i", "pipe:0",
            *filter_complex,

            "-vcodec", str_to_video_codec[vsettings.codec].value,
            *vsettings.codec_options,
            "-pix_fmt", vsettings.pix_fmt,
            "-color_range", "limited",

            "-y",
            out_video_fp
        ]
        if debug:
            print(purple(f"[V][E] command: "), " ".join(encoder_command))
        os.makedirs(path_split(out_video_fp)[0], exist_ok=True)
        e_subprocess: subprocess.Popen = None
        try:
            e_subprocess = subprocess.Popen(
                encoder_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        except Exception as e:
            print(f"[E] Unexpected error: {type(e)}", flush=True)
        e_stream: IO = e_subprocess.stdin
        os.set_blocking(e_subprocess.stdout.fileno(), False)

        # Seek
        src_seek_start: int = src_scene['start']
        src_seek_count: int = src_scene['count']

        src_seek_start_args = (
            ["-ss", f"{frame_to_sexagesimal(src_seek_start, frame_rate=in_video_info['frame_rate_r'])}"]
            if src_seek_start and src_seek_count
            else []
        )
        src_seek_count_args = (
            ["-t", f"{frame_to_s(src_seek_count, frame_rate=in_video_info['frame_rate_r'])}"]
            if src_seek_count
            else []
        )

        d_command: list[str] = [
            ffmpeg_exe,
            "-hide_banner",
            "-loglevel", "warning",
            "-nostats",
            *src_seek_start_args,
            "-i", in_video_fp,
            *src_seek_count_args,

            "-f", "image2pipe",
            "-pix_fmt", in_pipe_pixfmt,
            "-vcodec", "rawvideo",
            "-"
        ]
        d_subprocess: subprocess.Popen = None
        try:
            d_subprocess = subprocess.Popen(
                d_command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
        except Exception as e:
            print(red(f"[D][W] Unexpected error: {type(e)}"))
            return False
        print(lightcyan(f"Src scene no. {src_scene['no']}"))
        if debug:
            print(purple(f"  Decoder command:"), ' '.join(d_command))

        # SE loop
        start_loop: int = 0
        end_loop: int = 0
        if 'effects' in src_scene and src_scene['effects'].has_effect('se_loop'):
            e: Effect = src_scene['effects'].get_effect('se_loop')
            start_loop, end_loop = e.extra_param

        d_stream: IO = d_subprocess.stdout
        i: int = 0
        while i < src_seek_count:
            in_buffer = np.frombuffer(d_stream.read(in_pipe_nbytes), dtype=np.uint8)
            if i == 0 and start_loop:
                [e_stream.write(in_buffer) for _ in range(start_loop)]
                start_loop = 0

            if i == (src_seek_count - 1) and end_loop:
                [e_stream.write(in_buffer) for _ in range(end_loop)]
                end_loop = 0

            i += 1
            e_stream.write(in_buffer)

            line = e_subprocess.stdout.readline().decode('utf-8')
            if line:
                print(line.strip(), end='\r', file=sys.stdout)

        # if scene['no'] == 2:
        #     break

        stdout_bytes: bytes | None = None
        stdout_bytes, _ = e_subprocess.communicate(timeout=20)
        if stdout_bytes is not None:
            stdout = stdout_bytes.decode('utf-8)')
            # TODO: parse the output file
            if stdout != '':
                print(f"stdout:")
                pprint(stdout)








class TopazCategories(Enum):
    SCALING = "Scaling Models"
    INTERPOLATION = "Interpolation Models"
    STABILIZATION = "Stabilization Models"


TOPAZ_MODELS: dict[TopazCategories, dict[str, str]] = {
    TopazCategories.SCALING: {
        'aaa-9': "Aliasing or Moire",
        'ahq-10': "High Quality",
        'ahq-11': "High Quality",
        'ahq-12': "High Quality",
        'alq-10': "Low Quality",
        'alq-12': "Low Quality",
        'alq-13': "Low Quality",
        'alqs-1': "Strong Halo",
        'alqs-2': "Strong Halo",
        'amq-10': "Medium Quality",
        'amq-12': "Medium Quality",
        'amq-13': "Medium Quality",
        'amqs-1': "Medium Quality Halo",
        'amqs-2': "Medium Quality Halo",
        'ddv-1': "Dione DV 2X FPS",
        'ddv-2': "Dione DV 2X FPS",
        'ddv-3': "Dione DV 2X FPS",
        'dtd-1': "Dione Robust",
        'dtd-3': "Dione Robust",
        'dtd-4': "Dione Robust",
        'dtds-1': "Dione Robust Dehalo",
        'dtds-2': "Dione Robust Dehalo",
        'dtv-1': "Dione TV 2X FPS",
        'dtv-3': "Dione TV 2X FPS",
        'dtv-4': "Dione TV 2X FPS",
        'dtvs-1': "Dione Dehalo 2X FPS",
        'dtvs-2': "Dione Dehalo 2X FPS",
        'gcg-5': "Computer Generated",
        'ghq-5': "High Quality",
        'iris-1': "Iris",
        'nyx-1': "Nyx",
        'prob-1': "Proteus",
        'prob-2': "Proteus",
        'prob-3': "Proteus",
        'prob-4': "Proteus",
        'thd-3': "Fine Tune Detail",
        'thf-4': "Fine Tune Fidelity",
        'thm-2': "Themis",
    },
    TopazCategories.INTERPOLATION: {
        'apo-8': "Apollo v8",
        'apf-1': "Apollo Fast v1",
        'chr-2': "Chronos v2",
        'chf-1': "Chronos Fast v1",
        'chf-2': "Chronos Fast v2",
        'chf-3': "Chronos Fast v3",
        'chr-1': "Chronos Slo-Mo / FPS Conversion v1",
        'chr-2': "Chronos Slo-Mo / FPS Conversion v2",
    },
    TopazCategories.STABILIZATION: {
        'cpe-1': "Camera Pose Estimation (first pass)",
        'cpe-2': "Camera Pose Estimation (first pass) + rolling shutter correction",
        'ref-2': "Stabilization Model (final pass)",
    },
}

TOPAZ_RESOLUTIONS: tuple[str] = [
    "480x360",
    "640x480",
    "720x480",
    "768x576",
    "1280x720",
    "1920x1080",
    "3840x2160"
]

TOPAZ_SCALE: tuple[int] = [1, 2, 4]


def download_model(model:str|None=None):

    if model is None:
        for category_name in TOPAZ_MODELS.keys():
            print(f"Category: {category_name}")

            if category_name == TopazCategories.SCALING:
                for model, label in TOPAZ_MODELS[category_name].items():
                    print(f"\t{label}")

                    for scale in TOPAZ_SCALE:
                        for r in TOPAZ_RESOLUTIONS:
                            print(f"\t\tscale:{scale}, resolution:{r}", flush=True)
                            topaz_command = [
                                "ffmpeg.exe",
                                "-nostats",
                                "-hide_banner",
                                "-f", "lavfi",
                                "-i", f"color=c=black@0.8:duration=0.01:rate=25:size={r}",
                                "-vf", f"tvai_up=model={model}:scale={scale}:device=-2:vram=1:instances=0",
                                "-f", "null", "-"
                            ]

                            print("running topaz_command")
                            print("")
                            print(" ".join(topaz_command))
                            print("")
                            process = subprocess.run(
                                topaz_command,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                cwd=TOPAZ_INSTALL_DIR
                            )

                            return
