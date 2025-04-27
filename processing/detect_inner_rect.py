from __future__ import annotations
from pprint import pprint
import sys
import cv2
import numpy as np

from utils.images_io import write_image
from utils.p_print import *
from .brightness_contrast import automatic_brightness_and_contrast_gray

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from parsers import DetectInnerRectParams


def show_image(img, img_name:str='', ratio:float=1.0):
    window_name = 'image' if img_name == '' else img_name
    cv2.namedWindow(window_name)
    if ratio != 1:
        _img = cv2.resize(img.copy(), (0, 0), fx=ratio,fy=ratio) if img.shape[0] > 800 else img.copy()
    else:
        _img = img.copy()
    cv2.moveWindow(window_name, 100, 100)
    cv2.imshow(window_name, _img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def _get_coordinates(coordinates: np.ndarray) -> tuple[int, int]:
    threshold = (max(coordinates) - min(coordinates)) / 2
    return (
        max(coordinates[coordinates < threshold]),
        min(coordinates[coordinates > threshold])
    )


def np_to_uint8(img: np.ndarray) -> np.ndarray:
    """Convert a np array from float to uint8
        without normalizing it
        warning: slow because no in-place clipping
        TODO: evaluate in place clip
    """
    if img.dtype == np.uint8:
        return img

    if img.dtype == np.float32:
        return (img.clip(0, 1) * 255).astype(np.uint8)

    elif img.dtype == np.uint16:
        return (img // 257).astype(np.uint8)

    raise NotImplementedError(f"Cannot convert {img.dtype} np.array to uint8")




def detect_inner_rect(
    img: np.ndarray,
    params: DetectInnerRectParams,
    do_output_img: bool=False,
    index: int = 0
) -> tuple[np.ndarray, np.ndarray | None]:
    """Returns (x0, x1, y0, y1)
    """
    padding = 24
    debug: bool = False
    verbose: bool = False
    out_img = np.ones(1)
    # do_output_img = True

    # Optimize, simplify
    img: np.ndarray = np_to_uint8(img)
    in_h, in_w = img.shape[:2]
    fallback_coords = (padding, in_w - padding, padding, in_h - padding)

    border: int = 2 if params.do_add_borders else 0

    if params.erode_kernel != 0:
        erode_kernel: np.ndarray = np.ones(
            (params.erode_kernel, params.erode_kernel),
            img.dtype
        )

    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    brightness = cv2.mean(gray_img)[0]
    contrast = gray_img.std()
    if verbose:
        print(f"{index:03} brightness: {brightness}, contrast: {contrast}")

    if brightness < 15:
        print(f"  {index:03} brightness is too low, fallback")
        return fallback_coords, None

    # if brightness < 40:
    #     try:
    #         gray_img, _, _ = automatic_brightness_and_contrast_gray(gray_img)
    #         brightness = cv2.mean(gray_img)[0]
    #         contrast = gray_img.std()
    #         print(yellow(f"  corrected, brightness: {brightness}\tcontrast: {contrast}"))
    #         # write_image(f"N:\\gray\\gray_{index:03}.png", cv2.cvtColor(gray_img, cv2.COLOR_GRAY2BGR))

    #     except:
    #         # gray_img, _, _ = automatic_brightness_and_contrast_gray(gray_img)
    #         brightness = cv2.mean(gray_img)[0]
    #         contrast = gray_img.std()
    #         print(red(f"Error: cannot apply automatic brightness&contrast"))
    #         return (0, 0, in_w, in_h), img if do_output_img else None


    if border:
        # Add border to correctly detect the outer limits
        gray_img = cv2.copyMakeBorder(
            gray_img,
            top=border,
            bottom=border,
            left=border,
            right=border,
            borderType=cv2.BORDER_CONSTANT,
            value=[0, 0, 0])


    # gray_img_debug = gray_img.copy()
    # gray_img: np.ndarray = np_to_uint8(gray_img)

    morph_kernel: np.ndarray = np.ones(
        (params.morph_kernel, params.morph_kernel),
        img.dtype
    )
    gray_img = cv2.morphologyEx(gray_img, cv2.MORPH_OPEN, morph_kernel)
    gray_img = cv2.morphologyEx(gray_img, cv2.MORPH_CLOSE, morph_kernel)

    if params.erode_kernel and params.erode_iterations:
        gray_img = cv2.erode(gray_img, erode_kernel, iterations=params.erode_iterations)

    if debug:
        write_image(f"N:\\gray\\{index:03}_00_gray.png", cv2.cvtColor(gray_img, cv2.COLOR_GRAY2BGR))

    threshold_min = params.threshold_min
    _, gray_img = cv2.threshold(
        gray_img,
        threshold_min,
        255,
        cv2.THRESH_BINARY
    )
    if debug:
        write_image(f"N:\\gray\\{index:03}_01_threshold.png", cv2.cvtColor(gray_img, cv2.COLOR_GRAY2BGR))

    contours, hierarchy = cv2.findContours(
        gray_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    if debug:
        debug_img = cv2.cvtColor(gray_img, cv2.COLOR_GRAY2BGR)
        cv2.drawContours(debug_img, contours, -1, (0, 255, 0), 2)
        write_image(f"N:\\gray\\{index:03}_02_contours.png", debug_img)

    inner_contour = None
    for hierarchy_values, contour in zip(hierarchy[0], contours):
        if hierarchy_values[0] == -1 and hierarchy_values[3] == -1:
            inner_contour = contour
            if debug:
                debug_img = cv2.cvtColor(gray_img, cv2.COLOR_GRAY2BGR)
                x, y, in_w, in_h = cv2.boundingRect(contour)
                cv2.rectangle(debug_img,
                    (x, y ),
                    (x + in_w , y + in_h),
                    (0, 0, 255), 1)
                cv2.putText(debug_img,
                    f"{hierarchy_values}",
                    (x, y+10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (255,30,12), 2)
            break
    if debug:
        write_image(f"N:\\gray\\{index:03}_03_bounding_rect.png", debug_img)

    epsilon = 0.1 * cv2.arcLength(inner_contour, True)
    polygon: np.ndarray = cv2.approxPolyDP(inner_contour, epsilon, True)
    if debug:
        debug_img = cv2.cvtColor(gray_img, cv2.COLOR_GRAY2BGR)
        cv2.drawContours(debug_img, [polygon], -1, (255, 0, 0), 1)
        cv2.imwrite(f"N:\\gray\\{index:03}_04_approxPolyDP.png", debug_img)

    outer_contour = cv2.boundingRect(contour)
    ox, oy, ow, oh = outer_contour
    if polygon.shape[0] > 4:
        print(yellow(f"  polygon shape has more than 4 points, return outer: {outer_contour}"))
        pprint(polygon)
        ox, oy, ow, oh = outer_contour
        if (
            ox > 3 * padding
            or oy > 2 * padding
            or ow < in_w - 2 * padding
            or oh < in_h - 2 * padding
        ):
            # something wrong in outer contour
            return fallback_coords, None
        return (ox-border, ow-border, oy-border, oh-border), None

    polygon = polygon.reshape((-1, 2))
    try:
        left, right = _get_coordinates(polygon[:, 0])
        top, bottom = _get_coordinates(polygon[:, 1])
    except:
        print(red("failed getting coordinates"))
        pprint(polygon)
        return fallback_coords, None

    if left - ox > padding:
        print(f"  left, ox: {left}, {ox}")
        left = ox
    if ow - right > padding:
        print(f"  right, ow: {right}, {ow}")
        right = ow
    if top - oy > padding:
        print(f"  top, oy: {top}, {oy}")
        top = oy

    # Compare to padding
    #   min crop = padding + border
    if (
        left > 3 * padding
        or top > 2 * padding
        or right < in_w - 2 * padding
        or bottom < in_h - 2 * padding
    ):
        # something wrong
        if verbose:
            print(f"  {index:03} fallback to {fallback_coords}")
        return fallback_coords, None

    coordinates = np.array([left, right, top, bottom], dtype=np.uint32)
    coordinates -= border
    if verbose:
        print(f"  {index:03} x0, x1, y0, y1: {coordinates}")

    if debug:
        # debug_img = cv2.cvtColor(gray_img, cv2.COLOR_GRAY2BGR)
        left, right, top, bottom = coordinates
        x, y = left, top
        in_w, in_h = (right-left), (bottom-top)
        rect = np.array([
            [x, y],
            [x + in_w, y],
            [x + in_w, y + in_h],
            [x, y + in_h]
        ], dtype=np.int32)
        debug_img = img.copy()
        cv2.polylines(debug_img, [rect], isClosed=True, color=(0, 255, 0), thickness=1)
        cv2.imwrite(f"N:\\gray\\{index:03}_05_final.png", debug_img)

    return coordinates, out_img if do_output_img else None




def calculate_autocrop_values(
    coordinates: list[np.ndarray],
    in_shape: list[int, int]
) -> list[int, int, int, int]:
    # coordinates: (x0, x1, y0, y1)
    # coordinates = np.ndarray(coordinates)
    # pprint(coordinates)
    print("min:", np.min(coordinates, axis=0))
    print("max:", np.max(coordinates, axis=0))
    print("in_shape:", in_shape)

    if False:
        min_coords: np.ndarray = np.min(coordinates, axis=0)
        max_coords: np.ndarray = np.max(coordinates, axis=0)
        in_h, in_w = in_shape

        coord0_min = 1.5 * max(min_coords[0], 3)
        coord2_min = 1.5 * max(min_coords[2], 3)
        w_max = 1.5 * ((in_w - max_coords[1]) + 3)
        print(f"coord0_min={coord0_min}, coord2_min={coord2_min}, w_max={w_max}")
        consolidated_coordinates: list[np.ndarray] = []
        for coord in coordinates:
            if coord[0] > coord0_min:
                print(f"(0) discard: {coord}")
                continue

            if (in_w - coord[1] + 2) > w_max:
                print(f"(1) discard: {coord} ({(in_w - coord[1])} > {w_max})")
                continue

            if coord[2] > coord2_min:
                print(f"(2) discard: {coord}")
                continue
            consolidated_coordinates.append(coord)

        print("consolidated")
        print("min:", np.min(consolidated_coordinates, axis=0))
        print("max:", np.max(consolidated_coordinates, axis=0))
        print("in_shape:", in_shape)
        min_coords: np.ndarray = np.min(consolidated_coordinates, axis=0)
        max_coords: np.ndarray = np.max(consolidated_coordinates, axis=0)

        x0, x1 = max_coords[0], min_coords[1]
        y0, y1 = max_coords[2], min_coords[3]

    else:
        min_coords: np.ndarray = np.min(coordinates, axis=0)
        max_coords: np.ndarray = np.max(coordinates, axis=0)
        in_h, in_w = in_shape

        print(f"min_coords: {min_coords}")
        print(f"max_coords: {max_coords}")

        x0, x1 = max_coords[0], min_coords[1]
        y0, y1 = max_coords[2], min_coords[3]

    coordinates = (x0, x1, y0, y1)
    print(f"temporal consolidated coords: {coordinates}")
    # crop: top, bottom, left, right
    return [y0,  in_h - y1, x0, in_w - x1]
