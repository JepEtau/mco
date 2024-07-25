from collections import deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum
import math
import multiprocessing
import os
from pprint import pprint
import subprocess
import sys
from typing import Literal

import cv2
import numpy as np
from parsers import (
    db,
    get_fps,
    task_to_dirname,
    VideoSettings,
)
from processing.effects import effect_fadeout, effect_loop_and_fadeout
from processing.frame_replace import ItemCache, frame_occurences, get_frames_to_cache, get_frames_to_remove
from processing.watermark import add_watermark
from scene.filters import do_watermark
from scene.src_scene import SrcScene
from utils.images import IMG_FILENAME_TEMPLATE, Image, Images
from utils.images_io import load_image
from utils.logger import main_logger
from utils.mco_types import ChapterVideo, Effect, Effects, Scene
from utils.mco_utils import get_cache_path, get_dirname, get_target_audio, get_target_video, is_first_scene, is_last_scene, run_simple_command
from utils.p_print import *
from utils.path_utils import path_split
from utils.pxl_fmt import PIXEL_FORMAT
from utils.time_conversions import FrameRate, frame_to_s, frame_to_sexagesimal, ms_to_frame
from utils.tools import ffmpeg_exe
from video.out_frames import get_out_frame_paths
from utils.media import VideoInfo, extract_media_info, str_to_video_codec


@dataclass(slots=True)
class Frame:
    no: int
    img: np.ndarray




