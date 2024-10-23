from collections.abc import Callable, Iterable, Mapping
from concurrent.futures import ThreadPoolExecutor
import math
import multiprocessing as mp
from multiprocessing import Lock
import os
from pprint import pprint
from queue import Queue
import subprocess
import sys
from threading import Thread
import time
from typing import IO, Any
from PIL import Image
import cv2
import numpy as np
from processing.detect_inner_rect import detect_inner_rect
from processing.resize_to_4_3 import ConvertTo43Params, TransformationValues, calculate_transformation_values, resize_to_4_3
from parsers import (
    FINAL_WIDTH,
    TASK_NAMES,
    ColorSettings,
    db,
    ProcessingTask,
    SceneGeometry,
    TaskName,
    VideoSettings,
    FINAL_HEIGHT,
)
from processing.effects import apply_effect
from utils.logger import main_logger
from utils.mco_types import McoFrame, Scene, ChapterVideo
from utils.mco_utils import (
    calculate_frame_count,
    ffmpeg_metadata,
    get_target_video,
    is_first_scene,
    is_last_scene,
    run_simple_command
)
from utils.np_dtypes import np_to_float32, np_to_uint16, np_to_uint8
from utils.p_print import *
from utils.path_utils import absolute_path, path_split
from utils.pxl_fmt import PIXEL_FORMAT
from utils.tools import ffmpeg_exe
from utils.media import VideoInfo, extract_media_info, str_to_video_codec, vcodec_to_extension




def decode(
    i: int,
    in_size: int,
    in_pipe_dtype: np.dtype,
    in_pipe_shape: tuple[int],
    out_pipe_dtype: np.dtype,
    multiplier: float,
    ffmpeg_subprocess: subprocess.Popen,
    lock_array: list[mp.Lock],
) -> tuple[np.ndarray, np.ndarray, np.ndarray | None]:
    with lock_array[i]:
        stream = ffmpeg_subprocess.stdout.read(in_size)
        lock_array[i+1].release()
    img = np.frombuffer(stream, dtype=in_pipe_dtype).reshape(in_pipe_shape)
    in_img: np.ndarray = img
    # print(f"convert: {in_pipe_dtype} -> {out_pipe_dtype} ({multiplier})")
    if in_pipe_dtype != out_pipe_dtype:
        if multiplier > 1:
            in_img = img.astype(out_pipe_dtype)
            in_img *= multiplier
        elif multiplier < 1:
            in_img = img * multiplier
            in_img = in_img.astype(out_pipe_dtype)
    return in_img


def decode_and_ac_detect(
    i: int,
    in_size: int,
    in_pipe_dtype: np.dtype,
    in_pipe_shape: tuple[int],
    out_pipe_dtype: np.dtype,
    multiplier: float,
    ffmpeg_subprocess: subprocess.Popen,
    detect_params,
    lock_array: list[mp.Lock],
    debug: bool = False
) -> tuple[np.ndarray, np.ndarray, np.ndarray | None]:
    with lock_array[i]:
        stream = ffmpeg_subprocess.stdout.read(in_size)
        lock_array[i+1].release()
    img = np.frombuffer(stream, dtype=in_pipe_dtype).reshape(in_pipe_shape)
    in_img: np.ndarray = img
    # print(f"convert: {in_pipe_dtype} -> {out_pipe_dtype} ({multiplier})")
    if in_pipe_dtype != out_pipe_dtype:
        if multiplier > 1:
            in_img = img.astype(out_pipe_dtype)
            in_img *= multiplier
        elif multiplier < 1:
            in_img = img * multiplier
            in_img = in_img.astype(out_pipe_dtype)

    coords, debug_img = detect_inner_rect(
        in_img,
        detect_params,
        do_output_img=debug
    )
    # print(f"stdin_to_shared: {in_img.shape}, {in_pipe_dtype} -> {in_img.dtype}")
    return in_img, coords, debug_img




