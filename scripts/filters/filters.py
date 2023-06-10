# -*- coding: utf-8 -*-
import sys
from copy import deepcopy
import cv2
import numpy as np
import os.path

from pprint import pprint
from filters import IMG_BORDER_HIGH_RES, IMG_BORDER_LOW_RES

from filters.utils import (
    INITIAL_FRAME_HEIGHT,
    INITIAL_FRAME_WIDTH,
    FINAL_FRAME_HEIGHT,
    FINAL_FRAME_WIDTH,
    get_dimensions_from_crop_values,
    has_add_border_task,
)
from utils.pretty_print import *


def get_mean_luma(img):
    # return brightness (x100)
    h, s, v = cv2.split(cv2.cvtColor(img, cv2.COLOR_BGR2HSV))
    return 100 * np.mean(v / np.max(v))


def crop(img, geometry=[0,0,0,0]):
    h, w, c = img.shape
    crop_up = 50
    crop_down = 50
    crop_left = 80
    crop_right = 80
    if h < 700:
        crop_up = int(crop_up / 4) * 2
        crop_down = int(crop_up / 4) * 2
        crop_left = int(crop_up / 4) * 2
        crop_right = int(crop_up / 4) * 2

    cropped_img = np.ascontiguousarray(
        img[crop_up - 1: h - crop_down - 1,
            crop_left-1: w - crop_right - 1,])
    return cropped_img



def cv2_unsharp(img: np.ndarray, radius: float, amount: float) -> np.ndarray:
    if radius == 0 or amount == 0:
        return img

    blurred = cv2.GaussianBlur(img, (0, 0), radius)
    return cv2.addWeighted(img, amount + 1, blurred, -amount, 0)




def cv2_edge_sharpen_sobel(image, k_size=3, blend_factor=0.15):
    scale = 1
    delta = 0
    ddepth = cv2.CV_16S

    image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    if True:
        grad_x = cv2.Sobel(image_gray, ddepth, 1, 0, ksize=k_size, scale=scale, delta=delta, borderType=cv2.BORDER_DEFAULT)
        grad_y = cv2.Sobel(image_gray, ddepth, 0, 1, ksize=k_size, scale=scale, delta=delta, borderType=cv2.BORDER_DEFAULT)
    else:
        grad_x = cv2.Scharr(image_gray, ddepth, 1, 0, scale=scale, delta=delta, borderType=cv2.BORDER_DEFAULT)
        grad_y = cv2.Scharr(image_gray, ddepth, 0, 1, scale=scale, delta=delta, borderType=cv2.BORDER_DEFAULT)


    abs_grad_x = cv2.convertScaleAbs(grad_x)
    abs_grad_y = cv2.convertScaleAbs(grad_y)
    abs_grad_xy = cv2.addWeighted(abs_grad_x, 0.5, abs_grad_y, 0.5, 0)

    d_b, d_g, d_r = cv2.split(image)

    mask_float = abs_grad_xy.astype(np.float32)  / 255.0
    layer_b = np.clip(cv2.multiply(d_b.astype(np.float32), mask_float), 0, 255).astype(np.uint8)
    layer_g = np.clip(cv2.multiply(d_g.astype(np.float32), mask_float), 0, 255).astype(np.uint8)
    layer_r = np.clip(cv2.multiply(d_r.astype(np.float32), mask_float), 0, 255).astype(np.uint8)

    img_mult_bgr = cv2.merge((
        layer_b.reshape(d_b.shape),
        layer_g.reshape(d_g.shape),
        layer_r.reshape(d_r.shape)))

    # img_mult_bgr = (blend_factor * img_mult_bgr.astype(np.float32)).astype(np.uint8)
    # img_output = np.clip(cv2.subtract(image.astype(np.float32), img_mult_bgr), 0, 255)
    img_output = np.clip(cv2.addWeighted(image, 1, img_mult_bgr.astype(np.uint8), blend_factor, 0), 0, 255)
    return img_output



