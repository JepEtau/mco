from datetime import datetime
import subprocess
import sys
import os
import time
from pprint import pprint

from parsers.p_print import pprint_scene_mapping
from scene.consolidate import consolidate_scene
from utils.media import VideoInfo, extract_media_info
from utils.pxl_fmt import PIXEL_FORMAT
from video.consolidate_scenes import get_chapter_video
from .st_scenes import convert_video_for_evaluation
from utils.mco_types import Scene, ChapterVideo
from utils.mco_utils import ffmpeg_metadata, scene_id_str
from utils.tools import ffmpeg_exe
from utils.p_print import *
from utils.path_utils import absolute_path
from parsers import (
    db,
    Chapter,
    all_chapter_keys,
    ep_key,
    TaskName,
    ProcessingTask,
    VideoSettings,
)



def tf_scenes(
    episode: str,
    single_chapter: Chapter = '',
    scene_no: int = -1,
    task_name: TaskName = '',
    evaluate: bool = False,
    force: bool = False,
    debug: bool = False,
):
    k_ep = ep_key(episode)
    chapters: Chapter = all_chapter_keys() if single_chapter == '' else [single_chapter]

    if k_ep == '' and single_chapter not in ('g_debut', 'g_fin'):
        raise ValueError(red("[E] episode must be set"))

    for k_ch in chapters:

        ch_video: ChapterVideo | None = get_chapter_video(k_ep, k_ch)
        if ch_video is None:
            continue

        ch_video['task'] = ProcessingTask(name=task_name)
        if debug:
            print(f"\n<<<<<<<<<<<<<<<<<<<<< {k_ch} >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            print(f"scene_no: {scene_no}")

        # Walk through target scenes
        scenes: list[Scene] = ch_video['scenes']
        for scene in scenes:
            if scene_no != -1 and scene['no'] != scene_no:
                continue
            pprint_scene_mapping(scene)

            # Consolidate this scene
            consolidate_scene(scene, task_name=task_name)
            scene_id: str = scene_id_str(scene)

            if debug:
                print(lightcyan(f"======================= generate_{task_name}_scenes: {scene_id} ============================="))
                pprint(scene)
                print(lightcyan("==============================================================================="))

            do_process: bool = False

            in_fp: str = scene['task'].in_video_file
            in_mtime: float = 0
            if os.path.exists(in_fp):
                in_mtime = os.path.getmtime(in_fp)
            else:
                print(yellow(f"{scene_id}: missing input file:"), in_fp)
                print(yellow("  use non stabilized video"))
                # Fallback to HR if not stabilized
                in_fp: str = scene['task'].fallback_in_video_files['hr']
                in_mtime: float = 0
                if os.path.exists(in_fp):
                    in_mtime = os.path.getmtime(in_fp)
                else:
                    print(red(f"{scene_id}: missing input file:"), in_fp)
                    continue

            out_fp: str = scene['task'].video_file
            out_mtime: float = 0
            out_mtime_str: str = "-"
            if os.path.exists(out_fp):
                out_mtime = os.path.getmtime(out_fp)
                out_mtime_str = datetime.fromtimestamp(out_mtime).strftime("%Y-%m-%d %H:%M:%S")

            if out_mtime_str == "-":
                print(yellow(f"{scene_id}: temporal filtered scene is not generated"))
                do_process = True

            elif out_mtime < in_mtime or force:
                print(yellow(f"{scene_id} has to be updated"))
                do_process = True

            if not do_process:
                if evaluate:
                    convert_video_for_evaluation(
                        [in_fp, out_fp],
                        force=force,
                        debug=debug
                    )
                continue

            # Run temporalfilter
            print(lightcyan(f"{scene_id}: temporal filtering"))

            t_radius: int = 6
            strength: int = 400
            try:
                t_radius, strength = list(
                    map(int, scene['filters'][task_name].sequence.split(','))
                )
            except:
                pass

            # From temporal fix
            root_dir: str = os.path.dirname(
                absolute_path("A:\\py_temporalfix\\py_temporalfix.py")
            )
            vspipe_exe: str = absolute_path(
                os.path.join(root_dir, "external", "vspython", "VSPipe.exe")
            )
            vs_out_pix_fmt = 'yuv444p16le'


            # VSpipe command
            vs_command: list[str] = [
                vspipe_exe,
                os.path.join(root_dir, "vstf.vpy"),
                "--arg", f"input_fp=\"{in_fp}\"",
                "--arg", f"tr={t_radius}",
                "--arg", f"strength={strength}",
                "--arg", f"pix_fmt={vs_out_pix_fmt}",
                "-",
            ]
            if debug:
                print(lightcyan("VS command:"))
                print(lightgreen(' '.join(vs_command)))


            in_vi: VideoInfo = extract_media_info(in_fp)['video']
            f_rate = in_vi['frame_rate_r']
            frame_rate = str(f_rate)
            if isinstance(f_rate, tuple | list):
                if f_rate[1] != 1:
                    frame_rate = ":".join(map(str, f_rate))
                else:
                    frame_rate = str(f_rate[0])

            h, w = in_vi['shape'][:2]
            frame_count: int = in_vi['frame_count']
            out_bpp: int = PIXEL_FORMAT[vs_out_pix_fmt]['bpp']
            out_nbytes: int = h * w * out_bpp // 8
            color_params: str = "setparams=colorspace=bt709:color_primaries=bt709:color_trc=bt709"

            # Encoder command
            vsettings: VideoSettings = scene['task'].video_settings
            metadata: list[str] = ffmpeg_metadata(scene)
            if debug:
                pprint(vsettings)
            encoder_command: list[str] = [
                ffmpeg_exe,
                "-hide_banner",
                "-loglevel", "error",
                "-stats",
                '-f', 'rawvideo',
                '-pixel_format', vs_out_pix_fmt,
                '-video_size', f"{w}x{h}",
                "-r", frame_rate,
                '-i', 'pipe:0',
                "-filter_complex", f"[0:v]{color_params}[outv]",
                "-map", "[outv]",
                "-vcodec", vsettings.codec,
                *metadata,
                *vsettings.codec_options,
                "-pix_fmt", vsettings.pix_fmt,
                "-color_range", "full",
                "-y", out_fp
            ]

            # Encoder process
            e_subprocess: subprocess.Popen | None = None
            try:
                e_subprocess = subprocess.Popen(
                    encoder_command,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                )
            except Exception as e:
                sys.exit(red(f"[E] Unexpected error: {type(e)}"))
            if e_subprocess is None:
                sys.exit(red(f"[E] Encoder process is not started"))

            # Clean environment for vspython
            # vs_path: list[str] = []
            forbidden_names: tuple[str] = (
                'python',
                'conda',
                'vapoursynth',
                'ffmpeg',
            )

            # Create path used by vs subprocess
            vs_path: list[str] = []
            sep: str = ";"
            if sys.platform == "win32":
                for dir in ("Scripts", "vs-scripts", "vs-plugins", ""):
                    vs_path.insert(0, os.path.abspath(
                        os.path.join(root_dir, "external", "vspython", dir)
                    ))
            vs_path.insert(0, root_dir)

            # Clean environnment for vs
            vs_env = os.environ.copy()
            if sys.platform == 'win32':
                del vs_env['PATH']
                for k, v in vs_env.copy().items():
                    k_lower, v_lower = k.lower(), v.lower()
                    for n in forbidden_names:
                        if n in k_lower:
                            try:
                                del vs_env[k]
                            except:
                                pass

                        if n in v_lower:
                            try:
                                del vs_env[k]
                            except:
                                pass
                vs_env['PATH'] = sep.join(vs_path)

            # Vs process
            vs_subprocess: subprocess.Popen | None = None
            try:
                vs_subprocess = subprocess.Popen(
                    vs_command,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=vs_env,
                )
            except Exception as e:
                print(f"[E] Unexpected error: {type(e)}", flush=True)



            if debug:
                print(lightcyan("vs_temporalfix command:"))
                print(lightgreen(' '.join(vs_command)))
                print(lightcyan("Pipe in:"))
                print(f"  shape: {w}x{h}")
                print(f"  nb of bytes: {out_nbytes}")
                print(f"  frame_count: {frame_count}")

                print(lightcyan("Encoder command:"))
                print(lightgreen(' '.join(encoder_command)))

            frame: bytes = None
            line: str = ''
            os.set_blocking(e_subprocess.stdout.fileno(), False)
            os.set_blocking(vs_subprocess.stderr.fileno(), False)
            print(f"Processing:")
            try:
                for _ in range(frame_count):
                    # print(f"reading frame no. {i}", end="\r")
                    frame: bytes = vs_subprocess.stdout.read(out_nbytes)
                    if frame is None:
                        print(red("None"))
                    e_subprocess.stdin.write(frame)
                    line = e_subprocess.stdout.readline().decode('utf-8')
                    if line:
                        print(line.strip(), end='\r', file=sys.stderr)
                    line = vs_subprocess.stderr.readline().decode('utf-8')
                    if line:
                        print(line.strip(), end='\r', file=sys.stderr)
                print()
            except:
                pass

            stdout_b: bytes | None = None
            stderr_b: bytes | None = None
            try:
                # Arbitrary timeout value
                stdout_b, stderr_b = e_subprocess.communicate(timeout=10)
            except:
                e_subprocess.kill()
                return

            if stdout_b is not None:
                stdout = stdout_b.decode('utf-8)')
                if stdout:
                    print(f"FFmpeg stdout:\n{stdout}")

            if stderr_b is not None:
                stderr = stderr_b.decode('utf-8)')
                if stderr:
                    print(f"FFmpeg stderr:\n{stderr}")


            if evaluate:
                convert_video_for_evaluation(
                    [in_fp, out_fp],
                    force=force,
                    debug=debug
                )


