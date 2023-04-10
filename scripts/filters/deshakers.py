# -*- coding: utf-8 -*-
import sys
import cv2
import numpy as np
from statistics import mean

from skimage import data, io
from skimage.registration import phase_cross_correlation
from skimage import transform
from skimage.filters import sobel
from skimage.util import img_as_ubyte
from skimage.util import img_as_float

from filters.filters import edge_sharpen_sobel_gray
from filters.utils import STABILIZE_BORDER
from utils.hash import (
    calculate_hash,
    log_filter
)
from utils.pretty_print import *


def apply_cv2_transformation(img, x_y_theta:list):
    img_to_transform = cv2.copyMakeBorder(img,
        STABILIZE_BORDER, STABILIZE_BORDER,
        STABILIZE_BORDER, STABILIZE_BORDER,
        cv2.BORDER_CONSTANT, value=[0, 0, 0])

    t_x, t_y, t_theta = x_y_theta
    transformation_matrix = np.array(
        [[np.cos(t_theta), -np.sin(t_theta), t_x],
        [np.sin(t_theta), np.cos(t_theta), t_y]],
        dtype=np.float32)

    output_img = cv2.warpAffine(img_to_transform,
        transformation_matrix,
        (img_to_transform.shape[1], img_to_transform.shape[0]))
    return output_img