def edge_sharpen_sobel_gray(image_gray, index, k_size=3, blend_factor=0.2):
    # cv2.imwrite(filename="frames_23_sobel/f_%05d_0.png" % (index), img=image_gray)
    scale = 1
    delta = 0
    ddepth = cv2.CV_16S

    image_gray2 = image_gray
    # cv2.GaussianBlur(image_gray, (3, 3), 0)
    grad_x = cv2.Sobel(image_gray2, ddepth, 1, 0, ksize=k_size, scale=scale, delta=delta, borderType=cv2.BORDER_DEFAULT)
    grad_y = cv2.Sobel(image_gray2, ddepth, 0, 1, ksize=k_size, scale=scale, delta=delta, borderType=cv2.BORDER_DEFAULT)
    abs_grad_x = cv2.convertScaleAbs(grad_x)
    abs_grad_y = cv2.convertScaleAbs(grad_y)
    abs_grad_xy = cv2.addWeighted(abs_grad_x, 1-blend_factor, abs_grad_y, blend_factor, 0)

    kernel = np.ones((3, 3), np.uint8)
    img_output2 =  cv2.erode(abs_grad_xy, kernel, iterations=1)

    # img_output2 = abs_grad_xy
    # cv2.imwrite(filename="frames_23_sobel/f_%05d_1.png" % (index), img=img_output2)
    return img_output2



def cv2_morphology_ex(image, type, radius, iterations):
    if type == 'MORPH_RECT':
        kernelType = cv2.MORPH_RECT
    elif type == 'MORPH_ELLIPSE':
        kernelType = cv2.MORPH_ELLIPSE
    else:
        print("Error: unrecognized kernel type")
        sys.exit()

    kernel = cv2.getStructuringElement(kernelType, (radius, radius))
    return cv2.morphologyEx(
        image,
        cv2.MORPH_OPEN,
        kernel,
        iterations)



