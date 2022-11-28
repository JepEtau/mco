#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pprint import pprint
import os
import os.path
import cv2
import numpy as np
import matplotlib.pyplot as plt
import signal
import sys
import time
import math
from skimage.util import img_as_ubyte
from skimage.util import img_as_float


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    input_filepath = "../../frames/g_asuivre/ep00_33659_ep12__s__640.png"
    output_filepath = "../../frames/g_asuivre/ep00_33659_ep12__s__690.png"

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


    # compare with dilate: -> canny is better
    if False:
        radius = 3
        kernel = np.ones((radius, radius), np.uint8)
        img_output2 = cv2.dilate(img_input_rgb, kernel, iterations=1)
        output_filepath2 = "../../frames/g_asuivre/ep00_33659_ep12__s__691.png"
        cv2.imwrite(output_filepath2, img_output2)

