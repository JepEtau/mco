# -*- coding: utf-8 -*-
import sys
import cv2
import numpy as np
from statistics import mean



from filters.filters import *
from utils.hash import (
    calculate_hash,
    log_filter
)
from utils.pretty_print import *


DEBUG_DESHAKE = True
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
        self.__use_harris_detector = False
        self.__k = 0.04

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

        self.__improve_ref = True
        self.__img_contour = None
        self.__has_roi_defined = False

        self.__gamma_lut = np.empty((1,256), np.uint8)
        for i in range(256):
            self.__gamma_lut[0, i] = np.clip(pow(i / 255.0, 0.6) * 255.0, 0, 255)


    def improve_ref(self, img):
        if self.__improve_ref:
            return improve_ref_img(img,
                gamma_lut=self.__gamma_lut)
        return img


    def get_keypoints(self, img_gray):
        img_improved = self.improve_ref(img_gray)
        keypoints = cv2.goodFeaturesToTrack(img_improved, **self.__gftt)

        if not self.__has_roi_defined:
            return (keypoints, img_improved)

        filtered_keypoints = list()
        # display point
        do_show = False

        print(len(keypoints))
        for kp in keypoints:
            __kp = kp[0]
            # print(f"{__kp[0]}, {__kp[1]}")
            if do_show:
                cv2.circle(img_improved, (int(__kp[0]), int(__kp[1])), 3, [255,255,255], 1)

            # if not (self.__img_contour[2] < __kp[0] < self.__img_contour[3]
            #     and self.__img_contour[0] < __kp[1] < self.__img_contour[1]):
            #     # Not inside a cropped area of the image
            #     # i.e. on the border of the src img, bad quality
            #     # print("\tdiscard")
            #     continue

            if is_point_inside(__kp, self.__roi):
                filtered_keypoints.append(kp)

        if do_show:
            cv2.imshow("get_keypoints", img_improved)
            cv2.waitKey()


        print(lightcyan(f"filtered kp: "), f"{len(filtered_keypoints)}")
        # print_lightcyan(f"{len(filtered_keypoints)}")
        filtered_keypoints = np.array(filtered_keypoints, dtype=keypoints.dtype)

        return (filtered_keypoints, img_improved)



    def __get_initial_image(self, img, last_transformation, verbose=False):
        # Apply transformation to the initial image
        if last_transformation is not None:
            print("\tApply transformation to the initial image:", last_transformation)
            initial_img_stabilized = apply_cv2_transformation(img, last_transformation)
        else:
            print("\tNo transformation applied to the initial image:")
            initial_img_stabilized = img

        img_gray = cv2.cvtColor(initial_img_stabilized, cv2.COLOR_RGB2GRAY)
        (keypoints, img_for_tracking) = self.get_keypoints(img_gray=img_gray)

        return initial_img_stabilized, img_for_tracking, keypoints


    def __stabilize_image(self, img, img_ref_gray, keypoints_ref, mode, verbose=False):
        img_gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        img_for_tracking = self.improve_ref(img_gray)
        # img_for_tracking = cv2.bitwise_and(img_improved, img_improved, mask=self.img_mask)
        # Calculate optical flow (i.e. track feature points)
        keypoints, status, err = cv2.calcOpticalFlowPyrLK(
            prevImg=img_for_tracking,
            nextImg=img_ref_gray,
            prevPts=keypoints_ref,
            nextPts=None,
            **self.__lk_params)

        try:
            # Estimate transformation matrix
            transformation = cv2.estimateAffinePartial2D(
                keypoints_ref, keypoints[status==1])[0]

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
            print_red(f"exception: __stabilize_image: transformation not found, use previous")
            print_yellow(f"\tkeypoints_ref: {len(keypoints_ref)}, new: {len(keypoints[status==1])}")
            print(f"\t{self.__last_transformation}")
            t_x, t_y, t_theta = self.__last_transformation
            t_theta = 0

            if False:
                # draw the tracks
                for new in keypoints_ref:
                    a, b = new.ravel()
                    frame = cv2.circle(img_ref_gray, (int(a), int(b)), 5, [255,255,255], 1)
                cv2.imshow("ref", frame)
                cv2.waitKey()

                if keypoints is not None:
                    good_new = keypoints[status==1]

                # draw the tracks
                for new in good_new:
                    a, b = new.ravel()
                    frame2 = cv2.circle(img_for_tracking, (int(a), int(b)), 5, [255,255,255], 1)
                cv2.imshow("ref", frame2)
                cv2.waitKey()
                # cv2.destroyAllWindows()


        if not mode['vertical']:
            t_y = 0
        if not mode['horizontal']:
            t_x = 0
        if not mode['rotation']:
            t_theta = 0

        if verbose:
            print([t_x, t_y, t_theta])

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
            for new in good_new:
                a, b = new.ravel()
                frame = cv2.circle(img_for_tracking, (int(a), int(b)), 5, [255,255,255], 1)
            cv2.imshow("Stabilize", frame)
            cv2.waitKey()

        # Apply transformation
        img_stabilized = cv2.warpAffine(img,
            transformation_matrix, (img.shape[1], img.shape[0]))

        return img_stabilized, last_transformation


    def stabilize(self, shot, images,
        ref, mode, last_transformation,
        step_no, input_hash,
        roi:list=list(),
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
            # Start from middle of the segment
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

        # Generate and log hash
        filter_str = f"{input_hash},stab={filters_str}"
        if get_hash:
            hash = calculate_hash(filter_str=filter_str)
            return filters_str, None, transformations
        if do_log:
            hash = log_filter(filter_str, shot['hash_log_file'])
        else:
            hash = calculate_hash(filter_str=filter_str)
        print_lightcyan("\t\t\t(cv2) CV2_deshaker, images count:%d, start_index:%d" % (len(images), start_index))


        # Create a mask from roi coordinates
        self.img_mask = create_roi_mask(roi, images[0])
        self.__roi = roi
        h, w, _ = images[0].shape
        upscale_factor = int(h/(INITIAL_FRAME_HEIGHT + IMG_BORDER_LOW_RES))
        self.__img_contour = [
            upscale_factor * (ROI_MIN_T + IMG_BORDER_LOW_RES),
            h - upscale_factor * (ROI_MIN_B + IMG_BORDER_LOW_RES),
            upscale_factor * (ROI_MIN_L + IMG_BORDER_LOW_RES),
            w - upscale_factor * (ROI_MIN_R + IMG_BORDER_LOW_RES),
        ]
        # print(self.__img_contour)

        # Determine if this segment contains ROI
        roi_count = 0
        for area in roi:
            if area['enable'] and len(area['points']) >= 3:
                roi_count += 1
        self.__has_roi_defined = True if roi_count > 0 else False


        # Reset transformation
        self.__transformations.clear()

        if last_transformation is not None and ref == 'middle':
            print_red("Error: stabilize, previous transformation will be ignored, correct the stabilization segments!")
            last_transformation = None
        img_stabilized, img_for_tracking, keypoints_ref = self.__get_initial_image(
            img=images[start_index],
            last_transformation=last_transformation)
        self._height, self._width, self._channels = img_stabilized.shape

        # cv2.imwrite("/home/adg/mco/cache/ep01/asuivre/004/07/img_for_tracking.png", img_for_tracking)

        if ref == 'middle':
            output_images = [img_stabilized]
            # from ref to end of segment
            start = start_index + 1
            end = len(images)
            for i in range(start, end):
                img_colored = images[i]

                # compute and get keypoints
                img_stabilized, transformation = self.__stabilize_image(
                    img=img_colored,
                    img_ref_gray=img_for_tracking,
                    keypoints_ref=keypoints_ref,
                    mode=mode)

                # append image
                output_images.append(img_stabilized)
                self.__transformations.append(transformation)

                # current frame is the newest reference
                # identify new points
                img_gray = cv2.cvtColor(img_stabilized, cv2.COLOR_RGB2GRAY)
                (keypoints_ref, img_for_tracking) = self.get_keypoints(img_gray=img_gray)

            if verbose:
                print_yellow("Save last transformation, used for the start of next segment", end= '')
                print(transformation)
            transformations['end'] = transformation


            # From ref to 0
            img_stabilized, img_for_tracking, keypoints_ref = self.__get_initial_image(
                img=images[start_index], last_transformation=last_transformation)
            start = start_index - 1
            end = 0
            for i in range(start, end-1, -1):
                img_colored = images[i]

                # compute and get keypoints
                img_stabilized, transformation = self.__stabilize_image(
                    img=img_colored,
                    img_ref_gray=img_for_tracking,
                    keypoints_ref=keypoints_ref,
                    mode=mode)

                # insert image
                output_images.insert(0, img_stabilized)
                self.__transformations.insert(0, transformation)

                # current frame is the newest reference
                img_gray = cv2.cvtColor(img_stabilized, cv2.COLOR_RGB2GRAY)
                # identify new points
                (keypoints_ref, img_for_tracking) = self.get_keypoints(img_gray=img_gray)

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
                    img_ref_gray=img_for_tracking,
                    keypoints_ref=keypoints_ref,
                    mode=mode)
                # if verbose:
                #     print(f"transformation {transformation}")

                # append image
                output_images.append(img_stabilized)
                self.__transformations.append(transformation)

                # Current frame is the newest reference
                # Identify new points
                img_gray = cv2.cvtColor(img_stabilized, cv2.COLOR_RGB2GRAY)
                (keypoints_ref, img_for_tracking) = self.get_keypoints(img_gray=img_gray)

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
                    img_ref_gray=img_for_tracking,
                    keypoints_ref=keypoints_ref,
                    mode=mode)
                if verbose:
                    print(f"transformation {transformation}")

                output_images.insert(0, img_stabilized)
                self.__transformations.insert(0, transformation)

                # Current frame is the newest reference
                # Identify new points to track
                img_gray = cv2.cvtColor(img_stabilized, cv2.COLOR_RGB2GRAY)
                (keypoints_ref, img_for_tracking) = self.get_keypoints(img_gray=img_gray)


            print_yellow("ref=end, save transformation", end= '')
            print(transformation)
            # Transformation saved for the start of next segment
            transformations['end'] = None
            transformations['start'] = transformation

        return filters_str, output_images, transformations


    def get_transformations(self):
        return self.__transformations