def filter_remove_contours(in_img, thresh, maxval):
    gray_img = cv2.cvtColor(in_img, cv2.COLOR_BGR2GRAY)
    mask = np.zeros(in_img.shape, dtype=np.uint8)

    threshshold = cv2.threshold(gray_img, thresh, maxval, cv2.THRESH_BINARY)[1]
    # get bounding box coordinates from largest external contour
    contours = cv2.findContours(threshshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = contours[0] if len(contours) == 2 else contours[1]
    external_contour = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(external_contour)

    print("cropped: %d:%d %d:%d" % (y,y+h, x,x+w))
    # Crop image
    cropped_img = in_img[y:y+h, x:x+w]

    print("add padding: %d:%d %d:%d" % (y,in_img.shape[0]-(y+h), x,in_img.shape[1]-(x+w)))
    # Add padding
    out_img = cv2.copyMakeBorder(cropped_img,
        top=y, bottom=in_img.shape[0]-(y+h),
        left=x, right=in_img.shape[1]-(x+w),
        borderType=cv2.BORDER_CONSTANT,
        value=[0, 0, 0])

    return out_img



def cv2_rgb_filter(img, lut):
    b, g, r = cv2.split(img)

    matrix_r = lut['r']
    rrp = matrix_r[r.flat].reshape(r.shape)

    matrix_g = lut['g']
    ggp = matrix_g[g.flat].reshape(g.shape)

    matrix_b = lut['b']
    bbp = matrix_b[b.flat].reshape(b.shape)

    img_rgb = cv2.merge((bbp, ggp, rrp))
    return img_rgb



def cv2_geometry_filter(img, geometry):
    # print_green("cv2_geometry_filter")
    # pprint(geometry)

    # geometry = {
    #     'initial': {'h': img_height, 'w': img_width},
    #     'crop': [crop_top, crop_bottom, crop_left, crop_right],
    #     'resize': {'h': resized_height, 'w': resized_width},
    #     'crop_2': crop_2,
    #     'pad_error': pad_error,
    #     'pad': {'left': pad_left, 'right': pad_right},
    #     'final': {'h': h_final, 'w': w_final},
    # }

    # Crop the image
    crop_top, crop_bottom, crop_left, crop_right = geometry['crop']
    img_cropped = np.ascontiguousarray(img[
        crop_top : geometry['initial']['h'] - crop_bottom,
        crop_left : geometry['initial']['w'] - crop_right], dtype=np.uint8)

    # Resize
    img_resized = cv2.resize(src=img_cropped,
        dsize=(geometry['resize']['w'], geometry['resize']['h']),
        interpolation=cv2.INTER_LANCZOS4)

    # Crop the image a second time to fit to the target dimensions
    crop_2 = geometry['crop_2']
    if crop_2 is not None:
        crop_2_top, crop_2_bottom, crop_2_left, crop_2_right = crop_2
        img_resized_cropped = np.ascontiguousarray(img_resized[
            crop_2_top:img_resized.shape[0] - crop_2_bottom,
            crop_2_left:img_resized.shape[1] - crop_2_right,])
    else:
        img_resized_cropped = img_resized

    # Error case
    pad_error = geometry['pad_error']
    if pad_error is not None:
        print_red("Error: add padding but should not")
        img_resized_consolidated = cv2.copyMakeBorder(src=img_resized_cropped,
        top=pad_error[0], bottom=pad_error[1],
        left=pad_error[2], right=pad_error[3],
        borderType=cv2.BORDER_CONSTANT, value=[255, 255, 255])
    else:
        img_resized_consolidated = img_resized_cropped

    # Add padding
    img_finalized = cv2.copyMakeBorder(src=img_resized_consolidated,
        top=0, bottom=0, left=geometry['pad']['left'], right=geometry['pad']['right'],
        borderType=cv2.BORDER_CONSTANT, value=[0, 0, 0])

    return img_finalized





def calculate_geometry_parameters(shot, img, simulate:bool=False, verbose:bool=False):
    # Returns the values which will be used when resizing/cropping/padding an image
    verbose = False
    if verbose:
        print_cyan("\ncalculate_geometry_parameters\n------------------------------")
        pprint(shot['geometry'])

    if simulate:
        # Used for stats
        img_height, img_width = INITIAL_FRAME_HEIGHT, INITIAL_FRAME_WIDTH
        if has_add_border_task(shot=shot):
            img_height += 2*IMG_BORDER_LOW_RES
            img_width += 2*IMG_BORDER_LOW_RES
        img_height *= 2
        img_width *= 2
    else:
        img_height, img_width, c = img.shape
    if verbose:
        print_lightgrey(f"\t-> image shape ({img_width}, {img_height})")

    # Final width and height
    w_final = FINAL_FRAME_WIDTH
    h_final = FINAL_FRAME_HEIGHT

    # Shot geometry
    shot_geometry = shot['geometry']['shot']
    if shot_geometry is None and 'default' in shot['geometry'].keys():
        # Shot geometry may contains the default geometry when using video editor
        shot_geometry = shot['geometry']['default']
        if verbose:
            print_lightgrey(f"\t-> use default geometry")

    # Crop the image
    # Update the crop values if borders has been added
    if shot['last_task'] != 'deinterlace' or has_add_border_task(shot):
        cropped_value = [x + IMG_BORDER_HIGH_RES for x in shot_geometry['crop']]
        if verbose:
            print_lightgrey(f"\t-> image has borders")
            print(f"\t{cropped_value}")
    else:
        cropped_value = shot_geometry['crop']
        if verbose:
            print_lightgrey(f"\t-> image has no border")
            print(f"\t{cropped_value}")


    crop_top, crop_bottom, crop_left, crop_right, cropped_width, cropped_height = get_dimensions_from_crop_values(
        width=img_width, height=img_height, crop=cropped_value)
    if verbose:
        print_lightgrey(f"\t-> cropped size ({cropped_width}, {cropped_height}). Crop values: [{crop_top}, {crop_bottom}, {crop_left}, {crop_right}]")

    # (1) Crop

    # Resize image: calculate new dimensions
    target_width = shot['geometry']['target']['w']
    if target_width == -1:
        # Calculate target width
        fit_to_width = False
        keep_ratio = True
    else:
        fit_to_width = shot_geometry['fit_to_width']
        keep_ratio = shot_geometry['keep_ratio']
    crop_2 = None
    pad_error = None
    resized_height_debug = None
    resized_width_debug = None

    if keep_ratio and fit_to_width:
        # Use the width to calculate new height, then crop to final height
        if verbose:
            print_green("\tKeep ratio, fit to part width (%d)" % (target_width))
        resized_width = target_width
        resized_height = int((np.float64(cropped_height * target_width) / np.float64(cropped_width)))
        if verbose:
            print_lightgrey("\t-> resized (%d, %d)" % (resized_width, resized_height))

        # (2) Do resize

        if resized_height < h_final:
            # Error: do add white padding
            if verbose:
                print_red("\t-> Error: heigth is < final_height, add white padding")
            pad_error_top = int(((h_final - resized_height) / 2) + 0.5)
            pad_error_bottom = h_final - (resized_height + pad_error_top)
            pad_error = [pad_error_top, pad_error_bottom, 0, 0]
            # Recalculate resized_height (debug)
            resized_height_debug = resized_height + pad_error[0] + pad_error[1]

            # (3a) Do add padding (height)

        elif resized_height > h_final:
            # 2nd crop: crop height
            if verbose:
                print_lightgrey("\t-> 2nd crop: height (%d -> %d)" % (resized_height, h_final))
            crop_2_top = int((resized_height - h_final) / 2 + 0.5)
            crop_2_bottom = (resized_height - h_final) - crop_2_top
            crop_2 = [crop_2_top, crop_2_bottom, 0, 0]

            # Recalculate resized_height (debug)
            resized_height_debug = resized_height - (crop_2[0] + crop_2[1])

            # (3b) Do crop (height)

    elif keep_ratio and not fit_to_width :
        # Use the height to calculate new width, then crop to final width
        if verbose:
            print_green("\tkeep ratio, fit to final height (%d)" % (h_final))

        resized_height = h_final
        resized_width = int(((cropped_width * resized_height) / float(cropped_height))/2) * 2
        if verbose:
            print_lightgrey("\t-> resized (%d, %d)" % (resized_width, resized_height))

        # (2) Do resize

        if resized_width < target_width:
            # Error: do add white padding
            if verbose:
                print_red("\t-> Error: width is < final_width, add white padding")
            pad_error_left = int(((target_width - resized_width) / 2) + 0.5)
            pad_error_right = target_width - (resized_width + pad_error_left)
            pad_error = [0, 0, pad_error_left, pad_error_right]
            # Recalculate resized_width (debug)
            resized_width_debug = resized_width + (pad_error[2] + pad_error[3])

            # (3a) Do add padding (width)

        elif resized_width > target_width:
            # 2nd crop: crop width
            if verbose:
                print_lightgrey("\t-> 2nd crop: width (%d -> %d)" % (resized_width, target_width))
            crop_2_left = int((resized_width - target_width) / 2 + 0.5)
            crop_2_right = (resized_width - target_width) - crop_2_left
            crop_2 = [0, 0, crop_2_left, crop_2_right]

            # Recalculate resized_width (debug)
            resized_width_debug = resized_width - (crop_2[2] + crop_2[3])

            # (3b) Do crop (width)

    elif not keep_ratio and fit_to_width:
        # Adjust the image to the part width and final height
        if verbose:
            print_green("\tDo not keep ratio, fit to part width and final height (%d, %d)" % (target_width, h_final))
        resized_width = target_width
        resized_height = h_final
        if verbose:
            print_lightgrey("\t-> resized (%d, %d)" % (resized_width, resized_height))

        # (2) Do resize

    elif not keep_ratio and not fit_to_width:
        # Not possible
        pprint(shot['geometry'])
        sys.exit(print_red("Error: no valid values for keep_ratio/fit_to_width"))


    # Add padding to the cropped & resized image
    pad_left = int(((w_final - shot['geometry']['target']['w']) / 2) + 0.5)
    pad_right = w_final - (shot['geometry']['target']['w'] + pad_left)

    # (4) Add padding


    # Verifications
    resized_width_debug = resized_width if resized_width_debug is None else resized_width_debug
    resized_height_debug = resized_height if resized_height_debug is None else resized_height_debug
    # Verify resized dimensions (debug)
    if resized_width_debug != shot['geometry']['target']['w'] or resized_height_debug != h_final:
        sys.exit(print("error: resize: recalculated (w, h): (%d, %d), expected (%d, %d)" % (
            resized_width_debug, resized_height_debug, shot['geometry']['target']['w'], h_final)))
    # Verify final dimensions (debug)
    if (resized_width_debug  + pad_left + pad_right) != w_final or resized_height_debug != h_final:
        sys.exit(print("error: final: recalculated (w, h): (%d, %d), expected (%d, %d)" % (
            resized_width_debug, resized_height_debug, shot['geometry']['target']['w'], h_final)))


    geometry_parameters = {
        'initial': {'h': img_height, 'w': img_width},
        'crop': [crop_top, crop_bottom, crop_left, crop_right],
        'resize': {'h': resized_height, 'w': resized_width},
        'crop_2': crop_2,
        'pad_error': pad_error,
        'pad': {'left': pad_left, 'right': pad_right},
        'final': {'h': h_final, 'w': w_final},
    }
    if verbose:
        print_cyan("calculated geometry_parameters:")
        pprint(geometry_parameters)
        print_cyan("-----------------------------")
    # sys.exit()

    return geometry_parameters




def cv2_bilateral_filter(img, diameter, sigmaColor, sigmaSpace):
    return cv2.bilateralFilter(src=img,
        d=diameter,
        sigmaColor=sigmaColor,
        sigmaSpace=sigmaSpace)


def filter_brightness_contrast(input_img, brightness = 255, contrast = 127):
    brightness = map(brightness, 0, 510, -255, 255)
    contrast = map(contrast, 0, 254, -127, 127)
    if brightness != 0:
        if brightness > 0:
            shadow = brightness
            highlight = 255
        else:
            shadow = 0
            highlight = 255 + brightness
        alpha_b = (highlight - shadow)/255
        gamma_b = shadow
        buf = cv2.addWeighted(input_img, alpha_b, input_img, 0, gamma_b)
    else:
        buf = input_img.copy()
    if contrast != 0:
        f = float(131 * (contrast + 127)) / (127 * (131 - contrast))
        alpha_c = f
        gamma_c = 127*(1-f)
        buf = cv2.addWeighted(buf, alpha_c, buf, 0, gamma_c)
    # cv2.putText(buf,'B:{},C:{}'.format(brightness,contrast),(10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    return buf

INTERPOLATION_METHODS = {
    'bicubic': cv2.INTER_CUBIC,
    'lanczos': cv2.INTER_LANCZOS4,
    'lanczos4': cv2.INTER_LANCZOS4,
    'nearest': cv2.INTER_NEAREST,
    'linear': cv2.INTER_LINEAR,
}

def cv2_scale(image, scale:float, interpolation:str):
    # print("upscale image to %dx%d, inter=%s" % (width, height, interpolation))
    # startTime = time.time()
    try:
        cv2_interpolation = INTERPOLATION_METHODS[interpolation]
    except:
        sys.exit(print_red("error: cv2_scale: interpolation method not recognized [%s]" % (interpolation)))

    # 0.015s
    upscaled_image = cv2.resize(image,
        (int(image.shape[1]*scale), int(image.shape[0]*scale)),
        interpolation=cv2_interpolation)

    # print(">> %.04fs" % (time.time() - startTime), flush=True)
    return upscaled_image


def cv2_resize(image, width, height, interpolation):
    # print("upscale image to %dx%d, inter=%s" % (width, height, interpolation))
    # startTime = time.time()
    if interpolation == 'bicubic':
        cv2_interpolation = cv2.INTER_CUBIC
    elif interpolation in ['lanczos', 'lanczos4']:
        cv2_interpolation = cv2.INTER_LANCZOS4
    elif interpolation == 'nearest':
        cv2_interpolation = cv2.INTER_NEAREST
    elif interpolation == 'linear':
        cv2_interpolation = cv2.INTER_LINEAR
    else:
        sys.exit(print_red("error: cv2_resize: interpolation method not recognized [%s]" % (interpolation)))

    # 0.015s
    upscaled_image = cv2.resize(image, (width, height), interpolation=cv2_interpolation)

    # print(">> %.04fs" % (time.time() - startTime), flush=True)
    return upscaled_image



def map(x, in_min, in_max, out_min, out_max):
    return int((x-in_min) * (out_max-out_min) / (in_max-in_min) + out_min)


def filter_brightnessAndContrast(input_img, brightness = 255, contrast = 127):
    brightness = map(brightness, 0, 510, -255, 255)
    contrast = map(contrast, 0, 254, -127, 127)
    if brightness != 0:
        if brightness > 0:
            shadow = brightness
            highlight = 255
        else:
            shadow = 0
            highlight = 255 + brightness
        alpha_b = (highlight - shadow)/255
        gamma_b = shadow
        buf = cv2.addWeighted(input_img, alpha_b, input_img, 0, gamma_b)
    else:
        buf = input_img.copy()
    if contrast != 0:
        f = float(131 * (contrast + 127)) / (127 * (131 - contrast))
        alpha_c = f
        gamma_c = 127*(1-f)
        buf = cv2.addWeighted(buf, alpha_c, buf, 0, gamma_c)
    # cv2.putText(buf,'B:{},C:{}'.format(brightness,contrast),(10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    return buf




def filter_edge_sharpen_sobel(image, denoised_image, k_size=3, blend_factor=0.15):
    scale = 1
    delta = 0
    ddepth = cv2.CV_16S

    image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    if True:
        grad_x = cv2.Sobel(image_gray, ddepth, 1, 0, ksize=k_size, scale=scale, delta=delta, borderType=cv2.BORDER_DEFAULT)
        grad_y = cv2.Sobel(image_gray, ddepth, 0, 1, ksize=k_size, scale=scale, delta=delta, borderType=cv2.BORDER_DEFAULT)
    else:
        grad_x = cv2.Scharr(image_gray, ddepth, 1, 0, scale=scale, delta=delta, borderType=cv2.BORDER_DEFAULT)
        grad_y = cv2.Scharr(image_gray, ddepth, 0, 1, scale=scale, delta=delta, borderType=cv2.BORDER_DEFAULT)


    abs_grad_x = cv2.convertScaleAbs(grad_x)
    abs_grad_y = cv2.convertScaleAbs(grad_y)
    abs_grad_xy = cv2.addWeighted(abs_grad_x, 0.5, abs_grad_y, 0.5, 0)

    d_b, d_g, d_r = cv2.split(image)

    mask_float = abs_grad_xy.astype(np.float32)  / 255.0
    layer_b = np.clip(cv2.multiply(d_b.astype(np.float32), mask_float), 0, 255).astype(np.uint8)
    layer_g = np.clip(cv2.multiply(d_g.astype(np.float32), mask_float), 0, 255).astype(np.uint8)
    layer_r = np.clip(cv2.multiply(d_r.astype(np.float32), mask_float), 0, 255).astype(np.uint8)

    img_mult_bgr = cv2.merge((
        layer_b.reshape(d_b.shape),
        layer_g.reshape(d_g.shape),
        layer_r.reshape(d_r.shape)))

    # img_mult_bgr = (blend_factor * img_mult_bgr.astype(np.float32)).astype(np.uint8)
    # img_output = np.clip(cv2.subtract(image.astype(np.float32), img_mult_bgr), 0, 255)
    img_output = np.clip(cv2.addWeighted(image, 1, img_mult_bgr.astype(np.uint8), blend_factor, 0), 0, 255)
    return img_output



def cv2_gaussianBlur(image, radius, sigma):
    return cv2.GaussianBlur(image, (radius, radius), sigma)



def filter_fastNlMeansDenoisingColoredMulti(images, imgToDenoiseIndex, temporalWindowSize, h, hColor, templateWindowSize, searchWindowSize):
    return cv2.fastNlMeansDenoisingColoredMulti(
                                srcImgs=images,
                                imgToDenoiseIndex=imgToDenoiseIndex,
                                temporalWindowSize=temporalWindowSize,
                                h=h,
                                hColor=hColor,
                                templateWindowSize=templateWindowSize,
                                searchWindowSize=searchWindowSize)


def cv2_fastNlMeansDenoisingColored(image, h, hColor, templateWindowSize, searchWindowSize):
    return cv2.fastNlMeansDenoisingColored(
                                image,
                                None,
                                h,
                                hColor,
                                templateWindowSize,
                                searchWindowSize)


def  filter_morphologyEx(image, type, radius, iterations):
    if type == 'MORPH_RECT':
        kernelType = cv2.MORPH_RECT
    elif type == 'MORPH_ELLIPSE':
        kernelType = cv2.MORPH_ELLIPSE
    else:
        print("Error: unrecognized kernel type")
        sys.exit()

    kernel = cv2.getStructuringElement(kernelType, (radius, radius))
    return cv2.morphologyEx(
        image,
        cv2.MORPH_OPEN,
        kernel,
        iterations)




def auto_canny(image, sigma=0.33):
	# compute the median of the single channel pixel intensities
	v = np.median(image)
	# apply automatic Canny edge detection using the computed median
	lower = int(max(0, (1.0 - sigma) * v))
	upper = int(min(255, (1.0 + sigma) * v))
	edged = cv2.Canny(image, lower, upper)
	# return the edged image
	return edged

def strokeEdges(src, dst, blurKsize = 7, edgeKsize = 5):
   if blurKsize >= 3:
       blurredSrc = cv2.medianBlur(src, blurKsize)
       graySrc = cv2.cvtColor(blurredSrc, cv2.COLOR_BGR2GRAY)
   else:
       graySrc = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
   cv2.Laplacian(graySrc, cv2.CV_8U, graySrc, ksize = edgeKsize)
   normalizedInverseAlpha = (1.0 / 255) * (255 - graySrc)
   channels = cv2.split(src)
   for channel in channels:
       channel[:] = channel * normalizedInverseAlpha
   cv2.merge(channels, dst)



def improve_edges(input_filepath, output_filepath):
    img_input_rgb = cv2.imread(input_filepath, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img_input_rgb, cv2.COLOR_BGR2GRAY)

    canny = cv2.Canny(gray,240,255)
    b, g, r = cv2.split(img_input_rgb)
    layer_b = np.clip(cv2.multiply(b, canny), 0, 255).astype(np.uint8)
    layer_g = np.clip(cv2.multiply(g, canny), 0, 255).astype(np.uint8)
    layer_r = np.clip(cv2.multiply(r, canny), 0, 255).astype(np.uint8)

    blend_factor = 0.1
    bbp = cv2.addWeighted(b, 1, layer_b, blend_factor, 0).reshape(b.shape)
    ggp = cv2.addWeighted(g, 1, layer_g, blend_factor, 0).reshape(g.shape)
    rrp = cv2.addWeighted(r, 1, layer_r, blend_factor, 0).reshape(r.shape)
    img_output = cv2.merge((bbp, ggp, rrp))

    cv2.imwrite(output_filepath, img_output)

