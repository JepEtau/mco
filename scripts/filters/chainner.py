
# -*- coding: utf-8 -*-
import sys
import cv2
from enum import Enum
from math import ceil
import numpy as np
from typing import (
    Callable,
    List,
    Tuple,
    Union,
)

from pprint import pprint
from utils.pretty_print import *

# Filters from chaiNNer
# Unless specified:
#   Copyright (C) 2023, chaiNNer
# 2023-06-15

def get_h_w_c(image: np.ndarray) -> Tuple[int, int, int]:
    """Returns the height, width, and number of channels."""
    h, w = image.shape[:2]
    c = 1 if image.ndim == 2 else image.shape[2]
    return h, w, c

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

def canny_edge_detection_node(
    img: np.ndarray,
    t_lower: int,
    t_upper: int,
) -> np.ndarray:
    return cv2.Canny(to_uint8(img, normalized=True), t_lower, t_upper)



def sharpen_node(img: np.ndarray, radius: float, amount: float) -> np.ndarray:
    if radius == 0 or amount == 0:
        return img

    blurred = cv2.GaussianBlur(img, (0, 0), radius)
    return cv2.addWeighted(img, amount + 1, blurred, -amount, 0)



def brightness_and_contrast_node(
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



from dataclasses import dataclass
from random import Random

_U32_MAX = 4294967296


@dataclass(frozen=True)
class Seed:
    value: int
    """
    The value of the seed. This value may be signed and generally have any range.
    """

    @staticmethod
    def from_bytes(b: bytes):
        return Seed(Random(b).randint(0, _U32_MAX - 1))

    def to_range(self, a: int, b: int) -> int:
        """
        Returns the value of the seed within the given range [a,b] both ends inclusive.

        If the current seed is not within the given range, a value within the range will be derived from the current seed.
        """
        if a <= self.value <= b:
            return self.value
        return Random(self.value).randint(a, b)

    def to_u32(self) -> int:
        """
        Returns the value of the seed as a 32bit unsigned integer.
        """
        return self.to_range(0, _U32_MAX - 1)

    def cache_key_func(self):
        return self.value



class NoiseType(Enum):
    GAUSSIAN = "gaussian"
    UNIFORM = "uniform"
    SALT_AND_PEPPER = "salt_and_pepper"
    SPECKLE = "speckle"
    POISSON = "poisson"




def as_target_channels(
    img: np.ndarray, target_c: int, narrowing: bool = False
) -> np.ndarray:
    """
    Given a number of target channels (either 1, 3, or 4), this convert the given image
    to an image with that many channels. If the given image already has the correct
    number of channels, it will be returned as is.

    Narrowing conversions are only supported if narrowing is True.
    """
    c = img.shape[2]

    if c == target_c == 1:
        if img.ndim == 2:
            return img
        if img.ndim == 3 and img.shape[2] == 1:
            return img[:, :, 0]
    if c == target_c:
        return img

    if not narrowing:
        assert (
            c < target_c
        ), f"Narrowing is false, image channels ({c}) must be less than target channels ({target_c})"

    if c == 1:
        if target_c == 3:
            return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        if target_c == 4:
            return cv2.cvtColor(img, cv2.COLOR_GRAY2BGRA)

    if c == 3:
        if target_c == 1:
            return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        if target_c == 4:
            return cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)

    if c == 4:
        if target_c == 1:
            return cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
        if target_c == 3:
            return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    raise ValueError(f"Unable to convert {c} channel image to {target_c} channel image")



def __add_noises(
    image: np.ndarray,
    noise_gen: Callable[[int, int], List[np.ndarray]],
    combine: Callable[[np.ndarray, List[np.ndarray]], np.ndarray],
) -> np.ndarray:
    img = image
    h, w, c = img.shape
    assert c != 2, "Noise cannot be added to 2-channel images."

    if c > 3:
        img = img[:, :, :3]

    noises = noise_gen(h, w)

    assert len(noises) > 0

    max_channels = min(c, 3)
    for n in noises:
        noise_channels = get_h_w_c(n)[2]
        assert noise_channels in (1, 3), "Noise must be a grayscale or RGB image."
        max_channels = max(max_channels, noise_channels)

    noises = [as_target_channels(n, max_channels) for n in noises]
    img = as_target_channels(img, max_channels)

    result = combine(img, noises)

    if c > 3:
        result = np.concatenate([result, image[:, :, 3:]], axis=2)

    return np.clip(result, 0, 1)

