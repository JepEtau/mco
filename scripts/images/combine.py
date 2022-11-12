# -*- coding: utf-8 -*-
import cv2
import numpy as np
from copy import deepcopy



def detectAndDescribe(image, method=None):
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


def matchKeyPointsBF(featuresA, featuresB, method):
    bf = createMatcher(method, crossCheck=True)

    # Match descriptors.
    best_matches = bf.match(featuresA,featuresB)

    # Sort the features in order of distance.
    # The points with small distance (more similarity) are ordered first in the vector
    rawMatches = sorted(best_matches, key = lambda x:x.distance)
    # print("Raw matches (Brute force):", len(rawMatches))
    return rawMatches




def createMatcher(method,crossCheck):
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
def getHomography(kpsA, kpsB, featuresA, featuresB, matches, reprojThresh):
    # convert the keypoints to numpy arrays
    kpsA = np.float32([kp.pt for kp in kpsA])
    kpsB = np.float32([kp.pt for kp in kpsB])

    if len(matches) > 4:
        # construct the two sets of points
        ptsA = np.float32([kpsA[m.queryIdx] for m in matches])
        ptsB = np.float32([kpsB[m.trainIdx] for m in matches])

        # estimate the homography between the sets of points
        # (H, status) = cv2.findHomography(ptsA, ptsB, cv2.RANSAC, reprojThresh)
        # (H, status) = cv2.findHomography(ptsA, ptsB, cv2.LMEDS, reprojThresh)
        (H, status) = cv2.findHomography(ptsA, ptsB, cv2.RHO, reprojThresh)

        return (matches, H, status)
    else:
        print("Error: not enough points")
        return None





















def combine_images(geometry, img_fgd, img_bgd):
    # TODO:
    # - check if deepcopy is necessary


    # 1) crop foreground image
    img_foreground = img_fgd
    # img_foreground = deepcopy(img_fgd)
    img_foreground_tmp = img_foreground[
        geometry['cropT']:img_foreground.shape[0] - geometry['cropB'],
        geometry['cropL']:img_foreground.shape[1] - geometry['cropR']]


    # 2) resize image
    width_new = geometry['x1'] - geometry['x0']
    height_new = geometry['y1'] - geometry['y0']
    # print("\tx0=%d, x1=%d" % (geometry['x0'], geometry['x1']))
    # print("\ty0=%d, y1=%d" % (geometry['y0'], geometry['y1']))
    # print("\t%5d resize to: (%d, %d)" % (frame['no'], width_new, height_new))
    imgTmp = cv2.resize(img_foreground_tmp,
        (width_new, height_new),
        interpolation=cv2.INTER_LANCZOS4)
    # print("\t%5d resized: (%d, %d)" % (frame['no'], imgTmp.shape[1], imgTmp.shape[0]))


    # 3) position: add padding
    padLeft = geometry['x0']
    padRight = img_bgd.shape[1] - (padLeft + imgTmp.shape[1])
    padUp = geometry['y0']
    padDown = img_bgd.shape[0] - (padUp + imgTmp.shape[0])
    # print("\tpadLeft=%d, padRight=%d" % (padLeft, padRight))
    # print("\tpadUp=%d, padDown=%d" % (padUp, padDown))
    if padDown < 0:
        imgTmp = imgTmp[
            0:img_bgd.shape[0],
            0:imgTmp.shape[1]]
        padDown = 0
    if padRight < 0:
        imgTmp = imgTmp[
            0:imgTmp.shape[0],
            0:img_bgd.shape[1]]
        padRight = 0

    # 4) Calculate the coordinates for the foreground image (i.e. the image in the center)
    xStart = geometry['x0']
    xEnd = geometry['x1']
    yStart = geometry['y0']
    yEnd = geometry['y1']

    # print("\t(w, h) = (%d, %d) " % (xEnd - xStart + 1, yEnd - yStart + 1))
    # print("\t-> pad(l=%d, r=%d) " % (xStart, img_foreground_tmp['y0']))


    # 5) Replace the foreground image
    # print("xStart=%d, xEnd=%d, yStart=%d, yEnd=%d" % (xStart, xEnd, yStart, yEnd))
    # print("foreground=%d, xEnd=%d, yStart=%d, yEnd=%d" % (xStart, xEnd, yStart, yEnd))
    imgTmpBackground = deepcopy(img_bgd)
    imgTmpBackground[yStart:yEnd,xStart:xEnd,:] = imgTmp[0:imgTmp.shape[0],0:imgTmp.shape[1],:]

    return imgTmpBackground

