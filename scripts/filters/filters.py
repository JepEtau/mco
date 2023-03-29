# -*- coding: utf-8 -*-
import sys
from copy import deepcopy
import cv2
import numpy as np
import os.path
import platform
import time

from skimage.filters import unsharp_mask
from skimage.util import img_as_ubyte
from skimage.util import img_as_float
# from skimage.io import imshow, imread
# from skimage.color import rgb2yuv, rgb2hsv, rgb2gray, yuv2rgb, hsv2rgb
# from skimage.restoration import denoise_tv_bregman
from skimage.restoration import (
    calibrate_denoiser,
    denoise_wavelet,
    denoise_tv_chambolle,
    denoise_nl_means,
    denoise_bilateral,
    estimate_sigma)
from skimage.morphology import (
    remove_small_holes,
)
# from functools import partial
from pprint import pprint
from skimage import color
from skimage import restoration
from filters.ffmpeg_utils import clean_ffmpeg_filter

from utils.common import get_dimensions_from_crop_values
from utils.pretty_print import *




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


def sk_unsharp_mask(image, radius, amount):
    tmp = img_as_float(image)
    tmp = unsharp_mask(tmp,
        radius,
        amount,
        preserve_range=False,
        channel_axis=2)
    return img_as_ubyte(tmp)



def filter_remove_small_holes(in_img, area_threshold=64, connectivity=1):
    tmp = remove_small_holes(in_img, area_threshold, connectivity)
    img_out = img_as_ubyte(tmp)
    return img_out


def filter_nlmeans(img):
    # psf = np.ones((5, 5)) / 25
    # tmp = restoration.wiener(img,psf,1100)

    # sigma_est = estimate_sigma(img, channel_axis=-1, average_sigmas=True)
    # tmp = denoise_wavelet(img, channel_axis=-1)

    sigma = 0.05
    tmp = restoration.denoise_nl_means(img,
        3, 3, 0.2,
        fast_mode=True,
        channel_axis=-1,
        sigma=sigma)
    img_out = img_as_ubyte(tmp)
    return img_out



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
    abs_grad_xy = cv2.addWeighted(abs_grad_x, 0.5, abs_grad_y, 0.5, 0)

    kernel = np.ones((3, 3), np.uint8)
    img_output2 =  cv2.erode(abs_grad_xy, kernel, iterations=1)

    # img_output2 = abs_grad_xy
    cv2.imwrite(filename="frames_23_sobel/f_%05d_1.png" % (index), img=img_output2)
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


# openCV: superRes
# pip install opencv-contrib-python
from cv2 import dnn_superres
def filter_scale_superres(filter, image, out_img_filepath=None):
    # sys.exit("superres is not supported")
    print("\tfilter=%s" % (filter))
    method = filter[len('superres='):]
    print("\tmethod=%s" % (method))
    print("\toutput file: %s" % (out_img_filepath))

    sr = dnn_superres.DnnSuperResImpl_create()
    # method = 'edsr'
    # method = 'espcn'
    # method = 'fsrcnn'

    # input_image = image[0:int(image.shape[1]/2),
    #                 0:int(image.shape[0]/2)]
    input_image = image
    # cv2.imshow("image",input_image)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    if method == 'edsr':
        # slow and bad quality for g_reportage
        edsr_2x_filepath = "EDSR_x2.pb"
        sr.readModel(edsr_2x_filepath)
        print("\tmodel read")
        sr.setModel("edsr", 2)
        scale = sr.getScale()
        print("\tmodel set: scale=%d" % (scale))
        result = sr.upsample(input_image)
        print("\tdone")

    elif method == 'espcn':
        espcn_2x_filepath = "ESPCN_x2.pb"
        sr.readModel(espcn_2x_filepath)
        sr.setModel("espcn", 2)
        result = sr.upsample(input_image)
        print("done")

    elif method == 'fsrcnn':
        fsrcnn_2x_filepath = "FSRCNN_x2.pb"
        sr.readModel(fsrcnn_2x_filepath)
        sr.setModel("fsrcnn", 2)
        result = sr.upsample(input_image)

    elif method == 'lapsrn':
        lapsrn_2x_filepath = "LapSRN_x2.pb"
        sr.readModel(lapsrn_2x_filepath)
        sr.setModel("lapsrn", 2)
        result = sr.upsample(input_image)
    else:
        print("filters_scale_superres: option is not recognized: %s" % (method))
        sys.exit("filters_scale_superres: option is not recognized: %s" % (method))


    print("wite file to %s" % (out_img_filepath))
    cv2.imwrite(out_img_filepath, result)
    return result