def generate_lr_scene(scene: Scene, force: bool = False) -> bool:
    scene_key: str = f"{scene['dst']['k_ep']}:{scene['dst']['k_ch']}:{scene['no']}"

    for s in scene['src'].scenes():
        in_video_fp: str = s['scene']['inputs']['progressive']['filepath']
        if not os.path.exists(in_video_fp):
            raise FileExistsError(red(f"Missing input file: {in_video_fp}"))

    out_video_fp: str = scene['task'].video_file
    if not force:
        if os.path.exists(out_video_fp):
            try:
                out_video_info: VideoInfo = extract_media_info(out_video_fp)['video']
                if out_video_info['frame_count'] == scene['dst']['count']:
                    return True
            except:
                pass

    task_name: str = scene['task'].name

    # Output directory
    lr_directory: str = path_split(scene['task'].video_file)[0]
    os.makedirs(lr_directory, exist_ok=True)

    # Out video clip
    in_video_fp = scene['src'].primary_scene()['scene']['inputs']['progressive']['filepath']
    video_info: VideoInfo = extract_media_info(in_video_fp)['video']
    h, w, c = video_info['shape']
    pipe_pixfmt = 'bgr24'
    pipe_out_dtype = (
        np.uint8
        if PIXEL_FORMAT[pipe_pixfmt]['bpp'] <= 8
        else np.uint16
    )

    frame_rate: FrameRate = get_fps(db)
    vsettings: VideoSettings = scene['task'].video_settings
    writer_command: list[str] = [
        ffmpeg_exe,
        "-hide_banner",
        "-loglevel", "warning",
        "-nostats",

        "-f", "rawvideo",
        '-pixel_format', pipe_pixfmt,
        '-video_size', f"{w}x{h}",
        "-r", str(frame_rate),
        "-i", "pipe:0",

        "-vf", "scale=768:576",

        "-pix_fmt", vsettings.pix_fmt,
        "-vcodec", str_to_video_codec[vsettings.codec].value,
        *vsettings.codec_options,
        out_video_fp, "-y"
    ]
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

    produced: int = 0
    to_produce: int = scene['dst']['count']
    print(lightcyan(f"Frames to produce: {to_produce}"))
    for src in scene['src'].scenes():
        src_scene: Scene = src['scene']
        in_video_fp: str = src_scene['inputs']['progressive']['filepath']
        start: int = src['start']
        count: int = src['count']
        if to_produce < count:
            count = to_produce
        print(f"extract {count} frames")
        to_produce -= count


        xtract_command: list[str] = [
            ffmpeg_exe,
            "-hide_banner",
            "-loglevel", "warning",
            "-nostats",
            "-ss",
            str(
                frame_to_sexagesimal(
                    no=start - src_scene['inputs']['progressive']['start'],
                    frame_rate=frame_rate
                )
            ),
            "-i", in_video_fp,
            "-t", str(frame_to_s(no=count, frame_rate=frame_rate))
        ]
        video_info: VideoInfo = extract_media_info(in_video_fp)['video']
        h, w, c = video_info['shape']
        pipe_pixfmt = 'bgr24'
        pipe_img_nbytes = math.prod(video_info['shape'])
        pipe_dtype = np.uint8
        pipe_img_shape: tuple[int, int, int] = video_info['shape']
        xtract_command.extend([
            "-f", "image2pipe",
            "-pix_fmt", pipe_pixfmt,
            "-vcodec", "rawvideo",
            "-"
        ])

        reader_subproces: subprocess.Popen = None
        try:
            reader_subproces = subprocess.Popen(
                xtract_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except Exception as e:
            print(red(f"[E][W] {scene_key} Unexpected error: {type(e)}"))
            return False


        def _read_frame() -> np.ndarray:
            frame = reader_subproces.stdout.read(pipe_img_nbytes)
            if len(frame) < pipe_img_nbytes:
                raise ValueError(red(f"[E][R] {scene_key} Unexpected error: frame size < {pipe_img_nbytes}"))
            return frame

        # Replacements
        frame_replace = src_scene['replace']
        frames_to_replace: list[int] = get_frames_to_remove(frame_replace)
        frame_cache: ItemCache = ItemCache()
        frame_cache.set_occurences(frame_occurences(frame_replace))
        frame_cache.set_exceptions(frames_to_replace)


        from_cache: bool = False
        # pprint(frames_to_replace)

        ch_video: ChapterVideo = get_target_video(scene)
        if is_first_scene(scene):
            print(lightcyan("first scene"))
            pprint(ch_video['avsync'])
            if ch_video['avsync'] != 0:
                raise NotImplementedError("avsync not yet supported")

        in_f_no: int = start - 1
        out_f_no: int = start

        in_frame: Frame = None
        out_frame: Frame = None
        out_i: int = 0
        while count:

            in_frame: Frame = None
            while in_frame is None:
                in_f_no += 1
                img: np.ndarray = np.frombuffer(
                    reader_subproces.stdout.read(pipe_img_nbytes),
                    dtype=pipe_dtype,
                ).reshape(pipe_img_shape)
                if in_f_no not in frames_to_replace:
                    # print(purple(f"Read frame no.{in_f_no}"))
                    in_frame: Frame = Frame(no=in_f_no, img=img)

            out_frame = None
            while True:
                f_no = frame_replace[out_f_no] if out_f_no in frame_replace else out_f_no
                out_frame = None

                from_cache = False

                if f_no == in_f_no:
                    out_frame = in_frame

                elif f_no in frame_cache:
                    out_frame = frame_cache[f_no]
                    from_cache = True

                elif in_f_no not in frame_cache:
                    frame_cache.add(in_f_no, in_frame)

                if out_frame is not None:

                    out_frames = apply_effect(scene, out_f_no, out_frame)
                    if isinstance(out_frames, list):
                        # print(yellow(f"\t{out_i}: send {len(out_frames)}"))
                        [writer_subproces.stdin.write(f.img) for f in out_frames]
                        produced += len(out_frames)
                    else:
                        # print(yellow(f"\t{out_i}: send {out_frame.no} (from {'cache' if from_cache else 'producer'})"))
                        writer_subproces.stdin.write(out_frame.img)
                        produced += 1

                    out_f_no += 1
                    out_i += 1
                    count -= 1
                else:
                    break

    print(f"produced: {produced}")
    if is_last_scene(scene):
        if 'silence' in ch_video and ch_video['silence'] > 0:
            print(f"silence!!! {ch_video['silence']}")
            img_black = np.zeros(video_info['shape'], dtype=pipe_out_dtype)
            [writer_subproces.stdin.write(img_black) for _ in range(ch_video['silence'])]

            produced += ch_video['silence']
            print(f"produced w/ silence: {produced}")


    stderr_bytes: bytes | None = None
    try:
        # Arbitrary timeout value
        _, stderr_bytes = writer_subproces.communicate(timeout=10)
    except:
        writer_subproces.kill()
        return False

    if stderr_bytes is not None:
        stderr = stderr_bytes.decode('utf-8)')
        # TODO: parse the output file
        if stderr != '':
            print(f"{scene_key} stderr:")
            pprint(stderr)
            return False
    return True



def apply_effect(scene: Scene, out_f_no: int, frame: Frame) -> Frame | list[Frame]:
    if 'effects' in scene:
        effect: Effect = scene['effects'].primary_effect()
        if effect.name == 'loop' and out_f_no == effect.frame_ref:
            print(f"loop count = {effect.loop + 1}")
            return [frame] * (effect.loop + 1)

        elif effect.name == 'fadeout' and out_f_no >= effect.frame_ref:
            if out_f_no >= effect.frame_ref:
                coef: float = float(out_f_no - effect.frame_ref) / effect.fade
                img_black = np.zeros(frame.img.shape, dtype=frame.img.dtype)
                img_out: np.ndarray = cv2.addWeighted(frame.img, 1 - coef, img_black, coef, 0)
                print(f"out_i: {out_f_no}, coef={coef:.06f}")
                return Frame(no=frame.no, img=img_out)

        elif effect.name == 'loop_and_fadeout':
            fadeout_start = effect.frame_ref + effect.loop - effect.fade
            # print(f"fadeout_start= {fadeout_start}, out_f_no: {out_f_no}")

            if effect.fade > effect.loop and out_f_no >= fadeout_start:
                print(f"start @{out_f_no} (fadeout_start: {fadeout_start})")
                # print(f"effect.frame_ref: {effect.frame_ref} vs {scene['dst']['start'] + scene['dst']['count']}")
                img_black = np.zeros(frame.img.shape, dtype=frame.img.dtype)

                if out_f_no < effect.frame_ref:
                    i = float(out_f_no - fadeout_start)
                    coef: float = float(i) / effect.fade
                    img_out: np.ndarray = cv2.addWeighted(frame.img, 1 - coef, img_black, coef, 0)
                    print(f"out_i: {out_f_no}, coef={coef:.06f}")
                    return Frame(no=frame.no, img=img_out)

                elif out_f_no == effect.frame_ref:
                    out_frames: list[Frame] = []
                    for i in range (effect.loop + 1):
                        coef: float = float(effect.frame_ref + i - fadeout_start) / effect.fade
                        print(f"out_i: {out_f_no}, coef={coef:.06f}")
                        out_frames.append(Frame(
                            no=frame.no,
                            img=cv2.addWeighted(frame.img, 1 - coef, img_black, coef, 0),
                        ))
                    return out_frames

            elif out_f_no == effect.frame_ref:
                img_black = np.zeros(frame.img.shape, dtype=frame.img.dtype)
                if effect.loop >= effect.fade:
                    out_frames: list[Frame] = [frame] * (effect.loop - effect.fade + 1)
                else:
                    out_frames: list[Frame] = [frame]

                for i in range (effect.fade):
                    coef: float = float(i) / effect.fade
                    print(f"out_i: {out_f_no}, coef={coef:.06f}")
                    out_frames.append(Frame(
                        no=frame.no,
                        img=cv2.addWeighted(frame.img, 1 - coef, img_black, coef, 0),
                    ))
                return out_frames
            # else:
            #     raise NotImplementedError(effect.name)


        # else:
        #     raise NotImplementedError(effect.name)

    # else:
    #     print("no effect")

    return frame


class FadeCurve(Enum):
    LINEAR = "linear"

def coef_table(
    fade_type: Literal['in', 'out'],
    curve: FadeCurve,
    count: int
) -> np.ndarray[float]:
    if curve == FadeCurve.LINEAR:
        coefs = np.array([float(x) / count for x in range(count)])
    else:
        raise NotImplementedError("not yet implemented")
    return coefs if fade_type == 'in' else 1.0 - coefs
