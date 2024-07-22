from collections import deque
from copy import deepcopy
import math
import os
import sys
import subprocess
from pprint import pprint
import numpy as np

from parsers._types import VideoSettings
from processing.frame_replace import (
    ImageCache,
    frame_occurences,
    get_frames_to_cache,
    get_frames_to_remove,
)
from utils.mco_types import Scene, SrcScene
from utils.media import VideoInfo, extract_media_info, str_to_video_codec
from utils.p_print import *
from utils.path_utils import path_split
from utils.pxl_fmt import PIXEL_FORMAT
from utils.time_conversions import FrameRate
from utils.tools import ffmpeg_exe



def _get_framerate(video_info: VideoInfo) -> str:
    frame_rate: FrameRate = video_info['frame_rate_r']
    fps: str = ''
    if isinstance(frame_rate, tuple | list):
        if frame_rate[1] == 1:
            fps = str(frame_rate[0])
        else:
            fps = '/'.join(map(str, frame_rate))
    else:
        fps = f"{frame_rate}"
    return fps



def _get_complex_filter(scene: Scene) -> list[str]:
    vsettings: VideoSettings = scene['task'].video_settings

    filter_complex: list[str] = []
    if vsettings.pad != 0:
        pad: int = vsettings.pad
        pad_filter: str = f"pad=w=iw+{2*pad}:h={2*pad}+ih:x={pad}:y={pad}:color=black"
        filter_complex: list[str] = [
            "-filter_complex", f"[0:v]{pad_filter}[outv]",
            "-map", "[outv]"
        ]
    return filter_complex



def generate_hr_scene(scene: Scene, debug: bool = False) -> bool:
    src_scene: SrcScene = scene['src']
    scene_key: str = f"{src_scene['k_ed']}:{src_scene['k_ep']}:{src_scene['k_ch']}:{src_scene['k_ch']}"

    in_fp: str = scene['task'].in_video_file
    out_fp: str = scene['task'].video_file
    os.makedirs(path_split(out_fp)[0], exist_ok=True)

    # Input
    video_info: VideoInfo = extract_media_info(in_fp)['video']

    if len(scene['replace'].keys()) == 0:
        print("no frames to replace")
        return _add_borders_to_scene(scene, video_info, debug)

# Keep it for later use
#         print(f"{in_fp} -> {out_fp}")
#         shutil.copyfile(in_fp, out_fp)
#         xml_file: str = os.path.join(gettempdir(), "mco_tag_tmp.xml")
#         with open(xml_file, mode='w') as f:
#             f.write(
# f"""<?xml version="1.0"?>
# <Tags>
#     <Tag>
#         <Targets />
#         <Simple>
#             <Name>HR</Name>
#             <String>{scene['task'].hashcode}</String>
#         </Simple>
#     </Tag>
# </Tags>
# """
#             )

