import os
import cv2
import numpy as np


def generate_black_frame(filepath: str, ref_img_fp: str) -> None:
    if not os.path.exists(filepath):
        img: np.ndarray = cv2.imread(ref_img_fp, cv2.IMREAD_COLOR)
        black_image = np.zeros(img.shape, dtype=img.dtype)
        cv2.imwrite(filepath, black_image)

