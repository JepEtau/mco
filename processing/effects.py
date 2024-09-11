from enum import Enum
import math
import os
import subprocess
import sys
from typing import Literal
import numpy as np
import cv2
from pprint import pprint
from parsers._types import ProcessingTask
from parsers.helpers import get_fps
from scene.consolidate import consolidate_scene
from scene.src_scene import SrcScene
from utils.images_io import load_image_fp32, write_image
from utils.media import VideoInfo, extract_media_info
from utils.np_dtypes import np_to_float32, np_to_uint16, np_to_uint8
from utils.p_print import *
from utils.logger import main_logger
from utils.mco_types import Effect, McoFrame, Scene
from PIL import Image
from parsers import (
    db,
)
from utils.time_conversions import FrameRate, frame_to_s, frame_to_sexagesimal
from utils.tools import ffmpeg_exe


cached_frame: McoFrame | None = None


def apply_effect(
    out_f_no: int,
    frame: McoFrame
) -> McoFrame | list[McoFrame]:
    scene: Scene = frame.scene
    out_frames: list[McoFrame] = []

    last_src_scene: SrcScene = scene['src'].last_scene()
    if 'effects' in last_src_scene and last_src_scene['effects'] is not None:

        # Zoom in frame and generate a sequence of frames
        # Append title
        if effect := last_src_scene['effects'].get_effect('zoom_in'):
            if out_f_no == effect.frame_ref:
                print("ZOOOOM")
                out_frames: list[McoFrame] = [frame]
                in_h, in_w = frame.img.shape[:2]
                for i in range (effect.loop):
                    # Recalulate factor at every iteration: linear
                    factor: float = 1 + ((effect.zoom_factor - 1) * (i + 1)) / effect.loop
                    # print(lightcyan(f"factor = {factor}"))
                    out_h, out_w = int(factor * in_h), int(factor * in_w)
                    zoomed: np.ndarray = cv2.resize(
                        frame.img,
                        (out_w, out_h),
                        interpolation=cv2.INTER_LANCZOS4
                    )

                    # Crop to input image shape
                    top, left = int((out_h - in_h) / 2 + 0.5), int((out_w - in_w) / 2 + 0.5)
                    zoomed = np.ascontiguousarray(
                        zoomed[
                            top : top + in_h,
                            left : left + in_w,
                            :
                        ]
                    )
                    # print(zoomed.shape)
                    out_frames.append(McoFrame(
                        no=frame.no,
                        img=zoomed,
                    ))

                # Overlay title
                if (effect := last_src_scene['effects'].get_effect('title')):
                    print(yellow("ADD TITLE"))
                    pprint(effect)
                    title_fp: str = os.path.join(
                        db['common']['directories']['inputs'],
                        "title_fr.png"
                    )
                    initial_title_img: np.ndarray = load_image_fp32(title_fp)
                    start_factor: float = effect.zoom_factor
                    end_factor: float = effect.extra_param

                    bgd_h, bgd_w = frame.img.shape[:2]
                    in_h, in_w = initial_title_img.shape[:2]
                    end: int = min(effect.loop, len(out_frames))
                    for i, f in enumerate(out_frames[:end+1]):
                        bgd_img: np.ndarray = np_to_float32(f.img)
                        step: float = float(i / end)
                        factor: float = (start_factor * (1 - step) + end_factor * step)
                        print(f"\ntitle step: {step:.2f},  factor: {factor:.2f}")

                        out_h, out_w = int(factor * in_h), int(factor * in_w)
                        print(f"bgd shape: {bgd_img.shape}")
                        print(f"{in_w}x{in_h} -> {out_w}x{out_h}")
                        title_img: np.ndarray = cv2.resize(
                            initial_title_img,
                            (out_w, out_h),
                            interpolation=cv2.INTER_LANCZOS4
                        )

                        # Crop if overlay is > background
                        if out_w > bgd_w or out_h > bgd_h:
                            top = max(0, int((out_h - bgd_h) / 2))
                            left = max(0, int((out_w - bgd_w) / 2))

                            print(f"crop: {top}, {left}")
                            title_img = np.ascontiguousarray(
                                title_img[
                                    top : top + bgd_h,
                                    left : left + bgd_w,
                                    :
                                ]
                            )
                            print(f"  cropped_title: {title_img.shape}")

                        # Add borders if overlay is < background
                        out_h, out_w = title_img.shape[:2]
                        if out_w < bgd_w or out_h < bgd_h:
                            top, left = (bgd_h - out_h) // 2, (bgd_w - out_w) // 2
                            bottom, right = bgd_h - (out_h + top), bgd_w - (out_w + left)
                            borders = [top, bottom, left, right]
                            print(f"  borders: {borders}")
                            title_img: np.ndarray = cv2.copyMakeBorder(
                                title_img,
                                *borders,
                                cv2.BORDER_CONSTANT,
                                value=0
                            )

                        print(f"foreground: {title_img.shape}")
                        print(f"background: {bgd_img.shape}")

                        rgb_title_img = title_img[:,:,:3]
                        alpha = title_img[:,:,3:]
                        print(f"alpha shape: {alpha.shape}")
                        f.img = np_to_uint8(
                            (1.0 - alpha) * bgd_img
                            + alpha * rgb_title_img
                        )

                    for f in out_frames[end+1:]:
                        bgd_img: np.ndarray = np_to_float32(f.img)
                        f.img = np_to_uint8(
                            (1.0 - alpha) * bgd_img
                            + alpha * rgb_title_img
                        )


                return out_frames

            else:
                out_frames = frame

        # Blend image with previous frame
        elif effect := last_src_scene['effects'].get_effect('blend'):

            if out_f_no >= effect.frame_ref and out_f_no < effect.frame_ref + effect.fade:
                blend_factor = 1 - float(out_f_no - effect.frame_ref ) / effect.fade
                # print(f"BLEND {out_f_no}, factor: {blend_factor}")
                k_ch = scene['dst']['k_ch']
                if k_ch != 'g_debut':
                    raise ValueError(red("blend effect is supported for g_debut only"))
                previous_scene: Scene = db[k_ch]['video']['scenes'][scene['no'] - 1]

                # out_img: np.ndarray = 128 * np.ones(frame.img.shape, dtype=frame.img.dtype),
                # pprint(out_img)
                # return McoFrame(
                #     out_f_no,
                #     out_img,
                #     scene
                # )


                # Consolidate scene if not already done because we need its last image
                global cached_frame
                if 'task' not in previous_scene:
                    print(f"consolidate scene {previous_scene['no']}")
                    previous_scene['task'] = ProcessingTask(name=scene['task'].name)
                    consolidate_scene(scene=previous_scene, watermark=False)

                if cached_frame is None:
                    # Extract last frame
                    cached_frame = extract_last_frame(previous_scene, frame.img.dtype)
                    cached_img = cached_frame.img

                    prev_last_src_scene: SrcScene = previous_scene['src'].last_scene()
                    # pprint(prev_last_src_scene)

                    # Previous scene used a zoom
                    if 'effects' in prev_last_src_scene and prev_last_src_scene['effects'] is not None:
                        if prev_last_src_scene['effects'].has_effect('zoom_in'):
                            effect: Effect = prev_last_src_scene['effects'].get_effect('zoom_in')

                            factor: float = effect.zoom_factor
                            print(lightcyan(f"factor = {factor}"))
                            in_h, in_w = cached_img.shape[:2]
                            out_h, out_w = int(factor * in_h), int(factor * in_w)
                            # if scene['task'].name == 'lr':
                            #     out_h = int(factor * in_h * in_h / 576)
                            zoomed: np.ndarray = cv2.resize(
                                cached_img,
                                (out_w, out_h),
                                interpolation=Image.Resampling.LANCZOS
                            )

                            # Crop to input image shape
                            top, left = int((out_h - in_h) / 2), int((out_w - in_w) / 2)
                            cached_img = np.ascontiguousarray(zoomed[
                                top : top + in_h,
                                left : left + in_w,
                                :
                            ])

                    # write_image("test.png", cached_img)
                    cached_frame.img = np_to_float32(cached_img)

                    # Add Logo to the cached frame
                    if (effect := last_src_scene['effects'].get_effect('title')):
                        print(yellow("LOGO for blend"))
                        pprint(effect)

                        title_fp: str = os.path.join(
                            db['common']['directories']['inputs'],
                            "title_fr.png"
                        )
                        initial_title_img: np.ndarray = load_image_fp32(title_fp)
                        in_h, in_w = initial_title_img.shape[:2]
                        print(f"title shape: {initial_title_img.shape}")
                        bgd_h, bgd_w = cached_frame.img.shape[:2]
                        out_h, out_w = int(effect.zoom_factor * in_h), int(effect.zoom_factor * in_w)
                        initial_title_img = cv2.resize(
                            initial_title_img,
                            (out_w, out_h),
                            interpolation=cv2.INTER_LANCZOS4
                        )
                        print(f"resized title shape: {initial_title_img.shape}")
                        top, left = (bgd_h - out_h) // 2, (bgd_w - out_w) // 2
                        bottom, right = bgd_h - (out_h + top), bgd_w - (out_w + left)
                        borders = [top, bottom, left, right]
                        print(f"borders: {borders}")
                        initial_title_img: np.ndarray = cv2.copyMakeBorder(
                            initial_title_img,
                            *borders,
                            cv2.BORDER_CONSTANT,
                            value=0
                        )
                        print(f"bordered title shape: {initial_title_img.shape}")
                        rgb_title_img = initial_title_img[:,:,:3]
                        print(f"resized title shape w/out transparency: {rgb_title_img.shape}")
                        # write_image("test_rgb.png", np_to_uint8(rgb_title_img))

                        alpha = initial_title_img[:,:,3:]
                        print(f"alpha shape: {alpha.shape}")
                        cached_frame.img = (
                            (1.0 - alpha) * cached_frame.img
                            + alpha * rgb_title_img
                        )
                        # write_image("test.png", np_to_uint8(title_img))


                    # sys.exit()

                out_img: np.ndarray = blend_images(
                    in_img=np_to_float32(frame.img),
                    layer=cached_frame.img,
                    opacity0=1 - blend_factor,
                    opacity1=blend_factor
                )
                # print(f"{out_img.shape} vs {frame.img.shape}")
                frames = McoFrame(
                    no=out_f_no,
                    img=(
                        np_to_uint16(out_img)
                        if frame.img.dtype == np.uint16
                        else np_to_uint8(out_img)
                    ),
                    scene=scene
                )

            elif out_f_no == effect.frame_ref + effect.fade:
                # Delete cached frame
                cached_frame = None
                frames = frame

            else:
                frames = frame

            return frames

        # Add title to the frame, and loop the input frame if not enough frames
        # to add title
        elif effect := last_src_scene['effects'].get_effect('title'):
            # print("add title")
            # pprint(effect)
            # sys.exit()
            if out_f_no >= effect.frame_ref:
                if out_f_no > effect.frame_ref + effect.loop:
                    print(f"{out_f_no}: add title, loop")
                    frame.img = cached_frame.img
                else:
                    print(f"{out_f_no}: add title, zoom")
                    bgd_img = np_to_float32(frame.img)
                    title_fp: str = os.path.join(
                        db['common']['directories']['inputs'],
                        "title_fr.png"
                    )
                    bgd_h, bgd_w = bgd_img.shape[:2]
                    initial_title_img: np.ndarray = load_image_fp32(title_fp)
                    in_h, in_w = initial_title_img.shape[:2]

                    start_factor: float = effect.zoom_factor
                    end_factor: float = effect.extra_param

                    loop_start, loop_end = 0, 1
                    do_return: bool = False
                    if (
                        effect.loop > last_src_scene['count']
                        and out_f_no >= effect.frame_ref + last_src_scene['count'] - 1
                    ):
                        do_return = True
                        loop_start = out_f_no - effect.frame_ref + last_src_scene['count'] - 1
                        loop_end = effect.loop

                    print(f"for loop: start: {loop_start}, {loop_end}")
                    for i in range(loop_start, loop_end):
                        print(yellow(f"  iteration no. {i}"))
                        step: float = float((i + out_f_no - effect.frame_ref)/ effect.loop)
                        factor: float = (start_factor * (1 - step) + end_factor * step)
                        print(f"\n{out_f_no}: {step:.2f},  factor: {factor:.2f}")

                        out_h, out_w = int(factor * in_h), int(factor * in_w)
                        print(f"bgd shape: {bgd_img.shape}")
                        print(f"{in_w}x{in_h} -> {out_w}x{out_h}")
                        title_img: np.ndarray = cv2.resize(
                            initial_title_img,
                            (out_w, out_h),
                            interpolation=cv2.INTER_LANCZOS4
                        )

                        # Crop if overlay is > background
                        if out_w > in_w or out_h > bgd_h:
                            top = max(0, int((out_h - bgd_h) / 2))
                            left = max(0, int((out_w - bgd_w) / 2))

                            print(f"crop: {top}, {left}")
                            title_img = np.ascontiguousarray(
                                title_img[
                                    top : top + in_h,
                                    left : left + in_w,
                                    :
                                ]
                            )
                            print(f"  cropped_title: {title_img.shape}")

                        # Add borders if overlay is < background
                        out_h, out_w = title_img.shape[:2]
                        if out_w < bgd_w or out_h < bgd_h:
                            top, left = (bgd_h - out_h) // 2, (bgd_w - out_w) // 2
                            bottom, right = bgd_h - (out_h + top), bgd_w - (out_w + left)
                            borders = [top, bottom, left, right]
                            print(f"  borders: {borders}")
                            title_img: np.ndarray = cv2.copyMakeBorder(
                                title_img,
                                *borders,
                                cv2.BORDER_CONSTANT,
                                value=0
                            )

                        print(f"foreground: {title_img.shape}")
                        print(f"background: {bgd_img.shape}")

                        rgb_title_img = title_img[:,:,:3]
                        alpha = title_img[:,:,3:]
                        print(f"alpha shape: {alpha.shape}")
                        out_frames.append(
                            McoFrame(
                                no=frame.no,
                                img=np_to_uint8(
                                    (1.0 - alpha) * bgd_img
                                    + alpha * rgb_title_img
                                ),
                                scene=frame.scene
                            )
                        )

                    if out_f_no == effect.frame_ref + effect.loop or do_return:
                        print(lightcyan("cache frame"))
                        cached_frame = out_frames[-1]
                        frame.img = cached_frame.img

                    # if do_return and
                    #     print("returns")
                    #     return out_frames




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
                return McoFrame(no=frame.no, img=img_out)

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
                    return McoFrame(no=frame.no, img=img_out)

                elif out_f_no == effect.frame_ref:
                    out_frames: list[McoFrame] = []
                    for i in range (effect.loop + 1):
                        coef: float = float(effect.frame_ref + i - fadeout_start) / effect.fade
                        print(f"out_i: {out_f_no}, coef={coef:.06f}")
                        out_frames.append(McoFrame(
                            no=frame.no,
                            img=cv2.addWeighted(frame.img, 1 - coef, img_black, coef, 0),
                        ))
                    return out_frames

            elif out_f_no == effect.frame_ref:
                img_black = np.zeros(frame.img.shape, dtype=frame.img.dtype)
                count: int = effect.loop - effect.fade + 1 - len(out_frames)
                if effect.loop >= effect.fade:
                    out_frames.extend([frame] * (count))
                else:
                    out_frames.extend([frame])

                for i in range (effect.fade):
                    coef: float = float(i) / effect.fade
                    print(f"out_i: {out_f_no}, coef={coef:.06f}")
                    out_frames.append(McoFrame(
                        no=frame.no,
                        img=cv2.addWeighted(frame.img, 1 - coef, img_black, coef, 0),
                    ))
                print(yellow(f"out_frames: {len(out_frames)}"))
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