#         process = subprocess.run(
#             [
#                 "mkvpropedit",
#                 out_fp,
#                 "--tags",
#                 f"track:v1:{xml_file}"
#             ],
#             stdout=subprocess.PIPE
#         )
#         os.remove(xml_file)
#         stdout: str = process.stdout.decode('utf-8')
#         if stdout == "The file is being analyzed.\nThe changes are written to the file.\nDone.\n":
#             return True
#         print(red(f"Error: {stdout}"))

    pipe_pixfmt: str = video_info['pix_fmt']
    pipe_bpp: int = PIXEL_FORMAT[pipe_pixfmt]['pipe_bpp']
    if debug:
        print(f"pipe_pixfmt: {pipe_pixfmt}, bpp: {pipe_bpp}")
    nbytes = math.prod(video_info['shape'][:2]) * pipe_bpp / 8
    frame_count: int = video_info['frame_count']
    if int(nbytes) != nbytes:
        raise ValueError(f"[E] {scene_key} Number of bytes is not a multiple of 8: {nbytes} bytes ({pipe_pixfmt})")
    in_frame_nbytes: int = int(nbytes)
    if debug:
        print(f"Input frame, {frame_count} frames, nbytes = {in_frame_nbytes}")

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
        print(lightgreen(f"[V] FFmpeg reader command:"), ' '.join(reader_command))

    # Open subprocess
    reader_subproces: subprocess.Popen = None
    try:
        reader_subproces = subprocess.Popen(
            reader_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=10**8
        )
    except Exception as e:
        print(red(f"[E][R] {scene_key} Unexpected error: {type(e)}", flush=True))
        return False

    # Used to correct PIXEL_FORMAT array
    if False:
        total_size: int  = 0
        while True:
            try:
                data = reader_subproces.stdout.read()
            except:
                break
            if len(data) == 0:
                break
            # print(total_size)
            total_size += len(data)
        print(total_size)
        sys.exit()

    # Output settings
    vsettings: VideoSettings = scene['task'].video_settings
    if vsettings.codec not in str_to_video_codec:
        sys.exit(red(f"{vsettings.codec} is not supported"))
    h, w = video_info['shape'][:2]

    # Out filter: pad
    filter_complex: list[str] = _get_complex_filter(scene)

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
        "-r", _get_framerate(video_info),
        "-i", "pipe:0",

        *filter_complex,

        "-pix_fmt", vsettings.pix_fmt,
        "-vcodec", str_to_video_codec[vsettings.codec].value,
        *vsettings.codec_options
    ]

    # Add metadata
    writer_command.extend(["-movflags", "use_metadata_tags"])
    for metadata in (video_info['metadata'], vsettings.metadata):
        if len(metadata.keys()):
            for k, bpp in metadata.items():
                writer_command.extend(["-metadata:s:v:0", f"{k}={bpp}"])

    # Output filename
    writer_command.extend([out_fp, "-y"])

    if debug:
        print(purple(f"[V] {scene_key} FFmpeg writer command:"), ' '.join(writer_command))


    # Open subprocess
    writer_subproces: subprocess.Popen = None
    try:
        writer_subproces = subprocess.Popen(
            writer_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except Exception as e:
        print(red(f"[E][W] {scene_key} Unexpected error: {type(e)}"))
        return False

    # Read stdin, replace and write to stdout
    replacements = scene['replace']
    frames_to_replace: list[int] = get_frames_to_remove(replacements)
    frames_to_cache: deque[int] = get_frames_to_cache(replacements)

    img_cache: ImageCache = ImageCache()
    img_cache.set_occurences(frame_occurences(replacements))
    # Do not cache images that are replaced
    img_cache.set_exceptions(frames_to_replace)

    if debug:
        print(lightgreen("Frames to cache: "), deepcopy(list(frames_to_cache)))


    frame_to_cache: int = frames_to_cache.popleft()
    in_f_no: int = scene['src']['start']
    out_f_nos: deque[int] = deque(scene['out_frames'])
    _out_f_nos: list[int] = []
    out_f_no: int = out_f_nos.popleft()
    frame_to_replace: int = frames_to_replace[0]

    def _read_frame() -> np.ndarray:
        frame = reader_subproces.stdout.read(in_frame_nbytes)
        if len(frame) < in_frame_nbytes:
            raise ValueError(red(f"[E][R] {scene_key} Unexpected error: frame size < {in_frame_nbytes}"))
        return frame


    to_produce: int = len(scene['out_frames'])
    consumable: int = scene['src']['count']
    out_i: int = 0
    from_cache: bool = False
    while to_produce:
        # print(darkgrey(f"out_f_no: {out_f_no}"))
        frame = None
        from_cache = False

        if out_f_no == frame_to_replace:
            frame_to_use = replacements[out_f_no]
            print(red(f"replace frame no.{frame_to_replace} by {frame_to_use}"))
            if frame_to_use in img_cache:
                print(f"\tuse frame no.{frame_to_use} from cache")
                from_cache = True
                frame = img_cache[frame_to_use]
                try:
                    del frames_to_replace[0]
                    frame_to_replace = frames_to_replace[0]
                except:
                    frame_to_replace = -1
                print(lightcyan(f"next frame to replace: {frame_to_replace}"))
                print(f"\t{yellow(out_f_no)}: push frame {yellow(frame_to_use)} in out_slot")

            else:
                print(f"{frame_to_use} not yet in cache, cannot produce, let's caching")
                # frame_to_find = frame_to_use
                while in_f_no <= frame_to_use and consumable > 0:
                    print(purple(f"Read frame no.{in_f_no} -> to cache"))
                    img_cache.add(in_f_no, _read_frame())
                    in_f_no += 1
                    consumable -= 1

        else:
            if out_f_no in img_cache:
                frame = img_cache[out_f_no]
                from_cache = True

            else:
                from_cache = False
                # print(purple(f"Read frame no.{in_f_no} ({out_f_no} not in cache)"))
                frame = _read_frame()

                if in_f_no == frame_to_cache:
                    # print(lightgreen(f"\tput frame {in_f_no} in cache"))
                    # Put this image in the cache as it will be later used
                    img_cache.add(in_f_no, frame, bool(in_f_no > out_f_no))
                    try:
                        frame_to_cache = frames_to_cache.popleft()
                    except:
                        pass
                    # print(lightcyan(f"next frame to cache: {frame_to_cache}"))
                elif in_f_no in frames_to_replace:
                    frame = None

                in_f_no += 1
                consumable -= 1

        if frame is not None:
            # print(yellow(f"\t{out_i}: send {out_f_no} (from {'cache' if from_cache else 'producer'})"))
            out_i += 1
            writer_subproces.stdin.write(frame)
            to_produce -= 1
            _out_f_nos.append(out_f_no)
            if not to_produce:
                break
            out_f_no = out_f_nos.popleft()

    # Verify output list
    if _out_f_nos == scene['out_frames']:
        if debug:
            print(lightgreen(f"{scene_key} Valid"))
    else:
        no: int = 0
        for i, j in zip(_out_f_nos, scene['out_frames']):
            if i != j:
                print(f"{no}: {i}, must be {j}")
            no += 1
        print(red(f"[E] {scene_key} Output frame numbers don't match, {len(scene['out_frames'])} -> {len(_out_f_nos)}"))
        return False

    # Wait for the end of the encoding
    if writer_subproces is not None:
        stderr_bytes: bytes | None = None
        try:
            # Arbitrary timeout value
            _, stderr_bytes = writer_subproces.communicate(timeout=10)
        except:
            writer_subproces.kill()
            pass
        if stderr_bytes is not None:
            stderr = stderr_bytes.decode('utf-8)')
            # TODO: parse the output file
            if stderr != '':
                print(f"{scene_key} stderr:")
                pprint(stderr)

    return True



def _add_borders_to_scene(
    scene: Scene,
    video_info: VideoInfo,
    debug: bool = False
) -> bool:
    src_scene: SrcScene = scene['src']
    scene_key: str = f"{src_scene['k_ed']}:{src_scene['k_ep']}:{src_scene['k_ch']}:{src_scene['k_ch']}"
    vsettings: VideoSettings = scene['task'].video_settings
    filter_complex: list[str] = _get_complex_filter(scene)

    add_border_command: list[str] = [
        ffmpeg_exe,
        "-hide_banner",
        "-loglevel", "warning",
        "-nostats",
        "-i", scene['task'].in_video_file,
        *filter_complex,
        "-vcodec", str_to_video_codec[vsettings.codec].value,
        "-pix_fmt", vsettings.pix_fmt,
        *vsettings.codec_options
    ]

    # Add metadata
    add_border_command.extend(["-movflags", "use_metadata_tags"])
    for metadata in (video_info['metadata'], vsettings.metadata):
        if len(metadata.keys()):
            for k, bpp in metadata.items():
                add_border_command.extend(["-metadata:s:v:0", f"{k}={bpp}"])

    # Output filename
    add_border_command.extend([scene['task'].video_file, "-y"])

    if debug:
        print(lightgreen(f"[V] FFmpeg command (add border):"), ' '.join(add_border_command))

    try:
        add_border_subprocess = subprocess.Popen(
            add_border_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except Exception as e:
        print(red(f"[E][W] {scene_key} Unexpected error: {type(e)}"))
        return False

    stderr_bytes: bytes | None = None
    try:
        # Arbitrary timeout value
        _, stderr_bytes = add_border_subprocess.communicate()
    except:
        add_border_subprocess.kill()
        pass
    if stderr_bytes is not None:
        stderr = stderr_bytes.decode('utf-8)')
        # TODO: parse the output file
        if stderr != '':
            print(f"{scene_key} stderr:")
            pprint(stderr)
            return False

    return True

