
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.append("../scripts")

import cv2
import numpy as np
import signal
from pprint import pprint
import os

from filters.filters import *
import torch
import piqa




def show_image(img, img_name:str=''):
    window_name = 'image' if img_name == '' else img_name
    cv2.namedWindow(window_name)
    _img = cv2.resize(img.copy(), (0, 0), fx=0.5,fy=0.5) if img.shape[0] > 800 else img.copy()
    cv2.moveWindow(window_name, 40, 30)
    cv2.imshow(window_name, _img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


input_path = 'ep02_episode_000'

def main():
    image_list = list()
    for f in os.listdir(input_path):
        if f.endswith(".png") and not f.endswith("_cropped.png"):
            image_list.append(os.path.join(input_path, f))
    image_list = sorted(image_list)


    for filepath in image_list:
        bgr_img = cv2.imread(filepath)

        # PSNR
        x = torch.rand(5, 3, 256, 256)
        y = torch.rand(5, 3, 256, 256)

        psnr = piqa.PSNR()
        l = psnr(x, y)

        # SSIM
        x = torch.rand(5, 3, 256, 256, requires_grad=True).cuda()
        y = torch.rand(5, 3, 256, 256).cuda()

        ssim = piqa.SSIM().cuda()
        l = 1 - ssim(x, y)
        l.backward()



if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()


