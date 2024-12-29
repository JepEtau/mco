from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
import cv2
import numpy as np
from PIL import Image
from utils.np_dtypes import np_to_float32
from utils.p_print import *
# from .image.np_dtypes import (
#     np_to_float16,
#     np_to_uint8,
#     np_to_float32
# )


LibavResizeAlgorithm: dict = {
    'fast bilinear': "FAST_BILINEAR",
    'bilinear': "BILINEAR",
    'bicubic': "BICUBIC",
    'neighbor': "POINT",
    'area': "AREA",
    'bicubic/bilinear': "BICUBLIN",
    'gauss': "GAUSS",
    'sinc': "SINC",
    'lanczos': "LANCZOS",
    'spline': "SPLINE",
    # MITCHELL = 0x800
}


PillowResizeAlgorithm: dict = {
    'bilinear': Image.Resampling.BILINEAR,
    'nearest': Image.Resampling.NEAREST,
    'box': Image.Resampling.BOX,
    'hamming': Image.Resampling.HAMMING,
    'bicubic': Image.Resampling.BICUBIC,
    'lanczos': Image.Resampling.LANCZOS,
}


Cv2ResizeAlgorithm: dict = {
    'nearest': cv2.INTER_NEAREST,
    'linear': cv2.INTER_LINEAR,
    'bicubic': cv2.INTER_CUBIC,
    'area': cv2.INTER_AREA,
    'lanczos': cv2.INTER_LANCZOS4,
    # 'linear exact': cv2.INTER_LINEAR_EXACT,
    # 'nearest exact': cv2.INTER_NEAREST_EXACT,
}


def cv2_resize(
    img: np.ndarray,
    out_w: int,
    out_h: int,
    interpolation: int
) -> np.ndarray:
    in_dtype = img.dtype
    img = img.astype(np.float32)
    img = cv2.resize(
        img,
        (out_w, out_h),
        interpolation=interpolation
    )
    return img.astype(in_dtype)


def pillow_resize_channel(
    channel: np.ndarray,
    out_w: int,
    out_h: int,
    interpolation: Image.Resampling
) -> np.ndarray:
    return np.asarray(
        Image.fromarray(channel, 'F').resize(
            (out_w, out_h),
            resample=interpolation,
        )
    )


def pillow_resize(
    img: np.ndarray,
    out_w: int,
    out_h: int,
    interpolation: Image.Resampling
) -> np.ndarray:
    if False:
        pimg = Image.fromarray(np_to_uint8(img))
        pimg = pimg.resize(
            (out_w, out_h),
            resample=interpolation,
        )
        return np_to_float32(np.asarray(pimg))
    elif True:
        o_ch = [
            np.asarray(
                Image.fromarray(c, 'F').resize(
                    (out_w, out_h),
                    resample=interpolation,
                )
            )
            for c in cv2.split(img)
        ]
        return np_to_float32(cv2.merge(o_ch))
    else:
        o_ch = [None, None, None]
        with ThreadPoolExecutor(max_workers=3) as executor:
            for cno, channel in executor.map(
                lambda args: pillow_resize_channel(
                    *args,
                    out_w,
                    out_h,
                    interpolation
                ),
                [(i, c) for i, c in enumerate(cv2.split(img))]
            ):
                o_ch[cno] = channel
        return np_to_float32(cv2.merge(o_ch))



def libav_resize(
    img: np.ndarray,
    out_w: int,
    out_h: int,
    interpolation: str | int
) -> np.ndarray:
    # vframe = VideoFrame.from_ndarray(np_to_uint16(img), format='rgb48be')
    vframe = VideoFrame.from_ndarray(img, format='gbrpf32le')
    vframe = vframe.reformat(
        out_w,
        out_h,
        interpolation=interpolation
    )
    return vframe.to_ndarray(format='gbrpf32le')
