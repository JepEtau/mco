#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pprint import pprint
import os
import os.path
import cv2
import numpy as np
import signal
import sys
import time
import math
from skimage.util import img_as_ubyte
from skimage.util import img_as_float
from skimage.restoration import (
    calibrate_denoiser,
    denoise_wavelet,
    denoise_tv_chambolle,
    denoise_nl_means,
    denoise_bilateral,
)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    denoised_filepath = "../../frames/g_asuivre/ep00_33659_ep12__s__342.png"
    input_filepath = "../../frames/g_asuivre/ep00_33659_ep12__s__640.png"
    output_filepath = "../../frames/g_asuivre/ep00_33659_ep12__s__687.png"

    img_input_denoised = cv2.imread(denoised_filepath, cv2.IMREAD_COLOR)
    img_input_bgr = cv2.imread(input_filepath, cv2.IMREAD_COLOR)
    img_input_gray = cv2.cvtColor(img_input_bgr, cv2.COLOR_BGR2GRAY)



    # canny = cv2.Canny(gray,240,255)
    # b, g, r = cv2.split(img_input_bgr)
    # c_b = np.clip(cv2.multiply(b, canny), 0, 255).astype(np.uint8)
    # c_g = np.clip(cv2.multiply(g, canny), 0, 255).astype(np.uint8)
    # c_r = np.clip(cv2.multiply(r, canny), 0, 255).astype(np.uint8)

    # blend_factor = 0.1
    # cbp = cv2.addWeighted(b, 1, c_b, blend_factor, 0).reshape(b.shape)
    # cgp = cv2.addWeighted(g, 1, c_g, blend_factor, 0).reshape(g.shape)
    # crp = cv2.addWeighted(r, 1, c_r, blend_factor, 0).reshape(r.shape)
    # img_input_bgr_canny = cv2.merge((cbp, cgp, crp))
    # img_input_gray_canny = cv2.cvtColor(img_input_bgr, cv2.COLOR_BGR2GRAY)


    scale = 1
    delta = 0
    ddepth = cv2.CV_16S
    blend_factor = 0.15
    k_size = 3
    # img_input_gray = cv2.GaussianBlur(img_input_gray, (3, 3), 0)
    if True:
        grad_x = cv2.Sobel(img_input_gray, ddepth, 1, 0, ksize=k_size, scale=scale, delta=delta, borderType=cv2.BORDER_DEFAULT)
        grad_y = cv2.Sobel(img_input_gray, ddepth, 0, 1, ksize=k_size, scale=scale, delta=delta, borderType=cv2.BORDER_DEFAULT)
        abs_grad_x = cv2.convertScaleAbs(grad_x)
        abs_grad_y = cv2.convertScaleAbs(grad_y)
        abs_grad_xy = 255 - cv2.addWeighted(abs_grad_x, 0.5, abs_grad_y, 0.5, 0)
    else:
        grad_xy = cv2.Sobel(img_input_gray, ddepth, 1, 1, ksize=k_size, scale=scale, delta=delta, borderType=cv2.BORDER_DEFAULT)
        abs_grad_xy = 255 - cv2.convertScaleAbs(grad_xy)
    # grad = cv2.addWeighted(abs_grad_x, 0.5, abs_grad_y, 0.5, 0)

    # grad = np.clip(255 - grad, 0, 255).astype(np.uint8)

    if False:
        radius = 3
        kernel = np.ones((radius, radius), np.uint8)
        grad_2 = cv2.dilate(abs_grad_xy, kernel, iterations=1)
    elif False:
        radius = 3
        sigma = 0.01
        grad_2 = cv2.GaussianBlur(abs_grad_xy, (radius, radius), sigma)
    else:
        grad_2 = abs_grad_xy

    img_denoised_bgr = cv2.imread(denoised_filepath, cv2.IMREAD_COLOR)
    d_b, d_g, d_r = cv2.split(img_denoised_bgr)

    grad_float = (255 - grad_2).astype(np.float32)  / 255.0
    layer_b = np.clip(cv2.multiply(d_b.astype(np.float32), grad_float), 0, 255).astype(np.uint8)
    layer_g = np.clip(cv2.multiply(d_g.astype(np.float32), grad_float), 0, 255).astype(np.uint8)
    layer_r = np.clip(cv2.multiply(d_r.astype(np.float32), grad_float), 0, 255).astype(np.uint8)

    img_mult_bgr = cv2.merge((
        layer_b.reshape(d_b.shape),
        layer_g.reshape(d_g.shape),
        layer_r.reshape(d_r.shape)))

    # img_output = np.clip(cv2.addWeighted(img_input_bgr, 1, img_mult_bgr, blend_factor, 0), 0, 255).astype(np.uint8)
    # img_output = cv2.addWeighted(img_input_bgr, 1, img_mult_bgr, blend_factor, 0)

    img_mult_bgr = (blend_factor * img_mult_bgr.astype(np.float32)).astype(np.uint8)
    # img_output = cv2.subtract(img_input_bgr, img_mult_bgr)
    img_output = cv2.addWeighted(img_input_bgr, 1, img_mult_bgr, 1, 0)
    cv2.imwrite(output_filepath, img_output)



    cv2.imshow("Image",  img_mult_bgr)
    cv2.waitKey(0)
    cv2.destroyWindow("Image")


    # cv2.imshow("d_b", d_b)
    # cv2.waitKey(0)
    # cv2.destroyWindow("d_b")

    # cv2.imshow("grad_2", grad_2)
    # cv2.waitKey(0)
    # cv2.destroyWindow("grad_2")






