from __future__ import annotations
import cv2
import numpy as np

from utils.p_print import *
from .brightness_contrast import automatic_brightness_and_contrast_gray

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from parsers import DetectInnerRectParams




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
    verbose = False
    debug: bool = True

    # Optimize, simplify
    img: np.ndarray = np_to_uint8(img)

    border: int = 2 if params.do_add_borders else 0
    diameter = int(params.morph_kernel_radius * 2 + 1)
    morph_kernel: np.ndarray = np.ones((diameter, diameter), img.dtype)
    if params.erode_kernel_radius != 0:
        diameter = int(params.erode_kernel_radius * 2 + 1)
        erode_kernel: np.ndarray = np.ones((diameter, diameter), img.dtype)

    in_h, in_w = img.shape[:2]
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
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

    brightness_estimate = cv2.mean(gray_img)[0]
    contrast_estimate = gray_img.std()
    # print(yellow(f"\tmean: {brightness_estimate}\tcontrast: {contrast_estimate}"))

    if brightness_estimate < 25:
        try:
            gray_img, _, _ = automatic_brightness_and_contrast_gray(gray_img)
            brightness_estimate = cv2.mean(gray_img)[0]
            contrast_estimate = gray_img.std()
            print(yellow(f"\tcorrected, mean: {brightness_estimate}\tcontrast: {contrast_estimate}"))
        except:
            print(red(f"Error: cannot apply automatic brightness&contrast"))
            return (0, 0, in_w, in_h), img if do_output_img else None

    gray_img_debug = gray_img.copy()
    # gray_img: np.ndarray = np_to_uint8(gray_img)
    _, gray_img = cv2.threshold(
        gray_img,
        params.threshold_min,
        255,
        cv2.THRESH_BINARY
    )


    # if debug:
    #     global index
    #     # cv2.drawContours(gray_img, [polygon], -1, (0, 255, 0), 1)
    #     cv2.imwrite(f"mask_{index:03}.png", gray_img)
    #     # show_image(img_debug, f"{i}")
    #     index += 1

    gray_img = cv2.morphologyEx(gray_img, cv2.MORPH_OPEN, morph_kernel)
    gray_img = cv2.morphologyEx(gray_img, cv2.MORPH_CLOSE, morph_kernel)

    if params.erode_kernel_radius != 0:
        gray_img = cv2.erode(
            gray_img,
            erode_kernel,
            iterations=params.erode_iterations
        )

    contours, hierarchy = cv2.findContours(
        gray_img,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    outer_contour = None
    for hierarchy_values, contour in zip(hierarchy[0], contours):
        if hierarchy_values[0] == -1 and hierarchy_values[3] == -1:
            outer_contour = contour

            if False:
                debug_img = cv2.cvtColor(gray_img_debug, cv2.COLOR_GRAY2BGR)
                x,y,w,h = cv2.boundingRect(contour)
                cv2.rectangle(debug_img,
                    (x, y ),
                    (x + w , y + h),
                    (0, 0, 255), 1)
                cv2.putText(debug_img,
                    f"{hierarchy_values}",
                    (x, y+10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (255,30,12), 2)
                cv2.imwrite(f"mask_{index:03}.png", debug_img)
            break

    epsilon = 0.1 * cv2.arcLength(outer_contour, True)
    polygon: np.ndarray = cv2.approxPolyDP(outer_contour, epsilon, True)

    if False:
        debug_img = cv2.cvtColor(gray_img_debug, cv2.COLOR_GRAY2BGR)
        cv2.drawContours(debug_img, [polygon], -1, (0, 255, 0), 1)
        cv2.imwrite(f"mask_{index:03}.png", debug_img)
        # show_image(img_debug, f"{i}")

    if polygon.shape[0] < 4:
        print(red(f"Polygon not found"))
        print(lightcyan(f"\tshape:{polygon.shape}"))
        return None, None
        # print("hierarchy")
        # pprint(hierarchy)
        # print("contours")
        # pprint(contours)

        img_debug = cv2.cvtColor(gray_img.copy(), cv2.COLOR_GRAY2BGR)
        if True:
            # show all points
            contour = outer_contour.reshape(len(outer_contour),2)
            for (_x, _y) in contour:
                cv2.rectangle(img_debug, (_x-1, _y-1), (_x+1, _y+1), (0,255,0), 1)
            show_image(img_debug, f"{i}")

        if True:
            # Show all contours
            for hierarchy_values, contour in zip(hierarchy[0], contours):
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(img_debug,
                    (x, y ), (x + w , y + h),
                    (0, 0, 255), 1)
                cv2.putText(img_debug,
                    f"{hierarchy_values}",
                    (x, y+10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (255,30,12), 2)
            show_image(img_debug, f"{i}")

    contour = polygon.reshape(len(polygon), 2)
    x0, x1 = _get_coordinates(contour[:, 0:1])
    y0, y1 = _get_coordinates(contour[:, 1:])
    coordinates = np.array([max(0, x - border) for x in (x0, x1, y0, y1)])
    if verbose:
        print(f"rect: {coordinates}")

    if do_output_img:
        out_img = np.copy(img)
        cv2.rectangle(out_img,
            (coordinates[0], coordinates[2]),
            (coordinates[1], coordinates[3]),
            (0, 255, 0),
            1
        )
        # if debug:
        #     cv2.rectangle(img_debug, (x0 +1, y1+1), (x1-1, y0-1), (0,0,255), 2)
        #     cv2.imwrite("mask_final.png", img_debug)
        #     show_image(img_debug, f"{i}")
    else:
        out_img = np.ones(1)

    return coordinates, out_img if do_output_img else None
