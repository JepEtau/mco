import math
import sys
from typing import Literal
import numpy as np
from utils.media import ChannelOrder, FShape, VideoInfo


def decoder_frame_prop(
    video_info: VideoInfo,
    deint_algo: Literal[
        'nnedi',
        'bob',
        'bwdif',
        'decomb',
        'estdif',
        'kerneldeint',
        'mcdeint',
        'w3fdif',
        'yadif',
        'qtgmc'
    ] = 'qtgmc' if sys.platform == "win32" else 'nnedi',
    fp32: bool = False
) -> tuple[FShape, np.dtype, ChannelOrder, int] | None:
    """Returns the shape, dtype, channel order and size in bytes
        of a decoded frame
        fp32: force dtype to float32
    """

    out_c_order: ChannelOrder = (
        'rgb'
        if video_info['c_order'] == 'yuv' or deint_algo == 'qtgmc'
        else video_info['c_order']
    )
    out_c_order = 'bgr' if 'bgr' in out_c_order or fp32 else 'rgb'

    in_bpp = video_info['bpp']
    if in_bpp > 16:
        in_pix_fmt = video_info['pix_fmt']
        sys.exit(f"[E] {in_pix_fmt} is not a supported pixel format (bpp>16)")
        return None

    out_dtype: np.dtype = np.float32
    if not fp32:
        out_dtype = np.uint16 if in_bpp > 8 else np.uint8

    return (
        video_info['shape'],
        out_dtype,
        out_c_order,
        math.prod(video_info['shape']) * np.dtype(out_dtype).itemsize
    )
