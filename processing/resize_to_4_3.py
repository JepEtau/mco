from __future__ import annotations
import cv2
from dataclasses import dataclass
import numpy as np
from pprint import pprint
from processing.resize import PillowResizeAlgorithm, np_to_float32, pillow_resize
from utils.p_print import *
from PIL import Image


# This node converts an image to a 4:3 frame
# For this node, we ASSUME that this frame,
#   will not have the correct width when resized to the final height
#   has its height > final frame (do not upscale this frame)
#
# This node crops the initial image, resizes it
#   to have a consistent width among all scenes,
#   then a second crop is done and finally,
#   black borders are added (left and right borders)
#
# - Initial image size, eg. 1440x1152
# - Final frame 1440x1080  frame (4:3)
# - The min width of a set of scene calculated to 1350 (example)
#
# 1) Crop the image:
#       to remove dirty borders
#       obtain a clean rectangle, specially when the image has been rotated
# 2) Resize this cropped image:
#       a) keep ratio
#       b) without keeping ratio (see note)
#       c) if fit_to_width is set, then resize to width (1350px)
# 3) Crop the image to obtain a frame of 1350px:
#       a) crop left/right borders if wider than 1350px
#       b) crop top/down borders if this resized image has a width < 1350px (see note)
# 4) Add left and right borders
#
# Note: resizing without keeping the same ratio as the original image is a solution
#       to not crop both top/bottom borders on step 3
#       This can be done if the rartio is not too far from the original ratio
#
# Inputs:
#   - initial image size
#   - values of the 1st crop
#   - the dimension of the resized image
#   - final frame's dimensions


@dataclass(slots=True)
class ConvertTo43Params:
    # Initial crop:
    #   this crop is calculated before (external tool)
    #   manually or using an autocrop tool
    crop: tuple[int, int, int, int] | None
    # Keep ratio when resizing
    keep_ratio: bool
    # If true, crop top/bottom borders once image resized
    fit_to_width: bool
    # Final height is usually 1080px (fullHD)
    final_height: int
    # Scene width must be less than or equal to 4/3 of final_height
    scene_width: int
    # TODO: add a flag to allow upscaling this frame



@dataclass(slots=True)
class TransformationValues:
    # 1) crop: [top, bottom, left, right]
    crop: tuple[int, int, int, int]
    # 2) resize to [w, h]
    resize_to: tuple[int, int]
    # 3) crop_2
    crop_2: tuple[int, int, int, int] | None
    # 4) pad [left, right]
    borders: tuple[int, int]
    out_size: tuple[int, int]
    # Add borders to indicate that something wrong happened
    err_borders: tuple[int, int, int, int] | None



def dimensions_from_crop(
    in_w: int,
    in_h: int,
    crop: tuple[int, int, int, int]
) -> tuple[int, int, int, int]:
    c_t, c_b, c_l, c_r = crop
    c_w = in_w - (c_l + c_r)
    c_h = in_h - (c_t + c_b)
    return c_t, c_b, c_l, c_r, c_w, c_h