def resize_and_effects(
    i: int,
    in_img: np.ndarray,
    scene: Scene,
    transformation,
    convert_fct: Callable,
) -> list[np.ndarray]:
    img: np.ndarray = resize_to_4_3(
        np_to_float32(in_img), transformation
    )
    out_f_no: int = scene['src'].first_frame_no() + i
    out_frame = McoFrame(no=out_f_no, img=img, scene=scene)
    out_frames: list[McoFrame] | McoFrame = apply_effect(
        out_f_no=out_f_no,
        frame=out_frame,
        out_i=i
    )

    if isinstance(out_frames, list):
        out_frames: list[McoFrame]
        return list([convert_fct(f.img)for f in out_frames])
    else:
        out_frames: McoFrame
        return [convert_fct(out_frames.img)]




def generate_final_scene(
    scene: Scene,
    force: bool = False,
    debug: bool = False,
) -> bool:
    debug_scene: bool = False

    scene_key: str = f"{scene['dst']['k_ep']}:{scene['dst']['k_ch']}:{scene['no']}"
    task: ProcessingTask = scene['task']

    in_video_fp: str = task.in_video_file
    out_video_fp: str = task.video_file

    # Output directory
    final_directory: str = path_split(out_video_fp)[0]
    os.makedirs(final_directory, exist_ok=True)

    # Output video
    vsettings: VideoSettings = task.video_settings
    out_pipe_dtype: np.dtype = np.uint8
    out_pipe_pixfmt: str = 'bgr24'
    if PIXEL_FORMAT[vsettings.pix_fmt]['bpp'] > 8:
        out_pipe_dtype = np.uint16
        out_pipe_pixfmt = 'bgr48'

    # Input video scenes
    in_video_info: VideoInfo = extract_media_info(in_video_fp)['video']
    in_pipe_shape = in_video_info['shape']
    in_h, in_w = in_pipe_shape[:2]
    in_pipe_dtype: np.dtype = out_pipe_dtype
    in_pipe_pixfmt: str = out_pipe_pixfmt
    in_pipe_nbytes: int = math.prod(in_pipe_shape)
    # if PIXEL_FORMAT[in_video_info['pix_fmt']]['bpp'] > 8:
    #     in_pipe_dtype = np.uint16
    #     in_pipe_pixfmt = 'bgr48'
    #     in_pipe_nbytes: int = 2 * math.prod(in_pipe_shape)

    print(lightcyan(f"Input:"))
    print(f"  video file: {in_video_fp}")
    print(f"  frame_count: {in_video_info['frame_count']}")
    print(f"  dimensions: {in_w}x{in_h}")
    print(f"  pixfmt: {in_video_info['pix_fmt']}")
    print(f"  pipe dtype: {in_pipe_dtype}")
    print(f"  pipe pixfmt: {in_pipe_pixfmt}")
    print(f"  pipe nbytes: {in_pipe_nbytes}")

    print(lightcyan(f"Output:"))
    print(f"  video file: {out_video_fp}")
    print(f"  pixfmt: {vsettings.pix_fmt}")
    print(f"  pipe dtype: {out_pipe_dtype}")
    print(f"  pipe pixfmt: {out_pipe_pixfmt}")


    print(lightcyan(f"Processing:"))
    print(f"  frame_count: {scene['dst']['count']}")
    if in_video_info['frame_count'] < scene['dst']['count']:
        raise ValueError(red(
            f"[E] Erroneous frame count, waiting {scene['dst']['count']} but video has {in_video_info['frame_count']} ({in_video_fp})"
        ))

    # Scene geometry
    geometry: SceneGeometry = scene['geometry']
    geometry.set_in_size(in_pipe_shape[:2])
    ch_width = geometry.chapter.width
    out_h, out_w = FINAL_HEIGHT, FINAL_WIDTH
    print(f"  chapter width: {ch_width}")
    print(f"  final dimension: {out_w}x{out_h}")
    debug_imgs: list[np.ndarray] = []

    has_effects: bool = (
        'effects' in scene.keys()
        and scene['effects'].has_effects()
    )

    # if geometry.use_autocrop and has_effects:
    vsettings: VideoSettings = task.video_settings
    do_decode: bool = (
        (
            geometry.use_autocrop
            and any([c <= vsettings.pad for c in geometry.autocrop])
        )
        or has_effects
    )

    if do_decode:
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

        print(purple(f"[V] Decoder"), ' '.join(d_command))
        d_subprocess: subprocess.Popen = None
        try:
            d_subprocess = subprocess.Popen(
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

        # Change pixel value range
        # Normalize pixel range
        multiplier: float = 1.
        if in_pipe_dtype != out_pipe_dtype:
            num = float(np.iinfo(out_pipe_dtype).max)
            denum = float(np.iinfo(in_pipe_dtype).max)
            multiplier: float = num / denum
            print(f"multiplier: {multiplier}")

        # Extract all images
        remaining: int = scene['dst']['count']
        in_images: list[np.ndarray] = []
        write_index : int = 0

        start_time: int = time.time()
        if geometry.use_autocrop:
            pprint(geometry.detection_params)
            debug_imgs: list[np.ndarray] = []
            while remaining > 0:
                count = min(remaining, ofc)
                for l in locks:
                    l.acquire(block=False)
                locks[0].release()
                for img, coords, debug_img in executor.map(
                    lambda i: decode_and_ac_detect(
                        i,
                        in_pipe_nbytes,
                        in_pipe_dtype,
                        in_pipe_shape,
                        out_pipe_dtype,
                        multiplier,
                        d_subprocess,
                        geometry.detection_params,
                        locks,
                        debug=debug_scene
                    ),
                    range(count)
                ):
                    in_images.append(img)
                    if coords is not None:
                        coordinates.append(coords)
                        # if filtered_coord(coordinates, coords):
                        #     coordinates.append(coords)
                        # else:
                        #     print(f"not valid coords: {coords}")
                    if debug_img is not None:
                        debug_imgs.append(debug_img)
                remaining -= count
                write_index += count
            pprint(coordinates)
            print("  min:", np.min(coordinates, axis=0))
            print("  max:", np.max(coordinates, axis=0))
            min_coords: np.ndarray = np.min(coordinates, axis=0)
            max_coords: np.ndarray = np.max(coordinates, axis=0)
            x0, x1 = max_coords[0], min_coords[1]
            y0, y1 = max_coords[2], min_coords[3]
            autocrop = [y0,  in_h - y1, x0, in_w - x1]

            elapsed_time = time.time() - start_time
            print(yellow("geometry, autocrop:"), f"{geometry.autocrop}")
            print(yellow("final, autocrop:"), f"{autocrop}")


            print(f"read/autocrop in {elapsed_time:.02f}s ({scene['dst']['count']/elapsed_time:.1f}fps)")
            geometry.autocrop = autocrop

        else:
            while remaining > 0:
                count = min(remaining, ofc)
                for l in locks:
                    l.acquire(block=False)
                locks[0].release()
                for img in executor.map(
                    lambda i: decode(
                        i,
                        in_pipe_nbytes,
                        in_pipe_dtype,
                        in_pipe_shape,
                        out_pipe_dtype,
                        multiplier,
                        d_subprocess,
                        locks,
                    ),
                    range(count)
                ):
                    in_images.append(img)
                remaining -= count
                write_index += count


    # Geometry transformations
    transformation: TransformationValues = geometry.calculate_transformation()
    pprint(transformation)
    if transformation.err_borders is not None:
        raise ValueError(red("Erroneous chapter width"))
    # Create a video file for debug
    if debug and debug_imgs:
        # Draw rectangle
        print(f"debug: {in_w}x{in_h}, {len(debug_imgs)} images")
        debug_command: list[str] = [
            ffmpeg_exe,
            "-hide_banner",
            "-loglevel", "warning",
            "-nostats",

            "-f", "rawvideo",
            '-pixel_format', 'bgr24',
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
        for img in debug_imgs:
            debug_subproces.stdin.write(img)
        stderr_bytes: bytes | None = None
        _, stderr_bytes = debug_subproces.communicate(timeout=10)
        if stderr_bytes is not None:
            stderr = stderr_bytes.decode('utf-8)')
            # TODO: parse the output file
            if stderr != '':
                print(f"{scene_key} stderr:")
                pprint(stderr)

    # Colorspace, output is x264 so it's working like that
    colorspace: list[str] = []
    for k, v in ColorSettings().__dict__.items():
        colorspace.extend([f"-{k}:v", v])

    # Metadata
    metadata: list[str] = ffmpeg_metadata(scene)

    # Note: this could have be done with FFmpeg filter but as sson
    # as some effects could be used (loop, fade in, fadeout)
    ch_video: ChapterVideo = get_target_video(scene)
    if is_first_scene(scene):
        print(lightcyan("first scene, avsync:"), ch_video['avsync'])
        if ch_video['avsync'] != 0:
            raise NotImplementedError("avsync not yet supported")

    if not has_effects:
        print(f"{scene_key}: no effects, use FFmpeg to apply the final geometry")
        filters: list[str] = []

        # (1)
        c_t, c_b, c_l, c_r = transformation.crop
        w1, h1 = in_w - (c_l + c_r), in_h - (c_t + c_b)
        filters.append(f"crop={w1}:{h1}:{c_l}:{c_t}")

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
            f"[0:v]{filter_complex},setdar=4/3[outv]",
            "-map", "[outv]"
        ]

        e_command: list[str] = [
            ffmpeg_exe,
            "-hide_banner",
            "-loglevel", "warning",
            "-nostats",
            "-i", in_video_fp,
            *ffmpeg_filter,

            "-vcodec", str_to_video_codec[vsettings.codec].value,
            "-pix_fmt", vsettings.pix_fmt,
            *vsettings.codec_options,
            *colorspace,
            *metadata,
            out_video_fp, "-y"
        ]

        os.makedirs(path_split(out_video_fp)[0], exist_ok=True)
        print(purple(f"[V] command: "), " ".join(e_command))
        run_simple_command(e_command)

    else:
        print(f"{scene_key} has effects")
        # out_imgs: list[np.ndarray] = []
        # for out_img in executor.map(
        #     lambda img: resize_to_4_3(img, transformation), in_images
        # ):
        #     out_imgs.append(out_img)
        # print(len(out_imgs))
        # print(out_imgs[0].shape)

        in_pipe_shape = in_pipe_shape
        in_pipe_dtype: np.dtype = np.uint16 if in_video_info['bpp'] > 8 else np.uint8
        in_pipe_pixfmt: str = 'bgr24' if in_pipe_dtype == np.uint8 else 'bgr48le'
        in_pipe_nbytes: int = math.prod(in_pipe_shape) * np.dtype(in_pipe_dtype).itemsize
        print(purple("Decoder:"))
        print(f"  shape: {in_pipe_shape}")
        print(f"  dtype: {in_pipe_dtype}")
        print(f"  pixfmt: {in_pipe_pixfmt}")
        print(f"  nbytes: {in_pipe_nbytes}")

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
        print(lightcyan(f"  command:"), ' '.join(d_command))
        d_subprocess: subprocess.Popen = None
        try:
            d_subprocess = subprocess.Popen(
                d_command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except Exception as e:
            print(red(f"[E][W] {scene_key} Unexpected error: {type(e)}"))
            return False


        e_command: list[str] = [
            ffmpeg_exe,
            "-hide_banner",
            "-loglevel", "warning",
            "-nostats",

            "-f", "rawvideo",
            '-pixel_format', in_pipe_pixfmt,
            '-video_size', f"{out_w}x{out_h}",
            "-r", str(vsettings.frame_rate),

            "-i", "pipe:0",

            "-vcodec", str_to_video_codec[vsettings.codec].value,
            "-pix_fmt", vsettings.pix_fmt,
            *vsettings.codec_options,
            *colorspace,
            *metadata,
            out_video_fp, "-y"
        ]


        # Output filename
        os.makedirs(path_split(out_video_fp)[0], exist_ok=True)
        print(purple(f"[V] Encoder: "), " ".join(e_command))

        e_subprocess: subprocess.Popen = None
        try:
            e_subprocess = subprocess.Popen(
                e_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        except Exception as e:
            print(red(f"[E][W] {scene_key} Unexpected error: {type(e)}"))
            return False

        produced: int = 0

        in_frame_count: int = in_video_info['frame_count']
        convert_fct = np_to_uint16 if in_pipe_dtype == np.uint16 else np_to_uint8

        start_time: int = time.time()
        remaining: int = in_frame_count
        ofc: int = min(in_frame_count, int(3 * mp.cpu_count() / 4))
        executor = ThreadPoolExecutor(max_workers=ofc, thread_name_prefix='mco')



        def _d_thread(stream: IO, d_queue: Queue):
            try:
                while True:
                    d_queue.put(
                        np.frombuffer(
                            stream.read(in_pipe_nbytes), dtype=in_pipe_dtype
                        ).reshape(in_pipe_shape)
                    )
            except:
                pass

        def _e_thread(stream: IO, e_queue: Queue):
            while True:
                out_img: np.ndarray = e_queue.get()
                if out_img is None:
                    break
                stream.write(out_img)


        d_queue: Queue = Queue(maxsize=ofc)
        e_queue: Queue = Queue(maxsize=ofc * 2)
        d_thread = Thread(target=_d_thread, args=(d_subprocess.stdout, d_queue,))
        e_thread = Thread(target=_e_thread, args=(e_subprocess.stdin, e_queue,))
        d_thread.start()
        e_thread.start()
        decoded: int = 0
        while remaining:
            print(f"{in_frame_count - remaining}/{in_frame_count}", end='\r')

            # Decode by batch
            count = min(ofc, remaining)
            # in_imgs: list[np.ndarray] = list([
            #     np.frombuffer(
            #         d_subprocess.stdout.read(in_pipe_nbytes), dtype=in_pipe_dtype
            #     ).reshape(in_pipe_shape)
            #     for _ in range(count)
            # ])
            in_imgs: list[np.ndarray] = list([d_queue.get() for _ in range(count)])
            remaining -= count
            decoded += count

            # Resize and apply filters
            out_images: list[np.ndarray] = []
            for out in executor.map(
                lambda args: resize_and_effects(*args),
                [(decoded + i, img, scene, transformation, convert_fct)
                for i, img in enumerate(in_imgs)]
            ):
                out_images.extend(out)
            # for i, img in enumerate(in_imgs):
            #     out_images.extend(
            #         resize_and_effects(
            #             decoded + i, img, scene, transformation, convert_fct
            #     )
            # )

            # Send to encoder
            [e_queue.put(out_img) for out_img in out_images]
            # for out_img in out_images:
            #     e_subprocess.stdin.write(out_img)

            produced += len(out_images)


        if is_last_scene(scene):
            if 'silence' in ch_video and ch_video['silence'] > 0:
                img_black = np.zeros((FINAL_HEIGHT, FINAL_WIDTH, 3), dtype=in_pipe_dtype)
                # [e_queue.put(img_black) for _ in range(ch_video['silence'])]
                [e_subprocess.stdin.write(img_black) for _ in range(ch_video['silence'])]
                produced += ch_video['silence']
                print(f"produced w/ silence: {produced}")
        e_queue.put(None)
        e_thread.join()
        elapsed_time = time.time() - start_time
        print(f"produced {produced} frames in {elapsed_time:.02f}s ({scene['dst']['count']/elapsed_time:.1f}fps)")

        stdout_bytes: bytes | None = None
        stdout_bytes, _ = e_subprocess.communicate(timeout=10)
        if stdout_bytes is not None:
            stdout = stdout_bytes.decode('utf-8)')
            # TODO: parse the output file
            if stdout != '':
                print(f"{scene_key} stdout:")
                pprint(stdout)



    return True


def filtered_coord(coordinates: np.ndarray, coords: np.ndarray) -> bool:
    if not coordinates:
        return True

    last_coords: np.ndarray = coordinates[-1]
    # print(f"{last_coords} -> {coords}")
    for lc, c in zip(last_coords, coords):
        if abs(c - lc) > 10:
            print(red(f"not valid: {c}, {lc}"))
            return False
    # print(lightgreen(f"not valid: {c}, {lc}"))
    return True
