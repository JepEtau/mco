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
from utils.hash import (
    calculate_hash,
    log_filter
)
from utils.pretty_print import *



def apply_cv2_transformation(img, x_y_theta:list):
    print(f"\tapply last transformation:", ', '.join([f"{t:.02f}" for t in x_y_theta]))
    t_x, t_y, t_theta = x_y_theta
    transformation_matrix = np.array(
        [[np.cos(t_theta), -np.sin(t_theta), t_x],
        [np.sin(t_theta), np.cos(t_theta), t_y]],
        dtype=np.float32)

    output_img = cv2.warpAffine(img,
        transformation_matrix, (img.shape[1], img.shape[0]))
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
        self.__border_color = [0, 0, 0]

        self.__use_roi = False
        self.__crop_w = 12
        self.__crop_h = 12

        # Do not use sobel, only for testing purpose
        self.__sobel = False

        self._height, self._width, self._channels = 0, 0, 0

        self.__index = 0
        self.__transformations = list()


    def __get_initial_image(self, img, last_transformation, verbose=False):
        # Apply transformation to the initial image
        if last_transformation is not None:
            print("\tApply transformation to the initial image:", last_transformation)
            initial_img_stabilized = apply_cv2_transformation(img, last_transformation)
        else:
            print("\tNo transformation applied to the initial image:")
            initial_img_stabilized = img

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


    def __stabilize_image(self, img, img_ref_gray, keypoints_ref, mode, verbose=False):
        img_gray_tmp = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

        if self.__use_roi:
            img_gray_tmp2 = img_gray_tmp[
                self.__crop_h:img_gray_tmp.shape[0] - self.__crop_h,
                self.__crop_w:img_gray_tmp.shape[1] - self.__crop_w,]

        if self.__sobel:
            img_gray = edge_sharpen_sobel_gray(image_gray=img_gray_tmp, index=self.__index)
            self.__index += 1
        else:
            img_gray = img_gray_tmp

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

        if not mode['vertical']:
            t_y = 0
        if not mode['horizontal']:
            t_x = 0
        if not mode['rotation']:
            t_theta = 0

        if verbose:
            print([t_x, t_y, t_theta])

        last_transformation = [t_x, t_y, t_theta]

        # Transformation contains scale, discard it
        transformation_matrix = np.array(
            [[np.cos(t_theta), -np.sin(t_theta), t_x],
            [np.sin(t_theta), np.cos(t_theta), t_y]],
            dtype=np.float32)

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
        img_stabilized = cv2.warpAffine(img,
            transformation_matrix, (img.shape[1], img.shape[0]))

        return img_stabilized, last_transformation


    def stabilize(self, shot, images,
        ref, mode, last_transformation,
        step_no, input_hash,
        get_hash:bool=False, do_log:bool=True,
        do_force=False):
        """Stabilize images without smoothing the trajectory
        """
        verbose=True
        transformations = {
            'start': None,
            'end': None,
        }

        if ref == 'start':
            # Start from first frame
            start_index = 0
        elif ref == 'end':
            # Start from last frame
            start_index = len(images) - 1
        elif ref == 'middle':
            # STart from middle of the segment
            start_index = int(len(images) / 2 - 1)
        else:
            sys.exit(print_red("CV2_deshaker.stabilize: error: ref=%s" % (ref)))

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
            return filters_str, None, transformations
        if do_log:
            hash = log_filter(filter_str, shot['hash_log_file'])
        else:
            hash = calculate_hash(filter_str=filter_str)
        print_lightcyan("\t\t\t(cv2) CV2_deshaker, images count:%d, start_index:%d" % (len(images), start_index))

        # Reset transformation
        self.__transformations.clear()


        if last_transformation is not None and ref == 'middle':
            print_red("Error: stabilize, previous transformation will be ignored, correct the stabilization segments!")
            last_transformation = None
        img_stabilized, img_ref_gray, keypoints_ref = self.__get_initial_image(
            img=images[start_index],
            last_transformation=last_transformation)
        self._height, self._width, self._channels = img_stabilized.shape

        if ref == 'middle':
            output_images = list()
            # from ref to end of segment
            start = start_index + 1
            end = len(images)
            for i in range(start, end):
                img_colored = images[i]

                # compute and get keypoints
                img_stabilized, transformation = self.__stabilize_image(
                    img=img_colored,
                    img_ref_gray=img_ref_gray,
                    keypoints_ref=keypoints_ref,
                    mode=mode)

                # append image
                output_images.append(img_stabilized)
                self.__transformations.append(transformation)

                # current frame is the newest reference
                img_gray_tmp2 = cv2.cvtColor(img_stabilized.copy(), cv2.COLOR_RGB2GRAY)
                if self.__use_roi:
                    print_yellow("warning: use ROI: not validated")
                    img_gray_tmp2 = img_gray_tmp2[
                        self.__crop_h+self.__pad:self.__pad+img_gray_tmp2.shape[0],
                        self.__crop_w+self.__pad:self.__pad+img_gray_tmp2.shape[1]]
                if self.__sobel:
                    print_yellow("warning: use sobel: not validated")
                    img_ref_gray = edge_sharpen_sobel_gray(image_gray=img_gray_tmp2, index=self.__index)
                    self.__index += 1
                else:
                    img_ref_gray = img_gray_tmp2

                # identify new points
                keypoints_ref = cv2.goodFeaturesToTrack(img_ref_gray,
                    maxCorners=self.__max_corners,
                    qualityLevel=self.__quality_level,
                    minDistance=self.__min_distance,
                    blockSize=self.__block_size,
                    mask=self.__mask,
                    useHarrisDetector=self.__use_harris_detector,
                    k=self.__k)

            if verbose:
                print_yellow("Save last transformation, used for the start of next segment", end= '')
                print(transformation)
            transformations['end'] = transformation


            # From ref to 0
            img_stabilized, img_ref_gray, keypoints_ref = self.__get_initial_image(
                img=images[start_index], last_transformation=last_transformation)
            start = start_index - 1
            end = 0
            for i in range(start, end-1, -1):
                img_colored = images[i]

                # compute and get keypoints
                img_stabilized, transformation = self.__stabilize_image(
                    img=img_colored,
                    img_ref_gray=img_ref_gray,
                    keypoints_ref=keypoints_ref,
                    mode=mode)

                # insert image
                output_images.insert(0, img_stabilized)
                self.__transformations.insert(0, transformation)

                # current frame is the newest reference
                img_gray_tmp2 = cv2.cvtColor(img_stabilized.copy(), cv2.COLOR_RGB2GRAY)
                if self.__use_roi:
                    print_yellow("warning: use ROI: not validated")
                    img_gray_tmp2 = img_gray_tmp2[
                        self.__crop_h+self.__pad:self.__pad+img_gray_tmp2.shape[0],
                        self.__crop_w+self.__pad:self.__pad+img_gray_tmp2.shape[1]]
                if self.__sobel:
                    print_yellow("warning: use sobel: not validated")
                    img_ref_gray = edge_sharpen_sobel_gray(image_gray=img_gray_tmp2, index=self.__index)
                    self.__index += 1
                else:
                    img_ref_gray = img_gray_tmp2

                # identify new points
                keypoints_ref = cv2.goodFeaturesToTrack(img_ref_gray,
                    maxCorners=self.__max_corners,
                    qualityLevel=self.__quality_level,
                    minDistance=self.__min_distance,
                    blockSize=self.__block_size,
                    mask=self.__mask,
                    useHarrisDetector=self.__use_harris_detector,
                    k=self.__k)

            if verbose:
                print_yellow("Save last transformation, used for the start of next segment", end= '')
                print(transformation)
            transformations['start'] = transformation


        elif ref == 'start':
            self.__transformations.append(last_transformation)
            output_images = [img_stabilized]
            start = 1
            end = len(images)
            transformation = None

            print_pink(f"stabilize from {ref}, start={start}, end={end}")
            for i in range(start, end):
                # if verbose:
                #     print(f"\timage {i}", end=' ')

                img_colored = images[i]

                # compute and get keypoints
                img_stabilized, transformation = self.__stabilize_image(
                    img=img_colored,
                    img_ref_gray=img_ref_gray,
                    keypoints_ref=keypoints_ref,
                    mode=mode)
                # if verbose:
                #     print(f"transformation {transformation}")

                # append image
                output_images.append(img_stabilized)
                self.__transformations.append(transformation)

                # Current frame is the newest reference
                img_gray_tmp2 = cv2.cvtColor(img_stabilized.copy(), cv2.COLOR_RGB2GRAY)
                if self.__use_roi:
                    print_yellow("warning: use ROI: not validated")
                    img_gray_tmp2 = img_gray_tmp2[
                        self.__crop_h+self.__pad:self.__pad+img_gray_tmp2.shape[0],
                        self.__crop_w+self.__pad:self.__pad+img_gray_tmp2.shape[1]]
                if self.__sobel:
                    print_yellow("warning: use sobel: not validated")
                    img_ref_gray = edge_sharpen_sobel_gray(image_gray=img_gray_tmp2, index=self.__index)
                    self.__index += 1
                else:
                    img_ref_gray = img_gray_tmp2

                # Identify new points
                keypoints_ref = cv2.goodFeaturesToTrack(img_ref_gray,
                    maxCorners=self.__max_corners,
                    qualityLevel=self.__quality_level,
                    minDistance=self.__min_distance,
                    blockSize=self.__block_size,
                    mask=self.__mask,
                    useHarrisDetector=self.__use_harris_detector,
                    k=self.__k)

            if verbose:
                print_yellow("Save last transformation, used for the start of next segment", end= '')
                print(transformation)
            transformations['start'] = None
            transformations['end'] = transformation


        elif ref == 'end':
            self.__transformations.append(last_transformation)
            output_images = [img_stabilized]
            transformation = None
            print_pink(f"stabilize from {ref}, start={start_index}, end={0}")
            for i in range(start_index-1, -1, -1):
                if verbose:
                    print(f"\timage {i}", end=' ')
                img_colored = images[i]

                # Compute and get keypoints
                img_stabilized, transformation = self.__stabilize_image(
                    img=img_colored,
                    img_ref_gray=img_ref_gray,
                    keypoints_ref=keypoints_ref,
                    mode=mode)
                if verbose:
                    print(f"transformation {transformation}")

                output_images.insert(0, img_stabilized)
                self.__transformations.insert(0, transformation)

                # Current frame is the newest reference
                img_gray_tmp2 = cv2.cvtColor(img_stabilized.copy(), cv2.COLOR_RGB2GRAY)
                if self.__use_roi:
                    print_yellow("warning: use ROI: not validated")
                    img_gray_tmp2 = img_gray_tmp2[
                        self.__crop_h+self.__pad:self.__pad+img_gray_tmp2.shape[0],
                        self.__crop_w+self.__pad:self.__pad+img_gray_tmp2.shape[1]]

                if self.__sobel:
                    print_yellow("warning: use sobel: not validated")
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


            print_yellow("ref=end, save transformation", end= '')
            print(transformation)
            # Transformation saved for the start of next segment
            transformations['end'] = None
            transformations['start'] = transformation

        return filters_str, output_images, transformations


    def get_transformations(self):
        return self.__transformations


class Skimage_deshaker:
    # DO NOT USE (archive)
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


