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

    input_filepath = "../../frames/g_debut/ep00_00620_ep01__k__201.png"
    output_filepath = "../../frames/g_asuivre/ep00_00620_ep01__k__250.png"

    img_input_bgr = cv2.imread(input_filepath, cv2.IMREAD_COLOR)
    img_input_gray = cv2.cvtColor(img_input_bgr, cv2.COLOR_BGR2GRAY)










    cv2.imwrite(output_filepath, img_output)

    # cv2.imshow("Image",  )
    # cv2.waitKey(0)
    # cv2.destroyWindow("Image")