# if __name__ == "__main__":
#     signal.signal(signal.SIGINT, signal.SIG_DFL)

#     denoised_filepath = "../../frames/g_asuivre/ep00_33659_ep12__s__242.png"
#     input_filepath = "../../frames/g_asuivre/ep00_33659_ep12__s__642.png"
#     output_filepath = "../../frames/g_asuivre/ep00_33659_ep12__s__690.png"

#     img_input_bgr = cv2.imread(input_filepath, cv2.IMREAD_COLOR)
#     img_denoised_bgr = cv2.imread(input_filepath, cv2.IMREAD_COLOR)
#     gray = cv2.cvtColor(img_input_bgr, cv2.COLOR_BGR2GRAY)

#     if True:
#         scale = 1
#         delta = 0
#         ddepth = cv2.CV_16S

#         grad_x = cv2.Sobel(gray, ddepth, 1, 0, ksize=k_size, scale=scale, delta=delta, borderType=cv2.BORDER_DEFAULT)
#         abs_grad_x = cv2.convertScaleAbs(grad_x)
#         grad_y = cv2.Sobel(gray, ddepth, 0, 1, ksize=k_size, scale=scale, delta=delta, borderType=cv2.BORDER_DEFAULT)
#         abs_grad_y = cv2.convertScaleAbs(grad_y)
#         grad = cv2.addWeighted(abs_grad_x, 0.5, abs_grad_y, 0.5, 0)


#     # cv2.imshow("Image", edges)
#     # cv2.waitKey(0)
#     # cv2.destroyWindow("Image")

#     if True:
#         grad2 = np.clip(255 - grad, 0, 255).astype(np.uint8)
#     else:
#         grad2 = grad

#     if False:

#         kernel = np.ones((radius, radius), np.uint8)
#         grad3 = cv2.erode(grad2, kernel, iterations=1)
#     elif False:
#         radius = 3
#         sigma = 0.1
#         grad3 = cv2.GaussianBlur(grad2, (radius, radius), sigma)
#     else:
#         grad3 = grad2


#     if False:
#         blend_factor = 0.95
#         bbp = cv2.addWeighted(b, blend_factor, grad3, 1 - blend_factor, 0).reshape(b.shape)
#         ggp = cv2.addWeighted(g, blend_factor, grad3, 1 - blend_factor, 0).reshape(g.shape)
#         rrp = cv2.addWeighted(r, blend_factor, grad3, 1 - blend_factor, 0).reshape(r.shape)

#     d_b, d_g, d_r = cv2.split(img_denoised_bgr)
#     layer_b = 255 - np.clip(cv2.multiply(d_b, grad3), 0, 255).astype(np.uint8)
#     layer_g = 255 - np.clip(cv2.multiply(d_g, grad3), 0, 255).astype(np.uint8)
#     layer_r = 255 - np.clip(cv2.multiply(d_r, grad3), 0, 255).astype(np.uint8)
#     img_mult_bgr = cv2.merge((layer_b, layer_g, layer_r))