def __add_noise(
    image: np.ndarray,
    noise_gen: Callable[[int, int], np.ndarray],
    combine: Callable[[np.ndarray, np.ndarray], np.ndarray] = lambda i, n: i + n,
) -> np.ndarray:
    return __add_noises(
        image,
        lambda h, w: [noise_gen(h, w)],
        lambda i, n: combine(i, n[0]),
    )


class NoiseColor(Enum):
    RGB = "rgb"
    GRAY = "gray"

    @property
    def channels(self):
        return 3 if self is NoiseColor.RGB else 1


# Applies gaussian noise to an image
def gaussian_noise(
    image: np.ndarray,
    amount: float,
    noise_color: NoiseColor,
    seed: int = 0,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return __add_noise(
        image,
        lambda h, w: rng.normal(0, amount, (h, w, noise_color.channels)).astype(
            np.float32
        ),
    )


# Applies uniform noise to an image
def uniform_noise(
    image: np.ndarray,
    amount: float,
    noise_color: NoiseColor,
    seed: int = 0,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return __add_noise(
        image,
        lambda h, w: rng.uniform(-amount, amount, (h, w, noise_color.channels)).astype(
            np.float32
        ),
    )


# Applies salt and pepper noise to an image
def salt_and_pepper_noise(
    image: np.ndarray,
    amount: float,
    noise_color: NoiseColor,
    seed: int = 0,
) -> np.ndarray:
    def gen_noise(h: int, w: int):
        rng = np.random.default_rng(seed)
        noise_c = noise_color.channels
        amt = amount / 2
        pepper = rng.choice([0, 1], (h, w, noise_c), p=[amt, 1 - amt]).astype(np.uint8)
        salt = rng.choice([0, 1], (h, w, noise_c), p=[1 - amt, amt]).astype(np.uint8)
        return [pepper, salt]

    def combine(i: np.ndarray, n: List[np.ndarray]):
        pepper, salt = n
        return np.where(salt == 1, 1, np.where(pepper == 0, 0, i))

    return __add_noises(image, gen_noise, combine)


# Applies poisson noise to an image
def poisson_noise(
    image: np.ndarray,
    amount: float,
    noise_color: NoiseColor,
    seed: int = 0,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return __add_noise(
        image,
        lambda h, w: rng.poisson(amount, (h, w, noise_color.channels)).astype(np.uint8),
    )


# Applies speckle noise to an image
def speckle_noise(
    image: np.ndarray,
    amount: float,
    noise_color: NoiseColor,
    seed: int = 0,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return __add_noise(
        image,
        lambda h, w: rng.normal(0, amount, (h, w, noise_color.channels)).astype(
            np.float32
        ),
        lambda i, n: i + i * n,
    )


def add_noise_node(
    img: np.ndarray,
    noise_type: NoiseType,
    noise_color: NoiseColor,
    amount: int,
    seed: Seed,
) -> np.ndarray:
    if noise_type == NoiseType.GAUSSIAN:
        return gaussian_noise(img, amount / 100, noise_color, seed.value)
    elif noise_type == NoiseType.UNIFORM:
        return uniform_noise(img, amount / 100, noise_color, seed.value)
    elif noise_type == NoiseType.SALT_AND_PEPPER:
        return salt_and_pepper_noise(img, amount / 100, noise_color, seed.value)
    elif noise_type == NoiseType.POISSON:
        return poisson_noise(img, amount / 100, noise_color, seed.value)
    elif noise_type == NoiseType.SPECKLE:
        return speckle_noise(img, amount / 100, noise_color, seed.value)
    else:
        raise ValueError(f"Unknown noise type: {noise_type}")


def average_color_fix_node(
    input_img: np.ndarray, ref_img: np.ndarray, scale_factor: float
) -> np.ndarray:
    """Fixes the average color of the input image"""

    if scale_factor != 100.0:
        # Make sure reference image dims are not resized to 0
        h, w, _ = get_h_w_c(ref_img)
        out_dims = (
            max(ceil(w * (scale_factor / 100)), 1),
            max(ceil(h * (scale_factor / 100)), 1),
        )

        ref_img = cv2.resize(
            ref_img,
            out_dims,
            interpolation=cv2.INTER_AREA,
        )

    input_h, input_w, input_c = get_h_w_c(input_img)
    ref_h, ref_w, ref_c = get_h_w_c(ref_img)

    assert (
        ref_w < input_w and ref_h < input_h
    ), "Image must be larger than Reference Image"

    # adjust channels
    alpha = None
    if input_c > ref_c:
        alpha = input_img[:, :, 3:4]
        input_img = input_img[:, :, :ref_c]
    elif ref_c > input_c:
        ref_img = ref_img[:, :, :input_c]

    # Find the diff of both images

    # Downscale the input image
    downscaled_input = cv2.resize(
        input_img,
        (ref_w, ref_h),
        interpolation=cv2.INTER_AREA,
    )

    # Get difference between the reference image and downscaled input
    downscaled_diff = ref_img - downscaled_input  # type: ignore

    # Upsample the difference
    diff = cv2.resize(
        downscaled_diff,
        (input_w, input_h),
        interpolation=cv2.INTER_CUBIC,
    )

    result = input_img + diff

    # add alpha back in
    if alpha is not None:
        result = np.concatenate([result, alpha], axis=2)

    return result



class TransferColorSpace(Enum):
    LAB = "L*a*b*"
    RGB = "RGB"


class OverflowMethod(Enum):
    CLIP = 1
    SCALE = 0


def image_stats(img: np.ndarray):
    """Get means and standard deviations of channels"""

    # Compute the mean and standard deviation of each channel
    channel_a, channel_b, channel_c = cv2.split(img)
    a_mean, a_std = (channel_a.mean(), channel_a.std())
    b_mean, b_std = (channel_b.mean(), channel_b.std())
    c_mean, c_std = (channel_c.mean(), channel_c.std())

    # Return the color statistics
    return a_mean, a_std, b_mean, b_std, c_mean, c_std


def min_max_scale(img: np.ndarray, new_range=(0, 255)):
    """Perform min-max scaling to a NumPy array"""

    # Get arrays current min and max
    mn = img.min()
    mx = img.max()

    # Check if scaling needs to be done to be in new_range
    if mn < new_range[0] or mx > new_range[1]:
        # Perform min-max scaling
        range_diff = new_range[1] - new_range[0]
        scaled = range_diff * (img - mn) / (mx - mn) + new_range[0]
    else:
        # Return array if already in range
        scaled = img

    return scaled



def scale_array(
    arr: np.ndarray,
    overflow_method: OverflowMethod,
    clip_min: int = 0,
    clip_max: int = 255,
) -> np.ndarray:
    """
    Trim NumPy array values to be in [0, 255] range with option of
    clipping or scaling.
    """

    if overflow_method == OverflowMethod.CLIP:
        scaled = np.clip(arr, clip_min, clip_max)
    else:
        scale_range = (max([arr.min(), clip_min]), min([arr.max(), clip_max]))
        scaled = min_max_scale(arr, new_range=scale_range)

    return scaled


def color_transfer(
    img: np.ndarray,
    ref_img: np.ndarray,
    colorspace: TransferColorSpace,
    overflow_method: OverflowMethod,
    reciprocal_scale: bool = True,
) -> np.ndarray:
    """
    Transfers the color distribution from the source to the target image.
    Uses the mean and standard deviations of the specified
    colorspace. This implementation is (loosely) based on to the
    "Color Transfer between Images" paper by Reinhard et al., 2001.
    """

    a_clip_min, a_clip_max, b_clip_min, b_clip_max, c_clip_min, c_clip_max = (
        0,
        0,
        0,
        0,
        0,
        0,
    )

    # Convert the images from the RGB to L*a*b* color space, if necessary
    if colorspace == TransferColorSpace.LAB:
        a_clip_min, a_clip_max = (0, 100)
        b_clip_min, b_clip_max = (-127, 127)
        c_clip_min, c_clip_max = (-127, 127)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        ref_img = cv2.cvtColor(ref_img, cv2.COLOR_BGR2LAB)
    elif colorspace == TransferColorSpace.RGB:
        a_clip_min, a_clip_max = (0, 1)
        b_clip_min, b_clip_max = (0, 1)
        c_clip_min, c_clip_max = (0, 1)
        img = img[:, :, :3]
        ref_img = ref_img[:, :, :3]
    else:
        raise ValueError(f"Invalid color space {colorspace}")

    # Compute color statistics for the source and target images
    (
        a_mean_tar,
        a_std_tar,
        b_mean_tar,
        b_std_tar,
        c_mean_tar,
        c_std_tar,
    ) = image_stats(img)
    (
        a_mean_src,
        a_std_src,
        b_mean_src,
        b_std_src,
        c_mean_src,
        c_std_src,
    ) = image_stats(ref_img)

    # Subtract the means from the target image
    channel_a, channel_b, channel_c = cv2.split(img)
    channel_a -= a_mean_tar
    channel_b -= b_mean_tar
    channel_c -= c_mean_tar

    if reciprocal_scale:
        # Scale by the standard deviations using reciprocal of paper proposed factor
        channel_a = (a_std_src / a_std_tar) * channel_a
        channel_b = (b_std_src / b_std_tar) * channel_b
        channel_c = (c_std_src / c_std_tar) * channel_c
    else:
        # Scale by the standard deviations using paper proposed factor
        channel_a = (a_std_tar / a_std_src) * channel_a
        channel_b = (b_std_tar / b_std_src) * channel_b
        channel_c = (c_std_tar / c_std_src) * channel_c

    # Add in the source mean
    channel_a += a_mean_src
    channel_b += b_mean_src
    channel_c += c_mean_src

    # Clip/scale the pixel intensities to [clip_min, clip_max] if they fall
    # outside this range
    channel_a = scale_array(channel_a, overflow_method, a_clip_min, a_clip_max)
    channel_b = scale_array(channel_b, overflow_method, b_clip_min, b_clip_max)
    channel_c = scale_array(channel_c, overflow_method, c_clip_min, c_clip_max)

    # Merge the channels together, then convert back to the RGB color
    # space if necessary
    transfer = cv2.merge([channel_a, channel_b, channel_c])
    if colorspace == TransferColorSpace.LAB:
        transfer = cv2.cvtColor(transfer, cv2.COLOR_LAB2BGR)

    # Return the color transferred image
    return transfer



def color_transfer_node(
    img: np.ndarray,
    ref_img: np.ndarray,
    colorspace: TransferColorSpace,
    overflow_method: OverflowMethod,
    reciprocal_scale: bool,
) -> np.ndarray:
    """
        Transfers the color distribution from source image to target image.

    This code was adapted from Adrian Rosebrock's color_transfer script,
    found at: https://github.com/jrosebr1/color_transfer (© 2014, MIT license).
    """

    _, _, img_c = get_h_w_c(img)

    # Preserve alpha
    alpha = None
    if img_c == 4:
        alpha = img[:, :, 3]

    transfer = color_transfer(
        img, ref_img, colorspace, overflow_method, reciprocal_scale
    )

    if alpha is not None:
        transfer = np.dstack((transfer, alpha))

    return transfer



def convert_to_BGRA(img: np.ndarray, in_c: int) -> np.ndarray:
    assert in_c in (1, 3, 4), f"Number of channels ({in_c}) unexpected"
    if in_c == 1:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGRA)
    elif in_c == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)

    return img.copy()



class BlendMode(Enum):
    NORMAL = 0
    DARKEN = 2
    MULTIPLY = 1
    COLOR_BURN = 5
    LINEAR_BURN = 22
    LIGHTEN = 3
    SCREEN = 12
    COLOR_DODGE = 6
    ADD = 4
    OVERLAY = 9
    SOFT_LIGHT = 17
    HARD_LIGHT = 18
    VIVID_LIGHT = 19
    LINEAR_LIGHT = 20
    PIN_LIGHT = 21
    REFLECT = 7
    GLOW = 8
    DIFFERENCE = 10
    EXCLUSION = 16
    NEGATION = 11
    SUBTRACT = 14
    DIVIDE = 15
    XOR = 13



__normalized = {
    BlendMode.NORMAL: True,
    BlendMode.MULTIPLY: True,
    BlendMode.DARKEN: True,
    BlendMode.LIGHTEN: True,
    BlendMode.ADD: False,
    BlendMode.COLOR_BURN: False,
    BlendMode.COLOR_DODGE: False,
    BlendMode.REFLECT: False,
    BlendMode.GLOW: False,
    BlendMode.OVERLAY: True,
    BlendMode.DIFFERENCE: True,
    BlendMode.NEGATION: True,
    BlendMode.SCREEN: True,
    BlendMode.XOR: True,
    BlendMode.SUBTRACT: False,
    BlendMode.DIVIDE: False,
    BlendMode.EXCLUSION: True,
    BlendMode.SOFT_LIGHT: True,
    BlendMode.HARD_LIGHT: True,
    BlendMode.VIVID_LIGHT: False,
    BlendMode.LINEAR_LIGHT: False,
    BlendMode.PIN_LIGHT: True,
    BlendMode.LINEAR_BURN: False,
}

def blend_mode_normalized(blend_mode: BlendMode) -> bool:
    """
    Returns whether the given blend mode is guaranteed to produce normalized results (value between 0 and 1).
    """
    return __normalized.get(blend_mode, False)




class ImageBlender:
    """Class for compositing images using different blending modes."""

    def __init__(self):
        self.modes = {
            BlendMode.NORMAL: self.__normal,
            BlendMode.MULTIPLY: self.__multiply,
            BlendMode.DARKEN: self.__darken,
            BlendMode.LIGHTEN: self.__lighten,
            BlendMode.ADD: self.__add,
            BlendMode.COLOR_BURN: self.__color_burn,
            BlendMode.COLOR_DODGE: self.__color_dodge,
            BlendMode.REFLECT: self.__reflect,
            BlendMode.GLOW: self.__glow,
            BlendMode.OVERLAY: self.__overlay,
            BlendMode.DIFFERENCE: self.__difference,
            BlendMode.NEGATION: self.__negation,
            BlendMode.SCREEN: self.__screen,
            BlendMode.XOR: self.__xor,
            BlendMode.SUBTRACT: self.__subtract,
            BlendMode.DIVIDE: self.__divide,
            BlendMode.EXCLUSION: self.__exclusion,
            BlendMode.SOFT_LIGHT: self.__soft_light,
            BlendMode.HARD_LIGHT: self.__hard_light,
            BlendMode.VIVID_LIGHT: self.__vivid_light,
            BlendMode.LINEAR_LIGHT: self.__linear_light,
            BlendMode.PIN_LIGHT: self.__pin_light,
            BlendMode.LINEAR_BURN: self.__linear_burn,
        }

    def apply_blend(
        self, a: np.ndarray, b: np.ndarray, blend_mode: BlendMode
    ) -> np.ndarray:
        return self.modes[blend_mode](a, b)

    def __normal(self, a: np.ndarray, _: np.ndarray) -> np.ndarray:
        return a

    def __multiply(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return a * b

    def __darken(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return np.minimum(a, b)

    def __lighten(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return np.maximum(a, b)

    def __add(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return a + b

    def __color_burn(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return np.where(
            a == 0, 0, np.maximum(0, (1 - ((1 - b) / np.maximum(0.0001, a))))
        )

    def __color_dodge(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return np.where(a == 1, 1, np.minimum(1, b / np.maximum(0.0001, (1 - a))))

    def __reflect(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return np.where(a == 1, 1, np.minimum(1, b * b / np.maximum(0.0001, 1 - a)))

    def __glow(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return np.where(b == 1, 1, np.minimum(1, a * a / np.maximum(0.0001, 1 - b)))

    def __overlay(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return np.where(b < 0.5, 2 * b * a, 1 - 2 * (1 - b) * (1 - a))

    def __difference(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return cv2.absdiff(a, b)

    def __negation(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return 1 - cv2.absdiff(1 - b, a)

    def __screen(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return a + b - (a * b)  # type: ignore

    def __xor(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return normalize(
            np.bitwise_xor(to_uint8(a, normalized=True), to_uint8(b, normalized=True))
        )

    def __subtract(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return b - a  # type: ignore

    def __divide(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return b / np.maximum(0.0001, a)

    def __exclusion(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return a * (1 - b) + b * (1 - a)

    def __soft_light(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        l = 2 * b * a + np.square(b) * (1 - 2 * a)
        h = np.sqrt(b) * (2 * a - 1) + 2 * b * (1 - a)
        return np.where(a <= 0.5, l, h)

    def __hard_light(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return np.where(a <= 0.5, 2 * a * b, 1 - 2 * (1 - a) * (1 - b))

    def __vivid_light(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return np.where(a <= 0.5, self.__color_burn(a, b), self.__color_dodge(a, b))

    def __linear_light(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return b + 2 * a - 1

    def __pin_light(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        x = 2 * a
        y = x - 1
        return np.where(b < y, y, np.where(b > x, x, b))

    def __linear_burn(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return a + b - 1



def blend_images(overlay: np.ndarray, base: np.ndarray, blend_mode: BlendMode):
    """
    Changes the given image to the background overlayed with the image.

    The 2 given images must be the same size and their values must be between 0 and 1.

    The returned image is guaranteed to have values between 0 and 1.

    If the 2 given images have a different number of channels, then the returned image
    will have maximum of the two.

    Only grayscale, RGB, and RGBA images are supported.
    """
    o_shape = get_h_w_c(overlay)
    b_shape = get_h_w_c(base)

    assert (
        o_shape[:2] == b_shape[:2]
    ), "The overlay and the base image must have the same size"

    def assert_sane(c: int, name: str):
        sane = c in (1, 3, 4)
        assert sane, f"The {name} has to be a grayscale, RGB, or RGBA image"

    o_channels = o_shape[2]
    b_channels = b_shape[2]

    assert_sane(o_channels, "overlay layer")
    assert_sane(b_channels, "base layer")

    blender = ImageBlender()
    target_c = max(o_channels, b_channels)
    needs_clipping = not blend_mode_normalized(blend_mode)

    if target_c == 4 and b_channels < 4:
        base = as_target_channels(base, 3)

        # The general algorithm below can be optimized because we know that b_a is 1
        o_a = np.dstack((overlay[:, :, 3],) * 3)
        o_rgb = overlay[:, :, :3]

        blend_rgb = blender.apply_blend(o_rgb, base, blend_mode)
        final_rgb = o_a * blend_rgb + (1 - o_a) * base
        if needs_clipping:
            final_rgb = np.clip(final_rgb, 0, 1)

        return as_target_channels(final_rgb, 4)

    overlay = as_target_channels(overlay, target_c)
    base = as_target_channels(base, target_c)

    if target_c in (1, 3):
        # We don't need to do any alpha blending, so the images can blended directly
        result = blender.apply_blend(overlay, base, blend_mode)
        if needs_clipping:
            result = np.clip(result, 0, 1)
        return result

    # do the alpha blending for RGBA
    o_a = overlay[:, :, 3]
    b_a = base[:, :, 3]
    o_rgb = overlay[:, :, :3]
    b_rgb = base[:, :, :3]

    final_a = 1 - (1 - o_a) * (1 - b_a)

    blend_strength = o_a * b_a
    o_strength = o_a - blend_strength  # type: ignore
    b_strength = b_a - blend_strength  # type: ignore

    blend_rgb = blender.apply_blend(o_rgb, b_rgb, blend_mode)

    final_rgb = (
        (np.dstack((o_strength,) * 3) * o_rgb)
        + (np.dstack((b_strength,) * 3) * b_rgb)
        + (np.dstack((blend_strength,) * 3) * blend_rgb)
    )
    final_rgb /= np.maximum(np.dstack((final_a,) * 3), 0.0001)  # type: ignore
    final_rgb = np.clip(final_rgb, 0, 1)

    result = np.concatenate([final_rgb, np.expand_dims(final_a, axis=2)], axis=2)
    if needs_clipping:
        result = np.clip(result, 0, 1)
    return result



def opacity_node(img: np.ndarray, opacity: float) -> np.ndarray:
    """Apply opacity adjustment to alpha channel"""

    # Convert inputs
    c = get_h_w_c(img)[2]
    if opacity == 100 and c == 4:
        return img
    imgout = convert_to_BGRA(img, c)
    opacity /= 100

    imgout[:, :, 3] *= opacity

    return imgout
