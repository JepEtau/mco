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
    output_filepath = "../../frames/g_asuivre/ep00_33659_ep12__s__655.png"

    img_input_denoised = cv2.imread(denoised_filepath, cv2.IMREAD_COLOR)
    img_input_bgr = cv2.imread(input_filepath, cv2.IMREAD_COLOR)
    img_input_gray = cv2.cvtColor(img_input_bgr, cv2.COLOR_BGR2GRAY)

    k_size=3,
    blend_factor=0.15

    scale = 1
    delta = 0
    ddepth = cv2.CV_16S

    image_gray = cv2.cvtColor(img_input_bgr, cv2.COLOR_BGR2GRAY)

    # grad_x = cv2.Sobel(image_gray, ddepth, 1, 0, ksize=k_size, scale=scale, delta=delta, borderType=cv2.BORDER_DEFAULT)
    # grad_y = cv2.Sobel(image_gray, ddepth, 0, 1, ksize=k_size, scale=scale, delta=delta, borderType=cv2.BORDER_DEFAULT)

    grad_x = cv2.Scharr(image_gray, ddepth, 1, 0, scale=scale, delta=delta, borderType=cv2.BORDER_DEFAULT)
    grad_y = cv2.Scharr(image_gray, ddepth, 0, 1, scale=scale, delta=delta, borderType=cv2.BORDER_DEFAULT)



    abs_grad_x = cv2.convertScaleAbs(grad_x)
    abs_grad_y = cv2.convertScaleAbs(grad_y)
    abs_grad_xy = cv2.addWeighted(abs_grad_x, 0.5, abs_grad_y, 0.5, 0)

    if True:
        radius = 3
        kernel = np.ones((radius, radius), np.uint8)
        abs_grad_xy_filtered = cv2.erode(abs_grad_xy, kernel, iterations=1)
    else:
        abs_grad_xy_filtered = abs_grad_xy


    d_b, d_g, d_r = cv2.split(img_input_denoised)

    mask_float = abs_grad_xy_filtered.astype(np.float32)  / 255.0
    layer_b = np.clip(cv2.multiply(d_b.astype(np.float32), mask_float), 0, 255).astype(np.uint8)
    layer_g = np.clip(cv2.multiply(d_g.astype(np.float32), mask_float), 0, 255).astype(np.uint8)
    layer_r = np.clip(cv2.multiply(d_r.astype(np.float32), mask_float), 0, 255).astype(np.uint8)

    img_mult_bgr = cv2.merge((
        layer_b.reshape(d_b.shape),
        layer_g.reshape(d_g.shape),
        layer_r.reshape(d_r.shape)))

    img_mult_bgr = (blend_factor * img_mult_bgr.astype(np.float32)).astype(np.uint8)
    # img_output = cv2.addWeighted(img_input_bgr, 1, img_mult_bgr, 1, 0)
    img_output = cv2.subtract(img_input_bgr, img_mult_bgr)



    cv2.imwrite(output_filepath, img_output)

    # cv2.imshow("Image",  )
    # cv2.waitKey(0)
    # cv2.destroyWindow("Image")


