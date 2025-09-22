

from warnings import warn
import cv2
import numpy as np

from parsers import (
    Warp,
)
from utils.p_print import *
from .homography import (
    detect_and_describe,
    filter_matches_by_distance,
    get_homography,
    match_keypoints_bf,
    match_keypoints_knn,
)


def warp_image(img: np.ndarray, ref_img: np.ndarray, warp: Warp) -> np.ndarray:
    print(f"warp_image: {img.dtype}")
    feature_matching = warp.matcher

    current_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ref_gray = cv2.cvtColor(ref_img, cv2.COLOR_BGR2GRAY)

    # Worst:
    # window_size: int = 3
    # windows_search: int = 7
    # h = 3
    # ref_gray = cv2.fastNlMeansDenoising(
    #     ref_gray, h=h, templateWindowSize=window_size, searchWindowSize=windows_search
    # )
    # current_gray = cv2.fastNlMeansDenoising(
    #     current_gray, h=h, templateWindowSize=window_size, searchWindowSize=windows_search
    # )

    # Worst:
    # ref_gray = cv2.GaussianBlur(ref_gray, (3,3), 0)
    # current_gray = cv2.GaussianBlur(current_gray, (3,3), 0)

    # Create CLAHE object (Contrast Limited Adaptive Histogram Equalization)
    # 2 is better than 1 lor 3
    clip_limit=2
    tile_grid_size=(8, 8)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)

    ref_gray = clahe.apply(ref_gray)
    current_gray = clahe.apply(current_gray)

    # Add border to correctly detect the outer limits
    border = 20
    ref_gray_bordered = cv2.copyMakeBorder(
        ref_gray, top=border, bottom=border, left=border, right=border,
        borderType=cv2.BORDER_CONSTANT, value=[0, 0, 0]
    )
    current_gray = cv2.copyMakeBorder(
        current_gray, top=border, bottom=border, left=border, right=border,
        borderType=cv2.BORDER_CONSTANT, value=[0, 0, 0]
    )

    # Detect and describe
    feature_extractor: str = 'sift'
    # feature_extractor: str = 'akaze'


    keypoints_ref, features_ref = detect_and_describe(image=ref_gray_bordered, extractor_method=feature_extractor)
    keypoints, features = detect_and_describe(image=current_gray, extractor_method=feature_extractor)
    if feature_matching == 'bf':
        matches = match_keypoints_bf(
            keypoints, features, keypoints_ref, features_ref, method=feature_extractor,
            max_disp = 90
        )
    elif feature_matching == 'knn':
        matches = match_keypoints_knn(
            features, features_ref, ratio=warp.knn_ratio
        )
        matches = filter_matches_by_distance(
            matches,
            keypoints,
            keypoints_ref,
            max_disp=int(img.shape(0) * warp.max_distance_ratio)
        )
        print(f"matches: {len(matches)}")


    else:
        warn(red(f"error: unknown feature matching: {feature_matching}"))

    # Get homography
    M = get_homography(
        keypoints, keypoints_ref,
        features, features_ref,
        matches,
        reproj_threshold=4
    )
    if M is None:
        print(red("Error: get_homography returned None")) 
    (matches, H, status) = M

    # Apply the perspective transformation
    img: np.ndarray = cv2.copyMakeBorder(
        img, top=border, bottom=border, left=border, right=border,
        borderType=cv2.BORDER_CONSTANT, value=[0, 0, 0]
    )
    img_stabilized = cv2.warpPerspective(img ,H, (img.shape[1], img.shape[0]))

    img_stabilized = img_stabilized[
        border:img_stabilized.shape[0] - border,
        border:img_stabilized.shape[1] - border,
        :
    ]

    return img_stabilized
