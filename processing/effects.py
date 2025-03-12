from enum import Enum
import math
import os
import subprocess
import sys
from typing import Literal
from warnings import warn
import numpy as np
import cv2
from pprint import pprint
from parsers._types import ProcessingTask
from parsers.helpers import get_frame_rate
from scene.consolidate import consolidate_scene
from scene.src_scene import SrcScene
from utils.images_io import load_image_fp32, write_image
from utils.mco_utils import calculate_scene_frame_count
from utils.media import VideoInfo, extract_media_info_mco, FShape
from utils.np_dtypes import np_to_float32, np_to_uint16, np_to_uint8
from utils.p_print import *
from utils.logger import main_logger
from utils.mco_types import McoFrame, Scene
from PIL import Image
from parsers import (
    db,
    Effect,
    Effects,
    get_loop_nframes,
)
from utils.time_conversions import FrameRate, frame_to_s, frame_to_sexagesimal
from utils.tools import ffmpeg_exe


cached_frame: McoFrame | None = None
cached_overlay: McoFrame | None = None


def title_filepath() -> str:
    filepath: str = os.path.join(
        db['common']['directories']['images'],
        f"title_{db['common']['settings']['language']}.png"
    )
    return filepath


def apply_final_effects(
    out_f_no: int,
    frame: McoFrame,
    out_i: int
) -> McoFrame:
    # out_i is the index in the final scene from 0 to end
    # out_f_no is the f_no from start of the src scene
    scene: Scene = frame.scene

    # There is an effect in the scene used to generate this scene
    # Used by: g_debut
    last_src_scene: SrcScene = scene['src'].last_scene()
    if last_src_scene.effects is not None:

        # Blend image with previous frame
        if effect := last_src_scene.effects.get_effect('blend'):

            if out_f_no >= effect.f_ref and out_f_no < effect.f_ref + effect.fade:
                blend_factor = 1 - float(out_f_no - effect.f_ref ) / effect.fade
                # print(f"BLEND {out_f_no}, factor: {blend_factor}")
                k_ch = scene['dst']['k_ch']
                if k_ch != 'g_debut':
                    raise ValueError(red("blend effect is supported for g_debut only"))
                previous_scene: Scene = db[k_ch]['video']['scenes'][scene['no'] - 1]

                # Consolidate scene if not already done because we need its last image
                global cached_frame
                if 'task' not in previous_scene:
                    print(f"consolidate scene {previous_scene['no']} with task \'{scene['task'].name}\'")
                    previous_scene['task'] = ProcessingTask(name=scene['task'].name)
                    consolidate_scene(scene=previous_scene, watermark=False)
                in_img: np.ndarray = np_to_float32(frame.img)

                if cached_frame is None:
                    # Extract last frame
                    cached_frame = extract_last_frame_fp32(previous_scene)
                    cached_img: np.ndarray = cached_frame.img.copy()

                    if False:
                        prev_last_src_scene: SrcScene = previous_scene['src'].last_scene()
                        # pprint(prev_last_src_scene)

                        # Previous scene used a zoom
                        if (
                            'effects' in prev_last_src_scene
                            and prev_last_src_scene['effects'] is not None
                        ):
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


                        print(yellow(f"cached_frame: {type(cached_frame)}"))
                        # Add Logo to the cached frame
                        if (effect := last_src_scene['effects'].get_effect('title')):
                            print(yellow("LOGO for blend, "))
                            pprint(effect)
                            initial_title_img: np.ndarray = load_image_fp32(title_filepath())
                            in_h, in_w = initial_title_img.shape[:2]
                            print(f"  title shape: {initial_title_img.shape}")
                            bgd_h, bgd_w = cached_frame.img.shape[:2]
                            print(f"  cache frame: {cached_frame.img.shape}")

                            out_h, out_w = int(effect.zoom_factor * in_h), int(effect.zoom_factor * in_w)
                            print(f"  resize to: {out_w}x{out_h}")
                            initial_title_img = cv2.resize(
                                initial_title_img,
                                (out_w, out_h),
                                interpolation=cv2.INTER_LANCZOS4
                            )
                            print(f"  resized title shape: {initial_title_img.shape}")
                            top, left = (bgd_h - out_h) // 2, (bgd_w - out_w) // 2
                            bottom, right = bgd_h - (out_h + top), bgd_w - (out_w + left)
                            borders = [top, bottom, left, right]
                            print(f"  borders: {borders}")
                            initial_title_img: np.ndarray = cv2.copyMakeBorder(
                                initial_title_img,
                                *borders,
                                cv2.BORDER_CONSTANT,
                                value=0
                            )
                            print(f"  bordered title shape: {initial_title_img.shape}")
                            rgb = initial_title_img[:,:,:3]
                            print(f"  resized title shape w/out transparency: {rgb.shape}")
                            # write_image("test_rgb.png", np_to_uint8(rgb_title_img))

                            alpha = initial_title_img[:,:,3:]
                            print(f"  alpha shape: {alpha.shape}")
                            cached_frame.img = (
                                (1.0 - alpha) * cached_frame.img
                                + alpha * rgb
                            )
                            print(f"  cached img dtype: {cached_frame.img.dtype}")
                            # write_image(f"test_{frame.no}.png", np_to_uint8(cached_frame.img))


                            # sys.exit()
                        # write_image(f"test_{frame.no}.png", np_to_uint8(cached_frame.img))

                out_img: np.ndarray = blend_images(
                    in_img=in_img,
                    layer=cached_frame.img,
                    opacity0=1 - blend_factor,
                    opacity1=blend_factor
                )
                # print(f"  {out_img.shape}, {out_img.dtype}")
                if frame.img.dtype == np.uint16:
                    out_img = np_to_uint16(out_img)
                elif frame.img.dtype == np.uint8:
                    out_img = np_to_uint8(out_img)
                # print(f"  to {out_img.shape}, {out_img.dtype} (vs initial: {frame.img.dtype})")
                frame = McoFrame(
                    no=out_f_no,
                    img=out_img,
                    scene=scene
                )

            elif out_f_no == effect.f_ref + effect.fade:
                # Delete cached frame
                print(yellow("delete cache frame"))
                cached_frame = None
                frame = frame

            else:
                frame = frame

            return frame

        # Add title to the frame, and loop the input frame if not enough frames
        # to add title
        elif effect := last_src_scene.effects.get_effect('title'):

            start_no: int = effect.start
            # pprint(effect)
            print(out_i)
            # raise

            if out_i >= start_no:
                print(yellow(f"{out_i} add title ({out_f_no})"))

                # Input frame = background
                bgd_img = np_to_float32(frame.img)
                bgd_h, bgd_w = bgd_img.shape[:2]
                print(f"    bgd shape: {bgd_img.shape}")

                # Title = overlay
                initial_title_img: np.ndarray = load_image_fp32(title_filepath())
                title_h, title_w = initial_title_img.shape[:2]
                print(f"    initial_title_img: {initial_title_img.shape}")

                i = out_i - start_no
                start_factor: float = effect.zoom_factor
                end_factor: float = effect.extra_param

                step: float = min(1., float(i / effect.loop))
                factor: float = (
                    start_factor * (1 - step) + end_factor * step
                )
                print(f"    iteration no. {i}, factor={factor:.3f}")

                if scene['task'].name in ('lr', 'sim_lr'):
                    # in_h, in_w = initial_title_img.shape[:2]
                    # initial_title_img: np.ndarray = cv2.resize(
                    #     initial_title_img,
                    #     (in_w//2, in_h//2),
                    #     interpolation=cv2.INTER_LANCZOS4
                    # )
                    # in_h, in_w = initial_title_img.shape[:2]
                    factor /= 2

                overlay_h, overlay_w = int(factor * title_h), int(factor * title_w)
                overlay_img: np.ndarray = cv2.resize(
                    initial_title_img,
                    (overlay_w, overlay_h),
                    interpolation=cv2.INTER_LANCZOS4
                )

                # Crop if overlay is > background
                print(f"    title_img: out_w, out_h: {overlay_w}, {overlay_h}")
                if overlay_w > bgd_w or overlay_h > bgd_h:
                    top = max(0, int((overlay_h - bgd_h) / 2))
                    left = max(0, int((overlay_w - bgd_w) / 2))
                    overlay_img = np.ascontiguousarray(
                        overlay_img[
                            top : top + bgd_h,
                            left : left + bgd_w,
                            :
                        ]
                    )
                    print(f"    cropped_title: {overlay_img.shape}")

                # Add borders if overlay is < background
                overlay_h, overlay_w = overlay_img.shape[:2]
                if bgd_w > overlay_w or bgd_h > overlay_h:
                    top = (bgd_h - overlay_h) // 2
                    left = (bgd_w - overlay_w) // 2
                    bottom = bgd_h - (overlay_h + top)
                    right = bgd_w - (overlay_w + left)

                    borders = [top, bottom, left, right]
                    print(f"    add borders: {borders}")
                    overlay_img: np.ndarray = cv2.copyMakeBorder(
                        overlay_img,
                        *borders,
                        cv2.BORDER_CONSTANT,
                        value=0
                    )
                print(f"    title_img: {overlay_img.shape}")

                overlay_img = np.clip(overlay_img, 0, 1, out=overlay_img)
                rgb = overlay_img[:,:,:3]
                alpha = overlay_img[:,:,3:]
                # print(f"alpha shape: {alpha.shape}")
                blended: np.ndarray = (
                    (1.0 - alpha) * bgd_img + alpha * rgb
                )

                if frame.img.dtype == np.uint16:
                    blended = np_to_uint16(blended)
                elif frame.img.dtype == np.uint8:
                    blended = np_to_uint8(blended)

                frame = McoFrame(
                    no=frame.no,
                    img=blended,
                    scene=frame.scene
                )

                # if out_i == start_no + effect.loop:
                #     cached_frame = out_frames[-1]
                #     frame.img = cached_frame.img
                #     print(lightcyan(f"cache frame, dtype={frame.img.dtype}"))
                    # write_image("title_loop.png", frame.img)


    # Other effects
    # TODO: modify this to allow multiple effects?
    # Currently, only the first effect is applied
    if 'effects' in scene:
        effects: Effects = scene['effects']
        # use primary effect if no overlay to not refcator rn
        if effects.has_effect('overlay'):
            for effect in effects.get_effects('overlay'):
                # global cached_overlay
                # print(f"[{effect.frame_ref}..{effect.frame_ref + effect.loop}] i = {out_i}")
                if effect.f_ref <= out_i <= effect.f_ref + effect.loop:
                    # if cached_overlay is None:
                    x0: int = effect.extra_param[0]
                    overlay_fp: str = os.path.join(
                        db['common']['directories']['images'], effect.extra_param[1]
                    )
                    # print(lightcyan(f"load image: {overlay_fp}"))
                    overlay: np.ndarray = load_image_fp32(filepath=overlay_fp)

                    # position and overlay use the final coordinates system#
                    # -> resize to this resolution (lr task only)
                    h, w = frame.img.shape[:2]
                    sized_img: np.ndarray = None
                    if overlay.shape[0] != h:
                        sized_img = cv2.resize(
                            np_to_float32(frame.img),
                            (1440, 1080),
                            interpolation=cv2.INTER_CUBIC
                        )
                        sized_img = np.clip(sized_img, 0, 1)
                        h, w = sized_img.shape[:2]

                    overlay = cv2.copyMakeBorder(
                        overlay,
                        0, 0, x0, w - (overlay.shape[1] + x0),
                        borderType=cv2.BORDER_CONSTANT,
                    )

                    text = overlay
                    bgd = frame.img if sized_img is None else sized_img
                    rgb_text = text[:,:,:3]
                    alpha_text = text[:,:,3:]
                    overlayed: np.ndarray = (
                        (1.0 - alpha_text) * np_to_float32(bgd) + alpha_text * rgb_text
                    )

                    if sized_img is not None:
                        overlayed = cv2.resize(
                            overlayed,
                            (frame.img.shape[1], frame.img.shape[0]),
                            interpolation=cv2.INTER_LANCZOS4
                        )
                    overlayed = np.clip(overlayed, 0, 1)

                    if frame.img.dtype == np.uint16:
                        frame.img = np_to_uint16(overlayed)
                    elif frame.img.dtype == np.uint8:
                        frame.img = np_to_uint8(overlayed)
                    else:
                        frame.img = overlayed


        if effects.has_effect('fadeout') or effects.has_effect('loop_and_fadeout'):
            effect: Effect = effects.get_effect('fadeout')
            if effect is None:
                effect = effects.get_effect('loop_and_fadeout')

            start_no: int = scene['dst']['count'] - effect.fade

            if out_i >= start_no:
                coef: float = float(out_i - start_no) / effect.fade
                print(f"fadeout, start: {start_no}, out_i: {out_i}, coef={coef:.06f}, dtype={frame.img.dtype}")
                img_black: np.ndarray = np.zeros(frame.img.shape, dtype=np.float32)
                img_out: np.ndarray = cv2.addWeighted(
                    np_to_float32(frame.img), 1 - coef, img_black, coef, 0
                )
                if frame.img.dtype == np.uint16:
                    img_out = np_to_uint16(img_out)
                elif frame.img.dtype == np.uint8:
                    img_out = np_to_uint8(img_out)
                return McoFrame(no=frame.no, img=img_out, scene=scene)


        if effects.has_effect('fadein') or effects.has_effect('loop_and_fadein'):
            effect: Effect = effects.get_effect('fadein')
            if effect is None:
                effect = effects.get_effect('loop_and_fadein')

            if out_i <= effect.fade:
                coef: float = float(out_i) / effect.fade
                print(f"({out_i}) fadein, out_i: {out_i}, coef={coef:.06f}")
                img_black: np.ndarray = np.zeros(frame.img.shape, dtype=np.float32)
                img_out: np.ndarray = cv2.addWeighted(
                    np_to_float32(frame.img), coef, img_black, 1 - coef, 0
                )
                if frame.img.dtype == np.uint16:
                    img_out = np_to_uint16(img_out)
                elif frame.img.dtype == np.uint8:
                    img_out = np_to_uint8(img_out)
                return McoFrame(no=frame.no, img=img_out, scene=scene)
            # else:
            #     return None

    return frame



