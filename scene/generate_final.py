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
    ColorSettings,
    db,
    ProcessingTask,
    TaskName,
    VideoSettings,
)
from processing.effects import apply_effect
from utils.logger import main_logger
from utils.mco_types import McoFrame, Scene, SceneGeometry
from utils.mco_utils import (
    is_up_to_date,
    run_simple_command
)
from utils.p_print import *
from utils.path_utils import absolute_path, path_split
from utils.pxl_fmt import PIXEL_FORMAT
from utils.time_conversions import FrameRate, frame_to_s, frame_to_sexagesimal
from utils.tools import ffmpeg_exe
from utils.media import VideoInfo, extract_media_info, str_to_video_codec, vcodec_to_extension


def stdin_to_shared(
    i: int,
    in_size: int,
    in_pipe_dtype: np.dtype,
    in_pipe_shape: tuple[int],
    out_pipe_dtype: np.dtype,
    multiplier: float,
    ffmpeg_subprocess: subprocess.Popen,
    detect_inner_rect_params,
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
        detect_inner_rect_params,
        do_output_img=debug
    )
    # print(f"stdin_to_shared: {in_img.shape}, {in_pipe_dtype} -> {in_img.dtype}")
    return in_img, coords, debug_img



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

    suffix: str = ""
    if task_name not in ('hr', 'restored'):
        if scene['task'].hashcode != '':
            suffix = f"_{scene['task'].hashcode}"
        suffix += f"_{task_name}"

    pprint(db['common'])
    pprint(scene)
    sys.exit()
    ext: str = vcodec_to_extension['h264']
    return absolute_path(
        os.path.join(
            cache_path,
            f"scenes_{task_name}",
            f"{basename}{suffix}{ext}"
        )
    )



