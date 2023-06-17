
# -*- coding: utf-8 -*-
import sys
import cv2
import numpy as np
from pprint import pprint
from utils.pretty_print import *


# Filters from chaiNNer (2023-06-08)

def normalize(img: np.ndarray) -> np.ndarray:
    if img.dtype != np.float32:
        try:
            # Get min/max values
            info = np.iinfo(img.dtype)
            img = img.astype(np.float32)

            if info is not None:
                img /= info.max
                if info.min == 0:
                    # we don't need to clip
                    return img
        except:
            pass
        # we own `img`, so it's okay to write to it
        return np.clip(img, 0, 1, out=img)

    return np.clip(img, 0, 1)


def to_uint8(
    img: np.ndarray,
    normalized:bool=False,
    dither:bool=False,
) -> np.ndarray:
    """
    Returns a new uint8 image with the given image data.

    If `normalized` is `False`, then the image will be normalized before being converted to uint8.

    If `dither` is `True`, then dithering will be used to minimize the quantization error.
    """
    if img.dtype == np.uint8:
        return img.copy()

    if not normalized or img.dtype != np.float32:
        img = normalize(img)

    if not dither:
        return (img * 255).round().astype(np.uint8)

    # random dithering
    truth = img * 255
    quant = truth.round()

    err = truth - quant
    r = np.random.default_rng(0).uniform(0, 1, img.shape).astype(np.float32)
    quant += np.sign(err) * (np.abs(err) > r)

    return quant.astype(np.uint8)

def canny_edge_detection(
    img: np.ndarray,
    t_lower: int,
    t_upper: int,
) -> np.ndarray:
    return cv2.Canny(to_uint8(img, normalized=True), t_lower, t_upper)



def cv2_unsharp(img: np.ndarray, radius: float, amount: float) -> np.ndarray:
    if radius == 0 or amount == 0:
        return img

    blurred = cv2.GaussianBlur(img, (0, 0), radius)
    return cv2.addWeighted(img, amount + 1, blurred, -amount, 0)



def brightness_and_contrast(
    img: np.ndarray, brightness: float, contrast: float
) -> np.ndarray:
    """Adjusts the brightness and contrast of an image"""

    brightness /= 100
    contrast /= 100

    if brightness == 0 and contrast == 0:
        return img

    # Contrast correction factor
    max_c = 259 / 255
    factor: float = (max_c * (contrast + 1)) / (max_c - contrast)
    add: float = factor * brightness + 0.5 * (1 - factor)

    img = factor * img + add

    return img


def high_pass_filter_node(
    img: np.ndarray,
    radius: float,
    contrast: float,
) -> np.ndarray:
    alpha = None
    try:
        if img.shape[2] > 3:
            alpha = img[:, :, 3]
            img = img[:, :, :3]
    except:
        pass

    if radius == 0 or contrast == 0:
        img = img * 0 + 0.5
    else:
        img = contrast * (img - cv2.GaussianBlur(img, (0, 0), radius)) + 0.5

    if alpha is not None:
        img = np.dstack((img, alpha))

    return img