def create_roi_mask(roi, img):
    height, width, c = img.shape

    white_image = np.ones([height, width, 1], dtype=np.uint8) * 255
    black_image = np.zeros([height, width, 1], dtype=np.uint8)
    img_mask = draw_roi(black_image, roi)
    cv2.imwrite("/home/adg/mco/cache/mask.png", img_mask)
    return img_mask


def draw_roi(img, roi:list):
    for area in roi:
        points = np.array(area['points'], np.int32)
        if not area['enable'] or len(points) < 3:
            continue
        points = points.reshape((-1,1,2))
        if area['mode'] != 'in':
            cv2.fillPoly(img, [points], 0)
        else:
            cv2.fillPoly(img, [points], 255)

    return img



def improve_ref_img(img, gamma_lut:list=list()):
    img_improved = img

    # img_improved = cv2.normalize(img, img, 0, 255, cv2.NORM_MINMAX)

    # img_improved = cv2_bilateral_filter(img, 11, 13, 13)

    tmp = img_as_float(img_improved)
    tmp = unsharp_mask(tmp, 2, 0.5, preserve_range=False)
    img_improved = img_as_ubyte(tmp)

    # Gamma correction: pas d'amélioration notable
    # img_improved = cv2.LUT(img_improved, gamma_lut)

    # Increase contrast
    img_improved = cv2.convertScaleAbs(img_improved, alpha=1.3, beta=0)

    return img_improved


def is_point_inside(point, roi):
    for area in roi:
        if not area['enable'] or len(area['points']) < 3:
            continue

        contour = np.array(area['points'], np.float32).reshape((-1,1,2))
        result = cv2.pointPolygonTest(contour, point, False)
        if result >= 0:
            return True

    return False