class CV2_deshaker:
    def __init__(self) -> None:
        self.__max_corners = 1000
        self.__quality_level = 0.01
        self.__min_distance = 10.0
        self.__block_size = 3
        self.__mask = None
        self.__use_harris_detector = False
        self.__k = 0.04
        self.__pad_h = STABILIZE_BORDER
        self.__pad_w = STABILIZE_BORDER
        self.__border_color = [0, 0, 0]

        self.__use_roi = False
        self.__crop_w = 12
        self.__crop_h = 12

        # Do not use sobel, only for testing purpose
        self.__sobel = False

        self.filters_str = "%03d:%0.2f:%.1f:%d:%0.2f:%d" % (
            self.__max_corners,
            self.__quality_level,
            self.__min_distance,
            self.__block_size,
            self.__k,
            STABILIZE_BORDER)

        if self.__sobel:
            self.filters_str += ':sobel'

        self._height, self._width, self._channels = 0, 0, 0

        self.__index = 0


    def __get_initial_image(self, img, last_transformation):
        # Apply transformation to the initial image
        if last_transformation is not None:
            initial_img_stabilized = apply_cv2_transformation(img, last_transformation)
        else:
            initial_img_stabilized = cv2.copyMakeBorder(img,
                self.__pad_h, self.__pad_h, self.__pad_w, self.__pad_w,
                cv2.BORDER_CONSTANT, value=self.__border_color)

        img_gray_tmp = cv2.cvtColor(initial_img_stabilized, cv2.COLOR_RGB2GRAY)

        if self.__use_roi:
            img_gray_tmp2 = img_gray_tmp[
                self.__crop_h:img_gray_tmp.shape[0] - self.__crop_h,
                self.__crop_w:img_gray_tmp.shape[1] - self.__crop_w]
        else:
            img_gray_tmp2 = img_gray_tmp


        if self.__sobel:
            img_gray = edge_sharpen_sobel_gray(image_gray=img_gray_tmp2, index=self.__index)
            self.__index += 1
        else:
            img_gray = img_gray_tmp2

        keypoints = cv2.goodFeaturesToTrack(img_gray,
            maxCorners=self.__max_corners,
            qualityLevel=self.__quality_level,
            minDistance=self.__min_distance,
            blockSize=self.__block_size,
            mask=self.__mask,
            useHarrisDetector=self.__use_harris_detector,
            k=self.__k)

        return initial_img_stabilized, img_gray, keypoints


    def __stabilize_image(self, img, img_ref_gray, keypoints_ref, directions='all', verbose=False):
        img_gray_tmp = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        img_gray_tmp2 = cv2.copyMakeBorder(img_gray_tmp,
            self.__pad_h, self.__pad_h, self.__pad_w, self.__pad_w,
            cv2.BORDER_CONSTANT,
            value=self.__border_color)

        if self.__use_roi:
            img_gray_tmp2 = img_gray_tmp[
                self.__crop_h:img_gray_tmp.shape[0] - self.__crop_h,
                self.__crop_w:img_gray_tmp.shape[1] - self.__crop_w,]

        if self.__sobel:
            img_gray = edge_sharpen_sobel_gray(image_gray=img_gray_tmp2, index=self.__index)
            self.__index += 1
        else:
            img_gray = img_gray_tmp2

        try:
            # Calculate optical flow (i.e. track feature points)
            keypoints, status, err = cv2.calcOpticalFlowPyrLK(
                prevImg=img_gray,
                nextImg=img_ref_gray,
                prevPts=keypoints_ref,
                nextPts=None)

            # Estimate transformation matrix
            transformation = cv2.estimateAffinePartial2D(
                keypoints_ref[status == 1],
                keypoints[status == 1])[0]
            if transformation is not None:
                t_x = transformation[0][2]
                t_y = transformation[1][2]
                # Calculate angle, this cill also remove the scaling factor
                t_theta = mean([
                    np.arctan2(transformation[1][0], transformation[0][0]),
                    np.arctan2(-transformation[0][1], transformation[1][1])])
                # print("\t", t_theta)
                # t_theta = np.arctan2(transformation[1][0], transformation[0][0])
                # print("\t", t_theta)
                if verbose:
                    print("%d points, %d points" % (len(keypoints_ref[status == 1]), len(keypoints[status == 1])))
            else:
                print("\ttransformation not found")
                t_x = t_y = t_theta = 0
        except:
            print("warning: __stabilize_image: transformation not found")
            t_x = t_y = t_theta = 0

        if directions == 'vertical':
            t_x = 0
            t_theta = 0
        elif directions == 'horizontal':
            t_y = 0
            t_theta = 0
        elif directions == 'translation':
            t_theta = 0
        # else
        #  i.e. directions == 'all':

        if verbose:
            print([t_x, t_y, t_theta])

        last_transformation = [t_x, t_y, t_theta]

        # Transformation contains scale, discard it
        transformation_matrix = np.array(
            [[np.cos(t_theta), -np.sin(t_theta), t_x],
            [np.sin(t_theta), np.cos(t_theta), t_y]],
            dtype=np.float32)

        img_to_transform = cv2.copyMakeBorder(img,
            self.__pad_h, self.__pad_h, self.__pad_w, self.__pad_w,
            cv2.BORDER_CONSTANT, value=self.__border_color)

        if False:
            # Select good points
            if keypoints is not None:
                good_new = keypoints[status==1]

            # draw the tracks
            for new in good_new:
                a, b = new.ravel()
                frame = cv2.circle(img_gray, (int(a), int(b)), 5, [0,255,0], -1)
            cv2.imshow("Stabilize", frame)
            cv2.waitKey()

        # Apply transformation
        img_stabilized = cv2.warpAffine(img_to_transform,
            transformation_matrix,
            (img_to_transform.shape[1], img_to_transform.shape[0]))

        return img_stabilized, last_transformation


    def stabilize(self, shot, images,
        ref, directions, last_transformation,
        step_no, input_hash, get_hash:bool=False, do_force=False):
        """Stabilize images without smoothing the trajectory
        """
        verbose=False
        transformations = {
            'start': None,
            'end': None,
        }
        use_static_ref = False

        if ref == 'start':
            # Start from first frame
            ref_index = 0
            use_static_ref = False
        elif ref == 'end':
            # Start from last frame
            ref_index = len(images) - 1
        elif ref == 'middle':
            ref_index = int(len(images) / 2 - 1)
            use_static_ref = True

        suffix = ""
        if self.__use_roi:
            suffix += "roi_"

        # Generate and log hash
        filter_str = "%s,stab=%s:%s" % (input_hash, suffix, self.filters_str)
        if get_hash:
            hash = calculate_hash(filter_str=filter_str)
            return self.filters_str, None, transformations
        hash = log_filter(filter_str, shot['hash_log_file'])
        print_lightcyan("\t\t\t(cv2) CV2_deshaker, images count:%d, ref_index:%d" % (len(images), ref_index))

        if last_transformation is not None and ref_index != 0:
            print_red("error: stabilize, last transformation will be ignored")
            last_transformation = None
        img_stabilized, img_ref_gray, keypoints_ref = self.__get_initial_image(
            img=images[ref_index],
            last_transformation=last_transformation)
        self._height, self._width, self._channels = img_stabilized.shape

        if ref == 'middle':
            output_images = list()
            start = 0
            end = len(images)

            for i in range(start, end):
                if verbose:
                    print("frame %d: " % (i), end='')

                img_colored = images[i]
                if verbose:
                    print("%s: image=%d" % (ref, i), end=' ')

                # compute and get keypoints
                img_stabilized, transformation = self.__stabilize_image(
                    img=img_colored,
                    img_ref_gray=img_ref_gray,
                    keypoints_ref=keypoints_ref,
                    directions=directions)

                output_images.append(img_stabilized)
                if verbose:
                    print("append")

                if i == 0:
                    transformations['start'] = transformation
            transformations['end'] = transformation

        else:
            output_images = [img_stabilized]
            start = ref_index + 1
            end = len(images)
            transformation = None
            for _ref in ['start', 'end']:
                for i in range(start, end):
                    if verbose:
                        print("frame %d: " % (i), end='')

                    if _ref == 'start':
                        img_colored = images[i]
                        if verbose:
                            print("%s: image=%d" % (_ref, i), end=' ')
                    elif _ref == 'end':
                        index = ref_index - 1 - i
                        img_colored = images[index]
                        if verbose:
                            print("%s: image=%d" % (_ref, index), end=' ')


                    # compute and get keypoints
                    img_stabilized, transformation = self.__stabilize_image(
                        img=img_colored,
                        img_ref_gray=img_ref_gray,
                        keypoints_ref=keypoints_ref,
                        directions=directions)

                    if _ref == 'start':
                        output_images.append(img_stabilized)
                        if verbose:
                            print("append")
                    elif _ref == 'end':
                        output_images.insert(0, img_stabilized)
                        if verbose:
                            print("insert")

                    # Current frame is the newest reference
                    img_gray_tmp2 = cv2.cvtColor(img_stabilized.copy(), cv2.COLOR_RGB2GRAY)
                    if self.__use_roi:
                        img_gray_tmp2 = img_gray_tmp2[
                            self.__crop_h+self.__pad_h:self.__pad_h+img_gray_tmp2.shape[0],
                            self.__crop_w+self.__pad_w:self.__pad_w+img_gray_tmp2.shape[1]]

                    if self.__sobel:
                        img_ref_gray = edge_sharpen_sobel_gray(image_gray=img_gray_tmp2, index=self.__index)
                        self.__index += 1
                    else:
                        img_ref_gray = img_gray_tmp2

                    keypoints_ref = cv2.goodFeaturesToTrack(img_ref_gray,
                        maxCorners=self.__max_corners,
                        qualityLevel=self.__quality_level,
                        minDistance=self.__min_distance,
                        blockSize=self.__block_size,
                        mask=self.__mask,
                        useHarrisDetector=self.__use_harris_detector,
                        k=self.__k)

                start = 0
                end = ref_index

                if _ref == 'start':
                    print_yellow("ref=start, save transformation as the last", end= '')
                    print(transformation)
                    transformations['end'] = transformation
                elif _ref == 'end':
                    print_yellow("ref=end, save transformation as the begin", end= '')
                    print(transformation)
                    transformations['start'] = transformation
                transformation = None

        return self.filters_str, output_images, transformations




