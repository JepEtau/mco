# -*- coding: utf-8 -*-
import sys

from skimage import data, io
from skimage.registration import phase_cross_correlation
from skimage import transform
from skimage.filters import sobel
from skimage.util import img_as_ubyte
from skimage.util import img_as_float

from utils.hash import (
    calculate_hash,
    log_filter
)
from utils.pretty_print import *


# DO NOT USE: broken

class Skimage_deshaker:
    def __init__(self) -> None:
        self.__max_corners = 1000
        self.__quality_level = 0.01
        self.__min_distance = 10.0
        self.__block_size = 3
        self.__mask = None
        self.__use_harris_detector = False
        self.__k = 0.04
        self.__crop_w = 12
        self.__crop_h = 12
        self.__use_roi = False
        self.__sobel = False
        self.__border_color = [0, 0, 0]


        self._height, self._width, self._channels = 0, 0, 0
        self.__index = 0

        sys.exit(print_red("Error: Skimage_deshaker is not working"))



    def stabilize(self, shot, images, image_list, ref,
        step_no, input_hash, mode,
        get_hash:bool=False, do_log:bool=True,
        do_force=False, verbose=False):
        """Stabilize images without smoothing the trajectory
        """
        use_static_ref = False
        count = len(images)

        if ref == 'start':
            start_index = 0
            use_static_ref = False
        elif ref == 'end':
            start_index = len(images) - 1
        elif ref == 'middle':
            start_index = int(len(images) / 2 - 1)
            use_static_ref = True


        # Define a filter str
        filters_str = "%03d:%0.2f:%.1f:%d:%0.2f" % (
                    self.__max_corners,
                    self.__quality_level,
                    self.__min_distance,
                    self.__block_size,
                    self.__k)
        if self.__sobel:
            filters_str += ':sobel'
        suffix = ""
        if self.__use_roi:
            suffix += "roi_"

        # Generate and log hash
        filter_str = "%s,stab=%s:%s" % (input_hash, suffix, filters_str)
        if get_hash:
            hash = calculate_hash(filter_str=filter_str)
            return filters_str, None, None
        if do_log:
            hash = log_filter(filter_str, shot['hash_log_file'])
        else:
            hash = calculate_hash(filter_str=filter_str)
        print_lightcyan("\t\t\t(cv2) CV2_deshaker, images count:%d, start_index:%d" % (len(images), start_index))

        # Generate and log hash
        filters_str = "%s,stab=%s" % (input_hash, filters_str)
        if get_hash:
            hash = calculate_hash(filter_str=filters_str)
            return None, hash
        if do_log:
            hash = log_filter(filter_str, shot['hash_log_file'])
        else:
            hash = calculate_hash(filter_str=filter_str)
        print_lightcyan("\t\t\t(skimage) deshaker, output hash= %s" % (step_no, hash))

        # img_stabilized, img_ref_gray, keypoints_ref = self.__get_initial_image(
        #     img=images[start_index])
        # self._height, self._width, self._channels = img_stabilized.shape

        img_ref = images[0]

        # Apply sobel filter to enhance edges
        img_gray_ref = sobel(img_as_float(img_ref))

        # Add first image to the list
        output_images = [img_ref]

        for i in range(1, len(images)):
            img = images[i]

            # Apply sobel filter to enhance edges
            img_gray = sobel(img_as_float(img))

            shift, error, diffphase = phase_cross_correlation(
                img_gray_ref,
                img_gray,
                upsample_factor=100)

            (shift_y, shift_x) = shift
            print(shift)
            print(diffphase)
            tf_shift = transform.SimilarityTransform(translation=[-shift_x, -shift_y])
            img_stabilized = transform.warp(img_as_float(img), tf_shift)

            output_images.append(img_as_ubyte(img_stabilized))


        return output_images, filters_str


