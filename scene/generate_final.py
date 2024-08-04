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
from nn_inference.toolbox.resize_to_4_3 import ConvertTo43Params, calculate_transformation_values, resize_to_4_3
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
    is_up_to_date,
    run_simple_command
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
    detect_inner_rect_params,
    lock_array: list[mp.Lock],
    debug: bool = False
) -> tuple[np.ndarray, np.ndarray, np.ndarray | None]:
    with lock_array[i]:
        stream = ffmpeg_subprocess.stdout.read(in_size)
        lock_array[i+1].release()
    img = np.frombuffer(stream, dtype=in_dtype).reshape(img_shape)
    if in_dtype != img_dtype:
        img = img.astype(img_dtype)
        if max_value != 1.:
            img /= max_value

    coords, out_img = detect_inner_rect(
        img,
        detect_inner_rect_params,
        do_output_img=debug
    )
    return img, coords, out_img



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
    in_h, in_w = in_shape[:2]
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
    print(f"IN: dimensions: {in_w}x{in_h}")
    print(f"IN: pixfmt: {in_video_info['pix_fmt']}")
    print(f"IN: pipe dtype: {in_pipe_dtype}")
    print(f"IN: pipe pixfmt: {in_pipe_pixfmt}")
    print(f"IN: pipe nbytes: {in_pipe_nbytes}")

    img_dtype = np.uint8

    print(f"OUT: video file: {out_video_fp}")
    print(f"OUT: pixfmt: {vsettings.pix_fmt}")
    print(f"OUT: pipe dtype: {out_pipe_dtype}")
    print(f"OUT: pipe pixfmt: {out_pipe_pixfmt}")


    print(f"DST: frame_count: {scene['dst']['count']}")

    ch_width = 1412
    out_h, out_w = 1080, 1440
    print(f"chapter: width: {ch_width}")
    print(f"final dimension: {out_w}x{out_h}")
    detect_inner_rect_params = DetectInnerRectParams(
        threshold_min=25,
        morph_kernel_radius=1,
        erode_kernel_radius=2,
        erode_iterations=2,
        do_add_borders=True,
    )




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


    coordinates: list[np.ndarray] = []

    ofc: int = int(3 * mp.cpu_count() / 4)
    locks = [mp.Lock() for _ in range(ofc + 1)]
    executor = ThreadPoolExecutor(max_workers=ofc, thread_name_prefix='mco')


    # Extract all images
    remaining: int = scene['dst']['count']
    in_images: list[np.ndarray] = []
    write_index : int = 0
    debug_img: list[np.ndarray] = []
    while remaining > 0:
        count = min(remaining, ofc)

        for l in locks:
            l.acquire(block=False)
        locks[0].release()
        for img, coords, out_img in executor.map(
            lambda i: stdin_to_shared(
                i,
                in_pipe_nbytes,
                in_pipe_dtype,
                in_shape,
                img_dtype,
                1,
                decoder_subprocess,
                detect_inner_rect_params,
                locks,
                debug=True
            ),
            range(count)
        ):
            in_images.append(img)
            if coords is not None:
                coordinates.append(coords)
                debug_img.append(out_img)
            else:
                debug_img.append(img)

        remaining -= count
        write_index += count

    # Get min rectangle of coordinates
    x0, x1 = np.min(coordinates, axis=0)[:2]
    y0, y1 = np.max(coordinates, axis=0)[2:]

    elapsed_time = time.time() - start_time

    print(yellow("final:"))
    print(f"({x0}, {y0}) -> ({x1}, {y1})")
    print(f"executed in {elapsed_time:.02f}s ({scene['dst']['count']/elapsed_time:1}fps)")

    to_43_params: ConvertTo43Params = ConvertTo43Params(
        # [top, bottom, left, right]
        crop=(y0, in_h - y1, x0, in_w - x1),
        keep_ratio=True,
        fit_to_width=False,
        final_height=out_h,
        scene_width=ch_width
    )
    pprint(to_43_params)
    transformation = calculate_transformation_values(
        in_w=in_w,
        in_h=in_h,
        out_w=out_w,
        params=to_43_params,
        verbose=True
    )


    # Draw rectangle
    print(f"debug: {in_w}x{in_h}")
    debug_command: list[str] = [
        ffmpeg_exe,
        "-hide_banner",
        "-loglevel", "warning",
        "-nostats",

        "-f", "rawvideo",
        '-pixel_format', out_pipe_pixfmt,
        '-video_size', f"{in_w}x{in_h}",
        "-r", "25",
        "-i", "pipe:0",
        "-pix_fmt", "yuv420p",
        "-vcodec", "libx264",
        *vsettings.codec_options,
        "-y", out_video_fp.replace('.mkv', '_debug.mkv')
    ]
    debug_subproces: subprocess.Popen = None
    try:
        debug_subproces = subprocess.Popen(
            debug_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except Exception as e:
        print(red(f"[E][W] {scene_key} Unexpected error: {type(e)}"))
        return False
    for img in debug_img:
        debug_subproces.stdin.write(img)
    stderr_bytes: bytes | None = None
    _, stderr_bytes = debug_subproces.communicate(timeout=10)
    if stderr_bytes is not None:
        stderr = stderr_bytes.decode('utf-8)')
        # TODO: parse the output file
        if stderr != '':
            print(f"{scene_key} stderr:")
            pprint(stderr)



    # Note: this could have be done with FFmpeg filter but as sson
    # as some effects could be used (loop, fade in, fadeout)
    if (
        ('effects' not in scene.keys() or not scene['effects'].has_effects())
        # and False
    ):
        filters: list[str] = []

        # (1)
        w1, h1 = x1 - x0, y1 - y0
        filters.append(f"crop={w1}:{h1}:{x0}:{y0}")

        # (2)
        w2, h2 = transformation.resize_to
        interpolation_alg: str = (
            'lanczos' if w2 > w1 or h2 > h1
            else 'bicubic'
        )
        filters.append(
            f"""scale={w2}:{h2}:sws_flags={interpolation_alg}
                + full_chroma_int
                + full_chroma_inp
                + accurate_rnd
                + bitexact
            """
        )

        # (3)
        crop_2 = transformation.crop_2
        if crop_2 is not None:
            top, bottom, left, right = crop_2
            filters.append(
                f"""crop=
                    {w2 - (left + right)}:{h2 - (top + bottom)}
                    :{left}:{top}
                """
            )

        # Erroneous geometry: add white borders
        err_borders = transformation.err_borders
        if err_borders is not None:
            filters.append(
                f"""pad=
                    {w2 + err_borders[2] + err_borders[3]}
                    :{h2 + err_borders[0] + err_borders[1]}
                    :{err_borders[2]}:{err_borders[0]}
                    :green
                """
            )

        # (4)
        if transformation.borders[0] != 0:
            filters.append(
                f"""pad=
                    {transformation.out_size[0]}:{transformation.out_size[1]}
                    :{transformation.borders[0]}:0
                """
            )

        filter_complex: str = ','.join(filters)
        for c in (' ', '\n', '\r', '\t'):
            filter_complex = filter_complex.replace(c, '')

        ffmpeg_filter: list[str] = [
            "-filter_complex",
            f"[0:v]{filter_complex}[outv]",
            "-map", "[outv]"
        ]

        encoder_command: list[str] = [
            ffmpeg_exe,
            "-hide_banner",
            "-loglevel", "warning",
            "-nostats",
            "-i", in_video_fp,
            *ffmpeg_filter,

            "-vcodec", str_to_video_codec[vsettings.codec].value,
            "-pix_fmt", vsettings.pix_fmt,
            *vsettings.codec_options
        ]

        # Add metadata
        encoder_command.extend(["-movflags", "use_metadata_tags"])
        if len(vsettings.metadata.keys()):
            for k, v in vsettings.metadata.items():
                encoder_command.extend(["-metadata:s:v:0", f"{k}={v}"])

        # Output filename
        encoder_command.extend([out_video_fp, "-y"])

        os.makedirs(path_split(out_video_fp)[0], exist_ok=True)
        print(purple(f"[V] command: "), " ".join(encoder_command))
        run_simple_command(encoder_command)

    else:
        out_imgs: list[np.ndarray] = [
            resize_to_4_3(img, transformation=transformation)
            for img in in_images
        ]

        print(len(out_imgs))
        print(out_imgs[0].shape)



    # Effects

    # Send all images to pipe out


    sys.exit()
