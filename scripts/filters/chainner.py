
# -*- coding: utf-8 -*-
import sys
import cv2
from enum import Enum
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


def add_noise(
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
