from concurrent.futures import ThreadPoolExecutor
import math
import multiprocessing as mp
from multiprocessing import Lock
import os
from pprint import pprint
import subprocess
import sys
import time
import numpy as np
from nn_inference.toolbox.detect_inner_rect import DetectInnerRectParams, detect_inner_rect
from parsers import (
    db,
    get_fps,
    VideoSettings,
    TaskName,
)
from processing.effects import apply_effect
from processing.frame_replace import ItemCache, frame_occurences, get_frames_to_remove
from processing.watermark import add_watermark
from scene.filters import do_watermark
from utils.logger import main_logger
from utils.mco_types import ChapterVideo, McoFrame, Scene
from utils.mco_utils import (
    calculate_frame_count,
    get_target_video,
    is_first_scene,
    is_last_scene,
    is_up_to_date
)
from utils.p_print import *
from utils.path_utils import absolute_path, path_split
from utils.pxl_fmt import PIXEL_FORMAT
from utils.time_conversions import FrameRate, frame_to_s, frame_to_sexagesimal
from utils.tools import ffmpeg_exe
from utils.media import VideoInfo, extract_media_info, str_to_video_codec



def stdin_to_shared(
    i: int,
    in_size: int,
    in_dtype: np.dtype,
    img_shape: tuple[int],
    img_dtype: np.dtype,
    max_value: float,
    ffmpeg_subprocess: subprocess.Popen,
    lock_array: list[mp.Lock]
) -> bool:
    with lock_array[i]:
        stream = ffmpeg_subprocess.stdout.read(in_size)
        lock_array[i+1].release()
    img = np.frombuffer(stream, dtype=in_dtype).reshape(img_shape)
    if in_dtype != img_dtype:
        img = img.astype(img_dtype)
        if max_value != 1.:
            img /= max_value
    return img



def get_output_video_filepath(scene: Scene, task_name: TaskName | None = None) -> str:
    if task_name is None:
        task_name = scene['task'].name

    k_ep: str = scene['dst']['k_ep']
    k_ch: str = scene['dst']['k_ch']
    primary_src_scene = scene['src'].primary_scene()

    _k_ed, _k_ep = primary_src_scene['k_ed_ep_ch_no'][:2]
    if k_ch in ('g_debut', 'g_fin'):
        cache_path: str = db[k_ch]['cache_path']
        basename = f"{k_ch}_{scene['no']:03}__{_k_ed}_{_k_ep}"
    else:
        cache_path: str = db[k_ep]['cache_path']
        basename = f"{k_ep}_{k_ch}_{scene['no']:03}__{_k_ed}"

    suffix = f"_{scene['task'].hashcode}"
    suffix += f"_{task_name}"

    return absolute_path(
        os.path.join(
            cache_path,
            f"scenes_{task_name}",
            f"{basename}{suffix}.mkv"
        )
    )