def apply_upscale_effects(
    out_f_no: int,
    frame: McoFrame,
    out_i: int
) -> list[McoFrame]:
    """This function apply all loop effects. This is important to do it
    when upscaling to allow adding temporal grain (non static).
    This is also used by doc to loop over the first/last frame (se_loop).
    We assume that the loop generated when in fr will be > english version
    """
    scene: Scene = frame.scene

    if 'effects' in scene:
        scene_effects: Effects = scene['effects']
        for effect in scene_effects.effects:
            if (
                effect.name in (
                    'loop',
                    'loop_and_fadeout',
                    'loop_and_fadein'
                )
                and out_f_no == effect.f_ref
            ):
                return [frame] * (effect.loop + 1)

    src_scene = scene['src'].scenes()[frame.src_scene_index]
    if src_scene.effects is not None:
        if e := src_scene.effects.get_effect('loop'):
            if frame.no == e.f_ref:
                return [frame] * (e.loop + 1)

    # Replace by loop
    loop = get_loop_nframes(
        src_scene=frame.scene['src'].scenes()[frame.src_scene_index],
        f_no=frame.no
    )
    if loop:
        return [frame] * loop

    # Only for doc. to reduce number of tests, discard this if not doc
    if scene['dst']['k_ch'] == 'doc':
        in_scene: Scene = scene['src'].primary_scene().in_scene
        if 'effects' in in_scene and in_scene['effects'].has_effect('se_loop'):
            effect: Effect = in_scene['effects'].get_effect('se_loop')
            if out_i == 0 and effect.extra_param[0]:
                return [frame] * (effect.extra_param[0] + 1)

            if out_i == in_scene['count'] - 1 and effect.extra_param[1]:
                return [frame] * (effect.extra_param[1] + 1)

    # Only for g_debut. to reduce number of tests, discard this if not g_debut
    if scene['dst']['k_ch'] == 'g_debut':
        last_src_scene: SrcScene = scene['src'].last_scene()
        if last_src_scene.effects is not None:
            # Zoom in frame and generate a sequence of frames
            # Append title
            if effect := last_src_scene.effects.get_effect('zoom_in'):
                # pprint(effect)
                # raise
                print(f"out_i: {out_i}, {frame.no}, {out_f_no}, {effect.f_ref}")
                # pprint(effect)
                if out_f_no == effect.f_ref:
                    in_dtype: np.dtype = frame.img.dtype
                    print(f"ZOOOOM of frame {effect.f_ref}, shape={frame.img.shape}, dtype={frame.img.dtype}")
                    initial_img = frame.img
                    if in_dtype != np.float32:
                        initial_img: np.ndarray = np_to_float32(frame.img)

                    out_frames: list[McoFrame] = [frame]
                    in_h, in_w = frame.img.shape[:2]
                    for i in range(effect.loop):
                        # Recalulate factor at every iteration: linear
                        factor: float = 1 + ((effect.zoom_factor - 1) * (i + 1)) / effect.loop
                        print(lightcyan(f"factor = {factor}"))
                        out_h, out_w = int(factor * in_h), int(factor * in_w)
                        zoomed: np.ndarray = cv2.resize(
                            initial_img,
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

                        # Convert back to initial dtype
                        if in_dtype == np.uint16:
                            zoomed = np_to_uint16(zoomed)
                        elif in_dtype == np.uint16:
                            zoomed = np_to_uint8(zoomed)

                        out_frames.append(McoFrame(
                            no=frame.no + i,
                            img=np.ascontiguousarray(zoomed),
                            scene=frame.scene,
                            src_scene_index=frame.src_scene_index,
                        ))
                    print(f": {len(out_frames)}")
                    return out_frames

    return [frame]



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




def extract_last_frame_fp32(scene: Scene) -> McoFrame:
    in_video_fp = scene['task'].video_file
    # if scene['task'].name == 'sim':
    #     in_video_fp = scene['src'].last_scene()['scene']['inputs'].progressive().filepath
    # pprint(scene['task'])
    # sys.exit()

    if not os.path.exists(in_video_fp):
        raise ValueError(red(f"Missing file:", in_video_fp))

    in_video_info: VideoInfo = extract_media_info_mco(in_video_fp)['video']
    final_shape: FShape = in_video_info['shape']
    frame_no: int = in_video_info['frame_count'] - 1

    decoder_filters: list[str] = []
    # if scene['task'].name == 'sim':
    #     frame_no: int = scene['src'].last_frame_no() - 1
    #     final_shape: FShape = (1080, 1440, 3)
    #     h, w = final_shape[:2]
    #     decoder_filters = [
    #         "-filter_complex",
    #         f"[0:v]scale={w}:{h}:sws_flags=bicubic+accurate_rnd+bitexact+full_chroma_int[outv]",
    #         "-map", "[outv]"
    #     ]
    #     # patch bpp to force as 16bit because we may use a 8bpp in sim
    #     in_video_info['bpp'] = 16

    pipe_img_shape: FShape = final_shape
    pipe_dtype: np.dtype = (
        np.uint16 if in_video_info['bpp'] > 8
        else np.uint8
    )
    pipe_pix_fmt = 'bgr24' if pipe_dtype == np.uint8 else 'bgr48'
    pipe_img_nbytes = int(math.prod(final_shape) * np.dtype(pipe_dtype).itemsize)

    print(red("Error: extract_last_frame: fix this if task is not lr"))
    pprint(in_video_info)

    print(f"previous video input: {in_video_fp}")
    if not os.path.isfile(in_video_fp):
        raise FileNotFoundError(red("Missing file:", in_video_fp))
    print(f"  frame no. {frame_no}")
    print(f"  pipe pix fmt: {pipe_pix_fmt}")
    print(f"  pipe shape: {pipe_img_shape}")
    print(f"  pipe dtype: {pipe_dtype}")
    print(f"  pipe nbytes: {pipe_img_nbytes}")

    frame_rate: FrameRate = get_frame_rate()
    dec_command: list[str] = [
        ffmpeg_exe,
        "-hide_banner",
        "-loglevel", "warning",
        "-nostats",

        "-ss", str(frame_to_sexagesimal(no=frame_no, frame_rate=frame_rate)),
        "-i", in_video_fp,
        "-t", str(frame_to_s(no=1, frame_rate=frame_rate)),
        *decoder_filters,
        "-f", "image2pipe",
        "-pix_fmt", pipe_pix_fmt,
        "-vcodec", "rawvideo",
        "-"
    ]
    print(lightcyan("extract last frame from previous scene:"), " ".join(dec_command))

    dec_subproces: subprocess.Popen = None
    try:
        dec_subproces = subprocess.Popen(
            dec_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except Exception as e:
        scene_key: str = f"{scene['dst']['k_ep']}:{scene['dst']['k_ch']}:{scene['no']}"
        print(red(f"[E][W] {scene_key} Unexpected error: {type(e)}"))
        raise

    print(f"pipe dtype: {pipe_dtype}")
    img: np.ndarray = np.frombuffer(
        dec_subproces.stdout.read(pipe_img_nbytes),
        dtype=pipe_dtype,
    ).reshape(pipe_img_shape)
    img = np_to_float32(img)

    # write_image(filepath="extracted.png", img=np_to_uint8(img))

    stderr_bytes: bytes | None = None
    try:
        # Arbitrary timeout value
        _, stderr_bytes = dec_subproces.communicate(timeout=10)
    except:
        dec_subproces.kill()

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
#         f"{scene_no_str(scene)}", f"{step_no:02}")
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

