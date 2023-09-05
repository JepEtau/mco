# -*- coding: utf-8 -*-
import sys
import cv2
import numpy as np

from utils.pretty_print import *
from processing_chain.hash import log_filter


# TODO This class cannot be used anymore: rework this!
class Homography:
    def __init__(self, extractor=None, matching=None) -> None:
        self.__pad_h = 20
        self.__pad_w = 20
        self.__use_roi=False
        self.__crop_w = 20
        self.__crop_h = 20

        # sift, surf, brisk, orb
        if extractor is None:
            self.feature_extractor = 'sift'
        else:
            self.feature_extractor = extractor

        # flann, bf
        if matching is None:
            self.feature_matching = 'bf'
        else:
            self.feature_matching = matching

        self.filters_str = "%s_%s" % (
            self.feature_extractor,
            self.feature_matching)

        self._height, self._width, self._channels = 0, 0, 0

        sys.exit(print_red("Homography: rework this class"))


    def __get_initial_image(self, img):
        img_gray_tmp = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        if self.__use_roi:
            img_gray = img_gray[
                self.__crop_h:self.__crop_h+img_gray_tmp.shape[0],
                self.__crop_w:self.__crop_w+img_gray_tmp.shape[1]]

        keypoints, features = self.detect_and_describe(img_gray,
            method=self.feature_extractor)

        return img, keypoints, features


    def __stabilize_image(self, img, keypoints_ref, features_ref, do_log=False):
        img_gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        if self.__use_roi:
            img_gray = img_gray[
                self.__crop_h:img_gray.shape[0] - self.__crop_h,
                self.__crop_w:img_gray.shape[1] - self.__crop_w,]

        cv2.imwrite("test.png", img_gray)

        # Detect and describe
        keypoints, features = self.detect_and_describe(
            image=img_gray,
            method=self.feature_extractor)
        if self.feature_matching == 'bf':
            matches = self.match_keypoints_bf(
                features,
                features_ref,
                method=self.feature_extractor)
        elif self.feature_matching == 'knn':
            matches = self.match_keypoints_knn(
                features,
                features_ref,
                ratio=0.2,
                method=self.feature_extractor)
        else:
            sys.exit("error: unknown feature matching: %s" % (self.feature_matching))


        # Get homography
        M = self.get_homography(
            keypoints, keypoints_ref,
            features, features_ref,
            matches,
            reproj_threshold=4)
        if M is None:
            print("Error!")
        (matches, H, status) = M

        # Apply the perspective transformation
        img_stabilized = cv2.warpPerspective(img,
            H, (img.shape[1], img.shape[0]))

        return img_stabilized



    def stabilize(self, images, ref, step_no, input_hash, do_force=False, do_log=False):
        """Stabilize images without smoothing the trajectory
            note: a list of images is needed because it can be only a part of a shot
        """

        if ref == 'middle':
            use_static_ref = True
            ref_index = int(len(images) / 2)
        else:
            use_static_ref = False
            ref_index = 0

        suffix = ""
        if self.__use_roi:
            suffix += "roi_"

        # Generate and log hash
        hash = log_filter("%s,homography=%s:%s" % (input_hash, suffix, self.filters_str), shot['hash_log_file'])
        print_lightcyan("\t\t\t(cv2) homography, output hash= %s" % (step_no, hash))

        img_stabilized, keypoints_ref, features_ref = self.__get_initial_image(
            img=images[ref_index])
        self._height, self._width, self._channels = img_stabilized.shape

        if ref == 'middle':
            print("not yet implemented")
            sys.exit("error")
        else:
            output_images = [img_stabilized]
            for i in range(ref_index + 1, len(images)):
                if do_log:
                    print("frame %d/%d: " % (i, len(images)), end='')

                img_colored = images[i]
                if do_log:
                    print("image=%d" % (i), end=' ')

                # compute and get keypoints
                img_stabilized = self.__stabilize_image(
                    img=img_colored,
                    keypoints_ref=keypoints_ref,
                    features_ref=features_ref)

                output_images.append(img_stabilized)
                if do_log:
                    print("append")

                # Current frame is the newest reference
                img_ref_gray = cv2.cvtColor(img_stabilized.copy(), cv2.COLOR_RGB2GRAY)

                if self.__use_roi:
                    img_ref_gray = img_ref_gray[
                        self.__crop_h+self.__pad_h:self.__pad_h+img_ref_gray.shape[0],
                        self.__crop_w+self.__pad_w:self.__pad_w+img_ref_gray.shape[1]]

                keypoints_ref, features_ref = self.detect_and_describe(img_ref_gray,
                    method=self.feature_extractor)

        return self.filters_str, output_images





    def detect_and_describe(self, image, method=None):
        """
        Compute key points and feature descriptors using an specific method
        """

        assert method is not None, "You need to define a feature detection method. Values are: 'sift', 'surf'"

        # detect and extract features from the image
        if method == 'sift':
            descriptor = cv2.SIFT_create()
        elif method == 'surf':
            descriptor = cv2.xfeatures2d.SURF_create()
        elif method == 'brisk':
            descriptor = cv2.BRISK_create()
        elif method == 'orb':
            descriptor = cv2.ORB_create()

        # get keypoints and descriptors
        (kps, features) = descriptor.detectAndCompute(image, None)

        return (kps, features)


    def match_keypoints_bf(self, featuresA, featuresB, method):
        bf = self.create_matcher(method, crossCheck=True)

        # Match descriptors.
        best_matches = bf.match(featuresA,featuresB)

        # Sort the features in order of distance.
        # The points with small distance (more similarity) are ordered first in the vector
        raw_matches = sorted(best_matches, key = lambda x:x.distance)
        # print("Raw matches (Brute force):", len(raw_matches))
        return raw_matches


    def match_keypoints_knn(self, featuresA, featuresB, ratio, method):
        bf = self.create_matcher(method, crossCheck=False)
        # compute the raw matches and initialize the list of actual matches
        raw_matches = bf.knnMatch(featuresA, featuresB, 2)
        print("Raw matches (knn):", len(raw_matches))
        matches = []
        # loop over the raw matches
        for m, n in raw_matches:
            # ensure the distance is within a certain ratio of each
            # other (i.e. Lowe's ratio test)
            if m.distance < n.distance * ratio:
                matches.append(m)
        return matches


    def create_matcher(self, method, crossCheck):
        "Create and return a Matcher Object"

        if method == 'sift' or method == 'surf':
            bf = cv2.BFMatcher(cv2.NORM_L2, crossCheck=crossCheck)
            # bf = cv2.BFMatcher(cv2.NORM_L2SQR, crossCheck=crossCheck)
        elif method == 'orb' or method == 'brisk':
            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=crossCheck)
        return bf



    # def findHomography(srcPoints, dstPoints, method=None, ransacReprojThreshold=None, mask=None, maxIters=None, confidence=None, /) -> retval, mask
    # findHomography(srcPoints, dstPoints[, method[, ransacReprojThreshold[, mask[, maxIters[, confidence]]]]]) -> retval, mask
    # .   @brief Finds a perspective transformation between two planes.
    # .
    # .   @param srcPoints Coordinates of the points in the original plane, a matrix of the type CV_32FC2
    # .   or vector\<Point2f\> .
    # .   @param dstPoints Coordinates of the points in the target plane, a matrix of the type CV_32FC2 or
    # .   a vector\<Point2f\> .
    # .   @param method Method used to compute a homography matrix. The following methods are possible:
    # .   -   **0** - a regular method using all the points, i.e., the least squares method
    # .   -   @ref RANSAC - RANSAC-based robust method
    # .   -   @ref LMEDS - Least-Median robust method
    # .   -   @ref RHO - PROSAC-based robust method
    # .   @param ransacReprojThreshold Maximum allowed reprojection error to treat a point pair as an inlier
    # .   (used in the RANSAC and RHO methods only). That is, if
    # .   \f[\| \texttt{dstPoints} _i -  \texttt{convertPointsHomogeneous} ( \texttt{H} * \texttt{srcPoints} _i) \|_2  >  \texttt{ransacReprojThreshold}\f]
    # .   then the point \f$i\f$ is considered as an outlier. If srcPoints and dstPoints are measured in pixels,
    # .   it usually makes sense to set this parameter somewhere in the range of 1 to 10.
    # .   @param mask Optional output mask set by a robust method ( RANSAC or LMeDS ). Note that the input
    # .   mask values are ignored.
    # .   @param maxIters The maximum number of RANSAC iterations.
    # .   @param confidence Confidence level, between 0 and 1.
    # .
    # .   The function finds and returns the perspective transformation \f$H\f$ between the source and the
    # .   destination planes:
    # .
    # .   \f[s_i  \vecthree{x'_i}{y'_i}{1} \sim H  \vecthree{x_i}{y_i}{1}\f]
    # .
    # .   so that the back-projection error
    # .
    # .   \f[\sum _i \left ( x'_i- \frac{h_{11} x_i + h_{12} y_i + h_{13}}{h_{31} x_i + h_{32} y_i + h_{33}} \right )^2+ \left ( y'_i- \frac{h_{21} x_i + h_{22} y_i + h_{23}}{h_{31} x_i + h_{32} y_i + h_{33}} \right )^2\f]
    # .
    # .   is minimized. If the parameter method is set to the default value 0, the function uses all the point
    # .   pairs to compute an initial homography estimate with a simple least-squares scheme.
    # .
    # .   However, if not all of the point pairs ( \f$srcPoints_i\f$, \f$dstPoints_i\f$ ) fit the rigid perspective
    # .   transformation (that is, there are some outliers), this initial estimate will be poor. In this case,
    # .   you can use one of the three robust methods. The methods RANSAC, LMeDS and RHO try many different
    # .   random subsets of the corresponding point pairs (of four pairs each, collinear pairs are discarded), estimate the homography matrix
    # .   using this subset and a simple least-squares algorithm, and then compute the quality/goodness of the
    # .   computed homography (which is the number of inliers for RANSAC or the least median re-projection error for
    # .   LMeDS). The best subset is then used to produce the initial estimate of the homography matrix and
    # .   the mask of inliers/outliers.
    # .
    # .   Regardless of the method, robust or not, the computed homography matrix is refined further (using
    # .   inliers only in case of a robust method) with the Levenberg-Marquardt method to reduce the
    # .   re-projection error even more.
    # .
    # .   The methods RANSAC and RHO can handle practically any ratio of outliers but need a threshold to
    # .   distinguish inliers from outliers. The method LMeDS does not need any threshold but it works
    # .   correctly only when there are more than 50% of inliers. Finally, if there are no outliers and the
    # .   noise is rather small, use the default method (method=0).
    # .
    # .   The function is used to find initial intrinsic and extrinsic matrices. Homography matrix is
    # .   determined up to a scale. Thus, it is normalized so that \f$h_{33}=1\f$. Note that whenever an \f$H\f$ matrix
    # .   cannot be estimated, an empty one will be returned.
    # .
    # .   @sa
    # .   getAffineTransform, estimateAffine2D, estimateAffinePartial2D, getPerspectiveTransform, warpPerspective,
    # .   perspectiveTransform
    def get_homography(self, kpsA, kpsB, featuresA, featuresB, matches, reproj_threshold):
        # convert the keypoints to numpy arrays
        kpsA = np.float32([kp.pt for kp in kpsA])
        kpsB = np.float32([kp.pt for kp in kpsB])

        if len(matches) > 4:
            # construct the two sets of points
            ptsA = np.float32([kpsA[m.queryIdx] for m in matches])
            ptsB = np.float32([kpsB[m.trainIdx] for m in matches])

            # estimate the homography between the sets of points
            # (H, status) = cv2.findHomography(ptsA, ptsB, cv2.RANSAC, reproj_threshold)
            # (H, status) = cv2.findHomography(ptsA, ptsB, cv2.LMEDS, reproj_threshold)

            (H, status) = cv2.findHomography(
                srcPoints=ptsA,
                dstPoints=ptsB,
                method=cv2.RANSAC,
                ransacReprojThreshold=reproj_threshold)
            return (matches, H, status)
        else:
            print("Error: not enough points")
            return None