def generate_final_scene(scene: Scene, force: bool = False) -> bool:
    scene_key: str = f"{scene['dst']['k_ep']}:{scene['dst']['k_ch']}:{scene['no']}"
    out_video_fp: str = scene['task'].video_file

    if is_up_to_date(scene) and not force:
        return True

    # Output directory
    final_directory: str = path_split(scene['task'].video_file)[0]
    os.makedirs(final_directory, exist_ok=True)

    # Input video clip
    in_video_fp: str = get_output_video_filepath(scene, task_name='restored')
    if not os.path.exists(in_video_fp):
        raise FileExistsError(red(f"{in_video_fp}: No such file or directory"))
    in_video_info: VideoInfo = extract_media_info(in_video_fp)['video']
    in_shape = in_video_info['shape']
    h, w = in_shape[:2]
    in_pipe_dtype: np.dtype = np.uint8
    in_pipe_pixfmt: str = 'bgr24'
    in_pipe_nbytes: int = math.prod(in_shape)
    if PIXEL_FORMAT[in_video_info['pix_fmt']]['bpp'] > 8:
        in_pipe_dtype = np.uint16
        in_pipe_pixfmt = 'bgr48'
        in_pipe_nbytes: int = 2 * math.prod(in_shape)

    # Output video
    out_video_fp: str = get_output_video_filepath(scene)
    vsettings: VideoSettings = scene['task'].video_settings
    out_pipe_dtype: np.dtype = np.uint8
    out_pipe_pixfmt: str = 'bgr24'
    if PIXEL_FORMAT[vsettings.pix_fmt]['bpp'] > 8:
        out_pipe_dtype = np.uint16
        out_pipe_pixfmt = 'bgr48'


    print(f"IN: video file: {in_video_fp}")
    print(f"IN: frame_count: {in_video_info['frame_count']}")
    print(f"IN: dimensions: {w}x{h}")
    print(f"IN: pixfmt: {in_video_info['pix_fmt']}")
    print(f"IN: pipe dtype: {in_pipe_dtype}")
    print(f"IN: pipe pixfmt: {in_pipe_pixfmt}")
    print(f"IN: pipe nbytes: {in_pipe_nbytes}")

    print(f"OUT: video file: {out_video_fp}")
    print(f"OUT: pixfmt: {vsettings.pix_fmt}")
    print(f"OUT: pipe dtype: {out_pipe_dtype}")
    print(f"OUT: pipe pixfmt: {out_pipe_pixfmt}")


    print(f"DST: frame_count: {scene['dst']['count']}")

    if scene['dst']['count'] != in_video_info['frame_count']:
        raise ValueError(red(
            f"[E] Erroneous frame count, waiting {scene['dst']['count']} but video has {in_video_info['frame_count']}"
        ))

    start_time: int = time.time()

    # Decoder
    d_command: list[str] = [
        ffmpeg_exe,
        "-hide_banner",
        "-loglevel", "warning",
        "-nostats",
        "-i", in_video_fp,

        "-f", "image2pipe",
        "-pix_fmt", in_pipe_pixfmt,
        "-vcodec", "rawvideo",
        "-"
    ]
    decoder_subprocess: subprocess.Popen = None
    try:
        decoder_subprocess = subprocess.Popen(
            d_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except Exception as e:
        print(red(f"[E][W] {scene_key} Unexpected error: {type(e)}"))
        return False


    ofc: int = int(3 * mp.cpu_count() / 4)
    locks = [mp.Lock() for _ in range(ofc + 1)]
    executor = ThreadPoolExecutor(max_workers=ofc, thread_name_prefix='mco')

    # Extract all images
    remaining: int = scene['dst']['count']
    in_images: list[np.ndarray] = []
    write_index : int = 0
    while remaining > 0:
        count = min(remaining, ofc)

        for l in locks:
            l.acquire(block=False)
        locks[0].release()
        for img in executor.map(
            lambda i: stdin_to_shared(
                i,
                in_pipe_nbytes,
                in_pipe_dtype,
                in_shape,
                in_pipe_dtype,
                1,
                decoder_subprocess,
                locks
            ),
            range(count)
        ):
            in_images.append(img)

        remaining -= count
        write_index += count

    # print(len(in_images))
    # for img in in_images:
    #     print(img.shape)
    # Detect inner rect -> returns coordinates
    #   poolexecutor
    detect_inner_rect_params = DetectInnerRectParams()

    coordinates: list[np.ndarray] = []

    for coords, out_img in executor.map(
        lambda args:
            detect_inner_rect(*args),
            [(img, detect_inner_rect_params) for img in in_images]
        ):
            coordinates.append(coords)

    # pprint(coordinates)

    # Get min rectangle of coordinates
    x0, y0 = np.min(coordinates, axis=0)[:2]
    x1, y1 = np.max(coordinates, axis=0)[2:]
    final_coords = np.array((x0, x1, y0, y1))

    elapsed_time = time.time() - start_time

    print(yellow("final:"))
    pprint(final_coords)
    print(f"executed in {elapsed_time:.02f}s ({scene['dst']['count']/elapsed_time:1}fps)")

    # Crop every image
    # Resize to 1080p (pil resize)
    # Add borders
    #   poolexecutor


    # Effects

    # Send all images to pipe out


    sys.exit()