def filter_pre_upscale(frame, img):
    print("\t\tpre_upscale: %s -> %s" % (os.path.split(frame['filepath']['deinterlace'])[1], os.path.split(frame['filepath']['pre_upscale'])[1]))
    if 'pre_upscale' not in frame['filters']['opencv'].keys():
        print("Warning: no pre_upscale filter defined")
        return None

    if frame['filters']['opencv']['pre_upscale'] is not None:
        return filter_opencv(img, frame['filters']['opencv']['pre_upscale'], multi=False)

    return None




def filter_denoise(frame, img):
    # print("denoise: %s -> %s" % (frame['filepath']['upscale'], frame['filepath']['denoise']))



    if 'denoise' not in frame['filters']['opencv'].keys():
        print("Warning: no denoise filter defined")
        return None

    if frame['filters']['opencv']['denoise'] is not None:
        return filter_opencv(img, frame['filters']['opencv']['denoise'], multi=False)


    # elif frame['filters']['ffmpeg']['denoise'] is not None:
    #     print("Error: FFMPEG denoise filter shall be implemented before this function call")
    # else:
    #     print("warning: no denoise filter defined")
    return None



def filter_sharpen(frame, img):
    # print("sharpen: %s -> %s" % (frame['filepath']['denoise'], frame['filepath']['sharpen']))
    if frame['filters']['opencv']['sharpen'] is not None:
        imgTmp = filter_opencv(img, frame['filters']['opencv']['sharpen'], multi=False)
        return imgTmp
    # else:
    #     print("warning: no sharpen filter defined")
    return None




def filter_upscale(frame, img):
    # print("upscale: %s -> %s" % (frame['filepath']['pre_upscale'], frame['filepath']['upscale']))
    filter_array = frame['filters']['opencv']['upscale']
    if filter_array is not None:
        width = frame['dimensions']['upscale']['w']
        height = frame['dimensions']['upscale']['h']
        for i in range(len(filter_array)):
            filter_array[i] = filter_array[i].replace("height_upscale", "%d" % (height))
            filter_array[i] = filter_array[i].replace("width_upscale", "%d" % (width))
        imgTmp = filter_opencv(img, filter_array, multi=False)
        return imgTmp
    else:
        raise Exception("error: opencv: no upscale filter defined to generate %s" % (frame['filepath']['upscale']))
    return None



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


def filter_rgb(frame, img):
    # print("rgb: %s -> %s" % (frame['filepath']['sharpen'], frame['filepath']['rgb']))
    b, g, r = cv2.split(img)

    matrix_r = frame['curves']['lut']['r']
    matrix_g = frame['curves']['lut']['g']
    matrix_b = frame['curves']['lut']['b']

    rrp = matrix_r[r.flat].reshape(r.shape)
    ggp = matrix_g[g.flat].reshape(g.shape)
    bbp = matrix_b[b.flat].reshape(b.shape)

    img_rgb = cv2.merge((bbp, ggp, rrp))
    return img_rgb


def stabilize_image(frame, img):
    img_stabilized = img
    if frame['stabilize']['dx_dy'] is not None:
        if frame['stabilize']['dx_dy'][1] >= 1:
            # Add padding
            dy = abs(int(frame['stabilize']['dx_dy'][1]))

            img_tmp = img[
                0:img.shape[0] - dy,
                0:img.shape[1]
            ]
            img_stabilized = cv2.copyMakeBorder(img_tmp,
                top=dy, bottom=0,
                left=0, right=0,
                borderType=cv2.BORDER_CONSTANT,
                value=[0, 0, 0])
        elif frame['stabilize']['dx_dy'][1] <= -1:
            dy = abs(int(frame['stabilize']['dx_dy'][1]))
            # Remove
            img_tmp = img[
                dy:img.shape[0],
                0:img.shape[1]
            ]
            img_stabilized = cv2.copyMakeBorder(img_tmp,
                top = 0, bottom=dy,
                left=0, right=0,
                borderType=cv2.BORDER_CONSTANT,
                value=[0, 0, 0])

    return img_stabilized


