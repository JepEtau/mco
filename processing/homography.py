import cv2
import numpy as np




def detect_and_describe(image, extractor_method = None):
    """
    Compute key points and feature descriptors using an specific method
    """

    assert extractor_method is not None, "You need to define a feature detection method. Values are: 'sift', 'surf'"

    # detect and extract features from the image
    if extractor_method == 'sift':
        descriptor = cv2.SIFT_create()
    elif extractor_method == 'surf':
        descriptor = cv2.xfeatures2d.SURF_create()
    elif extractor_method == 'brisk':
        descriptor = cv2.BRISK_create()
    elif extractor_method == 'orb':
        descriptor = cv2.ORB_create()

    # get keypoints and descriptors
    (kps, features) = descriptor.detectAndCompute(image, None)

    return (kps, features)



def create_matcher(method, crossCheck: bool = True):
    "Create and return a Matcher Object"

    if method == 'sift' or method == 'surf':
        bf = cv2.BFMatcher(cv2.NORM_L2, crossCheck=crossCheck)
        # bf = cv2.BFMatcher(cv2.NORM_L2SQR, crossCheck=crossCheck)
    elif method == 'orb' or method == 'brisk':
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=crossCheck)
    return bf



def filter_matches_by_distance(matches, keypoints, keypoints_ref, max_disp=100):
    """
    Keep only matches where the pixel distance between matched points is below max_disp.
    """
    filtered = []
    for m in matches:
        pt1 = np.array(keypoints[m.queryIdx].pt)
        pt2 = np.array(keypoints_ref[m.trainIdx].pt)
        disp = np.linalg.norm(pt1 - pt2)
        if disp < max_disp:
            filtered.append(m)
    return filtered

    

def match_keypoints_bf(keypoints, features, keypoints_ref, features_ref, method='sift', max_disp=100):
    crossCheck: bool = True
    if method == 'sift' or method == 'surf':
        bf = cv2.BFMatcher(cv2.NORM_L2, crossCheck=crossCheck)
        # bf = cv2.BFMatcher(cv2.NORM_L2SQR, crossCheck=crossCheck)
    elif method == 'orb' or method == 'brisk':
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=crossCheck)

    # Match descriptors.
    best_matches = bf.match(features, features_ref)

    # Sort the features in order of distance.
    # The points with small distance (more similarity) are ordered first in the vector
    matches = sorted(best_matches, key = lambda x:x.distance)
    # print("Raw matches (Brute force):", len(raw_matches))

    # --- Filter by geometric distance ---
    filtered = []
    for m in matches:
        pt1 = np.array(keypoints[m.queryIdx].pt)
        pt2 = np.array(keypoints_ref[m.trainIdx].pt)
        disp = np.linalg.norm(pt1 - pt2)
        if disp < max_disp:
            filtered.append(m)

    return filtered



    return matches



def match_keypoints_knn(features, features_ref, ratio = 0.75):
    crossCheck = False
    matcher = cv2.BFMatcher(cv2.NORM_L2, crossCheck=crossCheck)

    raw_matches = matcher.knnMatch(features, features_ref, 2)
    # print("Raw matches (knn):", len(raw_matches))
    matches = []
    # loop over the raw matches
    for m, n in raw_matches:
        # ensure the distance is within a certain ratio of each
        # other (i.e. Lowe's ratio test)
        if m.distance < n.distance * ratio:
            matches.append(m)
    # print(f"matches: {len(matches)}")

    return matches


def get_homography(src_keypoints, dst_keypoints, featuresA, featuresB, matches, reproj_threshold):
    # convert the keypoints to numpy arrays
    src_pts = np.float32([kp.pt for kp in src_keypoints])
    dst_pts = np.float32([kp.pt for kp in dst_keypoints])

    if len(matches) > 4:
        # construct the two sets of points
        src_points = np.float32([src_pts[m.queryIdx] for m in matches]).reshape(-1, 1, 2)
        dst_points = np.float32([dst_pts[m.trainIdx] for m in matches]).reshape(-1, 1, 2)

        # estimate the homography between the sets of points
        # (H, status) = cv2.findHomography(ptsA, ptsB, cv2.RANSAC, reproj_threshold)
        # (H, status) = cv2.findHomography(ptsA, ptsB, cv2.LMEDS, reproj_threshold)

        (H, status) = cv2.findHomography(
            srcPoints=src_points,
            dstPoints=dst_points,
            method=cv2.RANSAC,
            ransacReprojThreshold=reproj_threshold)
        return (matches, H, status)
    else:
        print("Error: not enough points")
        return None
