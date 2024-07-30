from concurrent.futures import ThreadPoolExecutor
import math
import multiprocessing as mp
from multiprocessing import Lock
import os
from pprint import pprint
import subprocess
import sys
import numpy as np
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
    shared_images: np.ndarray,
    slot_no: int,
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
    shared_images[slot_no][:] = img[:]
    return True



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

    ofc: int = int(3 * mp.cpu_count() / 4)
    locks = [mp.Lock() for _ in range(ofc + 1)]
    executor = ThreadPoolExecutor(max_workers=ofc, thread_name_prefix='decoder')

    # Extract all images
    remaining: int = scene['dst']['count']
    in_images: list[np.ndarray] = [None] * remaining
    write_index : int = 0
    while remaining > 0:
        count = min(remaining, ofc)

        for l in locks:
            l.acquire(block=False)
        locks[0].release()
        for result in executor.map(
            lambda i: stdin_to_shared(
                i,
                in_pipe_nbytes,
                in_pipe_dtype,
                in_shape,
                in_pipe_dtype,
                1,
                decoder_subprocess,
                in_images,
                (write_index + i),
                locks
            ),
            range(count)
        ):
            success = success and result


        remaining -= count
        write_index += count

    # Detect inner rect -> returns coordinates
    #   poolexecutor

    # Get min rectangle of coordinates

    # Crop every image
    # Resize to 1080p (pil resize)
    # Add borders
    #   poolexecutor


    # Effects

    # Send all images to pipe out


    sys.exit()