def generate_final_scene(
    scene: Scene,
    force: bool = False,
    debug: bool = False,
    stats: bool = False
) -> bool:
    debug_scene: bool = False

    scene_key: str = f"{scene['dst']['k_ep']}:{scene['dst']['k_ch']}:{scene['no']}"
    task: ProcessingTask =scene['task']
    out_video_fp: str = scene['task'].video_file

    # Output directory
    final_directory: str = path_split(scene['task'].video_file)[0]
    os.makedirs(final_directory, exist_ok=True)


    # In/out files
    in_video_fp: str = scene['task'].in_video_file
    if not os.path.exists(in_video_fp):
        raise FileExistsError(red(f"{in_video_fp}: No such file or directory"))
    out_video_fp: str = scene['task'].video_file

    if (
        os.path.exists(out_video_fp)
        and os.path.getmtime(in_video_fp) < os.path.getmtime(out_video_fp)
        and not force
    ):
        # Already generated
        print("already generated")
        return True

    # Output video
    vsettings: VideoSettings = scene['task'].video_settings
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


    print(f"IN: video file: {in_video_fp}")
    print(f"IN: frame_count: {in_video_info['frame_count']}")
    print(f"IN: dimensions: {in_w}x{in_h}")
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
        if True:
            print(red(
                f"[E] Erroneous frame count, waiting {scene['dst']['count']} but video has {in_video_info['frame_count']}"
            ))
        else:
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


    # Scene geometry
    geometry: SceneGeometry = scene['geometry']
    ch_width = geometry.chapter.width
    out_h, out_w = 1080, 1440
    print(f"chapter: width: {ch_width}")
    print(f"final dimension: {out_w}x{out_h}")

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
    pprint(geometry.detection_params)


    # Extract all images
    remaining: int = scene['dst']['count']
    in_images: list[np.ndarray] = []
    write_index : int = 0
    debug_imgs: list[np.ndarray] = []

    start_time: int = time.time()
    while remaining > 0:
        count = min(remaining, ofc)

        for l in locks:
            l.acquire(block=False)
        locks[0].release()
        for img, coords, debug_img in executor.map(
            lambda i: stdin_to_shared(
                i,
                in_pipe_nbytes,
                in_pipe_dtype,
                in_pipe_shape,
                out_pipe_dtype,
                multiplier,
                decoder_subprocess,
                geometry.detection_params,
                locks,
                debug=debug_scene
            ),
            range(count)
        ):
            in_images.append(img)
            if coords is not None:
                if filtered_coord(coordinates, coords):
                    coordinates.append(coords)
                else:
                    print(f"not valid coords: {coords}")
            if debug_img is not None:
                debug_imgs.append(debug_img)

        remaining -= count
        write_index += count
    elapsed_time = time.time() - start_time

    pprint(coordinates)
    print("min:", np.min(coordinates, axis=0))
    print("max:", np.max(coordinates, axis=0))
    min_coords: np.ndarray = np.min(coordinates, axis=0)
    max_coords: np.ndarray = np.max(coordinates, axis=0)
    x0, x1 = max_coords[0], min_coords[1]
    y0, y1 = max_coords[2], min_coords[3]
    autocrop = [y0,  in_h - y1, x0, in_w - x1]

    print(yellow("final, autocrop:"), f"{autocrop}")
    print(f"read/autocrop in {elapsed_time:.02f}s ({scene['dst']['count']/elapsed_time:.1f}fps)")

    # Update scene parameters for stats
    if stats:
        print("stats")
        return True

    to_43_params: ConvertTo43Params = ConvertTo43Params(
        crop=autocrop if not geometry.use_autocrop else geometry.crop,
        keep_ratio=geometry.keep_ratio,
        fit_to_width=geometry.fit_to_width,
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



    # Colorspace
    colorspace: list[str] = []
    for k, v in ColorSettings().__dict__.items():
        colorspace.extend([f"-{k}:v", v])

    # Note: this could have be done with FFmpeg filter but as sson
    # as some effects could be used (loop, fade in, fadeout)
    if (
        ('effects' not in scene.keys() or not scene['effects'].has_effects())
        # and False
    ):
        print(f"{scene_key}: no effects")
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
            *colorspace,

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
        print(f"{scene_key} has effects")
        out_imgs: list[np.ndarray] = [
            resize_to_4_3(img, transformation=transformation)
            for img in in_images
        ]
        print(len(out_imgs))
        print(out_imgs[0].shape)

        encoder_command: list[str] = [
            ffmpeg_exe,
            "-hide_banner",
            "-loglevel", "warning",
            "-nostats",

            "-f", "rawvideo",
            '-pixel_format', out_pipe_pixfmt,
            '-video_size', f"{out_w}x{out_h}",
            "-r", str(vsettings.frame_rate),

            "-i", "pipe:0",

            "-vcodec", str_to_video_codec[vsettings.codec].value,
            "-pix_fmt", vsettings.pix_fmt,
            *colorspace,
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
        print(purple(f"[V] encoder command: "), " ".join(encoder_command))

        encoder_subproces: subprocess.Popen = None
        try:
            encoder_subproces = subprocess.Popen(
                encoder_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except Exception as e:
            print(red(f"[E][W] {scene_key} Unexpected error: {type(e)}"))
            return False

        produced: int = 0

        for i, img in enumerate(out_imgs):
            out_f_no = scene['src'].first_frame_no() + i
            out_frame = McoFrame(
                no=out_f_no,
                img=img,
                scene=scene
            )

            out_frames = apply_effect(
                out_f_no=out_f_no,
                frame=out_frame,
                out_i=i
            )
            if isinstance(out_frames, list):
                print(yellow(f"\t{produced}: send {len(out_frames)} frames"))
                [encoder_subproces.stdin.write(f.img) for f in out_frames]
                produced += len(out_frames)
            else:
                print(yellow(f"\t{produced}: send {out_frames.no}"))
                encoder_subproces.stdin.write(out_frames.img)
                produced += 1

        stderr_bytes: bytes | None = None
        _, stderr_bytes = encoder_subproces.communicate(timeout=10)
        if stderr_bytes is not None:
            stderr = stderr_bytes.decode('utf-8)')
            # TODO: parse the output file
            if stderr != '':
                print(f"{scene_key} stderr:")
                pprint(stderr)

        print(f"generated {produced} frames")


    sys.exit()



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