#     b, g, r = cv2.split(img_input_bgr)

#     blend_factor = 0.05
#     bbp = np.clip(cv2.addWeighted(b, 1, layer_b, blend_factor, 0), 0, 255).astype(np.uint8).reshape(b.shape)
#     ggp = np.clip(cv2.addWeighted(g, 1, layer_g, blend_factor, 0), 0, 255).astype(np.uint8).reshape(g.shape)
#     rrp = np.clip(cv2.addWeighted(r, 1, layer_r, blend_factor, 0), 0, 255).astype(np.uint8).reshape(r.shape)

#     img_output = cv2.merge((bbp, ggp, rrp))

#     cv2.imwrite(output_filepath, img_output)



#     cv2.imshow("Image", img_mult_bgr)
#     cv2.waitKey(0)
#     cv2.destroyWindow("Image")




################ ASUIVRE

    # scale = 1
    # delta = 0
    # ddepth = cv2.CV_16S
    # blend_factor = 0.15
    # k_size = 3
    # # img_input_gray = cv2.GaussianBlur(img_input_gray, (3, 3), 0)
    # if True:
    #     grad_x = cv2.Sobel(img_input_gray, ddepth, 1, 0, ksize=k_size, scale=scale, delta=delta, borderType=cv2.BORDER_DEFAULT)
    #     grad_y = cv2.Sobel(img_input_gray, ddepth, 0, 1, ksize=k_size, scale=scale, delta=delta, borderType=cv2.BORDER_DEFAULT)
    #     abs_grad_x = cv2.convertScaleAbs(grad_x)
    #     abs_grad_y = cv2.convertScaleAbs(grad_y)
    #     abs_grad_xy = 255 - cv2.addWeighted(abs_grad_x, 0.5, abs_grad_y, 0.5, 0)
    # else:
    #     grad_xy = cv2.Sobel(img_input_gray, ddepth, 1, 1, ksize=k_size, scale=scale, delta=delta, borderType=cv2.BORDER_DEFAULT)
    #     abs_grad_xy = 255 - cv2.convertScaleAbs(grad_xy)
    # # grad = cv2.addWeighted(abs_grad_x, 0.5, abs_grad_y, 0.5, 0)

    # # grad = np.clip(255 - grad, 0, 255).astype(np.uint8)

    # if False:
    #     radius = 3
    #     kernel = np.ones((radius, radius), np.uint8)
    #     grad_2 = cv2.dilate(abs_grad_xy, kernel, iterations=1)
    # elif False:
    #     radius = 3
    #     sigma = 0.01
    #     grad_2 = cv2.GaussianBlur(abs_grad_xy, (radius, radius), sigma)
    # else:
    #     grad_2 = abs_grad_xy

    # img_denoised_bgr = cv2.imread(denoised_filepath, cv2.IMREAD_COLOR)
    # d_b, d_g, d_r = cv2.split(img_denoised_bgr)

    # grad_float = (255 - grad_2).astype(np.float32)  / 255.0
    # layer_b = np.clip(cv2.multiply(d_b.astype(np.float32), grad_float), 0, 255).astype(np.uint8)
    # layer_g = np.clip(cv2.multiply(d_g.astype(np.float32), grad_float), 0, 255).astype(np.uint8)
    # layer_r = np.clip(cv2.multiply(d_r.astype(np.float32), grad_float), 0, 255).astype(np.uint8)

    # img_mult_bgr = cv2.merge((
    #     layer_b.reshape(d_b.shape),
    #     layer_g.reshape(d_g.shape),
    #     layer_r.reshape(d_r.shape)))

    # # img_output = np.clip(cv2.addWeighted(img_input_bgr, 1, img_mult_bgr, blend_factor, 0), 0, 255).astype(np.uint8)
    # # img_output = cv2.addWeighted(img_input_bgr, 1, img_mult_bgr, blend_factor, 0)

    # img_mult_bgr = (blend_factor * img_mult_bgr.astype(np.float32)).astype(np.uint8)
    # # img_output = cv2.subtract(img_input_bgr, img_mult_bgr)
    # img_output = cv2.addWeighted(img_input_bgr, 1, img_mult_bgr, 1, 0)
    # cv2.imwrite(output_filepath, img_output)
