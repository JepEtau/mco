# -*- coding: utf-8 -*-
import sys
import cv2
import numpy as np
from statistics import mean
# from matplotlib import pyplot as plt

from img_toolbox.filters import *
from img_toolbox.utils import is_highres_height, is_lowres_height
from utils.hash import (
    calculate_hash,
    log_filter
)
from utils.pretty_print import *


DEBUG_DESHAKE = False
# No improvments, sometime worst
# ROI_MIN_L = 17
# ROI_MIN_R = 14
# ROI_MIN_T = 6
# ROI_MIN_B = 4
ROI_MIN_L = 0
ROI_MIN_R = 0
ROI_MIN_T = 0
ROI_MIN_B = 0

def apply_cv2_transformation(img, x_y_theta:list):
    t_x, t_y, t_theta = x_y_theta
    transformation_matrix = np.array(
        [[np.cos(t_theta), -np.sin(t_theta), t_x],
        [np.sin(t_theta), np.cos(t_theta), t_y]],
        dtype=np.float32)

    output_img = cv2.warpAffine(img,
        transformation_matrix, (img.shape[1], img.shape[0]))
    return output_img


class Python_deshaker:

    def __init__(self) -> None:

        if False:
            self.__max_corners = 500
            self.__quality_level = 0.01
            self.__min_distance = 10
            self.__block_size = 3
            self.__use_harris_detector = False
            self.__k = 0.04
        else:
            # Previously
            self.__max_corners = 300
            self.__quality_level = 0.01
            self.__min_distance = 30.0
            self.__block_size = 3
            self.__use_harris_detector = True
            self.__k = 0.04



        self.__sift_contrast_hreshold = 0.04
        self.__sift_edge_threshold = 10


        self.__gftt = dict(
            maxCorners = self.__max_corners,
            qualityLevel = self.__quality_level,
            minDistance = self.__min_distance,
            blockSize = self.__block_size,
            useHarrisDetector=self.__use_harris_detector,
            k=self.__k)

        # Parameters for lucas kanade optical flow
        # self.__lk_params = dict(
        #     winSize = (15, 15),
        #     maxLevel = 2,
        #     criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT,
        #                 10, 0.03))
        self.__lk_params = dict()

        self._height, self._width, self._channels = 0, 0, 0
        self.__transformations = list()
        self.img_mask = None
        self.__img_contour = None

    def generate_filter_str(self, segment):
        filter_str = f"{segment['stab']}"
        if segment['stab'] == 'cv2':
            filter_str += f":{segment['cv2']['feature_extractor']}"

            if segment['cv2']['feature_extractor'] == 'gftt':
                filter_str += f":{self.__max_corners}"
                filter_str += f":{self.__quality_level:0.2f}"
                filter_str += f":{self.__min_distance:.1f}"
                filter_str += f":{self.__block_size}"

            elif segment['cv2']['feature_extractor'] == 'sift':
                try:
                    filter_str += f":{segment['cv2']['contrast_threshold']}"
                except:
                    filter_str += f":{self.__sift_contrast_hreshold}"
                try:
                    filter_str += f":{segment['cv2']['edge_threshold']}"
                except:
                    filter_str += f":{self.__sift_edge_threshold}"

        if segment['tracker']['enable']:
            filter_str += f":{'in' if segment['tracker']['inside'] else 'out'}"
            hash = calculate_hash(','.join([str(x) for x in np.array(segment['tracker']['regions'], dtype=list).reshape(-1).tolist()]))
            filter_str += f":{hash}"

        return filter_str


    def improve_ref(self, img):
        if self.__enhance != 'none':
            return enhance_gray_img(img, self.__enhance)
        return img


    def get_keypoints(self, img_gray):
        img_improved = self.improve_ref(img_gray)

        if self.__descriptor is None:
            keypoints = cv2.goodFeaturesToTrack(image=img_improved, **self.__gftt)
        else:
            if self.img_mask is not None:
                img_improved = cv2.bitwise_and(img_improved, img_improved,
                                               mask=self.img_mask * 255)
                # cv2.imshow('img_improved',img_improved)
                # cv2.waitKey()
                # cv2.destroyAllWindows()
            kpts, features = self.__descriptor.detectAndCompute(img_improved, None)
            keypoints = np.array([kp.pt for kp in kpts], dtype='float32').reshape(-1, 1, 2)

        return (keypoints, img_improved)

        # filtered_keypoints = list()
        # # display point
        # do_show = False
        #
        # if do_show:
        #     img_improved_copy = img_improved.copy()
        #     for kp in keypoints:
        #         __kp = kp[0]
        #         cv2.circle(img_improved_copy, (int(__kp[0]), int(__kp[1])), 5, [128,128,128], 1)
        #
        # for kp in keypoints:
        #     __kp = kp[0]
        #     # print(f"{__kp[0]}, {__kp[1]}")
        #     # if do_show:
        #     #     cv2.circle(img_improved_copy, (int(__kp[0]), int(__kp[1])), 3, [255,255,255], 1)

        #     # if not (self.__img_contour[2] < __kp[0] < self.__img_contour[3]
        #     #     and self.__img_contour[0] < __kp[1] < self.__img_contour[1]):
        #     #     # Not inside a cropped area of the image
        #     #     # i.e. on the border of the src img, bad quality
        #     #     # print("\tdiscard")
        #     #     continue
        #     if is_point_valid(__kp, self.__tracker_contours, self.__tracker_is_inside):
        #         filtered_keypoints.append(kp)
        #
        # filtered_keypoints = np.array(filtered_keypoints, dtype=np.float32)
        # for kp in filtered_keypoints:
        #     __kp = kp[0]
        #     if do_show:
        #         cv2.circle(img_improved_copy, (int(__kp[0]), int(__kp[1])), 3, [255,255,255], 2)
        #
        # if do_show:
        #     cv2.imshow(f"get_keypoints", img_improved_copy)
        #     cv2.waitKey()
        #
        # print(f" -> {len(filtered_keypoints)}")
        # # print_lightcyan(f"{len(filtered_keypoints)}")
        #
        # return (filtered_keypoints, img_improved)



    def __get_initial_image(self, img, last_transformation, verbose=False):
        # Apply transformation to the initial image
        if last_transformation is not None:
            print(f"\t\t\tapply last transformation to the initial img:", ', '.join([f"{t:.02f}" for t in last_transformation]))
            initial_img_stabilized = apply_cv2_transformation(img, last_transformation)
            self.__last_transformation = last_transformation
        else:
            print("\tNo transformation applied to the initial image:")
            initial_img_stabilized = img
            self.__last_transformation = [0, 0, 0]

        img_gray = cv2.cvtColor(initial_img_stabilized, cv2.COLOR_BGR2GRAY)
        (keypoints, img_for_tracking) = self.get_keypoints(img_gray=img_gray)

        return initial_img_stabilized, img_for_tracking, keypoints


    def __stabilize_image_cv2(self, img_to, img_from_gray, keypoints_from, mode, verbose=False):
        img_to_gray = cv2.cvtColor(img_to, cv2.COLOR_BGR2GRAY)
        img_to_gray = self.improve_ref(img_to_gray)

        keypoints_to = None
        is_erroneous = False
        try:
            keypoints_to, status, err = cv2.calcOpticalFlowPyrLK(
                prevImg=img_from_gray,
                nextImg=img_to_gray,
                prevPts=keypoints_from,
                nextPts=None,
                **self.__lk_params)
        except:
            print_red(f"exception: calcOpticalFlowPyrLK: erroneous")
            is_erroneous = True


        if not is_erroneous:
            if status is None:
                valid_keypoints_from, valid_keypoints_to = list(), list()
            else:
                valid_keypoints_from, valid_keypoints_to = keypoints_from[status==1], keypoints_to[status==1]
                # pprint(valid_keypoints_from)
                # pprint(valid_keypoints_to)
            # valid_keypoints_to, valid_keypoints_from = self.match_keypoints(optical_flow, keypoints_from)

            #drawing the tracks
            if False:
                resultingvectorcolor = np.random.randint(0, 255, (600, 3))
                resmask = np.zeros_like(img_to)
                second_frame = img_to.copy()
                for i, first, second in zip(range(len(valid_keypoints_to)), valid_keypoints_to, valid_keypoints_from):
                    # A, B = second.ravel()
                    # C, D = first.ravel()
                    # pprint(first)
                    # pprint(second)
                    A, B = np.array(second, dtype=int)
                    C, D = np.array(first, dtype=int)
                    color = resultingvectorcolor[i].tolist()
                    resmask = cv2.line(resmask, (A, B), (C, D), color, 1)
                    # second_frame = cv2.circle(second_frame, (A, B), 3, color, 1)
                    resvideo = cv2.add(second_frame, resmask)
                cv2.imshow('Result', resvideo)
                cv2.waitKey()


            # Estimate transformation matrix
            transformation = cv2.estimateAffinePartial2D(
                valid_keypoints_to, valid_keypoints_from)[0]

        try:
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
                    print_lightgrey(f"-> {len(valid_keypoints_to)} kps", end=' ')
            else:
                print("\ttransformation not found")
                t_x = t_y = t_theta = 0
        except:
            print_red(f"exception: __stabilize_image: transformation not found, use previous")
            # print_yellow(f"\tkeypoints_ref: {len(keypoints_ref)}, new: {len(keypoints[status==1])}")
            print(f"\t{self.__last_transformation}")
            t_x, t_y, t_theta = self.__last_transformation
            t_theta = 0

            if False:
                # draw the tracks
                if keypoints_ref is not None:
                    for new in keypoints_ref:
                        a, b = new.ravel()
                        frame = cv2.circle(img_ref_gray, (int(a), int(b)), 5, [255,255,255], 1)
                    cv2.imshow("ref", frame)
                    cv2.waitKey()
                else:
                    print_red("no keypointsref for image")
                    cv2.imshow("ref", img_ref_gray)

                if keypoints is not None:
                    good_new = keypoints[status==1]

                    # draw the tracks
                    for new in good_new:
                        a, b = new.ravel()
                        frame2 = cv2.circle(img_for_tracking, (int(a), int(b)), 5, [255,255,255], 1)
                    cv2.imshow("ref", frame2)
                    cv2.waitKey()
                else:
                    print_red("no keypoints for image to track")
                    cv2.imshow("ref", img_for_tracking)
                # cv2.destroyAllWindows()

        if abs(t_x) > 2*IMG_BORDER_HIGH_RES or abs(t_y) > 2*IMG_BORDER_HIGH_RES:
            print(p_red(f"erroneous calcOpticalFlowPyrLK: t_x={t_x}, t_y={t_y}"))
            print(f"{len(valid_keypoints_from)} points, {len(valid_keypoints_to)} points")
            if False:
                # draw the tracks
                if keypoints_ref is not None:
                    for new in keypoints_ref:
                        a, b = new.ravel()
                        frame = cv2.circle(img_ref_gray, (int(a), int(b)), 5, [255,255,255], 1)
                    cv2.imshow("ref", frame)
                    cv2.waitKey()
                else:
                    print_red("no keypointsref for image")
                    cv2.imshow("ref", img_ref_gray)

                if keypoints is not None:
                    good_new = keypoints[status==1]

                    # draw the tracks
                    for new in good_new:
                        a, b = new.ravel()
                        frame2 = cv2.circle(img_for_tracking, (int(a), int(b)), 5, [255,255,255], 1)
                    cv2.imshow("ref", frame2)
                    cv2.waitKey()
                else:
                    print_red("no keypoints for image to track")
                    cv2.imshow("ref", img_for_tracking)

                [t_x, t_y, t_theta] = [0,0,0]
            t_x, t_y, t_theta = self.__last_transformation

        if not mode['vertical']:
            t_y = 0
        if not mode['horizontal']:
            t_x = 0
        if not mode['rotation']:
            t_theta = 0

        self.__last_transformation = last_transformation = [t_x, t_y, t_theta]

        # Transformation contains scale, discard it
        transformation_matrix = np.array(
            [[np.cos(t_theta), -np.sin(t_theta), t_x],
            [np.sin(t_theta), np.cos(t_theta), t_y]],
            dtype=np.float32)

        if False:
            # Select good points
            if keypoints_ref is not None:
                good_new = keypoints_ref[status==1]

            # draw the tracks
            img_for_tracking_copy = img_for_tracking.copy()
            for new in good_new:
                a, b = new.ravel()
                cv2.circle(img_for_tracking_copy, (int(a), int(b)), 5, [255,255,255], 1)
            cv2.imshow("Stabilize", img_for_tracking_copy)
            cv2.waitKey()

        # Apply transformation
        img_stabilized = cv2.warpAffine(img_to.copy(),
            transformation_matrix, (img_to.shape[1], img_to.shape[0]))

        return img_stabilized, last_transformation


    def get_translation(self, flow, step=30):
        return (np.median(flow[:,:,0].T), flow[:, :, 0].T)

    def __stabilize_image(self, img_to, img_from_gray, keypoints_from, mode, verbose=False):
        if False:
            # Testing purpose
            img_to_gray = cv2.cvtColor(img_to, cv2.COLOR_BGR2GRAY)
            img_to_gray = self.improve_ref(img_to_gray)

            # flow = cv2.calcOpticalFlowFarneback(img_from_gray, img_to_gray, None, 0.5, 3, 15, 3, 5, 1.2, 0)
            # translation, pixel_direction = self.get_translation(flow)
            # pprint(translation)
            # pprint(pixel_direction)
            # img_stabilized = img_to
            # return img_stabilized, [0,0,0]


            shift, error, diffphase = phase_cross_correlation(
                img_as_float(img_from_gray),
                img_as_float(img_to_gray),
                upsample_factor=100)
            (shift_y, shift_x) = shift
            # print(shift)
            # print(diffphase)
            tf_shift = transform.SimilarityTransform(translation=[-shift_x, -shift_y])
            img_stabilized = img_as_ubyte(transform.warp(img_as_float(img_to), tf_shift))
            return img_stabilized, [shift_x, shift_y, 0]

        else:
            return self.__stabilize_image_cv2(img_to, img_from_gray, keypoints_from, mode, verbose=verbose)



    def stabilize(self, shot, images,
        segment, last_transformation,
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

        start_from = segment['from']
        start_frame_no = segment['ref']
        mode = segment['mode']
        static = segment['static']
        self.__enhance = segment['enhance']

        self.__is_tracker_enabled = segment['tracker']['enable']
        if self.__is_tracker_enabled:
            self.__tracker_contours = list()
            for region in segment['tracker']['regions']:
                self.__tracker_contours.append(np.array(region, np.float32).reshape((-1,1,2)))
            self.__tracker_is_inside = segment['tracker']['inside']

        if start_from == 'start':
            # Start from first frame
            start_index = 0
        elif start_from == 'end':
            # Start from last frame
            start_index = len(images) - 1
        elif start_from == 'middle':
            # Start from middle of the segment
            start_index = int(len(images) / 2 - 1)
        elif start_from == 'frame':
            # Start from specified frame no.
            start_index = start_frame_no
        else:
            sys.exit(print_red(f"CV2_deshaker.stabilize: error: ref={start_frame_no}"))

        stab_filter_str = self.generate_filter_str(segment=segment)

        # Generate and log hash
        filter_str = f"{input_hash},stab={stab_filter_str}"
        if get_hash:
            hash = calculate_hash(filter_str=filter_str)
            return stab_filter_str, None, transformations
        if do_log:
            hash = log_filter(filter_str, shot['hash_log_file'])
        else:
            hash = calculate_hash(filter_str=filter_str)
        print_lightcyan(f"\t\t\t(cv2) CV2_deshaker, images count:{len(images)}, start_index:{start_index}")


        self.__descriptor = None
        if segment['stab'] == 'cv2':
            if segment['cv2']['feature_extractor'] == 'sift':
                try:
                    contrast_threshold = segment['cv2']['contrast_threshold']
                    edge_threshold = segment['cv2']['edge_threshold']
                    self.__descriptor = cv2.SIFT_create(
                        contrastThreshold=contrast_threshold,
                        edgeThreshold=edge_threshold)
                except:
                    try:
                        contrast_threshold = segment['cv2']['contrast_threshold']
                        self.__descriptor = cv2.SIFT_create(
                            contrastThreshold=contrast_threshold)
                    except:
                        self.__descriptor = cv2.SIFT_create()

            elif segment['cv2']['feature_extractor'] == 'brisk':
                self.__descriptor = cv2.BRISK_create()


        # If using contour
        # h, w, _ = images[0].shape
        # upscale_factor = int(h/(INITIAL_FRAME_HEIGHT + IMG_BORDER_LOW_RES))
        # self.__img_contour = [
        #     upscale_factor * (ROI_MIN_T + IMG_BORDER_LOW_RES),
        #     h - upscale_factor * (ROI_MIN_B + IMG_BORDER_LOW_RES),
        #     upscale_factor * (ROI_MIN_L + IMG_BORDER_LOW_RES),
        #     w - upscale_factor * (ROI_MIN_R + IMG_BORDER_LOW_RES),
        # ]
        # print(self.__img_contour)

        self.img_mask = create_roi_mask(segment['tracker'], images[0].shape)
        if self.img_mask is not None:
            self.__gftt['mask'] = self.img_mask

        # Reset transformation
        self.__transformations.clear()

        if last_transformation is not None and start_from == 'middle':
            print_red("Error: stabilize, previous transformation will be ignored, correct the stabilization segments!")
            last_transformation = None
        img_stabilized, img_from_gray, keypoints_from = self.__get_initial_image(
            img=images[start_index],
            last_transformation=last_transformation)
        self._height, self._width, self._channels = img_stabilized.shape

        # cv2.imwrite("/home/adg/mco/cache/ep01/asuivre/004/07/img_for_tracking.png", img_for_tracking)

        if start_from in ['middle', 'frame']:
            verbose = True

            output_images = [img_stabilized]
            # from ref to end of segment
            start = start_index + 1
            end = len(images)
            for i in range(start, end):
                img_colored = images[i]
                if verbose:
                    print(f"\timage {i}")

                # compute and get keypoints
                img_stabilized, transformation = self.__stabilize_image(
                    img_to=img_colored,
                    img_from_gray=img_from_gray,
                    keypoints_from=keypoints_from,
                    mode=mode,
                    verbose=verbose)
                if verbose:
                    print_lightgrey(f"{transformation}")

                # append image
                output_images.append(img_stabilized)
                self.__transformations.append(transformation)

                if not static:
                    # current frame is the newest reference
                    # identify new points
                    img_gray = cv2.cvtColor(img_stabilized.copy(), cv2.COLOR_BGR2GRAY)
                    (keypoints_from, img_from_gray) = self.get_keypoints(img_gray=img_gray)

            if verbose:
                print_yellow("Save last transformation, used for the start of next segment", end= '')
                print(transformation)
            transformations['end'] = transformation


            # From ref to 0
            img_stabilized, img_from_gray, keypoints_from = self.__get_initial_image(
                img=images[start_index], last_transformation=last_transformation)
            start = start_index - 1
            end = 0
            for i in range(start, end-1, -1):
                img_colored = images[i]

                # compute and get keypoints
                img_stabilized, transformation = self.__stabilize_image(
                    img_to=img_colored,
                    img_from_gray=img_from_gray,
                    keypoints_from=keypoints_from,
                    mode=mode,
                    verbose=verbose)
                if verbose:
                    print_lightgrey(f"{transformation}")

                # insert image
                output_images.insert(0, img_stabilized)
                self.__transformations.insert(0, transformation)

                if not static:
                    # current frame is the newest reference
                    img_gray = cv2.cvtColor(img_stabilized, cv2.COLOR_BGR2GRAY)
                    # identify new points
                    (keypoints_from, img_from_gray) = self.get_keypoints(img_gray=img_gray)

            if verbose:
                print_yellow("Save last transformation, used for the start of next segment", end= '')
                print(transformation)
            transformations['start'] = transformation


        elif start_from == 'start':
            __debug = False

            self.__transformations.append(last_transformation)
            output_images = [img_stabilized]
            start = 1
            end = len(images)
            transformation = None

            print_pink(f"stabilize from {start_from}, start={start}, end={end}")
            for i in range(start, end):
                if verbose:
                    print(f"\timage {i}", end=' ')

                # compute and get keypoints
                img_stabilized, transformation = self.__stabilize_image(
                    img_to=images[i],
                    img_from_gray=img_from_gray,
                    keypoints_from=keypoints_from,
                    mode=mode,
                    verbose=verbose)
                if verbose:
                    print_lightgrey(f"{transformation}")

                # append image
                output_images.append(img_stabilized)
                self.__transformations.append(transformation)

                if not static:
                    # Current frame is the newest reference
                    # Identify new points
                    img_gray = cv2.cvtColor(img_stabilized.copy(), cv2.COLOR_RGB2GRAY)
                    del keypoints_from
                    del img_from_gray
                    (keypoints_from, img_from_gray) = self.get_keypoints(img_gray=img_gray)

            if verbose:
                print_yellow("Save last transformation, used for the start of next segment", end= '')
                print(transformation)
            transformations['start'] = None
            transformations['end'] = transformation


        elif start_from == 'end':
            self.__transformations.append(last_transformation)
            output_images = [img_stabilized]
            transformation = None
            print_pink(f"stabilize from {start_from}, start={start_index}, end={0}")
            for i in range(start_index-1, -1, -1):
                if verbose:
                    print(f"\timage {i}, ", end=' ')
                img_colored = images[i]

                # Compute and get keypoints
                img_stabilized, transformation = self.__stabilize_image(
                    img_to=img_colored,
                    img_from_gray=img_from_gray,
                    keypoints_from=keypoints_from,
                    mode=mode,
                    verbose=verbose)
                if verbose:
                    print_lightgrey(f"{transformation}")

                output_images.insert(0, img_stabilized)
                self.__transformations.insert(0, transformation)

                if not static:
                    # Current frame is the newest reference
                    # Identify new points to track
                    img_gray = cv2.cvtColor(output_images[0].copy(), cv2.COLOR_RGB2GRAY)
                    del keypoints_from
                    del img_from_gray
                    (keypoints_from, img_from_gray) = self.get_keypoints(img_gray=img_gray)


            print_yellow("ref=end, save transformation", end= '')
            # Transformation saved for the start of next segment
            transformations['end'] = None
            transformations['start'] = transformation
            pprint(transformations)
            print(f"{len(output_images)}")

        return stab_filter_str, output_images, transformations





def create_roi_mask(tracker, img_shape):
    if not tracker['enable']:
        return None

    height, width, c = img_shape

    if tracker['inside']:
        img_mask = np.zeros([height, width, 1], dtype=np.uint8)
        fill_color = 1
    else:
        img_mask = np.ones([height, width, 1], dtype=np.uint8)
        fill_color = 0

    for region in tracker['regions']:
        points = np.array(region, np.int32)
        points = points.reshape((-1,1,2))
        if tracker['is_hr'] and is_lowres_height(height):
            points /= 2
        elif not tracker['is_hr'] and is_highres_height(height):
            points *= 2
        cv2.fillPoly(img_mask, [points], fill_color)

    # cv2.imwrite("mask.png", img_mask)
    return img_mask


def enhance_gray_img(img, enhance:str):
    if enhance == 'auto':
        (img_improved, alpha, beta) = automatic_brightness_and_contrast_gray_deshake(img)

    elif enhance == 'contrast':
        # Increase contrast
        img_improved = cv2.convertScaleAbs(img, alpha=1.3, beta=0)
        img_improved = cv2.normalize(img_improved, img_improved, 0, 255, cv2.NORM_MINMAX)

    else:
        img_improved = img

    # hist = cv2.calcHist([img], [0], None, [256], [0, 256])
    # hist /= hist.sum()
    # img_norm = cv2.normalize(img, img, 0, 255, cv2.NORM_MINMAX)

    # img_improved = cv2_bilateral_filter(img, 11, 13, 13)

    # tmp = img_as_float(img_improved)
    # tmp = unsharp_mask(tmp, 2, 0.5, preserve_range=False)
    # img_improved = img_as_ubyte(tmp)

    # Gamma correction: pas d'amélioration notable
    # img_improved = cv2.LUT(img_improved, gamma_lut)

    # Increase contrast
    # img_improved = cv2.convertScaleAbs(img, alpha=0, beta=100)
    # ret,thresh = cv2.threshold(img,50,255,cv2.THRESH_BINARY)
    # img_improved = cv2.normalize(thresh, None, 0, 255, cv2.NORM_MINMAX)
    # if img_mask is not None and False:
    #     img_improved = cv2.bitwise_and(img, img, mask=img_mask)
    # else:
    #     img_improved = img

    # img_improved = cv2.normalize(img_improved, img_improved, 0, 255, cv2.NORM_MINMAX)

    # brightness = 100
    # contrast = 30
    # img = np.int16(img)
    # img = img * (contrast/127+1)  - contrast + brightness
    # img = np.clip(img, 0, 255)
    # img_improved = np.uint8(img)
    # img_improved = cv2.normalize(img_improved, img_improved, 0, 255, cv2.NORM_MINMAX)

    # img_sobel = sobel(img_as_float(img))
    # img_improved = img_as_ubyte(img_sobel)

    # img= cv2.bitwise_not(img)

    # tmp = img_as_float(blackAndWhiteImage)
    # tmp = unsharp_mask(tmp, 3, 0.5, preserve_range=False)
    # img_improved = img_as_ubyte(tmp)
    # threshold , blackAndWhiteImage= cv2.threshold(img, 20  , 255, cv2.THRESH_BINARY)
    # img_improved = cv2.normalize(img_improved, img_improved, 0, 255, cv2.NORM_MINMAX)

    # blurred = cv2.GaussianBlur(img, (3, 3), 0)
    # img_improved = cv2.Canny(blurred, 20, 200)

    # if img_mask is not None:
    #     img = cv2.bitwise_and(img, img, mask=img_mask)

    # cv2.imshow('Output',img_improved)
    # cv2.waitKey()
    # cv2.destroyAllWindows()

    return img_improved


def is_point_valid(point, contours, inside:bool=False):
    for contour in contours:
        result = cv2.pointPolygonTest(contour, point, False)
        if result >= 0:
            # Point is inside or on the contour
            return inside
    return not inside