def extract_last_frame(scene: Scene, dtype: np.dtype = np.uint8) -> McoFrame:
    in_video_fp: str = scene['src'].last_scene()['scene']['inputs']['progressive']['filepath']
    if not os.path.exists(in_video_fp):
        raise ValueError(red(f"Missing file: {in_video_fp}"))

    in_video_info: VideoInfo = extract_media_info(in_video_fp)['video']
    pipe_img_nbytes = math.prod(in_video_info['shape'])
    pipe_img_shape: tuple[int, int, int] = in_video_info['shape']
    pipe_dtype: np.dtype = dtype
    print(red("Error: extract_last_frame: fix this if task is not lr"))
    # frame_no: int = in_video_info['frame_count'] - 1
    frame_no: int = scene['src'].last_frame_no()
    print(f"extract frame no. {frame_no} from {in_video_fp}")

    frame_rate: FrameRate = get_fps(db)
    xtract_command: list[str] = [
        ffmpeg_exe,
        "-hide_banner",
        "-loglevel", "warning",
        "-nostats",

        "-ss", str(frame_to_sexagesimal(no=frame_no, frame_rate=frame_rate)),
        "-i", in_video_fp,
        "-t", str(frame_to_s(no=1, frame_rate=frame_rate)),

        "-f", "image2pipe",
        "-pix_fmt", 'bgr24' if dtype == np.uint8 else 'bgr48',
        "-vcodec", "rawvideo",
        "-"
    ]

    xtract_subproces: subprocess.Popen = None
    try:
        xtract_subproces = subprocess.Popen(
            xtract_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except Exception as e:
        scene_key: str = f"{scene['dst']['k_ep']}:{scene['dst']['k_ch']}:{scene['no']}"
        print(red(f"[E][W] {scene_key} Unexpected error: {type(e)}"))
        raise

    img: np.ndarray = np.frombuffer(
        xtract_subproces.stdout.read(pipe_img_nbytes),
        dtype=pipe_dtype,
    ).reshape(pipe_img_shape)

    stderr_bytes: bytes | None = None
    try:
        # Arbitrary timeout value
        _, stderr_bytes = xtract_subproces.communicate(timeout=10)
    except:
        xtract_subproces.kill()

    if stderr_bytes is not None:
        stderr = stderr_bytes.decode('utf-8)')
        # TODO: parse the output file
        if stderr != '':
            scene_key: str = f"{scene['dst']['k_ep']}:{scene['dst']['k_ch']}:{scene['no']}"
            print(f"{scene_key} stderr:")
            pprint(stderr)
            raise

    return McoFrame(frame_no, img, scene)







# https://www.w3.org/TR/compositing/#valdef-blend-mode-normal
def blend_images(
    in_img: np.ndarray,
    layer: np.ndarray,
    opacity0: float,
    opacity1: float,
) -> np.ndarray:

    # TODO: img0/img1 MUST be RGB/BGR and must have the same dtype
    # TODO: simplify if opacity == 1 for both

    h0, w0 = in_img.shape[:2]
    h1, w1 = layer.shape[:2]

    # Calculate coordinates of the overlay layer
    #   origin: top-let point of the img0 layer
    #   (x0, y0): top-left point of the overlay layer
    #   (x1, y1): bottom-right point of the overlay layer
    x0, y0 = [int((w0 - w1) / 2), int((h0 - h1) / 2)]
    x1, y1 = x0 + w1, y0 + h1

    # Add borders to the img0 layer
    left, right = abs(min(x0, 0)), max(0, (x1 - w0))
    top, bottom = abs(min(y0, 0)), max(0, (y1 - h0))


    if any((top, bottom, left, right)):
        in_img_copy = cv2.cvtColor(in_img, cv2.COLOR_BGR2BGRA)
        in_img_copy = cv2.copyMakeBorder(
            in_img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=(0.0,)
        )
    else:
        in_img_copy = in_img.copy()
        if opacity0 != 1.:
            in_alpha = np.empty((h0, w0, 1), dtype=in_img.dtype)
            in_alpha.fill(opacity0)
            in_img = np.dstack((in_img, in_alpha))


    # Coordinates of the intersection area
    i_x0, i_x1 = x0 + left, x1 + left
    i_y0, i_y1 = y0 + top, y1 + top
    i_h, i_w = i_y1 - i_y0, i_x1 - i_x0

    # TODO: optimize when opacity is 0 or 1

    # Opacity
    in_alpha = np.empty((i_h, i_w, 1), dtype=in_img.dtype)
    in_alpha.fill(opacity0)
    layer_alpha = np.empty((i_h, i_w, 1), dtype=in_img.dtype)
    layer_alpha.fill(opacity1)

    # Intersection
    in_intersection = in_img_copy[i_y0 : i_y1, i_x0 : i_x1, :3]
    # print(f"{i_y0}:{i_y1}, {i_x0}:{i_x1}")
    # print(in_intersection.shape)

    # Blend
    # gimp-2.10.36\app\operations\layer-modes\gimpoperationnormal.c
    alpha_out = layer_alpha + in_alpha - in_alpha * layer_alpha

    # print(f"alpha_out: {alpha_out}")
    # print(type(alpha_out))
    # print(alpha_out.shape)
    layer_weight = layer_alpha / alpha_out
    in_weight = 1 - layer_weight
    blended = layer * layer_weight + in_intersection * in_weight

    # blended = np.dstack((blended, alpha_out))
    in_img_copy[i_y0:i_y1, i_x0:i_x1, :3] = blended

    # out_img = cv2.cvtColor(in_img, cv2.COLOR_BGRA2BGR)

    return in_img_copy










# def effect_loop_and_fadein(scene: Scene, effect: Effect) -> None:
#     # Validate with:
#     #   - ep02: episode

#     sys.exit("effect_loop_and_fadein")

#     # Start and count of frames for the loop
#     fadein_count = effect.fade
#     print(green(f"\tloop and fadein: loop: start={fadein_count}, fadein: count={fadein_count}"))


#     # Get hash to set the suffix
#     hash = scene['last_step']['hash']
#     step_no = scene['last_step']['step_no']
#     if hash == '':
#         # Last filter is null, use previous hash
#         previous_filter = scene['filters'][step_no - STEP_INC]
#         hash = previous_filter['hash']
#         input_filepath = get_input_path_from_shot(
#             scene=scene, task=previous_filter['task'])
#     else:
#         input_filepath = get_input_path_from_shot(
#             scene=scene)
#     suffix = "_%s" % (hash)

#     # Input directory
#     print(lightgrey("\tinput_filepath: %s" % (input_filepath)))

#     # Output directory
#     k_ep_dst = scene['dst']['k_ep']
#     k_ch_dst = scene['dst']['k_part']
#     if k_ch_dst in ['g_debut', 'g_fin']:
#         output_filepath = os.path.join(db[k_ch_dst]['cache_path'])
#     else:
#         output_filepath = os.path.join(db[k_ep_dst]['cache_path'], k_ch_dst)
#     output_filepath = os.path.join(output_filepath,
#         f"{scene['no']:03}", f"{step_no:02}")
#     if not os.path.exists(output_filepath):
#         os.makedirs(output_filepath)
#     print(lightgrey(f"\toutput_filepath: {output_filepath}"))


#     # Input image list
#     if scene['last_task'] == 'edition':
#         image_list = get_image_list_pre_replace(scene=scene,
#             folder=input_filepath,
#             step_no=step_no,
#             hash=hash)
#     elif scene['last_step']['step_no'] == scene['last_step']['step_edition']:
#         image_list = get_new_image_list(scene=scene,
#             step_no=step_no,
#             hash=scene['filters'][step_no - STEP_INC]['hash'])
#     else:
#         image_list = get_image_list(scene=scene,
#             folder=input_filepath,
#             step_no=step_no,
#             hash=hash)
#     img_input = image_list[0]

#     # Output image list
#     filename_template = FILENAME_TEMPLATE % (
#         scene['k_ep'], scene['k_ed'], step_no, suffix)
#     if scene['last_task'] == 'deinterlace':
#         start = scene['start'] + scene['count']
#         end = start + fadein_count
#     else:
#         start = scene['count']
#         end = start + fadein_count
#     output_image_list = list([os.path.join(output_filepath, filename_template % (f_no))
#         for f_no in range(end-1, start-1, -1)])

#     print(lightgrey("\toutput image count: %d" % (len(output_image_list))))
#     # pprint(output_image_list)

#     (height, width, channel_count) = scene['last_step']['shape']

#     # Create a  black image for fadeout
#     img_black = np.zeros([height, width, channel_count], dtype=np.uint8)

#     cache_strlen = len(db['common']['directories']['cache']) + 1
#     img_src = cv2.imread(img_input, cv2.IMREAD_COLOR)
#     print(lightgrey("\tinput image filepath: %s" % (img_input)))
#     for count, img_output in zip(range(fadein_count), output_image_list):
#         coef = 1 - np.power(0.5, (float(count) / fadein_count))
#         # keep print for debug until end of validation
#         print(f"\t{count:02d}: {img_input[cache_strlen:]} -> {img_output[cache_strlen:]}, coef={coef:.02f}")

#         # Mix images
#         img_dst = cv2.addWeighted(img_src, 1 - coef, img_black, coef, 0)
#         img_src = img_dst

#         cv2.imwrite(img_output, img_dst)



# def effect_loop_and_fadeout(scene: Scene, effect: Effect) -> None:
#     # Validate with:
#     #   - ep01: episode
#     #   - ep01: asuivre
#     #   - g_debut
#     verbose: bool = True

#     # Start and count of frames for the loop
#     loop_start = effect.frame_ref
#     loop_count = effect.loop
#     fadeout_count = effect.fade
#     if verbose:
#         print(lightgreen("==========================================================="))
#         pprint(scene)
#         print(green(f"\tloop and fadeout: loop: start={loop_start}, count={loop_count} / fadeout: count={fadeout_count}"))

#     hash: str = scene['task'].hashcode
#     dirname: str = task_to_dirname[scene['task'].name]
#     task_no: int = int(dirname[:2])
#     suffix: str = f"_{hash}"
#     k_ed = scene['k_ed']
#     k_ep_src = scene['k_ep']

#     # Input directory
#     in_dir: str = os.path.join(
#         get_cache_path(scene), get_dirname(scene)[0]
#     )
#     if verbose:
#         print(lightgrey(f"\tinput_filepath: {in_dir}"))

#     # Output directory
#     k_ep_dst: str = scene['dst']['k_ep']
#     k_ch_dst: str = scene['dst']['k_ch']
#     if k_ch_dst in ('g_debut', 'g_fin'):
#         out_dir: str = os.path.join(db[k_ch_dst]['cache_path'])
#     else:
#         out_dir: str = os.path.join(db[k_ep_dst]['cache_path'], k_ch_dst)
#     out_dir = os.path.join(out_dir, f"{scene['no']:03}", dirname)
#     if verbose:
#         print(lightgrey("\toutput_directory: %s" % (out_dir)))
#     os.makedirs(out_dir, exist_ok=True)

#     # Duplicate the last one
#     filename_template = IMG_FILENAME_TEMPLATE % (k_ep_src, k_ed, task_no, suffix)
#     loop_img: str = os.path.join(in_dir, filename_template % (loop_start))
#     if verbose:
#         print(lightgrey(f"\tfile used for the loop effect: {loop_img}"))

#     in_imgs: list[str] = [
#         os.path.join(in_dir, filename_template % (
#             scene['start'] + scene['count'] - (fadeout_count - loop_count) + i
#         ))
#         for i in range(fadeout_count - loop_count)
#     ]
#     in_imgs.extend([loop_img] * loop_count)
#     if verbose:
#         pprint(in_imgs)
#         print(lightgrey(f"\toutput image count: {len(in_imgs)}"))

#     out_imgs: list[str] = scene['out_frames'][-fadeout_count:]
#     if k_ch_dst in ('g_debut', 'g_fin', 'precedemment'):
#         db_video = (
#             db[k_ch_dst]['video']
#             if k_ch_dst in ('g_debut', 'g_fin')
#             else db[k_ep_src]['video']['target'][k_ch_dst]
#         )
#         if 'silence' in db_video:
#             db_video['silence']
#             out_imgs: list[str] = scene['out_frames'][-(fadeout_count + db_video['silence']):]


#     if verbose:
#         print("OUT:")
#         pprint(out_imgs)
#         print(lightgrey(f"\toutput image count: {len(out_imgs)}"))

#     img_src: np.ndarray = cv2.imread(in_imgs[0], cv2.IMREAD_COLOR)
#     img_black = np.zeros(img_src.shape, dtype=img_src.dtype)

#     cache_strlen = len(db['common']['directories']['cache']) + 1
#     for count, img_input, img_output in zip(
#         range(fadeout_count),
#         in_imgs,
#         out_imgs
#     ):
#         # Calculate coefficient: last frame is not completely black because there is always
#         # a silence after this (i.e. black frames)
#         coef = float(count) / fadeout_count
#         # keep print for debug until end of validation
#         if verbose:
#             print(f"\t{count:02d}: {img_input[cache_strlen:]} -> {img_output[cache_strlen:]}, coef={coef:.02f}")

#         # Mix images
#         img_src = cv2.imread(img_input, cv2.IMREAD_COLOR)
#         img_dst = cv2.addWeighted(img_src, 1 - coef, img_black, coef, 0)

#         cv2.imwrite(img_output, img_dst)



# def effect_fadeout(scene: Scene, effect: Effect) -> None:
#     # verified:
#     #   - ep01: documentaire
#     # warning: ep02, 'en' version
#     verbose: bool = True

#     fadeout_start = effect.frame_ref
#     fadeout_count = effect.fade

#     if verbose:
#         pprint(scene)
#         print(green(f"\tfadeout: start={fadeout_start}, count={fadeout_count}"))
#         sys.exit()
#     hash: str = scene['task'].hashcode
#     dirname: str = task_to_dirname[scene['task'].name]
#     task_no: int = int(dirname[:2])
#     suffix: str = f"_{hash}"
#     k_ed = scene['k_ed']
#     k_ep_src = scene['k_ep']

#     # Input directory
#     in_dir: str = os.path.join(
#         get_cache_path(scene),
#         get_dirname(scene)[0]
#     )
#     if verbose:
#         print(lightgrey(f"\tinput_filepath: {in_dir}"))

#     # Output directory
#     k_ep_dst: str = scene['dst']['k_ep']
#     k_ch_dst: str = scene['dst']['k_ch']
#     if k_ch_dst in ('g_debut', 'g_fin'):
#         out_dir: str = os.path.join(db[k_ch_dst]['cache_path'])
#     else:
#         out_dir: str = os.path.join(db[k_ep_dst]['cache_path'], k_ch_dst)
#     out_dir = os.path.join(out_dir, f"{scene['no']:03}", dirname)
#     if verbose:
#         print(lightgrey("\toutput_directory: %s" % (out_dir)))
#     os.makedirs(out_dir, exist_ok=True)

#     filename_template = IMG_FILENAME_TEMPLATE % (k_ep_src, k_ed, task_no, suffix)
#     in_imgs: list[str] = [
#         os.path.join(in_dir, filename_template % (f_no))
#         for f_no in range(fadeout_start, fadeout_start + fadeout_count)
#     ]
#     out_imgs: list[str] = [
#         os.path.join(out_dir, filename_template % (scene['src']['start'] + scene['src']['count'] + i))
#         for i in range(fadeout_count)
#     ]

#     img_src: np.ndarray = cv2.imread(in_imgs[0], cv2.IMREAD_COLOR)
#     img_black = np.zeros(img_src.shape, dtype=img_src.dtype)

#     cache_strlen = len(db['common']['directories']['cache']) + 1
#     for i, img_input, img_output in zip(
#         range(fadeout_count),
#         in_imgs,
#         out_imgs
#     ):
#         # Calculate coefficient: last frame is not completely black because there is always
#         # a silence after this (i.e. black frames)
#         coef = float(i) / fadeout_count
#         # keep print for debug until end of validation
#         if verbose:
#             print(f"\t{i:02d}: {img_input[cache_strlen:]} -> {img_output[cache_strlen:]}, coef={coef:.02f}")

#         # Mix images
#         img_src = cv2.imread(img_input, cv2.IMREAD_COLOR)
#         img_dst = cv2.addWeighted(img_src, 1 - coef, img_black, coef, 0)

#         cv2.imwrite(img_output, img_dst)