def cv2_geometry_filter(img, geometry):
    # print_green("cv2_geometry_filter")
    # pprint(geometry)

    # geometry = {
    #     'initial': {'h': h, 'w': w},
    #     'crop': [c_t, c_b, c_l, c_r],
    #     'resize': {'h': h_final, 'w': w_tmp},
    #     'crop_2': {'x0': x0, 'x1': x1},
    #     'pad': {'left': pad_left, 'right': pad_right},
    #     'final': {'h': h_final, 'w': w_final},
    # }

    # Crop the image
    c_t, c_b, c_l, c_r = geometry['crop']
    img_cropped = np.ascontiguousarray(img[
        c_t : geometry['initial']['h'] - c_b,
        c_l : geometry['initial']['w'] - c_r], dtype=np.uint8)

    # Resize
    img_resized = cv2.resize(src=img_cropped,
        dsize=(geometry['resize']['w'], geometry['resize']['h']),
        interpolation=cv2.INTER_LANCZOS4)

    # Crop the image a second time to fit to the part dimensions
    if geometry['crop_2']['x0'] is not None:
        img_resized_cropped = np.ascontiguousarray(img_resized[
            0:geometry['final']['h'],
            geometry['crop_2']['x0']:geometry['crop_2']['x1'],])
    else:
        img_resized_cropped = img_resized

    img_finalized = cv2.copyMakeBorder(src=img_resized_cropped,
        top=0, bottom=0, left=geometry['pad']['left'], right=geometry['pad']['right'],
        borderType=cv2.BORDER_CONSTANT, value=[0, 0, 0])

    return img_finalized



