from typing import Literal
import cv2
import numpy as np


# MorphTypes
morph_operation: dict[str, int] = {
    'erosion': cv2.MORPH_ERODE,
    'dilation': cv2.MORPH_DILATE,
    'opening': cv2.MORPH_OPEN,
    'closing': cv2.MORPH_CLOSE,
    'gradient': cv2.MORPH_GRADIENT
}
MorphologyOperations = Literal[
    'erosion', 'dilation', 'opening', 'closing', 'gradient'
]


# MorphShapes
morph_shape: dict[str, int] = {
    'square': cv2.MORPH_RECT,
    'ellipse': cv2.MORPH_ELLIPSE,
    'cross': cv2.MORPH_CROSS,
}

MorphologyShapes = Literal[
    'square', 'ellipse', 'cross'
]


def cv2_erode(img: np.ndarray, kernel: np.ndarray, iterations: int) -> np.ndarray:
    return cv2.erode(img, kernel,iterations)


def cv2_dilate(img: np.ndarray, kernel: np.ndarray, iterations: int) -> np.ndarray:
    return cv2.dilate(img, kernel,iterations)


def cv2_morphology(
    img: np.ndarray,
    operation: MorphologyOperations,
    radius: int = 1,
    shape: MorphologyShapes = 'square',
    iterations: int = 1
) -> np.ndarray:

    diameter = int(radius * 2 + 1)
    kernel: np.ndarray = cv2.getStructuringElement(
        morph_shape[shape],
        (diameter, diameter)
    )
    operation = morph_operation[operation]
    iterations = iterations

    return cv2.morphologyEx(img, operation, kernel, iterations)