def calculate_transformation_values(
    in_w: int,
    in_h: int,
    out_w: int,
    params: ConvertTo43Params,
    verbose: bool = False
):
    # Returns the values which will be used when resizing/cropping/padding an image
    out_h = params.final_height
    scene_w = params.scene_width

    # (1) Crop
    c_t, c_b, c_l, c_r, c_w, c_h = dimensions_from_crop(
        in_w, in_h, params.crop
    )
    if verbose:
        print(lightgrey(f"\t-> cropped size ({c_w}, {c_h}). Crop values: [{c_t}, {c_b}, {c_l}, {c_r}]"))

    # (2) Resize image: calculate new dimensions
    if scene_w < 0:
        # Calculate target width because we ignore the scene width
        # This is usefull when "simulating" the process among all scenes from
        # an episode to calculate the maximum width we will use
        # to generate the episode
        fit_to_width = False
        keep_ratio = True
    else:
        fit_to_width = params.fit_to_width
        keep_ratio = params.keep_ratio

    crop_2: tuple[int, int, int, int] | None = None
    err_borders: tuple[int, int, int, int] | None = None
    resized_h_debug = None
    resized_w_debug = None

    # (2) Resize
    if keep_ratio and fit_to_width:
        # (2a) & (2c)

        # Use the scene width to calculate new height, then crop to final height
        if verbose:
            print(green(f"\tKeep ratio, fit to part width {scene_w}"))
        resized_w, resized_h = scene_w, int(float(c_h * scene_w) / float(c_w))
        if verbose:
            print(lightgrey(f"\t-> resized ({resized_w}, {resized_h})"))

        if resized_h < out_h:
            # Warning: add top/bottom borders to inform the user
            # that the input image height is less than than the final height
            # i.e. upscale rather than downscale
            print(red("\t-> Error: heigth is < final_height, add green padding"))
            err_border_top = int(((out_h - resized_h) / 2) + 0.5)
            err_border_bottom = out_h - (resized_h + err_border_top)
            err_borders = [err_border_top, err_border_bottom, 0, 0]
            # Recalculate resized_height (debug)
            resized_h_debug = resized_h + sum(err_borders)

        elif resized_h > out_h:
            # (3b)
            print(lightgrey(f"\t-> 2nd crop: height ({resized_h} -> {out_h})"))
            crop_2_top = int((resized_h - out_h) / 2 + 0.5)
            crop_2_bottom = (resized_h - out_h) - crop_2_top
            crop_2 = [crop_2_top, crop_2_bottom, 0, 0]
            # Recalculate resized_height (debug)
            resized_h_debug = resized_h - sum(crop_2)

    elif keep_ratio and not fit_to_width :
        # Use the height to calculate new width, then crop to final width
        if verbose:
            print(green(f"\tkeep ratio, fit to final height ({out_h})"))
        resized_w, resized_h = int(((c_w * out_h) / float(c_h)) / 2) * 2, out_h
        if verbose:
            print(lightgrey(f"\t-> resized ({resized_w}, {resized_h})"))

        if resized_w < scene_w:
            # Error: add borders because the resized image has its width
            #   less than the scen width
            if verbose:
                print(red("\t-> Error: width is < final_width, add white padding"))
            err_border_left = int(((scene_w - resized_w) / 2) + 0.5)
            err_border_right = scene_w - (resized_w + err_border_left)
            err_borders = [0, 0, err_border_left, err_border_right]
            # Recalculate width for debug
            resized_w_debug = resized_w + sum(err_borders)

        elif resized_w > scene_w:
            # (3a)
            if verbose:
                print(lightgrey(f"\t-> 2nd crop: width {resized_w} -> {scene_w}"))
            crop_2_left = int(float(resized_w - scene_w) / 2 + 0.5)
            crop_2_right = (resized_w - scene_w) - crop_2_left
            crop_2 = [0, 0, crop_2_left, crop_2_right]
            # Recalculate width for debug
            resized_w_debug = resized_w - sum(crop_2)

    elif not keep_ratio and fit_to_width:
        # Adjust the image to the scene width and final height
        if verbose:
            print(green(f"\tDo not keep ratio, fit to part width and final height ({scene_w}, {out_h})"))
        resized_w, resized_h = scene_w, out_h
        if verbose:
            print(lightgrey(f"\t-> resized to ({resized_w}, {resized_h})"))

    elif not keep_ratio and not fit_to_width:
        # Erroneous
        raise ValueError(red("Error: no valid values for keep_ratio/fit_to_width"))

    # (4) Add borders to the cropped & resized image
    border_left = int(((out_w - scene_w) / 2) + 0.5)
    border_right = out_w - (scene_w + border_left)

    # Verifications (debug)
    resized_w_debug = resized_w if resized_w_debug is None else resized_w_debug
    resized_h_debug = resized_h if resized_h_debug is None else resized_h_debug
    # Verify resized dimensions (debug)
    if resized_w_debug != scene_w or resized_h_debug != out_h:
        raise ValueError(
            f"Error: resizing: ({resized_w_debug}, {resized_h_debug}), expecting ({scene_w}, {out_h})"
        )
    # Verify final dimensions (debug)
    if (resized_w_debug + border_left + border_right) != out_w or resized_h_debug != out_h:
        raise ValueError(
            f"Error: final: ({resized_w_debug}, {resized_h_debug}), expecting ({scene_w}, {out_h})"
        )

    transformations = TransformationValues(
        crop=[c_t, c_b, c_l, c_r],
        resize_to=[resized_w, resized_h],
        crop_2=crop_2,
        borders=[border_left, border_right],
        out_size=[out_w, out_h],
        err_borders=err_borders,
    )
    if verbose:
        print(lightcyan("transformations:"))
        pprint(transformations)
        print(lightcyan("-----------------------------"))

    return transformations


def resize_to_4_3(
    img: np.ndarray,
    transformation: TransformationValues,
) -> np.ndarray:
    in_h, in_w = img.shape[:2]

    # (1)
    top, bottom, left, right = transformation.crop
    cropped_img: np.ndarray = np.ascontiguousarray(
        img[top : in_h - bottom, left : in_w - right, :]
    )
    h1, w1 = cropped_img.shape[:2]

    # (2)

    h2, w2 = transformation.resize_to
    interpolation_alg: str = (
        'lanczos' if w2 > w1 or h2 > h1
        else 'bicubic'
    )
    # pimg = Image.fromarray(cropped_img)
    # pimg = pimg.resize(
    #     transformation.resize_to,
    #     resample=PillowResizeAlgorithm[interpolation_alg],
    # )
    # resized_img = np.asarray(pimg)
    resized_img: np.ndarray = pillow_resize(
        cropped_img,
        transformation.resize_to[0],
        transformation.resize_to[1],
        PillowResizeAlgorithm['lanczos'],
    )

    # (3)
    crop_2 = transformation.crop_2
    if crop_2 is not None:
        top, bottom, left, right = crop_2
        h, w = resized_img.shape[:2]
        resized_img = np.ascontiguousarray(
            resized_img[top : h - bottom, left : w - right, :]
        )

    # Erroneous geometry: add white borders
    err_borders = transformation.err_borders
    if err_borders is not None:
        resized_img = cv2.copyMakeBorder(
            resized_img,
            top=err_borders[0], bottom=err_borders[1],
            left=err_borders[2], right=err_borders[3],
            borderType=cv2.BORDER_CONSTANT,
            value=[255, 255, 255]
        )

    # (4)
    return cv2.copyMakeBorder(
        resized_img,
        top=0,
        bottom=0,
        left=transformation.borders[0],
        right=transformation.borders[1],
        borderType=cv2.BORDER_CONSTANT,
        value=[0, 0, 0]
    )