def calculate_geometry_parameters(shot, img):
    # Returns the values which will be used when resizing/cropping/padding an image

    # print("crop and resize: %s -> %s" % (frame['filepath']['sharpen'], frame['filepath']['geometry']))
    h, w, c = img.shape

    # print("------------------")
    # pprint(frame['geometry'])
    # print(img.shape)
    # if (frame['geometry'] is None
    # or (frame['geometry']['part'] is None and frame['geometry']['shot'] is None)):
    #     print("Error: no geometry defined, cannot modify the image")
    #     return None


    # Crop
    try:
        c_t_p, c_b_p, c_l_p, c_r_p, c_w_p, c_h_p = get_dimensions_from_crop_values(
            width=w, height=h, crop=shot['geometry']['part']['crop'])
        try:
            # Use the customized geometry
            # print("use the customized geometry")
            c_t, c_b, c_l, c_r, c_w, c_h = get_dimensions_from_crop_values(
                width=w, height=h, crop=shot['geometry']['shot']['crop'])
        except:
            # Use the part geometry
            # print:("use the part geometry")
            c_t, c_b, c_l, c_r, c_w, c_h = get_dimensions_from_crop_values(
                width=w, height=h, crop=shot['geometry']['part']['crop'])
            # print("\t-> use the part geometry %d:%d:%d:%d  %dx%d" % (c_t, c_b, c_l, c_r, c_w, c_h))

        # Crop the image
        # img = np.ascontiguousarray(img[c_t:h-c_b, c_l:w-c_r], dtype=np.uint8)
    except:
        c_t_p, c_b_p, c_l_p, c_r_p, c_w_p, c_h_p = get_dimensions_from_crop_values(
            width=w, height=h, crop=[0,0,0,0])
        c_t, c_b, c_l, c_r, c_w, c_h = get_dimensions_from_crop_values(
            width=w, height=h, crop=[0,0,0,0])


    # Final width and height
    w_final = shot['geometry']['dimensions']['final']['w']
    h_final = shot['geometry']['dimensions']['final']['h']

    # Calculate resized width for both part and (part or custom)
    w_p_tmp = int((c_w_p * h_final) / float(c_h_p))
    w_tmp = int((c_w * h_final) / float(c_h))
    # print("cropped image: ", img.shape)
    # pprint("w_p_tmp=%d, w_tmp=%d" % (w_p_tmp, w_tmp))
    # pprint("h_final=%d" % (h_final))

    # Resize
    # img_resized = cv2.resize(img,
    #     (w_tmp, h_final),
    #     interpolation=cv2.INTER_LANCZOS4)
    # print("img_resized before adjustments: ", img_resized.shape)

    # Verify custom vs part cropped and resized image
    x0 = x1 = None
    if w_tmp != w_p_tmp:
        # This is a custom geometry, width shall be the same as the part's one
        # It is done AFTER resizing because the resize may be different:
        #   i.e. when keep_ratio is disabled (custom width)
        if w_tmp > w_p_tmp:
            # Crop the image
            # Calculate the position of the left crop of the part after resizing
            c_l_p_resized = int(((c_l_p) * h_final) / float(c_h_p))
            c_l_resized = int(((c_l) * h_final) / float(c_h))
            x0 = c_l_resized - c_l_p_resized
            x1 = w_p_tmp + x0
            # print("crop the image: x0=%d, x1=%d, (w_tmp + x0)=%d" % (x0, x1, w_tmp+x0))
            if x1 > w_tmp:
                # Crop is too big on the left
                # print("crop is too big")
                x0 = w_tmp - w_p_tmp
                x1 = w_tmp
            # print("crop the image: c_l_p_resized=%d, c_l_resized=%d, x0=%d, x1=%d -> new resized width=%d" % (
                # c_l_p_resized, c_l_resized, x0, x1, x1 - x0))
            # img_resized_final = np.ascontiguousarray(img_resized[0:h_final,  x0:x1,])
        elif w_p_tmp > w_tmp:
            # Add RED padding, for debug
            sys.exit(print_red("Error: incorrect shot geometry"))



    # print("img_resized after adjustments: ", img_resized_final.shape)
    # print("   w_resized should be: %s" % (w_p_tmp))

    # Add padding to the cropped & resized image
    pad_left = int(((w_final - w_p_tmp) / 2) + 0.5)
    pad_right = w_final - (w_p_tmp + pad_left)
    # img_finalized = cv2.copyMakeBorder(img_resized_final, 0, 0, pad_left, pad_right,
    #     cv2.BORDER_CONSTANT, value=[0, 0, 0])

    # print("img_finalized: ", img_finalized.shape)
    # sys.exit()

    geometry = {
        'initial': {'h': h, 'w': w},
        'crop': [c_t, c_b, c_l, c_r],
        'resize': {'h': h_final, 'w': w_tmp},
        'crop_2': {'x0': x0, 'x1': x1},
        'pad': {'left': pad_left, 'right': pad_right},
        'final': {'h': h_final, 'w': w_final},
    }

    return geometry



def filter_richardson_lucy(img, psf=None, num_iter=30):
    if psf is None:
        psf = np.ones((5, 5)) / 25
    # data = convolve2d(img, psf, 'auto')
    # tmp = cv2.cvtColor(input_img, cv2.COLOR_BGR2GRAY)
    # tmp2 = img_as_float(tmp)
    tmp = restoration.richardson_lucy(img, psf)
    img_out = img_as_ubyte(tmp)
    return img_out


def filter_nlmeans(img):
    # psf = np.ones((5, 5)) / 25
    # tmp = restoration.wiener(img,psf,1100)

    # sigma_est = estimate_sigma(img, channel_axis=-1, average_sigmas=True)
    # tmp = denoise_wavelet(img, channel_axis=-1)

    sigma = 0.05
    tmp = restoration.denoise_nl_means(img,
        3, 3, 0.2,
        fast_mode=True,
        channel_axis=-1,
        sigma=sigma)
    img_out = img_as_ubyte(tmp)
    return img_out