class Skimage_deshaker:
    def __init__(self) -> None:
        self.__max_corners = 1000
        self.__quality_level = 0.01
        self.__min_distance = 10.0
        self.__block_size = 3
        self.__mask = None
        self.__use_harris_detector = False
        self.__k = 0.04
        self.__pad_h = 20
        self.__pad_w = 20
        self.__crop_w = 12
        self.__crop_h = 12
        self.__sobel = False
        self.__border_color = [0, 0, 0]

        self.filters_str = "%03d:%0.2f:%.1f:%d:%0.2f:%d" % (
            self.__max_corners,
            self.__quality_level,
            self.__min_distance,
            self.__block_size,
            self.__k,
            STABILIZE_BORDER)

        if self.__sobel:
            self.filters_str += ':sobel'

        self._height, self._width, self._channels = 0, 0, 0

        self.__index = 0

        sys.exit(print_red("Error: Skimage_deshaker is not working"))



    def stabilize(self, shot, images, image_list, ref,
        step_no, input_hash, directions='both',
        get_hash:bool=False, do_force=False, verbose=False):
        """Stabilize images without smoothing the trajectory
        """
        use_static_ref = False
        count = len(images)

        if ref == 'start':
            ref_index = 0
            use_static_ref = False
        elif ref == 'end':
            ref_index = len(images) - 1
        elif ref == 'middle':
            ref_index = int(len(images) / 2 - 1)
            use_static_ref = True

        # if frame_ref_index is None:
        #     use_static_ref = False
        #     frame_ref_index = 0
        #     suffix = "prev"
        # elif frame_ref_index == -1:
        #     use_static_ref = True
        #     frame_ref_index = int(count/2)
        #     suffix = "static"
        # else:
        #     use_static_ref = True
        #     suffix = "static"


        # Generate and log hash
        filters_str = "%s,stab=%s" % (input_hash, self.filters_str)
        if get_hash:
            hash = calculate_hash(filter_str=filters_str)
            return None, hash
        hash = log_filter(filters_str, shot['hash_log_file'])
        print_lightcyan("\t\t\t(skimage) deshaker, output hash= %s" % (step_no, hash))

        # img_stabilized, img_ref_gray, keypoints_ref = self.__get_initial_image(
        #     img=images[ref_index],
        #     add_border=add_border)
        # self._height, self._width, self._channels = img_stabilized.shape

        img_ref = images[0]

        # Add padding and apply sobel filter to enhance edges
        img_gray_tmp = cv2.copyMakeBorder(cv2.cvtColor(img_ref, cv2.COLOR_RGB2GRAY),
            self.__pad_h, self.__pad_h, self.__pad_w, self.__pad_w,
            cv2.BORDER_CONSTANT, value=self.__border_color)
        img_gray_ref = sobel(img_as_float(img_gray_tmp))

        # Add first image to the list
        img_stabilized = cv2.copyMakeBorder(img_ref,
            self.__pad_h, self.__pad_h, self.__pad_w, self.__pad_w,
            cv2.BORDER_CONSTANT, value=self.__border_color)
        output_images = [img_stabilized]

        for i in range(1, len(images)):
            img = images[i]

            # Add padding and apply sobel filter to enhance edges
            img_gray_tmp = cv2.copyMakeBorder(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY),
                self.__pad_h, self.__pad_h, self.__pad_w, self.__pad_w,
                cv2.BORDER_CONSTANT, value=self.__border_color)
            img_gray = sobel(img_as_float(img_gray_tmp))

            shift, error, diffphase = phase_cross_correlation(
                img_gray_ref,
                img_gray,
                upsample_factor=100)

            (shift_y, shift_x) = shift
            print(shift)
            print(diffphase)
            tf_shift = transform.SimilarityTransform(translation=[-shift_x, -shift_y])

            img_bordered = cv2.copyMakeBorder(img,
                self.__pad_h, self.__pad_h, self.__pad_w, self.__pad_w,
                cv2.BORDER_CONSTANT, value=self.__border_color)
            img_stabilized = transform.warp(img_as_float(img_bordered), tf_shift)

            output_images.append(img_as_ubyte(img_stabilized))


        return output_images, self.filters_str