def filter_bilateral_sk(img, sigma_color, sigma_spatial):
    # Too long compared to opencv
    # img_float = img_as_float(img)
    tmp = denoise_bilateral(img,
        sigma_color=sigma_color if sigma_color != 0 else None,
        sigma_spatial=sigma_spatial,
        channel_axis=2)
    img_out = img_as_ubyte(tmp)
    return img_out


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


def cv2_scale(image, scale, interpolation):
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
        sys.exit(print_red("error: cv2_scale: interpolation method not recognized [%s]" % (interpolation)))

    # 0.015s
    upscaled_image = cv2.resize(image,
        (image.shape[1]*scale, image.shape[0]*scale),
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
    elif interpolation == 'superres':
        upscaled_image = filter_scale_superres(image, width, height)
        # print(">> %.04fs" % (time.time() - startTime), flush=True)
        return upscaled_image
    else:
        sys.exit(print_red("error: cv2_resize: interpolation method not recognized [%s]" % (interpolation)))

    # 0.015s
    upscaled_image = cv2.resize(image, (width, height), interpolation=cv2_interpolation)

    # print(">> %.04fs" % (time.time() - startTime), flush=True)
    return upscaled_image



def mco_unsharp_mask(image, kernel_size=(5, 5), sigma=1.0, amount=1.0, threshold=0):
    """Return a sharpened version of the image, using an unsharp mask."""
    # For details on unsharp masking, see:
    # https://en.wikipedia.org/wiki/Unsharp_masking
    # https://homepages.inf.ed.ac.uk/rbf/HIPR2/unsharp.htm
    blurred = cv2.GaussianBlur(image, kernel_size, sigma)
    sharpened = float(amount + 1) * image - float(amount) * blurred
    sharpened = np.maximum(sharpened, np.zeros(sharpened.shape))
    sharpened = np.minimum(sharpened, 255 * np.ones(sharpened.shape))
    sharpened = sharpened.round().astype(np.uint8)
    if threshold > 0:
        low_contrast_mask = np.absolute(image - blurred) < threshold
        np.copyto(sharpened, image, where=low_contrast_mask)
    return sharpened



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



def filter_opencv(images, filters, multi=True):
    if not multi:
        if type(images) is list:
            image = images[0]
        else:
            image = images
    initial_image = deepcopy(images)

    for f in filters:
        if f == '':
            continue
        args = f.split('=')
        function = args[0]
        try:
            args = args[1].split(':')
        except:
            pass
        if function == 'remove_contours':
            image = filter_remove_contours(image,
                thresh=int(args[0]),
                maxval=int(args[1]))

        elif function == 'fastNlMeansDenoisingColored':
            image = cv2_fastNlMeansDenoisingColored(image,
                h=int(args[0]),
                hColor=int(args[1]),
                templateWindowSize=int(args[2]),
                searchWindowSize=int(args[3]))

        elif function == 'fastNlMeansDenoisingColoredMulti':
            if not multi:
                print("Error, multiples/single images in filter_opencv")
                sys.exit()
            image = filter_fastNlMeansDenoisingColoredMulti(images,
                imgToDenoiseIndex=1,
                temporalWindowSize=3,
                h=int(args[0]),
                hColor=int(args[1]),
                templateWindowSize=int(args[2]),
                searchWindowSize=int(args[3]))

        elif function == 'gaussianBlur':
            image = filter_gaussianBlur(image,
                radius=int(args[0]),
                sigma=float(args[1]))

        elif function == 'unsharp_mask':
            image = filter_unsharp_mask(image,
                radius=int(args[0]),
                amount=float(args[1]))

        elif function == 'bilateralFilter':
            image = filter_bilateralFilter(image,
                diameter=int(args[0]),
                sigmaColor=float(args[1]),
                sigmaSpace=float(args[2]))

        elif function == 'bilateral_sk':
            image = filter_bilateral_sk(image,
                sigma_color=float(args[0]),
                sigma_spatial=float(args[1]))

        elif function == 'morphologyEx':
            image = filter_morphologyEx(image,
                type=args[0],
                radius=int(args[1]),
                iterations=int(args[2]))

        elif function == 'dilate':
            image = filter_dilate(image,
                radius=int(args[0]))

        elif function == 'erode':
            image = filter_erode(image,
                radius=int(args[0]))

        elif function == 'addGaussNoise':
            image = filter_addGaussNoise(image,
                mean=float(args[0]),
                var=float(args[1]),
                sigma=float(args[2]))

        elif function == 'brightness_contrast':
            image = filter_brightness_contrast(image,
                brightness=int(args[0]),
                contrast=int(args[1]))

        elif function == 'richardson_lucy':
            image = filter_richardson_lucy(image,
                num_iter=int(args[0]))

        elif function =='nl_means':
            image = filter_nlmeans(image)
        # elif function == 'denoise_tv_bregman':
        #     image = filter_denoise_tv_bregman(image,
        #         weight=float(args[0]),
        #         eps=float(args[1]),
        #         max_iter=int(args[2]))

        # elif function == 'wavelet':
        #     image = filter_wavelet(image)

        elif function == 'scale':
            image = filter_scale_opencv(image,
                width=int(args[0]),
                height=int(args[1]),
                interpolation=args[2])

        elif function =='edge_sharpen_sobel':
            image = filter_edge_sharpen_sobel(image,
                denoised_image=initial_image,
                k_size=int(args[0]),
                blend_factor=float(args[1]))
        elif function == 'remove_small_holes':
            filter_remove_small_holes(image,
                area_threshold=int(args[0]),
                connectivity=int(args[1]))

    return image



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


# def filter_bm3d(image, sigma):
#     tmp = img_as_float(image)
#     tmp2 = bm3d.bm3d_rgb(tmp, sigma)
#     return img_as_ubyte(tmp2)



# def filter_wavelet(image):
#     tmp = img_as_float(image)

#     _denoise_wavelet = partial(denoise_wavelet, rescale_sigma=True)
#     parameter_ranges = {'sigma': np.arange(0.1, 0.3, 0.02),
#                         'wavelet': ['db1', 'db2'],
#                         'convert2ycbcr': [True, False],
#                         'multichannel': [True]}

#     # Calibrate denoiser
#     calibrated_denoiser = calibrate_denoiser(tmp,
#                                             _denoise_wavelet,
#                                             denoise_parameters=parameter_ranges
#                                             )

#     # Denoised image using calibrated denoiser
#     tmp = calibrated_denoiser(tmp)
#     tmp = np.clip(tmp, 0.0, 1.0)
#     return img_as_ubyte(tmp)




# def filter_denoise_tv_bregman(image, weight, eps, max_iter):
#     tmp = img_as_float(image)
#     tmp = denoise_tv_bregman(tmp,
#         weight=weight,
#         max_iter=max_iter,
#         eps=eps,
#         isotropic=True,
#         multichannel=True)
#     tmp = np.clip(tmp, 0.0, 1.0)
#     return img_as_ubyte(tmp)


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


def filter_unsharp_mask(image, radius, amount):
    tmp = img_as_float(image)
    tmp = unsharp_mask(tmp,
        radius,
        amount,
        preserve_range=False,
        channel_axis=2)
    return img_as_ubyte(tmp)


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


def filter_bilateralFilter(img, diameter, sigmaColor, sigmaSpace):
    return cv2.bilateralFilter(img, diameter, sigmaColor, sigmaSpace)

def filter_gaussianBlur(image, radius, sigma):
    return cv2.GaussianBlur(image, (radius, radius), sigma)

def filter_dilate(image, radius):
    kernel = np.ones((radius, radius), np.uint8)
    return cv2.dilate(image, kernel, iterations=1)

def filter_erode(image, radius):
    kernel = np.ones((radius, radius), np.uint8)
    return cv2.erode(image, kernel, iterations=1)




def filter_addGaussNoise(image, mean, var, sigma):
    gaussian = np.random.normal(mean, var**sigma, image.shape).astype(np.float)
    gaussian_img = gaussian + img_as_float(image)
    gaussian_img = np.clip(gaussian_img, 0.0, 1.0)
    return img_as_ubyte(gaussian_img)


def gaussian_kernel(size, size_y=None):
    size = int(size)
    if not size_y:
        size_y = size
    else:
        size_y = int(size_y)
    x, y = np.mgrid[-size:size+1, -size_y:size_y+1]
    g = np.exp(-(x**2/float(size)+y**2/float(size_y)))
    return g / g.sum()


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






def detectAndDescribe(image, method=None):
    """
    Compute key points and feature descriptors using an specific method
    """

    assert method is not None, "You need to define a feature detection method. Values are: 'sift', 'surf'"

    # detect and extract features from the image
    if method == 'sift':
        descriptor = cv2.SIFT_create()
    elif method == 'surf':
        descriptor = cv2.xfeatures2d.SURF_create()
    elif method == 'brisk':
        descriptor = cv2.BRISK_create()
    elif method == 'orb':
        descriptor = cv2.ORB_create()

    # get keypoints and descriptors
    (kps, features) = descriptor.detectAndCompute(image, None)

    return (kps, features)




def createMatcher(method,crossCheck):
    "Create and return a Matcher Object"

    if method == 'sift' or method == 'surf':
        bf = cv2.BFMatcher(cv2.NORM_L2, crossCheck=crossCheck)
        # bf = cv2.BFMatcher(cv2.NORM_L2SQR, crossCheck=crossCheck)
    elif method == 'orb' or method == 'brisk':
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=crossCheck)
    return bf


def matchKeyPointsBF(featuresA, featuresB, method):
    bf = createMatcher(method, crossCheck=True)

    # Match descriptors.
    best_matches = bf.match(featuresA,featuresB)

    # Sort the features in order of distance.
    # The points with small distance (more similarity) are ordered first in the vector
    rawMatches = sorted(best_matches, key = lambda x:x.distance)
    # print("Raw matches (Brute force):", len(rawMatches))
    return rawMatches


def matchKeyPointsKNN(featuresA, featuresB, ratio, method):
    bf = createMatcher(method, crossCheck=False)
    # compute the raw matches and initialize the list of actual matches
    rawMatches = bf.knnMatch(featuresA, featuresB, 2)
    print("Raw matches (knn):", len(rawMatches))
    matches = []

    # loop over the raw matches
    for m,n in rawMatches:
        # ensure the distance is within a certain ratio of each
        # other (i.e. Lowe's ratio test)
        if m.distance < n.distance * ratio:
            matches.append(m)
    return matches





# def findHomography(srcPoints, dstPoints, method=None, ransacReprojThreshold=None, mask=None, maxIters=None, confidence=None, /) -> retval, mask
# findHomography(srcPoints, dstPoints[, method[, ransacReprojThreshold[, mask[, maxIters[, confidence]]]]]) -> retval, mask
# .   @brief Finds a perspective transformation between two planes.
# .
# .   @param srcPoints Coordinates of the points in the original plane, a matrix of the type CV_32FC2
# .   or vector\<Point2f\> .
# .   @param dstPoints Coordinates of the points in the target plane, a matrix of the type CV_32FC2 or
# .   a vector\<Point2f\> .
# .   @param method Method used to compute a homography matrix. The following methods are possible:
# .   -   **0** - a regular method using all the points, i.e., the least squares method
# .   -   @ref RANSAC - RANSAC-based robust method
# .   -   @ref LMEDS - Least-Median robust method
# .   -   @ref RHO - PROSAC-based robust method
# .   @param ransacReprojThreshold Maximum allowed reprojection error to treat a point pair as an inlier
# .   (used in the RANSAC and RHO methods only). That is, if
# .   \f[\| \texttt{dstPoints} _i -  \texttt{convertPointsHomogeneous} ( \texttt{H} * \texttt{srcPoints} _i) \|_2  >  \texttt{ransacReprojThreshold}\f]
# .   then the point \f$i\f$ is considered as an outlier. If srcPoints and dstPoints are measured in pixels,
# .   it usually makes sense to set this parameter somewhere in the range of 1 to 10.
# .   @param mask Optional output mask set by a robust method ( RANSAC or LMeDS ). Note that the input
# .   mask values are ignored.
# .   @param maxIters The maximum number of RANSAC iterations.
# .   @param confidence Confidence level, between 0 and 1.
# .
# .   The function finds and returns the perspective transformation \f$H\f$ between the source and the
# .   destination planes:
# .
# .   \f[s_i  \vecthree{x'_i}{y'_i}{1} \sim H  \vecthree{x_i}{y_i}{1}\f]
# .
# .   so that the back-projection error
# .
# .   \f[\sum _i \left ( x'_i- \frac{h_{11} x_i + h_{12} y_i + h_{13}}{h_{31} x_i + h_{32} y_i + h_{33}} \right )^2+ \left ( y'_i- \frac{h_{21} x_i + h_{22} y_i + h_{23}}{h_{31} x_i + h_{32} y_i + h_{33}} \right )^2\f]
# .
# .   is minimized. If the parameter method is set to the default value 0, the function uses all the point
# .   pairs to compute an initial homography estimate with a simple least-squares scheme.
# .
# .   However, if not all of the point pairs ( \f$srcPoints_i\f$, \f$dstPoints_i\f$ ) fit the rigid perspective
# .   transformation (that is, there are some outliers), this initial estimate will be poor. In this case,
# .   you can use one of the three robust methods. The methods RANSAC, LMeDS and RHO try many different
# .   random subsets of the corresponding point pairs (of four pairs each, collinear pairs are discarded), estimate the homography matrix
# .   using this subset and a simple least-squares algorithm, and then compute the quality/goodness of the
# .   computed homography (which is the number of inliers for RANSAC or the least median re-projection error for
# .   LMeDS). The best subset is then used to produce the initial estimate of the homography matrix and
# .   the mask of inliers/outliers.
# .
# .   Regardless of the method, robust or not, the computed homography matrix is refined further (using
# .   inliers only in case of a robust method) with the Levenberg-Marquardt method to reduce the
# .   re-projection error even more.
# .
# .   The methods RANSAC and RHO can handle practically any ratio of outliers but need a threshold to
# .   distinguish inliers from outliers. The method LMeDS does not need any threshold but it works
# .   correctly only when there are more than 50% of inliers. Finally, if there are no outliers and the
# .   noise is rather small, use the default method (method=0).
# .
# .   The function is used to find initial intrinsic and extrinsic matrices. Homography matrix is
# .   determined up to a scale. Thus, it is normalized so that \f$h_{33}=1\f$. Note that whenever an \f$H\f$ matrix
# .   cannot be estimated, an empty one will be returned.
# .
# .   @sa
# .   getAffineTransform, estimateAffine2D, estimateAffinePartial2D, getPerspectiveTransform, warpPerspective,
# .   perspectiveTransform
def getHomography(kpsA, kpsB, featuresA, featuresB, matches, method_str='RHO', ransacReprojThresh=None):
    # convert the keypoints to numpy arrays
    kpsA = np.float32([kp.pt for kp in kpsA])
    kpsB = np.float32([kp.pt for kp in kpsB])

    if len(matches) > 4:

        # construct the two sets of points
        ptsA = np.float32([kpsA[m.queryIdx] for m in matches])
        ptsB = np.float32([kpsB[m.trainIdx] for m in matches])

        if method_str.upper() == 'RHO':
            method = cv2.RHO
        elif method_str.upper() == 'RANSAC':
            method = cv2.RANSAC
        elif method_str.upper() == 'LMEDS':
            method = cv2.LMEDS

        # estimate the homography between the sets of points
        # (H, status) = cv2.findHomography(ptsA, ptsB, cv2.RANSAC, reprojThresh)
        # (H, status) = cv2.findHomography(ptsA, ptsB, cv2.LMEDS, reprojThresh)
        (H, status) = cv2.findHomography(ptsA, ptsB, method, ransacReprojThresh)

        return (matches, H, status)
    else:
        return None
